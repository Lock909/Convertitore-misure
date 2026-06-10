def info_tipo_dato(tipo):
    db_plc = {
        "BYTE": ("8 Bit (1 Byte)", "Nessuno (Sequenza di bit)", "0", "255"),
        "WORD": ("16 Bit (2 Byte) - 1 reg. %R", "Nessuno (Sequenza di bit)", "0", "65535"),
        "DWORD": ("32 Bit (4 Byte) - 2 reg. %R", "Nessuno (Sequenza di bit)", "0", "4294967295"),
        "INT (Integer)": ("16 Bit (2 Byte) - 1 reg. %R", "Intero con segno", "-32'768", "+32'767"),
        "UINT (Unsigned INT)": ("16 Bit (2 Byte) - 1 reg. %R", "Intero senza segno", "0", "+65'535"),
        "DINT (Double INT)": ("32 Bit (4 Byte) - 2 reg. %R", "Intero doppio con segno", "-2'147'483'648", "+2'147'483'647"),
        "REAL (Float)": ("32 Bit (4 Byte) - 2 reg. %R", "Virgola mobile", "-3.4e+38", "+3.4e+38")
    }
    return db_plc.get(tipo, ("-", "-", "-", "-"))

def esegui_scalatura(val_grezzo, in_min, in_max, out_min, out_max):
    if in_max == in_min: return 0.0, "Errore: Limiti uguali!"
    return (out_min + (val_grezzo - in_min) * (out_max - out_min) / (in_max - in_min)), "OK"

def calcola_esplosione_bits(valore_int):
    lista_bits = list()
    for b in range(16):
        lista_bits.append((int(valore_int) >> b) & 1)
    return lista_bits

def calcola_limiti_memoria_rx3i(prefisso, start_idx, quantita, tipo_var):
    offset = 2 if "32 Bit" in tipo_var else 1
    return f"{prefisso}{start_idx:04d} ➔ {prefisso}{(start_idx + offset * quantita - 1):04d}"
