# ==============================================================================
# batterie_litio.py — Curve di scarica reali per celle/pacchi Li-Ion
# ==============================================================================
#
# Modella la tensione di una cella Li-Ion (chimica NMC/NCA tipica) in funzione
# dello stato di carica (SOC), con caduta da resistenza interna e leggera
# riduzione di capacità effettiva alle correnti di scarica elevate (effetto
# Peukert, molto più contenuto che nel Pb-acido). Non sostituisce i dati di
# targa del costruttore: utile per stime e confronti tra C-rate.
# ==============================================================================

# Tabella OCV (tensione a circuito aperto) vs SOC per cella Li-Ion NMC/NCA, 25°C
# Valori tipici di letteratura — forma a "S" con ginocchi alle estremità.
_OCV_SOC_TABELLA = [
    (100, 4.20), (95, 4.10), (90, 4.03), (80, 3.93), (70, 3.87),
    (60, 3.82), (50, 3.78), (40, 3.73), (30, 3.68), (20, 3.60),
    (10, 3.45), (5, 3.30), (2, 3.15), (0, 3.00),
]


def ocv_per_soc(soc_pct: float) -> float:
    """Tensione a circuito aperto [V] di una cella Li-Ion per un dato SOC [%]
    (interpolazione lineare sulla tabella empirica)."""
    if soc_pct <= 0:
        return _OCV_SOC_TABELLA[-1][1]
    if soc_pct >= 100:
        return _OCV_SOC_TABELLA[0][1]
    for (soc_hi, v_hi), (soc_lo, v_lo) in zip(_OCV_SOC_TABELLA, _OCV_SOC_TABELLA[1:]):
        if soc_lo <= soc_pct <= soc_hi:
            frac = (soc_pct - soc_lo) / (soc_hi - soc_lo)
            return v_lo + frac * (v_hi - v_lo)
    return _OCV_SOC_TABELLA[-1][1]


def capacita_effettiva_ah(C_nom_Ah: float, c_rate: float, k_peukert: float = 1.05) -> float:
    """Capacità realmente disponibile a un dato C-rate (legge di Peukert).

    k_peukert tipico 1.02-1.10 per Li-Ion (effetto lieve, a differenza del
    Pb-acido dove k è tipicamente 1.2-1.4)."""
    if C_nom_Ah <= 0:
        raise ValueError("La capacità nominale deve essere > 0 Ah.")
    if c_rate <= 0:
        raise ValueError("Il C-rate deve essere > 0.")
    return C_nom_Ah / (c_rate ** (k_peukert - 1.0))


def curva_scarica(
    C_nom_Ah: float,
    c_rate: float = 1.0,
    n_celle_serie: int = 1,
    n_celle_parallelo: int = 1,
    R_int_cella_ohm: float = 0.02,
    soc_finale_pct: float = 0.0,
    k_peukert: float = 1.05,
    n_punti: int = 50,
) -> dict:
    """Genera la curva di scarica realistica tensione/tempo/capacità di un
    pacco Li-Ion (n_celle_serie in serie, n_celle_parallelo in parallelo).

    C_nom_Ah          : capacità nominale di un singolo ramo (1C) [Ah]
    c_rate            : corrente di scarica espressa in multipli di C
    R_int_cella_ohm   : resistenza interna di una cella [Ω]
    soc_finale_pct    : SOC di cutoff a fine scarica [%]
    """
    if n_celle_serie < 1 or n_celle_parallelo < 1:
        raise ValueError("Il numero di celle serie/parallelo deve essere almeno 1.")
    if not 0 <= soc_finale_pct < 100:
        raise ValueError("Il SOC finale deve essere tra 0 e 100% (escluso).")
    if R_int_cella_ohm < 0:
        raise ValueError("La resistenza interna non può essere negativa.")
    if n_punti < 2:
        raise ValueError("Il numero di punti deve essere almeno 2.")

    C_eff_ramo_Ah = capacita_effettiva_ah(C_nom_Ah, c_rate, k_peukert)
    I_per_cella_A = c_rate * C_nom_Ah
    I_pacco_A = I_per_cella_A * n_celle_parallelo
    t_pieno_h = C_eff_ramo_Ah / I_per_cella_A if I_per_cella_A > 0 else 0.0

    soc_step = (100.0 - soc_finale_pct) / (n_punti - 1)
    soc_pts, t_pts, v_pts, cap_pts = [], [], [], []
    for i in range(n_punti):
        soc = 100.0 - soc_step * i
        ocv = ocv_per_soc(soc)
        v_cella = max(0.0, ocv - I_per_cella_A * R_int_cella_ohm)
        v_pacco = v_cella * n_celle_serie
        t_h = (1.0 - soc / 100.0) * t_pieno_h
        cap_erogata = (1.0 - soc / 100.0) * C_eff_ramo_Ah * n_celle_parallelo
        soc_pts.append(round(soc, 1))
        t_pts.append(round(t_h, 3))
        v_pts.append(round(v_pacco, 3))
        cap_pts.append(round(cap_erogata, 3))

    return {
        "soc_pct": soc_pts,
        "tempo_h": t_pts,
        "tensione_pacco_V": v_pts,
        "capacita_erogata_Ah": cap_pts,
        "C_eff_ramo_Ah": round(C_eff_ramo_Ah, 3),
        "C_eff_pacco_Ah": round(C_eff_ramo_Ah * n_celle_parallelo, 3),
        "t_autonomia_h": round(t_pieno_h, 3),
        "I_pacco_A": round(I_pacco_A, 3),
        "tensione_nominale_pacco_V": round(ocv_per_soc(50.0) * n_celle_serie, 2),
        "tensione_iniziale_V": v_pts[0],
        "tensione_finale_V": v_pts[-1],
    }


def confronto_c_rate(
    C_nom_Ah: float,
    c_rates: list,
    n_celle_serie: int = 1,
    n_celle_parallelo: int = 1,
    R_int_cella_ohm: float = 0.02,
    soc_finale_pct: float = 0.0,
    k_peukert: float = 1.05,
    n_punti: int = 50,
) -> dict:
    """Calcola la curva di scarica per più C-rate, per il confronto tipico da
    datasheet (tensione vs capacità erogata, una curva per ciascun C-rate)."""
    if not c_rates:
        raise ValueError("Specificare almeno un C-rate.")
    curve = {}
    for c_rate in c_rates:
        curve[c_rate] = curva_scarica(
            C_nom_Ah, c_rate, n_celle_serie, n_celle_parallelo,
            R_int_cella_ohm, soc_finale_pct, k_peukert, n_punti,
        )
    return curve
