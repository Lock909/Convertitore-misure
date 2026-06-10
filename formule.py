import math

def calcola_ohm(ricerca, input_1, input_2):
    if ricerca == "Tensione": return f"Tensione (V): {input_1 * input_2:.4f} V"
    elif ricerca == "Corrente": return f"Corrente (I): {input_1 / input_2:.4f} A" if input_2 != 0 else "Errore: R=0"
    else: return f"Resistenza (R): {input_1 / input_2:.4f} \u03a9" if input_2 != 0 else "Errore: I=0"

def ottieni_sezioni():
    return (1.5, 2.5, 4.0, 6.0, 10.0, 16.0, 25.0, 35.0, 50.0, 70.0, 95.0, 120.0)

def ottieni_interruttori():
    return (6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125)

def calcola_sezione_protezione(i_max, densita):
    sezione_teorica = i_max / densita
    sez_scelta = 120.0
    for s in ottieni_sezioni():
        if s >= sezione_teorica:
            sez_scelta = s
            break
    int_scelto = 125
    for val_i in ottieni_interruttori():
        if val_i >= i_max:
            int_scelto = val_i
            break
    return int_scelto, sez_scelta, sezione_teorica

def calcola_caduta_avanzata(materiale, isolante, posa, fasi, amp, metri, sez, cos_phi, temp_amb, iz_nominale, num_circuiti):
    # 1. Resistività base del materiale a 20°C
    rho_20 = 0.0175 if materiale == "Rame" else 0.0282
    temp_regime = 70.0 if "PVC" in isolante else 90.0
    
    # 2. TABELLA CEI: Coefficiente termico ambientale (K1)
    tabella_k1 = {
        10: 1.22 if temp_regime == 70 else 1.15,
        15: 1.17 if temp_regime == 70 else 1.11,
        20: 1.12 if temp_regime == 70 else 1.07,
        25: 1.06 if temp_regime == 70 else 1.04,
        30: 1.00 if temp_regime == 70 else 1.00,
        35: 0.94 if temp_regime == 70 else 0.96,
        40: 0.87 if temp_regime == 70 else 0.91,
        45: 0.79 if temp_regime == 70 else 0.87,
        50: 0.71 if temp_regime == 70 else 0.82,
        55: 0.61 if temp_regime == 70 else 0.76,
        60: 0.50 if temp_regime == 70 else 0.71
    }
    k1 = tabella_k1.get(int(round(temp_amb / 5.0) * 5), 1.0)
    
    # 3. TABELLA CEI UNEL 35024: Coefficiente di raggruppamento circuiti affiancati (K2)
    # Valori standard per cavi in fascio o nello stesso condotto protettivo
    if num_circuiti <= 1: k2 = 1.00
    elif num_circuiti == 2: k2 = 0.80
    elif num_circuiti == 3: k2 = 0.70
    elif num_circuiti == 4: k2 = 0.65
    elif num_circuiti in (5, 6): k2 = 0.60
    elif num_circuiti in (7, 8, 9): k2 = 0.50
    else: k2 = 0.40 # 10 o più circuiti affiancati
    
    # 4. Calcolo della portata reale corretta (Iz_reale = Iz_nominale * K1 * K2)
    iz_corretta = iz_nominale * k1 * k2
    
    # 5. Formula di riscaldamento del conduttore sotto carico
    tasso_utilizzo = amp / iz_corretta if iz_corretta > 0 else 1.0
    temp_lavoro = temp_amb + (temp_regime - temp_amb) * (tasso_utilizzo ** 2)
    
    if temp_lavoro > temp_regime:
        temp_lavoro = temp_regime
        
    # 6. Resistività termica reale del cavo (rho_t) alla vera temperatura operativa
    rho_t = rho_20 * (1.0 + 0.004 * (temp_lavoro - 20.0))
    
    # 7. Calcolo Caduta di Tensione Vettoriale (con reattanza induttiva fissa 0.08 Ohm/km)
    r_km = (rho_t / sez) * 1000.0
    sin_phi = math.sqrt(1.0 - cos_phi**2)
    z_fattore = (r_km * cos_phi) + (0.08 * sin_phi)
    
    k = 2.0 if fasi == "Monofase" else math.sqrt(3)
    dv = (k * amp * (metri / 1000.0) * z_fattore)
    
    return dv, temp_lavoro, rho_t, k1, k2, iz_corretta
