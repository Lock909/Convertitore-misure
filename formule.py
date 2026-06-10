import math

def calcola_ohm(ricerca, input_1, input_2):
    if ricerca == "Tensione": return f"Tensione (V): {input_1 * input_2:.4f} V"
    elif ricerca == "Corrente": return f"Corrente (I): {input_1 / input_2:.4f} A" if input_2 != 0 else "Errore: R=0"
    else: return f"Resistenza (R): {input_1 / input_2:.4f} \u03a9" if input_2 != 0 else "Errore: I=0"

def calcola_sezione_protezione(i_max, densita):
    sezione_teorica = i_max / densita
    sez_scelta = 120.0
    for s in (1.5, 2.5, 4.0, 6.0, 10.0, 16.0, 25.0, 35.0, 50.0, 70.0, 95.0, 120.0):
        if s >= sezione_teorica:
            sez_scelta = s
            break
    int_scelto = 125
    for val_i in (6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125):
        if val_i >= i_max:
            int_scelto = val_i
            break
    return int_scelto, sez_scelta, sezione_teorica

def calcola_caduta_avanzata(materiale, isolante, posa, fasi, amp, metri, sez, cos_phi):
    rho = 0.0175 if materiale == "Rame" else 0.0282
    temp_regime = 70.0 if "PVC" in isolante else 90.0
    temp_lavoro = temp_regime if "molto gravosa" in posa.lower() else (temp_regime - 15.0 if "ventilazione" in posa.lower() else temp_regime - 5.0)
    rho_t = rho * (1.0 + 0.004 * (temp_lavoro - 20.0))
    r_km = (rho_t / sez) * 1000.0
    sin_phi = math.sqrt(1.0 - cos_phi**2)
    z_fattore = (r_km * cos_phi) + (0.08 * sin_phi)
    k = 2.0 if fasi == "Monofase" else math.sqrt(3)
    return (k * amp * (metri / 1000.0) * z_fattore), temp_lavoro, rho_t
