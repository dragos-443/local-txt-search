# src/

Contiene il package Python `local_txt_search`, il punto di ingresso CLI minimo e
l'API di indicizzazione persistente realizzata in M2.

La CLI è avviabile con `python -m local_txt_search --help`; i comandi applicativi
saranno collegati in M3. La funzione `local_txt_search.rebuild_index` costruisce
e pubblica in sicurezza l'indice Whoosh. Vedere `../docs/PRD.md` e
`../docs/ROADMAP.md`.
