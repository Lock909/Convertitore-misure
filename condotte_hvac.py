# ==============================================================================
# condotte_hvac.py — Dimensionamento condotte aria HVAC (Darcy-Weisbach)
# ==============================================================================

import math

_G = 9.80665


def proprieta_aria(T_C: float = 20.0, P_Pa: float = 101325.0) -> dict:
    """
    Proprietà dell'aria secca per temperatura T [°C] e pressione P [Pa].
    Formule di Sutherland per viscosità dinamica.
    """
    T_K = T_C + 273.15
    rho = P_Pa / (287.05 * T_K)              # [kg/m³]
    mu = 1.458e-6 * T_K**1.5 / (T_K + 110.4)  # [Pa·s] — formula Sutherland
    nu = mu / rho                              # [m²/s]

    return {
        "rho_kg_m3": rho,
        "mu_Pa_s": mu,
        "nu_m2_s": nu,
        "T_C": T_C,
    }


def diametro_idraulico_rettangolare(a_mm: float, b_mm: float) -> float:
    """Diametro idraulico di sezione rettangolare: Dh = 4A/P = 2ab/(a+b)."""
    if a_mm <= 0 or b_mm <= 0:
        raise ValueError("a e b devono essere > 0.")
    return 2.0 * a_mm * b_mm / (a_mm + b_mm)


def _reynolds_aria(v_ms: float, Dh_mm: float, T_C: float = 20.0) -> tuple:
    """Restituisce (Re, nu, rho)."""
    aria = proprieta_aria(T_C)
    Dh_m = Dh_mm / 1000.0
    Re = v_ms * Dh_m / aria["nu_m2_s"]
    return Re, aria["nu_m2_s"], aria["rho_kg_m3"]


def _fattore_attrito(Re: float, rugosita_relativa: float) -> float:
    if Re < 2300:
        return 64.0 / Re
    if rugosita_relativa <= 0:
        rugosita_relativa = 1e-8
    return 0.25 / (math.log10(rugosita_relativa / 3.7 + 5.74 / Re**0.9))**2


def perdita_carico_condotta(Q_m3h: float, Dh_mm: float, L_m: float,
                              forma: str = "circolare",
                              a_mm: float = 0.0, b_mm: float = 0.0,
                              rugosita_mm: float = 0.09,
                              T_C: float = 20.0) -> dict:
    """
    Perdita di carico distribuita in condotta aria.

    Per forma='circolare': Dh = D_mm
    Per forma='rettangolare': Dh calcolato da a_mm, b_mm

    Rugosità default 0.09 mm (condotte acciaio zincato standard UNI-CIG)

    Restituisce perdita in Pa/m e Pa totale.
    """
    if Q_m3h <= 0 or L_m <= 0:
        raise ValueError("Q e L devono essere > 0.")

    if forma == "rettangolare":
        if a_mm <= 0 or b_mm <= 0:
            raise ValueError("Per sezione rettangolare specificare a_mm e b_mm.")
        Dh_mm = diametro_idraulico_rettangolare(a_mm, b_mm)
        A_m2 = a_mm * b_mm / 1e6
    else:
        if Dh_mm <= 0:
            raise ValueError("Dh_mm deve essere > 0.")
        A_m2 = math.pi * (Dh_mm / 1000.0)**2 / 4.0

    Dh_m = Dh_mm / 1000.0
    Q_m3s = Q_m3h / 3600.0
    v_ms = Q_m3s / A_m2

    Re, nu, rho = _reynolds_aria(v_ms, Dh_mm, T_C)
    eps_rel = (rugosita_mm / 1000.0) / Dh_m
    f = _fattore_attrito(Re, eps_rel)

    dP_pa_m = f * (1.0 / Dh_m) * 0.5 * rho * v_ms**2  # Pa/m
    dP_tot = dP_pa_m * L_m

    return {
        "v_ms": v_ms,
        "Re": Re,
        "regime": "Laminare" if Re < 2300 else "Turbolento",
        "f_darcy": f,
        "dP_Pa_m": dP_pa_m,
        "dP_Pa_tot": dP_tot,
        "Dh_mm": Dh_mm,
        "A_m2": A_m2,
    }


def dimensiona_condotta_circolare(Q_m3h: float, v_max_ms: float = 8.0) -> dict:
    """
    Diametro minimo di condotta circolare per velocità massima consigliata.
    v_max: 6-8 m/s condotte principali, 4-6 m/s distribuzione, 2-4 m/s terminali
    """
    if Q_m3h <= 0 or v_max_ms <= 0:
        raise ValueError("Q e v_max devono essere > 0.")
    Q_m3s = Q_m3h / 3600.0
    D_m = math.sqrt(4.0 * Q_m3s / (math.pi * v_max_ms))
    D_mm = D_m * 1000.0
    # DN normalizzati condotte circolari [mm]
    _dn = [100, 125, 150, 160, 200, 250, 315, 355, 400, 450, 500, 560, 630, 710, 800, 900, 1000, 1120, 1250]
    D_norm = next((d for d in _dn if d >= D_mm), _dn[-1])
    return {
        "D_min_mm": D_mm,
        "D_normalizzato_mm": D_norm,
        "v_effettiva_ms": Q_m3s / (math.pi * (D_norm / 1000.0)**2 / 4.0),
    }


def dimensiona_condotta_rettangolare(Q_m3h: float, rapporto_lati: float = 1.5,
                                      v_max_ms: float = 8.0) -> dict:
    """
    Sezione rettangolare con rapporto lati = b/a (≥1).
    A = Q/v → a = √(A/rapporto), b = rapporto·a
    """
    if Q_m3h <= 0 or v_max_ms <= 0:
        raise ValueError("Q e v_max devono essere > 0.")
    if rapporto_lati < 1.0:
        raise ValueError("rapporto_lati deve essere ≥ 1.")

    Q_m3s = Q_m3h / 3600.0
    A_m2 = Q_m3s / v_max_ms
    a_m = math.sqrt(A_m2 / rapporto_lati)
    b_m = rapporto_lati * a_m

    # Arrotonda ai 50 mm superiori
    a_mm = math.ceil(a_m * 1000.0 / 50.0) * 50.0
    b_mm = math.ceil(b_m * 1000.0 / 50.0) * 50.0
    Dh = diametro_idraulico_rettangolare(a_mm, b_mm)
    A_adott = a_mm * b_mm / 1e6
    v_eff = Q_m3s / A_adott

    return {
        "a_mm": a_mm,
        "b_mm": b_mm,
        "Dh_mm": Dh,
        "A_m2": A_adott,
        "v_effettiva_ms": v_eff,
        "rapporto_lati": b_mm / a_mm,
    }


VELOCITA_RACCOMANDATE_MS = {
    "Condotta principale (mandata/ripresa)": {"min": 6.0, "max": 8.0},
    "Condotta di distribuzione":             {"min": 4.0, "max": 6.0},
    "Condotta terminale / diramazione":      {"min": 2.0, "max": 4.0},
    "Plenum / cassette VAV":                 {"min": 1.0, "max": 2.5},
    "Uffici (rumorosità contenuta)":         {"min": 2.0, "max": 4.0},
    "Industria / locali tecnici":            {"min": 6.0, "max": 10.0},
}
