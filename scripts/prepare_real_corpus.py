"""Prepare the pinned bilingual Wikipedia corpus used by the project.

Use ``--append-new-pairs`` once to select 75 additional bilingual pairs from
``datasets/real/candidates.json``. A normal run checks the frozen first 50
files and rebuilds the additional files from their pinned revisions.
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
INITIAL_PATH = REAL_DIR / "initial_50.json"
CANDIDATES_PATH = REAL_DIR / "candidates.json"
SELECTION_PATH = REAL_DIR / "selection.json"
LICENSE = "CC BY-SA 4.0"
TRANSFORMATION = (
    "HTML introduttivo prima della prima sezione; elementi non testuali rimossi; "
    "spazi normalizzati; Unicode NFC; UTF-8"
)
USER_AGENT = "local-txt-search/0.1 (academic corpus preparation)"

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


def select_new_pairs(
    existing: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], dict[str, bytes], list[dict[str, str]]]:
    """Select exactly 15 valid pairs per thematic group, in candidate order."""
    groups = json.loads(CANDIDATES_PATH.read_text(encoding="utf-8"))["groups"]
    if len(groups) != 5:
        raise ValueError("Servono esattamente cinque gruppi di candidati")
    seen_ids = {
        language: {pair[language]["page_id"] for pair in existing}
        for language in ("it", "en")
    }
    seen_hashes = {
        row["sha256"] for row in read_manifest()
    }
    pairs = list(existing)
    payloads: dict[str, bytes] = {}
    decisions: list[dict[str, str]] = []
    for group in groups:
        accepted = 0
        for title in group["titles"]:
            if accepted == 15:
                decisions.append({"group": group["name"], "title": title, "outcome": "not_needed"})
                continue
            try:
                italian = current_pages("it", [title], True)[title]
                english_title = italian["langlinks"][0]["title"]
                english = current_pages("en", [english_title], False)[english_title]
                if italian["pageid"] in seen_ids["it"] or english["pageid"] in seen_ids["en"]:
                    raise ValueError("pagina già presente nel corpus")
                new_payloads = {
                    "it": extract_lead("it", italian["revisions"][0]["revid"]).encode("utf-8"),
                    "en": extract_lead("en", english["revisions"][0]["revid"]).encode("utf-8"),
                }
                hashes = {hashlib.sha256(data).hexdigest() for data in new_payloads.values()}
                if len(hashes) != 2 or hashes & seen_hashes:
                    raise ValueError("contenuto duplicato")
                pair_id = f"{len(pairs) + 1:02d}"
                pair: dict[str, Any] = {"pair_id": pair_id, "selection_group": group["name"]}
                for language, page in (("it", italian), ("en", english)):
                    path = f"{language}/{pair_id}_{slugify(page['title'])}.txt"
                    pair[language] = {
                        "path": path,
                        "title": page["title"],
                        "page_id": page["pageid"],
                        "revision_id": page["revisions"][0]["revid"],
                    }
                    payloads[path] = new_payloads[language]
                    seen_ids[language].add(page["pageid"])
                seen_hashes.update(hashes)
                pairs.append(pair)
                accepted += 1
                decisions.append({"group": group["name"], "title": title, "outcome": "accepted", "pair_id": pair_id})
                print(f"{pair_id}/100 {title} / {english['title']}", flush=True)
            except (ValueError, KeyError, urllib.error.HTTPError) as error:
                decisions.append({"group": group["name"], "title": title, "outcome": "rejected", "reason": str(error)})
                print(f"Scartata {title}: {error}", flush=True)
        if accepted != 15:
            raise ValueError(f"Gruppo {group['name']}: {accepted} coppie valide, ne servono 15")
    return pairs, payloads, decisions


def read_sources() -> list[dict[str, Any]]:
    try:
        document = json.loads(SOURCES_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise SystemExit(
            f"{SOURCES_PATH} non esiste"
        ) from error
    pairs = document.get("pairs")
    if not isinstance(pairs, list) or len(pairs) not in (25, 100):
        raise ValueError("sources.json deve contenere 25 o 100 coppie")
    if [pair["pair_id"] for pair in pairs] != [f"{n:02d}" for n in range(1, len(pairs) + 1)]:
        raise ValueError("ID delle coppie non consecutivi")
    return pairs


def read_manifest() -> list[dict[str, str]]:
    with MANIFEST_PATH.open(encoding="utf-8", newline="") as stream:
        return list(csv.DictReader(stream))


def initial_entries() -> dict[str, dict[str, Any]]:
    entries = json.loads(INITIAL_PATH.read_text(encoding="utf-8"))["entries"]
    if len(entries) != 50:
        raise ValueError("Il riferimento iniziale deve contenere 50 file")
    return {entry["path"]: entry for entry in entries}


def extract_lead(language: str, revision_id: int) -> str:
    parser = LeadParagraphParser()
    parser.feed(revision_html(language, revision_id))
    text = "\n\n".join(parser.paragraphs).strip()
    if not text:
        raise ValueError(f"Introduzione vuota per {language}:{revision_id}")
    return unicodedata.normalize("NFC", text) + "\n"


def permanent_url(language: str, revision_id: int) -> str:
    return f"https://{language}.wikipedia.org/w/index.php?oldid={revision_id}"


def generate(pairs: list[dict[str, Any]], preloaded: dict[str, bytes] | None = None) -> None:
    preloaded = preloaded or {}
    frozen = initial_entries()
    previous_manifest = {row["path"]: row for row in read_manifest()}
    if len(pairs) != 100:
        raise ValueError("Il corpus finale deve contenere 100 coppie")
    generated: list[tuple[dict[str, str | int], bytes]] = []
    expected_paths: set[str] = set()
    seen_hashes: set[str] = set()
    for pair in pairs:
        for language in ("it", "en"):
            source = pair[language]
            relative_path = source["path"]
            if relative_path in expected_paths:
                raise ValueError(f"Percorso duplicato: {relative_path}")
            expected_paths.add(relative_path)
            if relative_path in frozen:
                reference = frozen[relative_path]
                if reference["revision_id"] != source["revision_id"]:
                    raise ValueError(f"Revisione iniziale modificata: {relative_path}")
                payload = (REAL_DIR / relative_path).read_bytes()
                if hashlib.sha256(payload).hexdigest() != reference["sha256"]:
                    raise ValueError(f"File iniziale modificato: {relative_path}")
            else:
                payload = preloaded.get(relative_path)
                if payload is None:
                    payload = extract_lead(language, source["revision_id"]).encode("utf-8")
            if not payload.decode("utf-8").strip():
                raise ValueError(f"Testo vuoto: {relative_path}")
            digest = hashlib.sha256(payload).hexdigest()
            previous = previous_manifest.get(relative_path)
            if previous is not None and (previous["sha256"] != digest or int(previous["revision_id"]) != source["revision_id"]):
                raise ValueError(f"La revisione fissata non riproduce i byte archiviati: {relative_path}")
            if previous is not None and (REAL_DIR / relative_path).exists():
                actual_digest = hashlib.sha256((REAL_DIR / relative_path).read_bytes()).hexdigest()
                if actual_digest != previous["sha256"]:
                    raise ValueError(f"File esistente modificato: {relative_path}")
            if digest in seen_hashes:
                raise ValueError(f"Contenuto duplicato: {relative_path}")
            seen_hashes.add(digest)
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
                "sha256": digest,
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

    if len(expected_paths) != 200 or len(frozen.keys() & expected_paths) != 50:
        raise ValueError("Conteggi o riferimenti iniziali non validi")

    for row, payload in generated:
        destination = REAL_DIR / str(row["path"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        if str(row["path"]) not in frozen:
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
        "--append-new-pairs",
        action="store_true",
        help="seleziona 75 coppie nuove dai candidati e congela le loro revisioni",
    )
    arguments = parser.parse_args()
    existing = read_sources()
    if arguments.append_new_pairs:
        if len(existing) != 25:
            raise ValueError("L'aggiunta richiede il corpus iniziale di 25 coppie")
        pairs, payloads, decisions = select_new_pairs(existing)
        generate(pairs, payloads)
        SOURCES_PATH.write_bytes((json.dumps({"pairs": pairs}, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
        SELECTION_PATH.write_bytes((json.dumps({"decisions": decisions}, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    else:
        generate(existing)
        pairs = existing
    print(f"Corpus generato: {len(pairs) * 2} file; manifest: {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
