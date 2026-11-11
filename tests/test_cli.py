from __future__ import annotations

import subprocess
import sys


def run_cli(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "local_txt_search", *arguments],
        check=False,
        capture_output=True,
        text=True,
    )


def test_help_describes_planned_commands() -> None:
    result = run_cli("--help")

    assert result.returncode == 0
    assert "index" in result.stdout
    assert "search" in result.stdout
    assert "non ancora" in result.stdout
    assert "disponibile" in result.stdout


def test_planned_command_fails_clearly() -> None:
    result = run_cli("index")

    assert result.returncode == 2
    assert "non è ancora disponibile" in result.stderr
    assert "M3" in result.stderr
