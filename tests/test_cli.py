from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from local_txt_search import rebuild_index


ROOT = Path(__file__).resolve().parents[1]
SYNTHETIC_DIR = ROOT / "datasets" / "synthetic"


def run_cli(
    *arguments: str, input_text: str | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "local_txt_search", *arguments],
        input=input_text,
        check=False,
        capture_output=True,
        text=True,
    )


@pytest.fixture
def synthetic_index(tmp_path: Path) -> Path:
    index_dir = tmp_path / "index"
    rebuild_index(SYNTHETIC_DIR, index_dir)
    return index_dir


def test_help_describes_available_commands() -> None:
    result = run_cli("--help")

    assert result.returncode == 0
    assert "index" in result.stdout
    assert "search" in result.stdout
    assert "non ancora" not in result.stdout


def test_index_command_builds_index_and_prints_statistics(tmp_path: Path) -> None:
    index_dir = tmp_path / "index"

    result = run_cli(
        "index",
        "--source",
        str(SYNTHETIC_DIR),
        "--index",
        str(index_dir),
    )

    assert result.returncode == 0
    assert index_dir.is_dir()
    assert "File individuati: 13" in result.stdout
    assert "File indicizzati: 12" in result.stdout
    assert "File saltati: 1" in result.stdout
    assert "Durata:" in result.stdout
    assert "invalid_encoding.txt" in result.stderr


def test_index_requires_source_and_reports_build_errors(tmp_path: Path) -> None:
    missing_argument = run_cli("index")
    invalid_source = run_cli(
        "index",
        "--source",
        str(tmp_path / "missing"),
        "--index",
        str(tmp_path / "index"),
    )

    assert missing_argument.returncode == 2
    assert "--source" in missing_argument.stderr
    assert invalid_source.returncode == 1
    assert "Errore di indicizzazione" in invalid_source.stderr


def test_search_session_supports_help_recovers_from_syntax_error_and_exits(
    synthetic_index: Path,
) -> None:
    result = run_cli(
        "search",
        "--index",
        str(synthetic_index),
        input_text="help\nnome data*\nnome notes\nexit\n",
    )

    assert result.returncode == 0
    assert result.stdout.count("Query supportate:") == 2
    assert "Errore di sintassi" in result.stderr
    assert "Risultati totali: 3" in result.stdout
    assert "a/notes.txt" in result.stdout
    assert "b/notes.txt" in result.stdout
    assert "en/data_notes.txt" in result.stdout


def test_search_accepts_eof_and_uses_persistent_index(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "document.txt").write_text("persistent value", encoding="utf-8")
    index_dir = tmp_path / "index"
    rebuild_index(source, index_dir)
    source.rename(tmp_path / "source-unavailable")

    result = run_cli(
        "search",
        "--index",
        str(index_dir),
        input_text="contenuto persistent\n",
    )

    assert result.returncode == 0
    assert "Risultati totali: 1" in result.stdout
    assert "document.txt" in result.stdout


def test_search_prints_total_but_limits_display_to_ten_hits(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    for number in range(1, 12):
        (source / f"document-{number:02}.txt").write_text("same", encoding="utf-8")
    index_dir = tmp_path / "index"
    rebuild_index(source, index_dir)

    result = run_cli(
        "search",
        "--index",
        str(index_dir),
        input_text="contenuto same\nexit\n",
    )

    assert result.returncode == 0
    assert "Risultati totali: 11" in result.stdout
    assert result.stdout.count("score:") == 10
    assert "document-10.txt" in result.stdout
    assert "document-11.txt" not in result.stdout


def test_search_reports_a_missing_index(tmp_path: Path) -> None:
    result = run_cli("search", "--index", str(tmp_path / "missing"), input_text="")

    assert result.returncode == 1
    assert "Errore dell'indice" in result.stderr
