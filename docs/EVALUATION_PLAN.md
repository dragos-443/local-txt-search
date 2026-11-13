# Piano di valutazione

Gli esiti funzionali M4 e i risultati sperimentali M5 sono archiviati
separatamente in `evaluation/`.

## 1. Obiettivi

- **RQ1:** la ricerca rispetta le regole degli analyzer e la grammatica delle query?
- **RQ2:** quanti file vengono indicizzati e quanto tempo richiede la costruzione dell'indice su corpus pubblici reali da 50 e 200 testi?
- **RQ3:** con quale precision, recall e F1 le query recuperano corrispondenze lessicali sui 50 testi iniziali?

## 2. Corpus preparati

| Corpus | Scopo | Dimensione obiettivo | Stato |
|---|---|---|---|
| Sintetico | Correttezza di query e gestione errori | 12 `.txt` validi + 1 non UTF-8 | Preparato in M1 |
| Reale iniziale | Tempi e giudizi lessicali | 50 `.txt`: 25 IT + 25 EN | Congelato in M1 |
| Reale esteso | Tempi di indicizzazione | 200 `.txt`: 100 IT + 100 EN | Preparato in M5 |

Il corpus reale usa introduzioni Wikipedia con revisioni congelate. Provenienza,
licenza CC BY-SA 4.0, trasformazioni, dimensioni e SHA-256 sono registrati in
`datasets/real/manifest.csv`; `sources.json` consente la rigenerazione dalle
revisioni esatte. `datasets/real/initial_50.json` identifica il sottoinsieme
iniziale per percorso, revisione e hash.

## 3. Matrice di casi funzionali

Le 13 query e i documenti attesi sono stati fissati in
`evaluation/queries.json` **prima dell'implementazione della ricerca**. La
matrice copre:

| Caso | Esempio di query | Verifica |
|---|---|---|
| Termini nel nome | `nome universita` | Accenti normalizzati |
| Nome in maiuscolo | `nome CITTÀ` | Lowercase |
| AND nel nome | `nome data notes` | Entrambi i token, qualsiasi ordine |
| Frase nel nome | `nome "data integration"` | Termini consecutivi |
| Frase inesistente | `nome "integration data"` | Assenza di falso positivo |
| Frase nel contenuto | `contenuto "urban mobility"` | Ricerca EN |
| Stopword nella frase | `contenuto "integrazione dei dati"` | Conservazione stopword |
| AND nel contenuto | `contenuto data sources` | Termini in posizioni diverse |
| Frase con accenti | `contenuto "citta sostenibili"` | Accenti + posizioni |
| Separazione dei campi | `nome "trasporto pubblico"` | Non cercare nel contenuto |
| Assenza stemming | `contenuto runs` | Non unificare automaticamente con `running` |
| Nome duplicato | `nome notes` | Distinguere percorsi differenti |

Gli ID attesi sono percorsi relativi al corpus sintetico. File vuoto e codifica
non UTF-8 sono fixture del corpus. M4 ha verificato tutte le 13 query e ha esteso
la copertura a errori di sintassi, normalizzazione, analyzer e recupero della
sessione CLI.

**Misura di correttezza:** per ogni query confrontare l'insieme completo dei percorsi restituiti con l'insieme atteso. Un test è superato solo se i due insiemi coincidono.

**Esito M4:** 13 casi su 13 superati. Attesi, osservati ed esiti sono registrati
in `evaluation/functional_results.json`; ambiente, comandi e limite relativo ai
symlink sono descritti in `evaluation/FUNCTIONAL_REPORT.md`.

## 4. Giudizi e metriche su testi reali

`evaluation/real_queries.json` definisce dieci query nei due campi. Prima di
eseguire il motore, `scripts/create_real_judgments.py` legge tutti i 50 file
iniziali e registra in `real_judgments.json` una decisione per ciascuna delle
500 coppie query-documento. Il criterio è testuale: parole intere, senza
distinguere maiuscole e accenti; `_` e `-` separano parole nei nomi; AND non
richiede ordine, mentre una frase richiede parole consecutive nell'ordine dato.
I giudizi sono prodotti da un'ispezione testuale indipendente dal codice Whoosh.

`scripts/evaluate_real.py` verifica completezza e hash dei giudizi, costruisce
un indice dei soli 50 file iniziali e conserva tutti i percorsi restituiti in
`real_results.json`. Per ogni query: TP = rilevanti restituiti, FP = restituiti
non rilevanti, FN = rilevanti non restituiti; precision = TP/(TP+FP), recall =
TP/(TP+FN), F1 = 2PR/(P+R). La precision e F1 valgono zero se non ci sono
risultati; ciascuna query deve avere almeno un rilevante. Le medie sono macro,
cioè la media aritmetica delle dieci metriche per query.

Questi giudizi misurano la corrispondenza lessicale, non la pertinenza semantica.
I 13 casi sintetici M4 restano una prova funzionale distinta.

## 5. Benchmark di indicizzazione

- Eseguire tre prove su 50 file e tre su 200 nello stesso ambiente, alternando le due dimensioni.
- Ricostruire ogni volta un indice nuovo; preparare la copia dei 50 file fuori dal tempo misurato.
- Misurare con orologio monotono dal momento prima della scansione fino all'indice completato e disponibile.
- Annotare Python/Whoosh, OS, CPU, data del test e commit/versione dei dati.
- Registrare per run: file individuati, indicizzati, saltati, bytes input, dimensione indice, tempo totale e cause di scarto.
- Riportare **tutti e sei i tempi e le due mediane**; distinguere risultati da esempi.

Non chiamare questa prova dimostrazione generale di scalabilità: entrambi i
corpus sono piccoli e omogenei, e i tempi possono dipendere da cache del file
system e hardware. `scripts/benchmark_indexing.py` conserva i dati grezzi in
`evaluation/indexing_benchmark.json`.

**Esiti M5 osservati:** 200/200 file indicizzati senza scarti. I tre tempi sui
50 file sono 1,423124, 1,098719 e 0,465418 s (mediana 1,098719 s); sui
200 file sono 3,492429, 1,531093 e 0,854928 s (mediana 1,531093 s).
Le dieci query reali hanno macro precision, recall e F1 pari a 1,000 secondo
il criterio testuale fissato. La tabella completa e i limiti sono in
`evaluation/M5_REPORT.md`, mentre i dati grezzi restano nei JSON.

## 6. Evidenze e report

Una volta implementato il sistema, conservare in `evaluation/` le query, gli attesi e gli osservati; in `report/` il documento finale. Le tabelle dell'Homework dovranno includere:

1. Motivazioni degli analyzer e compromessi introdotti.
2. Numero effettivo di file indicizzati e tempo di indicizzazione.
3. Query utilizzate e risultati con breve interpretazione.
4. Collegamento GitHub al codice e istruzioni di riproduzione.

**Regola:** nessun dato sperimentale anticipato o inventato nella relazione.
