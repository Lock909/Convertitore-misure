# ==============================================================================
# batterie_ups.py — Calcoli per batterie e sistemi UPS
# Riferimenti: IEC 62485-3, EN 50272-2
# ==============================================================================

import math


def calcola_autonomia(
    C_Ah: float,
    V_nom_V: float,
    P_carico_W: float,
    eta_inverter: float = 0.92,
    DOD: float = 0.80,
) -> dict:
    """
    Calcola l'autonomia di un banco batterie.

    Parametri
    ----------
    C_Ah        : capacità nominale [Ah]
    V_nom_V     : tensione nominale banco [V]
    P_carico_W  : potenza carico DC (o AC se si usa inverter) [W]
    eta_inverter: rendimento inverter/convertitore [-]
    DOD         : profondità di scarica ammissibile [-] (tipico 0.80)
    """
    if C_Ah <= 0 or V_nom_V <= 0 or P_carico_W <= 0:
        raise ValueError("Capacità, tensione e carico devono essere > 0.")
    if not 0 < eta_inverter <= 1:
        raise ValueError("Il rendimento deve essere tra 0 e 1.")
    if not 0 < DOD <= 1:
        raise ValueError("DOD deve essere tra 0 e 1.")

    E_utile_Wh = C_Ah * V_nom_V * DOD                  # energia utile [Wh]
    P_eff      = P_carico_W / eta_inverter              # potenza effettiva dalla batteria
    t_h        = E_utile_Wh / P_eff                    # autonomia [h]
    I_scarica  = P_eff / V_nom_V                        # corrente di scarica [A]
    C_rate     = C_Ah / I_scarica if I_scarica > 0 else float("inf")   # C/10, C/20, ecc.

    return {
        "t_autonomia_h":  t_h,
        "t_autonomia_min": t_h * 60.0,
        "E_utile_Wh":    E_utile_Wh,
        "I_scarica_A":   I_scarica,
        "C_rate":        C_rate,
        "P_dalla_bat_W": P_eff,
        "DOD":           DOD,
    }


def dimensiona_banco(
    P_carico_W: float,
    t_autonomia_h: float,
    V_banco_V: float,
    eta_inverter: float = 0.92,
    DOD: float = 0.80,
    fattore_invecchiamento: float = 1.25,
) -> dict:
    """
    Dimensiona il banco batterie per ottenere l'autonomia richiesta.

    Parametri
    ----------
    fattore_invecchiamento : margine per fine vita batteria (tipico 1.20-1.25)
    """
    if P_carico_W <= 0 or t_autonomia_h <= 0 or V_banco_V <= 0:
        raise ValueError("Tutti i parametri devono essere > 0.")

    P_bat  = P_carico_W / eta_inverter
    E_richiesta_Wh = P_bat * t_autonomia_h
    C_netta_Ah     = E_richiesta_Wh / V_banco_V
    C_nominale_Ah  = C_netta_Ah / DOD * fattore_invecchiamento

    return {
        "C_nominale_Ah":  C_nominale_Ah,
        "C_netta_Ah":     C_netta_Ah,
        "E_richiesta_Wh": E_richiesta_Wh,
        "I_scarica_A":    P_bat / V_banco_V,
        "C_rate_h":       C_nominale_Ah / (P_bat / V_banco_V) if P_bat > 0 else 0,
    }


def corrente_carica(C_Ah: float) -> dict:
    """
    Correnti di carica standard secondo EN 50272-2.

    C_Ah : capacità nominale batteria [Ah]
    """
    if C_Ah <= 0:
        raise ValueError("La capacità deve essere > 0 Ah.")
    return {
        "I_C1_A":   C_Ah / 1.0,     # ricarica rapida 1h
        "I_C5_A":   C_Ah / 5.0,
        "I_C10_A":  C_Ah / 10.0,    # tipica per Pb-acido
        "I_C20_A":  C_Ah / 20.0,    # lenta, per lunga vita
        "I_float_A": C_Ah * 0.002,  # corrente di mantenimento ≈ C/500
    }


def correzione_temperatura(C_Ah_nominale: float, T_C: float, tipo: str = "Pb-acido") -> dict:
    """
    Corregge la capacità in funzione della temperatura.

    Coefficienti tipici:
    - Pb-acido : -0.7% per °C sotto 25°C
    - Li-Ion   : -0.3% per °C sotto 25°C
    """
    coeff = {"Pb-acido": 0.007, "Li-Ion": 0.003, "NiMH": 0.005}.get(tipo, 0.007)
    delta = T_C - 25.0
    C_corr = C_Ah_nominale * (1.0 + coeff * delta) if delta < 0 else C_Ah_nominale
    return {
        "C_corretta_Ah":   max(C_corr, 0),
        "riduzione_pct":   (1 - C_corr / C_Ah_nominale) * 100.0 if C_corr < C_Ah_nominale else 0.0,
        "T_C":             T_C,
        "tipo_batteria":   tipo,
    }
