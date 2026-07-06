# ==============================================================================
# scambiatori.py — Calcoli termici per scambiatori di calore
# Metodi: LMTD (Log Mean Temperature Difference) e NTU-ε
# Riferimenti: EN ISO 15547, VDI Heat Atlas
# ==============================================================================

import math


# ------------------------------------------------------------------------------
# 1. Bilancio termico lato caldo/freddo
# ------------------------------------------------------------------------------

def bilancio_termico(
    m_h: float, cp_h: float, T_h_in: float, T_h_out: float,
    m_c: float = 0.0, cp_c: float = 4186.0,
) -> dict:
    """
    Calcola il calore scambiato e la temperatura d'uscita del fluido freddo.

    Parametri
    ----------
    m_h     : portata massica lato caldo [kg/s]
    cp_h    : calore specifico fluido caldo [J/(kg·K)]
    T_h_in  : temperatura ingresso lato caldo [°C]
    T_h_out : temperatura uscita lato caldo [°C]
    m_c     : portata massica lato freddo [kg/s]  (0 = non calcola T_c_out)
    cp_c    : calore specifico fluido freddo [J/(kg·K)]
    """
    if m_h <= 0:
        raise ValueError("Portata massica lato caldo deve essere > 0 kg/s.")
    if cp_h <= 0 or cp_c <= 0:
        raise ValueError("I calori specifici devono essere > 0 J/(kg·K).")
    if T_h_out >= T_h_in:
        raise ValueError("T_h_out deve essere minore di T_h_in.")

    Q_w    = m_h * cp_h * (T_h_in - T_h_out)   # W
    C_h    = m_h * cp_h

    result = {
        "Q_W":    Q_w,
        "Q_kW":   Q_w / 1000.0,
        "C_h":    C_h,
        "T_h_in": T_h_in,
        "T_h_out":T_h_out,
    }

    if m_c > 0:
        C_c          = m_c * cp_c
        T_c_rise     = Q_w / C_c
        result["C_c"]       = C_c
        result["delta_T_c"] = T_c_rise
        result["T_c_out_if_T_c_in_known"] = "T_c_in + {:.3f}°C".format(T_c_rise)

    return result


# ------------------------------------------------------------------------------
# 2. Metodo LMTD
# ------------------------------------------------------------------------------

def lmtd(
    T_h_in: float, T_h_out: float,
    T_c_in: float, T_c_out: float,
    configurazione: str = "controcorrente",
) -> dict:
    """
    Calcola la LMTD e la superficie di scambio richiesta.

    Parametri
    ----------
    T_h_in, T_h_out : temperature lato caldo ingresso/uscita [°C]
    T_c_in, T_c_out : temperature lato freddo ingresso/uscita [°C]
    configurazione  : 'controcorrente' | 'equicorrente'

    Ritorna dict con LMTD, verifica 2° principio, ΔT terminali
    """
    if T_h_in <= T_c_out or T_h_out <= T_c_in:
        raise ValueError("Incrocio temperature: verifica i valori (2° principio termodinamica violato).")

    if configurazione == "controcorrente":
        dT1 = T_h_in  - T_c_out
        dT2 = T_h_out - T_c_in
    elif configurazione == "equicorrente":
        dT1 = T_h_in  - T_c_in
        dT2 = T_h_out - T_c_out
        if dT2 <= 0:
            raise ValueError("In equicorrente T_h_out deve essere > T_c_out.")
    else:
        raise ValueError("Configurazione non valida: usa 'controcorrente' o 'equicorrente'.")

    if abs(dT1 - dT2) < 1e-6:
        lmtd_val = dT1
    else:
        lmtd_val = (dT1 - dT2) / math.log(dT1 / dT2)

    return {
        "LMTD_K":        lmtd_val,
        "dT1_K":         dT1,
        "dT2_K":         dT2,
        "configurazione": configurazione,
    }


def area_da_lmtd(Q_W: float, U_W_m2K: float, LMTD_K: float, F: float = 1.0) -> dict:
    """
    Calcola la superficie di scambio necessaria.
    Q = U · A · F · LMTD  →  A = Q / (U · F · LMTD)

    Parametri
    ----------
    Q_W      : potenza termica [W]
    U_W_m2K  : coefficiente globale di scambio [W/(m²·K)]
    LMTD_K   : LMTD [K]
    F        : fattore di correzione geometrica [-] (1.0 per puro contro/equicorrente)
    """
    if U_W_m2K <= 0:
        raise ValueError("Il coefficiente U deve essere > 0 W/(m²·K).")
    if LMTD_K <= 0:
        raise ValueError("La LMTD deve essere > 0 K.")
    if F <= 0 or F > 1.0:
        raise ValueError("Il fattore F deve essere compreso tra 0 e 1.")

    A = Q_W / (U_W_m2K * F * LMTD_K)
    return {
        "A_m2":      A,
        "Q_W":       Q_W,
        "U_W_m2K":   U_W_m2K,
        "LMTD_K":    LMTD_K,
        "F":         F,
    }


# ------------------------------------------------------------------------------
# 3. Metodo NTU-ε (Number of Transfer Units — Effectiveness)
# ------------------------------------------------------------------------------

def ntu_effectiveness(
    C_h: float, C_c: float,
    T_h_in: float, T_c_in: float,
    U_W_m2K: float, A_m2: float,
    configurazione: str = "controcorrente",
) -> dict:
    """
    Calcola l'efficienza dello scambiatore e le temperature di uscita.

    Parametri
    ----------
    C_h, C_c : capacità termiche [W/K]  (= m·cp per ciascun fluido)
    T_h_in   : temperatura ingresso lato caldo [°C]
    T_c_in   : temperatura ingresso lato freddo [°C]
    U_W_m2K  : coefficiente globale [W/(m²·K)]
    A_m2     : superficie di scambio [m²]
    configurazione : 'controcorrente' | 'equicorrente'
    """
    if C_h <= 0 or C_c <= 0:
        raise ValueError("Le capacità termiche devono essere > 0 W/K.")
    if T_h_in <= T_c_in:
        raise ValueError("T_h_in deve essere maggiore di T_c_in.")
    if U_W_m2K <= 0 or A_m2 <= 0:
        raise ValueError("U e A devono essere > 0.")

    C_min = min(C_h, C_c)
    C_max = max(C_h, C_c)
    C_r   = C_min / C_max
    NTU   = U_W_m2K * A_m2 / C_min

    if configurazione == "controcorrente":
        if abs(C_r - 1.0) < 1e-6:
            eps = NTU / (1.0 + NTU)
        else:
            exp_term = math.exp(-NTU * (1.0 - C_r))
            eps = (1.0 - exp_term) / (1.0 - C_r * exp_term)
    elif configurazione == "equicorrente":
        eps = (1.0 - math.exp(-NTU * (1.0 + C_r))) / (1.0 + C_r)
    else:
        raise ValueError("Configurazione non valida: usa 'controcorrente' o 'equicorrente'.")

    Q_max = C_min * (T_h_in - T_c_in)
    Q     = eps * Q_max

    T_h_out = T_h_in - Q / C_h
    T_c_out = T_c_in + Q / C_c

    return {
        "epsilon":    eps,
        "NTU":        NTU,
        "C_r":        C_r,
        "C_min":      C_min,
        "C_max":      C_max,
        "Q_W":        Q,
        "Q_kW":       Q / 1000.0,
        "Q_max_W":    Q_max,
        "T_h_out":    T_h_out,
        "T_c_out":    T_c_out,
        "configurazione": configurazione,
    }


# ------------------------------------------------------------------------------
# Database valori U tipici [W/(m²·K)]
# ------------------------------------------------------------------------------

U_TIPICI = {
    "Acqua-Acqua (tubo/mantello)":         (800,  1500),
    "Acqua-Vapore (condensatore)":         (1000, 6000),
    "Acqua-Olio termico":                  (150,  500),
    "Aria-Acqua (radiatore/batteria)":     (30,   300),
    "Aria-Aria (recuperatore)":            (10,   50),
    "Olio-Olio (tubo/mantello)":           (100,  400),
    "Vapore-Acqua (riscaldatore diretto)": (2000, 6000),
    "Acqua-Refrigerante (evaporatore)":    (500,  2000),
}
