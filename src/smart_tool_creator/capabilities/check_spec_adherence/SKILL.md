`check-spec-adherence` reviews a smart tool against the parts of the
[spec](https://github.com/microsoft/amplifier-smart-tools) the conformance kit cannot
decide: whether the library really holds every capability, whether the skills say what an
agent needs, whether failures name their remedy. The kit runs first, through
`check-conformance`; when it fails, no reviewer runs and the report says to fix the failing
rules and call again. Otherwise one reviewer per group of checks runs concurrently, each
read-only in the tool's root, and answers every check of its group with one finding. Nothing
is written to the tool.

```bash
smart-tool-creator check-spec-adherence --directory ~/src/incident-postmortem

# through Amplifier Agent, on another model
smart-tool-creator check-spec-adherence \
  --directory ~/src/incident-postmortem \
  --agent-provider amplifier-agent \
  --model anthropic/claude-opus-5

# one part of the checklist
smart-tool-creator check-spec-adherence \
  --directory ~/src/incident-postmortem \
  --check failure-names-remedy \
  --check prerequisite-failures-match-manifest
```

```python
from pathlib import Path

from smart_tool_creator.lib import check_spec_adherence

report = check_spec_adherence(
    directory=Path("~/src/incident-postmortem").expanduser(),
    checks=["failure-names-remedy", "prerequisite-failures-match-manifest"],
)
report.counts, report.deviating, report.findings, report.output_message
```

## Arguments

- `--directory PATH`: the smart tool's distribution root; the current directory when
  omitted. It must hold a `smart-tool.json` at its root, and no parent is searched.
- `--check ID`: repeatable; a check id from the list below. Every check when omitted. An id
  that is not on the list is refused before anything runs, and the message names the ids that
  are.
- `--agent-provider`: what the agent runs through, `{{ agent_providers | join: "` or `" }}`. The
  first installed, in that order, when omitted.
- `--model`: the model the reviewers run on: a Copilot model id for `copilot`,
  `<provider>/<model>` for `amplifier-agent` (for instance `anthropic/claude-opus-5`).
  Defaults to `{{ default_review_models.copilot }}` on `copilot` and
  `{{ default_review_models["amplifier-agent"] }}` on `amplifier-agent`.
- `--reasoning-effort`: how hard the model thinks before it answers, one of `low`, `medium`,
  `high`, `xhigh`, `max`. Defaults to `{{ default_review_reasoning_effort }}`. Applies to the
  `copilot` agent provider only.
- `intelligence`, library only: the `Intelligence` implementation the reviewers run through,
  which wins over `agent_provider`; `resolve_intelligence(agent_provider)` when omitted. Tests
  inject a fake.

## Result

`SpecAdherenceReport` carries `root`, the reviewed tool's distribution root; `conformance`,
the kit's report, which ran first; `findings`, one per check in the checklist's order, each
with `id`, `status`, `spec` (the spec sentence it operationalizes), `evidence` (`path:line`
references with a sentence each), and `suggestion` (what to change, empty when the tool
adheres); `counts`, how many findings carry each status; `deviating`, the ids the tool
deviates from; and `output_message`, all of that for the calling agent, which is what the CLI
prints.

A status is `adheres`, `deviates`, `not-applicable` (the check concerns something the tool
does not have), or `unclear` (the evidence does not settle it; a reviewer never guesses). A
check its reviewer returned no finding for is also `unclear`, with the evidence saying so, so
the report always carries every requested check.
When the kit failed, `findings` is empty, every count is 0, and the message carries the kit's
report and says to fix those rules first. The CLI exits 1 when the kit failed or anything
deviates.

The checklist ships as Markdown under `capabilities/check_spec_adherence/checks/`: one
directory per group holding a `GROUP.md` and one file per check, each carrying its spec
sentence verbatim and the guidance that calibrates a reviewer. `lib.spec_checks()` returns it
as `ReviewGroup` objects without running anything.

The checklist, by group:

```
boundary                              lib.py, cli.py, every other surface
  library-holds-every-capability      nothing a wrapper does is missing from the library
  cli-is-thin                         commands parse arguments and do I/O, then call the library
  help-comes-from-library             what --help prints is produced by the library, the CLI adds nothing

smart-paths                           the model-backed capabilities, their help text, the provider setup
  genuinely-model-backed              at least one capability does work a model does
  ai-capabilities-identifiable        a caller can tell which capabilities consult a model
  no-provider-failure-names-remedy    a smart path with nothing configured says so and never answers with less

self-description                      SMART_TOOL.md, each capability's skill, skills/<name>/SKILL.md, the rendered --help
  tool-skill-content                  when to reach for the tool, install, invocations, sharp edges; under 500 lines
  capability-skills-complete          every capability's skill has its arguments, an invocation, the result, the failures
  agent-skill-is-thin                 the shipped Agent Skill carries the name, description, install, and "run --help"
  manifest-describes-the-tool         description and use_cases match what the capabilities do

results                               how capabilities take input and hand back output, where they write
  context-accepted-as-data            the library accepts context as content, not only as a path
  stdout-results-stderr-diagnostics   results on stdout, progress and warnings on stderr
  artifact-location-named             a capability that writes a file says where
  files-outside-install-tree          state, caches, logs, and temporary files never land beside the source

failures                              error types, preflight code, exit codes, the manifest's requires
  failure-names-remedy                every failure says what went wrong and how to correct it
  partial-results-are-failures        a capability never silently returns the part that worked
  prerequisite-failures-match-manifest  a missing prerequisite fails as the manifest declares it
```

## Failures

Model-backed: it runs through the agent provider `--agent-provider` names. `copilot` runs
through GitHub Copilot, signed in as the GitHub CLI's user, so `gh` must be installed and
`gh auth login` completed with an account that has a Copilot subscription. `amplifier-agent`
runs through Amplifier Agent and needs the credentials of the model provider `--model` names,
for instance `OPENAI_API_KEY` for `openai/...`; see
https://github.com/microsoft/amplifier-agent/blob/v1/docs/providers.md. An agent provider
that is not installed fails with the command that installs it. With nothing configured it
fails immediately and names what to set; it never falls back to a deterministic answer.

A failure prints its message to stderr and exits 1: the directory holds no `smart-tool.json`
(scaffold it with `init` first), a `--check` id is not on the checklist, `uv` is not on
`PATH`, the intelligence preflight fails, the kit produced no verdict, or a reviewer fails.
Nothing is written to the tool, so a failed run leaves it exactly as it was. A bad invocation
exits 2.
