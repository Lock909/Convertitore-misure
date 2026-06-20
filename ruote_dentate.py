# ==============================================================================
# ruote_dentate.py — Dimensionamento ingranaggi cilindrici a denti dritti
# Riferimenti: formula di Lewis, AGMA/ISO 6336 (semplificata)
# ==============================================================================

import math


def geometria_ruota(modulo_mm: float, n_denti: int, angolo_pressione_deg: float = 20.0) -> dict:
    """
    Geometria di base di una ruota dentata a denti dritti normalizzata.

    d = m * z   (diametro primitivo)
    """
    if modulo_mm <= 0 or n_denti <= 0:
        raise ValueError("Modulo e numero denti devono essere > 0.")

    d_primitivo_mm = modulo_mm * n_denti
    d_esterno_mm   = d_primitivo_mm + 2.0 * modulo_mm
    d_interno_mm   = d_primitivo_mm - 2.5 * modulo_mm
    passo_mm       = math.pi * modulo_mm

    return {
        "d_primitivo_mm": d_primitivo_mm,
        "d_esterno_mm":   d_esterno_mm,
        "d_interno_mm":   d_interno_mm,
        "passo_mm":       passo_mm,
        "angolo_pressione_deg": angolo_pressione_deg,
    }


def modulo_minimo_lewis(coppia_Nm: float, n_denti: int, b_m_rapporto: float,
                         sigma_amm_MPa: float, Y_lewis: float = 0.35, Kv: float = 1.2) -> dict:
    """
    Modulo minimo richiesto secondo l'equazione di Lewis (verifica a flessione).

    sigma = (Ft * Kv) / (b * m * Y) <= sigma_amm
    con Ft = 2000 * T / (m * z)   e b = b_m_rapporto * m  (rapporto larghezza/modulo, tipico 8-12)

    Risolvendo per m: m^2 >= (2000 * T * Kv) / (z * b_m_rapporto * Y * sigma_amm)

    Parametri
    ----------
    coppia_Nm     : coppia trasmessa dalla ruota [N*m]
    n_denti       : numero di denti della ruota
    b_m_rapporto  : rapporto larghezza di fascia / modulo (tipico 8-12)
    sigma_amm_MPa : tensione ammissibile a flessione del materiale [MPa]
    Y_lewis       : fattore di forma di Lewis (tipico 0.30-0.40 per denti normali)
    Kv            : fattore dinamico (1.0 statico, 1.2-1.5 dinamico)
    """
    if coppia_Nm <= 0 or n_denti <= 0 or b_m_rapporto <= 0 or sigma_amm_MPa <= 0:
        raise ValueError("Tutti i parametri devono essere > 0.")

    T_Nmm = coppia_Nm * 1000.0
    # Ft = 2T/(m*z), b = b_m_rapporto*m, sigma = Ft*Kv/(b*m*Y) => risolvendo per m:
    m_min_mm = math.sqrt((2.0 * T_Nmm * Kv) / (n_denti * b_m_rapporto * Y_lewis * sigma_amm_MPa))

    return {
        "m_minimo_mm": m_min_mm,
        "Ft_stimata_N": 2.0 * T_Nmm / (m_min_mm * n_denti),
        "Y_lewis": Y_lewis,
        "Kv": Kv,
    }


def verifica_flessione_lewis(coppia_Nm: float, modulo_mm: float, n_denti: int, b_mm: float,
                              Y_lewis: float = 0.35, Kv: float = 1.2) -> dict:
    """
    Verifica a flessione (equazione di Lewis) per una ruota dentata di geometria nota.

    Ft = 2*T / (m*z)        (forza tangenziale sul diametro primitivo)
    sigma = (Ft * Kv) / (b * m * Y)
    """
    if coppia_Nm <= 0 or modulo_mm <= 0 or n_denti <= 0 or b_mm <= 0:
        raise ValueError("Tutti i parametri devono essere > 0.")

    T_Nmm = coppia_Nm * 1000.0
    d_primitivo_mm = modulo_mm * n_denti
    Ft_N = 2.0 * T_Nmm / d_primitivo_mm
    sigma_MPa = (Ft_N * Kv) / (b_mm * modulo_mm * Y_lewis)

    return {
        "Ft_N": Ft_N,
        "sigma_flessione_MPa": sigma_MPa,
        "d_primitivo_mm": d_primitivo_mm,
    }


def rapporto_trasmissione_ruote(z1: int, z2: int) -> dict:
    """
    Rapporto di trasmissione tra due ruote dentate in presa.
    """
    if z1 <= 0 or z2 <= 0:
        raise ValueError("Il numero di denti deve essere > 0.")

    tau = z2 / z1
    return {
        "tau": tau,
        "riduzione": tau > 1,
        "z1": z1,
        "z2": z2,
    }


FATTORI_LEWIS_Y = {
    "12 denti": 0.245,
    "14 denti": 0.277,
    "17 denti": 0.308,
    "20 denti": 0.332,
    "24 denti": 0.337,
    "30 denti": 0.358,
    "40 denti": 0.378,
    "60 denti": 0.398,
    "100 denti": 0.422,
    "Cremagliera (infiniti denti)": 0.484,
}
