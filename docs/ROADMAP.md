# ROADMAP — Dal progetto alla consegna

**Stato del progetto:** M0–M5 completate; bootstrap, corpus di 200 testi,
oracolo, indicizzazione persistente, parser, CLI, verifica funzionale e
valutazione sperimentale disponibili.
**Scadenza del corso:** 13 novembre 2026, ore 18:00.

## Dipendenze

```text
M0 Fondazioni
  -> M1 Preparazione corpus e oracoli
  -> M2 Indicizzazione
  -> M3 Parser + CLI
  -> M4 Test funzionali
  -> M5 Ampliamento corpus e valutazione sperimentale
  -> M6 Relazione finale
  -> M7 GitHub e consegna
```

| Milestone | Obiettivo | Deliverable principale | Condizione di completamento | Stato |
|---|---|---|---|---|
| **M0** | Definire architettura, scope e bootstrap | Package installabile, CLI minima, README, PRD, roadmap, piano sperimentale | Installazione e verifiche riproducibili | **Completata** |
| **M1** | Preparare corpus e casi attesi | Corpus sintetico, corpus pubblico, manifest, matrice query | Dataset e attesi verificati | **Completata** |
| **M2** | Implementare la costruzione indice | Scanner, reader, analyzer, schema, index writer | Scansione e indice persistente funzionanti | **Completata** |
| **M3** | Implementare ricerca e CLI | Parser validato, comandi `index` e `search` | Query base, AND e phrase disponibili | **Completata** |
| **M4** | Verificare correttezza | Test automatici, error handling | Query e casi limite conformi agli attesi | **Completata** |
| **M5** | Ampliare il corpus e valutare indicizzazione e ricerca | 200 testi reali, giudizi sui 50 iniziali, tempi e metriche | Corpus verificato, tre misure per dimensione, precision, recall e F1 archiviati | **Completata** |
| **M6** | Redigere la relazione | Relazione con email, metodo di costruzione del dataset e interpretazione dei dati | Ogni dato empirico è rintracciabile nei file di valutazione | Da fare |
| **M7** | Pubblicare e consegnare | Repo GitHub, README finale, relazione inviata | Link verificato e checklist della relazione completa prima dell'invio | Da fare |

## M0 — Fondazioni [completata]

- Fissare nome e obiettivo del progetto.
- Documentare requisiti, scelte degli analyzer, CLI e criteri di successo.
- Organizzare il layout `src/` e rendere installabile il package senza anticipare l'implementazione applicativa.
- Fissare le dipendenze, verificare Whoosh su Python 3.14 e fornire una CLI minima avviabile.
- Inizializzare il repository Git locale e ignorare ambiente, cache e indici generati.

**Gate superato:** un altro sviluppatore può creare l'ambiente, installare il package, avviare la guida CLI ed eseguire i test seguendo il README.

## M1 — Corpus e oracoli [completata]

- Selezionare **circa 50** testi pubblici, con obiettivo 25 IT/25 EN, verificando permessi di riuso.
- Convertire a `.txt` e UTF-8, se necessario, registrando metodi di trasformazione e provenienza.
- Preparare un piccolo corpus controllato e casi limite (stopword, accenti, path omonimi, errore di codifica).
- Definire almeno 10–12 query e, prima di eseguirle, l'insieme di file attesi.
- Aggiungere manifest con licenza, URL, SHA-256 e dimensione, senza dati o risultati falsamente dichiarati.

**Gate:** dataset reale disponibile e oracolo di test sintetico indipendente dal codice.

**Gate superato:** 12 documenti sintetici validi e un caso non UTF-8, 50
introduzioni Wikipedia IT/EN con revisioni e hash congelati, e 13 query con
insiemi attesi indipendenti dal motore. I controlli automatici verificano
conteggi, codifica, manifest e riferimenti dell'oracolo.

## M2 — Indicizzazione [completata]

- Implementare scansione ricorsiva e identificazione mediante percorso relativo.
- Leggere file UTF-8 / UTF-8 BOM; saltare con log i file non validi.
- Definire schema Whoosh con `filename` e `content`, analyzer distinti e posizioni.
- Implementare full rebuild persistente con protezione del precedente indice su fallimento.
- Conteggiare file individuati, indicizzati e saltati; misurare tempo end-to-end.

**Gate:** l'indice può essere riaperto e usato senza rileggere i documenti.

**Gate superato:** la scansione deterministica gestisce ricorsione, percorsi
relativi, UTF-8/BOM, scarti e symlink; lo schema mantiene analyzer distinti e
posizioni. La ricostruzione verifica il nuovo indice prima della pubblicazione e
ripristina quello precedente se la sostituzione fallisce. I test riaprono e
interrogano l'indice persistente anche dopo la rimozione della sorgente.

## M3 — Parser e CLI [completata]

- Realizzare `index` con directory di input e percorso indice opzionale.
- Realizzare `search` interattivo e uscita tramite `exit`.
- Applicare grammatica concordata (`nome`/`contenuto`, AND implicito, phrase tra virgolette).
- Gestire errori di sintassi senza interrompere la sessione.

**Gate:** ricerca per termine, multi-termine e frase funziona sui due campi.

**Gate superato:** `index` espone la ricostruzione persistente con statistiche e
avvisi; `search` mantiene aperto l'indice e gestisce `help`, `exit`, EOF ed errori
di sintassi senza interrompere la sessione. Il parser usa gli analyzer dello
schema e costruisce soltanto query `Term`, `And` e `Phrase`. Tutte le 13 query
dell'oracolo restituiscono l'insieme completo dei percorsi attesi.

## M4 — Test funzionali [completata]

- Mantenere come regressione il confronto completo delle 13 query con gli attesi.
- Testare accenti, maiuscole, stopword, ordine, assenza di stemming e separatori nei filename.
- Testare file vuoti, nomi duplicati, encoding non UTF-8, directory non valida e query malformate.
- Correggere i bug e mantenere traccia degli esiti.

**Gate:** suite di test riproducibile e problemi residui espliciti.

**Gate superato:** tutte le 13 query coincidono con gli insiemi completi attesi
e gli esiti strutturati sono conservati in `evaluation/functional_results.json`.
La suite copre inoltre analyzer, casi limite di indicizzazione, query malformate
e recupero della CLI: 62 test superati e un test dei symlink saltato perché
l'ambiente Windows di verifica non consente di crearli. Il limite è registrato
nel resoconto funzionale.

## M5 — Ampliamento corpus e valutazione sperimentale [completata]

- Conservare le 25 coppie IT/EN già preparate, con percorsi e revisioni invariati, e aggiungerne 75: il corpus reale finale deve contenere **200 file `.txt`**, 100 IT e 100 EN. Adeguare `scripts/prepare_real_corpus.py`, oggi vincolato a 25 coppie, e documentare i criteri di selezione delle nuove voci.
- Congelare le revisioni delle nuove fonti e aggiornare `sources.json` e `manifest.csv`. Verificare per tutti i 200 file provenienza, licenza, metodo di estrazione e trasformazione, UTF-8, dimensione in byte, SHA-256 e assenza di duplicati; conservare un riferimento identificabile ai 50 file iniziali.
- Eseguire **tre ricostruzioni complete** sui 50 file iniziali e **tre** sui 200 file, usando lo stesso ambiente e un indice nuovo per ogni prova. Conservare i tempi di ciascun run e la mediana per dimensione del corpus, insieme a byte dei testi, file trovati, indicizzati e saltati, dimensione dell'indice, cause degli scarti, versioni software e caratteristiche della macchina.
- Definire almeno 10 query sul sottoinsieme reale dei **50 file iniziali**, con termini e frasi nei campi nome e contenuto. Per ogni query stabilire il criterio di rilevanza e revisionare tutti e 50 i file **prima di esaminare i risultati del motore**; conservare gli insiemi completi dei documenti rilevanti e dei risultati restituiti.
- Calcolare per ogni query veri positivi, falsi positivi, falsi negativi, **precision, recall e F1**, poi le medie sulle query. Usare tutti i risultati della ricerca, non soltanto i primi 10 mostrati dalla CLI. Mantenere distinta questa valutazione sui testi reali dai 13 test funzionali sul corpus sintetico.
- Annotare limiti e possibili effetti di caching, hardware, dimensione ancora contenuta del corpus e omogeneità dei testi; non presentare il confronto fra 50 e 200 file come prova generale di scalabilità.

**Gate:** corpus di 200 file verificato e riproducibile; sei misure di indicizzazione con dati grezzi e mediane archiviate; giudizi di rilevanza completi sui 50 file iniziali e precision, recall e F1 tracciabili per ciascuna query e in media.

**Gate superato:** 200 file (100 IT/100 EN) verificati, con i 50 iniziali
invariati; sei run e due mediane in `evaluation/indexing_benchmark.json`;
500 giudizi e insiemi completi in `evaluation/real_judgments.json`, con metriche
per query e medie in `evaluation/real_results.json`. La suite conta 70 test
superati e un test dei symlink saltato per il privilegio Windows mancante.

## M6 — Report [da fare]

- Inserire nome e **indirizzo di posta elettronica dello studente** per consentire al docente di contattarlo senza ambiguità.
- Inquadrare problema, architettura, analyzer e trade-off.
- Spiegare come sono stati selezionati i documenti, fissate le revisioni, estratti e convertiti i testi in `.txt`, e verificati licenze, codifica, dimensioni e hash; indicare quantità dei due corpus reali usati nelle prove e procedura di riproduzione.
- Presentare le query reali, i criteri e gli insiemi di rilevanza, i risultati ottenuti e le metriche **precision, recall e F1** per query e in media. Riportare separatamente l'esito dei test funzionali sintetici.
- Inserire conteggi, dimensioni e tempi di indicizzazione **osservati** sui corpus da 50 e 200 file, con i tre run e la mediana per ciascuno, non valori di esempio.
- Discutere casi falliti, scelte progettuali e limiti dell'esperimento, soprattutto quelli che incidono sulla recall e sull'interpretazione dei tempi.
- Inserire URL GitHub aggiornato.

**Gate:** relazione completa, con email e metodo di costruzione del dataset; ogni numero e affermazione empirica è rintracciabile nei manifest, nei giudizi di rilevanza o nei risultati archiviati in `evaluation/`.

## M7 — Pubblicazione e consegna [da fare]

- Ripulire repository da indici generati, file temporanei e contenuti non ridistribuibili.
- Validare README, istruzioni di installazione e comandi.
- Pubblicare su GitHub, verificare URL e accessibilità.
- Verificare nella relazione la presenza di email, descrizione della costruzione dei `.txt`, conteggi e tempi di indicizzazione, precision, recall, F1 e riferimenti alle evidenze della valutazione.
- Inviare relazione attraverso il canale indicato dal docente entro scadenza.

**Gate:** progetto consultabile, checklist della relazione completa e consegna effettuata.

## Priorità

La consegna universitaria ha precedenza sulle estensioni facoltative. `index`, `search` e i test funzionali sono già disponibili: prima di ulteriori funzionalità, completare l'ampliamento e la documentazione del corpus, le misure sui 50 e 200 file, i giudizi di rilevanza, precision, recall e F1, poi la relazione con email e risultati verificabili. Non dichiarare completate misure o metriche prima di averle effettivamente raccolte.
