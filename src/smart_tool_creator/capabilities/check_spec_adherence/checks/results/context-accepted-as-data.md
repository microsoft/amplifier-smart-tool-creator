---
spec_file: invocation.md
spec: >-
  **The payload is data, not a reference.** At the library level, a caller passes the actual
  content. This keeps the library free of assumptions about where the caller's material lives
  and keeps it usable from processes that have no filesystem in common with the caller. A CLI
  wrapper may accept a file path and read it into the payload, because that is a convenience
  of the command line, not a change to what the library accepts.
---

## What to decide

Whether the library accepts context as content. The intent is that a caller in another process,
a container, or a service with no filesystem in common can still hand the tool its material.
Read this narrowly: it DEVIATES only when the library can ONLY take a reference to material it
must load itself and gives the caller no way to pass content.

## Adheres when

- A context or payload parameter takes the content as a string, bytes, or a structure.
- The input is inherently a file or a directory (a repository to scaffold, a tool to review,
  a document tree to index), so a path is the content.
- The CLI takes `--file` or `--from` and reads it into the value before calling the library.
- The capability's own agent reads the tool's working directory, and the documentation says so
  and says how permissions and scope are configured. Free-text `context` entries that name
  files an agent will read are acceptable under this.
- A path is offered alongside a content parameter, so the caller may use either.

## Deviates when

- The only way in is a path the library opens itself, with no content parameter anywhere, and
  no agent-reads-the-workspace design documented to explain it.
- The library accepts content but silently ignores it in favour of re-reading a path.
- The documentation promises content and the signature takes only a path.

## Look at

- `src/<package>/lib.py` signatures: what type each context or payload parameter takes.
- The CLI command that feeds it, for whether a path is read in at that layer.
- The capability's skill and `docs/`, for a documented agent-reads-the-workspace design.
- Spec: https://github.com/microsoft/amplifier-smart-tools/blob/main/spec/invocation.md#passing-context-in
- Worked example: https://github.com/microsoft/amplifier-smart-tool-creator/blob/main/src/smart_tool_creator/lib.py
- `reference/amplifier-smart-tools/spec/invocation.md` may be present locally with the full chapter.
