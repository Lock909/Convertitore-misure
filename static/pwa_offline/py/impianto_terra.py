# ==============================================================================
# impianto_terra.py — Impianto di terra (CEI 64-8 / CEI 11-1)
# ==============================================================================

import math


def resistenza_dispersore_picchetto(L_m: float, rho_ohm_m: float, d_m: float = 0.02) -> dict:
    """
    Resistenza di terra di un dispersore a picchetto verticale (formula di Dwight semplificata).

    R = (rho / (2*pi*L)) * (ln(4L/d) - 1)

    Parametri
    ----------
    L_m       : lunghezza infissa del picchetto [m]
    rho_ohm_m : resistività del terreno [Ω·m]
    d_m       : diametro del picchetto [m]
    """
    if L_m <= 0 or rho_ohm_m <= 0 or d_m <= 0:
        raise ValueError("L, rho e d devono essere > 0.")

    R = (rho_ohm_m / (2.0 * math.pi * L_m)) * (math.log(4.0 * L_m / d_m) - 1.0)
    return {
        "R_ohm":    R,
        "L_m":      L_m,
        "rho_ohm_m": rho_ohm_m,
    }


def resistenza_picchetti_paralleli(R_singolo_ohm: float, n: int, coeff_riduzione: float = 0.8) -> dict:
    """
    Resistenza equivalente di n picchetti in parallelo (con coefficiente di mutua influenza).

    R_eq = (R_singolo / n) / coeff_riduzione
    """
    if R_singolo_ohm <= 0 or n < 1:
        raise ValueError("R_singolo deve essere > 0 e n >= 1.")
    if not (0 < coeff_riduzione <= 1):
        raise ValueError("Il coefficiente di riduzione deve essere in (0, 1].")

    R_eq = (R_singolo_ohm / n) / coeff_riduzione
    return {
        "R_eq_ohm": R_eq,
        "n_picchetti": n,
        "coeff_riduzione": coeff_riduzione,
    }


def sezione_minima_pe(I_g_A: float, t_s: float, k: float = 143.0) -> dict:
    """
    Sezione minima del conduttore di protezione PE (formula adiabatica CEI 64-8 §543.1.3).

    S = sqrt(I^2 * t) / k

    Parametri
    ----------
    I_g_A : corrente di guasto a terra [A]
    t_s   : tempo di intervento della protezione [s]
    k     : costante materiale/isolamento (143 per rame con PVC, 176 per rame con XLPE)
    """
    if I_g_A <= 0 or t_s <= 0 or k <= 0:
        raise ValueError("I_g, t e k devono essere > 0.")

    S = math.sqrt(I_g_A**2 * t_s) / k
    return {
        "S_mm2_minima": S,
        "I_g_A": I_g_A,
        "t_s": t_s,
        "k": k,
    }


def verifica_tensione_contatto(R_terra_ohm: float, I_g_A: float, UTp_V: float = 50.0) -> dict:
    """
    Verifica della tensione di contatto applicata (sistemi TT/TN).

    U_c = R_terra * I_g   — deve essere <= UTp (50V in ambienti ordinari, 25V in ambienti speciali)
    """
    if R_terra_ohm <= 0 or I_g_A <= 0:
        raise ValueError("R_terra e I_g devono essere > 0.")

    U_c = R_terra_ohm * I_g_A
    conforme = U_c <= UTp_V
    return {
        "U_c_V": U_c,
        "UTp_V": UTp_V,
        "conforme": conforme,
        "giudizio": "Conforme" if conforme else "NON conforme — ridurre R_terra o tempo di intervento",
    }


def coordinamento_tt(R_terra_ohm: float, I_dn_A: float, UTp_V: float = 50.0) -> dict:
    """
    Verifica di coordinamento sistema TT (CEI 64-8 §413.1.4.2).

    Condizione: R_terra * I_dn <= UTp
    dove I_dn è la corrente differenziale nominale dell'interruttore (Idn).
    """
    if R_terra_ohm <= 0 or I_dn_A <= 0:
        raise ValueError("R_terra e I_dn devono essere > 0.")

    R_max = UTp_V / I_dn_A
    conforme = R_terra_ohm <= R_max
    return {
        "R_max_ohm": R_max,
        "R_terra_ohm": R_terra_ohm,
        "conforme": conforme,
        "giudizio": "Coordinamento verificato" if conforme else f"R_terra deve essere <= {R_max:.2f} Ω",
    }


# Resistività tipiche del terreno [Ω·m]
RESISTIVITA_TERRENO = {
    "Terreno paludoso":          10.0,
    "Limo":                      50.0,
    "Argilla":                   100.0,
    "Sabbia bagnata":            200.0,
    "Sabbia secca/ghiaia":       1000.0,
    "Roccia calcarea":           3000.0,
    "Roccia granitica":          10000.0,
}
