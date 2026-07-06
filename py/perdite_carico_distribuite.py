# ==============================================================================
# perdite_carico_distribuite.py — Perdite di carico distribuite (Darcy-Weisbach)
# Completa perdite_carico.py (che gestisce le perdite concentrate/localizzate)
# ==============================================================================

import math

_G = 9.80665


def fattore_attrito_swamee_jain(Re: float, rugosita_relativa: float) -> dict:
    """
    Fattore di attrito di Darcy secondo la correlazione esplicita di Swamee-Jain
    (approssima Colebrook-White, valida per 5000 < Re < 1e8, 1e-6 < eps/D < 0.05).
    """
    if Re <= 0:
        raise ValueError("Re deve essere > 0.")

    if Re < 2300:
        # regime laminare
        f = 64.0 / Re
        regime = "Laminare"
    else:
        if rugosita_relativa <= 0:
            raise ValueError("La rugosità relativa deve essere > 0 in regime turbolento.")
        f = 0.25 / (math.log10(rugosita_relativa / 3.7 + 5.74 / Re**0.9))**2
        regime = "Turbolento"

    return {
        "f_darcy": f,
        "regime": regime,
        "Re": Re,
    }


def numero_reynolds(v_ms: float, D_mm: float, nu_m2_s: float = 1.0e-6) -> dict:
    """
    Numero di Reynolds per flusso in tubazione circolare.

    Re = v*D / nu

    nu_m2_s : viscosità cinematica del fluido [m²/s] (1e-6 per acqua a 20°C)
    """
    if v_ms <= 0 or D_mm <= 0 or nu_m2_s <= 0:
        raise ValueError("v, D e nu devono essere > 0.")

    D_m = D_mm / 1000.0
    Re = v_ms * D_m / nu_m2_s

    return {"Re": Re, "D_m": D_m}


def perdita_distribuita(Q_m3h: float, D_mm: float, L_m: float, rugosita_mm: float = 0.045,
                         nu_m2_s: float = 1.0e-6, rho_kg_m3: float = 1000.0) -> dict:
    """
    Perdita di carico distribuita lungo una tubazione (equazione di Darcy-Weisbach).

    h = f * (L/D) * (v^2 / 2g)
    dP = rho * g * h

    Parametri
    ----------
    Q_m3h       : portata volumetrica [m³/h]
    D_mm        : diametro interno tubazione [mm]
    L_m         : lunghezza tubazione [m]
    rugosita_mm : rugosità assoluta del materiale [mm] (0.045 per acciaio commerciale nuovo)
    nu_m2_s     : viscosità cinematica del fluido [m²/s]
    rho_kg_m3   : densità del fluido [kg/m³]
    """
    if Q_m3h <= 0 or D_mm <= 0 or L_m <= 0:
        raise ValueError("Q, D e L devono essere > 0.")

    D_m = D_mm / 1000.0
    A_m2 = math.pi * D_m**2 / 4.0
    Q_m3s = Q_m3h / 3600.0
    v_ms = Q_m3s / A_m2

    re_res = numero_reynolds(v_ms, D_mm, nu_m2_s)
    eps_rel = (rugosita_mm / 1000.0) / D_m
    f_res = fattore_attrito_swamee_jain(re_res["Re"], eps_rel)

    h_m = f_res["f_darcy"] * (L_m / D_m) * (v_ms**2 / (2.0 * _G))
    dP_Pa = rho_kg_m3 * _G * h_m

    return {
        "v_ms": v_ms,
        "Re": re_res["Re"],
        "regime": f_res["regime"],
        "f_darcy": f_res["f_darcy"],
        "h_perdita_m": h_m,
        "dP_Pa": dP_Pa,
        "dP_bar": dP_Pa / 1.0e5,
        "dP_kPa": dP_Pa / 1000.0,
    }


def diametro_da_velocita_max(Q_m3h: float, v_max_ms: float = 2.0) -> dict:
    """
    Diametro minimo per non superare una velocità massima consigliata (criterio di pre-dimensionamento).
    """
    if Q_m3h <= 0 or v_max_ms <= 0:
        raise ValueError("Q e v_max devono essere > 0.")

    Q_m3s = Q_m3h / 3600.0
    D_m = math.sqrt(4.0 * Q_m3s / (math.pi * v_max_ms))

    return {
        "D_minimo_mm": D_m * 1000.0,
        "v_max_ms": v_max_ms,
    }


RUGOSITA_MATERIALI_MM = {
    "Acciaio commerciale nuovo":   0.045,
    "Acciaio commerciale usato":   0.15,
    "Acciaio zincato":             0.15,
    "Ghisa nuova":                 0.26,
    "Ghisa usata/incrostata":      1.5,
    "PVC / PE (plastica)":         0.0015,
    "Rame":                        0.0015,
    "Calcestruzzo":                0.3,
    "Acciaio inox":                0.015,
}
