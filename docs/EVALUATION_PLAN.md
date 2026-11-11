# Piano di valutazione — Specifica preliminare

**Non contiene risultati.** I dati e gli output saranno aggiunti soltanto dopo implementazione ed esecuzione.

## 1. Obiettivi

- **RQ1:** la ricerca rispetta le regole degli analyzer e la grammatica delle query?
- **RQ2:** quanti file vengono indicizzati e quanto tempo richiede la costruzione dell'indice su un corpus pubblico reale?

## 2. Corpus previsti (ancora da creare)

| Corpus | Scopo | Dimensione obiettivo | Stato |
|---|---|---|---|
| Sintetico | Correttezza di query e gestione errori | Circa 12 `.txt` validi + 1 non UTF-8 | Da realizzare |
| Reale | Conteggi e tempi di indicizzazione | Circa 50 `.txt`: 25 IT + 25 EN | Da selezionare |

Documentare provenienza, licenze, trasformazioni e SHA-256 dei file reali. Non usare testi non redistribuibili nella repository pubblica.

## 3. Matrice di casi funzionali

Realizzare almeno 10–12 query e fissare **prima dell'esecuzione** i documenti attesi. I casi dovranno includere:

| Caso | Esempio di query | Verifica |
|---|---|---|
| Termini nel nome | `nome universita` | Accenti normalizzati |
| Nome in maiuscolo | `nome CITTÀ` | Lowercase |
| AND nel nome | `nome data notes` | Entrambi i token, qualsiasi ordine |
| Frase nel nome | `nome "data integration"` | Termini consecutivi |
| Frase inesistente | `nome "data notes"` | Assenza di falso positivo |
| Frase nel contenuto | `contenuto "urban mobility"` | Ricerca EN |
| Stopword nella frase | `contenuto "integrazione dei dati"` | Conservazione stopword |
| AND nel contenuto | `contenuto data sources` | Termini in posizioni diverse |
| Frase con accenti | `contenuto "citta sostenibili"` | Accenti + posizioni |
| Separazione dei campi | `nome "trasporto pubblico"` | Non cercare nel contenuto |
| Assenza stemming | `contenuto runs` | Non unificare automaticamente con `running` |
| Nome duplicato | `nome notes` | Distinguere percorsi differenti |

Gli ID attesi per queste query saranno definiti **dopo** aver creato i documenti, senza assumere contenuti non ancora presenti. Si possono aggiungere test per sintassi non valida, file vuoto e codifica non UTF-8.

**Misura di correttezza:** per ogni query confrontare l'insieme completo dei percorsi restituiti con l'insieme atteso. Un test è superato solo se i due insiemi coincidono.

## 4. Benchmark di indicizzazione

- Usare sempre lo stesso corpus e la stessa configurazione per le tre esecuzioni.
- Ricostruire ogni volta l'indice da zero.
- Misurare con orologio monotono dal momento prima della scansione fino all'indice completato e disponibile.
- Annotare Python/Whoosh, OS, CPU, data del test e commit/versione dei dati.
- Registrare per run: file individuati, indicizzati, saltati, bytes input, dimensione indice, tempo totale e cause di scarto.
- Riportare **tutti e tre i tempi e la mediana**; distinguere risultati da esempi.

Non chiamare questa prova benchmark di scalabilità: 50 file sono un dataset introduttivo e i tempi possono dipendere da cache del file system e hardware.

## 5. Evidenze e report

Una volta implementato il sistema, conservare in `evaluation/` le query, gli attesi e gli osservati; in `report/` il documento finale. Le tabelle dell'Homework dovranno includere:

1. Motivazioni degli analyzer e compromessi introdotti.
2. Numero effettivo di file indicizzati e tempo di indicizzazione.
3. Query utilizzate e risultati con breve interpretazione.
4. Collegamento GitHub al codice e istruzioni di riproduzione.

**Regola:** nessun dato sperimentale anticipato o inventato nella relazione.
