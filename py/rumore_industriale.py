# ==============================================================================
# rumore_industriale.py — Acustica e rumore industriale
# Riferimenti: ISO 9612, D.Lgs 81/2008 Titolo VIII Capo II
# ==============================================================================

import math


# Valori limite D.Lgs 81/2008
LEX_INFERIORE_dB = 80.0    # valore inferiore di azione
LEX_SUPERIORE_dB = 85.0    # valore superiore di azione
LEX_LIMITE_dB    = 87.0    # valore limite di esposizione


def somma_livelli_db(livelli_db: list) -> dict:
    """
    Somma energetica di N sorgenti sonore indipendenti.
    L_tot = 10 · log10(Σ 10^(Li/10))

    Restituisce anche l'incremento rispetto alla sorgente più forte.
    """
    if not livelli_db:
        raise ValueError("Inserire almeno un livello sonoro.")
    if any(l < 0 for l in livelli_db):
        raise ValueError("I livelli devono essere ≥ 0 dB.")

    somma_lin  = sum(10.0 ** (l / 10.0) for l in livelli_db)
    L_tot      = 10.0 * math.log10(somma_lin)
    L_max      = max(livelli_db)
    incremento = L_tot - L_max

    return {
        "L_tot_dB":    L_tot,
        "L_max_dB":    L_max,
        "incremento_dB": incremento,
        "n_sorgenti":  len(livelli_db),
    }


def lex_8h(
    T_esposizioni_min: list,
    L_esposizioni_dBA: list,
) -> dict:
    """
    Livello di esposizione giornaliero normalizzato a 8 ore (ISO 9612).

    LEX,8h = 10 · log10(1/T0 · Σ Ti · 10^(LAeq,Ti / 10))
    con T0 = 480 min (8 ore)

    Parametri
    ----------
    T_esposizioni_min  : durata di ciascuna esposizione [min]
    L_esposizioni_dBA  : livello LAeq per ciascuna esposizione [dB(A)]
    """
    if len(T_esposizioni_min) != len(L_esposizioni_dBA):
        raise ValueError("Le liste devono avere la stessa lunghezza.")
    if not T_esposizioni_min:
        raise ValueError("Inserire almeno un'esposizione.")

    T0    = 480.0                   # 8 ore in minuti
    somma = sum(
        T * 10.0 ** (L / 10.0)
        for T, L in zip(T_esposizioni_min, L_esposizioni_dBA)
    )
    LEX   = 10.0 * math.log10(somma / T0)

    if LEX < LEX_INFERIORE_dB:
        rischio = "Trascurabile — nessun obbligo"
        dpi_obbligo = False
    elif LEX < LEX_SUPERIORE_dB:
        rischio = "Valore inferiore di azione — sorveglianza sanitaria su richiesta"
        dpi_obbligo = False
    elif LEX < LEX_LIMITE_dB:
        rischio = "Valore superiore di azione — DPI obbligatori, sorveglianza sanitaria"
        dpi_obbligo = True
    else:
        rischio = "VALORE LIMITE SUPERATO — intervento immediato obbligatorio"
        dpi_obbligo = True

    # Dose di esposizione (% rispetto al limite 87 dB(A))
    dose_pct = 10.0 ** ((LEX - LEX_LIMITE_dB) / 10.0) * 100.0

    return {
        "LEX_8h_dBA":    LEX,
        "rischio":       rischio,
        "dpi_obbligo":   dpi_obbligo,
        "dose_pct":      dose_pct,
        "T_tot_min":     sum(T_esposizioni_min),
        "limite_dBA":    LEX_LIMITE_dB,
    }


def attenuazione_dpi(SNR_dB: float, L_amb_dBA: float) -> dict:
    """
    Livello effettivo sotto il DPI secondo il metodo SNR (EN ISO 4869-2).

    L_p,eff = L_amb - SNR + 5   [dB(A)]  (metodo semplificato)
    """
    if SNR_dB < 0:
        raise ValueError("SNR deve essere ≥ 0 dB.")
    L_eff = L_amb_dBA - SNR_dB + 5.0     # +5 dB correzione conservativa
    return {
        "L_eff_dBA":   L_eff,
        "L_amb_dBA":   L_amb_dBA,
        "SNR_dB":      SNR_dB,
        "protezione_adeguata": L_eff <= 75.0,
        "giudizio": "Adeguato" if L_eff <= 75.0 else (
            "Accettabile (70-80 dBA)" if L_eff <= 80.0 else "Insufficiente"
        ),
    }


def attenuazione_distanza(L_sorgente_dB: float, d1_m: float, d2_m: float) -> dict:
    """
    Attenuazione geometrica in campo libero (sorgente puntuale).
    ΔL = 20 · log10(d2/d1)   → L(d2) = L(d1) - 20·log10(d2/d1)
    """
    if d1_m <= 0 or d2_m <= 0:
        raise ValueError("Le distanze devono essere > 0 m.")
    delta = 20.0 * math.log10(d2_m / d1_m)
    return {
        "L_d2_dB":  L_sorgente_dB - delta,
        "delta_dB": delta,
        "d1_m":     d1_m,
        "d2_m":     d2_m,
    }


# Database DPI tipici (SNR approssimativo)
DPI_SNR = {
    "Tappi monouso (inserimento corretto)": 30,
    "Tappi riutilizzabili":                 25,
    "Cuffie leggere (es. 3M Peltor H510)":  27,
    "Cuffie professionali (es. Peltor X5)": 37,
    "Casco + cuffie (combo)":              42,
}
