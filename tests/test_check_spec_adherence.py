"""Drives the reviewers with a fake intelligence and a faked conformance verdict, so no provider is needed."""

from pathlib import Path
import shutil

import pytest
from typer.testing import CliRunner

from smart_tool_creator.capabilities.check_spec_adherence import capability as adherence
from smart_tool_creator.capabilities.check_spec_adherence import checks as checklist
from smart_tool_creator.capabilities.check_spec_adherence.checks import checks_by_id, review_groups
from smart_tool_creator.cli import app
from smart_tool_creator.intelligence.schemas import AgentRequest, AgentResult
from smart_tool_creator.lib import check_spec_adherence, spec_checks
from smart_tool_creator.schemas import ConformanceReport, SmartToolCreatorError, SpecAdherenceReport

CHECK_COUNT = 17
GROUP_COUNT = 5
SUGGESTION = "Move the formatting out of the CLI and into the library."
OUTPUT_MESSAGE = "The message the library rendered."

GROUP_NAMES = ["boundary", "smart-paths", "self-description", "results", "failures"]
CHECK_IDS = [
    "library-holds-every-capability",
    "cli-is-thin",
    "help-comes-from-library",
    "genuinely-model-backed",
    "ai-capabilities-identifiable",
    "no-provider-failure-names-remedy",
    "tool-skill-content",
    "capability-skills-complete",
    "agent-skill-is-thin",
    "manifest-describes-the-tool",
    "context-accepted-as-data",
    "stdout-results-stderr-diagnostics",
    "artifact-location-named",
    "files-outside-install-tree",
    "failure-names-remedy",
    "partial-results-are-failures",
    "prerequisite-failures-match-manifest",
]

runner = CliRunner()


class FakeIntelligence:
    """Answers whichever group's checks appear in the prompt, so one fake serves every reviewer."""

    def __init__(self, deviating: set[str] | None = None, skip: set[str] | None = None) -> None:
        self.implementation = "fake"
        self.requests: list[AgentRequest] = []
        self.preflights = 0
        self._deviating = deviating or set()
        self._skip = skip or set()

    def preflight(self) -> None:
        self.preflights += 1

    def run(self, request: AgentRequest) -> AgentResult:
        self.requests.append(request)
        findings = [
            {
                "id": identifier,
                "status": "deviates" if identifier in self._deviating else "adheres",
                "evidence": [f"lib.py:1 evidence for {identifier}"],
                "suggestion": SUGGESTION if identifier in self._deviating else "",
            }
            for identifier in _asked(request.prompt)
            if identifier not in self._skip
        ]
        return AgentResult(output={"findings": findings})


def _asked(prompt: str) -> list[str]:
    return [identifier for identifier in checks_by_id() if f"### {identifier}\n" in prompt]


def _conformance(verdict: str) -> ConformanceReport:
    counts = {"pass": 0 if verdict == "FAIL" else 1, "fail": 1 if verdict == "FAIL" else 0, "skip": 0}
    return ConformanceReport(
        root=Path("/tmp/tool"),
        verdict="FAIL" if verdict == "FAIL" else "PASS",
        counts=counts,
        failed_rules=["descriptor-present"] if verdict == "FAIL" else [],
        rules=[],
        output_message="The kit's own report.",
    )


@pytest.fixture
def descriptor_only(tmp_path: Path) -> Path:
    """A directory that passes detection and nothing else; the kit's verdict is faked."""
    (tmp_path / "smart-tool.json").write_text('{"smart_tool_format": 1}', encoding="utf-8")
    return tmp_path


@pytest.fixture
def passing_kit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(adherence, "check_conformance", lambda directory: _conformance("PASS"))


@pytest.fixture
def failing_kit(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(adherence, "check_conformance", lambda directory: _conformance("FAIL"))


def test_the_checklist_loads_from_markdown_in_the_documented_order() -> None:
    groups = review_groups()

    assert [group.name for group in groups] == GROUP_NAMES
    assert [check.id for group in groups for check in group.checks] == CHECK_IDS
    assert len(CHECK_IDS) == CHECK_COUNT
    assert len(GROUP_NAMES) == GROUP_COUNT
    for group in groups:
        assert all(path.strip() for path in group.read_first)
        for check in group.checks:
            assert check.spec_file.endswith(".md")
            assert check.spec.strip()
            assert check.guidance.strip()


def test_the_library_hands_back_the_same_checklist() -> None:
    assert [check.id for group in spec_checks() for check in group.checks] == CHECK_IDS


def test_a_check_file_no_group_lists_is_refused_by_name(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    root = tmp_path / "checks"
    shutil.copytree(checklist.CHECKS_ROOT, root)
    stray = root / "boundary" / "stray-check.md"
    stray.write_text("---\nspec_file: structure.md\nspec: A sentence.\n---\n\nBody.\n", encoding="utf-8")
    monkeypatch.setattr(checklist, "CHECKS_ROOT", root)
    review_groups.cache_clear()

    try:
        with pytest.raises(SmartToolCreatorError) as failure:
            review_groups()
        assert "stray-check.md" in str(failure.value)
    finally:
        review_groups.cache_clear()


def test_an_unknown_check_is_refused_before_the_reviewers_run(descriptor_only: Path) -> None:
    fake = FakeIntelligence()

    with pytest.raises(SmartToolCreatorError) as failure:
        check_spec_adherence(directory=descriptor_only, checks=["cli-is-thin", "nope"], intelligence=fake)

    message = str(failure.value)
    assert "nope" in message
    assert "cli-is-thin" in message
    assert fake.requests == []
    assert fake.preflights == 0


@pytest.mark.usefixtures("passing_kit")
def test_every_group_is_reviewed_read_only_and_the_findings_follow_the_checklist(descriptor_only: Path) -> None:
    fake = FakeIntelligence(deviating={"cli-is-thin"}, skip={"failure-names-remedy"})

    report = check_spec_adherence(directory=descriptor_only, intelligence=fake)

    assert len(fake.requests) == GROUP_COUNT
    assert fake.preflights == 1
    for request in fake.requests:
        assert request.workspace is not None
        assert request.workspace.path == descriptor_only.resolve()
        assert request.writable is False
        assert request.output_schema is not None
        assert str(descriptor_only.resolve()) in request.prompt
    assert [finding.id for finding in report.findings] == list(checks_by_id())
    assert report.deviating == ["cli-is-thin"]
    assert report.counts == {"adheres": 15, "deviates": 1, "not-applicable": 0, "unclear": 1}
    unanswered = next(finding for finding in report.findings if finding.id == "failure-names-remedy")
    assert unanswered.status == "unclear"
    assert unanswered.evidence == [adherence.UNANSWERED]
    deviation = next(finding for finding in report.findings if finding.id == "cli-is-thin")
    assert deviation.spec == checks_by_id()["cli-is-thin"].spec
    assert SUGGESTION in report.output_message
    assert "deviates cli-is-thin" in report.output_message


@pytest.mark.usefixtures("passing_kit")
def test_only_the_groups_holding_a_selected_check_are_reviewed(descriptor_only: Path) -> None:
    fake = FakeIntelligence()

    report = check_spec_adherence(directory=descriptor_only, checks=["cli-is-thin"], intelligence=fake)

    assert len(fake.requests) == 1
    assert [finding.id for finding in report.findings] == ["cli-is-thin"]
    assert report.counts["adheres"] == 1
    assert report.deviating == []


@pytest.mark.usefixtures("failing_kit")
def test_a_failing_kit_stops_before_any_reviewer_runs(descriptor_only: Path) -> None:
    fake = FakeIntelligence()

    report = check_spec_adherence(directory=descriptor_only, intelligence=fake)

    assert fake.requests == []
    assert report.findings == []
    assert report.deviating == []
    assert report.conformance.verdict == "FAIL"
    assert "The kit's own report." in report.output_message
    assert "Fix the failing rules above and run check-spec-adherence again." in report.output_message


def test_the_cli_prints_the_message_and_exits_zero_when_nothing_deviates(monkeypatch: pytest.MonkeyPatch) -> None:
    report = SpecAdherenceReport(
        root=Path("/tmp/tool"),
        conformance=_conformance("PASS"),
        findings=[],
        counts={"adheres": CHECK_COUNT, "deviates": 0, "not-applicable": 0, "unclear": 0},
        deviating=[],
        output_message=OUTPUT_MESSAGE,
    )
    monkeypatch.setattr("smart_tool_creator.lib.check_spec_adherence", lambda *arguments, **keywords: report)

    result = runner.invoke(app, ["check-spec-adherence"])

    assert result.exit_code == 0
    assert result.stdout == f"{OUTPUT_MESSAGE}\n"


def test_the_cli_exits_one_when_a_check_deviates(monkeypatch: pytest.MonkeyPatch) -> None:
    report = SpecAdherenceReport(
        root=Path("/tmp/tool"),
        conformance=_conformance("PASS"),
        findings=[],
        counts={"adheres": CHECK_COUNT - 1, "deviates": 1, "not-applicable": 0, "unclear": 0},
        deviating=["cli-is-thin"],
        output_message=OUTPUT_MESSAGE,
    )
    monkeypatch.setattr("smart_tool_creator.lib.check_spec_adherence", lambda *arguments, **keywords: report)

    result = runner.invoke(app, ["check-spec-adherence"])

    assert result.exit_code == 1
    assert result.stdout == f"{OUTPUT_MESSAGE}\n"
