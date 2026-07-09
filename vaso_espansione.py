# ==============================================================================
# vaso_espansione.py — Dimensionamento vaso di espansione a membrana chiuso
# per impianti idronici (riscaldamento/raffrescamento), rif. pratica UNI 9182.
# ==============================================================================

import math

_BAR_PER_METRO_H2O = 1.0 / 10.197  # 1 bar = 10.197 m colonna d'acqua

# Coefficiente di dilatazione termica dell'acqua e(T), riferito a 10°C,
# valori tipici da tabelle di progettazione UNI 9182 / manuali impiantistici.
_COEFF_DILATAZIONE_TABELLA = [
    (10, 0.0003), (20, 0.0018), (30, 0.0044), (40, 0.0079), (50, 0.0121),
    (60, 0.0171), (70, 0.0227), (80, 0.0289), (90, 0.0359), (100, 0.0435),
]


def coefficiente_dilatazione(T_max_C: float) -> dict:
    """
    Coefficiente di dilatazione termica dell'acqua e(T) per la temperatura
    massima di esercizio data (interpolazione sulla tabella tipica, satura
    fuori dal campo tabellato 10-100°C).
    """
    tab = _COEFF_DILATAZIONE_TABELLA
    if T_max_C <= tab[0][0]:
        e = tab[0][1]
    elif T_max_C >= tab[-1][0]:
        e = tab[-1][1]
    else:
        e = None
        for (t_lo, e_lo), (t_hi, e_hi) in zip(tab, tab[1:]):
            if t_lo <= T_max_C <= t_hi:
                frac = (T_max_C - t_lo) / (t_hi - t_lo)
                e = e_lo + frac * (e_hi - e_lo)
                break
    return {"e": e, "T_max_C": T_max_C}


def volume_espansione(V_impianto_l: float, T_max_C: float) -> dict:
    """Volume di espansione Ve = V_impianto * e(T_max)."""
    if V_impianto_l <= 0:
        raise ValueError("Il volume dell'impianto deve essere > 0 l.")
    e = coefficiente_dilatazione(T_max_C)["e"]
    Ve = V_impianto_l * e
    return {"Ve_l": Ve, "e": e, "V_impianto_l": V_impianto_l, "T_max_C": T_max_C}


def fattore_utilizzo_vaso(P_precarica_bar: float, P_taratura_bar: float) -> dict:
    """
    Fattore di utilizzo del vaso a membrana: Fu = (Pf - Pi) / (Pf + 1),
    pressioni relative in bar. Pi = precarica del vaso (di norma pari alla
    pressione statica dell'impianto), Pf = pressione massima di esercizio
    (taratura valvola di sicurezza, con margine già applicato a monte).
    """
    if P_precarica_bar < 0:
        raise ValueError("La pressione di precarica deve essere >= 0 bar.")
    if P_taratura_bar <= P_precarica_bar:
        raise ValueError("La pressione di taratura deve essere > pressione di precarica.")
    Fu = (P_taratura_bar - P_precarica_bar) / (P_taratura_bar + 1.0)
    return {"Fu": Fu, "P_precarica_bar": P_precarica_bar, "P_taratura_bar": P_taratura_bar}


def pressione_statica_da_altezza(altezza_m: float) -> dict:
    """Pressione statica minima al vaso, dall'altezza della colonna d'acqua
    dell'impianto (1 bar ≈ 10.197 m)."""
    if altezza_m < 0:
        raise ValueError("L'altezza deve essere >= 0 m.")
    P_bar = altezza_m * _BAR_PER_METRO_H2O
    return {"P_statica_bar": P_bar, "altezza_m": altezza_m}


def volume_vaso_nominale(
    V_impianto_l: float,
    T_max_C: float,
    P_precarica_bar: float,
    P_taratura_bar: float,
) -> dict:
    """Dimensionamento completo in un'unica chiamata: volume di espansione,
    fattore di utilizzo e volume nominale minimo del vaso (Vn = Ve / Fu)."""
    ve = volume_espansione(V_impianto_l, T_max_C)
    fu = fattore_utilizzo_vaso(P_precarica_bar, P_taratura_bar)
    Vn = ve["Ve_l"] / fu["Fu"]

    risultato = {}
    risultato.update(ve)
    risultato.update(fu)
    risultato["Vn_l"] = Vn
    return risultato
