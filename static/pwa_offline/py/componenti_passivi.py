# ==============================================================================
# componenti_passivi.py — Resistori, condensatori, induttori: codice colori,
# combinazioni serie/parallelo, serie di valori normalizzati (IEC 60063).
# ==============================================================================
#
# Resistori: codice colori a 4 e 5 bande (EIA-RS-279 / IEC 60062).
# Combinazioni: resistori e induttori si comportano allo stesso modo (somma in
# serie, inversa della somma degli inversi in parallelo); i condensatori si
# comportano al contrario (inversa della somma degli inversi in serie, somma
# in parallelo) — da qui il termine "componenti analoghi" della richiesta.
# ==============================================================================

import math

# ------------------------------------------------------------------------------
# Codice colori resistori (EIA-RS-279 / IEC 60062)
# ------------------------------------------------------------------------------

# colore: (cifra, moltiplicatore, tolleranza_pct_o_None)
COLORI_RESISTORE = {
    "Nero":    (0, 1,        None),
    "Marrone": (1, 10,       1.0),
    "Rosso":   (2, 100,      2.0),
    "Arancione": (3, 1_000,  None),
    "Giallo":  (4, 10_000,   None),
    "Verde":   (5, 100_000,  0.5),
    "Blu":     (6, 1_000_000, 0.25),
    "Viola":   (7, 10_000_000, 0.1),
    "Grigio":  (8, 100_000_000, 0.05),
    "Bianco":  (9, 1_000_000_000, None),
    "Oro":     (None, 0.1,   5.0),
    "Argento": (None, 0.01,  10.0),
}
TOLLERANZA_NESSUNA_BANDA_PCT = 20.0

# Coefficiente di temperatura (ppm/°C) — sesta banda dei resistori di precisione
# (IEC 60062). Indica quanto varia la resistenza per grado di temperatura.
COLORI_COEFF_TEMPERATURA = {
    "Nero": 250, "Marrone": 100, "Rosso": 50, "Arancione": 15,
    "Giallo": 25, "Verde": 20, "Blu": 10, "Viola": 5, "Grigio": 1,
}

# Colori validi come cifra (esclude Oro/Argento, usabili solo come moltiplicatore/tolleranza)
_COLORI_CIFRA = [c for c, v in COLORI_RESISTORE.items() if v[0] is not None]
# Colori validi come banda di tolleranza
_COLORI_TOLLERANZA = [c for c, v in COLORI_RESISTORE.items() if v[2] is not None]


def lista_colori_resistore() -> list:
    return list(COLORI_RESISTORE.keys())


def lista_colori_coeff_temperatura() -> list:
    return list(COLORI_COEFF_TEMPERATURA.keys())


def _struttura_bande(n_bande: int) -> tuple:
    """Restituisce (n_cifre, ha_tolleranza, ha_coeff_temp) per il numero di bande dato.

    3 bande: cifra, cifra, moltiplicatore                              (tolleranza implicita ±20%)
    4 bande: cifra, cifra, moltiplicatore, tolleranza
    5 bande: cifra, cifra, cifra, moltiplicatore, tolleranza
    6 bande: cifra, cifra, cifra, moltiplicatore, tolleranza, coeff. temperatura
    """
    if n_bande == 3:
        return 2, False, False
    if n_bande == 4:
        return 2, True, False
    if n_bande == 5:
        return 3, True, False
    if n_bande == 6:
        return 3, True, True
    raise ValueError("Il numero di bande deve essere 3, 4, 5 o 6.")


def decodifica_colori_resistore(colori: list) -> dict:
    """Decodifica una resistenza a 3, 4, 5 o 6 bande colore in valore ohmico.

    colori : lista di nomi di colore, es. ["Marrone", "Nero", "Rosso", "Oro"]
             3 bande: cifra, cifra, moltiplicatore (tolleranza implicita ±20%)
             4 bande: cifra, cifra, moltiplicatore, tolleranza
             5 bande: cifra, cifra, cifra, moltiplicatore, tolleranza
             6 bande: cifra, cifra, cifra, moltiplicatore, tolleranza, coeff. temperatura
    """
    n_cifre, ha_tolleranza, ha_coeff_temp = _struttura_bande(len(colori))
    for c in colori[:-1] if ha_coeff_temp else colori:
        if c not in COLORI_RESISTORE:
            raise ValueError(f"Colore non riconosciuto: '{c}'.")

    cifre_colori = colori[:n_cifre]
    moltiplicatore_colore = colori[n_cifre]

    cifre = []
    for c in cifre_colori:
        cifra = COLORI_RESISTORE[c][0]
        if cifra is None:
            raise ValueError(f"'{c}' non è un colore valido per una banda di cifra.")
        cifre.append(str(cifra))
    valore_base = int("".join(cifre))

    moltiplicatore = COLORI_RESISTORE[moltiplicatore_colore][1]
    valore_ohm = valore_base * moltiplicatore

    if ha_tolleranza:
        tolleranza_colore = colori[n_cifre + 1]
        tolleranza_pct = COLORI_RESISTORE[tolleranza_colore][2]
        if tolleranza_pct is None:
            raise ValueError(f"'{tolleranza_colore}' non è un colore valido per la banda di tolleranza.")
    else:
        tolleranza_pct = TOLLERANZA_NESSUNA_BANDA_PCT

    risultato = {
        "valore_ohm": valore_ohm,
        "tolleranza_pct": tolleranza_pct,
        "valore_min_ohm": valore_ohm * (1 - tolleranza_pct / 100.0),
        "valore_max_ohm": valore_ohm * (1 + tolleranza_pct / 100.0),
        "n_bande": len(colori),
    }

    if ha_coeff_temp:
        coeff_colore = colori[-1]
        if coeff_colore not in COLORI_COEFF_TEMPERATURA:
            raise ValueError(f"'{coeff_colore}' non è un colore valido per il coefficiente di temperatura.")
        risultato["coeff_temperatura_ppm_C"] = COLORI_COEFF_TEMPERATURA[coeff_colore]

    return risultato


def colori_da_resistenza(valore_ohm: float, n_bande: int = 4, tolleranza_pct: float = 5.0,
                          coeff_temp_ppm_C: float = None) -> dict:
    """Determina le bande colore per un valore di resistenza dato (operazione
    inversa di decodifica_colori_resistore).

    n_bande          : 3, 4, 5 o 6
    tolleranza_pct   : tolleranza desiderata (ignorata per n_bande=3, dove è implicita ±20%;
                       deve corrispondere a un colore disponibile: 1, 2, 0.5, 0.25, 0.1, 0.05, 5 o 10%)
    coeff_temp_ppm_C : richiesto solo per n_bande=6 (1, 5, 10, 15, 20, 25, 50, 100 o 250 ppm/°C)
    """
    if valore_ohm <= 0:
        raise ValueError("Il valore della resistenza deve essere maggiore di zero.")
    n_cifre, ha_tolleranza, ha_coeff_temp = _struttura_bande(n_bande)

    colore_tolleranza = None
    if ha_tolleranza:
        for c in _COLORI_TOLLERANZA:
            if COLORI_RESISTORE[c][2] == tolleranza_pct:
                colore_tolleranza = c
                break
        if colore_tolleranza is None:
            raise ValueError(
                f"Tolleranza {tolleranza_pct}% non associata a nessun colore standard "
                f"({sorted(set(COLORI_RESISTORE[c][2] for c in _COLORI_TOLLERANZA))})."
            )

    colore_coeff_temp = None
    if ha_coeff_temp:
        if coeff_temp_ppm_C is None:
            raise ValueError("Specificare il coefficiente di temperatura per una resistenza a 6 bande.")
        for c, v in COLORI_COEFF_TEMPERATURA.items():
            if v == coeff_temp_ppm_C:
                colore_coeff_temp = c
                break
        if colore_coeff_temp is None:
            raise ValueError(
                f"Coefficiente {coeff_temp_ppm_C} ppm/°C non associato a nessun colore standard "
                f"({sorted(set(COLORI_COEFF_TEMPERATURA.values()))})."
            )

    # Porta il valore a n_cifre cifre significative ed estrae l'esponente del moltiplicatore
    esponente = math.floor(math.log10(valore_ohm)) - (n_cifre - 1)
    valore_base = round(valore_ohm / (10 ** esponente))
    # Eventuale arrotondamento che porta a n_cifre+1 cifre (es. 999 -> 1000)
    if valore_base >= 10 ** n_cifre:
        valore_base //= 10
        esponente += 1

    cifre_colori = []
    for cifra_str in str(valore_base).zfill(n_cifre):
        cifra = int(cifra_str)
        colore = next(c for c, v in COLORI_RESISTORE.items() if v[0] == cifra)
        cifre_colori.append(colore)

    moltiplicatore_target = 10 ** esponente
    colore_moltiplicatore = None
    for c, v in COLORI_RESISTORE.items():
        if v[1] == moltiplicatore_target:
            colore_moltiplicatore = c
            break
    if colore_moltiplicatore is None:
        raise ValueError(f"Valore {valore_ohm} Ω fuori dal campo rappresentabile con {n_bande} bande.")

    valore_arrotondato = valore_base * moltiplicatore_target
    colori = cifre_colori + [colore_moltiplicatore]
    tolleranza_effettiva = TOLLERANZA_NESSUNA_BANDA_PCT
    if ha_tolleranza:
        colori.append(colore_tolleranza)
        tolleranza_effettiva = tolleranza_pct
    if ha_coeff_temp:
        colori.append(colore_coeff_temp)

    return {
        "colori": colori,
        "valore_arrotondato_ohm": valore_arrotondato,
        "tolleranza_pct": tolleranza_effettiva,
    }


# ------------------------------------------------------------------------------
# Serie di valori normalizzati (IEC 60063) — E6/E12/E24/E48/E96
# ------------------------------------------------------------------------------

SERIE_E = {
    "E6":  [1.0, 1.5, 2.2, 3.3, 4.7, 6.8],
    "E12": [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2],
    "E24": [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0,
            3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1],
    "E48": [1.00, 1.05, 1.10, 1.15, 1.21, 1.27, 1.33, 1.40, 1.47, 1.54, 1.62, 1.69,
            1.78, 1.87, 1.96, 2.05, 2.15, 2.26, 2.37, 2.49, 2.61, 2.74, 2.87, 3.01,
            3.16, 3.32, 3.48, 3.65, 3.83, 4.02, 4.22, 4.42, 4.64, 4.87, 5.11, 5.36,
            5.62, 5.90, 6.19, 6.49, 6.81, 7.15, 7.50, 7.87, 8.25, 8.66, 9.09, 9.53],
    "E96": [1.00, 1.02, 1.05, 1.07, 1.10, 1.13, 1.15, 1.18, 1.21, 1.24, 1.27, 1.30,
            1.33, 1.37, 1.40, 1.43, 1.47, 1.50, 1.54, 1.58, 1.62, 1.65, 1.69, 1.74,
            1.78, 1.82, 1.87, 1.91, 1.96, 2.00, 2.05, 2.10, 2.15, 2.21, 2.26, 2.32,
            2.37, 2.43, 2.49, 2.55, 2.61, 2.67, 2.74, 2.80, 2.87, 2.94, 3.01, 3.09,
            3.16, 3.24, 3.32, 3.40, 3.48, 3.57, 3.65, 3.74, 3.83, 3.92, 4.02, 4.12,
            4.22, 4.32, 4.42, 4.53, 4.64, 4.75, 4.87, 4.99, 5.11, 5.23, 5.36, 5.49,
            5.62, 5.76, 5.90, 6.04, 6.19, 6.34, 6.49, 6.65, 6.81, 6.98, 7.15, 7.32,
            7.50, 7.68, 7.87, 8.06, 8.25, 8.45, 8.66, 8.87, 9.09, 9.31, 9.53, 9.76],
}
# Tolleranza tipica associata a ciascuna serie (uso commerciale comune)
TOLLERANZA_TIPICA_SERIE_E = {"E6": 20.0, "E12": 10.0, "E24": 5.0, "E48": 2.0, "E96": 1.0}


def lista_serie_e() -> list:
    return list(SERIE_E.keys())


def valore_normalizzato_e(valore: float, serie: str = "E12") -> dict:
    """Trova il valore normalizzato (serie E, IEC 60063) più vicino a un valore
    qualsiasi (resistenza, capacità o induttanza: il metodo è indipendente
    dall'unità, lavora solo sulla mantissa decimale)."""
    if valore <= 0:
        raise ValueError("Il valore deve essere maggiore di zero.")
    if serie not in SERIE_E:
        raise ValueError(f"Serie non riconosciuta: '{serie}'. Disponibili: {list(SERIE_E)}")

    esponente = math.floor(math.log10(valore))
    mantissa = valore / (10 ** esponente)

    candidati = SERIE_E[serie] + [SERIE_E[serie][0] * 10]  # includi il "giro" alla decade successiva
    migliore = min(candidati, key=lambda m: abs(math.log10(m) - math.log10(mantissa)))

    if migliore == SERIE_E[serie][0] * 10:
        valore_normalizzato = SERIE_E[serie][0] * 10 ** (esponente + 1)
    else:
        valore_normalizzato = migliore * 10 ** esponente

    return {
        "valore_originale": valore,
        "valore_normalizzato": valore_normalizzato,
        "serie": serie,
        "tolleranza_tipica_pct": TOLLERANZA_TIPICA_SERIE_E[serie],
        "scostamento_pct": (valore_normalizzato - valore) / valore * 100.0,
    }


# ------------------------------------------------------------------------------
# Combinazioni serie/parallelo — resistori, condensatori, induttori
# ------------------------------------------------------------------------------

def _valida_componenti(valori: list, nome: str):
    if not valori:
        raise ValueError(f"Specificare almeno un {nome}.")
    if any(v <= 0 for v in valori):
        raise ValueError(f"Tutti i valori di {nome} devono essere maggiori di zero.")


def _somma_diretta(valori: list, nome: str) -> float:
    _valida_componenti(valori, nome)
    return sum(valori)


def _somma_armonica(valori: list, nome: str) -> float:
    _valida_componenti(valori, nome)
    return 1.0 / sum(1.0 / v for v in valori)


def resistori_serie(valori_ohm: list) -> dict:
    """Resistenza equivalente di resistori in serie: R_eq = R1 + R2 + ... (vale
    anche per induttori in serie, ideali e non mutuamente accoppiati)."""
    return {"valore_equivalente": _somma_diretta(valori_ohm, "resistore")}


def resistori_parallelo(valori_ohm: list) -> dict:
    """Resistenza equivalente di resistori in parallelo: 1/R_eq = Σ(1/Ri)
    (vale anche per induttori in parallelo)."""
    return {"valore_equivalente": _somma_armonica(valori_ohm, "resistore")}


def induttori_serie(valori_H: list) -> dict:
    """Induttanza equivalente di induttori in serie (ideali, senza mutuo accoppiamento)."""
    return {"valore_equivalente": _somma_diretta(valori_H, "induttore")}


def induttori_parallelo(valori_H: list) -> dict:
    """Induttanza equivalente di induttori in parallelo (ideali)."""
    return {"valore_equivalente": _somma_armonica(valori_H, "induttore")}


def condensatori_serie(valori_F: list) -> dict:
    """Capacità equivalente di condensatori in serie: 1/C_eq = Σ(1/Ci)
    — comportamento opposto rispetto a resistori/induttori."""
    return {"valore_equivalente": _somma_armonica(valori_F, "condensatore")}


def condensatori_parallelo(valori_F: list) -> dict:
    """Capacità equivalente di condensatori in parallelo: C_eq = C1 + C2 + ...
    — comportamento opposto rispetto a resistori/induttori."""
    return {"valore_equivalente": _somma_diretta(valori_F, "condensatore")}


# ------------------------------------------------------------------------------
# LED — resistenza di limitazione
# ------------------------------------------------------------------------------

def resistenza_limitazione_led(v_alimentazione: float, v_forward_led: float, corrente_ma: float) -> dict:
    """Resistenza in serie necessaria per limitare la corrente in un LED.

    R = (Vcc - Vf) / I — la resistenza assorbe la differenza tra la tensione
    di alimentazione e la caduta diretta (forward) del LED.
    """
    if v_alimentazione <= 0:
        raise ValueError("La tensione di alimentazione deve essere maggiore di zero.")
    if v_forward_led <= 0:
        raise ValueError("La tensione forward del LED deve essere maggiore di zero.")
    if corrente_ma <= 0:
        raise ValueError("La corrente deve essere maggiore di zero.")
    if v_forward_led >= v_alimentazione:
        raise ValueError("La tensione di alimentazione deve essere maggiore della tensione forward del LED.")

    corrente_a = corrente_ma / 1000.0
    r_ohm = (v_alimentazione - v_forward_led) / corrente_a
    potenza_w = corrente_a ** 2 * r_ohm

    return {
        "resistenza_ohm": r_ohm,
        "potenza_dissipata_W": potenza_w,
        "potenza_consigliata_W": _potenza_normalizzata_resistore(potenza_w),
    }


def _potenza_normalizzata_resistore(potenza_w: float) -> float:
    """Taglia commerciale di potenza del resistore (W) immediatamente superiore
    al valore calcolato, con margine di sicurezza (buona pratica: doppio della
    potenza dissipata reale)."""
    taglie = [0.125, 0.25, 0.5, 1.0, 2.0, 3.0, 5.0, 10.0]
    richiesta = potenza_w * 2.0
    for t in taglie:
        if t >= richiesta:
            return t
    return taglie[-1]


# ------------------------------------------------------------------------------
# Partitore di tensione resistivo
# ------------------------------------------------------------------------------

def partitore_tensione_vout(v_in: float, r1_ohm: float, r2_ohm: float) -> dict:
    """Tensione di uscita di un partitore resistivo: Vout = Vin * R2/(R1+R2)
    (R2 è la resistenza su cui si preleva l'uscita, verso massa)."""
    if v_in <= 0:
        raise ValueError("La tensione di ingresso deve essere maggiore di zero.")
    if r1_ohm <= 0 or r2_ohm <= 0:
        raise ValueError("R1 e R2 devono essere maggiori di zero.")

    v_out = v_in * r2_ohm / (r1_ohm + r2_ohm)
    corrente_a = v_in / (r1_ohm + r2_ohm)
    return {
        "v_out": v_out,
        "corrente_mA": corrente_a * 1000.0,
        "rapporto": r2_ohm / (r1_ohm + r2_ohm),
    }


def partitore_tensione_r2(v_in: float, v_out: float, r1_ohm: float) -> dict:
    """R2 necessaria per ottenere una Vout desiderata, dato R1 e Vin
    (operazione inversa di partitore_tensione_vout)."""
    if v_in <= 0:
        raise ValueError("La tensione di ingresso deve essere maggiore di zero.")
    if r1_ohm <= 0:
        raise ValueError("R1 deve essere maggiore di zero.")
    if not 0 < v_out < v_in:
        raise ValueError("Vout deve essere compresa tra 0 e Vin (esclusi).")

    r2_ohm = r1_ohm * v_out / (v_in - v_out)
    corrente_a = v_in / (r1_ohm + r2_ohm)
    return {
        "r2_ohm": r2_ohm,
        "corrente_mA": corrente_a * 1000.0,
    }


# ------------------------------------------------------------------------------
# Costante di tempo RC / RL
# ------------------------------------------------------------------------------

def costante_di_tempo(tipo: str, resistenza_ohm: float, c_o_l: float, percentuale_target: float = 63.2) -> dict:
    """Costante di tempo di un circuito RC o RL, e tempo necessario per
    raggiungere una data percentuale del valore finale in carica.

    tipo   : 'RC' (c_o_l è la capacità in Farad) oppure 'RL' (c_o_l è l'induttanza in Henry)
    V(t) = Vfinale*(1 - e^(-t/tau))  — stessa forma per corrente in un RL
    Per raggiungere percentuale_target%: t = -tau * ln(1 - percentuale_target/100)
    """
    if tipo not in ("RC", "RL"):
        raise ValueError("Il tipo deve essere 'RC' oppure 'RL'.")
    if resistenza_ohm <= 0:
        raise ValueError("La resistenza deve essere maggiore di zero.")
    if c_o_l <= 0:
        raise ValueError("Il valore di capacità/induttanza deve essere maggiore di zero.")
    if not 0 < percentuale_target < 100:
        raise ValueError("La percentuale target deve essere compresa tra 0 e 100 (esclusi).")

    tau = resistenza_ohm * c_o_l if tipo == "RC" else c_o_l / resistenza_ohm
    tempo_s = -tau * math.log(1.0 - percentuale_target / 100.0)

    return {
        "tau_s": tau,
        "tempo_target_s": tempo_s,
        "tempo_5tau_s": 5.0 * tau,
        "percentuale_a_5tau": (1.0 - math.exp(-5.0)) * 100.0,
    }


# ------------------------------------------------------------------------------
# Ponte di Wheatstone
# ------------------------------------------------------------------------------

def wheatstone_resistenza_incognita(r1_ohm: float, r2_ohm: float, r3_ohm: float) -> dict:
    """Resistenza incognita Rx di un ponte di Wheatstone in condizione di
    equilibrio (ponte a zero, nessuna corrente nel galvanometro):

    R1 * Rx = R2 * R3  =>  Rx = R2 * R3 / R1

    R1 è il braccio in serie alla resistenza incognita Rx; R2 e R3 sono i
    bracci di rapporto noti.
    """
    if r1_ohm <= 0 or r2_ohm <= 0 or r3_ohm <= 0:
        raise ValueError("R1, R2 e R3 devono essere maggiori di zero.")

    rx_ohm = r2_ohm * r3_ohm / r1_ohm
    return {"rx_ohm": rx_ohm}


# ------------------------------------------------------------------------------
# Convertitore AWG (American Wire Gauge) <-> mm²
# ------------------------------------------------------------------------------

def awg_a_mm2(awg: float) -> dict:
    """Diametro e sezione di un conduttore dato il calibro AWG.

    Formula standard: diametro[mm] = 0.127 * 92^((36-AWG)/39)
    Valida per l'intervallo tipico AWG 0000 (-3) ... AWG 40.
    """
    if awg < -3 or awg > 40:
        raise ValueError("Il calibro AWG deve essere compreso tra -3 (0000) e 40.")

    diametro_mm = 0.127 * 92 ** ((36 - awg) / 39.0)
    area_mm2 = math.pi / 4.0 * diametro_mm ** 2
    return {
        "awg": awg,
        "diametro_mm": diametro_mm,
        "area_mm2": area_mm2,
    }


def mm2_a_awg(area_mm2: float) -> dict:
    """Calibro AWG più vicino a una data sezione in mm² (operazione inversa
    di awg_a_mm2, con arrotondamento all'intero AWG più vicino)."""
    if area_mm2 <= 0:
        raise ValueError("La sezione deve essere maggiore di zero.")

    diametro_mm = math.sqrt(area_mm2 * 4.0 / math.pi)
    awg_esatto = 36 - 39 * math.log(diametro_mm / 0.127) / math.log(92)
    awg_arrotondato = round(awg_esatto)
    awg_arrotondato = max(-3, min(40, awg_arrotondato))

    return {
        "area_mm2": area_mm2,
        "diametro_mm": diametro_mm,
        "awg_esatto": awg_esatto,
        "awg_piu_vicino": awg_arrotondato,
    }


# ------------------------------------------------------------------------------
# Resistori SMD — marcatura standard (3/4 cifre, notazione R) e EIA-96
# ------------------------------------------------------------------------------

_LETTERE_MOLTIPLICATORE_EIA96 = {
    "Z": 0.001, "Y": 0.01, "R": 0.01, "X": 0.1, "S": 0.1,
    "A": 1.0, "B": 10.0, "H": 10.0, "C": 100.0, "D": 1000.0,
    "E": 10000.0, "F": 100000.0,
}


def decodifica_smd_standard(codice: str) -> dict:
    """Decodifica una marcatura SMD standard a 3 o 4 cifre, inclusa la
    notazione con 'R' al posto della virgola per valori sotto 10 Ω (es. '4R7' = 4.7 Ω).

    3 cifre: le prime due sono le cifre significative, la terza il moltiplicatore
             (es. '103' = 10 * 10^3 = 10 000 Ω = 10 kΩ)
    4 cifre: le prime tre sono le cifre significative, la quarta il moltiplicatore
             (es. '1002' = 100 * 10^2 = 10 000 Ω = 10 kΩ)
    """
    codice = codice.strip().upper()
    if not codice:
        raise ValueError("Specificare un codice.")

    if "R" in codice:
        parti = codice.split("R")
        if len(parti) != 2 or not all(p.isdigit() or p == "" for p in parti):
            raise ValueError(f"Codice con notazione R non valido: '{codice}'.")
        intero = parti[0] or "0"
        decimale = parti[1] or "0"
        valore_ohm = float(f"{intero}.{decimale}")
        return {"valore_ohm": valore_ohm, "formato": "notazione R"}

    if not codice.isdigit():
        raise ValueError(f"Codice non valido: '{codice}'. Deve contenere solo cifre (o 'R' per valori < 10 Ω).")
    if len(codice) not in (3, 4):
        raise ValueError("Il codice standard deve avere 3 o 4 cifre (o usare la notazione R).")

    n_cifre_significative = len(codice) - 1
    cifre_significative = int(codice[:n_cifre_significative])
    moltiplicatore_esp = int(codice[n_cifre_significative:])
    valore_ohm = cifre_significative * 10 ** moltiplicatore_esp

    return {"valore_ohm": float(valore_ohm), "formato": f"{len(codice)} cifre"}


def decodifica_smd_eia96(codice: str) -> dict:
    """Decodifica una marcatura SMD in formato EIA-96: due cifre (01-96, indice
    nella serie E96) seguite da una lettera che indica il moltiplicatore.

    Es. '01A' = E96[01]=1.00 * moltiplicatore A(×1) = 1.00 Ω
        '68C' = E96[68]=4.99 * moltiplicatore C(×100) = 499 Ω
    """
    codice = codice.strip().upper()
    if len(codice) != 3:
        raise ValueError("Il codice EIA-96 deve avere esattamente 3 caratteri (2 cifre + 1 lettera).")

    cifre, lettera = codice[:2], codice[2]
    if not cifre.isdigit():
        raise ValueError(f"Le prime due posizioni devono essere cifre: '{cifre}'.")
    indice = int(cifre)
    if not 1 <= indice <= 96:
        raise ValueError("Il codice numerico EIA-96 deve essere compreso tra 01 e 96.")
    if lettera not in _LETTERE_MOLTIPLICATORE_EIA96:
        raise ValueError(f"Lettera moltiplicatore non riconosciuta: '{lettera}'.")

    mantissa = SERIE_E["E96"][indice - 1]
    moltiplicatore = _LETTERE_MOLTIPLICATORE_EIA96[lettera]
    valore_ohm = mantissa * moltiplicatore

    return {"valore_ohm": valore_ohm, "mantissa_e96": mantissa, "moltiplicatore": moltiplicatore}


# ------------------------------------------------------------------------------
# Filtro RC / RL — frequenza di taglio
# ------------------------------------------------------------------------------

def frequenza_taglio_rc_rl(tipo: str, resistenza_ohm: float, c_o_l: float) -> dict:
    """Frequenza di taglio (-3 dB) di un filtro RC o RL del primo ordine.

    tipo   : 'RC' (c_o_l è la capacità in Farad) oppure 'RL' (c_o_l è l'induttanza in Henry)
    fc_RC  = 1 / (2*pi*R*C)
    fc_RL  = R / (2*pi*L)

    La frequenza di taglio è la stessa sia per la configurazione passa-basso
    che passa-alto: cambia solo su quale componente si preleva l'uscita.
    """
    if tipo not in ("RC", "RL"):
        raise ValueError("Il tipo deve essere 'RC' oppure 'RL'.")
    if resistenza_ohm <= 0:
        raise ValueError("La resistenza deve essere maggiore di zero.")
    if c_o_l <= 0:
        raise ValueError("Il valore di capacità/induttanza deve essere maggiore di zero.")

    if tipo == "RC":
        fc_hz = 1.0 / (2.0 * math.pi * resistenza_ohm * c_o_l)
    else:
        fc_hz = resistenza_ohm / (2.0 * math.pi * c_o_l)

    return {
        "fc_Hz": fc_hz,
        "omega_rad_s": 2.0 * math.pi * fc_hz,
    }


# ------------------------------------------------------------------------------
# Amplificatore operazionale — guadagno invertente / non invertente
# ------------------------------------------------------------------------------

def guadagno_op_amp(configurazione: str, r1_ohm: float, r2_ohm: float) -> dict:
    """Guadagno in tensione di un amplificatore operazionale ideale in
    configurazione invertente o non invertente.

    Invertente     : Av = -R2/R1   (R1 in serie all'ingresso, R2 di reazione)
    Non invertente : Av = 1 + R2/R1  (R1 verso massa, R2 di reazione)
    """
    if configurazione not in ("Invertente", "Non invertente"):
        raise ValueError("La configurazione deve essere 'Invertente' oppure 'Non invertente'.")
    if r1_ohm <= 0 or r2_ohm <= 0:
        raise ValueError("R1 e R2 devono essere maggiori di zero.")

    if configurazione == "Invertente":
        guadagno = -r2_ohm / r1_ohm
    else:
        guadagno = 1.0 + r2_ohm / r1_ohm

    return {
        "guadagno": guadagno,
        "guadagno_dB": 20.0 * math.log10(abs(guadagno)),
    }


# ------------------------------------------------------------------------------
# Diodo Zener — regolatore shunt
# ------------------------------------------------------------------------------

def diodo_zener_regolatore(v_alimentazione: float, v_zener: float,
                            r_serie_ohm: float, r_carico_ohm: float) -> dict:
    """Analisi di un regolatore shunt a diodo zener: resistenza serie che
    limita la corrente totale, zener in parallelo al carico che stabilizza
    la tensione di uscita a Vz.

    I_totale = (Vin - Vz) / R_serie
    I_carico = Vz / R_carico
    I_zener  = I_totale - I_carico   (deve essere > 0: se negativo lo zener
               non riesce a regolare, la tensione di uscita scende sotto Vz)
    """
    if v_alimentazione <= 0:
        raise ValueError("La tensione di alimentazione deve essere maggiore di zero.")
    if v_zener <= 0:
        raise ValueError("La tensione di zener deve essere maggiore di zero.")
    if r_serie_ohm <= 0 or r_carico_ohm <= 0:
        raise ValueError("La resistenza serie e quella di carico devono essere maggiori di zero.")
    if v_zener >= v_alimentazione:
        raise ValueError("La tensione di alimentazione deve essere maggiore della tensione di zener.")

    i_totale_a = (v_alimentazione - v_zener) / r_serie_ohm
    i_carico_a = v_zener / r_carico_ohm
    i_zener_a = i_totale_a - i_carico_a
    p_zener_w = v_zener * i_zener_a

    return {
        "i_totale_mA": i_totale_a * 1000.0,
        "i_carico_mA": i_carico_a * 1000.0,
        "i_zener_mA": i_zener_a * 1000.0,
        "p_zener_W": p_zener_w,
        "regolazione_ok": i_zener_a > 0,
    }
