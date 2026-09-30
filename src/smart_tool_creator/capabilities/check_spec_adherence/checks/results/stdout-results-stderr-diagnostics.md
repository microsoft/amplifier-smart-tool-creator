---
spec_file: invocation.md
spec: >-
  Stdout carries the requested result, whether text or structured data. Stderr carries
  diagnostics such as progress messages and warnings, keeping them separate from results that
  callers may pipe to another command or save to a file.
---

## What to decide

Whether results reach stdout and progress messages, warnings, and errors reach stderr. The
intent is that a caller can redirect stdout to a file or pipe it into another command and get
only the result, with nothing interleaved. Judge the CLI and any other text surface; a library
return value is not affected by this check.

## Adheres when

- Every command prints its result, and only its result, to stdout.
- Progress lines, warnings, and spinners go to stderr, or are absent.
- A failure's message goes to stderr and the process exits non-zero.
- Logging, where the tool has any, is configured to stderr.

## Deviates when

- A progress message, banner, or warning is printed to stdout alongside the result.
- An error message is printed to stdout, so a caller redirecting stdout captures the error as
  though it were the answer.
- A `--json` or structured mode still emits human chatter on stdout, so the output does not parse.
- A subprocess the capability runs inherits stdout and leaks its own output into the result.

## Look at

- `src/<package>/cli.py`: every print or echo, and which stream it names. A framework's default
  echo usually goes to stdout, so an error path that uses it deviates.
- Where failures are caught and reported.
- Any logging setup, and any subprocess call that does not capture its output.
- Spec: https://github.com/microsoft/amplifier-smart-tools/blob/main/spec/invocation.md#what-comes-back
- Worked example: https://github.com/microsoft/amplifier-smart-tool-creator/blob/main/src/smart_tool_creator/cli.py
- `reference/amplifier-smart-tools/spec/invocation.md` may be present locally with the full chapter.
