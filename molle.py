# ==============================================================================
# molle.py — Dimensionamento molle meccaniche
# Riferimenti: teoria classica delle molle elicoidali (Shigley)
# ==============================================================================

import math


def molla_compressione(d_filo_mm: float, D_medio_mm: float, n_spire_attive: float,
                        G_MPa: float = 79300.0) -> dict:
    """
    Costante elastica e geometria di una molla elicoidale a compressione/trazione.

    k = (G * d^4) / (8 * D^3 * n)

    Parametri
    ----------
    d_filo_mm     : diametro del filo [mm]
    D_medio_mm    : diametro medio della spira [mm]
    n_spire_attive: numero di spire attive
    G_MPa         : modulo di elasticità tangenziale del materiale [MPa] (79300 per acciaio armonico)
    """
    if d_filo_mm <= 0 or D_medio_mm <= 0 or n_spire_attive <= 0:
        raise ValueError("d, D e n devono essere > 0.")

    C = D_medio_mm / d_filo_mm  # indice della molla
    k_N_mm = (G_MPa * d_filo_mm**4) / (8.0 * D_medio_mm**3 * n_spire_attive)

    return {
        "k_N_mm": k_N_mm,
        "k_N_m": k_N_mm * 1000.0,
        "indice_molla_C": C,
        "G_MPa": G_MPa,
    }


def tensione_torsionale_molla(F_N: float, d_filo_mm: float, D_medio_mm: float) -> dict:
    """
    Tensione di taglio massima nel filo (con fattore correttivo di Wahl per curvatura).

    tau = Kw * (8*F*D) / (pi*d^3)
    Kw = (4C-1)/(4C-4) + 0.615/C   (fattore di Wahl)
    """
    if F_N <= 0 or d_filo_mm <= 0 or D_medio_mm <= 0:
        raise ValueError("F, d e D devono essere > 0.")

    C = D_medio_mm / d_filo_mm
    if C <= 1:
        raise ValueError("L'indice della molla (D/d) deve essere > 1.")

    Kw = (4.0 * C - 1.0) / (4.0 * C - 4.0) + 0.615 / C
    tau_MPa = Kw * (8.0 * F_N * D_medio_mm) / (math.pi * d_filo_mm**3)

    return {
        "tau_MPa": tau_MPa,
        "Kw_wahl": Kw,
        "indice_molla_C": C,
    }


def frequenza_naturale_molla(k_N_mm: float, massa_kg: float) -> dict:
    """
    Frequenza naturale del sistema molla-massa (oscillatore semplice).

    f = (1/2pi) * sqrt(k/m)
    """
    if k_N_mm <= 0 or massa_kg <= 0:
        raise ValueError("k e massa devono essere > 0.")

    k_N_m = k_N_mm * 1000.0
    omega = math.sqrt(k_N_m / massa_kg)
    f_Hz = omega / (2.0 * math.pi)

    return {
        "f_Hz": f_Hz,
        "omega_rad_s": omega,
    }


def molla_torsione(d_filo_mm: float, D_medio_mm: float, n_spire_attive: float,
                    E_MPa: float = 200000.0) -> dict:
    """
    Costante elastica angolare di una molla di torsione (a bracci).

    k_theta = (E * d^4) / (64 * D * n)   [N*mm/rad]
    """
    if d_filo_mm <= 0 or D_medio_mm <= 0 or n_spire_attive <= 0:
        raise ValueError("d, D e n devono essere > 0.")

    k_theta = (E_MPa * d_filo_mm**4) / (64.0 * D_medio_mm * n_spire_attive)

    return {
        "k_theta_Nmm_rad": k_theta,
        "k_theta_Nmm_grad": k_theta * math.pi / 180.0,
        "E_MPa": E_MPa,
    }


MATERIALI_MOLLE = {
    "Acciaio armonico (G=79300 MPa)":      79300.0,
    "Acciaio inox AISI 302 (G=69000 MPa)": 69000.0,
    "Acciaio per molle Cr-V (G=78000 MPa)": 78000.0,
    "Bronzo fosforoso (G=41000 MPa)":      41000.0,
}
