from __future__ import annotations

import json
from pathlib import Path

import pytest
from whoosh.query import And, Phrase, Term

from local_txt_search import rebuild_index
from local_txt_search.indexing import index_schema
from local_txt_search.searching import QuerySyntaxError, SearchSession, parse_query


ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_DIR = ROOT / "datasets" / "synthetic"
QUERY_MATRIX = json.loads(
    (ROOT / "evaluation" / "queries.json").read_text(encoding="utf-8")
)


@pytest.fixture(scope="module")
def synthetic_index(tmp_path_factory: pytest.TempPathFactory) -> Path:
    index_dir = tmp_path_factory.mktemp("searching") / "index"
    rebuild_index(SYNTHETIC_DIR, index_dir)
    return index_dir


@pytest.mark.parametrize(
    ("case_id", "query_text", "expected_paths"),
    [
        (case["id"], case["query"], set(case["expected_paths"]))
        for case in QUERY_MATRIX
    ],
    ids=[case["id"] for case in QUERY_MATRIX],
)
def test_all_oracle_queries_return_the_complete_expected_set(
    synthetic_index: Path,
    case_id: str,
    query_text: str,
    expected_paths: set[str],
) -> None:
    del case_id
    with SearchSession(synthetic_index) as session:
        actual_paths = {hit.path for hit in session.search(query_text)}

    assert actual_paths == expected_paths


def test_parser_builds_only_the_supported_query_types() -> None:
    schema = index_schema()

    assert parse_query("nome città", schema) == Term("filename", "citta")
    assert parse_query("contenuto data sources", schema) == And(
        [Term("content", "data"), Term("content", "sources")]
    )
    assert parse_query('nome "data integration"', schema) == Phrase(
        "filename", ["data", "integration"]
    )
    assert parse_query("contenuto AND OR NOT", schema) == And(
        [Term("content", "and"), Term("content", "or"), Term("content", "not")]
    )


@pytest.mark.parametrize(
    "query_text",
    [
        "",
        "sconosciuto data",
        "nome",
        'nome "data integration',
        'nome "data integration" notes',
        "nome data*",
        "contenuto foo:bar",
        "contenuto !!!",
    ],
)
def test_parser_rejects_malformed_or_unsupported_queries(query_text: str) -> None:
    with pytest.raises(QuerySyntaxError):
        parse_query(query_text, index_schema())


def test_results_use_path_as_tie_breaker_and_keep_all_hits(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    for number in range(11, 0, -1):
        (source / f"document-{number:02}.txt").write_text("same", encoding="utf-8")
    index_dir = tmp_path / "index"
    rebuild_index(source, index_dir)

    with SearchSession(index_dir) as session:
        hits = session.search("contenuto same")

    assert len(hits) == 11
    assert [hit.path for hit in hits] == sorted(hit.path for hit in hits)
