---
spec_file: invocation.md
spec: >-
  **A partial result** is a failure unless the capability documents partial completion as a
  valid outcome, in which case the result says which parts succeeded. A capability never
  silently returns the portion that worked.
---

## What to decide

Whether any capability returns the part that worked without saying so. Returning a partial
result is fine where the capability DOCUMENTS it and the result NAMES which parts succeeded;
both conditions, not one. The intent is that a caller never mistakes an incomplete answer for a
complete one, because from the outside the two look identical.

## Adheres when

- A step that fails raises, so nothing incomplete is handed back.
- Partial completion is documented in the capability's skill as a valid outcome, and the result
  carries per-item status a caller can read.
- A summary in the result says how many items succeeded and which failed, so the caller can act.
- Retries and timeouts end in a failure rather than in whatever had been gathered so far.

## Deviates when

- A loop catches an exception per item, collects what worked, and returns it with no record of
  what did not.
- A timeout returns what was gathered so far as though it were the whole answer.
- The result has a status field for partial completion but the documentation never mentions it.
- The documentation promises partial results but the result shape cannot express which parts
  succeeded.

## Look at

- Every `except` that continues a loop rather than raising.
- Capabilities that fan out: several files, several subprocesses, several model calls.
- The result model of each such capability, for a per-item status.
- That capability's skill, for whether partial completion is documented.
- Spec: https://github.com/microsoft/amplifier-smart-tools/blob/main/spec/invocation.md#failure
- Worked example: https://github.com/microsoft/amplifier-smart-tool-creator/blob/main/src/smart_tool_creator/capabilities/check_spec_adherence/capability.py
- `reference/amplifier-smart-tools/spec/invocation.md` may be present locally with the full chapter.
