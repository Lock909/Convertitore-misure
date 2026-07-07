// ==============================================================================
// app.js — Motore dell'app offline: avvia Pyodide, carica i moduli Python
// puri (formule, portata_cavo, batterie_litio, bridge), costruisce il menu e
// i form a partire da CALCOLATORI (calcolatori.js) e mostra i risultati.
// ==============================================================================

const VERSIONE_APP = "55";

const FILE_PY = [
  "costanti.py", "formule.py", "portata_cavo.py", "batterie_litio.py",
  "strumentazione.py", "mark_vie.py",
  "riferimento_rapido.py", "grado_protezione_ip.py", "motore_asincrono.py", "canaline_passerelle.py",
  "componenti_passivi.py",
  "trasformatore.py", "circuito_rlc.py", "armonie_thd.py", "batterie_ups.py", "impianto_terra.py",
  "selettivita_protezioni.py", "fotovoltaico.py", "gruppo_elettrogeno.py", "quadro_elettrico.py",
  "rifasamento_condensatori.py", "caduta_tensione_bt.py",
  "avviamento_motore.py", "dissipatore.py", "illuminotecnica.py", "libreria_cavi.py",
  "batch_cavi.py", "costi_energetici.py",
  "vibrazioni.py", "resistenza_materiali.py", "bulloneria.py", "cuscinetti.py", "molle.py",
  "ruote_dentate.py", "alberi_torsione.py", "saldature.py", "trasmissioni.py",
  "nastri_trasportatori.py", "pompe.py", "perdite_carico.py", "perdite_carico_distribuite.py",
  "scambiatori.py", "isolamento_termico.py", "condotte_hvac.py", "serbatoi.py",
  "valvole_controllo.py", "tubazione_pressione.py",
  "pneumatica.py", "trasduttori_pressione.py", "rumore_industriale.py",
  "performance_level.py", "automazione.py",
  "idraulica.py",
  "bridge.py",
];

let pyodideReady = null;
let bridge = null;
let motorePronto = false;
let calcolatoreAttuale = null;

async function avviaPyodide() {
  const badge = document.getElementById("stato-pyodide");
  const pyodide = await loadPyodide();

  badge.textContent = "⏳ Caricamento numpy…";
  await pyodide.loadPackage("numpy");

  badge.textContent = "⏳ Caricamento moduli di calcolo…";
  const contenutiFile = await Promise.all(
    FILE_PY.map(nome => fetch(`py/${nome}?v=${VERSIONE_APP}`, { cache: "no-cache" }).then(r => r.text()))
  );
  FILE_PY.forEach((nome, i) => pyodide.FS.writeFile(`/home/pyodide/${nome}`, contenutiFile[i]));

  pyodide.runPython(`
import sys
if "/home/pyodide" not in sys.path:
    sys.path.insert(0, "/home/pyodide")
import bridge
`);

  bridge = pyodide.globals.get("bridge");
  badge.textContent = "✅ Pronto — funziona offline";
  badge.className = "badge badge-ok";
  motorePronto = true;
  document.querySelectorAll(".btn-calcola").forEach(b => {
    b.disabled = false;
    b.textContent = "Calcola";
  });
  const calcAttuale = CALCOLATORI.find(c => c.id === calcolatoreAttuale);
  if (calcAttuale && calcAttuale.campi.length === 0) renderForm(calcAttuale);
  return pyodide;
}

function chiamaBridge(nomeFunzione, kwargs) {
  const fn = bridge[nomeFunzione];
  const risultatoPy = fn.callKwargs(kwargs);
  const risultato = risultatoPy && risultatoPy.toJs ? risultatoPy.toJs({ dict_converter: Object.fromEntries }) : risultatoPy;
  if (risultatoPy && risultatoPy.destroy) risultatoPy.destroy();
  return risultato;
}

// ------------------------------------------------------------------ Interfaccia

let filtroRicerca = "";

// Stato di espansione/collasso di ciascuna categoria, per non dover scorrere
// tutte le ~200 voci ogni volta: al primo incontro una categoria si espande
// solo se contiene il calcolatore attivo (o è "⭐ Preferiti"), poi lo stato
// scelto dall'utente persiste tra un rebuild del menu e l'altro.
let statoGruppi = new Map();

function isGruppoEspanso(categoria, contieneAttivo) {
  if (statoGruppi.has(categoria)) return statoGruppi.get(categoria);
  const espanso = categoria === "⭐ Preferiti" || contieneAttivo;
  statoGruppi.set(categoria, espanso);
  return espanso;
}

function costruisciMenu() {
  const nav = document.getElementById("nav-calcolatori");
  nav.innerHTML = "";
  const query = filtroRicerca.trim().toLowerCase();
  const inRicerca = query.length > 0;
  const preferiti = leggiFavoriti();

  const gruppi = {};
  if (preferiti.length > 0) {
    const calcPreferiti = preferiti
      .map(id => CALCOLATORI.find(c => c.id === id))
      .filter(Boolean)
      .filter(c => !query || c.titolo.toLowerCase().includes(query));
    if (calcPreferiti.length > 0) gruppi["⭐ Preferiti"] = calcPreferiti;
  }
  for (const calc of CALCOLATORI) {
    if (query && !calc.titolo.toLowerCase().includes(query)) continue;
    (gruppi[calc.categoria] ||= []).push(calc);
  }

  if (Object.keys(gruppi).length === 0) {
    const vuoto = document.createElement("p");
    vuoto.className = "placeholder";
    vuoto.textContent = "Nessun calcolo trovato per questa ricerca.";
    nav.appendChild(vuoto);
    return;
  }

  for (const [categoria, lista] of Object.entries(gruppi)) {
    const contieneAttivo = lista.some(c => c.id === calcolatoreAttuale);
    // Durante una ricerca attiva mostriamo sempre tutti i risultati espansi:
    // altrimenti l'utente dovrebbe riaprire manualmente ogni categoria.
    const espanso = inRicerca ? true : isGruppoEspanso(categoria, contieneAttivo);

    const gruppo = document.createElement("div");
    gruppo.className = "nav-gruppo";

    const titolo = document.createElement("button");
    titolo.type = "button";
    titolo.className = "nav-titolo-gruppo";
    const freccia = document.createElement("span");
    freccia.className = "nav-titolo-freccia";
    freccia.textContent = espanso ? "▾" : "▸";
    const etichetta = document.createElement("span");
    etichetta.className = "nav-titolo-testo";
    etichetta.textContent = categoria;
    const conteggio = document.createElement("span");
    conteggio.className = "nav-titolo-conteggio";
    conteggio.textContent = lista.length;
    titolo.appendChild(freccia);
    titolo.appendChild(etichetta);
    titolo.appendChild(conteggio);
    titolo.addEventListener("click", () => {
      statoGruppi.set(categoria, !espanso);
      costruisciMenu();
    });
    gruppo.appendChild(titolo);

    const listaEl = document.createElement("div");
    listaEl.className = "nav-lista-gruppo";
    listaEl.hidden = !espanso;
    for (const calc of lista) {
      const riga = document.createElement("div");
      riga.className = "nav-riga";

      const btn = document.createElement("button");
      btn.textContent = calc.titolo;
      btn.className = "nav-btn" + (calc.id === calcolatoreAttuale ? " attivo" : "");
      btn.dataset.id = calc.id;
      btn.addEventListener("click", () => selezionaCalcolatore(calc.id));
      riga.appendChild(btn);

      const isPreferito = preferiti.includes(calc.id);
      const btnStar = document.createElement("button");
      btnStar.type = "button";
      btnStar.className = "nav-star" + (isPreferito ? " attivo" : "");
      btnStar.textContent = isPreferito ? "★" : "☆";
      btnStar.title = isPreferito ? "Rimuovi dai preferiti" : "Aggiungi ai preferiti";
      btnStar.addEventListener("click", (ev) => {
        ev.stopPropagation();
        toggleFavorito(calc.id);
        costruisciMenu();
      });
      riga.appendChild(btnStar);

      listaEl.appendChild(riga);
    }
    gruppo.appendChild(listaEl);
    nav.appendChild(gruppo);
  }
}

let modalitaConfrontoAttiva = false;

function selezionaCalcolatore(id) {
  document.querySelectorAll(".nav-btn").forEach(b => b.classList.toggle("attivo", b.dataset.id === id));
  const calc = CALCOLATORI.find(c => c.id === id);
  calcolatoreAttuale = id;
  modalitaConfrontoAttiva = false;
  try { localStorage.setItem("ultimoCalcolatore", id); } catch (e) { /* storage non disponibile */ }
  renderForm(calc);
  chiudiMenuMobile();
  const main = document.getElementById("contenuto-calcolatore");
  if (main) main.scrollTop = 0;
}

// ------------------------------------------------------------------ Menu mobile (drawer)

function apriMenuMobile() {
  document.getElementById("barra-laterale").classList.add("aperta");
  document.getElementById("overlay-menu").classList.add("visibile");
}

function chiudiMenuMobile() {
  document.getElementById("barra-laterale").classList.remove("aperta");
  document.getElementById("overlay-menu").classList.remove("visibile");
}

document.getElementById("btn-menu").addEventListener("click", apriMenuMobile);
document.getElementById("overlay-menu").addEventListener("click", chiudiMenuMobile);
document.getElementById("btn-chiudi-menu").addEventListener("click", chiudiMenuMobile);
document.addEventListener("keydown", (ev) => {
  if (ev.key === "Escape") chiudiMenuMobile();
});

function creaRigaListaValori(contenitore, valore) {
  const riga = document.createElement("div");
  riga.className = "lista-valori-riga";
  const inp = document.createElement("input");
  inp.type = "number";
  inp.step = "any";
  inp.value = valore;
  inp.className = "valore-input";
  const btnRm = document.createElement("button");
  btnRm.type = "button";
  btnRm.className = "azione-btn-piccolo";
  btnRm.textContent = "🗑️";
  btnRm.addEventListener("click", () => {
    if (contenitore.querySelectorAll(".lista-valori-riga").length > 1) riga.remove();
  });
  riga.appendChild(inp);
  riga.appendChild(btnRm);
  return riga;
}

function creaCampoListaValori(campo, idCampo) {
  const wrap = document.createElement("div");
  wrap.className = "campo";
  wrap.id = idCampo;

  const label = document.createElement("label");
  label.textContent = campo.label;
  wrap.appendChild(label);

  const contenitore = document.createElement("div");
  contenitore.className = "lista-valori-contenitore";
  const defaults = campo.defaultLista || [100, 100];
  for (const v of defaults) contenitore.appendChild(creaRigaListaValori(contenitore, v));
  wrap.appendChild(contenitore);

  const btnAdd = document.createElement("button");
  btnAdd.type = "button";
  btnAdd.className = "azione-btn";
  btnAdd.textContent = "➕ Aggiungi componente";
  btnAdd.addEventListener("click", () => {
    contenitore.appendChild(creaRigaListaValori(contenitore, defaults[0] ?? 100));
  });
  wrap.appendChild(btnAdd);

  if (campo.nota) {
    const nota = document.createElement("small");
    nota.className = "nota-campo";
    nota.textContent = campo.nota;
    wrap.appendChild(nota);
  }
  return wrap;
}

function creaCampoElemento(campo, prefisso) {
  const idCampo = `${prefisso}_${campo.name}`;
  if (campo.type === "lista_valori") return creaCampoListaValori(campo, idCampo);

  const wrap = document.createElement("div");
  wrap.className = "campo";

  const label = document.createElement("label");
  label.textContent = campo.label;
  label.htmlFor = idCampo;
  wrap.appendChild(label);

  let input;
  if (campo.type === "select") {
    input = document.createElement("select");
    for (const opz of campo.opzioni) {
      const opt = document.createElement("option");
      opt.value = opz;
      opt.textContent = opz;
      if (campo.default !== undefined && opz === String(campo.default)) opt.selected = true;
      input.appendChild(opt);
    }
  } else if (campo.type === "checkbox") {
    input = document.createElement("input");
    input.type = "checkbox";
    input.checked = !!campo.default;
  } else if (campo.type === "text") {
    input = document.createElement("input");
    input.type = "text";
    if (campo.default !== undefined) input.value = campo.default;
  } else {
    input = document.createElement("input");
    input.type = "number";
    if (campo.step !== undefined) input.step = campo.step;
    else input.step = "any";
    if (campo.default !== undefined) input.value = campo.default;
  }
  input.id = idCampo;
  input.name = campo.name;
  wrap.appendChild(input);

  if (campo.nota) {
    const nota = document.createElement("small");
    nota.className = "nota-campo";
    nota.textContent = campo.nota;
    wrap.appendChild(nota);
  }

  if (campo.rangePlausibile && campo.type !== "select" && campo.type !== "checkbox" && campo.type !== "text") {
    const avviso = document.createElement("small");
    avviso.className = "avviso-range";
    avviso.style.display = "none";
    wrap.appendChild(avviso);
    const [min, max] = campo.rangePlausibile;
    const controlla = () => {
      const v = parseFloat(input.value);
      if (!isNaN(v) && (v < min || v > max)) {
        avviso.textContent = `⚠️ Valore fuori dal range plausibile (${min}–${max}). Il calcolo procederà comunque.`;
        avviso.style.display = "block";
      } else {
        avviso.style.display = "none";
      }
    };
    input.addEventListener("input", controlla);
    controlla();
  }
  return wrap;
}

function leggiValoreCampo(campo, idCampo) {
  if (campo.type === "lista_valori") {
    const wrap = document.getElementById(idCampo);
    return [...wrap.querySelectorAll(".valore-input")]
      .map(inp => parseFloat(inp.value))
      .filter(v => !isNaN(v));
  }
  const el = document.getElementById(idCampo);
  if (campo.type === "checkbox") return el.checked;
  if (campo.type === "select" || campo.type === "text") return el.value;
  return parseFloat(el.value);
}

function leggiValoriPrefisso(calc, prefisso) {
  const kwargs = {};
  for (const campo of calc.campi) {
    kwargs[campo.name] = leggiValoreCampo(campo, `${prefisso}_${campo.name}`);
  }
  return kwargs;
}

function renderForm(calc) {
  const main = document.getElementById("contenuto-calcolatore");
  main.innerHTML = "";

  const titolo = document.createElement("h2");
  titolo.textContent = calc.titolo;
  main.appendChild(titolo);

  if (calc.nota) {
    const nota = document.createElement("p");
    nota.className = "nota-calcolatore";
    nota.textContent = calc.nota;
    main.appendChild(nota);
  }

  if (calc.speciale === "conversione") {
    renderConversione(main);
    return;
  }

  if (calc.speciale === "batch_cavi") {
    renderBatchCavi(main);
    return;
  }

  if (calc.campi.length === 0) {
    const divRisultati = document.createElement("div");
    divRisultati.id = "risultati";
    main.appendChild(divRisultati);
    eseguiCalcolo(calc, null);
    return;
  }

  const btnConfronto = document.createElement("button");
  btnConfronto.type = "button";
  btnConfronto.className = "azione-btn btn-toggle-confronto";
  btnConfronto.textContent = modalitaConfrontoAttiva ? "↩️ Torna a calcolo singolo" : "🔀 Confronta due scenari";
  btnConfronto.addEventListener("click", () => {
    modalitaConfrontoAttiva = !modalitaConfrontoAttiva;
    renderForm(calc);
  });
  main.appendChild(btnConfronto);

  if (modalitaConfrontoAttiva) {
    renderFormConfronto(calc, main);
    return;
  }

  const form = document.createElement("form");
  form.id = "form-calc";

  for (const campo of calc.campi) {
    form.appendChild(creaCampoElemento(campo, "f"));
  }

  const btnCalcola = document.createElement("button");
  btnCalcola.type = "submit";
  btnCalcola.className = "btn-calcola";
  btnCalcola.disabled = !motorePronto;
  btnCalcola.textContent = motorePronto ? "Calcola" : "Attendere — motore in caricamento…";
  form.appendChild(btnCalcola);

  main.appendChild(form);

  const divRisultati = document.createElement("div");
  divRisultati.id = "risultati";
  main.appendChild(divRisultati);

  form.addEventListener("submit", (ev) => {
    ev.preventDefault();
    eseguiCalcolo(calc, form);
  });
}

function renderFormConfronto(calc, main) {
  const griglia = document.createElement("div");
  griglia.className = "griglia-confronto";

  for (const [prefisso, etichetta] of [["a", "Scenario A"], ["b", "Scenario B"]]) {
    const colonna = document.createElement("div");
    colonna.className = "confronto-colonna";
    const h3 = document.createElement("h3");
    h3.textContent = etichetta;
    colonna.appendChild(h3);
    for (const campo of calc.campi) {
      colonna.appendChild(creaCampoElemento(campo, prefisso));
    }
    griglia.appendChild(colonna);
  }
  main.appendChild(griglia);

  const btnCalcola = document.createElement("button");
  btnCalcola.type = "button";
  btnCalcola.className = "btn-calcola";
  btnCalcola.disabled = !motorePronto;
  btnCalcola.textContent = motorePronto ? "Calcola entrambi" : "Attendere — motore in caricamento…";
  main.appendChild(btnCalcola);

  const divRisultati = document.createElement("div");
  divRisultati.id = "risultati";
  divRisultati.className = "griglia-confronto";
  main.appendChild(divRisultati);

  btnCalcola.addEventListener("click", () => {
    if (!bridge) {
      divRisultati.innerHTML = `<p class="errore">Il motore di calcolo non è ancora pronto. Attendere.</p>`;
      return;
    }
    divRisultati.innerHTML = "";
    for (const [prefisso, etichetta] of [["a", "Scenario A"], ["b", "Scenario B"]]) {
      const kwargs = leggiValoriPrefisso(calc, prefisso);
      const pannello = document.createElement("div");
      const h4 = document.createElement("h4");
      h4.textContent = etichetta;
      pannello.appendChild(h4);
      try {
        const risultato = chiamaBridge(calc.bridge, kwargs);
        if (risultato && risultato.errore) {
          pannello.innerHTML += `<p class="errore">⚠️ ${risultato.errore}</p>`;
        } else if (calc.risultati === "dict") {
          pannello.appendChild(renderTabellaDict(risultato));
        } else if (calc.risultati === "batteria") {
          pannello.appendChild(renderBatteria(risultato));
        } else if (calc.risultati === "derating") {
          pannello.appendChild(renderDerating(risultato));
        } else {
          pannello.appendChild(renderTabellaCampi(risultato, calc.risultati));
        }
      } catch (e) {
        pannello.innerHTML += `<p class="errore">Errore inatteso: ${e}</p>`;
      }
      divRisultati.appendChild(pannello);
    }
  });
}

// ------------------------------------------------------------------ Convertitore di unità (vista speciale)
//
// A differenza degli altri calcolatori, qui le opzioni del "Da"/"A" dipendono
// dalla grandezza scelta: il sistema statico di campi di CALCOLATORI non
// supporta select dipendenti, quindi questa vista è costruita a mano.

function renderConversione(main) {
  const campoCategoria = document.createElement("div");
  campoCategoria.className = "campo";
  const labelCategoria = document.createElement("label");
  labelCategoria.textContent = "Grandezza";
  const selCategoria = document.createElement("select");
  campoCategoria.appendChild(labelCategoria);
  campoCategoria.appendChild(selCategoria);
  main.appendChild(campoCategoria);

  const rigaUnita = document.createElement("div");
  rigaUnita.className = "conversione-riga-unita";

  const campoDa = document.createElement("div");
  campoDa.className = "campo";
  const labelDa = document.createElement("label");
  labelDa.textContent = "Da";
  const selDa = document.createElement("select");
  campoDa.appendChild(labelDa);
  campoDa.appendChild(selDa);

  const campoA = document.createElement("div");
  campoA.className = "campo";
  const labelA = document.createElement("label");
  labelA.textContent = "A";
  const selA = document.createElement("select");
  campoA.appendChild(labelA);
  campoA.appendChild(selA);

  rigaUnita.appendChild(campoDa);
  rigaUnita.appendChild(campoA);
  main.appendChild(rigaUnita);

  const campoValore = document.createElement("div");
  campoValore.className = "campo";
  const labelValore = document.createElement("label");
  labelValore.textContent = "Valore";
  const inputValore = document.createElement("input");
  inputValore.type = "number";
  inputValore.step = "any";
  inputValore.value = "1";
  campoValore.appendChild(labelValore);
  campoValore.appendChild(inputValore);
  main.appendChild(campoValore);

  const esito = document.createElement("div");
  main.appendChild(esito);

  const divRisultati = document.createElement("div");
  divRisultati.id = "risultati";
  main.appendChild(divRisultati);

  function aggiorna() {
    if (!motorePronto || !selDa.value || !selA.value) return;
    const valore = parseFloat(inputValore.value);
    if (Number.isNaN(valore)) {
      esito.innerHTML = `<p class="errore">Inserire un valore numerico.</p>`;
      divRisultati.innerHTML = "";
      return;
    }
    const r = chiamaBridge("conv_esegui_tutte", { categoria: selCategoria.value, da_unita: selDa.value, valore });
    if (r && r.errore) {
      esito.innerHTML = `<p class="errore">⚠️ ${r.errore}</p>`;
      divRisultati.innerHTML = "";
      return;
    }
    const aVal = r.risultati[selA.value];
    esito.innerHTML = "";
    const p = document.createElement("p");
    p.className = "conversione-esito";
    p.textContent = `${valore} ${selDa.value} = ${formattaNumero(aVal)} ${selA.value}`;
    esito.appendChild(p);

    const note = [];
    if (selCategoria.value === "Forza" || selCategoria.value === "Massa") {
      note.push("Forza e Massa sono grandezze fisicamente distinte.");
    }
    const unitaGauge = ["barg", "psig"];
    if (selCategoria.value === "Pressione" && (unitaGauge.includes(selDa.value) || unitaGauge.includes(selA.value))) {
      note.push("Le unità gauge (barg/psig) sono relative alla pressione atmosferica standard.");
    }
    if (note.length > 0) {
      const nota = document.createElement("small");
      nota.className = "nota-campo";
      nota.textContent = note.join(" ");
      esito.appendChild(nota);
    }

    divRisultati.innerHTML = "";
    divRisultati.appendChild(renderTabellaDict(r.risultati));
  }

  function popolaUnita(unitaPreferite) {
    const r = chiamaBridge("conv_lista_unita", { categoria: selCategoria.value });
    const unita = (r && r.unita) || [];
    selDa.innerHTML = "";
    selA.innerHTML = "";
    for (const u of unita) {
      selDa.appendChild(new Option(u, u));
      selA.appendChild(new Option(u, u));
    }
    if (unitaPreferite && unita.includes(unitaPreferite.da)) selDa.value = unitaPreferite.da;
    if (unitaPreferite && unita.includes(unitaPreferite.a)) {
      selA.value = unitaPreferite.a;
    } else {
      selA.selectedIndex = unita.length > 1 ? 1 : 0;
    }
    aggiorna();
  }

  function popolaCategorie() {
    const r = chiamaBridge("conv_lista_categorie", {});
    const categorie = (r && r.categorie) || [];
    selCategoria.innerHTML = "";
    for (const c of categorie) selCategoria.appendChild(new Option(c, c));
    popolaUnita();
  }

  selCategoria.addEventListener("change", () => popolaUnita());
  selDa.addEventListener("change", aggiorna);
  selA.addEventListener("change", aggiorna);
  inputValore.addEventListener("input", aggiorna);

  if (motorePronto) {
    popolaCategorie();
  } else {
    esito.innerHTML = `<p class="placeholder">In attesa del motore di calcolo…</p>`;
  }
}

// ------------------------------------------------------------------ Batch cavi (vista speciale)
//
// Come renderConversione, questa vista è costruita a mano: serve una tabella
// a righe dinamiche (aggiungi/rimuovi linea) che il sistema statico di campi
// di CALCOLATORI non supporta.

const COLONNE_BATCH = [
  { name: "nome", label: "Nome", type: "text" },
  { name: "fasi", label: "Sistema", type: "select", opzioni: ["Trifase", "Monofase"] },
  { name: "Ib_A", label: "Ib [A]", type: "number" },
  { name: "lunghezza_m", label: "Lunghezza [m]", type: "number" },
  { name: "cos_phi", label: "cos φ", type: "number" },
  { name: "isolante", label: "Isolante", type: "select", opzioni: ["PVC", "EPR"] },
  { name: "posa", label: "Posa", type: "select", opzioni: ["B1", "B2", "C", "E"] },
  { name: "T_amb", label: "T amb [°C]", type: "number" },
  { name: "n_circuiti", label: "N. circuiti", type: "number" },
  { name: "n_parallelo", label: "N. parallelo", type: "number" },
];

const RIGHE_BATCH_DEFAULT = [
  { nome: "Linea 1", fasi: "Trifase", Ib_A: 16, lunghezza_m: 30, cos_phi: 0.9, isolante: "PVC", posa: "C", T_amb: 30, n_circuiti: 1, n_parallelo: 1 },
  { nome: "Linea 2", fasi: "Monofase", Ib_A: 10, lunghezza_m: 25, cos_phi: 0.9, isolante: "PVC", posa: "C", T_amb: 30, n_circuiti: 1, n_parallelo: 1 },
];

function renderBatchCavi(main) {
  const contenitore = document.createElement("div");

  const scroll = document.createElement("div");
  scroll.className = "tabella-batch-scroll";
  const tabella = document.createElement("table");
  tabella.className = "tabella-batch";
  const thead = document.createElement("thead");
  const trHead = document.createElement("tr");
  for (const col of COLONNE_BATCH) {
    const th = document.createElement("th");
    th.textContent = col.label;
    trHead.appendChild(th);
  }
  trHead.appendChild(document.createElement("th"));
  thead.appendChild(trHead);
  tabella.appendChild(thead);
  const tbody = document.createElement("tbody");
  tabella.appendChild(tbody);
  scroll.appendChild(tabella);
  contenitore.appendChild(scroll);

  function aggiungiRiga(valori) {
    const tr = document.createElement("tr");
    for (const col of COLONNE_BATCH) {
      const td = document.createElement("td");
      let el;
      if (col.type === "select") {
        el = document.createElement("select");
        for (const opz of col.opzioni) el.appendChild(new Option(opz, opz));
        el.value = valori[col.name] ?? col.opzioni[0];
      } else {
        el = document.createElement("input");
        el.type = col.type === "number" ? "number" : "text";
        if (col.type === "number") el.step = "any";
        el.value = valori[col.name] ?? "";
      }
      el.name = col.name;
      td.appendChild(el);
      tr.appendChild(td);
    }
    const tdRimuovi = document.createElement("td");
    const btnRimuovi = document.createElement("button");
    btnRimuovi.type = "button";
    btnRimuovi.className = "btn-rimuovi-riga";
    btnRimuovi.textContent = "✕";
    btnRimuovi.title = "Rimuovi riga";
    btnRimuovi.addEventListener("click", () => tr.remove());
    tdRimuovi.appendChild(btnRimuovi);
    tr.appendChild(tdRimuovi);
    tbody.appendChild(tr);
  }

  for (const riga of RIGHE_BATCH_DEFAULT) aggiungiRiga(riga);

  const barraAzioni = document.createElement("div");
  barraAzioni.className = "barra-batch-azioni";

  const btnAggiungi = document.createElement("button");
  btnAggiungi.type = "button";
  btnAggiungi.className = "azione-btn";
  btnAggiungi.textContent = "➕ Aggiungi riga";
  btnAggiungi.addEventListener("click", () => aggiungiRiga({
    nome: `Linea ${tbody.children.length + 1}`, fasi: "Trifase", Ib_A: 16, lunghezza_m: 30,
    cos_phi: 0.9, isolante: "PVC", posa: "C", T_amb: 30, n_circuiti: 1, n_parallelo: 1,
  }));
  barraAzioni.appendChild(btnAggiungi);

  const btnCarica = document.createElement("button");
  btnCarica.type = "button";
  btnCarica.className = "azione-btn";
  btnCarica.textContent = "📂 Importa CSV";
  const inputFile = document.createElement("input");
  inputFile.type = "file";
  inputFile.accept = ".csv,text/csv";
  inputFile.style.display = "none";
  btnCarica.addEventListener("click", () => inputFile.click());
  inputFile.addEventListener("change", async () => {
    const file = inputFile.files[0];
    if (!file) return;
    try {
      const righe = parseCSVBatch(await file.text());
      for (const riga of righe) aggiungiRiga(riga);
      mostraToast(`Importate ${righe.length} righe dal CSV.`);
    } catch (e) {
      alert(`Errore nell'importazione del CSV: ${e}`);
    }
    inputFile.value = "";
  });
  barraAzioni.appendChild(btnCarica);
  barraAzioni.appendChild(inputFile);
  contenitore.appendChild(barraAzioni);

  const btnCalcola = document.createElement("button");
  btnCalcola.type = "button";
  btnCalcola.className = "btn-calcola";
  btnCalcola.disabled = !motorePronto;
  btnCalcola.textContent = motorePronto ? "Dimensiona tutte le linee" : "Attendere — motore in caricamento…";
  contenitore.appendChild(btnCalcola);

  const divRisultati = document.createElement("div");
  contenitore.appendChild(divRisultati);

  let ultimiRisultati = null;

  btnCalcola.addEventListener("click", () => {
    if (!bridge) {
      divRisultati.innerHTML = `<p class="errore">Il motore di calcolo non è ancora pronto. Attendere.</p>`;
      return;
    }
    const linee = [...tbody.children].map(tr => {
      const riga = {};
      for (const col of COLONNE_BATCH) {
        const el = tr.querySelector(`[name="${col.name}"]`);
        riga[col.name] = col.type === "number" ? parseFloat(el.value) : el.value;
      }
      return riga;
    });
    if (linee.length === 0) {
      divRisultati.innerHTML = `<p class="errore">Aggiungi almeno una linea.</p>`;
      return;
    }
    const risposta = chiamaBridge("batch_dimensiona_batch", { linee_json: JSON.stringify(linee) });
    if (risposta && risposta.errore) {
      divRisultati.innerHTML = `<p class="errore">⚠️ ${risposta.errore}</p>`;
      return;
    }
    ultimiRisultati = risposta.risultati;
    divRisultati.innerHTML = "";
    const nOk = ultimiRisultati.filter(r => r.esito === "OK").length;
    const nTot = ultimiRisultati.length;
    const riepilogo = document.createElement("p");
    riepilogo.className = "riepilogo-batch";
    riepilogo.textContent = nOk === nTot
      ? `✅ Tutte le ${nTot} linee sono a norma (sezione adeguata e caduta ≤ 4%).`
      : `⚠️ ${nOk}/${nTot} linee a norma. Controlla le righe con esito diverso da OK.`;
    divRisultati.appendChild(riepilogo);
    divRisultati.appendChild(renderTabellaRisultatiBatch(ultimiRisultati));

    const btnExport = document.createElement("button");
    btnExport.type = "button";
    btnExport.className = "azione-btn";
    btnExport.textContent = "⬇️ Esporta risultati in CSV";
    btnExport.addEventListener("click", () => scaricaCSVBatch(ultimiRisultati));
    divRisultati.appendChild(btnExport);
  });

  main.appendChild(contenitore);
}

const COLONNE_RISULTATO_BATCH = [
  "nome", "fasi", "Ib_A", "lunghezza_m", "sezione_mm2", "Iz_A", "utilizzo_pct",
  "caduta_V", "caduta_pct", "esito",
];

function renderTabellaRisultatiBatch(risultati) {
  const tabella = document.createElement("table");
  tabella.className = "tabella-risultati tabella-risultati-batch";
  const thead = document.createElement("thead");
  const trHead = document.createElement("tr");
  for (const col of COLONNE_RISULTATO_BATCH) {
    const th = document.createElement("th");
    th.textContent = col;
    trHead.appendChild(th);
  }
  thead.appendChild(trHead);
  tabella.appendChild(thead);
  const tbody = document.createElement("tbody");
  for (const riga of risultati) {
    const tr = document.createElement("tr");
    for (const col of COLONNE_RISULTATO_BATCH) {
      const td = document.createElement("td");
      td.textContent = col === "esito" ? riga[col] : formattaNumero(riga[col]);
      if (col === "esito") td.classList.add(riga[col] === "OK" ? "esito-ok" : "esito-errore");
      tr.appendChild(td);
    }
    tbody.appendChild(tr);
  }
  tabella.appendChild(tbody);
  return tabella;
}

function parseCSVBatch(testo) {
  const righe = testo.split(/\r?\n/).map(r => r.trim()).filter(r => r.length > 0);
  if (righe.length < 2) throw new Error("il file non contiene righe di dati.");
  const intestazioni = righe[0].split(",").map(h => h.trim());
  const risultato = [];
  for (const riga of righe.slice(1)) {
    const valori = riga.split(",").map(v => v.trim());
    const oggetto = {};
    intestazioni.forEach((h, i) => { oggetto[h] = valori[i]; });
    risultato.push(oggetto);
  }
  return risultato;
}

function scaricaCSVBatch(risultati) {
  const righe = [COLONNE_RISULTATO_BATCH];
  for (const r of risultati) righe.push(COLONNE_RISULTATO_BATCH.map(c => r[c]));
  const csv = righe.map(r => r.map(c => `"${String(c ?? "").replace(/"/g, '""')}"`).join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `dimensionamento_cavi_batch_${Date.now()}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

function leggiValoriForm(calc, form) {
  const kwargs = {};
  for (const campo of calc.campi) {
    kwargs[campo.name] = leggiValoreCampo(campo, `f_${campo.name}`);
  }
  return kwargs;
}

function eseguiCalcolo(calc, form) {
  const divRisultati = document.getElementById("risultati");
  if (!bridge) {
    divRisultati.innerHTML = `<p class="errore">Il motore di calcolo non è ancora pronto. Attendere.</p>`;
    return;
  }
  const kwargs = form ? leggiValoriForm(calc, form) : {};
  let risultato;
  try {
    risultato = chiamaBridge(calc.bridge, kwargs);
  } catch (e) {
    divRisultati.innerHTML = `<p class="errore">Errore inatteso: ${e}</p>`;
    return;
  }

  if (risultato && risultato.errore) {
    divRisultati.innerHTML = `<p class="errore">⚠️ ${risultato.errore}</p>`;
    return;
  }

  divRisultati.innerHTML = "";
  if (calc.risultati === "dict") {
    divRisultati.appendChild(renderTabellaDict(risultato));
  } else if (calc.risultati === "batteria") {
    divRisultati.appendChild(renderBatteria(risultato));
  } else if (calc.risultati === "derating") {
    divRisultati.appendChild(renderDerating(risultato));
  } else {
    divRisultati.appendChild(renderTabellaCampi(risultato, calc.risultati));
  }

  salvaInCronologia(calc, kwargs, risultato);
  const notaTextarea = creaCampoNote();
  divRisultati.appendChild(notaTextarea);
  divRisultati.appendChild(creaBarraAzioni(calc, kwargs, risultato, () => notaTextarea.querySelector("textarea").value));
}

function creaCampoNote() {
  const wrap = document.createElement("div");
  wrap.className = "campo campo-nota";
  const label = document.createElement("label");
  label.textContent = "📝 Note personali (opzionale, incluse nell'esportazione)";
  const textarea = document.createElement("textarea");
  textarea.rows = 2;
  textarea.placeholder = "Es. riferimento quadro, data sopralluogo, osservazioni…";
  wrap.appendChild(label);
  wrap.appendChild(textarea);
  return wrap;
}

function creaBarraAzioni(calc, kwargs, risultato, leggiNota) {
  const barra = document.createElement("div");
  barra.className = "barra-azioni";

  const azioni = [
    ["💾 Salva in progetto", () => apriDialogoProgetto(calc, kwargs, risultato, leggiNota())],
    ["📋 Copia", () => copiaRisultato(calc, kwargs, risultato, leggiNota())],
    ["⬇️ CSV", () => scaricaCSV(calc, kwargs, risultato, leggiNota())],
    ["📄 PDF", () => generaPDF(calc, kwargs, risultato, leggiNota())],
    ["🔲 QR", () => mostraQR(calc, kwargs, risultato, leggiNota())],
  ];
  if (navigator.share) {
    azioni.splice(3, 0, ["📤 Condividi", () => condividiRisultato(calc, kwargs, risultato, leggiNota())]);
  }

  for (const [etichetta, gestore] of azioni) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "azione-btn";
    btn.textContent = etichetta;
    btn.addEventListener("click", gestore);
    barra.appendChild(btn);
  }

  return barra;
}

function apriDialogoProgetto(calc, kwargs, risultato, nota) {
  const progettiEsistenti = Object.keys(leggiProgetti());
  const suggerimento = progettiEsistenti.length
    ? `Progetti esistenti: ${progettiEsistenti.join(", ")}.\nScrivi un nome esistente per aggiungere, o un nome nuovo per crearne uno.`
    : "Scrivi un nome per il nuovo progetto.";
  const nome = window.prompt(suggerimento, progettiEsistenti[0] || "");
  if (!nome) return;
  const voce = { calcId: calc.id, titolo: calc.titolo, input: kwargs, output: risultato };
  if (nota && nota.trim()) voce.nota = nota.trim();
  salvaInProgetto(nome.trim(), voce);
  alert(`Calcolo salvato nel progetto "${nome.trim()}".`);
}

// ------------------------------------------------------------------ Export e condivisione

function testoRisultato(calc, kwargs, risultato, nota) {
  const righeInput = Object.entries(kwargs).map(([k, v]) => `  ${k}: ${v}`).join("\n");
  const righeOutput = Object.entries(risultato).map(([k, v]) => `  ${k}: ${formattaNumero(v)}`).join("\n");
  let testo = `${calc.titolo}\n\nDati inseriti:\n${righeInput}\n\nRisultato:\n${righeOutput}`;
  if (nota && nota.trim()) testo += `\n\nNote:\n  ${nota.trim()}`;
  return testo;
}

function copiaRisultato(calc, kwargs, risultato, nota) {
  const testo = testoRisultato(calc, kwargs, risultato, nota);
  navigator.clipboard.writeText(testo)
    .then(() => mostraToast("Risultato copiato negli appunti."))
    .catch(() => alert("Copia non riuscita. Testo:\n\n" + testo));
}

function scaricaCSV(calc, kwargs, risultato, nota) {
  const righe = [["campo", "valore"]];
  for (const [k, v] of Object.entries(kwargs)) righe.push([`input.${k}`, v]);
  for (const [k, v] of Object.entries(risultato)) righe.push([`output.${k}`, formattaNumero(v)]);
  if (nota && nota.trim()) righe.push(["Note", nota.trim()]);
  const csv = righe.map(r => r.map(c => `"${String(c).replace(/"/g, '""')}"`).join(",")).join("\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `${calc.id}_${Date.now()}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}

function condividiRisultato(calc, kwargs, risultato, nota) {
  const testo = testoRisultato(calc, kwargs, risultato, nota);
  navigator.share({ title: calc.titolo, text: testo }).catch(() => { /* annullato dall'utente */ });
}

let _scriptCdnCaricati = {};
function caricaScriptCDN(url) {
  if (_scriptCdnCaricati[url]) return _scriptCdnCaricati[url];
  _scriptCdnCaricati[url] = new Promise((resolve, reject) => {
    const s = document.createElement("script");
    s.src = url;
    s.onload = resolve;
    s.onerror = reject;
    document.head.appendChild(s);
  });
  return _scriptCdnCaricati[url];
}

function mostraToast(messaggio) {
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = messaggio;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 2500);
}

function generaPDF(calc, kwargs, risultato, nota) {
  caricaScriptCDN("https://cdn.jsdelivr.net/npm/jspdf@2.5.1/dist/jspdf.umd.min.js").then(() => {
    const { jsPDF } = window.jspdf;
    const doc = new jsPDF();
    let y = 20;
    doc.setFontSize(16);
    doc.text(calc.titolo, 14, y);
    y += 10;
    doc.setFontSize(11);
    doc.text("Dati inseriti:", 14, y); y += 7;
    for (const [k, v] of Object.entries(kwargs)) { doc.text(`  ${k}: ${v}`, 14, y); y += 6; }
    y += 4;
    doc.text("Risultato:", 14, y); y += 7;
    for (const [k, v] of Object.entries(risultato)) { doc.text(`  ${k}: ${formattaNumero(v)}`, 14, y); y += 6; }
    if (nota && nota.trim()) {
      y += 4;
      doc.text("Note:", 14, y); y += 7;
      doc.text(`  ${nota.trim()}`, 14, y);
    }
    doc.save(`${calc.id}_${Date.now()}.pdf`);
  }).catch(() => alert("PDF non disponibile offline: serve una connessione la prima volta per scaricare la libreria."));
}

function mostraQR(calc, kwargs, risultato, nota) {
  caricaScriptCDN("https://cdn.jsdelivr.net/npm/qrcodejs@1.0.0/qrcode.min.js").then(() => {
    const overlay = document.createElement("div");
    overlay.className = "overlay-qr";
    const box = document.createElement("div");
    box.className = "box-qr";
    const titolo = document.createElement("p");
    titolo.textContent = calc.titolo;
    const divQr = document.createElement("div");
    const btnChiudi = document.createElement("button");
    btnChiudi.type = "button";
    btnChiudi.className = "azione-btn";
    btnChiudi.textContent = "Chiudi";
    btnChiudi.addEventListener("click", () => overlay.remove());
    box.appendChild(titolo);
    box.appendChild(divQr);
    box.appendChild(btnChiudi);
    overlay.appendChild(box);
    document.body.appendChild(overlay);
    new window.QRCode(divQr, { text: testoRisultato(calc, kwargs, risultato, nota), width: 220, height: 220 });
  }).catch(() => alert("QR non disponibile offline: serve una connessione la prima volta per scaricare la libreria."));
}

function formattaNumero(v) {
  if (v === null || v === undefined) return "n/d";
  if (typeof v === "number") {
    if (Number.isInteger(v)) return v.toString();
    if (v !== 0 && Math.abs(v) < 1e-4) return v.toExponential(3);
    return v.toFixed(4).replace(/0+$/, "").replace(/\.$/, "");
  }
  if (Array.isArray(v)) return v.map(formattaNumero).join(", ");
  if (v && typeof v === "object") {
    return Object.entries(v).map(([k, val]) => `${k}: ${formattaNumero(val)}`).join(", ");
  }
  return String(v);
}

function renderTabellaCampi(risultato, definizioni) {
  const tabella = document.createElement("table");
  tabella.className = "tabella-risultati";
  for (const def of definizioni) {
    const tr = document.createElement("tr");
    const tdLabel = document.createElement("td");
    tdLabel.textContent = def.label;
    const tdVal = document.createElement("td");
    tdVal.textContent = `${formattaNumero(risultato[def.key])} ${def.unit || ""}`.trim();
    tr.appendChild(tdLabel);
    tr.appendChild(tdVal);
    tabella.appendChild(tr);
  }
  return tabella;
}

function renderTabellaDict(risultato) {
  const tabella = document.createElement("table");
  tabella.className = "tabella-risultati";
  for (const [chiave, valore] of Object.entries(risultato)) {
    const tr = document.createElement("tr");
    const tdLabel = document.createElement("td");
    tdLabel.textContent = chiave;
    const tdVal = document.createElement("td");
    tdVal.textContent = formattaNumero(valore);
    tr.appendChild(tdLabel);
    tr.appendChild(tdVal);
    tabella.appendChild(tr);
  }
  return tabella;
}

function renderBatteria(risultato) {
  const contenitore = document.createElement("div");

  const riepilogo = document.createElement("table");
  riepilogo.className = "tabella-risultati";
  const righeRiepilogo = [
    ["Capacità effettiva pacco", `${formattaNumero(risultato.C_eff_pacco_Ah)} Ah`],
    ["Autonomia stimata", `${formattaNumero(risultato.t_autonomia_h)} h`],
    ["Corrente pacco", `${formattaNumero(risultato.I_pacco_A)} A`],
    ["Tensione nominale pacco", `${formattaNumero(risultato.tensione_nominale_pacco_V)} V`],
    ["Tensione iniziale → finale", `${formattaNumero(risultato.tensione_iniziale_V)} V → ${formattaNumero(risultato.tensione_finale_V)} V`],
  ];
  for (const [l, v] of righeRiepilogo) {
    const tr = document.createElement("tr");
    const td1 = document.createElement("td"); td1.textContent = l;
    const td2 = document.createElement("td"); td2.textContent = v;
    tr.appendChild(td1); tr.appendChild(td2);
    riepilogo.appendChild(tr);
  }
  contenitore.appendChild(riepilogo);

  contenitore.appendChild(grafico_svg(risultato.capacita_erogata_Ah, risultato.tensione_pacco_V,
    "Capacità erogata [Ah]", "Tensione pacco [V]"));

  return contenitore;
}

function renderDerating(risultato) {
  const contenitore = document.createElement("div");
  contenitore.appendChild(grafico_svg(risultato.T_amb_C, risultato.P_max_W,
    "T ambiente [°C]", "P massima [W]"));
  return contenitore;
}

function grafico_svg(xs, ys, labelX, labelY) {
  const larghezza = 600, altezza = 280, margine = 45;
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const minY = Math.min(...ys) * 0.98, maxY = Math.max(...ys) * 1.02;
  const scalaX = v => margine + (v - minX) / (maxX - minX || 1) * (larghezza - 2 * margine);
  const scalaY = v => altezza - margine - (v - minY) / (maxY - minY || 1) * (altezza - 2 * margine);

  const punti = xs.map((x, i) => `${scalaX(x)},${scalaY(ys[i])}`).join(" ");

  const svg = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  svg.setAttribute("viewBox", `0 0 ${larghezza} ${altezza}`);
  svg.classList.add("grafico-batteria");
  svg.innerHTML = `
    <line x1="${margine}" y1="${altezza - margine}" x2="${larghezza - margine}" y2="${altezza - margine}" class="asse" />
    <line x1="${margine}" y1="${margine}" x2="${margine}" y2="${altezza - margine}" class="asse" />
    <polyline points="${punti}" class="curva" />
    <text x="${larghezza / 2}" y="${altezza - 8}" class="etichetta-asse" text-anchor="middle">${labelX}</text>
    <text x="14" y="${altezza / 2}" class="etichetta-asse" text-anchor="middle" transform="rotate(-90 14 ${altezza / 2})">${labelY}</text>
  `;
  return svg;
}

// ------------------------------------------------------------------ Cronologia e progetti

function formattaData(iso) {
  const d = new Date(iso);
  return d.toLocaleString("it-IT", { dateStyle: "short", timeStyle: "short" });
}

function renderCronologia() {
  document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("attivo"));
  const main = document.getElementById("contenuto-calcolatore");
  main.innerHTML = "";

  const titolo = document.createElement("h2");
  titolo.textContent = "Cronologia calcoli";
  main.appendChild(titolo);

  const cronologia = leggiCronologia();
  if (cronologia.length === 0) {
    const vuoto = document.createElement("p");
    vuoto.className = "placeholder";
    vuoto.textContent = "Nessun calcolo eseguito finora.";
    main.appendChild(vuoto);
    return;
  }

  const btnCancella = document.createElement("button");
  btnCancella.type = "button";
  btnCancella.className = "azione-btn";
  btnCancella.textContent = "🗑️ Cancella cronologia";
  btnCancella.addEventListener("click", () => {
    if (confirm("Cancellare tutta la cronologia dei calcoli?")) {
      cancellaCronologia();
      renderCronologia();
    }
  });
  main.appendChild(btnCancella);

  const lista = document.createElement("div");
  lista.className = "lista-voci";
  for (const voce of cronologia) {
    const card = document.createElement("div");
    card.className = "card-voce";
    const intestazione = document.createElement("div");
    intestazione.className = "card-voce-intestazione";
    intestazione.innerHTML = `<strong>${voce.titolo}</strong><span>${formattaData(voce.timestamp)}</span>`;
    card.appendChild(intestazione);

    const dettaglio = document.createElement("div");
    dettaglio.className = "card-voce-dettaglio";
    dettaglio.textContent = "Output: " + Object.entries(voce.output)
      .map(([k, v]) => `${k}=${formattaNumero(v)}`).join(", ");
    card.appendChild(dettaglio);

    const btnRiapri = document.createElement("button");
    btnRiapri.type = "button";
    btnRiapri.className = "azione-btn";
    btnRiapri.textContent = "Riapri questo calcolo";
    btnRiapri.addEventListener("click", () => {
      const calc = CALCOLATORI.find(c => c.id === voce.calcId);
      if (!calc) { alert("Calcolatore non più disponibile."); return; }
      selezionaCalcolatore(calc.id);
      if (calc.campi.length > 0) {
        setTimeout(() => {
          const form = document.getElementById("form-calc");
          for (const campo of calc.campi) {
            const el = form.elements[campo.name];
            if (!el) continue;
            if (campo.type === "checkbox") el.checked = !!voce.input[campo.name];
            else el.value = voce.input[campo.name];
          }
        }, 0);
      }
    });
    card.appendChild(btnRiapri);
    lista.appendChild(card);
  }
  main.appendChild(lista);
}

function renderBarraBackup(main) {
  const barra = document.createElement("div");
  barra.className = "barra-azioni";

  const btnEsporta = document.createElement("button");
  btnEsporta.type = "button";
  btnEsporta.className = "azione-btn";
  btnEsporta.textContent = "⬇️ Esporta backup completo";
  btnEsporta.title = "Scarica cronologia e progetti in un unico file JSON, utile prima di cancellare la cache del browser.";
  btnEsporta.addEventListener("click", esportaBackupCompleto);
  barra.appendChild(btnEsporta);

  const inputFile = document.createElement("input");
  inputFile.type = "file";
  inputFile.accept = "application/json";
  inputFile.style.display = "none";
  inputFile.addEventListener("change", () => {
    const file = inputFile.files[0];
    if (!file) return;
    const modalita = confirm(
      "OK = unisci il backup ai dati attuali.\nAnnulla = sostituisci completamente i dati attuali con quelli del backup."
    ) ? "unisci" : "sostituisci";
    if (modalita === "sostituisci" && !confirm("Sei sicuro? I dati attuali (cronologia e progetti) verranno sovrascritti e persi.")) {
      inputFile.value = "";
      return;
    }
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const { nCronologia, nProgetti } = importaBackupCompleto(reader.result, modalita);
        mostraToast(`Importati ${nCronologia} calcoli in cronologia e ${nProgetti} progetti.`);
        renderProgetti();
      } catch (e) {
        alert("Errore durante l'importazione: " + e.message);
      }
      inputFile.value = "";
    };
    reader.readAsText(file);
  });
  barra.appendChild(inputFile);

  const btnImporta = document.createElement("button");
  btnImporta.type = "button";
  btnImporta.className = "azione-btn";
  btnImporta.textContent = "⬆️ Importa backup";
  btnImporta.addEventListener("click", () => inputFile.click());
  barra.appendChild(btnImporta);

  main.appendChild(barra);
}

function renderProgetti() {
  document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("attivo"));
  const main = document.getElementById("contenuto-calcolatore");
  main.innerHTML = "";

  const titolo = document.createElement("h2");
  titolo.textContent = "Progetti salvati";
  main.appendChild(titolo);

  renderBarraBackup(main);

  const progetti = leggiProgetti();
  const nomi = Object.keys(progetti);
  if (nomi.length === 0) {
    const vuoto = document.createElement("p");
    vuoto.className = "placeholder";
    vuoto.textContent = "Nessun progetto salvato. Usa \"💾 Salva in progetto\" sotto il risultato di un calcolo.";
    main.appendChild(vuoto);
    return;
  }

  for (const nome of nomi) {
    const sezione = document.createElement("div");
    sezione.className = "progetto-sezione";

    const intestazione = document.createElement("div");
    intestazione.className = "progetto-intestazione";
    const h3 = document.createElement("h3");
    h3.textContent = `📁 ${nome} (${progetti[nome].length})`;
    intestazione.appendChild(h3);

    const btnElimina = document.createElement("button");
    btnElimina.type = "button";
    btnElimina.className = "azione-btn";
    btnElimina.textContent = "Elimina progetto";
    btnElimina.addEventListener("click", () => {
      if (confirm(`Eliminare il progetto "${nome}" e tutti i suoi calcoli?`)) {
        eliminaProgetto(nome);
        renderProgetti();
      }
    });
    intestazione.appendChild(btnElimina);
    sezione.appendChild(intestazione);

    const lista = document.createElement("div");
    lista.className = "lista-voci";
    for (const voce of progetti[nome]) {
      const card = document.createElement("div");
      card.className = "card-voce";
      const int = document.createElement("div");
      int.className = "card-voce-intestazione";
      int.innerHTML = `<strong>${voce.titolo}</strong><span>${formattaData(voce.timestamp)}</span>`;
      card.appendChild(int);

      const dettaglio = document.createElement("div");
      dettaglio.className = "card-voce-dettaglio";
      dettaglio.textContent = "Output: " + Object.entries(voce.output)
        .map(([k, v]) => `${k}=${formattaNumero(v)}`).join(", ");
      card.appendChild(dettaglio);

      if (voce.nota) {
        const notaEl = document.createElement("div");
        notaEl.className = "card-voce-nota";
        notaEl.textContent = "📝 " + voce.nota;
        card.appendChild(notaEl);
      }

      const btnRimuovi = document.createElement("button");
      btnRimuovi.type = "button";
      btnRimuovi.className = "azione-btn";
      btnRimuovi.textContent = "Rimuovi";
      btnRimuovi.addEventListener("click", () => {
        rimuoviVoceProgetto(nome, voce.id);
        renderProgetti();
      });
      card.appendChild(btnRimuovi);
      lista.appendChild(card);
    }
    sezione.appendChild(lista);
    main.appendChild(sezione);
  }
}

// ------------------------------------------------------------------ Avvio

let ultimoCalcolatore = null;
try { ultimoCalcolatore = localStorage.getItem("ultimoCalcolatore"); } catch (e) { /* storage non disponibile */ }
const idIniziale = CALCOLATORI.find(c => c.id === ultimoCalcolatore) ? ultimoCalcolatore : CALCOLATORI[0].id;
// Impostato PRIMA del primo costruisciMenu() così la categoria del
// calcolatore iniziale risulta già espansa (vedi isGruppoEspanso).
calcolatoreAttuale = idIniziale;

costruisciMenu();

document.getElementById("ricerca-calcolatori").addEventListener("input", (ev) => {
  filtroRicerca = ev.target.value;
  costruisciMenu();
});

selezionaCalcolatore(idIniziale);

avviaPyodide().then(() => {
  if (new URLSearchParams(window.location.search).get("test") === "1") {
    caricaScriptCDN(`test.js?v=${VERSIONE_APP}`).then(() => mostraTestSuite());
  }
}).catch(err => {
  const badge = document.getElementById("stato-pyodide");
  if (!navigator.onLine) {
    badge.textContent = "❌ Sei offline e l'app non è ancora stata caricata una prima volta. Connettiti a Internet per il primo avvio, poi funzionerà anche offline.";
  } else {
    badge.textContent = "❌ Errore caricamento motore: " + err;
  }
  badge.className = "badge badge-errore";
  console.error(err);
});

document.getElementById("btn-cronologia").addEventListener("click", renderCronologia);
document.getElementById("btn-progetti").addEventListener("click", renderProgetti);

function aggiornaStatoConnessione() {
  const badge = document.getElementById("stato-connessione");
  if (navigator.onLine) {
    badge.textContent = "🟢 Online";
    badge.className = "badge badge-ok";
  } else {
    badge.textContent = "🔴 Offline (modalità locale)";
    badge.className = "badge badge-loading";
  }
}
window.addEventListener("online", aggiornaStatoConnessione);
window.addEventListener("offline", aggiornaStatoConnessione);
aggiornaStatoConnessione();
verificaPromemoriaBackup();

let eventoInstallazioneDifferito = null;
window.addEventListener("beforeinstallprompt", (ev) => {
  ev.preventDefault();
  eventoInstallazioneDifferito = ev;
  document.getElementById("btn-installa").hidden = false;
});
document.getElementById("btn-installa").addEventListener("click", async () => {
  if (!eventoInstallazioneDifferito) return;
  eventoInstallazioneDifferito.prompt();
  await eventoInstallazioneDifferito.userChoice;
  eventoInstallazioneDifferito = null;
  document.getElementById("btn-installa").hidden = true;
});
window.addEventListener("appinstalled", () => {
  document.getElementById("btn-installa").hidden = true;
});

const GIORNI_SOGLIA_PROMEMORIA_BACKUP = 30;

// Mostrato al massimo una volta per sessione: se l'utente lo chiude, non
// ricompare finché non ricarica la pagina (ma torna a comparire alla
// prossima apertura, finché non esporta davvero un backup — vedi
// esportaBackupCompleto() in storage.js, che aggiorna CHIAVE_ULTIMO_BACKUP).
function verificaPromemoriaBackup() {
  if (!esistonoDatiDaProteggere()) return;
  if (giorniDaUltimoBackup() < GIORNI_SOGLIA_PROMEMORIA_BACKUP) return;
  if (document.getElementById("banner-backup")) return;

  const banner = document.createElement("div");
  banner.id = "banner-backup";
  banner.className = "banner-promemoria";
  const testo = document.createElement("span");
  testo.textContent = "Non esporti un backup di cronologia e progetti da un po'. Se cancelli la cache del browser, li perderesti.";
  const btnEsporta = document.createElement("button");
  btnEsporta.textContent = "⬇️ Esporta backup ora";
  btnEsporta.addEventListener("click", () => {
    esportaBackupCompleto();
    banner.remove();
    mostraToast("Backup esportato.");
  });
  const btnChiudi = document.createElement("button");
  btnChiudi.className = "banner-chiudi";
  btnChiudi.textContent = "✕";
  btnChiudi.title = "Chiudi (ricomparirà al prossimo avvio se non esporti un backup)";
  btnChiudi.addEventListener("click", () => banner.remove());
  banner.appendChild(testo);
  banner.appendChild(btnEsporta);
  banner.appendChild(btnChiudi);
  document.body.prepend(banner);
}

function mostraBannerAggiornamento() {
  if (document.getElementById("banner-aggiornamento")) return;
  const banner = document.createElement("div");
  banner.id = "banner-aggiornamento";
  banner.className = "banner-aggiornamento";
  const testo = document.createElement("span");
  testo.textContent = "È disponibile una nuova versione dell'app.";
  const btn = document.createElement("button");
  btn.textContent = "Aggiorna ora";
  btn.addEventListener("click", () => window.location.reload());
  banner.appendChild(testo);
  banner.appendChild(btn);
  document.body.prepend(banner);
}

if ("serviceWorker" in navigator) {
  // Se all'avvio della pagina un service worker controlla già la pagina,
  // un successivo "controllerchange" significa che è stata installata una
  // nuova versione in background: avvisiamo l'utente invece di lasciarlo
  // bloccato in silenzio sulla versione vecchia in cache.
  const eraGiaControllata = !!navigator.serviceWorker.controller;
  navigator.serviceWorker.addEventListener("controllerchange", () => {
    if (eraGiaControllata) mostraBannerAggiornamento();
  });

  window.addEventListener("load", () => {
    navigator.serviceWorker.register("service-worker.js").catch(err => console.warn("Service worker non registrato:", err));
  });
}
