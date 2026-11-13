"""Run three fresh-index rebuilds on each real-corpus size and retain raw data."""

from __future__ import annotations

import csv
import hashlib
import importlib.metadata
import json
import os
import platform
import statistics
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from shutil import copy2

from local_txt_search import rebuild_index


ROOT = Path(__file__).resolve().parents[1]
REAL = ROOT / "datasets" / "real"
INITIAL = REAL / "initial_50.json"
MANIFEST = REAL / "manifest.csv"
OUTPUT = ROOT / "evaluation" / "indexing_benchmark.json"


def git_metadata() -> dict[str, str | bool]:
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip())
    return {"commit": commit, "dirty": dirty}


def benchmark() -> dict:
    initial = json.loads(INITIAL.read_text(encoding="utf-8"))["entries"]
    with MANIFEST.open(encoding="utf-8", newline="") as stream:
        manifest = list(csv.DictReader(stream))
    if len(initial) != 50 or len(manifest) != 200:
        raise ValueError("Il benchmark richiede 50 file iniziali e 200 file totali")
    if {row["path"] for row in manifest} != {
        path.relative_to(REAL).as_posix() for path in REAL.rglob("*.txt")
    }:
        raise ValueError("Il manifest non coincide con i file del corpus")
    for row in manifest:
        payload = (REAL / row["path"]).read_bytes()
        if len(payload) != int(row["bytes"]) or hashlib.sha256(payload).hexdigest() != row["sha256"]:
            raise ValueError(f"File non coerente col manifest: {row['path']}")
    for entry in initial:
        if not any(row["path"] == entry["path"] and row["sha256"] == entry["sha256"]
                   and int(row["revision_id"]) == entry["revision_id"] for row in manifest):
            raise ValueError(f"File iniziale modificato: {entry['path']}")

    runs = []
    with tempfile.TemporaryDirectory(prefix="local-txt-search-benchmark-") as temporary:
        base = Path(temporary)
        source_50 = base / "initial_source"
        for entry in initial:
            destination = source_50 / entry["path"]
            destination.parent.mkdir(parents=True, exist_ok=True)
            copy2(REAL / entry["path"], destination)
        for trial in range(1, 4):
            for size, source in ((50, source_50), (200, REAL)):
                index_dir = base / f"index_{size}_{trial}"
                stats = rebuild_index(source, index_dir)
                index_bytes = sum(path.stat().st_size for path in index_dir.rglob("*") if path.is_file())
                run = {"corpus_files": size, "trial": trial, "duration_seconds": stats.duration_seconds,
                       "source_bytes": stats.indexed_bytes, "discovered_files": stats.discovered_files,
                       "indexed_files": stats.indexed_files, "skipped_files": stats.skipped_files,
                       "skips": [{"path": item.path, "reason": item.reason.value, "detail": item.detail}
                                 for item in stats.skips], "index_bytes": index_bytes}
                if stats.discovered_files != size or stats.indexed_files != size or stats.skipped_files:
                    raise ValueError(f"Run incompleto: {run}")
                runs.append(run)
                print(f"{size} file, prova {trial}: {stats.duration_seconds:.6f} s", flush=True)
    return {"schema_version": 1, "measured_at_utc": datetime.now(timezone.utc).isoformat(),
            "environment": {"python": sys.version, "whoosh": importlib.metadata.version("Whoosh"),
                            "os": platform.platform(), "processor": platform.processor(),
                            "machine": platform.machine(), "cpu_count": os.cpu_count(), **git_metadata()},
            "inputs": {"initial_reference_sha256": hashlib.sha256(INITIAL.read_bytes()).hexdigest(),
                       "manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
                       "indexing_code_sha256": hashlib.sha256((ROOT / "src" / "local_txt_search" / "indexing.py").read_bytes()).hexdigest()},
            "method": "50 file copiati prima delle misure; run alternati 50/200; indice nuovo per ogni prova; durata end-to-end di rebuild_index, esclusa la copia del sottoinsieme.",
            "runs": runs,
            "median_seconds": {str(size): statistics.median(run["duration_seconds"] for run in runs if run["corpus_files"] == size)
                               for size in (50, 200)}}


def main() -> None:
    result = benchmark()
    OUTPUT.write_bytes((json.dumps(result, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    print(f"Sei misure archiviate in {OUTPUT}")


if __name__ == "__main__":
    main()
