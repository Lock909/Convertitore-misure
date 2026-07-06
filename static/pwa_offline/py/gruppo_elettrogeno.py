# ==============================================================================
# gruppo_elettrogeno.py — Dimensionamento gruppi electrogeni di emergenza
# ==============================================================================

import math


def potenza_spunto_motore(P_kW: float, cos_phi: float = 0.85, fattore_spunto: float = 6.0,
                           eta: float = 0.90) -> dict:
    """
    Potenza apparente di spunto richiesta per l'avviamento diretto di un motore asincrono.

    S_spunto = (P / (eta * cos_phi)) * fattore_spunto

    fattore_spunto tipico: 5-8 per avviamento diretto, 2-3 per avviamento soft-start/inverter
    """
    if P_kW <= 0 or cos_phi <= 0 or eta <= 0:
        raise ValueError("P, cos_phi ed eta devono essere > 0.")

    S_nom_kVA = P_kW / (eta * cos_phi)
    S_spunto_kVA = S_nom_kVA * fattore_spunto

    return {
        "S_nom_kVA": S_nom_kVA,
        "S_spunto_kVA": S_spunto_kVA,
        "fattore_spunto": fattore_spunto,
    }


def dimensiona_gruppo(carichi_kW: list, cos_phi_medio: float = 0.85,
                       fattore_contemporaneita: float = 0.80, margine_sicurezza: float = 1.20) -> dict:
    """
    Dimensionamento della potenza del gruppo electrogeno a partire dalla somma dei carichi.

    S_gruppo = (Sum(P_carichi) * fattore_contemporaneita / cos_phi) * margine_sicurezza
    """
    if not carichi_kW:
        raise ValueError("Inserire almeno un carico.")
    if any(c < 0 for c in carichi_kW):
        raise ValueError("I carichi non possono essere negativi.")
    if cos_phi_medio <= 0:
        raise ValueError("cos_phi deve essere > 0.")

    P_tot = sum(carichi_kW)
    P_contemporanea = P_tot * fattore_contemporaneita
    S_gruppo = (P_contemporanea / cos_phi_medio) * margine_sicurezza

    return {
        "P_tot_kW": P_tot,
        "P_contemporanea_kW": P_contemporanea,
        "S_gruppo_kVA": S_gruppo,
        "P_gruppo_kW": S_gruppo * cos_phi_medio,
    }


def autonomia_serbatoio(V_serbatoio_L: float, P_kW: float, consumo_specifico_L_kWh: float = 0.25,
                         fattore_carico: float = 0.75) -> dict:
    """
    Autonomia del gruppo elettrogeno in base al volume del serbatoio.

    consumo_specifico tipico: 0.20-0.30 L/kWh a pieno carico (diesel)
    """
    if V_serbatoio_L <= 0 or P_kW <= 0 or consumo_specifico_L_kWh <= 0:
        raise ValueError("V_serbatoio, P e consumo specifico devono essere > 0.")

    consumo_orario_L = P_kW * fattore_carico * consumo_specifico_L_kWh
    if consumo_orario_L <= 0:
        raise ValueError("Il consumo orario calcolato è nullo.")
    t_autonomia_h = V_serbatoio_L / consumo_orario_L

    return {
        "t_autonomia_h": t_autonomia_h,
        "consumo_orario_L": consumo_orario_L,
        "fattore_carico": fattore_carico,
    }


def serbatoio_per_autonomia(P_kW: float, t_autonomia_h: float, consumo_specifico_L_kWh: float = 0.25,
                             fattore_carico: float = 0.75) -> dict:
    """
    Volume di serbatoio necessario per garantire una data autonomia.
    """
    if P_kW <= 0 or t_autonomia_h <= 0:
        raise ValueError("P e t_autonomia devono essere > 0.")

    consumo_orario_L = P_kW * fattore_carico * consumo_specifico_L_kWh
    V_necessario_L = consumo_orario_L * t_autonomia_h

    return {
        "V_necessario_L": V_necessario_L,
        "consumo_orario_L": consumo_orario_L,
    }


FATTORI_SPUNTO_TIPICI = {
    "Motore asincrono - avviamento diretto": 6.0,
    "Motore asincrono - stella/triangolo":   3.0,
    "Motore asincrono - soft starter":       2.5,
    "Motore asincrono - inverter (VFD)":     1.2,
    "Compressore frigorifero":               4.0,
    "Pompa centrifuga":                      3.0,
    "Carico resistivo (riscaldatori)":       1.0,
}
