# tests/

Contiene i test automatici del bootstrap, dei dati, dell'indicizzazione e della
ricerca. Le verifiche controllano conteggi, UTF-8, caso non valido, manifest,
dimensioni, SHA-256, revisioni congelate e riferimenti dell'oracolo.

Le 13 query preparate in M1 vengono eseguite sul corpus sintetico e confrontate
con l'intero insieme atteso. I test CLI coprono costruzione indice, sessione
interattiva, `help`, `exit`, EOF e recupero dagli errori di sintassi.
