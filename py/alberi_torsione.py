# ==============================================================================
# alberi_torsione.py — Verifica alberi a torsione, flessione e fatica
# Riferimenti: ISO 281 (bearings), Shigley's (Goodman/Gerber)
# ==============================================================================

import math

MATERIALI_ALBERI = {
    "C45 (1.0503)":      {"Rm_MPa": 700, "Re_MPa": 490, "sigma_f_MPa": 350},
    "42CrMo4 (1.7225)":  {"Rm_MPa": 900, "Re_MPa": 700, "sigma_f_MPa": 450},
    "16MnCr5 (1.7131)":  {"Rm_MPa": 800, "Re_MPa": 600, "sigma_f_MPa": 400},
    "34CrNiMo6 (1.6582)":{"Rm_MPa": 1000,"Re_MPa": 800, "sigma_f_MPa": 500},
    "Acciaio C35":       {"Rm_MPa": 580, "Re_MPa": 360, "sigma_f_MPa": 290},
}


def momento_torcente(P_kW: float, n_rpm: float) -> dict:
    """Momento torcente da potenza e velocità."""
    if P_kW <= 0 or n_rpm <= 0:
        raise ValueError("P e n devono essere > 0.")
    Mt = P_kW * 1000.0 * 60.0 / (2.0 * math.pi * n_rpm)
    return {"Mt_Nm": Mt, "P_kW": P_kW, "n_rpm": n_rpm}


def diametro_minimo_torsione(Mt_Nm: float, tau_amm_MPa: float) -> dict:
    """
    Diametro minimo per solo torsione.

    tau = 16 · Mt / (π · d³)  →  d = (16·Mt / (π·tau_amm))^(1/3)
    """
    if Mt_Nm <= 0 or tau_amm_MPa <= 0:
        raise ValueError("Mt e tau_amm devono essere > 0.")
    d_m = (16.0 * Mt_Nm / (math.pi * tau_amm_MPa * 1e6)) ** (1.0 / 3.0)
    d_mm = d_m * 1000.0
    # Arrotonda al diametro normalizzato superiore (ISO 286)
    _std = [10, 12, 15, 17, 20, 22, 25, 28, 30, 32, 35, 38, 40, 42, 45, 48,
            50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 110, 120, 130, 140, 150]
    d_norm = next((s for s in _std if s >= d_mm), _std[-1])
    return {
        "d_min_mm": d_mm,
        "d_normalizzato_mm": d_norm,
        "tau_amm_MPa": tau_amm_MPa,
    }


def tensioni_albero(Mt_Nm: float, Mf_Nm: float, d_mm: float) -> dict:
    """
    Tensioni di torsione e flessione su sezione circolare piena.

    tau = 16·Mt / (π·d³)
    sigma = 32·Mf / (π·d³)
    sigma_eq (Von Mises) = √(sigma² + 3·tau²)
    """
    if d_mm <= 0:
        raise ValueError("d deve essere > 0.")
    d = d_mm / 1000.0
    Wt = math.pi * d**3 / 16.0  # modulo di resistenza torsionale
    Wf = math.pi * d**3 / 32.0  # modulo di resistenza flessionale

    tau_MPa = Mt_Nm / Wt / 1e6
    sigma_MPa = Mf_Nm / Wf / 1e6
    sigma_eq = math.sqrt(sigma_MPa**2 + 3.0 * tau_MPa**2)

    return {
        "tau_MPa": tau_MPa,
        "sigma_flessione_MPa": sigma_MPa,
        "sigma_eq_MPa": sigma_eq,
        "d_mm": d_mm,
    }


def fattore_sicurezza_statico(Mt_Nm: float, Mf_Nm: float, d_mm: float,
                               Re_MPa: float) -> dict:
    """
    Fattore di sicurezza statico (Von Mises) rispetto allo snervamento.
    """
    res = tensioni_albero(Mt_Nm, Mf_Nm, d_mm)
    n_s = Re_MPa / res["sigma_eq_MPa"] if res["sigma_eq_MPa"] > 0 else float("inf")
    return {
        **res,
        "Re_MPa": Re_MPa,
        "n_statico": n_s,
        "conforme": n_s >= 1.5,
        "giudizio": f"n = {n_s:.2f} — {'Conforme (≥ 1.5)' if n_s >= 1.5 else 'NON conforme'}",
    }


def verifica_goodman(sigma_m_MPa: float, sigma_a_MPa: float,
                      Rm_MPa: float, sigma_f_MPa: float) -> dict:
    """
    Diagramma di Goodman modificato (fatica a ciclo alterno con valor medio).

    n_Goodman:  1/n = sigma_a/sigma_f + sigma_m/Rm
    n_Gerber:   sigma_a/sigma_f + (sigma_m/Rm)² = 1/n_Gerber  (approx)

    sigma_f : limite di fatica a flessione rotante (≈ 0.5·Rm per acciaio)
    """
    if Rm_MPa <= 0 or sigma_f_MPa <= 0:
        raise ValueError("Rm e sigma_f devono essere > 0.")

    denom_gm = sigma_a_MPa / sigma_f_MPa + sigma_m_MPa / Rm_MPa
    n_goodman = (1.0 / denom_gm) if denom_gm > 0 else float("inf")

    # Gerber parabola: (sigma_a/sigma_f) + (sigma_m/Rm)² = 1
    A_gerber = sigma_a_MPa / sigma_f_MPa
    B_gerber = (sigma_m_MPa / Rm_MPa) ** 2
    n_gerber = (1.0 / (A_gerber + B_gerber)) if (A_gerber + B_gerber) > 0 else float("inf")

    return {
        "n_Goodman": n_goodman,
        "n_Gerber": n_gerber,
        "sigma_m_MPa": sigma_m_MPa,
        "sigma_a_MPa": sigma_a_MPa,
        "conforme_goodman": n_goodman >= 1.5,
        "giudizio": f"Goodman n={n_goodman:.2f}, Gerber n={n_gerber:.2f} — "
                    + ("Conforme (≥ 1.5)" if n_goodman >= 1.5 else "NON conforme — ridurre carichi o aumentare diametro"),
    }
