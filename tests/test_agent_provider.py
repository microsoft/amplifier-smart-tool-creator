"""Picks the agent provider and the model with the installed SDKs faked, so it runs on a bare install."""

from importlib.machinery import ModuleSpec
from pathlib import Path

import pytest
from typer.testing import CliRunner

from smart_tool_creator.capabilities.check_spec_adherence import capability as adherence
from smart_tool_creator.cli import app
from smart_tool_creator.intelligence import interface
from smart_tool_creator.intelligence.interface import resolve_agent_provider, select_intelligence
from smart_tool_creator.intelligence.schemas import AgentRequest, AgentResult
from smart_tool_creator.lib import check_spec_adherence
from smart_tool_creator.schemas import (
    DEFAULT_REVIEW_MODELS,
    AgentProvider,
    ConformanceReport,
    SmartToolCreatorError,
    SpecAdherenceReport,
)

REPOSITORY = "git+https://github.com/microsoft/amplifier-smart-tool-creator"

runner = CliRunner()


class FakeIntelligence:
    """Answers every reviewer with no findings and records the model it was asked for."""

    def __init__(self) -> None:
        self.implementation = "fake"
        self.requests: list[AgentRequest] = []

    def preflight(self) -> None:
        pass

    def run(self, request: AgentRequest) -> AgentResult:
        self.requests.append(request)
        return AgentResult(output={"findings": []})


def only_installed(monkeypatch: pytest.MonkeyPatch, *agent_providers: AgentProvider) -> None:
    modules = {interface.SDK_MODULES[agent_provider] for agent_provider in agent_providers}

    def find_spec(name: str) -> ModuleSpec | None:
        return ModuleSpec(name, None) if name in modules else None

    monkeypatch.setattr(interface, "find_spec", find_spec)


@pytest.mark.parametrize(
    ("installed", "named", "picked"),
    [
        (("copilot", "amplifier-agent", "codex", "claude"), None, "copilot"),
        (("copilot",), None, "copilot"),
        (("amplifier-agent",), None, "amplifier-agent"),
        (("codex",), None, "codex"),
        (("amplifier-agent", "codex"), None, "amplifier-agent"),
        (("claude",), None, "claude"),
        (("codex", "claude"), None, "codex"),
        (("copilot", "amplifier-agent"), "amplifier-agent", "amplifier-agent"),
        (("copilot", "amplifier-agent", "codex"), "codex", "codex"),
        (("copilot", "amplifier-agent", "codex", "claude"), "claude", "claude"),
    ],
)
def test_a_named_agent_provider_wins_and_otherwise_the_first_installed_is_picked(
    monkeypatch: pytest.MonkeyPatch,
    installed: tuple[AgentProvider, ...],
    named: AgentProvider | None,
    picked: AgentProvider,
) -> None:
    only_installed(monkeypatch, *installed)

    assert resolve_agent_provider(named) == picked


@pytest.mark.parametrize(
    ("named", "extras"),
    [
        (None, ["all", "copilot", "amplifier-agent", "codex", "claude"]),
        ("copilot", ["copilot"]),
        ("amplifier-agent", ["amplifier-agent"]),
        ("codex", ["codex"]),
        ("claude", ["claude"]),
    ],
)
def test_a_missing_agent_provider_names_the_install_command(
    monkeypatch: pytest.MonkeyPatch, named: AgentProvider | None, extras: list[str]
) -> None:
    only_installed(monkeypatch)

    with pytest.raises(SmartToolCreatorError) as failure:
        resolve_agent_provider(named)

    message = str(failure.value)
    assert f'uv tool install "amplifier-smart-tool-creator[{extras[0]}] @ {REPOSITORY}"' in message
    for extra in extras:
        assert f"[{extra}]" in message


def test_an_injected_intelligence_wins_and_needs_no_agent_provider_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    only_installed(monkeypatch)
    fake = FakeIntelligence()

    assert select_intelligence(fake, None, None, DEFAULT_REVIEW_MODELS) == (fake, DEFAULT_REVIEW_MODELS["copilot"])
    assert select_intelligence(fake, "amplifier-agent", None, DEFAULT_REVIEW_MODELS) == (
        fake,
        DEFAULT_REVIEW_MODELS["amplifier-agent"],
    )
    assert select_intelligence(fake, None, "anthropic/claude-opus-5", DEFAULT_REVIEW_MODELS) == (
        fake,
        "anthropic/claude-opus-5",
    )


def test_the_library_asks_for_the_agent_providers_default_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    (tmp_path / "smart-tool.json").write_text('{"smart_tool_format": 1}', encoding="utf-8")
    passing = ConformanceReport(
        root=tmp_path,
        verdict="PASS",
        counts={"pass": 1, "fail": 0, "skip": 0},
        failed_rules=[],
        rules=[],
        output_message="",
    )
    monkeypatch.setattr(adherence, "check_conformance", lambda directory: passing)
    fake = FakeIntelligence()

    check_spec_adherence(
        directory=tmp_path, checks=["cli-is-thin"], agent_provider="amplifier-agent", intelligence=fake
    )

    assert [request.model for request in fake.requests] == [DEFAULT_REVIEW_MODELS["amplifier-agent"]]


def test_the_cli_passes_the_agent_provider_and_model_through(monkeypatch: pytest.MonkeyPatch) -> None:
    received: dict[str, object] = {}
    report = SpecAdherenceReport(
        root=Path("/tmp/tool"),
        conformance=ConformanceReport(
            root=Path("/tmp/tool"), verdict="PASS", counts={}, failed_rules=[], rules=[], output_message=""
        ),
        findings=[],
        counts={},
        deviating=[],
        output_message="done",
    )

    def fake(**keywords: object) -> SpecAdherenceReport:
        received.update(keywords)
        return report

    monkeypatch.setattr("smart_tool_creator.lib.check_spec_adherence", fake)

    result = runner.invoke(
        app, ["check-spec-adherence", "--agent-provider", "amplifier-agent", "--model", "anthropic/claude-opus-5"]
    )

    assert result.exit_code == 0
    assert received["agent_provider"] == "amplifier-agent"
    assert received["model"] == "anthropic/claude-opus-5"


@pytest.mark.parametrize("agent_provider", ["amplifier-agent", "claude"])
def test_state_lives_in_the_platform_state_directory_under_the_tool(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, agent_provider: AgentProvider
) -> None:
    monkeypatch.setattr(interface.sys, "platform", "linux")
    monkeypatch.setenv("XDG_STATE_HOME", str(tmp_path))

    assert interface.state_directory(agent_provider) == tmp_path / "smart-tool-creator" / agent_provider
