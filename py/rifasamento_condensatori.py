# ==============================================================================
# rifasamento_condensatori.py — Rifasamento con batterie di condensatori
# Riferimenti: IEC 60831, CEI EN 60831
# ==============================================================================

import math

_OMEGA = 2.0 * math.pi * 50.0  # pulsazione 50 Hz


def potenza_reattiva_attuale(P_kW: float, cos_phi: float) -> dict:
    """Potenza apparente e reattiva allo stato attuale."""
    if not (0.0 < cos_phi <= 1.0):
        raise ValueError("cos_phi deve essere compreso tra 0 (escluso) e 1.")
    if P_kW <= 0:
        raise ValueError("P_kW deve essere > 0.")

    phi = math.acos(cos_phi)
    tan_phi = math.tan(phi)
    Q_kvar = P_kW * tan_phi
    S_kVA = P_kW / cos_phi

    return {
        "P_kW": P_kW,
        "Q_kvar": Q_kvar,
        "S_kVA": S_kVA,
        "cos_phi": cos_phi,
        "tan_phi": tan_phi,
    }


def kvar_necessari(P_kW: float, cos_phi_attuale: float, cos_phi_target: float) -> dict:
    """
    Potenza reattiva da fornire con condensatori per passare da cos_phi_attuale a cos_phi_target.

    Q_c = P * (tan_phi1 - tan_phi2)
    """
    if not (0.0 < cos_phi_attuale <= 1.0) or not (0.0 < cos_phi_target <= 1.0):
        raise ValueError("cos_phi deve essere compreso tra 0 (escluso) e 1.")
    if cos_phi_target < cos_phi_attuale:
        raise ValueError("cos_phi_target deve essere >= cos_phi_attuale.")
    if P_kW <= 0:
        raise ValueError("P_kW deve essere > 0.")

    tan1 = math.tan(math.acos(cos_phi_attuale))
    tan2 = math.tan(math.acos(cos_phi_target))
    Q_c_kvar = P_kW * (tan1 - tan2)

    return {
        "Q_c_kvar": Q_c_kvar,
        "Q_c_kvar_arrotondato": math.ceil(Q_c_kvar / 5.0) * 5.0,
        "tan_phi_attuale": tan1,
        "tan_phi_target": tan2,
    }


def capacita_condensatori(Q_c_kvar: float, V_linea_V: float = 400.0,
                           collegamento: str = "triangolo") -> dict:
    """
    Capacità dei condensatori trifase per erogare Q_c_kvar.

    Triangolo (delta):  C = Q_c / (3 · ω · V_L²)
    Stella   (star):    C = Q_c / (3 · ω · (V_L/√3)²) = Q_c / (ω · V_L²)
    """
    if Q_c_kvar <= 0 or V_linea_V <= 0:
        raise ValueError("Q_c e V devono essere > 0.")
    if collegamento not in ("triangolo", "stella"):
        raise ValueError("Collegamento deve essere 'triangolo' o 'stella'.")

    Q_VAR = Q_c_kvar * 1000.0
    if collegamento == "triangolo":
        C_F = Q_VAR / (3.0 * _OMEGA * V_linea_V**2)
    else:
        V_fase = V_linea_V / math.sqrt(3.0)
        C_F = Q_VAR / (3.0 * _OMEGA * V_fase**2)

    return {
        "C_per_fase_uF": C_F * 1e6,
        "C_per_fase_F": C_F,
        "collegamento": collegamento,
        "Q_c_kvar": Q_c_kvar,
        "V_linea_V": V_linea_V,
    }


def verifica_rifasamento(P_kW: float, cos_phi_attuale: float,
                          Q_aggiunta_kvar: float, V_V: float = 400.0) -> dict:
    """
    Verifica del cos_phi risultante dopo l'aggiunta di una batteria condensatori.
    """
    if not (0.0 < cos_phi_attuale <= 1.0):
        raise ValueError("cos_phi_attuale non valido.")

    res_att = potenza_reattiva_attuale(P_kW, cos_phi_attuale)
    Q_residua = res_att["Q_kvar"] - Q_aggiunta_kvar
    if Q_residua < 0:
        Q_residua = 0.0

    S_new = math.sqrt(P_kW**2 + Q_residua**2)
    cos_phi_new = P_kW / S_new if S_new > 0 else 1.0
    I_prima = res_att["S_kVA"] * 1000.0 / (math.sqrt(3) * V_V)
    I_dopo = S_new * 1000.0 / (math.sqrt(3) * V_V)

    return {
        "cos_phi_risultante": cos_phi_new,
        "Q_residua_kvar": Q_residua,
        "S_risultante_kVA": S_new,
        "I_prima_A": I_prima,
        "I_dopo_A": I_dopo,
        "riduzione_corrente_pct": (1.0 - I_dopo / I_prima) * 100.0 if I_prima > 0 else 0.0,
        "soddisfa_095": cos_phi_new >= 0.95,
    }


STEP_CONDENSATORI_KVAR = [5, 10, 12.5, 15, 20, 25, 30, 40, 50, 60, 75, 100]
