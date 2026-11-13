from __future__ import annotations

import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
REAL_DIR = ROOT / "datasets" / "real"
SYNTHETIC_DIR = ROOT / "datasets" / "synthetic"


def load_manifest() -> list[dict[str, str]]:
    with (REAL_DIR / "manifest.csv").open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def test_real_corpus_matches_manifest() -> None:
    rows = load_manifest()

    assert len(rows) == 200
    assert Counter(row["language"] for row in rows) == {"it": 100, "en": 100}
    assert Counter(row["pair_id"] for row in rows) == {
        f"{number:02d}": 2 for number in range(1, 101)
    }
    assert len({row["path"] for row in rows}) == 200
    assert len({row["sha256"] for row in rows}) == 200
    assert len({(row["language"], row["page_id"]) for row in rows}) == 200

    declared_paths = {row["path"] for row in rows}
    actual_paths = {
        path.relative_to(REAL_DIR).as_posix()
        for path in REAL_DIR.rglob("*.txt")
    }
    assert actual_paths == declared_paths

    for row in rows:
        path = REAL_DIR / row["path"]
        payload = path.read_bytes()
        text = payload.decode("utf-8")

        assert text.strip()
        assert len(payload) == int(row["bytes"])
        assert hashlib.sha256(payload).hexdigest() == row["sha256"]
        assert row["license"] == "CC BY-SA 4.0"
        assert row["permanent_url"].endswith(f"oldid={row['revision_id']}")


def test_manifest_matches_pinned_sources() -> None:
    pairs = json.loads((REAL_DIR / "sources.json").read_text(encoding="utf-8"))[
        "pairs"
    ]
    rows_by_path = {row["path"]: row for row in load_manifest()}

    assert len(pairs) == 100
    for pair in pairs:
        for language in ("it", "en"):
            source = pair[language]
            row = rows_by_path[source["path"]]
            assert row["language"] == language
            assert row["pair_id"] == pair["pair_id"]
            assert row["title"] == source["title"]
            assert int(row["page_id"]) == source["page_id"]
            assert int(row["revision_id"]) == source["revision_id"]


def test_initial_50_are_unchanged() -> None:
    reference = json.loads((REAL_DIR / "initial_50.json").read_text(encoding="utf-8"))["entries"]
    rows_by_path = {row["path"]: row for row in load_manifest()}
    assert len(reference) == 50
    assert len({entry["path"] for entry in reference}) == 50
    for entry in reference:
        row = rows_by_path[entry["path"]]
        assert int(row["pair_id"]) <= 25
        assert int(row["revision_id"]) == entry["revision_id"]
        assert row["sha256"] == entry["sha256"]
        assert hashlib.sha256((REAL_DIR / entry["path"]).read_bytes()).hexdigest() == entry["sha256"]


def test_synthetic_corpus_shape_and_encoding_cases() -> None:
    invalid = SYNTHETIC_DIR / "misc" / "invalid_encoding.txt"
    valid_paths = sorted(
        path
        for path in SYNTHETIC_DIR.rglob("*.txt")
        if path != invalid
    )

    assert len(valid_paths) == 12
    assert all(path.read_bytes().decode("utf-8") is not None for path in valid_paths)
    assert (SYNTHETIC_DIR / "misc" / "empty.txt").read_bytes() == b""
    assert invalid.read_bytes() == b"\xff"
    with pytest.raises(UnicodeDecodeError):
        invalid.read_text(encoding="utf-8")


def test_query_oracle_is_well_formed_and_references_valid_documents() -> None:
    queries = json.loads(
        (ROOT / "evaluation" / "queries.json").read_text(encoding="utf-8")
    )
    valid_paths = {
        path.relative_to(SYNTHETIC_DIR).as_posix()
        for path in SYNTHETIC_DIR.rglob("*.txt")
        if path.name != "invalid_encoding.txt"
    }

    assert len(queries) == 13
    assert len({case["id"] for case in queries}) == len(queries)
    assert all(set(case) == {"id", "query", "expected_paths"} for case in queries)
    assert all(case["query"].strip() for case in queries)
    assert all(len(paths) == len(set(paths)) for paths in (
        case["expected_paths"] for case in queries
    ))
    assert {
        path
        for case in queries
        for path in case["expected_paths"]
    } <= valid_paths
