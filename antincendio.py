# ==============================================================================
# antincendio.py — Rete idranti e naspi antincendio (UNI 10779)
# Portata di rete per livello di rischio, volume di riserva idrica e
# prevalenza minima della pompa. Valori tipici indicativi: per il
# dimensionamento esecutivo fare sempre riferimento al progetto antincendio
# specifico e alla norma vigente.
# ==============================================================================

import math

LIVELLI_RISCHIO = {
    1: {"n_contemporanei": 2, "durata_min": 60},
    2: {"n_contemporanei": 3, "durata_min": 60},
    3: {"n_contemporanei": 4, "durata_min": 90},
}

PARAMETRI_PROTEZIONE = {
    "naspo_UNI25":   {"Q_lmin": 35.0,  "P_bar": 2.0},
    "idrante_UNI45": {"Q_lmin": 120.0, "P_bar": 2.0},
    "idrante_UNI70": {"Q_lmin": 300.0, "P_bar": 4.0},
}

_BAR_PER_METRO_H2O = 1.0 / 10.197  # 1 bar = 10.197 m colonna d'acqua


def portata_rete_totale(tipo_protezione: str, livello_rischio: int) -> dict:
    """
    Portata totale di rete richiesta (UNI 10779), pari alla portata della
    singola protezione moltiplicata per il numero di apparecchi che si
    suppone operino in contemporanea al livello di rischio dato.
    """
    if tipo_protezione not in PARAMETRI_PROTEZIONE:
        raise ValueError(f"Tipo protezione non riconosciuto. Valori validi: {list(PARAMETRI_PROTEZIONE.keys())}")
    if livello_rischio not in LIVELLI_RISCHIO:
        raise ValueError(f"Livello di rischio non riconosciuto. Valori validi: {list(LIVELLI_RISCHIO.keys())}")

    p = PARAMETRI_PROTEZIONE[tipo_protezione]
    liv = LIVELLI_RISCHIO[livello_rischio]
    Q_tot_lmin = p["Q_lmin"] * liv["n_contemporanei"]

    return {
        "Q_tot_lmin": Q_tot_lmin,
        "Q_tot_m3h": Q_tot_lmin * 60.0 / 1000.0,
        "Q_singola_lmin": p["Q_lmin"],
        "P_min_bar": p["P_bar"],
        "n_contemporanei": liv["n_contemporanei"],
        "durata_min": liv["durata_min"],
        "tipo_protezione": tipo_protezione,
        "livello_rischio": livello_rischio,
    }


def volume_riserva_idrica(Q_tot_lmin: float, durata_min: float) -> dict:
    """Volume minimo della riserva idrica: V = Q_tot * durata."""
    if Q_tot_lmin <= 0:
        raise ValueError("La portata totale deve essere > 0 l/min.")
    if durata_min <= 0:
        raise ValueError("La durata deve essere > 0 min.")

    V_l = Q_tot_lmin * durata_min
    return {
        "V_m3": V_l / 1000.0,
        "V_l": V_l,
        "Q_tot_lmin": Q_tot_lmin,
        "durata_min": durata_min,
    }


def prevalenza_pompa(
    P_min_bar: float,
    altezza_geodetica_m: float,
    perdite_carico_bar: float = 0.0,
    margine_bar: float = 0.5,
) -> dict:
    """
    Prevalenza minima richiesta alla pompa antincendio:
    H_pompa = P_min + altezza_geodetica (convertita in bar) + perdite di carico + margine.
    """
    if P_min_bar <= 0:
        raise ValueError("La pressione minima richiesta deve essere > 0 bar.")
    if altezza_geodetica_m < 0:
        raise ValueError("L'altezza geodetica deve essere >= 0 m.")
    if perdite_carico_bar < 0:
        raise ValueError("Le perdite di carico devono essere >= 0 bar.")
    if margine_bar < 0:
        raise ValueError("Il margine deve essere >= 0 bar.")

    H_geodetica_bar = altezza_geodetica_m * _BAR_PER_METRO_H2O
    H_pompa_bar = P_min_bar + H_geodetica_bar + perdite_carico_bar + margine_bar

    return {
        "H_pompa_bar": H_pompa_bar,
        "H_pompa_m": H_pompa_bar / _BAR_PER_METRO_H2O,
        "P_min_bar": P_min_bar,
        "H_geodetica_bar": H_geodetica_bar,
        "perdite_carico_bar": perdite_carico_bar,
        "margine_bar": margine_bar,
    }


def numero_protezioni_area(area_m2: float, interasse_m: float = 45.0) -> dict:
    """
    Stima indicativa del numero minimo di naspi/idranti per coprire un'area,
    trattando l'interasse tipico UNI 10779 tra apparecchi come lato di una
    cella quadrata di copertura (stima grossolana, non sostituisce la verifica
    del raggio d'azione reale sulla planimetria).
    """
    if area_m2 <= 0:
        raise ValueError("L'area deve essere > 0 m².")
    if interasse_m <= 0:
        raise ValueError("L'interasse deve essere > 0 m.")

    n = max(1, math.ceil(area_m2 / interasse_m**2))
    return {
        "n_protezioni_stimato": n,
        "area_m2": area_m2,
        "interasse_m": interasse_m,
    }


def dimensionamento_completo(
    tipo_protezione: str,
    livello_rischio: int,
    altezza_geodetica_m: float,
    perdite_carico_bar: float = 0.0,
    margine_bar: float = 0.5,
) -> dict:
    """Dimensionamento completo in un'unica chiamata: portata totale di rete,
    volume di riserva idrica e prevalenza minima della pompa."""
    base = portata_rete_totale(tipo_protezione, livello_rischio)
    vol = volume_riserva_idrica(base["Q_tot_lmin"], base["durata_min"])
    pompa = prevalenza_pompa(base["P_min_bar"], altezza_geodetica_m, perdite_carico_bar, margine_bar)

    risultato = {}
    risultato.update(base)
    risultato.update(vol)
    risultato.update(pompa)
    return risultato
