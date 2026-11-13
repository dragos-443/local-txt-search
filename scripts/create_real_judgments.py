"""Freeze lexical relevance judgments for every initial file, without searching."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REAL = ROOT / "datasets" / "real"
INITIAL = REAL / "initial_50.json"
QUERIES = ROOT / "evaluation" / "real_queries.json"
OUTPUT = ROOT / "evaluation" / "real_judgments.json"


def words(value: str) -> list[str]:
    value = unicodedata.normalize("NFKD", value.casefold())
    value = "".join(character for character in value if not unicodedata.combining(character))
    return re.findall(r"[^\W_]+", value, flags=re.UNICODE)


def relevant(tokens: list[str], terms: list[str], mode: str) -> bool:
    if mode == "all_terms":
        return all(term in tokens for term in terms)
    if mode == "phrase":
        return any(tokens[position:position + len(terms)] == terms for position in range(len(tokens) - len(terms) + 1))
    raise ValueError(f"Modalità sconosciuta: {mode}")


def create_judgments() -> dict:
    initial = json.loads(INITIAL.read_text(encoding="utf-8"))["entries"]
    queries = json.loads(QUERIES.read_text(encoding="utf-8"))
    if len(initial) != 50 or len(queries) != 10:
        raise ValueError("Servono 50 documenti iniziali e 10 query")
    if len({entry["path"] for entry in initial}) != 50:
        raise ValueError("Percorsi iniziali duplicati")
    texts = {}
    for entry in initial:
        path = REAL / entry["path"]
        payload = path.read_bytes()
        if hashlib.sha256(payload).hexdigest() != entry["sha256"]:
            raise ValueError(f"File iniziale modificato: {entry['path']}")
        texts[entry["path"]] = payload.decode("utf-8")

    cases = []
    for query in queries:
        expected_terms = words(query["query"].split(maxsplit=1)[1])
        if expected_terms != query["terms"]:
            raise ValueError(f"Termini incoerenti: {query['id']}")
        if query["field"] not in ("filename", "content"):
            raise ValueError(f"Campo non valido: {query['id']}")
        labels = []
        for entry in initial:
            path = entry["path"]
            field_text = Path(path).stem if query["field"] == "filename" else texts[path]
            labels.append({"path": path, "relevant": relevant(words(field_text), query["terms"], query["mode"])})
        relevant_paths = sorted(label["path"] for label in labels if label["relevant"])
        if not relevant_paths:
            raise ValueError(f"Query senza documenti rilevanti: {query['id']}")
        cases.append({"id": query["id"], "query": query["query"], "field": query["field"],
                      "mode": query["mode"], "terms": query["terms"], "labels": labels,
                      "relevant_paths": relevant_paths})
    return {"schema_version": 1, "method": "Ispezione testuale indipendente dal motore sui 50 file iniziali; parole intere, casefold e accenti rimossi; AND senza ordine, phrase consecutiva.",
            "initial_reference_sha256": hashlib.sha256(INITIAL.read_bytes()).hexdigest(), "cases": cases}


def main() -> None:
    if OUTPUT.exists():
        raise SystemExit(f"Giudizi già congelati: {OUTPUT}")
    result = create_judgments()
    OUTPUT.write_bytes((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(f"Congelati {sum(len(case['labels']) for case in result['cases'])} giudizi in {OUTPUT}")


if __name__ == "__main__":
    main()
