# ==============================================================================
# resistenza_materiali.py — Calcoli di resistenza dei materiali (base)
# Riferimenti: EN 1993 (acciaio), EN 1999 (alluminio), Roark's Formulas
# ==============================================================================

import math


# ------------------------------------------------------------------------------
# Database materiali comuni
# ------------------------------------------------------------------------------

_MATERIALI = {
    "Acciaio S235 (EN 10025)":         {"E_mpa": 210_000, "sigma_snerv": 235,  "sigma_rott": 360,  "rho": 7850},
    "Acciaio S275 (EN 10025)":         {"E_mpa": 210_000, "sigma_snerv": 275,  "sigma_rott": 430,  "rho": 7850},
    "Acciaio S355 (EN 10025)":         {"E_mpa": 210_000, "sigma_snerv": 355,  "sigma_rott": 510,  "rho": 7850},
    "Acciaio inox 304 (AISI)":         {"E_mpa": 193_000, "sigma_snerv": 205,  "sigma_rott": 515,  "rho": 7900},
    "Acciaio inox 316L (AISI)":        {"E_mpa": 193_000, "sigma_snerv": 170,  "sigma_rott": 485,  "rho": 8000},
    "Alluminio 6061-T6":               {"E_mpa":  69_000, "sigma_snerv": 276,  "sigma_rott": 310,  "rho": 2700},
    "Alluminio 6082-T6":               {"E_mpa":  70_000, "sigma_snerv": 260,  "sigma_rott": 310,  "rho": 2710},
    "Ghisa grigia GJL-250":            {"E_mpa": 110_000, "sigma_snerv": None, "sigma_rott": 250,  "rho": 7150},
    "Rame (ricotto)":                  {"E_mpa": 117_000, "sigma_snerv": 70,   "sigma_rott": 220,  "rho": 8960},
}


def lista_materiali() -> list:
    return list(_MATERIALI.keys())


def info_materiale(nome: str) -> dict:
    return _MATERIALI.get(nome, {})


# ------------------------------------------------------------------------------
# 1. Trazione / Compressione
# ------------------------------------------------------------------------------

def calcola_trazione_compressione(
    F_N: float,
    A_mm2: float,
    E_mpa: float,
    L_mm: float,
    sigma_amm_mpa: float,
) -> dict:
    """
    Analisi di una sezione soggetta a carico assiale.

    Parametri
    ----------
    F_N           : forza assiale [N] (positiva = trazione)
    A_mm2         : area della sezione [mm²]
    E_mpa         : modulo di elasticità [MPa]
    L_mm          : lunghezza del pezzo [mm]
    sigma_amm_mpa : tensione ammissibile [MPa]  (σ_snerv / FS)
    """
    if A_mm2 <= 0:
        raise ValueError("L'area della sezione deve essere > 0 mm².")
    if E_mpa <= 0:
        raise ValueError("Il modulo elastico deve essere > 0 MPa.")
    if L_mm <= 0:
        raise ValueError("La lunghezza deve essere > 0 mm.")
    if sigma_amm_mpa <= 0:
        raise ValueError("La tensione ammissibile deve essere > 0 MPa.")

    sigma = F_N / A_mm2                  # MPa
    eps   = sigma / E_mpa                # adimensionale
    delta = eps * L_mm                   # mm (allungamento/accorciamento)
    CS    = sigma_amm_mpa / abs(sigma) if sigma != 0 else float("inf")
    ok    = abs(sigma) <= sigma_amm_mpa

    return {
        "sigma_mpa":      sigma,
        "epsilon":        eps,
        "delta_mm":       delta,
        "sigma_amm_mpa":  sigma_amm_mpa,
        "CS":             CS,
        "verificata":     ok,
        "tipo":           "Trazione" if F_N >= 0 else "Compressione",
    }


# ------------------------------------------------------------------------------
# 2. Proprietà geometriche delle sezioni trasversali
# ------------------------------------------------------------------------------

def sezione_rettangolare(b_mm: float, h_mm: float) -> dict:
    """Momento d'inerzia e modulo di resistenza di una sezione rettangolare."""
    if b_mm <= 0 or h_mm <= 0:
        raise ValueError("Base e altezza devono essere > 0 mm.")
    A  = b_mm * h_mm
    I  = b_mm * h_mm**3 / 12.0
    W  = b_mm * h_mm**2 / 6.0
    i_g = math.sqrt(I / A)   # raggio di inerzia
    return {"A_mm2": A, "I_mm4": I, "W_mm3": W, "i_mm": i_g, "forma": "rettangolo"}


def sezione_cerchio_pieno(d_mm: float) -> dict:
    """Momento d'inerzia e modulo di resistenza di una sezione circolare piena."""
    if d_mm <= 0:
        raise ValueError("Il diametro deve essere > 0 mm.")
    A  = math.pi * d_mm**2 / 4.0
    I  = math.pi * d_mm**4 / 64.0
    W  = math.pi * d_mm**3 / 32.0
    i_g = d_mm / 4.0
    return {"A_mm2": A, "I_mm4": I, "W_mm3": W, "i_mm": i_g, "forma": "cerchio pieno"}


def sezione_tubo(D_mm: float, d_mm: float) -> dict:
    """Momento d'inerzia di una sezione tubolare cava (D esterno, d interno)."""
    if D_mm <= d_mm:
        raise ValueError("Il diametro esterno deve essere > diametro interno.")
    if d_mm < 0:
        raise ValueError("Il diametro interno non può essere negativo.")
    A  = math.pi * (D_mm**2 - d_mm**2) / 4.0
    I  = math.pi * (D_mm**4 - d_mm**4) / 64.0
    W  = I / (D_mm / 2.0)
    i_g = math.sqrt(I / A)
    return {"A_mm2": A, "I_mm4": I, "W_mm3": W, "i_mm": i_g, "forma": "tubo"}


def sezione_hea_ipn(h_mm: float, b_mm: float, tw_mm: float, tf_mm: float) -> dict:
    """Momento d'inerzia di un profilo a doppio T (HEA/IPE/IPN) — asse forte."""
    if any(v <= 0 for v in (h_mm, b_mm, tw_mm, tf_mm)):
        raise ValueError("Tutte le dimensioni devono essere > 0 mm.")
    if tw_mm >= b_mm or tf_mm >= h_mm / 2.0:
        raise ValueError("Spessori non compatibili con le dimensioni del profilo.")
    hw = h_mm - 2.0 * tf_mm
    A  = 2.0 * b_mm * tf_mm + hw * tw_mm
    I  = (b_mm * h_mm**3 - (b_mm - tw_mm) * hw**3) / 12.0
    W  = I / (h_mm / 2.0)
    i_g = math.sqrt(I / A)
    return {"A_mm2": A, "I_mm4": I, "W_mm3": W, "i_mm": i_g, "forma": "doppio T"}


# ------------------------------------------------------------------------------
# 3. Momento flettente e tensione — travi semplici
# ------------------------------------------------------------------------------

_SCHEMI_TRAVE = {
    "Appoggiata — carico centrale concentrato":       "app_cc",
    "Appoggiata — carico distribuito uniforme":       "app_qu",
    "Appoggiata — carico distribuito + concentrato":  "app_qf",
    "A sbalzo — carico concentrato in punta":         "sba_cc",
    "A sbalzo — carico distribuito uniforme":         "sba_qu",
    "Incastro-appoggio — carico distribuito":         "inc_qu",
}


def calcola_trave(
    schema: str,
    L_mm: float,
    F_N: float = 0.0,
    q_N_mm: float = 0.0,
    I_mm4: float = 1.0,
    W_mm3: float = 1.0,
    E_mpa: float = 210_000,
    sigma_amm_mpa: float = 160.0,
) -> dict:
    """
    Calcola momento flettente massimo, tensione e freccia per schemi di trave comuni.

    Parametri
    ----------
    schema        : chiave dello schema (usa lista_schemi_trave())
    L_mm          : luce libera [mm]
    F_N           : forza concentrata [N]  (se prevista dallo schema)
    q_N_mm        : carico distribuito [N/mm]  (se previsto)
    I_mm4         : momento d'inerzia della sezione [mm⁴]
    W_mm3         : modulo di resistenza [mm³]
    E_mpa         : modulo di elasticità [MPa]
    sigma_amm_mpa : tensione ammissibile [MPa]
    """
    if L_mm <= 0:
        raise ValueError("La lunghezza della trave deve essere > 0 mm.")
    if I_mm4 <= 0 or W_mm3 <= 0:
        raise ValueError("I e W devono essere > 0.")
    if E_mpa <= 0:
        raise ValueError("Il modulo elastico deve essere > 0 MPa.")

    sc = _SCHEMI_TRAVE.get(schema)
    if sc is None:
        raise ValueError(f"Schema non riconosciuto: '{schema}'.")

    if sc == "app_cc":
        M_max = F_N * L_mm / 4.0
        f_max = F_N * L_mm**3 / (48.0 * E_mpa * I_mm4)
        R_A = R_B = F_N / 2.0
        descr = "M_max a L/2 = F·L/4"

    elif sc == "app_qu":
        M_max = q_N_mm * L_mm**2 / 8.0
        f_max = 5.0 * q_N_mm * L_mm**4 / (384.0 * E_mpa * I_mm4)
        R_A = R_B = q_N_mm * L_mm / 2.0
        descr = "M_max a L/2 = q·L²/8"

    elif sc == "app_qf":
        M_max = (q_N_mm * L_mm**2 / 8.0) + (F_N * L_mm / 4.0)
        f_max = (5.0 * q_N_mm * L_mm**4 / (384.0 * E_mpa * I_mm4)
                 + F_N * L_mm**3 / (48.0 * E_mpa * I_mm4))
        R_A = R_B = (q_N_mm * L_mm + F_N) / 2.0
        descr = "Sovrapposizione degli effetti: q·L²/8 + F·L/4"

    elif sc == "sba_cc":
        M_max = F_N * L_mm
        f_max = F_N * L_mm**3 / (3.0 * E_mpa * I_mm4)
        R_A   = F_N   # reazione all'incastro
        R_B   = 0.0
        descr = "M_max all'incastro = F·L"

    elif sc == "sba_qu":
        M_max = q_N_mm * L_mm**2 / 2.0
        f_max = q_N_mm * L_mm**4 / (8.0 * E_mpa * I_mm4)
        R_A   = q_N_mm * L_mm
        R_B   = 0.0
        descr = "M_max all'incastro = q·L²/2"

    elif sc == "inc_qu":
        # Trave con un estremo incastrato e uno appoggiato, carico distribuito
        M_max = q_N_mm * L_mm**2 / 8.0   # M all'incastro = q·L²/8
        f_max = q_N_mm * L_mm**4 / (185.0 * E_mpa * I_mm4)  # approssimato
        R_A   = 5.0 / 8.0 * q_N_mm * L_mm   # incastro
        R_B   = 3.0 / 8.0 * q_N_mm * L_mm   # appoggio
        descr = "M_max all'incastro = q·L²/8 (incastro-appoggio)"

    else:
        raise ValueError("Schema non implementato.")

    sigma_max = M_max / W_mm3
    CS        = sigma_amm_mpa / sigma_max if sigma_max > 0 else float("inf")
    verificata = sigma_max <= sigma_amm_mpa

    return {
        "M_max_Nmm":     M_max,
        "M_max_Nm":      M_max / 1000.0,
        "sigma_max_mpa": sigma_max,
        "f_max_mm":      f_max,
        "CS":            CS,
        "verificata":    verificata,
        "sigma_amm":     sigma_amm_mpa,
        "R_A_N":         R_A,
        "R_B_N":         R_B,
        "descrizione":   descr,
    }


def lista_schemi_trave() -> list:
    return list(_SCHEMI_TRAVE.keys())


# ------------------------------------------------------------------------------
# 4. Verifica a flessione con sezione nota
# ------------------------------------------------------------------------------

def verifica_flessione(
    M_max_nm: float,
    W_mm3: float,
    sigma_amm_mpa: float,
) -> dict:
    """
    Verifica a flessione: data la sezione, controlla se regge il momento.

    Parametri
    ----------
    M_max_nm      : momento flettente massimo [N·m]
    W_mm3         : modulo di resistenza a flessione [mm³]
    sigma_amm_mpa : tensione ammissibile [MPa]
    """
    if W_mm3 <= 0:
        raise ValueError("Il modulo di resistenza deve essere > 0 mm³.")
    if sigma_amm_mpa <= 0:
        raise ValueError("La tensione ammissibile deve essere > 0 MPa.")

    M_nmm     = M_max_nm * 1000.0
    sigma_max = M_nmm / W_mm3
    CS        = sigma_amm_mpa / sigma_max if sigma_max > 0 else float("inf")

    # W minimo richiesto per stare nella norma
    W_min = M_nmm / sigma_amm_mpa

    return {
        "sigma_max_mpa": sigma_max,
        "CS":            CS,
        "verificata":    sigma_max <= sigma_amm_mpa,
        "W_min_mm3":     W_min,
        "sigma_amm_mpa": sigma_amm_mpa,
    }
