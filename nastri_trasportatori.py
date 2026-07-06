# ==============================================================================
# nastri_trasportatori.py — Calcolo nastri trasportatori industriali
# Riferimenti: ISO 5048, DIN 22101
# ==============================================================================

import math

_G = 9.80665


def portata_massica(
    B_m: float,
    v_ms: float,
    rho_bulk_kg_m3: float,
    angolo_surcharge_deg: float = 20.0,
    inclinazione_deg: float = 0.0,
) -> dict:
    """
    Capacità di trasporto di un nastro trasportatore.

    Parametri
    ----------
    B_m                : larghezza nastro [m]
    v_ms               : velocità nastro [m/s]
    rho_bulk_kg_m3     : densità apparente del materiale [kg/m³]
    angolo_surcharge_deg : angolo di accumulo del materiale [°] (tipico 15-30°)
    inclinazione_deg   : inclinazione del nastro [°]
    """
    if B_m <= 0 or v_ms <= 0 or rho_bulk_kg_m3 <= 0:
        raise ValueError("B, v e ρ devono essere > 0.")

    # Sezione trasversale approssimata (metodo empirico DIN 22101)
    # A ≈ 0.16 · B²  per nastro piatto con 3 rulli portanti
    b_eff = 0.9 * B_m - 0.05        # larghezza utile [m]
    tan_s = math.tan(math.radians(angolo_surcharge_deg))
    A_m2  = (b_eff**2 / 6.0) * tan_s + b_eff * b_eff * 0.25   # sezione carico

    Q_m3h = A_m2 * v_ms * 3600.0
    Q_th  = Q_m3h * rho_bulk_kg_m3 / 1000.0    # [t/h]

    # Riduzione per inclinazione
    if inclinazione_deg > 0:
        corr = math.cos(math.radians(inclinazione_deg))
        Q_th_eff = Q_th * corr
    else:
        Q_th_eff = Q_th

    return {
        "Q_m3h":    Q_m3h,
        "Q_th":     Q_th,
        "Q_th_eff": Q_th_eff,
        "A_m2":     A_m2,
        "b_eff_m":  b_eff,
    }


def potenza_motore(
    Q_th: float,
    L_m: float,
    H_m: float = 0.0,
    eta_trasmissione: float = 0.85,
    f_attrito: float = 0.022,
    massa_nastro_kg_m: float = None,
) -> dict:
    """
    Potenza motore necessaria (ISO 5048, metodo semplificato).

    Parametri
    ----------
    Q_th              : portata [t/h]
    L_m               : lunghezza orizzontale nastro [m]
    H_m               : dislivello [m]  (positivo = salita)
    eta_trasmissione  : rendimento riduttore + pulegge [-]
    f_attrito         : coefficiente di attrito rulli (tipico 0.018-0.030)
    massa_nastro_kg_m : massa nastro [kg/m] (None = stima da larghezza)
    """
    if Q_th <= 0 or L_m <= 0:
        raise ValueError("Q e L devono essere > 0.")

    Q_kg_s = Q_th * 1000.0 / 3600.0    # [kg/s]

    # Potenza di sollevamento
    P_sollevamento = Q_kg_s * _G * H_m if H_m > 0 else 0.0

    # Potenza per attrito materiale
    P_materiale = f_attrito * Q_kg_s * _G * L_m

    # Potenza per nastro (stima)
    m_nas = massa_nastro_kg_m if massa_nastro_kg_m else Q_th * 0.3   # stima empirica
    P_nastro = f_attrito * m_nas * _G * L_m

    P_utile  = P_sollevamento + P_materiale + P_nastro
    P_motore = P_utile / eta_trasmissione

    return {
        "P_motore_W":      P_motore,
        "P_motore_kW":     P_motore / 1000.0,
        "P_utile_W":       P_utile,
        "P_sollevamento_W": P_sollevamento,
        "P_materiale_W":   P_materiale,
        "P_nastro_W":      P_nastro,
        "eta":             eta_trasmissione,
    }


def tensione_nastro(P_motore_W: float, v_ms: float, D_puleggia_mm: float = None) -> dict:
    """
    Forza periferica e tensione del nastro.

    F = P / v     (forza periferica sulla puleggia motrice)
    """
    if P_motore_W <= 0 or v_ms <= 0:
        raise ValueError("P e v devono essere > 0.")

    F_N    = P_motore_W / v_ms
    T_stret = F_N * 2.0          # tensione lato teso (rapporto 2:1 stima)
    T_molla = F_N                 # tensione lato molle

    result = {
        "F_periferica_N": F_N,
        "T_stretto_N":    T_stret,
        "T_molle_N":      T_molla,
        "v_ms":           v_ms,
    }
    if D_puleggia_mm:
        T_coppia = F_N * (D_puleggia_mm / 2000.0)
        result["coppia_Nm"] = T_coppia
    return result


def angolo_max_inclinazione(rho_bulk_kg_m3: float, tipo: str = "secco") -> dict:
    """Angolo massimo di inclinazione per materiale non scivoloso."""
    angoli = {
        "secco":      {"tipico": 18, "max": 22},
        "umido":      {"tipico": 22, "max": 28},
        "granuloso":  {"tipico": 15, "max": 18},
        "polveri":    {"tipico": 12, "max": 16},
    }
    if tipo not in angoli:
        raise ValueError(f"Tipo non valido. Scegli tra: {list(angoli.keys())}")
    a = angoli[tipo]
    return {
        "angolo_tipico_deg": a["tipico"],
        "angolo_max_deg":    a["max"],
        "tipo_materiale":    tipo,
        "note": "Superare l'angolo max causa scivolamento del materiale sul nastro.",
    }
