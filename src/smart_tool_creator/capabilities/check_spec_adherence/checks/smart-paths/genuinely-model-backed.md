---
spec_file: structure.md
spec: >-
  A smart tool has to do something genuinely powered by a model. If every path through it is
  deterministic code, it is a tool, and that is fine, but it is not a smart tool.
---

## What to decide

Whether at least one capability does work a model does, rather than wrapping a template the
code could have filled in itself. The intent is that the model earns its place: it is doing
judgment, language, or open-ended reasoning that deterministic code could not have produced.
One genuine model-backed capability satisfies this; the rest of the tool may be deterministic.

## Adheres when

- A capability sends a prompt built from the caller's input to a model and the model's answer
  is the result, or the work the model performed is the result.
- The model's job is judgment, summarization, classification, code it writes, or a review it
  forms: something whose output is not a function of the input alone.
- The model runs through the tool's own provider interface, so the call is real rather than
  stubbed.

## Deviates when

- Every path through the tool is deterministic code and no capability reaches a model.
- The only model call fills a template the code already determined, so the model's answer
  could be replaced by string formatting without changing the result.
- The model is called but its output is discarded, or is only used to pick among branches the
  code could have picked itself.

## Look at

- `src/<package>/lib.py` and the capability table, for which capabilities claim to be model-backed.
- The code of each such capability: the prompt it builds, what it sends, what it does with the answer.
- `src/<package>/intelligence/`, or wherever the provider interface and its implementation live.
- Spec: https://github.com/microsoft/amplifier-smart-tools/blob/main/spec/structure.md#the-ai-capability
- Worked example: https://github.com/microsoft/amplifier-smart-tool-creator/blob/main/src/smart_tool_creator/intelligence/copilot.py
- `reference/amplifier-smart-tools/spec/structure.md` may be present locally with the full chapter.
