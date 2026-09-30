---
spec_file: invocation.md
spec: >-
  **A smart path with no provider configured** fails saying exactly that, and says what to
  configure. It does not fall back to a degraded deterministic answer, because a caller that
  asked for the smart path and got a lesser result without being told has been misled about
  what it received.
---

## What to decide

Whether a model-backed capability, run with no provider configured, fails naming what to
configure, and never returns a deterministic answer instead. The intent is that the caller is
never quietly downgraded: a lesser result handed back as though it were the real one is worse
than a failure, because the caller cannot tell it happened.

## Adheres when

- The provider setup raises an error naming the missing credential, the command that supplies
  it, or the documentation that explains it.
- The failure arrives before tokens or time are spent, ideally in a preflight the capability
  runs first.
- A deterministic capability of the same tool still runs with nothing configured, which the
  spec requires separately.

## Deviates when

- A missing provider produces an empty result, a `None`, or a stub answer the caller cannot
  distinguish from a real one.
- The capability falls back to a template, a cached answer, or a deterministic approximation.
- The error says only that something failed, with no indication of what to configure.
- The tool refuses to load at all without a provider, which breaks the deterministic paths.

## Look at

- `src/<package>/intelligence/`, the provider interface and its preflight.
- Each model-backed capability's entry point, for where preflight is called and what happens
  when it raises.
- Search for fallbacks: `except`, `if provider is None`, default answers.
- Spec: https://github.com/microsoft/amplifier-smart-tools/blob/main/spec/invocation.md#failure
- Worked example: https://github.com/microsoft/amplifier-smart-tool-creator/blob/main/src/smart_tool_creator/intelligence/copilot.py
- `reference/amplifier-smart-tools/spec/invocation.md` may be present locally with the full chapter.
