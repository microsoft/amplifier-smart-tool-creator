---
spec_file: structure.md
spec: >-
  Everything the tool can do is reachable from the library. The rule is one-directional and
  absolute: no capability exists only in a wrapper.
---

## What to decide

Whether anything a wrapper does is missing from the library. The intent is that a capability
living only in the CLI can be reached by nothing else: not another Python caller, not an MCP
server, not a harness that cannot shell out. So the question is not whether the wrapper is
tidy, it is whether deleting the wrapper would lose something a different caller might want.
Argument parsing, output formatting, reading a path into a value, and HTTP routing are the
wrapper's own medium and are not capability.

## Adheres when

- Every wrapper entry point reads as: parse arguments, call the library, render the return
  value, map a failure to an exit code.
- Behaviour a wrapper needed and the library did not have was added to the library, and the
  wrapper calls it.
- The library exposes the same capabilities under the same names, taking the same inputs.

## Deviates when

- A command computes, filters, merges, or decides something around the library call that a
  library caller would have to reimplement.
- A command composes two library calls in an order that is itself the capability, and no
  library function does that composition.
- A flag changes behaviour inside the wrapper rather than by being passed through.
- A surface other than the CLI (an MCP server, a web handler) holds logic the library lacks.

## Look at

- `src/<package>/lib.py`, the library's entry point: every capability should be reachable there.
- `src/<package>/cli.py`, every command body.
- Any other surface the tool ships. A tool not scaffolded by this creator may lay these out
  differently; find the equivalents rather than assuming the paths.
- Spec: https://github.com/microsoft/amplifier-smart-tools/blob/main/spec/structure.md#the-library-is-the-tool
- Worked example: https://github.com/microsoft/amplifier-smart-tool-creator/blob/main/src/smart_tool_creator/lib.py
- `reference/amplifier-smart-tools/spec/structure.md` may be present locally with the full chapter.
