// ==============================================================================
// test.js — Suite di regressione minima sulle funzioni bridge, con valori noti.
// Si attiva solo aggiungendo ?test=1 all'URL (non caricato nell'uso normale).
// Confronta l'output reale di ciascuna funzione bridge con un valore atteso,
// per individuare rapidamente regressioni quando si modifica bridge.py o i
// moduli Python sottostanti.
//
// Include anche uno smoke test su TUTTI i calcolatori (CASI_TEST sopra copre
// solo componenti_passivi con valori verificati a mano): chiama ciascuna
// funzione bridge con i valori di default già dichiarati in calcolatori.js e
// verifica solo che non sollevi eccezioni e non ritorni {"errore": ...} — non
// verifica che il RISULTATO sia numericamente corretto, solo che il percorso
// JS→Pyodide→Python non sia rotto (tipi di argomento, nomi di funzione, ecc.).
// ==============================================================================

function _vicino(a, b, tolleranza = 0.01) {
  return Math.abs(a - b) <= tolleranza * Math.max(1, Math.abs(b));
}

const CASI_TEST = [
  { fn: "ohm", args: { ricerca: "Tensione", input_1: 230, input_2: 10 }, campo: "valore", atteso: 2300 },
  { fn: "rifasamento", args: { p_attiva_kw: 100, cos_ini: 0.75, cos_fin: 0.95 }, campo: "qc_kvar", atteso: 55.32 },
  { fn: "sezione_protezione", args: { i_max: 32, densita: 5 }, campo: "sezione_teorica_mm2", atteso: 6.4 },
  { fn: "rtd_resistenza", args: { temp_C: 100, R0: 100 }, campo: "R_ohm", atteso: 138.5055 },
  { fn: "rtd_temperatura", args: { R_ohm: 138.5055, R0: 100 }, campo: "temp_C", atteso: 100, tolleranza: 0.02 },
  { fn: "voting_tmr_mediano", args: { v1: 100, v2: 101, v3: 99.5, tolleranza: 1 }, campo: "valore_votato", atteso: 100 },
  { fn: "corrente_assorbita_tbci", args: { tipo: "H1 (125 Vdc)", n_circuiti_normali: 21, n_circuiti_alta: 3 }, campo: "I_totale_mA", atteso: 82.5 },
  { fn: "loading_ionet", args: { n_pacchi_io: 8, canali_medi_per_pacco: 16, frame_rate_hz: 100, banda_rete_mbps: 100, overhead_byte: 64, byte_per_canale: 4 }, campo: "utilizzo_pct", atteso: 0.82 },
  { fn: "colori_conduttori", args: {}, campo: "Giallo-Verde", atteso: "Conduttore di protezione (PE) — esclusivo, non utilizzabile per altre funzioni", confrontaTesto: true },
  { fn: "ik_energia", args: {}, campo: "IK10", atteso: 20 },
  { fn: "riempimento_canalina", args: { larghezza_mm: 100, altezza_mm: 60, d1: 9.5, q1: 6, d2: 0, q2: 0, d3: 0, q3: 0 }, campo: "riempimento_pct", atteso: 7.0882, tolleranza: 0.01 },
  { fn: "decodifica_ip", args: { codice: "IP65" }, campo: "prima_cifra", atteso: "6", confrontaTesto: true },
  { fn: "decodifica_colori_resistore",
    args: { c1: "Marrone", c2: "Nero", c3: "Nero", moltiplicatore: "Rosso", tolleranza: "Oro", coeff_temp: "Marrone", n_bande: "4" },
    campo: "valore_ohm", atteso: 1000 },
  { fn: "decodifica_colori_resistore",
    args: { c1: "Marrone", c2: "Nero", c3: "Nero", moltiplicatore: "Rosso", tolleranza: "Oro", coeff_temp: "Marrone", n_bande: "3" },
    campo: "tolleranza_pct", atteso: 20 },
  { fn: "decodifica_colori_resistore",
    args: { c1: "Marrone", c2: "Nero", c3: "Nero", moltiplicatore: "Rosso", tolleranza: "Oro", coeff_temp: "Marrone", n_bande: "6" },
    campo: "coeff_temperatura_ppm_C", atteso: 100 },
  { fn: "colori_da_resistenza", args: { valore_ohm: 1000, n_bande: "4", tolleranza_pct: "5", coeff_temp_ppm_C: "100" },
    campo: "colori", atteso: "Marrone,Nero,Rosso,Oro", confrontaTesto: true, formattaLista: true },
  { fn: "resistori_induttori_combinazione", args: { tipo: "Resistori", combinazione: "Serie", valori: [100, 220, 330] },
    campo: "valore_equivalente", atteso: 650 },
  { fn: "resistori_induttori_combinazione", args: { tipo: "Resistori", combinazione: "Parallelo", valori: [1000, 1000] },
    campo: "valore_equivalente", atteso: 500 },
  { fn: "condensatori_combinazione", args: { combinazione: "Serie", valori_uF: [10, 10] },
    campo: "valore_equivalente_uF", atteso: 5 },
  { fn: "condensatori_combinazione", args: { combinazione: "Parallelo", valori_uF: [10, 22] },
    campo: "valore_equivalente_uF", atteso: 32 },
  { fn: "valore_normalizzato_e", args: { valore: 53, serie: "E24" }, campo: "valore_normalizzato", atteso: 51 },
  { fn: "decodifica_smd_standard", args: { codice: "103" }, campo: "valore_ohm", atteso: 10000 },
  { fn: "decodifica_smd_eia96", args: { codice: "68C" }, campo: "valore_ohm", atteso: 499 },
  { fn: "resistenza_limitazione_led", args: { v_alimentazione: 9, v_forward_led: 2, corrente_ma: 20 },
    campo: "resistenza_ohm", atteso: 350 },
  { fn: "partitore_tensione_vout", args: { v_in: 12, r1_ohm: 1000, r2_ohm: 2000 }, campo: "v_out", atteso: 8 },
  { fn: "partitore_tensione_r2", args: { v_in: 12, v_out: 4, r1_ohm: 1000 }, campo: "r2_ohm", atteso: 500 },
  { fn: "costante_di_tempo", args: { tipo: "RC", resistenza_ohm: 1000, c_o_l: 0.000001, percentuale_target: 63.2 },
    campo: "tau_s", atteso: 0.001 },
  { fn: "wheatstone_resistenza_incognita", args: { r1_ohm: 100, r2_ohm: 200, r3_ohm: 150 }, campo: "rx_ohm", atteso: 300 },
  { fn: "awg_a_mm2", args: { awg: 24 }, campo: "area_mm2", atteso: 0.2047, tolleranza: 0.01 },
  { fn: "mm2_a_awg", args: { area_mm2: 2.5 }, campo: "awg_piu_vicino", atteso: 13 },
  { fn: "frequenza_taglio_rc_rl", args: { tipo: "RC", resistenza_ohm: 1000, c_o_l: 0.000001 }, campo: "fc_Hz", atteso: 159.1549 },
  { fn: "guadagno_op_amp", args: { configurazione: "Invertente", r1_ohm: 1000, r2_ohm: 10000 }, campo: "guadagno", atteso: -10 },
  { fn: "diodo_zener_regolatore", args: { v_alimentazione: 12, v_zener: 5.1, r_serie_ohm: 220, r_carico_ohm: 1000 },
    campo: "i_zener_mA", atteso: 26.2636, tolleranza: 0.001 },
];

function eseguiTestSuite() {
  const risultati = [];
  for (const caso of CASI_TEST) {
    let stato, ottenuto;
    try {
      const r = chiamaBridge(caso.fn, caso.args);
      ottenuto = r[caso.campo];
      if (caso.formattaLista && Array.isArray(ottenuto)) ottenuto = ottenuto.join(",");
      const ok = caso.confrontaTesto ? ottenuto === caso.atteso : _vicino(ottenuto, caso.atteso, caso.tolleranza ?? 0.01);
      stato = ok ? "✅ OK" : "❌ FALLITO";
    } catch (e) {
      ottenuto = "ERRORE: " + e;
      stato = "❌ FALLITO";
    }
    risultati.push({ fn: caso.fn, campo: caso.campo, atteso: caso.atteso, ottenuto, stato });
  }
  return risultati;
}

function valoreDefaultCampo(campo) {
  if (campo.type === "lista_valori") return campo.defaultLista ? [...campo.defaultLista] : [];
  if (campo.type === "select") return campo.default !== undefined ? campo.default : campo.opzioni[0];
  if (campo.type === "checkbox") return !!campo.default;
  return campo.default;
}

function costruisciKwargsDefault(calc) {
  const kwargs = {};
  for (const campo of calc.campi) kwargs[campo.name] = valoreDefaultCampo(campo);
  return kwargs;
}

// Le viste "speciale" (conversione, batch_cavi) sono costruite a mano con più
// funzioni bridge dipendenti tra loro (select a cascata, righe dinamiche): non
// hanno un'unica funzione bridge chiamabile con i soli valori di default, quindi
// restano fuori dallo smoke test automatico.
function eseguiSmokeTestCalcolatori() {
  const risultati = [];
  for (const calc of CALCOLATORI) {
    if (calc.speciale) continue;
    const kwargs = costruisciKwargsDefault(calc);
    let stato, dettaglio;
    try {
      const r = chiamaBridge(calc.bridge, kwargs);
      if (r && r.errore) {
        stato = "❌ FALLITO";
        dettaglio = r.errore;
      } else {
        stato = "✅ OK";
        dettaglio = "";
      }
    } catch (e) {
      stato = "❌ FALLITO";
      dettaglio = "ERRORE: " + e;
    }
    risultati.push({ id: calc.id, bridge: calc.bridge, stato, dettaglio });
  }
  return risultati;
}

function mostraTestSuite() {
  const main = document.getElementById("contenuto-calcolatore");
  main.innerHTML = "<h2>Suite di test bridge</h2>";

  const sottotitolo1 = document.createElement("h3");
  sottotitolo1.textContent = "Regressione con valore atteso (componenti_passivi)";
  main.appendChild(sottotitolo1);

  const risultati = eseguiTestSuite();
  const tabella = document.createElement("table");
  tabella.className = "tabella-risultati";
  for (const r of risultati) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${r.fn} → ${r.campo}</td><td>${r.stato} (atteso ${r.atteso}, ottenuto ${r.ottenuto})</td>`;
    tabella.appendChild(tr);
  }
  main.appendChild(tabella);
  const nFalliti = risultati.filter(r => r.stato.includes("FALLITO")).length;
  const riepilogo = document.createElement("p");
  riepilogo.textContent = nFalliti === 0
    ? `Tutti i ${risultati.length} test sono passati.`
    : `${nFalliti} test falliti su ${risultati.length}.`;
  main.appendChild(riepilogo);

  const sottotitolo2 = document.createElement("h3");
  sottotitolo2.textContent = "Smoke test su tutti i calcolatori (solo assenza di errori)";
  main.appendChild(sottotitolo2);

  const risultatiSmoke = eseguiSmokeTestCalcolatori();
  const tabellaSmoke = document.createElement("table");
  tabellaSmoke.className = "tabella-risultati";
  for (const r of risultatiSmoke) {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${r.id} (${r.bridge})</td><td>${r.stato}${r.dettaglio ? " — " + r.dettaglio : ""}</td>`;
    tabellaSmoke.appendChild(tr);
  }
  main.appendChild(tabellaSmoke);
  const nFallitiSmoke = risultatiSmoke.filter(r => r.stato.includes("FALLITO")).length;
  const riepilogoSmoke = document.createElement("p");
  riepilogoSmoke.textContent = nFallitiSmoke === 0
    ? `Tutti i ${risultatiSmoke.length} calcolatori rispondono senza errori con i valori di default.`
    : `${nFallitiSmoke} calcolatori falliti su ${risultatiSmoke.length}.`;
  main.appendChild(riepilogoSmoke);
}
