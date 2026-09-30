from pathlib import Path
from typing import Literal, NamedTuple

from pydantic import BaseModel, Field

ReasoningEffort = Literal["low", "medium", "high", "xhigh", "max"]
AgentProvider = Literal["copilot", "amplifier-agent"]
# Also the order an agent provider is picked in when none is named.
AGENT_PROVIDERS: tuple[AgentProvider, ...] = ("copilot", "amplifier-agent")

DEFAULT_INTELLIGENCE_MODEL = "gpt-6-astra"
DEFAULT_INTELLIGENCE_MODELS: dict[AgentProvider, str] = {
    "copilot": DEFAULT_INTELLIGENCE_MODEL,
    "amplifier-agent": "openai/gpt-6-astra",
}
DEFAULT_INTELLIGENCE_REASONING_EFFORT: ReasoningEffort = "high"
DEFAULT_REVIEW_MODELS: dict[AgentProvider, str] = {
    "copilot": "gpt-6.1-sol",
    "amplifier-agent": "openai/gpt-6.1-sol",
}
DEFAULT_REVIEW_REASONING_EFFORT: ReasoningEffort = "medium"
DEFAULT_PROBE_TIMEOUT_SECONDS = 20.0

SEMVER_PATTERN = r"^\d+\.\d+\.\d+$"
SLUG_PATTERN = r"^[a-z0-9]+(-[a-z0-9]+)*$"


class SmartToolCreatorError(Exception):
    """Raised for any failure the library can name and explain how to fix."""


# region: Manifest


class ManifestRequirement(BaseModel):
    """One environment prerequisite; `install` references documentation, never a command."""

    name: str
    purpose: str
    install: str
    optional: bool = False


class Manifest(BaseModel):
    """The structured form of SMART_TOOL.md: the frontmatter as fields, the Markdown below it as text."""

    smart_tool_format: int
    name: str = Field(pattern=SLUG_PATTERN)
    version: str = Field(pattern=SEMVER_PATTERN)
    description: str
    use_cases: list[str]
    platforms: list[str]
    requires: list[ManifestRequirement] = Field(default_factory=list)
    body: str = Field(description="The Markdown below the frontmatter: the skill `--help` renders")


# endregion

# region: Skill


class Capability(NamedTuple):
    """One capability of the tool: its line in the skill's capability list and its own skill."""

    name: str
    summary: str
    model_backed: bool
    skill: str  # the capability's skill body, a Markdown file relative to the skill directory
    resources: tuple[str, ...] = ()  # the files that skill refers to, relative to the skill directory


# endregion

# region: Init

Language = Literal["uv-python"]
IntelligenceLayer = Literal["copilot-sdk"]


class Scaffold(BaseModel):
    """What init produced."""

    root: Path = Field(description="The new tool's distribution root")
    files: list[Path] = Field(description="Every file written, relative to the root")
    references: list[str] = Field(description="The repositories cloned into reference/")
    output_message: str = Field(
        description="What was created and what to do next in the new tool, for the calling agent"
    )


# endregion

# region: Check conformance

ConformanceStatus = Literal["PASS", "FAIL", "SKIP"]
ConformanceVerdict = Literal["PASS", "FAIL"]


class ConformanceRule(BaseModel):
    """One rule of the conformance kit, as the kit reported it."""

    id: str
    status: ConformanceStatus
    spec: str = Field(description="The spec sentence the rule operationalizes")
    detail: str = Field(description="What the kit saw: the reason it passed, failed, or could not be evaluated")


class ConformanceReport(BaseModel):
    """What check_conformance produced: the kit's verdict, rule by rule, untouched."""

    root: Path = Field(description="The distribution root the kit inspected")
    verdict: ConformanceVerdict = Field(description="FAIL when any rule failed; a skipped rule never fails a tool")
    counts: dict[str, int] = Field(description="How many rules passed, failed, and were skipped")
    failed_rules: list[str] = Field(description="The ids of the rules that failed")
    rules: list[ConformanceRule]
    output_message: str = Field(
        description="Every rule with its status and detail, then the verdict, for the calling agent"
    )


# endregion

# region: Check spec adherence

FindingStatus = Literal["adheres", "deviates", "not-applicable", "unclear"]


class SpecCheck(BaseModel):
    """One check of the checklist: a sentence of the spec and the guidance a reviewer judges it by."""

    id: str
    spec_file: str = Field(description="The spec chapter the sentence comes from")
    spec: str = Field(description="The spec sentence the check operationalizes, quoted verbatim")
    guidance: str = Field(description="The Markdown the reviewer reads for this check")


class ReviewGroup(BaseModel):
    """Checks whose evidence lives in the same files, so one reviewer answers them all in one pass."""

    name: str
    read_first: list[str] = Field(description="Where the group's evidence sits in a scaffolded tool")
    guidance: str = Field(default="", description="Context the group's reviewer reads before its checks")
    checks: list[SpecCheck]


class Finding(BaseModel):
    """One reviewer's answer to one check."""

    id: str
    status: FindingStatus = Field(
        description="Whether the tool adheres, deviates, the check does not apply, or the evidence does not settle it"
    )
    spec: str = Field(description="The spec sentence the check operationalizes, taken from the checklist")
    evidence: list[str] = Field(description="path:line references with a sentence each")
    suggestion: str = Field(description="What to change, empty when the tool adheres")


class SpecAdherenceReport(BaseModel):
    """What check_spec_adherence produced: the kit's verdict, then a finding per check."""

    root: Path = Field(description="The reviewed tool's distribution root")
    conformance: ConformanceReport = Field(description="The conformance kit's verdict, which runs first")
    findings: list[Finding] = Field(description="One per check, in the checklist's order; empty when the kit failed")
    counts: dict[str, int] = Field(description="How many findings carry each status")
    deviating: list[str] = Field(description="The ids of the checks the tool deviates from")
    output_message: str = Field(
        description="Every finding, then each deviation with its spec sentence and suggestion, for the calling agent"
    )


# endregion

# region: Add smart capability


class Check(BaseModel):
    """One of the extended tool's own checks, as it stood after the agent finished."""

    name: str
    command: list[str]
    status: Literal["passed", "failed", "skipped"]
    output: str = Field(
        description="The tail of the combined output when it failed, the reason when it was skipped, empty when it passed"
    )


class AddedCapability(BaseModel):
    """What add_smart_capability produced."""

    root: Path = Field(description="The extended tool's distribution root")
    report: str = Field(description="The agent's final message: what it added, how to try it, caveats")
    checks: list[Check] = Field(description="The tool's own checks, run after the work finished")
    fix_rounds: int = Field(description="Extra agent runs spent on failing checks")
    output_message: str = Field(
        description="The report, the checks, what to do next, and any check still failing, for the calling agent"
    )


# endregion
