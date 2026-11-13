# local-txt-search

Progetto per l'**Homework 3 — Ingegneria dei dati (A.A. 2026/27)**.

**Stato:** M0–M5 completate. Il package Python è installabile, la costruzione
persistente dell'indice e la ricerca CLI sono disponibili, e i test funzionali
sono documentati. La valutazione M5 è in `evaluation/`.

## Obiettivo

Motore di ricerca locale per file `.txt`, basato su **Python + Whoosh**, con indicizzazione del nome e del contenuto, ricerca da console e supporto alle phrase query.

## Requisiti

- Python 3.14 (verificato con Python 3.14.3).
- Git.

Whoosh è bloccato alla versione 2.7.4. La compatibilità con Python 3.14 viene
controllata con la prova descritta sotto.

## Installazione su PowerShell

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

L'attivazione è facoltativa: i comandi seguenti possono essere eseguiti anche
specificando direttamente `.\.venv\Scripts\python.exe`.

## Uso della CLI

```powershell
python -m local_txt_search --help
python -m local_txt_search index --source datasets/real
python -m local_txt_search search
```

Entrambi i comandi usano `.local_index` per impostazione predefinita. È possibile
scegliere un'altra destinazione con `--index <directory>`.

Durante la ricerca sono accettate query come:

```text
nome robotica
nome data notes
nome "data integration"
contenuto mobilità sostenibile
contenuto "urban mobility"
```

I termini multipli sono combinati con AND. `help` mostra la grammatica ed `exit`
termina la sessione. Ogni query cerca in un solo campo; operatori avanzati,
wildcard e combinazioni fra termini liberi e frasi non sono supportati.

Per eseguire la suite completa:

```powershell
python -m pytest
```

Per rieseguire le 13 query dell'oracolo e aggiornare gli esiti osservati:

```powershell
python scripts/evaluate_functional.py
```

Il comando scrive `evaluation/functional_results.json` e restituisce un codice
di errore se almeno un insieme di risultati non coincide con l'atteso.

## Valutazione M5

Il corpus reale contiene 200 introduzioni Wikipedia, 100 italiane e 100
inglesi. `datasets/real/initial_50.json` identifica i 50 file iniziali,
usati come sottoinsieme fisso per le dieci query reali e per le misure a 50
file. Provenienza, licenza, trasformazione, revisioni e hash sono in
`datasets/real/manifest.csv`; i criteri di selezione sono nel README del corpus.

Per verificare i giudizi congelati, ricalcolare le metriche e ripetere le sei
misure di indicizzazione:

```powershell
python scripts/evaluate_real.py
python scripts/benchmark_indexing.py
```

I risultati archiviati sono `evaluation/real_judgments.json`,
`evaluation/real_results.json` e `evaluation/indexing_benchmark.json`.
Le mediane osservate sono 1,099 s sui 50 file e 1,531 s sui 200;
precision, recall e F1 macro delle dieci query sono 1,000. Il riepilogo è in
`evaluation/M5_REPORT.md`. I giudizi usano corrispondenza testuale, non
pertinenza semantica.

## API di indicizzazione

M2 espone la ricostruzione completa tramite Python:

```python
from pathlib import Path

from local_txt_search import rebuild_index

stats = rebuild_index(Path("datasets/real"), Path(".local_index"))
print(stats)
```

La funzione scansiona ricorsivamente i `.txt`, salta e registra i file non
leggibili come UTF-8 e pubblica il nuovo indice soltanto dopo averlo verificato.
Un eventuale indice precedente viene conservato se la ricostruzione fallisce.

## Documentazione

1. Leggere [`docs/PRD.md`](docs/PRD.md) per requisiti e scelte concordate.
2. Seguire [`docs/ROADMAP.md`](docs/ROADMAP.md) nell'ordine delle milestone.
3. Usare [`docs/EVALUATION_PLAN.md`](docs/EVALUATION_PLAN.md) per progettare esperimenti e relazione.

Il codice di bootstrap è in `src/local_txt_search/` e i suoi test sono in
`tests/`. I corpus sono in `datasets/`, mentre `evaluation/queries.json`
contiene le query e gli attesi definiti prima del motore di ricerca.

## Consegna

Il corso richiede una relazione con URL della repository, motivazioni degli analyzer, numero di file e tempi di indicizzazione, e query testate. Scadenza indicata: **13 novembre 2026, ore 18:00**.

## Note di progetto

- Il corpus reale comprende **200 documenti pubblici** (100 italiani e 100
  inglesi) derivati da revisioni Wikipedia dichiarate nel manifest.
- Il corpus sintetico comprende 12 documenti validi, una fixture non UTF-8 e
  13 query con insiemi completi di risultati attesi.
- Le 13 query dell'oracolo sono eseguite automaticamente contro l'indice del
  corpus sintetico e confrontate con l'insieme completo dei percorsi attesi;
  gli esiti M4 sono conservati in `evaluation/functional_results.json`.
- Il repository Git è locale; pubblicazione e verifica del collegamento GitHub
  sono previste in M7.
