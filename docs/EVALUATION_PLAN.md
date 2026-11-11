# Piano di valutazione — Specifica preliminare

**Non contiene risultati.** I dati e gli output saranno aggiunti soltanto dopo implementazione ed esecuzione.

## 1. Obiettivi

- **RQ1:** la ricerca rispetta le regole degli analyzer e la grammatica delle query?
- **RQ2:** quanti file vengono indicizzati e quanto tempo richiede la costruzione dell'indice su un corpus pubblico reale?

## 2. Corpus preparati

| Corpus | Scopo | Dimensione obiettivo | Stato |
|---|---|---|---|
| Sintetico | Correttezza di query e gestione errori | 12 `.txt` validi + 1 non UTF-8 | Preparato in M1 |
| Reale | Conteggi e tempi di indicizzazione | 50 `.txt`: 25 IT + 25 EN | Preparato in M1 |

Il corpus reale usa introduzioni Wikipedia con revisioni congelate. Provenienza,
licenza CC BY-SA 4.0, trasformazioni, dimensioni e SHA-256 sono registrati in
`datasets/real/manifest.csv`; `sources.json` consente la rigenerazione dalle
revisioni esatte.

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
non UTF-8 sono fixture del corpus. M3 verifica le 13 query e il recupero dagli
errori di sintassi di base; M4 estenderà la matrice dei casi limite.

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
