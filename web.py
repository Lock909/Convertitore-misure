import streamlit as st

st.set_page_config(page_title="Convertitore", layout="centered")
st.title("🔄 Convertitore di Unità")

P_ATM_PA = 101325.0

categories = {
    "Pressione": {"pa": 1.0, "kpa": 1000.0, "mpa": 1000000.0, "hpa": 100.0, "bar": 100000.0, "bara": 100000.0, "barg": 100000.0, "psi": 6894.75729, "psia": 6894.75729, "psig": 6894.75729, "atm": 101325.0, "mmhg": 133.322387, "torr": 133.322368},
    "Portata": {"m3/s": 1.0, "m3/h": 1.0/3600.0, "l/s": 0.001, "l/min": 0.001/60.0, "gpm": 0.0000630902, "kg/s": 1.0, "kg/h": 1.0/3600.0},
    "Lunghezza": {"m": 1.0, "mm": 0.001, "cm": 0.01, "km": 1000.0, "in": 0.0254, "ft": 0.3048, "yd": 0.9144, "mile": 1609.344},
    "Temperatura": {"c": "Special", "f": "Special", "k": "Special", "r": "Special"}
}

cat = st.selectbox("Grandezza:", list(categories.keys()))
units = list(categories[cat].keys())

col1, col2 = st.columns(2)
with col1: from_u = st.selectbox("Da:", units, index=0)
with col2: to_u = st.selectbox("A:", units, index=1 if len(units)>1 else 0)

val = st.number_input("Valore:", value=0.0, format="%.6f")

if cat == "Pressione":
    factors = categories[cat]
    p_pascal = val * factors[from_u]
    if from_u in ["barg", "psig"]: p_pascal += P_ATM_PA
    if to_u in ["barg", "psig"]: p_pascal -= P_ATM_PA
    res = p_pascal / factors[to_u]
elif cat == "Temperatura":
    if from_u == "c": k = val + 273.15
    elif from_u == "f": k = (val - 32) * 5/9 + 273.15
    elif from_u == "k": k = val
    elif from_u == "r": k = val * 5/9
    if to_u == "c": res = k - 273.15
    elif to_u == "f": res = (k - 273.15) * 9/5 + 32
    elif to_u == "k": res = k
    elif to_u == "r": res = k * 9/5
else:
    factors = categories[cat]
    res = (val * factors[from_u]) / factors[to_u]

st.success(f"**Risultato:** {res:.6f} {to_u}")
