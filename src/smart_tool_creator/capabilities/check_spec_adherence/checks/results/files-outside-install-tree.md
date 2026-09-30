---
spec_file: invocation.md
spec: >-
  State, caches, logs, and temporary files belong outside the tool's own directory. A smart
  tool is installed from a distribution it does not own and is invoked from a working directory
  it did not choose, so neither is a safe place to write. State goes to the conventional
  per-user location for the platform, temporary files to a temporary directory, and output
  artifacts where the caller asked for them.
---

## What to decide

Whether the tool's own state, caches, logs, or temporary files land beside its source or in the
working directory it was invoked from, rather than in a per-user or temporary location. This
check is about STATE, not about output. Output artifacts are the caller's: a caller-chosen or
documented default location under the working directory is fine, for instance a scaffolding
capability creating `./<name>`.

## Adheres when

- The tool writes no state at all, which is the common and simplest case.
- State and caches go to the platform's per-user location, or to a path the caller configured.
- Temporary files are created through the standard temporary-directory facility and cleaned up.
- Output artifacts land where the caller asked, or at a default under the working directory that
  the documentation names.
- A third-party tool the capability runs inside the target project leaves its own cache there,
  for instance a test runner's `.pytest_cache` in a tool being tested. That is not this tool's
  state; do not report it.

## Deviates when

- A cache, index, token, log, or config of the tool's own is written next to the installed
  package or inside the source tree.
- The tool drops a dot-directory of its own state into whatever working directory it was run
  from, without being asked.
- A temporary file is written to the package directory or to the current directory instead of a
  temporary one.

## Look at

- Every write in the codebase: `write_text`, `write_bytes`, `Path.open`, `mkdir`, `tempfile`.
- Paths built from `Path(__file__)`, which point inside the installed package.
- Paths built from `Path.cwd()`, and whether what lands there is output or state.
- Spec: https://github.com/microsoft/amplifier-smart-tools/blob/main/spec/invocation.md#where-a-tool-puts-its-files
- Worked example: https://github.com/microsoft/amplifier-smart-tool-creator/blob/main/src/smart_tool_creator/capabilities/init/scaffold.py
- `reference/amplifier-smart-tools/spec/invocation.md` may be present locally with the full chapter.
