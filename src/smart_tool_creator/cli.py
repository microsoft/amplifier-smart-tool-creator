"""Command line entry point for the Smart Tool Creator."""

from collections.abc import Callable
from pathlib import Path
from typing import Annotated, Any

import typer

# Typer 0.27 vendors Click, so a command that overrides Click's own hooks has to speak the vendored types.
from typer._click import Context, Parameter
from typer.core import TyperCommand, TyperOption
from typer.models import CommandFunctionType

from smart_tool_creator import lib
from smart_tool_creator.core.skill import DISTRIBUTION
from smart_tool_creator.schemas import (
    DEFAULT_INTELLIGENCE_MODELS,
    DEFAULT_INTELLIGENCE_REASONING_EFFORT,
    DEFAULT_PROBE_TIMEOUT_SECONDS,
    DEFAULT_REVIEW_MODELS,
    DEFAULT_REVIEW_REASONING_EFFORT,
    AgentProvider,
    IntelligenceLayer,
    Language,
    ReasoningEffort,
    SmartToolCreatorError,
)

AGENT_PROVIDER_HELP = (
    "What the model-backed work runs through: copilot (GitHub Copilot, signed in as the GitHub CLI's user), "
    "amplifier-agent (Amplifier Agent, with the model provider's credentials), codex (OpenAI Codex, with the "
    "Codex sign-in), or claude (Claude Agent SDK). The first installed, in that order, when omitted."
)
REASONING_EFFORT_NOTE = "Applies to the copilot, codex, and claude agent providers."


def _model_help(defaults: dict[AgentProvider, str]) -> str:
    named = "; ".join(f"{agent_provider}: {model}" for agent_provider, model in defaults.items())
    return (
        "A Copilot model id for copilot, <provider>/<model> for amplifier-agent, a Codex model id for codex, a "
        f"Claude model id for claude. Defaults to {named}."
    )


class CapabilityCommand(TyperCommand):
    """Every capability answers `-h` with the generated summary and `--help` with its skill from the library."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs["add_help_option"] = False
        super().__init__(*args, **kwargs)

    def get_params(self, ctx: Context) -> list[Parameter]:
        def short(ctx: Context, param: Parameter, value: bool) -> None:
            if value and not ctx.resilient_parsing:
                typer.echo(ctx.get_help())
                ctx.exit()

        def capability_skill(ctx: Context, param: Parameter, value: bool) -> None:
            if value and not ctx.resilient_parsing:
                typer.echo(lib.skill(self.name))
                ctx.exit()

        return [
            *super().get_params(ctx),
            TyperOption(
                param_decls=["-h"],
                is_flag=True,
                is_eager=True,
                expose_value=False,
                callback=short,
                help="Terse summary of this capability.",
            ),
            TyperOption(
                param_decls=["--help"],
                is_flag=True,
                is_eager=True,
                expose_value=False,
                callback=capability_skill,
                help="This capability's skill, for an agent about to call it.",
            ),
        ]


class SmartToolTyper(typer.Typer):
    """A Typer whose commands are CapabilityCommand by default, so a capability added later inherits the help split."""

    def command(
        self, *args: Any, cls: type[TyperCommand] = CapabilityCommand, **kwargs: Any
    ) -> Callable[[CommandFunctionType], CommandFunctionType]:
        return super().command(*args, cls=cls, **kwargs)


app = SmartToolTyper(
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
    # `-h` is the terse summary and `--help` is the skill, at both scopes. On the root, the callback's parameter
    # claims `--help` and Click drops a help option name a parameter already took, which leaves the generated
    # summary on `-h`; on a capability, CapabilityCommand splits the two itself.
    context_settings={"help_option_names": ["-h", "--help"]},
)


def _print_skill(value: bool) -> None:
    """Answer the root `--help` with the skill the library composes, leaving `-h` to Typer."""
    if value:
        typer.echo(lib.skill())
        raise typer.Exit()


def _print_version(value: bool) -> None:
    if value:
        typer.echo(f"{DISTRIBUTION} {lib.version()}")
        raise typer.Exit()


@app.callback()
def cli(
    version: Annotated[
        bool,
        typer.Option("--version", "-V", is_eager=True, callback=_print_version, help="Print the version and exit."),
    ] = False,
    help: Annotated[
        bool,
        typer.Option(
            "--help", is_eager=True, callback=_print_skill, help="This tool's skill, for an agent driving it."
        ),
    ] = False,
) -> None:
    """Create, validate, and evaluate smart tools."""


@app.command()
def manifest() -> None:
    """Print the tool's manifest as JSON. Deterministic."""
    typer.echo(lib.load_manifest().model_dump_json(indent=2))


@app.command()
def init(
    name: Annotated[str, typer.Argument(help="The tool's slug: lowercase alphanumeric and hyphens.")],
    description: Annotated[str, typer.Option("--description", help="What the tool is for and when to reach for it.")],
    directory: Annotated[
        Path | None,
        typer.Option("--directory", help="Where to create it; the name under the current directory when omitted."),
    ] = None,
    language: Annotated[Language, typer.Option("--language", help="The language the tool is written in.")] = (
        "uv-python"
    ),
    intelligence: Annotated[
        IntelligenceLayer, typer.Option("--intelligence", help="The SDK its model-backed capabilities run through.")
    ] = "copilot-sdk",
    skill: Annotated[
        bool, typer.Option("--skill", help="Also ship an Agent Skill that teaches an agent to drive the tool.")
    ] = False,
    repository: Annotated[
        str | None,
        typer.Option(
            "--repository",
            help="The https:// URL the tool will be cloned from. Declared in pyproject.toml, used by every install "
            "instruction, and added as the origin remote; nothing is pushed.",
        ),
    ] = None,
) -> None:
    """Scaffold a new smart tool: a git repository holding a spec-conforming tool that passes the conformance kit. Deterministic."""
    scaffold = lib.init(
        name,
        description,
        directory=directory,
        language=language,
        intelligence=intelligence,
        skill=skill,
        repository=repository,
    )
    typer.echo(scaffold.output_message)


@app.command()
def check_conformance(
    directory: Annotated[
        Path | None,
        typer.Option("--directory", help="The smart tool's distribution root; the current directory when omitted."),
    ] = None,
    timeout: Annotated[
        float, typer.Option("--timeout", help="Seconds allowed for each invocation the kit makes of the tool.")
    ] = DEFAULT_PROBE_TIMEOUT_SECONDS,
) -> None:
    """Run the spec's conformance kit against a smart tool and print its verdict, rule by rule. Deterministic."""
    report = lib.check_conformance(directory=directory, timeout=timeout)
    typer.echo(report.output_message)
    if report.verdict == "FAIL":
        raise typer.Exit(1)


@app.command()
def check_spec_adherence(
    directory: Annotated[
        Path | None,
        typer.Option("--directory", help="The smart tool's distribution root; the current directory when omitted."),
    ] = None,
    check: Annotated[
        list[str] | None,
        typer.Option("--check", help="Repeatable; a check id to review, from the checklist; every check when omitted."),
    ] = None,
    agent_provider: Annotated[
        AgentProvider | None,
        typer.Option("--agent-provider", help=AGENT_PROVIDER_HELP),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option("--model", help=f"The model the reviewers run on. {_model_help(DEFAULT_REVIEW_MODELS)}"),
    ] = None,
    reasoning_effort: Annotated[
        ReasoningEffort,
        typer.Option(
            "--reasoning-effort", help=f"How hard the model thinks before it answers. {REASONING_EFFORT_NOTE}"
        ),
    ] = DEFAULT_REVIEW_REASONING_EFFORT,
) -> None:
    """Review a smart tool against the parts of the spec the conformance kit cannot decide, and suggest fixes. Model-backed: runs through GitHub Copilot, Amplifier Agent, Codex, or Claude, whichever --agent-provider names."""
    report = lib.check_spec_adherence(
        directory=directory,
        checks=check,
        agent_provider=agent_provider,
        model=model,
        reasoning_effort=reasoning_effort,
    )
    typer.echo(report.output_message)
    if report.conformance.verdict == "FAIL" or report.deviating:
        raise typer.Exit(1)


@app.command()
def add_smart_capability(
    request: Annotated[
        str, typer.Argument(help="What the capability does, for whom, and what it takes in and gives back.")
    ],
    directory: Annotated[
        Path | None, typer.Option("--directory", help="The smart tool to work in; the current directory when omitted.")
    ] = None,
    context: Annotated[
        list[str] | None,
        typer.Option("--context", help="Repeatable; text, or paths the agent should read before it designs anything."),
    ] = None,
    agent_provider: Annotated[
        AgentProvider | None,
        typer.Option("--agent-provider", help=AGENT_PROVIDER_HELP),
    ] = None,
    model: Annotated[
        str | None,
        typer.Option("--model", help=f"The model the agent runs on. {_model_help(DEFAULT_INTELLIGENCE_MODELS)}"),
    ] = None,
    reasoning_effort: Annotated[
        ReasoningEffort,
        typer.Option("--reasoning-effort", help=f"How hard the model thinks before it acts. {REASONING_EFFORT_NOTE}"),
    ] = DEFAULT_INTELLIGENCE_REASONING_EFFORT,
) -> None:
    """Add one model-backed capability to an existing smart tool: library, CLI, tests, and docs, verified against the tool's own checks. Model-backed: runs through GitHub Copilot, Amplifier Agent, Codex, or Claude, whichever --agent-provider names."""
    added = lib.add_smart_capability(
        request,
        directory=directory,
        context=context,
        agent_provider=agent_provider,
        model=model,
        reasoning_effort=reasoning_effort,
    )
    typer.echo(added.output_message)
    if any(check.status == "failed" for check in added.checks):
        raise typer.Exit(1)


def main() -> int:
    try:
        app()
    except SmartToolCreatorError as error:
        typer.echo(error, err=True)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
