---
name: results
order: 4
read_first:
  - how each capability takes its input, in the library and in the CLI
  - how results reach stdout and diagnostics reach stderr
  - every place the code writes a file
checks:
  - context-accepted-as-data
  - stdout-results-stderr-diagnostics
  - artifact-location-named
  - files-outside-install-tree
---

These checks are about what goes in, what comes back, and where the tool writes. Follow one
capability from its CLI argument through the library call to its printed result, then look for
every write in the codebase.
