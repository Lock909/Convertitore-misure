import streamlit as st
import math
import formule

st.set_page_config(page_title="Tool Industriale", page_icon="⚙️", layout="centered")

P_ATM_PA = 101325.0
RHO_RAME = 0.0175
RHO_ALLUMINIO = 0.0282

categories = {
    "Pressione": {"pa": 1.0, "kpa": 1000.0, "mpa": 1000000.0, "bar": 100000.0, "bara": 100000.0, "barg": 100000.0, "psi": 6894.757, "psia": 6894.757, "psig": 6894.757, "atm": 101325.0, "mmhg": 133.322, "torr": 133.322},
    "Portata": {"m3/s": 1.0, "m3/h": 1.0/3600.0, "l/s": 0.001, "l/min": 0.001/60.0},
    "Lunghezza": {"m": 1.0, "mm": 0.001, "cm": 0.01, "km": 1000.0, "in": 0.0254, "ft": 0.3048},
    "Temperatura": {"c": "Special", "f": "Special", "k": "Special"}
}

st.title("⚙️ Strumento Multifunzione Industriale")
modalita = st.sidebar.radio("Seleziona Ambito:", ["Conversioni Standard", "Calcoli Elettrici ⚡"])

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
        if from_u in ["barg", "psig"]: p_pascal += P_ATM_PA
        if to_u in ["barg", "psig"]: p_pascal -= P_ATM_PA
        res = p_pascal / categories[cat][to_u]
    elif cat == "Temperatura":
        if from_u == "c": k = val + 273.15
        elif from_u == "f": k = (val - 32) * 5/9 + 273.15
        else: k = val
        if to_u == "c": res = k - 273.15
        elif to_u == "f": res = (k - 273.15) * 9/5 + 32
        else: res = k
    else:
        res = (val * categories[cat][from_u]) / categories[cat][to_u]
        
    st.success(f"**Risultato:** {res:.6f} {to_u}")

else:
    st.header("⚡ Calcolatore Elettrico")
    tipo = st.selectbox("Tipo di Analisi:", ["Legge di Ohm", "Calcolo Potenza (kW)", "Caduta di Tensione", "Dimensionamento Protezioni"])
    
    if tipo == "Legge di Ohm":
        cerca = st.selectbox("Cosa calcolare?", ["Tensione", "Corrente", "Resistenza"])
        in1 = st.number_input("Primo Valore:", value=1.0)
        in2 = st.number_input("Secondo Valore (R o I):", value=1.0)
        if st.button("Calcola"):
            st.success(formule.calcola_ohm(cerca, in1, in2))
            
    elif tipo == "Calcolo Potenza (kW)":
        sis = st.selectbox("Sistema:", ["DC", "Monofase", "Trifase"])
        v = st.number_input("Volt:", value=400.0 if sis=="Trifase" else 230.0)
        i = st.number_input("Ampere:", value=10.0)
        cos_phi = st.number_input("cos φ:", value=0.85) if sis != "DC" else 1.0
        if st.button("Calcola kW"):
            rad = math.sqrt(3) if sis == "Trifase" else 1.0
            kw = (v * i * cos_phi * rad) / 1000.0
            st.success(f"**Potenza Attiva:** {kw:.4f} kW")
            
    elif tipo == "Caduta di Tensione":
        mat = st.radio("Materiale:", ["Rame", "Alluminio"])
        fasi = st.selectbox("Linea:", ["Monofase", "Trifase"])
        amp = st.number_input("Ampere carico:", value=16.0)
        metri = st.number_input("Metri linea:", value=50.0)
        sez = st.selectbox("Sezione mm²:", formule.ottieni_sezioni())
        isol = st.selectbox("Isolante:", ["PVC (70°C)", "Gomma (90°C)"])
        
        if st.button("Calcola Perdita"):
            temp = 70.0 if "PVC" in isol else 90.0
            rho = RHO_RAME if mat == "Rame" else RHO_ALLUMINIO
            rho_t = rho * (1.0 + 0.004 * (temp - 20.0))
            k = 2.0 if fasi == "Monofase" else math.sqrt(3)
            dv = (k * rho_t * metri * amp * 0.85) / sez
            v_rif = 230.0 if fasi == "Monofase" else 400.0
            st.success(f"**Caduta di Tensione:** {dv:.2f} V ({ (dv/v_rif)*100.0 :.2f}%)")
            
    elif tipo == "Dimensionamento Protezioni":
        ib = st.number_input("Corrente di Impiego Carico (Ib) [A]:", value=16.0)
        j_dens = st.slider("Densità Ammessa (J) [A/mm²]:", 1.0, 6.0, 4.0, step=0.5)
        if st.button("Trova Soluzione Cavo/Interruttore"):
            mag, cavo, t_sez = formule.calcola_sezione_protezione(ib, j_dens)
            st.success(f"🔒 **Interruttore Magnetotermico consigliato (In):** {mag} A")
            st.info(f"📐 **Sezione Cavo commerciale:** {cavo} mm² (Calcolata: {t_sez:.2f} mm²)")
