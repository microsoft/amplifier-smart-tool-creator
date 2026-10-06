`add-smart-capability` extends a smart tool that already exists: an agent reads the tool,
implements one model-backed capability in its library, exposes it from the CLI, writes the
tests and the docs, then runs the tool's own checks (`uv run pytest`, the conformance kit,
and `prek run --all-files` when `prek` is installed) and fixes what they report. Nothing is
committed; the working tree is left for you to review.

```bash
smart-tool-creator add-smart-capability \
  "Given an incident id, fetch its chat transcript and alert timeline from the incident platform and draft a blameless postmortem: summary, impact, contributing factors, and action items with owners" \
  --directory ~/src/incident-postmortem \
  --context "The platform client is src/incident_postmortem/platform.py; fetch through it, never call the API directly" \
  --context "Our postmortem template is at ~/notes/postmortem-template.md; match its headings"
```

```python
from pathlib import Path

from smart_tool_creator.lib import add_smart_capability

added = add_smart_capability(
    "Given an incident id, fetch its chat transcript and alert timeline from the incident platform "
    "and draft a blameless postmortem: summary, impact, contributing factors, and action items with owners",
    directory=Path("~/src/incident-postmortem").expanduser(),
    context=[
        "The platform client is src/incident_postmortem/platform.py; fetch through it, never call the API directly",
        "Our postmortem template is at ~/notes/postmortem-template.md; match its headings",
    ],
)
added.report, added.checks, added.fix_rounds, added.output_message
```

## Arguments

- `REQUEST`: the whole brief for one capability: what it does, for whom, and what it takes in
  and gives back. Required.
- `--directory PATH`: the smart tool to work in; the current directory when omitted. It must
  hold a `smart-tool.json` at its root, and no parent is searched, so a workspace holding
  several tools is never extended by accident.
- `--context TEXT`: repeatable free text, usually paths to notes, transcripts, or exemplars
  the agent should read before it designs anything. It reads the paths itself, so name them
  rather than pasting their contents.
- `--agent-provider`: what the agent runs through, `{{ agent_providers | join: "` or `" }}`. The
  first installed, in that order, when omitted.
- `--model`: the model the agent runs on: a Copilot model id for `copilot`,
  `<provider>/<model>` for `amplifier-agent` (for instance
  `{{ default_intelligence_models["amplifier-agent"] }}`), a Codex model id for `codex`, a
  Claude model id for `claude`. Defaults to `{{ default_intelligence_models.copilot }}` on
  `copilot`, `{{ default_intelligence_models["amplifier-agent"] }}` on `amplifier-agent`,
  `{{ default_intelligence_models.codex }}` on `codex`, and
  `{{ default_intelligence_models.claude }}` on `claude`.
- `--reasoning-effort`: how hard the model thinks before it acts, one of `low`, `medium`,
  `high`, `xhigh`, `max`. Defaults to `{{ default_intelligence_reasoning_effort }}`. Applies to
  the `copilot`, `codex`, and `claude` agent providers.
- `intelligence`, library only: the `Intelligence` implementation the agent runs through,
  which wins over `agent_provider`; `resolve_intelligence(agent_provider)` when omitted. Tests
  inject a fake.

## Result

`AddedCapability` carries `root`, the extended tool's distribution root; `report`, the
agent's final message, which names the capability, the files it touched, the command to try
it, and its caveats; `checks`, one entry per check with its `name`, `command`, `status`
(`passed`, `failed`, or `skipped`), and the tail of its output when it failed or the reason
when it was skipped; `fix_rounds`, the extra agent runs spent on failing checks, at most 2;
and `output_message`, all of that for the calling agent, which is what the CLI prints.

The prek check is skipped, never failed, when the tool has no `.pre-commit-config.yaml` or
`prek` is not on `PATH`; the conformance check is skipped when the kit itself could not run,
and names the failing rules when it fails. A check still failing when the work stops is returned rather than
raised and named in the message, and the CLI exits 1; the work stays in the tool's working
tree either way, and what it is worth is the caller's call.
