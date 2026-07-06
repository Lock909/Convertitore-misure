# ==============================================================================
# tubazione_pressione.py — Spessore minimo tubazioni in pressione
# Riferimenti: EN 13480-3, ASME B31.3
# ==============================================================================

import math

# Tensione ammissibile per i materiali più comuni [MPa]
# f = Rm/2.4 secondo EN 13480-3 (schema semplificato a temperatura ambiente)
MATERIALI_TUBI = {
    "P235GH (acciaio C)":    {"Rm_MPa": 360, "Re_MPa": 235, "f_MPa": 150},
    "P265GH (acciaio C-Mn)": {"Rm_MPa": 410, "Re_MPa": 265, "f_MPa": 171},
    "P355NH (acciaio C-Mn)": {"Rm_MPa": 490, "Re_MPa": 355, "f_MPa": 204},
    "AISI 304 / 1.4301":     {"Rm_MPa": 515, "Re_MPa": 205, "f_MPa": 137},
    "AISI 316L / 1.4404":    {"Rm_MPa": 485, "Re_MPa": 170, "f_MPa": 115},
    "S235 (strutturale)":    {"Rm_MPa": 360, "Re_MPa": 235, "f_MPa": 117},
}

# Diametri nominali con Do esterno [mm] (serie ISO 4200 / EN 10220)
TABELLA_DN_DO_MM = {
    15:  17.2,
    20:  21.3,
    25:  26.9,
    32:  33.7,
    40:  42.4,
    50:  48.3,
    65:  60.3,
    80:  76.1,
    100: 101.6,
    125: 127.0,
    150: 152.4,
    200: 219.1,
    250: 273.0,
    300: 323.9,
    400: 406.4,
    500: 508.0,
}

# Spessori normalizzati [mm] (da DN e serie EN 10220)
SPESSORI_NORMALIZZATI_MM = [1.6, 2.0, 2.3, 2.6, 2.9, 3.2, 3.6, 4.0, 4.5, 5.0,
                              5.6, 6.3, 7.1, 8.0, 8.8, 10.0, 11.0, 12.5, 14.2, 16.0, 20.0]


def spessore_minimo(P_bar: float, D_esterno_mm: float, f_MPa: float,
                    E_giunzione: float = 1.0, c_corrosione_mm: float = 1.0,
                    y: float = 0.4) -> dict:
    """
    Spessore minimo di parete di una tubazione in pressione secondo EN 13480-3.

    t_calc = (P · Do) / (2 · f · E + 2 · y · P)
    t_min  = t_calc + c_corrosione

    Parametri
    ----------
    P_bar           : pressione di esercizio [bar]
    D_esterno_mm    : diametro esterno [mm]
    f_MPa           : tensione ammissibile del materiale a esercizio [MPa]
    E_giunzione     : coefficiente giuntura (1.0 = senza saldatura o esaminata al 100%)
    c_corrosione_mm : sovraspessore di corrosione [mm]
    y               : coefficiente di forma (0.4 per t < Do/6 e T < 480°C)
    """
    if P_bar <= 0 or D_esterno_mm <= 0 or f_MPa <= 0:
        raise ValueError("P, Do e f devono essere > 0.")

    P_MPa = P_bar / 10.0
    t_calc = (P_MPa * D_esterno_mm) / (2.0 * f_MPa * E_giunzione + 2.0 * y * P_MPa)
    t_min = t_calc + c_corrosione_mm

    # Spessore commerciale normalizzato superiore
    t_norm = next((s for s in SPESSORI_NORMALIZZATI_MM if s >= t_min),
                  SPESSORI_NORMALIZZATI_MM[-1])

    return {
        "t_calc_mm": t_calc,
        "t_min_mm": t_min,
        "t_normalizzato_mm": t_norm,
        "P_MPa": P_MPa,
        "D_interno_mm": D_esterno_mm - 2.0 * t_norm,
        "nota": "t_calc + c_corrosione ≤ t_normalizzato scelto",
    }


def pressione_ammissibile(t_mm: float, D_esterno_mm: float, f_MPa: float,
                           E_giunzione: float = 1.0, c_corrosione_mm: float = 1.0,
                           y: float = 0.4) -> dict:
    """
    Pressione ammissibile per uno spessore esistente (funzione inversa di spessore_minimo).

    P = 2·f·E·(t - c) / (Do - 2·y·(t - c))
    """
    if t_mm <= 0 or D_esterno_mm <= 0 or f_MPa <= 0:
        raise ValueError("t, Do e f devono essere > 0.")

    t_eff = t_mm - c_corrosione_mm
    if t_eff <= 0:
        raise ValueError("Lo spessore netto (t - c_corrosione) è ≤ 0.")

    P_MPa = (2.0 * f_MPa * E_giunzione * t_eff) / (D_esterno_mm - 2.0 * y * t_eff)
    P_bar = P_MPa * 10.0

    return {
        "P_amm_bar": P_bar,
        "P_amm_MPa": P_MPa,
        "t_efficace_mm": t_eff,
    }


def verifica_tubazione(P_bar: float, D_esterno_mm: float, t_adottato_mm: float,
                        f_MPa: float, E: float = 1.0, c: float = 1.0) -> dict:
    """
    Verifica completa: calcola t_min e confronta con t_adottato.
    """
    res = spessore_minimo(P_bar, D_esterno_mm, f_MPa, E, c)
    conforme = t_adottato_mm >= res["t_min_mm"]
    utilizzazione = res["t_calc_mm"] / (t_adottato_mm - c) if (t_adottato_mm - c) > 0 else float("inf")

    return {
        "t_min_mm": res["t_min_mm"],
        "t_adottato_mm": t_adottato_mm,
        "t_calc_mm": res["t_calc_mm"],
        "utilizzazione": utilizzazione,
        "conforme": conforme,
        "giudizio": "Conforme" if conforme else "NON conforme — aumentare lo spessore",
    }
