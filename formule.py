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

def calcola_caduta_avanzata(materiale, isolante, posa, fasi, amp, metri, sez, cos_phi):
    # 1. Resistività base a 20°C
    rho_base = 0.0175 if materiale == "Rame" else 0.0282
    temp_regime = 70.0 if "PVC" in isolante else 90.0
    
    # 2. Correzione temperatura lavoro in base alla posa
    if "molto gravosa" in posa.lower():
        temp_lavoro = temp_regime
    elif "ventilazione" in posa.lower():
        temp_lavoro = temp_regime - 15.0
    else:
        temp_lavoro = temp_regime - 5.0
        
    # 3. Resistenza R corretta termicamente per chilometro
    rho_t = rho_base * (1.0 + 0.004 * (temp_lavoro - 20.0))
    r_km = (rho_t / sez) * 1000.0
    
    # 4. Reattanza induttiva convenzionale standard per km (Norma CEI)
    x_km = 0.08
    
    # 5. Calcolo componenti trigonometriche dello sfasamento
    sin_phi = math.sqrt(1.0 - cos_phi**2)
    
    # 6. Impedenza totale equivalente combinata del cavo
    z_fattore = (r_km * cos_phi) + (x_km * sin_phi)
    
    # 7. Calcolo dV in Volt (metri convertiti in km dividendo per 1000)
    k = 2.0 if fasi == "Monofase" else math.sqrt(3)
    dv = (k * amp * (metri / 1000.0) * z_fattore)
    
    return dv, temp_lavoro, rho_t
