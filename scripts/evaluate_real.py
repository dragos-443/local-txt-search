"""Evaluate the ten frozen lexical judgments on the initial 50 documents."""

from __future__ import annotations

import gc
import hashlib
import json
import statistics
import tempfile
from pathlib import Path
from shutil import copy2

from local_txt_search import rebuild_index
from local_txt_search.searching import SearchSession


ROOT = Path(__file__).resolve().parents[1]
REAL = ROOT / "datasets" / "real"
INITIAL = REAL / "initial_50.json"
QUERIES = ROOT / "evaluation" / "real_queries.json"
JUDGMENTS = ROOT / "evaluation" / "real_judgments.json"
OUTPUT = ROOT / "evaluation" / "real_results.json"


def validate_judgments() -> tuple[list[dict], list[dict]]:
    initial = json.loads(INITIAL.read_text(encoding="utf-8"))["entries"]
    queries = json.loads(QUERIES.read_text(encoding="utf-8"))
    document = json.loads(JUDGMENTS.read_text(encoding="utf-8"))
    cases = document["cases"]
    paths = {entry["path"] for entry in initial}
    if len(paths) != 50 or len(queries) != 10 or len(cases) != 10:
        raise ValueError("Servono 50 documenti e 10 giudizi completi")
    if document["initial_reference_sha256"] != hashlib.sha256(INITIAL.read_bytes()).hexdigest():
        raise ValueError("I giudizi si riferiscono a un altro corpus iniziale")
    if len({case["id"] for case in cases}) != 10:
        raise ValueError("ID dei giudizi duplicati")
    for query, case in zip(queries, cases, strict=True):
        if any(case[key] != query[key] for key in ("id", "query", "field", "mode", "terms")):
            raise ValueError(f"Giudizio incoerente: {query['id']}")
        labels = case["labels"]
        if len(labels) != 50 or {label["path"] for label in labels} != paths:
            raise ValueError(f"Giudizi incompleti o esterni al corpus: {query['id']}")
        if any(type(label["relevant"]) is not bool for label in labels):
            raise ValueError(f"Etichetta non booleana: {query['id']}")
        relevant = sorted(label["path"] for label in labels if label["relevant"])
        if not relevant or relevant != case["relevant_paths"]:
            raise ValueError(f"Insieme rilevante incoerente o vuoto: {query['id']}")
    for entry in initial:
        if hashlib.sha256((REAL / entry["path"]).read_bytes()).hexdigest() != entry["sha256"]:
            raise ValueError(f"File iniziale modificato: {entry['path']}")
    return initial, cases


def metrics(relevant: set[str], returned: set[str]) -> dict[str, float | int]:
    tp = len(relevant & returned)
    fp = len(returned - relevant)
    fn = len(relevant - returned)
    precision = tp / (tp + fp) if returned else 0.0
    recall = tp / (tp + fn)
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def evaluate() -> dict:
    initial, cases = validate_judgments()
    results = []
    with tempfile.TemporaryDirectory(prefix="local-txt-search-real-") as temporary:
        base = Path(temporary)
        source = base / "source"
        for entry in initial:
            destination = source / entry["path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            copy2(REAL / entry["path"], destination)
        index_dir = base / "index"
        stats = rebuild_index(source, index_dir)
        if (stats.discovered_files, stats.indexed_files, stats.skipped_files) != (50, 50, 0):
            raise ValueError("Il sottoinsieme iniziale non è stato indicizzato integralmente")
        with SearchSession(index_dir) as session:
            for case in cases:
                returned = sorted(hit.path for hit in session.search(case["query"]))
                relevant = set(case["relevant_paths"])
                results.append({"id": case["id"], "query": case["query"],
                                "relevant_paths": sorted(relevant), "returned_paths": returned,
                                **metrics(relevant, set(returned))})
        del session
        gc.collect()
    return {"schema_version": 1, "corpus": "initial_50", "document_count": 50,
            "initial_reference_sha256": hashlib.sha256(INITIAL.read_bytes()).hexdigest(),
            "judgments_sha256": hashlib.sha256(JUDGMENTS.read_bytes()).hexdigest(),
            "search_code_sha256": hashlib.sha256((ROOT / "src" / "local_txt_search" / "searching.py").read_bytes()).hexdigest(),
            "cases": results,
            "macro_average": {key: statistics.mean(case[key] for case in results)
                              for key in ("precision", "recall", "f1")}}


def main() -> None:
    result = evaluate()
    OUTPUT.write_bytes((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(f"Valutate {len(result['cases'])} query; risultati: {OUTPUT}")


if __name__ == "__main__":
    main()
