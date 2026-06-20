# ==============================================================================
# caduta_tensione_bt.py — Caduta di tensione su cavi BT
# Riferimenti: CEI 64-8, IEC 60364-5-52
# ==============================================================================

import math

# Resistività [Ω·mm²/m] a 75°C (a caldo, più conservativo)
RESISTIVITA_OHM_MM2_M = {
    "rame":      0.0225,
    "alluminio": 0.036,
}

# Reattanza approssimativa per cavi multipolari fino a 95 mm² [Ω/m]
_X_OHMPERM = 0.08e-3  # 0.08 mΩ/m — valore tipico cavi multipolari BT

# Sezioni normalizzate CEI [mm²]
SEZIONI_NORMALIZZATE_MM2 = [1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240]


def resistenza_cavo(S_mm2: float, L_m: float, conduttore: str = "rame",
                    andata_ritorno: bool = True) -> float:
    """Resistenza totale del cavo [Ω]."""
    if conduttore not in RESISTIVITA_OHM_MM2_M:
        raise ValueError(f"Conduttore non riconosciuto: {conduttore}")
    rho = RESISTIVITA_OHM_MM2_M[conduttore]
    k = 2.0 if andata_ritorno else 1.0
    return rho * k * L_m / S_mm2


def caduta_tensione_monofase(I_A: float, L_m: float, S_mm2: float,
                              cos_phi: float = 0.9, conduttore: str = "rame") -> dict:
    """
    Caduta di tensione su linea monofase (andata + ritorno).

    ΔV = 2 · I · L · (R/L · cos_phi + X · sin_phi)
    """
    if I_A <= 0 or L_m <= 0 or S_mm2 <= 0:
        raise ValueError("I, L e S devono essere > 0.")
    if not (0.0 < cos_phi <= 1.0):
        raise ValueError("cos_phi non valido.")

    sin_phi = math.sqrt(1.0 - cos_phi**2)
    R_ohm = resistenza_cavo(S_mm2, L_m, conduttore, andata_ritorno=True)
    X_ohm = _X_OHMPERM * 2.0 * L_m
    dV_V = I_A * (R_ohm * cos_phi + X_ohm * sin_phi)
    V_nom = 230.0
    dV_pct = dV_V / V_nom * 100.0

    return {
        "dV_V": dV_V,
        "dV_pct": dV_pct,
        "R_cavo_ohm": R_ohm,
        "conforme_3pct": dV_pct <= 3.0,
        "conforme_5pct": dV_pct <= 5.0,
        "giudizio": _giudizio_dv(dV_pct),
    }


def caduta_tensione_trifase(I_A: float, L_m: float, S_mm2: float,
                             cos_phi: float = 0.9, conduttore: str = "rame") -> dict:
    """
    Caduta di tensione su linea trifase equilibrata.

    ΔV = √3 · I · L · (R/L · cos_phi + X · sin_phi)
    dove R/L è per singolo conduttore (andata = 1 lunghezza).
    """
    if I_A <= 0 or L_m <= 0 or S_mm2 <= 0:
        raise ValueError("I, L e S devono essere > 0.")
    if not (0.0 < cos_phi <= 1.0):
        raise ValueError("cos_phi non valido.")

    sin_phi = math.sqrt(1.0 - cos_phi**2)
    # Per trifase: R di un singolo conduttore (un'unica andatura)
    R_ohm_fase = resistenza_cavo(S_mm2, L_m, conduttore, andata_ritorno=False)
    X_ohm_fase = _X_OHMPERM * L_m
    dV_V = math.sqrt(3.0) * I_A * (R_ohm_fase * cos_phi + X_ohm_fase * sin_phi)
    V_nom = 400.0
    dV_pct = dV_V / V_nom * 100.0

    return {
        "dV_V": dV_V,
        "dV_pct": dV_pct,
        "R_fase_ohm": R_ohm_fase,
        "conforme_3pct": dV_pct <= 3.0,
        "conforme_5pct": dV_pct <= 5.0,
        "giudizio": _giudizio_dv(dV_pct),
    }


def sezione_da_caduta_max(P_kW: float, V_V: float, L_m: float,
                           dV_pct_max: float = 3.0, cos_phi: float = 0.9,
                           tipo: str = "trifase", conduttore: str = "rame") -> dict:
    """
    Sezione minima del cavo per rispettare la caduta di tensione massima.

    Formula inversa: S = rho * k * L * I / (dV_max * cos_phi)
    (approssimazione R-only, conservativa per cos_phi > 0.7)
    """
    if P_kW <= 0 or V_V <= 0 or L_m <= 0:
        raise ValueError("P, V e L devono essere > 0.")
    if tipo not in ("trifase", "monofase"):
        raise ValueError("tipo deve essere 'trifase' o 'monofase'.")

    rho = RESISTIVITA_OHM_MM2_M[conduttore]
    if tipo == "trifase":
        I_A = P_kW * 1000.0 / (math.sqrt(3.0) * V_V * cos_phi)
        k = 1.0  # singolo conduttore
        dV_V_max = dV_pct_max / 100.0 * V_V
        # dV = sqrt3 * I * (rho/S * L) * cos_phi → S = sqrt3 * I * rho * L * cos_phi / dV
        S_min = math.sqrt(3.0) * I_A * rho * L_m * cos_phi / dV_V_max
    else:
        I_A = P_kW * 1000.0 / (V_V * cos_phi)
        dV_V_max = dV_pct_max / 100.0 * V_V
        S_min = 2.0 * I_A * rho * L_m * cos_phi / dV_V_max

    # Arrotonda alla sezione normalizzata superiore
    S_norm = next((s for s in SEZIONI_NORMALIZZATE_MM2 if s >= S_min), SEZIONI_NORMALIZZATE_MM2[-1])

    return {
        "S_mm2_calcolata": S_min,
        "S_mm2_normalizzata": S_norm,
        "I_A": I_A,
        "tipo": tipo,
        "conduttore": conduttore,
    }


def _giudizio_dv(dV_pct: float) -> str:
    if dV_pct <= 3.0:
        return "Conforme — ΔV ≤ 3% (distribuzione)"
    elif dV_pct <= 5.0:
        return "Accettabile — ΔV ≤ 5% (utilizzo)"
    else:
        return "NON conforme — aumentare la sezione"
