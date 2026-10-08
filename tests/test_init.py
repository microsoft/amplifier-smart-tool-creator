"""Scaffolds a tool for real, then holds it to what a published smart tool is held to."""

import json
import os
from pathlib import Path
import subprocess
from typing import Any

import pytest
from typer.testing import CliRunner

from smart_tool_creator.cli import app
from smart_tool_creator.lib import init
from smart_tool_creator.schemas import AGENT_PROVIDERS, AgentProvider, SmartToolCreatorError

NAME = "release-notes"
DESCRIPTION = "Summarizes changelogs into release notes"

SPEC_REQUIRED = [
    "smart-tool.json",
    "pyproject.toml",
    "src/release_notes/SMART_TOOL.md",
    "src/release_notes/lib.py",
    "src/release_notes/cli.py",
]
SHIPPED_ALONGSIDE = [
    "AGENTS.md",
    "CONTRIBUTING.md",
    "README.md",
    "docs/00-vision.md",
    "docs/01-library.md",
    "docs/02-cli.md",
    "setup-for-dev.py",
    "src/release_notes/capabilities/__init__.py",
    "src/release_notes/core/manifest.md",
    "src/release_notes/core/skill.py",
    "skills/release-notes/SKILL.md",
    "tests/test_manifest.py",
    "tests/test_skill.py",
]
INTELLIGENCE = [
    "src/release_notes/intelligence/__init__.py",
    "src/release_notes/intelligence/interface.py",
    "src/release_notes/intelligence/schemas.py",
    "src/release_notes/intelligence/submission.py",
    "tests/test_agent_provider.py",
]
MODULES: dict[AgentProvider, str] = {
    "copilot": "copilot",
    "amplifier-agent": "amplifier_agent",
    "codex": "codex",
    "claude": "claude",
}
REFERENCES: dict[AgentProvider, str] = {
    "copilot": "copilot-sdk",
    "amplifier-agent": "amplifier-agent",
    "codex": "codex",
    "claude": "claude-agent-sdk-python",
}
# Where a scaffold names its agent providers to a reader, so one it does not ship must not appear there.
PROSE = ["README.md", "CONTRIBUTING.md", "AGENTS.md", "docs/01-library.md", "src/release_notes/SMART_TOOL.md"]

runner = CliRunner()
CREATOR_TRACES = ["smart-tool-creator", "smart_tool_creator", "SmartToolCreator"]


def run(command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    environment = dict(os.environ)
    environment.pop("VIRTUAL_ENV", None)
    return subprocess.run(command, cwd=cwd, capture_output=True, text=True, env=environment)


def passes(command: list[str], cwd: Path) -> None:
    completed = run(command, cwd)
    assert completed.returncode == 0, f"{' '.join(command)}\n{completed.stdout}\n{completed.stderr}"


def provider_files(agent_provider: AgentProvider) -> list[str]:
    module = MODULES[agent_provider]
    return [f"src/release_notes/intelligence/{module}.py", f"tests/test_{module}.py"]


def assert_ships_only(root: Path, files: list[Path], references: list[str], shipped: list[AgentProvider]) -> None:
    """The scaffold carries the shipped agent providers, in canonical order, and no trace of the others."""
    for agent_provider in AGENT_PROVIDERS:
        for relative in provider_files(agent_provider):
            assert (Path(relative) in files) == (agent_provider in shipped), relative
    for relative in INTELLIGENCE:
        assert (Path(relative) in files) == bool(shipped), relative
    cloned = {url.rsplit("/", 1)[-1] for url in references} - {"amplifier-smart-tools", "agentskills"}
    assert cloned == {REFERENCES[agent_provider] for agent_provider in shipped}

    pyproject = (root / "pyproject.toml").read_text(encoding="utf-8")
    schemas = (root / "src/release_notes/schemas.py").read_text(encoding="utf-8")
    if shipped:
        assert f'"{NAME}[{",".join(shipped)}]"' in pyproject
        assert (
            f"AgentProvider = Literal[{', '.join(json.dumps(agent_provider) for agent_provider in shipped)}]" in schemas
        )
    else:
        assert not (root / "src/release_notes/intelligence").exists()
        assert "[project.optional-dependencies]" not in pyproject
        assert "jsonschema" not in pyproject
        assert "AgentProvider" not in schemas
        assert "DEFAULT_INTELLIGENCE_MODELS" not in schemas
    for agent_provider in AGENT_PROVIDERS:
        if agent_provider not in shipped:
            for relative in PROSE:
                assert f"`{agent_provider}`" not in (root / relative).read_text(encoding="utf-8"), relative


def test_init_produces_a_conforming_committed_tool(tmp_path: Path) -> None:
    root = tmp_path / NAME
    result = init(NAME, DESCRIPTION, directory=root, skill=True)

    assert result.root == root.resolve()
    for relative in SPEC_REQUIRED + SHIPPED_ALONGSIDE:
        assert Path(relative) in result.files, relative
        assert (root / relative).is_file(), relative
    assert_ships_only(root, result.files, result.references, list(AGENT_PROVIDERS))

    committed = run(["git", "ls-files"], root).stdout.split()
    assert sorted(committed) == sorted([*(str(file) for file in result.files), "uv.lock"])
    assert len(run(["git", "log", "--oneline"], root).stdout.strip().splitlines()) == 1
    assert run(["git", "remote"], root).stdout.strip() == ""
    assert run(["git", "status", "--porcelain"], root).stdout.strip() == ""

    placeholder = f"https://github.com/<owner>/{NAME}"
    for relative in ("README.md", "pyproject.toml", "src/release_notes/SMART_TOOL.md", f"skills/{NAME}/SKILL.md"):
        assert placeholder in (root / relative).read_text(encoding="utf-8"), relative
    assert f"placeholder {placeholder}" in result.output_message
    assert "git remote add origin <url>" in result.output_message

    for relative in committed:
        content = (root / relative).read_text(encoding="utf-8")
        assert not any(trace in content for trace in CREATOR_TRACES), relative

    assert sorted(path.name for path in (root / "reference").iterdir()) == sorted(
        url.rsplit("/", 1)[-1] for url in result.references
    )
    assert {"amplifier-smart-tools", "copilot-sdk", "amplifier-agent", "codex", "claude-agent-sdk-python"} <= {
        url.rsplit("/", 1)[-1] for url in result.references
    }

    assert f"Scaffolded {NAME} at {root}" in result.output_message
    assert f"{len(result.files)} files written" in result.output_message
    assert all(url in result.output_message for url in result.references)
    next_steps = result.output_message.split("Next:", 1)[1]
    assert (
        next_steps.index("docs/00-vision.md")
        < next_steps.index("docs/01-library.md")
        < next_steps.index("capabilities/")
    )

    invoked = run(["uv", "run", NAME, "manifest"], root)
    assert invoked.returncode == 0, invoked.stderr
    manifest = json.loads(invoked.stdout)
    assert (manifest["name"], manifest["version"], manifest["description"]) == (NAME, "0.1.0", DESCRIPTION)

    passes(["prek", "run", "--all-files"], root)
    passes(["uv", "run", "pytest"], root)

    kit = Path("reference") / "amplifier-smart-tools" / "conformance" / "run.py"
    conformance = run(["uv", "run", "--", "uv", "run", "--no-project", str(kit), ".", "--json-only"], root)
    verdict = json.loads(conformance.stdout)
    assert conformance.returncode == 0, conformance.stderr
    assert verdict["verdict"] == "PASS", verdict["failed_rules"]
    assert verdict["counts"]["skip"] == 0, verdict


def test_init_with_a_repository_points_every_install_at_it(tmp_path: Path) -> None:
    root = tmp_path / NAME
    repository = "https://github.com/example/release-notes"
    result = init(NAME, DESCRIPTION, directory=root, skill=True, repository=f"{repository}.git")

    assert run(["git", "remote", "get-url", "origin"], root).stdout.strip() == repository
    assert run(["git", "status", "--porcelain"], root).stdout.strip() == ""
    assert f"whose origin is {repository}" in result.output_message
    assert "git push -u origin main" in result.output_message

    readme = (root / "README.md").read_text(encoding="utf-8")
    assert f'uv tool install "{NAME}[all | copilot | amplifier-agent | codex | claude] @ git+{repository}"' in readme
    assert f'uv add "{NAME}[all] @ git+{repository}"' in readme
    assert "npx skills add example/release-notes" in readme
    assert f"uv tool upgrade {NAME}" in readme
    assert f"uv tool uninstall {NAME}" in readme

    for relative in ("src/release_notes/SMART_TOOL.md", f"skills/{NAME}/SKILL.md"):
        assert f'uv add "{NAME}[all] @ git+{repository}"' in (root / relative).read_text(encoding="utf-8"), relative
    assert "github.com/<owner>/" not in "".join(
        (root / relative).read_text(encoding="utf-8") for relative in result.files
    )
    assert f"repository: {repository}" in (root / f"skills/{NAME}/SKILL.md").read_text(encoding="utf-8")
    assert f'Repository = "{repository}"' in (root / "pyproject.toml").read_text(encoding="utf-8")

    invoked = run(["uv", "run", NAME, "--help"], root)
    assert invoked.returncode == 0, invoked.stderr
    assert f"Repository: {repository}" in invoked.stdout.splitlines()[2]

    capability_skill = run(["uv", "run", NAME, "manifest", "--help"], root)
    terse = run(["uv", "run", NAME, "manifest", "-h"], root)
    assert capability_skill.returncode == 0, capability_skill.stderr
    assert f'<skill_content name="{NAME} manifest">' in capability_skill.stdout
    assert terse.returncode == 0, terse.stderr
    assert "Usage:" in terse.stdout
    assert terse.stdout != capability_skill.stdout

    version = run(["uv", "run", NAME, "--version"], root)
    assert version.returncode == 0, version.stderr
    assert version.stdout == f"{NAME} 0.1.0\n"

    passes(["uv", "run", "pytest"], root)


def test_init_refuses_a_repository_that_is_not_https(tmp_path: Path) -> None:
    root = tmp_path / NAME

    with pytest.raises(SmartToolCreatorError, match="not a usable repository URL"):
        init(NAME, DESCRIPTION, directory=root, repository="git@github.com:example/release-notes.git")

    assert not root.exists()


@pytest.mark.parametrize(
    ("chosen", "shipped"),
    [(["codex"], ["codex"]), (["claude", "copilot"], ["copilot", "claude"])],
    ids=["one", "two-out-of-order"],
)
def test_init_with_a_subset_ships_only_those_agent_providers_in_canonical_order(
    tmp_path: Path, chosen: list[AgentProvider], shipped: list[AgentProvider]
) -> None:
    root = tmp_path / NAME
    result = init(NAME, DESCRIPTION, directory=root, agent_providers=chosen)

    assert_ships_only(root, result.files, result.references, shipped)
    assert run(["git", "status", "--porcelain"], root).stdout.strip() == ""
    passes(["prek", "run", "--all-files"], root)
    passes(["uv", "run", "pytest"], root)
    assert run(["git", "status", "--porcelain"], root).stdout.strip() == ""
    for agent_provider in shipped:
        passes(
            [
                "uv",
                "run",
                "python",
                "-c",
                (
                    "from release_notes.intelligence.interface import installed, resolve_intelligence; "
                    f"assert installed({agent_provider!r}); resolve_intelligence({agent_provider!r})"
                ),
            ],
            root,
        )


def test_init_with_no_agent_providers_ships_a_deterministic_tool(tmp_path: Path) -> None:
    root = tmp_path / NAME
    result = init(NAME, DESCRIPTION, directory=root, agent_providers=[])

    assert_ships_only(root, result.files, result.references, [])
    assert "with no agent provider" in result.output_message
    passes(["prek", "run", "--all-files"], root)
    passes(["uv", "run", "pytest"], root)
    assert run(["git", "status", "--porcelain"], root).stdout.strip() == ""

    kit = Path("reference") / "amplifier-smart-tools" / "conformance" / "run.py"
    conformance = run(["uv", "run", "--", "uv", "run", "--no-project", str(kit), ".", "--json-only"], root)
    verdict = json.loads(conformance.stdout)
    assert verdict["verdict"] == "PASS", verdict["failed_rules"]


@pytest.mark.parametrize(
    ("chosen", "problem"),
    [(["gemini"], "Not an agent provider: gemini"), (["codex", "copilot", "codex"], "Named more than once: codex")],
    ids=["unknown", "duplicate"],
)
def test_init_refuses_an_agent_provider_it_cannot_ship_before_writing_anything(
    tmp_path: Path, chosen: list[Any], problem: str
) -> None:
    root = tmp_path / NAME

    with pytest.raises(SmartToolCreatorError, match=problem):
        init(NAME, DESCRIPTION, directory=root, agent_providers=chosen)

    assert not root.exists()


@pytest.mark.parametrize(
    ("arguments", "passed"),
    [
        ([], None),
        (["--agent-provider", "claude", "--agent-provider", "codex"], ["claude", "codex"]),
        (["--no-agent-providers"], []),
    ],
    ids=["omitted", "repeated", "none"],
)
def test_the_cli_passes_the_agent_providers_through(
    monkeypatch: pytest.MonkeyPatch, arguments: list[str], passed: list[str] | None
) -> None:
    received: dict[str, object] = {}

    def fake(*positional: object, **keywords: object) -> object:
        received.update(keywords)
        raise SmartToolCreatorError("Stopped after the arguments were read.")

    monkeypatch.setattr("smart_tool_creator.lib.init", fake)

    result = runner.invoke(app, ["init", NAME, "--description", DESCRIPTION, *arguments])

    assert result.exit_code == 1
    assert received["agent_providers"] == passed


def test_the_cli_refuses_agent_providers_together_with_none() -> None:
    result = runner.invoke(
        app, ["init", NAME, "--description", DESCRIPTION, "--agent-provider", "codex", "--no-agent-providers"]
    )

    assert result.exit_code == 2


def test_the_cli_refuses_an_unknown_agent_provider() -> None:
    result = runner.invoke(app, ["init", NAME, "--description", DESCRIPTION, "--agent-provider", "gemini"])

    assert result.exit_code == 2
