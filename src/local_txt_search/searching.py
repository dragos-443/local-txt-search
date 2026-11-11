"""Validated query parsing and persistent-index search."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from types import TracebackType

from whoosh.index import IndexError as WhooshIndexError
from whoosh.index import open_dir
from whoosh.query import And, Phrase, Query, Term


_FIELD_NAMES = {"nome": "filename", "contenuto": "content"}
_ADVANCED_SYNTAX = re.compile(r"[*?:()\[\]{}^~\\]")
_PHRASE = re.compile(r'"([^"]*)"')


class QuerySyntaxError(ValueError):
    """Raised when a user query does not follow the supported grammar."""


class SearchIndexError(RuntimeError):
    """Raised when the persistent index cannot be opened or searched."""


@dataclass(frozen=True, slots=True)
class SearchHit:
    """A stored document returned by a search."""

    filename: str
    path: str
    score: float


def parse_query(query_text: str, schema) -> Query:
    """Parse the small, explicit query language documented by the project."""

    text = query_text.strip()
    if not text:
        raise QuerySyntaxError("la query è vuota.")

    parts = text.split(maxsplit=1)
    field_label = parts[0]
    field = _FIELD_NAMES.get(field_label.casefold())
    if field is None:
        raise QuerySyntaxError(
            f"campo '{field_label}' non valido; usare 'nome' o 'contenuto'."
        )

    expression = parts[1] if len(parts) == 2 else ""
    expression = expression.strip()
    if not expression:
        raise QuerySyntaxError(f"manca il testo da cercare nel campo '{field_label}'.")

    phrase_match = _PHRASE.fullmatch(expression)
    if '"' in expression and phrase_match is None:
        raise QuerySyntaxError(
            "le virgolette devono racchiudere l'intera espressione di ricerca."
        )

    is_phrase = phrase_match is not None
    value = phrase_match.group(1) if phrase_match else expression
    if not is_phrase and _ADVANCED_SYNTAX.search(value):
        raise QuerySyntaxError("la sintassi di ricerca avanzata non è supportata.")

    analyzer = schema[field].analyzer
    terms = [token.text for token in analyzer(value)]
    if not terms:
        raise QuerySyntaxError("la query non contiene termini ricercabili.")

    if len(terms) == 1:
        return Term(field, terms[0])
    if is_phrase:
        return Phrase(field, terms)
    return And([Term(field, term) for term in terms])


class SearchSession:
    """Keep one Whoosh index and searcher open for an interactive session."""

    def __init__(self, index_dir: Path) -> None:
        self.index_dir = Path(index_dir)
        try:
            self._index = open_dir(self.index_dir)
            missing_fields = {"path", "filename", "content"} - set(
                self._index.schema.names()
            )
            if missing_fields:
                raise SearchIndexError(
                    "L'indice non contiene i campi richiesti: "
                    + ", ".join(sorted(missing_fields))
                    + "."
                )
            self._searcher = self._index.searcher()
        except SearchIndexError:
            if hasattr(self, "_index"):
                self._index.close()
            raise
        except (OSError, WhooshIndexError) as error:
            if hasattr(self, "_index"):
                self._index.close()
            raise SearchIndexError(
                f"Impossibile aprire l'indice in '{self.index_dir}': {error}"
            ) from error

    @property
    def schema(self):
        """Return the schema whose analyzers define query normalization."""

        return self._index.schema

    def search(self, query_text: str) -> tuple[SearchHit, ...]:
        """Parse and execute a query, returning all hits deterministically."""

        query = parse_query(query_text, self.schema)
        try:
            results = self._searcher.search(query, limit=None)
            hits = [
                SearchHit(
                    filename=result["filename"],
                    path=result["path"],
                    score=float(result.score),
                )
                for result in results
            ]
        except (OSError, WhooshIndexError, KeyError) as error:
            raise SearchIndexError(f"Errore durante la lettura dell'indice: {error}") from error

        return tuple(sorted(hits, key=lambda hit: (-hit.score, hit.path)))

    def close(self) -> None:
        """Release the searcher and its underlying index."""

        self._searcher.close()
        self._index.close()

    def __enter__(self) -> SearchSession:
        return self

    def __exit__(
        self,
        exception_type: type[BaseException] | None,
        exception: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
