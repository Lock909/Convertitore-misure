# ==============================================================================
# illuminazione_emergenza.py — Verifica illuminazione di sicurezza secondo
# UNI EN 1838 (vie di esodo, aree antipanico, aree a rischio specifico,
# uniformità, autonomia minima).
# ==============================================================================

_AUTONOMIA_MINIMA = {
    "normale": 1.0,
    "affollamento_elevato": 2.0,
    "alto_rischio": 1.0,
}


def verifica_via_esodo(E_asse_lux: float, E_min_lux: float, larghezza_m: float = 2.0) -> dict:
    """
    Verifica i requisiti minimi UNI EN 1838 per una via di esodo (larghezza
    fino a 2 m considerata come singola striscia; oltre si sommano più
    strisce da 2 m ciascuna): illuminamento sull'asse centrale >= 1 lux,
    sulla fascia centrale (metà larghezza) >= 0.5 lux.
    """
    if E_asse_lux < 0 or E_min_lux < 0:
        raise ValueError("Gli illuminamenti devono essere >= 0 lux.")
    if larghezza_m <= 0:
        raise ValueError("La larghezza deve essere > 0 m.")
    conforme = E_asse_lux >= 1.0 and E_min_lux >= 0.5
    return {
        "conforme": conforme,
        "E_asse_lux": E_asse_lux,
        "E_asse_minimo_lux": 1.0,
        "E_min_lux": E_min_lux,
        "E_min_minimo_lux": 0.5,
        "larghezza_m": larghezza_m,
    }


def verifica_area_aperta(E_lux: float) -> dict:
    """Verifica il requisito minimo per area aperta (antipanico): illuminamento
    >= 0.5 lux sull'area libera al suolo (esclusa una fascia perimetrale di 0.5 m)."""
    if E_lux < 0:
        raise ValueError("L'illuminamento deve essere >= 0 lux.")
    return {"conforme": E_lux >= 0.5, "E_lux": E_lux, "E_minimo_lux": 0.5}


def illuminamento_minimo_area_rischio(E_normale_lux: float) -> dict:
    """
    Illuminamento minimo richiesto in un'area a rischio specifico (es. punto
    di lavoro pericoloso): 10% dell'illuminamento normale di esercizio, con
    soglia minima assoluta di 15 lux.
    """
    if E_normale_lux <= 0:
        raise ValueError("L'illuminamento normale deve essere > 0 lux.")
    calcolato = E_normale_lux * 0.10
    minimo = max(calcolato, 15.0)
    return {
        "E_minimo_richiesto_lux": minimo,
        "E_normale_lux": E_normale_lux,
        "calcolato_10pct_lux": calcolato,
    }


def verifica_uniformita(E_max_lux: float, E_min_lux: float) -> dict:
    """Verifica il rapporto di uniformità su vie di esodo/aree aperte:
    E_max / E_min <= 40:1."""
    if E_max_lux <= 0 or E_min_lux <= 0:
        raise ValueError("Gli illuminamenti devono essere > 0 lux.")
    if E_min_lux > E_max_lux:
        raise ValueError("L'illuminamento minimo non può superare il massimo.")
    rapporto = E_max_lux / E_min_lux
    return {
        "conforme": rapporto <= 40.0,
        "rapporto": rapporto,
        "rapporto_massimo": 40.0,
        "E_max_lux": E_max_lux,
        "E_min_lux": E_min_lux,
    }


def autonomia_minima_richiesta(tipo_luogo: str = "normale") -> dict:
    """Autonomia minima raccomandata (ore) per il tipo di luogo dato."""
    if tipo_luogo not in _AUTONOMIA_MINIMA:
        raise ValueError(f"Tipo luogo non riconosciuto. Valori validi: {list(_AUTONOMIA_MINIMA.keys())}")
    return {"autonomia_minima_h": _AUTONOMIA_MINIMA[tipo_luogo], "tipo_luogo": tipo_luogo}
