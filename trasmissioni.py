# ==============================================================================
# trasmissioni.py — Trasmissioni meccaniche: ingranaggi, cinghie, catene
# Riferimenti: ISO 6336, ISO 10823, DIN 3990
# ==============================================================================

import math


# ------------------------------------------------------------------------------
# 1. Trasmissione semplice (un solo stadio)
# ------------------------------------------------------------------------------

def calcola_trasmissione(
    n1_rpm: float,
    T1_nm: float,
    i: float,
    eta: float = 0.97,
) -> dict:
    """
    Calcola velocità, coppia e potenza in uscita per una trasmissione a un stadio.

    Parametri
    ----------
    n1_rpm : velocità ingresso [RPM]
    T1_nm  : coppia ingresso [N·m]
    i      : rapporto di trasmissione (i = n1/n2 = z2/z1 per ingranaggi,
             i = d2/d1 per cinghie/catene)
    eta    : rendimento meccanico [-]

    Ritorna
    -------
    dict con n2, T2, P_in, P_out, omega1, omega2
    """
    if n1_rpm <= 0:
        raise ValueError("La velocità di ingresso deve essere > 0 RPM.")
    if T1_nm < 0:
        raise ValueError("La coppia di ingresso non può essere negativa.")
    if i <= 0:
        raise ValueError("Il rapporto di trasmissione deve essere > 0.")
    if not 0 < eta <= 1:
        raise ValueError("Il rendimento deve essere compreso tra 0 e 1.")

    omega1 = 2.0 * math.pi * n1_rpm / 60.0
    P_in   = T1_nm * omega1

    n2_rpm = n1_rpm / i
    omega2 = 2.0 * math.pi * n2_rpm / 60.0
    T2_nm  = T1_nm * i * eta
    P_out  = T2_nm * omega2

    return {
        "n1_rpm":  n1_rpm,
        "n2_rpm":  n2_rpm,
        "T1_nm":   T1_nm,
        "T2_nm":   T2_nm,
        "P_in_kW": P_in  / 1000.0,
        "P_out_kW":P_out / 1000.0,
        "omega1":  omega1,
        "omega2":  omega2,
        "i":       i,
        "eta":     eta,
        "perdita_kW": (P_in - P_out) / 1000.0,
    }


# ------------------------------------------------------------------------------
# 2. Riduttore a più stadi
# ------------------------------------------------------------------------------

def calcola_riduttore_multistadio(
    n_in_rpm: float,
    T_in_nm: float,
    stadi: list,
) -> dict:
    """
    Calcola il comportamento di un riduttore a più stadi in cascata.

    Parametri
    ----------
    n_in_rpm : velocità albero ingresso [RPM]
    T_in_nm  : coppia albero ingresso [N·m]
    stadi    : lista di dict  [{"i": ..., "eta": ...}, ...]
               i   = rapporto di trasmissione dello stadio
               eta = rendimento dello stadio (default 0.97)

    Ritorna
    -------
    dict con i_tot, eta_tot, n_out, T_out, P_in, P_out e dettagli per stadio
    """
    if not stadi:
        raise ValueError("Specificare almeno uno stadio.")
    if n_in_rpm <= 0:
        raise ValueError("La velocità di ingresso deve essere > 0 RPM.")
    if T_in_nm < 0:
        raise ValueError("La coppia di ingresso non può essere negativa.")

    i_tot   = 1.0
    eta_tot = 1.0
    n       = n_in_rpm
    T       = T_in_nm
    dettagli = []

    for k, stadio in enumerate(stadi):
        i_s   = stadio.get("i",   2.0)
        eta_s = stadio.get("eta", 0.97)
        if i_s <= 0:
            raise ValueError(f"Rapporto stadio {k+1} deve essere > 0.")
        if not 0 < eta_s <= 1:
            raise ValueError(f"Rendimento stadio {k+1} deve essere tra 0 e 1.")

        n_out  = n / i_s
        T_out  = T * i_s * eta_s
        omega  = 2.0 * math.pi * n / 60.0
        P_in_s = T * omega

        dettagli.append({
            "stadio":    k + 1,
            "i":         i_s,
            "eta":       eta_s,
            "n_in_rpm":  n,
            "n_out_rpm": n_out,
            "T_in_nm":   T,
            "T_out_nm":  T_out,
            "P_in_kW":   P_in_s / 1000.0,
        })
        i_tot   *= i_s
        eta_tot *= eta_s
        n = n_out
        T = T_out

    omega_in  = 2.0 * math.pi * n_in_rpm / 60.0
    omega_out = 2.0 * math.pi * n / 60.0
    P_in      = T_in_nm * omega_in
    P_out     = T * omega_out

    return {
        "i_tot":      i_tot,
        "eta_tot":    eta_tot,
        "n_out_rpm":  n,
        "T_out_nm":   T,
        "P_in_kW":    P_in  / 1000.0,
        "P_out_kW":   P_out / 1000.0,
        "perdita_kW": (P_in - P_out) / 1000.0,
        "stadi":      dettagli,
    }


# ------------------------------------------------------------------------------
# 3. Geometria cinghia trapezoidale / piatta
# ------------------------------------------------------------------------------

def calcola_geometria_cinghia(
    d1_mm: float,
    d2_mm: float,
    C_mm: float,
) -> dict:
    """
    Calcola la geometria di una trasmissione a cinghia (pulegge aperte).

    Parametri
    ----------
    d1_mm : diametro primitivo puleggia motrice [mm]
    d2_mm : diametro primitivo puleggia condotta [mm]
    C_mm  : interasse tra centri [mm]

    Ritorna
    -------
    dict con lunghezza cinghia, angolo di avvolgimento, rapporto di trasmissione
    """
    if d1_mm <= 0 or d2_mm <= 0:
        raise ValueError("I diametri delle pulegge devono essere > 0 mm.")
    if C_mm <= (d1_mm + d2_mm) / 2.0:
        raise ValueError("L'interasse è troppo piccolo rispetto alle pulegge.")

    i = d2_mm / d1_mm

    # Lunghezza cinghia aperta: L = 2C + π(d1+d2)/2 + (d2-d1)²/(4C)
    L_mm = (2.0 * C_mm
            + math.pi * (d1_mm + d2_mm) / 2.0
            + (d2_mm - d1_mm)**2 / (4.0 * C_mm))

    # Angolo di avvolgimento sulla puleggia piccola [rad] e [°]
    sin_alpha = (d2_mm - d1_mm) / (2.0 * C_mm)
    sin_alpha = max(-1.0, min(1.0, sin_alpha))
    alpha_rad = math.pi - 2.0 * math.asin(sin_alpha)
    alpha_deg = math.degrees(alpha_rad)

    # Angolo di avvolgimento sulla puleggia grande
    beta_deg  = 360.0 - alpha_deg

    return {
        "i":             i,
        "L_cinghia_mm":  L_mm,
        "alpha_piccola_deg": alpha_deg,
        "alpha_grande_deg":  beta_deg,
        "interasse_mm":  C_mm,
    }


# ------------------------------------------------------------------------------
# 4. Potenza, coppia e velocità: conversioni rapide
# ------------------------------------------------------------------------------

def converti_ptc(
    grandezza_nota: str,
    val1: float,
    val2: float,
) -> dict:
    """
    Calcola la terza grandezza tra Potenza [kW], Coppia [N·m], Velocità [RPM].

    Parametri
    ----------
    grandezza_nota : 'P_T'  → fornisce P [kW] e T [N·m], calcola n [RPM]
                     'P_n'  → fornisce P [kW] e n [RPM], calcola T [N·m]
                     'T_n'  → fornisce T [N·m] e n [RPM], calcola P [kW]
    val1, val2 : i due valori noti (nell'ordine indicato nel nome)
    """
    if val1 <= 0 or val2 <= 0:
        raise ValueError("I valori devono essere positivi.")

    if grandezza_nota == "P_T":
        P_w = val1 * 1000.0
        T   = val2
        omega = P_w / T
        n = omega * 60.0 / (2.0 * math.pi)
        return {"P_kW": val1, "T_nm": T, "n_rpm": n, "omega_rad_s": omega}
    elif grandezza_nota == "P_n":
        P_w = val1 * 1000.0
        n   = val2
        omega = 2.0 * math.pi * n / 60.0
        T = P_w / omega
        return {"P_kW": val1, "T_nm": T, "n_rpm": n, "omega_rad_s": omega}
    elif grandezza_nota == "T_n":
        T = val1
        n = val2
        omega = 2.0 * math.pi * n / 60.0
        P_w = T * omega
        return {"P_kW": P_w / 1000.0, "T_nm": T, "n_rpm": n, "omega_rad_s": omega}
    else:
        raise ValueError(f"Grandezza non riconosciuta: '{grandezza_nota}'.")
