# ==============================================================================
# web.py — Interfaccia Streamlit per lo Strumento Multifunzione Industriale
# Nota: ogni widget ha key= esplicito e univoco per evitare StreamlitDuplicateElementId
# ==============================================================================

import math
import streamlit as st
import formule
import idraulica
import automazione
from costanti import TENSIONE_MONOFASE, TENSIONE_TRIFASE, SEZIONI_COMMERCIALI

# ------------------------------------------------------------------------------
st.set_page_config(page_title="Tool Industriale", page_icon="⚙️", layout="centered")
st.title("⚙️ Strumento Multifunzione Industriale")

tab_conv, tab_elett, tab_plc = st.tabs([
    "🔄 Conversioni",
    "⚡ Calcoli Elettrici",
    "🤖 PLC & Automazione",
])

# ==============================================================================
# TAB 1 — CONVERSIONI DI UNITÀ
# ==============================================================================
with tab_conv:
    st.header("🔄 Convertitore di Unità")
    categories = idraulica.ottieni_categorie()

    modo_conv = st.radio(
        "Modalità:",
        ["Da → A (standard)", "Multi-unità live (scrivi in qualsiasi campo)"],
        key="conv_modo", horizontal=True
    )

    # ------------------------------------------------------------------
    # MODALITÀ STANDARD
    # ------------------------------------------------------------------
    if modo_conv == "Da → A (standard)":
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
            st.success(f"**Risultato:** {res:.6g} {to_u}")
        except ValueError as e:
            st.error(str(e))

        if cat in ("Forza", "Massa"):
            st.caption("ℹ️ Forza e Massa sono grandezze fisicamente distinte.")
        if cat == "Pressione" and (from_u in ("barg", "psig") or to_u in ("barg", "psig")):
            st.caption("ℹ️ Le unità 'g' (gauge) sono relative alla pressione atmosferica.")

    # ------------------------------------------------------------------
    # MODALITÀ MULTI-UNITÀ LIVE
    # ------------------------------------------------------------------
    else:
        cat_live = st.selectbox("Grandezza:", list(categories.keys()), key="live_cat")
        units_live = list(categories[cat_live].keys())

        # Prefisso per i key dei widget di questa categoria
        pfx = f"lv_{cat_live}_"
        src_st  = f"lv_src_{cat_live}"   # quale unità è la sorgente attiva

        # Reset quando si cambia categoria
        if st.session_state.get("lv_prev_cat") != cat_live:
            st.session_state["lv_prev_cat"] = cat_live
            st.session_state[src_st] = None
            for u in units_live:
                st.session_state[pfx + u] = 0.0

        source_key  = st.session_state.get(src_st)           # es. "lv_Pressione_bar"
        source_unit = source_key.replace(pfx, "") if source_key else None
        source_val  = float(st.session_state.get(source_key, 0.0)) if source_key else 0.0

        # Calcola tutti i valori dalla sorgente
        computed: dict = {}
        if source_unit and source_unit in units_live:
            for u in units_live:
                try:
                    computed[u] = idraulica.esegui_conversione(
                        cat_live, source_unit, u, source_val
                    )
                except Exception:
                    computed[u] = 0.0
        else:
            computed = {u: 0.0 for u in units_live}

        # Aggiorna session_state dei campi NON-sorgente PRIMA del rendering
        # → così i widget li leggono già aggiornati senza passare value=
        for u in units_live:
            k = pfx + u
            if k != source_key:
                st.session_state[k] = computed.get(u, 0.0)

        # Callback: segna quale campo è diventato la sorgente
        def _make_cb(unit_name: str, _pfx: str = pfx, _src_st: str = src_st):
            def _cb():
                st.session_state[_src_st] = _pfx + unit_name
            return _cb

        # Etichetta dell'unità attiva
        if source_unit:
            st.caption(f"✏️ Stai inserendo in **{source_unit}** — "
                       "scrivi in qualsiasi altro campo per cambiare unità di input.")
        else:
            st.caption("✏️ Scrivi un valore in qualsiasi campo per convertire in tutte le altre unità.")

        # Layout a colonne adattivo
        n_cols = 4 if len(units_live) > 8 else 3 if len(units_live) > 4 else 2
        cols_live = st.columns(n_cols)

        for i, u in enumerate(units_live):
            k = pfx + u
            is_src = (k == source_key)
            label  = f"**{u}** ✏️" if is_src else u
            with cols_live[i % n_cols]:
                st.number_input(
                    label,
                    key=k,
                    format="%.6g",
                    on_change=_make_cb(u),
                )

        # Note specifiche per categoria
        if cat_live == "Pressione":
            st.caption(
                "ℹ️ Le unità **barg** e **psig** sono relative alla pressione atmosferica "
                "(offset +101325 Pa). Il valore zero corrisponde alla pressione ambiente."
            )
        elif cat_live in ("Forza", "Massa"):
            st.caption("ℹ️ Forza (N) e Massa (kg) sono grandezze fisicamente distinte. "
                       "Non convertire tra le due categorie.")
        elif cat_live == "Temperatura":
            st.caption("ℹ️ Conversioni non lineari: usa **r** per Rankine.")


# ==============================================================================
# TAB 2 — CALCOLI ELETTRICI
# ==============================================================================
with tab_elett:
    st.header("⚡ Calcolatore Elettrico")
    tipo = st.selectbox("Tipo di Analisi:", [
        "Legge di Ohm",
        "Analisi Potenze & Estrazione Ampere",
        "Convertitore Potenze (kW / HP / kVA)",
        "Rendimento Motore (P_out → P_in → Corrente)",
        "Rifasamento Industriale (kVAR)",
        "Caduta di Tensione",
        "Corrente di Cortocircuito (Icc)",
        "Dimensionamento Protezioni",
    ], key="elett_tipo")

    # --- Legge di Ohm ---
    if tipo == "Legge di Ohm":
        cerca = st.selectbox("Cosa calcolare?", ["Tensione", "Corrente", "Resistenza"], key="ohm_cerca")
        in1 = st.number_input("Primo Valore:", value=1.0, key="ohm_in1")
        in2 = st.number_input("Secondo Valore:", value=1.0, key="ohm_in2")
        if st.button("Calcola", key="ohm_btn"):
            st.success(formule.calcola_ohm(cerca, in1, in2))

    # --- Potenze & Corrente ---
    elif tipo == "Analisi Potenze & Estrazione Ampere":
        st.subheader("Calcolo Avanzato Potenze e Corrente")
        sis = st.selectbox("Sistema Elettrico:", ["DC", "Monofase", "Trifase"], key="pot_sis")
        obiettivo = st.selectbox("Cosa desideri fare?", [
            "Estrai da Volt e Ampere",
            "Estrai Corrente (Ampere) da Watt",
        ], key="pot_obi")
        v_default = {"Trifase": 400.0, "Monofase": 230.0}.get(sis, 24.0)
        v = st.number_input("Tensione (Volt):", value=v_default, key="pot_v")
        cos_phi = (
            st.number_input("Fattore di potenza (cos φ):", min_value=0.1, max_value=1.0,
                            value=0.85, key="pot_cosphi")
            if sis != "DC" else 1.0
        )

        if obiettivo == "Estrai da Volt e Ampere":
            i = st.number_input("Corrente (Ampere):", value=10.0, key="pot_i")
            if st.button("Analizza Potenze", key="pot_btn_va"):
                res = formule.calcola_potenza_e_corrente(sis, v, i, 0.0, cos_phi, obiettivo)
                if res is None:
                    st.error("Valori non validi: controlla tensione, corrente e cos phi.")
                    res = {
                        "W": math.nan,
                        "kW": math.nan,
                        "VA": math.nan,
                        "kVA": math.nan,
                        "VAR": math.nan,
                        "kVAR": math.nan,
                        "HP": math.nan,
                        "CV": math.nan,
                    }
                st.success(f"🔌 **Potenza Attiva:** {res['W']:.1f} W ({res['kW']:.4f} kW)")
                st.info(f"🐎 **Meccanica:** {res['HP']:.3f} HP | {res['CV']:.3f} CV")
                st.info(f"📊 **Apparente:** {res['VA']:.1f} VA ({res['kVA']:.4f} kVA)")
                if sis != "DC":
                    st.info(f"📉 **Reattiva:** {res['VAR']:.1f} VAR ({res['kVAR']:.4f} kVAR)")
        else:
            w = st.number_input("Potenza in WATT (W):", value=2200.0, step=100.0, key="pot_w")
            if st.button("Estrai Ampere", key="pot_btn_w"):
                res = formule.calcola_potenza_e_corrente(sis, v, 0.0, w, cos_phi, obiettivo)
                if res is None:
                    st.error("Errore: divisione per zero — controlla tensione e cos φ.")
                else:
                    st.success(f"⚡ **Corrente Assorbita:** {res['A']:.2f} A")
                    st.info(f"🐎 **Potenza:** {res['HP']:.3f} HP | {res['CV']:.3f} CV")
                    st.info(f"📊 **Apparente:** {res['VA']:.1f} VA ({res['kVA']:.4f} kVA)")

    # --- Convertitore Potenze ---
    elif tipo == "Convertitore Potenze (kW / HP / kVA)":
        st.subheader("Conversione tra unità di potenza")
        unita_disp = ["W", "kW", "MW", "HP", "CV", "BTU/h", "kVA"]
        col1, col2 = st.columns(2)
        with col1:
            da_u = st.selectbox("Da:", unita_disp, index=1, key="cpot_da")
        with col2:
            a_u  = st.selectbox("A:",  unita_disp, index=3, key="cpot_a")
        val_pot = st.number_input("Valore:", value=1.0, format="%.4f", key="cpot_val")
        cos_phi_conv = 1.0
        if da_u == "kVA" or a_u == "kVA":
            cos_phi_conv = st.number_input(
                "Fattore di potenza (cos φ) — necessario per kVA:",
                min_value=0.1, max_value=1.0, value=0.85, key="cpot_cosphi"
            )
        if st.button("Converti", key="cpot_btn"):
            try:
                ris = formule.converti_potenza(val_pot, da_u, a_u, cos_phi_conv)
                st.success(f"**{val_pot} {da_u} = {ris:.6f} {a_u}**")
            except ValueError as e:
                st.error(str(e))

    # --- Rendimento Motore ---
    elif tipo == "Rendimento Motore (P_out → P_in → Corrente)":
        st.subheader("Da potenza all'albero → assorbimento dalla rete")
        sis_mot  = st.selectbox("Sistema:", ["Trifase", "Monofase"], key="mot_sis")
        p_out    = st.number_input("Potenza meccanica all'albero (P_out) [kW]:", value=11.0,
                                   min_value=0.01, key="mot_pout")
        eta_pct  = st.number_input("Rendimento motore η [%]:", value=92.0,
                                   min_value=1.0, max_value=99.9, key="mot_eta")
        v_mot    = st.number_input("Tensione [V]:",
                                   value=400.0 if sis_mot == "Trifase" else 230.0, key="mot_v")
        cosphi_m = st.number_input("cos φ (da targa motore):", min_value=0.1, max_value=1.0,
                                   value=0.85, key="mot_cosphi")
        if st.button("Calcola assorbimento", key="mot_btn"):
            res_m = formule.calcola_ingresso_motore(p_out, eta_pct, sis_mot, v_mot, cosphi_m)
            if res_m is None:
                st.error("Valori non validi: controlla potenza, rendimento, tensione e cos phi.")
            else:
                st.success(
                    f"🔌 **Potenza assorbita dalla rete:** {res_m['P_in_kW']:.3f} kW "
                    f"({res_m['P_in_W']:.0f} W)"
                )
                st.info(
                    f"⚡ **Corrente di linea:** {res_m['I_A']:.2f} A "
                    f"| 📊 **Apparente:** {res_m['P_app_kVA']:.3f} kVA"
                )
                st.info(f"🐎 **Potenza ingresso:** {res_m['HP_in']:.2f} HP")
                with st.expander("Dettagli"):
                    st.write(f"Rendimento: {res_m['eta']*100:.1f}% — "
                             f"energia persa in calore: {res_m['P_in_kW'] - p_out:.3f} kW")

    # --- Rifasamento ---
    elif tipo == "Rifasamento Industriale (kVAR)":
        st.subheader("Calcolo Batteria di Condensatori")
        p_kw    = st.number_input("Potenza attiva impianto (P) [kW]:", value=50.0, key="rif_pkw")
        cos_ini = st.number_input("cos φ attuale:", min_value=0.3, max_value=0.99,
                                  value=0.75, format="%.2f", key="rif_ini")
        cos_fin = st.number_input("cos φ obiettivo:", min_value=0.8, max_value=1.0,
                                  value=0.95, format="%.2f", key="rif_fin")
        if st.button("Calcola kVAR", key="rif_btn"):
            qc, stato = formule.calcola_rifasamento_kvar(p_kw, cos_ini, cos_fin)
            if stato != "OK":
                st.warning(stato)
            else:
                st.success(f"🔋 **Potenza rifasante necessaria:** {qc:.2f} kVAR")
                with st.expander("Dettagli calcolo"):
                    tan_i = math.tan(math.acos(cos_ini))
                    tan_f = math.tan(math.acos(cos_fin))
                    st.write(f"Potenza reattiva iniziale: {p_kw * tan_i:.2f} kVAR")
                    st.write(f"Potenza reattiva target:   {p_kw * tan_f:.2f} kVAR")
                    st.write(f"Differenza (condensatori): {qc:.2f} kVAR")

    # --- Caduta di Tensione ---
    elif tipo == "Caduta di Tensione":
        mat   = st.radio("Materiale Conduttore:", ["Rame", "Alluminio"], key="cdv_mat")
        fasi  = st.selectbox("Linea elettrica:", ["Monofase", "Trifase"], key="cdv_fasi")
        amp   = st.number_input("Corrente Ib [A]:", value=16.0, key="cdv_amp")
        metri = st.number_input("Lunghezza [Metri]:", value=50.0, key="cdv_metri")
        sez   = st.selectbox("Sezione mm²:", SEZIONI_COMMERCIALI, key="cdv_sez")
        isol  = st.selectbox("Isolante Cavo:", ["PVC (70°C)", "EPR / XLPE / Gomma (90°C)"],
                             key="cdv_isol")
        cos_phi       = st.number_input("cos φ:", value=0.85, min_value=0.1, max_value=1.0,
                                        key="cdv_cosphi")
        temp_ambiente = st.slider("Temperatura Ambiente (°C):", min_value=10, max_value=60,
                                  value=30, step=5, key="cdv_temp")
        n_circuiti    = st.number_input("Numero di Cavi affiancati:", min_value=1, max_value=20,
                                        value=1, key="cdv_ncir")
        iz_tabella    = st.number_input("Portata Nominale catalogo Iz [A] (a 30°C):", value=20.0,
                                        key="cdv_iz")
        posa = st.selectbox("Metodo di Posa (CEI 64-8):", [
            "Metodo A1/A2 (Tubo in parete isolante)",
            "Metodo B1/B2 (Tubo a parete)",
            "Metodo C (A vista a parete)",
            "Metodo E/F/G (Passerelle / Aria aperta)",
            "Posa Interrata",
        ], key="cdv_posa")

        if "Interrata" in posa:
            st.warning(
                "⚠️ Per posa interrata la norma CEI UNEL 35024 prevede una tabella K1 "
                "con riferimento a 20°C (non 30°C). Il calcolo usa la tabella per posa "
                "in aria, risultato leggermente conservativo. Verificare con tabelle CEI "
                "specifiche per interrato se la precisione è critica."
            )

        if st.button("Calcola Perdita Vettoriale Completa", key="cdv_btn"):
            dv, t_lav, rho_t, k1, k2, iz_real = formule.calcola_caduta_avanzata(
                mat, isol, posa, fasi, amp, metri, sez,
                cos_phi, temp_ambiente, iz_tabella, n_circuiti
            )
            if dv < 0:
                st.error(
                    f"⛔ **Temperatura ambiente ({temp_ambiente}°C) ≥ limite isolante "
                    f"({'70°C PVC' if 'PVC' in isol else '90°C EPR'})** — "
                    "cavo fuori specifica. Scegliere isolante con limite superiore."
                )
            else:
                v_ref = TENSIONE_MONOFASE if fasi == "Monofase" else TENSIONE_TRIFASE
                pct   = (dv / v_ref) * 100.0
                with st.expander("🔍 Dettagli calcolo termico"):
                    st.write(f"**K1** (temperatura ambiente): {k1:.2f}")
                    st.write(f"**K2** (raggruppamento {n_circuiti} cavi): {k2:.2f}")
                    st.write(f"**Portata reale Iz:** {iz_real:.2f} A")
                    st.write(f"**Temperatura interna cavo:** {t_lav:.1f} °C")
                    st.write(f"**Resistività operativa ρ_t:** {rho_t:.5f} Ω·mm²/m")
                if pct > 4.0:
                    st.error(f"**Perdita:** {dv:.2f} V ({pct:.2f}%) ⚠️ Fuori norma (limite: 4%)")
                else:
                    st.success(f"**Perdita:** {dv:.2f} V ({pct:.2f}%) ✅ A norma CEI 64-8")

    # --- Corrente di Cortocircuito ---
    elif tipo == "Corrente di Cortocircuito (Icc)":
        st.subheader("Stima Icc presunta in fondo linea (metodo semplificato IEC 60909)")
        st.caption("Utile per verificare il potere di interruzione degli interruttori.")
        col1, col2 = st.columns(2)
        with col1:
            fasi_cc   = st.selectbox("Sistema:", ["Trifase", "Monofase"], key="icc_fasi")
            v_cc      = st.number_input("Tensione nominale [V]:",
                                        value=400.0 if fasi_cc == "Trifase" else 230.0,
                                        key="icc_v")
            trafo_kva = st.number_input("Potenza trasformatore [kVA]:", value=400.0,
                                        min_value=1.0, key="icc_kva")
        with col2:
            vcc_pct = st.number_input("Vcc trasformatore [%] (tipico 4-6%):", value=4.0,
                                      min_value=1.0, max_value=20.0, key="icc_vcc")
            mat_cc  = st.radio("Materiale cavo:", ["Rame", "Alluminio"], key="icc_mat")
        sez_cc  = st.selectbox("Sezione cavo [mm²]:", SEZIONI_COMMERCIALI, key="icc_sez")
        lung_cc = st.number_input("Lunghezza linea [m]:", value=50.0, key="icc_lung")

        c_icc = st.radio(
            "Fattore tensione IEC 60909:",
            ["c = 1.05  — Icc MASSIMA (verifica potere interruzione)", 
             "c = 0.95  — Icc MINIMA  (coordinamento protezioni)"],
            key="icc_c",
        )
        c_val = 1.05 if "1.05" in c_icc else 0.95

        if st.button("Calcola Icc", key="icc_btn"):
            try:
                icc_ka, z_tot, z_tr, z_cv = formule.calcola_corrente_cortocircuito(
                    v_cc, trafo_kva, vcc_pct, mat_cc, sez_cc, lung_cc, fasi_cc,
                    c=c_val
                )
                tipo_icc = "MASSIMA" if c_val == 1.05 else "MINIMA"
                st.success(
                    f"⚡ **Icc {tipo_icc} (c={c_val}):** "
                    f"{icc_ka:.3f} kA  ({icc_ka*1000:.0f} A)"
                )
                with st.expander("🔍 Dettagli impedenze"):
                    st.write(f"**Z trafo:**  {z_tr:.2f} mΩ")
                    st.write(f"**Z cavo:**   {z_cv:.2f} mΩ")
                    st.write(f"**Z totale:** {z_tot:.2f} mΩ")
                if icc_ka < 1.0:
                    st.info("ℹ️ Icc < 1 kA: verifica potere di interruzione interruttore (min 6 kA per BT).")
            except ValueError as e:
                st.error(str(e))
        st.caption("⚠️ Calcolo semplificato. Per progettazione formale usare IEC 60909 completo.")

    # --- Dimensionamento Protezioni ---
    elif tipo == "Dimensionamento Protezioni":
        ib     = st.number_input("Corrente Ib [A]:", value=16.0, key="prot_ib")
        j_dens = st.slider("Densità J [A/mm²]:", 1.0, 6.0, 4.0, step=0.5, key="prot_j")
        if st.button("Trova Soluzione", key="prot_btn"):
            mag, cavo, t_sez = formule.calcola_sezione_protezione(ib, j_dens)
            st.success(
                f"🔒 **Interruttore consigliato (In):** {mag} A "
                f"| 📐 **Sezione commerciale:** {cavo} mm² "
                f"(teorica: {t_sez:.2f} mm²)"
            )

# ==============================================================================
# TAB 3 — PLC & AUTOMAZIONE
# ==============================================================================
with tab_plc:
    st.header("🤖 Utility per PLC (RX3i Optimized)")
    tool_plc = st.selectbox("Seleziona Strumento:", [
        "Info CPU & Memoria RX3i",
        "Info Modulo Analogico",
        "Tipi Dati",
        "Scalatura Analogica (Raw → Engineering)",
        "Scalatura Inversa (Engineering → Raw / Setpoint)",
        "Esplosione Parola nei Bit",
        "Composizione WORD da Bit",
        "Calcolo Memoria RX3i",
    ], key="plc_tool")

    # --- Info CPU ---
    if tool_plc == "Info CPU & Memoria RX3i":
        if hasattr(automazione, "lista_cpu_rx3i"):
            cpu_list = automazione.lista_cpu_rx3i()
        else:
            cpu_list = list(getattr(automazione, "_DB_CPU_RX3I", {}).keys())
        cpu_sel  = st.selectbox("Seleziona modello CPU:", cpu_list, key="cpu_sel")
        info     = automazione.info_cpu_rx3i(cpu_sel)
        if info:
            st.info(f"📌 {info['note']}")
            st.write(f"**RAM programma:** {info['ram_programma_mb']} MB")
            st.write("**Configurazione PME tipica (default nuovi progetti):**")
            tipici = info["tipici_pme"]
            col1, col2 = st.columns(2)
            aree = list(tipici.items())
            for i, (area, val_cpu) in enumerate(aree):
                unita = "bit" if area in ("%I", "%Q", "%M", "%G") else "word (16-bit)"
                with (col1 if i < len(aree)//2 else col2):
                    st.write(f"**{area}:** {val_cpu:,} {unita}")
            st.caption(
                "⚠️ Valori di default PME, non limiti hardware fissi. "
                "Modificabili in Hardware Configuration → CPU → Memory."
            )

    # --- Info Modulo ---
    elif tool_plc == "Info Modulo Analogico":
        moduli  = automazione.lista_moduli()
        mod_sel = st.selectbox("Seleziona modulo:", moduli, key="mod_sel")
        info_m  = automazione.info_modulo(mod_sel)
        if info_m:
            col1, col2, col3 = st.columns(3)
            with col1: st.metric("Famiglia", info_m["famiglia"])
            with col2: st.metric("Canali", str(info_m["canali"]) if info_m["canali"] > 0 else "—")
            with col3: st.metric("Tipo", info_m["tipo"])
            st.write(f"**Risoluzione:** {info_m['resol']}")
            st.info(f"ℹ️ {info_m['note_mod']}")
            st.write("**Configurazioni canale disponibili:**")
            for nome_cfg, cfg in info_m["config"].items():
                nota = f" — {cfg['note']}" if cfg["note"] else ""
                st.write(
                    f"- **{nome_cfg}**: raw {cfg['in_min']} → {cfg['in_max']}"
                    f" [{cfg['unita']}]{nota}"
                )

    # --- Tipi Dati ---
    elif tool_plc == "Tipi Dati":
        tipo_s = st.selectbox("Scegli Tipo:", [
            "BOOL", "BYTE", "WORD", "DWORD",
            "INT (Integer)", "UINT (Unsigned INT)",
            "DINT (Double INT)", "UDINT (Unsigned DINT)",
            "REAL (Float)",
        ], key="td_tipo")
        dim, cat_td, v_min, v_max = automazione.info_tipo_dato(tipo_s)
        st.info(f"**Dimensione:** {dim}")
        st.info(f"**Categoria:** {cat_td}")
        st.success(f"**Range:** [{v_min} ➔ {v_max}]")
        if tipo_s == "BOOL":
            st.caption("Su RX3i il BOOL è indirizzato singolarmente in %I, %Q, %M. "
                       "In area %R i BOOL vengono packed (16 per registro).")
        if "REAL" in tipo_s:
            st.caption("Il tipo REAL occupa 2 registri %R consecutivi.")

    # --- Scalatura Analogica ---
    elif tool_plc == "Scalatura Analogica (Raw → Engineering)":
        modo = st.radio("Seleziona modulo da:",
                        ["Database moduli RX3i", "Inserimento manuale range"],
                        key="sca_modo")

        if modo == "Database moduli RX3i":
            moduli_sca = automazione.lista_moduli()
            mod_sca    = st.selectbox("Modulo:", moduli_sca, key="sca_mod")
            info_sca   = automazione.info_modulo(mod_sca)
            cfg_list   = list(info_sca["config"].keys()) if info_sca else []
            cfg_sel    = st.selectbox("Configurazione canale:", cfg_list, key="sca_cfg")
            result_sca = automazione.get_range_canale(mod_sca, cfg_sel)
            if result_sca:
                in_min, in_max, unita_sca, nota_sca = result_sca
                st.caption(f"Range raw: **{in_min} → {in_max}** [{unita_sca}]"
                           + (f" — {nota_sca}" if nota_sca else ""))
            else:
                in_min, in_max = 0.0, 32000.0
        else:
            in_min = st.number_input("Limite raw minimo:", value=0.0, key="sca_man_min")
            in_max = st.number_input("Limite raw massimo:", value=32000.0, key="sca_man_max")

        clamp      = st.checkbox("Satura il risultato ai limiti fisici (clamp)",
                                 value=False, key="sca_clamp")
        val_grezzo = st.number_input("Valore grezzo letto dal PLC:",
                                     value=float(in_min), key="sca_raw")
        out_min    = st.number_input("Valore fisico a segnale minimo:", value=0.0, key="sca_omin")
        out_max    = st.number_input("Valore fisico a fondo scala:", value=100.0, key="sca_omax")

        if st.button("Scala", key="sca_btn"):
            ris, stato = automazione.esegui_scalatura(
                val_grezzo, in_min, in_max, out_min, out_max, abilita_clamp=clamp
            )
            if stato == "ROTTURA_CAVO":
                st.error("🔴 **ROTTURA CAVO / SEGNALE ASSENTE** — raw sotto soglia minima.")
            elif stato == "FUORI_RANGE":
                st.warning(f"⚠️ Valore fuori range — estrapolato: {ris:.4f}")
                pct = (val_grezzo - in_min) / (in_max - in_min) if in_max != in_min else 0
                st.progress(min(max(pct, 0.0), 1.0))
            else:
                st.success(f"🎯 **Valore Scalato:** {ris:.4f}")
                pct = (ris - out_min) / (out_max - out_min) if out_max != out_min else 0
                st.progress(min(max(pct, 0.0), 1.0))
                st.caption(f"{pct * 100.0:.1f}% del fondo scala")

    # --- Scalatura Inversa ---
    elif tool_plc == "Scalatura Inversa (Engineering → Raw / Setpoint)":
        st.caption("Converte un setpoint fisico nel valore raw da scrivere nel PLC.")
        modo_inv = st.radio("Seleziona modulo da:",
                            ["Database moduli RX3i", "Inserimento manuale range"],
                            key="sci_modo")

        if modo_inv == "Database moduli RX3i":
            moduli_inv  = automazione.lista_moduli()
            mod_inv     = st.selectbox("Modulo:", moduli_inv, key="sci_mod")
            info_inv    = automazione.info_modulo(mod_inv)
            cfg_inv     = list(info_inv["config"].keys()) if info_inv else []
            cfg_inv_sel = st.selectbox("Configurazione canale:", cfg_inv, key="sci_cfg")
            result_inv  = automazione.get_range_canale(mod_inv, cfg_inv_sel)
            if result_inv:
                in_min_inv, in_max_inv, _, _ = result_inv
                st.caption(f"Range raw: **{in_min_inv} → {in_max_inv}**")
            else:
                in_min_inv, in_max_inv = 0.0, 32000.0
        else:
            in_min_inv = st.number_input("Limite raw minimo:", value=0.0, key="sci_man_min")
            in_max_inv = st.number_input("Limite raw massimo:", value=32000.0, key="sci_man_max")

        out_min_inv = st.number_input("Valore fisico a segnale minimo:", value=0.0, key="sci_omin")
        out_max_inv = st.number_input("Valore fisico a fondo scala:", value=100.0, key="sci_omax")
        val_eng     = st.number_input("Setpoint fisico da convertire:", value=50.0, key="sci_eng")

        if st.button("Calcola Raw", key="sci_btn"):
            raw, stato_inv = automazione.esegui_scalatura_inversa(
                val_eng, in_min_inv, in_max_inv, out_min_inv, out_max_inv
            )
            if stato_inv == "FUORI_RANGE":
                st.warning(f"⚠️ Setpoint fuori range — raw estrapolato: {raw:.1f}")
            else:
                st.success(
                    f"📤 **Valore Raw da scrivere nel PLC:** {raw:.1f}  "
                    f"(INT: {int(round(raw))})"
                )

    # --- Esplosione Parola nei Bit ---
    elif tool_plc == "Esplosione Parola nei Bit":
        val_w = st.number_input(
            "Valore numerico WORD (0–65535):", min_value=0, max_value=65535,
            value=0, key="esp_val"
        )
        st.info(f"Dec: {val_w} | Hex: 16#{val_w:04X} | Bin: {val_w:016b}")
        bits = automazione.calcola_esplosione_bits(val_w)
        c1, c2 = st.columns(2)
        for idx, b_v in enumerate(bits):
            with (c1 if idx < 8 else c2):
                colore = "🟢" if b_v else "⚫"
                st.write(f"{colore} **Bit {idx:02d}** ➔ `{b_v}`")

    # --- Composizione WORD da Bit ---
    elif tool_plc == "Composizione WORD da Bit":
        st.caption("Imposta i singoli bit per comporre il valore WORD/Control Word.")
        bit_values = []
        c1, c2 = st.columns(2)
        for idx in range(16):
            with (c1 if idx < 8 else c2):
                b = st.checkbox(f"Bit {idx:02d}", value=False, key=f"cmp_bit_{idx}")
                bit_values.append(1 if b else 0)
        word = automazione.componi_word_da_bits(bit_values)
        st.success(
            f"**Valore WORD:** {word} (Dec) | 16#{word:04X} (Hex) | {word:016b} (Bin)"
        )

    # --- Calcolo Memoria RX3i ---
    elif tool_plc == "Calcolo Memoria RX3i":
        pref  = st.selectbox("Area Memoria:", ["%R", "%M", "%I", "%Q", "%AI", "%AQ"],
                             key="mem_pref")
        start = st.number_input("Indirizzo inizio:", min_value=1, value=1, key="mem_start")
        t_var = st.selectbox("Tipo variabile:", [
            "1 Bit (Digital I/O)",
            "16 Bit (WORD / INT)",
            "32 Bit (REAL / DINT)",
        ], key="mem_tipo")
        qta = st.number_input("Quantità (Array Size):", min_value=1, value=1, key="mem_qta")
        if st.button("Calcola", key="mem_btn"):
            intervallo = automazione.calcola_limiti_memoria_rx3i(pref, start, qta, t_var)
            st.success(f"💾 **Intervallo occupato:** `{intervallo}`")
            if t_var == "1 Bit (Digital I/O)" and pref == "%R":
                n_reg = math.ceil(int(qta) / 16)
                st.caption(
                    f"ℹ️ In area %R i BOOL sono packed: {int(qta)} bit "
                    f"occupano {n_reg} registro/i da 16 bit."
                )

# ==============================================================================
st.markdown("---")
st.caption(
    "⚠️ **Disclaimer Legale:** Strumento indicativo basato sulle norme tecniche CEI 64-8. "
    "Non sostituisce la progettazione formale di un professionista abilitato."
)
