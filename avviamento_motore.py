# ==============================================================================
# avviamento_motore.py — Avviamento motore asincrono trifase
# Riferimenti: IEC 60034-12, IEC 60947-4
# ==============================================================================

import math

# Fattori di spunto tipici per classe di avviamento (IEC 60034-12)
CLASSI_AVVIAMENTO = {
    "N (standard)":   {"Ia_In": 6.0, "Ma_Mn": 1.5, "descrizione": "Avviamento normale, rete rigida"},
    "H (spunto alto)": {"Ia_In": 8.0, "Ma_Mn": 1.8, "descrizione": "Pompe, compressori a coppia variabile"},
    "Sd (ridotto)":   {"Ia_In": 4.0, "Ma_Mn": 0.9, "descrizione": "Stella-triangolo o soft-starter"},
    "IE3 (EFF1)":     {"Ia_In": 7.0, "Ma_Mn": 2.0, "descrizione": "Alta efficienza, spunto più elevato"},
}

# Rendimento e cos_phi tipici per classe IE (IEC 60034-30)
RENDIMENTO_COSPHI_IE = {
    "IE1": {"eta": 0.88, "cos_phi": 0.82},
    "IE2": {"eta": 0.91, "cos_phi": 0.84},
    "IE3": {"eta": 0.93, "cos_phi": 0.86},
    "IE4": {"eta": 0.95, "cos_phi": 0.87},
}


def correnti_motore(P_kW: float, V_V: float = 400.0, cos_phi: float = 0.85,
                    eta: float = 0.92, Ia_In: float = 6.0) -> dict:
    """
    Corrente nominale e di avviamento di un motore asincrono trifase.

    I_n = P / (√3 · V · cos_phi · η)
    I_a = Ia_In · I_n
    """
    if P_kW <= 0 or V_V <= 0:
        raise ValueError("P e V devono essere > 0.")
    if not (0.0 < cos_phi <= 1.0) or not (0.0 < eta <= 1.0):
        raise ValueError("cos_phi e eta devono essere in (0, 1].")

    I_n = P_kW * 1000.0 / (math.sqrt(3.0) * V_V * cos_phi * eta)
    I_a = Ia_In * I_n
    S_kVA = math.sqrt(3.0) * V_V * I_n / 1000.0

    return {
        "I_nominale_A": I_n,
        "I_avviamento_A": I_a,
        "Ia_In": Ia_In,
        "S_nominale_kVA": S_kVA,
        "I_termica_A": I_n * 1.15,  # set protezione termica tipicamente +15%
    }


def coppia_motore(P_kW: float, n_rpm: float, Ma_Mn: float = 1.5) -> dict:
    """
    Coppia nominale e di avviamento.

    M_n = P / ω = P * 60 / (2π · n)
    M_a = Ma_Mn · M_n
    """
    if P_kW <= 0 or n_rpm <= 0:
        raise ValueError("P e n devono essere > 0.")

    omega = 2.0 * math.pi * n_rpm / 60.0
    M_n = P_kW * 1000.0 / omega
    M_a = Ma_Mn * M_n

    return {
        "M_nominale_Nm": M_n,
        "M_avviamento_Nm": M_a,
        "Ma_Mn": Ma_Mn,
        "omega_rad_s": omega,
    }


def caduta_tensione_avviamento(I_avv_A: float, Z_rete_mohm: float,
                                V_nom_V: float = 400.0) -> dict:
    """
    Caduta di tensione sulla rete durante lo spunto.

    ΔV% = √3 · I_a · Z_rete / V_nom · 100

    Z_rete_mohm : impedenza di rete vista dal punto di allacciamento [mΩ]
    Limite tipico: ΔV ≤ 10% (IEC 60034-12)
    """
    if I_avv_A <= 0 or Z_rete_mohm <= 0:
        raise ValueError("I_avv e Z_rete devono essere > 0.")

    Z_ohm = Z_rete_mohm / 1000.0
    dV_V = math.sqrt(3.0) * I_avv_A * Z_ohm
    dV_pct = dV_V / V_nom_V * 100.0

    return {
        "dV_V": dV_V,
        "dV_pct": dV_pct,
        "ammissibile": dV_pct <= 10.0,
        "giudizio": "ΔV ≤ 10% — avviamento diretto ammissibile" if dV_pct <= 10.0
                    else "ΔV > 10% — considerare riduttore di spunto (Y-Δ, soft-starter, inverter)",
    }


def metodi_avviamento(P_kW: float, V_V: float = 400.0, cos_phi: float = 0.85,
                       eta: float = 0.92) -> dict:
    """
    Tabella comparativa dei principali metodi di avviamento con correnti e coppie ridotte.
    """
    base = correnti_motore(P_kW, V_V, cos_phi, eta, Ia_In=6.0)
    I_n = base["I_nominale_A"]
    I_a_dir = base["I_avviamento_A"]

    risultati = {
        "Diretto (DOL)": {
            "I_avviamento_A": I_a_dir,
            "fattore_corrente": 6.0,
            "fattore_coppia": 1.0,
            "note": "Piena corrente e coppia",
        },
        "Stella-Triangolo (Y-Δ)": {
            "I_avviamento_A": I_a_dir / 3.0,
            "fattore_corrente": 2.0,
            "fattore_coppia": 1.0 / 3.0,
            "note": "Corrente e coppia ridotte a 1/3 — solo per carichi a bassa resistenza",
        },
        "Soft-starter": {
            "I_avviamento_A": I_n * 3.0,
            "fattore_corrente": 3.0,
            "fattore_coppia": 0.5,
            "note": "Corrente ~3×I_n regolabile — coppia proporzionale a V²",
        },
        "Inverter (VFD)": {
            "I_avviamento_A": I_n * 1.5,
            "fattore_corrente": 1.5,
            "fattore_coppia": 1.0,
            "note": "Minima corrente di spunto — coppia piena disponibile fin da zero",
        },
    }

    return {
        "I_nominale_A": I_n,
        "I_avviamento_diretto_A": I_a_dir,
        "metodi": risultati,
    }
