# Smart Tool Creator Development

## Development Setup

### Prerequisites

Install:

- [Git](https://git-scm.com/)
- [uv](https://docs.astral.sh/uv/getting-started/installation/) 0.9.17 or newer: Manages Python environments. Older versions cannot read the project's relative `exclude-newer` setting.
- [prek](https://github.com/j178/prek): Used for precommit hooks. Recommended to install through PyPI/uv with `uv tool install prek`. Use `uv tool upgrade prek` to update it.
- [GitHub CLI](https://cli.github.com/) for intelligence features with GitHub Copilot.
- [GitHub Copilot subscription](https://github.com/github/copilot-cli#prerequisites) for intelligent features through the `copilot` agent provider.
- [Model provider credentials](https://github.com/microsoft/amplifier-agent/blob/main/docs/providers.md), such as `OPENAI_API_KEY`, for intelligent features through the `amplifier-agent` agent provider.
- [Codex CLI](https://github.com/openai/codex) [signed in](https://developers.openai.com/codex/auth) with ChatGPT or an API key, for intelligent features through the `codex` agent provider.
- [`ANTHROPIC_API_KEY` or a cloud provider's credentials](https://code.claude.com/docs/en/agent-sdk/quickstart), for intelligent features through the `claude` agent provider.

### Initial Setup

1. Clone the repository:

   ```bash
   git clone https://github.com/microsoft/amplifier-smart-tool-creator.git
   cd amplifier-smart-tool-creator
   ```

1. Run the development installation script (sets up uv env and precommit hooks):

   ```bash
   uv run setup-for-dev.py
   ```

### Essential Development Commands

*Commands should be run from the repository root, unless otherwise specified.*

#### Precommit hooks

Setup precommit hooks:

```bash
prek install
```

Run precommit hooks manually:

```bash
prek run --all-files
```

#### Python Library Development

Create uv virtual environment and install dependencies:

```bash
uv sync --frozen --all-extras --all-groups
```

To update dependencies and the lock file:

```bash
uv sync -U --all-extras --all-groups
```

Lint code:

```bash
uv run ruff check --fix --config pyproject.toml
```

Format code (also formats code blocks in .md files):

```bash
uv run ruff format --config pyproject.toml
```

Type check:

```bash
uv run ty check .
```

Run tests:

```bash
uv run pytest
```

Run the deterministic capabilities on an install without any agent provider, then restore the full environment:

```bash
uv sync --no-dev
uv run --no-sync smart-tool-creator manifest
uv run --no-dev --with pytest --with pytest-asyncio pytest
uv sync --all-extras --all-groups
```

#### Conformance

Run the spec's [conformance kit](https://github.com/microsoft/amplifier-smart-tools/tree/main/conformance) against this repository through the tool's own capability, which fetches the kit and wraps it so this project's `smart-tool-creator` is on `PATH` for it to invoke:

```bash
uv run smart-tool-creator check-conformance
```

`uv run pytest` runs the same check, so a passing test suite includes conformance.
