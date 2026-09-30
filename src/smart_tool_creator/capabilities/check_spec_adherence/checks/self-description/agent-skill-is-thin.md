---
spec_file: invocation.md
spec: >-
  The skill carries the manifest's name and description, the install commands, and the
  instruction to run `--help` and follow it. Nothing more.
---

## What to decide

Whether the shipped Agent Skill, `skills/<name>/SKILL.md`, stays that thin. This is
NOT-APPLICABLE when the tool ships no such file; shipping one is optional. The intent is that
the skill never duplicates or drifts from what `--help` says: the tool brings the rest with it
at runtime, so there is one place the guidance is written and it stays correct when the tool
changes. Judge by what would go stale, not by line count.

## Adheres when

- Agent Skills frontmatter is present: `name`, `description`, and optionally `license` and
  `metadata`. This is required by the Agent Skills format and is not excess.
- Discovery trigger keywords inside the description are expected, and are not excess.
- A one-paragraph summary of what the tool does is fine.
- The install commands are there.
- It tells the reader to run `--help` and follow what it says, rather than restating it.

## Deviates when

- The skill carries capability-level detail: argument lists, per-capability invocations,
  result shapes, or failure lists.
- It carries instructions that could go stale when the tool changes, such as a capability list
  with descriptions, or defaults copied out of the code.
- It re-explains what the tool's own `--help` already renders.

## Look at

- `skills/<name>/SKILL.md`; if the tool ships none, answer `not-applicable` and say so.
- The rendered `<tool> --help`, to see what the skill would be duplicating.
- Spec: https://github.com/microsoft/amplifier-smart-tools/blob/main/spec/invocation.md#shipping-an-agent-skill-alongside
- Worked example of an acceptable skill: https://github.com/microsoft/amplifier-smart-tool-creator/blob/main/skills/smart-tool-creator/SKILL.md
- The Agent Skills format: https://agentskills.io/specification
- `reference/amplifier-smart-tools/spec/invocation.md` may be present locally with the full chapter.
