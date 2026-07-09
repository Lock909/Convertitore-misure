# ==============================================================================
# atex.py — Classificazione ATEX (Direttiva 2014/34/UE) per atmosfere
# esplosive da gas/vapori e da polveri: categoria minima di apparecchiatura,
# classe di temperatura e marcatura indicativa.
# ==============================================================================

_CATEGORIE_GAS = {
    0: {"categoria": "1G", "epl": "Ga", "descrizione": "atmosfera esplosiva presente continuamente o per lunghi periodi"},
    1: {"categoria": "2G", "epl": "Gb", "descrizione": "probabile occasionalmente in condizioni di funzionamento normale"},
    2: {"categoria": "3G", "epl": "Gc", "descrizione": "non probabile in condizioni di funzionamento normale, o solo per brevi periodi"},
}

_CATEGORIE_POLVERI = {
    20: {"categoria": "1D", "epl": "Da", "descrizione": "nube di polvere combustibile presente continuamente o per lunghi periodi"},
    21: {"categoria": "2D", "epl": "Db", "descrizione": "probabile occasionalmente in condizioni di funzionamento normale"},
    22: {"categoria": "3D", "epl": "Dc", "descrizione": "non probabile in condizioni di funzionamento normale, o solo per brevi periodi"},
}

_GRUPPI_GAS_VALIDI = ("IIA", "IIB", "IIC")

# Classi di temperatura (IEC 60079-0): T_max_superficie ammessa per
# apparecchiature idonee a sostanze con la data temperatura di autoaccensione.
_CLASSI_TEMPERATURA = [
    ("T1", 450.0), ("T2", 300.0), ("T3", 200.0), ("T4", 135.0), ("T5", 100.0), ("T6", 85.0),
]


def categoria_minima_gas(zona: int) -> dict:
    """Categoria minima di apparecchiatura (e relativo EPL) richiesta per una
    zona classificata per gas/vapori infiammabili (0, 1, 2)."""
    if zona not in _CATEGORIE_GAS:
        raise ValueError("Zona gas non valida. Valori ammessi: 0, 1, 2.")
    dati = _CATEGORIE_GAS[zona]
    return {
        "zona": zona,
        "categoria_minima": dati["categoria"],
        "epl_minimo": dati["epl"],
        "descrizione": dati["descrizione"],
    }


def categoria_minima_polveri(zona: int) -> dict:
    """Categoria minima di apparecchiatura (e relativo EPL) richiesta per una
    zona classificata per polveri combustibili (20, 21, 22)."""
    if zona not in _CATEGORIE_POLVERI:
        raise ValueError("Zona polveri non valida. Valori ammessi: 20, 21, 22.")
    dati = _CATEGORIE_POLVERI[zona]
    return {
        "zona": zona,
        "categoria_minima": dati["categoria"],
        "epl_minimo": dati["epl"],
        "descrizione": dati["descrizione"],
    }


def classe_temperatura(T_autoaccensione_C: float) -> dict:
    """
    Classe di temperatura (T1-T6) idonea per una sostanza con la temperatura
    di autoaccensione data: la temperatura massima superficiale
    dell'apparecchiatura deve restare sempre sotto tale soglia.
    """
    if T_autoaccensione_C <= 0:
        raise ValueError("La temperatura di autoaccensione deve essere > 0 °C.")
    for classe, soglia in _CLASSI_TEMPERATURA:
        if soglia < T_autoaccensione_C:
            return {
                "classe_temperatura": classe,
                "T_max_superficie_C": soglia,
                "T_autoaccensione_C": T_autoaccensione_C,
            }
    raise ValueError(
        "Temperatura di autoaccensione troppo bassa (<= 85 °C): nessuna classe di "
        "temperatura standard è idonea, serve una valutazione specifica."
    )


def marcatura_atex(zona: int, gruppo_gas: str = "IIB", T_autoaccensione_C: float = None) -> dict:
    """
    Marcatura ATEX indicativa per un'apparecchiatura destinata alla zona data
    (gas: 0/1/2, polveri: 20/21/22), con classe di temperatura opzionale se
    nota la temperatura di autoaccensione della sostanza presente.
    """
    if zona in _CATEGORIE_GAS:
        base = categoria_minima_gas(zona)
        tipo = "gas"
        if gruppo_gas not in _GRUPPI_GAS_VALIDI:
            raise ValueError(f"Gruppo gas non valido. Valori ammessi: {', '.join(_GRUPPI_GAS_VALIDI)}.")
    elif zona in _CATEGORIE_POLVERI:
        base = categoria_minima_polveri(zona)
        tipo = "polveri"
    else:
        raise ValueError("Zona non valida. Valori ammessi: 0, 1, 2 (gas) oppure 20, 21, 22 (polveri).")

    risultato = {
        "zona": zona,
        "tipo": tipo,
        "categoria_minima": base["categoria_minima"],
        "epl_minimo": base["epl_minimo"],
    }
    marcatura = f"II {base['categoria_minima']} Ex"
    if tipo == "gas":
        risultato["gruppo_gas"] = gruppo_gas
        marcatura += f" {gruppo_gas}"
    if T_autoaccensione_C is not None:
        risultato.update(classe_temperatura(T_autoaccensione_C))
        marcatura += f" {risultato['classe_temperatura']}"
    marcatura += f" {base['epl_minimo']}"
    risultato["marcatura_indicativa"] = marcatura
    return risultato
