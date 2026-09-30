---
name: failures
order: 5
read_first:
  - the error types and every place one is raised
  - preflight code and how missing prerequisites are detected
  - how the CLI maps failures to exit codes
  - the manifest's requires entries
checks:
  - failure-names-remedy
  - partial-results-are-failures
  - prerequisite-failures-match-manifest
---

These checks are about what happens when things go wrong. The caller is usually an agent that
cannot ask a human what to do next, so judge every message by whether it leaves that agent with
an action.
