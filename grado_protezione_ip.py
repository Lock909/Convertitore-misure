# ==============================================================================
# grado_protezione_ip.py — Grado di protezione IP / IK (IEC 60529 / IEC 62262)
# ==============================================================================
#
# Decodifica un codice IP (es. "IP65") nelle descrizioni delle due cifre
# caratteristiche e delle eventuali lettere addizionali, e fornisce il
# riferimento del grado IK (resistenza agli urti meccanici).
# ==============================================================================

# Prima cifra caratteristica — protezione contro corpi solidi / accesso parti
IP_PRIMA_CIFRA = {
    "0": ("Nessuna protezione", "Nessuna protezione contro l'ingresso di corpi solidi."),
    "1": ("Corpi ≥ 50 mm", "Protetto contro corpi solidi grandi (es. dorso della mano)."),
    "2": ("Corpi ≥ 12,5 mm", "Protetto contro corpi solidi medi (es. dito)."),
    "3": ("Corpi ≥ 2,5 mm", "Protetto contro utensili e fili spessi (es. cacciavite)."),
    "4": ("Corpi ≥ 1 mm", "Protetto contro fili e corpi sottili (≥ 1 mm)."),
    "5": ("Protetto dalla polvere", "Ingresso di polvere non totalmente impedito ma non in quantità dannosa."),
    "6": ("Totalmente protetto dalla polvere", "Nessun ingresso di polvere (a tenuta di polvere)."),
}

# Seconda cifra caratteristica — protezione contro l'ingresso di acqua
IP_SECONDA_CIFRA = {
    "0": ("Nessuna protezione", "Nessuna protezione contro l'acqua."),
    "1": ("Gocce verticali", "Gocce d'acqua in caduta verticale."),
    "2": ("Gocce inclinate 15°", "Gocce d'acqua con involucro inclinato fino a 15°."),
    "3": ("Pioggia (60°)", "Acqua nebulizzata fino a 60° dalla verticale."),
    "4": ("Spruzzi da ogni direzione", "Spruzzi d'acqua da qualsiasi direzione."),
    "5": ("Getti d'acqua", "Getti d'acqua (ugello 6,3 mm) da ogni direzione."),
    "6": ("Getti potenti", "Getti d'acqua potenti (ugello 12,5 mm), tipo onde di mare."),
    "7": ("Immersione temporanea", "Immersione temporanea fino a 1 m per 30 min."),
    "8": ("Immersione continua", "Immersione continua oltre 1 m (condizioni concordate col costruttore)."),
    "9": ("Getti alta pressione/temperatura", "Getti d'acqua ad alta pressione e temperatura (IPx9 / IPx9K)."),
}

# Lettere addizionali opzionali — protezione delle persone contro l'accesso
IP_LETTERE_ADDIZIONALI = {
    "A": "Protezione contro l'accesso con il dorso della mano",
    "B": "Protezione contro l'accesso con un dito",
    "C": "Protezione contro l'accesso con un utensile (Ø 2,5 mm)",
    "D": "Protezione contro l'accesso con un filo (Ø 1 mm)",
}

# Lettere supplementari opzionali — informazioni specifiche
IP_LETTERE_SUPPLEMENTARI = {
    "H": "Apparecchiatura ad alta tensione",
    "M": "Provato contro gli effetti dell'acqua con parti in moto",
    "S": "Provato contro gli effetti dell'acqua con parti immobili",
    "W": "Adatto a condizioni atmosferiche specificate (weather-protected)",
}

# Codici IK — energia d'urto (IEC 62262), in joule
IK_ENERGIA_JOULE = {
    "IK00": 0.0, "IK01": 0.14, "IK02": 0.20, "IK03": 0.35, "IK04": 0.50,
    "IK05": 0.70, "IK06": 1.0, "IK07": 2.0, "IK08": 5.0, "IK09": 10.0, "IK10": 20.0,
}

# Esempi applicativi comuni (uso → IP consigliato)
IP_ESEMPI_USO = {
    "Quadro elettrico interno (locale asciutto)": "IP4X / IP41",
    "Quadro elettrico ambiente industriale": "IP54 / IP55",
    "Cassetta di derivazione esterna": "IP55 / IP65",
    "Apparecchio illuminazione esterna": "IP65",
    "Componente lavabile con getti (alimentare)": "IP69 / IP69K",
    "Apparecchiatura sommersa": "IP68",
}


def decodifica_ip(codice: str) -> dict:
    """Decodifica un codice IP del tipo 'IP65', 'IP2X', 'IPX7', 'IP65CW'.

    Restituisce le descrizioni delle cifre e delle eventuali lettere.
    'X' indica cifra non specificata.
    """
    raw = codice.strip().upper().replace(" ", "")
    if not raw.startswith("IP"):
        raise ValueError("Il codice deve iniziare con 'IP' (es. IP65).")
    resto = raw[2:]
    if len(resto) < 2:
        raise ValueError("Codice IP incompleto: servono due cifre caratteristiche (es. IP65, IP2X).")

    c1, c2 = resto[0], resto[1]
    lettere = resto[2:]

    if c1 != "X" and c1 not in IP_PRIMA_CIFRA:
        raise ValueError(f"Prima cifra '{c1}' non valida (ammessi 0-6 oppure X).")
    if c2 != "X" and c2 not in IP_SECONDA_CIFRA:
        raise ValueError(f"Seconda cifra '{c2}' non valida (ammessi 0-9 oppure X).")

    desc1 = ("Non specificata", "Cifra sostituita da X: protezione contro i solidi non specificata.") \
        if c1 == "X" else IP_PRIMA_CIFRA[c1]
    desc2 = ("Non specificata", "Cifra sostituita da X: protezione contro i liquidi non specificata.") \
        if c2 == "X" else IP_SECONDA_CIFRA[c2]

    lettere_dec = []
    for L in lettere:
        if L in IP_LETTERE_ADDIZIONALI:
            lettere_dec.append((L, "addizionale", IP_LETTERE_ADDIZIONALI[L]))
        elif L in IP_LETTERE_SUPPLEMENTARI:
            lettere_dec.append((L, "supplementare", IP_LETTERE_SUPPLEMENTARI[L]))
        else:
            raise ValueError(f"Lettera '{L}' non riconosciuta (ammesse A,B,C,D / H,M,S,W).")

    return {
        "codice": raw,
        "prima_cifra": c1,
        "prima_titolo": desc1[0],
        "prima_descrizione": desc1[1],
        "seconda_cifra": c2,
        "seconda_titolo": desc2[0],
        "seconda_descrizione": desc2[1],
        "lettere": lettere_dec,
    }
