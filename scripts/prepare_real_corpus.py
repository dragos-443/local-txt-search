"""Prepare the pinned bilingual Wikipedia corpus used by the project.

Run with ``--update-revisions`` only when intentionally selecting newer page
revisions.  A normal run rebuilds every text file from the revision IDs stored
in ``datasets/real/sources.json``.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
REAL_DIR = ROOT / "datasets" / "real"
SOURCES_PATH = REAL_DIR / "sources.json"
MANIFEST_PATH = REAL_DIR / "manifest.csv"
LICENSE = "CC BY-SA 4.0"
TRANSFORMATION = (
    "HTML introduttivo prima della prima sezione; elementi non testuali rimossi; "
    "spazi normalizzati; Unicode NFC; UTF-8"
)
USER_AGENT = "local-txt-search/0.1 (academic corpus preparation)"

ITALIAN_TITLES = [
    "Informatica",
    "Banca dati",
    "Motore di ricerca",
    "Algoritmo",
    "Internet",
    "World Wide Web",
    "Intelligenza artificiale",
    "Apprendimento automatico",
    "Elaborazione del linguaggio naturale",
    "Statistica",
    "Probabilità",
    "Matematica",
    "Fisica",
    "Chimica",
    "Biologia",
    "Astronomia",
    "Terra",
    "Energia",
    "Ecologia",
    "Clima",
    "Cambiamento climatico",
    "Mobilità sostenibile",
    "Trasporto pubblico",
    "Città",
    "Robotica",
]


class LeadParagraphParser(HTMLParser):
    """Collect top-level prose paragraphs before the first section heading."""

    ignored_tags = {"style", "script", "table", "figure", "sup", "noscript"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.paragraphs: list[str] = []
        self._parts: list[str] | None = None
        self._ignored_depth = 0
        self._finished = False

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if self._finished:
            return
        if tag == "h2":
            self._finished = True
            return
        if tag in self.ignored_tags:
            self._ignored_depth += 1
            return
        if tag == "p" and self._ignored_depth == 0 and self._parts is None:
            self._parts = []
        elif tag == "br" and self._parts is not None and self._ignored_depth == 0:
            self._parts.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in self.ignored_tags and self._ignored_depth:
            self._ignored_depth -= 1
            return
        if tag == "p" and self._parts is not None and self._ignored_depth == 0:
            paragraph = normalize_space("".join(self._parts))
            if paragraph:
                self.paragraphs.append(paragraph)
            self._parts = None

    def handle_data(self, data: str) -> None:
        if self._parts is not None and self._ignored_depth == 0:
            self._parts.append(data)


def normalize_space(value: str) -> str:
    return re.sub(r"\s+", " ", unicodedata.normalize("NFC", value)).strip()


def api_request(
    language: str, parameters: dict[str, Any], attempts: int = 5
) -> dict[str, Any]:
    query = urllib.parse.urlencode(
        {"format": "json", "formatversion": 2, **parameters}
    )
    request = urllib.request.Request(
        f"https://{language}.wikipedia.org/w/api.php?{query}",
        headers={"User-Agent": USER_AGENT},
    )
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            if error.code != 429 or attempt == attempts - 1:
                raise
            retry_after = error.headers.get("Retry-After")
            time.sleep(float(retry_after) if retry_after else 2 ** (attempt + 1))
        except (urllib.error.URLError, TimeoutError):
            if attempt == attempts - 1:
                raise
            time.sleep(2 ** (attempt + 1))
    raise AssertionError("unreachable")


def revision_html(language: str, revision_id: int) -> str:
    try:
        response = api_request(
            language,
            {"action": "parse", "oldid": revision_id, "prop": "text|revid"},
            attempts=1,
        )
        parsed = response.get("parse")
        if not parsed or parsed.get("revid") != revision_id:
            raise ValueError(f"Revisione {language}:{revision_id} non recuperabile")
        return parsed["text"]
    except urllib.error.HTTPError as error:
        if error.code != 429:
            raise

    # The exact-revision render endpoint is equivalent parser output and keeps
    # corpus preparation usable when Wikimedia rate-limits the Action API.
    query = urllib.parse.urlencode({"oldid": revision_id, "action": "render"})
    request = urllib.request.Request(
        f"https://{language}.wikipedia.org/w/index.php?{query}",
        headers={"User-Agent": USER_AGENT},
    )
    for attempt in range(5):
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return response.read().decode("utf-8")
        except (urllib.error.URLError, TimeoutError):
            if attempt == 4:
                raise
            time.sleep(2 ** (attempt + 1))
    raise AssertionError("unreachable")


def slugify(title: str) -> str:
    ascii_title = unicodedata.normalize("NFKD", title).encode("ascii", "ignore").decode()
    slug = re.sub(r"[^a-z0-9]+", "_", ascii_title.lower()).strip("_")
    if not slug:
        raise ValueError(f"Impossibile creare il nome file per {title!r}")
    return slug


def current_pages(
    language: str, titles: list[str], include_english_links: bool
) -> dict[str, dict[str, Any]]:
    properties = "revisions|langlinks" if include_english_links else "revisions"
    parameters: dict[str, Any] = {
        "action": "query",
        "prop": properties,
        "rvprop": "ids",
        "redirects": 1,
        "titles": "|".join(titles),
    }
    if include_english_links:
        parameters.update({"lllang": "en", "lllimit": "max"})
    response = api_request(language, parameters)
    query = response["query"]
    aliases = {title: title for title in titles}
    for normalization in query.get("normalized", []):
        for original, resolved in list(aliases.items()):
            if resolved == normalization["from"]:
                aliases[original] = normalization["to"]
    for redirect in query.get("redirects", []):
        for original, resolved in list(aliases.items()):
            if resolved == redirect["from"]:
                aliases[original] = redirect["to"]

    pages_by_title = {page["title"]: page for page in query["pages"]}
    result: dict[str, dict[str, Any]] = {}
    for original, resolved in aliases.items():
        page = pages_by_title.get(resolved)
        if not page or "missing" in page:
            raise ValueError(f"Voce {language}:{original!r} non trovata")
        if include_english_links and not page.get("langlinks"):
            raise ValueError(f"Voce inglese collegata a it:{original!r} non trovata")
        result[original] = page
    return result


def update_sources() -> list[dict[str, Any]]:
    previous_paths: dict[tuple[str, str], str] = {}
    if SOURCES_PATH.exists():
        for pair in read_sources():
            for language in ("it", "en"):
                source = pair[language]
                previous_paths[(pair["pair_id"], language)] = source["path"]

    italian_pages = current_pages("it", ITALIAN_TITLES, include_english_links=True)
    english_titles = [
        italian_pages[title]["langlinks"][0]["title"] for title in ITALIAN_TITLES
    ]
    english_pages = current_pages("en", english_titles, include_english_links=False)

    pairs: list[dict[str, Any]] = []
    for position, requested_title in enumerate(ITALIAN_TITLES, start=1):
        pair_id = f"{position:02d}"
        italian = italian_pages[requested_title]
        english_title = italian["langlinks"][0]["title"]
        english = english_pages[english_title]
        pair: dict[str, Any] = {"pair_id": pair_id}
        for language, page in (("it", italian), ("en", english)):
            path = previous_paths.get(
                (pair_id, language),
                f"{language}/{pair_id}_{slugify(page['title'])}.txt",
            )
            pair[language] = {
                "path": path,
                "title": page["title"],
                "page_id": page["pageid"],
                "revision_id": page["revisions"][0]["revid"],
            }
        pairs.append(pair)

    SOURCES_PATH.write_text(
        json.dumps({"pairs": pairs}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return pairs


def read_sources() -> list[dict[str, Any]]:
    try:
        document = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise SystemExit(
            f"{SOURCES_PATH} non esiste: eseguire prima con --update-revisions"
        ) from error
    pairs = document.get("pairs")
    if not isinstance(pairs, list) or len(pairs) != 25:
        raise ValueError("sources.json deve contenere esattamente 25 coppie")
    return pairs


def extract_lead(language: str, revision_id: int) -> str:
    parser = LeadParagraphParser()
    parser.feed(revision_html(language, revision_id))
    text = "\n\n".join(parser.paragraphs).strip()
    if not text:
        raise ValueError(f"Introduzione vuota per {language}:{revision_id}")
    return unicodedata.normalize("NFC", text) + "\n"


def permanent_url(language: str, revision_id: int) -> str:
    return f"https://{language}.wikipedia.org/w/index.php?oldid={revision_id}"


def generate(pairs: list[dict[str, Any]]) -> None:
    generated: list[tuple[dict[str, str | int], bytes]] = []
    expected_paths: set[str] = set()
    for pair in pairs:
        for language in ("it", "en"):
            source = pair[language]
            relative_path = source["path"]
            if relative_path in expected_paths:
                raise ValueError(f"Percorso duplicato: {relative_path}")
            expected_paths.add(relative_path)
            text = extract_lead(language, source["revision_id"])
            payload = text.encode("utf-8")
            row: dict[str, str | int] = {
                "path": relative_path,
                "language": language,
                "pair_id": pair["pair_id"],
                "title": source["title"],
                "page_id": source["page_id"],
                "revision_id": source["revision_id"],
                "permanent_url": permanent_url(language, source["revision_id"]),
                "license": LICENSE,
                "transformation": TRANSFORMATION,
                "bytes": len(payload),
                "sha256": hashlib.sha256(payload).hexdigest(),
            }
            generated.append((row, payload))

    existing = {
        path.relative_to(REAL_DIR).as_posix()
        for language in ("it", "en")
        for path in (REAL_DIR / language).glob("*.txt")
    }
    stale = existing - expected_paths
    if stale:
        raise ValueError(f"File reali non registrati da rimuovere manualmente: {sorted(stale)}")

    for row, payload in generated:
        destination = REAL_DIR / str(row["path"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(payload)

    fieldnames = [
        "path",
        "language",
        "pair_id",
        "title",
        "page_id",
        "revision_id",
        "permanent_url",
        "license",
        "transformation",
        "bytes",
        "sha256",
    ]
    with MANIFEST_PATH.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(row for row, _ in generated)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--update-revisions",
        action="store_true",
        help="seleziona le revisioni correnti e aggiorna esplicitamente sources.json",
    )
    arguments = parser.parse_args()
    pairs = update_sources() if arguments.update_revisions else read_sources()
    generate(pairs)
    print(f"Corpus generato: {len(pairs) * 2} file; manifest: {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
