---
spec_file: invocation.md
spec: >-
  Where a capability writes an artifact, such as a profile, document, or configuration, to a
  file, the result clearly identifies its location.
---

## What to decide

Whether every capability that writes a file says where it landed. This is NOT-APPLICABLE when
no capability writes one. The intent is that a caller, usually an agent, can act on what was
produced without guessing or searching: the path it needs is in the result it already holds.

## Adheres when

- The returned value carries the path, as a field a caller can read without parsing prose.
- The message printed for the caller names the path too, so both the library and the CLI
  reader are served.
- A capability writing many files names the root it wrote under, and lists them, absolute or
  relative to that root with the root stated.
- Where the caller chose the location, the result still echoes it back.

## Deviates when

- A file is written and neither the return value nor the message names where.
- The result names a relative path with no stated base, so the caller cannot resolve it.
- The path appears only in a progress message that a caller capturing the result never sees.
- The documentation names a default location and the code writes somewhere else.

## Look at

- Every write in the codebase: search for `write_text`, `write_bytes`, `open(`, `Path.open`,
  `mkdir`, `shutil.copy`, and template rendering.
- The result model each such capability returns, for a path field.
- The message template each such capability renders, for the path in prose.
- If nothing writes a file, answer `not-applicable` and say so in the evidence.
- Spec: https://github.com/microsoft/amplifier-smart-tools/blob/main/spec/invocation.md#what-comes-back
- Worked example: https://github.com/microsoft/amplifier-smart-tool-creator/blob/main/src/smart_tool_creator/capabilities/init/scaffold.py
- `reference/amplifier-smart-tools/spec/invocation.md` may be present locally with the full chapter.
