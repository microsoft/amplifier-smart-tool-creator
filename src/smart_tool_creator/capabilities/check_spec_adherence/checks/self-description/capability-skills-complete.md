---
spec_file: invocation.md
spec: >-
  That is the capability's skill, required for every capability: the same shape as the tool's,
  scoped to one capability, and carrying what the tool's skill leaves out: when to use it,
  whether it is deterministic or model-backed, every argument and what it is for, a worked
  invocation, the result, and the failures.
---

## What to decide

Whether every capability has its own skill, and whether each carries when to use it, its kind,
every argument, a worked invocation, the result, and the failures. This is the tier an agent
reads once it has chosen the capability and now needs to call it correctly, so an omission
here is the thing the agent will get wrong. Check every capability, not a sample.

## Adheres when

- `<tool> <capability> --help` prints a skill for each capability the tool exposes.
- Each says when to use it, and whether it is deterministic or model-backed.
- Every argument the library and the CLI accept appears, with what it is for and its default.
- At least one worked invocation is present, in the shape a caller would actually type or write.
- The result is described: its fields, or what the text contains.
- The failures are listed: what raises, what exits non-zero, and what state is left behind.

## Deviates when

- A capability has no skill, or its `--help` is the framework's generated help.
- An argument the CLI accepts is missing from the skill, or a documented argument no longer exists.
- The result section says only that it returns a report, with no fields.
- The failures section is absent, so an agent cannot tell what a non-zero exit means.

## Look at

- The capability table or registry in the library, for the full list of capabilities.
- Each capability's `SKILL.md` beside its code.
- Run `<tool> <capability> --help` for every capability and read what it prints.
- Compare each skill's argument list against the library signature in `lib.py` and the CLI command.
- Spec: https://github.com/microsoft/amplifier-smart-tools/blob/main/spec/invocation.md#self-description
- Worked example: https://github.com/microsoft/amplifier-smart-tool-creator/blob/main/src/smart_tool_creator/capabilities/check_spec_adherence/SKILL.md
- `reference/amplifier-smart-tools/spec/invocation.md` may be present locally with the full chapter.
