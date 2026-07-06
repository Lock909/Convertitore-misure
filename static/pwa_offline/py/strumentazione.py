# ==============================================================================
# strumentazione.py — Strumentazione industriale e segnali
# Riferimenti: IEC 60751 (Pt100), NIST ITS-90 (termocoppie), IEC 60584
# ==============================================================================

import math

import numpy as np


# ------------------------------------------------------------------------------
# 1. Conversione segnale mA ↔ tensione (shunt)
# ------------------------------------------------------------------------------

def converti_ma_tensione(corrente_ma: float, R_shunt_ohm: float) -> dict:
    """
    Converte un segnale in corrente [mA] in tensione [V] su resistore shunt.
    Tipico: 4-20 mA su 250 Ω → 1-5 V (ingresso PLC/DCS).

    Parametri
    ----------
    corrente_ma  : corrente del loop [mA]
    R_shunt_ohm  : valore resistore shunt [Ω]
    """
    if corrente_ma < 0:
        raise ValueError("La corrente non può essere negativa.")
    if R_shunt_ohm <= 0:
        raise ValueError("La resistenza shunt deve essere > 0 Ω.")

    V = corrente_ma / 1000.0 * R_shunt_ohm
    P_mw = (corrente_ma / 1000.0)**2 * R_shunt_ohm * 1000.0

    # Percentuale nel range 4-20 mA
    pct_4_20 = ((corrente_ma - 4.0) / 16.0 * 100.0) if corrente_ma >= 4.0 else None

    return {
        "tensione_V":   V,
        "tensione_mV":  V * 1000.0,
        "potenza_mW":   P_mw,
        "pct_4_20":     pct_4_20,
    }


def tensione_a_ma(tensione_V: float, R_shunt_ohm: float) -> float:
    """Converte tensione [V] su shunt in corrente di loop [mA]."""
    if R_shunt_ohm <= 0:
        raise ValueError("La resistenza shunt deve essere > 0 Ω.")
    return (tensione_V / R_shunt_ohm) * 1000.0


# ------------------------------------------------------------------------------
# 2. Termocoppie — linearizzazione inversa NIST ITS-90 (mV → °C)
# ------------------------------------------------------------------------------

# Coefficienti polinomi inversi NIST ITS-90: T(°C) = Σ c_i · E^i
# dove E è il segnale in mV, T è in °C
# Fonte: https://srdata.nist.gov/its90/main/

_TC_INVERSA = {
    "K": [
        # Range -200 → 0 °C  (mV: -5.891 → 0)
        {
            "E_min": -5.891, "E_max": 0.0,
            "c": [0.0, 25.173462, -1.1662878, -1.0833638,
                  -0.8977354, -0.37342377, -0.086632643,
                  -0.010450598, -5.1920577e-4],
        },
        # Range 0 → 500 °C   (mV: 0 → 20.644)
        {
            "E_min": 0.0, "E_max": 20.644,
            "c": [0.0, 25.08355, 7.860106e-2, -2.503131e-1,
                  8.31527e-2, -1.228034e-2, 9.804036e-4,
                  -4.41303e-5, 1.057734e-6, -1.052755e-8],
        },
        # Range 500 → 1372 °C (mV: 20.644 → 54.886)
        {
            "E_min": 20.644, "E_max": 54.886,
            "c": [-1.318058e2, 4.830222e1, -1.646031,
                  5.464731e-2, -9.650715e-4, 8.802193e-6, -3.11081e-8],
        },
    ],
    "J": [
        # Range -210 → 0 °C  (mV: -8.095 → 0)
        {
            "E_min": -8.095, "E_max": 0.0,
            "c": [0.0, 19.528268, -1.2286185, -1.0752178,
                  -5.9086933e-1, -1.7256713e-1, -2.8131513e-2,
                  -2.396337e-3, -8.3823321e-5],
        },
        # Range 0 → 760 °C   (mV: 0 → 42.919)
        {
            "E_min": 0.0, "E_max": 42.919,
            "c": [0.0, 19.78425, -2.001204e-1, 1.036969e-2,
                  -2.549687e-4, 3.585153e-6, -5.344285e-8, 5.09989e-10],
        },
    ],
    "T": [
        # Range -200 → 0 °C  (mV: -5.603 → 0)
        {
            "E_min": -5.603, "E_max": 0.0,
            "c": [0.0, 25.949192, -2.1316967e-1, 7.9018692e-1,
                  4.2527777e-1, 1.3304473e-1, 2.0241446e-2, 1.2668171e-3],
        },
        # Range 0 → 400 °C   (mV: 0 → 20.872)
        {
            "E_min": 0.0, "E_max": 20.872,
            "c": [0.0, 25.928, -7.602961e-1, 4.637791e-2,
                  -2.165394e-3, 6.048144e-5, -7.293422e-7],
        },
    ],
    "E": [
        # Range -200 → 0 °C  (mV: -8.825 → 0)
        {
            "E_min": -8.825, "E_max": 0.0,
            "c": [0.0, 16.977288, -4.351497e-1, -1.5859697e-1,
                  -9.2502871e-2, -2.6084314e-2, -4.1360199e-3,
                  -3.403403e-4, -1.156489e-5],
        },
        # Range 0 → 1000 °C  (mV: 0 → 76.373)
        {
            "E_min": 0.0, "E_max": 76.373,
            "c": [0.0, 17.057035, -2.3301759e-1, 6.5435585e-3,
                  -7.3562749e-5, -1.7896001e-6, 8.4036165e-8,
                  -1.3735879e-9, 1.0629823e-11, -3.2447087e-14],
        },
    ],
}


def termocoppia_mv_a_gradi(mv: float, tipo: str, t_giunto_rif_C: float = 0.0) -> dict:
    """
    Linearizzazione NIST ITS-90: converte FEM termocoppia [mV] in temperatura [°C].

    Parametri
    ----------
    mv             : segnale della termocoppia [mV] (riferito al giunto freddo)
    tipo           : 'K' | 'J' | 'T' | 'E'
    t_giunto_rif_C : temperatura del giunto freddo per la compensazione (CJC).
                     Se ≠ 0, la CJC è disponibile solo per i tipi con polinomio
                     diretto (K, J, T, E).

    Ritorna
    -------
    dict con temperatura, tipo, range valido
    """
    tipo = tipo.upper()
    if tipo not in _TC_INVERSA:
        raise ValueError(f"Tipo termocoppia non supportato: '{tipo}'. Supportati: {list(_TC_INVERSA.keys())}")

    # Compensazione giunto freddo: FEM assoluta (rif. 0 °C) = misura + E(T_rif)
    mv_abs = mv
    if t_giunto_rif_C != 0.0:
        if tipo not in TC_ITS90_DIRETTA:
            raise ValueError(f"CJC disponibile solo per tipi con polinomio diretto {list(TC_ITS90_DIRETTA)}.")
        mv_abs = mv + _tc_emf_diretta(t_giunto_rif_C, tipo)

    segmenti = _TC_INVERSA[tipo]
    segmento = None
    for s in segmenti:
        if s["E_min"] <= mv_abs <= s["E_max"]:
            segmento = s
            break

    if segmento is None:
        E_min_tot = min(s["E_min"] for s in segmenti)
        E_max_tot = max(s["E_max"] for s in segmenti)
        raise ValueError(
            f"Segnale {mv_abs:.3f} mV fuori range per termocoppia tipo {tipo} "
            f"({E_min_tot:.3f} → {E_max_tot:.3f} mV)."
        )

    T = sum(c * mv_abs**i for i, c in enumerate(segmento["c"]))

    return {
        "temperatura_C": T,
        "tipo":          tipo,
        "mv_ingresso":   mv,
        "mv_assoluto":   mv_abs,
        "t_giunto_rif_C": t_giunto_rif_C,
        "range_mv":      (segmento["E_min"], segmento["E_max"]),
    }


def tipi_termocoppia() -> list:
    return list(_TC_INVERSA.keys())


# ------------------------------------------------------------------------------
# 2bis. Termocoppie — funzione di riferimento DIRETTA NIST ITS-90 (°C → mV)
# Polinomi diretti E(t) [mV], t in °C, riferimento giunto a 0 °C.
# Tipi implementati: J, K, T, E (tipo K con termine esponenziale ITS-90 sopra 0 °C).
# Fonte: https://srdata.nist.gov/its90/main/
# ------------------------------------------------------------------------------
TC_ITS90_DIRETTA = {
    "J": {
        "range_C": (-210.0, 1200.0),
        "range_mV": (-8.095, 69.553),
        "segmenti": [
            {"t_min": -210.0, "t_max": 760.0, "c": [
                0.0, 0.503811878150e-1, 0.304758369300e-4, -0.856810657200e-7,
                0.132281952950e-9, -0.170529583370e-12, 0.209480906970e-15,
                -0.125383953360e-18, 0.156317256970e-22]},
            {"t_min": 760.0, "t_max": 1200.0, "c": [
                0.296456256810e3, -0.149761277860e1, 0.317871039240e-2,
                -0.318476867010e-5, 0.157208190040e-8, -0.306913690560e-12]},
        ],
    },
    "K": {
        "range_C": (-270.0, 1372.0),
        "range_mV": (-6.458, 54.886),
        "segmenti": [
            {"t_min": -270.0, "t_max": 0.0, "c": [
                0.0, 0.394501280250e-1, 0.236223735980e-4, -0.328589067840e-6,
                -0.499048287770e-8, -0.675090591730e-10, -0.574103274280e-12,
                -0.310888728940e-14, -0.104516093650e-16, -0.198892668780e-19,
                -0.163226974860e-22]},
            {"t_min": 0.0, "t_max": 1372.0, "c": [
                -0.176004136860e-1, 0.389212049750e-1, 0.185587700320e-4,
                -0.994575928740e-7, 0.318409457190e-9, -0.560728448890e-12,
                0.560750590590e-15, -0.320207200030e-18, 0.971511471520e-22,
                -0.121047212750e-25],
             # termine esponenziale ITS-90 specifico del tipo K (solo questo segmento)
             "exp": {"a0": 0.118597600000e0, "a1": -0.118343200000e-3, "a2": 0.126968600000e3}},
        ],
    },
    "T": {
        "range_C": (-270.0, 400.0),
        "range_mV": (-6.258, 20.872),
        "segmenti": [
            {"t_min": -270.0, "t_max": 0.0, "c": [
                0.0, 0.387481063640e-1, 0.441944343470e-4, 0.118443231050e-6,
                0.200329735540e-7, 0.901380195590e-9, 0.226511565930e-10,
                0.360711542050e-12, 0.384939398830e-14, 0.282135219250e-16,
                0.142515947790e-18, 0.487686622860e-21, 0.107955392700e-23,
                0.139450270620e-26, 0.797951539270e-30]},
            {"t_min": 0.0, "t_max": 400.0, "c": [
                0.0, 0.387481063640e-1, 0.332922278800e-4, 0.206182434040e-6,
                -0.218822568460e-8, 0.109968809280e-10, -0.308157587720e-13,
                0.454791352900e-16, -0.275129016730e-19]},
        ],
    },
    "E": {
        "range_C": (-270.0, 1000.0),
        "range_mV": (-9.835, 76.373),
        "segmenti": [
            {"t_min": -270.0, "t_max": 0.0, "c": [
                0.0, 0.586655087080e-1, 0.454109771240e-4, -0.779980486860e-6,
                -0.258001608430e-7, -0.594525830570e-9, -0.932140586670e-11,
                -0.102876055340e-12, -0.803701236210e-15, -0.439794973910e-17,
                -0.164147763550e-19, -0.396736195160e-22, -0.558273287210e-25,
                -0.346578420130e-28]},
            {"t_min": 0.0, "t_max": 1000.0, "c": [
                0.0, 0.586655087100e-1, 0.450322755820e-4, 0.289084072120e-7,
                -0.330568966520e-9, 0.650244032700e-12, -0.191974955040e-15,
                -0.125366004970e-17, 0.214892175690e-20, -0.143880417820e-23,
                0.359608994810e-27]},
        ],
    },
}


def _tc_emf_diretta(temp_C: float, tipo: str) -> float:
    """Funzione di riferimento diretta ITS-90: temperatura [°C] → f.e.m. [mV] (rif. 0 °C)."""
    tipo = tipo.upper()
    if tipo not in TC_ITS90_DIRETTA:
        raise ValueError(f"Polinomio diretto non disponibile per tipo {tipo}. Disponibili: {list(TC_ITS90_DIRETTA)}.")
    spec = TC_ITS90_DIRETTA[tipo]
    seg = None
    for s in spec["segmenti"]:
        if s["t_min"] <= temp_C <= s["t_max"]:
            seg = s
            break
    if seg is None:
        raise ValueError(f"Temperatura {temp_C} °C fuori campo per tipo {tipo} {spec['range_C']} °C.")
    mv = sum(c * temp_C ** i for i, c in enumerate(seg["c"]))
    e = seg.get("exp")
    if e:
        mv += e["a0"] * math.exp(e["a1"] * (temp_C - e["a2"]) ** 2)
    return mv


def termocoppia_gradi_a_mv(temp_giunto_caldo_C: float, tipo: str, t_giunto_rif_C: float = 0.0) -> dict:
    """
    F.e.m. [mV] generata da una termocoppia (ITS-90) con compensazione del giunto
    freddo (CJC): V = E(T_caldo) − E(T_rif). Tipi: K, J, T, E.
    """
    v_hot = _tc_emf_diretta(temp_giunto_caldo_C, tipo)
    v_cold = _tc_emf_diretta(t_giunto_rif_C, tipo)
    return {
        "mv": v_hot - v_cold,
        "mv_assoluto_rif0": v_hot,
        "tipo": tipo.upper(),
        "T_giunto_caldo_C": temp_giunto_caldo_C,
        "t_giunto_rif_C": t_giunto_rif_C,
    }


def tipi_termocoppia_diretta() -> list:
    return list(TC_ITS90_DIRETTA.keys())


# ------------------------------------------------------------------------------
# 3. RTD Pt100 — IEC 60751 / Callendar-Van Dusen
# ------------------------------------------------------------------------------

# Costanti IEC 60751 (ASTM E1137 compatibile)
_PT100_R0    = 100.0        # Ω a 0°C
_PT100_A     = 3.9083e-3    # °C⁻¹
_PT100_B     = -5.775e-7    # °C⁻²
_PT100_C     = -4.183e-12   # °C⁻⁴ (solo T < 0°C)


RTD_RANGE_C = (-200.0, 850.0)   # campo nominale Pt100/Pt1000 (IEC 60751)


def pt100_t_a_r(T_C: float, R0: float = _PT100_R0) -> float:
    """
    Calcola resistenza RTD al platino [Ω] dalla temperatura [°C] (IEC 60751).
    R0 = 100 → Pt100 (default), R0 = 1000 → Pt1000.
    """
    if R0 <= 0:
        raise ValueError("R0 deve essere > 0.")
    if T_C < RTD_RANGE_C[0] or T_C > RTD_RANGE_C[1]:
        raise ValueError("Temperatura fuori range RTD IEC 60751 (-200 → 850 °C).")
    if T_C >= 0:
        return R0 * (1.0 + _PT100_A * T_C + _PT100_B * T_C**2)
    else:
        return R0 * (1.0 + _PT100_A * T_C + _PT100_B * T_C**2
                     + _PT100_C * (T_C - 100.0) * T_C**3)


def pt100_r_a_t(R_ohm: float, R0: float = _PT100_R0) -> dict:
    """
    Calcola temperatura [°C] dalla resistenza RTD al platino [Ω] (IEC 60751).
    Per T > 0°C: soluzione analitica dell'equazione quadratica.
    Per T < 0°C: bisection numerica (equazione di quarto grado).
    R0 = 100 → Pt100 (default), R0 = 1000 → Pt1000.

    Ritorna dict con temperatura, resistenza, range valido.
    """
    if R0 <= 0:
        raise ValueError("R0 deve essere > 0.")
    R_min = pt100_t_a_r(RTD_RANGE_C[0], R0)
    R_max = pt100_t_a_r(RTD_RANGE_C[1], R0)
    if R_ohm < R_min or R_ohm > R_max:
        raise ValueError(f"Resistenza {R_ohm:.2f} Ω fuori range RTD ({R_min:.2f} → {R_max:.2f} Ω).")

    R0_a = R0 * _PT100_A
    R0_b = R0 * _PT100_B
    # Equazione per T > 0: R0_b·T² + R0_a·T + (R0 - R) = 0
    discriminante = R0_a**2 - 4.0 * R0_b * (R0 - R_ohm)
    T_pos = (-R0_a + math.sqrt(max(0.0, discriminante))) / (2.0 * R0_b)

    if T_pos >= -1.0:   # soluzione nel dominio T ≥ 0
        T = T_pos
    else:
        # Bisection per T < 0
        lo, hi = RTD_RANGE_C[0], 0.0
        for _ in range(60):
            mid = (lo + hi) / 2.0
            if pt100_t_a_r(mid, R0) < R_ohm:
                lo = mid
            else:
                hi = mid
        T = (lo + hi) / 2.0

    return {
        "temperatura_C": T,
        "R_ohm":         R_ohm,
        "R_a_0C":        R0,
        "range_C":       RTD_RANGE_C,
    }


# ------------------------------------------------------------------------------
# 4. Calcolo errore di misura e incertezza
# ------------------------------------------------------------------------------

def calcola_errore_misura(
    valore_misurato: float,
    fondo_scala: float,
    errore_pct_fs: float,
    n_decimali_display: int = 0,
) -> dict:
    """
    Calcola l'errore assoluto e relativo di uno strumento.

    Parametri
    ----------
    valore_misurato   : valore letto dallo strumento
    fondo_scala       : fondo scala dello strumento
    errore_pct_fs     : accuratezza dichiarata [% del fondo scala]
    n_decimali_display: risoluzione display (per errore di quantizzazione)
    """
    if fondo_scala <= 0:
        raise ValueError("Il fondo scala deve essere > 0.")
    if errore_pct_fs < 0:
        raise ValueError("L'errore percentuale non può essere negativo.")

    err_ass = fondo_scala * errore_pct_fs / 100.0
    err_rel = (err_ass / abs(valore_misurato) * 100.0) if valore_misurato != 0 else float("inf")

    # Errore di risoluzione (quantizzazione display)
    risoluzione = 10**(-n_decimali_display) if n_decimali_display >= 0 else 1.0
    err_quant   = risoluzione / 2.0

    # Incertezza combinata (somma in quadratura)
    incertezza_comb = math.sqrt(err_ass**2 + err_quant**2)

    return {
        "errore_assoluto":    err_ass,
        "errore_relativo_pct": err_rel,
        "errore_quant":       err_quant,
        "incertezza_comb":    incertezza_comb,
        "valore_min":         valore_misurato - err_ass,
        "valore_max":         valore_misurato + err_ass,
    }


def combina_errori(errori_assoluti: list) -> dict:
    """
    Combina più sorgenti di errore in quadratura (regola GUM).

    Parametri
    ----------
    errori_assoluti : lista di errori assoluti delle singole sorgenti

    Ritorna
    -------
    dict con errore combinato RSS e somma lineare (worst-case)
    """
    if not errori_assoluti:
        raise ValueError("Fornire almeno un errore.")
    rss   = math.sqrt(sum(e**2 for e in errori_assoluti))
    worst = sum(abs(e) for e in errori_assoluti)
    return {
        "errore_rss":        rss,
        "errore_worst_case": worst,
        "n_sorgenti":        len(errori_assoluti),
    }


# ------------------------------------------------------------------------------
# 5. Taratura (calibrazione) — generica e per RTD/termocoppie
# Convenzione: ogni punto è (riferimento, letto) dove 'riferimento' è il valore
# vero (campione/standard) e 'letto' è il valore indicato dallo strumento.
# La curva di correzione restituisce il valore vero a partire da una lettura.
# ------------------------------------------------------------------------------

ALPHA_PT_NOMINALE = 0.003851   # coeff. di temperatura nominale Pt (IEC 60751), °C⁻¹


def taratura(punti: list, grado: int = 1) -> dict:
    """
    Costruisce una curva di taratura/correzione da punti (riferimento, letto).

    Modello: riferimento ≈ f(letto), polinomio di grado 'grado'
             (grado 1 = lineare → zero/span).

    Ritorna i coefficienti (ordine numpy, grado decrescente), R², gli errori
    dello strumento NON corretto e i residui DOPO la correzione, in unità e in
    % del campo (span). Usare applica_taratura() per correggere nuove letture.
    """
    if grado < 1:
        raise ValueError("Il grado deve essere ≥ 1.")
    if len(punti) < grado + 1:
        raise ValueError(f"Servono almeno {grado + 1} punti per un fit di grado {grado}.")

    rif = np.array([p[0] for p in punti], dtype=float)    # valore vero (campione)
    letto = np.array([p[1] for p in punti], dtype=float)  # valore strumento

    coeff = np.polyfit(letto, rif, grado)
    corretti = np.polyval(coeff, letto)
    residui = corretti - rif

    ss_res = float(np.sum(residui ** 2))
    ss_tot = float(np.sum((rif - rif.mean()) ** 2))
    r2 = (1.0 - ss_res / ss_tot) if ss_tot > 0 else 1.0

    span = float(rif.max() - rif.min())
    err_raw = letto - rif   # errore dello strumento non corretto
    max_raw = float(np.max(np.abs(err_raw)))
    max_res = float(np.max(np.abs(residui)))

    return {
        "coeff": coeff.tolist(),
        "grado": grado,
        "R2": r2,
        "span": span,
        "errore_max_raw": max_raw,
        "errore_max_raw_pct_fs": (max_raw / span * 100.0) if span > 0 else 0.0,
        "errore_max_residuo": max_res,
        "errore_max_residuo_pct_fs": (max_res / span * 100.0) if span > 0 else 0.0,
        "residui": residui.tolist(),
        # parametri zero/span (solo fit lineare)
        "pendenza": float(coeff[0]) if grado == 1 else None,
        "offset": float(coeff[1]) if grado == 1 else None,
        "n_punti": len(punti),
    }


def applica_taratura(coeff: list, valore_letto: float) -> float:
    """Applica la curva di taratura (coeff. da taratura()) a una lettura grezza."""
    return float(np.polyval(np.array(coeff, dtype=float), valore_letto))


def interpola_taratura(tabella: list, x: float, estrapola: bool = True) -> dict:
    """
    Interpolazione lineare da una tabella di taratura [(ingresso, valore), ...]
    (es. punti di un certificato). Se x è fuori dal campo dei punti: estrapola
    linearmente sul segmento più vicino (estrapola=True, con flag 'fuori_campo')
    oppure solleva ValueError (estrapola=False).
    """
    pts = sorted(tabella, key=lambda p: p[0])
    if len(pts) < 2:
        raise ValueError("Servono almeno 2 punti di taratura.")
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    fuori = x < xs[0] or x > xs[-1]
    if fuori and not estrapola:
        raise ValueError(f"Ingresso {x} fuori dal campo tarato [{xs[0]}, {xs[-1]}].")

    if x <= xs[0]:
        i = 0
    elif x >= xs[-1]:
        i = len(pts) - 2
    else:
        i = max(j for j in range(len(xs) - 1) if xs[j] <= x)

    x0, x1, y0, y1 = xs[i], xs[i + 1], ys[i], ys[i + 1]
    y = y0 + (y1 - y0) * (x - x0) / (x1 - x0)
    return {"valore": float(y), "fuori_campo": fuori, "campo": (xs[0], xs[-1])}


def caratterizza_rtd(punti: list) -> dict:
    """
    Ricava R0 e α effettivi di un RTD al platino dai punti di taratura
    (temperatura [°C], resistenza [Ω]), per regressione lineare R = R0·(1 + α·T).
    Confronta α con il valore nominale IEC 60751 (0,003851 °C⁻¹).
    """
    if len(punti) < 2:
        raise ValueError("Servono almeno 2 punti (temperatura, resistenza).")
    T = np.array([p[0] for p in punti], dtype=float)
    R = np.array([p[1] for p in punti], dtype=float)
    slope, intercept = np.polyfit(T, R, 1)   # R = slope·T + intercept
    R0 = float(intercept)
    if R0 == 0:
        raise ValueError("R0 stimato nullo: punti non validi.")
    alpha = float(slope / R0)
    return {
        "R0_effettivo": R0,
        "alpha_effettivo": alpha,
        "alpha_nominale": ALPHA_PT_NOMINALE,
        "scarto_alpha_pct": (alpha - ALPHA_PT_NOMINALE) / ALPHA_PT_NOMINALE * 100.0,
        "n_punti": len(punti),
    }


def caratterizza_offset_tc(punti: list, tipo: str) -> dict:
    """
    Offset di taratura di una termocoppia: confronta la f.e.m. letta con quella
    teorica ITS-90 (tipi K, J) a ciascuna temperatura di riferimento.
    punti: [(temperatura_rif_C, mV_letto), ...].
    """
    if len(punti) < 1:
        raise ValueError("Fornire almeno un punto (temperatura, mV).")
    offsets = []
    for T_rif, mv_letto in punti:
        mv_teo = _tc_emf_diretta(T_rif, tipo)
        offsets.append(mv_letto - mv_teo)
    off = np.array(offsets, dtype=float)
    return {
        "offset_medio_mV": float(off.mean()),
        "offset_max_mV": float(np.max(np.abs(off))),
        "offsets_mV": off.tolist(),
        "tipo": tipo.upper(),
        "n_punti": len(punti),
    }


# ------------------------------------------------------------------------------
# 6. Guida alla misura corretta (riferimento, non calcolo)
# Buone pratiche metrologiche per termocoppie, RTD, loop 4-20 mA e taratura.
# ------------------------------------------------------------------------------
GUIDA_MISURA = {
    "Termocoppie (IEC 60584 / ITS-90)": [
        "Compensare sempre il giunto freddo (CJC): la f.e.m. dipende dalla differenza "
        "di temperatura tra giunto caldo e giunto di riferimento.",
        "Usare cavo di compensazione/estensione del tipo corretto (stessa coppia) fino al "
        "giunto di riferimento; un tipo errato introduce errori di diversi °C.",
        "Curare i morsetti: gradienti termici e metalli diversi creano giunzioni parassite "
        "e f.e.m. spurie.",
        "Verificare la classe di tolleranza (IEC 60584-2, classe 1/2) e l'invecchiamento/"
        "deriva del sensore alle alte temperature.",
    ],
    "RTD Pt100/Pt1000 (IEC 60751)": [
        "Preferire il collegamento a 3 o 4 fili: a 2 fili la resistenza dei conduttori si "
        "somma alla misura (errore anche di alcuni °C su cavi lunghi).",
        "Limitare la corrente di eccitazione (tipicamente ≤ 1 mA) per contenere "
        "l'autoriscaldamento del sensore.",
        "Rispettare la profondità d'immersione minima per evitare dispersione termica lungo "
        "lo stelo (errore di conduzione).",
        "Verificare la classe (AA/A/B, IEC 60751) e usare R0 e α effettivi del sensore se "
        "disponibili da taratura.",
    ],
    "Loop 4-20 mA": [
        "Verificare il carico massimo del loop (burden): tensione di alimentazione ≥ somma "
        "delle cadute (trasmettitore + resistenze + barriere).",
        "Sfruttare le soglie NAMUR NE43 (≤3,6 mA e ≥21 mA) per distinguere un guasto sensore "
        "da un valore di processo reale.",
        "Schermare il cavo e collegare la schermatura a terra a un solo estremo per ridurre "
        "i disturbi di modo comune.",
    ],
    "Taratura e riferibilità": [
        "Usare campioni riferibili (traceability) a standard nazionali/internazionali, con "
        "incertezza adeguata (rapporto TUR tipico ≥ 4:1).",
        "Tarare su più punti coprendo l'intero campo di misura (non solo zero e fondo scala) "
        "per rilevare la non-linearità.",
        "Eseguire i punti in salita e in discesa per valutare l'isteresi e ripetere per la "
        "ripetibilità.",
        "Definire un intervallo di taratura e monitorare la deriva nel tempo (storico dei "
        "certificati).",
    ],
    "Incertezza di misura (GUM)": [
        "Costruire un budget d'incertezza con tutte le sorgenti: sensore, catena di "
        "acquisizione, CJC/cavi, risoluzione, deriva, condizioni ambientali.",
        "Combinare le incertezze tipo in quadratura (RSS) e applicare il fattore di "
        "copertura k (tipicamente k=2 per ~95%).",
        "Distinguere accuratezza (% del fondo scala vs % della lettura) e riportare sempre "
        "l'incertezza estesa con il relativo k.",
    ],
}
