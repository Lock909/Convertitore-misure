import streamlit as st
import math
import formule
import automazione

st.set_page_config(page_title="Tool Industriale", page_icon="⚙️", layout="centered")

categories = {
    "Pressione": {"pa": 1.0, "kpa": 1000.0, "mpa": 1000000.0, "bar": 100000.0, "bara": 100000.0, "barg": 100000.0, "psi": 6894.757, "psia": 6894.757, "psig": 6894.757},
    "Portata": {"m3/s": 1.0, "m3/h": 1.0/3600.0, "l/s": 0.001, "l/min": 0.001/60.0},
    "Lunghezza": {"m": 1.0, "mm": 0.001, "cm": 0.01, "in": 0.0254, "ft": 0.3048},
    "Temperatura": {"c": "Special", "f": "Special", "k": "Special"}
}

st.title("⚙️ Strumento Multifunzione Industriale")
modalita = st.sidebar.radio("Seleziona Ambito:", ["Conversioni Standard", "Calcoli Elettrici ⚡", "Mondo PLC & Automazione 🤖"])

if modalita == "Conversioni Standard":
    st.header("🔄 Convertitore di Unità")
    cat = st.selectbox("Grandezza:", list(categories.keys()))
    units = list(categories[cat].keys())
    col1, col2 = st.columns(2)
    with col1: from_u = st.selectbox("Da:", units, index=0)
    with col2: to_u = st.selectbox("A:", units, index=1 if len(units)>1 else 0)
    val = st.number_input("Valore:", value=0.0, format="%.6f")

    if cat == "Pressione":
        p_pascal = val * categories[cat][from_u]
        if from_u in ["barg", "psig"]: p_pascal += 101325.0
        if to_u in ["barg", "psig"]: p_pascal -= 101325.0
        res = p_pascal / categories[cat][to_u]
    elif cat == "Temperatura":
        k = val + 273.15 if from_u == "c" else ((val - 32) * 5/9 + 273.15 if from_u == "f" else val)
        res = k - 273.15 if to_u == "c" else ((k - 273.15) * 9/5 + 32 if to_u == "f" else k)
    else:
        res = (val * categories[cat][from_u]) / categories[cat][to_u]
    st.success(f"**Risultato:** {res:.6f} {to_u}")

elif modalita == "Calcoli Elettrici ⚡":
    st.header("⚡ Calcolatore Elettrico")
    tipo = st.selectbox("Tipo di Analisi:", ["Legge di Ohm", "Calcolo Potenza (kW)", "Caduta di Tensione", "Dimensionamento Protezioni"])
    
    if tipo == "Legge di Ohm":
        cerca = st.selectbox("Cosa calcolare?", ["Tensione", "Corrente", "Resistenza"])
        in1 = st.number_input("Primo Valore:", value=1.0)
        in2 = st.number_input("Secondo Valore:", value=1.0)
        if st.button("Calcola"): st.success(formule.calcola_ohm(cerca, in1, in2))
            
    elif tipo == "Calcolo Potenza (kW)":
        sis = st.selectbox("Sistema:", ["DC", "Monofase", "Trifase"])
        v = st.number_input("Volt:", value=400.0 if sis=="Trifase" else 230.0)
        i = st.number_input("Ampere:", value=10.0)
        cos_phi = st.number_input("cos φ:", value=0.85) if sis != "DC" else 1.0
        if st.button("Calcola kW"):
            kw = (v * i * cos_phi * (math.sqrt(3) if sis == "Trifase" else 1.0)) / 1000.0
            st.success(f"**Potenza Attiva:** {kw:.4f} kW")
            
    elif tipo == "Caduta di Tensione":
        mat = st.radio("Materiale Conduttore:", ["Rame", "Alluminio"])
        fasi = st.selectbox("Linea elettrica:", ["Monofase", "Trifase"])
        amp = st.number_input("Corrente Ib [A]:", value=16.0)
        metri = st.number_input("Lunghezza [Metri]:", value=50.0)
        sez = st.selectbox("Sezione mm²:", formule.ottieni_sezioni())
        isol = st.selectbox("Isolante:", ["PVC (70°C)", "Gomma (90°C)"])
        cos_phi = st.number_input("cos φ:", value=0.85)
        posa = st.selectbox("Metodo di Posa (CEI 64-8):", ["Metodo A1/A2 (Tubo in parete isolante)", "Metodo B1/B2 (Tubo a parete)", "Metodo C (A vista a parete)", "Metodo E/F/G (Passerelle / Aria aperta)", "Posa Interrata"])
        
        if st.button("Calcola Perdita"):
            dv, t_es, rho_t = formule.calcola_caduta_avanzata(mat, isol, posa, fasi, amp, metri, sez, cos_phi)
            pct = (dv / (230.0 if fasi == "Monofase" else 400.0)) * 100.0
            st.info(f"🌡️ Temp: {t_es:.0f}°C | \u03c1_t = {rho_t:.5f}")
            st.error(f"**Perdita:** {dv:.2f} V ({pct:.2f}%) ⚠️ >4%") if pct > 4.0 else st.success(f"**Perdita:** {dv:.2f} V ({pct:.2f}%) ✅ OK")
            
    elif tipo == "Dimensionamento Protezioni":
        ib = st.number_input("Corrente Ib [A]:", value=16.0)
        j_dens = st.slider("Densità J [A/mm²]:", 1.0, 6.0, 4.0, step=0.5)
        if st.button("Trova Soluzione"):
            mag, cavo, t_sez = formule.calcola_sezione_protezione(ib, j_dens)
            st.success(f"🔒 Interruttore consigliato (In): {mag} A")
            st.info(f"📐 Sezione Cavo commerciale: {cavo} mm²")

else:
    st.header("🤖 Utility per PLC (RX3i Optimized)")
    tool_plc = st.selectbox("Seleziona Strumento:", ["Tipi Dati", "Scalatura Analogica", "Esplosione Parola nei Bit", "Calcolo Memoria RX3i"])
    
    if tool_plc == "Tipi Dati":
        tipo_s = st.selectbox("Scegli Tipo:", ["BYTE", "WORD", "DWORD", "INT (Integer)", "UINT (Unsigned INT)", "DINT (Double INT)", "REAL (Float)"])
        dim, cat, v_min, v_max = automazione.info_tipo_dato(tipo_s)
        st.info(f"Dimensione: {dim} | Categoria: {cat}")
        st.success(f"Range: [{v_min} ➔ {v_max}]")
        
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
