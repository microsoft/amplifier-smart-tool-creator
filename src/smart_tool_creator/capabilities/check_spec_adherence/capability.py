"""Check spec adherence: reviewers judge a smart tool against the parts of the spec the kit cannot decide."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import shutil
from typing import Any

from liquid import Environment, StrictUndefined
from pydantic import BaseModel, ValidationError

from smart_tool_creator.capabilities.check_conformance.capability import check_conformance
from smart_tool_creator.capabilities.check_spec_adherence.checks import checks_by_id, select
from smart_tool_creator.intelligence.interface import Intelligence, select_intelligence
from smart_tool_creator.intelligence.schemas import AgentRequest, HostWorkspace
from smart_tool_creator.schemas import (
    DEFAULT_REVIEW_MODELS,
    DEFAULT_REVIEW_REASONING_EFFORT,
    AgentProvider,
    ConformanceReport,
    Finding,
    FindingStatus,
    ReasoningEffort,
    ReviewGroup,
    SmartToolCreatorError,
    SpecAdherenceReport,
)

REVIEW_PROMPT_PATH = Path(__file__).parent / "review.md.liquid"
OUTPUT_MESSAGE_PATH = Path(__file__).parent / "output_message.md.liquid"

DESCRIPTOR = "smart-tool.json"

REVIEW_TIMEOUT_SECONDS = 900
STATUSES: tuple[FindingStatus, ...] = ("adheres", "deviates", "not-applicable", "unclear")
UNANSWERED = "The reviewer returned no finding for this check."

ENVIRONMENT = Environment(undefined=StrictUndefined)


class SubmittedFinding(BaseModel):
    """One answer as a reviewer submitted it, before the checklist's spec sentence is attached."""

    id: str
    status: FindingStatus
    evidence: list[str]
    suggestion: str


class Submission(BaseModel):
    """What one reviewer submits: its answer to every check of its group."""

    findings: list[SubmittedFinding]


def check_spec_adherence(
    directory: Path | None = None,
    checks: list[str] | None = None,
    agent_provider: AgentProvider | None = None,
    model: str | None = None,
    reasoning_effort: ReasoningEffort = DEFAULT_REVIEW_REASONING_EFFORT,
    intelligence: Intelligence | None = None,
) -> SpecAdherenceReport:
    """Review the smart tool at `directory` against the spec sentences the conformance kit cannot decide."""
    root = (Path.cwd() if directory is None else directory).resolve()
    intelligence, model = select_intelligence(intelligence, agent_provider, model, DEFAULT_REVIEW_MODELS)
    groups = _preflight(root, checks, intelligence)

    conformance = check_conformance(directory=root)
    if conformance.verdict == "FAIL":
        return _kit_failed(root, conformance)

    with ThreadPoolExecutor(max_workers=len(groups)) as pool:
        answers = list(pool.map(lambda group: _review(intelligence, group, root, model, reasoning_effort), groups))

    findings = _ordered([finding for answer in answers for finding in answer])
    counts = _counts(findings)
    deviating = [finding.id for finding in findings if finding.status == "deviates"]
    output_message = _render(
        OUTPUT_MESSAGE_PATH,
        root=str(root),
        kit_failed=False,
        conformance_message=conformance.output_message,
        findings=[_summarized(finding) for finding in findings],
        deviations=[_summarized(finding) for finding in findings if finding.status == "deviates"],
        counts=counts,
    ).rstrip()
    return SpecAdherenceReport(
        root=root,
        conformance=conformance,
        findings=findings,
        counts=counts,
        deviating=deviating,
        output_message=output_message,
    )


def _preflight(root: Path, checks: list[str] | None, intelligence: Intelligence) -> list[ReviewGroup]:
    """Everything that can be known before a reviewer runs, so a bad call costs no tokens."""
    # The descriptor has to be at the root itself: walking up would review a neighbouring tool by
    # accident when this runs from a workspace holding several of them.
    if not (root / DESCRIPTOR).is_file():
        raise SmartToolCreatorError(
            f"No smart tool at {root}: {DESCRIPTOR} is not there. "
            f"Run 'smart-tool-creator init <name> --description \"...\" --directory {root}' first, "
            "then call check-spec-adherence again."
        )
    groups = select(checks)
    if shutil.which("uv") is None:
        raise SmartToolCreatorError("'uv' is not on PATH. Install it from https://docs.astral.sh/uv/ and try again.")
    intelligence.preflight()
    return groups


def _kit_failed(root: Path, conformance: ConformanceReport) -> SpecAdherenceReport:
    """The kit's verdict, and nothing else: judgment is not spent on a tool the mechanical rules reject."""
    counts = _counts([])
    output_message = _render(
        OUTPUT_MESSAGE_PATH,
        root=str(root),
        kit_failed=True,
        conformance_message=conformance.output_message,
        findings=[],
        deviations=[],
        counts=counts,
    ).rstrip()
    return SpecAdherenceReport(
        root=root,
        conformance=conformance,
        findings=[],
        counts=counts,
        deviating=[],
        output_message=output_message,
    )


def _review(
    intelligence: Intelligence,
    group: ReviewGroup,
    root: Path,
    model: str,
    reasoning_effort: ReasoningEffort,
) -> list[Finding]:
    """One reviewer, read-only in the tool's root, answering every check of one group."""
    prompt = _render(
        REVIEW_PROMPT_PATH,
        root=str(root),
        group=group.name,
        read_first=group.read_first,
        group_guidance=group.guidance,
        checks=[check.model_dump() for check in group.checks],
    )
    result = intelligence.run(
        AgentRequest(
            prompt=prompt,
            model=model,
            workspace=HostWorkspace(path=root),
            writable=False,
            output_schema=_output_schema(group),
            reasoning_effort=reasoning_effort,
            timeout_seconds=REVIEW_TIMEOUT_SECONDS,
        )
    )
    if result.error is not None:
        raise SmartToolCreatorError(
            f"The reviewer of the '{group.name}' checks in {root} failed: {result.error} "
            "Nothing was written to the tool; run check-spec-adherence again."
        )
    return _findings(group, _submission(group, result.output))


def _submission(group: ReviewGroup, output: dict[str, Any] | None) -> Submission:
    """The reviewer's answer, held to the shape it was asked for."""
    try:
        submission = Submission.model_validate(output)
    except ValidationError as error:
        raise SmartToolCreatorError(
            f"The reviewer of the '{group.name}' checks did not answer in the shape it was asked for: {error}. "
            "Nothing was written to the tool; run check-spec-adherence again."
        ) from None
    known = {check.id for check in group.checks}
    unknown = [finding.id for finding in submission.findings if finding.id not in known]
    if unknown:
        raise SmartToolCreatorError(
            f"The reviewer of the '{group.name}' checks answered about checks it was not given: "
            f"{', '.join(unknown)}. The group's checks are: {', '.join(sorted(known))}. "
            "Nothing was written to the tool; run check-spec-adherence again."
        )
    return submission


def _findings(group: ReviewGroup, submission: Submission) -> list[Finding]:
    """One finding per check of the group; the spec sentence comes from the checklist, never from the model."""
    answers = {finding.id: finding for finding in submission.findings}
    findings = []
    for check in group.checks:
        answer = answers.get(check.id)
        if answer is None:
            findings.append(
                Finding(id=check.id, status="unclear", spec=check.spec, evidence=[UNANSWERED], suggestion="")
            )
            continue
        findings.append(
            Finding(
                id=check.id,
                status=answer.status,
                spec=check.spec,
                evidence=answer.evidence,
                suggestion=answer.suggestion,
            )
        )
    return findings


def _counts(findings: list[Finding]) -> dict[str, int]:
    """How many findings carry each status, every status present even at zero."""
    return {status: sum(1 for finding in findings if finding.status == status) for status in STATUSES}


def _ordered(findings: list[Finding]) -> list[Finding]:
    """The checklist's order, so which reviewer finished first never shows in the report."""
    order = list(checks_by_id())
    return sorted(findings, key=lambda finding: order.index(finding.id))


def _summarized(finding: Finding) -> dict[str, Any]:
    """A finding with the one line that stands for it in the report's first section."""
    summary = finding.evidence[0] if finding.evidence else finding.suggestion
    return {**finding.model_dump(), "summary": summary}


def _output_schema(group: ReviewGroup) -> dict[str, Any]:
    """The shape a reviewer answers in: one finding per check, and only about the checks it was given."""
    return {
        "type": "object",
        "properties": {
            "findings": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "enum": [check.id for check in group.checks]},
                        "status": {"type": "string", "enum": list(STATUSES)},
                        "evidence": {"type": "array", "items": {"type": "string"}},
                        "suggestion": {"type": "string"},
                    },
                    "required": ["id", "status", "evidence", "suggestion"],
                    "additionalProperties": False,
                },
            }
        },
        "required": ["findings"],
        "additionalProperties": False,
    }


def _render(template: Path, **variables: object) -> str:
    return ENVIRONMENT.render(template.read_text(encoding="utf-8"), **variables)
