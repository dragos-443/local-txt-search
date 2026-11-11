"""Command-line interface for the project bootstrap."""

from __future__ import annotations

import argparse
from collections.abc import Sequence


_NOT_IMPLEMENTED = (
    "Il comando '{command}' non è ancora disponibile: "
    "sarà implementato nella milestone M3."
)


def build_parser() -> argparse.ArgumentParser:
    """Create the command-line parser."""
    parser = argparse.ArgumentParser(
        prog="python -m local_txt_search",
        description="Ricerca locale in file .txt basata su Whoosh.",
        epilog=(
            "M2 fornisce l'API Python di indicizzazione; "
            "i comandi index e search saranno implementati nella milestone M3."
        ),
    )
    subparsers = parser.add_subparsers(dest="command", metavar="{index,search}")

    subparsers.add_parser(
        "index",
        help="Comando di indicizzazione pianificato per M3 (non ancora disponibile).",
    )
    subparsers.add_parser(
        "search",
        help="Ricerca interattiva pianificata per M3 (non ancora disponibile).",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the bootstrap CLI."""
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command is None:
        parser.print_help()
        return 0

    parser.error(_NOT_IMPLEMENTED.format(command=args.command))
    return 2
