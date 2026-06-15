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
            "Carico Trifase",
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

    elif tipo == "Carico Trifase":
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
            "Bulloneria — Serraggio",
            "Bulloneria — Verifica",
            "Bulloneria — Flangia",
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


st.markdown("---")
st.caption("Disclaimer: strumento indicativo basato sulle norme tecniche CEI 64-8, ISO 10816, ISO 1940, ISO 1217, IEC 60751, NIST ITS-90. Non sostituisce la progettazione formale di un professionista abilitato.")
