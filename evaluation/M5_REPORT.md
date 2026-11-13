# Esiti sperimentali — Milestone 5

Esecuzione del 13 novembre 2026. I dati grezzi sono in
`indexing_benchmark.json`, `real_judgments.json` e `real_results.json`.
Il manifest contiene 200 file (100 IT, 100 EN), 334249 byte di testo. I primi
50 file, identificati in `datasets/real/initial_50.json`, sono invariati e
totalizzano 90207 byte. `datasets/real/selection.json` documenta 75 nuove
coppie accettate in cinque gruppi, sette candidati scartati e nove non necessari.

## Indicizzazione

| File | Prova | Testi (byte) | Indice (byte) | Trovati/indicizzati/saltati | Durata (s) |
|---:|---:|---:|---:|---|---:|
| 50 | 1 | 90207 | 888815 | 50/50/0 | 1,423124 |
| 200 | 1 | 334249 | 2240926 | 200/200/0 | 3,492429 |
| 50 | 2 | 90207 | 888815 | 50/50/0 | 1,098719 |
| 200 | 2 | 334249 | 2240926 | 200/200/0 | 1,531093 |
| 50 | 3 | 90207 | 888815 | 50/50/0 | 0,465418 |
| 200 | 3 | 334249 | 2240926 | 200/200/0 | 0,854928 |

Mediane: **1,098719 s** per 50 file e **1,531093 s** per 200 file. Nessun
file saltato. I run sono stati alternati nello stesso processo, con un indice
nuovo per prova; la copia del sottoinsieme da 50 file è fuori dal tempo misurato.
Ambiente: Python 3.14.3, Whoosh 2.7.4, Windows 11, CPU Intel64 Family 6
Model 140 Stepping 1 (8 CPU logiche). Hash dei dati e del codice usato sono
nell'output JSON.

## Ricerca sui 50 file iniziali

Le dieci query hanno 500 giudizi testuali fissati prima dell'interrogazione.
Per ciascuna, FP=0 e FN=0; la macro media di precision, recall e F1 è
**1,000** per tutte e tre. I valori per query, gli insiemi completi dei
rilevanti e quelli restituiti sono in `real_results.json`. I 13 casi del corpus
sintetico M4 sono documentati separatamente in `FUNCTIONAL_REPORT.md`.

## Limiti

I giudizi sono basati sulla corrispondenza lessicale: il risultato perfetto
non misura la pertinenza semantica né il recupero di parafrasi o flessioni.
I tempi diminuiscono nei run successivi, compatibilmente con effetti di cache;
hardware, sistema operativo e processi concorrenti possono influire. I due
corpus hanno dimensione modesta e testi omogenei, perciò il confronto non
dimostra scalabilità generale.
