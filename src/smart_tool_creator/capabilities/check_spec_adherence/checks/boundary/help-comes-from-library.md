---
spec_file: structure.md
spec: >-
  What `--help` prints is a skill, the tool's on the tool and a capability's on that
  capability, and every skill comes from the library. The CLI prints it and adds nothing.
---

## What to decide

Whether what `--help` prints, on the tool and on each capability, is produced by the library,
with the CLI adding nothing of its own. The intent is one source for the guidance: an agent
holding the library and an agent running the CLI must read the same words, and a skill that
the CLI assembles can drift from the library's own account of itself.

## Adheres when

- `<tool> --help` prints the string a library function returns, and the command does nothing
  to it but echo it.
- `<tool> <capability> --help` does the same with that capability's skill from the library.
- `-h` stays the terse generated summary at both scopes, which is the framework's own output
  and not a second skill.
- The library also exposes the pieces the skill is built from, so a library caller can reach
  them without the CLI.

## Deviates when

- The CLI concatenates, reformats, wraps, or appends to what the library returned.
- The CLI builds the capability list, the resources block, or the skill directory line itself.
- A capability's `--help` is the framework's generated help with no skill behind it.
- The skill text lives in the CLI module rather than in the library or in files the library reads.

## Look at

- `src/<package>/cli.py`, the help options and their callbacks at both scopes.
- `src/<package>/lib.py` and the module behind it that renders the skill.
- Run `<tool> --help`, `<tool> -h`, and `<tool> <capability> --help` and compare what each prints.
- Spec: https://github.com/microsoft/amplifier-smart-tools/blob/main/spec/structure.md#the-cli
- Spec: https://github.com/microsoft/amplifier-smart-tools/blob/main/spec/invocation.md#self-description
- Worked example: https://github.com/microsoft/amplifier-smart-tool-creator/blob/main/src/smart_tool_creator/core/skill.py
- `reference/amplifier-smart-tools/spec/` may be present locally with the full spec.
