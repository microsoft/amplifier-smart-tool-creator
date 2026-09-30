`check-conformance` runs the spec's
[conformance kit](https://github.com/microsoft/amplifier-smart-tools/tree/main/conformance)
against a smart tool and returns its verdict as the kit gave it: one entry per rule with the
kit's own id, status, spec sentence, and detail. Nothing is written to the tool. The kit is
fetched from the spec repository on each run, so the network is needed.

```bash
smart-tool-creator check-conformance --directory ~/src/incident-postmortem
```

```python
from pathlib import Path

from smart_tool_creator.lib import check_conformance

report = check_conformance(directory=Path("~/src/incident-postmortem").expanduser())
report.verdict, report.failed_rules, report.rules, report.output_message
```

## Arguments

- `--directory PATH`: the smart tool's distribution root, the directory holding its
  `pyproject.toml` or `package.json` and its `smart-tool.json`; the current directory when
  omitted. Whether that directory is a smart tool at all is the kit's call: a root without a
  descriptor fails `descriptor-present` rather than being refused here.
- `--timeout SECONDS`: how long the kit allows each invocation it makes of the tool. Defaults
  to 20.

## Result

`ConformanceReport` carries `root`, the directory inspected; `verdict`, `PASS` or `FAIL`;
`counts`, how many rules passed, failed, and were skipped; `failed_rules`, the ids of the
failing rules; `rules`, one entry per rule with `id`, `status` (`PASS`, `FAIL`, or `SKIP`),
`spec`, the sentence of the spec it operationalizes, and `detail`, what the kit saw; and
`output_message`, all of that for the calling agent, which is what the CLI prints.

The verdict is `FAIL` when any rule failed. A rule the kit could not evaluate is `SKIP` with
the reason in its detail, and never fails a tool. When the verdict is `FAIL`, the CLI exits 1
after printing the report; fix what the failing rules' details name and run it again.

The tool under test must already run: the kit never installs it. A uv project is run through
`uv run --`, which puts its console script on `PATH`, so a tool whose descriptor names its
script by bare command works from a fresh clone. Whatever the tool writes relative to its
working directory lands in a scratch directory the kit discards.

## Failures

Deterministic; it needs the network to fetch the kit.

A failure prints its message to stderr and exits 1: the directory does not exist, `uv` is
not on `PATH`, or the kit produced no verdict, which is the network, uv failing to run the
kit, or the kit's output contract changing; the message carries the command to rerun by hand
and the kit's stderr. A bad invocation exits 2.
