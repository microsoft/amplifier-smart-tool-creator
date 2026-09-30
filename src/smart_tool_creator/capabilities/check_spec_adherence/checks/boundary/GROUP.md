---
name: boundary
order: 1
read_first:
  - lib.py
  - cli.py
  - any other surface (MCP server, web service) the tool ships
checks:
  - library-holds-every-capability
  - cli-is-thin
  - help-comes-from-library
---

These checks are about the line between the library and the surfaces wrapped around it. Read
the library's entry point first and every wrapper second, and judge each wrapper by what a
caller that cannot use it would lose.
