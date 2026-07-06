# ==============================================================================
# bulloneria.py — Calcoli bulloneria metrica secondo ISO 898-1 / VDI 2230
# ==============================================================================

import math


# ------------------------------------------------------------------------------
# Database classi di resistenza (ISO 898-1)
# ------------------------------------------------------------------------------

_CLASSI = {
    "4.6":  {"sigma_snerv": 240,  "sigma_rott": 400},
    "5.8":  {"sigma_snerv": 400,  "sigma_rott": 500},
    "6.8":  {"sigma_snerv": 480,  "sigma_rott": 600},
    "8.8":  {"sigma_snerv": 640,  "sigma_rott": 800},
    "10.9": {"sigma_snerv": 900,  "sigma_rott": 1000},
    "12.9": {"sigma_snerv": 1080, "sigma_rott": 1200},
    "A2-70 (inox)": {"sigma_snerv": 450, "sigma_rott": 700},
    "A4-80 (inox)": {"sigma_snerv": 600, "sigma_rott": 800},
}

# Area di sezione resistente As [mm²] per viti metriche ISO 724
_SEZIONI = {
    "M4":  {"d_mm": 4.0,  "As_mm2": 8.78,  "passo_mm": 0.70},
    "M5":  {"d_mm": 5.0,  "As_mm2": 14.2,  "passo_mm": 0.80},
    "M6":  {"d_mm": 6.0,  "As_mm2": 20.1,  "passo_mm": 1.00},
    "M8":  {"d_mm": 8.0,  "As_mm2": 36.6,  "passo_mm": 1.25},
    "M10": {"d_mm": 10.0, "As_mm2": 58.0,  "passo_mm": 1.50},
    "M12": {"d_mm": 12.0, "As_mm2": 84.3,  "passo_mm": 1.75},
    "M14": {"d_mm": 14.0, "As_mm2": 115.0, "passo_mm": 2.00},
    "M16": {"d_mm": 16.0, "As_mm2": 157.0, "passo_mm": 2.00},
    "M20": {"d_mm": 20.0, "As_mm2": 245.0, "passo_mm": 2.50},
    "M24": {"d_mm": 24.0, "As_mm2": 353.0, "passo_mm": 3.00},
    "M27": {"d_mm": 27.0, "As_mm2": 459.0, "passo_mm": 3.00},
    "M30": {"d_mm": 30.0, "As_mm2": 561.0, "passo_mm": 3.50},
    "M36": {"d_mm": 36.0, "As_mm2": 817.0, "passo_mm": 4.00},
    "M42": {"d_mm": 42.0, "As_mm2": 1120.0,"passo_mm": 4.50},
    "M48": {"d_mm": 48.0, "As_mm2": 1470.0,"passo_mm": 5.00},
}

# Fattore k (coppia/diametro/precarico) per diverse condizioni di lubrificazione
_K_LUBRIFICAZIONE = {
    "Secco (non lubrificato)":          0.20,
    "Lubrificato (olio/grasso comune)": 0.15,
    "MoS₂ / lubrificante solido":       0.12,
    "Zincato + lubrificante":           0.18,
    "Cadmiato":                         0.14,
}


def lista_classi() -> list:
    return list(_CLASSI.keys())


def lista_diametri() -> list:
    return list(_SEZIONI.keys())


def lista_lubrificazioni() -> list:
    return list(_K_LUBRIFICAZIONE.keys())


# ------------------------------------------------------------------------------
# Calcolo coppia di serraggio e precarico (VDI 2230 semplificato)
# ------------------------------------------------------------------------------

def calcola_serraggio(
    diametro: str,
    classe: str,
    lubrificazione: str,
    nu_precarico: float = 0.70,
    FS: float = 1.0,
) -> dict:
    """
    Calcola il precarico e la coppia di serraggio secondo VDI 2230 (metodo semplificato).

    Parametri
    ----------
    diametro     : designazione metrica (es. 'M12')
    classe       : classe di resistenza ISO 898-1 (es. '8.8')
    lubrificazione: condizione di contatto dadi-testa
    nu_precarico : percentuale del limite elastico usata per il precarico [-]
                   (tipico 0.70 per serraggio controllato con chiave dinamometrica)
    FS           : fattore di sicurezza aggiuntivo sull'utilizzo del limite elastico

    Ritorna
    -------
    dict con F_p (precarico), M_a (coppia), tensione nel gambo
    """
    if diametro not in _SEZIONI:
        raise ValueError(f"Diametro non trovato: '{diametro}'.")
    if classe not in _CLASSI:
        raise ValueError(f"Classe non trovata: '{classe}'.")
    if lubrificazione not in _K_LUBRIFICAZIONE:
        raise ValueError(f"Condizione di lubrificazione non trovata: '{lubrificazione}'.")
    if not 0 < nu_precarico <= 1:
        raise ValueError("nu_precarico deve essere tra 0 e 1.")
    if FS < 1:
        raise ValueError("Il fattore di sicurezza deve essere ≥ 1.")

    sez  = _SEZIONI[diametro]
    mat  = _CLASSI[classe]
    k    = _K_LUBRIFICAZIONE[lubrificazione]

    As          = sez["As_mm2"]
    d           = sez["d_mm"]
    sigma_snerv = mat["sigma_snerv"]

    # Precarico [N]: F_p = nu · σ_snerv · As / FS
    F_p = nu_precarico * sigma_snerv * As / FS

    # Coppia di serraggio [N·m]: M_a = k · d · F_p  (d in mm → × 1e-3)
    M_a = k * (d / 1000.0) * F_p

    # Tensione nel gambo al precarico
    sigma_gambo = F_p / As

    # Tensione ammissibile a trazione pura
    sigma_amm = sigma_snerv / FS

    return {
        "F_p_N":         F_p,
        "F_p_kN":        F_p / 1000.0,
        "M_a_Nm":        M_a,
        "sigma_gambo":   sigma_gambo,
        "sigma_amm":     sigma_amm,
        "utilizzo_pct":  sigma_gambo / sigma_snerv * 100.0,
        "k":             k,
        "As_mm2":        As,
        "d_mm":          d,
        "sigma_snerv":   sigma_snerv,
        "sigma_rott":    mat["sigma_rott"],
    }


# ------------------------------------------------------------------------------
# Verifica bullone a trazione + taglio
# ------------------------------------------------------------------------------

def verifica_bullone(
    diametro: str,
    classe: str,
    F_trazione_N: float,
    F_taglio_N: float = 0.0,
    FS: float = 1.5,
    n_piani_taglio: int = 1,
) -> dict:
    """
    Verifica un bullone soggetto a trazione assiale e/o taglio trasversale.

    Parametri
    ----------
    diametro      : designazione metrica (es. 'M12')
    classe        : classe di resistenza
    F_trazione_N  : forza di trazione assiale [N]
    F_taglio_N    : forza di taglio trasversale [N]
    FS            : fattore di sicurezza richiesto
    n_piani_taglio: numero di piani di taglio (1 = singolo, 2 = doppio)
    """
    if diametro not in _SEZIONI:
        raise ValueError(f"Diametro non trovato: '{diametro}'.")
    if classe not in _CLASSI:
        raise ValueError(f"Classe non trovata: '{classe}'.")
    if F_trazione_N < 0 or F_taglio_N < 0:
        raise ValueError("Le forze non possono essere negative.")
    if FS < 1:
        raise ValueError("Il fattore di sicurezza deve essere ≥ 1.")

    sez  = _SEZIONI[diametro]
    mat  = _CLASSI[classe]
    As   = sez["As_mm2"]

    sigma_amm = mat["sigma_snerv"] / FS
    tau_amm   = sigma_amm / math.sqrt(3)   # Von Mises

    # Tensione di trazione
    sigma_t = F_trazione_N / As if F_trazione_N > 0 else 0.0

    # Tensione di taglio (su n_piani)
    tau = F_taglio_N / (As * n_piani_taglio) if F_taglio_N > 0 else 0.0

    # Verifica combinata (Von Mises): sigma_eq = sqrt(sigma_t² + 3·tau²)
    sigma_eq = math.sqrt(sigma_t**2 + 3.0 * tau**2)

    CS_trazione = sigma_amm / sigma_t  if sigma_t > 0 else float("inf")
    CS_taglio   = tau_amm   / tau      if tau > 0     else float("inf")
    CS_combined = sigma_amm / sigma_eq if sigma_eq > 0 else float("inf")

    return {
        "sigma_t_mpa":    sigma_t,
        "tau_mpa":        tau,
        "sigma_eq_mpa":   sigma_eq,
        "sigma_amm_mpa":  sigma_amm,
        "tau_amm_mpa":    tau_amm,
        "CS_trazione":    CS_trazione,
        "CS_taglio":      CS_taglio,
        "CS_combined":    CS_combined,
        "verificata":     sigma_eq <= sigma_amm,
        "As_mm2":         As,
        "sigma_snerv":    mat["sigma_snerv"],
    }


# ------------------------------------------------------------------------------
# Dimensionamento: numero minimo di bulloni per flangia
# ------------------------------------------------------------------------------

def dimensiona_flangia(
    F_totale_N: float,
    diametro: str,
    classe: str,
    lubrificazione: str,
    nu_precarico: float = 0.70,
    FS: float = 1.5,
) -> dict:
    """
    Calcola il numero minimo di bulloni per sopportare un carico assiale totale.

    Parametri
    ----------
    F_totale_N : forza assiale totale sulla flangia [N]
    """
    r   = calcola_serraggio(diametro, classe, lubrificazione, nu_precarico, FS)
    F_p = r["F_p_N"]
    n   = math.ceil(F_totale_N / F_p)
    return {
        "n_bulloni":    n,
        "F_per_bullone": F_totale_N / max(n, 1),
        "F_p_bullone":  F_p,
        "M_a_Nm":       r["M_a_Nm"],
        "diametro":     diametro,
        "classe":       classe,
    }
