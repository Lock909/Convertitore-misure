# ==============================================================================
# isolamento_termico.py — Perdite termiche e isolamento (ISO 12241 / EN ISO 6946)
# ==============================================================================

import math


def perdita_parete_piana(
    T_int_C: float,
    T_est_C: float,
    strati: list,
    R_si: float = 0.13,
    R_se: float = 0.04,
) -> dict:
    """
    Perdita termica per unità di area attraverso una parete piana.

    Parametri
    ----------
    T_int_C, T_est_C : temperature interna ed esterna [°C]
    strati           : list di dict [{"nome": ..., "spessore_m": ..., "lambda_W_mK": ...}]
    R_si, R_se       : resistenze superficiali interna ed esterna [m²K/W]
                       (default: parete verticale, EN ISO 6946)
    """
    if not strati:
        raise ValueError("Inserire almeno uno strato.")
    for s in strati:
        if s.get("spessore_m", 0) <= 0 or s.get("lambda_W_mK", 0) <= 0:
            raise ValueError("Spessore e lambda devono essere > 0 per ogni strato.")

    R_strati = [s["spessore_m"] / s["lambda_W_mK"] for s in strati]
    R_tot    = R_si + sum(R_strati) + R_se
    U        = 1.0 / R_tot
    dT       = T_int_C - T_est_C
    q_W_m2   = U * dT               # flusso [W/m²] (positivo = verso esterno)

    T_sup_int = T_int_C - R_si * q_W_m2
    T_sup_est = T_est_C + R_se * q_W_m2
    T_interfaces = [T_int_C - (R_si + sum(R_strati[:i])) * q_W_m2 for i in range(len(strati) + 1)]

    return {
        "U_W_m2K":       U,
        "R_tot_m2KW":    R_tot,
        "q_W_m2":        q_W_m2,
        "T_sup_int_C":   T_sup_int,
        "T_sup_est_C":   T_sup_est,
        "T_interfaces":  T_interfaces,
        "R_strati":      R_strati,
        "strati":        strati,
    }


def perdita_tubo_cilindrico(
    T_fluid_C: float,
    T_amb_C: float,
    D_int_mm: float,
    strati: list,
    L_m: float = 1.0,
    R_si: float = 0.01,
    R_se: float = 0.13,
) -> dict:
    """
    Perdita termica per tubo cilindrico con strati di isolamento.

    Parametri
    ----------
    D_int_mm : diametro interno tubo [mm]
    strati   : list di dict [{"nome": ..., "spessore_m": ..., "lambda_W_mK": ...}]
    L_m      : lunghezza tubo [m]
    R_si     : resistenza superficiale interna [m²K/W]
    R_se     : resistenza superficiale esterna [m²K/W]
    """
    if D_int_mm <= 0:
        raise ValueError("Il diametro deve essere > 0 mm.")
    if not strati:
        raise ValueError("Inserire almeno uno strato.")

    r = D_int_mm / 2000.0         # raggio interno [m]
    R_lin = R_si / (2 * math.pi * r * L_m)   # [K/W]
    for s in strati:
        r_est = r + s["spessore_m"]
        R_lin += math.log(r_est / r) / (2 * math.pi * s["lambda_W_mK"] * L_m)
        r = r_est
    R_lin += R_se / (2 * math.pi * r * L_m)

    dT  = T_fluid_C - T_amb_C
    Q_W = dT / R_lin

    return {
        "Q_W":          Q_W,
        "Q_W_m":        Q_W / L_m,
        "R_lin_KW":     R_lin,
        "D_est_mm":     r * 2000.0,
        "L_m":          L_m,
    }


def temperatura_rugiada(T_amb_C: float, UR_pct: float) -> float:
    """Formula di Magnus per il punto di rugiada [°C]."""
    if not 0 < UR_pct <= 100:
        raise ValueError("L'umidità relativa deve essere tra 0 e 100%.")
    a, b = 17.27, 237.7
    gamma = (a * T_amb_C) / (b + T_amb_C) + math.log(UR_pct / 100.0)
    return b * gamma / (a - gamma)


def verifica_condensa(
    T_sup_C: float,
    T_amb_C: float,
    UR_pct: float,
) -> dict:
    """Verifica il rischio di condensazione su una superficie."""
    T_dew = temperatura_rugiada(T_amb_C, UR_pct)
    margine = T_sup_C - T_dew
    return {
        "T_rugiada_C": T_dew,
        "T_superficie_C": T_sup_C,
        "margine_K": margine,
        "rischio_condensa": margine < 0,
        "giudizio": "RISCHIO CONDENSA" if margine < 0 else (
            "Attenzione (margine < 2 K)" if margine < 2 else "OK — nessun rischio"
        ),
    }


# Database lambda tipici [W/(m·K)]
MATERIALI_LAMBDA = {
    "Calcestruzzo normale":         2.30,
    "Calcestruzzo cellulare":       0.20,
    "Mattone pieno":                0.72,
    "Mattone forato":               0.40,
    "Legno (abete)":                0.13,
    "Pannello OSB":                 0.13,
    "Lana minerale (MW)":           0.04,
    "Polistirene espanso (EPS)":    0.038,
    "Poliuretano (PUR)":            0.026,
    "Sughero":                      0.045,
    "Vetro cellulare":              0.042,
    "Acciaio":                     50.0,
    "Rame":                       390.0,
    "Inox AISI 316":               15.0,
    "Elastomero espanso (Armaflex)": 0.035,
    "Lana di roccia per tubi":      0.040,
}
