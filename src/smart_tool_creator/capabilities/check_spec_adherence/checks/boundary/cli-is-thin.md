---
spec_file: structure.md
spec: >-
  Thin means the CLI hooks up argument parsing and I/O conventions and then calls the library.
  Domain logic in the CLI is a defect: it is capability the library cannot reach.
---

## What to decide

Whether the commands only parse arguments, do I/O, and call the library. This is the same
boundary as `library-holds-every-capability` seen from the other side: that check asks what
the library is missing, this one asks what the CLI has taken on. Judge each command body on
its own; one thick command is enough to deviate.

## Adheres when

- A command body is a handful of lines: build the arguments, call the library, print the
  result, exit.
- The CLI reads a file path into the value the library takes as data, which the spec names as
  the common permitted case.
- The CLI chooses text or JSON for printing, handles `--quiet` or colour, and maps the
  library's error type onto an exit code.
- Defaults shown in the help come from the library's constants rather than being retyped.

## Deviates when

- A command validates domain rules, normalizes domain input, or derives domain values before
  the library sees them.
- A command post-processes the library's return value into a different result rather than
  rendering it.
- A command branches on domain state to decide which library function to call, where that
  decision is the capability.
- A default that changes the answer is defined in the CLI and the library has a different one.

## Look at

- `src/<package>/cli.py`, every command, including the callback that runs before them.
- `src/<package>/lib.py`, to see whether what the command does has a home there.
- Any other wrapper the tool ships; the rule reads the same for it.
- Spec: https://github.com/microsoft/amplifier-smart-tools/blob/main/spec/structure.md#the-cli
- Worked example: https://github.com/microsoft/amplifier-smart-tool-creator/blob/main/src/smart_tool_creator/cli.py
- `reference/amplifier-smart-tools/spec/structure.md` may be present locally with the full chapter.
