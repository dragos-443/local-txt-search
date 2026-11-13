from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "evaluate_functional.py"
ORACLE = ROOT / "evaluation" / "queries.json"


def run_evaluation(*arguments: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *arguments],
        cwd=ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def test_functional_evaluation_records_all_passing_cases(tmp_path: Path) -> None:
    output = tmp_path / "functional-results.json"

    completed = run_evaluation("--output", str(output))
    result = json.loads(output.read_text(encoding="utf-8"))

    assert completed.returncode == 0
    assert "Casi superati: 13/13" in completed.stdout
    assert result["total_cases"] == result["passed_cases"] == 13
    assert result["all_passed"] is True
    assert all(case["passed"] for case in result["cases"])
    assert all("score" not in case for case in result["cases"])


def test_functional_evaluation_fails_when_observed_paths_differ(
    tmp_path: Path,
) -> None:
    cases = json.loads(ORACLE.read_text(encoding="utf-8"))
    cases[0]["expected_paths"] = ["missing.txt"]
    altered_oracle = tmp_path / "altered-oracle.json"
    altered_oracle.write_text(
        json.dumps(cases, ensure_ascii=False), encoding="utf-8"
    )
    output = tmp_path / "functional-results.json"

    completed = run_evaluation(
        "--oracle",
        str(altered_oracle),
        "--output",
        str(output),
    )
    result = json.loads(output.read_text(encoding="utf-8"))

    assert completed.returncode == 1
    assert result["passed_cases"] == 12
    assert result["all_passed"] is False
    assert result["cases"][0]["passed"] is False
