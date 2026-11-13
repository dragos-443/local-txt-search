from __future__ import annotations

import json
import math
from pathlib import Path

import pytest

from scripts import evaluate_real


ROOT = Path(__file__).resolve().parents[1]
JUDGMENTS = ROOT / "evaluation" / "real_judgments.json"
RESULTS = ROOT / "evaluation" / "real_results.json"


def test_judgments_cover_every_initial_document() -> None:
    initial, cases = evaluate_real.validate_judgments()
    paths = {entry["path"] for entry in initial}
    assert len(cases) == 10
    assert all({label["path"] for label in case["labels"]} == paths for case in cases)


@pytest.mark.parametrize("bad_path", [None, "it/not_in_initial.txt"])
def test_incomplete_or_external_judgments_are_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, bad_path: str | None
) -> None:
    document = json.loads(JUDGMENTS.read_text(encoding="utf-8"))
    if bad_path is None:
        document["cases"][0]["labels"].pop()
    else:
        document["cases"][0]["labels"][0]["path"] = bad_path
    altered = tmp_path / "bad_judgments.json"
    altered.write_text(json.dumps(document, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(evaluate_real, "JUDGMENTS", altered)
    with pytest.raises(ValueError, match="incompleti o esterni"):
        evaluate_real.validate_judgments()


def test_archived_metrics_recompute_from_complete_sets() -> None:
    document = json.loads(RESULTS.read_text(encoding="utf-8"))
    initial, judgments = evaluate_real.validate_judgments()
    paths = {entry["path"] for entry in initial}
    assert len(document["cases"]) == 10
    for case, judgment in zip(document["cases"], judgments, strict=True):
        assert case["id"] == judgment["id"]
        assert case["query"] == judgment["query"]
        assert case["relevant_paths"] == judgment["relevant_paths"]
        assert set(case["returned_paths"]) <= paths
        expected = evaluate_real.metrics(set(case["relevant_paths"]), set(case["returned_paths"]))
        for key, value in expected.items():
            assert math.isclose(case[key], value)
    for key in ("precision", "recall", "f1"):
        assert math.isclose(document["macro_average"][key], sum(case[key] for case in document["cases"]) / 10)


def test_no_returned_documents_have_zero_precision_and_f1() -> None:
    result = evaluate_real.metrics({"it/01_informatica.txt"}, set())
    assert result == {"tp": 0, "fp": 0, "fn": 1, "precision": 0.0, "recall": 0.0, "f1": 0.0}
