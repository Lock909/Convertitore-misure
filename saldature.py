# ==============================================================================
# saldature.py — Calcolo cordoni di saldatura angolari
# Riferimenti: EN 1993-1-8 (Eurocodice 3), ISO 5817
# ==============================================================================

import math

# Coefficienti di correlazione beta_w per classe di acciaio (EN 1993-1-8 Tab. 4.1)
BETA_W = {
    "S235": 0.80,
    "S275": 0.85,
    "S355": 0.90,
    "S420": 1.00,
    "S460": 1.00,
}

# Resistenze a trazione caratteristica fu [MPa]
FU_MPa = {
    "S235": 360,
    "S275": 430,
    "S355": 490,
    "S420": 520,
    "S460": 540,
}

_GAMMA_M2 = 1.25  # coefficiente parziale di sicurezza per saldatura (EN 1993-1-8)


def resistenza_ammissibile_cordone(acciaio: str = "S235") -> dict:
    """
    Tensione ammissibile di progetto del cordone d'angolo secondo EN 1993-1-8.

    f_vw,d = fu / (√3 · beta_w · gamma_M2)
    """
    if acciaio not in FU_MPa:
        raise ValueError(f"Acciaio non in tabella: {acciaio}. Disponibili: {list(FU_MPa)}")
    fu = FU_MPa[acciaio]
    beta = BETA_W[acciaio]
    f_vwd = fu / (math.sqrt(3.0) * beta * _GAMMA_M2)
    return {
        "f_vwd_MPa": f_vwd,
        "fu_MPa": fu,
        "beta_w": beta,
        "acciaio": acciaio,
    }


def gola_minima(t_min_pezzi_mm: float) -> dict:
    """
    Gola minima del cordone angolare in funzione dello spessore minimo dei pezzi
    collegati (EN 1993-1-8, Tabella 4.1).

    a_min = max(3 mm, 0.7·√t_min)  — formula di campo comune
    """
    a_min = max(3.0, 0.7 * math.sqrt(t_min_pezzi_mm))
    return {
        "a_min_mm": a_min,
        "t_pezzi_mm": t_min_pezzi_mm,
    }


def verifica_cordone_taglio(F_kN: float, a_mm: float, L_mm: float,
                              acciaio: str = "S235") -> dict:
    """
    Verifica cordone d'angolo a taglio puro (carico parallelo all'asse del cordone).

    A_gola = a · L
    tau_par = F / A_gola
    Verifica: tau_par ≤ f_vw,d / √3  →  oppure in formula EN 1993-1-8:
              √(3 · tau_par²) ≤ fu / (beta_w · gamma_M2)
    """
    if F_kN <= 0 or a_mm <= 0 or L_mm <= 0:
        raise ValueError("F, a e L devono essere > 0.")

    F_N = F_kN * 1000.0
    A_gola = a_mm * L_mm  # mm²
    tau_par = F_N / A_gola  # N/mm² = MPa

    res = resistenza_ammissibile_cordone(acciaio)
    fu = res["fu_MPa"]
    beta = res["beta_w"]

    # Verifica EN 1993-1-8: √(σ_perp² + 3(τ_perp² + τ_par²)) ≤ fu/(beta·gamma_M2)
    # Per taglio puro: sigma_perp=0, tau_perp=0
    lhs = math.sqrt(3.0) * abs(tau_par)
    rhs = fu / (beta * _GAMMA_M2)
    utilizzazione = lhs / rhs
    conforme = utilizzazione <= 1.0

    return {
        "A_gola_mm2": A_gola,
        "tau_par_MPa": tau_par,
        "f_vwd_MPa": res["f_vwd_MPa"],
        "utilizzazione": utilizzazione,
        "conforme": conforme,
        "giudizio": f"Utilizzo {utilizzazione*100:.1f}% — {'Conforme' if conforme else 'NON conforme — aumentare a o L'}",
    }


def verifica_cordone_normale(F_kN: float, a_mm: float, L_mm: float,
                               angolo_deg: float = 90.0,
                               acciaio: str = "S235") -> dict:
    """
    Verifica cordone d'angolo sotto carico normale (perpendicolare alla gola, angolo tra i pezzi = 90°).

    Sulla piano della gola (inclinato a 45°):
      sigma_perp = tau_perp = F_N / (a·L·√2)   [per angolo 90°]

    Verifica EN 1993-1-8:
      √(sigma_perp² + 3·tau_perp²) ≤ fu/(beta·gamma_M2)
      sigma_perp ≤ 0.9·fu/gamma_M2
    """
    if F_kN <= 0 or a_mm <= 0 or L_mm <= 0:
        raise ValueError("F, a e L devono essere > 0.")

    F_N = F_kN * 1000.0
    A_gola = a_mm * L_mm
    # Componenti sulla gola per cordone a 45°
    sigma_perp = F_N / (A_gola * math.sqrt(2.0))
    tau_perp = sigma_perp

    res = resistenza_ammissibile_cordone(acciaio)
    fu = res["fu_MPa"]
    beta = res["beta_w"]

    lhs1 = math.sqrt(sigma_perp**2 + 3.0 * tau_perp**2)
    rhs1 = fu / (beta * _GAMMA_M2)
    util1 = lhs1 / rhs1

    lhs2 = abs(sigma_perp)
    rhs2 = 0.9 * fu / _GAMMA_M2
    util2 = lhs2 / rhs2

    utilizzazione = max(util1, util2)
    conforme = utilizzazione <= 1.0

    return {
        "A_gola_mm2": A_gola,
        "sigma_perp_MPa": sigma_perp,
        "tau_perp_MPa": tau_perp,
        "utilizzazione": utilizzazione,
        "conforme": conforme,
        "giudizio": f"Utilizzo {utilizzazione*100:.1f}% — {'Conforme' if conforme else 'NON conforme — aumentare a o L'}",
    }


def cordone_a_doppio_T(F_kN: float, a_mm: float, larghezza_mm: float,
                        acciaio: str = "S235") -> dict:
    """
    Due cordoni simmetrici su flangia (es. saldatura pilastra a piastra):
    lunghezza totale efficace = 2 × larghezza.
    """
    L_tot = 2.0 * larghezza_mm
    return verifica_cordone_normale(F_kN, a_mm, L_tot, acciaio=acciaio)
