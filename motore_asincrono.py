# ==============================================================================
# motore_asincrono.py — Motore asincrono trifase (induzione)
# Riferimenti: IEC 60034-1, IEC 60034-30 (classi IE), formula di Kloss
# ==============================================================================

import math


# ------------------------------------------------------------------------------
# Velocità sincrona standard
# ------------------------------------------------------------------------------

_VELOCITA_SINCRONE = {1: 3000, 2: 1500, 3: 1000, 4: 750, 6: 500}


def velocita_sincrona(poli: int, f_hz: float = 50.0) -> float:
    """n_sync = 60·f/p   dove p = poli/2"""
    if poli not in (2, 4, 6, 8, 10, 12):
        raise ValueError("Numero di poli deve essere pari e tra 2 e 12.")
    if f_hz <= 0:
        raise ValueError("La frequenza deve essere > 0 Hz.")
    return 60.0 * f_hz / (poli / 2)


# ------------------------------------------------------------------------------
# Dati di targa → grandezze derivate
# ------------------------------------------------------------------------------

def da_targa(
    P_kw: float,
    n_rpm: float,
    V_v: float,
    cos_phi: float,
    eta_pct: float,
    poli: int = 4,
    f_hz: float = 50.0,
    lambda_max: float = 2.5,
    k_spunto: float = 6.0,
) -> dict:
    """
    Calcola grandezze elettriche e meccaniche dal dato di targa.

    Parametri
    ----------
    P_kw      : potenza nominale all'albero [kW]
    n_rpm     : velocità nominale [RPM]
    V_v       : tensione di linea [V]
    cos_phi   : fattore di potenza nominale
    eta_pct   : rendimento nominale [%]
    poli      : numero di poli
    f_hz      : frequenza di rete [Hz]
    lambda_max: sovraccaricabilità (T_max/T_n), tipico 2-3.5
    k_spunto  : rapporto corrente di spunto / corrente nominale, tipico 5-8
    """
    if P_kw <= 0:
        raise ValueError("La potenza deve essere > 0 kW.")
    if n_rpm <= 0:
        raise ValueError("La velocità deve essere > 0 RPM.")
    if not 0 < cos_phi <= 1:
        raise ValueError("cos_phi deve essere tra 0 e 1.")
    if not 0 < eta_pct <= 100:
        raise ValueError("Il rendimento deve essere tra 0 e 100%.")
    if lambda_max <= 1:
        raise ValueError("La sovraccaricabilità deve essere > 1.")
    if k_spunto <= 0:
        raise ValueError("Il rapporto di spunto deve essere > 0.")

    n_sync = velocita_sincrona(poli, f_hz)
    s_n    = (n_sync - n_rpm) / n_sync                         # scorrimento nominale
    omega_n = 2.0 * math.pi * n_rpm / 60.0
    T_n    = (P_kw * 1000.0) / omega_n                        # coppia nominale [N·m]
    P_in_w = (P_kw * 1000.0) / (eta_pct / 100.0)             # potenza assorbita dalla rete [W]
    eta    = eta_pct / 100.0
    I_n    = P_in_w / (math.sqrt(3) * V_v * cos_phi)          # corrente nominale [A]
    Q_n    = P_in_w * math.tan(math.acos(cos_phi))            # potenza reattiva [VAR]
    S_n    = P_in_w / cos_phi                                  # potenza apparente [VA]

    # Coppia massima e scorrimento critico (modello di Kloss)
    T_max  = lambda_max * T_n
    s_cr   = s_n * (lambda_max + math.sqrt(lambda_max**2 - 1.0))

    # Corrente di spunto
    I_sp   = k_spunto * I_n

    return {
        "n_sync_rpm":    n_sync,
        "s_n":           s_n,
        "s_n_pct":       s_n * 100.0,
        "T_n_nm":        T_n,
        "T_max_nm":      T_max,
        "s_cr":          s_cr,
        "s_cr_pct":      s_cr * 100.0,
        "P_in_kW":       P_in_w / 1000.0,
        "I_n_A":         I_n,
        "I_sp_A":        I_sp,
        "Q_n_kVAR":      Q_n / 1000.0,
        "S_n_kVA":       S_n / 1000.0,
        "eta":           eta,
        "cos_phi":       cos_phi,
        "perdite_kW":    (P_in_w - P_kw * 1000.0) / 1000.0,
    }


# ------------------------------------------------------------------------------
# Caratteristica meccanica T-n (formula di Kloss)
# ------------------------------------------------------------------------------

def caratteristica_tn(
    T_n_nm: float,
    n_sync_rpm: float,
    s_n: float,
    lambda_max: float = 2.5,
    n_punti: int = 60,
) -> dict:
    """
    Genera la curva coppia-velocità con la formula di Kloss.
    T/T_cr = 2 / (s/s_cr + s_cr/s)

    Ritorna liste (n_rpm, T_nm) per il grafico.
    """
    if T_n_nm <= 0 or n_sync_rpm <= 0 or s_n <= 0:
        raise ValueError("Tutti i parametri devono essere > 0.")

    T_cr = lambda_max * T_n_nm
    s_cr = s_n * (lambda_max + math.sqrt(lambda_max**2 - 1.0))

    s_vals = [i / n_punti for i in range(1, n_punti + 1)]
    n_vals, T_vals = [], []

    for s in s_vals:
        T = T_cr * 2.0 / (s / s_cr + s_cr / s)
        n_vals.append(n_sync_rpm * (1.0 - s))
        T_vals.append(T)

    return {
        "n_rpm":      n_vals,
        "T_nm":       T_vals,
        "T_cr_nm":    T_cr,
        "s_cr":       s_cr,
        "n_cr_rpm":   n_sync_rpm * (1.0 - s_cr),
        "T_n_nm":     T_n_nm,
        "s_n":        s_n,
    }


# ------------------------------------------------------------------------------
# Coppia a scorrimento arbitrario (Kloss)
# ------------------------------------------------------------------------------

def coppia_a_scorrimento(s: float, T_n_nm: float, s_n: float, lambda_max: float) -> float:
    """Restituisce la coppia [N·m] per un dato scorrimento s."""
    if s <= 0:
        return 0.0
    T_cr = lambda_max * T_n_nm
    s_cr = s_n * (lambda_max + math.sqrt(max(0.0, lambda_max**2 - 1.0)))
    return T_cr * 2.0 / (s / s_cr + s_cr / s)


# ------------------------------------------------------------------------------
# Classi di efficienza IE (IEC 60034-30-1:2014)
# Valori di rendimento nominale a 50 Hz, 4 poli, tipici per kW indicati
# ------------------------------------------------------------------------------

_IE_ETA = {
    # (kW): {IE1, IE2, IE3, IE4}   (valori percentuali approssimati)
    0.75:  (72.1, 77.4, 80.7, 82.5),
    1.1:   (75.0, 79.6, 82.7, 84.5),
    1.5:   (77.2, 81.3, 84.2, 86.0),
    2.2:   (79.7, 83.2, 85.9, 87.7),
    3.0:   (81.5, 84.6, 87.1, 88.9),
    4.0:   (83.1, 85.8, 88.1, 89.8),
    5.5:   (84.7, 87.0, 89.2, 90.9),
    7.5:   (86.0, 88.1, 90.1, 91.7),
    11.0:  (87.6, 89.4, 91.2, 92.8),
    15.0:  (88.7, 90.3, 91.9, 93.3),
    18.5:  (89.3, 90.9, 92.4, 93.7),
    22.0:  (89.9, 91.3, 92.7, 94.0),
    30.0:  (90.7, 92.0, 93.2, 94.5),
    37.0:  (91.2, 92.5, 93.6, 94.8),
    45.0:  (91.7, 92.9, 94.0, 95.0),
    55.0:  (92.1, 93.2, 94.3, 95.3),
    75.0:  (92.7, 93.8, 94.7, 95.6),
    90.0:  (93.0, 94.1, 95.0, 95.8),
    110.0: (93.3, 94.3, 95.2, 96.0),
    132.0: (93.5, 94.6, 95.4, 96.2),
    160.0: (93.8, 94.8, 95.6, 96.4),
    200.0: (94.0, 95.0, 95.8, 96.5),
    250.0: (94.3, 95.2, 96.0, 96.7),
    315.0: (94.5, 95.4, 96.1, 96.9),
}


def classe_ie_eta(P_kw: float, classe: str) -> float:
    """
    Restituisce il rendimento nominale tipico per la classe IE indicata.
    P_kw : potenza nominale [kW] (sceglie il valore più vicino in tabella)
    classe: 'IE1' | 'IE2' | 'IE3' | 'IE4'
    """
    idx = {"IE1": 0, "IE2": 1, "IE3": 2, "IE4": 3}
    if classe not in idx:
        raise ValueError(f"Classe non valida: '{classe}'. Usa IE1, IE2, IE3 o IE4.")
    chiave = min(_IE_ETA.keys(), key=lambda k: abs(k - P_kw))
    return _IE_ETA[chiave][idx[classe]]


def confronto_classi_ie(P_kw: float, ore_anno: float = 8000.0, costo_kwh: float = 0.15) -> dict:
    """
    Confronta il costo energetico annuo tra classi IE1/IE2/IE3/IE4.

    Parametri
    ----------
    P_kw      : potenza nominale [kW]
    ore_anno  : ore di funzionamento annue
    costo_kwh : costo energia [€/kWh]
    """
    chiave = min(_IE_ETA.keys(), key=lambda k: abs(k - P_kw))
    risultati = {}
    for cl, i in {"IE1": 0, "IE2": 1, "IE3": 2, "IE4": 3}.items():
        eta    = _IE_ETA[chiave][i] / 100.0
        P_in   = P_kw / eta
        E_anno = P_in * ore_anno
        costo  = E_anno * costo_kwh
        risultati[cl] = {
            "eta_pct":     _IE_ETA[chiave][i],
            "P_in_kW":     P_in,
            "E_anno_kWh":  E_anno,
            "costo_euro":  costo,
        }

    # Risparmio IE3 vs IE1
    r_ie1 = risultati["IE1"]["costo_euro"]
    for cl in ("IE2", "IE3", "IE4"):
        risultati[cl]["risparmio_vs_IE1"] = r_ie1 - risultati[cl]["costo_euro"]

    return risultati
