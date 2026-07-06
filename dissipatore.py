# ==============================================================================
# dissipatore.py — Calcoli termici per dissipatori e componenti di potenza
# Riferimenti: IEC 60747, JEDEC
# ==============================================================================

import math


def temperatura_giunzione(
    P_W: float,
    T_amb_C: float,
    R_jc: float,
    R_cs: float = 0.0,
    R_sa: float = None,
) -> dict:
    """
    Calcola la temperatura di giunzione del componente.

    Catena termica: Giunzione → Case → Dissipatore → Ambiente
    Tj = T_amb + P · (R_jc + R_cs + R_sa)

    Parametri
    ----------
    P_W    : potenza dissipata [W]
    T_amb_C: temperatura ambiente [°C]
    R_jc   : resistenza termica giunzione-case [°C/W] (dal datasheet)
    R_cs   : resistenza termica case-dissipatore [°C/W] (pasta termica + isolatore)
    R_sa   : resistenza termica dissipatore-ambiente [°C/W] (None = senza dissipatore)
    """
    if P_W < 0:
        raise ValueError("La potenza non può essere negativa.")
    if R_jc < 0 or R_cs < 0:
        raise ValueError("Le resistenze termiche non possono essere negative.")

    R_tot = R_jc + R_cs + (R_sa if R_sa is not None else 0.0)
    Tj    = T_amb_C + P_W * R_tot

    T_case = T_amb_C + P_W * (R_cs + (R_sa or 0.0))
    T_dis  = T_amb_C + P_W * (R_sa or 0.0)

    return {
        "Tj_C":      Tj,
        "T_case_C":  T_case,
        "T_diss_C":  T_dis,
        "T_amb_C":   T_amb_C,
        "R_tot_CW":  R_tot,
        "R_ja_CW":   R_tot,
        "P_W":       P_W,
    }


def rsa_necessario(
    P_W: float,
    Tj_max_C: float,
    T_amb_C: float,
    R_jc: float,
    R_cs: float = 0.5,
) -> dict:
    """
    Calcola la resistenza termica massima del dissipatore per rispettare Tj_max.

    R_sa_max = (Tj_max - T_amb) / P - R_jc - R_cs
    """
    if P_W <= 0:
        raise ValueError("La potenza deve essere > 0 W.")
    if Tj_max_C <= T_amb_C:
        raise ValueError("Tj_max deve essere > T_amb.")

    R_sa = (Tj_max_C - T_amb_C) / P_W - R_jc - R_cs
    if R_sa < 0:
        raise ValueError(
            f"Impossibile rispettare Tj_max={Tj_max_C}°C con R_jc={R_jc}+R_cs={R_cs} "
            f"già superano il budget termico ({R_jc+R_cs:.3f} > {(Tj_max_C-T_amb_C)/P_W:.3f} °C/W)."
        )
    return {
        "R_sa_max_CW":  R_sa,
        "Tj_max_C":     Tj_max_C,
        "budget_CW":    (Tj_max_C - T_amb_C) / P_W,
        "R_jc_R_cs_CW": R_jc + R_cs,
    }


def potenza_max_dissipabile(
    Tj_max_C: float,
    T_amb_C: float,
    R_jc: float,
    R_cs: float = 0.5,
    R_sa: float = None,
) -> dict:
    """
    Potenza massima dissipabile per rispettare Tj_max.
    P_max = (Tj_max - T_amb) / R_tot
    """
    R_tot = R_jc + R_cs + (R_sa if R_sa is not None else 0.0)
    if R_tot <= 0:
        raise ValueError("R_tot deve essere > 0.")
    P_max = (Tj_max_C - T_amb_C) / R_tot
    return {
        "P_max_W":  P_max,
        "R_tot_CW": R_tot,
        "Tj_max_C": Tj_max_C,
        "T_amb_C":  T_amb_C,
    }


def curva_derating(
    P_max_25C: float,
    Tj_max_C: float,
    T_amb_max_C: float = 100.0,
    n_punti: int = 30,
) -> dict:
    """
    Curva di derating: potenza massima in funzione della temperatura ambiente.
    Tipicamente lineare da P_max a T_amb = 25°C fino a P=0 a T_amb = Tj_max.
    """
    T_arr = [25.0 + i * (T_amb_max_C - 25.0) / n_punti for i in range(n_punti + 1)]
    P_arr = [
        max(0.0, P_max_25C * (Tj_max_C - T) / (Tj_max_C - 25.0))
        for T in T_arr
    ]
    return {"T_amb_C": T_arr, "P_max_W": P_arr}


# Database pasta termica tipica R_cs [°C/W]
PASTA_TERMICA = {
    "Pasta siliconica standard (λ≈1 W/mK)":  0.8,
    "Pasta buona (Artic MX-4, λ≈8.5 W/mK)":  0.15,
    "Pasta conduttiva (Shin-Etsu X23, λ≈6)":  0.20,
    "Indium foil":                             0.05,
    "Isolatore ceramico (Al2O3)":              0.50,
    "Isolatore Kapton 25µm":                   1.20,
    "Mica 0.12mm":                             0.40,
}
