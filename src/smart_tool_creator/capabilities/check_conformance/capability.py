"""Check conformance: run the spec's conformance kit against a smart tool and return its verdict."""

import json
import os
from pathlib import Path
import shutil
import subprocess

from liquid import Environment, StrictUndefined
from pydantic import BaseModel, Field, ValidationError

from smart_tool_creator.schemas import (
    DEFAULT_PROBE_TIMEOUT_SECONDS,
    ConformanceReport,
    ConformanceRule,
    ConformanceVerdict,
    SmartToolCreatorError,
)

OUTPUT_MESSAGE_PATH = Path(__file__).parent / "output_message.md.liquid"

CONFORMANCE_KIT = "https://raw.githubusercontent.com/microsoft/amplifier-smart-tools/main/conformance/run.py"
CONFORMANCE_KIT_README = "https://github.com/microsoft/amplifier-smart-tools/tree/main/conformance"
STDERR_TAIL_CHARACTERS = 2000

ENVIRONMENT = Environment(undefined=StrictUndefined)


class KitVerdict(BaseModel):
    """The document the kit prints on stdout: `smart-tools-conformance/v1`."""

    kit_schema: str = Field(alias="schema")
    target: Path
    verdict: ConformanceVerdict
    counts: dict[str, int]
    failed_rules: list[str]
    checks: list[ConformanceRule]


def check_conformance(
    directory: Path | None = None, timeout: float = DEFAULT_PROBE_TIMEOUT_SECONDS
) -> ConformanceReport:
    """Run the conformance kit against the smart tool at `directory` and return its verdict, rule by rule."""
    root = (Path.cwd() if directory is None else directory).resolve()
    if not root.is_dir():
        raise SmartToolCreatorError(
            f"{root} is not a directory. Point --directory at a smart tool's distribution root: "
            "the directory holding its pyproject.toml or package.json and its smart-tool.json."
        )
    if shutil.which("uv") is None:
        raise SmartToolCreatorError("'uv' is not on PATH. Install it from https://docs.astral.sh/uv/ and try again.")

    command = conformance_command(root, timeout)
    completed = subprocess.run(command, cwd=root, capture_output=True, text=True, env=clean_environment())
    verdict = _parse(completed, command)
    rules = verdict.checks
    output_message = ENVIRONMENT.render(
        OUTPUT_MESSAGE_PATH.read_text(encoding="utf-8"),
        root=str(root),
        rules=[rule.model_dump() for rule in rules],
        verdict=verdict.verdict,
        counts=verdict.counts,
        failed_rules=verdict.failed_rules,
    ).rstrip()
    return ConformanceReport(
        root=root,
        verdict=verdict.verdict,
        counts=verdict.counts,
        failed_rules=verdict.failed_rules,
        rules=rules,
        output_message=output_message,
    )


def conformance_command(root: Path, timeout: float = DEFAULT_PROBE_TIMEOUT_SECONDS) -> list[str]:
    """The kit invocation for `root`, to be run from `root`.

    The kit never installs the tool under test, so a uv project is wrapped in `uv run --` to put its console
    script on PATH; the inner `uv run --no-project` fetches the kit and resolves its inline dependencies.
    """
    kit = ["uv", "run", "--no-project", CONFORMANCE_KIT, str(root), "--json-only", "--timeout", f"{timeout:g}"]
    if (root / "pyproject.toml").is_file():
        return ["uv", "run", "--", *kit]
    return kit


def clean_environment() -> dict[str, str]:
    """This process's environment without its own virtual environment, which uv would otherwise use."""
    return {key: value for key, value in os.environ.items() if key != "VIRTUAL_ENV"}


def _parse(completed: subprocess.CompletedProcess[str], command: list[str]) -> KitVerdict:
    """The kit's verdict, or why there is none: it exits 1 on FAIL too, so only stdout tells the two apart."""
    try:
        return KitVerdict.model_validate(json.loads(completed.stdout))
    except (json.JSONDecodeError, ValidationError):
        stderr = completed.stderr.strip()
        tail = stderr[-STDERR_TAIL_CHARACTERS:] if stderr else "(nothing on stderr)"
        raise SmartToolCreatorError(
            f"The conformance kit did not return a verdict (exit {completed.returncode}). "
            f"It is fetched from {CONFORMANCE_KIT}, so check the network, that uv can run it, and that "
            f"its output contract has not changed ({CONFORMANCE_KIT_README}). "
            f"Command, run from the tool's root: {' '.join(command)}\n{tail}"
        ) from None
