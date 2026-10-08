from pathlib import Path
import tomllib

import pytest
import typer
from typer.testing import CliRunner

from smart_tool_creator.cli import app
from smart_tool_creator.core.skill import CAPABILITIES, ENVIRONMENT, SKILL_VARIABLES
from smart_tool_creator.lib import (
    capability_skill_resources,
    load_manifest,
    repository_url,
    skill,
    skill_directory,
    skill_resources,
    version,
)
from smart_tool_creator.schemas import DEFAULT_INTELLIGENCE_MODELS, DEFAULT_REVIEW_MODELS, SmartToolCreatorError

DISTRIBUTION_ROOT = Path(__file__).parents[1]
# The tool's skill routes to the capability skills, so it stays a router rather than a manual.
MAXIMUM_BODY_LINES = 120

runner = CliRunner()


def test_manifest_body_is_the_markdown_below_the_frontmatter() -> None:
    body = load_manifest().body

    assert body
    assert not body.startswith("#")


def test_skill_is_a_wrapped_document_naming_every_capability() -> None:
    document = skill()

    assert document.startswith('<skill_content name="smart-tool-creator">')
    assert document.endswith("</skill_content>")
    assert "# smart-tool-creator" in document
    assert load_manifest().body in document
    assert "Each has its own skill: `smart-tool-creator <capability> --help`." in document
    for capability in CAPABILITIES:
        kind = "model-backed" if capability.model_backed else "deterministic"
        assert f"- `{capability.name}` [{kind}] -- {capability.summary}" in document


def test_skill_routes_to_the_capability_skills_instead_of_carrying_them() -> None:
    body = load_manifest().body

    assert "## Scaffolding a new smart tool" not in body
    assert "## Adding a smart capability" not in body
    assert len(body.splitlines()) < MAXIMUM_BODY_LINES


def test_repository_line_names_the_url_the_package_declares() -> None:
    pyproject = tomllib.loads((DISTRIBUTION_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    declared = pyproject["project"]["urls"]["Repository"]
    header = skill().splitlines()

    assert repository_url() == declared
    assert header[1].startswith("Skill directory: ")
    assert header[2] == f"Repository: {declared}"
    assert header[3] == f"Version: {version()}"
    assert header[4] == "Relative paths in this skill are relative to the skill directory."


def test_version_line_names_the_manifest_version_in_every_skill() -> None:
    line = f"Version: {load_manifest().version}"

    assert skill().splitlines()[3] == line
    for capability in CAPABILITIES:
        assert skill(capability.name).splitlines()[3] == line


def test_skill_resources_resolve_under_the_skill_directory() -> None:
    root = skill_directory()
    resources = [line.removeprefix("<file>").removesuffix("</file>") for line in _resource_lines(skill())]

    assert resources
    assert resources == skill_resources()
    assert (root / "SMART_TOOL.md").is_file()
    for resource in resources:
        assert (root / resource).is_file()


def test_every_capability_ships_the_files_its_skill_names() -> None:
    root = skill_directory()

    for capability in CAPABILITIES:
        assert (root / capability.skill).is_file()
        assert capability_skill_resources(capability.name) == list(capability.resources)
        for resource in capability.resources:
            assert (root / resource).is_file()


def test_every_capability_skill_is_its_markdown_in_the_tool_s_shape() -> None:
    for capability in CAPABILITIES:
        document = skill(capability.name)
        template = (skill_directory() / capability.skill).read_text(encoding="utf-8")
        body = ENVIRONMENT.render(template, **SKILL_VARIABLES).strip()
        kind = "Model-backed." if capability.model_backed else "Deterministic."

        assert document.startswith(f'<skill_content name="smart-tool-creator {capability.name}">')
        assert f"# smart-tool-creator {capability.name}" in document
        assert kind in document
        assert body in document
        assert document.endswith("</skill_content>")
        if not capability.resources:
            assert "<skill_resources>" not in document


@pytest.mark.parametrize(
    ("name", "defaults"),
    [("add-smart-capability", DEFAULT_INTELLIGENCE_MODELS), ("check-spec-adherence", DEFAULT_REVIEW_MODELS)],
)
def test_a_capability_skill_renders_its_default_models_from_the_code(name: str, defaults: dict[str, str]) -> None:
    document = skill(name)

    for model in defaults.values():
        assert f"`{model}`" in document
    assert "{{" not in document
    assert "{%" not in document


def test_an_unknown_capability_names_the_ones_that_exist() -> None:
    with pytest.raises(SmartToolCreatorError) as failure:
        skill("nope")

    for capability in CAPABILITIES:
        assert capability.name in str(failure.value)


def _resource_lines(document: str) -> list[str]:
    lines = [line.strip() for line in document.splitlines()]
    start = lines.index("<skill_resources>")
    end = lines.index("</skill_resources>")
    return lines[start + 1 : end]


def test_help_prints_the_skill() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert result.stdout.strip() == skill()


def test_short_help_and_no_arguments_print_the_terse_summary() -> None:
    short = runner.invoke(app, ["-h"])
    bare = runner.invoke(app, [])

    assert short.exit_code == 0
    assert "<skill_content" not in short.stdout
    assert "manifest" in short.stdout
    assert "<skill_content" not in bare.stdout


def test_every_command_answers_help_with_its_own_skill() -> None:
    for capability in CAPABILITIES:
        result = runner.invoke(app, [capability.name, "--help"])

        assert result.exit_code == 0
        assert result.stdout.strip() == skill(capability.name)


def test_every_command_answers_short_help_with_the_terse_summary() -> None:
    for capability in CAPABILITIES:
        result = runner.invoke(app, [capability.name, "-h"])

        assert result.exit_code == 0
        assert "Usage:" in result.stdout
        assert "<skill_content" not in result.stdout


def test_the_cli_exposes_exactly_the_capabilities_the_skill_lists() -> None:
    commands = typer.main.get_group(app).commands

    assert set(commands) == {capability.name for capability in CAPABILITIES}


def test_every_capability_skill_documents_every_argument_the_cli_takes() -> None:
    commands = typer.main.get_group(app).commands

    for capability in CAPABILITIES:
        document = skill(capability.name)
        for parameter in commands[capability.name].get_params(typer.Context(commands[capability.name])):
            names = [name for name in parameter.opts if name.startswith("-")]
            if not names:
                assert parameter.name is not None
                assert parameter.name.upper() in document
                continue
            if set(names) <= {"-h", "--help"}:
                continue
            for name in names:
                assert name in document


@pytest.mark.parametrize("flag", ["--version", "-V"])
def test_version_prints_the_distribution_and_its_installed_version(flag: str) -> None:
    result = runner.invoke(app, [flag])

    assert result.exit_code == 0
    assert result.output == f"amplifier-smart-tool-creator {version()}\n"
