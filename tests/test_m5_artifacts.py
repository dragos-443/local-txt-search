from __future__ import annotations

import hashlib
import json
import math
import statistics
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REAL = ROOT / "datasets" / "real"
EVALUATION = ROOT / "evaluation"


def test_selection_has_15_pairs_per_group() -> None:
    selection = json.loads((REAL / "selection.json").read_text(encoding="utf-8"))["decisions"]
    accepted = [item for item in selection if item["outcome"] == "accepted"]
    assert len(accepted) == 75
    assert sorted(Counter(item["group"] for item in accepted).values()) == [15] * 5
    assert len({item["pair_id"] for item in accepted}) == 75
    sources = json.loads((REAL / "sources.json").read_text(encoding="utf-8"))["pairs"]
    assert {item["pair_id"] for item in accepted} == {pair["pair_id"] for pair in sources[25:]}


def test_indexing_benchmark_contains_six_reproducible_measurements() -> None:
    document = json.loads((EVALUATION / "indexing_benchmark.json").read_text(encoding="utf-8"))
    runs = document["runs"]
    assert len(runs) == 6
    assert Counter(run["corpus_files"] for run in runs) == {50: 3, 200: 3}
    assert [run["corpus_files"] for run in runs] == [50, 200] * 3
    assert document["inputs"]["manifest_sha256"] == hashlib.sha256((REAL / "manifest.csv").read_bytes()).hexdigest()
    assert document["inputs"]["initial_reference_sha256"] == hashlib.sha256((REAL / "initial_50.json").read_bytes()).hexdigest()
    for size in (50, 200):
        subset = [run for run in runs if run["corpus_files"] == size]
        assert [run["trial"] for run in subset] == [1, 2, 3]
        assert all(run["discovered_files"] == run["indexed_files"] == size for run in subset)
        assert all(run["skipped_files"] == 0 and run["skips"] == [] for run in subset)
        assert all(run["duration_seconds"] > 0 and run["index_bytes"] > 0 for run in subset)
        assert math.isclose(document["median_seconds"][str(size)], statistics.median(run["duration_seconds"] for run in subset))
