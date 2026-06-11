# ==============================================================================
# automazione.py — Utility per PLC GE PACSystems RX3i
# Standard: IEC 61131-3
# Riferimento: GE/Emerson PACSystems RX3i System Manual (IC695SYS001)
# ==============================================================================

import math


# ------------------------------------------------------------------------------
# Database tipi di dato PLC (IEC 61131-3 + specifiche RX3i)
# ------------------------------------------------------------------------------

_DB_TIPI_DATO = {
    # Tipo                   (dimensione,                    categoria,                    min,               max)
    "BOOL":                  ("1 Bit — %I/%Q/%M",            "Booleano (true/false)",      "0 (FALSE)",       "1 (TRUE)"),
    "BYTE":                  ("8 Bit (1 Byte)",               "Sequenza di bit",            "0",               "255"),
    "WORD":                  ("16 Bit — 1 reg. %R",          "Sequenza di bit",            "0",               "65535"),
    "DWORD":                 ("32 Bit — 2 reg. %R",          "Sequenza di bit",            "0",               "4294967295"),
    "INT (Integer)":         ("16 Bit — 1 reg. %R",          "Intero con segno",           "-32'768",         "+32'767"),
    "UINT (Unsigned INT)":   ("16 Bit — 1 reg. %R",          "Intero senza segno",         "0",               "+65'535"),
    "DINT (Double INT)":     ("32 Bit — 2 reg. %R",          "Intero doppio con segno",    "-2'147'483'648",  "+2'147'483'647"),
    "UDINT (Unsigned DINT)": ("32 Bit — 2 reg. %R",          "Intero doppio senza segno",  "0",               "+4'294'967'295"),
    "REAL (Float)":          ("32 Bit — 2 reg. %R",          "Virgola mobile IEEE 754",    "-3.4028e+38",     "+3.4028e+38"),
}


def info_tipo_dato(tipo):
    """Ritorna (dimensione, categoria, min, max) per il tipo dato PLC."""
    return _DB_TIPI_DATO.get(tipo, ("-", "-", "-", "-"))


# ------------------------------------------------------------------------------
# Database CPU PACSystems RX3i
#
# NOTA: Le dimensioni delle aree %I/%Q/%M/%R/%AI/%AQ sono CONFIGURABILI
# in Proficy Machine Edition (Hardware Configuration → CPU → Memory).
# I valori "tipici_pmea" sono i default più comuni per nuovi progetti;
# il limite reale dipende dalla RAM totale del modello CPU.
# ------------------------------------------------------------------------------

_DB_CPU_RX3I = {
    "IC695CPE302 (1 MB)": {
        "ram_programma_mb": 1,
        "note": "CPU base RX3i. Progetti piccoli/medi. No Ethernet embedded.",
        "tipici_pme": {
            "%I":  2048,   # bit
            "%Q":  2048,   # bit
            "%M":  8192,   # bit
            "%R":  4096,   # word (16-bit)
            "%AI": 2048,   # word
            "%AQ": 512,    # word
            "%G":  7680,   # bit (Genius bus)
        },
    },
    "IC695CPE305 (5 MB)": {
        "ram_programma_mb": 5,
        "note": "CPU standard. Uso più comune in campo. No Ethernet embedded.",
        "tipici_pme": {
            "%I":  2048,
            "%Q":  2048,
            "%M":  8192,
            "%R":  8192,
            "%AI": 2048,
            "%AQ": 512,
            "%G":  7680,
        },
    },
    "IC695CPE310 (10 MB)": {
        "ram_programma_mb": 10,
        "note": "CPU avanzata. Impianti medi-grandi. No Ethernet embedded.",
        "tipici_pme": {
            "%I":  4096,
            "%Q":  4096,
            "%M":  8192,
            "%R":  8192,
            "%AI": 4096,
            "%AQ": 1024,
            "%G":  7680,
        },
    },
    "IC695CPE400 (20 MB + Ethernet)": {
        "ram_programma_mb": 20,
        "note": "Ethernet embedded (SRTP, Modbus TCP, OPC). Supporta ridondanza.",
        "tipici_pme": {
            "%I":  8192,
            "%Q":  8192,
            "%M":  16384,
            "%R":  16384,
            "%AI": 8192,
            "%AQ": 2048,
            "%G":  7680,
        },
    },
    "IC695CPE410 (High Performance)": {
        "ram_programma_mb": 64,
        "note": "CPU ad alte prestazioni. Tempi di scansione ridotti. Ethernet embedded.",
        "tipici_pme": {
            "%I":  32768,
            "%Q":  32768,
            "%M":  32768,
            "%R":  32768,
            "%AI": 32768,
            "%AQ": 32768,
            "%G":  7680,
        },
    },
    "IC694CPU364 (legacy IC694)": {
        "ram_programma_mb": 0.24,   # 240 KB (0.24 MB)
        "note": "CPU della famiglia IC694 (backplane compatto). Non supporta moduli IC695.",
        "tipici_pme": {
            "%I":  2048,
            "%Q":  2048,
            "%M":  4096,
            "%R":  4096,
            "%AI": 1024,
            "%AQ": 256,
            "%G":  7680,
        },
    },
}


def info_cpu_rx3i(modello):
    """Ritorna il dict di info per il modello CPU selezionato."""
    return _DB_CPU_RX3I.get(modello, None)


# ------------------------------------------------------------------------------
# Database moduli analogici PACSystems RX3i
#
# Struttura di ogni configurazione canale:
#   "nome_config": {
#       "in_min": float,   raw PLC a segnale minimo
#       "in_max": float,   raw PLC a segnale massimo
#       "unita":  str,     unità fisica del segnale
#       "note":   str,
#   }
#
# ATTENZIONE: la configurazione del canale va impostata in PME prima di
# usare questi valori. Scheda non configurata → dati non attendibili.
# ------------------------------------------------------------------------------

_DB_MODULI_ANALOGICI = {

    # ================================================================
    # IC694 — famiglia COMPATTA (12-bit, 4096 counts)
    # ================================================================

    "IC694ALG220 — 4ch Analog Input (12-bit)": {
        "famiglia":  "IC694",
        "canali":    4,
        "tipo":      "Input",
        "resol":     "12-bit (0-4095 counts)",
        "note_mod":  "Configurazione per canale in PME. Range 0-4095 raw.",
        "config": {
            "0-10 V":          {"in_min": 0,     "in_max": 4095,  "unita": "V",  "note": ""},
            "0-5 V":           {"in_min": 0,     "in_max": 4095,  "unita": "V",  "note": ""},
            "±10 V (bip.)":    {"in_min": -2048, "in_max": 2047,  "unita": "V",  "note": ""},
            "±5 V (bip.)":     {"in_min": -2048, "in_max": 2047,  "unita": "V",  "note": ""},
            "0-20 mA":         {"in_min": 0,     "in_max": 4095,  "unita": "mA", "note": ""},
            "4-20 mA":         {"in_min": 819,   "in_max": 4095,  "unita": "mA", "note": "4mA≈819, 20mA=4095. Wire break: raw<500 circa"},
        },
    },

    "IC694ALG221 — 4ch Analog Input isolato (12-bit)": {
        "famiglia":  "IC694",
        "canali":    4,
        "tipo":      "Input (isolato)",
        "resol":     "12-bit (0-4095 counts)",
        "note_mod":  "Isolamento galvanico per canale. Stesso range ALG220.",
        "config": {
            "0-10 V":          {"in_min": 0,     "in_max": 4095,  "unita": "V",  "note": ""},
            "±10 V (bip.)":    {"in_min": -2048, "in_max": 2047,  "unita": "V",  "note": ""},
            "0-20 mA":         {"in_min": 0,     "in_max": 4095,  "unita": "mA", "note": ""},
            "4-20 mA":         {"in_min": 819,   "in_max": 4095,  "unita": "mA", "note": "4mA≈819"},
        },
    },

    "IC694ALG390 — 2ch Analog Output (12-bit)": {
        "famiglia":  "IC694",
        "canali":    2,
        "tipo":      "Output",
        "resol":     "12-bit",
        "note_mod":  "Uscita analogica. Scrivere il raw in %AQ.",
        "config": {
            "0-10 V":          {"in_min": 0,     "in_max": 4095,  "unita": "V",  "note": ""},
            "±10 V (bip.)":    {"in_min": -2048, "in_max": 2047,  "unita": "V",  "note": ""},
            "0-20 mA":         {"in_min": 0,     "in_max": 4095,  "unita": "mA", "note": ""},
            "4-20 mA":         {"in_min": 819,   "in_max": 4095,  "unita": "mA", "note": "4mA≈819"},
        },
    },

    "IC694ALG740 — 4ch Thermocouple Input": {
        "famiglia":  "IC694",
        "canali":    4,
        "tipo":      "Input TC",
        "resol":     "0.1 °C per digit (es. raw 250 = 25.0 °C)",
        "note_mod":  "Tipo termocoppia configurabile per canale in PME. Raw = °C × 10.",
        "config": {
            "Tipo J  (-200 → +900 °C)":   {"in_min": -2000, "in_max": 9000,  "unita": "×0.1°C", "note": ""},
            "Tipo K  (-200 → +1370 °C)":  {"in_min": -2000, "in_max": 13700, "unita": "×0.1°C", "note": ""},
            "Tipo E  (-200 → +1000 °C)":  {"in_min": -2000, "in_max": 10000, "unita": "×0.1°C", "note": ""},
            "Tipo T  (-200 → +400 °C)":   {"in_min": -2000, "in_max": 4000,  "unita": "×0.1°C", "note": ""},
            "Tipo R  (0 → +1760 °C)":     {"in_min": 0,     "in_max": 17600, "unita": "×0.1°C", "note": ""},
            "Tipo S  (0 → +1760 °C)":     {"in_min": 0,     "in_max": 17600, "unita": "×0.1°C", "note": ""},
            "Tipo B  (+200 → +1820 °C)":  {"in_min": 2000,  "in_max": 18200, "unita": "×0.1°C", "note": ""},
            "Tipo N  (-200 → +1300 °C)":  {"in_min": -2000, "in_max": 13000, "unita": "×0.1°C", "note": ""},
        },
    },

    "IC694ALG780 — 4ch RTD Input": {
        "famiglia":  "IC694",
        "canali":    4,
        "tipo":      "Input RTD",
        "resol":     "0.1 °C per digit (es. raw 1234 = 123.4 °C)",
        "note_mod":  "Tipo RTD configurabile per canale in PME. Raw = °C × 10.",
        "config": {
            "Pt100  (-200 → +870 °C)":   {"in_min": -2000, "in_max": 8700,  "unita": "×0.1°C", "note": ""},
            "Pt1000 (-200 → +870 °C)":   {"in_min": -2000, "in_max": 8700,  "unita": "×0.1°C", "note": ""},
            "Ni120  (-80 → +260 °C)":    {"in_min": -800,  "in_max": 2600,  "unita": "×0.1°C", "note": ""},
            "Cu10   (-200 → +260 °C)":   {"in_min": -2000, "in_max": 2600,  "unita": "×0.1°C", "note": "Bobina rame 10Ω"},
        },
    },

    # ================================================================
    # IC695 — famiglia RX3i STANDARD (16-bit scalati, 0-32000)
    # ================================================================

    "IC695ALG600 — 4ch Universal Analog Input": {
        "famiglia":  "IC695",
        "canali":    4,
        "tipo":      "Input",
        "resol":     "15-bit effettivi, scalati a 0-32000",
        "note_mod":  "Modulo universale. Ogni canale configurabile indipendentemente in PME.",
        "config": {
            "0-10 V":                  {"in_min": 0,      "in_max": 32000,  "unita": "V",  "note": ""},
            "0-5 V":                   {"in_min": 0,      "in_max": 32000,  "unita": "V",  "note": ""},
            "0-1 V":                   {"in_min": 0,      "in_max": 32000,  "unita": "V",  "note": ""},
            "±10 V (bip.)":            {"in_min": -32000, "in_max": 32000,  "unita": "V",  "note": ""},
            "±5 V (bip.)":             {"in_min": -32000, "in_max": 32000,  "unita": "V",  "note": ""},
            "0-20 mA":                 {"in_min": 0,      "in_max": 32000,  "unita": "mA", "note": ""},
            "4-20 mA (su scala 0-20)": {"in_min": 6400,   "in_max": 32000,  "unita": "mA", "note": "4mA=6400, 20mA=32000. Wire break: raw<3840"},
            "4-20 mA (su scala 4-20)": {"in_min": 0,      "in_max": 32000,  "unita": "mA", "note": "Se PME configurato 4-20mA full scale: 4mA=0"},
            "±20 mA (bip.)":           {"in_min": -32000, "in_max": 32000,  "unita": "mA", "note": ""},
        },
    },

    "IC695ALG608 — 8ch Universal Analog Input": {
        "famiglia":  "IC695",
        "canali":    8,
        "tipo":      "Input",
        "resol":     "15-bit effettivi, scalati a 0-32000",
        "note_mod":  "Come ALG600 ma 8 canali. Stesse configurazioni disponibili.",
        "config": {
            "0-10 V":                  {"in_min": 0,      "in_max": 32000,  "unita": "V",  "note": ""},
            "0-5 V":                   {"in_min": 0,      "in_max": 32000,  "unita": "V",  "note": ""},
            "±10 V (bip.)":            {"in_min": -32000, "in_max": 32000,  "unita": "V",  "note": ""},
            "±5 V (bip.)":             {"in_min": -32000, "in_max": 32000,  "unita": "V",  "note": ""},
            "0-20 mA":                 {"in_min": 0,      "in_max": 32000,  "unita": "mA", "note": ""},
            "4-20 mA (su scala 0-20)": {"in_min": 6400,   "in_max": 32000,  "unita": "mA", "note": "4mA=6400"},
            "4-20 mA (su scala 4-20)": {"in_min": 0,      "in_max": 32000,  "unita": "mA", "note": "4mA=0"},
        },
    },

    "IC695ALG616 — 16ch Universal Analog Input": {
        "famiglia":  "IC695",
        "canali":    16,
        "tipo":      "Input",
        "resol":     "15-bit effettivi, scalati a 0-32000",
        "note_mod":  "16 canali. Stesse configurazioni ALG600/608.",
        "config": {
            "0-10 V":                  {"in_min": 0,      "in_max": 32000,  "unita": "V",  "note": ""},
            "±10 V (bip.)":            {"in_min": -32000, "in_max": 32000,  "unita": "V",  "note": ""},
            "0-20 mA":                 {"in_min": 0,      "in_max": 32000,  "unita": "mA", "note": ""},
            "4-20 mA (su scala 0-20)": {"in_min": 6400,   "in_max": 32000,  "unita": "mA", "note": "4mA=6400"},
            "4-20 mA (su scala 4-20)": {"in_min": 0,      "in_max": 32000,  "unita": "mA", "note": "4mA=0"},
        },
    },

    "IC695ALG704 — 4ch Analog Output": {
        "famiglia":  "IC695",
        "canali":    4,
        "tipo":      "Output",
        "resol":     "15-bit, scalati a 0-32000",
        "note_mod":  "Uscita analogica. Scrivere raw in %AQ.",
        "config": {
            "0-10 V":                  {"in_min": 0,      "in_max": 32000,  "unita": "V",  "note": ""},
            "±10 V (bip.)":            {"in_min": -32000, "in_max": 32000,  "unita": "V",  "note": ""},
            "0-20 mA":                 {"in_min": 0,      "in_max": 32000,  "unita": "mA", "note": ""},
            "4-20 mA (su scala 0-20)": {"in_min": 6400,   "in_max": 32000,  "unita": "mA", "note": "4mA=6400"},
        },
    },

    "IC695ALG708 — 8ch Analog Output": {
        "famiglia":  "IC695",
        "canali":    8,
        "tipo":      "Output",
        "resol":     "15-bit, scalati a 0-32000",
        "note_mod":  "Come ALG704 ma 8 canali.",
        "config": {
            "0-10 V":                  {"in_min": 0,      "in_max": 32000,  "unita": "V",  "note": ""},
            "±10 V (bip.)":            {"in_min": -32000, "in_max": 32000,  "unita": "V",  "note": ""},
            "0-20 mA":                 {"in_min": 0,      "in_max": 32000,  "unita": "mA", "note": ""},
            "4-20 mA (su scala 0-20)": {"in_min": 6400,   "in_max": 32000,  "unita": "mA", "note": "4mA=6400"},
        },
    },


    "IC694ALG222 — 8ch Analog Input (12-bit)": {
        "famiglia":  "IC694",
        "canali":    8,
        "tipo":      "Input",
        "resol":     "12-bit (0-4095 counts)",
        "note_mod":  "8 canali su backplane IC694. Configurazione per canale in PME.",
        "config": {
            "0-10 V":          {"in_min": 0,     "in_max": 4095,  "unita": "V",  "note": ""},
            "0-5 V":           {"in_min": 0,     "in_max": 4095,  "unita": "V",  "note": ""},
            "±10 V (bip.)":    {"in_min": -2048, "in_max": 2047,  "unita": "V",  "note": ""},
            "0-20 mA":         {"in_min": 0,     "in_max": 4095,  "unita": "mA", "note": ""},
            "4-20 mA":         {"in_min": 819,   "in_max": 4095,  "unita": "mA", "note": "4mA≈819"},
        },
    },

    "IC695ALG806 — 6ch High-Speed Analog Input": {
        "famiglia":  "IC695",
        "canali":    6,
        "tipo":      "Input (alta velocità)",
        "resol":     "16-bit, scalati a 0-32000 (campionamento rapido)",
        "note_mod":  "Modulo ad alta velocità di campionamento. Ideale per controllo di processo rapido e vibrazioni.",
        "config": {
            "0-10 V":                  {"in_min": 0,      "in_max": 32000,  "unita": "V",  "note": ""},
            "0-5 V":                   {"in_min": 0,      "in_max": 32000,  "unita": "V",  "note": ""},
            "±10 V (bip.)":            {"in_min": -32000, "in_max": 32000,  "unita": "V",  "note": ""},
            "±5 V (bip.)":             {"in_min": -32000, "in_max": 32000,  "unita": "V",  "note": ""},
            "0-20 mA":                 {"in_min": 0,      "in_max": 32000,  "unita": "mA", "note": ""},
            "4-20 mA (su scala 0-20)": {"in_min": 6400,   "in_max": 32000,  "unita": "mA", "note": "4mA=6400"},
        },
    },

    # ================================================================
    # Siemens S7-300/400 — per confronto
    # ================================================================

    "Siemens S7 — AI generico (0-27648)": {
        "famiglia":  "Siemens",
        "canali":    -1,
        "tipo":      "Input",
        "resol":     "12-bit scalati a 0-27648",
        "note_mod":  "Standard Siemens per analogici S7-300/400/1200/1500.",
        "config": {
            "0-10 V":        {"in_min": 0,      "in_max": 27648,  "unita": "V",  "note": ""},
            "0-5 V":         {"in_min": 0,      "in_max": 27648,  "unita": "V",  "note": ""},
            "±10 V (bip.)":  {"in_min": -27648, "in_max": 27648,  "unita": "V",  "note": ""},
            "0-20 mA":       {"in_min": 0,      "in_max": 27648,  "unita": "mA", "note": ""},
            "4-20 mA":       {"in_min": 5530,   "in_max": 27648,  "unita": "mA", "note": "4mA≈5530, 20mA=27648"},
        },
    },
}


def lista_moduli():
    """Ritorna la lista dei nomi dei moduli disponibili."""
    return list(_DB_MODULI_ANALOGICI.keys())


def info_modulo(nome_modulo):
    """Ritorna il dict completo di info per il modulo selezionato."""
    return _DB_MODULI_ANALOGICI.get(nome_modulo, None)


def get_range_canale(nome_modulo, nome_config):
    """
    Ritorna (in_min, in_max, unita, note) per la configurazione canale scelta.
    Ritorna None se modulo o configurazione non trovati.
    """
    mod = _DB_MODULI_ANALOGICI.get(nome_modulo)
    if mod is None:
        return None
    cfg = mod["config"].get(nome_config)
    if cfg is None:
        return None
    return cfg["in_min"], cfg["in_max"], cfg["unita"], cfg["note"]


# ------------------------------------------------------------------------------
# Scalatura analogica (raw PLC → unità ingegneristica)
# ------------------------------------------------------------------------------

_SOGLIA_ROTTURA_CAVO_PCT = 0.05   # 5% — soglia rilevamento wire break su 4-20mA


def esegui_scalatura(val_grezzo, in_min, in_max, out_min, out_max,
                     abilita_clamp=False):
    """
    Scala linearmente un valore grezzo PLC verso l'unità ingegneristica.

    Formula: out = out_min + (val_grezzo - in_min) / (in_max - in_min) * (out_max - out_min)

    Ritorna (valore_scalato, stato)
    stato: 'OK' | 'FUORI_RANGE' | 'ROTTURA_CAVO' | stringa di errore
    """
    if in_max == in_min:
        return 0.0, "Errore: in_min e in_max non possono essere uguali."

    # Wire break: segnale sotto la soglia (applicabile solo se in_min > 0, es. 4-20mA)
    if in_min > 0 and val_grezzo < in_min * (1.0 - _SOGLIA_ROTTURA_CAVO_PCT):
        return 0.0, "ROTTURA_CAVO"

    stato = "OK" if in_min <= val_grezzo <= in_max else "FUORI_RANGE"

    valore = out_min + (val_grezzo - in_min) * (out_max - out_min) / (in_max - in_min)

    if abilita_clamp:
        lo, hi = min(out_min, out_max), max(out_min, out_max)
        valore = max(lo, min(hi, valore))

    return valore, stato


def esegui_scalatura_inversa(val_engineering, in_min, in_max, out_min, out_max):
    """
    Scala un valore ingegneristico verso il raw PLC (setpoint supervisione → PLC).
    Ritorna (valore_raw, stato).
    """
    if out_max == out_min:
        return 0.0, "Errore: out_min e out_max non possono essere uguali."

    raw = in_min + (val_engineering - out_min) * (in_max - in_min) / (out_max - out_min)
    stato = "OK" if in_min <= raw <= in_max else "FUORI_RANGE"
    return raw, stato


# ------------------------------------------------------------------------------
# Esplosione WORD / composizione WORD
# ------------------------------------------------------------------------------

def calcola_esplosione_bits(valore_int):
    """
    Scompone un intero a 16 bit in lista di bit.
    Indice 0 = LSB, indice 15 = MSB.
    """
    valore_int = int(valore_int) & 0xFFFF
    return [(valore_int >> b) & 1 for b in range(16)]


def componi_word_da_bits(lista_bits):
    """
    Compone un intero WORD (0-65535) da una lista di 16 bit (indice 0 = LSB).
    """
    if len(lista_bits) != 16:
        raise ValueError("La lista deve contenere esattamente 16 bit.")
    word = 0
    for i, bit in enumerate(lista_bits):
        if bit:
            word |= (1 << i)
    return word & 0xFFFF


# ------------------------------------------------------------------------------
# Calcolo intervallo di memoria RX3i
# ------------------------------------------------------------------------------

def calcola_limiti_memoria_rx3i(prefisso, start_idx, quantita, tipo_var):
    """
    Calcola l'intervallo di indirizzi occupato da un array di variabili RX3i.

    Aree bit (%I, %Q, %M): ogni indirizzo = 1 bit.
    Aree word (%R, %AI, %AQ): ogni indirizzo = 1 word (16 bit).
    BOOL in %R: packed 16 per registro → ceil(quantita/16) registri.
    REAL/DINT in %R: 2 registri per variabile.
    """
    aree_bit = ("%I", "%Q", "%M")

    if "32 Bit" in tipo_var:
        offset = 2 * int(quantita)
    elif "1 Bit" in tipo_var:
        if prefisso.upper() in aree_bit:
            offset = int(quantita)
        else:
            offset = math.ceil(int(quantita) / 16)
    else:
        offset = int(quantita)

    end_idx = start_idx + offset - 1
    return f"{prefisso}{start_idx:04d} ➔ {prefisso}{end_idx:04d}"
