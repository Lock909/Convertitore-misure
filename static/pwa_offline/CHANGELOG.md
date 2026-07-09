# Changelog — Calcolatore Industriale (app Streamlit + PWA offline)

Formato ispirato a [Keep a Changelog](https://keepachangelog.com/it/1.0.0/). Il numero di
versione qui sotto corrisponde a `VERSIONE_APP` in `static/pwa_offline/app.js` (gestito da
`bump_versione_pwa.py`), che è anche il tag Git della release (`vNN`).

Le versioni precedenti alla v28 sono state sviluppate prima dell'adozione di Git in questo
progetto: non hanno un tag corrispondente (nessun commit storico disponibile), ma sono
documentate qui per completezza.

## [v68] - 2026-07-09
### Added
- Nuova vista "Cronologia versioni", sempre raggiungibile (pulsante "🕘 Versioni" nell'header
  della PWA, sezione dedicata sotto "📁 Progetti Salvati" in Streamlit): elenca tutte le
  release passate con le relative novità, per chi vuole ricontrollare cosa è cambiato senza
  aspettare il banner mostrato una tantum dopo un aggiornamento.
### Changed
- Il banner "cosa è cambiato" ora copre tutte le versioni intercorse dall'ultima vista (non
  solo l'ultima): chi non apre l'app per un po' e salta più di un aggiornamento vede l'elenco
  completo delle novità, raggruppate per versione dalla più recente alla più vecchia.

## [v67] - 2026-07-09
### Added
- Banner "cosa è cambiato" mostrato una volta sola dopo un aggiornamento, sia in Streamlit
  che nella PWA offline: confronta la versione appena caricata con l'ultima vista (cookie in
  Streamlit, `localStorage` nella PWA) e mostra le novità lette direttamente da questo
  CHANGELOG, senza duplicarne il contenuto altrove.
### Fixed
- Service worker della PWA: la cache offline non includeva ancora i moduli `fulmini.py`,
  `batterie_piombo.py`, `misuratori_portata.py` e `antincendio.py` aggiunti in v62 — un
  dispositivo che avesse installato l'app e fosse andato offline prima di aprire uno di questi
  calcolatori almeno una volta online li avrebbe trovati non disponibili.

## [v62] - 2026-07-09
### Added
- Nuovo modulo **Protezione fulmini (LPS)** — valutazione semplificata Nd/Nc (IEC 62305) con
  area di raccolta equivalente, livello di protezione LPL minimo e parametri dell'impianto
  (sfera rotolante, maglia, calate), disponibile in Streamlit (Sicurezza & Utilities) e PWA.
- Nuovo modulo **Batterie al piombo — complementi avanzati (UPS statiche)**: correzione IEEE
  485 per temperatura, numero di celle in serie, tensione di fine scarica e capacità effettiva
  secondo la legge di Peukert. Si appoggia al dimensionamento di base già esistente
  (`batterie_ups.dimensiona_banco`) invece di duplicarlo con una formula diversa.
- Nuovo modulo **Misuratori di portata industriali**: diaframma tarato (ISO 5167-2, con verifica
  di Reynolds e velocità consigliata), misuratore a turbina (K-factor) ed elettromagnetico.
- Nuovo modulo **Antincendio — rete idranti/naspi (UNI 10779)**: portata totale di rete per
  livello di rischio, volume di riserva idrica, prevalenza minima pompa e stima indicativa del
  numero di protezioni per area.
### Fixed
- `web.py`: le voci "Protezione Fulmini (LPS)" e "Antincendio" mancavano nell'indice di ricerca
  della sidebar (introdotta in v34): aggiunte per renderle trovabili dalla ricerca.

## [v57] - 2026-07-08
### Fixed
- Crash `KeyError` in produzione sulla Conversione Grandezze Vibrazionali (Streamlit): il
  risultato salvato in sessione da un'esecuzione precedente all'aggiornamento v56 non aveva i
  nuovi campi (frequenza_cpm, unità imperiali, dB), e Streamlit mantiene lo stato di sessione
  anche dopo un aggiornamento del codice in corsa — accedervi con `dict['chiave']` faceva
  crashare la pagina. Ora si usa `.get()` con un fallback ricalcolato dai campi originali
  (sempre presenti), verificato per coincidere esattamente col ricalcolo diretto.
### Changed
- La stessa vista ora mostra tutte le conversioni (SI, imperiali, dB) in un'unica schermata a
  tre colonne, senza doverne espandere una parte: prima il crash impediva comunque di vedere
  la sezione con le unità aggiuntive.

## [v61] - 2026-07-08
### Changed
- Anche il riepilogo del calcolatore "Batteria Li-Ion — curva di scarica" usa ora la stessa
  griglia di schede metrica introdotta in v60 (era rimasta una tabella), per coerenza completa
  con tutti gli altri calcolatori.

## [v60] - 2026-07-08
### Changed
- I risultati scalari (renderTabellaDict e renderTabellaCampi) ora si presentano come una
  griglia di "schede metrica" (etichetta piccola sopra, valore grande in grassetto sotto, in
  colonne che si adattano alla larghezza) invece di una tabella impilata verticalmente — stesso
  trattamento visivo per tutti i calcolatori, sia quelli con etichette curate a mano sia quelli
  col fallback generico sul dict. Le tabelle con righe multiple (batch cavi, punti di taratura,
  riepilogo batteria) restano tabelle, perché rappresentano record ripetuti e non un insieme di
  grandezze scalari.

## [v59] - 2026-07-08
### Changed
- Uniformata la presentazione dei risultati tra i ~200 calcolatori della PWA offline: la
  maggioranza (191 su 209) mostrava i nomi grezzi delle variabili Python (es. "Tj_C",
  "R_tot_CW") invece di etichette leggibili con unità come i pochi calcolatori curati a mano
  (es. "Potenza rifasante necessaria — 55.3 kVAR"). Aggiunto un formattatore automatico che
  riconosce ~60 suffissi di unità verificati contro tutte le chiavi realmente restituite dai
  bridge (es. "Tj_C" → "Tj [°C]", "R_tot_CW" → "R tot [°C/W]"): dove il suffisso non è
  riconosciuto con certezza, il nome resta solo spaziato/capitalizzato senza inventare
  un'unità — in uno strumento di calcolo industriale un'etichetta sbagliata è un rischio
  reale, non solo estetico (scartato di proposito il suffisso "min", ambiguo tra "minimo" e
  "minuti" nel codice esistente: avrebbe etichettato erroneamente valori come "Ra_min" o
  "valore_min").

## [v58] - 2026-07-08
### Added
- Colmati gap trovati con un confronto sistematico Streamlit ↔ PWA offline (tutti gli altri
  strumenti erano già allineati): "Motore asincrono — Grandezze da dati di targa" (con curva
  coppia-velocità di Kloss) e 5 strumenti di strumentazione/metrologia finora presenti solo su
  Streamlit — "Errore di misura e incertezza", "Taratura strumento" (con applicazione della
  correzione a una nuova lettura), "Interpolazione da certificato di taratura",
  "Caratterizzazione RTD (R0/α reali)", "Offset taratura termocoppia". I quattro strumenti a
  tabella punti condividono una nuova vista generica riutilizzabile (`tabella_punti`).
### Fixed
- Bug nella selezione di default dei campi a tendina con opzioni numeriche (es. "Numero poli"):
  il confronto tra il valore selezionato e il default falliva per una discrepanza di tipo
  (numero vs stringa), selezionando sempre la prima opzione della lista invece del default
  dichiarato. Introdotto testando il nuovo calcolatore motore asincrono.
- Funzione bridge `strum_interpola_taratura`: nome del parametro non coerente con la vista
  generica `tabella_punti` (`tabella_json` invece di `punti_json`), causava un errore a runtime.

## [v56] - 2026-07-08
### Added
- Conversione grandezze vibrazionali (Streamlit + PWA offline): estesa con unità imperiali
  (velocità in in/s, accelerazione in ft/s²/in/s², spostamento in mils pk-pk), frequenza in
  CPM oltre a Hz, e livelli in dB (VdB/AdB) con riferimenti sia ISO 1683 (1 nm/s, 1 µm/s²) sia
  US storici (1E-8 m/s, 1 micro-g). Estratta confrontando input/output del programma
  "DLI Watchman VibCon" (fornito dall'utente come screenshot, senza sorgente disponibile):
  tutti i valori tranne adb_iso coincidono a 3+ cifre significative con l'originale (adb_iso
  usa i riferimenti ISO 1683 standard, con uno scarto di ~0.2 dB verosimilmente dovuto ad
  arrotondamenti interni del programma originale, non riproducibile senza il sorgente).

## [v55] - 2026-07-07
### Added
- Promemoria di backup periodico: se sono passati 30+ giorni dall'ultimo backup esportato (o
  non ne è mai stato fatto uno) e ci sono dati da proteggere (preferiti/cronologia/progetti),
  viene mostrato un banner con un pulsante "Esporta backup ora". Presente sia nella PWA
  offline (banner in alto, tracciato in `localStorage`) sia nella versione Streamlit (avviso
  in sidebar, tracciato nel JSON per-device). Evita di perdere i dati per una cancellazione
  della cache del browser senza essersene accorti.

## [v54] - 2026-07-07
### Changed
- Velocizzato il primo avvio della PWA offline: i 53 moduli Python vengono ora scaricati in
  parallelo (`Promise.all`) invece che uno alla volta in sequenza, riducendo il tempo di
  attesa al primo caricamento (specialmente su connessioni lente). Nessuna modifica al
  comportamento con connessione veloce o a cache già popolata (service worker).

## [v53] - 2026-07-07
### Added
- Smoke test automatico (`test.js`, attivabile con `?test=1`) su tutti i 201 calcolatori con
  bridge diretto: chiama ciascuna funzione con i valori di default di `calcolatori.js` e
  verifica solo l'assenza di eccezioni/errori (non il valore numerico). Prima la suite di test
  copriva solo i 33 casi con valore atteso verificato a mano di componenti_passivi.

## [v52] - 2026-07-07
### Added
- Dimensionamento Cavi in Batch (tabella) nella PWA offline: righe dinamiche
  (aggiungi/rimuovi linea), importazione da CSV, calcolo di tutte le linee in un colpo solo
  (sezione minima da portata + verifica caduta di tensione) ed esportazione dei risultati in
  CSV. Prima era disponibile solo il dimensionamento a singola linea.

## [v51] - 2026-07-07
### Added
- Grafico curva di derating del dissipatore termico nella PWA offline (potenza massima
  dissipabile in funzione della temperatura ambiente), già presente nella versione Streamlit
  ma finora mancante offline.

## [v50] - 2026-07-06
### Added
- Convertitore di unità di misura generico (16 grandezze: pressione, portate, lunghezza,
  superficie, volume, densità, forza, massa, coppia, energia, potenza, velocità,
  accelerazione, angolo, temperatura), con vista dedicata a select dipendenti e tabella di
  conversione simultanea in tutte le unità della categoria.

## [v49] - 2026-07-06
### Fixed
- Bug CSS che rendeva inefficace l'attributo `hidden` sulle categorie collassate nel menu
  (regola `.nav-lista-gruppo { display: flex }` aveva precedenza sullo user-agent stylesheet).

## [v48] - 2026-07-06
### Changed
- Rifatta l'interfaccia della PWA: layout a due colonne (sidebar + contenuto) con scroll
  indipendente, categorie del menu a fisarmonica (accordion, collassate di default tranne
  quella attiva), menu a scomparsa (drawer) su mobile/tablet con overlay e pulsante hamburger.

## [v47] - 2026-07-06
### Added
- Blocco Pneumatica/Strumenti + Sicurezza/PLC (5 moduli, 21 calcolatori): aria compressa,
  trasduttori 4-20 mA, rumore industriale, Performance Level/SIL (EN ISO 13849-1), utility
  PLC IEC 61131-3 (scalatura analogica, esplosione/composizione bit, indirizzi memoria RX3i).

## [v46] - 2026-07-06
### Added
- `tubazione_pressione.py`: spessore minimo/pressione ammissibile tubazioni in pressione
  (EN 13480-3). Chiude il blocco Termotecnica/Fluidi (9 moduli).

## [v45] - 2026-07-06
### Added
- `valvole_controllo.py`: dimensionamento Cv/Kv liquidi e gas, verifica cavitazione (IEC 60534).

## [v44] - 2026-07-06
### Added
- `serbatoi.py`: volumi geometrici, pressione idrostatica, portata di Torricelli, tempi di
  svuotamento/riempimento.

## [v43] - 2026-07-06
### Added
- `condotte_hvac.py`: proprietà aria, diametro idraulico, perdita di carico e
  dimensionamento condotte circolari/rettangolari.

## [v42] - 2026-07-06
### Added
- `isolamento_termico.py`: perdita termica parete piana multistrato e tubo cilindrico
  coibentato, verifica rischio condensa (formula di Magnus).

## [v41] - 2026-07-06
### Added
- `scambiatori.py`: bilancio termico, metodo LMTD, metodo NTU-ε.

## [v40] - 2026-07-06
### Added
- `perdite_carico_distribuite.py`: Darcy-Weisbach, numero di Reynolds, fattore di attrito
  di Swamee-Jain, diametro da velocità massima.

## [v39] - 2026-07-06
### Added
- `perdite_carico.py`: perdite concentrate su raccordi/valvole (database Idel'chik),
  lunghezza equivalente, allargamento/restringimento bruschi.

## [v38] - 2026-07-06
### Added
- `pompe.py`: punto di lavoro pompa/impianto, potenza idraulica, NPSH disponibile, numero
  specifico di giri.

## [v37] - 2026-07-06
### Added
- `nastri_trasportatori.py`: portata di trasporto, potenza motore (ISO 5048), tensione
  nastro, angolo massimo di inclinazione. Chiude il blocco Meccanica (10 moduli).

## [v36] - 2026-07-06
### Added
- `trasmissioni.py`: stadio singolo e riduttore multistadio, geometria cinghia,
  conversione potenza/coppia/velocità.

## [v35] - 2026-07-06
### Added
- `saldature.py`: resistenza ammissibile cordone (EN 1993-1-8), gola minima, verifica a
  taglio/carico normale, cordoni su flangia.

## [v34] - 2026-07-06
### Added
- `alberi_torsione.py`: momento torcente, diametro minimo, tensioni combinate, fattore di
  sicurezza statico, verifica a fatica (Goodman/Gerber).

## [v33] - 2026-07-06
### Added
- `ruote_dentate.py`: geometria, modulo minimo ed equazione di Lewis, rapporto di
  trasmissione.

## [v32] - 2026-07-06
### Added
- `molle.py`: costante elastica compressione/trazione, tensione di taglio (fattore di
  Wahl), frequenza naturale, molla di torsione.

## [v31] - 2026-07-06
### Added
- `cuscinetti.py`: durata L10 (ISO 281), carico dinamico equivalente, fattore di durata
  richiesta.

## [v30] - 2026-07-06
### Added
- Blocco Meccanica sotto-blocco 1: `vibrazioni.py`, `resistenza_materiali.py`,
  `bulloneria.py`.

## [v29] - 2026-07-06
### Added
- Elettrico sotto-blocco 3: `avviamento_motore.py`, `dissipatore.py`,
  `illuminotecnica.py`, `libreria_cavi.py`, `batch_cavi.py`, `costi_energetici.py`.
  Chiude il blocco Elettrico (17 moduli).

## [v1] - [v28] - fino al 2026-07-03
Sviluppo iniziale, prima dell'adozione di Git (nessun tag disponibile).
### Added
- Scaffold PWA offline con motore Pyodide, service worker e cache per l'uso offline.
- Moduli Elettrico sotto-blocchi 1-2 (trasformatore, RLC, THD, UPS, terra, selettività,
  fotovoltaico, gruppo elettrogeno, quadro elettrico, rifasamento, caduta di tensione BT).
- Riferimento rapido, canaline/passerelle, componenti passivi (con calcolatori LED,
  partitore, RC/RL, Wheatstone, AWG, SMD, filtro, op-amp, zener).
- Cronologia calcoli e progetti salvati (localStorage), esportazione (copia/CSV/PDF/QR),
  ricerca e preferiti nel menu.
- Backup/ripristino compatibile tra versione Streamlit e PWA offline.
- Collegamento della PWA al server Streamlit tramite file statici.
