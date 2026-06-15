# ==============================================================================
# illuminotecnica.py — Calcoli di illuminotecnica industriale
# Metodo: flusso luminoso (Metodo dei Lumen)
# Riferimenti: EN 12464-1 (illuminazione luoghi di lavoro interni)
#              CIE 117, UNI EN 12464-1:2021
# ==============================================================================

import math


# ------------------------------------------------------------------------------
# Livelli di illuminamento minimi EN 12464-1 (luoghi di lavoro interni)
# (Em_lux, UGRL_max, Ra_min, descrizione)
# ------------------------------------------------------------------------------

_AMBIENTI_EN12464 = {
    "Corridoio / zona di transito":               (100, 28, 40),
    "Scala / montacarichi":                        (150, 25, 40),
    "Magazzino / deposito":                        (200, 25, 60),
    "Area carico/scarico":                         (300, 25, 60),
    "Officina meccanica — lavori grossolani":      (300, 25, 60),
    "Officina meccanica — lavori medi":            (500, 22, 60),
    "Officina meccanica — lavori di precisione":   (750, 19, 80),
    "Ufficio generale":                            (500, 19, 80),
    "Sala riunioni / conferenze":                  (500, 19, 80),
    "Sala controllo / quadri":                     (500, 19, 80),
    "Laboratorio / reparto QC":                    (500, 22, 80),
    "Saldatura / taglio":                          (500, 25, 80),
    "Verniciatura / rivestimenti":                 (750, 25, 90),
    "Ispezione visiva fine":                      (1000, 19, 90),
    "Reparto elettronico (circuiti stampati)":    (1500, 19, 80),
    "Area parcheggio / piazzale esterno":          (75,  50, 20),
}


def lista_ambienti() -> list:
    return list(_AMBIENTI_EN12464.keys())


def requisiti_ambiente(ambiente: str) -> dict:
    if ambiente not in _AMBIENTI_EN12464:
        raise ValueError(f"Ambiente non trovato: '{ambiente}'.")
    Em, UGRL, Ra = _AMBIENTI_EN12464[ambiente]
    return {"Em_lux": Em, "UGRL_max": UGRL, "Ra_min": Ra}


# ------------------------------------------------------------------------------
# Metodo dei Lumen — numero di corpi illuminanti necessari
# N = (Em × A) / (Φ_corp × MF × UF)
# ------------------------------------------------------------------------------

def calcola_numero_lampade(
    Em_lux: float,
    A_m2: float,
    phi_corpo_lm: float,
    MF: float = 0.80,
    UF: float = 0.55,
) -> dict:
    """
    Calcola il numero di corpi illuminanti per raggiungere l'illuminamento medio.

    Parametri
    ----------
    Em_lux      : illuminamento medio richiesto [lux]
    A_m2        : area del locale [m²]
    phi_corpo_lm: flusso luminoso totale del singolo corpo illuminante [lm]
                  (lampade × lm/lampada, già incluso il corpo)
    MF          : fattore di manutenzione [-]  (tipico 0.70-0.90)
                  MF = LMF × LSF × LLMF × RSMF  (prodotto dei fattori parziali)
    UF          : fattore di utilizzo [-]  (dipende da sala e apparecchio, tipico 0.40-0.80)

    Ritorna
    -------
    dict con N (corpi illuminanti), Em_effettivo, flusso totale necessario
    """
    if Em_lux <= 0:
        raise ValueError("L'illuminamento deve essere > 0 lux.")
    if A_m2 <= 0:
        raise ValueError("L'area deve essere > 0 m².")
    if phi_corpo_lm <= 0:
        raise ValueError("Il flusso del corpo illuminante deve essere > 0 lm.")
    if not 0 < MF <= 1:
        raise ValueError("MF deve essere tra 0 e 1.")
    if not 0 < UF <= 1:
        raise ValueError("UF deve essere tra 0 e 1.")

    phi_tot_necessario = (Em_lux * A_m2) / (MF * UF)   # [lm]
    N_esatto           = phi_tot_necessario / phi_corpo_lm
    N_installati       = math.ceil(N_esatto)

    Em_effettivo = (N_installati * phi_corpo_lm * MF * UF) / A_m2

    return {
        "N_corpi":         N_installati,
        "N_esatto":        N_esatto,
        "Em_effettivo":    Em_effettivo,
        "Em_richiesto":    Em_lux,
        "phi_tot_lm":      phi_tot_necessario,
        "phi_corpo_lm":    phi_corpo_lm,
        "MF":              MF,
        "UF":              UF,
        "A_m2":            A_m2,
    }


# ------------------------------------------------------------------------------
# Indice del locale k (Room Index / Cavity Ratio)
# k = (L × W) / (Hm × (L + W))
# Serve per ricavare UF dal diagramma costruttore
# ------------------------------------------------------------------------------

def calcola_room_index(
    L_m: float,
    W_m: float,
    H_m: float,
    h_lavoro_m: float = 0.85,
) -> dict:
    """
    Calcola l'indice del locale k (Room Index / Cavity Ratio).

    Parametri
    ----------
    L_m, W_m    : lunghezza e larghezza del locale [m]
    H_m         : altezza soffitto [m]
    h_lavoro_m  : altezza piano di lavoro [m] (tipico 0.85 m)
    """
    if L_m <= 0 or W_m <= 0 or H_m <= 0:
        raise ValueError("Le dimensioni del locale devono essere > 0.")
    if h_lavoro_m >= H_m:
        raise ValueError("L'altezza del piano di lavoro deve essere minore dell'altezza soffitto.")

    Hm = H_m - h_lavoro_m   # altezza utile (soffitto - piano di lavoro)
    k  = (L_m * W_m) / (Hm * (L_m + W_m))
    A  = L_m * W_m

    # Distanza massima consigliata tra corpi illuminanti (regola empirica: Hm × 1.5)
    d_max = Hm * 1.5

    return {
        "k":         k,
        "Hm_m":      Hm,
        "A_m2":      A,
        "d_max_m":   d_max,
        "note_UF":   _uf_approssimato(k),
    }


def _uf_approssimato(k: float) -> str:
    """Stima orientativa del fattore di utilizzo da k (riflettanza soffitto/pareti medie)."""
    if k < 0.6:
        return f"k = {k:.2f} → UF ≈ 0.25-0.35 (locale molto stretto/basso)"
    elif k < 1.0:
        return f"k = {k:.2f} → UF ≈ 0.35-0.45"
    elif k < 1.5:
        return f"k = {k:.2f} → UF ≈ 0.45-0.55"
    elif k < 2.5:
        return f"k = {k:.2f} → UF ≈ 0.55-0.65"
    else:
        return f"k = {k:.2f} → UF ≈ 0.65-0.75 (locale ampio/alto)"


# ------------------------------------------------------------------------------
# Potenza elettrica totale e densità (LENI)
# ------------------------------------------------------------------------------

def calcola_potenza_illuminazione(
    N_corpi: int,
    P_corpo_W: float,
    A_m2: float,
) -> dict:
    """
    Calcola la potenza totale installata e la densità energetica.

    Parametri
    ----------
    N_corpi  : numero di corpi illuminanti installati
    P_corpo_W: potenza elettrica del singolo corpo [W]
    A_m2     : area del locale [m²]
    """
    if N_corpi <= 0:
        raise ValueError("Il numero di corpi deve essere > 0.")
    if P_corpo_W <= 0:
        raise ValueError("La potenza del corpo deve essere > 0 W.")
    if A_m2 <= 0:
        raise ValueError("L'area deve essere > 0 m².")

    P_tot_W  = N_corpi * P_corpo_W
    LENI     = P_tot_W / A_m2    # W/m² (Lighting Energy Numeric Indicator — semplificato)

    return {
        "P_tot_W":   P_tot_W,
        "P_tot_kW":  P_tot_W / 1000.0,
        "LENI_W_m2": LENI,
        "N_corpi":   N_corpi,
        "P_corpo_W": P_corpo_W,
    }


# ------------------------------------------------------------------------------
# Fattore di manutenzione MF — scomposizione in fattori parziali
# MF = LMF × LSF × LLMF × RSMF
# ------------------------------------------------------------------------------

def calcola_mf(
    LMF: float,
    LSF: float,
    LLMF: float,
    RSMF: float = 1.0,
) -> dict:
    """
    Calcola il fattore di manutenzione complessivo (EN 12464-1 Annex B).

    Parametri
    ----------
    LMF   : Luminaire Maintenance Factor — sporcizia sull'apparecchio (0.70-0.95)
    LSF   : Lamp Survival Factor — % lampade funzionanti a fine intervallo (0.90-1.00)
    LLMF  : Lamp Lumen Maintenance Factor — calo flusso lampada (0.70-0.95)
    RSMF  : Room Surface Maintenance Factor — sporcizia superfici (0.85-1.00)
    """
    for nome, val in (("LMF", LMF), ("LSF", LSF), ("LLMF", LLMF), ("RSMF", RSMF)):
        if not 0 < val <= 1.0:
            raise ValueError(f"{nome} deve essere tra 0 e 1.")
    MF = LMF * LSF * LLMF * RSMF
    return {
        "MF":   MF,
        "LMF":  LMF,
        "LSF":  LSF,
        "LLMF": LLMF,
        "RSMF": RSMF,
        "classificazione": "Buono" if MF >= 0.80 else ("Medio" if MF >= 0.67 else "Scarso"),
    }
