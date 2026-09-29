# ==============================================================================
# siemens_s7.py — Utility per PLC Siemens SIMATIC S7-1200 / S7-1500 (TIA Portal)
# Standard: IEC 61131-3 (l'SCL Siemens implementa lo Structured Text)
# Riferimenti: manuali di sistema SIMATIC S7-1200/S7-1500 e Information System
# di TIA Portal (tipi di dato, rappresentazione dei valori analogici, istruzioni
# NORM_X/SCALE_X, timer e contatori IEC).
#
# I valori sono quelli pubblicati da Siemens, ma variano con famiglia di CPU e
# firmware: per il progetto reale va sempre verificato sul manuale della CPU e
# sulla versione di TIA Portal in uso. Il codice SCL generato è un punto di
# partenza da incollare in un blocco e provare, non codice certificato.
# ==============================================================================

import re

# ------------------------------------------------------------------------------
# Tipi di dato
# ------------------------------------------------------------------------------

_S7_1500 = "Solo S7-1500 (non supportato su S7-1200)"
_ENTRAMBE = "S7-1200 e S7-1500"


def _tipo(bit, categoria, minimo, massimo, esempio, disponibile, note):
    return {
        "dimensione_bit": bit,
        "categoria": categoria,
        "minimo": minimo,
        "massimo": massimo,
        "esempio_costante": esempio,
        "disponibile_su": disponibile,
        "note": note,
    }


_TIPI_DATO_S7 = {
    "Bool": _tipo(1, "Booleano", "FALSE (0)", "TRUE (1)", "TRUE, FALSE, 1, 0", _ENTRAMBE,
                  "Indirizzo di bit, es. %M10.3. In un blocco ottimizzato i Bool vengono impacchettati."),
    "Byte": _tipo(8, "Sequenza di bit", "16#00", "16#FF", "16#1F, 2#0001_1111", _ENTRAMBE,
                  "Nessun segno: per aritmetica con segno usare SInt o USInt."),
    "Word": _tipo(16, "Sequenza di bit", "16#0000", "16#FFFF", "16#00FF", _ENTRAMBE,
                  "Tipo predefinito degli ingressi analogici periferici (%IW). Per usarlo nei calcoli va convertito (es. WORD_TO_INT)."),
    "DWord": _tipo(32, "Sequenza di bit", "16#0000_0000", "16#FFFF_FFFF", "16#0000_FFFF", _ENTRAMBE,
                   "Maschere di bit a 32 bit."),
    "LWord": _tipo(64, "Sequenza di bit", "16#0000_0000_0000_0000", "16#FFFF_FFFF_FFFF_FFFF",
                   "16#0000_0000_0000_FFFF", _S7_1500, "Maschere di bit a 64 bit."),
    "SInt": _tipo(8, "Intero con segno", "-128", "127", "-100", _ENTRAMBE, ""),
    "USInt": _tipo(8, "Intero senza segno", "0", "255", "200", _ENTRAMBE, ""),
    "Int": _tipo(16, "Intero con segno", "-32768", "32767", "-1500", _ENTRAMBE,
                 "Tipo tipico per valori analogici già convertiti e per contatori CTU_INT."),
    "UInt": _tipo(16, "Intero senza segno", "0", "65535", "60000", _ENTRAMBE, ""),
    "DInt": _tipo(32, "Intero con segno", "-2147483648", "2147483647", "100000", _ENTRAMBE, ""),
    "UDInt": _tipo(32, "Intero senza segno", "0", "4294967295", "3000000000", _ENTRAMBE, ""),
    "LInt": _tipo(64, "Intero con segno", "-9223372036854775808", "9223372036854775807",
                  "10000000000", _S7_1500, ""),
    "ULInt": _tipo(64, "Intero senza segno", "0", "18446744073709551615", "10000000000",
                   _S7_1500, ""),
    "Real": _tipo(32, "Virgola mobile IEEE 754", "-3.402823e+38", "+3.402823e+38", "3.14, -1.5E+3",
                  _ENTRAMBE,
                  "Circa 7 cifre significative. La costante deve contenere il punto decimale (10.0, non 10)."),
    "LReal": _tipo(64, "Virgola mobile IEEE 754", "-1.7976931348623158e+308",
                   "+1.7976931348623158e+308", "3.141592653589793", _ENTRAMBE,
                   "Circa 15 cifre significative."),
    "Time": _tipo(32, "Durata (ms, con segno)", "T#-24d_20h_31m_23s_648ms", "T#24d_20h_31m_23s_647ms",
                  "T#5s, T#1m_30s, T#250ms", _ENTRAMBE, "Memorizzato come DInt in millisecondi."),
    "LTime": _tipo(64, "Durata (ns, con segno)", "LT#-106751d_23h_47m_16s_854ms_775us_808ns",
                   "LT#106751d_23h_47m_16s_854ms_775us_807ns", "LT#5s", _S7_1500,
                   "Memorizzato come LInt in nanosecondi."),
    "S5Time": _tipo(16, "Durata in formato S5 (base tempi + valore)", "S5T#0ms", "S5T#2h_46m_30s_0ms",
                    "S5T#500ms", _ENTRAMBE,
                    "Formato dei timer S5 (SIMATIC) per compatibilità; la risoluzione dipende dalla base tempi."),
    "Date": _tipo(16, "Data", "D#1990-01-01", "D#2168-12-31", "D#2026-07-09", _ENTRAMBE,
                  "Giorni dal 1° gennaio 1990. Limite massimo da verificare sul manuale della CPU."),
    "Time_Of_Day": _tipo(32, "Ora del giorno (ms)", "TOD#00:00:00.000", "TOD#23:59:59.999",
                         "TOD#08:30:00", _ENTRAMBE, "Abbreviato anche TOD."),
    "DTL": _tipo(96, "Data e ora (struttura di 12 byte)", "DTL#1970-01-01-00:00:00.0",
                 "DTL#2262-04-11-23:47:16.854775807", "DTL#2026-07-09-08:30:00", _ENTRAMBE,
                 "Struttura con anno, mese, giorno, ora, minuti, secondi, nanosecondi."),
    "Char": _tipo(8, "Carattere ASCII", "16#00", "16#FF", "'A'", _ENTRAMBE, ""),
    "WChar": _tipo(16, "Carattere Unicode", "16#0000", "16#FFFF", "WCHAR#'A'", _ENTRAMBE, ""),
    "String": _tipo(2048, "Stringa di caratteri", "0 caratteri", "254 caratteri", "'Pompa 1'", _ENTRAMBE,
                    "Occupa n+2 byte (n = lunghezza massima dichiarata, predefinita 254 → 256 byte). "
                    "Dichiarare es. String[20] per risparmiare memoria."),
    "WString": _tipo(4096, "Stringa Unicode", "0 caratteri", "254 caratteri (predefinito)",
                     "WSTRING#'Pompa 1'", _ENTRAMBE,
                     "Occupa 2×(n+2) byte con n predefinito 254 (dimensione mostrata); la lunghezza massima "
                     "configurabile può essere maggiore."),
}


def lista_tipi_dato():
    return list(_TIPI_DATO_S7.keys())


def info_tipo_dato(nome):
    """Ritorna le caratteristiche del tipo di dato Siemens (case-insensitive)."""
    for chiave, valori in _TIPI_DATO_S7.items():
        if chiave.lower() == str(nome).strip().lower():
            risultato = {"tipo": chiave}
            risultato.update(valori)
            risultato["dimensione_byte"] = valori["dimensione_bit"] // 8 if valori["dimensione_bit"] >= 8 else "1 bit"
            return risultato
    raise ValueError(f"Tipo di dato sconosciuto: '{nome}'.")


# ------------------------------------------------------------------------------
# Valori analogici (moduli SM: rappresentazione a 16 bit)
# ------------------------------------------------------------------------------

_RAW_NOMINALE_MAX = 27648        # fondo scala nominale
_RAW_OVERRANGE_MAX = 32511       # 27649 ... 32511: campo di sovraccarico
_RAW_OVERFLOW_MIN = 32512        # 32512 ... 32767: overflow / errore
_RAW_UNDERFLOW_UNIPOLARE = -4864  # sotto questo valore: underflow (segnali unipolari)
_RAW_UNDERFLOW_BIPOLARE = -32512  # sotto questo valore: underflow (segnali bipolari)
_RAW_4MA = 5530                  # 4 mA (e 1 V nel campo 1-5 V): 27648 * 0.2 = 5529.6

# tipo: (raw_min_nominale, fisico_min, fisico_max, unita, bipolare, live_zero)
_TIPI_SEGNALE = {
    "0-20 mA": (0, 0.0, 20.0, "mA", False, False),
    "4-20 mA": (_RAW_4MA, 4.0, 20.0, "mA", False, True),
    "0-10 V": (0, 0.0, 10.0, "V", False, False),
    "1-5 V": (_RAW_4MA, 1.0, 5.0, "V", False, True),
    "±10 V": (-_RAW_NOMINALE_MAX, -10.0, 10.0, "V", True, False),
    "±5 V": (-_RAW_NOMINALE_MAX, -5.0, 5.0, "V", True, False),
    "±20 mA": (-_RAW_NOMINALE_MAX, -20.0, 20.0, "mA", True, False),
}


def lista_tipi_segnale():
    return list(_TIPI_SEGNALE.keys())


def _dati_segnale(tipo_segnale):
    if tipo_segnale not in _TIPI_SEGNALE:
        raise ValueError(f"Tipo di segnale sconosciuto: '{tipo_segnale}'.")
    raw_min, fis_min, fis_max, unita, bipolare, live_zero = _TIPI_SEGNALE[tipo_segnale]
    return {"raw_min": raw_min, "raw_max": _RAW_NOMINALE_MAX, "fisico_min": fis_min,
            "fisico_max": fis_max, "unita": unita, "bipolare": bipolare, "live_zero": live_zero}


def range_segnale(tipo_segnale):
    """Campo nominale del valore grezzo e limiti di diagnostica per il tipo di segnale."""
    d = _dati_segnale(tipo_segnale)
    limite_underflow = _RAW_UNDERFLOW_BIPOLARE if d["bipolare"] else _RAW_UNDERFLOW_UNIPOLARE
    return {
        "raw_nominale_min": d["raw_min"],
        "raw_nominale_max": d["raw_max"],
        "segnale_min": d["fisico_min"],
        "segnale_max": d["fisico_max"],
        "unita_segnale": d["unita"],
        "raw_overrange_max": _RAW_OVERRANGE_MAX,
        "raw_overflow_da": _RAW_OVERFLOW_MIN,
        "raw_underflow_fino_a": limite_underflow - 1,
    }


def diagnosi_valore_grezzo(raw, tipo_segnale):
    """Classifica il valore grezzo a 16 bit di un ingresso analogico."""
    d = _dati_segnale(tipo_segnale)
    if isinstance(raw, bool) or raw != raw:
        raise ValueError("Il valore grezzo deve essere un numero.")
    raw = int(round(raw))
    if raw < -32768 or raw > 32767:
        raise ValueError("Il valore grezzo di un ingresso analogico è un Int a 16 bit (-32768 ... 32767).")
    limite_underflow = _RAW_UNDERFLOW_BIPOLARE if d["bipolare"] else _RAW_UNDERFLOW_UNIPOLARE

    if raw >= _RAW_OVERFLOW_MIN:
        stato = "overflow"
        nota = ("Overflow: segnale oltre il campo di misura o errore del canale (32767 spesso "
                "indica un guasto). Il valore non è utilizzabile.")
    elif raw > d["raw_max"]:
        stato = "overrange"
        nota = "Sovraccarico: segnale oltre il fondo scala nominale, ma ancora misurabile."
    elif raw >= d["raw_min"]:
        stato = "nominale"
        nota = "Valore nel campo nominale."
    elif raw >= limite_underflow:
        stato = "underrange"
        nota = "Sotto il campo nominale, ancora misurabile."
        if d["live_zero"]:
            nota += " Con uno zero vivo (4-20 mA, 1-5 V) può indicare rottura del filo o sensore guasto."
    else:
        stato = "underflow"
        nota = "Underflow: segnale sotto il campo misurabile o errore del canale. Valore non utilizzabile."
        if d["live_zero"]:
            nota += " Con uno zero vivo (4-20 mA, 1-5 V) è tipico di una rottura del filo."

    return {
        "raw": raw,
        "stato": stato,
        "valido": stato == "nominale",
        "raw_nominale_min": d["raw_min"],
        "raw_nominale_max": d["raw_max"],
        "nota": nota,
    }


def _normalizza(raw, d):
    return (raw - d["raw_min"]) / (d["raw_max"] - d["raw_min"])


def scala_ingresso_analogico(raw, tipo_segnale, eng_min, eng_max, limita=True):
    """Da valore grezzo a valore ingegneristico, come NORM_X + SCALE_X.

    Con limita=True il risultato resta tra eng_min e eng_max (comportamento di
    NORM_X/SCALE_X); con limita=False il valore fuori campo viene estrapolato.
    """
    if eng_max == eng_min:
        raise ValueError("Il valore ingegneristico minimo e massimo devono essere diversi.")
    diagnosi = diagnosi_valore_grezzo(raw, tipo_segnale)
    d = _dati_segnale(tipo_segnale)
    norm_libera = _normalizza(diagnosi["raw"], d)
    norm = min(1.0, max(0.0, norm_libera)) if limita else norm_libera
    return {
        "valore_ingegneristico": eng_min + norm * (eng_max - eng_min),
        "normalizzato": norm,
        "segnale_fisico": d["fisico_min"] + norm_libera * (d["fisico_max"] - d["fisico_min"]),
        "unita_segnale": d["unita"],
        "stato": diagnosi["stato"],
        "valido": diagnosi["valido"],
        "nota": diagnosi["nota"],
    }


def scala_uscita_analogica(valore, tipo_segnale, eng_min, eng_max, limita=True):
    """Da valore ingegneristico (setpoint) al valore grezzo da scrivere su un'uscita analogica."""
    if eng_max == eng_min:
        raise ValueError("Il valore ingegneristico minimo e massimo devono essere diversi.")
    d = _dati_segnale(tipo_segnale)
    norm_libera = (valore - eng_min) / (eng_max - eng_min)
    norm = min(1.0, max(0.0, norm_libera)) if limita else norm_libera
    raw = int(round(d["raw_min"] + norm * (d["raw_max"] - d["raw_min"])))
    return {
        "valore_grezzo": raw,
        "normalizzato": norm,
        "segnale_fisico": d["fisico_min"] + norm * (d["fisico_max"] - d["fisico_min"]),
        "unita_segnale": d["unita"],
        "fuori_campo": norm_libera < 0.0 or norm_libera > 1.0,
        "nel_campo_nominale": d["raw_min"] <= raw <= d["raw_max"],
    }


# ------------------------------------------------------------------------------
# Indirizzi assoluti (%I, %Q, %M)
# ------------------------------------------------------------------------------

_AREE = ("I", "Q", "M")
# tipo -> (suffisso operando, dimensione in byte)
_OPERANDI = {
    "Bool": ("", 0),
    "Byte": ("B", 1),
    "Word": ("W", 2),
    "DWord": ("D", 4),
}
_ALIAS_TIPO = {"int": "Word", "uint": "Word", "dint": "DWord", "udint": "DWord", "real": "DWord",
               "sint": "Byte", "usint": "Byte"}


def _normalizza_area(area):
    a = str(area).strip().lstrip("%").upper()
    if a not in _AREE:
        raise ValueError("Area non valida: usare I (ingressi), Q (uscite) o M (merker).")
    return a


def _normalizza_tipo_operando(tipo):
    t = str(tipo).strip()
    if t.lower() in _ALIAS_TIPO:
        return _ALIAS_TIPO[t.lower()]
    for chiave in _OPERANDI:
        if chiave.lower() == t.lower():
            return chiave
    raise ValueError("Tipo non valido: usare Bool, Byte, Word, DWord (o Int/DInt/Real per la stessa occupazione).")


def _formatta_operando(area, tipo, byte, bit=0):
    suffisso = _OPERANDI[tipo][0]
    if tipo == "Bool":
        return f"%{area}{byte}.{bit}"
    return f"%{area}{suffisso}{byte}"


def operando_assoluto(area, tipo, byte, bit=0):
    """Operando assoluto (es. %MW10) e byte occupati."""
    area = _normalizza_area(area)
    tipo = _normalizza_tipo_operando(tipo)
    byte, bit = int(byte), int(bit)
    if byte < 0:
        raise ValueError("L'indirizzo di byte non può essere negativo.")
    if tipo == "Bool" and not 0 <= bit <= 7:
        raise ValueError("Il numero di bit deve essere compreso tra 0 e 7.")
    dimensione = _OPERANDI[tipo][1] or 1
    return {
        "operando": _formatta_operando(area, tipo, byte, bit),
        "byte_iniziale": byte,
        "byte_finale": byte + dimensione - 1,
        "byte_occupati": dimensione,
        "note": ("Nelle parole/doppie parole il byte con indirizzo più basso contiene i bit più significativi "
                 "(ordine big-endian): %MW10 = %MB10 (alto) + %MB11 (basso).") if dimensione > 1 else "",
    }


def intervallo_memoria_s7(area, tipo, byte_iniziale, quantita, bit_iniziale=0):
    """Primo e ultimo operando di un blocco contiguo di variabili dello stesso tipo."""
    area = _normalizza_area(area)
    tipo = _normalizza_tipo_operando(tipo)
    byte_iniziale, quantita, bit_iniziale = int(byte_iniziale), int(quantita), int(bit_iniziale)
    if byte_iniziale < 0:
        raise ValueError("L'indirizzo di byte non può essere negativo.")
    if quantita < 1:
        raise ValueError("La quantità deve essere almeno 1.")

    if tipo == "Bool":
        if not 0 <= bit_iniziale <= 7:
            raise ValueError("Il numero di bit deve essere compreso tra 0 e 7.")
        indice_ultimo = byte_iniziale * 8 + bit_iniziale + quantita - 1
        byte_ultimo, bit_ultimo = divmod(indice_ultimo, 8)
        return {
            "primo_operando": _formatta_operando(area, tipo, byte_iniziale, bit_iniziale),
            "ultimo_operando": _formatta_operando(area, tipo, byte_ultimo, bit_ultimo),
            "byte_iniziale": byte_iniziale,
            "byte_finale": byte_ultimo,
            "byte_occupati": byte_ultimo - byte_iniziale + 1,
            "prossimo_byte_libero": byte_ultimo + 1,
        }

    dimensione = _OPERANDI[tipo][1]
    byte_ultimo_elemento = byte_iniziale + (quantita - 1) * dimensione
    return {
        "primo_operando": _formatta_operando(area, tipo, byte_iniziale),
        "ultimo_operando": _formatta_operando(area, tipo, byte_ultimo_elemento),
        "byte_iniziale": byte_iniziale,
        "byte_finale": byte_ultimo_elemento + dimensione - 1,
        "byte_occupati": quantita * dimensione,
        "prossimo_byte_libero": byte_ultimo_elemento + dimensione,
    }


# ------------------------------------------------------------------------------
# Generatore di codice SCL
# ------------------------------------------------------------------------------

_RE_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _rif(nome, ruolo):
    """Riferimento SCL a una variabile: 'Raw' -> #Raw; '#Raw' e '"Tag"' restano invariati."""
    s = str(nome).strip() if nome is not None else ""
    if not s:
        raise ValueError(f"Indicare il nome di: {ruolo}.")
    if s.startswith('"') and s.endswith('"') and len(s) > 2 and "\n" not in s and ";" not in s:
        return s
    if s.startswith("#"):
        s = s[1:]
    if not _RE_IDENT.match(s):
        raise ValueError(
            f"Nome non valido per {ruolo}: '{nome}'. Usare lettere, cifre e underscore (es. Pressione_Raw), "
            "oppure il nome di un tag PLC tra virgolette doppie.")
    return "#" + s


def _decl(rif):
    """Nome per la dichiarazione: '#Raw' -> 'Raw'; '"Tag"' non va dichiarato."""
    return rif[1:] if rif.startswith("#") else None


def _lit_real(x):
    x = float(x)
    if x != x or x in (float("inf"), float("-inf")):
        raise ValueError("Valore numerico non valido.")
    s = repr(x)
    if "e" in s:
        mantissa, esponente = s.split("e")
        if "." not in mantissa:
            mantissa += ".0"
        return f"{mantissa}E{esponente}"
    return s


def _par(x):
    """Letterale Real; i negativi tra parentesi per evitare sequenze come '- -5.0'."""
    s = _lit_real(x)
    return f"({s})" if s.startswith("-") else s


def _formatta_time(ms):
    ms = int(ms)
    if ms <= 0:
        raise ValueError("Il tempo deve essere maggiore di zero.")
    if ms > 2147483647:
        raise ValueError("Il tempo supera il massimo del tipo Time (circa 24 giorni).")
    giorni, resto = divmod(ms, 86_400_000)
    ore, resto = divmod(resto, 3_600_000)
    minuti, resto = divmod(resto, 60_000)
    secondi, millisecondi = divmod(resto, 1000)
    parti = []
    for valore, unita in ((giorni, "d"), (ore, "h"), (minuti, "m"), (secondi, "s"), (millisecondi, "ms")):
        if valore:
            parti.append(f"{valore}{unita}")
    return "T#" + "_".join(parti)


def _dichiarazioni(righe):
    righe = [r for r in righe if r]
    return "\n".join(righe)


def genera_scl_scalatura(ingresso, uscita, tipo_segnale, eng_min, eng_max,
                         metodo="norm_scale", tipo_ingresso="Int", diagnostica=True):
    """Codice SCL per scalare un ingresso analogico in unità ingegneristiche."""
    d = _dati_segnale(tipo_segnale)
    if eng_max == eng_min:
        raise ValueError("Il valore ingegneristico minimo e massimo devono essere diversi.")
    if metodo not in ("norm_scale", "formula"):
        raise ValueError("Metodo non valido: usare 'norm_scale' o 'formula'.")
    if tipo_ingresso not in ("Int", "Word"):
        raise ValueError("Tipo ingresso non valido: usare 'Int' o 'Word'.")
    rif_in = _rif(ingresso, "l'ingresso grezzo")
    rif_out = _rif(uscita, "l'uscita scalata")

    raw_min, raw_max = d["raw_min"], d["raw_max"]
    righe = [
        f"// Scalatura ingresso analogico {tipo_segnale}: {raw_min} ... {raw_max} -> "
        f"{_lit_real(eng_min)} ... {_lit_real(eng_max)}",
    ]
    if tipo_ingresso == "Word":
        # NORM_X non accetta Word: si converte una sola volta in un Int locale.
        righe.append(f"#Raw_Int := WORD_TO_INT({rif_in});")
        valore_in = "#Raw_Int"
    else:
        valore_in = rif_in
    if metodo == "norm_scale":
        righe.append("// NORM_X e SCALE_X limitano il risultato tra i due estremi.")
        righe.append(f"#Norm := NORM_X(MIN := {raw_min}, VALUE := {valore_in}, MAX := {raw_max});")
        righe.append(f"{rif_out} := SCALE_X(MIN := {_lit_real(eng_min)}, VALUE := #Norm, MAX := {_lit_real(eng_max)});")
        usa_norm = True
    else:
        righe.append("// Formula lineare: nessun limite, il valore fuori campo viene estrapolato.")
        e_min, e_max = _lit_real(eng_min), _lit_real(eng_max)
        r_min, r_max = _par(raw_min), _par(raw_max)
        righe.append(
            f"{rif_out} := {e_min} + (INT_TO_REAL({valore_in}) - {r_min}) * "
            f"({_par(eng_max)} - {_par(eng_min)}) / ({r_max} - {r_min});")
        usa_norm = False

    decl = ["// Sezione Temp (o Static) del blocco:"]
    if tipo_ingresso == "Word":
        decl.append("Raw_Int : Int;")
    if usa_norm:
        decl.append("Norm : Real;")
    limite_underflow = _RAW_UNDERFLOW_BIPOLARE if d["bipolare"] else _RAW_UNDERFLOW_UNIPOLARE
    if diagnostica:
        righe.append("")
        righe.append("// Diagnostica del valore grezzo (rappresentazione analogica Siemens)")
        righe.append(f"#Diag_Errore := ({valore_in} >= {_RAW_OVERFLOW_MIN}) OR ({valore_in} < {limite_underflow});"
                     "   // overflow / underflow")
        righe.append(f"#Diag_FuoriCampo := ({valore_in} > {raw_max}) OR ({valore_in} < {raw_min});"
                     "   // fuori dal campo nominale")
        decl.append("Diag_Errore : Bool;")
        decl.append("Diag_FuoriCampo : Bool;")
        if d["live_zero"]:
            righe.append(f"#Diag_SottoMinimo := ({valore_in} < {raw_min});"
                         f"   // sotto {d['fisico_min']:g} {d['unita']}: possibile rottura filo")
            decl.append("Diag_SottoMinimo : Bool;")
    decl.append(f"// {rif_in}: {tipo_ingresso}   |   {rif_out}: Real")

    note = [
        "NORM_X e SCALE_X vanno chiamate in un blocco (OB/FC/FB); i tag #locali vanno dichiarati "
        "nell'interfaccia del blocco.",
        "Il valore grezzo degli ingressi periferici (%IW) è di tipo Word: se l'ingresso è Word il codice "
        "lo converte una volta sola in #Raw_Int con WORD_TO_INT.",
        "Verificare nel modulo il campo di misura configurato e l'eventuale diagnostica rottura filo abilitata.",
    ]
    return {"dichiarazioni": _dichiarazioni(decl), "codice": "\n".join(righe), "note": note}


_TIMER_TIPI = {"TON": "TON_TIME", "TOF": "TOF_TIME", "TP": "TP_TIME", "TONR": "TONR_TIME"}


def genera_scl_timer(tipo, istanza, ingresso, tempo_ms, reset=None, uscita_q=None, uscita_et=None):
    """Chiamata SCL di un timer IEC (TON, TOF, TP, TONR)."""
    tipo = str(tipo).strip().upper()
    if tipo not in _TIMER_TIPI:
        raise ValueError("Tipo di timer non valido: usare TON, TOF, TP o TONR.")
    rif_ist = _rif(istanza, "l'istanza del timer")
    rif_in = _rif(ingresso, "l'ingresso IN")
    pt = _formatta_time(tempo_ms)

    if tipo == "TONR":
        rif_reset = _rif(reset, "il reset (R) del TONR")
        chiamata = f"{rif_ist}(IN := {rif_in}, R := {rif_reset}, PT := {pt});"
    else:
        chiamata = f"{rif_ist}(IN := {rif_in}, PT := {pt});"

    righe = [f"// Timer {tipo}: tempo preimpostato {pt}", chiamata]
    decl = ["// Sezione Static del blocco (un FB), oppure usare un DB di istanza:",
            f"{_decl(rif_ist)} : {_TIMER_TIPI[tipo]};"]
    if uscita_q:
        righe.append(f"{_rif(uscita_q, 'l\'uscita Q')} := {rif_ist}.Q;")
    if uscita_et:
        righe.append(f"{_rif(uscita_et, 'l\'uscita ET')} := {rif_ist}.ET;")
    note = [
        "Il timer va richiamato a ogni ciclo, fuori da IF/CASE condizionali: se la chiamata viene saltata "
        "il tempo non avanza.",
    ]
    if tipo == "TON":
        note.append("TON: Q passa a 1 dopo PT che IN è rimasto a 1; ET conta da 0 a PT.")
    elif tipo == "TOF":
        note.append("TOF: Q sale subito con IN e scende dopo PT dalla caduta di IN.")
    elif tipo == "TP":
        note.append("TP: impulso di durata PT sul fronte di salita di IN, indipendente da IN durante l'impulso.")
    else:
        note.append("TONR: accumula il tempo tra un'attivazione e l'altra finché R non lo azzera.")
    return {"dichiarazioni": _dichiarazioni(decl), "codice": "\n".join(righe), "note": note}


_CONTATORI_TIPI = {"CTU": "CTU_INT", "CTD": "CTD_INT", "CTUD": "CTUD_INT"}


def genera_scl_contatore(tipo, istanza, preset, ingresso_su=None, ingresso_giu=None,
                         reset=None, carica=None, uscita_q=None, uscita_valore=None):
    """Chiamata SCL di un contatore IEC (CTU, CTD, CTUD) a 16 bit (Int)."""
    tipo = str(tipo).strip().upper()
    if tipo not in _CONTATORI_TIPI:
        raise ValueError("Tipo di contatore non valido: usare CTU, CTD o CTUD.")
    preset = int(preset)
    if preset < 0 or preset > 32767:
        raise ValueError("Il valore di preset di un contatore Int deve essere compreso tra 0 e 32767.")
    rif_ist = _rif(istanza, "l'istanza del contatore")

    if tipo == "CTU":
        argomenti = ["CU := " + _rif(ingresso_su, "l'ingresso di conteggio (CU)"),
                     "R := " + _rif(reset, "il reset (R)"), f"PV := {preset}"]
        nome_q = "Q"
    elif tipo == "CTD":
        argomenti = ["CD := " + _rif(ingresso_giu, "l'ingresso di conteggio (CD)"),
                     "LD := " + _rif(carica, "il caricamento (LD)"), f"PV := {preset}"]
        nome_q = "Q"
    else:
        argomenti = ["CU := " + _rif(ingresso_su, "l'ingresso di conteggio in avanti (CU)"),
                     "CD := " + _rif(ingresso_giu, "l'ingresso di conteggio indietro (CD)"),
                     "R := " + _rif(reset, "il reset (R)"),
                     "LD := " + _rif(carica, "il caricamento (LD)"), f"PV := {preset}"]
        nome_q = "QU"

    righe = [f"// Contatore {tipo} (Int): preset {preset}", f"{rif_ist}({', '.join(argomenti)});"]
    if uscita_q:
        righe.append(f"{_rif(uscita_q, 'l\'uscita Q')} := {rif_ist}.{nome_q};")
    if uscita_valore:
        righe.append(f"{_rif(uscita_valore, 'l\'uscita del valore')} := {rif_ist}.CV;")
    decl = ["// Sezione Static del blocco (un FB), oppure usare un DB di istanza:",
            f"{_decl(rif_ist)} : {_CONTATORI_TIPI[tipo]};"]
    note = [
        "I contatori contano sul fronte di salita degli ingressi e vanno richiamati a ogni ciclo.",
        "Per contare oltre 32767 usare le varianti a 32 bit (es. CTU_DINT).",
    ]
    if tipo == "CTUD":
        note.append("CTUD: QU = 1 quando CV >= PV; QD = 1 quando CV <= 0.")
    return {"dichiarazioni": _dichiarazioni(decl), "codice": "\n".join(righe), "note": note}


def genera_scl_allarme(valore, soglia, isteresi, tipo="massima", ritardo_ms=0, allarme="Allarme"):
    """Allarme di massima/minima con isteresi ed eventuale ritardo di intervento."""
    if tipo not in ("massima", "minima"):
        raise ValueError("Tipo di allarme non valido: usare 'massima' o 'minima'.")
    if isteresi < 0:
        raise ValueError("L'isteresi non può essere negativa.")
    rif_val = _rif(valore, "il valore misurato")
    rif_all = _rif(allarme, "l'uscita di allarme")
    ritardo_ms = int(ritardo_ms)

    if tipo == "massima":
        cond_set = f"{rif_val} >= {_lit_real(soglia)}"
        cond_reset = f"{rif_val} <= {_lit_real(soglia - isteresi)}"
        titolo = f"Allarme di massima: scatta a {_lit_real(soglia)}, rientra a {_lit_real(soglia - isteresi)}"
    else:
        cond_set = f"{rif_val} <= {_lit_real(soglia)}"
        cond_reset = f"{rif_val} >= {_lit_real(soglia + isteresi)}"
        titolo = f"Allarme di minima: scatta a {_lit_real(soglia)}, rientra a {_lit_real(soglia + isteresi)}"

    decl = ["// Sezione Static del blocco (la condizione deve mantenere lo stato tra i cicli):"]
    righe = [f"// {titolo}"]
    if ritardo_ms > 0:
        righe += [
            f"IF {cond_set} THEN",
            "    #Condizione := TRUE;",
            f"ELSIF {cond_reset} THEN",
            "    #Condizione := FALSE;",
            "END_IF;",
            f"#TempoIntervento(IN := #Condizione, PT := {_formatta_time(ritardo_ms)});",
            f"{rif_all} := #TempoIntervento.Q;",
        ]
        decl += ["Condizione : Bool;", "TempoIntervento : TON_TIME;"]
    else:
        righe += [
            f"IF {cond_set} THEN",
            f"    {rif_all} := TRUE;",
            f"ELSIF {cond_reset} THEN",
            f"    {rif_all} := FALSE;",
            "END_IF;",
        ]
        decl.append(f"// {rif_all} deve essere una variabile Static o un tag che mantiene il valore")
    note = [
        "L'isteresi evita che l'allarme commuti in continuazione quando il valore oscilla attorno alla soglia.",
        "Tra soglia di intervento e soglia di rientro l'allarme mantiene lo stato precedente.",
    ]
    return {"dichiarazioni": _dichiarazioni(decl), "codice": "\n".join(righe), "note": note}


# ------------------------------------------------------------------------------
# Guida ai concetti di base
# ------------------------------------------------------------------------------

_GUIDA = {
    "Indirizzamento (%I, %Q, %M, DB)": {
        "testo": (
            "Un operando assoluto è formato da area, dimensione e indirizzo di byte. "
            "Le aree principali sono %I (ingressi), %Q (uscite) e %M (merker, memoria interna)."),
        "punti": [
            "Bit: %M10.3 (byte 10, bit 3). Byte: %MB10. Word (16 bit): %MW10. DWord (32 bit): %MD10.",
            "Ordine big-endian: %MW10 occupa %MB10 (byte alto) e %MB11 (byte basso). %MW10 e %MW11 si sovrappongono "
            "in %MB11: la parola successiva a %MW10 è %MW12.",
            "Ingresso con lettura diretta dalla periferia: %I0.0:P (bypassa l'immagine di processo aggiornata a inizio ciclo).",
            "Le uscite con :P (%Q0.0:P) scrivono subito sul modulo, oltre che nell'immagine di processo.",
            "Con la lingua italiana di TIA Portal si possono trovare le sigle tedesche E (ingressi) e A (uscite) al posto di I e Q.",
            "Nei blocchi dati l'accesso è simbolico: \"DB_Impianto\".Pompa1.Marcia.",
        ],
    },
    "Blocchi di programma (OB, FC, FB, DB)": {
        "testo": (
            "Il programma S7 è organizzato in blocchi richiamati dal sistema operativo o da altri blocchi."),
        "punti": [
            "OB (Organization Block): punto di ingresso chiamato dal sistema. OB1 = ciclo principale, "
            "OB100 = avviamento (una volta a ogni passaggio in RUN), OB30-OB38 = interrupt ciclici.",
            "FC (Function): codice senza memoria propria; i valori non persistono tra un richiamo e l'altro.",
            "FB (Function Block): codice con memoria; ogni chiamata usa un DB di istanza (o una multi-istanza "
            "dentro un altro FB) che conserva le variabili Static.",
            "DB (Data Block): dati globali, con accesso standard oppure ottimizzato.",
            "Sezioni dell'interfaccia: Input, Output, InOut, Static (solo FB), Temp (perse a ogni richiamo), Constant.",
        ],
    },
    "Timer e contatori IEC": {
        "testo": (
            "Timer e contatori IEC sono blocchi funzione con memoria: vanno istanziati e richiamati a ogni ciclo."),
        "punti": [
            "Timer: TON (ritardo all'inserzione), TOF (ritardo al rilascio), TP (impulso), TONR (accumulo). "
            "Ingressi IN e PT (tipo Time); uscite Q ed ET (tempo trascorso).",
            "In SCL: #Ritardo(IN := #Start, PT := T#5s); #Fatto := #Ritardo.Q; dichiarando Ritardo : TON_TIME.",
            "Contatori: CTU (avanti), CTD (indietro), CTUD (avanti e indietro), disponibili in varianti per tipo "
            "(CTU_INT, CTU_DINT...). Contano sul fronte di salita.",
            "Il valore Time è memorizzato in millisecondi con segno a 32 bit: massimo circa 24 giorni.",
            "Non richiamare un timer dentro un IF: se la chiamata viene saltata il tempo si ferma.",
        ],
    },
    "Tipi di dato e conversioni": {
        "testo": (
            "In SCL il tipo di ogni operando conta: operazioni tra tipi diversi richiedono spesso una conversione."),
        "punti": [
            "Conversioni esplicite: INT_TO_REAL(x), DINT_TO_REAL(x), REAL_TO_INT(x), WORD_TO_INT(x), TRUNC(x), ROUND(x).",
            "Le conversioni implicite dipendono da famiglia di CPU e versione di TIA Portal: quelle esplicite sono "
            "la scelta più sicura.",
            "Gli ingressi analogici periferici sono di tipo Word: convertirli in Int prima di usarli in calcoli.",
            "REAL_TO_INT arrotonda al pari più vicino, TRUNC tronca verso zero: attenzione nei calcoli di scalatura.",
            "Le costanti Real richiedono il punto decimale (10.0): 10 è un Int.",
        ],
    },
    "Valori analogici e scalatura": {
        "testo": (
            "I moduli analogici Siemens restituiscono un valore a 16 bit in cui 27648 corrisponde al fondo scala nominale."),
        "punti": [
            "0-20 mA e 0-10 V: nominale 0 ... 27648. 4-20 mA e 1-5 V: nominale 5530 ... 27648 (4 mA = 5529,6). "
            "Segnali bipolari (±10 V): -27648 ... +27648.",
            "Oltre il fondo scala: overrange fino a 32511, overflow da 32512 a 32767. Sotto lo zero: underrange fino a -4864 "
            "(unipolari), poi underflow.",
            "NORM_X porta il valore grezzo a 0.0 ... 1.0; SCALE_X porta il valore normalizzato al campo ingegneristico. "
            "Entrambe limitano il risultato ai due estremi.",
            "Il limite nasconde i guasti: controllare overflow/underflow e rottura filo prima di usare il valore scalato.",
            "Configurare nel modulo il tipo di misura (corrente/tensione, campo) e la diagnostica di rottura filo.",
        ],
    },
    "SCL — sintassi essenziale": {
        "testo": (
            "SCL (Structured Control Language) è l'implementazione Siemens dello Structured Text IEC 61131-3."),
        "punti": [
            "Assegnazione con :=, istruzioni terminate da ;. Commenti: // fino a fine riga oppure (* ... *).",
            "Variabili locali del blocco precedute da # (#Valore); tag PLC e DB tra virgolette (\"Tag\", \"DB\".Campo).",
            "Costrutti: IF ... THEN ... ELSIF ... ELSE ... END_IF; CASE ... OF ... END_CASE; FOR i := 0 TO 9 DO ... END_FOR; "
            "WHILE ... DO ... END_WHILE.",
            "Chiamata di un FB con istanza: #Timer(IN := #Start, PT := T#5s); uscite con =>: #Timer(..., Q => #Fatto).",
            "REGION ... END_REGION raggruppa il codice e permette di comprimerlo nell'editor.",
            "Operatori logici AND, OR, XOR, NOT; confronti =, <>, <, >, <=, >=.",
        ],
    },
    "Accesso ai DB: standard e ottimizzato": {
        "testo": (
            "I blocchi dati possono essere ottimizzati (predefinito nei progetti nuovi) oppure standard."),
        "punti": [
            "Ottimizzato: le variabili non hanno offset fissi, l'accesso è solo simbolico, la memoria è organizzata dal "
            "sistema. Più robusto alle modifiche e con ritenzione impostabile per singola variabile.",
            "Standard: gli offset sono fissi e visibili, ammette l'accesso assoluto (%DB1.DBW4). Serve per puntatori, "
            "comunicazioni con partner che si aspettano una struttura fissa (es. Modbus, altri PLC).",
            "Cambiare la modalità di accesso a un DB esistente lo reinizializza: ricontrollare valori iniziali e ritenzione.",
        ],
    },
}


def lista_argomenti_guida():
    return list(_GUIDA.keys())


def guida(argomento):
    if argomento not in _GUIDA:
        raise ValueError(f"Argomento sconosciuto: '{argomento}'.")
    voce = _GUIDA[argomento]
    return {"titolo": argomento, "testo": voce["testo"], "punti": list(voce["punti"])}
