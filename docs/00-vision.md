# Vision

Smart Tool Creator is a [Smart Tool](https://github.com/microsoft/amplifier-smart-tools) for building smart tools.
Smart tools succeed when they are commonplace, and they become commonplace when sharing domain expertise as one is easier and more reliable than any alternative.
This tool takes expertise someone holds in a harness, a bundle, or a set of skills to a standalone tool any agent can call, and it tells them whether what they built is working.

## Goals

- Scaffolding a new smart tool is one deterministic command
  - The result conforms to the spec and passes the conformance kit before a line of domain code is written
  - A choice of language, intelligence layer, and optional surfaces is made at scaffold time
  - The tool could change language, add intelligence layers, add surfaces or capabilities after the fact.
- Validating a smart tool against the spec is one command
  - The conformance kit runs as is, and critique against the spec's principles is a model-backed capability built on it: the kit's rules are settled first, and the critique covers only what a machine cannot decide
- The smart capabilities of a smart tool can be evaluated in isolation
  - A tool that proves itself here is known to work before it is shared, so a problem in a host is a problem with the host
- Adding a smart tool to the catalog is one command
- The intelligence inside a smart tool is easy to wire up and easy to swap
  - This tool is itself the example: the intelligence is behind an interface, and every implementation of that interface is a choice a scaffolded tool can make

## Non-Goals

- Being a general-purpose project generator or template engine.
- Hosting or distributing smart tools; that is the catalog's job.
- Making a smart tool discoverable inside a host like Copilot or Claude Code; the catalog's skill does that.

## Principles

- The library is the tool. The CLI and any other surface are thin wrappers over it.
- The intelligence is implemented using the GitHub Copilot SDK first, but amplifier-agent and others will come soon. It is behind an interface so another implementation is a new module, not a rewrite.
- Deterministic paths run with no model provider configured.
- The tool works on Windows, macOS, and Linux seamlessly.

