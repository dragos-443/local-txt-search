# ROADMAP — Dal progetto alla consegna

**Stato del progetto:** M0 e M1 completate; bootstrap installabile, corpus e
oracolo disponibili. I comandi applicativi iniziano con M2.
**Scadenza del corso:** 13 novembre 2026, ore 18:00.

## Dipendenze

```text
M0 Fondazioni
  -> M1 Preparazione corpus e oracoli
  -> M2 Indicizzazione
  -> M3 Parser + CLI
  -> M4 Test funzionali
  -> M5 Misurazione sperimentale
  -> M6 Relazione finale
  -> M7 GitHub e consegna
```

| Milestone | Obiettivo | Deliverable principale | Condizione di completamento | Stato |
|---|---|---|---|---|
| **M0** | Definire architettura, scope e bootstrap | Package installabile, CLI minima, README, PRD, roadmap, piano sperimentale | Installazione e verifiche riproducibili | **Completata** |
| **M1** | Preparare corpus e casi attesi | Corpus sintetico, corpus pubblico, manifest, matrice query | Dataset e attesi verificati | **Completata** |
| **M2** | Implementare la costruzione indice | Scanner, reader, analyzer, schema, index writer | Scansione e indice persistente funzionanti | Da fare |
| **M3** | Implementare ricerca e CLI | Parser validato, comandi `index` e `search` | Query base, AND e phrase disponibili | Da fare |
| **M4** | Verificare correttezza | Test automatici, error handling | Query e casi limite conformi agli attesi | Da fare |
| **M5** | Misurare le prestazioni | Esecuzioni ripetute, risultati grezzi | Conteggi e tempi reali archiviati | Da fare |
| **M6** | Redigere la relazione | Relazione con interpretazione dei dati | Ogni affermazione empirica è sostenuta da una misura | Da fare |
| **M7** | Pubblicare e consegnare | Repo GitHub, README finale, relazione inviata | Link funzionante e invio completato | Da fare |

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

## M2 — Indicizzazione [da fare]

- Implementare scansione ricorsiva e identificazione mediante percorso relativo.
- Leggere file UTF-8 / UTF-8 BOM; saltare con log i file non validi.
- Definire schema Whoosh con `filename` e `content`, analyzer distinti e posizioni.
- Implementare full rebuild persistente con protezione del precedente indice su fallimento.
- Conteggiare file individuati, indicizzati e saltati; misurare tempo end-to-end.

**Gate:** l'indice può essere riaperto e usato senza rileggere i documenti.

## M3 — Parser e CLI [da fare]

- Realizzare `index` con directory di input e percorso indice opzionale.
- Realizzare `search` interattivo e uscita tramite `exit`.
- Applicare grammatica concordata (`nome`/`contenuto`, AND implicito, phrase tra virgolette).
- Gestire errori di sintassi senza interrompere la sessione.

**Gate:** ricerca per termine, multi-termine e frase funziona sui due campi.

## M4 — Test funzionali [da fare]

- Verificare insieme esatto dei risultati attesi, non soltanto i primi risultati.
- Testare accenti, maiuscole, stopword, ordine, assenza di stemming e separatori nei filename.
- Testare file vuoti, nomi duplicati, encoding non UTF-8, directory non valida e query malformate.
- Correggere i bug e mantenere traccia degli esiti.

**Gate:** suite di test riproducibile e problemi residui espliciti.

## M5 — Valutazione delle prestazioni [da fare]

- Congelare versione del corpus reale e configurazione dell'ambiente.
- Eseguire **tre ricostruzioni complete** sul medesimo corpus.
- Registrare tempi singoli, mediana, file trovati, indicizzati, saltati e dimensione dell'indice.
- Annotare limiti: caching, hardware, piccolo dataset, formati omogenei.

**Gate:** risultati sperimentali reali riproducibili, con input e metadati identificabili.

## M6 — Report [da fare]

- Inquadrare problema, architettura, analyzer e trade-off.
- Presentare dataset, query e attesi/ottenuti.
- Inserire conteggi e tempi **osservati**, non valori di esempio.
- Discutere casi falliti, scelte progettuali e limiti dell'esperimento.
- Inserire URL GitHub aggiornato.

**Gate:** relazione completa e verificabile con i file di valutazione.

## M7 — Pubblicazione e consegna [da fare]

- Ripulire repository da indici generati, file temporanei e contenuti non ridistribuibili.
- Validare README, istruzioni di installazione e comandi.
- Pubblicare su GitHub, verificare URL e accessibilità.
- Inviare relazione attraverso il canale indicato dal docente entro scadenza.

**Gate:** progetto consultabile e consegna completata.

## Priorità

La consegna universitaria ha precedenza su estensioni. Se il tempo è limitato: completare `index`, `search`, query test e relazione; considerare documenti aggiuntivi e perfezionamenti solo dopo che l'MVP è affidabile.
