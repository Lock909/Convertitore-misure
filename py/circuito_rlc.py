# ==============================================================================
# circuito_rlc.py — Circuiti RLC serie e parallelo
# ==============================================================================

import math


def impedenza_serie(R: float, L_H: float, C_F: float, f: float) -> dict:
    """
    Impedenza di un circuito RLC serie.

    Parametri
    ----------
    R   : resistenza [Ω]
    L_H : induttanza [H]   (0 = assente)
    C_F : capacità [F]     (0 = assente)
    f   : frequenza [Hz]
    """
    if f <= 0:
        raise ValueError("La frequenza deve essere > 0 Hz.")
    if R < 0 or L_H < 0 or C_F < 0:
        raise ValueError("R, L, C non possono essere negativi.")

    omega = 2.0 * math.pi * f
    X_L   = omega * L_H
    X_C   = 1.0 / (omega * C_F) if C_F > 0 else 0.0
    X_net = X_L - X_C
    Z     = math.sqrt(R**2 + X_net**2)
    phi   = math.atan2(X_net, R) if Z > 0 else 0.0

    return {
        "Z_ohm":    Z,
        "phi_rad":  phi,
        "phi_deg":  math.degrees(phi),
        "X_L_ohm":  X_L,
        "X_C_ohm":  X_C,
        "X_net_ohm": X_net,
        "R_ohm":    R,
        "cos_phi":  math.cos(phi),
        "tipo":     "Induttivo" if X_net > 0 else ("Capacitivo" if X_net < 0 else "Resistivo puro"),
    }


def impedenza_parallelo(R: float, L_H: float, C_F: float, f: float) -> dict:
    """Impedenza di un circuito RLC parallelo."""
    if f <= 0:
        raise ValueError("La frequenza deve essere > 0 Hz.")

    omega = 2.0 * math.pi * f
    G     = 1.0 / R if R > 0 else float("inf")
    B_L   = 1.0 / (omega * L_H) if L_H > 0 else 0.0
    B_C   = omega * C_F
    B_net = B_C - B_L                   # suscettanza totale (cap. positiva)
    Y     = math.sqrt(G**2 + B_net**2)
    Z     = 1.0 / Y if Y > 0 else float("inf")
    phi   = -math.atan2(B_net, G)       # in parallelo il segno si inverte

    return {
        "Z_ohm":    Z,
        "Y_S":      Y,
        "phi_rad":  phi,
        "phi_deg":  math.degrees(phi),
        "B_L_S":    B_L,
        "B_C_S":    B_C,
        "B_net_S":  B_net,
        "tipo":     "Induttivo" if B_net < 0 else ("Capacitivo" if B_net > 0 else "Resistivo puro"),
    }


def risonanza_serie(L_H: float, C_F: float, R: float = 0.0) -> dict:
    """Frequenza di risonanza, fattore Q e larghezza di banda per RLC serie."""
    if L_H <= 0 or C_F <= 0:
        raise ValueError("L e C devono essere > 0.")
    f0    = 1.0 / (2.0 * math.pi * math.sqrt(L_H * C_F))
    omega0 = 2.0 * math.pi * f0
    Q     = omega0 * L_H / R if R > 0 else float("inf")
    BW    = f0 / Q if Q != float("inf") else 0.0
    f_low = f0 - BW / 2.0 if Q != float("inf") else f0
    f_high = f0 + BW / 2.0 if Q != float("inf") else f0
    return {
        "f0_Hz":    f0,
        "omega0":   omega0,
        "Q":        Q,
        "BW_Hz":    BW,
        "f_low_Hz": f_low,
        "f_high_Hz": f_high,
        "Z_min_ohm": R,
    }


def risonanza_parallelo(L_H: float, C_F: float, R: float = float("inf")) -> dict:
    """Frequenza di risonanza per RLC parallelo."""
    if L_H <= 0 or C_F <= 0:
        raise ValueError("L e C devono essere > 0.")
    f0 = 1.0 / (2.0 * math.pi * math.sqrt(L_H * C_F))
    omega0 = 2.0 * math.pi * f0
    Q  = R / (omega0 * L_H) if R != float("inf") else float("inf")
    BW = f0 / Q if Q != float("inf") else 0.0
    return {
        "f0_Hz":  f0,
        "omega0": omega0,
        "Q":      Q,
        "BW_Hz":  BW,
        "Z_max_ohm": R,
    }


def risposta_frequenza(
    R: float,
    L_H: float,
    C_F: float,
    f_min: float = 1.0,
    f_max: float = 100000.0,
    tipo: str = "serie",
    n_punti: int = 200,
) -> dict:
    """
    Risposta in frequenza (Z e φ) su scala logaritmica.

    Ritorna liste f_Hz, Z_ohm, phi_deg per il grafico.
    """
    import math as _m
    if f_min <= 0 or f_max <= f_min:
        raise ValueError("f_min deve essere > 0 e f_max > f_min.")
    log_min = _m.log10(f_min)
    log_max = _m.log10(f_max)
    f_arr   = [10 ** (log_min + i * (log_max - log_min) / n_punti) for i in range(n_punti + 1)]
    Z_arr, phi_arr = [], []
    fn = impedenza_serie if tipo == "serie" else impedenza_parallelo
    for f in f_arr:
        r = fn(R, L_H, C_F, f)
        Z_arr.append(r["Z_ohm"])
        phi_arr.append(r["phi_deg"])
    return {"f_Hz": f_arr, "Z_ohm": Z_arr, "phi_deg": phi_arr}
