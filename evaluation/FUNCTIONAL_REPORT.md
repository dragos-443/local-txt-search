# Esiti funzionali — Milestone 4

Esecuzione effettuata l'11 novembre 2026 sul corpus sintetico versionato.

## Riproduzione

Da un ambiente in cui il progetto è installato con le dipendenze di sviluppo:

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe scripts\evaluate_functional.py
```

Il primo comando ha prodotto **62 test superati e 1 saltato**. Il secondo ha
confrontato gli insiemi completi dei risultati con l'oracolo congelato e ha
prodotto **13 casi superati su 13**. Attesi, osservati ed esito di ogni query
sono conservati in `functional_results.json`.

## Problemi residui e limiti

Non sono state osservate discrepanze funzionali. Il test che verifica di non
seguire i collegamenti simbolici è stato saltato perché l'account Windows usato
per questa esecuzione non dispone del privilegio necessario a creare symlink.
Il comportamento resta coperto automaticamente negli ambienti che consentono
di crearli.

Tempi e prestazioni di indicizzazione non fanno parte di questi esiti e saranno
misurati nella milestone 5.
