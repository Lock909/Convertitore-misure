# ==============================================================================
# vibrazioni.py — Calcoli di analisi vibrazionale industriale
# Riferimenti: ISO 10816-1, ISO 1940-1, IEC 60068, ISO 1683 (riferimenti dB)
# ==============================================================================

import math

_G_STD = 9.80665   # m/s²
_MM_PER_IN = 25.4
_MM_PER_FT = 304.8
_MM_PER_MIL = 0.0254

# Riferimenti standard per i livelli in dB (ISO 1683): velocità 1 nm/s (ISO) o
# 1E-8 m/s (US, convenzione storica del settore); accelerazione 1 µm/s² (ISO)
# o 1 micro-g (US, convenzione comune nella strumentazione per accelerometri).
_VDB_RIF_MS_ISO = 1e-9
_VDB_RIF_MS_US = 1e-8
_ADB_RIF_MS2_ISO = 1e-6
_ADB_RIF_G_US = 1e-6


def _db(valore: float, riferimento: float):
    """20·log10(valore/riferimento), oppure None se valore <= 0 (dB non definito)."""
    if valore <= 0:
        return None
    return 20.0 * math.log10(valore / riferimento)


# ------------------------------------------------------------------------------
# 1. Conversione tra grandezze vibrazionali
#    Relazioni (segnale sinusoidale puro):
#      v_pk  = ω · d_pk           (spostamento → velocità)
#      a_pk  = ω² · d_pk          (spostamento → accelerazione)
#      RMS   = peak / √2
#      pk-pk = 2 · peak
# ------------------------------------------------------------------------------

def converti_grandezze_vibrazionali(grandezza_in: str, valore: float, frequenza_hz: float) -> dict:
    """
    Converte tra spostamento, velocità e accelerazione per un segnale sinusoidale.

    Parametri
    ----------
    grandezza_in  : 'spostamento_pkpk_mm' | 'velocita_rms_mms' |
                    'accelerazione_rms_ms2' | 'accelerazione_rms_g'
    valore        : float — valore numerico nell'unità indicata
    frequenza_hz  : float — frequenza della vibrazione [Hz]

    Ritorna
    -------
    dict con tutte le grandezze derivate
    """
    if frequenza_hz <= 0:
        raise ValueError("La frequenza deve essere > 0 Hz.")
    if valore < 0:
        raise ValueError("Il valore di ingresso non può essere negativo.")

    omega = 2.0 * math.pi * frequenza_hz  # rad/s

    # Converti tutto in spostamento peak [mm]
    if grandezza_in == "spostamento_pkpk_mm":
        d_pk = valore / 2.0
    elif grandezza_in == "velocita_rms_mms":
        d_pk = (valore * math.sqrt(2)) / omega
    elif grandezza_in == "accelerazione_rms_ms2":
        a_pk_mms2 = valore * 1000.0 * math.sqrt(2)   # m/s² RMS → mm/s² pk
        d_pk = a_pk_mms2 / omega**2
    elif grandezza_in == "accelerazione_rms_g":
        a_pk_mms2 = valore * _G_STD * 1000.0 * math.sqrt(2)
        d_pk = a_pk_mms2 / omega**2
    else:
        raise ValueError(f"Grandezza non riconosciuta: '{grandezza_in}'.")

    # Calcola tutte le grandezze dal spostamento peak
    v_pk      = omega * d_pk                     # mm/s pk
    a_pk_mms2 = omega**2 * d_pk                  # mm/s² pk
    a_pk_ms2  = a_pk_mms2 / 1000.0              # m/s² pk
    sqrt2     = math.sqrt(2)

    v_rms_mms   = v_pk / sqrt2
    a_rms_ms2   = a_pk_ms2 / sqrt2
    a_rms_g     = a_rms_ms2 / _G_STD
    v_rms_ms    = v_rms_mms / 1000.0             # per i livelli in dB (unità SI base)

    return {
        "spostamento_pkpk_mm":    d_pk * 2.0,
        "spostamento_pk_mm":      d_pk,
        "spostamento_pkpk_mils":  (d_pk * 2.0) / _MM_PER_MIL,
        "velocita_pk_mms":        v_pk,
        "velocita_rms_mms":       v_rms_mms,
        "velocita_pk_ins":        v_pk / _MM_PER_IN,
        "velocita_rms_ins":       v_rms_mms / _MM_PER_IN,
        "accelerazione_pk_ms2":   a_pk_ms2,
        "accelerazione_rms_ms2":  a_rms_ms2,
        "accelerazione_pk_g":     a_pk_ms2 / _G_STD,
        "accelerazione_rms_g":    a_rms_g,
        "accelerazione_pk_fts2":  a_pk_ms2 / (_MM_PER_FT / 1000.0),
        "accelerazione_rms_fts2": a_rms_ms2 / (_MM_PER_FT / 1000.0),
        "accelerazione_pk_ins2":  a_pk_ms2 / (_MM_PER_IN / 1000.0),
        "accelerazione_rms_ins2": a_rms_ms2 / (_MM_PER_IN / 1000.0),
        "vdb_iso":                _db(v_rms_ms, _VDB_RIF_MS_ISO),
        "vdb_us":                 _db(v_rms_ms, _VDB_RIF_MS_US),
        "adb_iso":                _db(a_rms_ms2, _ADB_RIF_MS2_ISO),
        "adb_us":                 _db(a_rms_g, _ADB_RIF_G_US),
        "omega_rad_s":            omega,
        "frequenza_hz":           frequenza_hz,
        "frequenza_cpm":          frequenza_hz * 60.0,
    }


# ------------------------------------------------------------------------------
# 2. Classificazione severità vibrazionale ISO 10816-1
# ------------------------------------------------------------------------------

_ISO10816_CLASSI = {
    "Classe I — Piccole macchine < 15 kW": {
        "A": 0.71, "B": 1.8, "C": 4.5,
        "desc": "Es. motori elettrici piccoli, pompe di piccola taglia.",
    },
    "Classe II — Medie 15–75 kW (fondazione rigida)": {
        "A": 1.12, "B": 2.8, "C": 7.1,
        "desc": "Es. motori e pompe di media taglia su basamento rigido.",
    },
    "Classe III — Grandi > 75 kW (fondazione rigida)": {
        "A": 1.8,  "B": 4.5, "C": 11.2,
        "desc": "Es. grandi compressori, turbine su fondazione rigida.",
    },
    "Classe IV — Grandi > 75 kW (fondazione flessibile)": {
        "A": 2.8,  "B": 7.1, "C": 18.0,
        "desc": "Es. turboalternatori, macchine su fondazione elastica.",
    },
}

_ISO10816_ZONE = {
    "A": ("Verde",    "Vibrazione normale per macchine nuove o appena revisionate."),
    "B": ("Giallo",   "Vibrazione accettabile per esercizio continuativo a lungo termine."),
    "C": ("Arancione","Vibrazione al limite: tollerabile solo a breve. Pianificare manutenzione."),
    "D": ("Rosso",    "Vibrazione PERICOLOSA: rischio danni strutturali. Fermare la macchina."),
}


def classifica_iso10816(velocita_rms_mms: float, classe: str) -> tuple:
    """
    Classifica la severità vibrazionale secondo ISO 10816-1.

    Ritorna (zona, colore, descrizione_zona, limiti_dict)
    """
    if velocita_rms_mms < 0:
        raise ValueError("La velocità RMS non può essere negativa.")
    if classe not in _ISO10816_CLASSI:
        raise ValueError(f"Classe ISO non riconosciuta: '{classe}'.")

    lim = _ISO10816_CLASSI[classe]
    if velocita_rms_mms <= lim["A"]:
        zona = "A"
    elif velocita_rms_mms <= lim["B"]:
        zona = "B"
    elif velocita_rms_mms <= lim["C"]:
        zona = "C"
    else:
        zona = "D"

    colore, descr = _ISO10816_ZONE[zona]
    return zona, colore, descr, lim


def lista_classi_iso10816() -> list:
    return list(_ISO10816_CLASSI.keys())


# ------------------------------------------------------------------------------
# 3. Frequenza naturale sistema massa-molla (con smorzamento opzionale)
# ------------------------------------------------------------------------------

def calcola_frequenza_naturale(k_nm: float, m_kg: float, zeta: float = 0.0) -> dict:
    """
    Calcola la frequenza naturale di un sistema massa-molla-smorzatore.

    Parametri
    ----------
    k_nm  : rigidezza [N/m]
    m_kg  : massa [kg]
    zeta  : rapporto di smorzamento critico [-]  (0 = non smorzato)

    Ritorna
    -------
    dict con ωn, fn, T, ωd, fd, Q, c_critico, c_reale
    """
    if k_nm <= 0:
        raise ValueError("La rigidezza k deve essere > 0 N/m.")
    if m_kg <= 0:
        raise ValueError("La massa m deve essere > 0 kg.")
    if zeta < 0:
        raise ValueError("Il rapporto di smorzamento non può essere negativo.")

    omega_n = math.sqrt(k_nm / m_kg)
    fn      = omega_n / (2.0 * math.pi)
    T       = 1.0 / fn
    c_crit  = 2.0 * math.sqrt(k_nm * m_kg)   # smorzamento critico [N·s/m]
    c_reale = zeta * c_crit

    if zeta < 1.0:
        omega_d = omega_n * math.sqrt(1.0 - zeta**2)
        fd      = omega_d / (2.0 * math.pi)
        regime  = "Sottosmorzato" if zeta > 0 else "Non smorzato"
    elif zeta == 1.0:
        omega_d, fd = 0.0, 0.0
        regime = "Smorzamento critico"
    else:
        omega_d, fd = 0.0, 0.0
        regime = "Sovrasmorzato"

    q_factor = (1.0 / (2.0 * zeta)) if zeta > 0 else float("inf")

    return {
        "omega_n_rad_s":   omega_n,
        "fn_hz":           fn,
        "T_s":             T,
        "omega_d_rad_s":   omega_d,
        "fd_hz":           fd,
        "Q":               q_factor,
        "c_critico_ns_m":  c_crit,
        "c_reale_ns_m":    c_reale,
        "zeta":            zeta,
        "regime":          regime,
    }


# ------------------------------------------------------------------------------
# 4. Velocità critica albero — metodo freccia statica (Rankine / Dunkerley)
#    Nc = (30/π) · √(g / δ)    [RPM]
# ------------------------------------------------------------------------------

def calcola_velocita_critica(delta_mm: float) -> dict:
    """
    Stima la velocità critica di un albero dal cedimento statico.

    Parametri
    ----------
    delta_mm : freccia statica sotto carico [mm]

    Ritorna
    -------
    dict con Nc_rpm, fn_hz, zona_proibita_rpm (±20%)
    """
    if delta_mm <= 0:
        raise ValueError("La freccia statica deve essere > 0 mm.")

    delta_m   = delta_mm / 1000.0
    fn_crit   = (1.0 / (2.0 * math.pi)) * math.sqrt(_G_STD / delta_m)
    nc_rpm    = 60.0 * fn_crit
    omega_crit = 2.0 * math.pi * fn_crit

    return {
        "Nc_rpm":               nc_rpm,
        "fn_critica_hz":        fn_crit,
        "omega_critica_rad_s":  omega_crit,
        "zona_proibita_bassa":  nc_rpm * 0.80,
        "zona_proibita_alta":   nc_rpm * 1.20,
    }


# ------------------------------------------------------------------------------
# 5. Squilibrio residuo ammissibile — ISO 1940-1
#    G = e · ω  [mm/s]   dove e = eccentricità [mm], ω [rad/s]
#    U_max = m · e_max   [g·mm]
# ------------------------------------------------------------------------------

_ISO1940_GRADI = {
    "G 0.4  — Giroscopi, turbine vapore alta precisione":    0.4,
    "G 1    — Mandrini, dischi rigidi, turbine a gas":       1.0,
    "G 2.5  — Motori elettrici, pompe centrifughe":          2.5,
    "G 6.3  — Motori elettrici uso generale, ventilatori":   6.3,
    "G 16   — Alberi cardanici, parti motori agricoli":      16.0,
    "G 40   — Alberi di trasmissione":                       40.0,
    "G 100  — Parti di motori a benzina":                   100.0,
    "G 250  — Parti di motori diesel":                      250.0,
    "G 630  — Componenti agricoli, macchine da cantiere":   630.0,
}


def calcola_squilibrio_iso1940(
    massa_kg: float,
    raggio_corr_mm: float,
    velocita_rpm: float,
    grado_g: float,
) -> dict:
    """
    Calcola lo squilibrio residuo massimo ammissibile (ISO 1940-1)
    e verifica uno squilibrio esistente.

    Parametri
    ----------
    massa_kg       : massa totale del rotore [kg]
    raggio_corr_mm : raggio del piano di correzione [mm]
    velocita_rpm   : velocità operativa [RPM]
    grado_g        : valore G del grado ISO (es. 2.5, 6.3)

    Ritorna
    -------
    dict con e_max_mm, U_max_gmm, massa_corr_max_g (al raggio dato)
    """
    if massa_kg <= 0:
        raise ValueError("La massa del rotore deve essere > 0 kg.")
    if raggio_corr_mm <= 0:
        raise ValueError("Il raggio di correzione deve essere > 0 mm.")
    if velocita_rpm <= 0:
        raise ValueError("La velocità operativa deve essere > 0 RPM.")
    if grado_g <= 0:
        raise ValueError("Il grado G deve essere > 0.")

    omega      = 2.0 * math.pi * velocita_rpm / 60.0   # rad/s
    e_max_mm   = grado_g / omega                         # mm (eccentricità max)
    U_max_gmm  = massa_kg * 1000.0 * e_max_mm            # g·mm
    U_max_kgmm = U_max_gmm / 1000.0                      # kg·mm

    # Massa di correzione max da aggiungere/togliere al raggio indicato
    massa_corr_max_g = U_max_gmm / raggio_corr_mm        # g

    return {
        "e_max_mm":          e_max_mm,
        "U_max_gmm":         U_max_gmm,
        "U_max_kgmm":        U_max_kgmm,
        "massa_corr_max_g":  massa_corr_max_g,
        "omega_rad_s":       omega,
        "grado_g":           grado_g,
    }


def lista_gradi_iso1940() -> list:
    return list(_ISO1940_GRADI.keys())


def valore_grado_iso1940(nome_grado: str) -> float:
    return _ISO1940_GRADI.get(nome_grado)
