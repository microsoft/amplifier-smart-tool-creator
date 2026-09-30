`init` creates a git repository (no remote) holding a tool that already passes the
conformance kit: manifest, descriptor, library, thin CLI, docs, tests, an `AGENTS.md`
carrying the spec's principles, and a gitignored `reference/` with shallow clones of the
spec and the SDK to read while developing. The environment is synced and the first commit is
made.

```bash
smart-tool-creator init incident-postmortem --description "Writes, reviews, and tracks blameless postmortems from your incident platform's records" --skill --repository https://github.com/org/incident-postmortem
```

```python
from smart_tool_creator.lib import init

scaffold = init(
    "incident-postmortem",
    "Writes, reviews, and tracks blameless postmortems from your incident platform's records",
    skill=True,
    repository="https://github.com/org/incident-postmortem",
)
scaffold.root, scaffold.files, scaffold.references, scaffold.output_message
```

## Arguments

- `NAME`: the tool's slug, lowercase alphanumeric and hyphens. It becomes the manifest name,
  the CLI command, and the package name. Required.
- `--description TEXT`: what the tool is for and when to reach for it, in one sentence; it
  becomes the manifest description. Required.
- `--directory PATH`: where to create it; the name under the current directory when omitted.
  It must not exist, or must be empty.
- `--language`: the language the tool is written in. `uv-python`, the default, is the only
  one.
- `--intelligence`: the SDK its model-backed capabilities run through. `copilot-sdk`, the
  default, is the only one.
- `--skill`: also ship an Agent Skill at `skills/<name>/SKILL.md` that teaches an agent to
  drive the tool. Off by default.
- `--repository URL`: the `https://` URL the tool will be cloned from. It is declared in
  `pyproject.toml`, every install instruction is built on it, and it becomes the `origin`
  remote; nothing is pushed. Without it, `https://github.com/<owner>/<name>` stands in, there
  is no remote, and the install instructions do not work until the placeholder is replaced
  and the tool is pushed.

## Result

`Scaffold` carries `root`, the new tool's distribution root; `files`, every file written,
relative to that root; `references`, the repositories cloned into `reference/`; and
`output_message`, what was created and what to do next in the new tool. The CLI prints
`output_message`.

Afterwards, work inside the new repository, following the next steps in that message: read
its `AGENTS.md`, fill in `docs/00-vision.md` and, if the surface is already clear,
`docs/01-library.md`, then add domain capabilities to its library and run the conformance kit
as its `CONTRIBUTING.md` describes. The docs come first because they set the stage for
everything implemented; keep them concise and written for people. Pushing is the user's call,
as is creating the remote and replacing the placeholder when `--repository` was not given.

## Failures

Deterministic, but it needs the network for `uv sync` and the reference clones.

A failure prints its message to stderr and exits 1: the name is not a slug, the description
is empty, `--repository` is not an `https://` URL, the target directory is a file or is not
empty, `git` or `uv` is not on `PATH`, git has no `user.name` or `user.email` for the first
commit, or a reference cannot be cloned. A bad invocation exits 2. Everything knowable is
checked before a file is written, so a failure caught there leaves no half-built tool.
