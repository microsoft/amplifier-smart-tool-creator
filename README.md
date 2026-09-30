# Smart Tool Creator

[Explore the website](https://microsoft.github.io/amplifier-smart-tool-creator/)

Smart Tool Creator is the [Smart Tool](https://github.com/microsoft/amplifier-smart-tools) for building smart tools.
It scaffolds the structure the spec requires, checks a tool against the spec and its conformance kit, and evaluates a tool's model-backed capabilities in isolation.
The intelligence inside runs through an agent provider, the [GitHub Copilot SDK](https://github.com/github/copilot-sdk) or [Amplifier Agent](https://github.com/microsoft/amplifier-agent), behind an interface that other agent SDKs can implement.

## Installation

Prerequisites:
- Requires [uv](https://docs.astral.sh/uv/getting-started/installation/) 0.9.17 or newer.
- For the intelligent features, one of:
  - `copilot` agent provider: [GitHub CLI](https://cli.github.com/) signed in to an account with a [GitHub Copilot subscription](https://github.com/github/copilot-cli#prerequisites).
  - `amplifier-agent` agent provider: the model provider's credentials, for instance `OPENAI_API_KEY` for the default `openai/...` models. See [providers](https://github.com/microsoft/amplifier-agent/blob/v1/docs/providers.md).

```bash
uv tool install "amplifier-smart-tool-creator[all] @ git+https://github.com/microsoft/amplifier-smart-tool-creator"
```

To use it as a library:

```bash
uv add "amplifier-smart-tool-creator[all] @ git+https://github.com/microsoft/amplifier-smart-tool-creator"
```

To run it once without installing:

```bash
uvx --from "amplifier-smart-tool-creator[all] @ git+https://github.com/microsoft/amplifier-smart-tool-creator" smart-tool-creator --help
```

`[all]` brings both agent providers. Alternatives:

```bash
# Only the GitHub Copilot agent provider
uv tool install "amplifier-smart-tool-creator[copilot] @ git+https://github.com/microsoft/amplifier-smart-tool-creator"
# Only the Amplifier Agent agent provider
uv tool install "amplifier-smart-tool-creator[amplifier-agent] @ git+https://github.com/microsoft/amplifier-smart-tool-creator"
# Deterministic capabilities only
uv tool install git+https://github.com/microsoft/amplifier-smart-tool-creator
```

To teach a coding agent how to use it, install the [skill](skills/smart-tool-creator/SKILL.md):

```bash
npx skills add microsoft/amplifier-smart-tool-creator
```

To update:

```bash
uv tool upgrade amplifier-smart-tool-creator
npx skills update smart-tool-creator   # add --global if the skill was installed globally
```

To uninstall:

```bash
uv tool uninstall amplifier-smart-tool-creator
npx skills remove smart-tool-creator   # add --global if the skill was installed globally
```

## Interface

```bash
# Print the tool's manifest as JSON
smart-tool-creator manifest

# Scaffold a new smart tool into ./incident-postmortem, optionally with an Agent Skill and the repository it will be pushed to. Specify a specific directory with --directory
smart-tool-creator init incident-postmortem --description "Writes, reviews, and tracks blameless postmortems from your incident platform's records" --skill --repository https://github.com/org/incident-postmortem

# Run the conformance kit against a smart tool
smart-tool-creator check-conformance --directory ./incident-postmortem

# Review a smart tool against the parts of the spec the kit cannot decide, and get suggestions
smart-tool-creator check-spec-adherence --directory ./incident-postmortem

# The same review through Amplifier Agent on another model
smart-tool-creator check-spec-adherence --directory ./incident-postmortem --agent-provider amplifier-agent --model anthropic/claude-opus-5

# Add one model-backed capability to an existing smart tool, verified against that tool's own checks
smart-tool-creator add-smart-capability "Given an incident id, fetch its chat transcript and alert timeline from the incident platform and draft a blameless postmortem: summary, impact, contributing factors, and action items with owners" --directory ./incident-postmortem
```

See the [CLI reference](docs/02-cli.md) for every flag and the [library reference](docs/01-library.md) for the Python surface.

## Development

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) for details on how to set up your development environment.

## Contributing

> [!NOTE]
> This project is not currently accepting external contributions, but we're actively working toward opening this up. We value community input and look forward to collaborating in the future. For now, feel free to fork and experiment!

Most contributions require you to agree to a
Contributor License Agreement (CLA) declaring that you have the right to, and actually do, grant us
the rights to use your contribution. For details, visit [Contributor License Agreements](https://cla.opensource.microsoft.com).

When you submit a pull request, a CLA bot will automatically determine whether you need to provide
a CLA and decorate the PR appropriately (e.g., status check, comment). Simply follow the instructions
provided by the bot. You will only need to do this once across all repos using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/) or
contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.

## Trademarks

This project may contain trademarks or logos for projects, products, or services. Authorized use of Microsoft
trademarks or logos is subject to and must follow
[Microsoft's Trademark & Brand Guidelines](https://www.microsoft.com/legal/intellectualproperty/trademarks/usage/general).
Use of Microsoft trademarks or logos in modified versions of this project must not cause confusion or imply Microsoft sponsorship.
Any use of third-party trademarks or logos are subject to those third-party's policies.
