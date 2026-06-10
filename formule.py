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
    rho_base = 0.0175 if materiale == "Rame" else 0.0282
    temp_regime = 70.0 if "PVC" in isolante else 90.0
    if "molto gravosa" in posa.lower():
        temp_lavoro = temp_regime
    elif "ventilazione" in posa.lower():
        temp_lavoro = temp_regime - 15.0
    else:
        temp_lavoro = temp_regime - 5.0
    rho_t = rho_base * (1.0 + 0.004 * (temp_lavoro - 20.0))
    r_km = (rho_t / sez) * 1000.0
    x_km = 0.08
    sin_phi = math.sqrt(1.0 - cos_phi**2)
    z_fattore = (r_km * cos_phi) + (x_km * sin_phi)
    k = 2.0 if fasi == "Monofase" else math.sqrt(3)
    dv = (k * amp * (metri / 1000.0) * z_fattore)
    return dv, temp_lavoro, rho_t

def info_tipo_dato(tipo):
    db_plc = {
        "BYTE": ("8 Bit (1 Byte)", "Nessuno (Sequenza di bit)", "0", "255 (Esadecimale: 16#FF)"),
        "WORD": ("16 Bit (2 Byte) - Occupa 1 reg. %R", "Nessuno (Sequenza di bit)", "0", "65535 (Esadecimale: 16#FFFF)"),
        "DWORD": ("32 Bit (4 Byte) - Occupa 2 reg. %R", "Nessuno (Sequenza di bit)", "0", "4294967295 (Esadecimale: 16#FFFFFFFF)"),
        "INT (Integer)": ("16 Bit (2 Byte) - Occupa 1 reg. %R", "Intero con segno", "-32'768", "+32'767"),
        "UINT (Unsigned INT)": ("16 Bit (2 Byte) - Occupa 1 reg. %R", "Intero senza segno", "0", "+65'535"),
        "DINT (Double INT)": ("32 Bit (4 Byte) - Occupa 2 reg. %R", "Intero doppio con segno", "-2'147'483'648", "+2'147'483'647"),
        "UDINT (Unsigned DINT)": ("32 Bit (4 Byte) - Occupa 2 reg. %R", "Intero doppio senza segno", "0", "+4'294'967'295"),
        "REAL (Float)": ("32 Bit (4 Byte) - Occupa 2 reg. %R", "Virgola mobile (Precisione singola)", "-3.402823e+38", "+3.402823e+38")
    }
    return db_plc.get(tipo, ("-", "-", "-", "-"))

def esegui_scalatura(val_grezzo, in_min, in_max, out_min, out_max):
    if in_max == in_min:
        return 0.0, "Errore: I limiti di ingresso PLC non possono essere uguali!"
    val_scalato = out_min + (val_grezzo - in_min) * (out_max - out_min) / (in_max - in_min)
    return val_scalato, "OK"

# --- NUOVE FUNZIONI AVANZATE PER PLC & RX3I ---
def calcola_esplosione_bits(valore_int):
    # Converte un intero in una lista di 16 bit (0 o 1) dal bit 0 al bit 15
    valore_int = int(valore_int) & 0xFFFF  # Forza il limite a 16 bit
    lista_bits = list()
    for b in range(16):
        lista_bits.append((valore_int >> b) & 1)
    return lista_bits

def calcola_limiti_memoria_rx3i(prefisso, start_idx, quantita, tipo_var):
    # Calcola l'ultimo indirizzo occupato per evitare sovrascritture nei registri
    moltiplicatori = {"1 Bit (Digital I/O)": 1, "16 Bit (WORD / INT)": 1, "32 Bit (REAL / DINT)": 2}
    offset = moltiplicatori.get(tipo_var, 1) * quantita
    end_idx = start_idx + offset - 1
    return f"{prefisso}{start_idx:04d} ➔ {prefisso}{end_idx:04d}"
