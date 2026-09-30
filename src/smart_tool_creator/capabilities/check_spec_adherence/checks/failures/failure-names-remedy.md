---
spec_file: invocation.md
spec: >-
  Failures are loud and they name the remedy. A caller should never have to infer what went
  wrong from an empty result.
---

## What to decide

Whether every failure a caller can hit says what went wrong AND how to correct it. The caller
is usually an agent with no human to ask, so a message that names only the symptom leaves it
stuck. A remedy is an action: a command to run, a value to set, a file to fix, a path to remove
before retrying. Read the message text itself, not the intent behind it.

## Adheres when

- Each raised error names the thing that failed and the action that would fix it, in the same
  message.
- A failure caused by an external command explains what to check, not just what the command
  printed.
- A failure that leaves state behind says so and says what to do with it.
- The CLI surfaces that message on stderr and exits non-zero, so the failure is loud.

## Deviates when

- A message is of the shape "Could not X: <raw stderr>" with no action the caller can take.
- A message names a condition but not the fix, for instance "invalid configuration" with no
  statement of what a valid one is.
- A failure leaves state behind (a half-created directory, a partly written file, a stale lock)
  that the message does not mention, so the next attempt fails for a new reason.
- An exception from a dependency escapes uncaught, so the caller sees a traceback instead of a
  remedy.
- A failure is reported while the process exits 0.

## Look at

- The tool's error type and every `raise` of it.
- Any generic wrapper around subprocess calls: one shared message often covers many call sites
  and names no remedy for any of them.
- The CLI's error handling and its exit codes.
- Spec: https://github.com/microsoft/amplifier-smart-tools/blob/main/spec/invocation.md#failure
- Worked example: https://github.com/microsoft/amplifier-smart-tool-creator/blob/main/src/smart_tool_creator/capabilities/init/scaffold.py
- `reference/amplifier-smart-tools/spec/invocation.md` may be present locally with the full chapter.
