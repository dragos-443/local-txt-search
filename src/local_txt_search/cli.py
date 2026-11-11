"""Command-line interface for index construction and interactive search."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from .indexing import IndexBuildError, rebuild_index
from .searching import QuerySyntaxError, SearchIndexError, SearchSession


DEFAULT_INDEX_DIR = Path(".local_index")

_SEARCH_HELP = """Query supportate:
  nome <termine1> [termine2 ...]
  nome "<frase>"
  contenuto <termine1> [termine2 ...]
  contenuto "<frase>"
I termini multipli sono combinati con AND. Digita 'exit' per uscire."""


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(
        prog="python -m local_txt_search",
        description="Ricerca locale in file .txt basata su Whoosh.",
        epilog="Usare '<comando> --help' per le opzioni specifiche.",
    )
    subparsers = parser.add_subparsers(dest="command", metavar="{index,search}")

    index_parser = subparsers.add_parser(
        "index",
        help="Costruisce da zero l'indice persistente.",
    )
    index_parser.add_argument(
        "--source",
        required=True,
        type=Path,
        metavar="DIRECTORY",
        help="Directory da scandire ricorsivamente per file .txt.",
    )
    index_parser.add_argument(
        "--index",
        dest="index_dir",
        type=Path,
        default=DEFAULT_INDEX_DIR,
        metavar="DIRECTORY",
        help="Directory dell'indice (predefinita: .local_index).",
    )

    search_parser = subparsers.add_parser(
        "search",
        help="Avvia una sessione di ricerca interattiva.",
    )
    search_parser.add_argument(
        "--index",
        dest="index_dir",
        type=Path,
        default=DEFAULT_INDEX_DIR,
        metavar="DIRECTORY",
        help="Directory dell'indice (predefinita: .local_index).",
    )
    return parser


def _run_index(source: Path, index_dir: Path) -> int:
    try:
        stats = rebuild_index(source, index_dir)
    except IndexBuildError as error:
        print(f"Errore di indicizzazione: {error}", file=sys.stderr)
        return 1

    print(f"Indice creato in: {index_dir}")
    print(f"File individuati: {stats.discovered_files}")
    print(f"File indicizzati: {stats.indexed_files}")
    print(f"File saltati: {stats.skipped_files}")
    print(f"Byte indicizzati: {stats.indexed_bytes}")
    print(f"Durata: {stats.duration_seconds:.3f} s")
    return 0


def _print_hits(hits) -> None:
    print(f"Risultati totali: {len(hits)}")
    for position, hit in enumerate(hits[:10], start=1):
        print(
            f"{position}. {hit.filename} | percorso: {hit.path} | "
            f"score: {hit.score:.6f}"
        )


def _run_search(index_dir: Path) -> int:
    try:
        session = SearchSession(index_dir)
    except SearchIndexError as error:
        print(f"Errore dell'indice: {error}", file=sys.stderr)
        return 1

    print(_SEARCH_HELP)
    with session:
        while True:
            try:
                query_text = input("query> ")
            except EOFError:
                print()
                return 0
            except KeyboardInterrupt:
                print()
                return 0

            command = query_text.strip().casefold()
            if command == "exit":
                return 0
            if command == "help":
                print(_SEARCH_HELP)
                continue

            try:
                hits = session.search(query_text)
            except QuerySyntaxError as error:
                print(f"Errore di sintassi: {error}", file=sys.stderr)
                continue
            except SearchIndexError as error:
                print(f"Errore dell'indice: {error}", file=sys.stderr)
                return 1

            _print_hits(hits)


def main(argv: Sequence[str] | None = None) -> int:
    """Run the application CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "index":
        return _run_index(args.source, args.index_dir)
    return _run_search(args.index_dir)
