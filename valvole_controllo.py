# ==============================================================================
# valvole_controllo.py — Dimensionamento valvole di controllo (IEC 60534)
# ==============================================================================

import math


def cv_liquido(
    Q_m3h: float,
    dP_bar: float,
    SG: float = 1.0,
) -> dict:
    """
    Calcola Cv e Kv per liquido incomprimibile (IEC 60534-2-1).

    Cv = Q · √(SG / ΔP)   [unità US: gpm / √psi]
    Kv = Q · √(SG / ΔP)   [unità SI: m³/h / √bar]

    Parametri
    ----------
    Q_m3h : portata [m³/h]
    dP_bar: caduta di pressione [bar]
    SG    : densità relativa rispetto all'acqua [-]
    """
    if Q_m3h <= 0:
        raise ValueError("La portata deve essere > 0 m³/h.")
    if dP_bar <= 0:
        raise ValueError("La caduta di pressione deve essere > 0 bar.")
    if SG <= 0:
        raise ValueError("La densità relativa deve essere > 0.")

    Kv = Q_m3h * math.sqrt(SG / dP_bar)
    Cv = Kv / 0.865          # conversione Kv → Cv (US)

    return {
        "Kv":       Kv,
        "Cv":       Cv,
        "Q_m3h":    Q_m3h,
        "dP_bar":   dP_bar,
        "SG":       SG,
    }


def cv_gas(
    Q_Nm3h: float,
    P1_bar_a: float,
    P2_bar_a: float,
    T_K: float = 293.15,
    SG_gas: float = 1.0,
) -> dict:
    """
    Calcola Kv per gas comprimibili (IEC 60534).

    Controlla il choked flow: se P2 < P1/2, il flusso è bloccato (choking).

    Parametri
    ----------
    Q_Nm3h   : portata in condizioni normali [Nm³/h] (0°C, 1.013 bar)
    P1_bar_a : pressione a monte [bar a]
    P2_bar_a : pressione a valle [bar a]
    T_K      : temperatura a monte [K]
    SG_gas   : densità relativa rispetto all'aria [-]
    """
    if Q_Nm3h <= 0:
        raise ValueError("La portata deve essere > 0 Nm³/h.")
    if P1_bar_a <= 0 or P2_bar_a <= 0:
        raise ValueError("Le pressioni devono essere > 0 bar a.")
    if P2_bar_a >= P1_bar_a:
        raise ValueError("P2 deve essere minore di P1.")

    P_cr = P1_bar_a / 2.0           # pressione critica (choked flow, γ≈1.4 → r_cr=0.528 ≈ 0.5)
    choked = P2_bar_a <= P_cr
    P2_eff = P_cr if choked else P2_bar_a
    dP_eff = P1_bar_a - P2_eff
    P_med  = (P1_bar_a + P2_eff) / 2.0

    # Formula approssimata (IEC 60534, metodo semplificato):
    # Kv = Q_Nm3h / (514 · √(ΔP·P_med / (SG_gas · T_K / 273.15)))
    T_norm = T_K / 273.15
    Kv = Q_Nm3h / (514.0 * math.sqrt(dP_eff * P_med / (SG_gas * T_norm)))
    Cv = Kv / 0.865

    return {
        "Kv":          Kv,
        "Cv":          Cv,
        "choked_flow": choked,
        "P_critica_bar_a": P_cr,
        "dP_effettivo_bar": dP_eff,
    }


def verifica_cavitazione(
    P1_bar_a: float,
    P2_bar_a: float,
    P_vap_bar_a: float,
) -> dict:
    """
    Stima il rischio di cavitazione in una valvola liquido.
    σ (sigma) = (P1 - P_vap) / (P1 - P2)
    Rischio cavitazione quando σ < σ_critico (≈ 1.5-2.5 a seconda della valvola).
    """
    if P1_bar_a <= P2_bar_a:
        raise ValueError("P1 deve essere > P2.")
    if P_vap_bar_a >= P2_bar_a:
        raise ValueError("P_vap deve essere < P2 (altrimenti evaporazione certa).")

    dP  = P1_bar_a - P2_bar_a
    sigma = (P1_bar_a - P_vap_bar_a) / dP
    FL_stima = 0.85          # fattore di recupero pressione tipico globo

    rischio = "ALTA" if sigma < FL_stima**2 else ("MEDIA" if sigma < FL_stima else "BASSA")

    return {
        "sigma":       sigma,
        "FL":          FL_stima,
        "sigma_crit":  FL_stima**2,
        "rischio":     rischio,
        "dP_bar":      dP,
        "P_vap_bar_a": P_vap_bar_a,
    }


# Caratteristiche di portata tipiche
CARATTERISTICHE = {
    "Lineare":            "Q ∝ apertura  — buona per piccole escursioni di pressione",
    "Uguale percentuale": "Q ∝ e^(n·x)  — standard process, ampia variazione di pressione",
    "A via rapida":       "Q cresce rapidamente all'apertura — ON/OFF",
}
