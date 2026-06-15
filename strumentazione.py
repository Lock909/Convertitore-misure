# ==============================================================================
# strumentazione.py — Strumentazione industriale e segnali
# Riferimenti: IEC 60751 (Pt100), NIST ITS-90 (termocoppie), IEC 60584
# ==============================================================================

import math


# ------------------------------------------------------------------------------
# 1. Conversione segnale mA ↔ tensione (shunt)
# ------------------------------------------------------------------------------

def converti_ma_tensione(corrente_ma: float, R_shunt_ohm: float) -> dict:
    """
    Converte un segnale in corrente [mA] in tensione [V] su resistore shunt.
    Tipico: 4-20 mA su 250 Ω → 1-5 V (ingresso PLC/DCS).

    Parametri
    ----------
    corrente_ma  : corrente del loop [mA]
    R_shunt_ohm  : valore resistore shunt [Ω]
    """
    if corrente_ma < 0:
        raise ValueError("La corrente non può essere negativa.")
    if R_shunt_ohm <= 0:
        raise ValueError("La resistenza shunt deve essere > 0 Ω.")

    V = corrente_ma / 1000.0 * R_shunt_ohm
    P_mw = (corrente_ma / 1000.0)**2 * R_shunt_ohm * 1000.0

    # Percentuale nel range 4-20 mA
    pct_4_20 = ((corrente_ma - 4.0) / 16.0 * 100.0) if corrente_ma >= 4.0 else None

    return {
        "tensione_V":   V,
        "tensione_mV":  V * 1000.0,
        "potenza_mW":   P_mw,
        "pct_4_20":     pct_4_20,
    }


def tensione_a_ma(tensione_V: float, R_shunt_ohm: float) -> float:
    """Converte tensione [V] su shunt in corrente di loop [mA]."""
    if R_shunt_ohm <= 0:
        raise ValueError("La resistenza shunt deve essere > 0 Ω.")
    return (tensione_V / R_shunt_ohm) * 1000.0


# ------------------------------------------------------------------------------
# 2. Termocoppie — linearizzazione inversa NIST ITS-90 (mV → °C)
# ------------------------------------------------------------------------------

# Coefficienti polinomi inversi NIST ITS-90: T(°C) = Σ c_i · E^i
# dove E è il segnale in mV, T è in °C
# Fonte: https://srdata.nist.gov/its90/main/

_TC_INVERSA = {
    "K": [
        # Range -200 → 0 °C  (mV: -5.891 → 0)
        {
            "E_min": -5.891, "E_max": 0.0,
            "c": [0.0, 25.173462, -1.1662878, -1.0833638,
                  -0.8977354, -0.37342377, -0.086632643,
                  -0.010450598, -5.1920577e-4],
        },
        # Range 0 → 500 °C   (mV: 0 → 20.644)
        {
            "E_min": 0.0, "E_max": 20.644,
            "c": [0.0, 25.08355, 7.860106e-2, -2.503131e-1,
                  8.31527e-2, -1.228034e-2, 9.804036e-4,
                  -4.41303e-5, 1.057734e-6, -1.052755e-8],
        },
        # Range 500 → 1372 °C (mV: 20.644 → 54.886)
        {
            "E_min": 20.644, "E_max": 54.886,
            "c": [-1.318058e2, 4.830222e1, -1.646031,
                  5.464731e-2, -9.650715e-4, 8.802193e-6, -3.11081e-8],
        },
    ],
    "J": [
        # Range -210 → 0 °C  (mV: -8.095 → 0)
        {
            "E_min": -8.095, "E_max": 0.0,
            "c": [0.0, 19.528268, -1.2286185, -1.0752178,
                  -5.9086933e-1, -1.7256713e-1, -2.8131513e-2,
                  -2.396337e-3, -8.3823321e-5],
        },
        # Range 0 → 760 °C   (mV: 0 → 42.919)
        {
            "E_min": 0.0, "E_max": 42.919,
            "c": [0.0, 19.78425, -2.001204e-1, 1.036969e-2,
                  -2.549687e-4, 3.585153e-6, -5.344285e-8, 5.09989e-10],
        },
    ],
    "T": [
        # Range -200 → 0 °C  (mV: -5.603 → 0)
        {
            "E_min": -5.603, "E_max": 0.0,
            "c": [0.0, 25.949192, -2.1316967e-1, 7.9018692e-1,
                  4.2527777e-1, 1.3304473e-1, 2.0241446e-2, 1.2668171e-3],
        },
        # Range 0 → 400 °C   (mV: 0 → 20.872)
        {
            "E_min": 0.0, "E_max": 20.872,
            "c": [0.0, 25.928, -7.602961e-1, 4.637791e-2,
                  -2.165394e-3, 6.048144e-5, -7.293422e-7],
        },
    ],
    "E": [
        # Range -200 → 0 °C  (mV: -8.825 → 0)
        {
            "E_min": -8.825, "E_max": 0.0,
            "c": [0.0, 16.977288, -4.351497e-1, -1.5859697e-1,
                  -9.2502871e-2, -2.6084314e-2, -4.1360199e-3,
                  -3.403403e-4, -1.156489e-5],
        },
        # Range 0 → 1000 °C  (mV: 0 → 76.373)
        {
            "E_min": 0.0, "E_max": 76.373,
            "c": [0.0, 17.057035, -2.3301759e-1, 6.5435585e-3,
                  -7.3562749e-5, -1.7896001e-6, 8.4036165e-8,
                  -1.3735879e-9, 1.0629823e-11, -3.2447087e-14],
        },
    ],
}


def termocoppia_mv_a_gradi(mv: float, tipo: str) -> dict:
    """
    Linearizzazione NIST ITS-90: converte FEM termocoppia [mV] in temperatura [°C].

    Parametri
    ----------
    mv   : segnale della termocoppia [mV]
    tipo : 'K' | 'J' | 'T' | 'E'

    Ritorna
    -------
    dict con temperatura, tipo, range valido
    """
    tipo = tipo.upper()
    if tipo not in _TC_INVERSA:
        raise ValueError(f"Tipo termocoppia non supportato: '{tipo}'. Supportati: {list(_TC_INVERSA.keys())}")

    segmenti = _TC_INVERSA[tipo]
    segmento = None
    for s in segmenti:
        if s["E_min"] <= mv <= s["E_max"]:
            segmento = s
            break

    if segmento is None:
        E_min_tot = min(s["E_min"] for s in segmenti)
        E_max_tot = max(s["E_max"] for s in segmenti)
        raise ValueError(
            f"Segnale {mv:.3f} mV fuori range per termocoppia tipo {tipo} "
            f"({E_min_tot:.3f} → {E_max_tot:.3f} mV)."
        )

    T = sum(c * mv**i for i, c in enumerate(segmento["c"]))

    return {
        "temperatura_C": T,
        "tipo":          tipo,
        "mv_ingresso":   mv,
        "range_mv":      (segmento["E_min"], segmento["E_max"]),
    }


def tipi_termocoppia() -> list:
    return list(_TC_INVERSA.keys())


# ------------------------------------------------------------------------------
# 3. RTD Pt100 — IEC 60751 / Callendar-Van Dusen
# ------------------------------------------------------------------------------

# Costanti IEC 60751 (ASTM E1137 compatibile)
_PT100_R0    = 100.0        # Ω a 0°C
_PT100_A     = 3.9083e-3    # °C⁻¹
_PT100_B     = -5.775e-7    # °C⁻²
_PT100_C     = -4.183e-12   # °C⁻⁴ (solo T < 0°C)


def pt100_t_a_r(T_C: float) -> float:
    """Calcola resistenza Pt100 [Ω] dalla temperatura [°C] (IEC 60751)."""
    if T_C < -200.0 or T_C > 850.0:
        raise ValueError("Temperatura fuori range Pt100 IEC 60751 (-200 → 850 °C).")
    R0 = _PT100_R0
    if T_C >= 0:
        return R0 * (1.0 + _PT100_A * T_C + _PT100_B * T_C**2)
    else:
        return R0 * (1.0 + _PT100_A * T_C + _PT100_B * T_C**2
                     + _PT100_C * (T_C - 100.0) * T_C**3)


def pt100_r_a_t(R_ohm: float) -> dict:
    """
    Calcola temperatura [°C] dalla resistenza Pt100 [Ω] (IEC 60751).
    Per T > 0°C: soluzione analitica dell'equazione quadratica.
    Per T < 0°C: bisection numerica (equazione di quarto grado).

    Ritorna dict con temperatura, resistenza, range valido.
    """
    R_min = pt100_t_a_r(-200.0)
    R_max = pt100_t_a_r(850.0)
    if R_ohm < R_min or R_ohm > R_max:
        raise ValueError(f"Resistenza {R_ohm:.2f} Ω fuori range Pt100 ({R_min:.2f} → {R_max:.2f} Ω).")

    R0 = _PT100_R0
    R0_a = R0 * _PT100_A
    R0_b = R0 * _PT100_B
    # Equazione per T > 0: R0_b·T² + R0_a·T + (R0 - R) = 0
    discriminante = R0_a**2 - 4.0 * R0_b * (R0 - R_ohm)
    T_pos = (-R0_a + math.sqrt(max(0.0, discriminante))) / (2.0 * R0_b)

    if T_pos >= -1.0:   # soluzione nel dominio T ≥ 0
        T = T_pos
    else:
        # Bisection per T < 0
        lo, hi = -200.0, 0.0
        for _ in range(60):
            mid = (lo + hi) / 2.0
            if pt100_t_a_r(mid) < R_ohm:
                lo = mid
            else:
                hi = mid
        T = (lo + hi) / 2.0

    return {
        "temperatura_C": T,
        "R_ohm":         R_ohm,
        "R_a_0C":        R0,
        "range_C":       (-200.0, 850.0),
    }


# ------------------------------------------------------------------------------
# 4. Calcolo errore di misura e incertezza
# ------------------------------------------------------------------------------

def calcola_errore_misura(
    valore_misurato: float,
    fondo_scala: float,
    errore_pct_fs: float,
    n_decimali_display: int = 0,
) -> dict:
    """
    Calcola l'errore assoluto e relativo di uno strumento.

    Parametri
    ----------
    valore_misurato   : valore letto dallo strumento
    fondo_scala       : fondo scala dello strumento
    errore_pct_fs     : accuratezza dichiarata [% del fondo scala]
    n_decimali_display: risoluzione display (per errore di quantizzazione)
    """
    if fondo_scala <= 0:
        raise ValueError("Il fondo scala deve essere > 0.")
    if errore_pct_fs < 0:
        raise ValueError("L'errore percentuale non può essere negativo.")

    err_ass = fondo_scala * errore_pct_fs / 100.0
    err_rel = (err_ass / abs(valore_misurato) * 100.0) if valore_misurato != 0 else float("inf")

    # Errore di risoluzione (quantizzazione display)
    risoluzione = 10**(-n_decimali_display) if n_decimali_display >= 0 else 1.0
    err_quant   = risoluzione / 2.0

    # Incertezza combinata (somma in quadratura)
    incertezza_comb = math.sqrt(err_ass**2 + err_quant**2)

    return {
        "errore_assoluto":    err_ass,
        "errore_relativo_pct": err_rel,
        "errore_quant":       err_quant,
        "incertezza_comb":    incertezza_comb,
        "valore_min":         valore_misurato - err_ass,
        "valore_max":         valore_misurato + err_ass,
    }


def combina_errori(errori_assoluti: list) -> dict:
    """
    Combina più sorgenti di errore in quadratura (regola GUM).

    Parametri
    ----------
    errori_assoluti : lista di errori assoluti delle singole sorgenti

    Ritorna
    -------
    dict con errore combinato RSS e somma lineare (worst-case)
    """
    if not errori_assoluti:
        raise ValueError("Fornire almeno un errore.")
    rss   = math.sqrt(sum(e**2 for e in errori_assoluti))
    worst = sum(abs(e) for e in errori_assoluti)
    return {
        "errore_rss":        rss,
        "errore_worst_case": worst,
        "n_sorgenti":        len(errori_assoluti),
    }
