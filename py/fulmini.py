# ==============================================================================
# fulmini.py — Protezione contro i fulmini (IEC 62305 / CEI 81-10)
# Valutazione semplificata della necessità di protezione (Nd vs Nc) e
# parametri dell'impianto LPS (sfera rotolante, maglia, calate) per livello
# di protezione (LPL) secondo IEC 62305-3.
# ==============================================================================

import math

# IEC 62305-3 Tabella 2 — parametri dell'impianto di protezione per LPL
_PARAMETRI_LPL = {
    "I":   {"raggio_sfera_m": 20, "lato_maglia_m": 5,  "distanza_calate_m": 10, "efficienza_min": 0.98},
    "II":  {"raggio_sfera_m": 30, "lato_maglia_m": 10, "distanza_calate_m": 10, "efficienza_min": 0.95},
    "III": {"raggio_sfera_m": 45, "lato_maglia_m": 15, "distanza_calate_m": 15, "efficienza_min": 0.90},
    "IV":  {"raggio_sfera_m": 60, "lato_maglia_m": 20, "distanza_calate_m": 20, "efficienza_min": 0.80},
}


def area_raccolta_equivalente(L_m: float, W_m: float, H_m: float) -> dict:
    """
    Area di raccolta equivalente Ad di una struttura rettangolare isolata
    (IEC 62305-2 Allegato A): Ad = L·W + 2·(3H)·(L+W) + π·(3H)²

    Parametri
    ----------
    L_m, W_m : lunghezza e larghezza della struttura [m]
    H_m      : altezza della struttura [m]
    """
    if L_m <= 0 or W_m <= 0 or H_m <= 0:
        raise ValueError("Lunghezza, larghezza e altezza devono essere > 0.")

    Ad = L_m * W_m + 2.0 * (3.0 * H_m) * (L_m + W_m) + math.pi * (3.0 * H_m) ** 2
    return {"Ad_m2": Ad, "L_m": L_m, "W_m": W_m, "H_m": H_m}


def frequenza_fulmini_prevista(Ng_fulmini_km2_anno: float, Ad_m2: float, Cd: float = 1.0) -> dict:
    """
    Frequenza annua prevista di fulmini diretti sulla struttura (IEC 62305-2):
    Nd = Ng · Ad · Cd · 10⁻⁶

    Parametri
    ----------
    Ng_fulmini_km2_anno : densità di fulmini a terra della zona [fulmini/km²/anno]
                          (in Italia tipicamente 1-4, da mappe di ceraunicità)
    Ad_m2               : area di raccolta equivalente [m²]
    Cd                  : fattore di ubicazione (1 = struttura isolata in piano;
                          0.5 = circondata da strutture più basse; 0.25 = circondata
                          da strutture della stessa altezza o più alte; 2 = struttura
                          isolata su altura)
    """
    if Ng_fulmini_km2_anno < 0:
        raise ValueError("Ng non può essere negativo.")
    if Ad_m2 <= 0:
        raise ValueError("Ad deve essere > 0.")
    if Cd <= 0:
        raise ValueError("Cd deve essere > 0.")

    Nd = Ng_fulmini_km2_anno * Ad_m2 * Cd * 1e-6
    return {"Nd_fulmini_anno": Nd, "Ng_fulmini_km2_anno": Ng_fulmini_km2_anno, "Ad_m2": Ad_m2, "Cd": Cd}


def valuta_necessita_protezione(Nd_fulmini_anno: float, Nc_fulmini_anno: float = 1e-3) -> dict:
    """
    Confronta la frequenza prevista Nd con quella tollerabile Nc (valutazione
    semplificata IEC 62305-2): se Nd > Nc la protezione è necessaria, con
    efficienza minima richiesta E = 1 - Nc/Nd.

    Parametri
    ----------
    Nd_fulmini_anno : frequenza annua prevista di fulmini diretti
    Nc_fulmini_anno : frequenza annua tollerabile (default 10⁻³, valore di
                      riferimento comune per strutture ordinarie senza
                      particolari rischi di perdita — per un'analisi del
                      rischio completa secondo IEC 62305-2 va calcolato caso
                      per caso)
    """
    if Nd_fulmini_anno < 0:
        raise ValueError("Nd non può essere negativo.")
    if Nc_fulmini_anno <= 0:
        raise ValueError("Nc deve essere > 0.")

    necessaria = Nd_fulmini_anno > Nc_fulmini_anno
    efficienza_richiesta = max(0.0, 1.0 - Nc_fulmini_anno / Nd_fulmini_anno) if Nd_fulmini_anno > 0 else 0.0
    return {
        "protezione_necessaria": necessaria,
        "efficienza_richiesta": efficienza_richiesta,
        "efficienza_richiesta_pct": efficienza_richiesta * 100.0,
        "Nd_fulmini_anno": Nd_fulmini_anno,
        "Nc_fulmini_anno": Nc_fulmini_anno,
    }


def livello_protezione_da_efficienza(efficienza_richiesta: float) -> dict:
    """
    Determina il livello di protezione LPS (I-IV) minimo che soddisfa
    l'efficienza richiesta, secondo le efficienze di intercettazione di
    IEC 62305-3 (LPL I=0.98, II=0.95, III=0.90, IV=0.80).
    """
    if not 0.0 <= efficienza_richiesta <= 1.0:
        raise ValueError("L'efficienza richiesta deve essere tra 0 e 1.")

    for livello in ("IV", "III", "II", "I"):
        if efficienza_richiesta <= _PARAMETRI_LPL[livello]["efficienza_min"]:
            return {
                "livello": livello,
                "efficienza_min_livello": _PARAMETRI_LPL[livello]["efficienza_min"],
                "efficienza_richiesta": efficienza_richiesta,
                "raggiungibile_con_lps": True,
            }
    return {
        "livello": "I",
        "efficienza_min_livello": _PARAMETRI_LPL["I"]["efficienza_min"],
        "efficienza_richiesta": efficienza_richiesta,
        "raggiungibile_con_lps": False,
    }


def parametri_lps(livello: str) -> dict:
    """
    Parametri dell'impianto di protezione (captatori/calate) per livello LPL,
    secondo IEC 62305-3 Tabella 2.

    Parametri
    ----------
    livello : "I" | "II" | "III" | "IV"
    """
    if livello not in _PARAMETRI_LPL:
        raise ValueError(f"Livello LPL non riconosciuto: '{livello}' (usare I, II, III o IV).")
    p = _PARAMETRI_LPL[livello]
    return {
        "livello": livello,
        "raggio_sfera_rotolante_m": p["raggio_sfera_m"],
        "lato_maglia_m": p["lato_maglia_m"],
        "distanza_max_calate_m": p["distanza_calate_m"],
        "efficienza_min": p["efficienza_min"],
    }


def lista_livelli_lpl() -> list:
    return list(_PARAMETRI_LPL.keys())


def valutazione_lps(
    L_m: float, W_m: float, H_m: float,
    Ng_fulmini_km2_anno: float, Cd: float = 1.0, Nc_fulmini_anno: float = 1e-3,
) -> dict:
    """
    Valutazione semplificata completa, in un'unica chiamata: area di
    raccolta -> frequenza prevista -> necessità di protezione -> (se
    necessaria) livello LPL minimo e relativi parametri dell'impianto.
    """
    risultato = {}
    risultato.update(area_raccolta_equivalente(L_m, W_m, H_m))
    risultato.update(frequenza_fulmini_prevista(Ng_fulmini_km2_anno, risultato["Ad_m2"], Cd))
    risultato.update(valuta_necessita_protezione(risultato["Nd_fulmini_anno"], Nc_fulmini_anno))
    if risultato["protezione_necessaria"]:
        r_livello = livello_protezione_da_efficienza(risultato["efficienza_richiesta"])
        risultato.update(r_livello)
        risultato.update(parametri_lps(r_livello["livello"]))
    return risultato
