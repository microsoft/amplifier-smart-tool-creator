"""Runs the real conformance kit against this repository and against a directory that is not a smart tool."""

from pathlib import Path
import subprocess

import pytest
from typer.testing import CliRunner

from smart_tool_creator.capabilities.check_conformance.capability import CONFORMANCE_KIT
from smart_tool_creator.cli import app
from smart_tool_creator.lib import check_conformance
from smart_tool_creator.schemas import SmartToolCreatorError

DISTRIBUTION_ROOT = Path(__file__).parents[1]

runner = CliRunner()


def test_this_repository_passes_every_rule() -> None:
    report = check_conformance(directory=DISTRIBUTION_ROOT)

    assert report.root == DISTRIBUTION_ROOT.resolve()
    assert report.verdict == "PASS"
    assert report.failed_rules == []
    assert report.counts["fail"] == 0
    assert {rule.status for rule in report.rules} == {"PASS"}, report.output_message
    assert report.output_message.endswith(f"Verdict: PASS ({len(report.rules)} pass, 0 fail, 0 skip)")


def test_a_directory_that_is_not_a_smart_tool_is_judged_by_the_kit_and_exits_one(tmp_path: Path) -> None:
    result = runner.invoke(app, ["check-conformance", "--directory", str(tmp_path)])

    assert result.exit_code == 1, result.output
    assert "FAIL descriptor-present: no smart-tool.json at the distribution root" in result.stdout
    assert "SKIP loads-without-provider:" in result.stdout
    assert "Verdict: FAIL" in result.stdout
    assert "Failing: descriptor-present, manifest-present." in result.stdout
    assert "descriptor-present: packaging.md:" in result.stdout


def test_a_kit_that_returns_no_verdict_names_the_kit_the_command_and_its_stderr(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def no_verdict(command: list[str], **keywords: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 2, stdout="", stderr="error: Failed to download the script")

    monkeypatch.setattr(subprocess, "run", no_verdict)

    with pytest.raises(SmartToolCreatorError) as failure:
        check_conformance(directory=tmp_path)

    message = str(failure.value)
    assert "did not return a verdict (exit 2)" in message
    assert CONFORMANCE_KIT in message
    assert str(tmp_path.resolve()) in message
    assert message.endswith("error: Failed to download the script")
