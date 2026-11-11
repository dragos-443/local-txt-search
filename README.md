# local-txt-search

Progetto per l'**Homework 3 — Ingegneria dei dati (A.A. 2026/27)**.

**Stato:** M0 completata. Il package Python è installabile e la CLI minima è
avviabile; indicizzazione, ricerca, dataset, risultati e report conclusivo saranno
realizzati nelle milestone successive.

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

## Verifica del bootstrap

```powershell
python -m local_txt_search --help
python -m pytest
```

La guida elenca `index` e `search`, ma in M0 entrambi sono segnaposto espliciti.
La suite include anche una prova di compatibilità che crea su disco un indice
Whoosh, inserisce un documento e lo ritrova con una query. L'implementazione dei
comandi appartiene rispettivamente a M2 e M3.

## Documentazione

1. Leggere [`docs/PRD.md`](docs/PRD.md) per requisiti e scelte concordate.
2. Seguire [`docs/ROADMAP.md`](docs/ROADMAP.md) nell'ordine delle milestone.
3. Usare [`docs/EVALUATION_PLAN.md`](docs/EVALUATION_PLAN.md) per progettare esperimenti e relazione.

Il codice di bootstrap è in `src/local_txt_search/` e i suoi test sono in
`tests/`. Le directory `datasets/`, `evaluation/` e `report/` contengono ancora
solo README segnaposto; non sono stati creati o scaricati corpus.

## Consegna

Il corso richiede una relazione con URL della repository, motivazioni degli analyzer, numero di file e tempi di indicizzazione, e query testate. Scadenza indicata: **13 novembre 2026, ore 18:00**.

## Note di progetto

- Il target sperimentale concordato è un corpus reale di **circa 50 documenti pubblici** (25 italiani, 25 inglesi), da selezionare in una milestone successiva.
- Sono previsti anche documenti sintetici controllati per verificare la correttezza; **non sono inclusi in questo scaffold**.
- I comandi applicativi descritti nel PRD sono ancora una specifica futura. La
  CLI di M0 ne segnala esplicitamente la mancata implementazione.
- Il repository Git è locale; pubblicazione e verifica del collegamento GitHub
  sono previste in M7.
