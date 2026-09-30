---
spec_file: invocation.md
spec: >-
  It says what an agent would otherwise get wrong: when to reach for the tool and when not,
  install and prerequisites, worked invocations, sharp edges, where to read more. The Agent
  Skills ceiling of 500 lines applies.
---

## What to decide

Whether the tool's skill, which is the manifest body as `<tool> --help` renders it, carries
all of that and stays under 500 lines. A skill that routes to the capability skills for the
detail still has to say when to reach for the tool, when NOT to, and how to install it: those
are the parts no capability skill covers. The intent is that an agent reading this one
document does not have to guess whether this tool is the right one.

## Adheres when

- There is a section saying when to reach for the tool, and it also says when not to: the
  cases this tool is the wrong choice for, or its non-goals.
- Install commands are present and copy-pasteable, and prerequisites are named.
- At least one worked invocation appears, or the skill points at the capability skills that
  carry them and says so.
- Sharp edges and pointers to deeper documentation are there.
- The rendered skill is under 500 lines; count it.

## Deviates when

- The skill says when to reach for the tool but never when not to.
- Install or prerequisites are missing, so an agent cannot get from reading to running.
- It is a bare description with no guidance an agent would otherwise get wrong.
- It exceeds 500 lines.

## Look at

- `src/<package>/SMART_TOOL.md`, the Markdown body below the frontmatter.
- The rendered `<tool> --help`; run it and count the lines.
- `docs/` for non-goals the skill could be repeating and does not.
- Spec: https://github.com/microsoft/amplifier-smart-tools/blob/main/spec/invocation.md#self-description
- Spec: https://github.com/microsoft/amplifier-smart-tools/blob/main/spec/manifest.md#the-body
- Worked example: https://github.com/microsoft/amplifier-smart-tool-creator/blob/main/src/smart_tool_creator/SMART_TOOL.md
- `reference/amplifier-smart-tools/spec/` may be present locally with the full spec.
