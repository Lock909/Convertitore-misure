# ==============================================================================
# serbatoi.py — Calcoli idraulici per serbatoi e vasche
# ==============================================================================

import math

_G = 9.80665   # m/s²


def volume_geometrico(forma: str, **dim) -> float:
    """
    Calcola il volume geometrico di un serbatoio.

    forme : 'cilindro_vert', 'cilindro_oriz', 'parallelepipedo', 'cono', 'sfera'
    dim   : parametri specifici per forma (in [m])
    """
    if forma == "cilindro_vert":
        D, H = dim["D_m"], dim["H_m"]
        return math.pi * D**2 / 4.0 * H
    elif forma == "cilindro_oriz":
        D, L = dim["D_m"], dim["L_m"]
        return math.pi * D**2 / 4.0 * L
    elif forma == "parallelepipedo":
        return dim["L_m"] * dim["W_m"] * dim["H_m"]
    elif forma == "cono":
        return math.pi * dim["D_m"]**2 / 4.0 * dim["H_m"] / 3.0
    elif forma == "sfera":
        return 4.0 / 3.0 * math.pi * (dim["D_m"] / 2.0)**3
    else:
        raise ValueError(f"Forma non riconosciuta: '{forma}'.")


def pressione_fondo(H_m: float, rho_kg_m3: float = 1000.0) -> dict:
    """Pressione idrostatica al fondo del serbatoio."""
    if H_m <= 0:
        raise ValueError("L'altezza deve essere > 0 m.")
    P_pa  = rho_kg_m3 * _G * H_m
    return {
        "P_Pa":   P_pa,
        "P_bar":  P_pa / 1e5,
        "P_kPa":  P_pa / 1000.0,
        "P_mca":  H_m,
        "H_m":    H_m,
    }


def portata_torricelli(
    H_m: float,
    D_foro_mm: float,
    Cd: float = 0.62,
    rho_kg_m3: float = 1000.0,
) -> dict:
    """
    Portata di scarico per gravità (legge di Torricelli).
    v = Cd · √(2gH)   Q = A · v

    Cd : coefficiente di efflusso (0.60-0.65 per orifizio affilato)
    """
    if H_m <= 0 or D_foro_mm <= 0:
        raise ValueError("H e D_foro devono essere > 0.")
    if not 0 < Cd <= 1:
        raise ValueError("Cd deve essere tra 0 e 1.")

    A_foro = math.pi * (D_foro_mm / 1000.0)**2 / 4.0
    v_ms   = Cd * math.sqrt(2.0 * _G * H_m)
    Q_m3s  = A_foro * v_ms
    Q_m3h  = Q_m3s * 3600.0
    Q_lmin = Q_m3s * 1000.0 * 60.0

    return {
        "v_ms":   v_ms,
        "Q_m3s":  Q_m3s,
        "Q_m3h":  Q_m3h,
        "Q_lmin": Q_lmin,
        "A_foro_m2": A_foro,
    }


def tempo_svuotamento(
    V_m3: float,
    H_m: float,
    D_foro_mm: float,
    Cd: float = 0.62,
    A_serbatoio_m2: float = None,
) -> dict:
    """
    Tempo di svuotamento con integrazione numerica (Torricelli variabile).
    Se A_serbatoio_m2 è None, il serbatoio è trattato come cilindrico verticale con V e H noti.

    Metodo: integrazione Eulero con 500 passi su H.
    """
    if V_m3 <= 0 or H_m <= 0 or D_foro_mm <= 0:
        raise ValueError("V, H e D_foro devono essere > 0.")

    A_ser = A_serbatoio_m2 if A_serbatoio_m2 else V_m3 / H_m
    A_for = math.pi * (D_foro_mm / 1000.0)**2 / 4.0
    n     = 500
    dt_step = 0.0
    h     = H_m
    t     = 0.0
    for _ in range(n * 10000):
        if h <= 0.001:
            break
        v  = Cd * math.sqrt(2.0 * _G * h)
        Q  = A_for * v
        dh = -Q / A_ser
        dt_calc = min(-h / dh * 0.01, 60.0)
        t  += dt_calc
        h  += dh * dt_calc
        if h < 0:
            h = 0.0

    return {
        "t_svuotamento_s":  t,
        "t_svuotamento_min": t / 60.0,
        "t_svuotamento_h":  t / 3600.0,
        "H_iniziale_m":     H_m,
        "V_iniziale_m3":    V_m3,
    }


def tempo_riempimento(V_m3: float, Q_m3h: float) -> dict:
    """Tempo di riempimento a portata costante."""
    if V_m3 <= 0 or Q_m3h <= 0:
        raise ValueError("V e Q devono essere > 0.")
    t_h   = V_m3 / Q_m3h
    return {
        "t_h":    t_h,
        "t_min":  t_h * 60.0,
        "t_s":    t_h * 3600.0,
        "V_m3":   V_m3,
        "Q_m3h":  Q_m3h,
    }
