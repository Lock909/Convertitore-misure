import math

def calcola_ohm(ricerca, input_1, input_2):
    if ricerca == "Tensione":
        return f"Tensione (V): {input_1 * input_2:.4f} V"
    elif ricerca == "Corrente":
        return f"Corrente (I): {input_1 / input_2:.4f} A" if input_2 != 0 else "Errore: Resistenza zero!"
    elif ricerca == "Resistenza":
        return f"Resistenza (R): {input_1 / input_2:.4f} \u03a9" if input_2 != 0 else "Errore: Corrente zero!"

def ottieni_sezioni():
    return (1.5, 2.5, 4.0, 6.0, 10.0, 16.0, 25.0, 35.0, 50.0, 70.0, 95.0, 120.0)

def ottieni_interruttori():
    return (6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125)

def calcola_sezione_protezione(i_max, densita):
    sezione_teorica = i_max / densita
    sez_scelta = ottieni_sezioni()[-1]
    for s in ottieni_sezioni():
        if s >= sezione_teorica:
            sez_scelta = s
            break
    int_scelto = ottieni_interruttori()[-1]
    for val_i in ottieni_interruttori():
        if val_i >= i_max:
            int_scelto = val_i
            break
    return int_scelto, sez_scelta, sezione_teorica

def calcola_rho_termica(materiale, isolante, posa):
    # Determina la resistività base a 20°C
    rho_base = 0.0175 if materiale == "Rame" else 0.0282
    # Determina la temperatura massima dell'isolamento
    temp_regime = 70.0 if "PVC" in isolante else 90.0
    
    # Assegna la temperatura reale di lavoro in base allo scambio termico della posa
    if "molto gravosa" in posa.lower():
        temp_lavoro = temp_regime
    elif "ventilazione" in posa.lower():
        temp_lavoro = temp_regime - 15.0
    else:
        temp_lavoro = temp_regime - 5.0
        
    # Formula CEI di variazione termica: rho_t = rho_20 * (1 + 0.004 * (T - 20))
    rho_t = rho_base * (1.0 + 0.004 * (temp_lavoro - 20.0))
    return rho_t, temp_lavoro
