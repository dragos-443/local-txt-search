# PRD — Product Requirements Document

**Progetto:** `local-txt-search`  
**Corso:** Ingegneria dei dati — Homework 3 (individuale), 2026/2027  
**Stato:** M0–M5 completate; indicizzazione, ricerca CLI e valutazione sperimentale disponibili
**Ultima revisione:** 13 novembre 2026

## 1. Problema

Consentire la ricerca efficiente fra documenti `.txt` locali, distinguendo le ricerche nel **nome del file** da quelle nel **contenuto**. La soluzione rende espliciti concetti del corso: indice invertito, tokenizzazione, normalizzazione e indici posizionali per phrase query.

## 2. Requisiti richiesti dall'Homework 3

- Programma che indicizza i `.txt` in una directory.
- Due campi indicizzati, **nome** e **contenuto**, ciascuno con analyzer appropriato.
- Programma che riceve query dalla console e stampa i risultati; devono essere possibili phrase query.
- Circa 10 query di prova.
- Relazione con URL GitHub, analyzer motivati, numero di file, tempi di indicizzazione e query utilizzate.

**Nota:** tutte le altre scelte riportate di seguito sono nostre decisioni architetturali, non prescrizioni esplicite del docente.

## 3. Obiettivi del prodotto

1. Indicizzare ricorsivamente file `.txt` locali con Whoosh.
2. Ricercare separatamente per nome o contenuto tramite CLI.
3. Gestire italiano e inglese con analyzer indipendenti dalla lingua.
4. Fornire comportamento deterministico e testabile per termini, AND e frasi.
5. Salvare l'indice su disco e riutilizzarlo senza reindicizzare ad ogni ricerca.
6. Registrare statistiche e produrre una relazione basata su risultati realmente misurati.

## 4. Ambito MVP

### Incluso

- **Stack:** Python + Whoosh.
- **Scansione:** directory e sottodirectory, file con estensione `.txt` senza distinzione delle maiuscole.
- **Identità:** percorso relativo come ID univoco del documento, per distinguere file omonimi.
- **Schema logico:** `path` (identificatore), `filename` e `content` (ricercabili).
- **Indice:** un indice Whoosh persistente, con due campi indicizzati distintamente. La scelta di un solo indice fisico va spiegata nella relazione in riferimento alla richiesta di due indici/campi.
- **Codifica:** UTF-8, incluso UTF-8 con BOM. File non UTF-8 saltati e segnalati, non decodificati in modo approssimativo.
- **Errori:** problemi su singoli file registrati senza arrestare la scansione; errori di configurazione o scrittura indice bloccanti.
- **File vuoti:** accettati come documenti con contenuto vuoto.
- **Symlink:** non seguire collegamenti simbolici nella versione iniziale.
- **Ricostruzione:** esplicita e completa; preparare l'indice nuovo separatamente e mantenere quello precedente in caso di fallimento.

### Escluso

Interfaccia Web, scraping, indicizzazione PDF/DOCX, aggiornamenti incrementali, OR/NOT/wildcard/fuzzy, ricerca cross-field, traduzione, riconoscimento automatico della lingua, cloud, API HTTP, modello ML e ottimizzazioni premature.

## 5. Analyzer previsti

| Campo | Operazioni | Motivazione |
|---|---|---|
| `filename` | Rimuovere `.txt` **solo dalla rappresentazione da indicizzare**; separare spazi, `_`, `-` e punteggiatura utile; lowercase; normalizzare accenti | Nomi brevi con separatori tecnici, più efficaci come sequenze di token |
| `content` | Tokenizzare parole; lowercase; normalizzare accenti | Testo in italiano/inglese, ricerca tollerante a maiuscole e diacritici |

**Per entrambi:** mantenere stopword, non applicare stemming, preservare le posizioni dei token. La normalizzazione deve essere identica in indicizzazione e in ricerca. Nella milestone tecnica andranno verificati gli effetti su apostrofi, Unicode e tokenizzazione del nome.

**Trade-off:** più affidabilità e leggibilità delle phrase query, ma minore recall morfologica rispetto allo stemming e minore precisione ortografica dopo la rimozione degli accenti.

## 6. Contratto CLI (realizzato in M3)

Sono disponibili due comandi:

```text
python -m local_txt_search index --source <directory> [--index <percorso>]
python -m local_txt_search search [--index <percorso>]
```

Il comando `index` conta documenti scoperti/indicizzati/saltati, costruisce il
nuovo indice e mostra durata e avvisi. `search` apre l'indice esistente una sola
volta e legge ripetutamente query dalla console, con `help` ed `exit`. Il percorso
predefinito condiviso è `.local_index`.

### Grammatica di ricerca

```text
nome <termine>
nome <termine1> <termine2> ...         # AND implicito
nome "<frase>"                         # adiacenza e ordine
contenuto <termine>
contenuto <termine1> <termine2> ...    # AND implicito
contenuto "<frase>"                    # adiacenza e ordine
```

- Campo obbligatorio: `nome` o `contenuto`.
- Nessun supporto iniziale per combinazioni miste di frasi e termini liberi o operatori avanzati.
- Errori leggibili per campo sconosciuto, query vuota, virgolette sbilanciate, sintassi non ammessa.
- Ricerca case- e accent-insensitive, senza traduzione e senza match per sottostringhe.
- Risultati: numero totale, primi 10 documenti, `filename`, percorso relativo e score; BM25F predefinito di Whoosh come ordinamento, senza attribuire allo score significato probabilistico.

## 7. Dati sperimentali

- **Corpus A (sintetico):** 12 documenti costruiti a mano e un caso di errore
  di codifica separato; include testo IT/EN, accenti, underscore, trattini, file
  omonimi, frasi e file vuoti.
- **Corpus B (reale):** 200 introduzioni Wikipedia `.txt` (100 IT + 100 EN) con
  revisioni congelate; fonte, licenza, trasformazioni, percorso, bytes e hash
  SHA-256 sono registrati nel manifest. I primi 50 file restano identificati
  separatamente per la valutazione di ricerca e il confronto dei tempi.
- Le 13 query e gli insiemi attesi sintetici sono in `evaluation/queries.json`;
  gli esiti M4 sono in `evaluation/functional_results.json`. Query, giudizi e
  risultati reali M5 e le sei misure sono in file separati in `evaluation/`.

## 8. Qualità, verificabilità e limiti

- Risultati attesi documentati prima dell'esecuzione dei test.
- Nessuna misura presentata come osservata prima di aver eseguito il programma.
- Test ripetibili e chiari messaggi d'errore.
- Indice generato escluso dal controllo versione.
- Documentare le versioni di Python, Whoosh e l'ambiente di misura.

## 9. Criteri di accettazione finali

- [x] `index` scansiona ricorsivamente e costruisce un indice persistente.
- [x] Nomi e contenuti sono interrogabili separatamente.
- [x] I due analyzer sono implementati e motivati.
- [x] Query semplici, AND e per frase restituiscono l'insieme corretto di documenti.
- [x] File non UTF-8 vengono saltati e segnalati.
- [x] Test funzionali documentati e superati, salvo problemi dichiarati.
- [x] Tre misurazioni sui 50 file e tre sui 200, con mediane e dati grezzi registrati.
- [ ] Relazione completata con URL GitHub e dati realmente osservati.

## 10. Vincoli temporali

Consegna della relazione indicata nel testo dell'Homework: **13 novembre 2026, ore 18:00**. La roadmap deve privilegiare l'MVP richiesto prima di qualsiasi estensione.
