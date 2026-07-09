# ==============================================================================
# misuratori_portata.py — Misuratori di portata industriali
# Diaframma tarato (ISO 5167-2), misuratore a turbina (K-factor) e
# elettromagnetico (da velocità), con verifica di Reynolds e velocità
# consigliata.
# ==============================================================================

import math

VELOCITA_CONSIGLIATA_MS = {
    "acqua":                 (1.0, 3.0),
    "vapore_saturo":         (15.0, 25.0),
    "vapore_surriscaldato":  (20.0, 40.0),
    "aria_gas_compressi":    (8.0, 15.0),
    "olio_liquidi_viscosi":  (0.5, 1.5),
}


def portata_diaframma_iso5167(
    dP_mbar: float,
    D_mm: float,
    beta: float,
    rho_kgm3: float,
    C: float = 0.6,
    eps: float = 1.0,
) -> dict:
    """
    Portata attraverso un diaframma tarato a spigolo vivo (ISO 5167-2).

    Q = C / sqrt(1 - beta^4) * eps * (pi/4) * d^2 * sqrt(2*dP / rho)

    Parametri
    ----------
    dP_mbar : caduta di pressione misurata ai presa del diaframma [mbar]
    D_mm    : diametro interno della tubazione [mm]
    beta    : rapporto diametri d/D (0.1-0.75 per campo di validità ISO 5167)
    rho_kgm3: densità del fluido [kg/m³]
    C       : coefficiente di efflusso (tipico 0.6-0.62)
    eps     : fattore di espansione (1.0 per liquidi incomprimibili)
    """
    if dP_mbar <= 0:
        raise ValueError("La caduta di pressione deve essere > 0 mbar.")
    if D_mm <= 0:
        raise ValueError("Il diametro della tubazione deve essere > 0 mm.")
    if not 0.1 <= beta <= 0.75:
        raise ValueError("beta deve essere nel campo di validità ISO 5167 (0.1-0.75).")
    if rho_kgm3 <= 0:
        raise ValueError("La densità deve essere > 0 kg/m³.")
    if C <= 0 or eps <= 0:
        raise ValueError("C ed eps devono essere > 0.")

    D_m = D_mm / 1000.0
    d_m = beta * D_m
    dP_pa = dP_mbar * 100.0  # 1 mbar = 100 Pa

    Q_m3s = C / math.sqrt(1 - beta**4) * eps * (math.pi / 4.0) * d_m**2 * math.sqrt(2 * dP_pa / rho_kgm3)
    Q_m3h = Q_m3s * 3600.0
    v_ms = Q_m3s / (math.pi / 4.0 * D_m**2)

    return {
        "Q_m3h": Q_m3h,
        "Q_kgh": Q_m3h * rho_kgm3,
        "v_ms": v_ms,
        "d_foro_mm": d_m * 1000.0,
        "D_mm": D_mm,
        "beta": beta,
        "dP_mbar": dP_mbar,
    }


def portata_turbina(freq_Hz: float, k_factor_imp_l: float) -> dict:
    """
    Portata da misuratore a turbina, noto il K-factor del costruttore.

    Q [L/min] = freq_Hz * 60 / K_factor   (K_factor tipico 100-1000 imp/L)
    """
    if freq_Hz <= 0:
        raise ValueError("La frequenza degli impulsi deve essere > 0 Hz.")
    if k_factor_imp_l <= 0:
        raise ValueError("Il K-factor deve essere > 0 impulsi/litro.")

    Q_lmin = freq_Hz * 60.0 / k_factor_imp_l
    Q_m3h = Q_lmin * 60.0 / 1000.0

    return {
        "Q_lmin": Q_lmin,
        "Q_m3h": Q_m3h,
        "freq_Hz": freq_Hz,
        "k_factor_imp_l": k_factor_imp_l,
    }


def portata_elettromagnetico(v_ms: float, D_mm: float) -> dict:
    """
    Portata da misuratore elettromagnetico, nota la velocità media misurata.

    Q = v * A,  A = (pi/4) * D^2
    """
    if v_ms <= 0:
        raise ValueError("La velocità deve essere > 0 m/s.")
    if D_mm <= 0:
        raise ValueError("Il diametro della tubazione deve essere > 0 mm.")

    D_m = D_mm / 1000.0
    A_m2 = math.pi / 4.0 * D_m**2
    Q_m3s = v_ms * A_m2
    Q_m3h = Q_m3s * 3600.0

    return {
        "Q_m3h": Q_m3h,
        "Q_m3s": Q_m3s,
        "A_m2": A_m2,
        "v_ms": v_ms,
        "D_mm": D_mm,
    }


def numero_reynolds(v_ms: float, D_mm: float, rho_kgm3: float, mu_Pas: float) -> dict:
    """
    Numero di Reynolds in tubazione: Re = rho * v * D / mu.
    """
    if v_ms <= 0:
        raise ValueError("La velocità deve essere > 0 m/s.")
    if D_mm <= 0:
        raise ValueError("Il diametro deve essere > 0 mm.")
    if rho_kgm3 <= 0:
        raise ValueError("La densità deve essere > 0 kg/m³.")
    if mu_Pas <= 0:
        raise ValueError("La viscosità dinamica deve essere > 0 Pa·s.")

    D_m = D_mm / 1000.0
    Re = rho_kgm3 * v_ms * D_m / mu_Pas
    regime = "laminare" if Re < 2300 else ("transitorio" if Re < 4000 else "turbolento")

    return {
        "Re": Re,
        "regime": regime,
        "valido_iso5167": Re >= 5000,
    }


def verifica_velocita_consigliata(v_ms: float, tipo_fluido: str = "acqua") -> dict:
    """
    Confronta la velocità con il campo indicativo tipico di buona pratica
    impiantistica per il fluido dato (per limitare perdite di carico, erosione
    e rumore).
    """
    if v_ms <= 0:
        raise ValueError("La velocità deve essere > 0 m/s.")
    if tipo_fluido not in VELOCITA_CONSIGLIATA_MS:
        raise ValueError(f"Tipo fluido non riconosciuto. Valori validi: {list(VELOCITA_CONSIGLIATA_MS.keys())}")

    v_min, v_max = VELOCITA_CONSIGLIATA_MS[tipo_fluido]
    nel_range = v_min <= v_ms <= v_max

    return {
        "nel_range": nel_range,
        "v_min_ms": v_min,
        "v_max_ms": v_max,
        "v_ms": v_ms,
        "tipo_fluido": tipo_fluido,
    }


def valuta_diaframma(
    dP_mbar: float,
    D_mm: float,
    beta: float,
    rho_kgm3: float,
    mu_Pas: float,
    C: float = 0.6,
    eps: float = 1.0,
    tipo_fluido: str = "acqua",
) -> dict:
    """Valutazione completa di un diaframma tarato: portata, numero di
    Reynolds (con verifica di validità ISO 5167) e confronto con la velocità
    consigliata per il fluido."""
    base = portata_diaframma_iso5167(dP_mbar, D_mm, beta, rho_kgm3, C, eps)
    re = numero_reynolds(base["v_ms"], D_mm, rho_kgm3, mu_Pas)
    vel = verifica_velocita_consigliata(base["v_ms"], tipo_fluido)

    risultato = {}
    risultato.update(base)
    risultato.update(re)
    risultato.update(vel)
    return risultato
