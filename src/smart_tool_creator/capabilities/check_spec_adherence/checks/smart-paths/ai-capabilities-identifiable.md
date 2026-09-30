---
spec_file: structure.md
spec: >-
  Callers should know which features are AI-enabled, and which ones are not based on the
  context and the capability being advertised. If it is genuinely ambiguous, it can be
  explicitly stated which capabilities require AI.
---

## What to decide

Whether a caller can tell which capabilities consult a model. An explicit statement is
required ONLY where that is not obvious from the context. The intent is a budget and retry
signal: a model-backed path costs tokens and may answer differently on a second run, so a
caller deciding what to invoke needs to know which kind it is reaching for. Do not demand a
particular sentence or a particular place for it.

## Adheres when

- A capability list tags each entry deterministic or model-backed, in the skill, the help
  text, or the documentation.
- Help text for a model-backed capability says it runs through a named provider, or names the
  credentials it needs.
- The capability's own name and description make it plain, for instance where the whole tool
  exists to do one obviously model-backed job.
- The library's signatures carry a provider or model argument that a reader cannot miss.

## Deviates when

- Nothing anywhere distinguishes the paths and the names do not settle it, so a caller cannot
  tell whether a call will spend tokens.
- The documentation claims one set of capabilities is model-backed and the code shows another.
- A capability quietly consults a model while presenting itself as deterministic.

## Look at

- The rendered `<tool> --help` and `<tool> <capability> --help`; run them.
- `SMART_TOOL.md`, the capability list, and each capability's skill.
- The capability table in the library, where one exists, and whether it carries the kind.
- Spec: https://github.com/microsoft/amplifier-smart-tools/blob/main/spec/structure.md#the-ai-capability
- Spec: https://github.com/microsoft/amplifier-smart-tools/blob/main/spec/invocation.md#self-description
- Worked example: https://github.com/microsoft/amplifier-smart-tool-creator/blob/main/src/smart_tool_creator/core/skill.py
- `reference/amplifier-smart-tools/spec/` may be present locally with the full spec.
