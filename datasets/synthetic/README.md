# Corpus sintetico

Corpus controllato della milestone M1. Contiene 12 documenti UTF-8 progettati
per verificare nomi, contenuti, accenti, maiuscole, stopword, phrase query,
assenza di stemming, percorsi omonimi e file vuoti.

`misc/invalid_encoding.txt` è una fixture separata composta dal solo byte
`0xFF`: deve essere scoperta dalla scansione e poi saltata perché non è UTF-8.
Non fa parte dei 12 documenti validi.

Gli ID dei documenti sono i percorsi relativi a questa directory. Le query e
gli insiemi attesi, fissati prima dell'implementazione della ricerca, sono in
[`../../evaluation/queries.json`](../../evaluation/queries.json).
