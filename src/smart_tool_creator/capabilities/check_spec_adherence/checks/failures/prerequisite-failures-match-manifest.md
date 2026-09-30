---
spec_file: invocation.md
spec: >-
  **A missing prerequisite** fails immediately, naming what is absent and how to install it.
  The manifest already declares these, so the failure and the manifest must agree.
---

## What to decide

Whether what the tool fails with on a missing prerequisite agrees with what the manifest's
`requires` entries declare. Two directions, both required: every prerequisite the preflight
checks for has a `requires` entry, and every non-optional entry is something the tool actually
fails without. The intent is that a caller reading the manifest before installing learns the
same set of prerequisites it would learn by running the tool and hitting the failure.

## Adheres when

- Each executable or credential the preflight checks for (`uv`, `git`, `gh`, and the like) has
  a `requires` entry with a `name`, a `purpose`, and an `install` reference.
- The failure message names the missing thing and where to install it from, and the manifest's
  `install` points at the same documentation.
- Entries marked `optional: true` are ones the tool genuinely runs without, in a reduced form
  the `purpose` describes.
- The check happens before work begins, so nothing is half-done when it fails.

## Deviates when

- A preflight fails on something the manifest never declares, so an agent could not have
  prepared for it.
- A non-optional entry names something the tool runs fine without, or that nothing checks.
- An entry is marked optional but its absence stops a capability the tool advertises.
- The failure names no install reference, or names a different one from the manifest.
- The prerequisite is discovered late, after files have been written or tokens spent.

## Look at

- `src/<package>/SMART_TOOL.md` frontmatter: every `requires` entry and its `optional` flag.
- Every preflight in the codebase: search for `shutil.which`, environment variable reads, and
  credential lookups, in each capability and in the provider setup.
- The message each raises, and compare its install reference with the manifest's.
- Spec: https://github.com/microsoft/amplifier-smart-tools/blob/main/spec/invocation.md#failure
- Spec: https://github.com/microsoft/amplifier-smart-tools/blob/main/spec/manifest.md#the-frontmatter
- Worked example: https://github.com/microsoft/amplifier-smart-tool-creator/blob/main/src/smart_tool_creator/SMART_TOOL.md
- `reference/amplifier-smart-tools/spec/` may be present locally with the full spec.
