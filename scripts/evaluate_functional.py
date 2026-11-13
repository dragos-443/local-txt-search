"""Execute the frozen functional oracle and record the observed result sets."""

from __future__ import annotations

import argparse
import gc
import json
import tempfile
from pathlib import Path
from typing import Any

from local_txt_search import rebuild_index
from local_txt_search.searching import SearchSession


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "datasets" / "synthetic"
DEFAULT_ORACLE = ROOT / "evaluation" / "queries.json"
DEFAULT_OUTPUT = ROOT / "evaluation" / "functional_results.json"


def _relative_to_root(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def evaluate(source: Path, oracle_path: Path) -> dict[str, Any]:
    """Build a temporary index and compare every query with its expected set."""

    oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
    cases: list[dict[str, Any]] = []

    with tempfile.TemporaryDirectory(prefix="local-txt-search-functional-") as temporary:
        index_dir = Path(temporary) / "index"
        rebuild_index(source, index_dir)

        with SearchSession(index_dir) as session:
            for case in oracle:
                expected_paths = sorted(set(case["expected_paths"]))
                observed_paths = sorted(
                    hit.path for hit in session.search(case["query"])
                )
                cases.append(
                    {
                        "id": case["id"],
                        "query": case["query"],
                        "expected_paths": expected_paths,
                        "observed_paths": observed_paths,
                        "passed": observed_paths == expected_paths,
                    }
                )

        # Whoosh readers can participate in reference cycles. Collect them before
        # TemporaryDirectory removes segment files, which Windows keeps locked.
        del session
        gc.collect()

    passed_cases = sum(case["passed"] for case in cases)
    return {
        "schema_version": 1,
        "corpus": _relative_to_root(source),
        "oracle": _relative_to_root(oracle_path),
        "total_cases": len(cases),
        "passed_cases": passed_cases,
        "all_passed": passed_cases == len(cases),
        "cases": cases,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Esegue l'oracolo funzionale e registra attesi e osservati."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help="Corpus sintetico da indicizzare.",
    )
    parser.add_argument(
        "--oracle",
        type=Path,
        default=DEFAULT_ORACLE,
        help="File JSON contenente query e percorsi attesi.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help="File JSON in cui scrivere gli esiti osservati.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = evaluate(args.source, args.oracle)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(
        f"Casi superati: {result['passed_cases']}/{result['total_cases']}. "
        f"Esiti scritti in: {args.output}"
    )
    return 0 if result["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
