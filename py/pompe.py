# ==============================================================================
# pompe.py — Calcoli idraulici per pompe centrifughe
# Riferimenti: ISO 9906, HI (Hydraulic Institute Standards)
# ==============================================================================

import math

_G = 9.80665   # m/s²


# ------------------------------------------------------------------------------
# 1. Punto di lavoro pompa (intersezione curva pompa / curva impianto)
#    Curva pompa (parabolica): H_p(Q) = H0 - k_p × Q²
#    Curva impianto:           H_i(Q) = H_st + k_i × Q²
#    Punto di lavoro:          H_p(Q*) = H_i(Q*)  → bisection
# ------------------------------------------------------------------------------

def _curva_pompa(Q: float, H0: float, k_p: float) -> float:
    return H0 - k_p * Q**2


def _curva_impianto(Q: float, H_st: float, k_i: float) -> float:
    return H_st + k_i * Q**2


def calcola_punto_lavoro(
    H0: float,
    Q_nom: float,
    H_nom: float,
    H_statica: float,
    Q_imp: float,
    H_imp: float,
) -> dict:
    """
    Calcola il punto di lavoro di una pompa centrifuga.

    La curva pompa è approssimata come parabola: H_p = H0 - k_p·Q²
    La curva impianto è: H_i = H_st + k_i·Q²

    Parametri
    ----------
    H0        : prevalenza a portata nulla (shutoff head) [m]
    Q_nom     : portata nominale [m³/h]
    H_nom     : prevalenza alla portata nominale [m]
    H_statica : prevalenza statica impianto [m]  (differenza quote + P_scarico-P_asp)
    Q_imp     : portata di riferimento impianto [m³/h]
    H_imp     : prevalenza di riferimento impianto (a Q_imp) [m]

    Ritorna
    -------
    dict con Q*, H*, e coefficienti delle curve
    """
    if H0 <= 0:
        raise ValueError("La prevalenza di chiusura H0 deve essere > 0 m.")
    if Q_nom <= 0 or H_nom <= 0:
        raise ValueError("Portata e prevalenza nominali devono essere > 0.")
    if H_nom >= H0:
        raise ValueError("H_nom deve essere minore di H0 (shutoff head).")
    if Q_imp <= 0 or H_imp <= H_statica:
        raise ValueError("Punto di riferimento impianto non valido.")

    k_p = (H0 - H_nom) / Q_nom**2
    k_i = (H_imp - H_statica) / Q_imp**2

    # Risoluzione analitica: H0 - k_p·Q² = H_st + k_i·Q²
    # Q*² = (H0 - H_st) / (k_p + k_i)
    delta = H0 - H_statica
    if delta <= 0:
        raise ValueError("La prevalenza statica è superiore alla prevalenza di chiusura: pompa inadeguata.")

    Q_star = math.sqrt(delta / (k_p + k_i))
    H_star = _curva_impianto(Q_star, H_statica, k_i)

    # Portata massima (H_pompa = 0)
    Q_max = math.sqrt(H0 / k_p) if k_p > 0 else float("inf")

    # Punti curva per il grafico (facoltativo, restituiti come liste)
    n_pts = 20
    Q_graf = [Q_max * k / n_pts for k in range(n_pts + 1)]
    H_p_graf = [max(0.0, _curva_pompa(q, H0, k_p)) for q in Q_graf]
    H_i_graf = [_curva_impianto(q, H_statica, k_i) for q in Q_graf]

    return {
        "Q_star_m3h":    Q_star,
        "H_star_m":      H_star,
        "k_pompa":       k_p,
        "k_impianto":    k_i,
        "Q_max_m3h":     Q_max,
        "H_statica_m":   H_statica,
        "Q_graf":        Q_graf,
        "H_pompa_graf":  H_p_graf,
        "H_imp_graf":    H_i_graf,
    }


# ------------------------------------------------------------------------------
# 2. Potenza idraulica e assorbita
# ------------------------------------------------------------------------------

def calcola_potenza_pompa(
    Q_m3h: float,
    H_m: float,
    eta_pompa: float,
    rho_kg_m3: float = 1000.0,
) -> dict:
    """
    Calcola la potenza idraulica e quella assorbita dalla pompa.

    Parametri
    ----------
    Q_m3h      : portata [m³/h]
    H_m        : prevalenza [m]
    eta_pompa  : rendimento idraulico-meccanico [-]
    rho_kg_m3  : densità fluido [kg/m³]
    """
    if Q_m3h <= 0:
        raise ValueError("La portata deve essere > 0 m³/h.")
    if H_m <= 0:
        raise ValueError("La prevalenza deve essere > 0 m.")
    if not 0 < eta_pompa <= 1:
        raise ValueError("Il rendimento deve essere compreso tra 0 e 1.")
    if rho_kg_m3 <= 0:
        raise ValueError("La densità deve essere > 0 kg/m³.")

    Q_m3s = Q_m3h / 3600.0
    P_id  = rho_kg_m3 * _G * Q_m3s * H_m   # W
    P_ass = P_id / eta_pompa

    return {
        "P_id_kW":   P_id  / 1000.0,
        "P_ass_kW":  P_ass / 1000.0,
        "Q_m3s":     Q_m3s,
        "eta":       eta_pompa,
        "perdita_kW":(P_ass - P_id) / 1000.0,
    }


# ------------------------------------------------------------------------------
# 3. NPSH disponibile
# ------------------------------------------------------------------------------

def calcola_npsh_disponibile(
    P_asp_bar_a: float,
    P_vap_bar_a: float,
    H_asp_m: float,
    v_asp_ms: float,
    perdite_asp_m: float,
) -> dict:
    """
    Calcola il Net Positive Suction Head disponibile (NPSHd).

    NPSHd = (P_asp - P_vap)/(ρ·g) + v²/(2g) - perdite_aspirazione

    Parametri
    ----------
    P_asp_bar_a   : pressione assoluta alla superficie del serbatoio di aspirazione [bar a]
    P_vap_bar_a   : pressione di vapore del fluido alla temperatura di lavoro [bar a]
    H_asp_m       : altezza geometrica di aspirazione [m] (positiva = pompa sopra serbatoio)
    v_asp_ms      : velocità nel condotto di aspirazione [m/s]
    perdite_asp_m : perdite di carico nel condotto di aspirazione [m]
    """
    if P_asp_bar_a <= 0:
        raise ValueError("La pressione di aspirazione deve essere > 0 bar a.")
    if P_vap_bar_a <= 0 or P_vap_bar_a >= P_asp_bar_a:
        raise ValueError("La pressione di vapore deve essere 0 < P_vap < P_asp.")
    if perdite_asp_m < 0:
        raise ValueError("Le perdite di aspirazione non possono essere negative.")

    rho   = 1000.0   # kg/m³ (acqua — adeguare per altri fluidi)
    P_asp = P_asp_bar_a * 1e5
    P_vap = P_vap_bar_a * 1e5

    NPSH_d = (P_asp - P_vap) / (rho * _G) - H_asp_m + v_asp_ms**2 / (2.0 * _G) - perdite_asp_m

    return {
        "NPSH_d_m":   NPSH_d,
        "P_asp_pa":   P_asp,
        "P_vap_pa":   P_vap,
        "termine_pressione_m": (P_asp - P_vap) / (rho * _G),
        "termine_velocita_m":  v_asp_ms**2 / (2.0 * _G),
        "avvertimento": "NPSH_d deve superare NPSH_r della pompa + margine ≥ 0.5 m" if NPSH_d > 0 else "NPSH_d NEGATIVO: rischio cavitazione certo.",
    }


# ------------------------------------------------------------------------------
# 4. Numero specifico di giri (ns) — classificazione tipo pompa
# ------------------------------------------------------------------------------

def calcola_ns(n_rpm: float, Q_m3s: float, H_m: float) -> dict:
    """
    Calcola il numero specifico di giri (ns) per classificare il tipo di pompa.
    ns = n · √Q / H^(3/4)    [giri specifici adimensionali per convenzione europea]

    Valori tipici:
      ns 10-30  → pompe centrifughe radiali (bassa portata, alta prevalenza)
      ns 30-80  → pompe centrifughe miste
      ns 80-300 → pompe centrifughe assiali (alta portata, bassa prevalenza)
    """
    if n_rpm <= 0 or Q_m3s <= 0 or H_m <= 0:
        raise ValueError("Tutti i parametri devono essere > 0.")

    ns = n_rpm * math.sqrt(Q_m3s) / H_m**(3.0 / 4.0)

    if ns < 30:
        tipo = "Centrifuga radiale (bassa portata, alta prevalenza)"
    elif ns < 80:
        tipo = "Centrifuga mista"
    else:
        tipo = "Centrifuga assiale / elica (alta portata, bassa prevalenza)"

    return {
        "ns":   ns,
        "tipo": tipo,
        "n_rpm": n_rpm,
        "Q_m3s": Q_m3s,
        "H_m":   H_m,
    }
