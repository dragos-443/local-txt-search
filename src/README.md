# src/

Contiene il package Python `local_txt_search`, il punto di ingresso CLI e i
moduli per indicizzazione e ricerca.

La CLI è avviabile con `python -m local_txt_search --help`. Il comando `index`
costruisce e pubblica in sicurezza l'indice Whoosh; `search` apre una sessione
interattiva con parser validato. Vedere `../docs/PRD.md` e `../docs/ROADMAP.md`
per il contratto applicativo.
