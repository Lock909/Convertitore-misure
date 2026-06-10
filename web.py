import streamlit as st
import idraulica
import elettrica
import automazione

st.set_page_config(page_title="Tool Industriale", page_icon="⚙️", layout="centered")

st.title("⚙️ Strumento Multifunzione Industriale")
modalita = st.sidebar.radio("Seleziona Ambito:", ["Conversioni Standard", "Calcoli Elettrici ⚡", "Mondo PLC & Automazione 🤖"])

# ==============================================================================
# AMBITO 1: CONVERSIONI IDRAULICHE STANDARD
# ==============================================================================
if modalita == "Conversioni Standard":
    st.header("🔄 Convertitore di Unità")
    categories = idraulica.ottieni_categorie()
    cat = st.selectbox("Grandezza:", list(categories.keys()))
    units = list(categories[cat].keys())
    
    col1, col2 = st.columns(2)
    with col1: from_u = st.selectbox("Da:", units, index=0)
    with col2: to_u = st.selectbox("A:", units, index=1 if len(units)>1 else 0)
    val = st.number_input("Valore:", value=0.0, format="%.6f")

    res = idraulica.esegui_conversione(cat, from_u, to_u, val)
    st.success(f"**Risultato:** {res:.6f} {to_u}")

# ==============================================================================
# AMBITO 2: CALCOLI ELETTRICI ⚡
# ==============================================================================
elif modalita == "Calcoli Elettrici ⚡":
    st.header("⚡ Calcolatore Elettrico")
    tipo = st.selectbox("Tipo di Analisi:", ["Legge di Ohm", "Analisi Potenze & Estrazione Ampere", "Caduta di Tensione", "Dimensionamento Protezioni"])
    
    if tipo == "Legge di Ohm":
        cerca = st.selectbox("Cosa calcolare?", ["Tensione", "Corrente", "Resistenza"])
        in1 = st.number_input("Primo Valore:", value=1.0)
        in2 = st.number_input("Secondo Valore:", value=1.0)
        if st.button("Calcola"): st.success(elettrica.calcola_ohm(cerca, in1, in2))
            
    elif tipo == "Analisi Potenze & Estrazione Ampere":
        st.subheader("Calcolo Avanzato Potenze Elettriche e Corrente")
        sis = st.selectbox("Sistema Elettrico:", ["DC", "Monofase", "Trifase"])
        obiettivo = st.selectbox("Cosa desideri fare?", ["Estrai da Volt e Ampere", "Estrai Corrente (Ampere) da Watt"])
        v = st.number_input("Tensione (Volt):", value=400.0 if sis=="Trifase" else (230.0 if sis=="Monofase" else 24.0))
        cos_phi = st.number_input("Fattore di potenza (cos φ):", min_value=0.1, max_value=1.0, value=0.85) if sis != "DC" else 1.0
        
        if obiettivo == "Estrai da Volt e Ampere":
            i = st.number_input("Corrente (Ampere):", value=10.0)
            if st.button("Analizza Potenze"):
                res = elettrica.calcola_potenza_e_corrente(sis, v, i, 0.0, cos_phi, obiettivo)
                st.success(f"🔌 **Potenza Attiva:** {res['W']:.1f} W ({res['kW']:.4f} kW) | 🐎 **Meccanica:** {res['HP']:.2f} HP")
                st.info(f"📊 **Apparente:** {res['VA']:.1f} VA | 📉 **Reattiva:** {res['VAR']:.1f} VAR")
        else:
            w = st.number_input("Potenza in WATT (W):", value=2200.0, step=100.0)
            if st.button("Estrai Ampere"):
                res = elettrica.calcola_potenza_e_corrente(sis, v, 0.0, w, cos_phi, obiettivo)
                if res is None: st.error("Errore divisione per zero!")
                else: st.success(f"⚡ **Corrente Assorbita:** {res['A']:.2f} A | 🐎 **Potenza:** {res['HP']:.2f} HP")
            
    elif tipo == "Caduta di Tensione":
        mat = st.radio("Materiale Conduttore:", ["Rame", "Alluminio"])
        fasi = st.selectbox("Linea elettrica:", ["Monofase", "Trifase"])
        amp = st.number_input("Corrente Ib [A]:", value=16.0)
        metri = st.number_input("Lunghezza [Metri]:", value=50.0)
        sez = st.selectbox("Sezione mm²:", (1.5, 2.5, 4.0, 6.0, 10.0, 16.0, 25.0, 35.0, 50.0, 70.0, 95.0, 120.0))
        isol = st.selectbox("Isolante Cavo:", ["PVC (70°C)", "EPR / XLPE / Gomma (90°C)"])
        cos_phi = st.number_input("cos φ:", value=0.85, min_value=0.1, max_value=1.0)
        temp_ambiente = st.slider("Temperatura Ambiente (°C):", min_value=10, max_value=60, value=30, step=5)
        n_circuiti = st.number_input("Numero di Cavi affiancati:", min_value=1, max_value=20, value=1)
        iz_tabella = st.number_input("Portata Nominale catalogo (Iz base a 30°C) [A]:", value=20.0)
        posa = st.selectbox("Metodo di Posa (CEI 64-8):", ["Metodo A1/A2", "Metodo B1/B2", "Metodo C", "Metodo E/F/G", "Posa Interrata"])
        
        if st.button("Calcola Perdita Vettoriale Completa"):
            dv, t_es, rho_t, k1, k2, iz_real = elettrica.calcola_caduta_avanzata(mat, isol, posa, fasi, amp, metri, sez, cos_phi, temp_ambiente, iz_tabella, n_circuiti)
            pct = (dv / (230.0 if fasi == "Monofase" else 400.0)) * 100.0
            st.info(f"📊 Declassamento: K1={k1:.2f}, K2={k2:.2f} | Portata reale Iz: {iz_real:.2f} A")
            st.info(f"🔥 Temperatura interna cavo: {t_es:.1f} °C | \u03c1_t = {rho_t:.5f}")
            st.error(f"**Perdita:** {dv:.2f} V ({pct:.2f}%) ⚠️ Fuori norma > 4%") if pct > 4.0 else st.success(f"**Perdita:** {dv:.2f} V ({pct:.2f}%) ✅ A norma")
            
    elif tipo == "Dimensionamento Protezioni":
        ib = st.number_input("Corrente Ib [A]:", value=16.0)
        j_dens = st.slider("Densità J [A/mm²]:", 1.0, 6.0, 4.0, step=0.5)
        if st.button("Trova Soluzione"):
            mag, cavo, t_sez = elettrica.calcola_sezione_protezione(ib, j_dens)
            st.success(f"🔒 Interruttore consigliato (In): {mag} A | 📐 Sezione commerciale: {cavo} mm²")

# ==============================================================================
# AMBITO 3: MONDO PLC & AUTOMAZIONE 🤖
# ==============================================================================
else:
    st.header("🤖 Utility per PLC (RX3i Optimized)")
    tool_plc = st.selectbox("Seleziona Strumento:", ["Tipi Dati", "Scalatura Analogica", "Esplosione Parola nei Bit", "Calcolo Memoria RX3i"])
    
    if tool_plc == "Tipi Dati":
        tipo_s = st.selectbox("Scegli Tipo:", ["BYTE", "WORD", "DWORD", "INT (Integer)", "UINT (Unsigned INT)", "DINT (Double INT)", "REAL (Float)"])
        dim, cat, v_min, v_max = automazione.info_tipo_dato(tipo_s)
        st.info(f"Dimensione: {dim} | Categoria: {cat} | Range: [{v_min} ➔ {v_max}]")
        
    elif tool_plc == "Scalatura Analogica":
        pre = st.selectbox("Risoluzione:", ["Siemens S7 (0 - 27648)", "GE RX3i (0 - 32000)", "16 Bit (0 - 65535)"])
        in_min, in_max = (0.0, 27648.0) if "Siemens" in pre else ((0.0, 32000.0) if "RX3i" in pre else (0.0, 65535.0))
        val_grezzo = st.number_input("Valore grezzo PLC:", value=0.0)
        out_min = st.number_input("Valore allo Zero strumento:", value=0.0)
        out_max = st.number_input("Valore a Fondo Scala:", value=10.0)
        if st.button("Scala"):
            ris, st_sc = automazione.esegui_scalatura(val_grezzo, in_min, in_max, out_min, out_max)
            if st_sc != "OK": st.error(st_sc)
            else:
                st.success(f"🎯 Valore Scalato (REAL): {ris:.4f}")
                pct = ((ris - out_min) / (out_max - out_min)) * 100.0 if (out_max - out_min) != 0 else 0.0
                st.progress(min(max(pct / 100.0, 0.0), 1.0))

    elif tool_plc == "Esplosione Parola nei Bit":
        val_w = st.number_input("Valore numerico WORD (0-65535):", min_value=0, max_value=65535, value=0)
        st.info(f"Dec: {val_w} | Hex: 16#{val_w:04X} | Bin: {val_w:016b}")
        bits = automazione.calcola_esplosione_bits(val_w)
        c1, c2 = st.columns(2)
        for idx, b_v in enumerate(bits):
            with (c1 if idx < 8 else c2): st.write(f"**Bit {idx:02d}** ➔ `{b_v}`")

    elif tool_plc == "Calcolo Memoria RX3i":
        pref = st.selectbox("Area Memoria (%):", ["%R", "%M", "%I", "%Q", "%AI", "%AQ"])
        start = st.number_input("Indirizzo inizio:", min_value=1, value=1)
        t_var = st.selectbox("Tipo variabile:", ["1 Bit (Digital I/O)", "16 Bit (WORD / INT)", "32 Bit (REAL / DINT)"])
        qta = st.number_input("Quantità (Array Size):", min_value=1, value=1)
        if st.button("Calcola"):
            st.success(f"💾 Intervallo occupato: `{automazione.calcola_limiti_memoria_rx3i(pref, start, qta, t_var)}`")

st.markdown("---")
st.caption("⚠️ **Disclaimer Legale:** Strumento indicativo basato sulle norme tecniche CEI 64-8. Non sostituisce la progettazione formale di un professionista abilitato.")
