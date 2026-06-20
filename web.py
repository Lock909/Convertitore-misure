import math

import streamlit as st
try:
    import plotly.graph_objects as go
    _PLOTLY = True
except ImportError:
    _PLOTLY = False

import automazione
import formule
import idraulica
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
from costanti import SEZIONI_COMMERCIALI, TENSIONE_MONOFASE, TENSIONE_TRIFASE


st.set_page_config(
    page_title="Tool Industriale",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

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
[data-testid="stSidebar"] .stRadio label { font-size: 0.92rem; padding: 4px 0; }
[data-testid="stSidebar"] .stRadio [data-baseweb="radio"] { gap: 0.3rem; }

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
]

if "_nav_goto" in st.session_state:
    dest = st.session_state.pop("_nav_goto")
    if dest in _SEZIONI:
        st.session_state["sidebar_cat"] = dest

with st.sidebar:
    st.markdown("## ⚙️ Tool Industriale")
    st.markdown("---")
    categoria = st.radio(
        "Sezione",
        _SEZIONI,
        key="sidebar_cat",
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.caption("v4.0 · CEI 64-8 · ISO 10816 · IEC 60034-30 · EN 12464-1")


# ── Home ──────────────────────────────────────────────────────────────────────

_NAV_MAP = {
    "⚖️  Conversioni":              "⚖️  Conversioni",
    "⚡  Calcoli Elettrici":        "⚡  Calcoli Elettrici",
    "🤖  PLC e Automazione":        "🤖  PLC e Automazione",
    "〜  Vibrazioni":               "〜  Vibrazioni",
    "🔩  Meccanica":                "🔩  Meccanica",
    "🔧  Pneumatica & Strumenti":   "🔧  Pneumatica & Strumenti",
    "🌡️  Termotecnica & Impianti":  "🌡️  Termotecnica & Impianti",
}

if categoria == "🏠  Home":
    st.title("⚙️ Strumento Multifunzione Industriale")
    st.markdown("Calcoli tecnici per ingegneria industriale. Clicca una sezione per iniziare.")
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
    ]

    cols = st.columns(4)
    for i, (icon, label, nav_key, desc, norma) in enumerate(_HOME_CARDS):
        with cols[i % 4]:
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
        ],
        key="elett_tipo",
    )

    if tipo == "Legge di Ohm":
        cerca = st.selectbox("Cosa calcolare?", ["Tensione", "Corrente", "Resistenza"], key="ohm_cerca")
        in1 = st.number_input("Primo Valore:", value=1.0, key="ohm_in1")
        in2 = st.number_input("Secondo Valore:", value=1.0, key="ohm_in2")
        if st.button("Calcola", key="ohm_btn"):
            try:
                val_ohm = formule.calcola_ohm(cerca, in1, in2)
                unita_ohm = {"Tensione": "V", "Corrente": "A", "Resistenza": "Ω"}[cerca]
                st.success(f"{cerca}: {val_ohm:.4f} {unita_ohm}")
            except ValueError as e:
                st.error(str(e))

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
                    st.error("Valori non validi: controlla tensione, corrente e cos phi.")
                else:
                    st.success(f"Potenza attiva: {res['W']:.1f} W ({res['kW']:.4f} kW)")
                    st.info(f"Meccanica: {res['HP']:.3f} HP | {res['CV']:.3f} CV")
                    st.info(f"Apparente: {res['VA']:.1f} VA ({res['kVA']:.4f} kVA)")
                    if sis != "DC":
                        st.info(f"Reattiva: {res['VAR']:.1f} VAR ({res['kVAR']:.4f} kVAR)")
        else:
            w = st.number_input("Potenza in WATT (W):", value=2200.0, step=100.0, key="pot_w")
            if st.button("Estrai Ampere", key="pot_btn_w"):
                res = formule.calcola_potenza_e_corrente(sis, v, 0.0, w, cos_phi, obiettivo)
                if res is None:
                    st.error("Valori non validi: controlla tensione, potenza e cos phi.")
                else:
                    st.success(f"Corrente assorbita: {res['A']:.2f} A")
                    st.info(f"Potenza: {res['HP']:.3f} HP | {res['CV']:.3f} CV")
                    st.info(f"Apparente: {res['VA']:.1f} VA ({res['kVA']:.4f} kVA)")

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
                st.success(f"{val_pot} {da_u} = {ris:.6f} {a_u}")
            except ValueError as e:
                st.error(str(e))

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
                st.error("Valori non validi: controlla potenza, rendimento, tensione e cos phi.")
            else:
                st.success(f"Potenza assorbita dalla rete: {res_m['P_in_kW']:.3f} kW ({res_m['P_in_W']:.0f} W)")
                st.info(f"Corrente di linea: {res_m['I_A']:.2f} A | Apparente: {res_m['P_app_kVA']:.3f} kVA")
                st.info(f"Potenza ingresso: {res_m['HP_in']:.2f} HP")
                with st.expander("Dettagli"):
                    st.write(f"Rendimento: {res_m['eta']*100:.1f}% - energia persa in calore: {res_m['P_in_kW'] - p_out:.3f} kW")

    elif tipo == "Rifasamento Industriale (kVAR)":
        st.subheader("Calcolo Batteria di Condensatori")
        p_kw = st.number_input("Potenza attiva impianto (P) [kW]:", value=50.0, key="rif_pkw")
        cos_ini = st.number_input("cos phi attuale:", min_value=0.3, max_value=0.99, value=0.75, format="%.2f", key="rif_ini")
        cos_fin = st.number_input("cos phi obiettivo:", min_value=0.8, max_value=1.0, value=0.95, format="%.2f", key="rif_fin")
        if st.button("Calcola kVAR", key="rif_btn"):
            qc, stato = formule.calcola_rifasamento_kvar(p_kw, cos_ini, cos_fin)
            if stato != "OK":
                st.warning(stato)
            else:
                st.success(f"Potenza rifasante necessaria: {qc:.2f} kVAR")
                with st.expander("Dettagli calcolo"):
                    tan_i = math.tan(math.acos(cos_ini))
                    tan_f = math.tan(math.acos(cos_fin))
                    st.write(f"Potenza reattiva iniziale: {p_kw * tan_i:.2f} kVAR")
                    st.write(f"Potenza reattiva target: {p_kw * tan_f:.2f} kVAR")
                    st.write(f"Differenza (condensatori): {qc:.2f} kVAR")

    elif tipo == "Caduta di Tensione":
        mat = st.radio("Materiale Conduttore:", ["Rame", "Alluminio"], key="cdv_mat")
        fasi = st.selectbox("Linea elettrica:", ["Monofase", "Trifase"], key="cdv_fasi")
        amp = st.number_input("Corrente Ib [A]:", value=16.0, key="cdv_amp")
        metri = st.number_input("Lunghezza [Metri]:", value=50.0, key="cdv_metri")
        sez = st.selectbox("Sezione mm2:", SEZIONI_COMMERCIALI, key="cdv_sez")
        isol = st.selectbox("Isolante Cavo:", ["PVC (70C)", "EPR / XLPE / Gomma (90C)"], key="cdv_isol")
        cos_phi = st.number_input("cos phi:", value=0.85, min_value=0.1, max_value=1.0, key="cdv_cosphi")
        temp_ambiente = st.slider("Temperatura Ambiente (C):", min_value=10, max_value=60, value=30, step=5, key="cdv_temp")
        n_circuiti = st.number_input("Numero di Cavi affiancati:", min_value=1, max_value=20, value=1, key="cdv_ncir")
        iz_tabella = st.number_input("Portata Nominale catalogo Iz [A] (a 30C):", value=20.0, key="cdv_iz")
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
        )

        if "Interrata" in posa:
            st.warning("Per posa interrata il calcolo usa una tabella in aria: il risultato puo essere leggermente conservativo.")

        if st.button("Calcola Perdita Vettoriale Completa", key="cdv_btn"):
            try:
                dv, t_lav, rho_t, k1, k2, iz_real = formule.calcola_caduta_avanzata(
                    mat, isol, posa, fasi, amp, metri, sez, cos_phi, temp_ambiente, iz_tabella, n_circuiti
                )
                if dv < 0:
                    st.error(f"Temperatura ambiente ({temp_ambiente}C) oltre il limite dell'isolante selezionato.")
                else:
                    v_ref = TENSIONE_MONOFASE if fasi == "Monofase" else TENSIONE_TRIFASE
                    pct = (dv / v_ref) * 100.0
                    with st.expander("Dettagli calcolo termico"):
                        st.write(f"K1 (temperatura ambiente): {k1:.2f}")
                        st.write(f"K2 (raggruppamento {n_circuiti} cavi): {k2:.2f}")
                        st.write(f"Portata reale Iz: {iz_real:.2f} A")
                        st.write(f"Temperatura interna cavo: {t_lav:.1f} C")
                        st.write(f"Resistivita operativa rho_t: {rho_t:.5f} ohm*mm2/m")
                    if pct > 4.0:
                        st.error(f"Perdita: {dv:.2f} V ({pct:.2f}%) - Fuori norma (limite: 4%)")
                    else:
                        st.success(f"Perdita: {dv:.2f} V ({pct:.2f}%) - A norma CEI 64-8")
            except ValueError as e:
                st.error(str(e))

    elif tipo == "Corrente di Cortocircuito (Icc)":
        st.subheader("Stima Icc presunta in fondo linea (metodo semplificato IEC 60909)")
        st.caption("Utile per verificare il potere di interruzione degli interruttori.")
        col1, col2 = st.columns(2)
        with col1:
            fasi_cc = st.selectbox("Sistema:", ["Trifase", "Monofase"], key="icc_fasi")
            v_cc = st.number_input("Tensione nominale [V]:", value=400.0 if fasi_cc == "Trifase" else 230.0, key="icc_v")
            trafo_kva = st.number_input("Potenza trasformatore [kVA]:", value=400.0, min_value=1.0, key="icc_kva")
        with col2:
            vcc_pct = st.number_input("Vcc trasformatore [%] (tipico 4-6%):", value=4.0, min_value=1.0, max_value=20.0, key="icc_vcc")
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
        )
        c_val = 1.05 if "1.05" in c_icc else 0.95

        if st.button("Calcola Icc", key="icc_btn"):
            try:
                icc_ka, z_tot, z_tr, z_cv = formule.calcola_corrente_cortocircuito(v_cc, trafo_kva, vcc_pct, mat_cc, sez_cc, lung_cc, fasi_cc, c=c_val)
                tipo_icc = "MASSIMA" if c_val == 1.05 else "MINIMA"
                st.success(f"Icc {tipo_icc} (c={c_val}): {icc_ka:.3f} kA ({icc_ka*1000:.0f} A)")
                with st.expander("Dettagli impedenze"):
                    st.write(f"Z trafo: {z_tr:.2f} mOhm")
                    st.write(f"Z cavo: {z_cv:.2f} mOhm")
                    st.write(f"Z totale: {z_tot:.2f} mOhm")
                if icc_ka < 1.0:
                    st.info("Nota: Icc < 1 kA. Verifica il potere di interruzione dell'interruttore.")
            except ValueError as e:
                st.error(str(e))
        st.caption("Calcolo semplificato. Per progettazione formale usare IEC 60909 completo.")

    elif tipo == "Dimensionamento Protezioni":
        ib = st.number_input("Corrente Ib [A]:", value=16.0, key="prot_ib")
        j_dens = st.slider("Densita J [A/mm2]:", 1.0, 6.0, 4.0, step=0.5, key="prot_j")
        if st.button("Trova Soluzione", key="prot_btn"):
            try:
                mag, cavo, t_sez = formule.calcola_sezione_protezione(ib, j_dens)
                st.success(f"Interruttore consigliato (In): {mag} A | Sezione commerciale: {cavo} mm2 (teorica: {t_sez:.2f} mm2)")
            except ValueError as e:
                st.error(str(e))

    elif tipo == "Carico Trifase Equilibrato":
        st.subheader("Carico trifase equilibrato — potenze e forme d'onda")
        col1, col2, col3 = st.columns(3)
        with col1:
            V_lin  = st.number_input("Tensione di linea V_L [V]:", value=400.0, min_value=1.0, key="tf_Vl")
            f_hz   = st.number_input("Frequenza [Hz]:", value=50.0, min_value=1.0, key="tf_f")
        with col2:
            cos_tf = st.number_input("cos φ:", value=0.85, min_value=0.01, max_value=1.0, key="tf_cos")
            tipo_carico = st.selectbox("Tipo carico:", ["Induttivo (ritardo)", "Capacitivo (anticipo)", "Resistivo puro"], key="tf_tipo")
        with col3:
            P_kW   = st.number_input("Potenza attiva P [kW]:", value=30.0, min_value=0.01, key="tf_P")
            collegamento = st.selectbox("Collegamento:", ["Stella (Y)", "Triangolo (Δ)"], key="tf_coll")

        if st.button("Calcola e traccia", key="tf_btn"):
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
            try:
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
                r = trafo.calcola_trasformatore(S_kVA, V1_V, V2_V, P_ferro_W, P_rame_W, V_cc_pct, 2.0, cos_phi, trifase)
                c1, c2, c3 = st.columns(3)
                c1.metric("Rapporto di trasf.", f"{r['rapporto_a']:.4f}")
                c1.metric("I1 nominale", f"{r['I1_nom_A']:.2f} A")
                c1.metric("I2 nominale", f"{r['I2_nom_A']:.2f} A")
                c2.metric("Rendimento nom.", f"{r['eta_nom_pct']:.2f} %")
                c2.metric("Rendimento max.", f"{r['eta_max_pct']:.2f} %")
                c2.metric("β ottimale", f"{r['beta_opt']:.3f}")
                c3.metric("Icc", f"{r['I_cc_A']:.1f} A")
                c3.metric("Caduta tensione ΔV%", f"{r['dV_pct']:.2f} %")
                c3.metric("Z_cc [%]", f"{V_cc_pct:.1f} %")
                st.markdown("**Parametri circuito equivalente**")
                st.markdown(f"R_eq = {r['R_eq_ohm']:.4f} Ω &nbsp;|&nbsp; X_eq = {r['X_eq_ohm']:.4f} Ω &nbsp;|&nbsp; R_cc% = {r['R_cc_pct']:.3f}% &nbsp;|&nbsp; X_cc% = {r['X_cc_pct']:.3f}%")
                if _PLOTLY:
                    rv = trafo.rendimento_vs_carico(S_kVA, P_ferro_W, P_rame_W, cos_phi)
                    fig_tr = go.Figure()
                    fig_tr.add_trace(go.Scatter(x=rv["beta"], y=rv["eta_pct"], mode="lines", name="η vs β", line=dict(color="#2196F3", width=2)))
                    fig_tr.add_vline(x=r["beta_opt"], line_dash="dash", line_color="#FF5722", annotation_text=f"β_opt={r['beta_opt']:.3f}")
                    fig_tr.update_layout(title="Rendimento vs. Fattore di Carico", xaxis_title="β (fattore di carico)", yaxis_title="η [%]", height=320)
                    st.plotly_chart(fig_tr, use_container_width=True)
            except (ValueError, ZeroDivisionError) as e:
                st.error(str(e))

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
                    r = rlc.impedenza_serie(R_rlc, L_H, C_F, f_rlc)
                    st.success(f"Z = {abs(r['Z']):.3f} Ω  |  φ = {r['phi_deg']:.2f}°  |  cos φ = {r['cos_phi']:.4f}  |  Tipo: {r['tipo']}")
                    c1, c2, c3 = st.columns(3)
                    c1.metric("X_L", f"{r['X_L_ohm']:.3f} Ω")
                    c1.metric("X_C", f"{r['X_C_ohm']:.3f} Ω")
                    c2.metric("X_netto", f"{r['X_net_ohm']:.3f} Ω")
                    c2.metric("|Z|", f"{abs(r['Z']):.3f} Ω")
                    c3.metric("φ", f"{r['phi_deg']:.2f}°")
                    c3.metric("cos φ", f"{r['cos_phi']:.4f}")
                else:
                    r = rlc.impedenza_parallelo(R_rlc, L_H, C_F, f_rlc)
                    st.success(f"|Z| = {abs(r['Z']):.3f} Ω  |  φ = {r['phi_deg']:.2f}°  |  Tipo: {r['tipo']}")
                    c1, c2 = st.columns(2)
                    c1.metric("B_L", f"{r['B_L']:.5f} S")
                    c1.metric("B_C", f"{r['B_C']:.5f} S")
                    c2.metric("|Y|", f"{abs(r['Y']):.5f} S")
                    c2.metric("φ", f"{r['phi_deg']:.2f}°")
                r_ris = rlc.risonanza_serie(L_H, C_F, R_rlc)
                st.info(f"Risonanza serie: f₀ = {r_ris['f0']:.2f} Hz  |  Q = {r_ris['Q']:.2f}  |  BW = {r_ris['BW']:.2f} Hz")
                if _PLOTLY:
                    resp = rlc.risposta_frequenza(R_rlc, L_H, C_F, max(1.0, f_rlc*0.01), f_rlc*20, tipo_rlc.lower(), 200)
                    fig_rlc = go.Figure()
                    fig_rlc.add_trace(go.Scatter(x=resp["f_Hz"], y=resp["Z_ohm"], mode="lines", name="|Z| [Ω]", line=dict(color="#2196F3")))
                    fig_rlc.update_layout(title="Risposta in frequenza |Z|", xaxis_title="f [Hz]", yaxis_title="|Z| [Ω]", xaxis_type="log", height=300)
                    st.plotly_chart(fig_rlc, use_container_width=True)
            except (ValueError, ZeroDivisionError) as e:
                st.error(str(e))

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
                r = thd.calcola_thd(V1_thd, harm_vals)
                c1, c2, c3 = st.columns(3)
                c1.metric("THD", f"{r['THD_pct']:.2f} %")
                c2.metric("V_rms totale", f"{r['rms_totale']:.2f} V")
                c3.metric("Giudizio IEEE", r['giudizio_ieee'])
                if r["contributi"]:
                    st.markdown("**Contributi per ordine:**")
                    contrib_str = "  ".join([f"H{k}: {v:.1f}%" for k, v in sorted(r["contributi"].items())])
                    st.text(contrib_str)
                if _PLOTLY:
                    onda = thd.forma_onda_armonica(V1_thd, harm_vals, 50.0, 2, 500)
                    fig_thd = go.Figure()
                    fig_thd.add_trace(go.Scatter(x=onda["t_ms"], y=onda["V_tot"], mode="lines", name="V totale", line=dict(color="#2196F3", width=2)))
                    for ord_h, vals in onda["per_ordine"].items():
                        fig_thd.add_trace(go.Scatter(x=onda["t_ms"], y=vals, mode="lines", name=f"H{ord_h}", line=dict(dash="dot"), opacity=0.6))
                    fig_thd.update_layout(title="Forma d'onda con armoniche", xaxis_title="t [ms]", yaxis_title="V [V]", height=320)
                    st.plotly_chart(fig_thd, use_container_width=True)
            except (ValueError, ZeroDivisionError) as e:
                st.error(str(e))

    elif tipo == "Batterie e UPS":
        st.subheader("Calcolo Batterie e UPS")
        sub_bat = st.radio("Calcolo:", ["Autonomia batteria", "Dimensionamento banco", "Corrente di carica", "Correzione temperatura"], horizontal=True, key="bat_sub")
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
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Autonomia", f"{r['t_autonomia_h']:.2f} h  ({r['t_autonomia_min']:.0f} min)")
                    c2.metric("Energia utile", f"{r['E_utile_Wh']:.0f} Wh")
                    c3.metric("I scarica", f"{r['I_scarica_A']:.1f} A  (C-rate: {r['C_rate']:.2f})")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))
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
                    c1, c2 = st.columns(2)
                    c1.metric("C nominale richiesta", f"{r['C_nominale_Ah']:.0f} Ah")
                    c2.metric("Energia richiesta", f"{r['E_richiesta_Wh']:.0f} Wh")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))
        elif sub_bat == "Corrente di carica":
            C_ch = st.number_input("Capacità C [Ah]:", value=100.0, min_value=1.0, key="bat_chC")
            if st.button("Calcola Correnti", key="bat_btn3"):
                r = bat.corrente_carica(C_ch)
                st.markdown(f"**I_C1** = {r['I_C1_A']:.1f} A  |  **I_C5** = {r['I_C5_A']:.1f} A  |  **I_C10** = {r['I_C10_A']:.1f} A  |  **I_C20** = {r['I_C20_A']:.1f} A  |  **I_float** = {r['I_float_A']:.2f} A")
        else:
            col1, col2 = st.columns(2)
            with col1:
                C_T  = st.number_input("Capacità C [Ah]:", value=100.0, min_value=1.0, key="bat_TC")
                T_C  = st.number_input("Temperatura [°C]:", value=25.0, key="bat_Temp")
            with col2:
                tipo_bat = st.selectbox("Tipo batteria:", ["piombo", "Li-ion", "NiMH"], key="bat_tipo")
            if st.button("Correggi per Temperatura", key="bat_btn4"):
                try:
                    r = bat.correzione_temperatura(C_T, T_C, tipo_bat)
                    st.success(f"C corretta = {r['C_corretta_Ah']:.1f} Ah  (riduzione: {r['riduzione_pct']:.1f}%)")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))

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
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Tj [°C]", f"{r['Tj_C']:.1f}")
                    c2.metric("T_case [°C]", f"{r['T_case_C']:.1f}")
                    c3.metric("T_diss [°C]", f"{r['T_diss_C']:.1f}")
                    c4.metric("R_tot [°C/W]", f"{r['R_tot_CW']:.3f}")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))
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
                    st.success(f"R_sa max = {r['R_sa_max_CW']:.3f} °C/W  (budget termico = {r['budget_CW']:.3f} °C/W)")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))
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
            else:
                if st.button("Calcola Derating", key="der_btn"):
                    r = diss.curva_derating(P25, Tj_der, T_max_d)
                    st.write({f"{t:.0f}°C": f"{p:.1f} W" for t, p in zip(r["T_amb_C"], r["P_max_W"])})

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
                    if n_picchetti > 1:
                        r2 = terra.resistenza_picchetti_paralleli(r1["R_ohm"], int(n_picchetti))
                        st.success(f"R singolo picchetto = {r1['R_ohm']:.2f} Ω  →  R equivalente ({int(n_picchetti)} picchetti) = {r2['R_eq_ohm']:.2f} Ω")
                    else:
                        st.success(f"R dispersore = {r1['R_ohm']:.2f} Ω")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))
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
                    st.success(f"Sezione minima PE = {r['S_mm2_minima']:.2f} mm²")
                    st.caption("Arrotondare alla sezione commerciale superiore disponibile.")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))
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
                    colore = "success" if r["conforme"] else "error"
                    getattr(st, colore)(f"U_c = {r['U_c_V']:.2f} V  (limite {UTp} V)  —  {r['giudizio']}")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))
        else:
            col1, col2 = st.columns(2)
            with col1:
                R_tt = st.number_input("Resistenza di terra R [Ω]:", value=20.0, min_value=0.1, key="terra_Rtt")
            with col2:
                I_dn = st.number_input("Corrente diff. nominale I_dn [A]:", value=0.3, min_value=0.001, key="terra_Idn")
            if st.button("Verifica Coordinamento", key="terra_btn4"):
                try:
                    r = terra.coordinamento_tt(R_tt, I_dn)
                    colore = "success" if r["conforme"] else "error"
                    getattr(st, colore)(f"R_max ammessa = {r['R_max_ohm']:.2f} Ω  —  {r['giudizio']}")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))

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
                    colore = "success" if r["selettivo"] else "error"
                    getattr(st, colore)(f"Rapporto = {r['rapporto']:.2f}  (minimo {r['rapporto_minimo']})  —  {r['giudizio']}")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))
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
                    st.info(f"Rapporto I_dn = {r['rapporto_Idn']:.2f}  —  {r['giudizio']}")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))
        elif sub_sel == "Icc minima":
            col1, col2 = st.columns(2)
            with col1:
                V_icc = st.number_input("Tensione V [V]:", value=230.0, min_value=1.0, key="sel_Vicc")
            with col2:
                Z_icc = st.number_input("Impedenza anello di guasto Z [Ω]:", value=0.5, min_value=0.001, key="sel_Zicc")
            if st.button("Calcola Icc min", key="sel_btn3"):
                try:
                    r = selet.corrente_corto_circuito_minima(V_icc, Z_icc)
                    st.success(f"Icc minima = {r['Icc_min_A']:.1f} A")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))
        else:
            col1, col2 = st.columns(2)
            with col1:
                curva_sel = st.selectbox("Tipo curva:", ["B", "C", "D", "K", "Z"], index=1, key="sel_curva")
            with col2:
                I_In = st.number_input("Rapporto I/In:", value=7.0, min_value=0.1, key="sel_I_In")
            if st.button("Verifica Zona", key="sel_btn4"):
                try:
                    r = selet.tempo_intervento_curva(I_In, curva_sel)
                    st.info(f"Zona: {r['zona_intervento']}  (soglia magnetica {r['soglia_min_In']}-{r['soglia_max_In']} In)")
                    st.caption("Curve: " + "  |  ".join([f"**{k}**: {v}" for k, v in selet.CURVE_MAGNETOTERMICI.items()]))
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))

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
                    c1, c2, c3 = st.columns(3)
                    c1.metric("E annua", f"{r['E_anno_kWh']:.0f} kWh")
                    c2.metric("E mensile media", f"{r['E_mese_kWh']:.0f} kWh")
                    c3.metric("Ore equivalenti", f"{r['ore_equivalenti_h']:.0f} h")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))
        elif sub_fv == "Numero pannelli":
            col1, col2 = st.columns(2)
            with col1:
                P_rich = st.number_input("Potenza richiesta [kWp]:", value=6.0, min_value=0.1, key="fv_Prich")
            with col2:
                P_pan = st.number_input("Potenza per pannello [Wp]:", value=450.0, min_value=50.0, key="fv_Ppan")
            if st.button("Calcola Numero Pannelli", key="fv_btn2"):
                try:
                    r = fv.numero_pannelli(P_rich, P_pan)
                    st.success(f"Pannelli necessari: {r['n_pannelli']}  →  Potenza reale: {r['P_reale_kWp']:.2f} kWp")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))
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
                    colore = "success" if r["entro_limiti"] else "error"
                    getattr(st, colore)(f"V stringa a {T_min}°C = {r['V_stringa_V']:.1f} V  —  {r['giudizio']}")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))
            st.markdown("---")
            P_picco_inv = st.number_input("Potenza di picco impianto [kWp]:", value=6.0, min_value=0.1, key="fv_Ppicco_inv")
            if st.button("Suggerisci Inverter", key="fv_btn4"):
                try:
                    r = fv.scelta_inverter(P_picco_inv)
                    st.info(f"Potenza inverter consigliata: {r['P_inverter_kW']:.2f} kW  (DC/AC ratio {r['rapporto_DC_AC']})")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))
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
                    st.success(f"Risparmio annuo: {r['risparmio_anno_eur']:.0f} €  —  Payback: {r['payback_anni']:.1f} anni")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))

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
                    st.success(f"S nominale = {r['S_nom_kVA']:.1f} kVA  →  S di spunto = {r['S_spunto_kVA']:.1f} kVA")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))
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
                    c1, c2 = st.columns(2)
                    c1.metric("Potenza gruppo", f"{r['P_gruppo_kW']:.1f} kW")
                    c2.metric("Potenza apparente", f"{r['S_gruppo_kVA']:.1f} kVA")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))
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
                    st.success(f"Autonomia: {r['t_autonomia_h']:.1f} ore  (consumo {r['consumo_orario_L']:.1f} L/h)")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))

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
                    st.success(f"Potenza totale dissipata: {r['P_tot_W']:.1f} W  ({r['n_componenti']} componenti)")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))
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
                    colore = "success" if r["conforme"] else "error"
                    getattr(st, colore)(f"T interna stimata = {r['T_interna_C']:.1f} °C  (ΔT = {r['delta_T_K']:.1f} K)  —  {r['giudizio']}")
                    st.caption(f"Superficie di scambio: {sup['A_tot_m2']:.2f} m²")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))
        else:
            col1, col2 = st.columns(2)
            with col1:
                P_diss_v = st.number_input("Potenza dissipata [W]:", value=200.0, min_value=0.1, key="qe_Pdissv")
            with col2:
                dT_max = st.number_input("ΔT massimo ammesso [K]:", value=15.0, min_value=1.0, key="qe_dTmax")
            if st.button("Calcola Portata Ventilazione", key="qe_btn3"):
                try:
                    r = qe.portata_ventilazione_forzata(P_diss_v, dT_max)
                    st.success(f"Portata aria necessaria: {r['Q_m3h']:.1f} m³/h")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))

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
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Q reattiva attuale", f"{ra['Q_kvar']:.1f} kvar")
                c2.metric("Q_c necessaria", f"{rc['Q_c_kvar']:.1f} kvar")
                c3.metric("Q_c arrotondato", f"{rc['Q_c_kvar_arrotondato']:.0f} kvar")
                c4.metric("cos_phi risultante", f"{rv['cos_phi_risultante']:.3f}")
                st.info(f"Capacità per fase ({coll_rf}): **{rcap['C_per_fase_uF']:.2f} µF** "
                        f"| Corrente prima: {rv['I_prima_A']:.1f} A → dopo: {rv['I_dopo_A']:.1f} A "
                        f"(riduzione {rv['riduzione_corrente_pct']:.1f}%)")
                if rv["soddisfa_095"]:
                    st.success("cos_phi ≥ 0.95 — obiettivo raggiunto")
                else:
                    st.warning("cos_phi < 0.95 — aumentare la batteria")
            except ValueError as e:
                st.error(str(e))

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
                    r = cadbt.caduta_tensione_trifase(P_cv * 1000.0 / (1.732 * V_cv * cphi_cv), L_cv,
                                                      cadbt.SEZIONI_NORMALIZZATE_MM2[5], cphi_cv, cond_cv)
                    rs = cadbt.sezione_da_caduta_max(P_cv, V_cv, L_cv, dv_max, cphi_cv, "trifase", cond_cv)
                else:
                    r = cadbt.caduta_tensione_monofase(P_cv * 1000.0 / (V_cv * cphi_cv), L_cv,
                                                       cadbt.SEZIONI_NORMALIZZATE_MM2[5], cphi_cv, cond_cv)
                    rs = cadbt.sezione_da_caduta_max(P_cv, V_cv, L_cv, dv_max, cphi_cv, "monofase", cond_cv)
                c1, c2, c3 = st.columns(3)
                c1.metric("Sezione minima calcolata", f"{rs['S_mm2_calcolata']:.2f} mm²")
                c2.metric("Sezione normalizzata", f"{rs['S_mm2_normalizzata']:.0f} mm²")
                c3.metric("Corrente", f"{rs['I_A']:.1f} A")
                rv2 = (cadbt.caduta_tensione_trifase(rs["I_A"], L_cv, rs["S_mm2_normalizzata"], cphi_cv, cond_cv)
                       if tipo_cv == "trifase"
                       else cadbt.caduta_tensione_monofase(rs["I_A"], L_cv, rs["S_mm2_normalizzata"], cphi_cv, cond_cv))
                st.info(f"Con {rs['S_mm2_normalizzata']:.0f} mm² ({cond_cv}): "
                        f"ΔV = {rv2['dV_V']:.2f} V = **{rv2['dV_pct']:.2f}%**")
                (st.success if rv2["conforme_3pct"] else st.warning)(rv2["giudizio"])
            except (ValueError, ZeroDivisionError) as e:
                st.error(str(e))

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
            except (ValueError, ZeroDivisionError) as e:
                st.error(str(e))

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
                        tn = motore_asincrono.caratteristica_tn(r["T_n_nm"], r["n_sync_rpm"], r["s_n"], lam_ma)
                        fig = go.Figure()
                        fig.add_trace(go.Scatter(
                            x=tn["n_rpm"], y=tn["T_nm"], mode="lines",
                            line=dict(color="#2196F3", width=2.5), name="T-n (Kloss)",
                        ))
                        fig.add_trace(go.Scatter(
                            x=[n_ma], y=[r["T_n_nm"]], mode="markers",
                            marker=dict(color="#4CAF50", size=10, symbol="circle"),
                            name=f"Punto nominale ({n_ma:.0f} RPM, {r['T_n_nm']:.1f} N·m)",
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
            except ValueError as e:
                st.error(str(e))

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
            except (ValueError, KeyError) as e:
                st.error(str(e))


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
            if stato == "ROTTURA_CAVO":
                st.error("Rottura cavo o segnale assente: raw sotto soglia minima.")
            elif stato == "FUORI_RANGE":
                st.warning(f"Valore fuori range - estrapolato: {ris:.4f}")
                pct = (val_grezzo - in_min) / (in_max - in_min) if in_max != in_min else 0
                st.progress(min(max(pct, 0.0), 1.0))
            else:
                st.success(f"Valore scalato: {ris:.4f}")
                pct = (ris - out_min) / (out_max - out_min) if out_max != out_min else 0
                st.progress(min(max(pct, 0.0), 1.0))
                st.caption(f"{pct * 100.0:.1f}% del fondo scala")

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
            if stato_inv == "FUORI_RANGE":
                st.warning(f"Setpoint fuori range - raw estrapolato: {raw:.1f}")
            else:
                st.success(f"Valore raw da scrivere nel PLC: {raw:.1f} (INT: {int(round(raw))})")

    elif tool_plc == "Esplosione Parola nei Bit":
        val_w = st.number_input("Valore numerico WORD (0-65535):", min_value=0, max_value=65535, value=0, key="esp_val")
        st.info(f"Dec: {val_w} | Hex: 16#{val_w:04X} | Bin: {val_w:016b}")
        bits = automazione.calcola_esplosione_bits(val_w)
        c1, c2 = st.columns(2)
        for idx, b_v in enumerate(bits):
            with (c1 if idx < 8 else c2):
                st.write(f"Bit {idx:02d} -> {b_v}")

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

    elif tool_plc == "Calcolo Memoria RX3i":
        pref = st.selectbox("Area Memoria:", ["%R", "%M", "%I", "%Q", "%AI", "%AQ"], key="mem_pref")
        start = st.number_input("Indirizzo inizio:", min_value=1, value=1, key="mem_start")
        t_var = st.selectbox("Tipo variabile:", ["1 Bit (Digital I/O)", "16 Bit (WORD / INT)", "32 Bit (REAL / DINT)"], key="mem_tipo")
        qta = st.number_input("Quantita (Array Size):", min_value=1, value=1, key="mem_qta")
        if st.button("Calcola", key="mem_btn"):
            intervallo = automazione.calcola_limiti_memoria_rx3i(pref, start, qta, t_var)
            st.success(f"Intervallo occupato: {intervallo}")
            if t_var == "1 Bit (Digital I/O)" and pref == "%R":
                n_reg = math.ceil(int(qta) / 16)
                st.caption(f"In area %R i BOOL sono packed: {int(qta)} bit occupano {n_reg} registro/i da 16 bit.")


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
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Spostamento pk-pk",   f"{r['spostamento_pkpk_mm']:.4g} mm")
                    st.metric("Spostamento peak",     f"{r['spostamento_pk_mm']:.4g} mm")
                    st.metric("Velocita peak",        f"{r['velocita_pk_mms']:.4g} mm/s")
                    st.metric("Velocita RMS",         f"{r['velocita_rms_mms']:.4g} mm/s")
                with col2:
                    st.metric("Accelerazione peak",   f"{r['accelerazione_pk_ms2']:.4g} m/s²")
                    st.metric("Accelerazione RMS",    f"{r['accelerazione_rms_ms2']:.4g} m/s²")
                    st.metric("Accelerazione peak",   f"{r['accelerazione_pk_g']:.4g} g")
                    st.metric("Accelerazione RMS",    f"{r['accelerazione_rms_g']:.4g} g")
                st.caption(f"ω = {r['omega_rad_s']:.4f} rad/s")
            except ValueError as e:
                st.error(str(e))

    # ------------------------------------------------------------------
    elif tool_vib == "Classificazione ISO 10816 (Severita)":
        st.subheader("Severita vibrazionale secondo ISO 10816-1")
        classi = vibrazioni.lista_classi_iso10816()
        classe_sel = st.selectbox("Classe macchina:", classi, key="iso_classe")
        v_rms = st.number_input("Velocita RMS misurata [mm/s]:", value=1.0, min_value=0.0, format="%.4g", key="iso_vrms")

        if st.button("Classifica", key="iso_btn"):
            try:
                zona, colore, descr, lim = vibrazioni.classifica_iso10816(v_rms, classe_sel)
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
            except ValueError as e:
                st.error(str(e))

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
                st.success(f"Frequenza naturale fn: {r['fn_hz']:.4f} Hz  |  ωn: {r['omega_n_rad_s']:.4f} rad/s")
                st.info(f"Periodo T: {r['T_s']:.4f} s  |  Regime: {r['regime']}")
                if usa_smorzamento and zeta_val < 1.0 and zeta_val > 0:
                    st.info(f"Frequenza smorzata fd: {r['fd_hz']:.4f} Hz  |  ωd: {r['omega_d_rad_s']:.4f} rad/s")
                    if r['Q'] != float('inf'):
                        st.info(f"Fattore Q (amplificazione a risonanza): {r['Q']:.2f}")
                with st.expander("Dettagli smorzatore"):
                    st.write(f"Smorzamento critico cc: {r['c_critico_ns_m']:.2f} N·s/m")
                    st.write(f"Smorzamento reale c: {r['c_reale_ns_m']:.2f} N·s/m")
                    st.write(f"ζ = {r['zeta']:.4f}")
            except ValueError as e:
                st.error(str(e))

    # ------------------------------------------------------------------
    elif tool_vib == "Velocita Critica Albero":
        st.subheader("Velocita critica di un albero rotante (metodo freccia statica)")
        st.caption("Formula di Rankine: Nc = (30/π) · √(g / δ). Inserire la freccia statica misurata o calcolata dall'analisi strutturale.")
        delta = st.number_input("Freccia statica δ [mm]:", value=0.5, min_value=0.001, format="%.6g", key="vc_delta")

        if st.button("Calcola", key="vc_btn"):
            try:
                r = vibrazioni.calcola_velocita_critica(delta)
                st.success(f"Velocita critica Nc: {r['Nc_rpm']:.1f} RPM  ({r['fn_critica_hz']:.3f} Hz)")
                st.warning(
                    f"Zona proibita (±20%): {r['zona_proibita_bassa']:.0f} ÷ {r['zona_proibita_alta']:.0f} RPM — "
                    "evitare esercizio prolungato in questo intervallo."
                )
                with st.expander("Dettagli"):
                    st.write(f"ωc = {r['omega_critica_rad_s']:.4f} rad/s")
                    st.write("Il metodo della freccia statica (Rankine) è conservativo: fornisce una stima della prima velocità critica flessionale. Per alberi con più masse o geometria complessa usare FEM o metodo di Dunkerley.")
            except ValueError as e:
                st.error(str(e))

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
                st.success(f"Squilibrio massimo ammissibile: {r['U_max_gmm']:.2f} g·mm  ({r['U_max_kgmm']:.4f} kg·mm)")
                st.info(f"Eccentricita massima e_max: {r['e_max_mm']:.4f} mm")
                st.info(f"Massa di correzione max al raggio {raggio_corr:.0f} mm: {r['massa_corr_max_g']:.3f} g")
                with st.expander("Come usare il risultato"):
                    st.write("1. Misurare lo squilibrio effettivo con la bilanciatrice (in g·mm).")
                    st.write(f"2. Se squilibrio misurato ≤ {r['U_max_gmm']:.2f} g·mm → conforme al grado G {grado_val}.")
                    st.write(f"3. Altrimenti aggiungere/rimuovere masse al piano di correzione (raggio {raggio_corr:.0f} mm) fino a rientrare nel limite.")
            except ValueError as e:
                st.error(str(e))


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
                st.success(f"Velocita uscita: {r['n2_rpm']:.2f} RPM  |  Coppia uscita: {r['T2_nm']:.3f} N·m")
                st.info(f"P ingresso: {r['P_in_kW']:.4f} kW  |  P uscita: {r['P_out_kW']:.4f} kW  |  Perdita: {r['perdita_kW']:.4f} kW")
            except ValueError as e:
                st.error(str(e))

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
                st.success(f"i_tot = {r['i_tot']:.3f}  |  eta_tot = {r['eta_tot']:.4f}")
                st.info(f"Uscita: {r['n_out_rpm']:.2f} RPM  |  {r['T_out_nm']:.3f} N·m  |  {r['P_out_kW']:.4f} kW")
                with st.expander("Dettaglio per stadio"):
                    for s in r["stadi"]:
                        st.write(f"Stadio {s['stadio']}: {s['n_in_rpm']:.1f} → {s['n_out_rpm']:.1f} RPM  |  T_out = {s['T_out_nm']:.2f} N·m  |  i={s['i']}  eta={s['eta']}")
            except ValueError as e:
                st.error(str(e))

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
                st.success(f"Rapporto i = {r['i']:.3f}  |  Lunghezza cinghia: {r['L_cinghia_mm']:.1f} mm")
                st.info(f"Angolo avvolgimento puleggia piccola: {r['alpha_piccola_deg']:.1f}°  (min. consigliato: 120°)")
                if r["alpha_piccola_deg"] < 120:
                    st.warning("Angolo di avvolgimento < 120°: rischio slittamento. Aumentare l'interasse o usare un tenditore.")
            except ValueError as e:
                st.error(str(e))

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
                st.success(f"P = {r['P_kW']:.4f} kW  |  T = {r['T_nm']:.4f} N·m  |  n = {r['n_rpm']:.2f} RPM")
                st.caption(f"ω = {r['omega_rad_s']:.4f} rad/s")
            except ValueError as e:
                st.error(str(e))

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
                st.success(f"P idraulica: {r['P_id_kW']:.3f} kW  |  P assorbita: {r['P_ass_kW']:.3f} kW")
                st.info(f"Perdite meccaniche: {r['perdita_kW']:.3f} kW")
            except ValueError as e:
                st.error(str(e))

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
                if r["NPSH_d_m"] > 0:
                    st.success(f"NPSH disponibile: {r['NPSH_d_m']:.3f} m")
                else:
                    st.error(f"NPSH disponibile: {r['NPSH_d_m']:.3f} m — CAVITAZIONE CERTA")
                st.caption(r["avvertimento"])
                with st.expander("Dettagli"):
                    st.write(f"Termine pressione: {r['termine_pressione_m']:.3f} m")
                    st.write(f"Termine velocita: {r['termine_velocita_m']:.4f} m")
            except ValueError as e:
                st.error(str(e))

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
                st.success(f"ns = {r['ns']:.1f}")
                st.info(r["tipo"])
            except ValueError as e:
                st.error(str(e))

    elif tool_mec == "Proprieta Sezione":
        tipo_sez = st.selectbox("Forma sezione:", ["Rettangolo", "Cerchio pieno", "Tubo", "Doppio T (HEA/IPE)"], key="sez_tipo")
        if tipo_sez == "Rettangolo":
            c1, c2 = st.columns(2)
            b_s = c1.number_input("Base b [mm]:", value=50.0, min_value=0.1, key="sez_b")
            h_s = c2.number_input("Altezza h [mm]:", value=100.0, min_value=0.1, key="sez_h")
            if st.button("Calcola", key="sez_btn"):
                r = rm.sezione_rettangolare(b_s, h_s)
                st.success(f"A = {r['A_mm2']:.2f} mm²  |  I = {r['I_mm4']:.2f} mm⁴  |  W = {r['W_mm3']:.2f} mm³")
        elif tipo_sez == "Cerchio pieno":
            d_s = st.number_input("Diametro d [mm]:", value=50.0, min_value=0.1, key="sez_d")
            if st.button("Calcola", key="sez_btn"):
                r = rm.sezione_cerchio_pieno(d_s)
                st.success(f"A = {r['A_mm2']:.2f} mm²  |  I = {r['I_mm4']:.2f} mm⁴  |  W = {r['W_mm3']:.2f} mm³")
        elif tipo_sez == "Tubo":
            c1, c2 = st.columns(2)
            D_s = c1.number_input("Diametro esterno D [mm]:", value=60.0, min_value=0.1, key="sez_De")
            d_s = c2.number_input("Diametro interno d [mm]:", value=50.0, min_value=0.0, key="sez_di")
            if st.button("Calcola", key="sez_btn"):
                try:
                    r = rm.sezione_tubo(D_s, d_s)
                    st.success(f"A = {r['A_mm2']:.2f} mm²  |  I = {r['I_mm4']:.2f} mm⁴  |  W = {r['W_mm3']:.2f} mm³")
                except ValueError as e:
                    st.error(str(e))
        else:
            c1, c2, c3, c4 = st.columns(4)
            h_dt = c1.number_input("Altezza H [mm]:", value=200.0, min_value=1.0, key="dt_h")
            b_dt = c2.number_input("Larghezza B [mm]:", value=100.0, min_value=1.0, key="dt_b")
            tw_dt = c3.number_input("Anima tw [mm]:", value=5.5, min_value=0.5, key="dt_tw")
            tf_dt = c4.number_input("Flangia tf [mm]:", value=8.5, min_value=0.5, key="dt_tf")
            if st.button("Calcola", key="sez_btn"):
                try:
                    r = rm.sezione_hea_ipn(h_dt, b_dt, tw_dt, tf_dt)
                    st.success(f"A = {r['A_mm2']:.2f} mm²  |  I = {r['I_mm4']:.2f} mm⁴  |  W = {r['W_mm3']:.2f} mm³")
                except ValueError as e:
                    st.error(str(e))

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
                if r["verificata"]:
                    st.success(f"VERIFICATA — sigma_max = {r['sigma_max_mpa']:.2f} MPa  |  CS = {r['CS']:.2f}")
                else:
                    st.error(f"NON VERIFICATA — sigma_max = {r['sigma_max_mpa']:.2f} MPa > {sigma_amm_tr:.1f} MPa")
                st.info(f"M_max = {r['M_max_Nm']:.2f} N·m  |  Freccia max = {r['f_max_mm']:.3f} mm")
                with st.expander("Dettagli"):
                    st.write(f"Schema: {r['descrizione']}")
                    st.write(f"Reazione A: {r['R_A_N']:.1f} N  |  Reazione B: {r['R_B_N']:.1f} N")
            except ValueError as e:
                st.error(str(e))

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
                if r["verificata"]:
                    st.success(f"VERIFICATA — sigma = {r['sigma_max_mpa']:.2f} MPa  |  CS = {r['CS']:.2f}")
                else:
                    st.error(f"NON VERIFICATA — sigma = {r['sigma_max_mpa']:.2f} MPa  |  W minimo richiesto: {r['W_min_mm3']:.0f} mm³")
                _barra_utilizzo(r["sigma_max_mpa"] / s_vf * 100.0, "Utilizzo tensione (σ / σ_amm)")
            except ValueError as e:
                st.error(str(e))

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
                if r["verificata"]:
                    st.success(f"VERIFICATA — sigma = {r['sigma_mpa']:.2f} MPa  ({r['tipo']})  |  CS = {r['CS']:.2f}")
                else:
                    st.error(f"NON VERIFICATA — sigma = {r['sigma_mpa']:.2f} MPa > {sigma_amm_tc:.1f} MPa")
                st.info(f"Deformazione unitaria: {r['epsilon']:.6f}  |  Variazione lunghezza: {r['delta_mm']:.4f} mm")
            except ValueError as e:
                st.error(str(e))

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
                st.success(f"K totale = {r['K_tot']:.3f}  |  ΔP = {r['dP_Pa']:.1f} Pa  ({r['dP_mbar']:.2f} mbar)  |  h_f = {r['h_f_m']:.4f} m")
                with st.expander("Dettaglio per raccordo"):
                    for d in r["dettaglio"]:
                        st.write(f"{d['n']}× {d['nome']}  →  K parziale = {d['K_parziale']:.3f}")
            except ValueError as e:
                st.error(str(e))

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
                c1, c2, c3 = st.columns(3)
                c1.metric("Velocità", f"{r['v_ms']:.2f} m/s")
                c2.metric("ΔP", f"{r['dP_bar']:.4f} bar")
                c3.metric("Perdita h", f"{r['h_perdita_m']:.3f} m")
                st.info(f"Re = {r['Re']:.0f}  ({r['regime']})  |  f Darcy = {r['f_darcy']:.4f}  |  ΔP = {r['dP_kPa']:.2f} kPa")
            except (ValueError, ZeroDivisionError) as e:
                st.error(str(e))
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
                st.success(f"Diametro minimo: {r['D_minimo_mm']:.1f} mm")
            except (ValueError, ZeroDivisionError) as e:
                st.error(str(e))

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
            except ValueError as e:
                st.error(str(e))

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
            except ValueError as e:
                st.error(str(e))

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
                st.success(f"Bulloni necessari: {r['n_bulloni']}× {r['diametro']} cl. {r['classe']}")
                st.info(f"F per bullone: {r['F_per_bullone']:.0f} N  |  Precarico F_p: {r['F_p_bullone']:.0f} N  |  Coppia serraggio: {r['M_a_Nm']:.2f} N·m")
            except ValueError as e:
                st.error(str(e))

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
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Q [m³/h]", f"{r['Q_m3h']:.1f}")
                    c2.metric("Q [t/h]", f"{r['Q_th']:.1f}")
                    c3.metric("Q eff. [t/h]", f"{r['Q_th_eff']:.1f}")
                    st.info(f"Sezione di carico A = {r['A_m2']:.4f} m²  |  Larghezza utile b_eff = {r['b_eff_m']:.3f} m")
                except ValueError as e:
                    st.error(str(e))
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
                    c1, c2, c3 = st.columns(3)
                    c1.metric("P motore", f"{r['P_motore_kW']:.2f} kW")
                    c2.metric("P utile", f"{r['P_utile_W']/1000:.2f} kW")
                    c3.metric("P sollevamento", f"{r['P_sollevamento_W']/1000:.2f} kW")
                    _barra_utilizzo(r["eta"] * 100, "Rendimento trasmissione")
                except ValueError as e:
                    st.error(str(e))
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
                    c1, c2, c3 = st.columns(3)
                    c1.metric("F periferica", f"{r['F_periferica_N']:.0f} N")
                    c2.metric("T lato teso", f"{r['T_stretto_N']:.0f} N")
                    c3.metric("T lato molle", f"{r['T_molle_N']:.0f} N")
                    if "coppia_Nm" in r:
                        st.info(f"Coppia su puleggia: {r['coppia_Nm']:.1f} N·m")
                except ValueError as e:
                    st.error(str(e))
        else:
            tipo_mat = st.selectbox("Tipo materiale:", ["secco", "umido", "granuloso", "polveri"], key="nas_tipomat")
            rho_ang  = st.number_input("Densità apparente [kg/m³]:", value=800.0, key="nas_rhoang")
            if st.button("Mostra Angoli", key="nas_btn4"):
                try:
                    r = nastri.angolo_max_inclinazione(rho_ang, tipo_mat)
                    st.success(f"Angolo tipico: {r['angolo_tipico_deg']}°  |  Angolo max: {r['angolo_max_deg']}°")
                    st.caption(r["note"])
                except ValueError as e:
                    st.error(str(e))

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
                c1, c2, c3 = st.columns(3)
                c1.metric("L10", f"{r1['L10_milioni_giri']:.1f} milioni giri")
                c2.metric("L10h", f"{r2['L10h']:.0f} ore")
                c3.metric("Anni (8h/die, 250gg)", f"{r2['L10h_anni_8h_die_250gg']:.1f}")
            except (ValueError, ZeroDivisionError) as e:
                st.error(str(e))
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
                st.success(f"Carico dinamico equivalente P_eq = {r['P_eq_kN']:.2f} kN")
            except (ValueError, ZeroDivisionError) as e:
                st.error(str(e))

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
                    c1, c2 = st.columns(2)
                    c1.metric("k", f"{r['k_N_mm']:.3f} N/mm")
                    c2.metric("Indice molla C", f"{r['indice_molla_C']:.1f}")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))
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
                    st.success(f"τ = {r['tau_MPa']:.1f} MPa  (fattore di Wahl Kw = {r['Kw_wahl']:.3f})")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))
        elif sub_molle == "Frequenza naturale":
            col1, col2 = st.columns(2)
            with col1:
                k_freq = st.number_input("Costante elastica k [N/mm]:", value=2.0, min_value=0.01, key="molle_kfreq")
            with col2:
                m_freq = st.number_input("Massa applicata [kg]:", value=1.0, min_value=0.001, key="molle_mfreq")
            if st.button("Calcola Frequenza", key="molle_btn3"):
                try:
                    r = molle.frequenza_naturale_molla(k_freq, m_freq)
                    st.success(f"Frequenza naturale f = {r['f_Hz']:.2f} Hz  (ω = {r['omega_rad_s']:.2f} rad/s)")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))
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
                    st.success(f"k_θ = {r['k_theta_Nmm_rad']:.2f} N·mm/rad  ({r['k_theta_Nmm_grad']:.2f} N·mm/grado)")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))

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
                    c1, c2, c3 = st.columns(3)
                    c1.metric("d primitivo", f"{r['d_primitivo_mm']:.1f} mm")
                    c2.metric("d esterno", f"{r['d_esterno_mm']:.1f} mm")
                    c3.metric("d interno", f"{r['d_interno_mm']:.1f} mm")
                    st.info(f"Passo = {r['passo_mm']:.2f} mm")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))
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
                    st.success(f"Modulo minimo richiesto: {r['m_minimo_mm']:.2f} mm  (forza tangenziale stimata {r['Ft_stimata_N']:.0f} N)")
                    st.caption("Arrotondare al modulo normalizzato superiore (es. 1, 1.25, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10...).")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))
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
                    c1, c2 = st.columns(2)
                    c1.metric("Forza tangenziale Ft", f"{r['Ft_N']:.0f} N")
                    c2.metric("Tensione flessione σ", f"{r['sigma_flessione_MPa']:.1f} MPa")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))
        else:
            col1, col2 = st.columns(2)
            with col1:
                z1_rd = st.number_input("Denti pignone z1:", value=20, min_value=1, step=1, key="rd_z1")
            with col2:
                z2_rd = st.number_input("Denti ruota z2:", value=60, min_value=1, step=1, key="rd_z2")
            if st.button("Calcola Rapporto", key="rd_btn4"):
                try:
                    r = rd.rapporto_trasmissione_ruote(int(z1_rd), int(z2_rd))
                    st.success(f"τ = {r['tau']:.3f}  ({'Riduzione' if r['riduzione'] else 'Moltiplica'})")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))

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
                    st.success(f"Momento torcente: **{r['Mt_Nm']:.2f} N·m**")
                except ValueError as e:
                    st.error(str(e))
        elif sub_alb == "Diametro minimo":
            col1, col2 = st.columns(2)
            with col1:
                Mt_alb = st.number_input("Momento torcente Mt [N·m]:", value=100.0, min_value=0.01, key="alb_Mt")
            with col2:
                tau_alb = st.number_input("Tensione ammissibile τ [MPa]:", value=float(props["Re_MPa"] // 3), min_value=1.0, key="alb_tau")
            if st.button("Calcola Diametro", key="alb_btn2"):
                try:
                    r = alb.diametro_minimo_torsione(Mt_alb, tau_alb)
                    st.success(f"d_min = {r['d_min_mm']:.2f} mm → normalizzato: **{r['d_normalizzato_mm']} mm**")
                except ValueError as e:
                    st.error(str(e))
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
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("τ torsione", f"{r['tau_MPa']:.1f} MPa")
                    c2.metric("σ flessione", f"{r['sigma_flessione_MPa']:.1f} MPa")
                    c3.metric("σ eq (Von Mises)", f"{r['sigma_eq_MPa']:.1f} MPa")
                    c4.metric("n statico", f"{r['n_statico']:.2f}")
                    (st.success if r["conforme"] else st.error)(r["giudizio"])
                except ValueError as e:
                    st.error(str(e))
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
                    c1, c2 = st.columns(2)
                    c1.metric("n Goodman", f"{r['n_Goodman']:.2f}")
                    c2.metric("n Gerber", f"{r['n_Gerber']:.2f}")
                    (st.success if r["conforme_goodman"] else st.error)(r["giudizio"])
                except ValueError as e:
                    st.error(str(e))

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
                    c1, c2, c3 = st.columns(3)
                    c1.metric("A gola", f"{r['A_gola_mm2']:.0f} mm²")
                    c2.metric("τ par", f"{r['tau_par_MPa']:.1f} MPa")
                    c3.metric("Utilizzazione", f"{r['utilizzazione']*100:.1f}%")
                    (st.success if r["conforme"] else st.error)(r["giudizio"])
                except ValueError as e:
                    st.error(str(e))
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
                    c1, c2, c3 = st.columns(3)
                    c1.metric("σ perp", f"{r['sigma_perp_MPa']:.1f} MPa")
                    c2.metric("τ perp", f"{r['tau_perp_MPa']:.1f} MPa")
                    c3.metric("Utilizzazione", f"{r['utilizzazione']*100:.1f}%")
                    (st.success if r["conforme"] else st.error)(r["giudizio"])
                except ValueError as e:
                    st.error(str(e))
        else:
            t_sald = st.number_input("Spessore minimo dei pezzi [mm]:", value=10.0, min_value=1.0, key="sald_t")
            if st.button("Calcola Gola Minima", key="sald_btn3"):
                try:
                    r = sald.gola_minima(t_sald)
                    st.success(f"Gola minima a_min = **{r['a_min_mm']:.1f} mm** (per t = {r['t_pezzi_mm']:.0f} mm)")
                    ra = sald.resistenza_ammissibile_cordone(acciaio_s)
                    st.info(f"Resistenza cordone {acciaio_s}: f_vw,d = {ra['f_vwd_MPa']:.1f} MPa")
                except ValueError as e:
                    st.error(str(e))

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
                    c1, c2, c3 = st.columns(3)
                    c1.metric("t calcolato", f"{r['t_calc_mm']:.2f} mm")
                    c2.metric("t minimo (+ corros.)", f"{r['t_min_mm']:.2f} mm")
                    c3.metric("t normalizzato", f"{r['t_normalizzato_mm']:.1f} mm")
                    st.info(f"D interno con t adottato: {r['D_interno_mm']:.1f} mm")
                except ValueError as e:
                    st.error(str(e))
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
                    st.success(f"Pressione ammissibile: **{r['P_amm_bar']:.2f} bar** ({r['P_amm_MPa']:.3f} MPa)")
                except ValueError as e:
                    st.error(str(e))
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
                    c1, c2, c3 = st.columns(3)
                    c1.metric("t minimo richiesto", f"{r['t_min_mm']:.2f} mm")
                    c2.metric("t adottato", f"{r['t_adottato_mm']:.1f} mm")
                    c3.metric("Utilizzazione", f"{r['utilizzazione']*100:.1f}%")
                    (st.success if r["conforme"] else st.error)(r["giudizio"])
                except ValueError as e:
                    st.error(str(e))


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
            "Valvola di Controllo Cv/Kv",
            "Trasduttore di Pressione 4-20mA",
        ],
        key="strum_tool",
    )

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
                st.success(f"Portata reale: {r['Qr_l_min']:.2f} l/min  ({r['Qr_m3h']:.4f} m³/h)")
                st.info(f"Pressione assoluta: {r['P_abs_bar']:.4f} bar  |  Rapporto espansione: 1/{1/r['rapporto_esp']:.2f}")
            except ValueError as e:
                st.error(str(e))

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
                pct_color = "error" if r["dP_pct"] > 5.0 else ("warning" if r["dP_pct"] > 3.0 else "success")
                getattr(st, pct_color)(f"ΔP = {r['dP_mbar']:.2f} mbar  ({r['dP_pct']:.2f}% della pressione assoluta)")
                st.info(f"Velocita aria: {r['velocita_ms']:.2f} m/s  |  Re = {r['Re']:.0f}  |  λ = {r['lambda']:.4f}")
                if r["dP_pct"] > 5.0:
                    st.warning("Caduta > 5%: aumentare il diametro della tubazione.")
            except ValueError as e:
                st.error(str(e))

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
                st.success(f"Volume minimo serbatoio: {r['V_litri']:.1f} litri  ({r['V_m3']:.4f} m³)")
                st.caption(f"ΔP ciclo: {r['delta_P_bar']:.1f} bar  |  P ciclo: {r['P_min_abs']:.3f} → {r['P_max_abs']:.3f} bar a")
            except ValueError as e:
                st.error(str(e))

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
                st.success(f"Potenza assorbita: {r['P_kW']:.2f} kW  (P ideale: {r['P_id_kW']:.2f} kW)")
                st.info(f"Rapporto di compressione totale: {r['beta_tot']:.2f}  |  Temp. uscita: {r['T_out_C']:.1f} °C")
                if ns_cmp == 2:
                    st.caption(f"Rapporto per stadio: {r['beta_stadio']:.2f}")
            except ValueError as e:
                st.error(str(e))

    elif tool_strum == "Segnale mA ↔ Tensione":
        col1, col2 = st.columns(2)
        with col1:
            ma_val = st.number_input("Corrente loop [mA]:", value=12.0, min_value=0.0, max_value=25.0, key="ma_i")
        with col2:
            shunt  = st.number_input("Resistenza shunt [Ω]:", value=250.0, min_value=1.0, key="ma_r")
        if st.button("Converti", key="ma_btn"):
            try:
                r = strumentazione.converti_ma_tensione(ma_val, shunt)
                st.success(f"{ma_val} mA su {shunt} Ω = {r['tensione_V']:.4f} V  ({r['tensione_mV']:.2f} mV)")
                if r["pct_4_20"] is not None:
                    st.info(f"Posizione nel range 4-20 mA: {r['pct_4_20']:.1f}%")
                    st.progress(min(max(r["pct_4_20"] / 100.0, 0.0), 1.0))
                st.caption(f"Potenza dissipata sullo shunt: {r['potenza_mW']:.3f} mW")
            except ValueError as e:
                st.error(str(e))

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
                st.success(f"Tipo {tipo_tc}: {mv_tc:.4f} mV → {r['temperatura_C']:.2f} °C")
                st.caption(f"Range valido: {r['range_mv'][0]:.3f} → {r['range_mv'][1]:.3f} mV")
            except ValueError as e:
                st.error(str(e))

    elif tool_strum == "Pt100 — Temperatura ↔ Resistenza":
        st.subheader("Pt100 secondo IEC 60751 (Callendar-Van Dusen)")
        direzione = st.radio("Direzione:", ["T → R  (calcola resistenza dalla temperatura)", "R → T  (calcola temperatura dalla resistenza)"], key="pt_dir")
        if "T → R" in direzione:
            T_pt = st.number_input("Temperatura [°C]:", value=100.0, min_value=-200.0, max_value=850.0, key="pt_t")
            if st.button("Calcola R", key="pt_btn"):
                try:
                    R = strumentazione.pt100_t_a_r(T_pt)
                    st.success(f"{T_pt:.2f} °C → {R:.4f} Ω")
                except ValueError as e:
                    st.error(str(e))
        else:
            R_pt = st.number_input("Resistenza [Ω]:", value=138.5, min_value=18.0, max_value=390.0, format="%.4f", key="pt_r")
            if st.button("Calcola T", key="pt_btn"):
                try:
                    r = strumentazione.pt100_r_a_t(R_pt)
                    st.success(f"{R_pt:.4f} Ω → {r['temperatura_C']:.3f} °C")
                except ValueError as e:
                    st.error(str(e))

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
                st.success(f"Errore assoluto: ±{r['errore_assoluto']:.4f}  |  Errore relativo: {r['errore_relativo_pct']:.2f}%")
                st.info(f"Incertezza combinata (RSS): ±{r['incertezza_comb']:.4f}")
                st.info(f"Valore vero stimato: [{r['valore_min']:.4f} → {r['valore_max']:.4f}]")
            except ValueError as e:
                st.error(str(e))

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
                    c1, c2 = st.columns(2)
                    c1.metric("Kv [m³/h/√bar]", f"{r['Kv']:.3f}")
                    c2.metric("Cv [US gpm/√psi]", f"{r['Cv']:.3f}")
                    st.caption("Caratteristiche: " + "  |  ".join([f"**{k}**: {v}" for k, v in valvole.CARATTERISTICHE.items()]))
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))
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
                    c1, c2 = st.columns(2)
                    c1.metric("Kv", f"{r['Kv']:.3f}")
                    c2.metric("Cv", f"{r['Cv']:.3f}")
                    if r["choked_flow"]:
                        st.warning(f"Flusso bloccato (choked flow)! P_critica = {r['P_critica_bar_a']:.2f} bar a  — ΔP effettivo = {r['dP_effettivo_bar']:.2f} bar")
                    else:
                        st.info(f"Flusso non bloccato  |  ΔP effettivo = {r['dP_effettivo_bar']:.2f} bar")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))
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
                    colore = {"BASSA": "success", "MEDIA": "warning", "ALTA": "error"}[r["rischio"]]
                    getattr(st, colore)(f"Rischio cavitazione: {r['rischio']}  |  σ = {r['sigma']:.3f}  |  σ_crit = {r['sigma_crit']:.3f}")
                    st.info(f"ΔP = {r['dP_bar']:.2f} bar  |  FL = {r['FL']:.2f}")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))

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
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Pressione", f"{r['P_bar']:.3f} bar")
                    c2.metric("Pressione", f"{r['P_kPa']:.1f} kPa")
                    c3.metric("% Fondo Scala", f"{r['percentuale_FS']:.1f} %")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))
        elif sub_tp == "Pressione → mA":
            col1, col2 = st.columns(2)
            with col1:
                FS_tp2 = st.selectbox("Fondo scala trasduttore [bar]:", tp.RANGE_COMMERCIALI_BAR, index=1, key="tp_FS2")
            with col2:
                P_tp = st.number_input("Pressione [bar]:", value=10.0, min_value=0.0, key="tp_P")
            if st.button("Convertiti in mA", key="tp_btn2"):
                try:
                    r = tp.pressione_a_ma(P_tp, FS_tp2)
                    st.success(f"Corrente: {r['I_mA']:.2f} mA  ({r['percentuale_FS']:.1f} % FS)")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))
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
                    colore = "success" if r["entro_accuratezza"] else "error"
                    getattr(st, colore)(f"Errore = {r['errore_pct_FS']:.3f} % FS  ({r['errore_bar']:.4f} bar)  —  {r['giudizio']}")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))
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
                    colore = "success" if r["sufficiente"] else "error"
                    getattr(st, colore)(f"Tensione residua al trasduttore: {r['V_residua_trasduttore_V']:.2f} V  —  {r['giudizio']}")
                    st.caption(f"R cavo = {r['R_cavo_ohm']:.2f} Ω  |  Caduta su cavo = {r['V_caduta_cavo_V']:.2f} V  |  Caduta su carico = {r['V_caduta_carico_V']:.2f} V")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))


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
        ],
        key="termo_tool",
    )

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
                Q_kW = r["Q_kW"]
                Tfo = Tfi_sc + r["delta_T_c"]
                st.success(f"Q = {Q_kW:.3f} kW  |  C_h = {r['C_h']:.1f} W/K  |  C_f = {r['C_c']:.1f} W/K")
                st.metric("Temperatura uscita fluido freddo T_f,out", f"{Tfo:.2f} °C")
            except (ValueError, KeyError) as e:
                st.error(str(e))

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
                st.success(f"LMTD = {rl['LMTD_K']:.2f} K  |  Area = {ra['A_m2']:.3f} m²")
                st.info(f"ΔT1 = {rl['dT1_K']:.2f} K  |  ΔT2 = {rl['dT2_K']:.2f} K")
                st.caption("Valori U tipici (W/m²·K): acqua-acqua 800-1500, vapore-acqua 1000-6000, aria-aria 10-50.")
            except ValueError as e:
                st.error(str(e))

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
                st.success(f"NTU = {r['NTU']:.3f}  |  ε = {r['epsilon']:.4f}  ({r['epsilon']*100:.1f}%)")
                st.metric("Potenza termica trasferita Q", f"{r['Q_kW']:.3f} kW")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("T uscita fluido caldo", f"{r['T_h_out']:.2f} °C")
                with col2:
                    st.metric("T uscita fluido freddo", f"{r['T_c_out']:.2f} °C")
                st.caption(f"C_r = C_min/C_max = {r['C_r']:.3f}")
            except ValueError as e:
                st.error(str(e))

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
                st.success(f"Corpi necessari: {r['N_corpi']}  (teorico: {r['N_esatto']:.2f})")
                st.metric("Em effettivo con N corpi installati", f"{r['Em_effettivo']:.1f} lux")
                if r["Em_effettivo"] < Em_il:
                    st.warning("Em effettivo inferiore al richiesto — verificare UF/MF.")
                rp = illuminotecnica.calcola_potenza_illuminazione(r["N_corpi"], P_lamp, A_il)
                st.info(f"Potenza totale: {rp['P_tot_W']:.0f} W  |  LENI: {rp['LENI_W_m2']:.2f} W/m²")
            except ValueError as e:
                st.error(str(e))

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
                st.success(f"k = {r['k']:.3f}  |  Hm = {r['Hm_m']:.2f} m  |  A = {r['A_m2']:.1f} m²")
                st.info(r["note_UF"])
                st.caption(f"Distanza max consigliata tra corpi: {r['d_max_m']:.2f} m")
            except ValueError as e:
                st.error(str(e))

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
                color = "success" if r["MF"] >= 0.80 else ("warning" if r["MF"] >= 0.67 else "error")
                getattr(st, color)(f"MF = {r['MF']:.4f}  ({r['classificazione']})")
                st.caption(f"LMF={r['LMF']:.2f}  ×  LSF={r['LSF']:.2f}  ×  LLMF={r['LLMF']:.2f}  ×  RSMF={r['RSMF']:.2f}")
            except ValueError as e:
                st.error(str(e))

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
                st.success(f"Potenza totale: {r['P_tot_W']:.0f} W  ({r['P_tot_kW']:.3f} kW)")
                st.metric("LENI (Lighting Energy Numeric Indicator)", f"{r['LENI_W_m2']:.2f} W/m²")
                if r["LENI_W_m2"] > 15:
                    st.warning("LENI > 15 W/m²: considerare l'uso di LED più efficienti o ridurre il numero di corpi.")
                elif r["LENI_W_m2"] > 8:
                    st.info("LENI nella norma per ambienti industriali con lampade fluorescenti.")
                else:
                    st.success("LENI ottimo — tipico di impianti LED moderni.")
            except ValueError as e:
                st.error(str(e))

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
                c1, c2, c3 = st.columns(3)
                c1.metric("U [W/m²K]", f"{r['U_W_m2K']:.3f}")
                c2.metric("q [W/m²]", f"{r['q_W_m2']:.1f}")
                c3.metric("R_tot [m²K/W]", f"{r['R_tot_m2KW']:.3f}")
                T_ifaces = r.get("T_interfaces", [])
                if T_ifaces:
                    st.markdown("**Temperature alle interfacce:**")
                    st.text("  →  ".join([f"{t:.1f}°C" for t in T_ifaces]))
                T_rug = iso_t.temperatura_rugiada(T_int_iso, 60.0)
                verif = iso_t.verifica_condensa(T_ifaces[0] if T_ifaces else T_int_iso, T_int_iso, 60.0)
                if verif["rischio_condensa"]:
                    st.warning(f"Rischio condensa! T_sup = {T_ifaces[0]:.1f}°C < T_rugiada = {verif['T_rugiada_C']:.1f}°C (a UR=60%)")
            except (ValueError, ZeroDivisionError) as e:
                st.error(str(e))

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
                c1, c2, c3 = st.columns(3)
                c1.metric("Q totale [W]", f"{r['Q_W']:.1f}")
                c2.metric("q lineare [W/m]", f"{r['Q_W_m']:.2f}")
                c3.metric("D esterno [mm]", f"{r['D_est_mm']:.1f}")
                st.info(f"Resistenza lineare R_lin = {r['R_lin_KW']:.4f} K·m/W")
            except (ValueError, ZeroDivisionError) as e:
                st.error(str(e))

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
                c1, c2, c3 = st.columns(3)
                c1.metric("Volume totale [m³]", f"{V_tot:.3f}")
                c1.metric("Volume [L]", f"{V_tot*1000:.0f}")
                c2.metric("Pressione fondo", f"{pf['P_bar']:.4f} bar")
                c2.metric("Altezza equiv.", f"{pf['P_mca']:.2f} mca")
                c3.metric("Riempimento (10 m³/h)", f"{tf['t_min']:.1f} min")
                c3.metric("P fondo [kPa]", f"{pf['P_kPa']:.2f}")
            except (ValueError, ZeroDivisionError) as e:
                st.error(str(e))

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
                c1, c2, c3 = st.columns(3)
                c1.metric("Tempo [s]", f"{r['t_svuotamento_s']:.0f}")
                c2.metric("Tempo [min]", f"{r['t_svuotamento_min']:.1f}")
                c3.metric("Tempo [h]", f"{r['t_svuotamento_h']:.3f}")
            except (ValueError, ZeroDivisionError) as e:
                st.error(str(e))

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
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Velocità", f"{r['v_ms']:.2f} m/s")
                    c2.metric("Perdita lineare", f"{r['dP_Pa_m']:.2f} Pa/m")
                    c3.metric("Perdita totale", f"{r['dP_Pa_tot']:.0f} Pa")
                    st.info(f"Re = {r['Re']:.0f} ({r['regime']})  |  f = {r['f_darcy']:.4f}")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))
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
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Dh", f"{r['Dh_mm']:.0f} mm")
                    c2.metric("Velocità", f"{r['v_ms']:.2f} m/s")
                    c3.metric("Perdita totale", f"{r['dP_Pa_tot']:.0f} Pa")
                    st.info(f"Re = {r['Re']:.0f} ({r['regime']})  |  ΔP/m = {r['dP_Pa_m']:.2f} Pa/m")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))
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
                    c1, c2, c3 = st.columns(3)
                    c1.metric("D minimo", f"{r['D_min_mm']:.0f} mm")
                    c2.metric("D normalizzato", f"{r['D_normalizzato_mm']} mm")
                    c3.metric("Velocità effettiva", f"{r['v_effettiva_ms']:.2f} m/s")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))
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
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Lato a", f"{r['a_mm']:.0f} mm")
                    c2.metric("Lato b", f"{r['b_mm']:.0f} mm")
                    c3.metric("Dh", f"{r['Dh_mm']:.0f} mm")
                    c4.metric("v effettiva", f"{r['v_effettiva_ms']:.2f} m/s")
                except (ValueError, ZeroDivisionError) as e:
                    st.error(str(e))


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
        ],
        key="sic_tool",
    )

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
                c1, c2, c3 = st.columns(3)
                c1.metric("L_tot", f"{r['L_tot_dB']:.1f} dB")
                c2.metric("L_max sorgente", f"{r['L_max_dB']:.1f} dB")
                c3.metric("Incremento", f"+{r['incremento_dB']:.1f} dB")
                st.info(f"Somma di {r['n_sorgenti']} sorgenti: il livello totale supera la sorgente dominante di {r['incremento_dB']:.1f} dB")
            except (ValueError, ZeroDivisionError) as e:
                st.error(str(e))

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
                colore = "error" if r["LEX_8h_dBA"] >= rumore.LEX_LIMITE_dB else ("warning" if r["LEX_8h_dBA"] >= rumore.LEX_SUPERIORE_dB else ("info" if r["LEX_8h_dBA"] >= rumore.LEX_INFERIORE_dB else "success"))
                getattr(st, colore)(f"LEX,8h = {r['LEX_8h_dBA']:.1f} dB(A)  —  {r['rischio']}")
                c1, c2, c3 = st.columns(3)
                c1.metric("LEX,8h", f"{r['LEX_8h_dBA']:.1f} dB(A)")
                c2.metric("Dose esposizione", f"{r['dose_pct']:.1f} %")
                c3.metric("DPI obbligatori", "SÌ" if r["dpi_obbligo"] else "NO")
                _barra_utilizzo(min(r["dose_pct"], 100), "Dose rispetto al limite 87 dB(A)")
            except (ValueError, ZeroDivisionError) as e:
                st.error(str(e))

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
                colore_dpi = "success" if r["protezione_adeguata"] else "error"
                getattr(st, colore_dpi)(f"L efficace sotto DPI: {r['L_eff_dBA']:.1f} dB(A)  —  {r['giudizio']}")
                c1, c2 = st.columns(2)
                c1.metric("L amb", f"{r['L_amb_dBA']:.1f} dB(A)")
                c2.metric("L eff. DPI", f"{r['L_eff_dBA']:.1f} dB(A)")
            except (ValueError, ZeroDivisionError) as e:
                st.error(str(e))

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
            except (ValueError, ZeroDivisionError) as e:
                st.error(str(e))

    elif tool_sic == "Performance Level — EN ISO 13849":
        st.subheader("Performance Level (PL) e SIL — EN ISO 13849-1")
        sub_pl = st.radio("Calcolo:", ["Calcola PL da parametri", "MTTFd da B10d", "Verifica PLr"], horizontal=True, key="pl_sub")
        if sub_pl == "Calcola PL da parametri":
            col1, col2 = st.columns(2)
            with col1:
                MTTFd_pl = st.number_input("MTTFd canale [anni]:", value=30.0, min_value=0.1, max_value=100.0, key="pl_mttfd")
                DCavg_pl = st.slider("DCavg [%]:", 0, 100, 90, key="pl_dc")
            with col2:
                cat_pl = st.selectbox("Categoria architetturale:", ["B", "1", "2", "3", "4"], index=3, key="pl_cat")
            if st.button("Calcola PL", key="pl_btn1"):
                try:
                    r = pl_iso.calcola_PL(MTTFd_pl, DCavg_pl, cat_pl)
                    c1, c2, c3, c4 = st.columns(4)
                    c1.metric("Performance Level", f"PL {r['PL']}")
                    c2.metric("SIL equivalente", r["SIL"])
                    c3.metric("PFHd [1/h]", f"{r['PFHd_1_h']:.0e}")
                    c4.metric("MTTFd classe", r["MTTFd_classe"])
                    st.info(f"Categoria {r['categoria']}: {r['descrizione_categoria']}")
                    st.caption(f"DC classe: {r['DC_classe']}  |  MTTFd: {r['MTTFd_anni']} anni ({r['MTTFd_classe']})")
                except ValueError as e:
                    st.error(str(e))
        elif sub_pl == "MTTFd da B10d":
            col1, col2 = st.columns(2)
            with col1:
                B10d_pl = st.number_input("B10d [cicli]:", value=2000000.0, min_value=1000.0, key="pl_B10d")
            with col2:
                n_op = st.number_input("Operazioni/anno:", value=52000.0, min_value=1.0, key="pl_nop",
                                        help="Es. 1 op/giorno × 250gg = 250; 200op/giorno × 250gg = 50000")
            if st.button("Calcola MTTFd", key="pl_btn2"):
                try:
                    r = pl_iso.MTTFd_da_B10d(B10d_pl, n_op)
                    st.success(f"MTTFd = **{r['MTTFd_anni']:.1f} anni** ({r['MTTFd_classe']})")
                    if r["nota"]:
                        st.warning(r["nota"])
                except ValueError as e:
                    st.error(str(e))
        else:
            col1, col2 = st.columns(2)
            with col1:
                PL_rag = st.selectbox("PL raggiunto:", ["a", "b", "c", "d", "e"], index=3, key="pl_rag")
            with col2:
                PLr_req = st.selectbox("PLr richiesto:", ["a", "b", "c", "d", "e"], index=3, key="pl_req")
            if st.button("Verifica PLr", key="pl_btn3"):
                try:
                    r = pl_iso.verifica_PLr(PL_rag, PLr_req)
                    (st.success if r["conforme"] else st.error)(r["giudizio"])
                    st.caption(f"SIL raggiunto: {r['SIL_raggiunto']}")
                except ValueError as e:
                    st.error(str(e))


st.markdown("---")
st.caption("Disclaimer: strumento indicativo basato sulle norme tecniche CEI 64-8, ISO 10816, ISO 1940, ISO 1217, IEC 60751, NIST ITS-90. Non sostituisce la progettazione formale di un professionista abilitato.")
