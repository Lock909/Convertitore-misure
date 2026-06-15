# ==============================================================================
# pneumatica.py — Calcoli aria compressa industriale
# Riferimenti: ISO 1217, ISO 6358, EN 983
# Condizioni normali (N): 1.01325 bar, 20°C (293.15 K) — ISO 1217
# ==============================================================================

import math

_P0_BAR  = 1.01325   # bar assoluti (pressione atmosferica standard)
_T0_K    = 293.15    # K (20°C — condizioni normali ISO 1217)
_RHO0    = 1.204     # kg/m³ — densità aria a 20°C, 1 atm
_MU_AIR  = 1.81e-5   # Pa·s — viscosità dinamica aria (20°C)


# ------------------------------------------------------------------------------
# 1. Conversione portata normalizzata ↔ portata reale a pressione di lavoro
# ------------------------------------------------------------------------------

def converti_portata(Qn_nl_min: float, P_bar_g: float, T_C: float = 20.0) -> dict:
    """
    Converte portata normalizzata [Nl/min] in portata reale [l/min] alla
    pressione e temperatura di lavoro, e viceversa.

    Parametri
    ----------
    Qn_nl_min : portata normalizzata [Nl/min]  (condizioni ISO: 1 atm, 20°C)
    P_bar_g   : pressione manometrica di lavoro [bar g]
    T_C       : temperatura di lavoro [°C]

    Ritorna
    -------
    dict con Qr (portata reale), P_abs, rapporto di espansione, portata in m³/h
    """
    if Qn_nl_min < 0:
        raise ValueError("La portata normalizzata non può essere negativa.")
    if P_bar_g < 0:
        raise ValueError("La pressione manometrica non può essere negativa.")

    P_abs = P_bar_g + _P0_BAR          # bar assoluti
    T_K   = T_C + 273.15

    # Legge dei gas: Qr = Qn × (P0/P_abs) × (T/T0)
    rapporto = (_P0_BAR / P_abs) * (T_K / _T0_K)
    Qr_l_min = Qn_nl_min * rapporto

    return {
        "Qn_nl_min":   Qn_nl_min,
        "Qr_l_min":    Qr_l_min,
        "Qn_m3h":      Qn_nl_min * 60.0 / 1000.0,
        "Qr_m3h":      Qr_l_min  * 60.0 / 1000.0,
        "P_abs_bar":   P_abs,
        "T_K":         T_K,
        "rapporto_esp": rapporto,
    }


# ------------------------------------------------------------------------------
# 2. Caduta di pressione in tubazione (Darcy-Weisbach + Colebrook-White)
# ------------------------------------------------------------------------------

def _friction_factor(Re: float, rugosita_rel: float) -> float:
    """Fattore d'attrito di Darcy-Weisbach con Colebrook-White (iterativo)."""
    if Re < 2300:
        return 64.0 / Re  # laminare
    # Approssimazione Swamee-Jain (esplicita, errore < 3%)
    return 0.25 / (math.log10(rugosita_rel / 3.7 + 5.74 / Re**0.9))**2


def caduta_pressione_tubazione(
    Qn_nl_min: float,
    L_m: float,
    D_mm: float,
    P_bar_g: float,
    T_C: float = 20.0,
    rugosita_mm: float = 0.046,
) -> dict:
    """
    Calcola la caduta di pressione in una tubazione di aria compressa.
    Metodo: Darcy-Weisbach con densità corretta alla pressione di lavoro.

    Parametri
    ----------
    Qn_nl_min   : portata normalizzata [Nl/min]
    L_m         : lunghezza tubazione [m]
    D_mm        : diametro interno [mm]
    P_bar_g     : pressione manometrica di ingresso [bar g]
    T_C         : temperatura aria [°C]
    rugosita_mm : rugosità assoluta parete [mm] (acciaio: 0.046, inox: 0.015)
    """
    if Qn_nl_min <= 0:
        raise ValueError("La portata deve essere > 0 Nl/min.")
    if L_m <= 0:
        raise ValueError("La lunghezza deve essere > 0 m.")
    if D_mm <= 0:
        raise ValueError("Il diametro deve essere > 0 mm.")
    if P_bar_g < 0:
        raise ValueError("La pressione manometrica non può essere negativa.")

    P_abs = (P_bar_g + _P0_BAR) * 1e5   # Pa assoluti
    T_K   = T_C + 273.15
    D_m   = D_mm / 1000.0
    A     = math.pi * D_m**2 / 4.0

    # Densità aria alla pressione di lavoro (gas ideale)
    rho = _RHO0 * (P_abs / (_P0_BAR * 1e5)) * (_T0_K / T_K)

    # Portata volumetrica reale [m³/s]
    Qr_m3s = (Qn_nl_min / 1000.0 / 60.0) * (_P0_BAR * 1e5 / P_abs) * (T_K / _T0_K)

    v   = Qr_m3s / A                          # velocità media [m/s]
    Re  = rho * v * D_m / _MU_AIR
    eps = rugosita_mm / D_mm                  # rugosità relativa
    lam = _friction_factor(Re, eps)

    dP_pa  = lam * (L_m / D_m) * (rho * v**2 / 2.0)
    dP_bar = dP_pa / 1e5
    dP_mbar = dP_bar * 1000.0
    dP_pct  = (dP_bar / (P_bar_g + _P0_BAR)) * 100.0

    return {
        "dP_bar":     dP_bar,
        "dP_mbar":    dP_mbar,
        "dP_pct":     dP_pct,
        "velocita_ms": v,
        "Re":         Re,
        "lambda":     lam,
        "rho_kg_m3":  rho,
    }


# ------------------------------------------------------------------------------
# 3. Dimensionamento serbatoio aria compressa
# ------------------------------------------------------------------------------

def dimensiona_serbatoio(
    Qc_nl_min: float,
    t_s: float,
    P_max_bar_g: float,
    P_min_bar_g: float,
) -> dict:
    """
    Calcola il volume minimo del serbatoio per garantire autonomia durante
    la fase di scarica (compressore fermo).

    Formula: V = Qc × t × P0 / (ΔP × 60)

    Parametri
    ----------
    Qc_nl_min   : consumo utenze [Nl/min]
    t_s         : tempo di autonomia richiesto [s]
    P_max_bar_g : pressione massima serbatoio [bar g]
    P_min_bar_g : pressione minima di servizio [bar g]
    """
    if Qc_nl_min <= 0:
        raise ValueError("Il consumo deve essere > 0 Nl/min.")
    if t_s <= 0:
        raise ValueError("Il tempo di autonomia deve essere > 0 s.")
    if P_max_bar_g <= P_min_bar_g:
        raise ValueError("P_max deve essere maggiore di P_min.")
    if P_min_bar_g < 0:
        raise ValueError("La pressione minima non può essere negativa.")

    delta_P = P_max_bar_g - P_min_bar_g
    # V [litri] = Qc[Nl/min] × t[s] × P0[bar] / (ΔP[bar] × 60)
    V_l = (Qc_nl_min * t_s * _P0_BAR) / (delta_P * 60.0)

    # Pressione in bar assoluti per ciclo compressore
    P_max_abs = P_max_bar_g + _P0_BAR
    P_min_abs = P_min_bar_g + _P0_BAR

    return {
        "V_litri":     V_l,
        "V_m3":        V_l / 1000.0,
        "delta_P_bar": delta_P,
        "P_max_abs":   P_max_abs,
        "P_min_abs":   P_min_abs,
    }


# ------------------------------------------------------------------------------
# 4. Potenza assorbita dal compressore (compressione politropica)
# ------------------------------------------------------------------------------

def potenza_compressore(
    Qn_nl_min: float,
    P1_bar_g: float,
    P2_bar_g: float,
    eta_tot: float = 0.75,
    n_stadi: int = 1,
) -> dict:
    """
    Stima la potenza assorbita da un compressore alternativo/a vite.
    Modello: compressione adiabatica (γ = 1.4 per aria) con rendimento globale.

    Parametri
    ----------
    Qn_nl_min : portata erogata in condizioni normali [Nl/min]
    P1_bar_g  : pressione di aspirazione [bar g]
    P2_bar_g  : pressione di mandata [bar g]
    eta_tot   : rendimento globale compressore [-] (tipico 0.65-0.85)
    n_stadi   : numero di stadi di compressione (1 o 2)
    """
    if Qn_nl_min <= 0:
        raise ValueError("La portata deve essere > 0 Nl/min.")
    if P2_bar_g <= P1_bar_g:
        raise ValueError("La pressione di mandata deve essere > quella di aspirazione.")
    if not 0 < eta_tot <= 1:
        raise ValueError("Il rendimento deve essere compreso tra 0 e 1.")
    if n_stadi not in (1, 2):
        raise ValueError("Il numero di stadi deve essere 1 o 2.")

    gamma = 1.4
    P1_abs = (P1_bar_g + _P0_BAR) * 1e5   # Pa
    P2_abs = (P2_bar_g + _P0_BAR) * 1e5

    Qn_m3s = Qn_nl_min / 1000.0 / 60.0

    # Rapporto di compressione per stadio
    beta_tot = P2_abs / P1_abs
    beta = beta_tot ** (1.0 / n_stadi)

    # Potenza ideale adiabatica per stadio
    esp = (gamma - 1.0) / gamma
    P_id_stadio = (gamma / (gamma - 1.0)) * P1_abs * Qn_m3s * (beta**esp - 1.0)
    P_id_tot = P_id_stadio * n_stadi

    P_assorbita = P_id_tot / eta_tot

    # Stima temperatura uscita (compressione adiabatica)
    T_in_K = _T0_K
    T_out_K = T_in_K * beta**esp

    return {
        "P_kW":         P_assorbita / 1000.0,
        "P_id_kW":      P_id_tot / 1000.0,
        "beta_tot":     beta_tot,
        "beta_stadio":  beta,
        "T_out_C":      T_out_K - 273.15,
        "eta_tot":      eta_tot,
        "n_stadi":      n_stadi,
    }
