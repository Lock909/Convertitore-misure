# ==============================================================================
# performance_level.py — Performance Level (EN ISO 13849-1) e SIL (IEC 62061)
# ==============================================================================

import math

# Tabella K.1 EN ISO 13849-1: (Categoria, DCavg, MTTFd) → PL
# Codifica: PL = a/b/c/d/e  →  PFHd ordine di grandezza [1/h]
# PFHd tipici: PLa~1e-4, PLb~3e-6, PLc~1e-6, PLd~1e-7, PLe~1e-8

_PL_TABELLA = {
    # (categoria, DC_classe, MTTFd_classe) → PL
    # DC: "nessuna"=<60%, "bassa"=60-90%, "media"=90-99%, "alta"=>=99%
    # MTTFd: "bassa"=<10a, "media"=10-30a, "alta"=30-100a
    ("B",   "nessuna", "bassa"):  "a",
    ("B",   "nessuna", "media"):  "b",
    ("B",   "nessuna", "alta"):   "b",
    ("1",   "nessuna", "bassa"):  "b",
    ("1",   "nessuna", "media"):  "b",
    ("1",   "nessuna", "alta"):   "c",
    ("2",   "bassa",   "bassa"):  "b",
    ("2",   "bassa",   "media"):  "c",
    ("2",   "bassa",   "alta"):   "c",
    ("2",   "media",   "bassa"):  "b",
    ("2",   "media",   "media"):  "c",
    ("2",   "media",   "alta"):   "d",
    ("3",   "bassa",   "bassa"):  "b",
    ("3",   "bassa",   "media"):  "c",
    ("3",   "bassa",   "alta"):   "d",
    ("3",   "media",   "bassa"):  "c",
    ("3",   "media",   "media"):  "d",
    ("3",   "media",   "alta"):   "d",
    ("4",   "alta",    "alta"):   "e",
}

# PFHd rappresentativo [1/h] per ogni PL (valore medio dell'intervallo)
PFHD_PL = {
    "a": 1.0e-4,
    "b": 3.0e-6,
    "c": 1.0e-6,
    "d": 1.0e-7,
    "e": 1.0e-8,
}

# Corrispondenza PL → SIL (EN ISO 13849-1, Tabella 4)
PL_TO_SIL = {
    "a": "—",
    "b": "SIL 1",
    "c": "SIL 1",
    "d": "SIL 2",
    "e": "SIL 3",
}

CATEGORIE_DESCRIZIONE = {
    "B": "Struttura base — componenti conformi a norme di prodotto. Nessun requisito architetturale specifico.",
    "1": "Componenti collaudati (well-tried). Principi di sicurezza consolidati.",
    "2": "Architettura con funzione di test periodico da sistema di controllo.",
    "3": "Architettura ridondante (2 canali). Il guasto singolo non causa la perdita della funzione.",
    "4": "Architettura ridondante con DCavg ≥ 99%. Il guasto singolo deve essere rilevato prima della richiesta.",
}


def _classe_mttfd(MTTFd_anni: float) -> str:
    if MTTFd_anni < 10:
        return "bassa"
    elif MTTFd_anni < 30:
        return "media"
    else:
        return "alta"


def _classe_dc(DCavg_pct: float) -> str:
    if DCavg_pct < 60:
        return "nessuna"
    elif DCavg_pct < 90:
        return "bassa"
    elif DCavg_pct < 99:
        return "media"
    else:
        return "alta"


def calcola_PL(MTTFd_anni: float, DCavg_pct: float, categoria: str) -> dict:
    """
    Calcolo del Performance Level secondo EN ISO 13849-1 (tabella K.1).

    MTTFd_anni : Mean Time To dangerous Failure [anni] del canale
    DCavg_pct  : Diagnostic Coverage media [%]
    categoria  : "B", "1", "2", "3" o "4"
    """
    if MTTFd_anni <= 0:
        raise ValueError("MTTFd deve essere > 0.")
    if not (0.0 <= DCavg_pct <= 100.0):
        raise ValueError("DCavg deve essere in [0, 100].")
    if str(categoria) not in ("B", "1", "2", "3", "4"):
        raise ValueError("Categoria deve essere B, 1, 2, 3 o 4.")

    cat = str(categoria)
    dc_cl = _classe_dc(DCavg_pct)
    mt_cl = _classe_mttfd(MTTFd_anni)

    # Verifica coerenza categoria/DC: cat B/1 non richiedono DC
    if cat in ("B", "1") and dc_cl not in ("nessuna",):
        dc_cl = "nessuna"  # non applicabile

    key = (cat, dc_cl, mt_cl)
    PL = _PL_TABELLA.get(key, "< a")

    PFHd = PFHD_PL.get(PL, PFHD_PL["a"])
    SIL = PL_TO_SIL.get(PL, "—")

    return {
        "PL": PL,
        "SIL": SIL,
        "PFHd_1_h": PFHd,
        "categoria": cat,
        "MTTFd_anni": MTTFd_anni,
        "MTTFd_classe": mt_cl,
        "DCavg_pct": DCavg_pct,
        "DC_classe": dc_cl,
        "descrizione_categoria": CATEGORIE_DESCRIZIONE[cat],
    }


def MTTFd_da_B10d(B10d_cicli: float, n_operazioni_anno: float) -> dict:
    """
    MTTFd da B10d per componenti meccanici/elettromeccanici.

    MTTFd = B10d / (0.1 · n_op_anno)  [anni]

    B10d   : numero di cicli in cui il 10% dei componenti ha fallito in modo pericoloso
    n_op_anno : numero di operazioni per anno
    """
    if B10d_cicli <= 0 or n_operazioni_anno <= 0:
        raise ValueError("B10d e n_operazioni_anno devono essere > 0.")

    MTTFd = B10d_cicli / (0.1 * n_operazioni_anno)
    MTTFd_anni = min(MTTFd, 100.0)  # EN ISO 13849-1 limita a 100 anni

    return {
        "MTTFd_anni": MTTFd_anni,
        "MTTFd_classe": _classe_mttfd(MTTFd_anni),
        "n_operazioni_anno": n_operazioni_anno,
        "B10d_cicli": B10d_cicli,
        "nota": "Limitato a 100 anni per EN ISO 13849-1" if MTTFd > 100.0 else "",
    }


def verifica_PLr(PL_raggiunto: str, PLr_richiesto: str) -> dict:
    """
    Verifica che il PL raggiunto soddisfi il PLr richiesto dalla valutazione del rischio.
    """
    ordine = {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}
    if PL_raggiunto not in ordine or PLr_richiesto not in ordine:
        raise ValueError("PL deve essere uno tra: a, b, c, d, e.")

    conforme = ordine[PL_raggiunto] >= ordine[PLr_richiesto]
    return {
        "PL_raggiunto": PL_raggiunto,
        "PLr_richiesto": PLr_richiesto,
        "conforme": conforme,
        "giudizio": f"PL {PL_raggiunto} ≥ PLr {PLr_richiesto} — Conforme" if conforme
                    else f"PL {PL_raggiunto} < PLr {PLr_richiesto} — NON conforme: aumentare categoria o MTTFd/DC",
        "SIL_raggiunto": PL_TO_SIL.get(PL_raggiunto, "—"),
    }


DC_MISURE_TIPICHE = {
    "Nessuna diagnostica (DC = 0%)":                             0,
    "Test manuale periodico (DC ≈ 60%)":                        60,
    "Monitoraggio di 1 di 2 canali (DC ≈ 90%)":                90,
    "Test automatico all'avvio (DC ≈ 90%)":                     90,
    "Monitoraggio incrociato + test ciclico (DC ≈ 99%)":        99,
}
