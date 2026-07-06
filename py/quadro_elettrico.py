# ==============================================================================
# quadro_elettrico.py — Potenza dissipata e ventilazione quadri elettrici
# Riferimenti: IEC 61439-1/2
# ==============================================================================

import math


def potenza_dissipata_componenti(componenti: dict) -> dict:
    """
    Somma della potenza dissipata dai componenti installati nel quadro.

    Parametri
    ----------
    componenti : dict {nome_componente: potenza_dissipata_W}
    """
    if not componenti:
        raise ValueError("Inserire almeno un componente.")
    if any(p < 0 for p in componenti.values()):
        raise ValueError("Le potenze dissipate non possono essere negative.")

    P_tot_W = sum(componenti.values())
    return {
        "P_tot_W": P_tot_W,
        "n_componenti": len(componenti),
        "dettaglio": dict(componenti),
    }


def aumento_temperatura_quadro(P_diss_W: float, superficie_m2: float, k_trasmissione: float = 5.5) -> dict:
    """
    Stima dell'aumento di temperatura interna del quadro per dissipazione naturale (IEC 61439-1, metodo semplificato).

    delta_T = P_diss / (k * A)

    k_trasmissione : coefficiente globale di scambio termico [W/(m²·K)] (tipico 5-6 per lamiera, senza ventilazione forzata)
    """
    if P_diss_W <= 0 or superficie_m2 <= 0 or k_trasmissione <= 0:
        raise ValueError("P_diss, superficie e k devono essere > 0.")

    delta_T = P_diss_W / (k_trasmissione * superficie_m2)

    return {
        "delta_T_K": delta_T,
        "k_trasmissione": k_trasmissione,
        "superficie_m2": superficie_m2,
    }


def superficie_quadro(larghezza_m: float, altezza_m: float, profondita_m: float,
                       installato_a_parete: bool = False) -> dict:
    """
    Superficie utile di scambio termico di un quadro (involucro metallico), secondo IEC 61439-1.

    Se installato a parete, la superficie posteriore non contribuisce allo scambio.
    """
    if larghezza_m <= 0 or altezza_m <= 0 or profondita_m <= 0:
        raise ValueError("Le dimensioni devono essere > 0.")

    A_frontale = larghezza_m * altezza_m
    A_laterali = 2.0 * profondita_m * altezza_m
    A_superiore = larghezza_m * profondita_m
    A_posteriore = 0.0 if installato_a_parete else A_frontale

    A_tot = A_frontale + A_laterali + A_superiore + A_posteriore

    return {
        "A_tot_m2": A_tot,
        "A_frontale_m2": A_frontale,
        "A_laterali_m2": A_laterali,
        "installato_a_parete": installato_a_parete,
    }


def portata_ventilazione_forzata(P_diss_W: float, delta_T_max_K: float = 15.0,
                                  rho_aria: float = 1.2, cp_aria: float = 1005.0) -> dict:
    """
    Portata d'aria necessaria per ventilazione forzata a salto termico imposto.

    Q = P_diss / (rho * cp * delta_T)
    """
    if P_diss_W <= 0 or delta_T_max_K <= 0:
        raise ValueError("P_diss e delta_T_max devono essere > 0.")

    Q_m3s = P_diss_W / (rho_aria * cp_aria * delta_T_max_K)
    Q_m3h = Q_m3s * 3600.0

    return {
        "Q_m3h": Q_m3h,
        "Q_m3s": Q_m3s,
        "delta_T_max_K": delta_T_max_K,
    }


def verifica_temperatura_quadro(P_diss_W: float, superficie_m2: float, T_amb_C: float,
                                 T_max_componenti_C: float = 55.0, k_trasmissione: float = 5.5) -> dict:
    """
    Verifica complessiva: la temperatura interna stimata non deve superare la temperatura massima
    ammessa dai componenti più sensibili (tipicamente PLC/elettronica: 40-55°C).
    """
    res = aumento_temperatura_quadro(P_diss_W, superficie_m2, k_trasmissione)
    T_interna = T_amb_C + res["delta_T_K"]
    conforme = T_interna <= T_max_componenti_C

    return {
        "T_interna_C": T_interna,
        "delta_T_K": res["delta_T_K"],
        "conforme": conforme,
        "giudizio": "Conforme — raffreddamento naturale sufficiente" if conforme else
                    "NON conforme — necessaria ventilazione forzata o scambiatore",
    }


POTENZE_DISSIPATE_TIPICHE_W = {
    "PLC CPU":                      8.0,
    "Modulo I/O digitale (16ch)":    3.0,
    "Modulo I/O analogico (8ch)":    2.5,
    "Alimentatore switching 24V/5A": 12.0,
    "Inverter/VFD (per kW motore)":  30.0,
    "Contattore (per A nominale)":   0.8,
    "Magnetotermico (per A nominale)": 0.5,
    "Trasformatore ausiliari 230/24V": 8.0,
}
