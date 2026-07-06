# ==============================================================================
# trasformatore.py — Trasformatore monofase e trifase (IEC 60076)
# ==============================================================================

import math


def calcola_trasformatore(
    S_kVA: float,
    V1_V: float,
    V2_V: float,
    P_ferro_W: float,
    P_rame_W: float,
    V_cc_pct: float = 4.0,
    I0_pct: float = 2.0,
    cos_phi: float = 0.85,
    trifase: bool = True,
) -> dict:
    """
    Calcola le grandezze principali di un trasformatore.

    Parametri
    ----------
    S_kVA     : potenza apparente nominale [kVA]
    V1_V      : tensione primario [V]
    V2_V      : tensione secondario [V]
    P_ferro_W : perdite nel ferro a vuoto [W]
    P_rame_W  : perdite nel rame a pieno carico [W]
    V_cc_pct  : tensione di cortocircuito [%]
    I0_pct    : corrente a vuoto [%]
    cos_phi   : fattore di potenza del carico
    trifase   : True = trifase, False = monofase
    """
    if S_kVA <= 0:
        raise ValueError("La potenza deve essere > 0 kVA.")
    if V1_V <= 0 or V2_V <= 0:
        raise ValueError("Le tensioni devono essere > 0 V.")
    if not 0 < cos_phi <= 1:
        raise ValueError("cos_phi deve essere tra 0 e 1.")

    S_VA    = S_kVA * 1000.0
    rapporto = V1_V / V2_V

    # Correnti nominali
    if trifase:
        I1_nom = S_VA / (math.sqrt(3) * V1_V)
        I2_nom = S_VA / (math.sqrt(3) * V2_V)
    else:
        I1_nom = S_VA / V1_V
        I2_nom = S_VA / V2_V

    # Corrente a vuoto
    I0_A = I0_pct / 100.0 * I1_nom

    # Resistenza e reattanza equivalenti ridotte al secondario
    Z_cc  = (V_cc_pct / 100.0) * V2_V / I2_nom          # [Ω]
    R_eq  = P_rame_W / I2_nom**2                          # [Ω]
    X_eq  = math.sqrt(max(Z_cc**2 - R_eq**2, 0.0))       # [Ω]

    # Caduta di tensione sotto carico nominale (a cos_phi)
    sin_phi = math.sin(math.acos(cos_phi))
    dV_pct  = I2_nom * (R_eq * cos_phi + X_eq * sin_phi) / V2_V * 100.0

    # Rendimento al variare del carico
    eta_nominale = (S_VA * cos_phi - P_rame_W - P_ferro_W) / (S_VA * cos_phi) * 100.0

    # Carico ottimale (rendimento massimo)
    beta_opt = math.sqrt(P_ferro_W / P_rame_W)
    eta_max  = (
        (beta_opt * S_VA * cos_phi)
        / (beta_opt * S_VA * cos_phi + P_ferro_W + beta_opt**2 * P_rame_W)
    ) * 100.0

    # Impedenza di cortocircuito
    Z_cc_pct = V_cc_pct
    R_cc_pct = P_rame_W / (S_VA) * 100.0
    X_cc_pct = math.sqrt(max(Z_cc_pct**2 - R_cc_pct**2, 0.0))

    # Corrente di cortocircuito lato secondario
    I_cc = I2_nom / (V_cc_pct / 100.0)

    return {
        "rapporto_a":    rapporto,
        "I1_nom_A":      I1_nom,
        "I2_nom_A":      I2_nom,
        "I0_A":          I0_A,
        "I_cc_A":        I_cc,
        "R_eq_ohm":      R_eq,
        "X_eq_ohm":      X_eq,
        "Z_cc_ohm":      Z_cc,
        "dV_pct":        dV_pct,
        "eta_nom_pct":   eta_nominale,
        "eta_max_pct":   eta_max,
        "beta_opt":      beta_opt,
        "P_ferro_W":     P_ferro_W,
        "P_rame_W":      P_rame_W,
        "P_tot_W":       P_ferro_W + P_rame_W,
        "R_cc_pct":      R_cc_pct,
        "X_cc_pct":      X_cc_pct,
        "V_cc_pct":      V_cc_pct,
        "trifase":       trifase,
    }


def rendimento_vs_carico(
    S_kVA: float,
    P_ferro_W: float,
    P_rame_W: float,
    cos_phi: float = 0.85,
    n_punti: int = 20,
) -> dict:
    """Genera la curva rendimento vs. fattore di carico β (0→1.2)."""
    S_VA  = S_kVA * 1000.0
    betas = [i / n_punti * 1.2 for i in range(1, n_punti + 1)]
    etas  = []
    for b in betas:
        P_out = b * S_VA * cos_phi
        P_perd = P_ferro_W + b**2 * P_rame_W
        etas.append(P_out / (P_out + P_perd) * 100.0 if P_out > 0 else 0.0)
    return {"beta": betas, "eta_pct": etas}
