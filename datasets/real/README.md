# Corpus reale Wikipedia IT/EN

Il corpus contiene le introduzioni di 25 coppie di voci Wikipedia: 25 file in
italiano in `it/` e le 25 voci collegate in inglese in `en/`. I file sono in
UTF-8 e vengono conservati nel repository per rendere riproducibili le prove.

## Provenienza e manifest

`sources.json` congela titolo, page ID, revision ID e percorso di ogni voce.
`manifest.csv` aggiunge URL permanente, lingua, coppia, licenza, trasformazione,
dimensione in byte e SHA-256 di ciascun file. L'URL permanente attribuisce il
testo ai contributori della relativa voce e permette di consultare la revisione
esatta da cui è stato derivato.

La selezione delle revisioni è stata congelata l'11 novembre 2026. Le
introduzioni estratte non contengono avvisi di licenza aggiuntivi. Quando si
aggiornano le revisioni occorre controllare nuovamente la pagina, la sua
cronologia e le eventuali note specifiche prima di accettare il nuovo corpus.

## Trasformazione e riproduzione

Lo script `../../scripts/prepare_real_corpus.py` recupera tramite MediaWiki
l'HTML della revisione indicata da `oldid`, conserva i paragrafi introduttivi
prima della prima sezione, rimuove gli elementi non testuali, normalizza gli
spazi e Unicode in NFC e scrive UTF-8. Non effettua correzioni editoriali o
traduzioni.

Per rigenerare file e manifest dalle revisioni già fissate:

```powershell
python scripts/prepare_real_corpus.py
```

Solo per selezionare deliberatamente le revisioni correnti, aggiornare il lock
e rigenerare il corpus:

```powershell
python scripts/prepare_real_corpus.py --update-revisions
```

L'aggiornamento può cambiare contenuti, dimensioni e hash e richiede una nuova
verifica delle condizioni di riuso.

## Licenza e attribuzione

I testi sono opere derivate da Wikipedia e sono redistribuiti secondo la
[Creative Commons Attribution-ShareAlike 4.0 International](https://creativecommons.org/licenses/by-sa/4.0/).
Autori e fonte di ogni testo sono attribuiti tramite l'URL permanente nel
manifest. Le modifiche applicate sono quelle descritte sopra e nella colonna
`transformation`.

Questa licenza riguarda il corpus derivato. Non modifica la licenza del codice
del progetto, che resta separata. Per le condizioni di riuso originali vedere
i [Termini d'uso Wikimedia](https://foundation.wikimedia.org/wiki/Terms_of_Use).
