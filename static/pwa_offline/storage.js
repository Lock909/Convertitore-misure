// ==============================================================================
// storage.js — Cronologia calcoli e progetti salvati, persistenza locale via
// localStorage (funziona offline, nessun server coinvolto).
// ==============================================================================

const CHIAVE_CRONOLOGIA = "cronologiaCalcoli";
const CHIAVE_PROGETTI = "progettiSalvati";
const CHIAVE_PREFERITI = "preferitiCalcolatori";
const CHIAVE_ULTIMO_BACKUP = "ultimoBackupIl";
const MAX_CRONOLOGIA = 100;

function _leggiJSON(chiave, fallback) {
  try {
    const raw = localStorage.getItem(chiave);
    return raw ? JSON.parse(raw) : fallback;
  } catch (e) {
    return fallback;
  }
}

function _scriviJSON(chiave, valore) {
  try { localStorage.setItem(chiave, JSON.stringify(valore)); } catch (e) { /* storage non disponibile */ }
}

function salvaInCronologia(calc, kwargs, risultato) {
  const cronologia = _leggiJSON(CHIAVE_CRONOLOGIA, []);
  cronologia.unshift({
    id: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    calcId: calc.id,
    titolo: calc.titolo,
    timestamp: new Date().toISOString(),
    input: kwargs,
    output: risultato,
  });
  if (cronologia.length > MAX_CRONOLOGIA) cronologia.length = MAX_CRONOLOGIA;
  _scriviJSON(CHIAVE_CRONOLOGIA, cronologia);
}

function leggiCronologia() {
  return _leggiJSON(CHIAVE_CRONOLOGIA, []);
}

function cancellaCronologia() {
  _scriviJSON(CHIAVE_CRONOLOGIA, []);
}

function leggiFavoriti() {
  return _leggiJSON(CHIAVE_PREFERITI, []);
}

function toggleFavorito(id) {
  const preferiti = leggiFavoriti();
  const idx = preferiti.indexOf(id);
  if (idx >= 0) preferiti.splice(idx, 1);
  else preferiti.push(id);
  _scriviJSON(CHIAVE_PREFERITI, preferiti);
}

function leggiProgetti() {
  return _leggiJSON(CHIAVE_PROGETTI, {});
}

function salvaInProgetto(nomeProgetto, voce) {
  const progetti = leggiProgetti();
  if (!progetti[nomeProgetto]) progetti[nomeProgetto] = [];
  progetti[nomeProgetto].unshift({
    id: `${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
    timestamp: new Date().toISOString(),
    ...voce,
  });
  _scriviJSON(CHIAVE_PROGETTI, progetti);
}

function eliminaProgetto(nomeProgetto) {
  const progetti = leggiProgetti();
  delete progetti[nomeProgetto];
  _scriviJSON(CHIAVE_PROGETTI, progetti);
}

function rimuoviVoceProgetto(nomeProgetto, idVoce) {
  const progetti = leggiProgetti();
  if (!progetti[nomeProgetto]) return;
  progetti[nomeProgetto] = progetti[nomeProgetto].filter(v => v.id !== idVoce);
  if (progetti[nomeProgetto].length === 0) delete progetti[nomeProgetto];
  _scriviJSON(CHIAVE_PROGETTI, progetti);
}

// ------------------------------------------------------------------ Backup/ripristino

function esportaBackupCompleto() {
  const backup = {
    tipo: "backup-calcolatore-industriale",
    versione: 1,
    esportatoIl: new Date().toISOString(),
    cronologia: leggiCronologia(),
    progetti: leggiProgetti(),
  };
  const blob = new Blob([JSON.stringify(backup, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `backup_calcolatore_${new Date().toISOString().slice(0, 10)}.json`;
  a.click();
  URL.revokeObjectURL(url);
  try { localStorage.setItem(CHIAVE_ULTIMO_BACKUP, new Date().toISOString()); } catch (e) { /* storage non disponibile */ }
}

// Usato dal promemoria di backup periodico (vedi app.js): Infinity se non è
// mai stato esportato un backup, altrimenti giorni trascorsi dall'ultimo.
function giorniDaUltimoBackup() {
  let iso;
  try { iso = localStorage.getItem(CHIAVE_ULTIMO_BACKUP); } catch (e) { return Infinity; }
  if (!iso) return Infinity;
  const millisecondi = Date.now() - new Date(iso).getTime();
  return millisecondi / (1000 * 60 * 60 * 24);
}

function esistonoDatiDaProteggere() {
  return leggiCronologia().length > 0 || Object.keys(leggiProgetti()).length > 0;
}

function importaBackupCompleto(testoJSON, modalita = "unisci") {
  let backup;
  try {
    backup = JSON.parse(testoJSON);
  } catch (e) {
    throw new Error("Il file non è un JSON valido.");
  }
  if (backup.tipo !== "backup-calcolatore-industriale") {
    throw new Error("Il file non sembra un backup di questa app (campo 'tipo' mancante o errato).");
  }
  const cronologiaImportata = Array.isArray(backup.cronologia) ? backup.cronologia : [];
  const progettiImportati = backup.progetti && typeof backup.progetti === "object" ? backup.progetti : {};

  if (modalita === "sostituisci") {
    _scriviJSON(CHIAVE_CRONOLOGIA, cronologiaImportata.slice(0, MAX_CRONOLOGIA));
    _scriviJSON(CHIAVE_PROGETTI, progettiImportati);
  } else {
    // Unisci: aggiunge le voci importate senza duplicare quelle con lo stesso id.
    const cronologiaAttuale = leggiCronologia();
    const idEsistenti = new Set(cronologiaAttuale.map(v => v.id));
    const nuoveVoci = cronologiaImportata.filter(v => !idEsistenti.has(v.id));
    const cronologiaUnita = [...nuoveVoci, ...cronologiaAttuale].slice(0, MAX_CRONOLOGIA);
    _scriviJSON(CHIAVE_CRONOLOGIA, cronologiaUnita);

    const progettiAttuali = leggiProgetti();
    for (const [nome, voci] of Object.entries(progettiImportati)) {
      if (!progettiAttuali[nome]) {
        progettiAttuali[nome] = voci;
      } else {
        const idEsistentiProgetto = new Set(progettiAttuali[nome].map(v => v.id));
        progettiAttuali[nome].push(...voci.filter(v => !idEsistentiProgetto.has(v.id)));
      }
    }
    _scriviJSON(CHIAVE_PROGETTI, progettiAttuali);
  }

  return {
    nCronologia: cronologiaImportata.length,
    nProgetti: Object.keys(progettiImportati).length,
  };
}
