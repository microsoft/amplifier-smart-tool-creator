"""Drives the capability with a fake intelligence, and holds its checks to a tool scaffolded for real."""

from collections.abc import Callable
import os
from pathlib import Path
import shutil

import pytest
from typer.testing import CliRunner

from smart_tool_creator.capabilities.add_smart_capability.capability import MAX_FIX_ROUNDS
from smart_tool_creator.cli import app
from smart_tool_creator.intelligence.interface import Intelligence, resolve_intelligence
from smart_tool_creator.intelligence.schemas import AgentRequest, AgentResult
from smart_tool_creator.lib import add_smart_capability, init
from smart_tool_creator.schemas import DEFAULT_INTELLIGENCE_MODEL, AddedCapability, Check, SmartToolCreatorError

NAME = "release-notes"
DESCRIPTION = "Summarizes changelogs into release notes"
REQUEST = "Summarize a changelog into release notes grouped by audience"
REPORT = "Added the summarize capability."
OUTPUT_MESSAGE = "The message the library rendered."
SESSION = "fake-session"
FAILING_TEST = Path("tests") / "test_temporarily_failing.py"
PLANTED_IMPORT = "import module_that_does_not_exist\n"

runner = CliRunner()


class FakeIntelligence:
    """Records what the capability asks for and optionally edits the workspace, so no provider is needed."""

    def __init__(
        self,
        edit: Callable[[Path, int], None] | None = None,
        error: str | None = None,
        session_ids: bool = True,
    ) -> None:
        self.implementation = "fake"
        self.requests: list[AgentRequest] = []
        self.results: list[AgentResult] = []
        self.preflights = 0
        self._edit = edit
        self._error = error
        self._session_ids = session_ids

    def preflight(self) -> None:
        self.preflights += 1

    def run(self, request: AgentRequest) -> AgentResult:
        self.requests.append(request)
        if self._error is not None:
            return AgentResult(error=self._error)
        if self._edit is not None and request.workspace is not None:
            self._edit(request.workspace.path, len(self.requests))
        result = AgentResult(
            text=f"{REPORT} Run {len(self.requests)}.",
            session_id=f"{SESSION}-{len(self.requests)}" if self._session_ids else None,
        )
        self.results.append(result)
        return result


def fail_then_repair(root: Path, run: int) -> None:
    """Breaks the tool's checks on the first run so a fix round happens, and repairs it on the next."""
    if run == 1:
        (root / FAILING_TEST).write_text(
            "def test_temporarily_failing() -> None:\n    raise AssertionError\n", encoding="utf-8"
        )
    else:
        (root / FAILING_TEST).unlink()


@pytest.fixture(scope="module")
def scaffolded(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """One real scaffold for the whole module; the tests that need a tool copy it."""
    root = tmp_path_factory.mktemp("scaffolded") / NAME
    init(NAME, DESCRIPTION, directory=root)
    return root


@pytest.fixture
def tool(scaffolded: Path, tmp_path: Path) -> Path:
    """A private copy of the scaffolded tool. Its environment and reference clones are rebuilt on demand."""
    root = tmp_path / NAME
    shutil.copytree(scaffolded, root, ignore=shutil.ignore_patterns(".venv", "reference"))
    return root


@pytest.fixture
def descriptor_only(tmp_path: Path) -> Path:
    """A directory that passes detection and nothing else, so the checks fail fast."""
    (tmp_path / "smart-tool.json").write_text('{"smart_tool_format": 1}', encoding="utf-8")
    return tmp_path


def test_a_directory_without_a_descriptor_names_init_and_never_reaches_the_model(tmp_path: Path) -> None:
    fake = FakeIntelligence()

    with pytest.raises(SmartToolCreatorError) as failure:
        add_smart_capability(REQUEST, directory=tmp_path, intelligence=fake)

    message = str(failure.value)
    assert str(tmp_path.resolve()) in message
    assert "smart-tool.json is not there" in message
    assert "smart-tool-creator init" in message
    assert fake.requests == []
    assert fake.preflights == 0


def test_an_empty_request_is_refused_before_the_agent_runs(descriptor_only: Path) -> None:
    fake = FakeIntelligence()

    with pytest.raises(SmartToolCreatorError) as failure:
        add_smart_capability("   \n  ", directory=descriptor_only, intelligence=fake)

    assert "needs a request" in str(failure.value)
    assert fake.requests == []


def test_the_prompt_carries_the_request_the_context_and_the_root(descriptor_only: Path) -> None:
    context = ["Exemplar prompt at ~/notes/release-prompt.md", "Transcript at ~/sessions/abc/transcript.md"]
    fake = FakeIntelligence()

    add_smart_capability(REQUEST, directory=descriptor_only, context=context, intelligence=fake)

    request = fake.requests[0]
    assert REQUEST in request.prompt
    for entry in context:
        assert entry in request.prompt
    assert str(descriptor_only.resolve()) in request.prompt
    assert DEFAULT_INTELLIGENCE_MODEL in request.prompt
    assert request.workspace is not None
    assert request.workspace.path == descriptor_only.resolve()
    assert request.writable is True
    assert request.output_schema is None
    assert request.timeout_seconds > 0
    assert fake.preflights == 1


def test_a_scaffolded_tool_left_untouched_passes_every_check(tool: Path) -> None:
    fake = FakeIntelligence()

    added = add_smart_capability(REQUEST, directory=tool, intelligence=fake)

    assert added.root == tool.resolve()
    assert added.report == f"{REPORT} Run 1."
    assert added.fix_rounds == 0
    assert len(fake.requests) == 1
    assert [check.name for check in added.checks] == ["pytest", "prek", "conformance"]
    assert [check.status for check in added.checks] == ["passed"] * 3, added.checks
    assert added.output_message.startswith(added.report)
    assert "pytest passed" in added.output_message
    assert "Next:" in added.output_message
    assert "docs/00-vision.md" in added.output_message
    assert "Still failing" not in added.output_message


def test_prek_is_skipped_when_it_is_not_installed(tool: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    installed = shutil.which
    monkeypatch.setattr(shutil, "which", lambda name: None if name == "prek" else installed(name))

    fake = FakeIntelligence()

    added = add_smart_capability(REQUEST, directory=tool, intelligence=fake)

    prek = next(check for check in added.checks if check.name == "prek")
    assert prek.status == "skipped"
    assert "prek" in prek.output
    assert [check.status for check in added.checks] == ["passed", "skipped", "passed"], added.checks
    assert f"prek skipped: {prek.output}" in added.output_message
    assert added.fix_rounds == 0
    assert len(fake.requests) == 1


def test_a_failing_check_is_fixed_in_one_more_round(tool: Path) -> None:
    fake = FakeIntelligence(fail_then_repair)

    added = add_smart_capability(REQUEST, directory=tool, intelligence=fake)

    assert added.fix_rounds == 1
    assert len(fake.requests) == 2
    assert FAILING_TEST.name in fake.requests[1].prompt
    assert "uv run pytest" in fake.requests[1].prompt
    assert added.report == f"{REPORT} Run 2."
    assert [check.status for check in added.checks] == ["passed"] * 3, added.checks


def test_the_fix_round_continues_the_implementation_session(tool: Path) -> None:
    fake = FakeIntelligence(fail_then_repair)

    add_smart_capability(REQUEST, directory=tool, intelligence=fake)

    assert fake.requests[0].resume is None
    assert fake.requests[1].resume == fake.results[0].session_id


def test_a_fix_round_starts_fresh_when_the_run_before_it_named_no_session(tool: Path) -> None:
    fake = FakeIntelligence(fail_then_repair, session_ids=False)

    add_smart_capability(REQUEST, directory=tool, intelligence=fake)

    assert [request.resume for request in fake.requests] == [None, None]


def test_checks_still_failing_after_the_cap_are_returned_rather_than_raised(descriptor_only: Path) -> None:
    fake = FakeIntelligence()

    added = add_smart_capability(REQUEST, directory=descriptor_only, intelligence=fake)

    assert added.fix_rounds == MAX_FIX_ROUNDS
    assert len(fake.requests) == MAX_FIX_ROUNDS + 1
    assert [check.name for check in added.checks if check.status == "failed"]
    assert added.report == f"{REPORT} Run {MAX_FIX_ROUNDS + 1}."
    assert f"Still failing after {MAX_FIX_ROUNDS} fix rounds" in added.output_message
    assert str(descriptor_only.resolve()) in added.output_message


def test_an_agent_failure_names_the_error_and_the_working_tree(descriptor_only: Path) -> None:
    fake = FakeIntelligence(error="The agent did not finish within 1800 seconds.")

    with pytest.raises(SmartToolCreatorError) as failure:
        add_smart_capability(REQUEST, directory=descriptor_only, intelligence=fake)

    message = str(failure.value)
    assert "The agent did not finish within 1800 seconds." in message
    assert "partial edits" in message
    assert str(descriptor_only.resolve()) in message


def test_the_cli_prints_the_output_message_and_exits_zero_when_no_check_failed(monkeypatch: pytest.MonkeyPatch) -> None:
    added = AddedCapability(
        root=Path("/tmp/release-notes"),
        report=REPORT,
        checks=[Check(name="pytest", command=["uv", "run", "pytest"], status="passed", output="")],
        fix_rounds=0,
        output_message=OUTPUT_MESSAGE,
    )
    monkeypatch.setattr("smart_tool_creator.lib.add_smart_capability", lambda *arguments, **keywords: added)

    result = runner.invoke(app, ["add-smart-capability", REQUEST])

    assert result.exit_code == 0
    assert result.stdout == f"{OUTPUT_MESSAGE}\n"


def test_the_cli_exits_one_when_a_check_is_still_failing(monkeypatch: pytest.MonkeyPatch) -> None:
    added = AddedCapability(
        root=Path("/tmp/release-notes"),
        report=REPORT,
        checks=[Check(name="pytest", command=["uv", "run", "pytest"], status="failed", output="1 failed")],
        fix_rounds=MAX_FIX_ROUNDS,
        output_message=OUTPUT_MESSAGE,
    )
    monkeypatch.setattr("smart_tool_creator.lib.add_smart_capability", lambda *arguments, **keywords: added)

    result = runner.invoke(app, ["add-smart-capability", REQUEST])

    assert result.exit_code == 1
    assert result.stdout == f"{OUTPUT_MESSAGE}\n"


@pytest.mark.skipif(
    os.environ.get("SMART_TOOL_CREATOR_LIVE") != "1",
    reason="Runs a real agent through the first installed agent provider; set SMART_TOOL_CREATOR_LIVE=1 to include it.",
)
def test_live_adds_a_working_capability_to_a_scaffolded_tool(tool: Path) -> None:
    added = add_smart_capability(
        "A `reverse` capability that takes TEXT and returns it with its words in reverse order, "
        "decided by the model rather than by string manipulation",
        directory=tool,
    )

    assert added.report.strip()
    assert [check.status for check in added.checks if check.status == "failed"] == [], added.checks


class BreaksTheToolOnce:
    """Runs the real intelligence and breaks the capability it wrote after its first run, forcing a fix round."""

    def __init__(self, intelligence: Intelligence, root: Path) -> None:
        self.implementation = intelligence.implementation
        self.requests: list[AgentRequest] = []
        self.results: list[AgentResult] = []
        self.broken: Path | None = None
        self._intelligence = intelligence
        self._root = root

    def preflight(self) -> None:
        self._intelligence.preflight()

    def run(self, request: AgentRequest) -> AgentResult:
        self.requests.append(request)
        result = self._intelligence.run(request)
        self.results.append(result)
        if len(self.results) == 1:
            # A bogus import is a real defect with one honest fix, unlike a planted failing test the
            # fix prompt forbids the agent to delete or weaken.
            self.broken = next((self._root / "src").rglob("capabilities/*/capability.py"))
            with self.broken.open("a", encoding="utf-8") as handle:
                handle.write(PLANTED_IMPORT)
        return result


@pytest.mark.skipif(
    os.environ.get("SMART_TOOL_CREATOR_LIVE") != "1",
    reason="Runs a real agent through the first installed agent provider; set SMART_TOOL_CREATOR_LIVE=1 to include it.",
)
def test_live_a_fix_round_resumes_the_implementation_session(tool: Path) -> None:
    intelligence = BreaksTheToolOnce(resolve_intelligence(), tool)

    added = add_smart_capability(
        "Add a model-backed capability `greet` that takes a name and returns a one-line greeting",
        directory=tool,
        intelligence=intelligence,
    )

    assert added.fix_rounds >= 1
    assert [check.status for check in added.checks if check.status == "failed"] == [], added.checks
    assert intelligence.results[0].session_id is not None
    assert intelligence.requests[1].resume == intelligence.results[0].session_id
    assert intelligence.broken is not None
    assert PLANTED_IMPORT not in intelligence.broken.read_text(encoding="utf-8")
