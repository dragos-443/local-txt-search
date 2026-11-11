from __future__ import annotations

from pathlib import Path

from whoosh.fields import TEXT, Schema
from whoosh.index import create_in
from whoosh.query import Term


def test_whoosh_can_create_and_query_a_disk_index(tmp_path: Path) -> None:
    index = create_in(tmp_path, Schema(content=TEXT(stored=True)))
    writer = index.writer()
    writer.add_document(content="prova whoosh")
    writer.commit()

    with index.searcher() as searcher:
        results = searcher.search(Term("content", "whoosh"))
        assert [result["content"] for result in results] == ["prova whoosh"]

    index.close()
