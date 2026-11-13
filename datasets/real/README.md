# Corpus reale Wikipedia IT/EN

Il corpus contiene le introduzioni di 100 coppie di voci Wikipedia: 100 file
italiani in `it/` e 100 voci collegate in inglese in `en/`. I file sono in
UTF-8 e vengono conservati nel repository per rendere riproducibili le prove.
Le coppie 01–25 sono il sottoinsieme iniziale usato per i giudizi di rilevanza
e per il benchmark a 50 file; percorsi, revisioni e SHA-256 sono congelati in
`initial_50.json`.

## Provenienza e manifest

`sources.json` congela titolo, page ID, revision ID e percorso di ogni voce.
`manifest.csv` aggiunge URL permanente, lingua, coppia, licenza, trasformazione,
dimensione in byte e SHA-256 di ciascun file. L'URL permanente attribuisce il
testo ai contributori della relativa voce e permette di consultare la revisione
esatta da cui è stato derivato.

Le 75 coppie aggiunte sono state selezionate in cinque gruppi da 15:
informatica e dati, matematica e statistica, scienze naturali, ambiente ed
energia, mobilità e robotica. `candidates.json` conserva la lista ordinata dei
candidati e `selection.json` registra accettazioni, scarti e relative cause.
Sono accettate voci italiane distinte da quelle già presenti, con collegamento
inglese, due introduzioni non vuote e contenuti non duplicati. Si estrae solo
il testo dei paragrafi introduttivi, escludendo immagini, tabelle ed elementi
non testuali.

Le prime 25 coppie sono state congelate l'11 novembre 2026; le successive
sono state selezionate il 13 novembre 2026. Una revisione fissa identifica
la pagina di origine, mentre il file versionato e il suo SHA-256 fissano
esattamente i byte usati nell'esperimento.

## Trasformazione e riproduzione

Lo script `../../scripts/prepare_real_corpus.py` recupera tramite MediaWiki
l'HTML della revisione indicata da `oldid`, conserva i paragrafi introduttivi
prima della prima sezione, rimuove gli elementi non testuali, normalizza gli
spazi e Unicode in NFC e scrive UTF-8. Non effettua correzioni editoriali o
traduzioni. Prima di scrivere controlla hash e revisioni dei 50 file iniziali,
codifica, duplicati e conteggi; un disaccordo interrompe la generazione.

Per verificare i 50 iniziali e rigenerare i 150 nuovi file dalle revisioni fissate:

```powershell
python scripts/prepare_real_corpus.py
```

Per ripetere la selezione *a partire dal corpus iniziale di 25 coppie*:

```powershell
python scripts/prepare_real_corpus.py --append-new-pairs
```

La selezione usa le revisioni correnti dei nuovi candidati e può quindi produrre
file diversi da quelli versionati. Per riprodurre le misure pubblicate usare i
file e gli hash presenti nel repository.

## Licenza e attribuzione

I testi sono opere derivate da Wikipedia e sono redistribuiti secondo la
[Creative Commons Attribution-ShareAlike 4.0 International](https://creativecommons.org/licenses/by-sa/4.0/).
Autori e fonte di ogni testo sono attribuiti tramite l'URL permanente nel
manifest. Le modifiche applicate sono quelle descritte sopra e nella colonna
`transformation`.

Questa licenza riguarda il corpus derivato. Non modifica la licenza del codice
del progetto, che resta separata. Per le condizioni di riuso originali vedere
i [Termini d'uso Wikimedia](https://foundation.wikimedia.org/wiki/Terms_of_Use).
