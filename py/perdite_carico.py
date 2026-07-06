# ==============================================================================
# perdite_carico.py — Perdite di carico concentrate in tubazioni
# Formula base: ΔP = K · (ρ·v²/2)    h_f = K · v²/(2g)
# Riferimenti: Idel'chik (Handbook of Hydraulic Resistance), EN 1267
# ==============================================================================

import math

_G = 9.80665   # m/s²


# ------------------------------------------------------------------------------
# Coefficienti K per raccordi e valvole più comuni
# ------------------------------------------------------------------------------

_DB_K = {
    # Curve
    "Curva 90° — raggio largo (R/D ≥ 1.5)":   0.30,
    "Curva 90° — raggio stretto (R/D ≈ 1)":    0.75,
    "Curva 90° — gomito a spigolo vivo":         1.30,
    "Curva 45° — raggio largo":                  0.20,
    "Curva 45° — gomito a spigolo":              0.40,
    "Curva 180° (U-bend)":                       1.50,
    # Tee
    "Tee — passante (flusso diretto)":           0.30,
    "Tee — deviato 90°":                         1.30,
    "Tee — confluenza (ramo laterale)":          0.90,
    # Valvole
    "Valvola a globo — completamente aperta":   10.00,
    "Valvola a globo — 50% aperta":             40.00,
    "Valvola a sfera — completamente aperta":    0.05,
    "Valvola a sfera — 50% aperta":              6.40,
    "Valvola a farfalla — completamente aperta": 0.30,
    "Valvola a saracinesca — completamente aperta": 0.15,
    "Valvola di ritegno (clapet)":               2.00,
    "Valvola di sicurezza / sfiato":             6.00,
    # Filtri e misuratori
    "Filtro a Y — completamente pulito":         3.00,
    "Misuratore a diaframma":                    8.00,
    # Ingressi/uscite
    "Entrata a tubo (bordo affilato)":           0.50,
    "Entrata a tubo (bordo raccordato)":         0.04,
    "Uscita da tubo (scarico in serbatoio)":     1.00,
    # Riduzioni/allargamenti
    "Riduzione brusca (A2/A1 = 0.5)":           0.38,
    "Riduzione brusca (A2/A1 = 0.25)":          0.49,
}


def lista_raccordi() -> list:
    return list(_DB_K.keys())


def k_raccordo(nome: str) -> float:
    if nome not in _DB_K:
        raise ValueError(f"Raccordo non trovato: '{nome}'.")
    return _DB_K[nome]


# ------------------------------------------------------------------------------
# Perdita singolo raccordo
# ------------------------------------------------------------------------------

def perdita_raccordo(
    K: float,
    v_ms: float,
    rho_kg_m3: float = 1000.0,
) -> dict:
    """
    Calcola la perdita di carico concentrata per un raccordo/valvola.

    Parametri
    ----------
    K          : coefficiente di resistenza [-]
    v_ms       : velocità media nel condotto [m/s]
    rho_kg_m3  : densità del fluido [kg/m³]
    """
    if K < 0:
        raise ValueError("K non può essere negativo.")
    if v_ms < 0:
        raise ValueError("La velocità non può essere negativa.")
    if rho_kg_m3 <= 0:
        raise ValueError("La densità deve essere > 0 kg/m³.")

    q_din  = 0.5 * rho_kg_m3 * v_ms**2   # pressione dinamica [Pa]
    dP_pa  = K * q_din
    h_f_m  = K * v_ms**2 / (2.0 * _G)

    return {
        "K":         K,
        "dP_Pa":     dP_pa,
        "dP_bar":    dP_pa / 1e5,
        "dP_mbar":   dP_pa / 100.0,
        "h_f_m":     h_f_m,
        "q_din_Pa":  q_din,
    }


# ------------------------------------------------------------------------------
# Lunghezza equivalente di un raccordo
# ------------------------------------------------------------------------------

def lunghezza_equivalente(K: float, D_mm: float, lambda_f: float) -> float:
    """
    Converte K in lunghezza equivalente di tubo retto.
    L_eq = K · D / λ

    Parametri
    ----------
    K        : coefficiente di resistenza
    D_mm     : diametro interno [mm]
    lambda_f : fattore di attrito Darcy-Weisbach [-]
    """
    if lambda_f <= 0:
        raise ValueError("Il fattore di attrito deve essere > 0.")
    if D_mm <= 0:
        raise ValueError("Il diametro deve essere > 0 mm.")
    return K * (D_mm / 1000.0) / lambda_f


# ------------------------------------------------------------------------------
# Perdita totale per lista di raccordi
# ------------------------------------------------------------------------------

def perdita_totale(
    raccordi: list,
    v_ms: float,
    rho_kg_m3: float = 1000.0,
) -> dict:
    """
    Calcola la perdita di carico totale per una lista di raccordi.

    Parametri
    ----------
    raccordi  : lista di dict [{"nome": ..., "n": ...}]  n = quantità
    v_ms      : velocità media nel condotto [m/s]
    rho_kg_m3 : densità fluido [kg/m³]

    Ritorna
    -------
    dict con K_tot, dP_tot, h_f_tot e dettaglio per raccordo
    """
    if v_ms < 0:
        raise ValueError("La velocità non può essere negativa.")

    K_tot    = 0.0
    dettaglio = []

    for item in raccordi:
        nome = item.get("nome", "")
        n    = item.get("n", 1)
        K_s  = _DB_K.get(nome, item.get("K", 0.0))
        K_tot += K_s * n
        dettaglio.append({"nome": nome, "n": n, "K": K_s, "K_parziale": K_s * n})

    r_tot = perdita_raccordo(K_tot, v_ms, rho_kg_m3)
    r_tot["K_tot"]    = K_tot
    r_tot["dettaglio"] = dettaglio
    return r_tot


# ------------------------------------------------------------------------------
# Allargamento / restringimento brusco
# ------------------------------------------------------------------------------

def perdita_allargamento_brusco(
    v1_ms: float,
    D1_mm: float,
    D2_mm: float,
    rho_kg_m3: float = 1000.0,
) -> dict:
    """
    Perdita di Borda-Carnot per allargamento brusco di sezione.
    ΔP = ρ/2 · (v1 - v2)²
    """
    if D1_mm <= 0 or D2_mm <= 0:
        raise ValueError("I diametri devono essere > 0 mm.")
    if D2_mm <= D1_mm:
        raise ValueError("D2 deve essere maggiore di D1 per un allargamento.")
    if v1_ms < 0:
        raise ValueError("La velocità non può essere negativa.")

    A1 = math.pi * D1_mm**2 / 4.0
    A2 = math.pi * D2_mm**2 / 4.0
    v2 = v1_ms * A1 / A2
    K  = (1.0 - A1 / A2)**2

    dP_pa = 0.5 * rho_kg_m3 * (v1_ms - v2)**2
    h_f_m = dP_pa / (rho_kg_m3 * _G)

    return {
        "K_equiv": K,
        "v1_ms":   v1_ms,
        "v2_ms":   v2,
        "A1_mm2":  A1,
        "A2_mm2":  A2,
        "dP_Pa":   dP_pa,
        "dP_mbar": dP_pa / 100.0,
        "h_f_m":   h_f_m,
    }


def perdita_restringimento_brusco(
    v2_ms: float,
    D1_mm: float,
    D2_mm: float,
    rho_kg_m3: float = 1000.0,
) -> dict:
    """
    Perdita per restringimento brusco (formula empirica K ≈ 0.5·(1 - A2/A1)).
    v2_ms è la velocità nella sezione ridotta (uscita).
    """
    if D1_mm <= 0 or D2_mm <= 0:
        raise ValueError("I diametri devono essere > 0 mm.")
    if D1_mm <= D2_mm:
        raise ValueError("D1 deve essere maggiore di D2 per un restringimento.")
    if v2_ms < 0:
        raise ValueError("La velocità non può essere negativa.")

    A2_A1 = (D2_mm / D1_mm)**2
    K     = 0.5 * (1.0 - A2_A1)
    dP_pa = K * 0.5 * rho_kg_m3 * v2_ms**2
    h_f_m = dP_pa / (rho_kg_m3 * _G)

    return {
        "K": K,
        "A2_A1_ratio": A2_A1,
        "v2_ms": v2_ms,
        "dP_Pa": dP_pa,
        "dP_mbar": dP_pa / 100.0,
        "h_f_m": h_f_m,
    }
