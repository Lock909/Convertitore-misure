# ==============================================================================
# armonie_thd.py — Analisi armonica e THD (Total Harmonic Distortion)
# Riferimenti: IEC 61000-4-7, IEEE 519
# ==============================================================================

import math


def calcola_thd(fondamentale_rms: float, armoniche: dict) -> dict:
    """
    Calcola il THD% da fondamentale e armoniche.

    Parametri
    ----------
    fondamentale_rms : valore RMS della fondamentale (1ª armonica) [V o A]
    armoniche        : dict {ordine: ampiezza_rms} es. {3: 15.0, 5: 10.0, 7: 5.0}

    Ritorna
    -------
    dict con THD_pct, potenza distorta, contributo per armonica
    """
    if fondamentale_rms <= 0:
        raise ValueError("La fondamentale deve essere > 0.")
    if not armoniche:
        raise ValueError("Inserire almeno un'armonica.")

    somma_quadrati = sum(v**2 for v in armoniche.values())
    THD = math.sqrt(somma_quadrati) / fondamentale_rms * 100.0
    rms_totale = math.sqrt(fondamentale_rms**2 + somma_quadrati)

    contributi = {
        ordine: {
            "ampiezza_rms": v,
            "pct_fondamentale": v / fondamentale_rms * 100.0,
            "contributo_thd_pct": v**2 / somma_quadrati * 100.0 if somma_quadrati > 0 else 0.0,
        }
        for ordine, v in sorted(armoniche.items())
    }

    # Classificazione IEEE 519 (tensione, bus < 69 kV)
    if THD < 5.0:
        giudizio = "Conforme IEEE 519 (THD_V < 5%)"
    elif THD < 8.0:
        giudizio = "Limite attenzione (5% ≤ THD < 8%)"
    else:
        giudizio = "Non conforme IEEE 519 (THD ≥ 8%)"

    return {
        "THD_pct":       THD,
        "rms_totale":    rms_totale,
        "fondamentale":  fondamentale_rms,
        "contributi":    contributi,
        "giudizio_ieee": giudizio,
    }


def forma_onda_armonica(
    fondamentale_rms: float,
    armoniche: dict,
    f1_Hz: float = 50.0,
    n_periodi: int = 2,
    n_punti: int = 500,
) -> dict:
    """
    Ricostruisce la forma d'onda nel dominio del tempo sommando fondamentale + armoniche.

    Parametri
    ----------
    armoniche : dict {ordine: ampiezza_rms}  (fase zero per tutte)
    """
    if f1_Hz <= 0:
        raise ValueError("La frequenza deve essere > 0 Hz.")
    T  = 1.0 / f1_Hz
    dt = n_periodi * T / n_punti
    t_arr = [i * dt for i in range(n_punti + 1)]
    t_ms  = [t * 1000 for t in t_arr]

    omega1 = 2.0 * math.pi * f1_Hz
    V_fund = [fondamentale_rms * math.sqrt(2) * math.sin(omega1 * t) for t in t_arr]
    V_tot  = list(V_fund)
    per_ordine = {"1ª (fondamentale)": V_fund}

    for ordine, amp_rms in sorted(armoniche.items()):
        v_h = [amp_rms * math.sqrt(2) * math.sin(ordine * omega1 * t) for t in t_arr]
        V_tot = [V_tot[i] + v_h[i] for i in range(len(t_arr))]
        per_ordine[f"{ordine}ª armonica"] = v_h

    return {
        "t_ms":       t_ms,
        "V_tot":      V_tot,
        "per_ordine": per_ordine,
    }


# Limiti IEC 61000-3-2 classe A (correnti armoniche, A)
LIMITI_IEC61000_3_2 = {
    2:  1.08, 3: 2.30, 4: 0.43, 5: 1.14, 6: 0.30, 7: 0.77,
    8:  0.23, 9: 0.40, 10: 0.184, 11: 0.33, 12: 0.153, 13: 0.21,
}
