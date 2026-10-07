"""Add smart capability: an agent implements one model-backed capability inside an existing smart tool."""

from pathlib import Path
import shutil
import subprocess

from liquid import Environment, StrictUndefined

from smart_tool_creator.capabilities.check_conformance.capability import (
    check_conformance,
    clean_environment,
    conformance_command,
)
from smart_tool_creator.intelligence.interface import Intelligence, select_intelligence
from smart_tool_creator.intelligence.schemas import AgentRequest, AgentResult, HostWorkspace
from smart_tool_creator.schemas import (
    DEFAULT_INTELLIGENCE_MODELS,
    DEFAULT_INTELLIGENCE_REASONING_EFFORT,
    AddedCapability,
    AgentProvider,
    Check,
    ReasoningEffort,
    SmartToolCreatorError,
)

PROMPT_PATH = Path(__file__).parent / "add_smart_capability.md.liquid"
FIX_CHECKS_PROMPT_PATH = Path(__file__).parent / "fix_checks.md.liquid"
OUTPUT_MESSAGE_PATH = Path(__file__).parent / "output_message.md.liquid"

DESCRIPTOR = "smart-tool.json"
PRE_COMMIT_CONFIG = ".pre-commit-config.yaml"

PYTEST_COMMAND = ["uv", "run", "pytest"]
PREK_COMMAND = ["prek", "run", "--all-files"]

ADD_SMART_CAPABILITY_TIMEOUT_SECONDS = 1800
MAX_FIX_ROUNDS = 2
# A failing check names itself at the end of its output, so the tail is what the agent needs.
OUTPUT_TAIL_CHARACTERS = 4000

ENVIRONMENT = Environment(undefined=StrictUndefined)


def add_smart_capability(
    request: str,
    directory: Path | None = None,
    context: list[str] | None = None,
    agent_provider: AgentProvider | None = None,
    model: str | None = None,
    reasoning_effort: ReasoningEffort = DEFAULT_INTELLIGENCE_REASONING_EFFORT,
    intelligence: Intelligence | None = None,
) -> AddedCapability:
    """Extend an existing smart tool with one model-backed capability, then hold it to the tool's own checks."""
    root = (Path.cwd() if directory is None else directory).resolve()
    request = " ".join(request.split())
    entries = list(context or [])
    intelligence, model = select_intelligence(intelligence, agent_provider, model, DEFAULT_INTELLIGENCE_MODELS)
    _preflight(request, root, intelligence)

    prompt = _render(
        PROMPT_PATH,
        root=str(root),
        request=request,
        context=entries,
        default_models=list(DEFAULT_INTELLIGENCE_MODELS.items()),
    )
    result = _agent(intelligence, prompt, root, model, reasoning_effort)

    checks = _checks(root)
    fix_rounds = 0
    while _failed(checks) and fix_rounds < MAX_FIX_ROUNDS:
        prompt = _render(FIX_CHECKS_PROMPT_PATH, root=str(root), checks=_failing_summary(checks))
        # Continuing the implementation session keeps what the agent already learned about the tool.
        result = _agent(intelligence, prompt, root, model, reasoning_effort, resume=result.session_id)
        checks = _checks(root)
        fix_rounds += 1
    output_message = _render(
        OUTPUT_MESSAGE_PATH,
        root=str(root),
        report=result.text,
        checks=[check.model_dump() for check in checks],
        fix_rounds=fix_rounds,
        failing=[check.name for check in _failed(checks)],
    ).rstrip()
    return AddedCapability(
        root=root, report=result.text, checks=checks, fix_rounds=fix_rounds, output_message=output_message
    )


def _preflight(request: str, root: Path, intelligence: Intelligence) -> None:
    """Everything that can be known before the agent runs, so a failure leaves the tool as it was."""
    # The descriptor has to be at the root itself: walking up would pick a neighbouring tool by
    # accident when this runs from a workspace holding several of them.
    if not (root / DESCRIPTOR).is_file():
        raise SmartToolCreatorError(
            f"No smart tool at {root}: {DESCRIPTOR} is not there. "
            f"Run 'smart-tool-creator init <name> --description \"...\" --directory {root}' first, "
            "then call add-smart-capability again."
        )
    if not _intelligence_interfaces(root):
        raise SmartToolCreatorError(
            f"The tool at {root} has no Intelligence interface for a model-backed capability to run through: "
            "no intelligence/interface.py under src/<package>/. Scaffold the tool with at least one agent provider "
            "('smart-tool-creator init <name> --description \"...\" --agent-provider copilot'), or add an "
            "intelligence package like the one that command writes, then call add-smart-capability again."
        )
    if not request:
        raise SmartToolCreatorError(
            "The new capability needs a request. Say what it does, who it is for, and what it takes in and gives back."
        )
    if shutil.which("uv") is None:
        raise SmartToolCreatorError("'uv' is not on PATH. Install it from https://docs.astral.sh/uv/ and try again.")
    intelligence.preflight()


def _intelligence_interfaces(root: Path) -> list[Path]:
    """The tool's Intelligence interface, in the src layout a scaffold uses or the flat one."""
    return [*root.glob("src/*/intelligence/interface.py"), *root.glob("*/intelligence/interface.py")]


def _render(template: Path, **variables: object) -> str:
    return ENVIRONMENT.render(template.read_text(encoding="utf-8"), **variables)


def _agent(
    intelligence: Intelligence,
    prompt: str,
    root: Path,
    model: str,
    reasoning_effort: ReasoningEffort,
    resume: str | None = None,
) -> AgentResult:
    """One agent run against the tool's own working tree; its final message is the report."""
    result = intelligence.run(
        AgentRequest(
            prompt=prompt,
            model=model,
            workspace=HostWorkspace(path=root),
            writable=True,
            output_schema=None,
            reasoning_effort=reasoning_effort,
            timeout_seconds=ADD_SMART_CAPABILITY_TIMEOUT_SECONDS,
            resume=resume,
        )
    )
    if result.error is not None:
        raise SmartToolCreatorError(
            f"The agent extending {root} failed: {result.error} "
            f"The tool's working tree may hold partial edits; inspect them with `git -C {root} status` "
            "and discard them if they are not worth keeping."
        )
    return result


def _checks(root: Path) -> list[Check]:
    """The tool's own checks, run in its root: what a published smart tool is held to."""
    return [
        _run_check("pytest", PYTEST_COMMAND, root),
        _prek(root),
        _conformance(root),
    ]


def _conformance(root: Path) -> Check:
    """The conformance kit's verdict as a check; a failing rule's detail is what the agent needs to fix it.

    Skipped, like prek, when the kit itself could not run: that is the machine's problem, not the tool's.
    """
    command = conformance_command(root)
    try:
        report = check_conformance(directory=root)
    except SmartToolCreatorError as error:
        return Check(name="conformance", command=command, status="skipped", output=str(error))
    failing = [rule for rule in report.rules if rule.status == "FAIL"]
    if not failing:
        return Check(name="conformance", command=command, status="passed", output="")
    output = "\n".join(f"{rule.id}: {rule.detail}\n  {rule.spec}" for rule in failing)
    return Check(name="conformance", command=command, status="failed", output=_tail(output))


def _prek(root: Path) -> Check:
    """Lint and format, skipped rather than failed when the tool or the machine has no prek."""
    if not (root / PRE_COMMIT_CONFIG).is_file():
        return Check(
            name="prek",
            command=PREK_COMMAND,
            status="skipped",
            output=f"{PRE_COMMIT_CONFIG} is not in {root}, so this tool has no lint and format hooks to run.",
        )
    if shutil.which("prek") is None:
        return Check(
            name="prek",
            command=PREK_COMMAND,
            status="skipped",
            output="'prek' is not on PATH; install it from https://github.com/j178/prek to run this tool's hooks.",
        )
    return _run_check("prek", PREK_COMMAND, root)


def _run_check(name: str, command: list[str], root: Path) -> Check:
    completed = subprocess.run(command, cwd=root, capture_output=True, text=True, env=clean_environment())
    if completed.returncode == 0:
        return Check(name=name, command=command, status="passed", output="")
    return Check(name=name, command=command, status="failed", output=_tail(completed.stdout + completed.stderr))


def _failed(checks: list[Check]) -> list[Check]:
    return [check for check in checks if check.status == "failed"]


def _failing_summary(checks: list[Check]) -> list[dict[str, str]]:
    return [
        {"name": check.name, "command": " ".join(check.command), "output": check.output} for check in _failed(checks)
    ]


def _tail(output: str) -> str:
    text = output.strip()
    if len(text) <= OUTPUT_TAIL_CHARACTERS:
        return text
    return f"[earlier output omitted]\n{text[-OUTPUT_TAIL_CHARACTERS:]}"
