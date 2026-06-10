def ottieni_categorie():
    return {
        "Pressione": {"pa": 1.0, "kpa": 1000.0, "mpa": 1000000.0, "bar": 100000.0, "bara": 100000.0, "barg": 100000.0, "psi": 6894.757, "psia": 6894.757, "psig": 6894.757},
        "Portata": {"m3/s": 1.0, "m3/h": 1.0/3600.0, "l/s": 0.001, "l/min": 0.001/60.0},
        "Lunghezza": {"m": 1.0, "mm": 0.001, "cm": 0.01, "in": 0.0254, "ft": 0.3048},
        "Temperatura": {"c": "Special", "f": "Special", "k": "Special"}
    }

def esegui_conversione(cat, from_u, to_u, val):
    categories = ottieni_categorie()
    p_atm = 101325.0
    
    if cat == "Pressione":
        p_pascal = val * categories[cat][from_u]
        if from_u in ["barg", "psig"]: p_pascal += p_atm
        if to_u in ["barg", "psig"]: p_pascal -= p_atm
        return p_pascal / categories[cat][to_u]
        
    elif cat == "Temperatura":
        k = val + 273.15 if from_u == "c" else ((val - 32) * 5/9 + 273.15 if from_u == "f" else val)
        return k - 273.15 if to_u == "c" else ((k - 273.15) * 9/5 + 32 if to_u == "f" else k)
        
    else:
        return (val * categories[cat][from_u]) / categories[cat][to_u]
