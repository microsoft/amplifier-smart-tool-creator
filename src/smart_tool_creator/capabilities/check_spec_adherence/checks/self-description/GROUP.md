---
name: self-description
order: 3
read_first:
  - the SMART_TOOL.md body
  - each capability's skill (the Markdown --help renders for it)
  - skills/<name>/SKILL.md when present
  - the output of `<tool> --help` and `<tool> <capability> --help`, run them
checks:
  - tool-skill-content
  - capability-skills-complete
  - agent-skill-is-thin
  - manifest-describes-the-tool
---

These checks are about what the tool says about itself to an agent that has decided to drive
it. The three tiers are the manifest description, the tool's skill, and each capability's
skill; judge each against what its own tier is for.
