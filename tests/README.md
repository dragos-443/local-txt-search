# tests/

Contiene i test automatici del bootstrap, dei dati, dell'indicizzazione, della
ricerca e della valutazione funzionale. Le verifiche controllano conteggi,
UTF-8, file vuoti e non validi, manifest, dimensioni, SHA-256, revisioni
congelate e riferimenti dell'oracolo.

Le 13 query preparate in M1 vengono eseguite sul corpus sintetico e confrontate
con l'intero insieme atteso. Casi mirati verificano accenti, maiuscole,
stopword, ordine delle frasi, assenza di stemming, separatori nei nomi e file
omonimi. I test CLI coprono costruzione indice, sessione interattiva, `help`,
`exit`, EOF e recupero dagli errori di sintassi. Il runner di valutazione è
verificato sia in caso di successo sia in presenza di una discrepanza.
