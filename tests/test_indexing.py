from __future__ import annotations

import logging
import os
from pathlib import Path

import pytest
from whoosh.index import open_dir
from whoosh.query import Every, Phrase, Term

from local_txt_search import IndexBuildError, SkipReason, rebuild_index
from local_txt_search import indexing


ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_DIR = ROOT / "datasets" / "synthetic"


def result_paths(index_dir: Path, query) -> set[str]:
    index = open_dir(index_dir)
    try:
        with index.searcher() as searcher:
            return {result["path"] for result in searcher.search(query, limit=None)}
    finally:
        index.close()


def test_rebuilds_the_synthetic_corpus_and_persists_searchable_fields(
    tmp_path: Path,
) -> None:
    index_dir = tmp_path / "index"

    stats = rebuild_index(SYNTHETIC_DIR, index_dir)

    expected_bytes = sum(
        path.stat().st_size
        for path in SYNTHETIC_DIR.rglob("*.txt")
        if path.name != "invalid_encoding.txt"
    )
    assert stats.discovered_files == 13
    assert stats.indexed_files == 12
    assert stats.skipped_files == 1
    assert stats.indexed_bytes == expected_bytes
    assert stats.duration_seconds >= 0
    assert len(stats.skips) == 1
    assert stats.skips[0].path == "misc/invalid_encoding.txt"
    assert stats.skips[0].reason is SkipReason.INVALID_ENCODING

    assert result_paths(index_dir, Term("filename", "universita")) == {
        "it/università_città.txt"
    }
    assert result_paths(index_dir, Phrase("filename", ["data", "integration"])) == {
        "en/data-integration.txt"
    }
    assert result_paths(index_dir, Phrase("content", ["urban", "mobility"])) == {
        "en/data_notes.txt",
        "en/urban-mobility.txt",
    }
    assert result_paths(
        index_dir, Phrase("content", ["integrazione", "dei", "dati"])
    ) == {
        "it/integrazione_dati.txt",
        "it/università_città.txt",
    }
    assert result_paths(index_dir, Term("filename", "notes")) == {
        "a/notes.txt",
        "b/notes.txt",
        "en/data_notes.txt",
    }
    assert result_paths(index_dir, Term("filename", "txt")) == set()

    index = open_dir(index_dir)
    try:
        with index.searcher() as searcher:
            documents = {
                result["path"]: dict(result)
                for result in searcher.search(Every(), limit=None)
            }
    finally:
        index.close()
    assert "misc/empty.txt" in documents
    assert documents["en/data_notes.txt"]["filename"] == "data_notes.txt"
    assert all("content" not in document for document in documents.values())


def test_index_remains_usable_without_the_source_files(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "example.txt").write_text("persistent content", encoding="utf-8")
    index_dir = tmp_path / "index"
    rebuild_index(source, index_dir)

    source.rename(tmp_path / "source-unavailable")

    assert result_paths(index_dir, Term("content", "persistent")) == {
        "example.txt"
    }


def test_accepts_utf8_bom_and_uppercase_txt_extension(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "CITTÀ.TXT").write_bytes(
        b"\xef\xbb\xbf" + "Mobilità urbana".encode("utf-8")
    )

    index_dir = tmp_path / "index"
    stats = rebuild_index(source, index_dir)

    assert stats.discovered_files == stats.indexed_files == 1
    assert stats.skipped_files == 0
    assert result_paths(index_dir, Term("filename", "citta")) == {"CITTÀ.TXT"}
    assert result_paths(index_dir, Term("content", "mobilita")) == {"CITTÀ.TXT"}
    assert result_paths(index_dir, Term("content", "\ufeffmobilita")) == set()


def test_ignores_symbolic_links(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "real.txt").write_text("real document", encoding="utf-8")
    target_dir = tmp_path / "external"
    target_dir.mkdir()
    (target_dir / "linked.txt").write_text("linked document", encoding="utf-8")
    try:
        (source / "file-link.txt").symlink_to(target_dir / "linked.txt")
        (source / "directory-link").symlink_to(target_dir, target_is_directory=True)
    except OSError as error:
        pytest.skip(f"I symlink non sono disponibili in questo ambiente: {error}")

    index_dir = tmp_path / "index"
    stats = rebuild_index(source, index_dir)

    assert stats.discovered_files == stats.indexed_files == 1
    assert result_paths(index_dir, Every()) == {"real.txt"}


def test_rejects_an_invalid_source_directory(tmp_path: Path) -> None:
    with pytest.raises(IndexBuildError, match="directory sorgente"):
        rebuild_index(tmp_path / "missing", tmp_path / "index")


def test_skips_and_logs_a_file_that_cannot_be_read(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "valid.txt").write_text("searchable", encoding="utf-8")
    unreadable = source / "unreadable.txt"
    unreadable.write_text("hidden", encoding="utf-8")
    real_read_bytes = Path.read_bytes

    def simulate_read_error(path: Path) -> bytes:
        if path == unreadable:
            raise PermissionError("simulated read failure")
        return real_read_bytes(path)

    monkeypatch.setattr(Path, "read_bytes", simulate_read_error)

    with caplog.at_level(logging.WARNING, logger="local_txt_search.indexing"):
        stats = rebuild_index(source, tmp_path / "index")

    assert stats.discovered_files == 2
    assert stats.indexed_files == stats.skipped_files == 1
    assert stats.skips[0].path == "unreadable.txt"
    assert stats.skips[0].reason is SkipReason.READ_ERROR
    assert "unreadable.txt" in caplog.text


def test_rejects_an_index_directory_that_contains_the_source(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "document.txt").write_text("content", encoding="utf-8")

    with pytest.raises(IndexBuildError, match="né contenerla"):
        rebuild_index(source, tmp_path)

    assert (source / "document.txt").exists()


def test_zero_valid_documents_preserves_the_previous_index(tmp_path: Path) -> None:
    valid_source = tmp_path / "valid"
    valid_source.mkdir()
    (valid_source / "old.txt").write_text("previous value", encoding="utf-8")
    index_dir = tmp_path / "index"
    rebuild_index(valid_source, index_dir)

    invalid_source = tmp_path / "invalid"
    invalid_source.mkdir()
    (invalid_source / "broken.txt").write_bytes(b"\xff")

    with pytest.raises(IndexBuildError, match="Nessun documento valido"):
        rebuild_index(invalid_source, index_dir)

    assert result_paths(index_dir, Term("content", "previous")) == {"old.txt"}


def test_publication_failure_restores_the_previous_index(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    old_source = tmp_path / "old-source"
    old_source.mkdir()
    (old_source / "old.txt").write_text("previous value", encoding="utf-8")
    index_dir = tmp_path / "index"
    rebuild_index(old_source, index_dir)

    new_source = tmp_path / "new-source"
    new_source.mkdir()
    (new_source / "new.txt").write_text("replacement value", encoding="utf-8")
    real_replace = os.replace
    replace_calls = 0

    def fail_new_index_publication(source: Path, destination: Path) -> None:
        nonlocal replace_calls
        replace_calls += 1
        if replace_calls == 2:
            raise OSError("simulated publication failure")
        real_replace(source, destination)

    monkeypatch.setattr(indexing.os, "replace", fail_new_index_publication)

    with pytest.raises(IndexBuildError, match="simulated publication failure"):
        rebuild_index(new_source, index_dir)

    assert replace_calls == 3
    assert result_paths(index_dir, Term("content", "previous")) == {"old.txt"}
    assert result_paths(index_dir, Term("content", "replacement")) == set()
