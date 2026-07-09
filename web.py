import csv
import io
import json
import math
import os
import re
import uuid
from datetime import datetime

import pandas as pd
import streamlit as st
try:
    import plotly.graph_objects as go
    _PLOTLY = True
except ImportError:
    _PLOTLY = False
try:
    import qrcode
    _QRCODE = True
except ImportError:
    _QRCODE = False

import automazione
import formule
import idraulica
import fulmini
import batterie_piombo
import misuratori_portata
import antincendio
import vibrazioni
import pneumatica
import trasmissioni
import pompe
import strumentazione
import resistenza_materiali as rm
import scambiatori
import perdite_carico
import motore_asincrono
import bulloneria
import illuminotecnica
import trasformatore as trafo
import circuito_rlc as rlc
import armonie_thd as thd
import batterie_ups as bat
import isolamento_termico as iso_t
import serbatoi
import valvole_controllo as valvole
import rumore_industriale as rumore
import dissipatore as diss
import nastri_trasportatori as nastri
import impianto_terra as terra
import selettivita_protezioni as selet
import fotovoltaico as fv
import gruppo_elettrogeno as ge
import cuscinetti as cus
import molle
import ruote_dentate as rd
import perdite_carico_distribuite as pcd
import trasduttori_pressione as tp
import quadro_elettrico as qe
import rifasamento_condensatori as rifas
import caduta_tensione_bt as cadbt
import tubazione_pressione as tubp
import avviamento_motore as avv
import alberi_torsione as alb
import saldature as sald
import condotte_hvac as hvac
import performance_level as pl_iso
import mark_vie as mv
import portata_cavo as pcav
import grado_protezione_ip as gip
import costi_energetici as cen
import libreria_cavi as libcavi
import riferimento_rapido as rifr
import canaline_passerelle as canp
import batch_cavi
import batterie_litio as blit
import componenti_passivi as cpas
import backup_compat
from costanti import SEZIONI_COMMERCIALI, TENSIONE_MONOFASE, TENSIONE_TRIFASE


st.set_page_config(
    page_title="Tool Industriale",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Streamlit mantiene st.session_state tra un rerun "a caldo" e l'altro anche
# quando il codice di questo script viene aggiornato (es. dopo un push, se una
# sessione era gia' aperta): un dict di risultato calcolato con la versione
# precedente del codice puo' non avere le chiavi che la versione nuova si
# aspetta, causando un KeyError in produzione (successo il 2026-07-08 con
# "frequenza_cpm" nella conversione vibrazioni). Rileviamo il cambio di codice
# confrontando l'mtime di questo file con quello registrato all'apertura della
# sessione, e in tal caso scartiamo le cache dei risultati per forzare un
# ricalcolo pulito coerente col codice attuale.
_MTIME_SCRIPT = os.path.getmtime(__file__)
if st.session_state.get("_mtime_avvio_sessione") != _MTIME_SCRIPT:
    if "_mtime_avvio_sessione" in st.session_state:
        for _k in list(st.session_state.keys()):
            # "_result*": risultati calcolati con la versione precedente del
            # codice. "_device_data": cache dei dati per-device (preferiti/
            # cronologia/progetti/impostazioni), ricaricata da disco al
            # prossimo _load_device_data() — anche qui un nuovo campo di
            # primo livello aggiunto in futuro non sarebbe altrimenti presente
            # nella cache di una sessione gia' aperta.
            if "_result" in _k or _k == "_device_data":
                del st.session_state[_k]
    st.session_state["_mtime_avvio_sessione"] = _MTIME_SCRIPT

st.markdown("""
<style>
/* ── Global ─────────────────────────────────────────── */
[data-testid="block-container"] { padding-top: 1.5rem; padding-bottom: 3rem; }
h1 { letter-spacing: -0.03em; font-size: 1.6rem !important; }
h2 { letter-spacing: -0.02em; font-size: 1.25rem !important; margin-top: 0.4rem !important; }
h3 { font-size: 1.05rem !important; color: #555; }

/* ── Sidebar ─────────────────────────────────────────── */
[data-testid="stSidebar"] { background: #0f1117; }
[data-testid="stSidebar"] * { color: #e8eaf0 !important; }
[data-testid="stSidebar"] .stRadio label { font-size: 0.92rem; padding: 6px 8px; border-radius: 6px; }
[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] { gap: 0.3rem; }
[data-testid="stSidebar"] .stRadio label:has(input:checked) {
    background: #1f6feb22;
    border-left: 3px solid #1f6feb;
}
[data-testid="stSidebar"] .stTextInput input {
    background: #1a1d27; border: 1px solid #2a2e3a; color: #e8eaf0 !important;
}

/* ── Card per sezione ────────────────────────────────── */
.ti-card {
    border-left: 4px solid #2196F3;
    background: #f8f9fc;
    border-radius: 0 8px 8px 0;
    padding: 0.75rem 1rem 0.65rem 1rem;
    margin-bottom: 1.1rem;
}
.ti-card.mec  { border-color: #FF9800; }
.ti-card.vib  { border-color: #9C27B0; }
.ti-card.termo{ border-color: #E91E63; }
.ti-card.plc  { border-color: #00BCD4; }
.ti-card.conv { border-color: #4CAF50; }
.ti-card.strum{ border-color: #607D8B; }
.ti-card h2   { margin: 0 0 0.15rem 0 !important; }
.ti-badge {
    display: inline-block;
    background: #e3eeff;
    color: #1a4fa0 !important;
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.04em;
    padding: 2px 7px;
    border-radius: 99px;
    margin-left: 8px;
    vertical-align: middle;
}
.ti-card.mec  .ti-badge { background:#fff3e0; color:#b35a00 !important; }
.ti-card.vib  .ti-badge { background:#f3e5f5; color:#6a1b9a !important; }
.ti-card.termo .ti-badge{ background:#fce4ec; color:#880e4f !important; }
.ti-card.plc  .ti-badge { background:#e0f7fa; color:#006064 !important; }
.ti-card.conv .ti-badge { background:#e8f5e9; color:#1b5e20 !important; }
.ti-card.strum .ti-badge{ background:#eceff1; color:#263238 !important; }

/* ── Barra utilizzo ──────────────────────────────────── */
.ti-bar-wrap { background:#e9ecef; border-radius:99px; height:12px; margin:6px 0 2px 0; }
.ti-bar-fill { height:12px; border-radius:99px; transition: width 0.4s ease; }

/* ── Home cards ──────────────────────────────────────── */
.home-card {
    border: 1px solid #e0e4ee;
    border-radius: 10px;
    padding: 1.1rem 1rem 0.9rem 1rem;
    text-align: center;
    cursor: pointer;
    transition: box-shadow 0.2s, transform 0.15s;
    background: #fff;
}
.home-card:hover { box-shadow: 0 4px 18px rgba(0,0,0,0.1); transform: translateY(-2px); }
.home-card .icon { font-size: 2rem; margin-bottom: 0.4rem; }
.home-card .label { font-weight: 700; font-size: 0.9rem; color: #222; }
.home-card .count { font-size: 0.75rem; color: #888; margin-top: 2px; }

/* ── Responsive mobile ──────────────────────────────── */
@media (max-width: 640px) {
    [data-testid="block-container"] { padding-top: 0.8rem; padding-left: 0.8rem; padding-right: 0.8rem; }
    h1 { font-size: 1.3rem !important; }

    /* Sidebar overlay a piena larghezza: la versione nativa di Streamlit è
       larga ~300px fissi, su schermi piu' strui lascia una fetta di body
       visibile e cliccabile dietro al menu aperto. Forziamo qui 100vw sia
       sulla larghezza che sulla traslazione (in % invece che px) cosi'
       l'apertura/chiusura resta coerente con qualunque larghezza schermo. */
    [data-testid="stSidebar"] { width: 100vw !important; min-width: 100vw !important; }
    [data-testid="stSidebar"][aria-expanded="false"] { transform: translateX(-100%) !important; }
    [data-testid="stSidebar"][aria-expanded="true"]  { transform: translateX(0) !important; }

    /* Selectbox lunghi: popover più basso per lasciare spazio alla tastiera
       virtuale, opzioni piu' alte per un tocco preciso col dito. */
    div[data-baseweb="popover"] ul { max-height: 38vh !important; }
    div[data-baseweb="popover"] li { padding-top: 10px !important; padding-bottom: 10px !important; }
    button { min-height: 2.6rem; }
}
</style>
""", unsafe_allow_html=True)


# ── helpers ──────────────────────────────────────────────────────────────────

def _card_open(categoria: str, titolo: str, norma: str = ""):
    cls_map = {
        "elett": "elett", "conv": "conv", "mec": "mec",
        "vib": "vib", "plc": "plc", "strum": "strum", "termo": "termo",
    }
    cls = cls_map.get(categoria, "")
    badge = f'<span class="ti-badge">{norma}</span>' if norma else ""
    st.markdown(
        f'<div class="ti-card {cls}"><h2>{titolo}{badge}</h2></div>',
        unsafe_allow_html=True,
    )


def _barra_utilizzo(valore_pct: float, etichetta: str = "Utilizzo"):
    v = min(max(valore_pct, 0.0), 120.0)
    frac = min(v / 100.0, 1.0)
    if v < 70:
        colore = "#4CAF50"
    elif v < 90:
        colore = "#FF9800"
    else:
        colore = "#f44336"
    pct_display = f"{v:.1f}%"
    st.markdown(
        f"**{etichetta}**: {pct_display}"
        f'<div class="ti-bar-wrap">'
        f'<div class="ti-bar-fill" style="width:{frac*100:.1f}%;background:{colore};"></div>'
        f"</div>",
        unsafe_allow_html=True,
    )


# Font Unicode per il PDF: cerca un TTF di sistema con copertura ampia
# (Ω, lettere greche, frecce, apici). Su Windows c'è sempre arial.ttf; su Linux
# si prova DejaVuSans. Se nessuno è disponibile si ricade su sanitizzazione.
_PDF_FONT_CANDIDATES = [
    r"C:\Windows\Fonts\arial.ttf",
    r"C:\Windows\Fonts\segoeui.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/Library/Fonts/Arial.ttf",
]


@st.cache_resource
def _pdf_font_path() -> str | None:
    for p in _PDF_FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    return None


def _pdf_sanitize(testo: str) -> str:
    """Fallback senza font Unicode: rende il testo in latin-1 sostituendo i
    simboli più comuni dei calcoli con equivalenti ASCII."""
    rimpiazzi = {
        "Ω": "ohm", "·": ".", "→": "->", "²": "2", "³": "3", "µ": "u", "μ": "u",
        "°": "deg", "±": "+/-", "ε": "epsilon", "σ": "sigma", "τ": "tau",
        "λ": "lambda", "β": "beta", "η": "eta", "φ": "phi", "ω": "omega",
        "≤": "<=", "≥": ">=", "√": "sqrt", "×": "x", "–": "-", "—": "-",
        "★": "*", "☆": "*", "✓": "ok", "⚠️": "!", "Δ": "delta",
    }
    for k, v in rimpiazzi.items():
        testo = testo.replace(k, v)
    return testo.encode("latin-1", "replace").decode("latin-1")


def _pdf_bytes(strumento: str, dati: dict) -> bytes:
    """Genera un PDF report (titolo + data + tabella campo/valore)."""
    from fpdf import FPDF

    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    font_path = _pdf_font_path()
    if font_path:
        pdf.add_font("rep", "", font_path)
        pdf.add_font("rep", "B", font_path)
        fam, conv = "rep", (lambda s: s)
    else:
        fam, conv = "Helvetica", _pdf_sanitize

    pdf.set_font(fam, "B", 15)
    pdf.cell(0, 10, conv("Tool Industriale - Report calcolo"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(fam, "B", 12)
    pdf.cell(0, 8, conv(strumento), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(fam, "", 9)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 6, conv("Generato il " + datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
             new_x="LMARGIN", new_y="NEXT")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    # Tabella campo/valore
    larghezza = pdf.w - 2 * pdf.l_margin
    w_campo = larghezza * 0.55
    w_valore = larghezza - w_campo
    pdf.set_font(fam, "B", 10)
    pdf.set_fill_color(235, 238, 245)
    pdf.cell(w_campo, 8, conv("Campo"), border=1, fill=True)
    pdf.cell(w_valore, 8, conv("Valore"), border=1, fill=True, new_x="LMARGIN", new_y="NEXT")
    pdf.set_font(fam, "", 10)
    for k, v in dati.items():
        y0 = pdf.get_y()
        x0 = pdf.get_x()
        # multi_cell per la colonna campo, poi valore allineato
        pdf.multi_cell(w_campo, 7, conv(str(k)), border=1, new_x="RIGHT", new_y="TOP", max_line_height=6)
        y1 = pdf.get_y()
        pdf.set_xy(x0 + w_campo, y0)
        pdf.multi_cell(w_valore, 7, conv(str(v)), border=1, new_x="LMARGIN", new_y="TOP", max_line_height=6)
        pdf.set_y(max(y1, pdf.get_y()))

    out = pdf.output()
    return bytes(out)


def _export_csv_button(strumento: str, dati: dict, key: str) -> None:
    """Mostra i pulsanti di esportazione (CSV + PDF) per un risultato.

    dati: dict {etichetta: valore} nell'ordine in cui vanno esportati.
    Nota: il nome storico è rimasto per non toccare i ~150 punti di chiamata;
    in realtà ora genera entrambi i formati.
    """
    nome_file = strumento.replace(" ", "_").replace("/", "-")

    nota = st.text_area(
        "📝 Note personali (opzionale, incluse nell'esportazione):",
        key=f"{key}_nota", height=68,
    )
    dati_export = dict(dati)
    if nota.strip():
        dati_export["Note"] = nota.strip()

    with st.expander("💾 Salva questo calcolo in un progetto"):
        opzioni_proj = ["➕ Nuovo progetto..."] + _lista_progetti()
        scelta_proj = st.selectbox("Progetto:", opzioni_proj, key=f"{key}_proj_sel")
        if scelta_proj == "➕ Nuovo progetto...":
            nome_proj = st.text_input("Nome nuovo progetto:", key=f"{key}_proj_nome")
        else:
            nome_proj = scelta_proj
        if st.button("💾 Salva nel progetto", key=f"{key}_proj_btn"):
            try:
                _salva_calcolo_in_progetto(nome_proj, strumento, dati_export)
                st.success(f"Calcolo salvato nel progetto '{nome_proj.strip()}'.")
            except ValueError as e:
                st.error(str(e))

    if _QRCODE:
        with st.expander("📱 QR Code (per smartphone)"):
            righe_qr = [strumento] + [f"{k}: {v}" for k, v in dati_export.items()]
            testo_qr = "\n".join(righe_qr)
            if len(testo_qr) > 700:
                testo_qr = testo_qr[:697] + "..."
            st.image(_qr_bytes(testo_qr), caption="Inquadra per leggere il risultato sullo schermo del telefono", width=220)
            st.download_button(
                "📥 Scarica QR Code",
                data=_qr_bytes(testo_qr),
                file_name=f"{nome_file}_qr.png",
                mime="image/png",
                key=f"{key}_qr_dl",
            )

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Strumento", strumento])
    writer.writerow(["Data/ora", datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
    writer.writerow([])
    writer.writerow(["Campo", "Valore"])
    for k, v in dati_export.items():
        writer.writerow([k, v])

    col_csv, col_pdf = st.columns(2)
    with col_csv:
        st.download_button(
            "📥 Esporta CSV",
            data=buf.getvalue(),
            file_name=f"{nome_file}.csv",
            mime="text/csv",
            key=f"{key}_csv",
            use_container_width=True,
        )
    with col_pdf:
        try:
            st.download_button(
                "📄 Esporta PDF",
                data=_pdf_bytes(strumento, dati_export),
                file_name=f"{nome_file}.pdf",
                mime="application/pdf",
                key=f"{key}_pdf",
                use_container_width=True,
            )
        except Exception:
            st.caption("PDF non disponibile")


def _qr_bytes(testo: str) -> bytes:
    """Genera un QR code PNG (bytes) che codifica il testo fornito."""
    img = qrcode.make(testo, error_correction=qrcode.constants.ERROR_CORRECT_M)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def _warn_range(valore: float, minimo: float, massimo: float,
                etichetta: str, unita: str = "") -> None:
    """Avviso NON bloccante se un valore è fuori da un range plausibile.

    Non interrompe il calcolo: serve solo a segnalare un possibile errore di
    inserimento (es. tensione BT a 50000 V, cos phi a 3, temperatura a 200 °C).
    """
    try:
        v = float(valore)
    except (TypeError, ValueError):
        return
    if v < minimo or v > massimo:
        u = f" {unita}" if unita else ""
        st.warning(
            f"⚠️ {etichetta}: il valore {v:g}{u} è fuori dal range plausibile "
            f"({minimo:g}–{massimo:g}{u}). Verifica di non aver sbagliato a digitare."
        )


def _lista_componenti_interattiva(chiave: str, etichetta_unita: str, valore_default: float = 100.0) -> list:
    """Lista interattiva aggiungi/rimuovi per componenti in numero variabile
    (es. resistori, induttori, condensatori in serie/parallelo).

    Usa id univoci (non l'indice di posizione) come chiave dei widget, così
    rimuovere un componente in mezzo alla lista non fa "scivolare" per errore
    il valore di un altro componente su una chiave diversa.

    Ritorna la lista dei valori correnti, nello stesso ordine mostrato a schermo.
    """
    chiave_ids = f"_{chiave}_ids"
    chiave_contatore = f"_{chiave}_contatore"
    if chiave_ids not in st.session_state:
        st.session_state[chiave_ids] = [0, 1]
        st.session_state[chiave_contatore] = 2

    valori = []
    for comp_id in list(st.session_state[chiave_ids]):
        col_val, col_rm = st.columns([6, 1])
        with col_val:
            v = st.number_input(
                f"Componente #{comp_id + 1} [{etichetta_unita}]",
                value=valore_default, min_value=0.000001, key=f"{chiave}_v_{comp_id}",
            )
            valori.append(v)
        with col_rm:
            st.write("")  # allinea verticalmente il bottone con il campo
            if len(st.session_state[chiave_ids]) > 1:
                if st.button("🗑️", key=f"{chiave}_rm_{comp_id}"):
                    st.session_state[chiave_ids].remove(comp_id)
                    st.rerun()

    if st.button("➕ Aggiungi componente", key=f"{chiave}_add"):
        nuovo_id = st.session_state[chiave_contatore]
        st.session_state[chiave_ids].append(nuovo_id)
        st.session_state[chiave_contatore] += 1
        st.rerun()

    return valori


# ── Rilevamento dispositivo ────────────────────────────────────────────────────
# Niente JS: lo User-Agent arriva già nell'header della request, quindi il ramo
# mobile/desktop si decide prima di renderizzare qualunque cosa (zero flicker).

def is_mobile() -> bool:
    try:
        ua = st.context.headers.get("User-Agent", "").lower()
    except Exception:
        ua = ""
    return any(k in ua for k in ("android", "iphone", "ipad", "mobile"))


_IS_MOBILE = is_mobile()


# ── Indice globale strumenti (per ricerca) ─────────────────────────────────────
# Copia delle liste passate ai selectbox "Seleziona Strumento" di ogni sezione:
# se si aggiunge un'opzione lì, aggiungerla anche qui per mantenerla cercabile.

def _build_tool_index() -> list:
    idx = []

    def _add(tools, sezione, select_key):
        for t in tools:
            idx.append((t, sezione, select_key))

    _add(idraulica.ottieni_categorie().keys(), "⚖️  Conversioni", "conv_cat")

    _add([
        "Legge di Ohm", "Analisi Potenze e Corrente", "Convertitore Potenze (kW / HP / kVA)",
        "Rendimento Motore (P_out -> P_in -> Corrente)", "Rifasamento Industriale (kVAR)",
        "Caduta di Tensione", "Portata Cavo / Sezione Minima (CEI-UNEL 35024)",
        "Grado di Protezione IP (IEC 60529)",
        "Corrente di Cortocircuito (Icc)", "Dimensionamento Protezioni",
        "Carico Trifase Equilibrato", "Carico Trifase Non Equilibrato", "Trasformatore",
        "Circuito RLC", "Armonie e THD", "Batterie e UPS", "Dissipatore Termico",
        "Impianto di Terra", "Selettività Protezioni", "Fotovoltaico", "Gruppo Elettrogeno",
        "Quadro Elettrico — Dissipazione", "Rifasamento Condensatori",
        "Caduta Tensione BT (CEI 64-8)", "Avviamento Motore Asincrono",
        "Motore Asincrono — Dati di Targa", "Motore Asincrono — Classi IE (Efficienza)",
        "Tabelle di Riferimento Rapido (cavi, colori, IP, IE)",
        "Canaline / Passerelle — Riempimento e Derating",
        "Portata Cavo + Caduta di Tensione (combinato)",
        "Dimensionamento Cavi in Batch (tabella/CSV)",
        "Caduta di Tensione — Confronto A/B",
        "Componenti Passivi (Resistori, Condensatori, Induttori)",
    ], "⚡  Calcoli Elettrici", "elett_tipo")

    _add([
        "Info CPU e Memoria RX3i", "Info Modulo Analogico", "Tipi Dati",
        "Scalatura Analogica (Raw -> Engineering)", "Scalatura Inversa (Engineering -> Raw / Setpoint)",
        "Esplosione Parola nei Bit", "Composizione WORD da Bit", "Calcolo Memoria RX3i",
    ], "🤖  PLC e Automazione", "plc_tool")

    _add([
        "Conversione Grandezze Vibrazionali", "Classificazione ISO 10816 (Severita)",
        "Frequenza Naturale Massa-Molla", "Velocita Critica Albero", "Squilibrio Residuo ISO 1940",
    ], "〜  Vibrazioni", "vib_tool")

    _add([
        "Trasmissione Semplice (ingranaggi / cinghia / catena)", "Riduttore a Piu Stadi",
        "Geometria Cinghia", "Potenza-Coppia-Velocita", "Punto di Lavoro Pompa", "Potenza Pompa",
        "NPSH Disponibile", "Numero Specifico di Giri (ns)", "Proprieta Sezione", "Calcolo Trave",
        "Verifica a Flessione", "Trazione / Compressione", "Perdite di Carico Concentrate",
        "Perdite di Carico Distribuite (Darcy-Weisbach)", "Bulloneria — Serraggio",
        "Bulloneria — Verifica", "Bulloneria — Flangia", "Nastri Trasportatori",
        "Cuscinetti — Durata L10 (ISO 281)", "Molle Meccaniche", "Ruote Dentate — Verifica Lewis",
        "Alberi — Torsione e Flessione", "Saldature a Cordone d'Angolo",
        "Tubazione in Pressione (EN 13480)",
    ], "🔩  Meccanica", "mec_tool")

    _add([
        "Converti Portata Normalizzata", "Caduta di Pressione Tubazione Aria",
        "Dimensionamento Serbatoio", "Potenza Compressore", "Segnale mA ↔ Tensione",
        "Termocoppia mV → °C (NIST)", "Pt100 — Temperatura ↔ Resistenza",
        "Errore di Misura e Incertezza", "Taratura Strumento (generica)",
        "Interpolazione da Certificato di Taratura", "Caratterizzazione RTD (R0/α reali)",
        "Offset Taratura Termocoppia", "Guida — Come effettuare una misura corretta",
        "Valvola di Controllo Cv/Kv", "Trasduttore di Pressione 4-20mA",
    ], "🔧  Pneumatica & Strumenti", "strum_tool")

    _add([
        "Scambiatori — Bilancio Termico", "Scambiatori — Area LMTD", "Scambiatori — Metodo NTU-ε",
        "Illuminotecnica — Numero Lampade", "Illuminotecnica — Indice Locale",
        "Illuminotecnica — Fattore di Manutenzione MF", "Illuminotecnica — Potenza e LENI",
        "Isolamento Termico — Parete Piana", "Isolamento Termico — Tubo Cilindrico",
        "Serbatoi — Volume e Pressione", "Serbatoi — Svuotamento (Torricelli)",
        "Condotte Aria HVAC", "Misuratori di Portata",
    ], "🌡️  Termotecnica & Impianti", "termo_tool")

    _add([
        "Rumore — Somma Sorgenti", "Rumore — LEX,8h Esposizione", "Rumore — Verifica DPI (SNR)",
        "Rumore — Attenuazione per Distanza", "Performance Level — EN ISO 13849",
        "Costi Energetici e Payback Efficientamento",
        "Protezione Fulmini (LPS)", "Antincendio — Rete Idranti/Naspi (UNI 10779)",
    ], "🔒  Sicurezza & Utilities", "sic_tool")

    _add([
        "Riferimento — Schede I/O", "Riferimento — Architetture di Ridondanza",
        "Riferimento — Terminologia ControlST/ToolboxST", "Riferimento — Suite ControlST / WorkstationST",
        "Riferimento — Troubleshooting (sintomo → manuale)", "Calcolo — Scalatura Canale PAIC",
        "Calcolo — Voting TMR (2oo3)", "Calcolo — MTBF Serie (Simplex)",
        "Calcolo — Disponibilità TMR 2oo3", "Calcolo — Corrente Assorbita TBCI",
        "Calcolo — Derating Relè TRLYH1x", "Calcolo — RTD Pt100/Pt1000 (IEC 60751)",
        "Calcolo — Termocoppia (ITS-90)", "Calcolo — Diagnostica Loop 4–20 mA (NE43)",
        "Calcolo — Velocità / Sovravelocità Turbina",
    ], "🎛️  Mark VI/VIe & ToolboxST", "mv_tool")

    return idx


_TOOL_INDEX = _build_tool_index()


# ── Preferiti e cronologia (persistenza per dispositivo) ───────────────────────
# Niente account/login: un cookie identifica il browser, i dati vivono in un
# file JSON per dispositivo. Nessuno storage condiviso tra dispositivi diversi.

_FAV_DIR = os.path.join(os.path.dirname(__file__), "data", "device_prefs")
os.makedirs(_FAV_DIR, exist_ok=True)


def _get_device_id() -> str:
    if "device_id" in st.session_state:
        return st.session_state["device_id"]
    try:
        cid = st.context.cookies.get("ti_device_id")
    except Exception:
        cid = None
    if not cid:
        cid = uuid.uuid4().hex
        # st.markdown(unsafe_allow_html=True) inietta via innerHTML: i browser
        # ignorano i tag <script> inseriti cosi', quindi il cookie non verrebbe
        # mai impostato davvero. st.iframe con una stringa HTML renderizza un
        # iframe con un documento vero, dove lo script esegue ed eredita il
        # cookie jar del dominio corrente. height=0 non e' ammesso da st.iframe
        # (StreamlitInvalidHeightError): 1 e' il minimo valido.
        st.iframe(
            f"<script>document.cookie='ti_device_id={cid}; max-age=31536000; path=/';</script>",
            height=1,
        )
    st.session_state["device_id"] = cid
    return cid


def _device_data_path(device_id: str) -> str:
    return os.path.join(_FAV_DIR, f"{device_id}.json")


def _load_device_data() -> dict:
    if "_device_data" in st.session_state:
        return st.session_state["_device_data"]
    path = _device_data_path(_get_device_id())
    data = {"favorites": [], "history": [], "projects": {}, "settings": {}, "checklist_mv": {}}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            pass
    data.setdefault("favorites", [])
    data.setdefault("history", [])
    data.setdefault("projects", {})
    data.setdefault("settings", {})
    data.setdefault("checklist_mv", {})
    st.session_state["_device_data"] = data
    return data


def _save_device_data(data: dict) -> None:
    try:
        with open(_device_data_path(_get_device_id()), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError:
        pass


# ── Banner "cosa è cambiato" dopo un aggiornamento ──────────────────────────
# Stesso numero di versione usato per la PWA (VERSIONE_APP in
# static/pwa_offline/app.js) e per CHANGELOG.md, letto qui in sola lettura:
# le release di questo progetto aggiornano entrambe le piattaforme insieme
# (vedi bump_versione_pwa.py e release.py), quindi non serve un contatore
# separato per Streamlit.

_CHANGELOG_PATH = os.path.join(os.path.dirname(__file__), "CHANGELOG.md")

_NOMI_SEZIONE_CHANGELOG = {
    "Added": "Aggiunte", "Changed": "Modifiche", "Fixed": "Correzioni", "Removed": "Rimozioni",
}


def _leggi_versione_app() -> str:
    percorso = os.path.join(os.path.dirname(__file__), "static", "pwa_offline", "app.js")
    try:
        testo = open(percorso, "r", encoding="utf-8").read()
    except OSError:
        return ""
    m = re.search(r'VERSIONE_APP\s*=\s*"(\d+)"', testo)
    return m.group(1) if m else ""


def _analizza_sezioni_blocco(blocco: str) -> list:
    """Ritorna [(nome_sezione, [bullet, ...]), ...] per UN blocco versione
    (testo che parte da "## [vN] - data"), gestendo bullet su più righe
    (continuazione: riga che non inizia con "-" né "#" viene accodata al
    bullet precedente)."""
    sezioni = []
    sezione_corrente = None
    for riga in blocco.split("\n")[1:]:
        r = riga.strip()
        if not r:
            continue
        if r.startswith("### "):
            sezione_corrente = [r[4:].strip(), []]
            sezioni.append(sezione_corrente)
        elif r.startswith("- "):
            if sezione_corrente is None:
                sezione_corrente = ["", []]
                sezioni.append(sezione_corrente)
            sezione_corrente[1].append(r[2:].strip())
        elif sezione_corrente and sezione_corrente[1]:
            sezione_corrente[1][-1] += " " + r
    return sezioni


def _elenca_blocchi_changelog(testo: str) -> list:
    """Ritorna [(numero_versione, testo_blocco), ...] per ogni blocco
    "## [vN] - data" trovato nel changelog, nell'ordine in cui compaiono nel file."""
    match_iter = list(re.finditer(r"^## \[v(\d+)\]", testo, re.MULTILINE))
    blocchi = []
    for i, m in enumerate(match_iter):
        fine = match_iter[i + 1].start() if i + 1 < len(match_iter) else len(testo)
        blocchi.append((int(m.group(1)), testo[m.start():fine]))
    return blocchi


def _estrai_novita_intervallo(versione_vista, versione_corrente: str) -> list:
    """Ritorna [(numero_versione, sezioni), ...] per ogni versione tra
    versione_vista (esclusa) e versione_corrente (inclusa), dalla più recente
    alla più vecchia — copre chi ha saltato più di un aggiornamento. Se
    versione_vista manca/non è valida o l'intervallo risulta vuoto, ricade
    sulla sola versione corrente."""
    try:
        testo = open(_CHANGELOG_PATH, "r", encoding="utf-8").read()
    except OSError:
        return []
    blocchi = _elenca_blocchi_changelog(testo)
    corrente = int(versione_corrente)

    selezionati = []
    if versione_vista:
        try:
            vista = int(versione_vista)
            selezionati = [(n, b) for n, b in blocchi if vista < n <= corrente]
        except ValueError:
            selezionati = []
    if not selezionati:
        selezionati = [(n, b) for n, b in blocchi if n == corrente]

    selezionati.sort(key=lambda x: x[0], reverse=True)
    return [(n, _analizza_sezioni_blocco(b)) for n, b in selezionati]


def _scrivi_cookie_versione_vista(versione: str) -> None:
    # Stessa tecnica di _get_device_id(): st.markdown(unsafe_allow_html=True)
    # inietta via innerHTML e i browser ignorano gli <script> inseriti così,
    # mentre st.iframe con una stringa HTML crea un documento vero il cui
    # script eredita il cookie jar del dominio corrente.
    st.iframe(
        f"<script>document.cookie='ti_ultima_versione_vista={versione}; max-age=31536000; path=/';</script>",
        height=1,
    )


def _chiudi_banner_novita(versione: str) -> None:
    # Eseguito da Streamlit come on_click PRIMA del rerun innescato dal click
    # (a differenza di un st.rerun() manuale dentro il corpo della funzione,
    # che interromperebbe lo script troppo presto perché l'iframe che scrive
    # il cookie faccia in tempo a caricarsi ed eseguire il suo script: provato,
    # il cookie non veniva scritto). Qui mutiamo solo session_state; l'iframe
    # si scrive nel rerun successivo, con tutto il tempo di uno script completo.
    st.session_state["_banner_novita_chiuso"] = versione


def _mostra_banner_novita() -> None:
    versione = _leggi_versione_app()
    if not versione:
        return
    try:
        vista_cookie = st.context.cookies.get("ti_ultima_versione_vista")
    except Exception:
        vista_cookie = None
    if vista_cookie == versione:
        return

    if st.session_state.get("_banner_novita_chiuso") == versione:
        # Chiuso in questa sessione: st.context.cookies riflette solo i cookie
        # presenti al caricamento della pagina, quindi anche dopo aver scritto
        # il cookie via iframe non lo vedremo qui finché la pagina non viene
        # ricaricata da capo — scriviamolo una sola volta (session_state come
        # guardia) invece di ripeterlo a ogni rerun successivo.
        if not st.session_state.get("_cookie_versione_vista_scritto"):
            _scrivi_cookie_versione_vista(versione)
            st.session_state["_cookie_versione_vista_scritto"] = True
        return

    if vista_cookie is None:
        # Primo avvio in assoluto: non ha senso mostrare tutta la cronologia
        # a un utente nuovo, segniamo solo la versione attuale come vista.
        _scrivi_cookie_versione_vista(versione)
        return

    blocchi = _estrai_novita_intervallo(vista_cookie, versione)
    if not blocchi:
        # Niente da mostrare (es. subito dopo il deploy, prima che il CHANGELOG
        # sia stato committato): segna comunque come vista per non ritentare la
        # lettura del file a ogni sessione.
        _scrivi_cookie_versione_vista(versione)
        return

    multiplo = len(blocchi) > 1
    testo_md = (
        f"**✨ Novità dalla versione v{vista_cookie} alla v{versione}**\n\n" if multiplo
        else f"**✨ Novità della versione v{versione}**\n\n"
    )
    for num_v, sezioni in blocchi:
        if multiplo:
            testo_md += f"**v{num_v}**\n"
        for nome_sez, bullet in sezioni:
            etichetta = _NOMI_SEZIONE_CHANGELOG.get(nome_sez, nome_sez)
            if etichetta:
                testo_md += f"_{etichetta}_\n"
            for b in bullet:
                testo_md += f"- {b}\n"
        testo_md += "\n"

    col1, col2 = st.columns([30, 1])
    with col1:
        st.info(testo_md)
    with col2:
        st.button("✕", key="banner_novita_chiudi", help="Chiudi",
                   on_click=_chiudi_banner_novita, args=(versione,))


def _entry_key(sezione: str, sel_key: str, nome_tool: str) -> str:
    return f"{sezione}||{sel_key}||{nome_tool}"


def _track_history(sezione: str, sel_key: str, nome_tool: str) -> None:
    data = _load_device_data()
    fk = _entry_key(sezione, sel_key, nome_tool)
    hist = data["history"]
    if hist and hist[0]["fk"] == fk:
        return
    hist = [h for h in hist if h["fk"] != fk]
    hist.insert(0, {"fk": fk, "nome": nome_tool, "sezione": sezione, "sel_key": sel_key})
    data["history"] = hist[:15]
    _save_device_data(data)


def _is_favorite(sezione: str, sel_key: str, nome_tool: str) -> bool:
    data = _load_device_data()
    fk = _entry_key(sezione, sel_key, nome_tool)
    return any(f["fk"] == fk for f in data["favorites"])


def _toggle_favorite(sezione: str, sel_key: str, nome_tool: str) -> None:
    data = _load_device_data()
    fk = _entry_key(sezione, sel_key, nome_tool)
    favs = data["favorites"]
    existing = next((f for f in favs if f["fk"] == fk), None)
    if existing:
        favs.remove(existing)
    else:
        favs.insert(0, {"fk": fk, "nome": nome_tool, "sezione": sezione, "sel_key": sel_key})
    data["favorites"] = favs[:30]
    _save_device_data(data)


def _lista_progetti() -> list:
    return list(_load_device_data()["projects"].keys())


def _salva_calcolo_in_progetto(nome_progetto: str, strumento: str, dati: dict) -> None:
    nome_progetto = nome_progetto.strip()
    if not nome_progetto:
        raise ValueError("Indicare un nome per il progetto.")
    data = _load_device_data()
    voci = data["projects"].setdefault(nome_progetto, [])
    voci.append({
        "strumento": strumento,
        "dati": dati,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    _save_device_data(data)


def _elimina_voce_progetto(nome_progetto: str, idx: int) -> None:
    data = _load_device_data()
    voci = data["projects"].get(nome_progetto, [])
    if 0 <= idx < len(voci):
        voci.pop(idx)
        _save_device_data(data)


def _elimina_progetto(nome_progetto: str) -> None:
    data = _load_device_data()
    data["projects"].pop(nome_progetto, None)
    _save_device_data(data)


def _render_fav_toggle(sezione: str, sel_key: str, nome_tool: str) -> None:
    """Traccia lo strumento corrente nella cronologia e mostra il pulsante preferiti."""
    _track_history(sezione, sel_key, nome_tool)
    is_fav = _is_favorite(sezione, sel_key, nome_tool)
    label = "★ Nei preferiti" if is_fav else "☆ Aggiungi ai preferiti"
    if st.button(label, key=f"fav_{sel_key}"):
        _toggle_favorite(sezione, sel_key, nome_tool)
        st.rerun()


def _render_entry_row(entry: dict, icon: str, key_prefix: str, idx: int, compact: bool = False) -> None:
    def _testo():
        st.markdown(
            f"{icon} **{entry['nome']}**  \n"
            f"<span style='color:#888;font-size:0.78rem'>{entry['sezione'].strip()}</span>",
            unsafe_allow_html=True,
        )

    def _apri():
        if st.button("Apri", key=f"{key_prefix}_{idx}", use_container_width=True):
            st.session_state["_nav_goto"] = entry["sezione"]
            st.session_state["_nav_tool_key"] = entry["sel_key"]
            st.session_state["_nav_tool_val"] = entry["nome"]
            st.rerun()

    if compact:
        _testo()
        _apri()
    else:
        c1, c2 = st.columns([5, 1])
        with c1:
            _testo()
        with c2:
            _apri()


# ── Sidebar ───────────────────────────────────────────────────────────────────
# Intercetta la navigazione dalle card Home PRIMA che il radio venga renderizzato.
# I bottoni scrivono su "_nav_goto"; qui lo trasferiamo su "sidebar_cat" e lo puliamo.

_SEZIONI = [
    "🏠  Home",
    "⚖️  Conversioni",
    "⚡  Calcoli Elettrici",
    "🤖  PLC e Automazione",
    "〜  Vibrazioni",
    "🔩  Meccanica",
    "🔧  Pneumatica & Strumenti",
    "🌡️  Termotecnica & Impianti",
    "🔒  Sicurezza & Utilities",
    "🎛️  Mark VI/VIe & ToolboxST",
    "📁  Progetti Salvati",
]

if "_nav_goto" in st.session_state:
    dest = st.session_state.pop("_nav_goto")
    if dest in _SEZIONI:
        st.session_state["sidebar_cat"] = dest

if "_nav_tool_key" in st.session_state:
    _tk = st.session_state.pop("_nav_tool_key")
    _tv = st.session_state.pop("_nav_tool_val", None)
    if _tk and _tv is not None:
        st.session_state[_tk] = _tv

_mostra_banner_novita()

with st.sidebar:
    st.markdown("## ⚙️ Tool Industriale")
    st.markdown("---")

    filtro_sez = st.text_input(
        "Cerca sezione",
        key="sidebar_search",
        placeholder="🔎 Cerca sezione...",
        label_visibility="collapsed",
    )
    _sezioni_filtrate = (
        [s for s in _SEZIONI if filtro_sez.lower() in s.lower()] if filtro_sez else _SEZIONI
    )
    if "🏠  Home" not in _sezioni_filtrate and not filtro_sez:
        _sezioni_filtrate = _SEZIONI
    if not _sezioni_filtrate:
        st.caption("Nessuna sezione trovata.")
        _sezioni_filtrate = _SEZIONI

    if st.session_state.get("sidebar_cat") not in _sezioni_filtrate:
        st.session_state["sidebar_cat"] = _sezioni_filtrate[0]

    categoria = st.radio(
        "Sezione",
        _sezioni_filtrate,
        key="sidebar_cat",
        label_visibility="collapsed",
    )

    _dd_sidebar = _load_device_data()
    if _dd_sidebar["favorites"]:
        st.markdown("---")
        with st.expander(f"⭐ Preferiti ({len(_dd_sidebar['favorites'])})", expanded=False):
            for i, entry in enumerate(_dd_sidebar["favorites"][:10]):
                _render_entry_row(entry, "⭐", "fav_sidebar", i, compact=True)

    st.markdown("---")
    _schermo_grande = st.checkbox(
        "🔍 Modalità schermo grande",
        value=_dd_sidebar["settings"].get("schermo_grande", False),
        key="schermo_grande_toggle",
        help="Aumenta testi, pulsanti e campi per leggere e toccare meglio da distante o con i guanti.",
    )
    if _schermo_grande != _dd_sidebar["settings"].get("schermo_grande", False):
        _dd_sidebar["settings"]["schermo_grande"] = _schermo_grande
        _save_device_data(_dd_sidebar)

    _ha_dati_da_proteggere = bool(_dd_sidebar["favorites"] or _dd_sidebar["history"] or _dd_sidebar["projects"])
    if _ha_dati_da_proteggere:
        _ultimo_backup_iso = _dd_sidebar["settings"].get("ultimo_backup_il")
        _giorni_da_backup = (
            (datetime.now() - datetime.fromisoformat(_ultimo_backup_iso)).days
            if _ultimo_backup_iso else None
        )
        if _giorni_da_backup is None or _giorni_da_backup >= 30:
            st.markdown("---")
            st.warning(
                "Non esporti un backup di preferiti/cronologia/progetti da un po'. "
                "Se cambi dispositivo o cancelli i dati del browser, li perderesti. "
                "Vai su **Progetti Salvati → Scambio con la versione offline** per esportarlo.",
                icon="💾",
            )

    st.markdown("---")
    st.markdown("[📱 **Versione offline / installabile**](https://lock909.github.io/Convertitore-misure/)")
    st.caption(
        "Aprila una volta con connessione e installala: da lì in poi i calcoli "
        "funzionano anche senza internet. I progetti si scambiano con i pulsanti "
        "di backup nella sezione Progetti Salvati."
    )

    st.markdown("---")
    st.caption("v4.0 · CEI 64-8 · ISO 10816 · IEC 60034-30 · EN 12464-1")

if st.session_state.get("schermo_grande_toggle"):
    st.markdown("""
<style>
[data-testid="block-container"] * { font-size: 1.12rem !important; }
h1 { font-size: 2.0rem !important; }
h2 { font-size: 1.55rem !important; }
h3 { font-size: 1.3rem !important; }
button, [data-testid="stBaseButton-secondary"], [data-testid="stBaseButton-primary"] {
    min-height: 3.2rem !important; font-size: 1.15rem !important; padding: 0.5rem 1rem !important;
}
input, textarea { font-size: 1.15rem !important; padding: 0.55rem !important; }
[data-baseweb="select"] { font-size: 1.15rem !important; min-height: 3.0rem !important; }
[data-testid="stNumberInputStepUp"], [data-testid="stNumberInputStepDown"] {
    min-width: 2.8rem !important; min-height: 2.8rem !important;
}
[data-testid="stMetricValue"] { font-size: 2.2rem !important; }
[data-testid="stMetricLabel"] { font-size: 1.05rem !important; }
.stCheckbox label, .stRadio label { font-size: 1.1rem !important; }
</style>
""", unsafe_allow_html=True)


# ── Home ──────────────────────────────────────────────────────────────────────

_NAV_MAP = {
    "⚖️  Conversioni":              "⚖️  Conversioni",
    "⚡  Calcoli Elettrici":        "⚡  Calcoli Elettrici",
    "🤖  PLC e Automazione":        "🤖  PLC e Automazione",
    "〜  Vibrazioni":               "〜  Vibrazioni",
    "🔩  Meccanica":                "🔩  Meccanica",
    "🔧  Pneumatica & Strumenti":   "🔧  Pneumatica & Strumenti",
    "🌡️  Termotecnica & Impianti":  "🌡️  Termotecnica & Impianti",
    "🎛️  Mark VI/VIe & ToolboxST":  "🎛️  Mark VI/VIe & ToolboxST",
}

if categoria == "🏠  Home":
    st.title("⚙️ Strumento Multifunzione Industriale")
    st.markdown("Calcoli tecnici per ingegneria industriale. Cerca o clicca una sezione per iniziare.")

    _dd = _load_device_data()

    if _dd["favorites"]:
        with st.expander(f"⭐ Preferiti ({len(_dd['favorites'])})", expanded=True):
            for i, entry in enumerate(_dd["favorites"][:10]):
                _render_entry_row(entry, "⭐", "fav_home", i)

    if _dd["history"]:
        with st.expander(f"🕘 Usati di recente ({len(_dd['history'])})", expanded=False):
            for i, entry in enumerate(_dd["history"][:10]):
                _render_entry_row(entry, "🕘", "hist_home", i)

    if _dd["favorites"] or _dd["history"]:
        st.markdown("---")

    filtro_home = st.text_input(
        "Cerca uno strumento",
        key="home_search",
        placeholder="🔎 Cerca uno strumento... (es. motori, vibrazioni, PLC)",
        label_visibility="collapsed",
    )
    st.markdown("---")

    _HOME_CARDS = [
        ("⚖️", "Conversioni",          "⚖️  Conversioni",            "Unità, pressione, temperatura", "Universale"),
        ("⚡", "Calcoli Elettrici",    "⚡  Calcoli Elettrici",       "Ohm, motori, sezioni, IE",      "CEI 64-8"),
        ("🤖", "PLC e Automazione",    "🤖  PLC e Automazione",       "GE RX3i, scalature, tipi dato", "IEC 61131-3"),
        ("〜", "Vibrazioni",           "〜  Vibrazioni",              "ISO 10816, squilibrio rotori",  "ISO 10816"),
        ("🔩", "Meccanica",            "🔩  Meccanica",               "Travi, pompe, bulloni, trasm.", "ISO 898-1"),
        ("🔧", "Pneumatica & Strum.",  "🔧  Pneumatica & Strumenti",  "Aria compressa, TC, Pt100",     "IEC 60751"),
        ("🌡️", "Termotecnica",         "🌡️  Termotecnica & Impianti", "Scambiatori, illuminotecnica",  "EN 12464-1"),
        ("🔒", "Sicurezza & Utilities","🔒  Sicurezza & Utilities",   "Rumore, serbatoi, valvole, UPS","ISO 9612"),
        ("🎛️", "Mark VI/VIe",          "🎛️  Mark VI/VIe & ToolboxST", "Schede I/O, TMR, ToolboxST",    "GEH-6721"),
    ]

    if filtro_home:
        f = filtro_home.lower()
        _cards_show = [c for c in _HOME_CARDS if f in c[1].lower() or f in c[3].lower()]
        _tool_matches = [t for t in _TOOL_INDEX if f in t[0].lower()]
    else:
        _cards_show = _HOME_CARDS
        _tool_matches = []

    if filtro_home and _tool_matches:
        st.markdown(f"**Strumenti trovati ({len(_tool_matches)})**")
        for j, (nome_tool, sez, sel_key) in enumerate(_tool_matches[:15]):
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(f"🔍 **{nome_tool}**  \n<span style='color:#888;font-size:0.78rem'>{sez.strip()}</span>",
                            unsafe_allow_html=True)
            with c2:
                if st.button("Apri", key=f"tool_match_{j}", use_container_width=True):
                    st.session_state["_nav_goto"] = sez
                    st.session_state["_nav_tool_key"] = sel_key
                    st.session_state["_nav_tool_val"] = nome_tool
                    st.rerun()
        st.markdown("---")

    if filtro_home and not _cards_show and not _tool_matches:
        st.info("Nessuno strumento corrisponde alla ricerca.")

    n_cols = 1 if _IS_MOBILE else 4
    cols = st.columns(n_cols)
    for i, (icon, label, nav_key, desc, norma) in enumerate(_cards_show):
        with cols[i % n_cols]:
            st.markdown(
                f'<div style="border:1px solid #e0e4ee;border-radius:10px;padding:0.8rem 0.7rem 0.6rem;'
                f'text-align:center;background:#fff;margin-bottom:0.5rem;">'
                f'<div style="font-size:1.9rem;line-height:1.2">{icon}</div>'
                f'<div style="font-weight:700;font-size:0.88rem;color:#222;margin:4px 0 2px">{label}</div>'
                f'<div style="font-size:0.73rem;color:#666">{desc}</div>'
                f'<div style="font-size:0.68rem;color:#aaa;margin-top:3px">{norma}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
            if st.button("Apri", key=f"home_btn_{i}", use_container_width=True):
                st.session_state["_nav_goto"] = nav_key
                st.rerun()
    st.markdown("---")
    st.caption("CEI 64-8 · ISO 10816 · ISO 1940 · IEC 60751 · NIST ITS-90 · ISO 898-1 · EN 12464-1 · IEC 60034-30")


elif categoria == "⚖️  Conversioni":
    _card_open("conv", "⚖️ Convertitore di Unità", "Universale")
    categories = idraulica.ottieni_categorie()

    modo_conv = st.radio(
        "Modalita:",
        ["Da -> A (standard)", "Multi-unita live (scrivi in qualsiasi campo)"],
        key="conv_modo",
        horizontal=True,
    )

    if modo_conv == "Da -> A (standard)":
        cat = st.selectbox("Grandezza:", list(categories.keys()), key="conv_cat")
        units = list(categories[cat].keys())

        col1, col2 = st.columns(2)
        with col1:
            from_u = st.selectbox("Da:", units, index=0, key="conv_from")
        with col2:
            to_u = st.selectbox("A:", units, index=1 if len(units) > 1 else 0, key="conv_to")

        val = st.number_input("Valore:", value=0.0, format="%.6g", key="conv_val")
        try:
            res = idraulica.esegui_conversione(cat, from_u, to_u, val)
            st.success(f"Risultato: {res:.6g} {to_u}")
        except ValueError as e:
            st.error(str(e))

        if cat in ("Forza", "Massa"):
            st.caption("Nota: Forza e Massa sono grandezze fisicamente distinte.")
        if cat == "Pressione" and (from_u in ("barg", "psig") or to_u in ("barg", "psig")):
            st.caption("Nota: le unita gauge sono relative alla pressione atmosferica.")

    else:
        cat_live = st.selectbox("Grandezza:", list(categories.keys()), key="live_cat")
        units_live = list(categories[cat_live].keys())

        pfx = f"lv_{cat_live}_"
        src_st = f"lv_src_{cat_live}"

        if st.session_state.get("lv_prev_cat") != cat_live:
            st.session_state["lv_prev_cat"] = cat_live
            st.session_state[src_st] = None
            for u in units_live:
                st.session_state[pfx + u] = 0.0

        source_key = st.session_state.get(src_st)
        source_unit = source_key.replace(pfx, "") if source_key else None
        source_val = float(st.session_state.get(source_key, 0.0)) if source_key else 0.0

        computed = {}
        if source_unit and source_unit in units_live:
            for u in units_live:
                try:
                    computed[u] = idraulica.esegui_conversione(cat_live, source_unit, u, source_val)
                except Exception:
                    computed[u] = 0.0
        else:
            computed = {u: 0.0 for u in units_live}

        for u in units_live:
            k = pfx + u
            if k != source_key:
                st.session_state[k] = computed.get(u, 0.0)

        def _make_cb(unit_name: str, _pfx: str = pfx, _src_st: str = src_st):
            def _cb():
                st.session_state[_src_st] = _pfx + unit_name
            return _cb

        if source_unit:
            st.caption(f"Input attivo: {source_unit}. Scrivi in un altro campo per cambiare unita di input.")
        else:
            st.caption("Scrivi un valore in qualsiasi campo per convertire in tutte le altre unita.")

        n_cols = 4 if len(units_live) > 8 else 3 if len(units_live) > 4 else 2
        cols_live = st.columns(n_cols)

        for i, u in enumerate(units_live):
            k = pfx + u
            is_src = k == source_key
            label = f"{u} (input)" if is_src else u
            with cols_live[i % n_cols]:
                st.number_input(label, key=k, format="%.6g", on_change=_make_cb(u))

        if cat_live == "Pressione":
            st.caption("Nota: barg e psig sono relativi alla pressione atmosferica. Zero corrisponde alla pressione ambiente.")
        elif cat_live in ("Forza", "Massa"):
            st.caption("Nota: Forza (N) e Massa (kg) sono grandezze fisicamente distinte.")
        elif cat_live == "Temperatura":
            st.caption("Nota: conversioni non lineari. Usa r per Rankine.")


elif categoria == "⚡  Calcoli Elettrici":
    _card_open("elett", "⚡ Calcoli Elettrici", "CEI 64-8")
    tipo = st.selectbox(
        "Tipo di Analisi:",
        [
            "Legge di Ohm",
            "Analisi Potenze e Corrente",
            "Convertitore Potenze (kW / HP / kVA)",
            "Rendimento Motore (P_out -> P_in -> Corrente)",
            "Rifasamento Industriale (kVAR)",
            "Caduta di Tensione",
            "Portata Cavo / Sezione Minima (CEI-UNEL 35024)",
            "Grado di Protezione IP (IEC 60529)",
            "Corrente di Cortocircuito (Icc)",
            "Dimensionamento Protezioni",
            "Carico Trifase Equilibrato",
            "Carico Trifase Non Equilibrato",
            "Trasformatore",
            "Circuito RLC",
            "Armonie e THD",
            "Batterie e UPS",
            "Dissipatore Termico",
            "Impianto di Terra",
            "Selettività Protezioni",
            "Fotovoltaico",
            "Gruppo Elettrogeno",
            "Quadro Elettrico — Dissipazione",
            "Rifasamento Condensatori",
            "Caduta Tensione BT (CEI 64-8)",
            "Avviamento Motore Asincrono",
            "Motore Asincrono — Dati di Targa",
            "Motore Asincrono — Classi IE (Efficienza)",
            "Tabelle di Riferimento Rapido (cavi, colori, IP, IE)",
            "Canaline / Passerelle — Riempimento e Derating",
            "Portata Cavo + Caduta di Tensione (combinato)",
            "Dimensionamento Cavi in Batch (tabella/CSV)",
            "Caduta di Tensione — Confronto A/B",
            "Componenti Passivi (Resistori, Condensatori, Induttori)",
        ],
        key="elett_tipo",
    )
    _render_fav_toggle("⚡  Calcoli Elettrici", "elett_tipo", tipo)

    if tipo == "Legge di Ohm":
        cerca = st.selectbox("Cosa calcolare?", ["Tensione", "Corrente", "Resistenza"], key="ohm_cerca")
        # I due ingressi cambiano significato in base alla grandezza incognita:
        #   Tensione  = Resistenza · Corrente   (V = R · I)
        #   Corrente  = Tensione / Resistenza   (I = V / R)
        #   Resistenza = Tensione / Corrente    (R = V / I)
        _ohm_ingressi = {
            "Tensione":   [("Resistenza R [Ω]:", "Ω"), ("Corrente I [A]:", "A")],
            "Corrente":   [("Tensione V [V]:", "V"),  ("Resistenza R [Ω]:", "Ω")],
            "Resistenza": [("Tensione V [V]:", "V"),  ("Corrente I [A]:", "A")],
        }
        (lbl1, u1), (lbl2, u2) = _ohm_ingressi[cerca]
        in1 = st.number_input(lbl1, value=1.0, key="ohm_in1")
        in2 = st.number_input(lbl2, value=1.0, key="ohm_in2")
        if st.button("Calcola", key="ohm_btn"):
            try:
                val_ohm = formule.calcola_ohm(cerca, in1, in2)
                unita_ohm = {"Tensione": "V", "Corrente": "A", "Resistenza": "Ω"}[cerca]
                st.session_state["_ohm_result"] = {
                    "cerca": cerca, "in1": in1, "in2": in2, "lbl1": lbl1, "lbl2": lbl2,
                    "valore": val_ohm, "unita": unita_ohm,
                }
            except ValueError as e:
                st.session_state["_ohm_result"] = None
                st.error(str(e))

        res_ohm = st.session_state.get("_ohm_result")
        if res_ohm:
            st.success(f"{res_ohm['cerca']}: {res_ohm['valore']:.4f} {res_ohm['unita']}")
            _export_csv_button(
                "Legge di Ohm",
                {
                    "Grandezza calcolata": res_ohm["cerca"],
                    res_ohm.get("lbl1", "Primo valore").rstrip(":"): res_ohm["in1"],
                    res_ohm.get("lbl2", "Secondo valore").rstrip(":"): res_ohm["in2"],
                    "Risultato": f"{res_ohm['valore']:.4f} {res_ohm['unita']}",
                },
                key="ohm_export",
            )

    elif tipo == "Analisi Potenze e Corrente":
        st.subheader("Calcolo Avanzato Potenze e Corrente")
        sis = st.selectbox("Sistema Elettrico:", ["DC", "Monofase", "Trifase"], key="pot_sis")
        obiettivo = st.selectbox(
            "Cosa desideri fare?",
            ["Estrai da Volt e Ampere", "Estrai Corrente (Ampere) da Watt"],
            key="pot_obi",
        )
        v_default = {"Trifase": 400.0, "Monofase": 230.0}.get(sis, 24.0)
        v = st.number_input("Tensione (Volt):", value=v_default, key="pot_v")
        cos_phi = (
            st.number_input("Fattore di potenza (cos phi):", min_value=0.1, max_value=1.0, value=0.85, key="pot_cosphi")
            if sis != "DC" else 1.0
        )

        if obiettivo == "Estrai da Volt e Ampere":
            i = st.number_input("Corrente (Ampere):", value=10.0, key="pot_i")
            if st.button("Analizza Potenze", key="pot_btn_va"):
                res = formule.calcola_potenza_e_corrente(sis, v, i, 0.0, cos_phi, obiettivo)
                if res is None:
                    st.session_state["_pot_result"] = None
                    st.error("Valori non validi: controlla tensione, corrente e cos phi.")
                else:
                    st.session_state["_pot_result"] = {"mode": "va", "sis": sis, "v": v, "i": i, "res": res}

            r = st.session_state.get("_pot_result")
            if r and r["mode"] == "va":
                res = r["res"]
                st.success(f"Potenza attiva: {res['W']:.1f} W ({res['kW']:.4f} kW)")
                st.info(f"Meccanica: {res['HP']:.3f} HP | {res['CV']:.3f} CV")
                st.info(f"Apparente: {res['VA']:.1f} VA ({res['kVA']:.4f} kVA)")
                if r["sis"] != "DC":
                    st.info(f"Reattiva: {res['VAR']:.1f} VAR ({res['kVAR']:.4f} kVAR)")
                _export_csv_button(
                    "Analisi Potenze e Corrente",
                    {
                        "Sistema": r["sis"], "Tensione [V]": r["v"], "Corrente [A]": r["i"],
                        "Potenza attiva [W]": f"{res['W']:.1f}", "Potenza apparente [VA]": f"{res['VA']:.1f}",
                        "HP": f"{res['HP']:.3f}", "CV": f"{res['CV']:.3f}",
                    },
                    key="pot_export_va",
                )
        else:
            w = st.number_input("Potenza in WATT (W):", value=2200.0, step=100.0, key="pot_w")
            if st.button("Estrai Ampere", key="pot_btn_w"):
                res = formule.calcola_potenza_e_corrente(sis, v, 0.0, w, cos_phi, obiettivo)
                if res is None:
                    st.session_state["_pot_result"] = None
                    st.error("Valori non validi: controlla tensione, potenza e cos phi.")
                else:
                    st.session_state["_pot_result"] = {"mode": "w", "sis": sis, "v": v, "w": w, "res": res}

            r = st.session_state.get("_pot_result")
            if r and r["mode"] == "w":
                res = r["res"]
                st.success(f"Corrente assorbita: {res['A']:.2f} A")
                st.info(f"Potenza: {res['HP']:.3f} HP | {res['CV']:.3f} CV")
                st.info(f"Apparente: {res['VA']:.1f} VA ({res['kVA']:.4f} kVA)")
                _export_csv_button(
                    "Analisi Potenze e Corrente",
                    {
                        "Sistema": r["sis"], "Tensione [V]": r["v"], "Potenza [W]": r["w"],
                        "Corrente assorbita [A]": f"{res['A']:.2f}", "Apparente [VA]": f"{res['VA']:.1f}",
                    },
                    key="pot_export_w",
                )

    elif tipo == "Convertitore Potenze (kW / HP / kVA)":
        st.subheader("Conversione tra unita di potenza")
        unita_disp = ["W", "kW", "MW", "HP", "CV", "BTU/h", "kVA"]
        col1, col2 = st.columns(2)
        with col1:
            da_u = st.selectbox("Da:", unita_disp, index=1, key="cpot_da")
        with col2:
            a_u = st.selectbox("A:", unita_disp, index=3, key="cpot_a")
        val_pot = st.number_input("Valore:", value=1.0, format="%.4f", key="cpot_val")
        cos_phi_conv = 1.0
        if da_u == "kVA" or a_u == "kVA":
            cos_phi_conv = st.number_input(
                "Fattore di potenza (cos phi) - necessario per kVA:",
                min_value=0.1,
                max_value=1.0,
                value=0.85,
                key="cpot_cosphi",
            )
        if st.button("Converti", key="cpot_btn"):
            try:
                ris = formule.converti_potenza(val_pot, da_u, a_u, cos_phi_conv)
                st.session_state["_cpot_result"] = {"val": val_pot, "da": da_u, "a": a_u, "ris": ris}
            except ValueError as e:
                st.session_state["_cpot_result"] = None
                st.error(str(e))

        r = st.session_state.get("_cpot_result")
        if r:
            st.success(f"{r['val']} {r['da']} = {r['ris']:.6f} {r['a']}")
            _export_csv_button(
                "Convertitore Potenze",
                {"Valore": r["val"], "Da": r["da"], "A": r["a"], "Risultato": f"{r['ris']:.6f}"},
                key="cpot_export",
            )

    elif tipo == "Rendimento Motore (P_out -> P_in -> Corrente)":
        st.subheader("Da potenza all'albero a assorbimento dalla rete")
        sis_mot = st.selectbox("Sistema:", ["Trifase", "Monofase"], key="mot_sis")
        p_out = st.number_input("Potenza meccanica all'albero (P_out) [kW]:", value=11.0, min_value=0.01, key="mot_pout")
        eta_pct = st.number_input("Rendimento motore eta [%]:", value=92.0, min_value=1.0, max_value=99.9, key="mot_eta")
        v_mot = st.number_input("Tensione [V]:", value=400.0 if sis_mot == "Trifase" else 230.0, key="mot_v")
        cosphi_m = st.number_input("cos phi (da targa motore):", min_value=0.1, max_value=1.0, value=0.85, key="mot_cosphi")
        if st.button("Calcola assorbimento", key="mot_btn"):
            res_m = formule.calcola_ingresso_motore(p_out, eta_pct, sis_mot, v_mot, cosphi_m)
            if res_m is None:
                st.session_state["_mot_result"] = None
                st.error("Valori non validi: controlla potenza, rendimento, tensione e cos phi.")
            else:
                st.session_state["_mot_result"] = {"p_out": p_out, "res": res_m}

        r = st.session_state.get("_mot_result")
        if r:
            res_m = r["res"]
            st.success(f"Potenza assorbita dalla rete: {res_m['P_in_kW']:.3f} kW ({res_m['P_in_W']:.0f} W)")
            st.info(f"Corrente di linea: {res_m['I_A']:.2f} A | Apparente: {res_m['P_app_kVA']:.3f} kVA")
            st.info(f"Potenza ingresso: {res_m['HP_in']:.2f} HP")
            with st.expander("Dettagli"):
                st.write(f"Rendimento: {res_m['eta']*100:.1f}% - energia persa in calore: {res_m['P_in_kW'] - r['p_out']:.3f} kW")
            _export_csv_button(
                "Rendimento Motore",
                {
                    "P_out [kW]": r["p_out"], "P_in [kW]": f"{res_m['P_in_kW']:.3f}",
                    "Corrente linea [A]": f"{res_m['I_A']:.2f}", "Apparente [kVA]": f"{res_m['P_app_kVA']:.3f}",
                    "Rendimento [%]": f"{res_m['eta']*100:.1f}",
                },
                key="mot_export",
            )

    elif tipo == "Rifasamento Industriale (kVAR)":
        st.subheader("Calcolo Batteria di Condensatori")
        p_kw = st.number_input("Potenza attiva impianto (P) [kW]:", value=50.0, key="rif_pkw")
        cos_ini = st.number_input("cos phi attuale:", min_value=0.3, max_value=0.99, value=0.75, format="%.2f", key="rif_ini")
        cos_fin = st.number_input("cos phi obiettivo:", min_value=0.8, max_value=1.0, value=0.95, format="%.2f", key="rif_fin")
        if st.button("Calcola kVAR", key="rif_btn"):
            qc, stato = formule.calcola_rifasamento_kvar(p_kw, cos_ini, cos_fin)
            if stato != "OK":
                st.session_state["_rif_result"] = None
                st.warning(stato)
            else:
                st.session_state["_rif_result"] = {"p_kw": p_kw, "cos_ini": cos_ini, "cos_fin": cos_fin, "qc": qc}

        r = st.session_state.get("_rif_result")
        if r:
            st.success(f"Potenza rifasante necessaria: {r['qc']:.2f} kVAR")
            with st.expander("Dettagli calcolo"):
                tan_i = math.tan(math.acos(r["cos_ini"]))
                tan_f = math.tan(math.acos(r["cos_fin"]))
                st.write(f"Potenza reattiva iniziale: {r['p_kw'] * tan_i:.2f} kVAR")
                st.write(f"Potenza reattiva target: {r['p_kw'] * tan_f:.2f} kVAR")
                st.write(f"Differenza (condensatori): {r['qc']:.2f} kVAR")
            _export_csv_button(
                "Rifasamento Industriale",
                {
                    "Potenza [kW]": r["p_kw"], "cos phi iniziale": r["cos_ini"], "cos phi obiettivo": r["cos_fin"],
                    "Potenza rifasante [kVAR]": f"{r['qc']:.2f}",
                },
                key="rif_export",
            )

    elif tipo == "Caduta di Tensione":
        mat = st.radio("Materiale Conduttore:", ["Rame", "Alluminio"], key="cdv_mat")
        fasi = st.selectbox("Linea elettrica:", ["Monofase", "Trifase"], key="cdv_fasi")
        amp = st.number_input("Corrente Ib [A]:", value=16.0, key="cdv_amp")
        _warn_range(amp, 0.1, 2000, "Corrente Ib", "A")
        metri = st.number_input("Lunghezza [Metri]:", value=50.0, key="cdv_metri")
        _warn_range(metri, 0.1, 5000, "Lunghezza linea", "m")
        sez = st.selectbox(
            "Sezione mm2:", SEZIONI_COMMERCIALI, key="cdv_sez",
            help="Sezione commerciale del conduttore (serie CEI-UNEL). Deve coincidere con la "
                 "portata Iz dichiarata sotto: non viene ricalcolata automaticamente in questo calcolo.",
        )
        isol = st.selectbox(
            "Isolante Cavo:", ["PVC (70C)", "EPR / XLPE / Gomma (90C)"], key="cdv_isol",
            help="Temperatura massima di esercizio del conduttore (CEI-UNEL 35024/1): 70°C per PVC, "
                 "90°C per EPR/XLPE/Gomma. Determina il fattore di correzione per resistività e derating termico.",
        )
        cos_phi = st.number_input(
            "cos phi:", value=0.85, min_value=0.1, max_value=1.0, key="cdv_cosphi",
            help="Fattore di potenza del carico. Influenza la componente reattiva della caduta di "
                 "tensione (CEI 64-8); tipico 0.8-0.9 per carichi industriali, 0.95-1.0 per carichi resistivi.",
        )
        temp_ambiente = st.slider(
            "Temperatura Ambiente (C):", min_value=10, max_value=60, value=30, step=5, key="cdv_temp",
            help="Temperatura ambiente di posa. La tabella CEI-UNEL 35024/1 è riferita a 30°C in aria / "
                 "20°C nel terreno: valori diversi applicano un fattore di derating alla portata.",
        )
        n_circuiti = st.number_input(
            "Numero di Cavi affiancati:", min_value=1, max_value=20, value=1, key="cdv_ncir",
            help="Numero di circuiti/cavi multipolari posati a contatto sulla stessa passerella/tubo: "
                 "il raggruppamento riduce la portata per il mutuo riscaldamento (CEI-UNEL 35024/1, tabella raggruppamento).",
        )
        n_parallelo_cdv = st.number_input(
            "Conduttori in parallelo per fase:", min_value=1, max_value=10, value=1, step=1,
            key="cdv_npar", help="Numero di cavi identici posati in parallelo sulla stessa fase.",
        )
        iz_tabella = st.number_input(
            "Portata Nominale catalogo Iz [A] (a 30C, per conduttore):", value=20.0, key="cdv_iz",
            help="Portata di base da tabella CEI-UNEL 35024/1 per la sezione/isolante/posa scelti, "
                 "riferita a 30°C senza raggruppamento. Si trova nelle tabelle norma o nel datasheet del cavo.",
        )
        considera_x_cdv = st.checkbox(
            "Considera reattanza X nel calcolo", value=True, key="cdv_considera_x",
            help="Significativa per sezioni grandi (≥95 mm²); per sezioni piccole il contributo "
                 "è trascurabile e può essere disattivato per un calcolo semplificato a sola resistenza.",
        )
        posa = st.selectbox(
            "Metodo di Posa (CEI 64-8):",
            [
                "Metodo A1/A2 (Tubo in parete isolante)",
                "Metodo B1/B2 (Tubo a parete)",
                "Metodo C (A vista a parete)",
                "Metodo E/F/G (Passerelle / Aria aperta)",
                "Posa Interrata",
            ],
            key="cdv_posa",
            help="Metodo di installazione secondo le tabelle di posa CEI 64-8 / CEI-UNEL 35024/1: "
                 "incide sul fattore di dissipazione termica e quindi sulla portata ammissibile.",
        )

        if "Interrata" in posa:
            st.warning("Per posa interrata il calcolo usa una tabella in aria: il risultato puo essere leggermente conservativo.")

        usa_datasheet_cdv = st.checkbox(
            "Usa R/X specifiche del cavo da datasheet (sovrascrive il calcolo teorico)",
            key="cdv_usa_datasheet",
        )
        r20_cdv, x_cdv = None, None
        if usa_datasheet_cdv:
            with st.expander("📚 Carica valori da libreria cavi commerciali (opzionale)"):
                coll1, coll2, coll3 = st.columns([2, 1, 1])
                with coll1:
                    cavo_lib_cdv = st.selectbox(
                        "Cavo commerciale:", libcavi.lista_cavi_commerciali(), key="cdv_lib_cavo",
                    )
                with coll2:
                    sez_lib_cdv = st.selectbox(
                        "Sezione [mm²]:", libcavi.lista_sezioni_libreria(), key="cdv_lib_sez",
                    )
                with coll3:
                    st.write("")
                    st.write("")
                    if st.button("Carica", key="cdv_lib_btn"):
                        p_lib = libcavi.parametri_cavo(cavo_lib_cdv, sez_lib_cdv)
                        st.session_state["cdv_r20"] = p_lib["R20_ohm_km"]
                        st.session_state["cdv_x"] = p_lib["X_ohm_km"]
            colr, colx = st.columns(2)
            with colr:
                r20_cdv = st.number_input(
                    "Resistenza cavo a 20°C [Ω/km]:", value=4.61, min_value=0.001,
                    format="%.4f", key="cdv_r20",
                )
            with colx:
                x_cdv = st.number_input(
                    "Reattanza cavo [Ω/km]:", value=0.08, min_value=0.0,
                    format="%.4f", key="cdv_x",
                )
            st.caption("Valori tipici riportati sul datasheet del produttore del cavo specifico.")

        if st.button("Calcola Perdita Vettoriale Completa", key="cdv_btn"):
            try:
                dv, t_lav, rho_t, k1, k2, iz_real = formule.calcola_caduta_avanzata(
                    mat, isol, posa, fasi, amp, metri, sez, cos_phi, temp_ambiente, iz_tabella, n_circuiti,
                    r20_km_override=r20_cdv, x_km_override=x_cdv, n_parallelo=int(n_parallelo_cdv),
                    considera_reattanza=considera_x_cdv,
                )
                st.session_state["_cdv_result"] = {
                    "mat": mat, "fasi": fasi, "amp": amp, "metri": metri, "sez": sez,
                    "temp_ambiente": temp_ambiente, "dv": dv, "t_lav": t_lav, "rho_t": rho_t,
                    "k1": k1, "k2": k2, "iz_real": iz_real, "n_circuiti": n_circuiti,
                    "datasheet": usa_datasheet_cdv, "r20_cdv": r20_cdv, "x_cdv": x_cdv,
                    "n_parallelo": int(n_parallelo_cdv), "considera_x": considera_x_cdv,
                }
            except ValueError as e:
                st.session_state["_cdv_result"] = None
                st.error(str(e))

        r = st.session_state.get("_cdv_result")
        if r:
            if r["dv"] < 0:
                st.error(f"Temperatura ambiente ({r['temp_ambiente']}C) oltre il limite dell'isolante selezionato.")
            else:
                v_ref = TENSIONE_MONOFASE if r["fasi"] == "Monofase" else TENSIONE_TRIFASE
                pct = (r["dv"] / v_ref) * 100.0
                with st.expander("Dettagli calcolo termico"):
                    st.write(f"K1 (temperatura ambiente): {r['k1']:.2f}")
                    st.write(f"K2 (raggruppamento {r['n_circuiti']} cavi): {r['k2']:.2f}")
                    st.write(f"Portata reale Iz (totale, {r.get('n_parallelo', 1)} cond. in parallelo): {r['iz_real']:.2f} A")
                    st.write(f"Reattanza X considerata: {'Sì' if r.get('considera_x', True) else 'No (calcolo a sola R)'}")
                    st.write(f"Temperatura interna cavo: {r['t_lav']:.1f} C")
                    st.write(f"Resistivita operativa rho_t: {r['rho_t']:.5f} ohm*mm2/m")
                    if r.get("datasheet"):
                        st.write(f"R datasheet a 20°C: {r['r20_cdv']:.4f} Ω/km")
                        st.write(f"X datasheet: {r['x_cdv']:.4f} Ω/km")
                if pct > 4.0:
                    st.error(f"Perdita: {r['dv']:.2f} V ({pct:.2f}%) - Fuori norma (limite: 4%)")
                else:
                    st.success(f"Perdita: {r['dv']:.2f} V ({pct:.2f}%) - A norma CEI 64-8")
                dati_cdv_export = {
                    "Materiale": r["mat"], "Linea": r["fasi"], "Corrente Ib [A]": r["amp"],
                    "Lunghezza [m]": r["metri"], "Sezione [mm2]": r["sez"],
                    "Conduttori in parallelo": r.get("n_parallelo", 1),
                    "Reattanza X considerata": "Sì" if r.get("considera_x", True) else "No",
                    "Caduta [V]": f"{r['dv']:.2f}", "Caduta [%]": f"{pct:.2f}",
                }
                if r.get("datasheet"):
                    dati_cdv_export["R datasheet [Ω/km]"] = f"{r['r20_cdv']:.4f}"
                    dati_cdv_export["X datasheet [Ω/km]"] = f"{r['x_cdv']:.4f}"
                _export_csv_button("Caduta di Tensione", dati_cdv_export, key="cdv_export")

    elif tipo == "Portata Cavo / Sezione Minima (CEI-UNEL 35024)":
        st.subheader("Sezione minima del cavo da portata (CEI-UNEL 35024/1)")
        st.caption("Conduttore in rame, 3 conduttori attivi a 30 °C. Sceglie la sezione "
                   "commerciale minima con Iz declassata ≥ Ib. Valori rappresentativi: "
                   "per il progetto formale consultare la tabella CEI-UNEL del cavo specifico.")

        usa_datasheet_pc = st.checkbox(
            "Usa portata Iz0 specifica del cavo da datasheet (al posto della tabella CEI-UNEL)",
            key="pc_usa_datasheet",
        )

        if usa_datasheet_pc:
            with st.expander("📚 Carica valori da libreria cavi commerciali (opzionale)"):
                coll1, coll2, coll3 = st.columns([2, 1, 1])
                with coll1:
                    cavo_lib_pc = st.selectbox(
                        "Cavo commerciale:", libcavi.lista_cavi_commerciali(), key="pc_lib_cavo",
                    )
                with coll2:
                    sez_lib_pc = st.selectbox(
                        "Sezione [mm²]:", pcav.lista_sezioni_disponibili(), key="pc_lib_sez",
                    )
                with coll3:
                    st.write("")
                    st.write("")
                    if st.button("Carica", key="pc_lib_btn"):
                        isolante_lib = libcavi.CAVI_COMMERCIALI[cavo_lib_pc]
                        iz0_lib = pcav.IZ0_CEI_UNEL[(isolante_lib, "C")].get(sez_lib_pc)
                        if iz0_lib is not None:
                            st.session_state["pc_iz0_datasheet"] = iz0_lib
                            st.session_state["pc_iso"] = isolante_lib

        col1, col2 = st.columns(2)
        with col1:
            Ib_pc = st.number_input(
                "Corrente di impiego Ib [A]:", value=25.0, min_value=0.1, key="pc_Ib",
                help="Corrente di progetto del circuito (carico massimo previsto). Per CEI 64-8 deve "
                     "risultare Ib ≤ In ≤ Iz, dove In è la corrente nominale della protezione.",
            )
            iso_pc = st.selectbox("Isolante:", pcav.lista_isolanti(),
                                  format_func=lambda x: "PVC (70 °C)" if x == "PVC" else "EPR / XLPE (90 °C)",
                                  key="pc_iso",
                                  help="Temperatura massima di esercizio del conduttore (CEI-UNEL 35024/1): "
                                       "determina la tabella di portata da usare.")
        with col2:
            if not usa_datasheet_pc:
                posa_pc = st.selectbox("Metodo di posa:", pcav.lista_metodi_posa(),
                                       format_func=lambda x: f"{x} — {pcav.METODI_POSA[x]}", key="pc_posa",
                                       help="Metodo di installazione secondo le tabelle CEI-UNEL 35024/1: "
                                            "incide sulla capacità di dissipazione termica del cavo.")
            else:
                iz0_datasheet_pc = st.number_input(
                    "Portata Iz0 da datasheet a 30°C [A] (per conduttore):", value=30.0, min_value=0.1,
                    key="pc_iz0_datasheet",
                )
        col3, col4, col5 = st.columns(3)
        with col3:
            T_pc = st.slider(
                "Temperatura ambiente [°C]:", 10, 60, 30, step=5, key="pc_T",
                help="La tabella CEI-UNEL 35024/1 è riferita a 30°C in aria: temperature diverse "
                     "applicano un fattore di correzione k1 alla portata.",
            )
        with col4:
            n_pc = st.number_input(
                "Circuiti raggruppati:", min_value=1, max_value=20, value=1, step=1, key="pc_n",
                help="Numero di circuiti/cavi multipolari posati a contatto: il raggruppamento riduce "
                     "la portata per il mutuo riscaldamento (fattore di correzione k2, CEI-UNEL 35024/1).",
            )
        with col5:
            n_parallelo_pc = st.number_input(
                "Conduttori in parallelo per fase:", min_value=1, max_value=10, value=1, step=1,
                key="pc_npar", help="Numero di cavi identici posati in parallelo sulla stessa fase.",
            )

        if st.button("Calcola sezione minima", key="pc_btn"):
            try:
                if usa_datasheet_pc:
                    r = pcav.verifica_cavo_personalizzato(
                        Ib_pc, iz0_datasheet_pc, iso_pc, float(T_pc), int(n_pc), int(n_parallelo_pc)
                    )
                    r["sezione_mm2"] = None
                    r["posa"] = "personalizzata (datasheet)"
                else:
                    r = pcav.sezione_minima_portata(
                        Ib_pc, iso_pc, posa_pc, float(T_pc), int(n_pc), int(n_parallelo_pc)
                    )
                st.session_state["_pcav_result"] = r
                st.session_state["_pcav_datasheet"] = usa_datasheet_pc
            except ValueError as e:
                st.session_state["_pcav_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_pcav_result")
        if rr:
            if rr.get("sezione_mm2") is not None:
                st.success(f"Sezione minima: **{rr['sezione_mm2']:.1f} mm²**  "
                           f"(Iz = {rr['Iz_A']:.1f} A ≥ Ib = {rr['Ib_A']:.1f} A)")
            elif rr.get("idoneo"):
                st.success(f"Cavo idoneo: Iz = {rr['Iz_A']:.1f} A ≥ Ib = {rr['Ib_A']:.1f} A")
            else:
                st.error(f"Cavo NON idoneo: Iz = {rr['Iz_A']:.1f} A < Ib = {rr['Ib_A']:.1f} A")
            c1, c2, c3 = st.columns(3)
            c1.metric("Portata base Iz0 (per cond.)", f"{rr['Iz0_A']:.0f} A")
            c2.metric("Portata reale Iz (totale)", f"{rr['Iz_A']:.1f} A")
            c3.metric("Utilizzo Ib/Iz", f"{rr['tasso_utilizzo_pct']:.1f} %")
            _barra_utilizzo(rr["tasso_utilizzo_pct"], "Utilizzo portata (Ib / Iz)")
            with st.expander("Dettagli declassamento"):
                st.write(f"K1 (temperatura {T_pc} °C): {rr['K1']:.2f}")
                st.write(f"K2 (raggruppamento {int(n_pc)} circuiti): {rr['K2']:.2f}")
                st.write(f"Conduttori in parallelo per fase: {rr.get('n_parallelo', 1)}")
                if rr.get("Iz0_richiesto_A") is not None:
                    st.write(f"Iz0 minimo richiesto per conduttore (prima del declassamento): {rr['Iz0_richiesto_A']:.1f} A")
            dati_pc_export = {
                "Ib [A]": rr["Ib_A"], "Isolante": rr["isolante"], "Posa": rr["posa"],
                "Temperatura [°C]": T_pc, "Circuiti": int(n_pc),
                "Conduttori in parallelo": rr.get("n_parallelo", 1),
                "Iz0 base [A] (per cond.)": rr["Iz0_A"],
                "Iz reale [A] (totale)": f"{rr['Iz_A']:.1f}", "Utilizzo [%]": f"{rr['tasso_utilizzo_pct']:.1f}",
            }
            if rr.get("sezione_mm2") is not None:
                dati_pc_export["Sezione minima [mm²]"] = rr["sezione_mm2"]
            _export_csv_button("Portata Cavo — Sezione Minima", dati_pc_export, key="pcav_export")

    elif tipo == "Portata Cavo + Caduta di Tensione (combinato)":
        st.subheader("Dimensionamento combinato: sezione minima da portata + verifica caduta di tensione")
        st.caption("Conduttore in rame. Calcola la sezione minima secondo CEI-UNEL 35024/1 e verifica "
                   "nella stessa schermata che la caduta di tensione su quella sezione resti entro il "
                   "limite del 4% (CEI 64-8).")

        col1, col2 = st.columns(2)
        with col1:
            fasi_comb = st.selectbox("Linea elettrica:", ["Monofase", "Trifase"], key="comb_fasi")
            Ib_comb = st.number_input("Corrente di impiego Ib [A]:", value=16.0, min_value=0.1, key="comb_Ib")
            metri_comb = st.number_input("Lunghezza linea [m]:", value=50.0, min_value=0.0, key="comb_metri")
            cos_phi_comb = st.number_input("cos phi:", min_value=0.1, max_value=1.0, value=0.85, key="comb_cosphi")
        with col2:
            isol_comb = st.selectbox("Isolante:", pcav.lista_isolanti(),
                                     format_func=lambda x: "PVC (70 °C)" if x == "PVC" else "EPR / XLPE (90 °C)",
                                     key="comb_iso")
            posa_comb = st.selectbox("Metodo di posa:", pcav.lista_metodi_posa(),
                                     format_func=lambda x: f"{x} — {pcav.METODI_POSA[x]}", key="comb_posa")
            T_comb = st.slider("Temperatura ambiente [°C]:", 10, 60, 30, step=5, key="comb_T")
            n_comb = st.number_input("Circuiti raggruppati:", min_value=1, max_value=20, value=1, step=1, key="comb_n")

        col3, col4 = st.columns(2)
        with col3:
            n_parallelo_comb = st.number_input(
                "Conduttori in parallelo per fase:", min_value=1, max_value=10, value=1, step=1, key="comb_npar",
            )
        with col4:
            considera_x_comb = st.checkbox(
                "Considera reattanza X nel calcolo", value=True, key="comb_considera_x",
                help="Significativa per sezioni grandi (≥95 mm²); per sezioni piccole il contributo "
                     "è trascurabile e può essere disattivato per un calcolo semplificato a sola resistenza.",
            )

        if st.button("Calcola sezione e caduta", key="comb_btn"):
            try:
                r_port = pcav.sezione_minima_portata(
                    Ib_comb, isol_comb, posa_comb, float(T_comb), int(n_comb), int(n_parallelo_comb)
                )
                dv, t_lav, rho_t, k1, k2, iz_real = formule.calcola_caduta_avanzata(
                    "Rame", isol_comb, posa_comb, fasi_comb, Ib_comb, metri_comb,
                    r_port["sezione_mm2"], cos_phi_comb, float(T_comb), r_port["Iz0_A"], int(n_comb),
                    n_parallelo=int(n_parallelo_comb), considera_reattanza=considera_x_comb,
                )
                st.session_state["_comb_result"] = {
                    "r_port": r_port, "dv": dv, "t_lav": t_lav, "fasi": fasi_comb,
                    "Ib": Ib_comb, "metri": metri_comb, "considera_x": considera_x_comb,
                }
            except ValueError as e:
                st.session_state["_comb_result"] = None
                st.error(str(e))

        rc = st.session_state.get("_comb_result")
        if rc:
            r_port = rc["r_port"]
            st.success(f"Sezione minima: **{r_port['sezione_mm2']:.1f} mm²**  "
                       f"(Iz = {r_port['Iz_A']:.1f} A ≥ Ib = {r_port['Ib_A']:.1f} A, "
                       f"utilizzo {r_port['tasso_utilizzo_pct']:.1f}%)")
            if rc["dv"] < 0:
                st.error("Temperatura ambiente oltre il limite dell'isolante selezionato: caduta non calcolabile.")
            else:
                v_ref = TENSIONE_MONOFASE if rc["fasi"] == "Monofase" else TENSIONE_TRIFASE
                pct = (rc["dv"] / v_ref) * 100.0
                if pct > 4.0:
                    st.error(f"Caduta di tensione: {rc['dv']:.2f} V ({pct:.2f}%) - Fuori norma (limite: 4%)")
                else:
                    st.success(f"Caduta di tensione: {rc['dv']:.2f} V ({pct:.2f}%) - A norma CEI 64-8")
                with st.expander("Dettagli"):
                    st.write(f"Sezione scelta: {r_port['sezione_mm2']:.1f} mm² — Iz0 catalogo (per cond.): {r_port['Iz0_A']:.0f} A")
                    st.write(f"K1 (temperatura {T_comb} °C): {r_port['K1']:.2f} — K2 (raggruppamento {int(n_comb)} circuiti): {r_port['K2']:.2f}")
                    st.write(f"Conduttori in parallelo per fase: {r_port.get('n_parallelo', 1)}")
                    st.write(f"Reattanza X considerata: {'Sì' if rc['considera_x'] else 'No (calcolo a sola R)'}")
                    st.write(f"Temperatura interna cavo stimata: {rc['t_lav']:.1f} °C")
                dati_comb = {
                    "Linea": rc["fasi"], "Ib [A]": rc["Ib"], "Lunghezza [m]": rc["metri"],
                    "Sezione minima [mm²]": r_port["sezione_mm2"], "Iz [A]": f"{r_port['Iz_A']:.1f}",
                    "Utilizzo portata [%]": f"{r_port['tasso_utilizzo_pct']:.1f}",
                    "Caduta [V]": f"{rc['dv']:.2f}", "Caduta [%]": f"{pct:.2f}",
                }
                _export_csv_button("Portata + Caduta combinato", dati_comb, key="comb_export")

    elif tipo == "Dimensionamento Cavi in Batch (tabella/CSV)":
        st.subheader("Dimensionamento di più linee in una volta")
        st.caption("Compila la tabella (o incolla righe da un foglio di calcolo) e dimensiona tutte "
                   "le linee insieme: sezione minima da portata CEI-UNEL 35024 + verifica caduta CEI 64-8. "
                   "Conduttore in rame. fasi: Monofase/Trifase · isolante: PVC/EPR · posa: B1/B2/C/E.")

        _righe_default = pd.DataFrame([
            {"nome": "Linea 1", "fasi": "Trifase", "Ib_A": 16.0, "lunghezza_m": 30.0, "cos_phi": 0.9,
             "isolante": "PVC", "posa": "C", "T_amb": 30.0, "n_circuiti": 1, "n_parallelo": 1},
            {"nome": "Linea 2", "fasi": "Monofase", "Ib_A": 10.0, "lunghezza_m": 25.0, "cos_phi": 0.9,
             "isolante": "PVC", "posa": "C", "T_amb": 30.0, "n_circuiti": 1, "n_parallelo": 1},
        ])
        tabella_in = st.data_editor(
            _righe_default, num_rows="dynamic", use_container_width=True, key="batch_editor",
        )

        if st.button("Dimensiona tutte le linee", key="batch_btn"):
            linee = tabella_in.to_dict("records")
            risultati = batch_cavi.dimensiona_batch(linee)
            st.session_state["_batch_result"] = risultati

        rb = st.session_state.get("_batch_result")
        if rb:
            df_out = pd.DataFrame(rb)
            n_ok = sum(1 for r in rb if r["esito"] == "OK")
            n_tot = len(rb)
            if n_ok == n_tot:
                st.success(f"Tutte le {n_tot} linee sono a norma (sezione adeguata e caduta ≤ 4%).")
            else:
                st.warning(f"{n_ok}/{n_tot} linee a norma. Controlla le righe con esito diverso da OK.")
            st.dataframe(df_out, use_container_width=True)

            csv_out = df_out.to_csv(index=False)
            st.download_button(
                "📥 Esporta risultati in CSV",
                data=csv_out, file_name="dimensionamento_cavi_batch.csv",
                mime="text/csv", key="batch_export",
            )

    elif tipo == "Caduta di Tensione — Confronto A/B":
        st.subheader("Confronto affiancato di due scenari di caduta di tensione")
        st.caption("Imposta due varianti (es. due sezioni diverse, o due lunghezze) e confrontale "
                   "fianco a fianco. Conduttore in rame, metodo C, reattanza inclusa.")

        _posa_cmp = "Metodo C (A vista a parete)"
        _isolanti_cmp = ["PVC (70C)", "EPR / XLPE / Gomma (90C)"]

        def _scenario_inputs(label: str, key: str, sez_default):
            st.markdown(f"#### Scenario {label}")
            fasi = st.selectbox("Linea:", ["Monofase", "Trifase"], key=f"{key}_fasi")
            amp = st.number_input("Corrente Ib [A]:", value=16.0, min_value=0.1, key=f"{key}_amp")
            metri = st.number_input("Lunghezza [m]:", value=50.0, min_value=0.1, key=f"{key}_metri")
            sez = st.selectbox("Sezione [mm²]:", SEZIONI_COMMERCIALI,
                               index=SEZIONI_COMMERCIALI.index(sez_default), key=f"{key}_sez")
            isol = st.selectbox("Isolante:", _isolanti_cmp, key=f"{key}_isol")
            cos_phi = st.number_input("cos phi:", value=0.9, min_value=0.1, max_value=1.0, key=f"{key}_cos")
            return {"fasi": fasi, "amp": amp, "metri": metri, "sez": sez, "isol": isol, "cos_phi": cos_phi}

        colA, colB = st.columns(2)
        with colA:
            scen_a = _scenario_inputs("A", "cmpA", 2.5)
        with colB:
            scen_b = _scenario_inputs("B", "cmpB", 4)

        def _calcola_scenario(s):
            dv, t_lav, rho_t, k1, k2, iz_real = formule.calcola_caduta_avanzata(
                "Rame", s["isol"], _posa_cmp, s["fasi"], s["amp"], s["metri"], s["sez"],
                s["cos_phi"], 30.0, 20.0, 1,
            )
            v_ref = TENSIONE_MONOFASE if s["fasi"] == "Monofase" else TENSIONE_TRIFASE
            pct = dv / v_ref * 100.0 if dv >= 0 else None
            return dv, pct

        if st.button("Confronta scenari", key="cmp_btn"):
            try:
                dv_a, pct_a = _calcola_scenario(scen_a)
                dv_b, pct_b = _calcola_scenario(scen_b)
                st.session_state["_cmp_result"] = {
                    "a": (scen_a, dv_a, pct_a), "b": (scen_b, dv_b, pct_b),
                }
            except ValueError as e:
                st.session_state["_cmp_result"] = None
                st.error(str(e))

        rc = st.session_state.get("_cmp_result")
        if rc:
            (sa, dv_a, pct_a) = rc["a"]
            (sb, dv_b, pct_b) = rc["b"]
            righe = [
                {"Parametro": "Linea", "Scenario A": sa["fasi"], "Scenario B": sb["fasi"]},
                {"Parametro": "Ib [A]", "Scenario A": f"{sa['amp']:g}", "Scenario B": f"{sb['amp']:g}"},
                {"Parametro": "Lunghezza [m]", "Scenario A": f"{sa['metri']:g}", "Scenario B": f"{sb['metri']:g}"},
                {"Parametro": "Sezione [mm²]", "Scenario A": f"{sa['sez']:g}", "Scenario B": f"{sb['sez']:g}"},
                {"Parametro": "Isolante", "Scenario A": sa["isol"], "Scenario B": sb["isol"]},
                {"Parametro": "Caduta [V]", "Scenario A": f"{dv_a:.2f}", "Scenario B": f"{dv_b:.2f}"},
                {"Parametro": "Caduta [%]", "Scenario A": f"{pct_a:.2f}", "Scenario B": f"{pct_b:.2f}"},
            ]
            st.table(righe)
            if pct_a is not None and pct_b is not None:
                if pct_a < pct_b:
                    st.success(f"Scenario A ha la caduta minore ({pct_a:.2f}% vs {pct_b:.2f}%).")
                elif pct_b < pct_a:
                    st.success(f"Scenario B ha la caduta minore ({pct_b:.2f}% vs {pct_a:.2f}%).")
                else:
                    st.info("I due scenari hanno la stessa caduta di tensione.")
            dati_cmp = {f"A — {r['Parametro']}": r["Scenario A"] for r in righe}
            dati_cmp.update({f"B — {r['Parametro']}": r["Scenario B"] for r in righe})
            _export_csv_button("Caduta Tensione — Confronto A/B", dati_cmp, key="cmp_export")

    elif tipo == "Grado di Protezione IP (IEC 60529)":
        st.subheader("Decodifica grado di protezione IP (IEC 60529)")
        col1, col2 = st.columns([2, 1])
        with col1:
            codice_ip = st.text_input(
                "Codice IP (es. IP65, IP2X, IPX7, IP54CW):",
                value="IP65", key="ip_codice",
                help="IEC 60529: 1ª cifra = protezione da solidi/polvere (0-6), 2ª cifra = protezione "
                     "da liquidi (0-9). X indica cifra non specificata; lettere addizionali (es. W, M, S) "
                     "indicano condizioni di prova particolari.",
            )
        with col2:
            esempio = st.selectbox("…oppure parti da un uso tipico:",
                                   ["—"] + list(gip.IP_ESEMPI_USO.keys()), key="ip_esempio")
            if esempio != "—":
                st.caption(f"Consigliato: {gip.IP_ESEMPI_USO[esempio]}")

        if st.button("Decodifica IP", key="ip_btn"):
            try:
                r = gip.decodifica_ip(codice_ip)
                st.session_state["_ip_result"] = r
            except ValueError as e:
                st.session_state["_ip_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_ip_result")
        if rr:
            st.success(f"**{rr['codice']}** decodificato")
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"**1ª cifra ({rr['prima_cifra']}) — solidi/polvere**")
                st.markdown(f"*{rr['prima_titolo']}*")
                st.caption(rr["prima_descrizione"])
            with c2:
                st.markdown(f"**2ª cifra ({rr['seconda_cifra']}) — acqua**")
                st.markdown(f"*{rr['seconda_titolo']}*")
                st.caption(rr["seconda_descrizione"])
            if rr["lettere"]:
                st.markdown("**Lettere addizionali/supplementari:**")
                for L, tipo_L, desc_L in rr["lettere"]:
                    st.markdown(f"- **{L}** ({tipo_L}): {desc_L}")

            with st.expander("Tabelle di riferimento (IK urti, esempi d'uso)"):
                st.markdown("**Codici IK — energia d'urto (IEC 62262):**")
                st.table([{"Codice IK": k, "Energia [J]": v} for k, v in gip.IK_ENERGIA_JOULE.items()])
                st.markdown("**Esempi d'uso → IP consigliato:**")
                for uso, ipc in gip.IP_ESEMPI_USO.items():
                    st.markdown(f"- {uso}: **{ipc}**")

            dati_ip = {
                "Codice IP": rr["codice"],
                f"1ª cifra ({rr['prima_cifra']})": rr["prima_titolo"],
                f"2ª cifra ({rr['seconda_cifra']})": rr["seconda_titolo"],
            }
            for L, tipo_L, desc_L in rr["lettere"]:
                dati_ip[f"Lettera {L} ({tipo_L})"] = desc_L
            _export_csv_button("Grado di Protezione IP", dati_ip, key="ip_export")

    elif tipo == "Tabelle di Riferimento Rapido (cavi, colori, IP, IE)":
        st.subheader("Tabelle di consultazione rapida — elettrico industriale")
        st.caption("Solo lookup, nessun calcolo: per consultazione veloce da banco o in campo.")

        with st.expander("🎨 Colori conduttori (CEI 64-8 / CEI-UNEL 00722)", expanded=True):
            st.table([{"Colore": c, "Significato": d} for c, d in rifr.COLORI_CONDUTTORI.items()])

        with st.expander("📏 Sezioni cavo normalizzate (IEC 60228)"):
            st.write(", ".join(f"{s:g}" for s in rifr.SEZIONI_CAVO_NORMALIZZATE_MM2) + " mm²")

        with st.expander("🛡️ Classi IP — prima e seconda cifra (IEC 60529)"):
            st.markdown("**Solidi/polvere:**")
            st.table([{"Cifra": k, "Titolo": v[0], "Descrizione": v[1]} for k, v in gip.IP_PRIMA_CIFRA.items()])
            st.markdown("**Acqua:**")
            st.table([{"Cifra": k, "Titolo": v[0], "Descrizione": v[1]} for k, v in gip.IP_SECONDA_CIFRA.items()])

        with st.expander("💥 Classi IK — energia d'urto (IEC 62262)"):
            st.table([{"Codice IK": k, "Energia [J]": v} for k, v in gip.IK_ENERGIA_JOULE.items()])

        with st.expander("⚙️ Classi IE — rendimento motori asincroni (IEC 60034-30-1)"):
            righe_ie = [
                {"Potenza [kW]": p, "IE1 [%]": v[0], "IE2 [%]": v[1], "IE3 [%]": v[2], "IE4 [%]": v[3]}
                for p, v in motore_asincrono.tabella_ie_eta().items()
            ]
            st.table(righe_ie)
            st.caption("Valori di rendimento nominale a 50 Hz, 4 poli, tipici per la potenza indicata.")

        with st.expander("📖 Glossario termini e acronimi"):
            st.table([{"Termine": t, "Significato": d} for t, d in rifr.GLOSSARIO.items()])

    elif tipo == "Canaline / Passerelle — Riempimento e Derating":
        st.subheader("Riempimento canalina/passerella portacavi")
        st.caption("Non esiste un limite normativo unico CEI: la soglia indicativa di buona pratica "
                   "(IEC 61537) è ≤35% ottimale, ≤50% accettabile, oltre eccessivo (dissipazione termica "
                   "e futuri ampliamenti compromessi).")

        col1, col2 = st.columns(2)
        with col1:
            larghezza = st.number_input("Larghezza canalina [mm]:", value=200.0, min_value=1.0, key="canp_larg")
        with col2:
            altezza = st.number_input("Altezza utile canalina [mm]:", value=75.0, min_value=1.0, key="canp_alt")

        sezioni_note = sorted(rifr.DIAMETRO_ESTERNO_INDICATIVO_MM.keys())
        n_tipi = st.number_input("Numero di tipologie di cavo diverse:", min_value=1, max_value=8, value=2, step=1, key="canp_ntipi")

        cavi_input = []
        for i in range(int(n_tipi)):
            c1, c2 = st.columns(2)
            with c1:
                sez_i = st.selectbox(f"Sezione cavo #{i+1} [mm²]:", sezioni_note, key=f"canp_sez_{i}")
            with c2:
                qta_i = st.number_input(f"Quantità cavi #{i+1}:", min_value=1, max_value=200, value=3, step=1, key=f"canp_qta_{i}")
            cavi_input.append((rifr.DIAMETRO_ESTERNO_INDICATIVO_MM[sez_i], qta_i, sez_i))

        if st.button("Verifica riempimento", key="canp_btn"):
            try:
                r = canp.verifica_riempimento(larghezza, altezza, [(d, q) for d, q, _ in cavi_input])
                r["dettaglio_cavi"] = cavi_input
                st.session_state["_canp_result"] = r
            except ValueError as e:
                st.session_state["_canp_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_canp_result")
        if rr:
            esito_msg = {
                "ottimale": ("success", "Riempimento ottimale"),
                "accettabile": ("warning", "Riempimento accettabile (vicino al limite consigliato)"),
                "eccessivo": ("error", "Riempimento eccessivo — usare una canalina più grande o suddividere i cavi"),
            }[rr["esito"]]
            getattr(st, esito_msg[0])(f"{esito_msg[1]}: {rr['riempimento_pct']:.1f}% "
                                       f"({rr['n_cavi_totale']} cavi, area {rr['area_cavi_mm2']:.0f} mm² "
                                       f"su {rr['area_canalina_mm2']:.0f} mm²)")
            c1, c2, c3 = st.columns(3)
            c1.metric("Area canalina", f"{rr['area_canalina_mm2']:.0f} mm²")
            c2.metric("Area cavi", f"{rr['area_cavi_mm2']:.0f} mm²")
            c3.metric("Riempimento", f"{rr['riempimento_pct']:.1f} %")
            with st.expander("Dettaglio cavi considerati"):
                for diam, qta, sez in rr["dettaglio_cavi"]:
                    st.write(f"{qta} × cavo {sez:g} mm² (Ø est. indicativo {diam:.1f} mm)")
            dati_canp = {
                "Larghezza canalina [mm]": larghezza, "Altezza canalina [mm]": altezza,
                "N. cavi totale": rr["n_cavi_totale"], "Area cavi [mm²]": f"{rr['area_cavi_mm2']:.0f}",
                "Riempimento [%]": f"{rr['riempimento_pct']:.1f}", "Esito": rr["esito"],
            }
            _export_csv_button("Canaline — Riempimento", dati_canp, key="canp_export")

    elif tipo == "Componenti Passivi (Resistori, Condensatori, Induttori)":
        st.subheader("Resistori, condensatori e induttori")
        st.caption("Codice colori resistori (EIA-RS-279/IEC 60062), combinazioni serie/parallelo e "
                   "valori normalizzati (serie E, IEC 60063).")

        sotto = st.radio(
            "Cosa calcolare?",
            ["Codice colori → valore", "Valore → codice colori",
             "Resistori / Induttori — Serie e Parallelo", "Condensatori — Serie e Parallelo",
             "Valore Normalizzato (serie E)", "Resistore SMD (codice)",
             "LED — Resistenza di limitazione", "Partitore di tensione",
             "Costante di tempo RC/RL", "Ponte di Wheatstone", "Convertitore AWG ↔ mm²",
             "Filtro RC/RL — Frequenza di taglio", "Amplificatore operazionale — Guadagno",
             "Diodo Zener — Regolatore shunt"],
            key="cpas_sotto", horizontal=True,
        )

        if sotto == "Codice colori → valore":
            n_bande = st.radio("Numero di bande:", [3, 4, 5, 6], index=1, horizontal=True, key="cpas_dec_nbande")
            colori_lista = cpas.lista_colori_resistore()
            n_cifre = 3 if n_bande in (5, 6) else 2
            ha_tolleranza = n_bande != 3
            ha_coeff_temp = n_bande == 6

            etichette_cifre = [f"Cifra {i+1}" for i in range(n_cifre)]
            cols = st.columns(n_cifre + 1 + int(ha_tolleranza))
            colori_scelti = []
            for i in range(n_cifre):
                with cols[i]:
                    default_idx = 1 if i == 0 else 0  # Marrone, poi Nero...
                    colori_scelti.append(st.selectbox(etichette_cifre[i], colori_lista, index=default_idx, key=f"cpas_dec_cifra_{i}"))
            with cols[n_cifre]:
                colori_scelti.append(st.selectbox("Moltiplicatore", colori_lista, index=2, key="cpas_dec_molt"))
            if ha_tolleranza:
                with cols[n_cifre + 1]:
                    colori_scelti.append(st.selectbox("Tolleranza", colori_lista, index=10, key="cpas_dec_tol"))
            if ha_coeff_temp:
                colore_coeff = st.selectbox("Coeff. temperatura", cpas.lista_colori_coeff_temperatura(),
                                            key="cpas_dec_coeff")
                colori_scelti.append(colore_coeff)

            if st.button("Decodifica", key="cpas_dec_btn"):
                try:
                    r = cpas.decodifica_colori_resistore(colori_scelti)
                    st.session_state["_cpas_dec_result"] = r
                except ValueError as e:
                    st.session_state["_cpas_dec_result"] = None
                    st.error(str(e))
            rr = st.session_state.get("_cpas_dec_result")
            if rr:
                msg = (f"**{rr['valore_ohm']:,.0f} Ω** ± {rr['tolleranza_pct']}% "
                       f"({rr['valore_min_ohm']:,.1f} – {rr['valore_max_ohm']:,.1f} Ω)").replace(",", ".")
                if "coeff_temperatura_ppm_C" in rr:
                    msg += f" — coeff. temperatura {rr['coeff_temperatura_ppm_C']} ppm/°C"
                st.success(msg)
                _export_csv_button("Componenti — Decodifica colori", rr, key="cpas_dec_export")

        elif sotto == "Valore → codice colori":
            col1, col2 = st.columns(2)
            with col1:
                valore_r = st.number_input("Valore resistenza [Ω]:", value=1000.0, min_value=0.01, key="cpas_cod_valore")
            with col2:
                n_bande_c = st.radio("Numero di bande:", [3, 4, 5, 6], index=1, horizontal=True, key="cpas_cod_nbande")

            tolleranza_c = None
            coeff_temp_c = None
            if n_bande_c != 3:
                tolleranza_c = st.selectbox("Tolleranza:", [10.0, 5.0, 2.0, 1.0, 0.5, 0.25, 0.1, 0.05],
                                            key="cpas_cod_tol")
            else:
                st.caption("A 3 bande la tolleranza è implicita: ±20% (nessuna banda dedicata).")
            if n_bande_c == 6:
                coeff_temp_c = st.selectbox("Coeff. temperatura [ppm/°C]:",
                                            sorted(set(cpas.COLORI_COEFF_TEMPERATURA.values())),
                                            key="cpas_cod_coeff")

            if st.button("Trova bande colore", key="cpas_cod_btn"):
                try:
                    r = cpas.colori_da_resistenza(valore_r, int(n_bande_c), tolleranza_c or 5.0, coeff_temp_c)
                    st.session_state["_cpas_cod_result"] = r
                except ValueError as e:
                    st.session_state["_cpas_cod_result"] = None
                    st.error(str(e))
            rr = st.session_state.get("_cpas_cod_result")
            if rr:
                st.success(f"Bande: **{' — '.join(rr['colori'])}**")
                st.caption(f"Valore rappresentato: {rr['valore_arrotondato_ohm']:,.0f} Ω".replace(",", "."))
                _export_csv_button("Componenti — Codice colori", {
                    "Bande": " - ".join(rr["colori"]), "Valore [Ω]": rr["valore_arrotondato_ohm"],
                    "Tolleranza [%]": rr["tolleranza_pct"],
                }, key="cpas_cod_export")

        elif sotto == "Resistori / Induttori — Serie e Parallelo":
            col1, col2 = st.columns(2)
            with col1:
                tipo_comp = st.radio("Componente:", ["Resistori [Ω]", "Induttori [H]"], key="cpas_ri_tipo")
            with col2:
                combinazione = st.radio("Combinazione:", ["Serie", "Parallelo"], key="cpas_ri_comb", horizontal=True)
            unita = "Ω" if tipo_comp.startswith("Resistori") else "H"
            st.caption("Aggiungi quanti componenti servono: nessun limite fisso a 4.")
            valori = _lista_componenti_interattiva("cpas_ri", unita, 100.0)
            if st.button("Calcola equivalente", key="cpas_ri_btn"):
                try:
                    if tipo_comp.startswith("Resistori"):
                        r = cpas.resistori_serie(valori) if combinazione == "Serie" else cpas.resistori_parallelo(valori)
                    else:
                        r = cpas.induttori_serie(valori) if combinazione == "Serie" else cpas.induttori_parallelo(valori)
                    r["n_componenti"] = len(valori)
                    st.session_state["_cpas_ri_result"] = r
                except ValueError as e:
                    st.session_state["_cpas_ri_result"] = None
                    st.error(str(e))
            rr = st.session_state.get("_cpas_ri_result")
            if rr:
                st.success(f"Valore equivalente ({rr['n_componenti']} componenti): **{rr['valore_equivalente']:,.4g} {unita}**".replace(",", "."))
                _export_csv_button("Componenti — Serie/Parallelo", rr, key="cpas_ri_export")

        elif sotto == "Condensatori — Serie e Parallelo":
            combinazione_c = st.radio("Combinazione:", ["Serie", "Parallelo"], key="cpas_c_comb", horizontal=True)
            st.caption("Aggiungi quanti condensatori servono: nessun limite fisso a 4.")
            valori_uf = _lista_componenti_interattiva("cpas_c", "µF", 10.0)
            if st.button("Calcola equivalente", key="cpas_c_btn"):
                try:
                    valori_f = [v * 1e-6 for v in valori_uf]
                    r = cpas.condensatori_serie(valori_f) if combinazione_c == "Serie" else cpas.condensatori_parallelo(valori_f)
                    r["valore_equivalente_uF"] = r["valore_equivalente"] * 1e6
                    r["n_componenti"] = len(valori_uf)
                    st.session_state["_cpas_c_result"] = r
                except ValueError as e:
                    st.session_state["_cpas_c_result"] = None
                    st.error(str(e))
            rr = st.session_state.get("_cpas_c_result")
            if rr:
                st.success(f"Capacità equivalente ({rr['n_componenti']} componenti): **{rr['valore_equivalente_uF']:,.4g} µF**".replace(",", "."))
                _export_csv_button("Componenti — Condensatori", rr, key="cpas_c_export")

        elif sotto == "Valore Normalizzato (serie E)":
            col1, col2 = st.columns(2)
            with col1:
                valore_norm = st.number_input("Valore da normalizzare:", value=53.0, min_value=0.0001, key="cpas_norm_valore")
            with col2:
                serie_norm = st.selectbox("Serie:", cpas.lista_serie_e(), index=2, key="cpas_norm_serie",
                                          help="E6/E12/E24: resistori/condensatori standard (tolleranza 20/10/5%). "
                                               "E48/E96: componenti di precisione (2%/1%).")
            if st.button("Trova valore normalizzato", key="cpas_norm_btn"):
                try:
                    r = cpas.valore_normalizzato_e(valore_norm, serie_norm)
                    st.session_state["_cpas_norm_result"] = r
                except ValueError as e:
                    st.session_state["_cpas_norm_result"] = None
                    st.error(str(e))
            rr = st.session_state.get("_cpas_norm_result")
            if rr:
                st.success(f"Valore normalizzato **{serie_norm}** più vicino: **{rr['valore_normalizzato']:,.4g}** "
                           f"(scostamento {rr['scostamento_pct']:+.2f}%, tolleranza tipica ±{rr['tolleranza_tipica_pct']}%)".replace(",", "."))
                _export_csv_button("Componenti — Valore Normalizzato", rr, key="cpas_norm_export")

        elif sotto == "Resistore SMD (codice)":
            formato_smd = st.radio("Formato marcatura:", ["Standard (3/4 cifre o notazione R)", "EIA-96 (2 cifre + lettera)"],
                                   key="cpas_smd_formato")
            if formato_smd.startswith("Standard"):
                codice_smd = st.text_input("Codice SMD:", value="103", key="cpas_smd_codice",
                                           help="Es. '103' = 10×10³ = 10 kΩ · '1002' = 100×10² = 10 kΩ · '4R7' = 4.7 Ω")
                if st.button("Decodifica SMD", key="cpas_smd_btn"):
                    try:
                        st.session_state["_cpas_smd_result"] = cpas.decodifica_smd_standard(codice_smd)
                    except ValueError as e:
                        st.session_state["_cpas_smd_result"] = None
                        st.error(str(e))
            else:
                codice_smd = st.text_input("Codice EIA-96:", value="01A", key="cpas_smd96_codice",
                                           help="Es. '01A' = 1.00Ω · '68C' = 4.99×100 = 499 Ω. Lettera = moltiplicatore "
                                                "(Z=×0.001, R/Y=×0.01, X/S=×0.1, A=×1, B/H=×10, C=×100, D=×1000, E=×10000, F=×100000).")
                if st.button("Decodifica EIA-96", key="cpas_smd96_btn"):
                    try:
                        st.session_state["_cpas_smd_result"] = cpas.decodifica_smd_eia96(codice_smd)
                    except ValueError as e:
                        st.session_state["_cpas_smd_result"] = None
                        st.error(str(e))
            rr = st.session_state.get("_cpas_smd_result")
            if rr:
                st.success(f"**{rr['valore_ohm']:,.4g} Ω**".replace(",", "."))
                _export_csv_button("Componenti — SMD", rr, key="cpas_smd_export")

        elif sotto == "LED — Resistenza di limitazione":
            col1, col2, col3 = st.columns(3)
            with col1:
                vcc_led = st.number_input("Tensione alimentazione Vcc [V]:", value=9.0, min_value=0.1, key="cpas_led_vcc")
            with col2:
                vf_led = st.number_input("Tensione forward LED Vf [V]:", value=2.0, min_value=0.1, key="cpas_led_vf",
                                        help="Tipica: rosso/giallo ≈1.8-2.2V, verde ≈2.0-3.2V, blu/bianco ≈2.8-3.4V.")
            with col3:
                i_led = st.number_input("Corrente desiderata [mA]:", value=20.0, min_value=0.1, key="cpas_led_i")
            if st.button("Calcola resistenza", key="cpas_led_btn"):
                try:
                    st.session_state["_cpas_led_result"] = cpas.resistenza_limitazione_led(vcc_led, vf_led, i_led)
                except ValueError as e:
                    st.session_state["_cpas_led_result"] = None
                    st.error(str(e))
            rr = st.session_state.get("_cpas_led_result")
            if rr:
                st.success(f"Resistenza: **{rr['resistenza_ohm']:,.1f} Ω** — potenza dissipata: {rr['potenza_dissipata_W']:.3f} W "
                           f"→ usa una resistenza da **{rr['potenza_consigliata_W']:g} W** (margine di sicurezza)".replace(",", "."))
                _export_csv_button("Componenti — LED", rr, key="cpas_led_export")

        elif sotto == "Partitore di tensione":
            verso = st.radio("Calcola:", ["Vout (date R1, R2, Vin)", "R2 (dati Vin, Vout target, R1)"],
                             key="cpas_part_verso", horizontal=True)
            if verso.startswith("Vout"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    vin_p = st.number_input("Vin [V]:", value=12.0, key="cpas_part_vin")
                with col2:
                    r1_p = st.number_input("R1 [Ω]:", value=1000.0, min_value=0.01, key="cpas_part_r1")
                with col3:
                    r2_p = st.number_input("R2 [Ω]:", value=2000.0, min_value=0.01, key="cpas_part_r2")
                if st.button("Calcola Vout", key="cpas_part_btn"):
                    try:
                        st.session_state["_cpas_part_result"] = cpas.partitore_tensione_vout(vin_p, r1_p, r2_p)
                    except ValueError as e:
                        st.session_state["_cpas_part_result"] = None
                        st.error(str(e))
                rr = st.session_state.get("_cpas_part_result")
                if rr:
                    st.success(f"Vout = **{rr['v_out']:.3f} V** (corrente {rr['corrente_mA']:.3f} mA)")
                    _export_csv_button("Componenti — Partitore", rr, key="cpas_part_export")
            else:
                col1, col2, col3 = st.columns(3)
                with col1:
                    vin_p2 = st.number_input("Vin [V]:", value=12.0, key="cpas_part_vin2")
                with col2:
                    vout_p2 = st.number_input("Vout target [V]:", value=4.0, key="cpas_part_vout2")
                with col3:
                    r1_p2 = st.number_input("R1 [Ω]:", value=1000.0, min_value=0.01, key="cpas_part_r1_2")
                if st.button("Calcola R2", key="cpas_part_btn2"):
                    try:
                        st.session_state["_cpas_part_result2"] = cpas.partitore_tensione_r2(vin_p2, vout_p2, r1_p2)
                    except ValueError as e:
                        st.session_state["_cpas_part_result2"] = None
                        st.error(str(e))
                rr = st.session_state.get("_cpas_part_result2")
                if rr:
                    st.success(f"R2 = **{rr['r2_ohm']:,.1f} Ω** (corrente {rr['corrente_mA']:.3f} mA)".replace(",", "."))
                    _export_csv_button("Componenti — Partitore (R2)", rr, key="cpas_part_export2")

        elif sotto == "Costante di tempo RC/RL":
            col1, col2, col3 = st.columns(3)
            with col1:
                tipo_rc = st.radio("Circuito:", ["RC", "RL"], key="cpas_rc_tipo", horizontal=True)
            with col2:
                r_rc = st.number_input("Resistenza R [Ω]:", value=1000.0, min_value=0.01, key="cpas_rc_r")
            with col3:
                if tipo_rc == "RC":
                    cl_rc = st.number_input("Capacità C [µF]:", value=1.0, min_value=0.000001, key="cpas_rc_c") * 1e-6
                else:
                    cl_rc = st.number_input("Induttanza L [mH]:", value=100.0, min_value=0.000001, key="cpas_rc_l") * 1e-3
            pct_rc = st.slider("Percentuale del valore finale da raggiungere [%]:", 1, 99, 63, key="cpas_rc_pct")
            if st.button("Calcola costante di tempo", key="cpas_rc_btn"):
                try:
                    st.session_state["_cpas_rc_result"] = cpas.costante_di_tempo(tipo_rc, r_rc, cl_rc, float(pct_rc))
                except ValueError as e:
                    st.session_state["_cpas_rc_result"] = None
                    st.error(str(e))
            rr = st.session_state.get("_cpas_rc_result")
            if rr:
                st.success(f"τ = **{rr['tau_s']*1000:.4g} ms** — tempo per il {pct_rc}%: **{rr['tempo_target_s']*1000:.4g} ms** "
                           f"(a 5τ = {rr['tempo_5tau_s']*1000:.4g} ms si raggiunge il {rr['percentuale_a_5tau']:.2f}%, "
                           "convenzionalmente il regime permanente)")
                _export_csv_button("Componenti — Costante di tempo", rr, key="cpas_rc_export")

        elif sotto == "Ponte di Wheatstone":
            st.caption("Condizione di equilibrio (nessuna corrente nel galvanometro): R1·Rx = R2·R3 → Rx = R2·R3 / R1")
            col1, col2, col3 = st.columns(3)
            with col1:
                r1_w = st.number_input("R1 (braccio in serie a Rx) [Ω]:", value=100.0, min_value=0.01, key="cpas_wh_r1")
            with col2:
                r2_w = st.number_input("R2 (braccio di rapporto) [Ω]:", value=200.0, min_value=0.01, key="cpas_wh_r2")
            with col3:
                r3_w = st.number_input("R3 (braccio di rapporto) [Ω]:", value=150.0, min_value=0.01, key="cpas_wh_r3")
            if st.button("Calcola Rx", key="cpas_wh_btn"):
                try:
                    st.session_state["_cpas_wh_result"] = cpas.wheatstone_resistenza_incognita(r1_w, r2_w, r3_w)
                except ValueError as e:
                    st.session_state["_cpas_wh_result"] = None
                    st.error(str(e))
            rr = st.session_state.get("_cpas_wh_result")
            if rr:
                st.success(f"Rx = **{rr['rx_ohm']:,.2f} Ω**".replace(",", "."))
                _export_csv_button("Componenti — Wheatstone", rr, key="cpas_wh_export")

        elif sotto == "Convertitore AWG ↔ mm²":
            verso_awg = st.radio("Calcola:", ["AWG → mm²", "mm² → AWG"], key="cpas_awg_verso", horizontal=True)
            if verso_awg == "AWG → mm²":
                awg_val = st.number_input("Calibro AWG:", value=24.0, min_value=-3.0, max_value=40.0, step=1.0, key="cpas_awg_val",
                                          help="AWG 0000=-3, 000=-2, 00=-1, 0=0, poi 1, 2, 3... (numeri più alti = fili più sottili).")
                if st.button("Converti", key="cpas_awg_btn"):
                    try:
                        st.session_state["_cpas_awg_result"] = cpas.awg_a_mm2(awg_val)
                    except ValueError as e:
                        st.session_state["_cpas_awg_result"] = None
                        st.error(str(e))
                rr = st.session_state.get("_cpas_awg_result")
                if rr:
                    st.success(f"AWG {rr['awg']:g} = **{rr['diametro_mm']:.4g} mm** ⌀ = **{rr['area_mm2']:.4g} mm²**")
                    _export_csv_button("Componenti — AWG→mm²", rr, key="cpas_awg_export")
            else:
                area_val = st.number_input("Sezione [mm²]:", value=2.5, min_value=0.001, key="cpas_awg_area")
                if st.button("Converti", key="cpas_awg_btn2"):
                    try:
                        st.session_state["_cpas_awg_result2"] = cpas.mm2_a_awg(area_val)
                    except ValueError as e:
                        st.session_state["_cpas_awg_result2"] = None
                        st.error(str(e))
                rr = st.session_state.get("_cpas_awg_result2")
                if rr:
                    st.success(f"{rr['area_mm2']:g} mm² ≈ **AWG {rr['awg_piu_vicino']}** (⌀ {rr['diametro_mm']:.4g} mm, "
                               f"AWG esatto {rr['awg_esatto']:.2f})")
                    _export_csv_button("Componenti — mm²→AWG", rr, key="cpas_awg_export2")

        elif sotto == "Filtro RC/RL — Frequenza di taglio":
            col1, col2, col3 = st.columns(3)
            with col1:
                tipo_filtro = st.radio("Circuito:", ["RC", "RL"], key="cpas_filt_tipo", horizontal=True)
            with col2:
                r_filtro = st.number_input("Resistenza R [Ω]:", value=1000.0, min_value=0.01, key="cpas_filt_r")
            with col3:
                if tipo_filtro == "RC":
                    cl_filtro = st.number_input("Capacità C [µF]:", value=1.0, min_value=0.000001, key="cpas_filt_c") * 1e-6
                else:
                    cl_filtro = st.number_input("Induttanza L [mH]:", value=100.0, min_value=0.000001, key="cpas_filt_l") * 1e-3
            st.caption("La frequenza di taglio è la stessa sia in configurazione passa-basso che passa-alto: "
                       "cambia solo su quale componente si preleva l'uscita.")
            if st.button("Calcola frequenza di taglio", key="cpas_filt_btn"):
                try:
                    st.session_state["_cpas_filt_result"] = cpas.frequenza_taglio_rc_rl(tipo_filtro, r_filtro, cl_filtro)
                except ValueError as e:
                    st.session_state["_cpas_filt_result"] = None
                    st.error(str(e))
            rr = st.session_state.get("_cpas_filt_result")
            if rr:
                st.success(f"fc = **{rr['fc_Hz']:,.4g} Hz** (ω = {rr['omega_rad_s']:,.4g} rad/s)".replace(",", "."))
                _export_csv_button("Componenti — Filtro RC/RL", rr, key="cpas_filt_export")

        elif sotto == "Amplificatore operazionale — Guadagno":
            col1, col2, col3 = st.columns(3)
            with col1:
                config_opamp = st.radio("Configurazione:", ["Invertente", "Non invertente"], key="cpas_opamp_config")
            with col2:
                r1_opamp = st.number_input("R1 [Ω]:", value=1000.0, min_value=0.01, key="cpas_opamp_r1")
            with col3:
                r2_opamp = st.number_input("R2 (reazione) [Ω]:", value=10000.0, min_value=0.01, key="cpas_opamp_r2")
            if st.button("Calcola guadagno", key="cpas_opamp_btn"):
                try:
                    st.session_state["_cpas_opamp_result"] = cpas.guadagno_op_amp(config_opamp, r1_opamp, r2_opamp)
                except ValueError as e:
                    st.session_state["_cpas_opamp_result"] = None
                    st.error(str(e))
            rr = st.session_state.get("_cpas_opamp_result")
            if rr:
                st.success(f"Guadagno Av = **{rr['guadagno']:.4g}** ({rr['guadagno_dB']:+.2f} dB)")
                _export_csv_button("Componenti — Guadagno OpAmp", rr, key="cpas_opamp_export")

        else:  # Diodo Zener — Regolatore shunt
            col1, col2 = st.columns(2)
            with col1:
                vin_z = st.number_input("Tensione alimentazione Vin [V]:", value=12.0, min_value=0.1, key="cpas_z_vin")
                vz_z = st.number_input("Tensione zener Vz [V]:", value=5.1, min_value=0.1, key="cpas_z_vz")
            with col2:
                rs_z = st.number_input("Resistenza serie [Ω]:", value=220.0, min_value=0.01, key="cpas_z_rs")
                rc_z = st.number_input("Resistenza di carico [Ω]:", value=1000.0, min_value=0.01, key="cpas_z_rc")
            if st.button("Calcola regolatore", key="cpas_z_btn"):
                try:
                    st.session_state["_cpas_z_result"] = cpas.diodo_zener_regolatore(vin_z, vz_z, rs_z, rc_z)
                except ValueError as e:
                    st.session_state["_cpas_z_result"] = None
                    st.error(str(e))
            rr = st.session_state.get("_cpas_z_result")
            if rr:
                if rr["regolazione_ok"]:
                    st.success(f"Regolazione OK — I_zener = **{rr['i_zener_mA']:.2f} mA** "
                               f"(P_zener = {rr['p_zener_W']:.3f} W), I_carico = {rr['i_carico_mA']:.2f} mA")
                else:
                    st.error(f"⚠️ Il regolatore NON riesce a stabilizzare: I_zener risulterebbe negativa "
                             f"({rr['i_zener_mA']:.2f} mA). Riduci la resistenza serie o la resistenza di carico.")
                _export_csv_button("Componenti — Zener", rr, key="cpas_z_export")

    elif tipo == "Corrente di Cortocircuito (Icc)":
        st.subheader("Stima Icc presunta in fondo linea (metodo semplificato IEC 60909)")
        st.caption("Utile per verificare il potere di interruzione degli interruttori.")
        col1, col2 = st.columns(2)
        with col1:
            fasi_cc = st.selectbox("Sistema:", ["Trifase", "Monofase"], key="icc_fasi")
            v_cc = st.number_input("Tensione nominale [V]:", value=400.0 if fasi_cc == "Trifase" else 230.0, key="icc_v")
            _warn_range(v_cc, 100, 1000, "Tensione nominale BT", "V")
            trafo_kva = st.number_input(
                "Potenza trasformatore [kVA]:", value=400.0, min_value=1.0, key="icc_kva",
                help="Potenza apparente nominale del trasformatore MT/BT a monte, da targa.",
            )
        with col2:
            vcc_pct = st.number_input(
                "Vcc trasformatore [%] (tipico 4-6%):", value=4.0, min_value=1.0, max_value=20.0, key="icc_vcc",
                help="Tensione di corto circuito percentuale da targa trasformatore: definisce "
                     "l'impedenza interna e quindi il contributo del trasformatore alla Icc.",
            )
            mat_cc = st.radio("Materiale cavo:", ["Rame", "Alluminio"], key="icc_mat")
        sez_cc = st.selectbox("Sezione cavo [mm2]:", SEZIONI_COMMERCIALI, key="icc_sez")
        lung_cc = st.number_input("Lunghezza linea [m]:", value=50.0, key="icc_lung")

        c_icc = st.radio(
            "Fattore tensione IEC 60909:",
            [
                "c = 1.05 - Icc MASSIMA (verifica potere interruzione)",
                "c = 0.95 - Icc MINIMA (coordinamento protezioni)",
            ],
            key="icc_c",
            help="IEC 60909: c=1.05 stima la Icc massima (verifica del potere di interruzione delle "
                 "protezioni), c=0.95 la Icc minima (verifica del coordinamento/tempi di intervento).",
        )
        c_val = 1.05 if "1.05" in c_icc else 0.95

        if st.button("Calcola Icc", key="icc_btn"):
            try:
                icc_ka, z_tot, z_tr, z_cv = formule.calcola_corrente_cortocircuito(v_cc, trafo_kva, vcc_pct, mat_cc, sez_cc, lung_cc, fasi_cc, c=c_val)
                st.session_state["_icc_result"] = {
                    "v": v_cc, "kva": trafo_kva, "sez": sez_cc, "lung": lung_cc,
                    "c_val": c_val, "icc_ka": icc_ka, "z_tot": z_tot, "z_tr": z_tr, "z_cv": z_cv,
                }
            except ValueError as e:
                st.session_state["_icc_result"] = None
                st.error(str(e))

        r = st.session_state.get("_icc_result")
        if r:
            tipo_icc = "MASSIMA" if r["c_val"] == 1.05 else "MINIMA"
            st.success(f"Icc {tipo_icc} (c={r['c_val']}): {r['icc_ka']:.3f} kA ({r['icc_ka']*1000:.0f} A)")
            with st.expander("Dettagli impedenze"):
                st.write(f"Z trafo: {r['z_tr']:.2f} mOhm")
                st.write(f"Z cavo: {r['z_cv']:.2f} mOhm")
                st.write(f"Z totale: {r['z_tot']:.2f} mOhm")
            if r["icc_ka"] < 1.0:
                st.info("Nota: Icc < 1 kA. Verifica il potere di interruzione dell'interruttore.")
            _export_csv_button(
                "Corrente di Cortocircuito (Icc)",
                {
                    "Tensione [V]": r["v"], "Trasformatore [kVA]": r["kva"], "Sezione [mm2]": r["sez"],
                    "Lunghezza [m]": r["lung"], "Tipo Icc": tipo_icc, "Icc [kA]": f"{r['icc_ka']:.3f}",
                },
                key="icc_export",
            )
        st.caption("Calcolo semplificato. Per progettazione formale usare IEC 60909 completo.")

    elif tipo == "Dimensionamento Protezioni":
        ib = st.number_input(
            "Corrente Ib [A]:", value=16.0, key="prot_ib",
            help="Corrente di progetto del circuito: la protezione scelta deve avere In ≥ Ib (CEI 64-8).",
        )
        j_dens = st.slider(
            "Densita J [A/mm2]:", 1.0, 6.0, 4.0, step=0.5, key="prot_j",
            help="Densità di corrente di progetto per il dimensionamento di massima del cavo "
                 "(non sostituisce la verifica di portata CEI-UNEL 35024/1); tipica 4-6 A/mm² in BT.",
        )
        if st.button("Trova Soluzione", key="prot_btn"):
            try:
                mag, cavo, t_sez = formule.calcola_sezione_protezione(ib, j_dens)
                st.session_state["_prot_result"] = {"ib": ib, "j_dens": j_dens, "mag": mag, "cavo": cavo, "t_sez": t_sez}
            except ValueError as e:
                st.session_state["_prot_result"] = None
                st.error(str(e))

        r = st.session_state.get("_prot_result")
        if r:
            st.success(f"Interruttore consigliato (In): {r['mag']} A | Sezione commerciale: {r['cavo']} mm2 (teorica: {r['t_sez']:.2f} mm2)")
            _export_csv_button(
                "Dimensionamento Protezioni",
                {"Ib [A]": r["ib"], "Densita J [A/mm2]": r["j_dens"], "Interruttore [A]": r["mag"], "Sezione [mm2]": r["cavo"]},
                key="prot_export",
            )

    elif tipo == "Carico Trifase Equilibrato":
        st.subheader("Carico trifase equilibrato — potenze e forme d'onda")
        col1, col2, col3 = st.columns(3)
        with col1:
            V_lin  = st.number_input("Tensione di linea V_L [V]:", value=400.0, min_value=1.0, key="tf_Vl")
            _warn_range(V_lin, 100, 1000, "Tensione di linea BT", "V")
            f_hz   = st.number_input("Frequenza [Hz]:", value=50.0, min_value=1.0, key="tf_f")
            _warn_range(f_hz, 40, 70, "Frequenza", "Hz")
        with col2:
            cos_tf = st.number_input("cos φ:", value=0.85, min_value=0.01, max_value=1.0, key="tf_cos")
            tipo_carico = st.selectbox("Tipo carico:", ["Induttivo (ritardo)", "Capacitivo (anticipo)", "Resistivo puro"], key="tf_tipo")
        with col3:
            P_kW   = st.number_input("Potenza attiva P [kW]:", value=30.0, min_value=0.01, key="tf_P")
            collegamento = st.selectbox("Collegamento:", ["Stella (Y)", "Triangolo (Δ)"], key="tf_coll")

        if st.button("Calcola e traccia", key="tf_btn"):
            st.session_state["_tf_result"] = {
                "V_lin": V_lin, "f_hz": f_hz, "cos_tf": cos_tf,
                "tipo_carico": tipo_carico, "P_kW": P_kW, "collegamento": collegamento,
            }

        r = st.session_state.get("_tf_result")
        if r:
            V_lin, f_hz, cos_tf = r["V_lin"], r["f_hz"], r["cos_tf"]
            tipo_carico, P_kW, collegamento = r["tipo_carico"], r["P_kW"], r["collegamento"]

            phi = math.acos(cos_tf)
            if tipo_carico == "Capacitivo (anticipo)":
                phi = -phi
            elif tipo_carico == "Resistivo puro":
                phi = 0.0

            sin_phi = math.sin(phi)
            P_W  = P_kW * 1000.0
            S_VA = P_W / cos_tf
            Q_VAR = S_VA * abs(sin_phi) * (1 if phi > 0 else -1 if phi < 0 else 0)
            I_L  = S_VA / (math.sqrt(3) * V_lin)
            V_fase = V_lin / math.sqrt(3)
            I_fase = I_L if "Stella" in collegamento else I_L / math.sqrt(3)
            V_picco = V_fase * math.sqrt(2)
            I_picco = I_fase * math.sqrt(2)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Potenza attiva P", f"{P_kW:.3f} kW")
                st.metric("Potenza reattiva Q", f"{Q_VAR/1000:.3f} kVAR")
            with col2:
                st.metric("Potenza apparente S", f"{S_VA/1000:.3f} kVA")
                st.metric("Corrente di linea I_L", f"{I_L:.3f} A")
            with col3:
                st.metric("Tensione di fase V_f", f"{V_fase:.2f} V")
                st.metric("cos φ / sfasamento φ", f"{cos_tf:.3f} / {math.degrees(phi):.1f}°")

            _barra_utilizzo(abs(phi) / (math.pi / 2) * 100, "Angolo di sfasamento (0 % = puro resistivo, 100 % = φ=90°)")

            if _PLOTLY:
                omega  = 2 * math.pi * f_hz
                n_punti = 500
                T_tot   = 2.0 / f_hz
                t_arr   = [i * T_tot / n_punti for i in range(n_punti + 1)]

                V_R = [V_picco * math.sin(omega * t)               for t in t_arr]
                V_S = [V_picco * math.sin(omega * t - 2*math.pi/3) for t in t_arr]
                V_T = [V_picco * math.sin(omega * t + 2*math.pi/3) for t in t_arr]
                I_R = [I_picco * math.sin(omega * t - phi)               for t in t_arr]
                I_S = [I_picco * math.sin(omega * t - phi - 2*math.pi/3) for t in t_arr]
                I_T = [I_picco * math.sin(omega * t - phi + 2*math.pi/3) for t in t_arr]

                t_ms = [ti * 1000 for ti in t_arr]

                mostra_correnti = st.checkbox("Mostra anche correnti di fase", value=True, key="tf_showcurr")

                fig_tf = go.Figure()

                fig_tf.add_trace(go.Scatter(x=t_ms, y=V_R, name="V<sub>R</sub>",
                    line=dict(color="#E53935", width=2.2)))
                fig_tf.add_trace(go.Scatter(x=t_ms, y=V_S, name="V<sub>S</sub>",
                    line=dict(color="#1E88E5", width=2.2)))
                fig_tf.add_trace(go.Scatter(x=t_ms, y=V_T, name="V<sub>T</sub>",
                    line=dict(color="#43A047", width=2.2)))

                if mostra_correnti and abs(I_picco) > 0:
                    fig_tf.add_trace(go.Scatter(x=t_ms, y=I_R, name="I<sub>R</sub>",
                        line=dict(color="#E53935", width=1.4, dash="dash"),
                        yaxis="y2"))
                    fig_tf.add_trace(go.Scatter(x=t_ms, y=I_S, name="I<sub>S</sub>",
                        line=dict(color="#1E88E5", width=1.4, dash="dash"),
                        yaxis="y2"))
                    fig_tf.add_trace(go.Scatter(x=t_ms, y=I_T, name="I<sub>T</sub>",
                        line=dict(color="#43A047", width=1.4, dash="dash"),
                        yaxis="y2"))

                    fig_tf.update_layout(
                        yaxis2=dict(
                            title="Corrente [A]",
                            overlaying="y", side="right",
                            showgrid=False,
                            zeroline=True, zerolinecolor="#ccc",
                        )
                    )

                fig_tf.add_vline(x=1000/f_hz, line=dict(color="#aaa", dash="dot", width=1),
                                 annotation_text=f"T = {1000/f_hz:.1f} ms", annotation_position="top right")

                phi_label = f"φ = {abs(math.degrees(phi)):.1f}° {'(rit.)' if phi > 0 else '(ant.)' if phi < 0 else ''}"
                if abs(phi) > 0.01:
                    t_phi_ms = abs(phi) / omega * 1000
                    fig_tf.add_annotation(
                        x=t_phi_ms / 2, y=I_picco * 0.6,
                        text=phi_label, showarrow=False,
                        font=dict(size=11, color="#555"),
                    )

                fig_tf.update_layout(
                    xaxis_title="Tempo [ms]",
                    yaxis=dict(title="Tensione [V]", zeroline=True, zerolinecolor="#ccc"),
                    legend=dict(orientation="h", y=-0.22, x=0),
                    margin=dict(t=20, b=20, r=60),
                    height=380,
                    hovermode="x unified",
                )
                st.plotly_chart(fig_tf, use_container_width=True)
                st.caption(f"Forme d'onda a regime — V_picco = {V_picco:.1f} V  |  I_picco = {I_picco:.2f} A  |  sequenza RST diretta")

            _export_csv_button(
                "Carico Trifase Equilibrato",
                {
                    "Tensione linea [V]": V_lin, "Potenza [kW]": P_kW, "cos phi": cos_tf,
                    "Potenza apparente [kVA]": f"{S_VA/1000:.3f}", "Potenza reattiva [kVAR]": f"{Q_VAR/1000:.3f}",
                    "Corrente di linea [A]": f"{I_L:.3f}",
                },
                key="tf_export",
            )

    elif tipo == "Carico Trifase Non Equilibrato":
        import cmath as _cm

        st.subheader("Carico trifase non equilibrato — impedanze asimmetriche")
        st.caption("Supporta stella con/senza neutro (teorema di Millman) e triangolo. Inserisci R e X per ogni fase.")

        col1, col2 = st.columns(2)
        with col1:
            V_lin_ne = st.number_input("Tensione di linea V_L [V]:", value=400.0, min_value=1.0, key="ne_Vl")
            f_ne     = st.number_input("Frequenza [Hz]:", value=50.0, min_value=1.0, key="ne_f")
        with col2:
            coll_ne = st.selectbox(
                "Collegamento:",
                ["Stella con neutro (Y-N)", "Stella senza neutro (Y)", "Triangolo (Δ)"],
                key="ne_coll",
            )

        delta = "Triangolo" in coll_ne
        if delta:
            ph_labels = ["Ramo RS", "Ramo ST", "Ramo TR"]
            help_txt  = "Inserisci l'impedanza di ciascun ramo del triangolo."
        else:
            ph_labels = ["Fase R", "Fase S", "Fase T"]
            help_txt  = "Inserisci l'impedanza di ciascuna fase (tra filo e neutro)."
        st.caption(help_txt)

        cols3 = st.columns(3)
        _COLORS = ["#E53935", "#1E88E5", "#43A047"]
        Z_list = []
        for i, (lbl, col3) in enumerate(zip(ph_labels, cols3)):
            with col3:
                st.markdown(f"<span style='color:{_COLORS[i]};font-weight:700'>{lbl}</span>", unsafe_allow_html=True)
                R_ph = st.number_input(f"R [Ω]", value=10.0 + i * 5.0, min_value=0.0, key=f"ne_R{i}")
                X_ph = st.number_input(f"X [Ω]  (+ind / −cap)", value=float(i * 4), key=f"ne_X{i}")
            Z_list.append(complex(R_ph, X_ph))

        if st.button("Calcola", key="ne_btn"):
            st.session_state["_ne_result"] = {
                "V_lin_ne": V_lin_ne, "f_ne": f_ne, "coll_ne": coll_ne, "Z_list": Z_list,
            }

        r = st.session_state.get("_ne_result")
        if r:
            try:
                V_lin_ne, f_ne, coll_ne, Z_list = r["V_lin_ne"], r["f_ne"], r["coll_ne"], r["Z_list"]
                delta = "Triangolo" in coll_ne

                V_fase = V_lin_ne / math.sqrt(3)
                omega  = 2 * math.pi * f_ne
                ang120 = 2 * math.pi / 3

                # Fasori tensione di fase (riferimento V_R a 0°)
                V_R_ph = complex(V_fase, 0)
                V_S_ph = V_fase * _cm.rect(1, -ang120)
                V_T_ph = V_fase * _cm.rect(1,  ang120)

                if delta:
                    # ── Triangolo ─────────────────────────────────────────────
                    # Tensioni di linea: V_RS = V_R - V_S, ecc.
                    V_RS = V_R_ph - V_S_ph
                    V_ST = V_S_ph - V_T_ph
                    V_TR = V_T_ph - V_R_ph
                    Z_RS, Z_ST, Z_TR = Z_list
                    if abs(Z_RS) == 0 or abs(Z_ST) == 0 or abs(Z_TR) == 0:
                        raise ValueError("Impedanza nulla: cortocircuito.")
                    I_RS = V_RS / Z_RS
                    I_ST = V_ST / Z_ST
                    I_TR = V_TR / Z_TR
                    # Correnti di linea (KCL ai nodi)
                    I_R = I_RS - I_TR
                    I_S = I_ST - I_RS
                    I_T = I_TR - I_ST
                    I_N = None
                    # Potenze per ramo
                    fase_data = [
                        ("RS", Z_RS, I_RS, V_RS),
                        ("ST", Z_ST, I_ST, V_ST),
                        ("TR", Z_TR, I_TR, V_TR),
                    ]
                    # Tensioni su cui plottare waveform → linee
                    V_wave = [V_RS, V_ST, V_TR]
                    I_wave = [I_R, I_S, I_T]
                    V_labels = ["V_RS", "V_ST", "V_TR"]
                    I_labels = ["I_R", "I_S", "I_T"]

                else:
                    # ── Stella ────────────────────────────────────────────────
                    Z_R_ph, Z_S_ph, Z_T_ph = Z_list
                    if abs(Z_R_ph) == 0 or abs(Z_S_ph) == 0 or abs(Z_T_ph) == 0:
                        raise ValueError("Impedanza nulla: cortocircuito.")

                    if "con neutro" in coll_ne:
                        # Ogni fase indipendente
                        I_R = V_R_ph / Z_R_ph
                        I_S = V_S_ph / Z_S_ph
                        I_T = V_T_ph / Z_T_ph
                        I_N = -(I_R + I_S + I_T)
                        V_N0 = complex(0, 0)
                    else:
                        # Teorema di Millman: V_N0 = (V_R·Y_R + V_S·Y_S + V_T·Y_T) / (Y_R+Y_S+Y_T)
                        Y_R = 1 / Z_R_ph
                        Y_S = 1 / Z_S_ph
                        Y_T = 1 / Z_T_ph
                        V_N0 = (V_R_ph * Y_R + V_S_ph * Y_S + V_T_ph * Y_T) / (Y_R + Y_S + Y_T)
                        I_R  = (V_R_ph - V_N0) / Z_R_ph
                        I_S  = (V_S_ph - V_N0) / Z_S_ph
                        I_T  = (V_T_ph - V_N0) / Z_T_ph
                        I_N  = None
                    fase_data = [
                        ("R", Z_R_ph, I_R, V_R_ph - V_N0),
                        ("S", Z_S_ph, I_S, V_S_ph - V_N0),
                        ("T", Z_T_ph, I_T, V_T_ph - V_N0),
                    ]
                    V_wave  = [V_R_ph, V_S_ph, V_T_ph]
                    I_wave  = [I_R, I_S, I_T]
                    V_labels = ["V_R", "V_S", "V_T"]
                    I_labels = ["I_R", "I_S", "I_T"]

                # ── Risultati tabellari ────────────────────────────────────────
                P_tot = Q_tot = S_tot = 0.0
                rows = []
                for lbl, Z_ph, I_ph, V_ph_eff in fase_data:
                    I_mag = abs(I_ph)
                    V_mag = abs(V_ph_eff)
                    phi_f = _cm.phase(I_ph) - _cm.phase(V_ph_eff)
                    P_f   = V_mag * I_mag * math.cos(phi_f)
                    Q_f   = V_mag * I_mag * math.sin(phi_f)
                    S_f   = V_mag * I_mag
                    P_tot += P_f; Q_tot += Q_f; S_tot += S_f
                    rows.append({
                        "Fase": lbl,
                        "Z [Ω]": f"{abs(Z_ph):.3f} ∠{math.degrees(_cm.phase(Z_ph)):.1f}°",
                        "I [A]": f"{I_mag:.4f} ∠{math.degrees(_cm.phase(I_ph)):.1f}°",
                        "P [W]": f"{P_f:.2f}",
                        "Q [VAR]": f"{Q_f:.2f}",
                        "cos φ": f"{math.cos(phi_f):.4f}",
                    })

                import pandas as _pd
                st.dataframe(_pd.DataFrame(rows), use_container_width=True, hide_index=True)

                col1, col2, col3 = st.columns(3)
                col1.metric("P totale",  f"{P_tot/1000:.3f} kW")
                col2.metric("Q totale",  f"{Q_tot/1000:.3f} kVAR")
                col3.metric("S totale",  f"{S_tot/1000:.3f} kVA")

                if "senza neutro" in coll_ne:
                    st.info(f"Spostamento nodo neutro V_N0 = {abs(V_N0):.3f} V ∠{math.degrees(_cm.phase(V_N0)):.1f}°"
                            + (" (sistema equilibrato se = 0 V)" if abs(V_N0) < 0.01 else ""))

                if I_N is not None:
                    st.info(f"Corrente di neutro I_N = {abs(I_N):.4f} A ∠{math.degrees(_cm.phase(I_N)):.1f}°")

                if _PLOTLY:
                    # ── Diagramma fasori ──────────────────────────────────────
                    fig_fas = go.Figure()
                    scale_I = abs(V_R_ph) / max(abs(I_R), abs(I_S), abs(I_T), 1e-9) * 0.6

                    for (ph_lbl, V_ph, I_ph_f, col_c) in zip(
                        V_labels, V_wave, I_wave, _COLORS
                    ):
                        # Fasore tensione
                        fig_fas.add_trace(go.Scatter(
                            x=[0, V_ph.real], y=[0, V_ph.imag],
                            mode="lines+markers",
                            line=dict(color=col_c, width=2.5),
                            marker=dict(size=[0, 8], symbol=["circle", "arrow-bar-up"],
                                        angleref="previous"),
                            name=ph_lbl, legendgroup=ph_lbl,
                        ))
                        # Fasore corrente (scalata per visibilità)
                        I_sc = I_ph_f * scale_I
                        fig_fas.add_trace(go.Scatter(
                            x=[0, I_sc.real], y=[0, I_sc.imag],
                            mode="lines+markers",
                            line=dict(color=col_c, width=1.5, dash="dash"),
                            marker=dict(size=[0, 7]),
                            name=I_labels[V_labels.index(ph_lbl)] + f" (×{scale_I:.1f})",
                            legendgroup=ph_lbl,
                        ))

                    lim = abs(V_R_ph) * 1.15
                    fig_fas.update_layout(
                        xaxis=dict(range=[-lim, lim], scaleanchor="y", zeroline=True, zerolinecolor="#ccc"),
                        yaxis=dict(range=[-lim, lim], zeroline=True, zerolinecolor="#ccc"),
                        margin=dict(t=10, b=10), height=380,
                        legend=dict(orientation="h", y=-0.15),
                        title=dict(text="Diagramma fasori (tensioni piene, correnti tratteggiate e scalate)", font=dict(size=12)),
                    )
                    st.plotly_chart(fig_fas, use_container_width=True)

                    # ── Forme d'onda ──────────────────────────────────────────
                    n_punti = 600
                    T_tot_w = 2.0 / f_ne
                    t_arr   = [i * T_tot_w / n_punti for i in range(n_punti + 1)]
                    t_ms    = [ti * 1000 for ti in t_arr]

                    fig_wave = go.Figure()
                    for ph_lbl, V_ph, I_ph_f, col_c, I_lbl in zip(
                        V_labels, V_wave, I_wave, _COLORS, I_labels
                    ):
                        V_mag_w = abs(V_ph) * math.sqrt(2)
                        V_ang_w = _cm.phase(V_ph)
                        v_waveform = [V_mag_w * math.sin(omega * t + V_ang_w) for t in t_arr]
                        fig_wave.add_trace(go.Scatter(
                            x=t_ms, y=v_waveform, name=ph_lbl,
                            line=dict(color=col_c, width=2.2),
                        ))
                        I_mag_w = abs(I_ph_f) * math.sqrt(2)
                        I_ang_w = _cm.phase(I_ph_f)
                        i_waveform = [I_mag_w * math.sin(omega * t + I_ang_w) for t in t_arr]
                        fig_wave.add_trace(go.Scatter(
                            x=t_ms, y=i_waveform, name=I_lbl,
                            line=dict(color=col_c, width=1.4, dash="dash"),
                            yaxis="y2",
                        ))

                    fig_wave.update_layout(
                        xaxis_title="Tempo [ms]",
                        yaxis=dict(title="Tensione [V]", zeroline=True, zerolinecolor="#ccc"),
                        yaxis2=dict(title="Corrente [A]", overlaying="y", side="right",
                                    showgrid=False, zeroline=True, zerolinecolor="#eee"),
                        legend=dict(orientation="h", y=-0.22),
                        margin=dict(t=20, b=20, r=60), height=400,
                        hovermode="x unified",
                    )
                    st.plotly_chart(fig_wave, use_container_width=True)
                    st.caption("Linee continue = tensioni  |  Linee tratteggiate = correnti (asse destro)  |  Asimmetria visibile nelle ampiezze")

                _export_csv_button(
                    "Carico Trifase Non Equilibrato",
                    {
                        "Tensione linea [V]": V_lin_ne, "Collegamento": coll_ne,
                        "P totale [kW]": f"{P_tot/1000:.3f}", "Q totale [kVAR]": f"{Q_tot/1000:.3f}",
                        "S totale [kVA]": f"{S_tot/1000:.3f}",
                    },
                    key="ne_export",
                )
            except (ValueError, ZeroDivisionError) as e:
                st.error(str(e))

    elif tipo == "Trasformatore":
        st.subheader("Calcolo Trasformatore (IEC 60076)")
        col1, col2 = st.columns(2)
        with col1:
            S_kVA   = st.number_input("Potenza apparente S [kVA]:", value=630.0, min_value=1.0, key="tr_S")
            V1_V    = st.number_input("Tensione primario V1 [V]:", value=10000.0, min_value=1.0, key="tr_V1")
            V2_V    = st.number_input("Tensione secondario V2 [V]:", value=400.0, min_value=1.0, key="tr_V2")
            trifase = st.checkbox("Trifase", value=True, key="tr_3f")
        with col2:
            P_ferro_W = st.number_input("Perdite a vuoto P_Fe [W]:", value=1350.0, min_value=1.0, key="tr_pfe")
            P_rame_W  = st.number_input("Perdite a pieno carico P_Cu [W]:", value=7600.0, min_value=1.0, key="tr_pcu")
            V_cc_pct  = st.number_input("Tensione di cc V_cc [%]:", value=4.0, min_value=0.1, max_value=20.0, key="tr_vcc")
            cos_phi   = st.number_input("cos phi carico:", value=0.85, min_value=0.1, max_value=1.0, key="tr_cphi")
        if st.button("Calcola Trasformatore", key="tr_btn"):
            try:
                res_tr = trafo.calcola_trasformatore(S_kVA, V1_V, V2_V, P_ferro_W, P_rame_W, V_cc_pct, 2.0, cos_phi, trifase)
                st.session_state["_tr_result"] = {
                    "S_kVA": S_kVA, "V1_V": V1_V, "V2_V": V2_V, "V_cc_pct": V_cc_pct,
                    "P_ferro_W": P_ferro_W, "P_rame_W": P_rame_W, "cos_phi": cos_phi, "res": res_tr,
                }
            except (ValueError, ZeroDivisionError) as e:
                st.session_state["_tr_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_tr_result")
        if rr:
            res_tr = rr["res"]
            c1, c2, c3 = st.columns(3)
            c1.metric("Rapporto di trasf.", f"{res_tr['rapporto_a']:.4f}")
            c1.metric("I1 nominale", f"{res_tr['I1_nom_A']:.2f} A")
            c1.metric("I2 nominale", f"{res_tr['I2_nom_A']:.2f} A")
            c2.metric("Rendimento nom.", f"{res_tr['eta_nom_pct']:.2f} %")
            c2.metric("Rendimento max.", f"{res_tr['eta_max_pct']:.2f} %")
            c2.metric("β ottimale", f"{res_tr['beta_opt']:.3f}")
            c3.metric("Icc", f"{res_tr['I_cc_A']:.1f} A")
            c3.metric("Caduta tensione ΔV%", f"{res_tr['dV_pct']:.2f} %")
            c3.metric("Z_cc [%]", f"{rr['V_cc_pct']:.1f} %")
            st.markdown("**Parametri circuito equivalente**")
            st.markdown(f"R_eq = {res_tr['R_eq_ohm']:.4f} Ω &nbsp;|&nbsp; X_eq = {res_tr['X_eq_ohm']:.4f} Ω &nbsp;|&nbsp; R_cc% = {res_tr['R_cc_pct']:.3f}% &nbsp;|&nbsp; X_cc% = {res_tr['X_cc_pct']:.3f}%")
            if _PLOTLY:
                rv = trafo.rendimento_vs_carico(rr["S_kVA"], rr["P_ferro_W"], rr["P_rame_W"], rr["cos_phi"])
                fig_tr = go.Figure()
                fig_tr.add_trace(go.Scatter(x=rv["beta"], y=rv["eta_pct"], mode="lines", name="η vs β", line=dict(color="#2196F3", width=2)))
                fig_tr.add_vline(x=res_tr["beta_opt"], line_dash="dash", line_color="#FF5722", annotation_text=f"β_opt={res_tr['beta_opt']:.3f}")
                fig_tr.update_layout(title="Rendimento vs. Fattore di Carico", xaxis_title="β (fattore di carico)", yaxis_title="η [%]", height=320)
                st.plotly_chart(fig_tr, use_container_width=True)
            _export_csv_button(
                "Trasformatore",
                {
                    "S [kVA]": rr["S_kVA"], "V1 [V]": rr["V1_V"], "V2 [V]": rr["V2_V"],
                    "Rapporto trasf.": f"{res_tr['rapporto_a']:.4f}", "Rendimento nom. [%]": f"{res_tr['eta_nom_pct']:.2f}",
                    "Caduta tensione [%]": f"{res_tr['dV_pct']:.2f}",
                },
                key="tr_export",
            )

    elif tipo == "Circuito RLC":
        st.subheader("Analisi Circuito RLC")
        col1, col2 = st.columns(2)
        with col1:
            R_rlc = st.number_input("Resistenza R [Ω]:", value=100.0, min_value=0.0, key="rlc_R")
            L_rlc = st.number_input("Induttanza L [mH]:", value=100.0, min_value=0.0, key="rlc_L")
            C_rlc = st.number_input("Capacità C [μF]:", value=10.0, min_value=0.0, key="rlc_C")
        with col2:
            f_rlc = st.number_input("Frequenza f [Hz]:", value=50.0, min_value=0.1, key="rlc_f")
            tipo_rlc = st.selectbox("Configurazione:", ["Serie", "Parallelo"], key="rlc_tipo")
        if st.button("Calcola RLC", key="rlc_btn"):
            try:
                L_H = L_rlc / 1000.0
                C_F = C_rlc / 1e6
                if tipo_rlc == "Serie":
                    res_rlc = rlc.impedenza_serie(R_rlc, L_H, C_F, f_rlc)
                else:
                    res_rlc = rlc.impedenza_parallelo(R_rlc, L_H, C_F, f_rlc)
                r_ris = rlc.risonanza_serie(L_H, C_F, R_rlc)
                st.session_state["_rlc_result"] = {
                    "R": R_rlc, "L_H": L_H, "C_F": C_F, "f": f_rlc, "tipo_rlc": tipo_rlc,
                    "res": res_rlc, "r_ris": r_ris,
                }
            except (ValueError, ZeroDivisionError) as e:
                st.session_state["_rlc_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_rlc_result")
        if rr:
            res_rlc, r_ris = rr["res"], rr["r_ris"]
            if rr["tipo_rlc"] == "Serie":
                st.success(f"Z = {abs(res_rlc['Z']):.3f} Ω  |  φ = {res_rlc['phi_deg']:.2f}°  |  cos φ = {res_rlc['cos_phi']:.4f}  |  Tipo: {res_rlc['tipo']}")
                c1, c2, c3 = st.columns(3)
                c1.metric("X_L", f"{res_rlc['X_L_ohm']:.3f} Ω")
                c1.metric("X_C", f"{res_rlc['X_C_ohm']:.3f} Ω")
                c2.metric("X_netto", f"{res_rlc['X_net_ohm']:.3f} Ω")
                c2.metric("|Z|", f"{abs(res_rlc['Z']):.3f} Ω")
                c3.metric("φ", f"{res_rlc['phi_deg']:.2f}°")
                c3.metric("cos φ", f"{res_rlc['cos_phi']:.4f}")
            else:
                st.success(f"|Z| = {abs(res_rlc['Z']):.3f} Ω  |  φ = {res_rlc['phi_deg']:.2f}°  |  Tipo: {res_rlc['tipo']}")
                c1, c2 = st.columns(2)
                c1.metric("B_L", f"{res_rlc['B_L']:.5f} S")
                c1.metric("B_C", f"{res_rlc['B_C']:.5f} S")
                c2.metric("|Y|", f"{abs(res_rlc['Y']):.5f} S")
                c2.metric("φ", f"{res_rlc['phi_deg']:.2f}°")
            st.info(f"Risonanza serie: f₀ = {r_ris['f0']:.2f} Hz  |  Q = {r_ris['Q']:.2f}  |  BW = {r_ris['BW']:.2f} Hz")
            if _PLOTLY:
                resp = rlc.risposta_frequenza(rr["R"], rr["L_H"], rr["C_F"], max(1.0, rr["f"]*0.01), rr["f"]*20, rr["tipo_rlc"].lower(), 200)
                fig_rlc = go.Figure()
                fig_rlc.add_trace(go.Scatter(x=resp["f_Hz"], y=resp["Z_ohm"], mode="lines", name="|Z| [Ω]", line=dict(color="#2196F3")))
                fig_rlc.update_layout(title="Risposta in frequenza |Z|", xaxis_title="f [Hz]", yaxis_title="|Z| [Ω]", xaxis_type="log", height=300)
                st.plotly_chart(fig_rlc, use_container_width=True)
            _export_csv_button(
                "Circuito RLC",
                {
                    "R [Ω]": rr["R"], "L [mH]": rr["L_H"]*1000, "C [μF]": rr["C_F"]*1e6, "f [Hz]": rr["f"],
                    "Configurazione": rr["tipo_rlc"], "|Z| [Ω]": f"{abs(res_rlc['Z']):.3f}",
                    "f0 risonanza [Hz]": f"{r_ris['f0']:.2f}",
                },
                key="rlc_export",
            )

    elif tipo == "Armonie e THD":
        st.subheader("Analisi Armoniche e THD (IEC 61000-3-2)")
        V1_thd = st.number_input("Fondamentale V₁ [Vrms]:", value=230.0, min_value=1.0, key="thd_v1")
        st.markdown("**Inserisci ampiezza armoniche (0 = assente):**")
        cols_thd = st.columns(6)
        harm_vals = {}
        for idx, ord_h in enumerate([2, 3, 4, 5, 6, 7, 9, 11, 13]):
            with cols_thd[idx % 6]:
                v_h = st.number_input(f"H{ord_h} [Vrms]", value=0.0 if ord_h % 2 == 0 else (V1_thd*0.3 if ord_h == 3 else V1_thd*0.1), min_value=0.0, key=f"thd_h{ord_h}")
                if v_h > 0:
                    harm_vals[ord_h] = v_h
        if st.button("Calcola THD", key="thd_btn"):
            try:
                res_thd = thd.calcola_thd(V1_thd, harm_vals)
                st.session_state["_thd_result"] = {"V1": V1_thd, "harm_vals": harm_vals, "res": res_thd}
            except (ValueError, ZeroDivisionError) as e:
                st.session_state["_thd_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_thd_result")
        if rr:
            res_thd = rr["res"]
            c1, c2, c3 = st.columns(3)
            c1.metric("THD", f"{res_thd['THD_pct']:.2f} %")
            c2.metric("V_rms totale", f"{res_thd['rms_totale']:.2f} V")
            c3.metric("Giudizio IEEE", res_thd['giudizio_ieee'])
            if res_thd["contributi"]:
                st.markdown("**Contributi per ordine:**")
                contrib_str = "  ".join([f"H{k}: {v:.1f}%" for k, v in sorted(res_thd["contributi"].items())])
                st.text(contrib_str)
            if _PLOTLY:
                onda = thd.forma_onda_armonica(rr["V1"], rr["harm_vals"], 50.0, 2, 500)
                fig_thd = go.Figure()
                fig_thd.add_trace(go.Scatter(x=onda["t_ms"], y=onda["V_tot"], mode="lines", name="V totale", line=dict(color="#2196F3", width=2)))
                for ord_h, vals in onda["per_ordine"].items():
                    fig_thd.add_trace(go.Scatter(x=onda["t_ms"], y=vals, mode="lines", name=f"H{ord_h}", line=dict(dash="dot"), opacity=0.6))
                fig_thd.update_layout(title="Forma d'onda con armoniche", xaxis_title="t [ms]", yaxis_title="V [V]", height=320)
                st.plotly_chart(fig_thd, use_container_width=True)
            _export_csv_button(
                "Armonie e THD",
                {
                    "V1 [Vrms]": rr["V1"], "THD [%]": f"{res_thd['THD_pct']:.2f}",
                    "V_rms totale [V]": f"{res_thd['rms_totale']:.2f}", "Giudizio IEEE": res_thd['giudizio_ieee'],
                },
                key="thd_export",
            )

    elif tipo == "Batterie e UPS":
        st.subheader("Calcolo Batterie e UPS")
        sub_bat = st.radio("Calcolo:", ["Autonomia batteria", "Dimensionamento banco", "Corrente di carica", "Correzione temperatura", "Curve di scarica Li-Ion", "Piombo — Dimensionamento avanzato (IEEE 485)", "Piombo — Capacità effettiva (Peukert)"], horizontal=True, key="bat_sub")
        if sub_bat == "Autonomia batteria":
            col1, col2 = st.columns(2)
            with col1:
                C_Ah    = st.number_input("Capacità nominale C [Ah]:", value=100.0, min_value=1.0, key="bat_C")
                V_nom   = st.number_input("Tensione nominale V [V]:", value=48.0, min_value=1.0, key="bat_V")
            with col2:
                P_W     = st.number_input("Carico P [W]:", value=2000.0, min_value=1.0, key="bat_P")
                eta_inv = st.number_input("η inverter:", value=0.92, min_value=0.5, max_value=1.0, key="bat_eta")
                DOD     = st.number_input("DOD (profondità scarica):", value=0.80, min_value=0.1, max_value=1.0, key="bat_DOD")
            if st.button("Calcola Autonomia", key="bat_btn1"):
                try:
                    r = bat.calcola_autonomia(C_Ah, V_nom, P_W, eta_inv, DOD)
                    st.session_state["_bat1_result"] = {"C_Ah": C_Ah, "V_nom": V_nom, "P_W": P_W, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_bat1_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_bat1_result")
            if rr:
                r = rr["res"]
                c1, c2, c3 = st.columns(3)
                c1.metric("Autonomia", f"{r['t_autonomia_h']:.2f} h  ({r['t_autonomia_min']:.0f} min)")
                c2.metric("Energia utile", f"{r['E_utile_Wh']:.0f} Wh")
                c3.metric("I scarica", f"{r['I_scarica_A']:.1f} A  (C-rate: {r['C_rate']:.2f})")
                _export_csv_button(
                    "Batterie e UPS — Autonomia",
                    {"C [Ah]": rr["C_Ah"], "V [V]": rr["V_nom"], "Carico [W]": rr["P_W"],
                     "Autonomia [h]": f"{r['t_autonomia_h']:.2f}", "Energia utile [Wh]": f"{r['E_utile_Wh']:.0f}"},
                    key="bat1_export",
                )
        elif sub_bat == "Dimensionamento banco":
            col1, col2 = st.columns(2)
            with col1:
                P_dim   = st.number_input("Carico P [W]:", value=3000.0, min_value=1.0, key="bat_dimP")
                t_aut   = st.number_input("Autonomia richiesta [h]:", value=1.0, min_value=0.1, key="bat_dimt")
            with col2:
                V_ban   = st.number_input("Tensione banco [V]:", value=48.0, min_value=1.0, key="bat_dimV")
                fa      = st.number_input("Fattore invecchiamento:", value=1.25, min_value=1.0, key="bat_dimfa")
            if st.button("Dimensiona Banco", key="bat_btn2"):
                try:
                    r = bat.dimensiona_banco(P_dim, t_aut, V_ban, 0.92, 0.80, fa)
                    st.session_state["_bat2_result"] = {"P_dim": P_dim, "t_aut": t_aut, "V_ban": V_ban, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_bat2_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_bat2_result")
            if rr:
                r = rr["res"]
                c1, c2 = st.columns(2)
                c1.metric("C nominale richiesta", f"{r['C_nominale_Ah']:.0f} Ah")
                c2.metric("Energia richiesta", f"{r['E_richiesta_Wh']:.0f} Wh")
                _export_csv_button(
                    "Batterie e UPS — Dimensionamento banco",
                    {"Carico [W]": rr["P_dim"], "Autonomia [h]": rr["t_aut"], "V banco [V]": rr["V_ban"],
                     "C nominale [Ah]": f"{r['C_nominale_Ah']:.0f}", "Energia richiesta [Wh]": f"{r['E_richiesta_Wh']:.0f}"},
                    key="bat2_export",
                )
        elif sub_bat == "Corrente di carica":
            C_ch = st.number_input("Capacità C [Ah]:", value=100.0, min_value=1.0, key="bat_chC")
            if st.button("Calcola Correnti", key="bat_btn3"):
                r = bat.corrente_carica(C_ch)
                st.session_state["_bat3_result"] = {"C_ch": C_ch, "res": r}

            rr = st.session_state.get("_bat3_result")
            if rr:
                r = rr["res"]
                st.markdown(f"**I_C1** = {r['I_C1_A']:.1f} A  |  **I_C5** = {r['I_C5_A']:.1f} A  |  **I_C10** = {r['I_C10_A']:.1f} A  |  **I_C20** = {r['I_C20_A']:.1f} A  |  **I_float** = {r['I_float_A']:.2f} A")
                _export_csv_button(
                    "Batterie e UPS — Corrente di carica",
                    {"C [Ah]": rr["C_ch"], "I_C1 [A]": f"{r['I_C1_A']:.1f}", "I_C5 [A]": f"{r['I_C5_A']:.1f}",
                     "I_C10 [A]": f"{r['I_C10_A']:.1f}", "I_float [A]": f"{r['I_float_A']:.2f}"},
                    key="bat3_export",
                )
        elif sub_bat == "Correzione temperatura":
            col1, col2 = st.columns(2)
            with col1:
                C_T  = st.number_input("Capacità C [Ah]:", value=100.0, min_value=1.0, key="bat_TC")
                T_C  = st.number_input("Temperatura [°C]:", value=25.0, key="bat_Temp")
            with col2:
                tipo_bat = st.selectbox("Tipo batteria:", ["piombo", "Li-ion", "NiMH"], key="bat_tipo")
            if st.button("Correggi per Temperatura", key="bat_btn4"):
                try:
                    r = bat.correzione_temperatura(C_T, T_C, tipo_bat)
                    st.session_state["_bat4_result"] = {"C_T": C_T, "T_C": T_C, "tipo_bat": tipo_bat, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_bat4_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_bat4_result")
            if rr:
                r = rr["res"]
                st.success(f"C corretta = {r['C_corretta_Ah']:.1f} Ah  (riduzione: {r['riduzione_pct']:.1f}%)")
                _export_csv_button(
                    "Batterie e UPS — Correzione temperatura",
                    {"C [Ah]": rr["C_T"], "Temperatura [°C]": rr["T_C"], "Tipo batteria": rr["tipo_bat"],
                     "C corretta [Ah]": f"{r['C_corretta_Ah']:.1f}", "Riduzione [%]": f"{r['riduzione_pct']:.1f}"},
                    key="bat4_export",
                )

        elif sub_bat == "Curve di scarica Li-Ion":
            st.caption(
                "Modello empirico (tabella OCV vs SOC tipica per celle Li-Ion NMC/NCA a 25°C) con "
                "caduta da resistenza interna e riduzione di capacità da legge di Peukert. "
                "Utile per stime/confronti; per il dimensionamento finale fare riferimento al datasheet del costruttore."
            )
            col1, col2, col3 = st.columns(3)
            with col1:
                C_nom_li = st.number_input("Capacità nominale cella/ramo [Ah]:", value=3.0, min_value=0.01, key="bli_C")
                n_serie  = st.number_input("Celle in serie:", value=4, min_value=1, step=1, key="bli_ns")
            with col2:
                n_par    = st.number_input("Celle in parallelo:", value=1, min_value=1, step=1, key="bli_np")
                R_int    = st.number_input("Resistenza interna per cella [Ω]:", value=0.02, min_value=0.0, step=0.005, format="%.3f", key="bli_rint")
            with col3:
                soc_fin  = st.number_input("SOC finale di cutoff [%]:", value=0.0, min_value=0.0, max_value=99.0, key="bli_socfin")
                c_rates_str = st.text_input("C-rate da confrontare (separati da virgola):", value="0.2, 0.5, 1, 2", key="bli_crates")

            if st.button("Genera Curve di Scarica", key="bli_btn"):
                try:
                    c_rates = [float(x.strip()) for x in c_rates_str.split(",") if x.strip()]
                    curve = blit.confronto_c_rate(C_nom_li, c_rates, int(n_serie), int(n_par), R_int, soc_fin)
                    st.session_state["_bli_result"] = {
                        "C_nom_li": C_nom_li, "n_serie": int(n_serie), "n_par": int(n_par),
                        "R_int": R_int, "soc_fin": soc_fin, "curve": curve,
                    }
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_bli_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_bli_result")
            if rr:
                curve = rr["curve"]
                import pandas as pd
                df_v = pd.DataFrame({
                    f"{cr}C": pd.Series(c["tensione_pacco_V"], index=c["capacita_erogata_Ah"])
                    for cr, c in curve.items()
                })
                st.markdown("**Tensione pacco [V] vs Capacità erogata [Ah]** (una curva per C-rate)")
                st.line_chart(df_v)

                righe_riepilogo = []
                for cr, c in curve.items():
                    righe_riepilogo.append({
                        "C-rate": cr,
                        "Autonomia [h]": c["t_autonomia_h"],
                        "Capacità effettiva pacco [Ah]": c["C_eff_pacco_Ah"],
                        "Corrente pacco [A]": c["I_pacco_A"],
                        "V iniziale [V]": c["tensione_iniziale_V"],
                        "V finale [V]": c["tensione_finale_V"],
                    })
                st.dataframe(pd.DataFrame(righe_riepilogo), hide_index=True, use_container_width=True)

                v_nom_pacco = next(iter(curve.values()))["tensione_nominale_pacco_V"]
                st.metric("Tensione nominale pacco (SOC 50%)", f"{v_nom_pacco:.1f} V")

                dati_export = {"C nominale [Ah]": rr["C_nom_li"], "Celle serie": rr["n_serie"], "Celle parallelo": rr["n_par"],
                               "R interna [Ω]": rr["R_int"], "SOC finale [%]": rr["soc_fin"]}
                for cr, c in curve.items():
                    dati_export[f"Autonomia a {cr}C [h]"] = round(c["t_autonomia_h"], 2)
                    dati_export[f"V finale a {cr}C [V]"] = c["tensione_finale_V"]
                _export_csv_button("Batterie Li-Ion — Curve di scarica", dati_export, key="bli_export")

        elif sub_bat == "Piombo — Dimensionamento avanzato (IEEE 485)":
            st.caption(
                "Si appoggia allo stesso dimensionamento di base di 'Dimensionamento banco' (DOD/invecchiamento) "
                "e aggiunge: correzione IEEE 485 per temperatura, numero di celle in serie e tensione di fine scarica."
            )
            col1, col2, col3 = st.columns(3)
            with col1:
                P_pb   = st.number_input("Carico P [W]:", value=5000.0, min_value=1.0, key="pb_P")
                t_pb   = st.number_input("Autonomia richiesta [h]:", value=0.5, min_value=0.1, key="pb_t")
            with col2:
                V_pb   = st.number_input("Tensione banco [V]:", value=48.0, min_value=1.0, key="pb_V")
                eta_pb = st.number_input("η inverter:", value=0.90, min_value=0.5, max_value=1.0, key="pb_eta")
                DOD_pb = st.number_input("DOD (profondità scarica):", value=0.80, min_value=0.1, max_value=1.0, key="pb_DOD")
            with col3:
                fa_pb  = st.number_input("Fattore invecchiamento:", value=1.25, min_value=1.0, key="pb_fa")
                T_pb   = st.number_input("Temperatura ambiente prevista [°C]:", value=20.0, key="pb_T")
                tc_pb  = st.number_input("Tasso di carica boost [C]:", value=0.10, min_value=0.01, key="pb_tc")
            if st.button("Dimensiona Banco Piombo", key="pb_btn1"):
                try:
                    r = batterie_piombo.dimensionamento_completo(P_pb, t_pb, V_pb, eta_pb, DOD_pb, fa_pb, T_pb, tc_pb)
                    st.session_state["_pb1_result"] = r
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_pb1_result"] = None
                    st.error(str(e))

            r = st.session_state.get("_pb1_result")
            if r:
                c1, c2, c3 = st.columns(3)
                c1.metric("C nominale (base, 25°C)", f"{r['C_nominale_Ah']:.1f} Ah")
                c2.metric("C corretta (temperatura)", f"{r['Ah_corretti_temperatura']:.1f} Ah")
                c3.metric("Fattore temperatura", f"{r['fattore_temperatura']:.2f}")
                c1.metric("Celle in serie", f"{r['n_celle']}")
                c2.metric("Tensione fine scarica", f"{r['V_fine_scarica_bus']:.1f} V")
                c3.metric("Corrente carica boost", f"{r['I_carica_A']:.2f} A")
                _export_csv_button(
                    "Batterie e UPS — Piombo, dimensionamento avanzato",
                    {"Carico [W]": P_pb, "Autonomia [h]": t_pb, "V banco [V]": V_pb, "DOD": DOD_pb,
                     "T ambiente [°C]": T_pb, "C nominale base [Ah]": f"{r['C_nominale_Ah']:.1f}",
                     "C corretta temperatura [Ah]": f"{r['Ah_corretti_temperatura']:.1f}",
                     "Celle in serie": r["n_celle"], "V fine scarica [V]": f"{r['V_fine_scarica_bus']:.1f}",
                     "I carica boost [A]": f"{r['I_carica_A']:.2f}"},
                    key="pb1_export",
                )

        elif sub_bat == "Piombo — Capacità effettiva (Peukert)":
            st.caption(
                "A scariche rapide (tipiche UPS, minuti anziché 10h) la capacità utile del piombo è "
                "sensibilmente inferiore a quella nominale (legge di Peukert)."
            )
            col1, col2 = st.columns(2)
            with col1:
                C_pk  = st.number_input("Capacità nominale a 10h [Ah]:", value=100.0, min_value=1.0, key="pk_C")
                t_pk  = st.number_input("Tempo di scarica effettivo [h]:", value=0.5, min_value=0.01, key="pk_t")
            with col2:
                k_pk  = st.number_input("Esponente di Peukert k:", value=1.3, min_value=1.0, max_value=2.0, step=0.01, key="pk_k")
            if st.button("Calcola Capacità Effettiva", key="pb_btn2"):
                try:
                    r = batterie_piombo.capacita_effettiva_scarica(C_pk, t_pk, k_pk)
                    st.session_state["_pb2_result"] = {"C_pk": C_pk, "t_pk": t_pk, "k_pk": k_pk, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_pb2_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_pb2_result")
            if rr:
                r = rr["res"]
                c1, c2 = st.columns(2)
                c1.metric("Capacità effettiva", f"{r['C_eff_Ah']:.1f} Ah")
                c2.metric("Corrente di scarica", f"{r['I_scarica_A']:.1f} A")
                _export_csv_button(
                    "Batterie e UPS — Piombo, capacità effettiva (Peukert)",
                    {"C nominale 10h [Ah]": rr["C_pk"], "Tempo scarica [h]": rr["t_pk"], "k Peukert": rr["k_pk"],
                     "C effettiva [Ah]": f"{r['C_eff_Ah']:.1f}", "I scarica [A]": f"{r['I_scarica_A']:.1f}"},
                    key="pb2_export",
                )

    elif tipo == "Dissipatore Termico":
        st.subheader("Calcolo Dissipatore Termico (IEC 60747 / JEDEC)")
        sub_diss = st.radio("Calcolo:", ["Temperatura giunzione", "R_sa necessario", "Curva di derating"], horizontal=True, key="diss_sub")
        if sub_diss == "Temperatura giunzione":
            col1, col2 = st.columns(2)
            with col1:
                P_diss  = st.number_input("Potenza dissipata P [W]:", value=50.0, min_value=0.0, key="diss_P")
                T_amb_d = st.number_input("Temperatura ambiente [°C]:", value=25.0, key="diss_Tamb")
                R_jc    = st.number_input("R_jc [°C/W]:", value=1.5, min_value=0.0, key="diss_Rjc")
            with col2:
                pasta_sel = st.selectbox("Pasta termica:", list(diss.PASTA_TERMICA.keys()), key="diss_pasta")
                R_cs    = diss.PASTA_TERMICA[pasta_sel]
                st.info(f"R_cs = {R_cs} °C/W")
                R_sa    = st.number_input("R_sa dissipatore [°C/W]:", value=2.0, min_value=0.0, key="diss_Rsa")
            if st.button("Calcola Tj", key="diss_btn1"):
                try:
                    r = diss.temperatura_giunzione(P_diss, T_amb_d, R_jc, R_cs, R_sa)
                    st.session_state["_diss1_result"] = {"P": P_diss, "T_amb": T_amb_d, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_diss1_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_diss1_result")
            if rr:
                r = rr["res"]
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Tj [°C]", f"{r['Tj_C']:.1f}")
                c2.metric("T_case [°C]", f"{r['T_case_C']:.1f}")
                c3.metric("T_diss [°C]", f"{r['T_diss_C']:.1f}")
                c4.metric("R_tot [°C/W]", f"{r['R_tot_CW']:.3f}")
                _export_csv_button(
                    "Dissipatore Termico — Tj",
                    {"P [W]": rr["P"], "T amb [°C]": rr["T_amb"], "Tj [°C]": f"{r['Tj_C']:.1f}", "R_tot [°C/W]": f"{r['R_tot_CW']:.3f}"},
                    key="diss1_export",
                )
        elif sub_diss == "R_sa necessario":
            col1, col2 = st.columns(2)
            with col1:
                P_rsa   = st.number_input("Potenza P [W]:", value=50.0, min_value=0.1, key="rsa_P")
                Tj_max  = st.number_input("Tj_max [°C]:", value=150.0, key="rsa_Tjmax")
            with col2:
                T_amb_r = st.number_input("T ambiente [°C]:", value=40.0, key="rsa_Tamb")
                R_jc_r  = st.number_input("R_jc [°C/W]:", value=1.5, min_value=0.0, key="rsa_Rjc")
            if st.button("Calcola R_sa", key="rsa_btn"):
                try:
                    r = diss.rsa_necessario(P_rsa, Tj_max, T_amb_r, R_jc_r)
                    st.session_state["_rsa_result"] = {"P": P_rsa, "Tj_max": Tj_max, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_rsa_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_rsa_result")
            if rr:
                r = rr["res"]
                st.success(f"R_sa max = {r['R_sa_max_CW']:.3f} °C/W  (budget termico = {r['budget_CW']:.3f} °C/W)")
                _export_csv_button(
                    "Dissipatore Termico — R_sa",
                    {"P [W]": rr["P"], "Tj_max [°C]": rr["Tj_max"], "R_sa max [°C/W]": f"{r['R_sa_max_CW']:.3f}"},
                    key="rsa_export",
                )
        else:
            col1, col2 = st.columns(2)
            with col1:
                P25     = st.number_input("P_max a 25°C [W]:", value=100.0, min_value=1.0, key="der_P25")
                Tj_der  = st.number_input("Tj_max [°C]:", value=150.0, key="der_Tj")
            with col2:
                T_max_d = st.number_input("T_amb max asse X [°C]:", value=120.0, key="der_Tmax")
            if _PLOTLY:
                r = diss.curva_derating(P25, Tj_der, T_max_d)
                fig_der = go.Figure()
                fig_der.add_trace(go.Scatter(x=r["T_amb_C"], y=r["P_max_W"], mode="lines", fill="tozeroy", name="P_max", line=dict(color="#FF5722", width=2)))
                fig_der.update_layout(title="Curva di Derating", xaxis_title="T ambiente [°C]", yaxis_title="P_max [W]", height=320)
                st.plotly_chart(fig_der, use_container_width=True)
                _export_csv_button(
                    "Dissipatore Termico — Derating",
                    {"P @25°C [W]": P25, "Tj_max [°C]": Tj_der, "T_max asse [°C]": T_max_d},
                    key="der_export_plot",
                )
            else:
                if st.button("Calcola Derating", key="der_btn"):
                    r = diss.curva_derating(P25, Tj_der, T_max_d)
                    st.session_state["_der_result"] = {"P25": P25, "Tj_der": Tj_der, "res": r}

                rr = st.session_state.get("_der_result")
                if rr:
                    r = rr["res"]
                    st.write({f"{t:.0f}°C": f"{p:.1f} W" for t, p in zip(r["T_amb_C"], r["P_max_W"])})
                    _export_csv_button(
                        "Dissipatore Termico — Derating",
                        {"P @25°C [W]": rr["P25"], "Tj_max [°C]": rr["Tj_der"]},
                        key="der_export_nb",
                    )

    elif tipo == "Impianto di Terra":
        st.subheader("Impianto di Terra (CEI 64-8 / CEI 11-1)")
        sub_terra = st.radio("Calcolo:", ["Resistenza dispersore", "Sezione minima PE", "Verifica tensione di contatto", "Coordinamento TT"], horizontal=True, key="terra_sub")
        if sub_terra == "Resistenza dispersore":
            col1, col2 = st.columns(2)
            with col1:
                L_picchetto = st.number_input("Lunghezza picchetto L [m]:", value=2.0, min_value=0.1, key="terra_L")
                rho_sel = st.selectbox("Tipo terreno:", list(terra.RESISTIVITA_TERRENO.keys()), key="terra_rho_sel")
                rho_val = terra.RESISTIVITA_TERRENO[rho_sel]
                st.info(f"ρ = {rho_val} Ω·m")
            with col2:
                d_picchetto = st.number_input("Diametro picchetto d [mm]:", value=20.0, min_value=1.0, key="terra_d") / 1000.0
                n_picchetti = st.number_input("Numero picchetti in parallelo:", value=1, min_value=1, step=1, key="terra_n")
            if st.button("Calcola Resistenza", key="terra_btn1"):
                try:
                    r1 = terra.resistenza_dispersore_picchetto(L_picchetto, rho_val, d_picchetto)
                    r2 = terra.resistenza_picchetti_paralleli(r1["R_ohm"], int(n_picchetti)) if n_picchetti > 1 else None
                    st.session_state["_terra1_result"] = {"L": L_picchetto, "n": n_picchetti, "r1": r1, "r2": r2}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_terra1_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_terra1_result")
            if rr:
                r1, r2 = rr["r1"], rr["r2"]
                if r2 is not None:
                    st.success(f"R singolo picchetto = {r1['R_ohm']:.2f} Ω  →  R equivalente ({int(rr['n'])} picchetti) = {r2['R_eq_ohm']:.2f} Ω")
                    r_export = f"{r2['R_eq_ohm']:.2f}"
                else:
                    st.success(f"R dispersore = {r1['R_ohm']:.2f} Ω")
                    r_export = f"{r1['R_ohm']:.2f}"
                _export_csv_button(
                    "Impianto di Terra — Resistenza dispersore",
                    {"Lunghezza [m]": rr["L"], "N picchetti": rr["n"], "R equivalente [Ω]": r_export},
                    key="terra1_export",
                )
        elif sub_terra == "Sezione minima PE":
            col1, col2 = st.columns(2)
            with col1:
                I_g = st.number_input("Corrente di guasto I_g [A]:", value=1000.0, min_value=1.0, key="terra_Ig")
                t_int = st.number_input("Tempo di intervento t [s]:", value=0.5, min_value=0.01, key="terra_t")
            with col2:
                k_mat = st.selectbox("Materiale/isolamento:", ["Rame con PVC (k=143)", "Rame con XLPE (k=176)", "Alluminio con PVC (k=95)"], key="terra_k")
                k_val = {"Rame con PVC (k=143)": 143.0, "Rame con XLPE (k=176)": 176.0, "Alluminio con PVC (k=95)": 95.0}[k_mat]
            if st.button("Calcola Sezione PE", key="terra_btn2"):
                try:
                    r = terra.sezione_minima_pe(I_g, t_int, k_val)
                    st.session_state["_terra2_result"] = {"I_g": I_g, "t_int": t_int, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_terra2_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_terra2_result")
            if rr:
                r = rr["res"]
                st.success(f"Sezione minima PE = {r['S_mm2_minima']:.2f} mm²")
                st.caption("Arrotondare alla sezione commerciale superiore disponibile.")
                _export_csv_button(
                    "Impianto di Terra — Sezione PE",
                    {"I_g [A]": rr["I_g"], "t [s]": rr["t_int"], "Sezione minima [mm2]": f"{r['S_mm2_minima']:.2f}"},
                    key="terra2_export",
                )
        elif sub_terra == "Verifica tensione di contatto":
            col1, col2 = st.columns(2)
            with col1:
                R_t = st.number_input("Resistenza di terra R [Ω]:", value=20.0, min_value=0.1, key="terra_Rt")
                I_g2 = st.number_input("Corrente di guasto I_g [A]:", value=0.5, min_value=0.001, key="terra_Ig2")
            with col2:
                UTp = st.number_input("Tensione di contatto limite UTp [V]:", value=50.0, min_value=1.0, key="terra_UTp")
            if st.button("Verifica", key="terra_btn3"):
                try:
                    r = terra.verifica_tensione_contatto(R_t, I_g2, UTp)
                    st.session_state["_terra3_result"] = {"R_t": R_t, "I_g2": I_g2, "UTp": UTp, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_terra3_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_terra3_result")
            if rr:
                r = rr["res"]
                colore = "success" if r["conforme"] else "error"
                getattr(st, colore)(f"U_c = {r['U_c_V']:.2f} V  (limite {rr['UTp']} V)  —  {r['giudizio']}")
                _export_csv_button(
                    "Impianto di Terra — Tensione di contatto",
                    {"R [Ω]": rr["R_t"], "I_g [A]": rr["I_g2"], "UTp [V]": rr["UTp"], "U_c [V]": f"{r['U_c_V']:.2f}", "Conforme": r["conforme"]},
                    key="terra3_export",
                )
        else:
            col1, col2 = st.columns(2)
            with col1:
                R_tt = st.number_input("Resistenza di terra R [Ω]:", value=20.0, min_value=0.1, key="terra_Rtt")
            with col2:
                I_dn = st.number_input("Corrente diff. nominale I_dn [A]:", value=0.3, min_value=0.001, key="terra_Idn")
            if st.button("Verifica Coordinamento", key="terra_btn4"):
                try:
                    r = terra.coordinamento_tt(R_tt, I_dn)
                    st.session_state["_terra4_result"] = {"R_tt": R_tt, "I_dn": I_dn, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_terra4_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_terra4_result")
            if rr:
                r = rr["res"]
                colore = "success" if r["conforme"] else "error"
                getattr(st, colore)(f"R_max ammessa = {r['R_max_ohm']:.2f} Ω  —  {r['giudizio']}")
                _export_csv_button(
                    "Impianto di Terra — Coordinamento TT",
                    {"R [Ω]": rr["R_tt"], "I_dn [A]": rr["I_dn"], "R_max ammessa [Ω]": f"{r['R_max_ohm']:.2f}", "Conforme": r["conforme"]},
                    key="terra4_export",
                )

    elif tipo == "Selettività Protezioni":
        st.subheader("Selettività e Coordinamento Protezioni (CEI 64-8 / IEC 60947-2)")
        sub_sel = st.radio("Calcolo:", ["Selettività amperometrica", "Selettività differenziale", "Icc minima", "Curve di intervento"], horizontal=True, key="sel_sub")
        if sub_sel == "Selettività amperometrica":
            col1, col2 = st.columns(2)
            with col1:
                I_monte = st.number_input("I_n interruttore a monte [A]:", value=100.0, min_value=1.0, key="sel_Imonte")
            with col2:
                I_valle = st.number_input("I_n interruttore a valle [A]:", value=40.0, min_value=1.0, key="sel_Ivalle")
            if st.button("Verifica Selettività", key="sel_btn1"):
                try:
                    r = selet.verifica_selettivita_amperometrica(I_monte, I_valle)
                    st.session_state["_sel1_result"] = {"I_monte": I_monte, "I_valle": I_valle, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_sel1_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_sel1_result")
            if rr:
                r = rr["res"]
                colore = "success" if r["selettivo"] else "error"
                getattr(st, colore)(f"Rapporto = {r['rapporto']:.2f}  (minimo {r['rapporto_minimo']})  —  {r['giudizio']}")
                _export_csv_button(
                    "Selettività Protezioni — Amperometrica",
                    {"I monte [A]": rr["I_monte"], "I valle [A]": rr["I_valle"], "Selettivo": r["selettivo"]},
                    key="sel1_export",
                )
        elif sub_sel == "Selettività differenziale":
            col1, col2 = st.columns(2)
            with col1:
                Idn_monte = st.number_input("I_dn a monte [mA]:", value=300.0, min_value=1.0, key="sel_Idnmonte")
                Idn_valle = st.number_input("I_dn a valle [mA]:", value=30.0, min_value=1.0, key="sel_Idnvalle")
            with col2:
                t_monte = st.number_input("Tempo intervento a monte [ms] (0=non noto):", value=0.0, min_value=0.0, key="sel_tmonte")
                t_valle = st.number_input("Tempo intervento a valle [ms] (0=non noto):", value=0.0, min_value=0.0, key="sel_tvalle")
            if st.button("Verifica Selettività Diff.", key="sel_btn2"):
                try:
                    r = selet.verifica_selettivita_differenziale(Idn_monte, Idn_valle, t_monte, t_valle)
                    st.session_state["_sel2_result"] = {"Idn_monte": Idn_monte, "Idn_valle": Idn_valle, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_sel2_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_sel2_result")
            if rr:
                r = rr["res"]
                st.info(f"Rapporto I_dn = {r['rapporto_Idn']:.2f}  —  {r['giudizio']}")
                _export_csv_button(
                    "Selettività Protezioni — Differenziale",
                    {"I_dn monte [mA]": rr["Idn_monte"], "I_dn valle [mA]": rr["Idn_valle"], "Rapporto": f"{r['rapporto_Idn']:.2f}"},
                    key="sel2_export",
                )
        elif sub_sel == "Icc minima":
            col1, col2 = st.columns(2)
            with col1:
                V_icc = st.number_input("Tensione V [V]:", value=230.0, min_value=1.0, key="sel_Vicc")
            with col2:
                Z_icc = st.number_input("Impedenza anello di guasto Z [Ω]:", value=0.5, min_value=0.001, key="sel_Zicc")
            if st.button("Calcola Icc min", key="sel_btn3"):
                try:
                    r = selet.corrente_corto_circuito_minima(V_icc, Z_icc)
                    st.session_state["_sel3_result"] = {"V": V_icc, "Z": Z_icc, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_sel3_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_sel3_result")
            if rr:
                r = rr["res"]
                st.success(f"Icc minima = {r['Icc_min_A']:.1f} A")
                _export_csv_button(
                    "Selettività Protezioni — Icc minima",
                    {"V [V]": rr["V"], "Z [Ω]": rr["Z"], "Icc minima [A]": f"{r['Icc_min_A']:.1f}"},
                    key="sel3_export",
                )
        else:
            col1, col2 = st.columns(2)
            with col1:
                curva_sel = st.selectbox("Tipo curva:", ["B", "C", "D", "K", "Z"], index=1, key="sel_curva")
            with col2:
                I_In = st.number_input("Rapporto I/In:", value=7.0, min_value=0.1, key="sel_I_In")
            if st.button("Verifica Zona", key="sel_btn4"):
                try:
                    r = selet.tempo_intervento_curva(I_In, curva_sel)
                    st.session_state["_sel4_result"] = {"curva": curva_sel, "I_In": I_In, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_sel4_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_sel4_result")
            if rr:
                r = rr["res"]
                st.info(f"Zona: {r['zona_intervento']}  (soglia magnetica {r['soglia_min_In']}-{r['soglia_max_In']} In)")
                st.caption("Curve: " + "  |  ".join([f"**{k}**: {v}" for k, v in selet.CURVE_MAGNETOTERMICI.items()]))
                _export_csv_button(
                    "Selettività Protezioni — Curve di intervento",
                    {"Curva": rr["curva"], "I/In": rr["I_In"], "Zona": r["zona_intervento"]},
                    key="sel4_export",
                )

    elif tipo == "Fotovoltaico":
        st.subheader("Dimensionamento Impianto Fotovoltaico")
        sub_fv = st.radio("Calcolo:", ["Producibilità annua", "Numero pannelli", "Stringa e inverter", "Tempo di ritorno"], horizontal=True, key="fv_sub")
        if sub_fv == "Producibilità annua":
            col1, col2 = st.columns(2)
            with col1:
                P_picco = st.number_input("Potenza di picco [kWp]:", value=6.0, min_value=0.1, key="fv_Ppicco")
                zona_sel = st.selectbox("Zona geografica:", list(fv.IRRAGGIAMENTO_ITALIA.keys()), key="fv_zona")
                irraggio = fv.IRRAGGIAMENTO_ITALIA[zona_sel]
            with col2:
                PR = st.number_input("Performance Ratio:", value=0.80, min_value=0.5, max_value=1.0, key="fv_PR")
            if st.button("Calcola Producibilità", key="fv_btn1"):
                try:
                    r = fv.producibilita_annua(P_picco, irraggio, PR)
                    st.session_state["_fv1_result"] = {"P_picco": P_picco, "zona": zona_sel, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_fv1_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_fv1_result")
            if rr:
                r = rr["res"]
                c1, c2, c3 = st.columns(3)
                c1.metric("E annua", f"{r['E_anno_kWh']:.0f} kWh")
                c2.metric("E mensile media", f"{r['E_mese_kWh']:.0f} kWh")
                c3.metric("Ore equivalenti", f"{r['ore_equivalenti_h']:.0f} h")
                _export_csv_button(
                    "Fotovoltaico — Producibilità",
                    {"P picco [kWp]": rr["P_picco"], "Zona": rr["zona"], "E annua [kWh]": f"{r['E_anno_kWh']:.0f}"},
                    key="fv1_export",
                )
        elif sub_fv == "Numero pannelli":
            col1, col2 = st.columns(2)
            with col1:
                P_rich = st.number_input("Potenza richiesta [kWp]:", value=6.0, min_value=0.1, key="fv_Prich")
            with col2:
                P_pan = st.number_input("Potenza per pannello [Wp]:", value=450.0, min_value=50.0, key="fv_Ppan")
            if st.button("Calcola Numero Pannelli", key="fv_btn2"):
                try:
                    r = fv.numero_pannelli(P_rich, P_pan)
                    st.session_state["_fv2_result"] = {"P_rich": P_rich, "P_pan": P_pan, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_fv2_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_fv2_result")
            if rr:
                r = rr["res"]
                st.success(f"Pannelli necessari: {r['n_pannelli']}  →  Potenza reale: {r['P_reale_kWp']:.2f} kWp")
                _export_csv_button(
                    "Fotovoltaico — Numero pannelli",
                    {"P richiesta [kWp]": rr["P_rich"], "P pannello [Wp]": rr["P_pan"], "N pannelli": r["n_pannelli"]},
                    key="fv2_export",
                )
        elif sub_fv == "Stringa e inverter":
            col1, col2 = st.columns(2)
            with col1:
                V_oc = st.number_input("V_oc pannello [V]:", value=45.0, min_value=1.0, key="fv_Voc")
                n_pan_str = st.number_input("Pannelli in serie:", value=20, min_value=1, step=1, key="fv_npanstr")
            with col2:
                V_max_inv = st.number_input("V max inverter [V]:", value=1000.0, min_value=1.0, key="fv_Vmaxinv")
                T_min = st.number_input("T minima di progetto [°C]:", value=-10.0, key="fv_Tmin")
            if st.button("Verifica Stringa", key="fv_btn3"):
                try:
                    r = fv.dimensiona_stringa(V_oc, int(n_pan_str), V_max_inv, -0.30, T_min)
                    st.session_state["_fv3_result"] = {"V_oc": V_oc, "n_pan": n_pan_str, "T_min": T_min, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_fv3_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_fv3_result")
            if rr:
                r = rr["res"]
                colore = "success" if r["entro_limiti"] else "error"
                getattr(st, colore)(f"V stringa a {rr['T_min']}°C = {r['V_stringa_V']:.1f} V  —  {r['giudizio']}")
                _export_csv_button(
                    "Fotovoltaico — Stringa",
                    {"V_oc [V]": rr["V_oc"], "N pannelli serie": rr["n_pan"], "V stringa [V]": f"{r['V_stringa_V']:.1f}"},
                    key="fv3_export",
                )
            st.markdown("---")
            P_picco_inv = st.number_input("Potenza di picco impianto [kWp]:", value=6.0, min_value=0.1, key="fv_Ppicco_inv")
            if st.button("Suggerisci Inverter", key="fv_btn4"):
                try:
                    r = fv.scelta_inverter(P_picco_inv)
                    st.session_state["_fv4_result"] = {"P_picco_inv": P_picco_inv, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_fv4_result"] = None
                    st.error(str(e))

            rr4 = st.session_state.get("_fv4_result")
            if rr4:
                r = rr4["res"]
                st.info(f"Potenza inverter consigliata: {r['P_inverter_kW']:.2f} kW  (DC/AC ratio {r['rapporto_DC_AC']})")
                _export_csv_button(
                    "Fotovoltaico — Inverter",
                    {"P picco impianto [kWp]": rr4["P_picco_inv"], "P inverter [kW]": f"{r['P_inverter_kW']:.2f}"},
                    key="fv4_export",
                )
        else:
            col1, col2 = st.columns(2)
            with col1:
                costo_imp = st.number_input("Costo impianto [€]:", value=8000.0, min_value=100.0, key="fv_costo")
                E_anno_pb = st.number_input("Energia prodotta annua [kWh]:", value=6720.0, min_value=100.0, key="fv_Eanno")
            with col2:
                prezzo_en = st.number_input("Prezzo energia [€/kWh]:", value=0.25, min_value=0.01, key="fv_prezzo")
                autocons = st.number_input("Autoconsumo [%]:", value=70.0, min_value=1.0, max_value=100.0, key="fv_autocons")
            if st.button("Calcola Payback", key="fv_btn5"):
                try:
                    r = fv.tempo_ritorno_investimento(costo_imp, E_anno_pb, prezzo_en, autocons)
                    st.session_state["_fv5_result"] = {"costo": costo_imp, "E_anno": E_anno_pb, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_fv5_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_fv5_result")
            if rr:
                r = rr["res"]
                st.success(f"Risparmio annuo: {r['risparmio_anno_eur']:.0f} €  —  Payback: {r['payback_anni']:.1f} anni")
                _export_csv_button(
                    "Fotovoltaico — Payback",
                    {"Costo impianto [€]": rr["costo"], "E annua [kWh]": rr["E_anno"], "Payback [anni]": f"{r['payback_anni']:.1f}"},
                    key="fv5_export",
                )

    elif tipo == "Gruppo Elettrogeno":
        st.subheader("Dimensionamento Gruppo Elettrogeno")
        sub_ge = st.radio("Calcolo:", ["Potenza di spunto motore", "Dimensiona gruppo", "Autonomia serbatoio"], horizontal=True, key="ge_sub")
        if sub_ge == "Potenza di spunto motore":
            col1, col2 = st.columns(2)
            with col1:
                P_mot_ge = st.number_input("Potenza motore [kW]:", value=15.0, min_value=0.1, key="ge_Pmot")
                cphi_ge = st.number_input("cos phi:", value=0.85, min_value=0.1, max_value=1.0, key="ge_cphi")
            with col2:
                tipo_avv = st.selectbox("Tipo avviamento:", list(ge.FATTORI_SPUNTO_TIPICI.keys()), key="ge_avv")
                fatt_spunto = ge.FATTORI_SPUNTO_TIPICI[tipo_avv]
                st.info(f"Fattore di spunto: {fatt_spunto}")
            if st.button("Calcola Spunto", key="ge_btn1"):
                try:
                    r = ge.potenza_spunto_motore(P_mot_ge, cphi_ge, fatt_spunto)
                    st.session_state["_ge1_result"] = {"P_mot": P_mot_ge, "tipo_avv": tipo_avv, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_ge1_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_ge1_result")
            if rr:
                r = rr["res"]
                st.success(f"S nominale = {r['S_nom_kVA']:.1f} kVA  →  S di spunto = {r['S_spunto_kVA']:.1f} kVA")
                _export_csv_button(
                    "Gruppo Elettrogeno — Spunto",
                    {"P motore [kW]": rr["P_mot"], "Tipo avviamento": rr["tipo_avv"], "S spunto [kVA]": f"{r['S_spunto_kVA']:.1f}"},
                    key="ge1_export",
                )
        elif sub_ge == "Dimensiona gruppo":
            st.markdown("**Carichi da alimentare:**")
            n_car_ge = st.number_input("Numero carichi:", min_value=1, max_value=10, value=3, step=1, key="ge_ncar")
            carichi = []
            cols_ge = st.columns(int(n_car_ge))
            for i in range(int(n_car_ge)):
                with cols_ge[i]:
                    c_val = st.number_input(f"Carico {i+1} [kW]", value=10.0, min_value=0.0, key=f"ge_c{i}")
                    carichi.append(c_val)
            col1, col2 = st.columns(2)
            with col1:
                cphi_g = st.number_input("cos phi medio:", value=0.85, min_value=0.1, max_value=1.0, key="ge_cphig")
            with col2:
                fc_g = st.number_input("Fattore di contemporaneità:", value=0.80, min_value=0.1, max_value=1.0, key="ge_fcg")
            if st.button("Dimensiona Gruppo", key="ge_btn2"):
                try:
                    r = ge.dimensiona_gruppo(carichi, cphi_g, fc_g)
                    st.session_state["_ge2_result"] = {"carichi": carichi, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_ge2_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_ge2_result")
            if rr:
                r = rr["res"]
                c1, c2 = st.columns(2)
                c1.metric("Potenza gruppo", f"{r['P_gruppo_kW']:.1f} kW")
                c2.metric("Potenza apparente", f"{r['S_gruppo_kVA']:.1f} kVA")
                _export_csv_button(
                    "Gruppo Elettrogeno — Dimensionamento",
                    {"Carichi [kW]": rr["carichi"], "P gruppo [kW]": f"{r['P_gruppo_kW']:.1f}", "S gruppo [kVA]": f"{r['S_gruppo_kVA']:.1f}"},
                    key="ge2_export",
                )
        else:
            col1, col2 = st.columns(2)
            with col1:
                V_serb_ge = st.number_input("Volume serbatoio [L]:", value=500.0, min_value=1.0, key="ge_Vserb")
                P_ge = st.number_input("Potenza gruppo [kW]:", value=50.0, min_value=1.0, key="ge_Pge")
            with col2:
                cons_spec = st.number_input("Consumo specifico [L/kWh]:", value=0.25, min_value=0.05, key="ge_cons")
                fc_carico = st.number_input("Fattore di carico medio:", value=0.75, min_value=0.1, max_value=1.0, key="ge_fccarico")
            if st.button("Calcola Autonomia", key="ge_btn3"):
                try:
                    r = ge.autonomia_serbatoio(V_serb_ge, P_ge, cons_spec, fc_carico)
                    st.session_state["_ge3_result"] = {"V_serb": V_serb_ge, "P_ge": P_ge, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_ge3_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_ge3_result")
            if rr:
                r = rr["res"]
                st.success(f"Autonomia: {r['t_autonomia_h']:.1f} ore  (consumo {r['consumo_orario_L']:.1f} L/h)")
                _export_csv_button(
                    "Gruppo Elettrogeno — Autonomia",
                    {"V serbatoio [L]": rr["V_serb"], "P gruppo [kW]": rr["P_ge"], "Autonomia [h]": f"{r['t_autonomia_h']:.1f}"},
                    key="ge3_export",
                )

    elif tipo == "Quadro Elettrico — Dissipazione":
        st.subheader("Potenza Dissipata e Ventilazione Quadri Elettrici (IEC 61439)")
        sub_qe = st.radio("Calcolo:", ["Potenza dissipata componenti", "Verifica temperatura", "Ventilazione forzata"], horizontal=True, key="qe_sub")
        if sub_qe == "Potenza dissipata componenti":
            st.markdown("**Componenti installati:**")
            n_comp = st.number_input("Numero componenti:", min_value=1, max_value=10, value=3, step=1, key="qe_ncomp")
            componenti = {}
            for i in range(int(n_comp)):
                c1, c2 = st.columns(2)
                with c1:
                    nome_c = st.text_input(f"Nome componente {i+1}:", value=f"Componente {i+1}", key=f"qe_nome{i}")
                with c2:
                    p_c = st.number_input(f"Potenza dissipata [W]:", value=8.0, min_value=0.0, key=f"qe_p{i}")
                componenti[nome_c] = p_c
            if st.button("Somma Potenza Dissipata", key="qe_btn1"):
                try:
                    r = qe.potenza_dissipata_componenti(componenti)
                    st.session_state["_qe1_result"] = {"res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_qe1_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_qe1_result")
            if rr:
                r = rr["res"]
                st.success(f"Potenza totale dissipata: {r['P_tot_W']:.1f} W  ({r['n_componenti']} componenti)")
                _export_csv_button(
                    "Quadro Elettrico — Potenza dissipata",
                    {"N componenti": r["n_componenti"], "P totale [W]": f"{r['P_tot_W']:.1f}"},
                    key="qe1_export",
                )
            st.caption("Valori tipici: " + "  |  ".join([f"**{k}**: {v} W" for k, v in qe.POTENZE_DISSIPATE_TIPICHE_W.items()]))
        elif sub_qe == "Verifica temperatura":
            col1, col2 = st.columns(2)
            with col1:
                P_diss_qe = st.number_input("Potenza dissipata totale [W]:", value=50.0, min_value=0.1, key="qe_Pdiss")
                T_amb_qe = st.number_input("Temperatura ambiente [°C]:", value=30.0, key="qe_Tamb")
            with col2:
                L_qe = st.number_input("Larghezza quadro [m]:", value=0.6, min_value=0.1, key="qe_L")
                H_qe = st.number_input("Altezza quadro [m]:", value=0.8, min_value=0.1, key="qe_H")
                Pr_qe = st.number_input("Profondità quadro [m]:", value=0.3, min_value=0.1, key="qe_Pr")
            a_parete = st.checkbox("Installato a parete", value=False, key="qe_aparete")
            if st.button("Verifica Temperatura", key="qe_btn2"):
                try:
                    sup = qe.superficie_quadro(L_qe, H_qe, Pr_qe, a_parete)
                    r = qe.verifica_temperatura_quadro(P_diss_qe, sup["A_tot_m2"], T_amb_qe)
                    st.session_state["_qe2_result"] = {"P_diss": P_diss_qe, "sup": sup, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_qe2_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_qe2_result")
            if rr:
                r, sup = rr["res"], rr["sup"]
                colore = "success" if r["conforme"] else "error"
                getattr(st, colore)(f"T interna stimata = {r['T_interna_C']:.1f} °C  (ΔT = {r['delta_T_K']:.1f} K)  —  {r['giudizio']}")
                st.caption(f"Superficie di scambio: {sup['A_tot_m2']:.2f} m²")
                _export_csv_button(
                    "Quadro Elettrico — Temperatura",
                    {"P dissipata [W]": rr["P_diss"], "Superficie [m2]": f"{sup['A_tot_m2']:.2f}", "T interna [°C]": f"{r['T_interna_C']:.1f}"},
                    key="qe2_export",
                )
        else:
            col1, col2 = st.columns(2)
            with col1:
                P_diss_v = st.number_input("Potenza dissipata [W]:", value=200.0, min_value=0.1, key="qe_Pdissv")
            with col2:
                dT_max = st.number_input("ΔT massimo ammesso [K]:", value=15.0, min_value=1.0, key="qe_dTmax")
            if st.button("Calcola Portata Ventilazione", key="qe_btn3"):
                try:
                    r = qe.portata_ventilazione_forzata(P_diss_v, dT_max)
                    st.session_state["_qe3_result"] = {"P_diss": P_diss_v, "dT_max": dT_max, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_qe3_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_qe3_result")
            if rr:
                r = rr["res"]
                st.success(f"Portata aria necessaria: {r['Q_m3h']:.1f} m³/h")
                _export_csv_button(
                    "Quadro Elettrico — Ventilazione",
                    {"P dissipata [W]": rr["P_diss"], "ΔT max [K]": rr["dT_max"], "Portata [m3/h]": f"{r['Q_m3h']:.1f}"},
                    key="qe3_export",
                )

    elif tipo == "Rifasamento Condensatori":
        st.subheader("Rifasamento con batterie di condensatori — IEC 60831")
        col1, col2 = st.columns(2)
        with col1:
            P_rf = st.number_input("Potenza attiva P [kW]:", value=50.0, min_value=0.1, key="rf_P")
            cphi_att = st.slider("cos_phi attuale:", 0.50, 0.99, 0.72, step=0.01, key="rf_cphi_att")
        with col2:
            cphi_tgt = st.slider("cos_phi target:", 0.80, 1.00, 0.95, step=0.01, key="rf_cphi_tgt")
            V_rf = st.number_input("Tensione di rete [V]:", value=400.0, min_value=100.0, key="rf_V")
        coll_rf = st.radio("Collegamento condensatori:", ["triangolo", "stella"], horizontal=True, key="rf_coll")
        if st.button("Calcola Rifasamento", key="rf_btn"):
            try:
                ra = rifas.potenza_reattiva_attuale(P_rf, cphi_att)
                rc = rifas.kvar_necessari(P_rf, cphi_att, cphi_tgt)
                rcap = rifas.capacita_condensatori(rc["Q_c_kvar"], V_rf, coll_rf)
                rv = rifas.verifica_rifasamento(P_rf, cphi_att, rc["Q_c_kvar"], V_rf)
                st.session_state["_rf_result"] = {"P": P_rf, "coll": coll_rf, "ra": ra, "rc": rc, "rcap": rcap, "rv": rv}
            except ValueError as e:
                st.session_state["_rf_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_rf_result")
        if rr:
            ra, rc, rcap, rv = rr["ra"], rr["rc"], rr["rcap"], rr["rv"]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Q reattiva attuale", f"{ra['Q_kvar']:.1f} kvar")
            c2.metric("Q_c necessaria", f"{rc['Q_c_kvar']:.1f} kvar")
            c3.metric("Q_c arrotondato", f"{rc['Q_c_kvar_arrotondato']:.0f} kvar")
            c4.metric("cos_phi risultante", f"{rv['cos_phi_risultante']:.3f}")
            st.info(f"Capacità per fase ({rr['coll']}): **{rcap['C_per_fase_uF']:.2f} µF** "
                    f"| Corrente prima: {rv['I_prima_A']:.1f} A → dopo: {rv['I_dopo_A']:.1f} A "
                    f"(riduzione {rv['riduzione_corrente_pct']:.1f}%)")
            if rv["soddisfa_095"]:
                st.success("cos_phi ≥ 0.95 — obiettivo raggiunto")
            else:
                st.warning("cos_phi < 0.95 — aumentare la batteria")
            _export_csv_button(
                "Rifasamento Condensatori",
                {
                    "P [kW]": rr["P"], "Collegamento": rr["coll"], "Q_c necessaria [kvar]": f"{rc['Q_c_kvar']:.1f}",
                    "cos phi risultante": f"{rv['cos_phi_risultante']:.3f}", "C per fase [µF]": f"{rcap['C_per_fase_uF']:.2f}",
                },
                key="rf_export",
            )

    elif tipo == "Caduta Tensione BT (CEI 64-8)":
        st.subheader("Caduta di tensione su cavo BT — CEI 64-8 / IEC 60364")
        col1, col2 = st.columns(2)
        with col1:
            tipo_cv = st.radio("Sistema:", ["trifase", "monofase"], horizontal=True, key="cdvbt_tipo")
            P_cv = st.number_input("Potenza [kW]:", value=10.0, min_value=0.01, key="cdvbt_P")
            V_cv = st.number_input("Tensione nominale [V]:", value=400.0 if "trifase" else 230.0, min_value=100.0, key="cdvbt_V")
        with col2:
            L_cv = st.number_input("Lunghezza cavo [m]:", value=50.0, min_value=0.1, key="cdvbt_L")
            cphi_cv = st.slider("cos_phi:", 0.60, 1.00, 0.90, step=0.01, key="cdvbt_cphi")
            cond_cv = st.radio("Conduttore:", ["rame", "alluminio"], horizontal=True, key="cdvbt_cond")
        dv_max = st.slider("ΔV% massimo ammesso:", 1.0, 10.0, 3.0, step=0.5, key="cdvbt_dvmax")
        if st.button("Calcola Caduta Tensione", key="cdvbt_btn"):
            try:
                if tipo_cv == "trifase":
                    rs = cadbt.sezione_da_caduta_max(P_cv, V_cv, L_cv, dv_max, cphi_cv, "trifase", cond_cv)
                else:
                    rs = cadbt.sezione_da_caduta_max(P_cv, V_cv, L_cv, dv_max, cphi_cv, "monofase", cond_cv)
                rv2 = (cadbt.caduta_tensione_trifase(rs["I_A"], L_cv, rs["S_mm2_normalizzata"], cphi_cv, cond_cv)
                       if tipo_cv == "trifase"
                       else cadbt.caduta_tensione_monofase(rs["I_A"], L_cv, rs["S_mm2_normalizzata"], cphi_cv, cond_cv))
                st.session_state["_cdvbt_result"] = {
                    "tipo_cv": tipo_cv, "P": P_cv, "L": L_cv, "cond": cond_cv, "rs": rs, "rv2": rv2,
                }
            except (ValueError, ZeroDivisionError) as e:
                st.session_state["_cdvbt_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_cdvbt_result")
        if rr:
            rs, rv2 = rr["rs"], rr["rv2"]
            c1, c2, c3 = st.columns(3)
            c1.metric("Sezione minima calcolata", f"{rs['S_mm2_calcolata']:.2f} mm²")
            c2.metric("Sezione normalizzata", f"{rs['S_mm2_normalizzata']:.0f} mm²")
            c3.metric("Corrente", f"{rs['I_A']:.1f} A")
            st.info(f"Con {rs['S_mm2_normalizzata']:.0f} mm² ({rr['cond']}): "
                    f"ΔV = {rv2['dV_V']:.2f} V = **{rv2['dV_pct']:.2f}%**")
            (st.success if rv2["conforme_3pct"] else st.warning)(rv2["giudizio"])
            _export_csv_button(
                "Caduta Tensione BT",
                {
                    "Sistema": rr["tipo_cv"], "P [kW]": rr["P"], "Lunghezza [m]": rr["L"], "Conduttore": rr["cond"],
                    "Sezione normalizzata [mm2]": f"{rs['S_mm2_normalizzata']:.0f}", "ΔV [%]": f"{rv2['dV_pct']:.2f}",
                },
                key="cdvbt_export",
            )

    elif tipo == "Avviamento Motore Asincrono":
        st.subheader("Avviamento motore asincrono trifase")
        col1, col2 = st.columns(2)
        with col1:
            P_av = st.number_input("Potenza nominale [kW]:", value=11.0, min_value=0.1, key="av_P")
            V_av = st.number_input("Tensione [V]:", value=400.0, min_value=100.0, key="av_V")
            n_av = st.number_input("Velocità nominale [RPM]:", value=1450.0, min_value=1.0, key="av_n")
        with col2:
            cl_av = st.selectbox("Classe avviamento:", list(avv.CLASSI_AVVIAMENTO.keys()), key="av_cl")
            cphi_av = st.slider("cos_phi nominale:", 0.60, 1.00, 0.86, step=0.01, key="av_cphi")
            eta_av = st.slider("Rendimento η:", 0.80, 1.00, 0.93, step=0.01, key="av_eta")
        Z_rete = st.number_input("Impedenza di rete Z [mΩ]:", value=10.0, min_value=0.1, key="av_Z",
                                  help="Impedenza vista dal punto di allacciamento — tipicamente 5-20 mΩ")
        if st.button("Calcola Avviamento", key="av_btn"):
            try:
                info_cl = avv.CLASSI_AVVIAMENTO[cl_av]
                rc = avv.correnti_motore(P_av, V_av, cphi_av, eta_av, info_cl["Ia_In"])
                rm = avv.coppia_motore(P_av, n_av, info_cl["Ma_Mn"])
                rdv = avv.caduta_tensione_avviamento(rc["I_avviamento_A"], Z_rete, V_av)
                rmet = avv.metodi_avviamento(P_av, V_av, cphi_av, eta_av)
                st.session_state["_av_result"] = {
                    "P": P_av, "V": V_av, "cl_av": cl_av, "rc": rc, "rm": rm, "rdv": rdv, "rmet": rmet,
                }
            except (ValueError, ZeroDivisionError) as e:
                st.session_state["_av_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_av_result")
        if rr:
            rc, rm, rdv, rmet = rr["rc"], rr["rm"], rr["rdv"], rr["rmet"]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("I nominale", f"{rc['I_nominale_A']:.1f} A")
            c2.metric("I avviamento", f"{rc['I_avviamento_A']:.0f} A")
            c3.metric("M nominale", f"{rm['M_nominale_Nm']:.1f} N·m")
            c4.metric("M avviamento", f"{rm['M_avviamento_Nm']:.1f} N·m")
            st.info(f"Caduta di tensione spunto: {rdv['dV_V']:.1f} V = {rdv['dV_pct']:.1f}%  |  {rdv['giudizio']}")
            st.subheader("Confronto metodi di avviamento")
            rows = []
            for nome, val in rmet["metodi"].items():
                rows.append({"Metodo": nome, "I_avv [A]": f"{val['I_avviamento_A']:.0f}",
                             "× I_n": f"{val['fattore_corrente']:.1f}",
                             "Coppia": f"{val['fattore_coppia']:.2f} × M_n", "Note": val["note"]})
            st.table(rows)
            _export_csv_button(
                "Avviamento Motore Asincrono",
                {
                    "P [kW]": rr["P"], "V [V]": rr["V"], "Classe avviamento": rr["cl_av"],
                    "I nominale [A]": f"{rc['I_nominale_A']:.1f}", "I avviamento [A]": f"{rc['I_avviamento_A']:.0f}",
                    "Caduta tensione spunto [%]": f"{rdv['dV_pct']:.1f}",
                },
                key="av_export",
            )

    elif tipo == "Motore Asincrono — Dati di Targa":
        st.subheader("Grandezze elettromeccaniche da dati di targa")
        col1, col2, col3 = st.columns(3)
        with col1:
            P_ma   = st.number_input("Potenza nominale P_n [kW]:", value=11.0, min_value=0.1, key="ma_P")
            n_ma   = st.number_input("Velocita nominale n_n [RPM]:", value=1455.0, min_value=1.0, key="ma_n")
        with col2:
            V_ma   = st.number_input("Tensione di linea V_n [V]:", value=400.0, min_value=1.0, key="ma_V")
            cos_ma = st.number_input("cos phi nominale:", value=0.85, min_value=0.1, max_value=1.0, key="ma_cos")
        with col3:
            eta_ma  = st.number_input("Rendimento eta [%]:", value=91.0, min_value=1.0, max_value=99.9, key="ma_eta")
            poli_ma = st.selectbox("Numero poli:", [2, 4, 6, 8], index=1, key="ma_poli")
            lam_ma  = st.number_input("Sovraccaricabilita (T_max/T_n):", value=2.5, min_value=1.1, max_value=4.0, key="ma_lam")
            ksp_ma  = st.number_input("Rapporto spunto I_sp/I_n:", value=6.0, min_value=2.0, max_value=12.0, key="ma_ksp")
        if st.button("Calcola", key="ma_btn"):
            try:
                r = motore_asincrono.da_targa(P_ma, n_ma, V_ma, cos_ma, eta_ma, poli_ma, lambda_max=lam_ma, k_spunto=ksp_ma)
                st.session_state["_ma_result"] = {"P": P_ma, "n": n_ma, "V": V_ma, "lam": lam_ma, "res": r}
            except ValueError as e:
                st.session_state["_ma_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_ma_result")
        if rr:
            r = rr["res"]
            st.success(f"n_sync = {r['n_sync_rpm']:.0f} RPM  |  s_n = {r['s_n_pct']:.2f}%  |  T_n = {r['T_n_nm']:.2f} N·m")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Corrente nominale I_n", f"{r['I_n_A']:.2f} A")
                st.metric("Corrente di spunto I_sp", f"{r['I_sp_A']:.1f} A")
                st.metric("Potenza assorbita P_in", f"{r['P_in_kW']:.3f} kW")
            with col2:
                st.metric("Coppia massima T_max", f"{r['T_max_nm']:.2f} N·m")
                st.metric("Scorrimento critico s_cr", f"{r['s_cr_pct']:.2f}%")
                st.metric("Perdite totali", f"{r['perdite_kW']:.3f} kW")
            with st.expander("Potenze reattiva e apparente"):
                st.write(f"Q_n = {r['Q_n_kVAR']:.3f} kVAR  |  S_n = {r['S_n_kVA']:.3f} kVA")
            if _PLOTLY:
                with st.expander("Curva T-n (formula di Kloss)", expanded=True):
                    tn = motore_asincrono.caratteristica_tn(r["T_n_nm"], r["n_sync_rpm"], r["s_n"], rr["lam"])
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=tn["n_rpm"], y=tn["T_nm"], mode="lines",
                        line=dict(color="#2196F3", width=2.5), name="T-n (Kloss)",
                    ))
                    fig.add_trace(go.Scatter(
                        x=[rr["n"]], y=[r["T_n_nm"]], mode="markers",
                        marker=dict(color="#4CAF50", size=10, symbol="circle"),
                        name=f"Punto nominale ({rr['n']:.0f} RPM, {r['T_n_nm']:.1f} N·m)",
                    ))
                    fig.add_trace(go.Scatter(
                        x=[tn["n_cr_rpm"]], y=[tn["T_cr_nm"]], mode="markers",
                        marker=dict(color="#f44336", size=10, symbol="diamond"),
                        name=f"Coppia max ({tn['T_cr_nm']:.1f} N·m)",
                    ))
                    fig.update_layout(
                        xaxis_title="Velocità [RPM]", yaxis_title="Coppia [N·m]",
                        legend=dict(orientation="h", y=-0.25),
                        margin=dict(t=20, b=20), height=320,
                    )
                    st.plotly_chart(fig, use_container_width=True)
            _export_csv_button(
                "Motore Asincrono — Dati di Targa",
                {
                    "P [kW]": rr["P"], "n [RPM]": rr["n"], "V [V]": rr["V"],
                    "I_n [A]": f"{r['I_n_A']:.2f}", "T_n [N·m]": f"{r['T_n_nm']:.2f}", "T_max [N·m]": f"{r['T_max_nm']:.2f}",
                },
                key="ma_export",
            )

    elif tipo == "Motore Asincrono — Classi IE (Efficienza)":
        st.subheader("Confronto costo energetico annuo tra classi IE1 / IE2 / IE3 / IE4")
        col1, col2, col3 = st.columns(3)
        with col1:
            P_ie = st.number_input("Potenza nominale [kW]:", value=11.0, min_value=0.75, key="ie_P")
        with col2:
            ore_ie = st.number_input("Ore di funzionamento/anno:", value=8000.0, min_value=1.0, key="ie_ore")
        with col3:
            costo_ie = st.number_input("Costo energia [€/kWh]:", value=0.15, min_value=0.01, key="ie_costo")
        if st.button("Confronta classi IE", key="ie_btn"):
            try:
                r = motore_asincrono.confronto_classi_ie(P_ie, ore_ie, costo_ie)
                st.session_state["_ie_result"] = {"P": P_ie, "ore": ore_ie, "costo": costo_ie, "res": r}
            except (ValueError, KeyError) as e:
                st.session_state["_ie_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_ie_result")
        if rr:
            r = rr["res"]
            for cl, dati in r.items():
                txt = f"**{cl}** — eta = {dati['eta_pct']:.1f}%  |  P_in = {dati['P_in_kW']:.3f} kW  |  Costo annuo = €{dati['costo_euro']:,.0f}"
                if cl == "IE1":
                    st.warning(txt)
                elif cl == "IE2":
                    st.info(txt)
                elif cl == "IE3":
                    st.success(txt + f"  |  Risparmio vs IE1: **€{dati['risparmio_vs_IE1']:,.0f}/anno**")
                else:
                    st.success(txt + f"  |  Risparmio vs IE1: **€{dati['risparmio_vs_IE1']:,.0f}/anno**")
            st.caption("Valori di rendimento da IEC 60034-30-1:2014 (4 poli, 50 Hz).")
            _export_csv_button(
                "Motore Asincrono — Classi IE",
                {
                    "P [kW]": rr["P"], "Ore/anno": rr["ore"], "Costo energia [€/kWh]": rr["costo"],
                    **{f"Costo annuo {cl} [€]": f"{dati['costo_euro']:,.0f}" for cl, dati in r.items()},
                },
                key="ie_export",
            )


elif categoria == "🤖  PLC e Automazione":
    _card_open("plc", "🤖 PLC e Automazione", "IEC 61131-3")
    tool_plc = st.selectbox(
        "Seleziona Strumento:",
        [
            "Info CPU e Memoria RX3i",
            "Info Modulo Analogico",
            "Tipi Dati",
            "Scalatura Analogica (Raw -> Engineering)",
            "Scalatura Inversa (Engineering -> Raw / Setpoint)",
            "Esplosione Parola nei Bit",
            "Composizione WORD da Bit",
            "Calcolo Memoria RX3i",
        ],
        key="plc_tool",
    )
    _render_fav_toggle("🤖  PLC e Automazione", "plc_tool", tool_plc)

    if tool_plc == "Info CPU e Memoria RX3i":
        if hasattr(automazione, "lista_cpu_rx3i"):
            cpu_list = automazione.lista_cpu_rx3i()
        else:
            cpu_list = list(getattr(automazione, "_DB_CPU_RX3I", {}).keys())
        cpu_sel = st.selectbox("Seleziona modello CPU:", cpu_list, key="cpu_sel")
        info = automazione.info_cpu_rx3i(cpu_sel)
        if info:
            st.info(info["note"])
            st.write(f"RAM programma: {info['ram_programma_mb']} MB")
            st.write("Configurazione PME tipica (default nuovi progetti):")
            tipici = info["tipici_pme"]
            col1, col2 = st.columns(2)
            aree = list(tipici.items())
            for i, (area, val_cpu) in enumerate(aree):
                unita = "bit" if area in ("%I", "%Q", "%M", "%G") else "word (16-bit)"
                with (col1 if i < len(aree) // 2 else col2):
                    st.write(f"{area}: {val_cpu:,} {unita}")
            st.caption("Valori di default PME, non limiti hardware fissi.")

    elif tool_plc == "Info Modulo Analogico":
        moduli = automazione.lista_moduli()
        mod_sel = st.selectbox("Seleziona modulo:", moduli, key="mod_sel")
        info_m = automazione.info_modulo(mod_sel)
        if info_m:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Famiglia", info_m["famiglia"])
            with col2:
                st.metric("Canali", str(info_m["canali"]) if info_m["canali"] > 0 else "-")
            with col3:
                st.metric("Tipo", info_m["tipo"])
            st.write(f"Risoluzione: {info_m['resol']}")
            st.info(info_m["note_mod"])
            st.write("Configurazioni canale disponibili:")
            for nome_cfg, cfg in info_m["config"].items():
                nota = f" - {cfg['note']}" if cfg["note"] else ""
                st.write(f"- {nome_cfg}: raw {cfg['in_min']} -> {cfg['in_max']} [{cfg['unita']}]{nota}")

    elif tool_plc == "Tipi Dati":
        tipo_s = st.selectbox(
            "Scegli Tipo:",
            [
                "BOOL",
                "BYTE",
                "WORD",
                "DWORD",
                "INT (Integer)",
                "UINT (Unsigned INT)",
                "DINT (Double INT)",
                "UDINT (Unsigned DINT)",
                "REAL (Float)",
            ],
            key="td_tipo",
        )
        dim, cat_td, v_min, v_max = automazione.info_tipo_dato(tipo_s)
        st.info(f"Dimensione: {dim}")
        st.info(f"Categoria: {cat_td}")
        st.success(f"Range: [{v_min} -> {v_max}]")
        if tipo_s == "BOOL":
            st.caption("Su RX3i il BOOL e indirizzato singolarmente in %I, %Q e %M. In area %R i BOOL vengono packed.")
        if "REAL" in tipo_s:
            st.caption("Il tipo REAL occupa 2 registri %R consecutivi.")

    elif tool_plc == "Scalatura Analogica (Raw -> Engineering)":
        modo = st.radio("Seleziona modulo da:", ["Database moduli RX3i", "Inserimento manuale range"], key="sca_modo")

        if modo == "Database moduli RX3i":
            moduli_sca = automazione.lista_moduli()
            mod_sca = st.selectbox("Modulo:", moduli_sca, key="sca_mod")
            info_sca = automazione.info_modulo(mod_sca)
            cfg_list = list(info_sca["config"].keys()) if info_sca else []
            cfg_sel = st.selectbox("Configurazione canale:", cfg_list, key="sca_cfg")
            result_sca = automazione.get_range_canale(mod_sca, cfg_sel)
            if result_sca:
                in_min, in_max, unita_sca, nota_sca = result_sca
                suffix = f" - {nota_sca}" if nota_sca else ""
                st.caption(f"Range raw: {in_min} -> {in_max} [{unita_sca}]{suffix}")
            else:
                in_min, in_max = 0.0, 32000.0
        else:
            in_min = st.number_input("Limite raw minimo:", value=0.0, key="sca_man_min")
            in_max = st.number_input("Limite raw massimo:", value=32000.0, key="sca_man_max")

        clamp = st.checkbox("Satura il risultato ai limiti fisici (clamp)", value=False, key="sca_clamp")
        val_grezzo = st.number_input("Valore grezzo letto dal PLC:", value=float(in_min), key="sca_raw")
        out_min = st.number_input("Valore fisico a segnale minimo:", value=0.0, key="sca_omin")
        out_max = st.number_input("Valore fisico a fondo scala:", value=100.0, key="sca_omax")

        if st.button("Scala", key="sca_btn"):
            ris, stato = automazione.esegui_scalatura(val_grezzo, in_min, in_max, out_min, out_max, abilita_clamp=clamp)
            st.session_state["_sca_result"] = {
                "raw": val_grezzo, "in_min": in_min, "in_max": in_max,
                "out_min": out_min, "out_max": out_max, "ris": ris, "stato": stato,
            }

        rr = st.session_state.get("_sca_result")
        if rr:
            ris, stato = rr["ris"], rr["stato"]
            if stato == "ROTTURA_CAVO":
                st.error("Rottura cavo o segnale assente: raw sotto soglia minima.")
            elif stato == "FUORI_RANGE":
                st.warning(f"Valore fuori range - estrapolato: {ris:.4f}")
                pct = (rr["raw"] - rr["in_min"]) / (rr["in_max"] - rr["in_min"]) if rr["in_max"] != rr["in_min"] else 0
                st.progress(min(max(pct, 0.0), 1.0))
            else:
                st.success(f"Valore scalato: {ris:.4f}")
                pct = (ris - rr["out_min"]) / (rr["out_max"] - rr["out_min"]) if rr["out_max"] != rr["out_min"] else 0
                st.progress(min(max(pct, 0.0), 1.0))
                st.caption(f"{pct * 100.0:.1f}% del fondo scala")
            _export_csv_button(
                "Scalatura Analogica",
                {
                    "Valore raw": rr["raw"], "Range raw": f"{rr['in_min']} → {rr['in_max']}",
                    "Range fisico": f"{rr['out_min']} → {rr['out_max']}",
                    "Valore scalato": f"{ris:.4f}", "Stato": stato,
                },
                key="sca_export",
            )

    elif tool_plc == "Scalatura Inversa (Engineering -> Raw / Setpoint)":
        st.caption("Converte un setpoint fisico nel valore raw da scrivere nel PLC.")
        modo_inv = st.radio("Seleziona modulo da:", ["Database moduli RX3i", "Inserimento manuale range"], key="sci_modo")

        if modo_inv == "Database moduli RX3i":
            moduli_inv = automazione.lista_moduli()
            mod_inv = st.selectbox("Modulo:", moduli_inv, key="sci_mod")
            info_inv = automazione.info_modulo(mod_inv)
            cfg_inv = list(info_inv["config"].keys()) if info_inv else []
            cfg_inv_sel = st.selectbox("Configurazione canale:", cfg_inv, key="sci_cfg")
            result_inv = automazione.get_range_canale(mod_inv, cfg_inv_sel)
            if result_inv:
                in_min_inv, in_max_inv, _, _ = result_inv
                st.caption(f"Range raw: {in_min_inv} -> {in_max_inv}")
            else:
                in_min_inv, in_max_inv = 0.0, 32000.0
        else:
            in_min_inv = st.number_input("Limite raw minimo:", value=0.0, key="sci_man_min")
            in_max_inv = st.number_input("Limite raw massimo:", value=32000.0, key="sci_man_max")

        out_min_inv = st.number_input("Valore fisico a segnale minimo:", value=0.0, key="sci_omin")
        out_max_inv = st.number_input("Valore fisico a fondo scala:", value=100.0, key="sci_omax")
        val_eng = st.number_input("Setpoint fisico da convertire:", value=50.0, key="sci_eng")

        if st.button("Calcola Raw", key="sci_btn"):
            raw, stato_inv = automazione.esegui_scalatura_inversa(val_eng, in_min_inv, in_max_inv, out_min_inv, out_max_inv)
            st.session_state["_sci_result"] = {
                "eng": val_eng, "in_min": in_min_inv, "in_max": in_max_inv,
                "out_min": out_min_inv, "out_max": out_max_inv, "raw": raw, "stato": stato_inv,
            }

        rr = st.session_state.get("_sci_result")
        if rr:
            raw, stato_inv = rr["raw"], rr["stato"]
            if stato_inv == "FUORI_RANGE":
                st.warning(f"Setpoint fuori range - raw estrapolato: {raw:.1f}")
            else:
                st.success(f"Valore raw da scrivere nel PLC: {raw:.1f} (INT: {int(round(raw))})")
            _export_csv_button(
                "Scalatura Inversa",
                {
                    "Setpoint fisico": rr["eng"], "Range fisico": f"{rr['out_min']} → {rr['out_max']}",
                    "Range raw": f"{rr['in_min']} → {rr['in_max']}",
                    "Valore raw": f"{raw:.1f}", "Raw INT": int(round(raw)), "Stato": stato_inv,
                },
                key="sci_export",
            )

    elif tool_plc == "Esplosione Parola nei Bit":
        val_w = st.number_input("Valore numerico WORD (0-65535):", min_value=0, max_value=65535, value=0, key="esp_val")
        st.info(f"Dec: {val_w} | Hex: 16#{val_w:04X} | Bin: {val_w:016b}")
        bits = automazione.calcola_esplosione_bits(val_w)
        c1, c2 = st.columns(2)
        for idx, b_v in enumerate(bits):
            with (c1 if idx < 8 else c2):
                st.write(f"Bit {idx:02d} -> {b_v}")
        _export_csv_button(
            "Esplosione Parola nei Bit",
            {
                "WORD (Dec)": val_w, "Hex": f"16#{val_w:04X}", "Bin": f"{val_w:016b}",
                **{f"Bit {idx:02d}": b_v for idx, b_v in enumerate(bits)},
            },
            key="esp_export",
        )

    elif tool_plc == "Composizione WORD da Bit":
        st.caption("Imposta i singoli bit per comporre il valore WORD o Control Word.")
        bit_values = []
        c1, c2 = st.columns(2)
        for idx in range(16):
            with (c1 if idx < 8 else c2):
                b = st.checkbox(f"Bit {idx:02d}", value=False, key=f"cmp_bit_{idx}")
                bit_values.append(1 if b else 0)
        word = automazione.componi_word_da_bits(bit_values)
        st.success(f"Valore WORD: {word} (Dec) | 16#{word:04X} (Hex) | {word:016b} (Bin)")
        _export_csv_button(
            "Composizione WORD da Bit",
            {
                "WORD (Dec)": word, "Hex": f"16#{word:04X}", "Bin": f"{word:016b}",
                **{f"Bit {idx:02d}": v for idx, v in enumerate(bit_values)},
            },
            key="cmp_export",
        )

    elif tool_plc == "Calcolo Memoria RX3i":
        pref = st.selectbox("Area Memoria:", ["%R", "%M", "%I", "%Q", "%AI", "%AQ"], key="mem_pref")
        start = st.number_input("Indirizzo inizio:", min_value=1, value=1, key="mem_start")
        t_var = st.selectbox("Tipo variabile:", ["1 Bit (Digital I/O)", "16 Bit (WORD / INT)", "32 Bit (REAL / DINT)"], key="mem_tipo")
        qta = st.number_input("Quantita (Array Size):", min_value=1, value=1, key="mem_qta")
        if st.button("Calcola", key="mem_btn"):
            intervallo = automazione.calcola_limiti_memoria_rx3i(pref, start, qta, t_var)
            st.session_state["_mem_result"] = {
                "pref": pref, "start": start, "qta": qta, "t_var": t_var, "intervallo": intervallo,
            }

        rr = st.session_state.get("_mem_result")
        if rr:
            st.success(f"Intervallo occupato: {rr['intervallo']}")
            if rr["t_var"] == "1 Bit (Digital I/O)" and rr["pref"] == "%R":
                n_reg = math.ceil(int(rr["qta"]) / 16)
                st.caption(f"In area %R i BOOL sono packed: {int(rr['qta'])} bit occupano {n_reg} registro/i da 16 bit.")
            _export_csv_button(
                "Calcolo Memoria RX3i",
                {
                    "Area": rr["pref"], "Indirizzo inizio": rr["start"], "Quantità": rr["qta"],
                    "Tipo variabile": rr["t_var"], "Intervallo occupato": rr["intervallo"],
                },
                key="mem_export",
            )


elif categoria == "〜  Vibrazioni":
    _card_open("vib", "〜 Analisi Vibrazionale", "ISO 10816 / ISO 1940")
    tool_vib = st.selectbox(
        "Seleziona Strumento:",
        [
            "Conversione Grandezze Vibrazionali",
            "Classificazione ISO 10816 (Severita)",
            "Frequenza Naturale Massa-Molla",
            "Velocita Critica Albero",
            "Squilibrio Residuo ISO 1940",
        ],
        key="vib_tool",
    )
    _render_fav_toggle("〜  Vibrazioni", "vib_tool", tool_vib)

    # ------------------------------------------------------------------
    if tool_vib == "Conversione Grandezze Vibrazionali":
        st.subheader("Converti tra spostamento, velocita e accelerazione")
        st.caption("Valido per segnale sinusoidale puro a frequenza costante.")

        grandezze_disp = {
            "Spostamento pk-pk [mm]":       "spostamento_pkpk_mm",
            "Velocita RMS [mm/s]":          "velocita_rms_mms",
            "Accelerazione RMS [m/s²]":     "accelerazione_rms_ms2",
            "Accelerazione RMS [g]":        "accelerazione_rms_g",
        }
        g_label = st.selectbox("Grandezza di ingresso:", list(grandezze_disp.keys()), key="vib_gin")
        g_key   = grandezze_disp[g_label]
        val_vib = st.number_input("Valore:", value=1.0, min_value=0.0, format="%.6g", key="vib_val")
        freq_vib = st.number_input("Frequenza [Hz]:", value=50.0, min_value=0.01, format="%.4g", key="vib_freq")

        if st.button("Converti", key="vib_conv_btn"):
            try:
                r = vibrazioni.converti_grandezze_vibrazionali(g_key, val_vib, freq_vib)
                st.session_state["_vibconv_result"] = {"g_label": g_label, "val": val_vib, "freq": freq_vib, "res": r}
            except ValueError as e:
                st.session_state["_vibconv_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_vibconv_result")
        if rr:
            r = rr["res"]
            # r puo' provenire da una sessione già aperta prima che questi campi
            # aggiuntivi esistessero (Streamlit mantiene session_state tra un
            # rerun e l'altro anche quando il codice viene aggiornato): non si
            # accede mai con r['chiave'] a un campo aggiunto dopo la prima
            # versione di questa funzione, sempre con .get() e un fallback
            # ricalcolato dai campi originali (sempre presenti).
            freq_hz = r["frequenza_hz"]
            frequenza_cpm = r.get("frequenza_cpm", freq_hz * 60.0)
            spostamento_pkpk_mils = r.get("spostamento_pkpk_mils", r["spostamento_pkpk_mm"] / 0.0254)
            velocita_pk_ins = r.get("velocita_pk_ins", r["velocita_pk_mms"] / 25.4)
            velocita_rms_ins = r.get("velocita_rms_ins", r["velocita_rms_mms"] / 25.4)
            accelerazione_rms_fts2 = r.get("accelerazione_rms_fts2", r["accelerazione_rms_ms2"] / 0.3048)
            accelerazione_rms_ins2 = r.get("accelerazione_rms_ins2", r["accelerazione_rms_ms2"] / 0.0254)
            vdb_iso = r.get("vdb_iso", vibrazioni.livello_db(r["velocita_rms_mms"] / 1000.0, 1e-9))
            vdb_us = r.get("vdb_us", vibrazioni.livello_db(r["velocita_rms_mms"] / 1000.0, 1e-8))
            adb_iso = r.get("adb_iso", vibrazioni.livello_db(r["accelerazione_rms_ms2"], 1e-6))
            adb_us = r.get("adb_us", vibrazioni.livello_db(r["accelerazione_rms_g"], 1e-6))

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Spostamento pk-pk",   f"{r['spostamento_pkpk_mm']:.4g} mm")
                st.metric("Spostamento pk-pk",   f"{spostamento_pkpk_mils:.4g} mils")
                st.metric("Velocita peak",        f"{r['velocita_pk_mms']:.4g} mm/s")
                st.metric("Velocita peak",        f"{velocita_pk_ins:.4g} in/s")
                st.metric("Velocita RMS",         f"{r['velocita_rms_mms']:.4g} mm/s")
                st.metric("Velocita RMS",         f"{velocita_rms_ins:.4g} in/s")
            with col2:
                st.metric("Accelerazione peak",   f"{r['accelerazione_pk_ms2']:.4g} m/s²")
                st.metric("Accelerazione RMS",    f"{r['accelerazione_rms_ms2']:.4g} m/s²")
                st.metric("Accelerazione RMS",    f"{accelerazione_rms_fts2:.4g} ft/s²")
                st.metric("Accelerazione RMS",    f"{accelerazione_rms_ins2:.4g} in/s²")
                st.metric("Accelerazione peak",   f"{r['accelerazione_pk_g']:.4g} g")
                st.metric("Accelerazione RMS",    f"{r['accelerazione_rms_g']:.4g} g")
            with col3:
                st.metric("VdB (rif. ISO 1nm/s)",     f"{vdb_iso:.4g}" if vdb_iso is not None else "—")
                st.metric("VdB (rif. US 1E-8 m/s)",   f"{vdb_us:.4g}" if vdb_us is not None else "—")
                st.metric("AdB (rif. ISO 1µm/s²)",    f"{adb_iso:.4g}" if adb_iso is not None else "—")
                st.metric("AdB (rif. US 1 micro-g)",  f"{adb_us:.4g}" if adb_us is not None else "—")
            st.caption(
                f"ω = {r['omega_rad_s']:.4f} rad/s · {freq_hz:.4g} Hz = {frequenza_cpm:.4g} CPM. "
                "Livelli in dB secondo i riferimenti standard ISO 1683 (1 µm/s² per l'accelerazione, "
                "1 nm/s per la velocità) e le convenzioni US storiche del settore (1 micro-g, 1E-8 m/s)."
            )

            _export_csv_button(
                "Conversione Grandezze Vibrazionali",
                {
                    "Grandezza ingresso": rr["g_label"], "Valore": rr["val"], "Frequenza [Hz]": rr["freq"],
                    "Frequenza [CPM]": f"{frequenza_cpm:.4g}",
                    "Spostamento pk-pk [mm]": f"{r['spostamento_pkpk_mm']:.4g}",
                    "Spostamento pk-pk [mils]": f"{spostamento_pkpk_mils:.4g}",
                    "Velocita RMS [mm/s]": f"{r['velocita_rms_mms']:.4g}",
                    "Velocita RMS [in/s]": f"{velocita_rms_ins:.4g}",
                    "Accelerazione RMS [m/s²]": f"{r['accelerazione_rms_ms2']:.4g}",
                    "Accelerazione RMS [g]": f"{r['accelerazione_rms_g']:.4g}",
                    "VdB ISO": f"{vdb_iso:.4g}" if vdb_iso is not None else "",
                    "AdB ISO": f"{adb_iso:.4g}" if adb_iso is not None else "",
                },
                key="vibconv_export",
            )

    # ------------------------------------------------------------------
    elif tool_vib == "Classificazione ISO 10816 (Severita)":
        st.subheader("Severita vibrazionale secondo ISO 10816-1")
        classi = vibrazioni.lista_classi_iso10816()
        classe_sel = st.selectbox("Classe macchina:", classi, key="iso_classe")
        v_rms = st.number_input("Velocita RMS misurata [mm/s]:", value=1.0, min_value=0.0, format="%.4g", key="iso_vrms")

        if st.button("Classifica", key="iso_btn"):
            try:
                zona, colore, descr, lim = vibrazioni.classifica_iso10816(v_rms, classe_sel)
                st.session_state["_iso10816_result"] = {
                    "classe": classe_sel, "v_rms": v_rms, "zona": zona, "colore": colore, "descr": descr, "lim": lim,
                }
            except ValueError as e:
                st.session_state["_iso10816_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_iso10816_result")
        if rr:
            zona, colore, descr, lim, v_rms = rr["zona"], rr["colore"], rr["descr"], rr["lim"], rr["v_rms"]
            if zona == "A":
                st.success(f"Zona {zona} ({colore}) — {descr}")
            elif zona == "B":
                st.info(f"Zona {zona} ({colore}) — {descr}")
            elif zona == "C":
                st.warning(f"Zona {zona} ({colore}) — {descr}")
            else:
                st.error(f"Zona {zona} ({colore}) — {descr}")

            with st.expander("Limiti di zona per la classe selezionata"):
                st.write(f"Zona A: ≤ {lim['A']} mm/s RMS")
                st.write(f"Zona B: ≤ {lim['B']} mm/s RMS")
                st.write(f"Zona C: ≤ {lim['C']} mm/s RMS")
                st.write(f"Zona D: > {lim['C']} mm/s RMS")
            if _PLOTLY:
                v_max_plot = max(v_rms * 1.5, lim["C"] * 1.3, 1.0)
                fig_vib = go.Figure()
                fig_vib.add_hrect(y0=0,        y1=lim["A"], fillcolor="#4CAF50", opacity=0.15, line_width=0, annotation_text="Zona A", annotation_position="right")
                fig_vib.add_hrect(y0=lim["A"], y1=lim["B"], fillcolor="#2196F3", opacity=0.15, line_width=0, annotation_text="Zona B", annotation_position="right")
                fig_vib.add_hrect(y0=lim["B"], y1=lim["C"], fillcolor="#FF9800", opacity=0.15, line_width=0, annotation_text="Zona C", annotation_position="right")
                fig_vib.add_hrect(y0=lim["C"], y1=v_max_plot, fillcolor="#f44336", opacity=0.15, line_width=0, annotation_text="Zona D", annotation_position="right")
                fig_vib.add_hline(y=v_rms, line=dict(color="#222", width=2, dash="dot"),
                                  annotation_text=f"Misurato: {v_rms:.3f} mm/s", annotation_position="top left")
                fig_vib.update_layout(
                    yaxis=dict(title="Velocità vibrazionale RMS [mm/s]", range=[0, v_max_plot]),
                    xaxis=dict(visible=False),
                    margin=dict(t=20, b=10, r=80), height=260,
                    showlegend=False,
                )
                st.plotly_chart(fig_vib, use_container_width=True)
            _export_csv_button(
                "Classificazione ISO 10816",
                {
                    "Classe macchina": rr["classe"], "Velocita RMS [mm/s]": v_rms,
                    "Zona": zona, "Descrizione": descr,
                    "Limite A [mm/s]": lim["A"], "Limite B [mm/s]": lim["B"], "Limite C [mm/s]": lim["C"],
                },
                key="iso10816_export",
            )

    # ------------------------------------------------------------------
    elif tool_vib == "Frequenza Naturale Massa-Molla":
        st.subheader("Sistema massa-molla: frequenza naturale e smorzamento")
        col1, col2 = st.columns(2)
        with col1:
            k_val = st.number_input("Rigidezza k [N/m]:", value=10000.0, min_value=0.01, format="%.6g", key="fn_k")
            m_val = st.number_input("Massa m [kg]:", value=10.0, min_value=0.001, format="%.6g", key="fn_m")
        with col2:
            usa_smorzamento = st.checkbox("Includi smorzamento", value=False, key="fn_smorzato")
            zeta_val = 0.0
            if usa_smorzamento:
                zeta_val = st.number_input("Rapporto di smorzamento ζ [-]:", value=0.1, min_value=0.0, max_value=5.0, format="%.4f", key="fn_zeta")

        if st.button("Calcola", key="fn_btn"):
            try:
                r = vibrazioni.calcola_frequenza_naturale(k_val, m_val, zeta_val)
                st.session_state["_fn_result"] = {"k": k_val, "m": m_val, "zeta": zeta_val, "smorz": usa_smorzamento, "res": r}
            except ValueError as e:
                st.session_state["_fn_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_fn_result")
        if rr:
            r = rr["res"]
            st.success(f"Frequenza naturale fn: {r['fn_hz']:.4f} Hz  |  ωn: {r['omega_n_rad_s']:.4f} rad/s")
            st.info(f"Periodo T: {r['T_s']:.4f} s  |  Regime: {r['regime']}")
            if rr["smorz"] and 0 < rr["zeta"] < 1.0:
                st.info(f"Frequenza smorzata fd: {r['fd_hz']:.4f} Hz  |  ωd: {r['omega_d_rad_s']:.4f} rad/s")
                if r['Q'] != float('inf'):
                    st.info(f"Fattore Q (amplificazione a risonanza): {r['Q']:.2f}")
            with st.expander("Dettagli smorzatore"):
                st.write(f"Smorzamento critico cc: {r['c_critico_ns_m']:.2f} N·s/m")
                st.write(f"Smorzamento reale c: {r['c_reale_ns_m']:.2f} N·s/m")
                st.write(f"ζ = {r['zeta']:.4f}")
            _export_csv_button(
                "Frequenza Naturale Massa-Molla",
                {
                    "Rigidezza k [N/m]": rr["k"], "Massa m [kg]": rr["m"], "ζ": rr["zeta"],
                    "Frequenza naturale fn [Hz]": f"{r['fn_hz']:.4f}", "Periodo T [s]": f"{r['T_s']:.4f}",
                    "Regime": r["regime"],
                },
                key="fn_export",
            )

    # ------------------------------------------------------------------
    elif tool_vib == "Velocita Critica Albero":
        st.subheader("Velocita critica di un albero rotante (metodo freccia statica)")
        st.caption("Formula di Rankine: Nc = (30/π) · √(g / δ). Inserire la freccia statica misurata o calcolata dall'analisi strutturale.")
        delta = st.number_input("Freccia statica δ [mm]:", value=0.5, min_value=0.001, format="%.6g", key="vc_delta")

        if st.button("Calcola", key="vc_btn"):
            try:
                r = vibrazioni.calcola_velocita_critica(delta)
                st.session_state["_vc_result"] = {"delta": delta, "res": r}
            except ValueError as e:
                st.session_state["_vc_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_vc_result")
        if rr:
            r = rr["res"]
            st.success(f"Velocita critica Nc: {r['Nc_rpm']:.1f} RPM  ({r['fn_critica_hz']:.3f} Hz)")
            st.warning(
                f"Zona proibita (±20%): {r['zona_proibita_bassa']:.0f} ÷ {r['zona_proibita_alta']:.0f} RPM — "
                "evitare esercizio prolungato in questo intervallo."
            )
            with st.expander("Dettagli"):
                st.write(f"ωc = {r['omega_critica_rad_s']:.4f} rad/s")
                st.write("Il metodo della freccia statica (Rankine) è conservativo: fornisce una stima della prima velocità critica flessionale. Per alberi con più masse o geometria complessa usare FEM o metodo di Dunkerley.")
            _export_csv_button(
                "Velocita Critica Albero",
                {
                    "Freccia statica δ [mm]": rr["delta"], "Velocita critica Nc [RPM]": f"{r['Nc_rpm']:.1f}",
                    "Frequenza critica [Hz]": f"{r['fn_critica_hz']:.3f}",
                    "Zona proibita [RPM]": f"{r['zona_proibita_bassa']:.0f} ÷ {r['zona_proibita_alta']:.0f}",
                },
                key="vc_export",
            )

    # ------------------------------------------------------------------
    elif tool_vib == "Squilibrio Residuo ISO 1940":
        st.subheader("Squilibrio residuo ammissibile — ISO 1940-1")
        gradi = vibrazioni.lista_gradi_iso1940()
        grado_sel = st.selectbox("Grado di bilanciamento:", gradi, key="iso40_grado")
        grado_val = vibrazioni.valore_grado_iso1940(grado_sel)

        col1, col2 = st.columns(2)
        with col1:
            massa_rot = st.number_input("Massa rotore [kg]:", value=10.0, min_value=0.001, format="%.4g", key="iso40_m")
            rpm_rot   = st.number_input("Velocita operativa [RPM]:", value=1500.0, min_value=1.0, format="%.4g", key="iso40_rpm")
        with col2:
            raggio_corr = st.number_input("Raggio piano di correzione [mm]:", value=100.0, min_value=0.1, format="%.4g", key="iso40_r")

        if st.button("Calcola", key="iso40_btn"):
            try:
                r = vibrazioni.calcola_squilibrio_iso1940(massa_rot, raggio_corr, rpm_rot, grado_val)
                st.session_state["_iso40_result"] = {
                    "grado": grado_sel, "grado_val": grado_val, "massa": massa_rot, "rpm": rpm_rot, "raggio": raggio_corr, "res": r,
                }
            except ValueError as e:
                st.session_state["_iso40_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_iso40_result")
        if rr:
            r = rr["res"]
            raggio_corr = rr["raggio"]
            st.success(f"Squilibrio massimo ammissibile: {r['U_max_gmm']:.2f} g·mm  ({r['U_max_kgmm']:.4f} kg·mm)")
            st.info(f"Eccentricita massima e_max: {r['e_max_mm']:.4f} mm")
            st.info(f"Massa di correzione max al raggio {raggio_corr:.0f} mm: {r['massa_corr_max_g']:.3f} g")
            with st.expander("Come usare il risultato"):
                st.write("1. Misurare lo squilibrio effettivo con la bilanciatrice (in g·mm).")
                st.write(f"2. Se squilibrio misurato ≤ {r['U_max_gmm']:.2f} g·mm → conforme al grado G {rr['grado_val']}.")
                st.write(f"3. Altrimenti aggiungere/rimuovere masse al piano di correzione (raggio {raggio_corr:.0f} mm) fino a rientrare nel limite.")
            _export_csv_button(
                "Squilibrio Residuo ISO 1940",
                {
                    "Grado bilanciamento": rr["grado"], "Massa rotore [kg]": rr["massa"],
                    "Velocita [RPM]": rr["rpm"], "Raggio correzione [mm]": raggio_corr,
                    "Squilibrio max [g·mm]": f"{r['U_max_gmm']:.2f}", "Eccentricita max [mm]": f"{r['e_max_mm']:.4f}",
                    "Massa correzione max [g]": f"{r['massa_corr_max_g']:.3f}",
                },
                key="iso40_export",
            )


elif categoria == "🔩  Meccanica":
    _card_open("mec", "🔩 Meccanica", "ISO 898-1 / VDI 2230")
    tool_mec = st.selectbox(
        "Seleziona Strumento:",
        [
            "Trasmissione Semplice (ingranaggi / cinghia / catena)",
            "Riduttore a Piu Stadi",
            "Geometria Cinghia",
            "Potenza-Coppia-Velocita",
            "Punto di Lavoro Pompa",
            "Potenza Pompa",
            "NPSH Disponibile",
            "Numero Specifico di Giri (ns)",
            "Proprieta Sezione",
            "Calcolo Trave",
            "Verifica a Flessione",
            "Trazione / Compressione",
            "Perdite di Carico Concentrate",
            "Perdite di Carico Distribuite (Darcy-Weisbach)",
            "Bulloneria — Serraggio",
            "Bulloneria — Verifica",
            "Bulloneria — Flangia",
            "Nastri Trasportatori",
            "Cuscinetti — Durata L10 (ISO 281)",
            "Molle Meccaniche",
            "Ruote Dentate — Verifica Lewis",
            "Alberi — Torsione e Flessione",
            "Saldature a Cordone d'Angolo",
            "Tubazione in Pressione (EN 13480)",
        ],
        key="mec_tool",
    )
    _render_fav_toggle("🔩  Meccanica", "mec_tool", tool_mec)

    # ------------------------------------------------------------------
    if tool_mec == "Trasmissione Semplice (ingranaggi / cinghia / catena)":
        st.subheader("Singolo stadio di trasmissione")
        col1, col2 = st.columns(2)
        with col1:
            n1_tr = st.number_input("Velocita ingresso n1 [RPM]:", value=1450.0, min_value=0.1, key="tr_n1")
            T1_tr = st.number_input("Coppia ingresso T1 [N·m]:", value=10.0, min_value=0.0, key="tr_t1")
        with col2:
            i_tr  = st.number_input("Rapporto di trasmissione i (n1/n2):", value=3.0, min_value=0.01, key="tr_i")
            eta_tr = st.slider("Rendimento eta:", 0.80, 1.00, 0.97, step=0.01, key="tr_eta")
        if st.button("Calcola", key="tr_btn"):
            try:
                r = trasmissioni.calcola_trasmissione(n1_tr, T1_tr, i_tr, eta_tr)
                st.session_state["_mectr_result"] = {"n1": n1_tr, "T1": T1_tr, "i": i_tr, "eta": eta_tr, "res": r}
            except ValueError as e:
                st.session_state["_mectr_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_mectr_result")
        if rr:
            r = rr["res"]
            st.success(f"Velocita uscita: {r['n2_rpm']:.2f} RPM  |  Coppia uscita: {r['T2_nm']:.3f} N·m")
            st.info(f"P ingresso: {r['P_in_kW']:.4f} kW  |  P uscita: {r['P_out_kW']:.4f} kW  |  Perdita: {r['perdita_kW']:.4f} kW")
            _export_csv_button(
                "Trasmissione Semplice",
                {
                    "n1 [RPM]": rr["n1"], "T1 [N·m]": rr["T1"], "Rapporto i": rr["i"], "Rendimento": rr["eta"],
                    "n2 [RPM]": f"{r['n2_rpm']:.2f}", "T2 [N·m]": f"{r['T2_nm']:.3f}", "P uscita [kW]": f"{r['P_out_kW']:.4f}",
                },
                key="mectr_export",
            )

    elif tool_mec == "Riduttore a Piu Stadi":
        st.subheader("Riduttore multistadio in cascata")
        n_stadi_rid = st.number_input("Numero di stadi:", min_value=1, max_value=5, value=2, key="rid_ns")
        n_in_rid = st.number_input("Velocita ingresso [RPM]:", value=1450.0, min_value=0.1, key="rid_n")
        T_in_rid = st.number_input("Coppia ingresso [N·m]:", value=10.0, min_value=0.0, key="rid_t")
        stadi_rid = []
        for k in range(int(n_stadi_rid)):
            c1, c2 = st.columns(2)
            with c1:
                i_s = st.number_input(f"Rapporto stadio {k+1}:", value=3.0, min_value=0.01, key=f"rid_i_{k}")
            with c2:
                e_s = st.number_input(f"Rendimento stadio {k+1}:", value=0.97, min_value=0.5, max_value=1.0, key=f"rid_e_{k}")
            stadi_rid.append({"i": i_s, "eta": e_s})
        if st.button("Calcola", key="rid_btn"):
            try:
                r = trasmissioni.calcola_riduttore_multistadio(n_in_rid, T_in_rid, stadi_rid)
                st.session_state["_rid_result"] = {"n_in": n_in_rid, "T_in": T_in_rid, "res": r}
            except ValueError as e:
                st.session_state["_rid_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_rid_result")
        if rr:
            r = rr["res"]
            st.success(f"i_tot = {r['i_tot']:.3f}  |  eta_tot = {r['eta_tot']:.4f}")
            st.info(f"Uscita: {r['n_out_rpm']:.2f} RPM  |  {r['T_out_nm']:.3f} N·m  |  {r['P_out_kW']:.4f} kW")
            with st.expander("Dettaglio per stadio"):
                for s in r["stadi"]:
                    st.write(f"Stadio {s['stadio']}: {s['n_in_rpm']:.1f} → {s['n_out_rpm']:.1f} RPM  |  T_out = {s['T_out_nm']:.2f} N·m  |  i={s['i']}  eta={s['eta']}")
            _export_csv_button(
                "Riduttore a Più Stadi",
                {
                    "n ingresso [RPM]": rr["n_in"], "T ingresso [N·m]": rr["T_in"],
                    "i_tot": f"{r['i_tot']:.3f}", "eta_tot": f"{r['eta_tot']:.4f}",
                    "n uscita [RPM]": f"{r['n_out_rpm']:.2f}", "T uscita [N·m]": f"{r['T_out_nm']:.3f}", "P uscita [kW]": f"{r['P_out_kW']:.4f}",
                },
                key="rid_export",
            )

    elif tool_mec == "Geometria Cinghia":
        st.subheader("Trasmissione a cinghia — geometria")
        col1, col2, col3 = st.columns(3)
        with col1:
            d1_c = st.number_input("Diametro puleggia motrice d1 [mm]:", value=100.0, min_value=1.0, key="cin_d1")
        with col2:
            d2_c = st.number_input("Diametro puleggia condotta d2 [mm]:", value=200.0, min_value=1.0, key="cin_d2")
        with col3:
            C_c  = st.number_input("Interasse C [mm]:", value=400.0, min_value=1.0, key="cin_c")
        if st.button("Calcola", key="cin_btn"):
            try:
                r = trasmissioni.calcola_geometria_cinghia(d1_c, d2_c, C_c)
                st.session_state["_cin_result"] = {"d1": d1_c, "d2": d2_c, "C": C_c, "res": r}
            except ValueError as e:
                st.session_state["_cin_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_cin_result")
        if rr:
            r = rr["res"]
            st.success(f"Rapporto i = {r['i']:.3f}  |  Lunghezza cinghia: {r['L_cinghia_mm']:.1f} mm")
            st.info(f"Angolo avvolgimento puleggia piccola: {r['alpha_piccola_deg']:.1f}°  (min. consigliato: 120°)")
            if r["alpha_piccola_deg"] < 120:
                st.warning("Angolo di avvolgimento < 120°: rischio slittamento. Aumentare l'interasse o usare un tenditore.")
            _export_csv_button(
                "Geometria Cinghia",
                {
                    "d1 [mm]": rr["d1"], "d2 [mm]": rr["d2"], "Interasse C [mm]": rr["C"],
                    "Rapporto i": f"{r['i']:.3f}", "Lunghezza cinghia [mm]": f"{r['L_cinghia_mm']:.1f}",
                    "Angolo avvolgimento [°]": f"{r['alpha_piccola_deg']:.1f}",
                },
                key="cin_export",
            )

    elif tool_mec == "Potenza-Coppia-Velocita":
        st.subheader("Calcola la terza grandezza tra P, T, n")
        modo_ptc = st.radio("Fornisco:", ["P [kW] e T [N·m] → calcola n", "P [kW] e n [RPM] → calcola T", "T [N·m] e n [RPM] → calcola P"], key="ptc_modo")
        mapping = {"P [kW] e T [N·m] → calcola n": "P_T", "P [kW] e n [RPM] → calcola T": "P_n", "T [N·m] e n [RPM] → calcola P": "T_n"}
        gran = mapping[modo_ptc]
        etichette = {"P_T": ("P [kW]", "T [N·m]"), "P_n": ("P [kW]", "n [RPM]"), "T_n": ("T [N·m]", "n [RPM]")}
        l1, l2 = etichette[gran]
        v1 = st.number_input(f"{l1}:", value=5.5, min_value=0.001, key="ptc_v1")
        v2 = st.number_input(f"{l2}:", value=1450.0, min_value=0.001, key="ptc_v2")
        if st.button("Calcola", key="ptc_btn"):
            try:
                r = trasmissioni.converti_ptc(gran, v1, v2)
                st.session_state["_ptc_result"] = {"modo": modo_ptc, "v1": v1, "v2": v2, "res": r}
            except ValueError as e:
                st.session_state["_ptc_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_ptc_result")
        if rr:
            r = rr["res"]
            st.success(f"P = {r['P_kW']:.4f} kW  |  T = {r['T_nm']:.4f} N·m  |  n = {r['n_rpm']:.2f} RPM")
            st.caption(f"ω = {r['omega_rad_s']:.4f} rad/s")
            _export_csv_button(
                "Potenza-Coppia-Velocità",
                {
                    "Modalità": rr["modo"], "P [kW]": f"{r['P_kW']:.4f}", "T [N·m]": f"{r['T_nm']:.4f}", "n [RPM]": f"{r['n_rpm']:.2f}",
                },
                key="ptc_export",
            )

    elif tool_mec == "Punto di Lavoro Pompa":
        st.subheader("Intersezione curva pompa / curva impianto")
        st.caption("La curva pompa è approssimata come parabola: H_p = H0 - k·Q²")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Curva pompa**")
            H0_p   = st.number_input("Shutoff head H0 [m] (a Q=0):", value=30.0, min_value=0.1, key="pp_H0")
            Qnom_p = st.number_input("Portata nominale Q_nom [m³/h]:", value=20.0, min_value=0.1, key="pp_Qn")
            Hnom_p = st.number_input("Prevalenza nominale H_nom [m]:", value=22.0, min_value=0.1, key="pp_Hn")
        with col2:
            st.markdown("**Curva impianto**")
            Hst_p  = st.number_input("Prevalenza statica H_st [m]:", value=10.0, min_value=0.0, key="pp_Hst")
            Qimp_p = st.number_input("Portata riferimento Q_imp [m³/h]:", value=20.0, min_value=0.1, key="pp_Qi")
            Himp_p = st.number_input("Prevalenza riferimento H_imp [m]:", value=25.0, min_value=0.1, key="pp_Hi")
        if st.button("Calcola punto di lavoro", key="pp_btn"):
            try:
                r = pompe.calcola_punto_lavoro(H0_p, Qnom_p, Hnom_p, Hst_p, Qimp_p, Himp_p)
                st.session_state["_pp_result"] = {
                    "H0": H0_p, "Qnom": Qnom_p, "Hnom": Hnom_p, "Hst": Hst_p, "Qimp": Qimp_p, "Himp": Himp_p, "res": r,
                }
            except ValueError as e:
                st.session_state["_pp_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_pp_result")
        if rr:
            try:
                r = rr["res"]
                H0_p, Qnom_p, Hnom_p = rr["H0"], rr["Qnom"], rr["Hnom"]
                Hst_p, Qimp_p, Himp_p = rr["Hst"], rr["Qimp"], rr["Himp"]
                st.success(f"Punto di lavoro: Q* = {r['Q_star_m3h']:.2f} m³/h  |  H* = {r['H_star_m']:.2f} m")
                st.info(f"Portata massima pompa (H=0): {r['Q_max_m3h']:.2f} m³/h")
                if _PLOTLY:
                    import numpy as _np
                    _k_p = (H0_p - Hnom_p) / Qnom_p**2
                    _k_i = (Himp_p - Hst_p) / Qimp_p**2
                    _Q_max = r["Q_max_m3h"]
                    _Q_arr = [i * _Q_max / 80 for i in range(81)]
                    _H_pump = [H0_p - _k_p * q**2 for q in _Q_arr]
                    _H_syst = [Hst_p + _k_i * q**2 for q in _Q_arr]
                    fig_p = go.Figure()
                    fig_p.add_trace(go.Scatter(x=_Q_arr, y=_H_pump, mode="lines",
                        line=dict(color="#2196F3", width=2.5), name="Curva pompa"))
                    fig_p.add_trace(go.Scatter(x=_Q_arr, y=_H_syst, mode="lines",
                        line=dict(color="#FF9800", width=2.5, dash="dash"), name="Curva impianto"))
                    fig_p.add_trace(go.Scatter(
                        x=[r["Q_star_m3h"]], y=[r["H_star_m"]], mode="markers",
                        marker=dict(color="#4CAF50", size=12, symbol="star"),
                        name=f"Punto di lavoro Q*={r['Q_star_m3h']:.2f} m³/h"))
                    fig_p.update_layout(
                        xaxis_title="Portata [m³/h]", yaxis_title="Prevalenza [m]",
                        legend=dict(orientation="h", y=-0.25),
                        margin=dict(t=20, b=20), height=300,
                    )
                    st.plotly_chart(fig_p, use_container_width=True)
                _export_csv_button(
                    "Punto di Lavoro Pompa",
                    {
                        "Shutoff head H0 [m]": rr["H0"], "Prevalenza statica [m]": rr["Hst"],
                        "Q* [m³/h]": f"{r['Q_star_m3h']:.2f}", "H* [m]": f"{r['H_star_m']:.2f}",
                        "Q max [m³/h]": f"{r['Q_max_m3h']:.2f}",
                    },
                    key="pp_export",
                )
            except ValueError as e:
                st.error(str(e))

    elif tool_mec == "Potenza Pompa":
        col1, col2 = st.columns(2)
        with col1:
            Q_pw = st.number_input("Portata Q [m³/h]:", value=20.0, min_value=0.01, key="pw_q")
            H_pw = st.number_input("Prevalenza H [m]:", value=25.0, min_value=0.01, key="pw_h")
        with col2:
            eta_pw  = st.number_input("Rendimento pompa:", value=0.75, min_value=0.1, max_value=1.0, key="pw_eta")
            rho_pw  = st.number_input("Densita fluido [kg/m³]:", value=1000.0, min_value=1.0, key="pw_rho")
        if st.button("Calcola", key="pw_btn"):
            try:
                r = pompe.calcola_potenza_pompa(Q_pw, H_pw, eta_pw, rho_pw)
                st.session_state["_pw_result"] = {"Q": Q_pw, "H": H_pw, "eta": eta_pw, "rho": rho_pw, "res": r}
            except ValueError as e:
                st.session_state["_pw_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_pw_result")
        if rr:
            r = rr["res"]
            st.success(f"P idraulica: {r['P_id_kW']:.3f} kW  |  P assorbita: {r['P_ass_kW']:.3f} kW")
            st.info(f"Perdite meccaniche: {r['perdita_kW']:.3f} kW")
            _export_csv_button(
                "Potenza Pompa",
                {
                    "Portata [m³/h]": rr["Q"], "Prevalenza [m]": rr["H"], "Rendimento": rr["eta"], "Densità [kg/m³]": rr["rho"],
                    "P idraulica [kW]": f"{r['P_id_kW']:.3f}", "P assorbita [kW]": f"{r['P_ass_kW']:.3f}",
                },
                key="pw_export",
            )

    elif tool_mec == "NPSH Disponibile":
        st.subheader("Net Positive Suction Head disponibile")
        col1, col2 = st.columns(2)
        with col1:
            P_asp_n  = st.number_input("Pressione aspirazione P_asp [bar a]:", value=1.013, min_value=0.01, format="%.4f", key="npsh_pasp")
            P_vap_n  = st.number_input("Pressione vapore P_vap [bar a]:", value=0.023, min_value=0.001, format="%.4f", key="npsh_pvap")
        with col2:
            H_asp_n  = st.number_input("Altezza geometrica aspirazione [m]:", value=3.0, key="npsh_hasp")
            v_asp_n  = st.number_input("Velocita condotto aspirazione [m/s]:", value=1.5, min_value=0.0, key="npsh_v")
            perd_n   = st.number_input("Perdite di carico aspirazione [m]:", value=0.5, min_value=0.0, key="npsh_perd")
        if st.button("Calcola NPSH_d", key="npsh_btn"):
            try:
                r = pompe.calcola_npsh_disponibile(P_asp_n, P_vap_n, H_asp_n, v_asp_n, perd_n)
                st.session_state["_npsh_result"] = {"P_asp": P_asp_n, "P_vap": P_vap_n, "H_asp": H_asp_n, "res": r}
            except ValueError as e:
                st.session_state["_npsh_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_npsh_result")
        if rr:
            r = rr["res"]
            if r["NPSH_d_m"] > 0:
                st.success(f"NPSH disponibile: {r['NPSH_d_m']:.3f} m")
            else:
                st.error(f"NPSH disponibile: {r['NPSH_d_m']:.3f} m — CAVITAZIONE CERTA")
            st.caption(r["avvertimento"])
            with st.expander("Dettagli"):
                st.write(f"Termine pressione: {r['termine_pressione_m']:.3f} m")
                st.write(f"Termine velocita: {r['termine_velocita_m']:.4f} m")
            _export_csv_button(
                "NPSH Disponibile",
                {
                    "P aspirazione [bar a]": rr["P_asp"], "P vapore [bar a]": rr["P_vap"], "H aspirazione [m]": rr["H_asp"],
                    "NPSH disponibile [m]": f"{r['NPSH_d_m']:.3f}",
                },
                key="npsh_export",
            )

    elif tool_mec == "Numero Specifico di Giri (ns)":
        col1, col2, col3 = st.columns(3)
        with col1:
            n_ns = st.number_input("Velocita [RPM]:", value=1450.0, min_value=1.0, key="ns_n")
        with col2:
            Q_ns = st.number_input("Portata [m³/s]:", value=0.005, min_value=1e-6, format="%.6f", key="ns_q")
        with col3:
            H_ns = st.number_input("Prevalenza [m]:", value=25.0, min_value=0.1, key="ns_h")
        if st.button("Calcola ns", key="ns_btn"):
            try:
                r = pompe.calcola_ns(n_ns, Q_ns, H_ns)
                st.session_state["_ns_result"] = {"n": n_ns, "Q": Q_ns, "H": H_ns, "res": r}
            except ValueError as e:
                st.session_state["_ns_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_ns_result")
        if rr:
            r = rr["res"]
            st.success(f"ns = {r['ns']:.1f}")
            st.info(r["tipo"])
            _export_csv_button(
                "Numero Specifico di Giri (ns)",
                {"n [RPM]": rr["n"], "Q [m³/s]": rr["Q"], "H [m]": rr["H"], "ns": f"{r['ns']:.1f}", "Tipo": r["tipo"]},
                key="ns_export",
            )

    elif tool_mec == "Proprieta Sezione":
        tipo_sez = st.selectbox("Forma sezione:", ["Rettangolo", "Cerchio pieno", "Tubo", "Doppio T (HEA/IPE)"], key="sez_tipo")
        if tipo_sez == "Rettangolo":
            c1, c2 = st.columns(2)
            b_s = c1.number_input("Base b [mm]:", value=50.0, min_value=0.1, key="sez_b")
            h_s = c2.number_input("Altezza h [mm]:", value=100.0, min_value=0.1, key="sez_h")
            if st.button("Calcola", key="sez_btn_rect"):
                r = rm.sezione_rettangolare(b_s, h_s)
                st.session_state["_sez_result"] = {"forma": tipo_sez, "input": {"Base b [mm]": b_s, "Altezza h [mm]": h_s}, "res": r}
        elif tipo_sez == "Cerchio pieno":
            d_s = st.number_input("Diametro d [mm]:", value=50.0, min_value=0.1, key="sez_d")
            if st.button("Calcola", key="sez_btn_circ"):
                r = rm.sezione_cerchio_pieno(d_s)
                st.session_state["_sez_result"] = {"forma": tipo_sez, "input": {"Diametro d [mm]": d_s}, "res": r}
        elif tipo_sez == "Tubo":
            c1, c2 = st.columns(2)
            D_s = c1.number_input("Diametro esterno D [mm]:", value=60.0, min_value=0.1, key="sez_De")
            d_s = c2.number_input("Diametro interno d [mm]:", value=50.0, min_value=0.0, key="sez_di")
            if st.button("Calcola", key="sez_btn_tubo"):
                try:
                    r = rm.sezione_tubo(D_s, d_s)
                    st.session_state["_sez_result"] = {"forma": tipo_sez, "input": {"D esterno [mm]": D_s, "d interno [mm]": d_s}, "res": r}
                except ValueError as e:
                    st.session_state["_sez_result"] = None
                    st.error(str(e))
        else:
            c1, c2, c3, c4 = st.columns(4)
            h_dt = c1.number_input("Altezza H [mm]:", value=200.0, min_value=1.0, key="dt_h")
            b_dt = c2.number_input("Larghezza B [mm]:", value=100.0, min_value=1.0, key="dt_b")
            tw_dt = c3.number_input("Anima tw [mm]:", value=5.5, min_value=0.5, key="dt_tw")
            tf_dt = c4.number_input("Flangia tf [mm]:", value=8.5, min_value=0.5, key="dt_tf")
            if st.button("Calcola", key="sez_btn_dt"):
                try:
                    r = rm.sezione_hea_ipn(h_dt, b_dt, tw_dt, tf_dt)
                    st.session_state["_sez_result"] = {"forma": tipo_sez, "input": {"H [mm]": h_dt, "B [mm]": b_dt, "tw [mm]": tw_dt, "tf [mm]": tf_dt}, "res": r}
                except ValueError as e:
                    st.session_state["_sez_result"] = None
                    st.error(str(e))

        rr = st.session_state.get("_sez_result")
        if rr and rr["forma"] == tipo_sez:
            r = rr["res"]
            st.success(f"A = {r['A_mm2']:.2f} mm²  |  I = {r['I_mm4']:.2f} mm⁴  |  W = {r['W_mm3']:.2f} mm³")
            _export_csv_button(
                f"Proprietà Sezione — {tipo_sez}",
                {
                    "Forma": tipo_sez, **rr["input"],
                    "Area [mm²]": f"{r['A_mm2']:.2f}", "Momento I [mm⁴]": f"{r['I_mm4']:.2f}", "Modulo W [mm³]": f"{r['W_mm3']:.2f}",
                },
                key="sez_export",
            )

    elif tool_mec == "Calcolo Trave":
        st.subheader("Momento, tensione e freccia per schemi di trave comuni")
        mat_trave = st.selectbox("Materiale:", rm.lista_materiali(), key="tr2_mat")
        info_mat  = rm.info_materiale(mat_trave)
        E_tr  = st.number_input("Modulo elastico E [MPa]:", value=float(info_mat.get("E_mpa", 210000)), key="tr2_E")
        FS_tr = st.number_input("Fattore di sicurezza FS:", value=1.5, min_value=1.0, key="tr2_fs")
        sigma_amm_tr = (info_mat["sigma_snerv"] / FS_tr
                        if info_mat.get("sigma_snerv") else 160.0)
        st.caption(f"Tensione ammissibile: {sigma_amm_tr:.1f} MPa (σ_snerv / FS)")

        schema_tr = st.selectbox("Schema di trave:", rm.lista_schemi_trave(), key="tr2_schema")
        L_tr = st.number_input("Luce libera L [mm]:", value=2000.0, min_value=1.0, key="tr2_L")

        usa_F = "concentrato" in schema_tr.lower() or "centrale" in schema_tr.lower() or "punta" in schema_tr.lower() or "+" in schema_tr
        usa_q = "distribuito" in schema_tr.lower() or "+" in schema_tr
        F_tr = st.number_input("Forza concentrata F [N]:", value=5000.0, min_value=0.0, key="tr2_F") if usa_F else 0.0
        q_tr = st.number_input("Carico distribuito q [N/mm]:", value=2.0, min_value=0.0, key="tr2_q") if usa_q else 0.0

        tipo_sez2 = st.selectbox("Sezione:", ["Rettangolo", "Cerchio pieno", "Tubo"], key="tr2_sez")
        if tipo_sez2 == "Rettangolo":
            b2 = st.number_input("b [mm]:", value=50.0, key="tr2_b")
            h2 = st.number_input("h [mm]:", value=100.0, key="tr2_h")
            sez2 = rm.sezione_rettangolare(b2, h2)
        elif tipo_sez2 == "Cerchio pieno":
            d2 = st.number_input("d [mm]:", value=60.0, key="tr2_d")
            sez2 = rm.sezione_cerchio_pieno(d2)
        else:
            D2 = st.number_input("D esterno [mm]:", value=60.0, key="tr2_De")
            d2i = st.number_input("d interno [mm]:", value=50.0, key="tr2_di")
            try:
                sez2 = rm.sezione_tubo(D2, d2i)
            except ValueError as e:
                st.error(str(e))
                sez2 = None

        if st.button("Calcola trave", key="tr2_btn") and sez2:
            try:
                r = rm.calcola_trave(schema_tr, L_tr, F_tr, q_tr,
                                      sez2["I_mm4"], sez2["W_mm3"], E_tr, sigma_amm_tr)
                st.session_state["_trave_result"] = {"schema": schema_tr, "L": L_tr, "F": F_tr, "q": q_tr, "sigma_amm": sigma_amm_tr, "res": r}
            except ValueError as e:
                st.session_state["_trave_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_trave_result")
        if rr:
            r = rr["res"]
            if r["verificata"]:
                st.success(f"VERIFICATA — sigma_max = {r['sigma_max_mpa']:.2f} MPa  |  CS = {r['CS']:.2f}")
            else:
                st.error(f"NON VERIFICATA — sigma_max = {r['sigma_max_mpa']:.2f} MPa > {rr['sigma_amm']:.1f} MPa")
            st.info(f"M_max = {r['M_max_Nm']:.2f} N·m  |  Freccia max = {r['f_max_mm']:.3f} mm")
            with st.expander("Dettagli"):
                st.write(f"Schema: {r['descrizione']}")
                st.write(f"Reazione A: {r['R_A_N']:.1f} N  |  Reazione B: {r['R_B_N']:.1f} N")
            _export_csv_button(
                "Calcolo Trave",
                {
                    "Schema": rr["schema"], "Luce L [mm]": rr["L"], "Forza F [N]": rr["F"], "Carico q [N/mm]": rr["q"],
                    "sigma_max [MPa]": f"{r['sigma_max_mpa']:.2f}", "M_max [N·m]": f"{r['M_max_Nm']:.2f}",
                    "Freccia max [mm]": f"{r['f_max_mm']:.3f}", "Verificata": "Sì" if r["verificata"] else "No",
                },
                key="trave_export",
            )

    elif tool_mec == "Verifica a Flessione":
        col1, col2 = st.columns(2)
        with col1:
            M_vf = st.number_input("Momento flettente M [N·m]:", value=1000.0, min_value=0.0, key="vf_m")
            W_vf = st.number_input("Modulo di resistenza W [mm³]:", value=50000.0, min_value=1.0, key="vf_w")
        with col2:
            s_vf = st.number_input("Tensione ammissibile [MPa]:", value=160.0, min_value=1.0, key="vf_s")
        if st.button("Verifica", key="vf_btn"):
            try:
                r = rm.verifica_flessione(M_vf, W_vf, s_vf)
                st.session_state["_vf_result"] = {"M": M_vf, "W": W_vf, "s": s_vf, "res": r}
            except ValueError as e:
                st.session_state["_vf_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_vf_result")
        if rr:
            r = rr["res"]
            if r["verificata"]:
                st.success(f"VERIFICATA — sigma = {r['sigma_max_mpa']:.2f} MPa  |  CS = {r['CS']:.2f}")
            else:
                st.error(f"NON VERIFICATA — sigma = {r['sigma_max_mpa']:.2f} MPa  |  W minimo richiesto: {r['W_min_mm3']:.0f} mm³")
            _barra_utilizzo(r["sigma_max_mpa"] / rr["s"] * 100.0, "Utilizzo tensione (σ / σ_amm)")
            _export_csv_button(
                "Verifica a Flessione",
                {
                    "Momento M [N·m]": rr["M"], "Modulo W [mm³]": rr["W"], "σ ammissibile [MPa]": rr["s"],
                    "σ_max [MPa]": f"{r['sigma_max_mpa']:.2f}", "Verificata": "Sì" if r["verificata"] else "No",
                },
                key="vf_export",
            )

    elif tool_mec == "Trazione / Compressione":
        mat_tc = st.selectbox("Materiale:", rm.lista_materiali(), key="tc_mat")
        info_tc = rm.info_materiale(mat_tc)
        col1, col2 = st.columns(2)
        with col1:
            F_tc  = st.number_input("Forza assiale F [N] (+ trazione, - compressione):", value=10000.0, key="tc_f")
            A_tc  = st.number_input("Area sezione A [mm²]:", value=100.0, min_value=0.1, key="tc_a")
        with col2:
            L_tc  = st.number_input("Lunghezza L [mm]:", value=500.0, min_value=0.1, key="tc_l")
            FS_tc = st.number_input("Fattore di sicurezza FS:", value=1.5, min_value=1.0, key="tc_fs")
        E_tc = float(info_tc.get("E_mpa", 210000))
        s_snerv = info_tc.get("sigma_snerv")
        sigma_amm_tc = (s_snerv / FS_tc) if s_snerv else st.number_input("Tensione ammissibile [MPa]:", value=160.0, key="tc_samm")
        if st.button("Calcola", key="tc_btn"):
            try:
                r = rm.calcola_trazione_compressione(F_tc, A_tc, E_tc, L_tc, sigma_amm_tc)
                st.session_state["_tc_result"] = {"F": F_tc, "A": A_tc, "L": L_tc, "sigma_amm": sigma_amm_tc, "res": r}
            except ValueError as e:
                st.session_state["_tc_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_tc_result")
        if rr:
            r = rr["res"]
            if r["verificata"]:
                st.success(f"VERIFICATA — sigma = {r['sigma_mpa']:.2f} MPa  ({r['tipo']})  |  CS = {r['CS']:.2f}")
            else:
                st.error(f"NON VERIFICATA — sigma = {r['sigma_mpa']:.2f} MPa > {rr['sigma_amm']:.1f} MPa")
            st.info(f"Deformazione unitaria: {r['epsilon']:.6f}  |  Variazione lunghezza: {r['delta_mm']:.4f} mm")
            _export_csv_button(
                "Trazione / Compressione",
                {
                    "Forza F [N]": rr["F"], "Area A [mm²]": rr["A"], "Lunghezza L [mm]": rr["L"],
                    "σ [MPa]": f"{r['sigma_mpa']:.2f}", "Tipo": r["tipo"], "Δlunghezza [mm]": f"{r['delta_mm']:.4f}",
                },
                key="tc_export",
            )

    elif tool_mec == "Perdite di Carico Concentrate":
        st.subheader("Perdite di carico concentrate — raccordi e valvole")
        raccordi_disp = perdite_carico.lista_raccordi()
        col1, col2, col3 = st.columns(3)
        with col1:
            v_pc = st.number_input("Velocita fluido [m/s]:", value=1.5, min_value=0.0, key="pc_v")
        with col2:
            rho_pc = st.number_input("Densita fluido [kg/m³]:", value=1000.0, min_value=1.0, key="pc_rho")
        with col3:
            n_tipi = st.number_input("Numero di tipi da aggiungere:", min_value=1, max_value=10, value=2, key="pc_ntipi")
        raccordi_input = []
        for ki in range(int(n_tipi)):
            ci1, ci2 = st.columns([3, 1])
            nome_r = ci1.selectbox(f"Raccordo {ki+1}:", raccordi_disp, key=f"pc_r{ki}")
            n_r    = ci2.number_input("Qtà:", min_value=1, value=1, key=f"pc_n{ki}")
            raccordi_input.append({"nome": nome_r, "n": int(n_r)})
        if st.button("Calcola perdita totale", key="pc_btn"):
            try:
                r = perdite_carico.perdita_totale(raccordi_input, v_pc, rho_pc)
                st.session_state["_pc_result"] = {"v": v_pc, "rho": rho_pc, "res": r}
            except ValueError as e:
                st.session_state["_pc_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_pc_result")
        if rr:
            r = rr["res"]
            st.success(f"K totale = {r['K_tot']:.3f}  |  ΔP = {r['dP_Pa']:.1f} Pa  ({r['dP_mbar']:.2f} mbar)  |  h_f = {r['h_f_m']:.4f} m")
            with st.expander("Dettaglio per raccordo"):
                for d in r["dettaglio"]:
                    st.write(f"{d['n']}× {d['nome']}  →  K parziale = {d['K_parziale']:.3f}")
            _export_csv_button(
                "Perdite di Carico Concentrate",
                {
                    "Velocità [m/s]": rr["v"], "Densità [kg/m³]": rr["rho"],
                    "K totale": f"{r['K_tot']:.3f}", "ΔP [Pa]": f"{r['dP_Pa']:.1f}", "h_f [m]": f"{r['h_f_m']:.4f}",
                },
                key="pc_export",
            )

    elif tool_mec == "Perdite di Carico Distribuite (Darcy-Weisbach)":
        st.subheader("Perdite di Carico Distribuite — Equazione di Darcy-Weisbach")
        col1, col2 = st.columns(2)
        with col1:
            Q_dw = st.number_input("Portata Q [m³/h]:", value=50.0, min_value=0.01, key="dw_Q")
            D_dw = st.number_input("Diametro interno D [mm]:", value=100.0, min_value=1.0, key="dw_D")
            L_dw = st.number_input("Lunghezza tubazione L [m]:", value=100.0, min_value=0.1, key="dw_L")
        with col2:
            mat_dw = st.selectbox("Materiale tubazione:", list(pcd.RUGOSITA_MATERIALI_MM.keys()), key="dw_mat")
            rug_dw = pcd.RUGOSITA_MATERIALI_MM[mat_dw]
            st.info(f"Rugosità: {rug_dw} mm")
            rho_dw = st.number_input("Densità fluido [kg/m³]:", value=1000.0, min_value=1.0, key="dw_rho")
        if st.button("Calcola Perdita Distribuita", key="dw_btn"):
            try:
                r = pcd.perdita_distribuita(Q_dw, D_dw, L_dw, rug_dw, 1.0e-6, rho_dw)
                st.session_state["_dw_result"] = {"Q": Q_dw, "D": D_dw, "L": L_dw, "mat": mat_dw, "res": r}
            except (ValueError, ZeroDivisionError) as e:
                st.session_state["_dw_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_dw_result")
        if rr:
            r = rr["res"]
            c1, c2, c3 = st.columns(3)
            c1.metric("Velocità", f"{r['v_ms']:.2f} m/s")
            c2.metric("ΔP", f"{r['dP_bar']:.4f} bar")
            c3.metric("Perdita h", f"{r['h_perdita_m']:.3f} m")
            st.info(f"Re = {r['Re']:.0f}  ({r['regime']})  |  f Darcy = {r['f_darcy']:.4f}  |  ΔP = {r['dP_kPa']:.2f} kPa")
            _export_csv_button(
                "Perdite di Carico Distribuite",
                {
                    "Portata [m³/h]": rr["Q"], "Diametro [mm]": rr["D"], "Lunghezza [m]": rr["L"], "Materiale": rr["mat"],
                    "Velocità [m/s]": f"{r['v_ms']:.2f}", "ΔP [bar]": f"{r['dP_bar']:.4f}", "Perdita h [m]": f"{r['h_perdita_m']:.3f}",
                },
                key="dw_export",
            )
        st.markdown("---")
        st.markdown("**Pre-dimensionamento diametro da velocità massima:**")
        col3, col4 = st.columns(2)
        with col3:
            Q_dim = st.number_input("Portata Q [m³/h]:", value=50.0, min_value=0.01, key="dw_Qdim")
        with col4:
            v_max_dim = st.number_input("Velocità massima consigliata [m/s]:", value=2.0, min_value=0.1, key="dw_vmax")
        if st.button("Calcola Diametro Minimo", key="dw_btn2"):
            try:
                r = pcd.diametro_da_velocita_max(Q_dim, v_max_dim)
                st.session_state["_dwdim_result"] = {"Q": Q_dim, "v_max": v_max_dim, "res": r}
            except (ValueError, ZeroDivisionError) as e:
                st.session_state["_dwdim_result"] = None
                st.error(str(e))

        rr2 = st.session_state.get("_dwdim_result")
        if rr2:
            r2 = rr2["res"]
            st.success(f"Diametro minimo: {r2['D_minimo_mm']:.1f} mm")
            _export_csv_button(
                "Perdite di Carico Distribuite — Diametro minimo",
                {"Portata [m³/h]": rr2["Q"], "Velocità max [m/s]": rr2["v_max"], "Diametro minimo [mm]": f"{r2['D_minimo_mm']:.1f}"},
                key="dwdim_export",
            )

    elif tool_mec == "Bulloneria — Serraggio":
        st.subheader("Precarico e coppia di serraggio (VDI 2230 — metodo semplificato)")
        col1, col2, col3 = st.columns(3)
        with col1:
            diam_bs  = st.selectbox("Diametro:", bulloneria.lista_diametri(), key="bs_d")
            classe_bs = st.selectbox("Classe ISO 898-1:", bulloneria.lista_classi(), key="bs_cl")
        with col2:
            lubr_bs  = st.selectbox("Lubrificazione:", bulloneria.lista_lubrificazioni(), key="bs_lub")
            nu_bs    = st.slider("Utilizzo limite elastico ν:", 0.50, 0.90, 0.70, step=0.05, key="bs_nu")
        with col3:
            fs_bs    = st.number_input("Fattore di sicurezza FS:", value=1.0, min_value=1.0, key="bs_fs")
        if st.button("Calcola serraggio", key="bs_btn"):
            try:
                r = bulloneria.calcola_serraggio(diam_bs, classe_bs, lubr_bs, nu_bs, fs_bs)
                st.session_state["_bs_result"] = {"diam": diam_bs, "classe": classe_bs, "lubr": lubr_bs, "res": r}
            except ValueError as e:
                st.session_state["_bs_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_bs_result")
        if rr:
            r = rr["res"]
            st.success(f"Precarico F_p = {r['F_p_kN']:.3f} kN  |  Coppia M_a = {r['M_a_Nm']:.2f} N·m")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Tensione gambo", f"{r['sigma_gambo']:.1f} MPa")
                st.metric("Utilizzo σ_snerv", f"{r['utilizzo_pct']:.1f}%")
            with col2:
                st.metric("σ_snerv", f"{r['sigma_snerv']} MPa")
                st.metric("σ_rott", f"{r['sigma_rott']} MPa")
            _barra_utilizzo(r["utilizzo_pct"], "Utilizzo limite elastico (σ_gambo / σ_snerv)")
            st.caption(f"As = {r['As_mm2']} mm²  |  d = {r['d_mm']} mm  |  k = {r['k']}")
            _export_csv_button(
                "Bulloneria — Serraggio",
                {
                    "Diametro": rr["diam"], "Classe": rr["classe"], "Lubrificazione": rr["lubr"],
                    "Precarico F_p [kN]": f"{r['F_p_kN']:.3f}", "Coppia M_a [N·m]": f"{r['M_a_Nm']:.2f}", "Utilizzo [%]": f"{r['utilizzo_pct']:.1f}",
                },
                key="bs_export",
            )

    elif tool_mec == "Bulloneria — Verifica":
        st.subheader("Verifica bullone a trazione + taglio (Von Mises)")
        col1, col2 = st.columns(2)
        with col1:
            diam_bv   = st.selectbox("Diametro:", bulloneria.lista_diametri(), key="bv_d")
            classe_bv = st.selectbox("Classe:", bulloneria.lista_classi(), key="bv_cl")
            fs_bv     = st.number_input("Fattore di sicurezza FS:", value=1.5, min_value=1.0, key="bv_fs")
        with col2:
            Ft_bv  = st.number_input("Forza trazione F_t [N]:", value=5000.0, min_value=0.0, key="bv_ft")
            Fv_bv  = st.number_input("Forza taglio F_v [N]:", value=2000.0, min_value=0.0, key="bv_fv")
            np_bv  = st.number_input("Piani di taglio:", min_value=1, max_value=4, value=1, key="bv_np")
        if st.button("Verifica", key="bv_btn"):
            try:
                r = bulloneria.verifica_bullone(diam_bv, classe_bv, Ft_bv, Fv_bv, fs_bv, int(np_bv))
                st.session_state["_bv_result"] = {"diam": diam_bv, "classe": classe_bv, "Ft": Ft_bv, "Fv": Fv_bv, "res": r}
            except ValueError as e:
                st.session_state["_bv_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_bv_result")
        if rr:
            r = rr["res"]
            if r["verificata"]:
                st.success(f"VERIFICATA — σ_eq = {r['sigma_eq_mpa']:.2f} MPa ≤ {r['sigma_amm_mpa']:.2f} MPa  |  CS = {r['CS_combined']:.2f}")
            else:
                st.error(f"NON VERIFICATA — σ_eq = {r['sigma_eq_mpa']:.2f} MPa > {r['sigma_amm_mpa']:.2f} MPa")
            utilizzo_bv = r["sigma_eq_mpa"] / r["sigma_amm_mpa"] * 100.0
            _barra_utilizzo(utilizzo_bv, "Utilizzo Von Mises (σ_eq / σ_amm)")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("σ_t (trazione)", f"{r['sigma_t_mpa']:.2f} MPa")
                st.metric("τ (taglio)", f"{r['tau_mpa']:.2f} MPa")
            with col2:
                st.metric("CS trazione", f"{r['CS_trazione']:.2f}" if r['CS_trazione'] != float('inf') else "∞")
                st.metric("CS taglio", f"{r['CS_taglio']:.2f}" if r['CS_taglio'] != float('inf') else "∞")
            _export_csv_button(
                "Bulloneria — Verifica",
                {
                    "Diametro": rr["diam"], "Classe": rr["classe"], "F trazione [N]": rr["Ft"], "F taglio [N]": rr["Fv"],
                    "σ_eq [MPa]": f"{r['sigma_eq_mpa']:.2f}", "σ_amm [MPa]": f"{r['sigma_amm_mpa']:.2f}", "Verificata": "Sì" if r["verificata"] else "No",
                },
                key="bv_export",
            )

    elif tool_mec == "Bulloneria — Flangia":
        st.subheader("Numero minimo di bulloni per flangia (carico assiale)")
        col1, col2 = st.columns(2)
        with col1:
            F_bf   = st.number_input("Carico assiale totale F [N]:", value=50000.0, min_value=1.0, key="bf_F")
            diam_bf = st.selectbox("Diametro:", bulloneria.lista_diametri(), key="bf_d")
            classe_bf = st.selectbox("Classe:", bulloneria.lista_classi(), key="bf_cl")
        with col2:
            lubr_bf = st.selectbox("Lubrificazione:", bulloneria.lista_lubrificazioni(), key="bf_lub")
            nu_bf   = st.slider("Utilizzo ν:", 0.50, 0.90, 0.70, step=0.05, key="bf_nu")
            fs_bf   = st.number_input("Fattore di sicurezza FS:", value=1.5, min_value=1.0, key="bf_fs")
        if st.button("Dimensiona", key="bf_btn"):
            try:
                r = bulloneria.dimensiona_flangia(F_bf, diam_bf, classe_bf, lubr_bf, nu_bf, fs_bf)
                st.session_state["_bf_result"] = {"F": F_bf, "res": r}
            except ValueError as e:
                st.session_state["_bf_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_bf_result")
        if rr:
            r = rr["res"]
            st.success(f"Bulloni necessari: {r['n_bulloni']}× {r['diametro']} cl. {r['classe']}")
            st.info(f"F per bullone: {r['F_per_bullone']:.0f} N  |  Precarico F_p: {r['F_p_bullone']:.0f} N  |  Coppia serraggio: {r['M_a_Nm']:.2f} N·m")
            _export_csv_button(
                "Bulloneria — Flangia",
                {
                    "Carico assiale [N]": rr["F"], "N bulloni": r["n_bulloni"], "Diametro": r["diametro"], "Classe": r["classe"],
                    "F per bullone [N]": f"{r['F_per_bullone']:.0f}", "Coppia serraggio [N·m]": f"{r['M_a_Nm']:.2f}",
                },
                key="bf_export",
            )

    elif tool_mec == "Nastri Trasportatori":
        st.subheader("Nastri Trasportatori (ISO 5048 / DIN 22101)")
        sub_nas = st.radio("Calcolo:", ["Portata e capacità", "Potenza motore", "Tensione nastro", "Angolo max inclinazione"], horizontal=True, key="nas_sub")
        if sub_nas == "Portata e capacità":
            col1, col2 = st.columns(2)
            with col1:
                B_nas   = st.number_input("Larghezza nastro B [m]:", value=0.8, min_value=0.1, key="nas_B")
                v_nas   = st.number_input("Velocità v [m/s]:", value=1.5, min_value=0.1, key="nas_v")
            with col2:
                rho_nas = st.number_input("Densità apparente ρ [kg/m³]:", value=800.0, min_value=10.0, key="nas_rho")
                ang_sur = st.number_input("Angolo surcharge [°]:", value=20.0, min_value=0.0, max_value=35.0, key="nas_sur")
                incl_nas= st.number_input("Inclinazione nastro [°]:", value=0.0, min_value=0.0, max_value=30.0, key="nas_incl")
            if st.button("Calcola Portata", key="nas_btn1"):
                try:
                    r = nastri.portata_massica(B_nas, v_nas, rho_nas, ang_sur, incl_nas)
                    st.session_state["_nas1_result"] = {"B": B_nas, "v": v_nas, "rho": rho_nas, "res": r}
                except ValueError as e:
                    st.session_state["_nas1_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_nas1_result")
            if rr:
                r = rr["res"]
                c1, c2, c3 = st.columns(3)
                c1.metric("Q [m³/h]", f"{r['Q_m3h']:.1f}")
                c2.metric("Q [t/h]", f"{r['Q_th']:.1f}")
                c3.metric("Q eff. [t/h]", f"{r['Q_th_eff']:.1f}")
                st.info(f"Sezione di carico A = {r['A_m2']:.4f} m²  |  Larghezza utile b_eff = {r['b_eff_m']:.3f} m")
                _export_csv_button(
                    "Nastri — Portata e capacità",
                    {"Larghezza B [m]": rr["B"], "Velocità [m/s]": rr["v"], "Densità [kg/m³]": rr["rho"],
                     "Q [m³/h]": f"{r['Q_m3h']:.1f}", "Q [t/h]": f"{r['Q_th']:.1f}", "Q eff [t/h]": f"{r['Q_th_eff']:.1f}"},
                    key="nas1_export",
                )
        elif sub_nas == "Potenza motore":
            col1, col2 = st.columns(2)
            with col1:
                Q_nas   = st.number_input("Portata Q [t/h]:", value=200.0, min_value=1.0, key="nas_Q")
                L_nas   = st.number_input("Lunghezza orizzontale L [m]:", value=50.0, min_value=1.0, key="nas_L")
                H_nas   = st.number_input("Dislivello H [m]:", value=0.0, key="nas_H")
            with col2:
                eta_nas = st.number_input("η trasmissione:", value=0.85, min_value=0.5, max_value=1.0, key="nas_eta")
                f_att   = st.number_input("f attrito rulli:", value=0.022, min_value=0.010, max_value=0.050, key="nas_f")
            if st.button("Calcola Potenza", key="nas_btn2"):
                try:
                    r = nastri.potenza_motore(Q_nas, L_nas, H_nas, eta_nas, f_att)
                    st.session_state["_nas2_result"] = {"Q": Q_nas, "L": L_nas, "H": H_nas, "res": r}
                except ValueError as e:
                    st.session_state["_nas2_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_nas2_result")
            if rr:
                r = rr["res"]
                c1, c2, c3 = st.columns(3)
                c1.metric("P motore", f"{r['P_motore_kW']:.2f} kW")
                c2.metric("P utile", f"{r['P_utile_W']/1000:.2f} kW")
                c3.metric("P sollevamento", f"{r['P_sollevamento_W']/1000:.2f} kW")
                _barra_utilizzo(r["eta"] * 100, "Rendimento trasmissione")
                _export_csv_button(
                    "Nastri — Potenza motore",
                    {"Portata [t/h]": rr["Q"], "Lunghezza [m]": rr["L"], "Dislivello [m]": rr["H"],
                     "P motore [kW]": f"{r['P_motore_kW']:.2f}"},
                    key="nas2_export",
                )
        elif sub_nas == "Tensione nastro":
            col1, col2 = st.columns(2)
            with col1:
                P_tens  = st.number_input("Potenza motore P [W]:", value=15000.0, min_value=1.0, key="nas_Ptens")
                v_tens  = st.number_input("Velocità v [m/s]:", value=1.5, min_value=0.1, key="nas_vtens")
            with col2:
                D_pul   = st.number_input("Diametro puleggia D [mm] (0=ignora):", value=400.0, min_value=0.0, key="nas_Dpul")
            if st.button("Calcola Tensione", key="nas_btn3"):
                try:
                    r = nastri.tensione_nastro(P_tens, v_tens, D_pul if D_pul > 0 else None)
                    st.session_state["_nas3_result"] = {"P": P_tens, "v": v_tens, "res": r}
                except ValueError as e:
                    st.session_state["_nas3_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_nas3_result")
            if rr:
                r = rr["res"]
                c1, c2, c3 = st.columns(3)
                c1.metric("F periferica", f"{r['F_periferica_N']:.0f} N")
                c2.metric("T lato teso", f"{r['T_stretto_N']:.0f} N")
                c3.metric("T lato molle", f"{r['T_molle_N']:.0f} N")
                if "coppia_Nm" in r:
                    st.info(f"Coppia su puleggia: {r['coppia_Nm']:.1f} N·m")
                _export_csv_button(
                    "Nastri — Tensione nastro",
                    {"Potenza [W]": rr["P"], "Velocità [m/s]": rr["v"],
                     "F periferica [N]": f"{r['F_periferica_N']:.0f}", "T lato teso [N]": f"{r['T_stretto_N']:.0f}", "T lato molle [N]": f"{r['T_molle_N']:.0f}"},
                    key="nas3_export",
                )
        else:
            tipo_mat = st.selectbox("Tipo materiale:", ["secco", "umido", "granuloso", "polveri"], key="nas_tipomat")
            rho_ang  = st.number_input("Densità apparente [kg/m³]:", value=800.0, key="nas_rhoang")
            if st.button("Mostra Angoli", key="nas_btn4"):
                try:
                    r = nastri.angolo_max_inclinazione(rho_ang, tipo_mat)
                    st.session_state["_nas4_result"] = {"tipo": tipo_mat, "rho": rho_ang, "res": r}
                except ValueError as e:
                    st.session_state["_nas4_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_nas4_result")
            if rr:
                r = rr["res"]
                st.success(f"Angolo tipico: {r['angolo_tipico_deg']}°  |  Angolo max: {r['angolo_max_deg']}°")
                st.caption(r["note"])
                _export_csv_button(
                    "Nastri — Angolo max inclinazione",
                    {"Tipo materiale": rr["tipo"], "Densità [kg/m³]": rr["rho"],
                     "Angolo tipico [°]": r["angolo_tipico_deg"], "Angolo max [°]": r["angolo_max_deg"]},
                    key="nas4_export",
                )

    elif tool_mec == "Cuscinetti — Durata L10 (ISO 281)":
        st.subheader("Durata a Fatica Cuscinetti a Rotolamento (ISO 281)")
        col1, col2 = st.columns(2)
        with col1:
            C_cus = st.number_input("Capacità di carico dinamico C [kN]:", value=25.0, min_value=0.1, key="cus_C")
            P_cus = st.number_input("Carico dinamico equivalente P [kN]:", value=5.0, min_value=0.1, key="cus_P")
        with col2:
            tipo_cus = st.selectbox("Tipo cuscinetto:", ["sfere", "rulli"], key="cus_tipo")
            n_cus = st.number_input("Velocità di rotazione n [RPM]:", value=1500.0, min_value=1.0, key="cus_n")
        if st.button("Calcola Durata", key="cus_btn1"):
            try:
                r1 = cus.durata_l10(C_cus, P_cus, tipo_cus)
                r2 = cus.durata_ore(r1["L10_milioni_giri"], n_cus)
                st.session_state["_cus1_result"] = {"C": C_cus, "P": P_cus, "tipo": tipo_cus, "n": n_cus, "r1": r1, "r2": r2}
            except (ValueError, ZeroDivisionError) as e:
                st.session_state["_cus1_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_cus1_result")
        if rr:
            r1, r2 = rr["r1"], rr["r2"]
            c1, c2, c3 = st.columns(3)
            c1.metric("L10", f"{r1['L10_milioni_giri']:.1f} milioni giri")
            c2.metric("L10h", f"{r2['L10h']:.0f} ore")
            c3.metric("Anni (8h/die, 250gg)", f"{r2['L10h_anni_8h_die_250gg']:.1f}")
            _export_csv_button(
                "Cuscinetti — Durata L10",
                {"C [kN]": rr["C"], "P [kN]": rr["P"], "Tipo": rr["tipo"], "n [RPM]": rr["n"],
                 "L10 [milioni giri]": f"{r1['L10_milioni_giri']:.1f}", "L10h [ore]": f"{r2['L10h']:.0f}"},
                key="cus1_export",
            )
        st.markdown("---")
        st.markdown("**Carico dinamico equivalente (ciclo variabile):**")
        n_fasi_cus = st.number_input("Numero fasi di carico:", min_value=1, max_value=6, value=2, step=1, key="cus_nfasi")
        forze_cus, frazioni_cus = [], []
        for i in range(int(n_fasi_cus)):
            c1, c2 = st.columns(2)
            with c1:
                F_i = st.number_input(f"Carico fase {i+1} [kN]:", value=5.0, min_value=0.01, key=f"cus_F{i}")
            with c2:
                q_i = st.number_input(f"Frazione tempo fase {i+1}:", value=round(1.0/n_fasi_cus, 2), min_value=0.0, max_value=1.0, key=f"cus_q{i}")
            forze_cus.append(F_i)
            frazioni_cus.append(q_i)
        if st.button("Calcola Carico Equivalente", key="cus_btn2"):
            try:
                r = cus.carico_dinamico_equivalente(forze_cus, frazioni_cus, 3.0 if tipo_cus == "sfere" else 10.0/3.0)
                st.session_state["_cus2_result"] = {"tipo": tipo_cus, "res": r}
            except (ValueError, ZeroDivisionError) as e:
                st.session_state["_cus2_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_cus2_result")
        if rr:
            r = rr["res"]
            st.success(f"Carico dinamico equivalente P_eq = {r['P_eq_kN']:.2f} kN")
            _export_csv_button(
                "Cuscinetti — Carico equivalente",
                {"Tipo": rr["tipo"], "P_eq [kN]": f"{r['P_eq_kN']:.2f}"},
                key="cus2_export",
            )

    elif tool_mec == "Molle Meccaniche":
        st.subheader("Dimensionamento Molle Meccaniche")
        sub_molle = st.radio("Calcolo:", ["Compressione/Trazione", "Tensione torsionale", "Frequenza naturale", "Molla di torsione"], horizontal=True, key="molle_sub")
        if sub_molle == "Compressione/Trazione":
            col1, col2 = st.columns(2)
            with col1:
                d_molla = st.number_input("Diametro filo d [mm]:", value=2.0, min_value=0.1, key="molle_d")
                D_molla = st.number_input("Diametro medio spira D [mm]:", value=20.0, min_value=0.5, key="molle_D")
            with col2:
                n_molla = st.number_input("Numero spire attive n:", value=10.0, min_value=1.0, key="molle_n")
                mat_molla = st.selectbox("Materiale:", list(molle.MATERIALI_MOLLE.keys()), key="molle_mat")
                G_molla = molle.MATERIALI_MOLLE[mat_molla]
            if st.button("Calcola Costante Elastica", key="molle_btn1"):
                try:
                    r = molle.molla_compressione(d_molla, D_molla, n_molla, G_molla)
                    st.session_state["_molle1_result"] = {"d": d_molla, "D": D_molla, "n": n_molla, "mat": mat_molla, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_molle1_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_molle1_result")
            if rr:
                r = rr["res"]
                c1, c2 = st.columns(2)
                c1.metric("k", f"{r['k_N_mm']:.3f} N/mm")
                c2.metric("Indice molla C", f"{r['indice_molla_C']:.1f}")
                _export_csv_button(
                    "Molle — Compressione/Trazione",
                    {"d filo [mm]": rr["d"], "D medio [mm]": rr["D"], "n spire": rr["n"], "Materiale": rr["mat"],
                     "k [N/mm]": f"{r['k_N_mm']:.3f}", "Indice C": f"{r['indice_molla_C']:.1f}"},
                    key="molle1_export",
                )
        elif sub_molle == "Tensione torsionale":
            col1, col2, col3 = st.columns(3)
            with col1:
                F_molla = st.number_input("Forza applicata F [N]:", value=100.0, min_value=0.1, key="molle_F")
            with col2:
                d_t = st.number_input("Diametro filo d [mm]:", value=2.0, min_value=0.1, key="molle_dt")
            with col3:
                D_t = st.number_input("Diametro medio D [mm]:", value=20.0, min_value=0.5, key="molle_Dt")
            if st.button("Calcola Tensione", key="molle_btn2"):
                try:
                    r = molle.tensione_torsionale_molla(F_molla, d_t, D_t)
                    st.session_state["_molle2_result"] = {"F": F_molla, "d": d_t, "D": D_t, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_molle2_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_molle2_result")
            if rr:
                r = rr["res"]
                st.success(f"τ = {r['tau_MPa']:.1f} MPa  (fattore di Wahl Kw = {r['Kw_wahl']:.3f})")
                _export_csv_button(
                    "Molle — Tensione torsionale",
                    {"Forza [N]": rr["F"], "d filo [mm]": rr["d"], "D medio [mm]": rr["D"], "τ [MPa]": f"{r['tau_MPa']:.1f}", "Kw Wahl": f"{r['Kw_wahl']:.3f}"},
                    key="molle2_export",
                )
        elif sub_molle == "Frequenza naturale":
            col1, col2 = st.columns(2)
            with col1:
                k_freq = st.number_input("Costante elastica k [N/mm]:", value=2.0, min_value=0.01, key="molle_kfreq")
            with col2:
                m_freq = st.number_input("Massa applicata [kg]:", value=1.0, min_value=0.001, key="molle_mfreq")
            if st.button("Calcola Frequenza", key="molle_btn3"):
                try:
                    r = molle.frequenza_naturale_molla(k_freq, m_freq)
                    st.session_state["_molle3_result"] = {"k": k_freq, "m": m_freq, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_molle3_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_molle3_result")
            if rr:
                r = rr["res"]
                st.success(f"Frequenza naturale f = {r['f_Hz']:.2f} Hz  (ω = {r['omega_rad_s']:.2f} rad/s)")
                _export_csv_button(
                    "Molle — Frequenza naturale",
                    {"k [N/mm]": rr["k"], "Massa [kg]": rr["m"], "f [Hz]": f"{r['f_Hz']:.2f}"},
                    key="molle3_export",
                )
        else:
            col1, col2 = st.columns(2)
            with col1:
                d_tor = st.number_input("Diametro filo d [mm]:", value=2.0, min_value=0.1, key="molle_dtor")
                D_tor = st.number_input("Diametro medio D [mm]:", value=20.0, min_value=0.5, key="molle_Dtor")
            with col2:
                n_tor = st.number_input("Numero spire attive n:", value=10.0, min_value=1.0, key="molle_ntor")
            if st.button("Calcola Costante Angolare", key="molle_btn4"):
                try:
                    r = molle.molla_torsione(d_tor, D_tor, n_tor)
                    st.session_state["_molle4_result"] = {"d": d_tor, "D": D_tor, "n": n_tor, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_molle4_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_molle4_result")
            if rr:
                r = rr["res"]
                st.success(f"k_θ = {r['k_theta_Nmm_rad']:.2f} N·mm/rad  ({r['k_theta_Nmm_grad']:.2f} N·mm/grado)")
                _export_csv_button(
                    "Molle — Molla di torsione",
                    {"d filo [mm]": rr["d"], "D medio [mm]": rr["D"], "n spire": rr["n"], "k_θ [N·mm/rad]": f"{r['k_theta_Nmm_rad']:.2f}"},
                    key="molle4_export",
                )

    elif tool_mec == "Ruote Dentate — Verifica Lewis":
        st.subheader("Ruote Dentate — Geometria e Verifica a Flessione (Lewis)")
        sub_rd = st.radio("Calcolo:", ["Geometria ruota", "Modulo minimo (Lewis)", "Verifica a flessione", "Rapporto di trasmissione"], horizontal=True, key="rd_sub")
        if sub_rd == "Geometria ruota":
            col1, col2 = st.columns(2)
            with col1:
                m_rd = st.number_input("Modulo m [mm]:", value=3.0, min_value=0.1, key="rd_m")
            with col2:
                z_rd = st.number_input("Numero denti z:", value=20, min_value=1, step=1, key="rd_z")
            if st.button("Calcola Geometria", key="rd_btn1"):
                try:
                    r = rd.geometria_ruota(m_rd, int(z_rd))
                    st.session_state["_rd1_result"] = {"m": m_rd, "z": int(z_rd), "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_rd1_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_rd1_result")
            if rr:
                r = rr["res"]
                c1, c2, c3 = st.columns(3)
                c1.metric("d primitivo", f"{r['d_primitivo_mm']:.1f} mm")
                c2.metric("d esterno", f"{r['d_esterno_mm']:.1f} mm")
                c3.metric("d interno", f"{r['d_interno_mm']:.1f} mm")
                st.info(f"Passo = {r['passo_mm']:.2f} mm")
                _export_csv_button(
                    "Ruote Dentate — Geometria",
                    {"Modulo m [mm]": rr["m"], "Denti z": rr["z"], "d primitivo [mm]": f"{r['d_primitivo_mm']:.1f}",
                     "d esterno [mm]": f"{r['d_esterno_mm']:.1f}", "Passo [mm]": f"{r['passo_mm']:.2f}"},
                    key="rd1_export",
                )
        elif sub_rd == "Modulo minimo (Lewis)":
            col1, col2 = st.columns(2)
            with col1:
                T_rd = st.number_input("Coppia trasmessa T [N·m]:", value=50.0, min_value=0.1, key="rd_T")
                z_min = st.number_input("Numero denti z:", value=20, min_value=1, step=1, key="rd_zmin")
            with col2:
                bm_rd = st.number_input("Rapporto b/m:", value=10.0, min_value=4.0, max_value=16.0, key="rd_bm")
                sigma_rd = st.number_input("Tensione ammissibile [MPa]:", value=200.0, min_value=10.0, key="rd_sigma")
            if st.button("Calcola Modulo Minimo", key="rd_btn2"):
                try:
                    r = rd.modulo_minimo_lewis(T_rd, int(z_min), bm_rd, sigma_rd)
                    st.session_state["_rd2_result"] = {"T": T_rd, "z": int(z_min), "sigma": sigma_rd, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_rd2_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_rd2_result")
            if rr:
                r = rr["res"]
                st.success(f"Modulo minimo richiesto: {r['m_minimo_mm']:.2f} mm  (forza tangenziale stimata {r['Ft_stimata_N']:.0f} N)")
                st.caption("Arrotondare al modulo normalizzato superiore (es. 1, 1.25, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10...).")
                _export_csv_button(
                    "Ruote Dentate — Modulo minimo (Lewis)",
                    {"Coppia [N·m]": rr["T"], "Denti z": rr["z"], "σ amm [MPa]": rr["sigma"], "Modulo minimo [mm]": f"{r['m_minimo_mm']:.2f}"},
                    key="rd2_export",
                )
        elif sub_rd == "Verifica a flessione":
            col1, col2 = st.columns(2)
            with col1:
                T_vf = st.number_input("Coppia trasmessa T [N·m]:", value=50.0, min_value=0.1, key="rd_Tvf")
                m_vf = st.number_input("Modulo m [mm]:", value=3.0, min_value=0.1, key="rd_mvf")
            with col2:
                z_vf = st.number_input("Numero denti z:", value=20, min_value=1, step=1, key="rd_zvf")
                b_vf = st.number_input("Larghezza fascia b [mm]:", value=24.0, min_value=1.0, key="rd_bvf")
            Y_sel = st.selectbox("Fattore di Lewis Y (per numero denti):", list(rd.FATTORI_LEWIS_Y.keys()), index=2, key="rd_Ysel")
            Y_val = rd.FATTORI_LEWIS_Y[Y_sel]
            if st.button("Verifica Flessione", key="rd_btn3"):
                try:
                    r = rd.verifica_flessione_lewis(T_vf, m_vf, int(z_vf), b_vf, Y_val)
                    st.session_state["_rd3_result"] = {"T": T_vf, "m": m_vf, "z": int(z_vf), "b": b_vf, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_rd3_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_rd3_result")
            if rr:
                r = rr["res"]
                c1, c2 = st.columns(2)
                c1.metric("Forza tangenziale Ft", f"{r['Ft_N']:.0f} N")
                c2.metric("Tensione flessione σ", f"{r['sigma_flessione_MPa']:.1f} MPa")
                _export_csv_button(
                    "Ruote Dentate — Verifica flessione",
                    {"Coppia [N·m]": rr["T"], "Modulo [mm]": rr["m"], "Denti z": rr["z"], "Larghezza b [mm]": rr["b"],
                     "Ft [N]": f"{r['Ft_N']:.0f}", "σ flessione [MPa]": f"{r['sigma_flessione_MPa']:.1f}"},
                    key="rd3_export",
                )
        else:
            col1, col2 = st.columns(2)
            with col1:
                z1_rd = st.number_input("Denti pignone z1:", value=20, min_value=1, step=1, key="rd_z1")
            with col2:
                z2_rd = st.number_input("Denti ruota z2:", value=60, min_value=1, step=1, key="rd_z2")
            if st.button("Calcola Rapporto", key="rd_btn4"):
                try:
                    r = rd.rapporto_trasmissione_ruote(int(z1_rd), int(z2_rd))
                    st.session_state["_rd4_result"] = {"z1": int(z1_rd), "z2": int(z2_rd), "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_rd4_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_rd4_result")
            if rr:
                r = rr["res"]
                st.success(f"τ = {r['tau']:.3f}  ({'Riduzione' if r['riduzione'] else 'Moltiplica'})")
                _export_csv_button(
                    "Ruote Dentate — Rapporto trasmissione",
                    {"Denti z1": rr["z1"], "Denti z2": rr["z2"], "τ": f"{r['tau']:.3f}"},
                    key="rd4_export",
                )

    elif tool_mec == "Alberi — Torsione e Flessione":
        st.subheader("Alberi — Verifica a torsione, flessione e fatica (Goodman)")
        sub_alb = st.radio("Calcolo:", ["Momento torcente", "Diametro minimo", "Tensioni sezione", "Fatica — Goodman"], horizontal=True, key="alb_sub")
        mat_alb = st.selectbox("Materiale albero:", list(alb.MATERIALI_ALBERI.keys()), key="alb_mat")
        props = alb.MATERIALI_ALBERI[mat_alb]
        if sub_alb == "Momento torcente":
            col1, col2 = st.columns(2)
            with col1:
                P_alb = st.number_input("Potenza P [kW]:", value=15.0, min_value=0.01, key="alb_P")
            with col2:
                n_alb = st.number_input("Velocità n [RPM]:", value=1450.0, min_value=1.0, key="alb_n")
            if st.button("Calcola Mt", key="alb_btn1"):
                try:
                    r = alb.momento_torcente(P_alb, n_alb)
                    st.session_state["_alb1_result"] = {"P": P_alb, "n": n_alb, "res": r}
                except ValueError as e:
                    st.session_state["_alb1_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_alb1_result")
            if rr:
                r = rr["res"]
                st.success(f"Momento torcente: **{r['Mt_Nm']:.2f} N·m**")
                _export_csv_button(
                    "Alberi — Momento torcente",
                    {"Potenza [kW]": rr["P"], "Velocità [RPM]": rr["n"], "Momento torcente [N·m]": f"{r['Mt_Nm']:.2f}"},
                    key="alb1_export",
                )
        elif sub_alb == "Diametro minimo":
            col1, col2 = st.columns(2)
            with col1:
                Mt_alb = st.number_input("Momento torcente Mt [N·m]:", value=100.0, min_value=0.01, key="alb_Mt")
            with col2:
                tau_alb = st.number_input("Tensione ammissibile τ [MPa]:", value=float(props["Re_MPa"] // 3), min_value=1.0, key="alb_tau")
            if st.button("Calcola Diametro", key="alb_btn2"):
                try:
                    r = alb.diametro_minimo_torsione(Mt_alb, tau_alb)
                    st.session_state["_alb2_result"] = {"Mt": Mt_alb, "tau": tau_alb, "res": r}
                except ValueError as e:
                    st.session_state["_alb2_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_alb2_result")
            if rr:
                r = rr["res"]
                st.success(f"d_min = {r['d_min_mm']:.2f} mm → normalizzato: **{r['d_normalizzato_mm']} mm**")
                _export_csv_button(
                    "Alberi — Diametro minimo",
                    {"Momento torcente [N·m]": rr["Mt"], "τ amm [MPa]": rr["tau"], "d minimo [mm]": f"{r['d_min_mm']:.2f}", "d normalizzato [mm]": r["d_normalizzato_mm"]},
                    key="alb2_export",
                )
        elif sub_alb == "Tensioni sezione":
            col1, col2 = st.columns(2)
            with col1:
                Mt_ts = st.number_input("Momento torcente Mt [N·m]:", value=100.0, min_value=0.0, key="alb_Mt_ts")
                Mf_ts = st.number_input("Momento flettente Mf [N·m]:", value=80.0, min_value=0.0, key="alb_Mf_ts")
            with col2:
                d_ts = st.number_input("Diametro albero d [mm]:", value=40.0, min_value=1.0, key="alb_d_ts")
            if st.button("Verifica Tensioni", key="alb_btn3"):
                try:
                    r = alb.fattore_sicurezza_statico(Mt_ts, Mf_ts, d_ts, props["Re_MPa"])
                    st.session_state["_alb3_result"] = {"Mt": Mt_ts, "Mf": Mf_ts, "d": d_ts, "res": r}
                except ValueError as e:
                    st.session_state["_alb3_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_alb3_result")
            if rr:
                r = rr["res"]
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("τ torsione", f"{r['tau_MPa']:.1f} MPa")
                c2.metric("σ flessione", f"{r['sigma_flessione_MPa']:.1f} MPa")
                c3.metric("σ eq (Von Mises)", f"{r['sigma_eq_MPa']:.1f} MPa")
                c4.metric("n statico", f"{r['n_statico']:.2f}")
                (st.success if r["conforme"] else st.error)(r["giudizio"])
                _export_csv_button(
                    "Alberi — Tensioni sezione",
                    {"Mt [N·m]": rr["Mt"], "Mf [N·m]": rr["Mf"], "d [mm]": rr["d"],
                     "σ eq [MPa]": f"{r['sigma_eq_MPa']:.1f}", "n statico": f"{r['n_statico']:.2f}", "Conforme": "Sì" if r["conforme"] else "No"},
                    key="alb3_export",
                )
        else:
            col1, col2 = st.columns(2)
            with col1:
                sm_gm = st.number_input("σ medio σ_m [MPa]:", value=120.0, min_value=0.0, key="alb_sm")
                sa_gm = st.number_input("σ alternato σ_a [MPa]:", value=80.0, min_value=0.0, key="alb_sa")
            with col2:
                Rm_gm = st.number_input("Resistenza a rottura Rm [MPa]:", value=float(props["Rm_MPa"]), min_value=100.0, key="alb_Rm")
                sf_gm = st.number_input("Limite fatica σ_f [MPa]:", value=float(props["sigma_f_MPa"]), min_value=50.0, key="alb_sf")
            if st.button("Verifica Goodman", key="alb_btn4"):
                try:
                    r = alb.verifica_goodman(sm_gm, sa_gm, Rm_gm, sf_gm)
                    st.session_state["_alb4_result"] = {"sm": sm_gm, "sa": sa_gm, "Rm": Rm_gm, "sf": sf_gm, "res": r}
                except ValueError as e:
                    st.session_state["_alb4_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_alb4_result")
            if rr:
                r = rr["res"]
                c1, c2 = st.columns(2)
                c1.metric("n Goodman", f"{r['n_Goodman']:.2f}")
                c2.metric("n Gerber", f"{r['n_Gerber']:.2f}")
                (st.success if r["conforme_goodman"] else st.error)(r["giudizio"])
                _export_csv_button(
                    "Alberi — Fatica Goodman",
                    {"σ medio [MPa]": rr["sm"], "σ alternato [MPa]": rr["sa"], "Rm [MPa]": rr["Rm"], "σ_f [MPa]": rr["sf"],
                     "n Goodman": f"{r['n_Goodman']:.2f}", "n Gerber": f"{r['n_Gerber']:.2f}", "Conforme": "Sì" if r["conforme_goodman"] else "No"},
                    key="alb4_export",
                )

    elif tool_mec == "Saldature a Cordone d'Angolo":
        st.subheader("Saldature a cordone d'angolo — EN 1993-1-8 (Eurocodice 3)")
        acciaio_s = st.selectbox("Acciaio base:", list(sald.FU_MPa.keys()), key="sald_acc")
        sub_sald = st.radio("Verifica:", ["Taglio puro (forza parallela)", "Carico normale (forza perp.)", "Gola minima"], horizontal=True, key="sald_sub")
        if sub_sald == "Taglio puro (forza parallela)":
            col1, col2 = st.columns(2)
            with col1:
                F_sald = st.number_input("Forza di taglio F [kN]:", value=30.0, min_value=0.01, key="sald_F")
                a_sald = st.number_input("Gola cordone a [mm]:", value=5.0, min_value=1.0, key="sald_a")
            with col2:
                L_sald = st.number_input("Lunghezza cordone L [mm]:", value=100.0, min_value=5.0, key="sald_L")
            if st.button("Verifica Cordone", key="sald_btn1"):
                try:
                    r = sald.verifica_cordone_taglio(F_sald, a_sald, L_sald, acciaio_s)
                    st.session_state["_sald1_result"] = {"acc": acciaio_s, "F": F_sald, "a": a_sald, "L": L_sald, "res": r}
                except ValueError as e:
                    st.session_state["_sald1_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_sald1_result")
            if rr:
                r = rr["res"]
                c1, c2, c3 = st.columns(3)
                c1.metric("A gola", f"{r['A_gola_mm2']:.0f} mm²")
                c2.metric("τ par", f"{r['tau_par_MPa']:.1f} MPa")
                c3.metric("Utilizzazione", f"{r['utilizzazione']*100:.1f}%")
                (st.success if r["conforme"] else st.error)(r["giudizio"])
                _export_csv_button(
                    "Saldature — Taglio puro",
                    {"Acciaio": rr["acc"], "Forza [kN]": rr["F"], "Gola a [mm]": rr["a"], "Lunghezza L [mm]": rr["L"],
                     "τ par [MPa]": f"{r['tau_par_MPa']:.1f}", "Utilizzazione [%]": f"{r['utilizzazione']*100:.1f}", "Conforme": "Sì" if r["conforme"] else "No"},
                    key="sald1_export",
                )
        elif sub_sald == "Carico normale (forza perp.)":
            col1, col2 = st.columns(2)
            with col1:
                F_sn = st.number_input("Forza normale F [kN]:", value=20.0, min_value=0.01, key="sald_Fn")
                a_sn = st.number_input("Gola cordone a [mm]:", value=5.0, min_value=1.0, key="sald_an")
            with col2:
                L_sn = st.number_input("Lunghezza cordone L [mm]:", value=100.0, min_value=5.0, key="sald_Ln")
            if st.button("Verifica Cordone Normale", key="sald_btn2"):
                try:
                    r = sald.verifica_cordone_normale(F_sn, a_sn, L_sn, acciaio=acciaio_s)
                    st.session_state["_sald2_result"] = {"acc": acciaio_s, "F": F_sn, "a": a_sn, "L": L_sn, "res": r}
                except ValueError as e:
                    st.session_state["_sald2_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_sald2_result")
            if rr:
                r = rr["res"]
                c1, c2, c3 = st.columns(3)
                c1.metric("σ perp", f"{r['sigma_perp_MPa']:.1f} MPa")
                c2.metric("τ perp", f"{r['tau_perp_MPa']:.1f} MPa")
                c3.metric("Utilizzazione", f"{r['utilizzazione']*100:.1f}%")
                (st.success if r["conforme"] else st.error)(r["giudizio"])
                _export_csv_button(
                    "Saldature — Carico normale",
                    {"Acciaio": rr["acc"], "Forza [kN]": rr["F"], "Gola a [mm]": rr["a"], "Lunghezza L [mm]": rr["L"],
                     "σ perp [MPa]": f"{r['sigma_perp_MPa']:.1f}", "Utilizzazione [%]": f"{r['utilizzazione']*100:.1f}", "Conforme": "Sì" if r["conforme"] else "No"},
                    key="sald2_export",
                )
        else:
            t_sald = st.number_input("Spessore minimo dei pezzi [mm]:", value=10.0, min_value=1.0, key="sald_t")
            if st.button("Calcola Gola Minima", key="sald_btn3"):
                try:
                    r = sald.gola_minima(t_sald)
                    ra = sald.resistenza_ammissibile_cordone(acciaio_s)
                    st.session_state["_sald3_result"] = {"acc": acciaio_s, "t": t_sald, "res": r, "ra": ra}
                except ValueError as e:
                    st.session_state["_sald3_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_sald3_result")
            if rr:
                r, ra = rr["res"], rr["ra"]
                st.success(f"Gola minima a_min = **{r['a_min_mm']:.1f} mm** (per t = {r['t_pezzi_mm']:.0f} mm)")
                st.info(f"Resistenza cordone {rr['acc']}: f_vw,d = {ra['f_vwd_MPa']:.1f} MPa")
                _export_csv_button(
                    "Saldature — Gola minima",
                    {"Acciaio": rr["acc"], "Spessore pezzi [mm]": rr["t"], "Gola minima [mm]": f"{r['a_min_mm']:.1f}", "f_vw,d [MPa]": f"{ra['f_vwd_MPa']:.1f}"},
                    key="sald3_export",
                )

    elif tool_mec == "Tubazione in Pressione (EN 13480)":
        st.subheader("Spessore minimo tubazione in pressione — EN 13480-3 / ASME B31.3")
        sub_tub = st.radio("Calcolo:", ["Spessore minimo", "Pressione ammissibile", "Verifica spessore esistente"], horizontal=True, key="tub_sub")
        mat_tub = st.selectbox("Materiale:", list(tubp.MATERIALI_TUBI.keys()), key="tub_mat")
        props_tub = tubp.MATERIALI_TUBI[mat_tub]
        if sub_tub == "Spessore minimo":
            col1, col2 = st.columns(2)
            with col1:
                P_tub = st.number_input("Pressione esercizio P [bar]:", value=10.0, min_value=0.1, key="tub_P")
                DN_sel = st.selectbox("DN nominale:", list(tubp.TABELLA_DN_DO_MM.keys()), index=4, key="tub_DN")
                Do_tub = tubp.TABELLA_DN_DO_MM[DN_sel]
                st.info(f"D esterno: {Do_tub} mm")
            with col2:
                f_tub = st.number_input("Tensione ammissibile f [MPa]:", value=float(props_tub["f_MPa"]), min_value=10.0, key="tub_f")
                c_tub = st.number_input("Sovraspessore corrosione c [mm]:", value=1.0, min_value=0.0, key="tub_c")
                E_tub = st.slider("Coefficiente giuntura E:", 0.60, 1.00, 1.00, step=0.05, key="tub_E")
            if st.button("Calcola Spessore", key="tub_btn1"):
                try:
                    r = tubp.spessore_minimo(P_tub, Do_tub, f_tub, E_tub, c_tub)
                    st.session_state["_tub1_result"] = {"P": P_tub, "DN": DN_sel, "Do": Do_tub, "res": r}
                except ValueError as e:
                    st.session_state["_tub1_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_tub1_result")
            if rr:
                r = rr["res"]
                c1, c2, c3 = st.columns(3)
                c1.metric("t calcolato", f"{r['t_calc_mm']:.2f} mm")
                c2.metric("t minimo (+ corros.)", f"{r['t_min_mm']:.2f} mm")
                c3.metric("t normalizzato", f"{r['t_normalizzato_mm']:.1f} mm")
                st.info(f"D interno con t adottato: {r['D_interno_mm']:.1f} mm")
                _export_csv_button(
                    "Tubazione — Spessore minimo",
                    {"Pressione [bar]": rr["P"], "DN": rr["DN"], "D esterno [mm]": rr["Do"],
                     "t calcolato [mm]": f"{r['t_calc_mm']:.2f}", "t minimo [mm]": f"{r['t_min_mm']:.2f}", "t normalizzato [mm]": f"{r['t_normalizzato_mm']:.1f}"},
                    key="tub1_export",
                )
        elif sub_tub == "Pressione ammissibile":
            col1, col2 = st.columns(2)
            with col1:
                t_exist = st.number_input("Spessore esistente t [mm]:", value=3.2, min_value=0.5, key="tub_texist")
                DN_sel2 = st.selectbox("DN nominale:", list(tubp.TABELLA_DN_DO_MM.keys()), index=4, key="tub_DN2")
                Do_tub2 = tubp.TABELLA_DN_DO_MM[DN_sel2]
            with col2:
                f_tub2 = st.number_input("Tensione ammissibile f [MPa]:", value=float(props_tub["f_MPa"]), min_value=10.0, key="tub_f2")
                c_tub2 = st.number_input("Sovraspessore corrosione c [mm]:", value=1.0, min_value=0.0, key="tub_c2")
            if st.button("Calcola P_ammissibile", key="tub_btn2"):
                try:
                    r = tubp.pressione_ammissibile(t_exist, Do_tub2, f_tub2, c_corrosione_mm=c_tub2)
                    st.session_state["_tub2_result"] = {"t": t_exist, "DN": DN_sel2, "Do": Do_tub2, "res": r}
                except ValueError as e:
                    st.session_state["_tub2_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_tub2_result")
            if rr:
                r = rr["res"]
                st.success(f"Pressione ammissibile: **{r['P_amm_bar']:.2f} bar** ({r['P_amm_MPa']:.3f} MPa)")
                _export_csv_button(
                    "Tubazione — Pressione ammissibile",
                    {"Spessore [mm]": rr["t"], "DN": rr["DN"], "D esterno [mm]": rr["Do"], "P ammissibile [bar]": f"{r['P_amm_bar']:.2f}"},
                    key="tub2_export",
                )
        else:
            col1, col2 = st.columns(2)
            with col1:
                P_vt = st.number_input("Pressione esercizio P [bar]:", value=10.0, min_value=0.1, key="tub_Pvt")
                DN_vt = st.selectbox("DN:", list(tubp.TABELLA_DN_DO_MM.keys()), index=4, key="tub_DNvt")
                Do_vt = tubp.TABELLA_DN_DO_MM[DN_vt]
            with col2:
                t_vt = st.number_input("Spessore adottato t [mm]:", value=4.0, min_value=0.5, key="tub_tvt")
                f_vt = st.number_input("Tensione ammissibile f [MPa]:", value=float(props_tub["f_MPa"]), min_value=10.0, key="tub_fvt")
            if st.button("Verifica Spessore", key="tub_btn3"):
                try:
                    r = tubp.verifica_tubazione(P_vt, Do_vt, t_vt, f_vt)
                    st.session_state["_tub3_result"] = {"P": P_vt, "DN": DN_vt, "t": t_vt, "res": r}
                except ValueError as e:
                    st.session_state["_tub3_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_tub3_result")
            if rr:
                r = rr["res"]
                c1, c2, c3 = st.columns(3)
                c1.metric("t minimo richiesto", f"{r['t_min_mm']:.2f} mm")
                c2.metric("t adottato", f"{r['t_adottato_mm']:.1f} mm")
                c3.metric("Utilizzazione", f"{r['utilizzazione']*100:.1f}%")
                (st.success if r["conforme"] else st.error)(r["giudizio"])
                _export_csv_button(
                    "Tubazione — Verifica spessore",
                    {"Pressione [bar]": rr["P"], "DN": rr["DN"], "t adottato [mm]": rr["t"],
                     "t minimo [mm]": f"{r['t_min_mm']:.2f}", "Utilizzazione [%]": f"{r['utilizzazione']*100:.1f}", "Conforme": "Sì" if r["conforme"] else "No"},
                    key="tub3_export",
                )


elif categoria == "🔧  Pneumatica & Strumenti":
    _card_open("strum", "🔧 Pneumatica & Strumentazione", "IEC 60751 / NIST ITS-90")
    tool_strum = st.selectbox(
        "Seleziona Strumento:",
        [
            "Converti Portata Normalizzata",
            "Caduta di Pressione Tubazione Aria",
            "Dimensionamento Serbatoio",
            "Potenza Compressore",
            "Segnale mA ↔ Tensione",
            "Termocoppia mV → °C (NIST)",
            "Pt100 — Temperatura ↔ Resistenza",
            "Errore di Misura e Incertezza",
            "Taratura Strumento (generica)",
            "Interpolazione da Certificato di Taratura",
            "Caratterizzazione RTD (R0/α reali)",
            "Offset Taratura Termocoppia",
            "Guida — Come effettuare una misura corretta",
            "Valvola di Controllo Cv/Kv",
            "Trasduttore di Pressione 4-20mA",
        ],
        key="strum_tool",
    )
    _render_fav_toggle("🔧  Pneumatica & Strumenti", "strum_tool", tool_strum)

    if tool_strum == "Converti Portata Normalizzata":
        st.subheader("Portata normalizzata [Nl/min] → portata reale a pressione di lavoro")
        col1, col2, col3 = st.columns(3)
        with col1:
            Qn_pn = st.number_input("Portata normalizzata [Nl/min]:", value=100.0, min_value=0.0, key="pn_qn")
        with col2:
            P_pn  = st.number_input("Pressione manometrica [bar g]:", value=6.0, min_value=0.0, key="pn_p")
        with col3:
            T_pn  = st.number_input("Temperatura lavoro [°C]:", value=20.0, key="pn_t")
        if st.button("Converti", key="pn_btn"):
            try:
                r = pneumatica.converti_portata(Qn_pn, P_pn, T_pn)
                st.session_state["_pn_result"] = {"Qn": Qn_pn, "P": P_pn, "T": T_pn, "res": r}
            except ValueError as e:
                st.session_state["_pn_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_pn_result")
        if rr:
            r = rr["res"]
            st.success(f"Portata reale: {r['Qr_l_min']:.2f} l/min  ({r['Qr_m3h']:.4f} m³/h)")
            st.info(f"Pressione assoluta: {r['P_abs_bar']:.4f} bar  |  Rapporto espansione: 1/{1/r['rapporto_esp']:.2f}")
            _export_csv_button(
                "Converti Portata Normalizzata",
                {"Portata norm [Nl/min]": rr["Qn"], "Pressione [bar g]": rr["P"], "Temperatura [°C]": rr["T"],
                 "Portata reale [l/min]": f"{r['Qr_l_min']:.2f}", "Portata reale [m³/h]": f"{r['Qr_m3h']:.4f}"},
                key="pn_export",
            )

    elif tool_strum == "Caduta di Pressione Tubazione Aria":
        st.subheader("Perdita di carico in tubazione aria compressa (Darcy-Weisbach)")
        col1, col2 = st.columns(2)
        with col1:
            Qn_cd = st.number_input("Portata normalizzata [Nl/min]:", value=200.0, min_value=0.1, key="cd_qn")
            L_cd  = st.number_input("Lunghezza tubazione [m]:", value=20.0, min_value=0.1, key="cd_L")
            D_cd  = st.number_input("Diametro interno tubo [mm]:", value=25.0, min_value=1.0, key="cd_D")
        with col2:
            P_cd  = st.number_input("Pressione manometrica [bar g]:", value=6.0, min_value=0.0, key="cd_p")
            T_cd  = st.number_input("Temperatura [°C]:", value=20.0, key="cd_t")
            rug_cd = st.selectbox("Rugosita parete:", ["Acciaio (0.046 mm)", "Inox / rame (0.015 mm)", "Polietilene (0.007 mm)"], key="cd_rug")
            rug_map = {"Acciaio (0.046 mm)": 0.046, "Inox / rame (0.015 mm)": 0.015, "Polietilene (0.007 mm)": 0.007}
            rug_val = rug_map[rug_cd]
        if st.button("Calcola", key="cd_btn"):
            try:
                r = pneumatica.caduta_pressione_tubazione(Qn_cd, L_cd, D_cd, P_cd, T_cd, rug_val)
                st.session_state["_cd_result"] = {"Qn": Qn_cd, "L": L_cd, "D": D_cd, "P": P_cd, "res": r}
            except ValueError as e:
                st.session_state["_cd_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_cd_result")
        if rr:
            r = rr["res"]
            pct_color = "error" if r["dP_pct"] > 5.0 else ("warning" if r["dP_pct"] > 3.0 else "success")
            getattr(st, pct_color)(f"ΔP = {r['dP_mbar']:.2f} mbar  ({r['dP_pct']:.2f}% della pressione assoluta)")
            st.info(f"Velocita aria: {r['velocita_ms']:.2f} m/s  |  Re = {r['Re']:.0f}  |  λ = {r['lambda']:.4f}")
            if r["dP_pct"] > 5.0:
                st.warning("Caduta > 5%: aumentare il diametro della tubazione.")
            _export_csv_button(
                "Caduta di Pressione Tubazione Aria",
                {"Portata [Nl/min]": rr["Qn"], "Lunghezza [m]": rr["L"], "Diametro [mm]": rr["D"], "Pressione [bar g]": rr["P"],
                 "ΔP [mbar]": f"{r['dP_mbar']:.2f}", "ΔP [%]": f"{r['dP_pct']:.2f}", "Velocità [m/s]": f"{r['velocita_ms']:.2f}"},
                key="cd_export",
            )

    elif tool_strum == "Dimensionamento Serbatoio":
        st.subheader("Volume minimo serbatoio aria compressa")
        col1, col2 = st.columns(2)
        with col1:
            Qc_sr = st.number_input("Consumo utenze [Nl/min]:", value=300.0, min_value=0.1, key="sr_qc")
            t_sr  = st.number_input("Autonomia richiesta [s]:", value=30.0, min_value=1.0, key="sr_t")
        with col2:
            Pmax_sr = st.number_input("Pressione massima serbatoio [bar g]:", value=8.0, min_value=0.1, key="sr_pmax")
            Pmin_sr = st.number_input("Pressione minima servizio [bar g]:", value=6.0, min_value=0.0, key="sr_pmin")
        if st.button("Calcola", key="sr_btn"):
            try:
                r = pneumatica.dimensiona_serbatoio(Qc_sr, t_sr, Pmax_sr, Pmin_sr)
                st.session_state["_sr_result"] = {"Qc": Qc_sr, "t": t_sr, "Pmax": Pmax_sr, "Pmin": Pmin_sr, "res": r}
            except ValueError as e:
                st.session_state["_sr_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_sr_result")
        if rr:
            r = rr["res"]
            st.success(f"Volume minimo serbatoio: {r['V_litri']:.1f} litri  ({r['V_m3']:.4f} m³)")
            st.caption(f"ΔP ciclo: {r['delta_P_bar']:.1f} bar  |  P ciclo: {r['P_min_abs']:.3f} → {r['P_max_abs']:.3f} bar a")
            _export_csv_button(
                "Dimensionamento Serbatoio",
                {"Consumo [Nl/min]": rr["Qc"], "Autonomia [s]": rr["t"], "P max [bar g]": rr["Pmax"], "P min [bar g]": rr["Pmin"],
                 "Volume [litri]": f"{r['V_litri']:.1f}"},
                key="sr_export",
            )

    elif tool_strum == "Potenza Compressore":
        col1, col2 = st.columns(2)
        with col1:
            Qn_cmp = st.number_input("Portata erogata [Nl/min]:", value=500.0, min_value=0.1, key="cmp_q")
            P1_cmp = st.number_input("Pressione aspirazione [bar g]:", value=0.0, min_value=-0.5, key="cmp_p1")
            P2_cmp = st.number_input("Pressione mandata [bar g]:", value=8.0, min_value=0.1, key="cmp_p2")
        with col2:
            eta_cmp = st.number_input("Rendimento globale:", value=0.75, min_value=0.3, max_value=0.95, key="cmp_eta")
            ns_cmp  = st.radio("Numero stadi:", [1, 2], key="cmp_ns")
        if st.button("Calcola", key="cmp_btn"):
            try:
                r = pneumatica.potenza_compressore(Qn_cmp, P1_cmp, P2_cmp, eta_cmp, ns_cmp)
                st.session_state["_cmp_result"] = {"Qn": Qn_cmp, "P1": P1_cmp, "P2": P2_cmp, "ns": ns_cmp, "res": r}
            except ValueError as e:
                st.session_state["_cmp_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_cmp_result")
        if rr:
            r = rr["res"]
            st.success(f"Potenza assorbita: {r['P_kW']:.2f} kW  (P ideale: {r['P_id_kW']:.2f} kW)")
            st.info(f"Rapporto di compressione totale: {r['beta_tot']:.2f}  |  Temp. uscita: {r['T_out_C']:.1f} °C")
            if rr["ns"] == 2:
                st.caption(f"Rapporto per stadio: {r['beta_stadio']:.2f}")
            _export_csv_button(
                "Potenza Compressore",
                {"Portata [Nl/min]": rr["Qn"], "P aspirazione [bar g]": rr["P1"], "P mandata [bar g]": rr["P2"], "N stadi": rr["ns"],
                 "Potenza assorbita [kW]": f"{r['P_kW']:.2f}", "β totale": f"{r['beta_tot']:.2f}", "T uscita [°C]": f"{r['T_out_C']:.1f}"},
                key="cmp_export",
            )

    elif tool_strum == "Segnale mA ↔ Tensione":
        col1, col2 = st.columns(2)
        with col1:
            ma_val = st.number_input("Corrente loop [mA]:", value=12.0, min_value=0.0, max_value=25.0, key="ma_i")
        with col2:
            shunt  = st.number_input("Resistenza shunt [Ω]:", value=250.0, min_value=1.0, key="ma_r")
        if st.button("Converti", key="ma_btn"):
            try:
                r = strumentazione.converti_ma_tensione(ma_val, shunt)
                st.session_state["_ma_result"] = {"ma": ma_val, "shunt": shunt, "res": r}
            except ValueError as e:
                st.session_state["_ma_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_ma_result")
        if rr:
            r = rr["res"]
            st.success(f"{rr['ma']} mA su {rr['shunt']} Ω = {r['tensione_V']:.4f} V  ({r['tensione_mV']:.2f} mV)")
            if r["pct_4_20"] is not None:
                st.info(f"Posizione nel range 4-20 mA: {r['pct_4_20']:.1f}%")
                st.progress(min(max(r["pct_4_20"] / 100.0, 0.0), 1.0))
            st.caption(f"Potenza dissipata sullo shunt: {r['potenza_mW']:.3f} mW")
            _export_csv_button(
                "Segnale mA ↔ Tensione",
                {"Corrente [mA]": rr["ma"], "Shunt [Ω]": rr["shunt"], "Tensione [V]": f"{r['tensione_V']:.4f}", "Tensione [mV]": f"{r['tensione_mV']:.2f}"},
                key="ma_export",
            )

    elif tool_strum == "Termocoppia mV → °C (NIST)":
        st.subheader("Linearizzazione NIST ITS-90")
        col1, col2 = st.columns(2)
        with col1:
            tipo_tc = st.selectbox("Tipo termocoppia:", strumentazione.tipi_termocoppia(), key="tc_tipo")
        with col2:
            mv_tc = st.number_input("Segnale FEM [mV]:", value=20.0, format="%.4f", key="tc_mv")
        if st.button("Calcola temperatura", key="tc_btn"):
            try:
                r = strumentazione.termocoppia_mv_a_gradi(mv_tc, tipo_tc)
                st.session_state["_tcmv_result"] = {"tipo": tipo_tc, "mv": mv_tc, "res": r}
            except ValueError as e:
                st.session_state["_tcmv_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_tcmv_result")
        if rr:
            r = rr["res"]
            st.success(f"Tipo {rr['tipo']}: {rr['mv']:.4f} mV → {r['temperatura_C']:.2f} °C")
            st.caption(f"Range valido: {r['range_mv'][0]:.3f} → {r['range_mv'][1]:.3f} mV")
            _export_csv_button(
                "Termocoppia mV → °C (NIST)",
                {"Tipo": rr["tipo"], "FEM [mV]": rr["mv"], "Temperatura [°C]": f"{r['temperatura_C']:.2f}"},
                key="tcmv_export",
            )

    elif tool_strum == "Pt100 — Temperatura ↔ Resistenza":
        st.subheader("Pt100 secondo IEC 60751 (Callendar-Van Dusen)")
        direzione = st.radio("Direzione:", ["T → R  (calcola resistenza dalla temperatura)", "R → T  (calcola temperatura dalla resistenza)"], key="pt_dir")
        if "T → R" in direzione:
            T_pt = st.number_input("Temperatura [°C]:", value=100.0, min_value=-200.0, max_value=850.0, key="pt_t")
            if st.button("Calcola R", key="pt_btn_tr"):
                try:
                    R = strumentazione.pt100_t_a_r(T_pt)
                    st.session_state["_pt_result"] = {"dir": "TR", "T": T_pt, "R": R}
                except ValueError as e:
                    st.session_state["_pt_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_pt_result")
            if rr and rr["dir"] == "TR":
                st.success(f"{rr['T']:.2f} °C → {rr['R']:.4f} Ω")
                _export_csv_button(
                    "Pt100 — T → R",
                    {"Temperatura [°C]": rr["T"], "Resistenza [Ω]": f"{rr['R']:.4f}"},
                    key="pt_export_tr",
                )
        else:
            R_pt = st.number_input("Resistenza [Ω]:", value=138.5, min_value=18.0, max_value=390.0, format="%.4f", key="pt_r")
            if st.button("Calcola T", key="pt_btn_rt"):
                try:
                    r = strumentazione.pt100_r_a_t(R_pt)
                    st.session_state["_pt_result"] = {"dir": "RT", "R": R_pt, "T": r["temperatura_C"]}
                except ValueError as e:
                    st.session_state["_pt_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_pt_result")
            if rr and rr["dir"] == "RT":
                st.success(f"{rr['R']:.4f} Ω → {rr['T']:.3f} °C")
                _export_csv_button(
                    "Pt100 — R → T",
                    {"Resistenza [Ω]": rr["R"], "Temperatura [°C]": f"{rr['T']:.3f}"},
                    key="pt_export_rt",
                )

    elif tool_strum == "Errore di Misura e Incertezza":
        st.subheader("Errore assoluto, relativo e incertezza combinata")
        col1, col2 = st.columns(2)
        with col1:
            val_em = st.number_input("Valore misurato:", value=75.0, key="em_val")
            fs_em  = st.number_input("Fondo scala strumento:", value=100.0, min_value=0.01, key="em_fs")
        with col2:
            acc_em = st.number_input("Accuratezza [% FS]:", value=0.5, min_value=0.0, key="em_acc")
            dec_em = st.number_input("Decimali display:", min_value=0, max_value=6, value=1, key="em_dec")
        if st.button("Calcola errore", key="em_btn"):
            try:
                r = strumentazione.calcola_errore_misura(val_em, fs_em, acc_em, int(dec_em))
                st.session_state["_em_result"] = {"val": val_em, "fs": fs_em, "acc": acc_em, "res": r}
            except ValueError as e:
                st.session_state["_em_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_em_result")
        if rr:
            r = rr["res"]
            st.success(f"Errore assoluto: ±{r['errore_assoluto']:.4f}  |  Errore relativo: {r['errore_relativo_pct']:.2f}%")
            st.info(f"Incertezza combinata (RSS): ±{r['incertezza_comb']:.4f}")
            st.info(f"Valore vero stimato: [{r['valore_min']:.4f} → {r['valore_max']:.4f}]")
            _export_csv_button(
                "Errore di Misura e Incertezza",
                {"Valore misurato": rr["val"], "Fondo scala": rr["fs"], "Accuratezza [% FS]": rr["acc"],
                 "Errore assoluto": f"±{r['errore_assoluto']:.4f}", "Errore relativo [%]": f"{r['errore_relativo_pct']:.2f}", "Incertezza comb.": f"±{r['incertezza_comb']:.4f}"},
                key="em_export",
            )

    elif tool_strum == "Valvola di Controllo Cv/Kv":
        st.subheader("Dimensionamento Valvola di Controllo (IEC 60534)")
        sub_val = st.radio("Tipo fluido:", ["Liquido", "Gas comprimibile", "Verifica cavitazione"], horizontal=True, key="val_sub")
        if sub_val == "Liquido":
            col1, col2, col3 = st.columns(3)
            with col1:
                Q_val   = st.number_input("Portata Q [m³/h]:", value=10.0, min_value=0.01, key="val_Q")
            with col2:
                dP_val  = st.number_input("ΔP [bar]:", value=1.0, min_value=0.01, key="val_dP")
            with col3:
                SG_val  = st.number_input("Densità relativa SG:", value=1.0, min_value=0.1, key="val_SG")
            if st.button("Calcola Kv / Cv", key="val_btn1"):
                try:
                    r = valvole.cv_liquido(Q_val, dP_val, SG_val)
                    st.session_state["_val1_result"] = {"Q": Q_val, "dP": dP_val, "SG": SG_val, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_val1_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_val1_result")
            if rr:
                r = rr["res"]
                c1, c2 = st.columns(2)
                c1.metric("Kv [m³/h/√bar]", f"{r['Kv']:.3f}")
                c2.metric("Cv [US gpm/√psi]", f"{r['Cv']:.3f}")
                st.caption("Caratteristiche: " + "  |  ".join([f"**{k}**: {v}" for k, v in valvole.CARATTERISTICHE.items()]))
                _export_csv_button(
                    "Valvola di Controllo — Liquido",
                    {"Portata [m³/h]": rr["Q"], "ΔP [bar]": rr["dP"], "SG": rr["SG"], "Kv": f"{r['Kv']:.3f}", "Cv": f"{r['Cv']:.3f}"},
                    key="val1_export",
                )
        elif sub_val == "Gas comprimibile":
            col1, col2 = st.columns(2)
            with col1:
                Q_gas   = st.number_input("Portata Q [Nm³/h]:", value=500.0, min_value=0.1, key="val_Qgas")
                P1_gas  = st.number_input("P1 a monte [bar a]:", value=6.0, min_value=0.1, key="val_P1gas")
                P2_gas  = st.number_input("P2 a valle [bar a]:", value=3.0, min_value=0.01, key="val_P2gas")
            with col2:
                T_gas   = st.number_input("Temperatura T [°C]:", value=20.0, key="val_Tgas")
                SG_gas  = st.number_input("Densità relativa gas / aria:", value=1.0, min_value=0.1, key="val_SGgas")
            if st.button("Calcola Kv gas", key="val_btn2"):
                try:
                    r = valvole.cv_gas(Q_gas, P1_gas, P2_gas, T_gas + 273.15, SG_gas)
                    st.session_state["_val2_result"] = {"Q": Q_gas, "P1": P1_gas, "P2": P2_gas, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_val2_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_val2_result")
            if rr:
                r = rr["res"]
                c1, c2 = st.columns(2)
                c1.metric("Kv", f"{r['Kv']:.3f}")
                c2.metric("Cv", f"{r['Cv']:.3f}")
                if r["choked_flow"]:
                    st.warning(f"Flusso bloccato (choked flow)! P_critica = {r['P_critica_bar_a']:.2f} bar a  — ΔP effettivo = {r['dP_effettivo_bar']:.2f} bar")
                else:
                    st.info(f"Flusso non bloccato  |  ΔP effettivo = {r['dP_effettivo_bar']:.2f} bar")
                _export_csv_button(
                    "Valvola di Controllo — Gas",
                    {"Portata [Nm³/h]": rr["Q"], "P1 [bar a]": rr["P1"], "P2 [bar a]": rr["P2"], "Kv": f"{r['Kv']:.3f}", "Cv": f"{r['Cv']:.3f}", "Choked flow": "Sì" if r["choked_flow"] else "No"},
                    key="val2_export",
                )
        else:
            col1, col2, col3 = st.columns(3)
            with col1:
                P1_cav  = st.number_input("P1 a monte [bar a]:", value=6.0, min_value=0.1, key="val_P1cav")
            with col2:
                P2_cav  = st.number_input("P2 a valle [bar a]:", value=2.0, min_value=0.01, key="val_P2cav")
            with col3:
                Pvap    = st.number_input("P vapore liquido [bar a]:", value=0.023, min_value=0.001, key="val_Pvap")
            if st.button("Verifica cavitazione", key="val_btn3"):
                try:
                    r = valvole.verifica_cavitazione(P1_cav, P2_cav, Pvap)
                    st.session_state["_val3_result"] = {"P1": P1_cav, "P2": P2_cav, "Pvap": Pvap, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_val3_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_val3_result")
            if rr:
                r = rr["res"]
                colore = {"BASSA": "success", "MEDIA": "warning", "ALTA": "error"}[r["rischio"]]
                getattr(st, colore)(f"Rischio cavitazione: {r['rischio']}  |  σ = {r['sigma']:.3f}  |  σ_crit = {r['sigma_crit']:.3f}")
                st.info(f"ΔP = {r['dP_bar']:.2f} bar  |  FL = {r['FL']:.2f}")
                _export_csv_button(
                    "Valvola di Controllo — Cavitazione",
                    {"P1 [bar a]": rr["P1"], "P2 [bar a]": rr["P2"], "P vapore [bar a]": rr["Pvap"],
                     "Rischio": r["rischio"], "σ": f"{r['sigma']:.3f}", "σ_crit": f"{r['sigma_crit']:.3f}"},
                    key="val3_export",
                )

    elif tool_strum == "Trasduttore di Pressione 4-20mA":
        st.subheader("Trasduttore di Pressione con Uscita 4-20 mA")
        sub_tp = st.radio("Calcolo:", ["mA → Pressione", "Pressione → mA", "Errore di misura", "Caduta tensione loop"], horizontal=True, key="tp_sub")
        if sub_tp == "mA → Pressione":
            col1, col2 = st.columns(2)
            with col1:
                I_tp = st.number_input("Corrente misurata [mA]:", value=12.0, min_value=4.0, max_value=20.0, key="tp_I")
            with col2:
                FS_tp = st.selectbox("Fondo scala trasduttore [bar]:", tp.RANGE_COMMERCIALI_BAR, index=1, key="tp_FS")
            if st.button("Convertiti in Pressione", key="tp_btn1"):
                try:
                    r = tp.ma_a_pressione(I_tp, FS_tp)
                    st.session_state["_tp1_result"] = {"I": I_tp, "FS": FS_tp, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_tp1_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_tp1_result")
            if rr:
                r = rr["res"]
                c1, c2, c3 = st.columns(3)
                c1.metric("Pressione", f"{r['P_bar']:.3f} bar")
                c2.metric("Pressione", f"{r['P_kPa']:.1f} kPa")
                c3.metric("% Fondo Scala", f"{r['percentuale_FS']:.1f} %")
                _export_csv_button(
                    "Trasduttore — mA → Pressione",
                    {"Corrente [mA]": rr["I"], "Fondo scala [bar]": rr["FS"], "Pressione [bar]": f"{r['P_bar']:.3f}", "% FS": f"{r['percentuale_FS']:.1f}"},
                    key="tp1_export",
                )
        elif sub_tp == "Pressione → mA":
            col1, col2 = st.columns(2)
            with col1:
                FS_tp2 = st.selectbox("Fondo scala trasduttore [bar]:", tp.RANGE_COMMERCIALI_BAR, index=1, key="tp_FS2")
            with col2:
                P_tp = st.number_input("Pressione [bar]:", value=10.0, min_value=0.0, key="tp_P")
            if st.button("Convertiti in mA", key="tp_btn2"):
                try:
                    r = tp.pressione_a_ma(P_tp, FS_tp2)
                    st.session_state["_tp2_result"] = {"P": P_tp, "FS": FS_tp2, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_tp2_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_tp2_result")
            if rr:
                r = rr["res"]
                st.success(f"Corrente: {r['I_mA']:.2f} mA  ({r['percentuale_FS']:.1f} % FS)")
                _export_csv_button(
                    "Trasduttore — Pressione → mA",
                    {"Pressione [bar]": rr["P"], "Fondo scala [bar]": rr["FS"], "Corrente [mA]": f"{r['I_mA']:.2f}", "% FS": f"{r['percentuale_FS']:.1f}"},
                    key="tp2_export",
                )
        elif sub_tp == "Errore di misura":
            col1, col2 = st.columns(2)
            with col1:
                I_mis = st.number_input("Corrente misurata [mA]:", value=12.2, min_value=4.0, max_value=20.0, key="tp_Imis")
                I_teo = st.number_input("Corrente teorica [mA]:", value=12.0, min_value=4.0, max_value=20.0, key="tp_Iteo")
            with col2:
                FS_err = st.selectbox("Fondo scala [bar]:", tp.RANGE_COMMERCIALI_BAR, index=1, key="tp_FSerr")
                acc_err = st.number_input("Accuratezza dichiarata [% FS]:", value=0.5, min_value=0.01, key="tp_acc")
            if st.button("Calcola Errore", key="tp_btn3"):
                try:
                    r = tp.errore_misura_trasduttore(I_mis, I_teo, FS_err, acc_err)
                    st.session_state["_tp3_result"] = {"I_mis": I_mis, "I_teo": I_teo, "FS": FS_err, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_tp3_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_tp3_result")
            if rr:
                r = rr["res"]
                colore = "success" if r["entro_accuratezza"] else "error"
                getattr(st, colore)(f"Errore = {r['errore_pct_FS']:.3f} % FS  ({r['errore_bar']:.4f} bar)  —  {r['giudizio']}")
                _export_csv_button(
                    "Trasduttore — Errore di misura",
                    {"I misurata [mA]": rr["I_mis"], "I teorica [mA]": rr["I_teo"], "Fondo scala [bar]": rr["FS"],
                     "Errore [% FS]": f"{r['errore_pct_FS']:.3f}", "Errore [bar]": f"{r['errore_bar']:.4f}", "Entro accuratezza": "Sì" if r["entro_accuratezza"] else "No"},
                    key="tp3_export",
                )
        else:
            col1, col2 = st.columns(2)
            with col1:
                R_loop = st.number_input("Resistenza di carico (shunt/PLC) [Ω]:", value=250.0, min_value=0.0, key="tp_Rloop")
                L_loop = st.number_input("Lunghezza cavo [m]:", value=100.0, min_value=1.0, key="tp_Lloop")
            with col2:
                S_loop = st.number_input("Sezione cavo [mm²]:", value=0.75, min_value=0.1, key="tp_Sloop")
                V_loop = st.number_input("Tensione alimentazione [V]:", value=24.0, min_value=12.0, key="tp_Vloop")
            if st.button("Verifica Loop", key="tp_btn4"):
                try:
                    r = tp.caduta_tensione_loop_4_20(R_loop, L_loop, S_loop, V_loop)
                    st.session_state["_tp4_result"] = {"R": R_loop, "L": L_loop, "S": S_loop, "V": V_loop, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_tp4_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_tp4_result")
            if rr:
                r = rr["res"]
                colore = "success" if r["sufficiente"] else "error"
                getattr(st, colore)(f"Tensione residua al trasduttore: {r['V_residua_trasduttore_V']:.2f} V  —  {r['giudizio']}")
                st.caption(f"R cavo = {r['R_cavo_ohm']:.2f} Ω  |  Caduta su cavo = {r['V_caduta_cavo_V']:.2f} V  |  Caduta su carico = {r['V_caduta_carico_V']:.2f} V")
                _export_csv_button(
                    "Trasduttore — Caduta tensione loop",
                    {"R carico [Ω]": rr["R"], "Lunghezza cavo [m]": rr["L"], "Sezione [mm²]": rr["S"], "Alimentazione [V]": rr["V"],
                     "V residua [V]": f"{r['V_residua_trasduttore_V']:.2f}", "Sufficiente": "Sì" if r["sufficiente"] else "No"},
                    key="tp4_export",
                )

    elif tool_strum == "Taratura Strumento (generica)":
        st.subheader("Taratura strumento — curva di correzione (generica)")
        st.caption("Inserisci i punti di taratura: **Riferimento** = valore vero del campione, "
                   "**Letto** = valore indicato dallo strumento. Vale per qualsiasi grandezza.")
        col1, col2 = st.columns(2)
        with col1:
            grado_cal = st.selectbox("Modello di fit:", ["Lineare (zero/span)", "Polinomiale grado 2", "Polinomiale grado 3"], key="cal_grado")
        with col2:
            unita_cal = st.text_input("Unità di misura (etichetta):", value="", key="cal_unita")
        grado_map = {"Lineare (zero/span)": 1, "Polinomiale grado 2": 2, "Polinomiale grado 3": 3}
        g_cal = grado_map[grado_cal]

        df_default = pd.DataFrame({"Riferimento": [0.0, 50.0, 100.0], "Letto": [0.0, 50.0, 100.0]})
        df_cal = st.data_editor(df_default, num_rows="dynamic", key="cal_editor",
                                use_container_width=True)
        if st.button("Calcola Taratura", key="cal_btn"):
            try:
                punti = [(float(r["Riferimento"]), float(r["Letto"]))
                         for _, r in df_cal.iterrows()
                         if r["Riferimento"] is not None and r["Letto"] is not None]
                res = strumentazione.taratura(punti, g_cal)
                st.session_state["cal_coeff"] = res["coeff"]
                st.session_state["_cal_result"] = {"grado": g_cal, "unita": unita_cal, "res": res}
            except (ValueError, TypeError) as e:
                st.session_state["_cal_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_cal_result")
        if rr:
            res, g_cal_r, unita_cal = rr["res"], rr["grado"], rr["unita"]
            c1, c2, c3 = st.columns(3)
            c1.metric("R²", f"{res['R2']:.6f}")
            c2.metric("Errore max strumento", f"{res['errore_max_raw']:.4g} {unita_cal}".strip())
            c3.metric("Errore residuo (corretto)", f"{res['errore_max_residuo']:.4g} {unita_cal}".strip())
            if res["span"] > 0:
                st.caption(f"Errore strumento {res['errore_max_raw_pct_fs']:.3f}% FS → "
                           f"dopo correzione {res['errore_max_residuo_pct_fs']:.3f}% FS (span {res['span']:.4g}).")
            if g_cal_r == 1:
                st.info(f"Correzione lineare:  vero = {res['pendenza']:.6f} · letto + ({res['offset']:.6f})")
            else:
                st.info("Coefficienti correzione (grado decrescente): "
                        + ", ".join(f"{c:.6g}" for c in res["coeff"]))
            _export_csv_button(
                "Taratura Strumento",
                {"Grado fit": g_cal_r, "R²": f"{res['R2']:.6f}", "Errore max strumento": f"{res['errore_max_raw']:.4g}",
                 "Errore residuo": f"{res['errore_max_residuo']:.4g}", "Coefficienti": ", ".join(f"{c:.6g}" for c in res["coeff"])},
                key="cal_export",
            )

        if "cal_coeff" in st.session_state:
            st.markdown("**Applica la correzione a una nuova lettura**")
            letto_new = st.number_input("Valore letto dallo strumento:", value=0.0, key="cal_apply_in")
            if st.button("Correggi Lettura", key="cal_apply_btn"):
                corretto = strumentazione.applica_taratura(st.session_state["cal_coeff"], letto_new)
                st.success(f"Valore corretto: **{corretto:.6g} {unita_cal}**".strip())

    elif tool_strum == "Interpolazione da Certificato di Taratura":
        st.subheader("Interpolazione da tabella di taratura (certificato)")
        st.caption("Tabella **Ingresso → Valore corretto** (dal certificato del sensore/campione). "
                   "Interpolazione lineare; fuori campo è possibile estrapolare (segnalato).")
        df_def_int = pd.DataFrame({"Ingresso": [0.0, 50.0, 100.0], "Valore": [0.0, 50.2, 100.4]})
        df_int = st.data_editor(df_def_int, num_rows="dynamic", key="int_editor", use_container_width=True)
        col1, col2 = st.columns(2)
        with col1:
            x_int = st.number_input("Ingresso da convertire:", value=25.0, key="int_x")
        with col2:
            estrap = st.checkbox("Permetti estrapolazione fuori campo", value=True, key="int_estrap")
        if st.button("Interpola", key="int_btn"):
            try:
                tab = [(float(r["Ingresso"]), float(r["Valore"]))
                       for _, r in df_int.iterrows()
                       if r["Ingresso"] is not None and r["Valore"] is not None]
                res = strumentazione.interpola_taratura(tab, x_int, estrap)
                st.session_state["_int_result"] = {"x": x_int, "res": res}
            except (ValueError, TypeError) as e:
                st.session_state["_int_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_int_result")
        if rr:
            res = rr["res"]
            st.success(f"Valore corretto: **{res['valore']:.6g}**")
            if res["fuori_campo"]:
                st.warning(f"⚠️ Ingresso fuori dal campo tarato {res['campo']}: valore estrapolato, meno affidabile.")
            _export_csv_button(
                "Interpolazione da Certificato",
                {"Ingresso": rr["x"], "Valore corretto": f"{res['valore']:.6g}", "Fuori campo": "Sì" if res["fuori_campo"] else "No"},
                key="int_export",
            )

    elif tool_strum == "Caratterizzazione RTD (R0/α reali)":
        st.subheader("Caratterizzazione RTD — R0 e α effettivi dai punti di taratura")
        st.caption("Punti **Temperatura [°C] → Resistenza [Ω]**. Regressione R = R0·(1 + α·T), "
                   "confronto con α nominale IEC 60751 (0,003851 °C⁻¹).")
        df_def_rtd = pd.DataFrame({"Temperatura_C": [0.0, 100.0, 200.0], "Resistenza_ohm": [100.0, 138.5, 175.84]})
        df_rtd = st.data_editor(df_def_rtd, num_rows="dynamic", key="rtdcar_editor", use_container_width=True)
        if st.button("Caratterizza RTD", key="rtdcar_btn"):
            try:
                punti = [(float(r["Temperatura_C"]), float(r["Resistenza_ohm"]))
                         for _, r in df_rtd.iterrows()
                         if r["Temperatura_C"] is not None and r["Resistenza_ohm"] is not None]
                res = strumentazione.caratterizza_rtd(punti)
                st.session_state["_rtdcar_result"] = {"res": res}
            except (ValueError, TypeError) as e:
                st.session_state["_rtdcar_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_rtdcar_result")
        if rr:
            res = rr["res"]
            c1, c2, c3 = st.columns(3)
            c1.metric("R0 effettivo", f"{res['R0_effettivo']:.4f} Ω")
            c2.metric("α effettivo", f"{res['alpha_effettivo']:.6f} °C⁻¹")
            c3.metric("Scarto α vs nominale", f"{res['scarto_alpha_pct']:+.2f} %")
            _export_csv_button(
                "Caratterizzazione RTD",
                {"R0 effettivo [Ω]": f"{res['R0_effettivo']:.4f}", "α effettivo [°C⁻¹]": f"{res['alpha_effettivo']:.6f}",
                 "Scarto α [%]": f"{res['scarto_alpha_pct']:+.2f}"},
                key="rtdcar_export",
            )

    elif tool_strum == "Offset Taratura Termocoppia":
        st.subheader("Offset di taratura termocoppia (vs ITS-90)")
        st.caption("Punti **Temperatura riferimento [°C] → f.e.m. letta [mV]**. "
                   "Confronto con la f.e.m. teorica ITS-90 (tipi K, J).")
        tipo_off = st.selectbox("Tipo termocoppia:", strumentazione.tipi_termocoppia_diretta(), key="off_tipo")
        df_def_off = pd.DataFrame({"Temperatura_C": [100.0, 500.0], "mV_letto": [4.15, 20.70]})
        df_off = st.data_editor(df_def_off, num_rows="dynamic", key="off_editor", use_container_width=True)
        if st.button("Calcola Offset", key="off_btn"):
            try:
                punti = [(float(r["Temperatura_C"]), float(r["mV_letto"]))
                         for _, r in df_off.iterrows()
                         if r["Temperatura_C"] is not None and r["mV_letto"] is not None]
                res = strumentazione.caratterizza_offset_tc(punti, tipo_off)
                st.session_state["_off_result"] = {"tipo": tipo_off, "res": res}
            except (ValueError, TypeError) as e:
                st.session_state["_off_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_off_result")
        if rr:
            res = rr["res"]
            c1, c2 = st.columns(2)
            c1.metric("Offset medio", f"{res['offset_medio_mV']:.4f} mV")
            c2.metric("Offset max", f"{res['offset_max_mV']:.4f} mV")
            _export_csv_button(
                "Offset Taratura Termocoppia",
                {"Tipo": rr["tipo"], "Offset medio [mV]": f"{res['offset_medio_mV']:.4f}", "Offset max [mV]": f"{res['offset_max_mV']:.4f}"},
                key="off_export",
            )

    elif tool_strum == "Guida — Come effettuare una misura corretta":
        st.subheader("Guida — Come effettuare una misura corretta")
        st.caption("Buone pratiche metrologiche (IEC 60751, IEC 60584, ITS-90, GUM).")
        for sezione, punti in strumentazione.GUIDA_MISURA.items():
            with st.expander(sezione):
                for p in punti:
                    st.markdown(f"- {p}")

elif categoria == "🌡️  Termotecnica & Impianti":
    _card_open("termo", "🌡️ Termotecnica & Impianti", "EN 12464-1 / ISO 15547")
    tool_termo = st.selectbox(
        "Seleziona Strumento:",
        [
            "Scambiatori — Bilancio Termico",
            "Scambiatori — Area LMTD",
            "Scambiatori — Metodo NTU-ε",
            "Illuminotecnica — Numero Lampade",
            "Illuminotecnica — Indice Locale",
            "Illuminotecnica — Fattore di Manutenzione MF",
            "Illuminotecnica — Potenza e LENI",
            "Isolamento Termico — Parete Piana",
            "Isolamento Termico — Tubo Cilindrico",
            "Serbatoi — Volume e Pressione",
            "Serbatoi — Svuotamento (Torricelli)",
            "Condotte Aria HVAC",
            "Misuratori di Portata",
        ],
        key="termo_tool",
    )
    _render_fav_toggle("🌡️  Termotecnica & Impianti", "termo_tool", tool_termo)

    # ------------------------------------------------------------------
    if tool_termo == "Scambiatori — Bilancio Termico":
        st.subheader("Bilancio termico scambiatore di calore")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**Fluido caldo**")
            mh_sc  = st.number_input("Portata m_h [kg/s]:", value=1.0, min_value=0.001, key="sc_mh")
            Cph_sc = st.number_input("Cp_h [J/(kg·K)]:", value=4180.0, min_value=1.0, key="sc_Cph")
            Thi_sc = st.number_input("T_h,in [°C]:", value=90.0, key="sc_Thi")
            Tho_sc = st.number_input("T_h,out [°C]:", value=60.0, key="sc_Tho")
        with col2:
            st.markdown("**Fluido freddo**")
            mf_sc  = st.number_input("Portata m_f [kg/s]:", value=1.2, min_value=0.001, key="sc_mf")
            Cpf_sc = st.number_input("Cp_f [J/(kg·K)]:", value=4180.0, min_value=1.0, key="sc_Cpf")
            Tfi_sc = st.number_input("T_f,in [°C]:", value=20.0, key="sc_Tfi")
        if st.button("Calcola bilancio", key="sc_bil_btn"):
            try:
                r = scambiatori.bilancio_termico(mh_sc, Cph_sc, Thi_sc, Tho_sc, mf_sc, Cpf_sc)
                st.session_state["_scbil_result"] = {"Thi": Thi_sc, "Tho": Tho_sc, "Tfi": Tfi_sc, "res": r}
            except (ValueError, KeyError) as e:
                st.session_state["_scbil_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_scbil_result")
        if rr:
            r = rr["res"]
            Q_kW = r["Q_kW"]
            Tfo = rr["Tfi"] + r["delta_T_c"]
            st.success(f"Q = {Q_kW:.3f} kW  |  C_h = {r['C_h']:.1f} W/K  |  C_f = {r['C_c']:.1f} W/K")
            st.metric("Temperatura uscita fluido freddo T_f,out", f"{Tfo:.2f} °C")
            _export_csv_button(
                "Scambiatori — Bilancio Termico",
                {"T_h,in [°C]": rr["Thi"], "T_h,out [°C]": rr["Tho"], "T_f,in [°C]": rr["Tfi"],
                 "Q [kW]": f"{Q_kW:.3f}", "T_f,out [°C]": f"{Tfo:.2f}"},
                key="scbil_export",
            )

    elif tool_termo == "Scambiatori — Area LMTD":
        st.subheader("Area di scambio con metodo LMTD")
        col1, col2, col3 = st.columns(3)
        with col1:
            Q_lm   = st.number_input("Potenza termica Q [kW]:", value=100.0, min_value=0.01, key="lm_Q")
            U_lm   = st.number_input("Coefficiente globale U [W/(m²·K)]:", value=500.0, min_value=1.0, key="lm_U")
        with col2:
            Thi_lm = st.number_input("T_h,in [°C]:", value=90.0, key="lm_Thi")
            Tho_lm = st.number_input("T_h,out [°C]:", value=60.0, key="lm_Tho")
        with col3:
            Tfi_lm = st.number_input("T_f,in [°C]:", value=20.0, key="lm_Tfi")
            Tfo_lm = st.number_input("T_f,out [°C]:", value=45.0, key="lm_Tfo")
            config_lm = st.selectbox("Configurazione:", ["controcorrente", "equicorrente"], key="lm_cfg")
        if st.button("Calcola area", key="lm_btn"):
            try:
                rl = scambiatori.lmtd(Thi_lm, Tho_lm, Tfi_lm, Tfo_lm, config_lm)
                ra = scambiatori.area_da_lmtd(Q_lm * 1000.0, U_lm, rl["LMTD_K"])
                st.session_state["_lm_result"] = {"Q": Q_lm, "U": U_lm, "cfg": config_lm, "rl": rl, "ra": ra}
            except ValueError as e:
                st.session_state["_lm_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_lm_result")
        if rr:
            rl, ra = rr["rl"], rr["ra"]
            st.success(f"LMTD = {rl['LMTD_K']:.2f} K  |  Area = {ra['A_m2']:.3f} m²")
            st.info(f"ΔT1 = {rl['dT1_K']:.2f} K  |  ΔT2 = {rl['dT2_K']:.2f} K")
            st.caption("Valori U tipici (W/m²·K): acqua-acqua 800-1500, vapore-acqua 1000-6000, aria-aria 10-50.")
            _export_csv_button(
                "Scambiatori — Area LMTD",
                {"Q [kW]": rr["Q"], "U [W/(m²·K)]": rr["U"], "Configurazione": rr["cfg"],
                 "LMTD [K]": f"{rl['LMTD_K']:.2f}", "Area [m²]": f"{ra['A_m2']:.3f}"},
                key="lm_export",
            )

    elif tool_termo == "Scambiatori — Metodo NTU-ε":
        st.subheader("Metodo NTU-ε (efficacia — numero di unita di trasferimento)")
        col1, col2 = st.columns(2)
        with col1:
            Ch_n  = st.number_input("C_h [W/K] (m_h × Cp_h):", value=4180.0, min_value=1.0, key="ntu_Ch")
            Cc_n  = st.number_input("C_c [W/K] (m_c × Cp_c):", value=5016.0, min_value=1.0, key="ntu_Cc")
            U_n   = st.number_input("Coefficiente U [W/(m²·K)]:", value=500.0, min_value=1.0, key="ntu_U")
            A_n   = st.number_input("Area A [m²]:", value=2.0, min_value=0.01, key="ntu_A")
        with col2:
            Thi_n = st.number_input("T_h,in [°C]:", value=90.0, key="ntu_Thi")
            Tci_n = st.number_input("T_c,in [°C]:", value=20.0, key="ntu_Tci")
            cfg_n = st.selectbox("Configurazione:", ["controcorrente", "equicorrente"], key="ntu_cfg")
        if st.button("Calcola NTU-ε", key="ntu_btn"):
            try:
                r = scambiatori.ntu_effectiveness(Ch_n, Cc_n, Thi_n, Tci_n, U_n, A_n, cfg_n)
                st.session_state["_ntu_result"] = {"U": U_n, "A": A_n, "cfg": cfg_n, "res": r}
            except ValueError as e:
                st.session_state["_ntu_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_ntu_result")
        if rr:
            r = rr["res"]
            st.success(f"NTU = {r['NTU']:.3f}  |  ε = {r['epsilon']:.4f}  ({r['epsilon']*100:.1f}%)")
            st.metric("Potenza termica trasferita Q", f"{r['Q_kW']:.3f} kW")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("T uscita fluido caldo", f"{r['T_h_out']:.2f} °C")
            with col2:
                st.metric("T uscita fluido freddo", f"{r['T_c_out']:.2f} °C")
            st.caption(f"C_r = C_min/C_max = {r['C_r']:.3f}")
            _export_csv_button(
                "Scambiatori — NTU-ε",
                {"U [W/(m²·K)]": rr["U"], "Area [m²]": rr["A"], "Configurazione": rr["cfg"],
                 "NTU": f"{r['NTU']:.3f}", "ε": f"{r['epsilon']:.4f}", "Q [kW]": f"{r['Q_kW']:.3f}"},
                key="ntu_export",
            )

    # ------------------------------------------------------------------
    elif tool_termo == "Illuminotecnica — Numero Lampade":
        st.subheader("Numero di corpi illuminanti — Metodo dei Lumen (EN 12464-1)")
        ambienti = illuminotecnica.lista_ambienti()
        uso_ambiente = st.checkbox("Usa preset ambiente EN 12464-1", value=True, key="il_preset")
        if uso_ambiente:
            amb_sel = st.selectbox("Tipo ambiente:", ambienti, key="il_amb")
            req = illuminotecnica.requisiti_ambiente(amb_sel)
            st.info(f"Em richiesto: {req['Em_lux']} lux  |  UGR_L max: {req['UGRL_max']}  |  Ra min: {req['Ra_min']}")
            Em_il = float(req["Em_lux"])
        else:
            Em_il = st.number_input("Illuminamento medio Em [lux]:", value=500.0, min_value=1.0, key="il_Em")

        col1, col2, col3 = st.columns(3)
        with col1:
            A_il   = st.number_input("Area locale [m²]:", value=100.0, min_value=1.0, key="il_A")
            phi_il = st.number_input("Flusso corpo illuminante [lm]:", value=4000.0, min_value=1.0, key="il_phi",
                                      help="Flusso totale del singolo corpo (lampade × lm/lampada)")
        with col2:
            MF_il  = st.slider("Fattore di manutenzione MF:", 0.50, 0.95, 0.80, step=0.01, key="il_MF")
            UF_il  = st.slider("Fattore di utilizzo UF:", 0.25, 0.85, 0.55, step=0.05, key="il_UF")
        with col3:
            P_lamp = st.number_input("Potenza corpo [W]:", value=36.0, min_value=1.0, key="il_P")
        if st.button("Calcola corpi illuminanti", key="il_btn"):
            try:
                r = illuminotecnica.calcola_numero_lampade(Em_il, A_il, phi_il, MF_il, UF_il)
                rp = illuminotecnica.calcola_potenza_illuminazione(r["N_corpi"], P_lamp, A_il)
                st.session_state["_il_result"] = {"Em": Em_il, "A": A_il, "phi": phi_il, "res": r, "rp": rp}
            except ValueError as e:
                st.session_state["_il_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_il_result")
        if rr:
            r, rp = rr["res"], rr["rp"]
            st.success(f"Corpi necessari: {r['N_corpi']}  (teorico: {r['N_esatto']:.2f})")
            st.metric("Em effettivo con N corpi installati", f"{r['Em_effettivo']:.1f} lux")
            if r["Em_effettivo"] < rr["Em"]:
                st.warning("Em effettivo inferiore al richiesto — verificare UF/MF.")
            st.info(f"Potenza totale: {rp['P_tot_W']:.0f} W  |  LENI: {rp['LENI_W_m2']:.2f} W/m²")
            _export_csv_button(
                "Illuminotecnica — Numero Lampade",
                {"Em richiesto [lux]": rr["Em"], "Area [m²]": rr["A"], "Flusso corpo [lm]": rr["phi"],
                 "Corpi necessari": r["N_corpi"], "Em effettivo [lux]": f"{r['Em_effettivo']:.1f}", "Potenza tot [W]": f"{rp['P_tot_W']:.0f}"},
                key="il_export",
            )

    elif tool_termo == "Illuminotecnica — Indice Locale":
        st.subheader("Indice del locale k (Room Index) — stima UF")
        col1, col2 = st.columns(2)
        with col1:
            L_il = st.number_input("Lunghezza L [m]:", value=10.0, min_value=0.1, key="ri_L")
            W_il = st.number_input("Larghezza W [m]:", value=8.0, min_value=0.1, key="ri_W")
        with col2:
            H_il = st.number_input("Altezza soffitto H [m]:", value=3.5, min_value=0.5, key="ri_H")
            hl_il = st.number_input("Altezza piano di lavoro [m]:", value=0.85, min_value=0.0, key="ri_hl")
        if st.button("Calcola k", key="ri_btn"):
            try:
                r = illuminotecnica.calcola_room_index(L_il, W_il, H_il, hl_il)
                st.session_state["_ri_result"] = {"L": L_il, "W": W_il, "H": H_il, "res": r}
            except ValueError as e:
                st.session_state["_ri_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_ri_result")
        if rr:
            r = rr["res"]
            st.success(f"k = {r['k']:.3f}  |  Hm = {r['Hm_m']:.2f} m  |  A = {r['A_m2']:.1f} m²")
            st.info(r["note_UF"])
            st.caption(f"Distanza max consigliata tra corpi: {r['d_max_m']:.2f} m")
            _export_csv_button(
                "Illuminotecnica — Indice Locale",
                {"Lunghezza [m]": rr["L"], "Larghezza [m]": rr["W"], "Altezza [m]": rr["H"],
                 "k": f"{r['k']:.3f}", "Hm [m]": f"{r['Hm_m']:.2f}", "Area [m²]": f"{r['A_m2']:.1f}"},
                key="ri_export",
            )

    elif tool_termo == "Illuminotecnica — Fattore di Manutenzione MF":
        st.subheader("Fattore di manutenzione MF = LMF × LSF × LLMF × RSMF")
        col1, col2 = st.columns(2)
        with col1:
            LMF_il  = st.slider("LMF (sporcizia apparecchio):", 0.60, 0.98, 0.85, step=0.01, key="mf_LMF",
                                 help="Luminaire Maintenance Factor")
            LSF_il  = st.slider("LSF (sopravvivenza lampade):", 0.80, 1.00, 0.97, step=0.01, key="mf_LSF",
                                 help="Lamp Survival Factor")
        with col2:
            LLMF_il = st.slider("LLMF (calo flusso lampada):", 0.60, 0.98, 0.88, step=0.01, key="mf_LLMF",
                                 help="Lamp Lumen Maintenance Factor")
            RSMF_il = st.slider("RSMF (sporcizia superfici):", 0.80, 1.00, 0.92, step=0.01, key="mf_RSMF",
                                 help="Room Surface Maintenance Factor")
        if st.button("Calcola MF", key="mf_btn"):
            try:
                r = illuminotecnica.calcola_mf(LMF_il, LSF_il, LLMF_il, RSMF_il)
                st.session_state["_mf_result"] = {"res": r}
            except ValueError as e:
                st.session_state["_mf_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_mf_result")
        if rr:
            r = rr["res"]
            color = "success" if r["MF"] >= 0.80 else ("warning" if r["MF"] >= 0.67 else "error")
            getattr(st, color)(f"MF = {r['MF']:.4f}  ({r['classificazione']})")
            st.caption(f"LMF={r['LMF']:.2f}  ×  LSF={r['LSF']:.2f}  ×  LLMF={r['LLMF']:.2f}  ×  RSMF={r['RSMF']:.2f}")
            _export_csv_button(
                "Illuminotecnica — Fattore di Manutenzione MF",
                {"LMF": f"{r['LMF']:.2f}", "LSF": f"{r['LSF']:.2f}", "LLMF": f"{r['LLMF']:.2f}", "RSMF": f"{r['RSMF']:.2f}",
                 "MF": f"{r['MF']:.4f}", "Classificazione": r["classificazione"]},
                key="mf_export",
            )

    elif tool_termo == "Illuminotecnica — Potenza e LENI":
        st.subheader("Potenza installata e densita energetica (LENI)")
        col1, col2, col3 = st.columns(3)
        with col1:
            N_leni  = st.number_input("Numero corpi installati:", min_value=1, value=20, key="leni_N")
        with col2:
            P_leni  = st.number_input("Potenza per corpo [W]:", value=36.0, min_value=1.0, key="leni_P")
        with col3:
            A_leni  = st.number_input("Area locale [m²]:", value=100.0, min_value=1.0, key="leni_A")
        if st.button("Calcola LENI", key="leni_btn"):
            try:
                r = illuminotecnica.calcola_potenza_illuminazione(int(N_leni), P_leni, A_leni)
                st.session_state["_leni_result"] = {"N": int(N_leni), "P": P_leni, "A": A_leni, "res": r}
            except ValueError as e:
                st.session_state["_leni_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_leni_result")
        if rr:
            r = rr["res"]
            st.success(f"Potenza totale: {r['P_tot_W']:.0f} W  ({r['P_tot_kW']:.3f} kW)")
            st.metric("LENI (Lighting Energy Numeric Indicator)", f"{r['LENI_W_m2']:.2f} W/m²")
            if r["LENI_W_m2"] > 15:
                st.warning("LENI > 15 W/m²: considerare l'uso di LED più efficienti o ridurre il numero di corpi.")
            elif r["LENI_W_m2"] > 8:
                st.info("LENI nella norma per ambienti industriali con lampade fluorescenti.")
            else:
                st.success("LENI ottimo — tipico di impianti LED moderni.")
            _export_csv_button(
                "Illuminotecnica — Potenza e LENI",
                {"N corpi": rr["N"], "Potenza per corpo [W]": rr["P"], "Area [m²]": rr["A"],
                 "Potenza totale [W]": f"{r['P_tot_W']:.0f}", "LENI [W/m²]": f"{r['LENI_W_m2']:.2f}"},
                key="leni_export",
            )

    elif tool_termo == "Isolamento Termico — Parete Piana":
        st.subheader("Isolamento Termico Parete Piana (EN ISO 6946)")
        col1, col2 = st.columns(2)
        with col1:
            T_int_iso = st.number_input("T interna [°C]:", value=20.0, key="iso_Tint")
            T_est_iso = st.number_input("T esterna [°C]:", value=-5.0, key="iso_Test")
        with col2:
            R_si = st.number_input("R_si [m²K/W]:", value=0.13, min_value=0.01, key="iso_Rsi")
            R_se = st.number_input("R_se [m²K/W]:", value=0.04, min_value=0.01, key="iso_Rse")
        st.markdown("**Strati della parete (da interno a esterno):**")
        n_strati = st.number_input("Numero strati:", min_value=1, max_value=8, value=3, step=1, key="iso_nstr")
        mat_list = list(iso_t.MATERIALI_LAMBDA.keys())
        strati_list = []
        for i in range(int(n_strati)):
            c1, c2, c3 = st.columns([2, 1, 1])
            with c1:
                mat_sel = st.selectbox(f"Materiale strato {i+1}:", mat_list, key=f"iso_mat{i}")
            with c2:
                lambda_default = iso_t.MATERIALI_LAMBDA[mat_sel]
                lam = st.number_input(f"λ [W/mK]:", value=lambda_default, min_value=0.001, key=f"iso_lam{i}")
            with c3:
                sp = st.number_input(f"Spessore [m]:", value=0.10, min_value=0.001, key=f"iso_sp{i}")
            strati_list.append({"nome": mat_sel, "spessore_m": sp, "lambda_W_mK": lam})
        if st.button("Calcola U e Perdita", key="iso_btn"):
            try:
                r = iso_t.perdita_parete_piana(T_int_iso, T_est_iso, strati_list, R_si, R_se)
                st.session_state["_iso_result"] = {"Tint": T_int_iso, "Test": T_est_iso, "res": r}
            except (ValueError, ZeroDivisionError) as e:
                st.session_state["_iso_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_iso_result")
        if rr:
            r = rr["res"]
            T_int_iso = rr["Tint"]
            c1, c2, c3 = st.columns(3)
            c1.metric("U [W/m²K]", f"{r['U_W_m2K']:.3f}")
            c2.metric("q [W/m²]", f"{r['q_W_m2']:.1f}")
            c3.metric("R_tot [m²K/W]", f"{r['R_tot_m2KW']:.3f}")
            T_ifaces = r.get("T_interfaces", [])
            if T_ifaces:
                st.markdown("**Temperature alle interfacce:**")
                st.text("  →  ".join([f"{t:.1f}°C" for t in T_ifaces]))
            verif = iso_t.verifica_condensa(T_ifaces[0] if T_ifaces else T_int_iso, T_int_iso, 60.0)
            if verif["rischio_condensa"]:
                st.warning(f"Rischio condensa! T_sup = {T_ifaces[0]:.1f}°C < T_rugiada = {verif['T_rugiada_C']:.1f}°C (a UR=60%)")
            _export_csv_button(
                "Isolamento Termico — Parete Piana",
                {"T interna [°C]": rr["Tint"], "T esterna [°C]": rr["Test"],
                 "U [W/m²K]": f"{r['U_W_m2K']:.3f}", "q [W/m²]": f"{r['q_W_m2']:.1f}", "R_tot [m²K/W]": f"{r['R_tot_m2KW']:.3f}"},
                key="iso_export",
            )

    elif tool_termo == "Isolamento Termico — Tubo Cilindrico":
        st.subheader("Isolamento Tubo Cilindrico (EN ISO 6946)")
        col1, col2 = st.columns(2)
        with col1:
            T_fl    = st.number_input("T fluido interno [°C]:", value=80.0, key="isot_Tfl")
            T_amb_t = st.number_input("T ambiente [°C]:", value=20.0, key="isot_Tamb")
            D_int   = st.number_input("Diametro interno D_int [mm]:", value=100.0, min_value=5.0, key="isot_Di")
        with col2:
            L_tub   = st.number_input("Lunghezza tubo [m]:", value=10.0, min_value=0.1, key="isot_L")
            sp_iso  = st.number_input("Spessore isolante [m]:", value=0.05, min_value=0.001, key="isot_sp")
            mat_tub = st.selectbox("Materiale isolante:", list(iso_t.MATERIALI_LAMBDA.keys()), index=list(iso_t.MATERIALI_LAMBDA.keys()).index("Lana di roccia (100 kg/m³)") if "Lana di roccia (100 kg/m³)" in iso_t.MATERIALI_LAMBDA else 0, key="isot_mat")
            lam_tub = iso_t.MATERIALI_LAMBDA[mat_tub]
        if st.button("Calcola Perdita Tubo", key="isot_btn"):
            try:
                strati_tub = [{"nome": mat_tub, "spessore_m": sp_iso, "lambda_W_mK": lam_tub}]
                r = iso_t.perdita_tubo_cilindrico(T_fl, T_amb_t, D_int, strati_tub, L_tub, 0.05, 0.04)
                st.session_state["_isot_result"] = {"Tfl": T_fl, "Tamb": T_amb_t, "Dint": D_int, "L": L_tub, "res": r}
            except (ValueError, ZeroDivisionError) as e:
                st.session_state["_isot_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_isot_result")
        if rr:
            r = rr["res"]
            c1, c2, c3 = st.columns(3)
            c1.metric("Q totale [W]", f"{r['Q_W']:.1f}")
            c2.metric("q lineare [W/m]", f"{r['Q_W_m']:.2f}")
            c3.metric("D esterno [mm]", f"{r['D_est_mm']:.1f}")
            st.info(f"Resistenza lineare R_lin = {r['R_lin_KW']:.4f} K·m/W")
            _export_csv_button(
                "Isolamento Termico — Tubo Cilindrico",
                {"T fluido [°C]": rr["Tfl"], "T ambiente [°C]": rr["Tamb"], "D interno [mm]": rr["Dint"], "Lunghezza [m]": rr["L"],
                 "Q totale [W]": f"{r['Q_W']:.1f}", "q lineare [W/m]": f"{r['Q_W_m']:.2f}"},
                key="isot_export",
            )

    elif tool_termo == "Serbatoi — Volume e Pressione":
        st.subheader("Serbatoi — Volume Geometrico e Pressione di Fondo")
        sub_ser = st.radio("Forma:", ["Cilindro verticale", "Cilindro orizzontale", "Parallelepipedo", "Sfera", "Cono"], horizontal=True, key="ser_forma")
        forma_map = {"Cilindro verticale": "cilindro_vert", "Cilindro orizzontale": "cilindro_oriz", "Parallelepipedo": "parallelepipedo", "Sfera": "sfera", "Cono": "cono"}
        forma_key = forma_map[sub_ser]
        col1, col2 = st.columns(2)
        if forma_key == "cilindro_vert":
            with col1: D_ser = st.number_input("Diametro [m]:", value=1.0, min_value=0.01, key="ser_D")
            with col2: L_ser = st.number_input("Altezza [m]:", value=2.0, min_value=0.01, key="ser_L")
            dims = {"D_m": D_ser, "H_m": L_ser}
        elif forma_key == "cilindro_oriz":
            with col1: D_ser = st.number_input("Diametro [m]:", value=1.0, min_value=0.01, key="ser_D")
            with col2: L_ser = st.number_input("Lunghezza [m]:", value=2.0, min_value=0.01, key="ser_L")
            dims = {"D_m": D_ser, "L_m": L_ser}
        elif forma_key == "parallelepipedo":
            with col1:
                a_ser = st.number_input("Larghezza L [m]:", value=1.0, min_value=0.01, key="ser_a")
                b_ser = st.number_input("Profondità W [m]:", value=1.0, min_value=0.01, key="ser_b")
            with col2: h_ser = st.number_input("Altezza H [m]:", value=1.0, min_value=0.01, key="ser_h")
            dims = {"L_m": a_ser, "W_m": b_ser, "H_m": h_ser}
        elif forma_key == "sfera":
            with col1: D_sfera = st.number_input("Diametro [m]:", value=1.0, min_value=0.01, key="ser_Dsf")
            dims = {"D_m": D_sfera}
        else:  # cono
            with col1: D_cono = st.number_input("Diametro base [m]:", value=1.0, min_value=0.01, key="ser_Dco")
            with col2: H_cono = st.number_input("Altezza [m]:", value=2.0, min_value=0.01, key="ser_Hco")
            dims = {"D_m": D_cono, "H_m": H_cono}
        H_liv  = st.number_input("Livello liquido H [m]:", value=1.5, min_value=0.01, key="ser_Hliq")
        rho_ser = st.number_input("Densità liquido ρ [kg/m³]:", value=1000.0, min_value=100.0, key="ser_rho")
        if st.button("Calcola", key="ser_btn1"):
            try:
                V_tot = serbatoi.volume_geometrico(forma_key, **dims)
                pf    = serbatoi.pressione_fondo(H_liv, rho_ser)
                tf    = serbatoi.tempo_riempimento(V_tot, 10.0)
                st.session_state["_ser1_result"] = {"forma": sub_ser, "Hliv": H_liv, "rho": rho_ser, "V_tot": V_tot, "pf": pf, "tf": tf}
            except (ValueError, ZeroDivisionError) as e:
                st.session_state["_ser1_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_ser1_result")
        if rr:
            V_tot, pf, tf = rr["V_tot"], rr["pf"], rr["tf"]
            c1, c2, c3 = st.columns(3)
            c1.metric("Volume totale [m³]", f"{V_tot:.3f}")
            c1.metric("Volume [L]", f"{V_tot*1000:.0f}")
            c2.metric("Pressione fondo", f"{pf['P_bar']:.4f} bar")
            c2.metric("Altezza equiv.", f"{pf['P_mca']:.2f} mca")
            c3.metric("Riempimento (10 m³/h)", f"{tf['t_min']:.1f} min")
            c3.metric("P fondo [kPa]", f"{pf['P_kPa']:.2f}")
            _export_csv_button(
                "Serbatoi — Volume e Pressione",
                {"Forma": rr["forma"], "Livello liquido [m]": rr["Hliv"], "Densità [kg/m³]": rr["rho"],
                 "Volume [m³]": f"{V_tot:.3f}", "Pressione fondo [bar]": f"{pf['P_bar']:.4f}"},
                key="ser1_export",
            )

    elif tool_termo == "Serbatoi — Svuotamento (Torricelli)":
        st.subheader("Svuotamento Serbatoio — Legge di Torricelli")
        col1, col2 = st.columns(2)
        with col1:
            V_svu   = st.number_input("Volume liquido V [m³]:", value=5.0, min_value=0.01, key="svu_V")
            H_svu   = st.number_input("Altezza colonna H [m]:", value=2.0, min_value=0.1, key="svu_H")
            D_foro  = st.number_input("Diametro foro scarico D [mm]:", value=50.0, min_value=1.0, key="svu_Df")
        with col2:
            Cd_svu  = st.number_input("Coefficiente scarico Cd:", value=0.62, min_value=0.1, max_value=1.0, key="svu_Cd")
            rho_svu = st.number_input("Densità ρ [kg/m³]:", value=1000.0, min_value=100.0, key="svu_rho")
            A_serb  = st.number_input("Sezione serbatoio A [m²]:", value=V_svu / H_svu, min_value=0.01, key="svu_A")
        col_q1, col_q2, col_q3 = st.columns(3)
        q_tor = serbatoi.portata_torricelli(H_svu, D_foro, Cd_svu, rho_svu)
        col_q1.metric("Velocità scarico v", f"{q_tor['v_ms']:.2f} m/s")
        col_q2.metric("Portata iniziale", f"{q_tor['Q_lmin']:.1f} L/min")
        col_q3.metric("Portata iniziale", f"{q_tor['Q_m3h']:.3f} m³/h")
        if st.button("Calcola Tempo Svuotamento", key="svu_btn"):
            try:
                r = serbatoi.tempo_svuotamento(V_svu, H_svu, D_foro, Cd_svu, A_serb)
                st.session_state["_svu_result"] = {"V": V_svu, "H": H_svu, "Df": D_foro, "res": r}
            except (ValueError, ZeroDivisionError) as e:
                st.session_state["_svu_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_svu_result")
        if rr:
            r = rr["res"]
            c1, c2, c3 = st.columns(3)
            c1.metric("Tempo [s]", f"{r['t_svuotamento_s']:.0f}")
            c2.metric("Tempo [min]", f"{r['t_svuotamento_min']:.1f}")
            c3.metric("Tempo [h]", f"{r['t_svuotamento_h']:.3f}")
            _export_csv_button(
                "Serbatoi — Svuotamento (Torricelli)",
                {"Volume [m³]": rr["V"], "Altezza [m]": rr["H"], "Diametro foro [mm]": rr["Df"],
                 "Tempo [s]": f"{r['t_svuotamento_s']:.0f}", "Tempo [min]": f"{r['t_svuotamento_min']:.1f}"},
                key="svu_export",
            )

    elif tool_termo == "Condotte Aria HVAC":
        st.subheader("Condotte Aria HVAC — Darcy-Weisbach")
        sub_hvac = st.radio("Calcolo:", ["Perdita di carico (circolare)", "Perdita di carico (rettangolare)", "Dimensionamento circolare", "Dimensionamento rettangolare"], horizontal=True, key="hvac_sub")
        T_hvac = st.slider("Temperatura aria [°C]:", -10, 60, 20, key="hvac_T")
        if sub_hvac == "Perdita di carico (circolare)":
            col1, col2 = st.columns(2)
            with col1:
                Q_hv = st.number_input("Portata aria Q [m³/h]:", value=2000.0, min_value=1.0, key="hv_Q")
                D_hv = st.number_input("Diametro interno D [mm]:", value=315.0, min_value=50.0, key="hv_D")
            with col2:
                L_hv = st.number_input("Lunghezza condotta L [m]:", value=20.0, min_value=0.1, key="hv_L")
                rug_hv = st.number_input("Rugosità [mm]:", value=0.09, min_value=0.001, key="hv_rug")
            if st.button("Calcola Perdita", key="hv_btn1"):
                try:
                    r = hvac.perdita_carico_condotta(Q_hv, D_hv, L_hv, rugosita_mm=rug_hv, T_C=T_hvac)
                    st.session_state["_hv1_result"] = {"Q": Q_hv, "D": D_hv, "L": L_hv, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_hv1_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_hv1_result")
            if rr:
                r = rr["res"]
                c1, c2, c3 = st.columns(3)
                c1.metric("Velocità", f"{r['v_ms']:.2f} m/s")
                c2.metric("Perdita lineare", f"{r['dP_Pa_m']:.2f} Pa/m")
                c3.metric("Perdita totale", f"{r['dP_Pa_tot']:.0f} Pa")
                st.info(f"Re = {r['Re']:.0f} ({r['regime']})  |  f = {r['f_darcy']:.4f}")
                _export_csv_button(
                    "Condotte HVAC — Perdita circolare",
                    {"Portata [m³/h]": rr["Q"], "Diametro [mm]": rr["D"], "Lunghezza [m]": rr["L"],
                     "Velocità [m/s]": f"{r['v_ms']:.2f}", "Perdita totale [Pa]": f"{r['dP_Pa_tot']:.0f}"},
                    key="hv1_export",
                )
        elif sub_hvac == "Perdita di carico (rettangolare)":
            col1, col2 = st.columns(2)
            with col1:
                Q_hvr = st.number_input("Portata aria Q [m³/h]:", value=2000.0, min_value=1.0, key="hvr_Q")
                a_hvr = st.number_input("Lato a [mm]:", value=400.0, min_value=50.0, key="hvr_a")
            with col2:
                b_hvr = st.number_input("Lato b [mm]:", value=300.0, min_value=50.0, key="hvr_b")
                L_hvr = st.number_input("Lunghezza L [m]:", value=20.0, min_value=0.1, key="hvr_L")
            if st.button("Calcola Perdita Rettangolare", key="hvr_btn"):
                try:
                    r = hvac.perdita_carico_condotta(Q_hvr, 0.0, L_hvr, forma="rettangolare", a_mm=a_hvr, b_mm=b_hvr, T_C=T_hvac)
                    st.session_state["_hvr_result"] = {"Q": Q_hvr, "a": a_hvr, "b": b_hvr, "L": L_hvr, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_hvr_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_hvr_result")
            if rr:
                r = rr["res"]
                c1, c2, c3 = st.columns(3)
                c1.metric("Dh", f"{r['Dh_mm']:.0f} mm")
                c2.metric("Velocità", f"{r['v_ms']:.2f} m/s")
                c3.metric("Perdita totale", f"{r['dP_Pa_tot']:.0f} Pa")
                st.info(f"Re = {r['Re']:.0f} ({r['regime']})  |  ΔP/m = {r['dP_Pa_m']:.2f} Pa/m")
                _export_csv_button(
                    "Condotte HVAC — Perdita rettangolare",
                    {"Portata [m³/h]": rr["Q"], "Lato a [mm]": rr["a"], "Lato b [mm]": rr["b"], "Lunghezza [m]": rr["L"],
                     "Dh [mm]": f"{r['Dh_mm']:.0f}", "Velocità [m/s]": f"{r['v_ms']:.2f}", "Perdita totale [Pa]": f"{r['dP_Pa_tot']:.0f}"},
                    key="hvr_export",
                )
        elif sub_hvac == "Dimensionamento circolare":
            col1, col2 = st.columns(2)
            with col1:
                Q_hd = st.number_input("Portata aria Q [m³/h]:", value=2000.0, min_value=1.0, key="hd_Q")
            with col2:
                tipo_cond = st.selectbox("Tipo condotta:", list(hvac.VELOCITA_RACCOMANDATE_MS.keys()), key="hd_tipo")
                v_max_hd = hvac.VELOCITA_RACCOMANDATE_MS[tipo_cond]["max"]
                st.info(f"v max consigliata: {v_max_hd} m/s")
            if st.button("Dimensiona Condotta", key="hd_btn"):
                try:
                    r = hvac.dimensiona_condotta_circolare(Q_hd, v_max_hd)
                    st.session_state["_hd_result"] = {"Q": Q_hd, "tipo": tipo_cond, "vmax": v_max_hd, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_hd_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_hd_result")
            if rr:
                r = rr["res"]
                c1, c2, c3 = st.columns(3)
                c1.metric("D minimo", f"{r['D_min_mm']:.0f} mm")
                c2.metric("D normalizzato", f"{r['D_normalizzato_mm']} mm")
                c3.metric("Velocità effettiva", f"{r['v_effettiva_ms']:.2f} m/s")
                _export_csv_button(
                    "Condotte HVAC — Dimensionamento circolare",
                    {"Portata [m³/h]": rr["Q"], "Tipo condotta": rr["tipo"], "v max [m/s]": rr["vmax"],
                     "D minimo [mm]": f"{r['D_min_mm']:.0f}", "D normalizzato [mm]": r["D_normalizzato_mm"], "v effettiva [m/s]": f"{r['v_effettiva_ms']:.2f}"},
                    key="hd_export",
                )
        else:
            col1, col2 = st.columns(2)
            with col1:
                Q_hrect = st.number_input("Portata aria Q [m³/h]:", value=2000.0, min_value=1.0, key="hrect_Q")
                rap_hrect = st.number_input("Rapporto lati b/a:", value=1.5, min_value=1.0, max_value=4.0, key="hrect_rap")
            with col2:
                tipo_rect = st.selectbox("Tipo condotta:", list(hvac.VELOCITA_RACCOMANDATE_MS.keys()), key="hrect_tipo")
                v_max_rect = hvac.VELOCITA_RACCOMANDATE_MS[tipo_rect]["max"]
                st.info(f"v max consigliata: {v_max_rect} m/s")
            if st.button("Dimensiona Rettangolare", key="hrect_btn"):
                try:
                    r = hvac.dimensiona_condotta_rettangolare(Q_hrect, rap_hrect, v_max_rect)
                    st.session_state["_hrect_result"] = {"Q": Q_hrect, "rap": rap_hrect, "tipo": tipo_rect, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_hrect_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_hrect_result")
            if rr:
                r = rr["res"]
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Lato a", f"{r['a_mm']:.0f} mm")
                c2.metric("Lato b", f"{r['b_mm']:.0f} mm")
                c3.metric("Dh", f"{r['Dh_mm']:.0f} mm")
                c4.metric("v effettiva", f"{r['v_effettiva_ms']:.2f} m/s")
                _export_csv_button(
                    "Condotte HVAC — Dimensionamento rettangolare",
                    {"Portata [m³/h]": rr["Q"], "Rapporto b/a": rr["rap"], "Tipo condotta": rr["tipo"],
                     "Lato a [mm]": f"{r['a_mm']:.0f}", "Lato b [mm]": f"{r['b_mm']:.0f}", "Dh [mm]": f"{r['Dh_mm']:.0f}"},
                    key="hrect_export",
                )

    elif tool_termo == "Misuratori di Portata":
        st.subheader("Misuratori di Portata Industriali")
        sub_mport = st.radio("Tipo di misuratore:", ["Diaframma tarato (ISO 5167)", "Turbina (K-factor)", "Elettromagnetico"], horizontal=True, key="mport_sub")

        if sub_mport == "Diaframma tarato (ISO 5167)":
            col1, col2, col3 = st.columns(3)
            with col1:
                dP_mp = st.number_input("Caduta di pressione [mbar]:", value=250.0, min_value=0.1, key="mp_dP")
                D_mp  = st.number_input("Diametro tubazione D [mm]:", value=100.0, min_value=1.0, key="mp_D")
            with col2:
                beta_mp = st.number_input("Rapporto diametri beta = d/D:", value=0.5, min_value=0.1, max_value=0.75, step=0.01, key="mp_beta")
                rho_mp  = st.number_input("Densità fluido [kg/m³]:", value=1000.0, min_value=0.01, key="mp_rho")
                mu_mp   = st.number_input("Viscosità dinamica [Pa·s]:", value=0.001, min_value=0.00001, step=0.0001, format="%.5f", key="mp_mu")
            with col3:
                C_mp   = st.number_input("Coefficiente di efflusso C:", value=0.6, min_value=0.1, step=0.01, key="mp_C")
                eps_mp = st.number_input("Fattore di espansione eps:", value=1.0, min_value=0.1, max_value=1.0, step=0.01, key="mp_eps")
                fluido_mp = st.selectbox("Tipo di fluido:", list(misuratori_portata.VELOCITA_CONSIGLIATA_MS.keys()), key="mp_fluido")
            if st.button("Valuta Diaframma", key="mp_btn1"):
                try:
                    r = misuratori_portata.valuta_diaframma(dP_mp, D_mp, beta_mp, rho_mp, mu_mp, C_mp, eps_mp, fluido_mp)
                    st.session_state["_mp1_result"] = r
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_mp1_result"] = None
                    st.error(str(e))

            r = st.session_state.get("_mp1_result")
            if r:
                c1, c2, c3 = st.columns(3)
                c1.metric("Portata", f"{r['Q_m3h']:.2f} m³/h")
                c2.metric("Velocità", f"{r['v_ms']:.2f} m/s")
                c3.metric("Diametro foro", f"{r['d_foro_mm']:.1f} mm")
                st.info(f"Re = {r['Re']:.0f} ({r['regime']}) — {'✅ valido per ISO 5167 (Re≥5000)' if r['valido_iso5167'] else '⚠️ Re troppo basso per ISO 5167 (serve Re≥5000)'}")
                if r["nel_range"]:
                    st.success(f"Velocità nel range consigliato per {r['tipo_fluido']} ({r['v_min_ms']}-{r['v_max_ms']} m/s).")
                else:
                    st.warning(f"Velocità fuori dal range consigliato per {r['tipo_fluido']} ({r['v_min_ms']}-{r['v_max_ms']} m/s).")
                _export_csv_button(
                    "Misuratori di Portata — Diaframma ISO 5167",
                    {"dP [mbar]": dP_mp, "D [mm]": D_mp, "beta": beta_mp, "Fluido": fluido_mp,
                     "Portata [m³/h]": f"{r['Q_m3h']:.2f}", "Velocità [m/s]": f"{r['v_ms']:.2f}", "Re": f"{r['Re']:.0f}"},
                    key="mp1_export",
                )

        elif sub_mport == "Turbina (K-factor)":
            col1, col2 = st.columns(2)
            with col1:
                freq_mp = st.number_input("Frequenza impulsi [Hz]:", value=50.0, min_value=0.01, key="mp_freq")
            with col2:
                k_mp = st.number_input("K-factor [impulsi/litro]:", value=100.0, min_value=0.01, key="mp_k")
            if st.button("Calcola Portata Turbina", key="mp_btn2"):
                try:
                    r = misuratori_portata.portata_turbina(freq_mp, k_mp)
                    st.session_state["_mp2_result"] = {"freq": freq_mp, "k": k_mp, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_mp2_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_mp2_result")
            if rr:
                r = rr["res"]
                c1, c2 = st.columns(2)
                c1.metric("Portata", f"{r['Q_lmin']:.2f} L/min")
                c2.metric("Portata", f"{r['Q_m3h']:.3f} m³/h")
                _export_csv_button(
                    "Misuratori di Portata — Turbina",
                    {"Frequenza [Hz]": rr["freq"], "K-factor [imp/L]": rr["k"],
                     "Portata [L/min]": f"{r['Q_lmin']:.2f}", "Portata [m³/h]": f"{r['Q_m3h']:.3f}"},
                    key="mp2_export",
                )

        else:
            col1, col2 = st.columns(2)
            with col1:
                v_mp = st.number_input("Velocità media misurata [m/s]:", value=2.0, min_value=0.01, key="mp_v")
            with col2:
                D_mp2 = st.number_input("Diametro tubazione D [mm]:", value=100.0, min_value=1.0, key="mp_D2")
            if st.button("Calcola Portata Elettromagnetico", key="mp_btn3"):
                try:
                    r = misuratori_portata.portata_elettromagnetico(v_mp, D_mp2)
                    st.session_state["_mp3_result"] = {"v": v_mp, "D": D_mp2, "res": r}
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_mp3_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_mp3_result")
            if rr:
                r = rr["res"]
                c1, c2 = st.columns(2)
                c1.metric("Portata", f"{r['Q_m3h']:.2f} m³/h")
                c2.metric("Sezione tubazione", f"{r['A_m2']*1e4:.1f} cm²")
                _export_csv_button(
                    "Misuratori di Portata — Elettromagnetico",
                    {"Velocità [m/s]": rr["v"], "D [mm]": rr["D"], "Portata [m³/h]": f"{r['Q_m3h']:.2f}"},
                    key="mp3_export",
                )


elif categoria == "🔒  Sicurezza & Utilities":
    _card_open("sic", "🔒 Sicurezza & Utilities", "ISO 9612 / D.Lgs 81/2008")
    tool_sic = st.selectbox(
        "Seleziona Strumento:",
        [
            "Rumore — Somma Sorgenti",
            "Rumore — LEX,8h Esposizione",
            "Rumore — Verifica DPI (SNR)",
            "Rumore — Attenuazione per Distanza",
            "Performance Level — EN ISO 13849",
            "Costi Energetici e Payback Efficientamento",
            "Protezione Fulmini (LPS)",
            "Antincendio — Rete Idranti/Naspi (UNI 10779)",
        ],
        key="sic_tool",
    )
    _render_fav_toggle("🔒  Sicurezza & Utilities", "sic_tool", tool_sic)

    if tool_sic == "Rumore — Somma Sorgenti":
        st.subheader("Somma Energetica Sorgenti Sonore (ISO 9612)")
        n_sorg = st.number_input("Numero sorgenti:", min_value=1, max_value=10, value=3, step=1, key="rum_n")
        livelli = []
        cols_rum = st.columns(int(n_sorg))
        for i in range(int(n_sorg)):
            with cols_rum[i]:
                lv = st.number_input(f"L{i+1} [dB]", value=85.0 - i*3, min_value=0.0, max_value=150.0, key=f"rum_l{i}")
                livelli.append(lv)
        if st.button("Calcola Livello Totale", key="rum_btn1"):
            try:
                r = rumore.somma_livelli_db(livelli)
                st.session_state["_rum_result"] = {"livelli": list(livelli), "res": r}
            except (ValueError, ZeroDivisionError) as e:
                st.session_state["_rum_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_rum_result")
        if rr:
            r = rr["res"]
            c1, c2, c3 = st.columns(3)
            c1.metric("L_tot", f"{r['L_tot_dB']:.1f} dB")
            c2.metric("L_max sorgente", f"{r['L_max_dB']:.1f} dB")
            c3.metric("Incremento", f"+{r['incremento_dB']:.1f} dB")
            st.info(f"Somma di {r['n_sorgenti']} sorgenti: il livello totale supera la sorgente dominante di {r['incremento_dB']:.1f} dB")
            _export_csv_button(
                "Rumore — Somma Sorgenti",
                {"Sorgenti [dB]": ", ".join(f"{l:.1f}" for l in rr["livelli"]),
                 "L totale [dB]": f"{r['L_tot_dB']:.1f}", "L max [dB]": f"{r['L_max_dB']:.1f}", "Incremento [dB]": f"{r['incremento_dB']:.1f}"},
                key="rum_export",
            )

    elif tool_sic == "Rumore — LEX,8h Esposizione":
        st.subheader("Livello Esposizione Giornaliero LEX,8h (D.Lgs 81/2008)")
        n_esp = st.number_input("Numero esposizioni giornaliere:", min_value=1, max_value=8, value=2, step=1, key="lex_n")
        t_list, L_list = [], []
        for i in range(int(n_esp)):
            c1, c2 = st.columns(2)
            with c1:
                t_i = st.number_input(f"Durata {i+1} [min]:", value=240.0 if i == 0 else 60.0, min_value=1.0, key=f"lex_t{i}")
            with c2:
                L_i = st.number_input(f"LAeq,{i+1} [dB(A)]:", value=88.0 if i == 0 else 75.0, min_value=40.0, max_value=140.0, key=f"lex_L{i}")
            t_list.append(t_i)
            L_list.append(L_i)
        if st.button("Calcola LEX,8h", key="lex_btn"):
            try:
                r = rumore.lex_8h(t_list, L_list)
                st.session_state["_lex_result"] = {"res": r}
            except (ValueError, ZeroDivisionError) as e:
                st.session_state["_lex_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_lex_result")
        if rr:
            r = rr["res"]
            colore = "error" if r["LEX_8h_dBA"] >= rumore.LEX_LIMITE_dB else ("warning" if r["LEX_8h_dBA"] >= rumore.LEX_SUPERIORE_dB else ("info" if r["LEX_8h_dBA"] >= rumore.LEX_INFERIORE_dB else "success"))
            getattr(st, colore)(f"LEX,8h = {r['LEX_8h_dBA']:.1f} dB(A)  —  {r['rischio']}")
            c1, c2, c3 = st.columns(3)
            c1.metric("LEX,8h", f"{r['LEX_8h_dBA']:.1f} dB(A)")
            c2.metric("Dose esposizione", f"{r['dose_pct']:.1f} %")
            c3.metric("DPI obbligatori", "SÌ" if r["dpi_obbligo"] else "NO")
            _barra_utilizzo(min(r["dose_pct"], 100), "Dose rispetto al limite 87 dB(A)")
            _export_csv_button(
                "Rumore — LEX,8h Esposizione",
                {"LEX,8h [dB(A)]": f"{r['LEX_8h_dBA']:.1f}", "Rischio": r["rischio"],
                 "Dose [%]": f"{r['dose_pct']:.1f}", "DPI obbligatori": "Sì" if r["dpi_obbligo"] else "No"},
                key="lex_export",
            )

    elif tool_sic == "Rumore — Verifica DPI (SNR)":
        st.subheader("Verifica Adeguatezza DPI — Metodo SNR (EN ISO 4869-2)")
        col1, col2 = st.columns(2)
        with col1:
            dpi_sel  = st.selectbox("DPI:", list(rumore.DPI_SNR.keys()), key="dpi_sel")
            SNR_val  = rumore.DPI_SNR[dpi_sel]
            st.info(f"SNR nominale: {SNR_val} dB")
        with col2:
            L_amb_dpi = st.number_input("Livello ambiente L_amb [dB(A)]:", value=95.0, min_value=40.0, max_value=140.0, key="dpi_Lamb")
        if st.button("Verifica DPI", key="dpi_btn"):
            try:
                r = rumore.attenuazione_dpi(SNR_val, L_amb_dpi)
                st.session_state["_dpi_result"] = {"dpi": dpi_sel, "SNR": SNR_val, "Lamb": L_amb_dpi, "res": r}
            except (ValueError, ZeroDivisionError) as e:
                st.session_state["_dpi_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_dpi_result")
        if rr:
            r = rr["res"]
            colore_dpi = "success" if r["protezione_adeguata"] else "error"
            getattr(st, colore_dpi)(f"L efficace sotto DPI: {r['L_eff_dBA']:.1f} dB(A)  —  {r['giudizio']}")
            c1, c2 = st.columns(2)
            c1.metric("L amb", f"{r['L_amb_dBA']:.1f} dB(A)")
            c2.metric("L eff. DPI", f"{r['L_eff_dBA']:.1f} dB(A)")
            _export_csv_button(
                "Rumore — Verifica DPI (SNR)",
                {"DPI": rr["dpi"], "SNR [dB]": rr["SNR"], "L ambiente [dB(A)]": rr["Lamb"],
                 "L efficace [dB(A)]": f"{r['L_eff_dBA']:.1f}", "Protezione adeguata": "Sì" if r["protezione_adeguata"] else "No"},
                key="dpi_export",
            )

    elif tool_sic == "Rumore — Attenuazione per Distanza":
        st.subheader("Attenuazione Geometrica (campo libero, sorgente puntuale)")
        col1, col2, col3 = st.columns(3)
        with col1:
            L_sorg  = st.number_input("L a distanza d1 [dB]:", value=95.0, min_value=0.0, key="att_L")
        with col2:
            d1_att  = st.number_input("d1 [m]:", value=1.0, min_value=0.01, key="att_d1")
        with col3:
            d2_att  = st.number_input("d2 [m]:", value=10.0, min_value=0.01, key="att_d2")
        if st.button("Calcola Attenuazione", key="att_btn"):
            try:
                r = rumore.attenuazione_distanza(L_sorg, d1_att, d2_att)
                st.session_state["_att_result"] = {"L": L_sorg, "d1": d1_att, "d2": d2_att, "res": r}
            except (ValueError, ZeroDivisionError) as e:
                st.session_state["_att_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_att_result")
        if rr:
            r = rr["res"]
            L_sorg, d1_att, d2_att = rr["L"], rr["d1"], rr["d2"]
            st.success(f"L a {d2_att} m = {r['L_d2_dB']:.1f} dB  (attenuazione: -{r['delta_dB']:.1f} dB)")
            if _PLOTLY:
                import numpy as _np
                d_arr = [d1_att * (d2_att/d1_att)**(i/49) for i in range(50)]
                L_arr = [L_sorg - 20*_np.log10(d/d1_att) for d in d_arr]
                fig_att = go.Figure()
                fig_att.add_trace(go.Scatter(x=d_arr, y=L_arr, mode="lines", name="L(d)", line=dict(color="#FF5722", width=2)))
                fig_att.add_hline(y=rumore.LEX_LIMITE_dB, line_dash="dash", line_color="red", annotation_text="Limite 87 dB(A)")
                fig_att.add_hline(y=rumore.LEX_SUPERIORE_dB, line_dash="dot", line_color="orange", annotation_text="Val. sup. 85 dB(A)")
                fig_att.update_layout(title="Attenuazione per distanza", xaxis_title="Distanza [m]", yaxis_title="L [dB]", xaxis_type="log", height=320)
                st.plotly_chart(fig_att, use_container_width=True)
            _export_csv_button(
                "Rumore — Attenuazione per Distanza",
                {"L a d1 [dB]": L_sorg, "d1 [m]": d1_att, "d2 [m]": d2_att,
                 "L a d2 [dB]": f"{r['L_d2_dB']:.1f}", "Attenuazione [dB]": f"{r['delta_dB']:.1f}"},
                key="att_export",
            )

    elif tool_sic == "Performance Level — EN ISO 13849":
        st.subheader("Performance Level (PL) e SIL — EN ISO 13849-1")
        sub_pl = st.radio("Calcolo:", ["Calcola PL da parametri", "MTTFd da B10d", "Verifica PLr"], horizontal=True, key="pl_sub")
        if sub_pl == "Calcola PL da parametri":
            col1, col2 = st.columns(2)
            with col1:
                MTTFd_pl = st.number_input(
                    "MTTFd canale [anni]:", value=30.0, min_value=0.1, max_value=100.0, key="pl_mttfd",
                    help="Tempo medio al guasto pericoloso di un canale (EN ISO 13849-1, max 100 anni per "
                         "canale). Si ricava dal B10d del componente (vedi tab 'MTTFd da B10d') o dal datasheet.",
                )
                DCavg_pl = st.slider(
                    "DCavg [%]:", 0, 100, 90, key="pl_dc",
                    help="Copertura diagnostica media del sistema (EN ISO 13849-1, Annex E): percentuale "
                         "di guasti pericolosi rilevati dal sistema di diagnosi/monitoraggio.",
                )
            with col2:
                cat_pl = st.selectbox(
                    "Categoria architetturale:", ["B", "1", "2", "3", "4"], index=3, key="pl_cat",
                    help="Categoria EN ISO 13849-1: B/1 = singolo canale, 2 = singolo canale con test "
                         "periodico, 3/4 = ridondanza con (4: anche) rilevamento guasto singolo.",
                )
            if st.button("Calcola PL", key="pl_btn1"):
                try:
                    r = pl_iso.calcola_PL(MTTFd_pl, DCavg_pl, cat_pl)
                    st.session_state["_pl1_result"] = {"MTTFd": MTTFd_pl, "DCavg": DCavg_pl, "cat": cat_pl, "res": r}
                except ValueError as e:
                    st.session_state["_pl1_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_pl1_result")
            if rr:
                r = rr["res"]
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Performance Level", f"PL {r['PL']}")
                c2.metric("SIL equivalente", r["SIL"])
                c3.metric("PFHd [1/h]", f"{r['PFHd_1_h']:.0e}")
                c4.metric("MTTFd classe", r["MTTFd_classe"])
                st.info(f"Categoria {r['categoria']}: {r['descrizione_categoria']}")
                st.caption(f"DC classe: {r['DC_classe']}  |  MTTFd: {r['MTTFd_anni']} anni ({r['MTTFd_classe']})")
                _export_csv_button(
                    "Performance Level — Calcolo PL",
                    {"MTTFd [anni]": rr["MTTFd"], "DCavg [%]": rr["DCavg"], "Categoria": rr["cat"],
                     "PL": r["PL"], "SIL": r["SIL"], "PFHd [1/h]": f"{r['PFHd_1_h']:.0e}"},
                    key="pl1_export",
                )
        elif sub_pl == "MTTFd da B10d":
            col1, col2 = st.columns(2)
            with col1:
                B10d_pl = st.number_input(
                    "B10d [cicli]:", value=2000000.0, min_value=1000.0, key="pl_B10d",
                    help="Numero di cicli dopo i quali il 10% dei componenti si guasta in modo "
                         "pericoloso (dato del costruttore, tipico per componenti elettromeccanici/pneumatici).",
                )
            with col2:
                n_op = st.number_input("Operazioni/anno:", value=52000.0, min_value=1.0, key="pl_nop",
                                        help="Es. 1 op/giorno × 250gg = 250; 200op/giorno × 250gg = 50000")
            if st.button("Calcola MTTFd", key="pl_btn2"):
                try:
                    r = pl_iso.MTTFd_da_B10d(B10d_pl, n_op)
                    st.session_state["_pl2_result"] = {"B10d": B10d_pl, "nop": n_op, "res": r}
                except ValueError as e:
                    st.session_state["_pl2_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_pl2_result")
            if rr:
                r = rr["res"]
                st.success(f"MTTFd = **{r['MTTFd_anni']:.1f} anni** ({r['MTTFd_classe']})")
                if r["nota"]:
                    st.warning(r["nota"])
                _export_csv_button(
                    "Performance Level — MTTFd da B10d",
                    {"B10d [cicli]": rr["B10d"], "Operazioni/anno": rr["nop"], "MTTFd [anni]": f"{r['MTTFd_anni']:.1f}", "Classe": r["MTTFd_classe"]},
                    key="pl2_export",
                )
        else:
            col1, col2 = st.columns(2)
            with col1:
                PL_rag = st.selectbox(
                    "PL raggiunto:", ["a", "b", "c", "d", "e"], index=3, key="pl_rag",
                    help="Performance Level effettivamente ottenuto dalla funzione di sicurezza progettata.",
                )
            with col2:
                PLr_req = st.selectbox(
                    "PLr richiesto:", ["a", "b", "c", "d", "e"], index=3, key="pl_req",
                    help="Performance Level richiesto (PLr), determinato dalla valutazione del rischio "
                         "secondo EN ISO 13849-1 (grafico del rischio, Annex A).",
                )
            if st.button("Verifica PLr", key="pl_btn3"):
                try:
                    r = pl_iso.verifica_PLr(PL_rag, PLr_req)
                    st.session_state["_pl3_result"] = {"PL": PL_rag, "PLr": PLr_req, "res": r}
                except ValueError as e:
                    st.session_state["_pl3_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_pl3_result")
            if rr:
                r = rr["res"]
                (st.success if r["conforme"] else st.error)(r["giudizio"])
                st.caption(f"SIL raggiunto: {r['SIL_raggiunto']}")
                _export_csv_button(
                    "Performance Level — Verifica PLr",
                    {"PL raggiunto": rr["PL"], "PLr richiesto": rr["PLr"], "Conforme": "Sì" if r["conforme"] else "No", "SIL raggiunto": r["SIL_raggiunto"]},
                    key="pl3_export",
                )

    elif tool_sic == "Costi Energetici e Payback Efficientamento":
        st.subheader("Costi energetici e tempo di ritorno di un efficientamento")
        modo_cen = st.radio("Modalità:",
                            ["Confronto potenze assorbite", "Sostituzione motore (rendimenti IE)"],
                            horizontal=True, key="cen_modo")
        col1, col2 = st.columns(2)
        with col1:
            ore_cen = st.number_input("Ore di funzionamento/anno [h]:", value=6000.0, min_value=1.0, max_value=8760.0, key="cen_ore")
            tariffa_cen = st.number_input("Tariffa energia [€/kWh]:", value=0.22, min_value=0.0, format="%.4f", key="cen_tariffa")
        with col2:
            extra_cen = st.number_input("Sovracosto soluzione efficiente [€]:", value=600.0, min_value=0.0, key="cen_extra")
            co2_cen = st.number_input("Fattore CO₂ [kg/kWh]:", value=cen.FATTORE_CO2_KG_KWH_DEFAULT, min_value=0.0, format="%.3f", key="cen_co2")

        if modo_cen == "Confronto potenze assorbite":
            c1, c2 = st.columns(2)
            with c1:
                p_prima = st.number_input("Potenza assorbita ATTUALE [kW]:", value=24.5, min_value=0.0, key="cen_pprima")
            with c2:
                p_dopo = st.number_input("Potenza assorbita NUOVA [kW]:", value=23.7, min_value=0.0, key="cen_pdopo")
            calcola_cen = st.button("Calcola risparmio", key="cen_btn1")
            if calcola_cen:
                try:
                    r = cen.confronto_efficientamento(p_prima, p_dopo, ore_cen, tariffa_cen, extra_cen, co2_cen)
                    r["_intestazione"] = {"Modalità": "Confronto potenze", "P attuale [kW]": p_prima, "P nuova [kW]": p_dopo}
                    st.session_state["_cen_result"] = r
                except ValueError as e:
                    st.session_state["_cen_result"] = None
                    st.error(str(e))
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                pmecc_cen = st.number_input("Potenza all'albero [kW]:", value=22.0, min_value=0.01, key="cen_pmecc")
            with c2:
                eta1_cen = st.number_input("Rendimento attuale [%]:", value=89.8, min_value=1.0, max_value=99.9, key="cen_eta1")
            with c3:
                eta2_cen = st.number_input("Rendimento nuovo [%]:", value=93.0, min_value=1.0, max_value=99.9, key="cen_eta2")
            calcola_cen = st.button("Calcola risparmio", key="cen_btn2")
            if calcola_cen:
                try:
                    r = cen.confronto_motore_ie(pmecc_cen, eta1_cen, eta2_cen, ore_cen, tariffa_cen, extra_cen, co2_cen)
                    r["_intestazione"] = {"Modalità": "Sostituzione motore", "P albero [kW]": pmecc_cen,
                                          "η attuale [%]": eta1_cen, "η nuovo [%]": eta2_cen}
                    st.session_state["_cen_result"] = r
                except ValueError as e:
                    st.session_state["_cen_result"] = None
                    st.error(str(e))

        rr = st.session_state.get("_cen_result")
        if rr:
            if rr["conveniente"]:
                pb = rr["payback_anni"]
                pb_txt = f"{pb:.2f} anni ({pb*12:.0f} mesi)" if pb > 0 else "immediato (nessun sovracosto)"
                st.success(f"Risparmio: **{rr['risparmio_eur_anno']:.0f} €/anno**  |  Tempo di ritorno: **{pb_txt}**")
            else:
                st.error("La soluzione 'nuova' non genera risparmio: assorbe più o uguale energia.")
            c1, c2, c3 = st.columns(3)
            c1.metric("Energia risparmiata", f"{rr['risparmio_kWh_anno']:,.0f} kWh/anno")
            c2.metric("Costo evitato", f"{rr['risparmio_eur_anno']:,.0f} €/anno")
            c3.metric("CO₂ evitata", f"{rr['risparmio_co2_kg_anno']:,.0f} kg/anno")
            with st.expander("Dettaglio costi annui"):
                st.write(f"Costo attuale: {rr['costo_prima_eur']:,.0f} €/anno  ({rr['energia_prima_kWh']:,.0f} kWh)")
                st.write(f"Costo nuovo: {rr['costo_dopo_eur']:,.0f} €/anno  ({rr['energia_dopo_kWh']:,.0f} kWh)")
                if "P_assorbita_prima_kW" in rr:
                    st.write(f"Potenza assorbita: {rr['P_assorbita_prima_kW']:.2f} kW → {rr['P_assorbita_dopo_kW']:.2f} kW")
            dati_cen = dict(rr["_intestazione"])
            dati_cen.update({
                "Ore/anno": ore_cen, "Tariffa [€/kWh]": tariffa_cen, "Sovracosto [€]": extra_cen,
                "Risparmio [kWh/anno]": f"{rr['risparmio_kWh_anno']:.0f}",
                "Risparmio [€/anno]": f"{rr['risparmio_eur_anno']:.0f}",
                "CO2 evitata [kg/anno]": f"{rr['risparmio_co2_kg_anno']:.0f}",
                "Payback [anni]": "∞" if rr["payback_anni"] == float("inf") else f"{rr['payback_anni']:.2f}",
            })
            _export_csv_button("Costi Energetici e Payback", dati_cen, key="cen_export")

    elif tool_sic == "Protezione Fulmini (LPS)":
        st.subheader("Protezione contro i fulmini — Valutazione semplificata (IEC 62305)")
        st.caption(
            "Valutazione semplificata Nd/Nc: confronta la frequenza di fulmini prevista sulla "
            "struttura con quella tollerabile. Per un'analisi del rischio completa (perdite di "
            "vite umane, servizio pubblico, patrimonio culturale, ecc.) fare riferimento a "
            "IEC 62305-2 con un professionista abilitato."
        )
        col1, col2, col3 = st.columns(3)
        with col1:
            L_lps = st.number_input("Lunghezza struttura [m]:", value=20.0, min_value=0.1, key="lps_L")
            W_lps = st.number_input("Larghezza struttura [m]:", value=15.0, min_value=0.1, key="lps_W")
        with col2:
            H_lps = st.number_input("Altezza struttura [m]:", value=10.0, min_value=0.1, key="lps_H")
            Ng_lps = st.number_input("Densità fulmini a terra Ng [fulmini/km²/anno]:", value=2.0, min_value=0.0, step=0.1, key="lps_Ng",
                                      help="Da mappe di ceraunicità della zona; in Italia tipicamente 1-4.")
        with col3:
            Cd_lps = st.selectbox(
                "Fattore di ubicazione Cd:",
                [1.0, 0.5, 0.25, 2.0], key="lps_Cd",
                format_func=lambda v: {
                    1.0: "1 — struttura isolata in piano", 0.5: "0.5 — circondata da strutture più basse",
                    0.25: "0.25 — circondata da strutture della stessa altezza o più alte",
                    2.0: "2 — struttura isolata su altura",
                }[v],
            )
            Nc_lps = st.number_input("Frequenza tollerabile Nc [fulmini/anno]:", value=0.001, min_value=0.0001, step=0.0001, format="%.4f", key="lps_Nc",
                                      help="Valore di riferimento 10⁻³ per strutture ordinarie; un'analisi del rischio completa lo calcola caso per caso.")

        if st.button("Valuta", key="lps_btn"):
            try:
                r = fulmini.valutazione_lps(L_lps, W_lps, H_lps, Ng_lps, Cd_lps, Nc_lps)
                st.session_state["_lps_result"] = r
            except ValueError as e:
                st.session_state["_lps_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_lps_result")
        if rr:
            c1, c2 = st.columns(2)
            c1.metric("Area di raccolta equivalente", f"{rr['Ad_m2']:,.0f} m²")
            c2.metric("Frequenza fulmini prevista Nd", f"{rr['Nd_fulmini_anno']:.5f} /anno")
            if rr["protezione_necessaria"]:
                st.warning(f"Protezione necessaria: Nd ({rr['Nd_fulmini_anno']:.5f}) > Nc ({rr['Nc_fulmini_anno']:.5f}).")
                st.success(f"Livello di protezione minimo: **LPL {rr['livello']}** "
                           f"(efficienza richiesta {rr['efficienza_richiesta_pct']:.1f}%)")
                if not rr["raggiungibile_con_lps"]:
                    st.error("Efficienza richiesta oltre il massimo garantito da un solo LPS (LPL I = 98%): "
                             "servono misure di protezione aggiuntive (SPD, schermature, ecc.).")
                c3, c4, c5 = st.columns(3)
                c3.metric("Raggio sfera rotolante", f"{rr['raggio_sfera_rotolante_m']} m")
                c4.metric("Lato maglia captatori", f"{rr['lato_maglia_m']} m")
                c5.metric("Distanza max calate", f"{rr['distanza_max_calate_m']} m")
            else:
                st.info(f"Protezione non obbligatoria: Nd ({rr['Nd_fulmini_anno']:.5f}) ≤ Nc ({rr['Nc_fulmini_anno']:.5f}).")
            _export_csv_button(
                "Protezione Fulmini — Valutazione LPS",
                {
                    "Ad [m²]": f"{rr['Ad_m2']:.1f}", "Nd [fulmini/anno]": f"{rr['Nd_fulmini_anno']:.5f}",
                    "Nc [fulmini/anno]": f"{rr['Nc_fulmini_anno']:.5f}",
                    "Protezione necessaria": "Sì" if rr["protezione_necessaria"] else "No",
                    "Livello LPL": rr.get("livello", "-"),
                },
                key="lps_export",
            )

    elif tool_sic == "Antincendio — Rete Idranti/Naspi (UNI 10779)":
        st.subheader("Antincendio — Rete idranti/naspi (UNI 10779)")
        st.caption(
            "Valori tipici indicativi (UNI 10779): portata totale di rete per livello di rischio, "
            "volume di riserva idrica e prevalenza minima della pompa. Per il progetto esecutivo "
            "fare sempre riferimento a un professionista abilitato e alla norma vigente."
        )
        sub_ai = st.radio("Calcolo:", ["Dimensionamento completo", "Numero indicativo protezioni per area"], horizontal=True, key="ai_sub")

        if sub_ai == "Dimensionamento completo":
            col1, col2, col3 = st.columns(3)
            with col1:
                tipo_ai = st.selectbox("Tipo di protezione:", list(antincendio.PARAMETRI_PROTEZIONE.keys()), key="ai_tipo")
                liv_ai = st.selectbox("Livello di rischio:", [1, 2, 3], key="ai_liv",
                                       format_func=lambda v: {1: "1 — basso", 2: "2 — medio", 3: "3 — alto"}[v])
            with col2:
                H_ai = st.number_input("Altezza geodetica riserva→apparecchio più sfavorito [m]:", value=15.0, min_value=0.0, key="ai_H")
                perd_ai = st.number_input("Perdite di carico di rete stimate [bar]:", value=0.3, min_value=0.0, step=0.05, key="ai_perd")
            with col3:
                marg_ai = st.number_input("Margine di sicurezza [bar]:", value=0.5, min_value=0.0, step=0.05, key="ai_marg")
            if st.button("Dimensiona Rete Antincendio", key="ai_btn1"):
                try:
                    r = antincendio.dimensionamento_completo(tipo_ai, liv_ai, H_ai, perd_ai, marg_ai)
                    st.session_state["_ai1_result"] = r
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_ai1_result"] = None
                    st.error(str(e))

            r = st.session_state.get("_ai1_result")
            if r:
                c1, c2, c3 = st.columns(3)
                c1.metric("Portata totale rete", f"{r['Q_tot_lmin']:.0f} L/min")
                c2.metric("Volume riserva idrica", f"{r['V_m3']:.1f} m³")
                c3.metric("Prevalenza minima pompa", f"{r['H_pompa_bar']:.2f} bar")
                st.info(f"{r['n_contemporanei']} apparecchi contemporanei ({r['Q_singola_lmin']:.0f} L/min cad.) "
                        f"per {r['durata_min']} min — pressione minima {r['P_min_bar']:.1f} bar all'apparecchio più sfavorito.")
                _export_csv_button(
                    "Antincendio — Dimensionamento rete",
                    {"Tipo protezione": tipo_ai, "Livello rischio": liv_ai,
                     "Portata totale [L/min]": f"{r['Q_tot_lmin']:.0f}", "Volume riserva [m³]": f"{r['V_m3']:.1f}",
                     "Prevalenza pompa [bar]": f"{r['H_pompa_bar']:.2f}"},
                    key="ai1_export",
                )

        else:
            col1, col2 = st.columns(2)
            with col1:
                area_ai = st.number_input("Area da proteggere [m²]:", value=2000.0, min_value=1.0, key="ai_area")
            with col2:
                inter_ai = st.number_input("Interasse tipico tra apparecchi [m]:", value=45.0, min_value=1.0, key="ai_inter",
                                            help="Tipico 45m per naspi/idranti UNI45 interni, fino a 60m per idranti UNI70 esterni.")
            if st.button("Stima Numero Protezioni", key="ai_btn2"):
                try:
                    r = antincendio.numero_protezioni_area(area_ai, inter_ai)
                    st.session_state["_ai2_result"] = r
                except (ValueError, ZeroDivisionError) as e:
                    st.session_state["_ai2_result"] = None
                    st.error(str(e))

            r = st.session_state.get("_ai2_result")
            if r:
                st.metric("Numero indicativo di apparecchi", f"{r['n_protezioni_stimato']}")
                st.caption("Stima grossolana a griglia quadrata: non sostituisce la verifica del raggio d'azione reale sulla planimetria.")
                _export_csv_button(
                    "Antincendio — Numero protezioni per area",
                    {"Area [m²]": area_ai, "Interasse [m]": inter_ai, "N. protezioni stimato": r["n_protezioni_stimato"]},
                    key="ai2_export",
                )


elif categoria == "🎛️  Mark VI/VIe & ToolboxST":
    _card_open("markvie", "🎛️ GE Mark VI/VIe & ToolboxST", "GEH-6721")
    st.caption("Fonti: GEH-6721 Vol. I (System Guide — architettura) e GEH-6721G Vol. II (System Guide — schede I/O), GE Vernova / GE Energy, documentazione pubblica.")
    tool_mv = st.selectbox(
        "Seleziona Strumento:",
        [
            "Riferimento — Schede I/O",
            "Riferimento — Architetture di Ridondanza",
            "Riferimento — Terminologia ControlST/ToolboxST",
            "Riferimento — Suite ControlST / WorkstationST",
            "Riferimento — Troubleshooting (sintomo → manuale)",
            "Calcolo — Scalatura Canale PAIC",
            "Calcolo — Voting TMR (2oo3)",
            "Calcolo — MTBF Serie (Simplex)",
            "Calcolo — Disponibilità TMR 2oo3",
            "Calcolo — Corrente Assorbita TBCI",
            "Calcolo — Derating Relè TRLYH1x",
            "Calcolo — RTD Pt100/Pt1000 (IEC 60751)",
            "Calcolo — Termocoppia (ITS-90)",
            "Calcolo — Diagnostica Loop 4–20 mA (NE43)",
            "Calcolo — Velocità / Sovravelocità Turbina",
            "Checklist — Commissioning Mark VI/VIe",
            "Calcolo — Loading Rete IONet",
        ],
        key="mv_tool",
    )
    _render_fav_toggle("🎛️  Mark VI/VIe & ToolboxST", "mv_tool", tool_mv)

    if tool_mv == "Riferimento — Schede I/O":
        st.subheader("Tabella di riferimento schede I/O Mark VIe (GEH-6721G Vol. II)")
        filtro = st.text_input("Filtra per sigla o funzione:", key="mv_filtro")
        rows = []
        for sigla, info in mv.SCHEDE_IO.items():
            riga = f"{sigla} {info['nome']} {info['funzione']}".lower()
            if filtro and filtro.lower() not in riga:
                continue
            rows.append({"Sigla": sigla, "Nome": info["nome"], "Funzione": info["funzione"], "Canali": info["canali"]})
        st.table(rows)
        st.caption(f"{len(rows)} schede mostrate su {len(mv.SCHEDE_IO)} totali.")

    elif tool_mv == "Riferimento — Architetture di Ridondanza":
        st.subheader("Architetture di ridondanza controllore (GEH-6721 Vol. I §1.6)")
        for nome, info in mv.ARCHITETTURE_RIDONDANZA.items():
            with st.expander(f"{nome} — {info['controllori']} controllori, {info['reti_ionet']} IONet"):
                st.write(info["descrizione"])
        st.subheader("Opzioni di ridondanza I/O")
        for nome, desc in mv.RIDONDANZA_IO.items():
            st.markdown(f"- **{nome}**: {desc}")

    elif tool_mv == "Riferimento — Terminologia ControlST/ToolboxST":
        st.subheader("Terminologia ControlST / ToolboxST")
        for termine, desc in mv.TERMINOLOGIA_TOOLBOXST.items():
            st.markdown(f"**{termine}** — {desc}")

        st.markdown("---")
        st.subheader("Concetti di programmazione ToolboxST")
        st.caption("Fonte: GEI-100746 ControlST Release Notes — riferimenti di capitolo al manuale GEH-6700 "
                   "'ToolboxST User Guide for Mark VIe' (manuale stesso non disponibile in questa raccolta).")
        for termine, desc in mv.CONCETTI_PROGRAMMAZIONE_TOOLBOXST.items():
            st.markdown(f"**{termine}** — {desc}")

        st.markdown("---")
        st.subheader("Struttura del manuale GEH-6700 (capitoli confermati)")
        for cap, contenuto in mv.STRUTTURA_GEH6700_TOOLBOXST.items():
            st.markdown(f"- **{cap}**: {contenuto}")

    elif tool_mv == "Riferimento — Suite ControlST / WorkstationST":
        st.subheader("Suite software ControlST / WorkstationST — componenti")
        st.caption("Fonti: manuali GE Vernova / GE Energy presenti nella cartella Documentation/ "
                   "(codice GEH/GEI/GHT + revisione indicati per ciascun componente). "
                   "WorkstationST è la piattaforma software lato operatore della famiglia Mark VIe.")

        filtro_sw = st.text_input("Filtra per componente, categoria o funzione:", key="mv_sw_filtro")
        per_cat = mv.componenti_per_categoria()
        n_mostrati = 0
        for categoria, componenti in per_cat.items():
            righe_cat = []
            for nome in componenti:
                ref = mv.documento_componente(nome)
                blob = f"{nome} {categoria} {ref['funzione']} {ref['documento_rev']} {ref['titolo']}".lower()
                if filtro_sw and filtro_sw.lower() not in blob:
                    continue
                righe_cat.append(ref)
            if not righe_cat:
                continue
            st.markdown(f"#### {categoria}")
            for ref in righe_cat:
                st.markdown(
                    f"**{ref['componente']}** — {ref['funzione']}  \n"
                    f"<small>📄 {ref['documento_rev']} · {ref['titolo']} · {ref['pagine']} pag.</small>",
                    unsafe_allow_html=True,
                )
                if ref["sezioni"]:
                    sez = "  ·  ".join(f"{titolo} (p. {pag})" for titolo, pag in ref["sezioni"])
                    st.markdown(f"<small>🔖 {sez}</small>", unsafe_allow_html=True)
                n_mostrati += 1
        st.caption(f"{n_mostrati} componenti mostrati su {len(mv.SUITE_CONTROLST_WORKSTATIONST)} totali.")

        st.markdown("---")
        with st.expander(f"📚 Indice documenti disponibili nella raccolta ({len(mv.DOCUMENTI_CONTROLST)} manuali)"):
            doc_rows = []
            for code, d in mv.DOCUMENTI_CONTROLST.items():
                sigla = f"{code}{d['rev']}" if d["rev"] not in ("-", "") else code
                doc_rows.append({"Documento": sigla, "Titolo": d["titolo"], "Pagine": d["pagine"]})
            st.table(doc_rows)

    elif tool_mv == "Riferimento — Troubleshooting (sintomo → manuale)":
        st.subheader("Matrice di troubleshooting ControlST / WorkstationST")
        st.caption("Ogni voce rimanda alla sezione e pagina del manuale presente nella cartella Documentation/.")
        filtro_ts = st.text_input("Filtra per sintomo, componente o area:", key="mv_ts_filtro")
        voci = mv.cerca_troubleshooting(filtro_ts)
        for v in voci:
            doc = mv.DOCUMENTI_CONTROLST.get(v["doc"], {})
            rev = f"{v['doc']}{doc.get('rev','')}" if doc.get("rev") not in (None, "-", "") else v["doc"]
            with st.expander(f"⚠️ {v['sintomo']}"):
                st.markdown(f"**Componente:** {v['componente']}")
                st.markdown(f"**Dove guardare:** {v['dove']}")
                st.markdown(f"<small>📄 {rev} · {v['sezione']} (p. {v['pagina']})</small>", unsafe_allow_html=True)
        st.caption(f"{len(voci)} voci su {len(mv.TROUBLESHOOTING)} totali.")

    elif tool_mv == "Calcolo — Scalatura Canale PAIC":
        st.subheader("Scalatura canale analogico PAIC (GEH-6721G p.43)")
        col1, col2 = st.columns(2)
        with col1:
            span_mv = st.selectbox("Span canale:", list(mv.PAIC_SPAN.keys()), key="mv_span")
        with col2:
            pct_mv = st.slider("Percentuale di scala [%]:", 0.0, 100.0, 50.0, step=0.1, key="mv_pct")
        if st.button("Calcola Scalatura", key="mv_btn1"):
            try:
                r = mv.scala_paic(pct_mv, span_mv)
                st.session_state["_mvpaic_result"] = {"span": span_mv, "pct": pct_mv, "res": r}
            except ValueError as e:
                st.session_state["_mvpaic_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_mvpaic_result")
        if rr:
            r = rr["res"]
            c1, c2, c3 = st.columns(3)
            c1.metric("Valore", f"{r['valore']:.4f} {r['unita']}")
            c2.metric("Risoluzione (LSB)", f"{r['lsb']:.6f} {r['unita']}")
            c3.metric("Accuratezza ±", f"{r['accuratezza_assoluta']:.4f} {r['unita']}")
            st.caption(f"PAIC: convertitore A/D a {mv.PAIC_RISOLUZIONE_BIT} bit, accuratezza {mv.PAIC_ACCURATEZZA_PCT_FS}% FS.")
            _export_csv_button(
                "Mark VIe — Scalatura Canale PAIC",
                {"Span": rr["span"], "Percentuale [%]": rr["pct"], "Valore": f"{r['valore']:.4f} {r['unita']}", "LSB": f"{r['lsb']:.6f}"},
                key="mvpaic_export",
            )

    elif tool_mv == "Calcolo — Voting TMR (2oo3)":
        st.subheader("Voting a 2 su 3 (mediano) per ingressi TMR fanned/voted")
        col1, col2, col3 = st.columns(3)
        with col1:
            v1_mv = st.number_input("Valore canale R:", value=100.0, key="mv_v1")
        with col2:
            v2_mv = st.number_input("Valore canale S:", value=100.2, key="mv_v2")
        with col3:
            v3_mv = st.number_input("Valore canale T:", value=99.7, key="mv_v3")
        tol_mv = st.number_input("Tolleranza diagnostica (stesse unità):", value=1.0, min_value=0.0, key="mv_tol")
        if st.button("Calcola Voting", key="mv_btn2"):
            r = mv.voting_tmr_mediano(v1_mv, v2_mv, v3_mv, tol_mv)
            st.session_state["_mvvote_result"] = {"v1": v1_mv, "v2": v2_mv, "v3": v3_mv, "tol": tol_mv, "res": r}

        rr = st.session_state.get("_mvvote_result")
        if rr:
            r = rr["res"]
            st.success(f"Valore votato (mediano): **{r['valore_votato']:.4f}**")
            c1, c2, c3 = st.columns(3)
            c1.metric("Scarto R", f"{r['scarti']['v1']:.4f}")
            c2.metric("Scarto S", f"{r['scarti']['v2']:.4f}")
            c3.metric("Scarto T", f"{r['scarti']['v3']:.4f}")
            if r["canali_sospetti"]:
                st.error(f"Canali fuori tolleranza: {', '.join(r['canali_sospetti'])}")
            else:
                st.info("Tutti i canali entro tolleranza.")
            _export_csv_button(
                "Mark VIe — Voting TMR (2oo3)",
                {"Canale R": rr["v1"], "Canale S": rr["v2"], "Canale T": rr["v3"], "Tolleranza": rr["tol"],
                 "Valore votato": f"{r['valore_votato']:.4f}", "Canali sospetti": ", ".join(r["canali_sospetti"]) if r["canali_sospetti"] else "nessuno"},
                key="mvvote_export",
            )

    elif tool_mv == "Calcolo — MTBF Serie (Simplex)":
        st.subheader("MTBF risultante di componenti in serie (architettura simplex)")
        n_mtbf = st.number_input("Numero componenti:", min_value=2, max_value=10, value=3, step=1, key="mv_nmtbf")
        mtbf_vals = []
        cols_mtbf = st.columns(int(n_mtbf))
        for i in range(int(n_mtbf)):
            with cols_mtbf[i]:
                m = st.number_input(f"MTBF #{i+1} [anni]:", value=50.0, min_value=0.1, key=f"mv_mtbf{i}")
                mtbf_vals.append(m)
        if st.button("Calcola MTBF Sistema", key="mv_btn3"):
            try:
                r = mv.mtbf_serie(mtbf_vals)
                st.session_state["_mvmtbf_result"] = {"vals": list(mtbf_vals), "res": r}
            except ValueError as e:
                st.session_state["_mvmtbf_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_mvmtbf_result")
        if rr:
            r = rr["res"]
            st.success(f"MTBF sistema (serie): **{r['MTBF_sistema_anni']:.2f} anni**")
            _export_csv_button(
                "Mark VIe — MTBF Serie",
                {"MTBF componenti [anni]": ", ".join(f"{v:.1f}" for v in rr["vals"]), "MTBF sistema [anni]": f"{r['MTBF_sistema_anni']:.2f}"},
                key="mvmtbf_export",
            )

    elif tool_mv == "Calcolo — Disponibilità TMR 2oo3":
        st.subheader("Stima semplificata disponibilità TMR 2oo3")
        st.caption("Modello didattico (k-su-n) — il calcolo certificato IEC 61508 richiede lo strumento Exida exSILentia (GEH-6721 Vol. I §1.7.1).")
        col1, col2 = st.columns(2)
        with col1:
            mtbf_can = st.number_input("MTBF canale singolo [anni]:", value=50.0, min_value=0.1, key="mv_mtbfcan")
        with col2:
            mttr_mv = st.number_input("MTTR [ore]:", value=4.0, min_value=0.1, key="mv_mttr")
        if st.button("Calcola Disponibilità TMR", key="mv_btn4"):
            try:
                r = mv.disponibilita_tmr_2oo3(mtbf_can, mttr_mv)
                st.session_state["_mvtmr_result"] = {"mtbf": mtbf_can, "mttr": mttr_mv, "res": r}
            except ValueError as e:
                st.session_state["_mvtmr_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_mvtmr_result")
        if rr:
            r = rr["res"]
            c1, c2 = st.columns(2)
            c1.metric("MTBF sistema TMR", f"{r['MTBF_sistema_TMR_anni']:,.0f} anni")
            c2.metric("Fattore miglioramento", f"×{r['fattore_miglioramento']:,.0f}")
            st.caption(f"Indisponibilità canale: {r['indisponibilita_canale']:.2e}  |  Indisponibilità sistema TMR: {r['indisponibilita_sistema_TMR']:.2e}")
            _export_csv_button(
                "Mark VIe — Disponibilità TMR 2oo3",
                {"MTBF canale [anni]": rr["mtbf"], "MTTR [ore]": rr["mttr"],
                 "MTBF sistema TMR [anni]": f"{r['MTBF_sistema_TMR_anni']:.0f}", "Fattore miglioramento": f"{r['fattore_miglioramento']:.0f}"},
                key="mvtmr_export",
            )

    elif tool_mv == "Calcolo — Corrente Assorbita TBCI":
        st.subheader("Corrente e potenza assorbita scheda TBCI (24 canali contatto)")
        col1, col2 = st.columns(2)
        with col1:
            tipo_tbci = st.selectbox("Tipo eccitazione:", list(mv.TBCI_SPECS.keys()), key="mv_tbci_tipo")
        with col2:
            n_alta_tbci = st.number_input("Circuiti a corrente elevata:", value=3, min_value=0, max_value=24, key="mv_tbci_nalta")
        n_norm_tbci = st.number_input("Circuiti a corrente normale:", value=21, min_value=0, max_value=24, key="mv_tbci_nnorm")
        if st.button("Calcola Corrente TBCI", key="mv_btn5"):
            try:
                r = mv.corrente_assorbita_tbci(tipo_tbci, int(n_norm_tbci), int(n_alta_tbci))
                st.session_state["_mvtbci_result"] = {"tipo": tipo_tbci, "nnorm": int(n_norm_tbci), "nalta": int(n_alta_tbci), "res": r}
            except ValueError as e:
                st.session_state["_mvtbci_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_mvtbci_result")
        if rr:
            r = rr["res"]
            c1, c2, c3 = st.columns(3)
            c1.metric("Corrente totale", f"{r['I_totale_mA']:.1f} mA")
            c2.metric("Potenza totale", f"{r['P_totale_W']:.2f} W")
            c3.metric("Circuiti totali", r["n_circuiti_totali"])
            _export_csv_button(
                "Mark VIe — Corrente Assorbita TBCI",
                {"Tipo eccitazione": rr["tipo"], "Circuiti normali": rr["nnorm"], "Circuiti elevati": rr["nalta"],
                 "Corrente totale [mA]": f"{r['I_totale_mA']:.1f}", "Potenza totale [W]": f"{r['P_totale_W']:.2f}"},
                key="mvtbci_export",
            )

    elif tool_mv == "Calcolo — Derating Relè TRLYH1x":
        st.subheader("Derating corrente relè TRLYH1x vs temperatura ambiente")
        col1, col2 = st.columns(2)
        with col1:
            tipo_trly = st.selectbox("Tipo relè:", list(mv.TRLY_DERATING.keys()), key="mv_trly_tipo")
        with col2:
            T_trly = st.slider("Temperatura ambiente [°C]:", -30, 65, 45, key="mv_trly_T")
        if st.button("Calcola Derating", key="mv_btn6"):
            r = mv.corrente_derating_relay_trly(tipo_trly, T_trly)
            st.session_state["_mvtrly_result"] = {"tipo": tipo_trly, "T": T_trly, "res": r}

        rr = st.session_state.get("_mvtrly_result")
        if rr:
            r = rr["res"]
            c1, c2 = st.columns(2)
            c1.metric("Corrente ammissibile", f"{r['I_ammissibile_A']:.2f} A")
            c2.metric("MTBF relè", f"{r['MTBF_relay_anni']:.0f} anni")
            _export_csv_button(
                "Mark VIe — Derating Relè TRLYH1x",
                {"Tipo relè": rr["tipo"], "Temperatura [°C]": rr["T"],
                 "Corrente ammissibile [A]": f"{r['I_ammissibile_A']:.2f}", "MTBF relè [anni]": f"{r['MTBF_relay_anni']:.0f}"},
                key="mvtrly_export",
            )

    elif tool_mv == "Calcolo — RTD Pt100/Pt1000 (IEC 60751)":
        st.subheader("Conversione RTD ↔ temperatura — scheda PRTD (IEC 60751)")
        st.caption("Equazione di Callendar–Van Dusen, campo nominale −200…850 °C.")
        col1, col2 = st.columns(2)
        with col1:
            tipo_rtd = st.selectbox("Tipo sensore:", ["Pt100 (R0=100 Ω)", "Pt1000 (R0=1000 Ω)"], key="mv_rtd_tipo")
        R0_rtd = 100.0 if tipo_rtd.startswith("Pt100 ") else 1000.0
        with col2:
            verso_rtd = st.radio("Direzione:", ["Temperatura → Resistenza", "Resistenza → Temperatura"], key="mv_rtd_verso")
        if verso_rtd == "Temperatura → Resistenza":
            t_rtd = st.number_input("Temperatura [°C]:", value=100.0, min_value=-200.0, max_value=850.0, key="mv_rtd_t")
            if st.button("Calcola Resistenza", key="mv_btn_rtd1"):
                try:
                    r = mv.rtd_resistenza(t_rtd, R0_rtd)
                    st.session_state["_mvrtd_result"] = {"dir": "TR", "tipo": tipo_rtd, "T": t_rtd, "R": r["R_ohm"]}
                except ValueError as e:
                    st.session_state["_mvrtd_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_mvrtd_result")
            if rr and rr["dir"] == "TR":
                st.metric("Resistenza", f"{rr['R']:.3f} Ω")
                _export_csv_button(
                    "Mark VIe — RTD (T → R)",
                    {"Tipo sensore": rr["tipo"], "Temperatura [°C]": rr["T"], "Resistenza [Ω]": f"{rr['R']:.3f}"},
                    key="mvrtd_export_tr",
                )
        else:
            r_rtd = st.number_input("Resistenza [Ω]:", value=138.505, min_value=1.0, key="mv_rtd_r")
            if st.button("Calcola Temperatura", key="mv_btn_rtd2"):
                try:
                    r = mv.rtd_temperatura(r_rtd, R0_rtd)
                    st.session_state["_mvrtd_result"] = {"dir": "RT", "tipo": tipo_rtd, "R": r_rtd, "T": r["temp_C"]}
                except ValueError as e:
                    st.session_state["_mvrtd_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_mvrtd_result")
            if rr and rr["dir"] == "RT":
                st.metric("Temperatura", f"{rr['T']:.3f} °C")
                _export_csv_button(
                    "Mark VIe — RTD (R → T)",
                    {"Tipo sensore": rr["tipo"], "Resistenza [Ω]": rr["R"], "Temperatura [°C]": f"{rr['T']:.3f}"},
                    key="mvrtd_export_rt",
                )

    elif tool_mv == "Calcolo — Termocoppia (ITS-90)":
        st.subheader("Conversione termocoppia ↔ temperatura — scheda PTCC (ITS-90)")
        st.caption("Funzioni di riferimento NIST ITS-90 con compensazione del giunto freddo (CJC). "
                   "Tipi implementati: J, K, T, E.")
        col1, col2 = st.columns(2)
        with col1:
            tipo_tc = st.selectbox("Tipo termocoppia:", list(mv.TC_ITS90.keys()), key="mv_tc_tipo")
        with col2:
            t_cj = st.number_input("Temperatura giunto freddo [°C]:", value=0.0, key="mv_tc_cj")
        verso_tc = st.radio("Direzione:", ["Temperatura → mV", "mV → Temperatura"], key="mv_tc_verso", horizontal=True)
        rng_c = mv.TC_ITS90[tipo_tc]["range_C"]
        if verso_tc == "Temperatura → mV":
            t_tc = st.number_input(f"Temperatura giunto caldo [°C] (campo {rng_c[0]:.0f}…{rng_c[1]:.0f}):",
                                   value=500.0, key="mv_tc_t")
            if st.button("Calcola f.e.m.", key="mv_btn_tc1"):
                try:
                    r = mv.termocoppia_mv(tipo_tc, t_tc, t_cj)
                    st.session_state["_mvtc_result"] = {"dir": "TmV", "tipo": tipo_tc, "cj": t_cj, "T": t_tc, "res": r}
                except ValueError as e:
                    st.session_state["_mvtc_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_mvtc_result")
            if rr and rr["dir"] == "TmV":
                r = rr["res"]
                c1, c2 = st.columns(2)
                c1.metric("F.e.m. (con CJC)", f"{r['mV']:.4f} mV")
                c2.metric("F.e.m. rif. 0 °C", f"{r['mV_assoluto_rif0']:.4f} mV")
                _export_csv_button(
                    "Mark VIe — Termocoppia (T → mV)",
                    {"Tipo": rr["tipo"], "T giunto caldo [°C]": rr["T"], "T giunto freddo [°C]": rr["cj"], "F.e.m. [mV]": f"{r['mV']:.4f}"},
                    key="mvtc_export_tmv",
                )
        else:
            mv_tc = st.number_input("F.e.m. misurata [mV]:", value=20.644, key="mv_tc_mv")
            if st.button("Calcola Temperatura", key="mv_btn_tc2"):
                try:
                    r = mv.termocoppia_temp(tipo_tc, mv_tc, t_cj)
                    st.session_state["_mvtc_result"] = {"dir": "mVT", "tipo": tipo_tc, "cj": t_cj, "mv": mv_tc, "res": r}
                except ValueError as e:
                    st.session_state["_mvtc_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_mvtc_result")
            if rr and rr["dir"] == "mVT":
                r = rr["res"]
                st.metric("Temperatura giunto caldo", f"{r['temp_C']:.2f} °C")
                _export_csv_button(
                    "Mark VIe — Termocoppia (mV → T)",
                    {"Tipo": rr["tipo"], "F.e.m. [mV]": rr["mv"], "T giunto freddo [°C]": rr["cj"], "Temperatura [°C]": f"{r['temp_C']:.2f}"},
                    key="mvtc_export_mvt",
                )

    elif tool_mv == "Calcolo — Diagnostica Loop 4–20 mA (NE43)":
        st.subheader("Diagnostica loop analogico 4–20 mA (NAMUR NE43)")
        st.caption("Soglie standard: ≤3.6 mA sotto-range/rottura, ≥21 mA sovra-range/corto. "
                   "Applicabile ai canali PAIC/PHRA.")
        col1, col2, col3 = st.columns(3)
        with col1:
            i_loop = st.number_input("Corrente misurata [mA]:", value=12.0, min_value=0.0, max_value=25.0, step=0.1, key="mv_ne43_i")
        with col2:
            sp_min = st.number_input("Valore a 4 mA:", value=0.0, key="mv_ne43_min")
        with col3:
            sp_max = st.number_input("Valore a 20 mA:", value=100.0, key="mv_ne43_max")
        if st.button("Diagnostica Loop", key="mv_btn_ne43"):
            try:
                r = mv.diagnostica_loop_420(i_loop, sp_min, sp_max)
                st.session_state["_mvne43_result"] = {"i": i_loop, "min": sp_min, "max": sp_max, "res": r}
            except ValueError as e:
                st.session_state["_mvne43_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_mvne43_result")
        if rr:
            r = rr["res"]
            if r["valido"]:
                st.success(r["stato"])
                c1, c2 = st.columns(2)
                c1.metric("Valore di processo", f"{r['valore_processo']:.2f}")
                c2.metric("Percentuale scala", f"{r['percentuale']:.1f} %")
            else:
                st.error(r["stato"])
            _export_csv_button(
                "Mark VIe — Diagnostica Loop 4–20 mA (NE43)",
                {"Corrente [mA]": rr["i"], "Valore a 4 mA": rr["min"], "Valore a 20 mA": rr["max"], "Stato": r["stato"],
                 "Valore processo": f"{r['valore_processo']:.2f}" if r["valido"] else "-"},
                key="mvne43_export",
            )

    elif tool_mv == "Calcolo — Velocità / Sovravelocità Turbina":
        st.subheader("Velocità e sovravelocità turbina — schede PTUR/PPRO/PGEN")
        st.caption("Ruota fonica + pickup magnetico (MPU). Campo sensore 2 Hz – 20 kHz (GEH-6721G).")
        col1, col2 = st.columns(2)
        with col1:
            n_denti = st.number_input("Numero denti ruota fonica:", value=60, min_value=1, step=1, key="mv_spd_denti")
        with col2:
            modo_spd = st.radio("Modalità:", ["rpm → frequenza", "frequenza → rpm", "Trip sovravelocità"], key="mv_spd_modo")
        if modo_spd == "rpm → frequenza":
            rpm_in = st.number_input("Velocità [rpm]:", value=3000.0, min_value=0.0, key="mv_spd_rpm")
            if st.button("Calcola Frequenza", key="mv_btn_spd1"):
                r = mv.frequenza_da_velocita(rpm_in, int(n_denti))
                st.session_state["_mvspd_result"] = {"modo": "rf", "denti": int(n_denti), "rpm": rpm_in, "res": r}

            rr = st.session_state.get("_mvspd_result")
            if rr and rr["modo"] == "rf":
                r = rr["res"]
                st.metric("Frequenza impulsi", f"{r['freq_hz']:.1f} Hz")
                if not r["in_campo_sensore"]:
                    st.warning("Frequenza fuori dal campo 2 Hz – 20 kHz del sensore.")
                _export_csv_button(
                    "Mark VIe — Velocità (rpm → frequenza)",
                    {"N denti": rr["denti"], "Velocità [rpm]": rr["rpm"], "Frequenza [Hz]": f"{r['freq_hz']:.1f}"},
                    key="mvspd_export_rf",
                )
        elif modo_spd == "frequenza → rpm":
            f_in = st.number_input("Frequenza impulsi [Hz]:", value=3000.0, min_value=0.0, key="mv_spd_freq")
            if st.button("Calcola Velocità", key="mv_btn_spd2"):
                r = mv.velocita_da_frequenza(f_in, int(n_denti))
                st.session_state["_mvspd_result"] = {"modo": "fr", "denti": int(n_denti), "freq": f_in, "res": r}

            rr = st.session_state.get("_mvspd_result")
            if rr and rr["modo"] == "fr":
                r = rr["res"]
                st.metric("Velocità", f"{r['rpm']:.1f} rpm")
                if not r["in_campo_sensore"]:
                    st.warning("Frequenza fuori dal campo 2 Hz – 20 kHz del sensore.")
                _export_csv_button(
                    "Mark VIe — Velocità (frequenza → rpm)",
                    {"N denti": rr["denti"], "Frequenza [Hz]": rr["freq"], "Velocità [rpm]": f"{r['rpm']:.1f}"},
                    key="mvspd_export_fr",
                )
        else:
            col3, col4 = st.columns(2)
            with col3:
                rpm_nom = st.number_input("Velocità nominale [rpm]:", value=3000.0, min_value=1.0, key="mv_spd_nom")
            with col4:
                soglia = st.number_input("Soglia trip [% nominale]:", value=110.0, min_value=100.1, key="mv_spd_soglia")
            if st.button("Calcola Trip", key="mv_btn_spd3"):
                try:
                    r = mv.trip_sovravelocita(rpm_nom, int(n_denti), soglia)
                    st.session_state["_mvtrip_result"] = {"denti": int(n_denti), "nom": rpm_nom, "soglia": soglia, "res": r}
                except ValueError as e:
                    st.session_state["_mvtrip_result"] = None
                    st.error(str(e))

            rr = st.session_state.get("_mvtrip_result")
            if rr:
                r = rr["res"]
                c1, c2, c3 = st.columns(3)
                c1.metric("Velocità trip", f"{r['rpm_trip']:.0f} rpm")
                c2.metric("Frequenza trip", f"{r['freq_trip_hz']:.1f} Hz")
                c3.metric("Margine", f"+{r['margine_rpm']:.0f} rpm")
                if not r["freq_trip_in_campo_sensore"]:
                    st.warning("Frequenza di trip fuori dal campo 2 Hz – 20 kHz del sensore.")
                _export_csv_button(
                    "Mark VIe — Trip Sovravelocità",
                    {"N denti": rr["denti"], "Velocità nominale [rpm]": rr["nom"], "Soglia [%]": rr["soglia"],
                     "Velocità trip [rpm]": f"{r['rpm_trip']:.0f}", "Frequenza trip [Hz]": f"{r['freq_trip_hz']:.1f}"},
                    key="mvtrip_export",
                )

    elif tool_mv == "Checklist — Commissioning Mark VI/VIe":
        st.subheader("Checklist di commissioning Mark VI/VIe")
        st.caption("Sequenza didattica di buona pratica per il commissioning di un sistema di controllo turbina "
                   "(verifiche pre-avviamento, I/O, ridondanza, protezioni, logica applicativa). Per la procedura "
                   "di dettaglio dello specifico impianto fare riferimento alle istruzioni di progetto e a GEH-6721.")

        _dd_chk = _load_device_data()
        _stato_chk = _dd_chk["checklist_mv"]
        flat_chk = mv.checklist_commissioning_flat()
        n_totali = len(flat_chk)
        n_fatte = sum(1 for v in flat_chk if _stato_chk.get(v["id"]))
        st.progress(n_fatte / n_totali if n_totali else 0.0,
                    text=f"{n_fatte} / {n_totali} voci completate ({n_fatte / n_totali * 100:.0f}%)" if n_totali else "")

        col_chk1, col_chk2 = st.columns(2)
        with col_chk1:
            if st.button("☑️ Segna tutto", key="mv_chk_all"):
                for v in flat_chk:
                    _stato_chk[v["id"]] = True
                _save_device_data(_dd_chk)
                st.rerun()
        with col_chk2:
            if st.button("🔄 Azzera checklist", key="mv_chk_reset"):
                _dd_chk["checklist_mv"] = {}
                _save_device_data(_dd_chk)
                st.rerun()

        for blocco in mv.CHECKLIST_COMMISSIONING:
            n_fase_tot = len(blocco["voci"])
            n_fase_fatte = sum(1 for vi in range(n_fase_tot) if _stato_chk.get(f"{mv.CHECKLIST_COMMISSIONING.index(blocco)}_{vi}"))
            with st.expander(f"{blocco['fase']} ({n_fase_fatte}/{n_fase_tot})", expanded=(n_fase_fatte < n_fase_tot)):
                fi = mv.CHECKLIST_COMMISSIONING.index(blocco)
                for vi, voce in enumerate(blocco["voci"]):
                    vid = f"{fi}_{vi}"
                    checked = st.checkbox(voce, value=_stato_chk.get(vid, False), key=f"mv_chk_{vid}")
                    if checked != _stato_chk.get(vid, False):
                        _stato_chk[vid] = checked
                        _save_device_data(_dd_chk)

        st.markdown("---")
        dati_chk_export = {v["fase"]: ("✅ fatto" if _stato_chk.get(v["id"]) else "⬜ da fare") for v in flat_chk}
        dati_chk_export["Avanzamento totale"] = f"{n_fatte}/{n_totali} ({n_fatte / n_totali * 100:.0f}%)" if n_totali else "-"
        _export_csv_button("Mark VIe — Checklist Commissioning", dati_chk_export, key="mvchk_export")

    elif tool_mv == "Calcolo — Loading Rete IONet":
        st.subheader("Stima carico (loading) rete IONet")
        st.caption("Modello didattico semplificato: traffico ciclico controllore ↔ pacchi I/O a ogni frame di "
                   "scansione. Non riproduce il protocollo proprietario GE; utile per una stima di massima del "
                   "margine di banda disponibile su una IONet Ethernet (tipicamente 100 Mbps).")
        col1, col2, col3 = st.columns(3)
        with col1:
            n_pacchi_ion = st.number_input("Numero pacchi I/O sulla rete:", value=8, min_value=1, step=1, key="mv_ion_npacchi")
            canali_ion = st.number_input("Canali medi per pacco:", value=16.0, min_value=1.0, step=1.0, key="mv_ion_canali")
        with col2:
            frame_ion = st.number_input("Frame rate scansione [Hz]:", value=100.0, min_value=1.0, key="mv_ion_frame",
                                         help="Frequenza di scansione del controllore Mark VIe — tipicamente 100 Hz.")
            banda_ion = st.number_input("Banda rete IONet [Mbps]:", value=mv.IONET_BANDA_TIPICA_MBPS, min_value=1.0, key="mv_ion_banda")
        with col3:
            over_ion = st.number_input("Overhead per datagramma [byte]:", value=float(mv.IONET_OVERHEAD_BYTE), min_value=0.0, key="mv_ion_over")
            byte_can_ion = st.number_input("Byte utili per canale:", value=mv.IONET_BYTE_PER_CANALE, min_value=0.1, key="mv_ion_bytecan")

        if st.button("Calcola Loading IONet", key="mv_ion_btn"):
            try:
                r = mv.loading_ionet(int(n_pacchi_ion), canali_ion, frame_ion, banda_ion, over_ion, byte_can_ion)
                st.session_state["_mvion_result"] = {
                    "n_pacchi": int(n_pacchi_ion), "canali": canali_ion, "frame": frame_ion, "banda": banda_ion, "res": r,
                }
            except ValueError as e:
                st.session_state["_mvion_result"] = None
                st.error(str(e))

        rr = st.session_state.get("_mvion_result")
        if rr:
            r = rr["res"]
            c1, c2, c3 = st.columns(3)
            c1.metric("Utilizzo banda", f"{r['utilizzo_pct']:.2f} %")
            c2.metric("Bit rate totale", f"{r['bit_rate_totale_Mbps']:.3f} Mbps")
            c3.metric("Max pacchi (margine consigliato)", f"{r['n_pacchi_max_raccomandato']}")
            if r["entro_margine_raccomandato"]:
                st.success(f"Entro il margine ingegneristico consigliato (≤ {r['margine_raccomandato_pct']:.0f}% di utilizzo).")
            else:
                st.warning(f"Sopra il margine ingegneristico consigliato (≤ {r['margine_raccomandato_pct']:.0f}% di utilizzo): "
                           "valutare di distribuire i pacchi su più reti IONet o ridurre i canali per pacco.")
            _export_csv_button(
                "Mark VIe — Loading Rete IONet",
                {"Pacchi I/O": rr["n_pacchi"], "Canali medi/pacco": rr["canali"], "Frame rate [Hz]": rr["frame"],
                 "Banda rete [Mbps]": rr["banda"], "Utilizzo [%]": f"{r['utilizzo_pct']:.2f}",
                 "Bit rate totale [Mbps]": f"{r['bit_rate_totale_Mbps']:.3f}",
                 "Max pacchi raccomandato": r["n_pacchi_max_raccomandato"]},
                key="mvion_export",
            )


elif categoria == "📁  Progetti Salvati":
    st.title("📁 Progetti Salvati")
    st.caption("Un progetto raggruppa più calcoli salvati con il pulsante \"💾 Salva questo calcolo in un progetto\" "
               "presente sotto ogni risultato. Persistenza per dispositivo (nessun account).")

    _dd_proj = _load_device_data()
    _progetti = _dd_proj["projects"]

    if not _progetti:
        st.info("Nessun progetto salvato. Calcola qualcosa in un qualunque modulo e usa "
                "\"💾 Salva questo calcolo in un progetto\" sotto il risultato per crearne uno.")
    else:
        nome_sel = st.selectbox("Progetto:", list(_progetti.keys()), key="proj_view_sel")
        voci = _progetti.get(nome_sel, [])
        st.subheader(f"{nome_sel} — {len(voci)} calcoli salvati")

        for i, voce in enumerate(voci):
            with st.expander(f"{voce['strumento']} — {voce['timestamp']}"):
                st.table([{"Campo": k, "Valore": v} for k, v in voce["dati"].items()])
                if st.button("🗑️ Rimuovi questa voce", key=f"proj_del_{nome_sel}_{i}"):
                    _elimina_voce_progetto(nome_sel, i)
                    st.rerun()

        if voci:
            buf_proj = io.StringIO()
            writer_proj = csv.writer(buf_proj)
            writer_proj.writerow(["Progetto", nome_sel])
            writer_proj.writerow([])
            for voce in voci:
                writer_proj.writerow(["Strumento", voce["strumento"]])
                writer_proj.writerow(["Data/ora", voce["timestamp"]])
                writer_proj.writerow(["Campo", "Valore"])
                for k, v in voce["dati"].items():
                    writer_proj.writerow([k, v])
                writer_proj.writerow([])
            st.download_button(
                "📥 Esporta intero progetto in CSV",
                data=buf_proj.getvalue(),
                file_name=f"progetto_{nome_sel.replace(' ', '_')}.csv",
                mime="text/csv",
                key="proj_export_all",
            )

        st.markdown("---")
        if st.button(f"🗑️ Elimina progetto '{nome_sel}'", key="proj_del_all"):
            _elimina_progetto(nome_sel)
            st.rerun()

    st.markdown("---")
    st.subheader("🔄 Scambio con la versione offline")
    st.caption("Stesso file JSON in entrambe le direzioni: esporta da qui e importa nella versione "
               "offline (vista Progetti → \"⬆️ Importa backup\"), o viceversa. Le voci già presenti "
               "non vengono duplicate.")

    col_bk1, col_bk2 = st.columns(2)
    with col_bk1:
        _backup_json = json.dumps(
            backup_compat.esporta_progetti_per_pwa(_progetti),
            ensure_ascii=False, indent=2,
        )
        _backup_click = st.download_button(
            "⬇️ Esporta backup (per versione offline)",
            data=_backup_json,
            file_name=f"backup_calcolatore_{datetime.now().strftime('%Y-%m-%d')}.json",
            mime="application/json",
            key="proj_backup_export",
            disabled=not _progetti,
        )
        if _backup_click:
            _dd_proj["settings"]["ultimo_backup_il"] = datetime.now().isoformat()
            _save_device_data(_dd_proj)
    with col_bk2:
        _file_bk = st.file_uploader("⬆️ Importa backup (anche dalla versione offline):",
                                    type=["json"], key="proj_backup_import")
        if _file_bk is not None and st.button("Importa nel dispositivo", key="proj_backup_import_btn"):
            try:
                _backup = json.loads(_file_bk.getvalue().decode("utf-8"))
                _n_agg = backup_compat.importa_backup_pwa(_backup, _dd_proj["projects"])
                _save_device_data(_dd_proj)
                st.success(f"Importate {_n_agg} voci nei progetti di questo dispositivo.")
                if _n_agg:
                    st.rerun()
            except (ValueError, json.JSONDecodeError, UnicodeDecodeError) as e:
                st.error(f"Importazione non riuscita: {e}")

st.markdown("---")
st.caption("Disclaimer: strumento indicativo basato sulle norme tecniche CEI 64-8, ISO 10816, ISO 1940, ISO 1217, IEC 60751, NIST ITS-90. Non sostituisce la progettazione formale di un professionista abilitato.")
