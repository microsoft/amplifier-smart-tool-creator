"""Top level entry point for the Smart Tool Creator library."""

from pathlib import Path

from smart_tool_creator.capabilities.add_smart_capability import capability
from smart_tool_creator.capabilities.check_conformance import capability as conformance
from smart_tool_creator.capabilities.check_spec_adherence import capability as adherence
from smart_tool_creator.capabilities.check_spec_adherence import checks as adherence_checks
from smart_tool_creator.capabilities.init import scaffold
from smart_tool_creator.core import manifest
from smart_tool_creator.core import skill as skill_module
from smart_tool_creator.intelligence.interface import Intelligence
from smart_tool_creator.schemas import (
    DEFAULT_INTELLIGENCE_REASONING_EFFORT,
    DEFAULT_PROBE_TIMEOUT_SECONDS,
    DEFAULT_REVIEW_REASONING_EFFORT,
    AddedCapability,
    AgentProvider,
    ConformanceReport,
    IntelligenceLayer,
    Language,
    Manifest,
    ReasoningEffort,
    ReviewGroup,
    Scaffold,
    SpecAdherenceReport,
)


def load_manifest() -> Manifest:
    """The tool's manifest as structured data, read from the SMART_TOOL.md shipped inside the package."""
    return manifest.load_manifest()


def skill(capability: str | None = None) -> str:
    """The tool's skill, or the named capability's own skill, wrapped so a reader knows where the tool's files are."""
    return skill_module.skill(capability)


def skill_directory() -> Path:
    """The installed package root, where the files the skill names can be read."""
    return skill_module.skill_directory()


def skill_resources() -> list[str]:
    """The files the skill lists, as paths relative to the skill directory. Every one ships inside the package."""
    return skill_module.skill_resources()


def capability_skill_resources(capability: str) -> list[str]:
    """The files that capability's skill lists, as paths relative to the skill directory."""
    return skill_module.capability_skill_resources(capability)


def version() -> str:
    """The installed package's version, from its metadata."""
    return skill_module.version()


def repository_url() -> str | None:
    """The tool's canonical source, from the package metadata, or None when the package declares none."""
    return skill_module.repository_url()


def init(
    name: str,
    description: str,
    directory: Path | None = None,
    language: Language = "uv-python",
    intelligence: IntelligenceLayer = "copilot-sdk",
    skill: bool = False,
    repository: str | None = None,
) -> Scaffold:
    """Scaffold a new smart tool: a git repository, synced, committed, and conforming to the spec.

    With `repository`, the URL it will be cloned from, the scaffold declares it in `pyproject.toml`, points every
    install instruction at it, and adds it as the `origin` remote; nothing is pushed.
    """
    return scaffold.init(
        name,
        description,
        directory=directory,
        language=language,
        intelligence=intelligence,
        skill=skill,
        repository=repository,
    )


def check_conformance(
    directory: Path | None = None, timeout: float = DEFAULT_PROBE_TIMEOUT_SECONDS
) -> ConformanceReport:
    """Run the spec's conformance kit against a smart tool and return its verdict, rule by rule.

    `timeout` bounds each invocation the kit makes of the tool, in seconds.
    """
    return conformance.check_conformance(directory=directory, timeout=timeout)


def check_spec_adherence(
    directory: Path | None = None,
    checks: list[str] | None = None,
    agent_provider: AgentProvider | None = None,
    model: str | None = None,
    reasoning_effort: ReasoningEffort = DEFAULT_REVIEW_REASONING_EFFORT,
    intelligence: Intelligence | None = None,
) -> SpecAdherenceReport:
    """Review a smart tool against the parts of the spec the conformance kit cannot decide, and suggest fixes.

    The kit runs first: when it fails, no reviewer runs and the report says to fix the failing rules.
    `checks` names the ids to review, from the checklist `spec_checks()` returns.
    `agent_provider` is the first installed one when omitted, and `model` that agent provider's default for a review.
    """
    return adherence.check_spec_adherence(
        directory=directory,
        checks=checks,
        agent_provider=agent_provider,
        model=model,
        reasoning_effort=reasoning_effort,
        intelligence=intelligence,
    )


def spec_checks() -> list[ReviewGroup]:
    """The checklist check_spec_adherence reviews against, group by group, without running anything."""
    return adherence_checks.review_groups()


def add_smart_capability(
    request: str,
    directory: Path | None = None,
    context: list[str] | None = None,
    agent_provider: AgentProvider | None = None,
    model: str | None = None,
    reasoning_effort: ReasoningEffort = DEFAULT_INTELLIGENCE_REASONING_EFFORT,
    intelligence: Intelligence | None = None,
) -> AddedCapability:
    """Add one model-backed capability to an existing smart tool, then hold it to that tool's own checks.

    `agent_provider` is the first installed one when omitted, and `model` that agent provider's default.
    """
    return capability.add_smart_capability(
        request,
        directory=directory,
        context=context,
        agent_provider=agent_provider,
        model=model,
        reasoning_effort=reasoning_effort,
        intelligence=intelligence,
    )
