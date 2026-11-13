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
Il riepilogo dell'esecuzione M4 è in `FUNCTIONAL_REPORT.md`. Le tre misure di
indicizzazione saranno aggiunte in M5 seguendo
[`../docs/EVALUATION_PLAN.md`](../docs/EVALUATION_PLAN.md).
