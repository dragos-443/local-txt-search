"""Persistent Whoosh index construction."""

from __future__ import annotations

import logging
import os
import shutil
import tempfile
import time
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from whoosh.analysis import CharsetFilter, LowercaseFilter, RegexTokenizer
from whoosh.fields import ID, TEXT, Schema
from whoosh.index import create_in, open_dir
from whoosh.support.charset import accent_map


LOGGER = logging.getLogger(__name__)


class IndexBuildError(RuntimeError):
    """Raised when a complete index cannot be built and published."""


class SkipReason(StrEnum):
    """Stable reason codes for files omitted from an index."""

    INVALID_ENCODING = "invalid_encoding"
    READ_ERROR = "read_error"


@dataclass(frozen=True, slots=True)
class SkippedFile:
    """A discovered text file that could not be indexed."""

    path: str
    reason: SkipReason
    detail: str


@dataclass(frozen=True, slots=True)
class IndexStats:
    """Measurements collected during a successful full rebuild."""

    discovered_files: int
    indexed_files: int
    skipped_files: int
    indexed_bytes: int
    duration_seconds: float
    skips: tuple[SkippedFile, ...]


def filename_analyzer():
    """Build the analyzer used for file names.

    Underscores are separators here, unlike in Whoosh's default tokenizer.
    Positions are preserved because no filter removes tokens.
    """

    return (
        RegexTokenizer(r"[^\W_]+")
        | LowercaseFilter()
        | CharsetFilter(accent_map)
    )


def content_analyzer():
    """Build the language-independent analyzer used for document text."""

    return RegexTokenizer() | LowercaseFilter() | CharsetFilter(accent_map)


def index_schema() -> Schema:
    """Return the schema shared by index construction and search."""

    return Schema(
        path=ID(stored=True, unique=True),
        filename=TEXT(stored=True, phrase=True, analyzer=filename_analyzer()),
        content=TEXT(stored=False, phrase=True, analyzer=content_analyzer()),
    )


def _scan_text_files(source: Path):
    """Yield non-symlink text files recursively in deterministic order."""

    def raise_scan_error(error: OSError) -> None:
        raise error

    for root, directory_names, file_names in os.walk(
        source, topdown=True, onerror=raise_scan_error, followlinks=False
    ):
        root_path = Path(root)
        directory_names[:] = sorted(
            (
                name
                for name in directory_names
                if not (root_path / name).is_symlink()
            ),
            key=lambda name: (name.casefold(), name),
        )
        for name in sorted(file_names, key=lambda item: (item.casefold(), item)):
            path = root_path / name
            if path.suffix.lower() == ".txt" and not path.is_symlink():
                yield path


def _read_document(path: Path, relative_path: str) -> tuple[str, bytes] | SkippedFile:
    try:
        payload = path.read_bytes()
    except OSError as error:
        return SkippedFile(relative_path, SkipReason.READ_ERROR, str(error))

    try:
        text = payload.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        return SkippedFile(relative_path, SkipReason.INVALID_ENCODING, str(error))

    return text, payload


def _verify_index(index_dir: Path, expected_documents: int) -> None:
    index = open_dir(index_dir)
    try:
        with index.searcher() as searcher:
            actual_documents = searcher.doc_count_all()
    finally:
        index.close()

    if actual_documents != expected_documents:
        raise IndexBuildError(
            "Verifica dell'indice fallita: "
            f"attesi {expected_documents} documenti, trovati {actual_documents}."
        )


def _publish_index(staging_dir: Path, index_dir: Path) -> None:
    """Publish staging_dir and restore the previous directory on failure."""

    if index_dir.exists() and not index_dir.is_dir():
        raise IndexBuildError(
            f"Il percorso dell'indice esiste ma non è una directory: {index_dir}"
        )

    backup_dir: Path | None = None
    if index_dir.exists():
        backup_dir = Path(
            tempfile.mkdtemp(
                prefix=f".{index_dir.name}.backup-", dir=index_dir.parent
            )
        )
        backup_dir.rmdir()
        os.replace(index_dir, backup_dir)

    try:
        os.replace(staging_dir, index_dir)
    except BaseException:
        if backup_dir is not None:
            try:
                os.replace(backup_dir, index_dir)
            except BaseException as restore_error:
                raise IndexBuildError(
                    "Pubblicazione fallita e impossibile ripristinare "
                    f"l'indice precedente da {backup_dir}."
                ) from restore_error
        raise

    if backup_dir is not None:
        try:
            shutil.rmtree(backup_dir)
        except OSError as error:
            LOGGER.warning(
                "Nuovo indice pubblicato, ma il backup non è stato rimosso: %s — %s",
                backup_dir,
                error,
            )


def rebuild_index(source: Path, index_dir: Path) -> IndexStats:
    """Build and atomically publish a complete persistent index.

    Individual read and decoding failures are recorded as skips. Configuration,
    traversal, writing, verification, and publication failures abort the rebuild.
    The destination is only touched after the new index has been verified.
    """

    started_at = time.monotonic()
    source = Path(source)
    index_dir = Path(index_dir)

    if source.is_symlink() or not source.is_dir():
        raise IndexBuildError(
            f"La directory sorgente non esiste o non è valida: {source}"
        )

    resolved_source = source.resolve()
    resolved_index = index_dir.resolve(strict=False)
    if resolved_index == resolved_source or resolved_index in resolved_source.parents:
        raise IndexBuildError(
            "La directory dell'indice non può coincidere con la sorgente "
            "né contenerla."
        )

    index_parent = index_dir.parent
    try:
        index_parent.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        raise IndexBuildError(
            f"Impossibile preparare la directory dell'indice: {index_parent}"
        ) from error

    staging_dir = Path(
        tempfile.mkdtemp(prefix=f".{index_dir.name}.build-", dir=index_parent)
    )
    discovered_files = 0
    indexed_files = 0
    indexed_bytes = 0
    skips: list[SkippedFile] = []
    index = None
    writer = None

    try:
        index = create_in(staging_dir, index_schema())
        writer = index.writer()

        for path in _scan_text_files(source):
            discovered_files += 1
            relative_path = path.relative_to(source).as_posix()
            document = _read_document(path, relative_path)
            if isinstance(document, SkippedFile):
                skips.append(document)
                LOGGER.warning(
                    "File saltato (%s): %s — %s",
                    document.reason,
                    document.path,
                    document.detail,
                )
                continue

            content, payload = document
            writer.add_document(
                path=relative_path,
                filename=path.name[:-4],
                _stored_filename=path.name,
                content=content,
            )
            indexed_files += 1
            indexed_bytes += len(payload)

        if indexed_files == 0:
            writer.cancel()
            writer = None
            raise IndexBuildError(
                "Nessun documento valido da indicizzare; l'indice precedente "
                "è stato conservato."
            )

        writer.commit()
        writer = None
        index.close()
        index = None

        _verify_index(staging_dir, indexed_files)
        _publish_index(staging_dir, index_dir)
    except IndexBuildError:
        raise
    except OSError as error:
        raise IndexBuildError(f"Ricostruzione dell'indice fallita: {error}") from error
    except Exception as error:
        raise IndexBuildError("Ricostruzione dell'indice fallita.") from error
    finally:
        if writer is not None:
            try:
                writer.cancel()
            except Exception:
                pass
        if index is not None:
            index.close()
        if staging_dir.exists():
            shutil.rmtree(staging_dir, ignore_errors=True)

    duration_seconds = time.monotonic() - started_at
    return IndexStats(
        discovered_files=discovered_files,
        indexed_files=indexed_files,
        skipped_files=len(skips),
        indexed_bytes=indexed_bytes,
        duration_seconds=duration_seconds,
        skips=tuple(skips),
    )
