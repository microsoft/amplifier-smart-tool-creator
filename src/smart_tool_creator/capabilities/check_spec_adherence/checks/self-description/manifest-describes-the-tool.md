---
spec_file: manifest.md
spec: >-
  **`description`** says what the tool does and when to reach for it, in that order.
  **`use_cases`** are the concrete jobs the tool is for. These are selection aids, not a
  capability list, and they should read like things a person wants, not like functions the
  tool exposes.
---

## What to decide

Whether the manifest's `description` and `use_cases` match what the capabilities actually do.
This is the first tier of disclosure: it is what a registry shows and what an agent routes
work by, so a promise here that no capability keeps sends work to a tool that cannot do it.
The test is the promise, not the prose.

## Adheres when

- The description says what the tool does, then when to reach for it, in that order.
- Every job the description and the use cases name is something a capability actually performs
  today.
- The use cases read like outcomes a person wants, in their words.
- The description carries the words someone would use when they need this tool, so it can be
  found.

## Deviates when

- The description or a use case promises something no capability does: a planned feature, a
  roadmap item, or a capability that was removed.
- The use cases are a capability list in disguise: one entry per function, named after the
  function.
- The description says only what the tool is, never when to reach for it.
- The description contradicts what the tool's skill or its documentation says it does.

## Look at

- `src/<package>/SMART_TOOL.md` frontmatter: `description` and `use_cases`.
- The capability table or registry in the library, for what actually exists.
- Each capability's skill, to confirm a promised job is really performed.
- `README.md` and any shipped Agent Skill, which usually repeat the same sentence and drift together.
- Spec: https://github.com/microsoft/amplifier-smart-tools/blob/main/spec/manifest.md#the-frontmatter
- Worked example: https://github.com/microsoft/amplifier-smart-tool-creator/blob/main/src/smart_tool_creator/SMART_TOOL.md
- `reference/amplifier-smart-tools/spec/manifest.md` may be present locally with the full chapter.
