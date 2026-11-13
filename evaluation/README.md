# evaluation/

`queries.json` contiene l'oracolo definito in M1: query e insiemi completi di
percorsi attesi sul corpus sintetico.

`functional_results.json` contiene gli insiemi osservati e l'esito delle 13
query, generati con:

```powershell
.\.venv\Scripts\python.exe scripts\evaluate_functional.py
```

Il comando ricostruisce l'indice in una directory temporanea e termina con
codice diverso da zero se almeno un insieme osservato differisce dall'atteso.
Il riepilogo dell'esecuzione M4 è in `FUNCTIONAL_REPORT.md`.

M5 usa file distinti: `real_queries.json` per le dieci query, `real_judgments.json`
per i 500 giudizi fissati prima delle ricerche, `real_results.json` per tutti i
risultati e le metriche, e `indexing_benchmark.json` per i sei run e le mediane.
La procedura e le definizioni sono in
[`../docs/EVALUATION_PLAN.md`](../docs/EVALUATION_PLAN.md). Il riepilogo dei
risultati osservati e dei limiti è in `M5_REPORT.md`.

```powershell
.\.venv\Scripts\python.exe scripts\create_real_judgments.py  # solo prima di congelare i giudizi
.\.venv\Scripts\python.exe scripts\evaluate_real.py
.\.venv\Scripts\python.exe scripts\benchmark_indexing.py
```

La creazione dei giudizi rifiuta di sovrascrivere il file già congelato.
