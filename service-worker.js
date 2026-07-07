// ==============================================================================
// service-worker.js — Cache dell'app shell (HTML/CSS/JS/py) e degli asset CDN
// (Pyodide, numpy, jsPDF, QR), per consentire l'uso completamente offline dopo
// una sola visita con connessione attiva.
// ==============================================================================

const CACHE_APP = "calc-industriale-app-v51";
const CACHE_RUNTIME = "calc-industriale-runtime-v51";

// Nota: niente "./" in questa lista — il server Streamlit (/app/static/...) non
// serve l'indice di directory e un singolo 404 farebbe fallire l'intero addAll.
// Le navigazioni verso la radice sono gestite dal fallback su index.html nel
// gestore fetch qui sotto.
const ASSET_APP = [
  "./index.html",
  "./style.css",
  "./app.js",
  "./calcolatori.js",
  "./storage.js",
  "./manifest.json",
  "./icons/icon.svg",
  "./icons/icon-192.png",
  "./icons/icon-512.png",
  "./py/costanti.py",
  "./py/formule.py",
  "./py/portata_cavo.py",
  "./py/batterie_litio.py",
  "./py/strumentazione.py",
  "./py/mark_vie.py",
  "./py/riferimento_rapido.py",
  "./py/grado_protezione_ip.py",
  "./py/motore_asincrono.py",
  "./py/canaline_passerelle.py",
  "./py/componenti_passivi.py",
  "./py/trasformatore.py",
  "./py/circuito_rlc.py",
  "./py/armonie_thd.py",
  "./py/batterie_ups.py",
  "./py/impianto_terra.py",
  "./py/selettivita_protezioni.py",
  "./py/fotovoltaico.py",
  "./py/gruppo_elettrogeno.py",
  "./py/quadro_elettrico.py",
  "./py/rifasamento_condensatori.py",
  "./py/caduta_tensione_bt.py",
  "./py/avviamento_motore.py",
  "./py/dissipatore.py",
  "./py/illuminotecnica.py",
  "./py/libreria_cavi.py",
  "./py/batch_cavi.py",
  "./py/costi_energetici.py",
  "./py/vibrazioni.py",
  "./py/resistenza_materiali.py",
  "./py/bulloneria.py",
  "./py/cuscinetti.py",
  "./py/molle.py",
  "./py/ruote_dentate.py",
  "./py/alberi_torsione.py",
  "./py/saldature.py",
  "./py/trasmissioni.py",
  "./py/nastri_trasportatori.py",
  "./py/pompe.py",
  "./py/perdite_carico.py",
  "./py/perdite_carico_distribuite.py",
  "./py/scambiatori.py",
  "./py/isolamento_termico.py",
  "./py/condotte_hvac.py",
  "./py/serbatoi.py",
  "./py/valvole_controllo.py",
  "./py/tubazione_pressione.py",
  "./py/pneumatica.py",
  "./py/trasduttori_pressione.py",
  "./py/rumore_industriale.py",
  "./py/performance_level.py",
  "./py/automazione.py",
  "./py/idraulica.py",
  "./py/bridge.py",
];

// Asset esterni (CDN) necessari per l'uso offline completo: motore Pyodide,
// numpy e le librerie dei pulsanti PDF/QR. Pre-scaricati all'installazione in
// modo NON bloccante: se il CDN non risponde, l'app shell resta comunque
// installata e questi file verranno ripresi al primo utilizzo online.
const ASSET_CDN = [
  "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.js",
  "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide-lock.json",
  "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.asm.js",
  "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/pyodide.asm.wasm",
  "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/python_stdlib.zip",
  "https://cdn.jsdelivr.net/pyodide/v0.26.4/full/numpy-1.26.4-cp312-cp312-pyodide_2024_0_wasm32.whl",
  "https://cdn.jsdelivr.net/npm/jspdf@2.5.1/dist/jspdf.umd.min.js",
  "https://cdn.jsdelivr.net/npm/qrcodejs@1.0.0/qrcode.min.js",
];

self.addEventListener("install", (event) => {
  // cache: "no-cache" forza la rivalidazione col server: senza, addAll può
  // pescare dalla cache HTTP del browser copie stantie dei file e "congelare"
  // la versione vecchia dentro la cache nuova (visto succedere davvero).
  event.waitUntil(
    caches.open(CACHE_APP).then((cache) =>
      cache.addAll(ASSET_APP.map((u) => new Request(u, { cache: "no-cache" })))
    )
  );
  // CDN: Pyodide/numpy non cambiano tra le release dell'app, quindi quando il
  // dispositivo si aggiorna riusiamo i file già presenti nella cache della
  // versione precedente (caches.match cerca in TUTTE le cache, comprese quelle
  // vecchie non ancora eliminate) e scarichiamo solo ciò che manca: un
  // aggiornamento costa pochi KB invece di ~15 MB.
  event.waitUntil(
    caches.open(CACHE_RUNTIME).then(async (cache) => {
      for (const url of ASSET_CDN) {
        const esistente = await caches.match(url);
        if (esistente) {
          await cache.put(url, esistente.clone());
        } else {
          await cache.add(url).catch(() => { /* ripreso al primo uso online */ });
        }
      }
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((nomi) =>
      Promise.all(
        nomi
          .filter((nome) => nome !== CACHE_APP && nome !== CACHE_RUNTIME)
          .map((nome) => caches.delete(nome))
      )
    )
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  const stessaOrigine = url.origin === self.location.origin;

  if (stessaOrigine) {
    // App shell: cache-first. Le richieste versionate (es. "app.js?v=23") o
    // con query di cache-busting ("/?nocache=...") ricadono sulla copia
    // pre-caricata senza query grazie a ignoreSearch: l'app si apre offline
    // anche se in cache esiste solo la versione "pulita" dell'URL.
    event.respondWith(
      caches.match(event.request)
        .then((r) => r || caches.match(event.request, { ignoreSearch: true }))
        .then((risposta) => {
          if (risposta) return risposta;
          return fetch(event.request).then((rete) => {
            if (rete.ok) {
              caches.open(CACHE_APP).then((cache) => cache.put(event.request, rete.clone()));
            }
            return rete;
          }).catch((err) => {
            // Offline e URL non in cache: le navigazioni (es. la radice "/"
            // del server standalone, non pre-elencata) ricadono su index.html.
            if (event.request.mode === "navigate") {
              return caches.match("./index.html");
            }
            throw err;
          });
        })
    );
  } else {
    // Asset CDN: rete con fallback su cache + salvataggio runtime, così anche
    // eventuali file non pre-elencati in ASSET_CDN restano disponibili offline
    // dopo il primo uso online.
    event.respondWith(
      caches.open(CACHE_RUNTIME).then((cache) =>
        fetch(event.request)
          .then((risposta) => {
            if (risposta.ok || risposta.type === "opaque") {
              cache.put(event.request, risposta.clone());
            }
            return risposta;
          })
          .catch(() => cache.match(event.request))
      )
    );
  }
});
