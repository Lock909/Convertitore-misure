# ==============================================================================
# batch_cavi.py — Dimensionamento cavi in batch (più linee in una volta)
# ==============================================================================
#
# Applica a una lista di linee elettriche il dimensionamento della sezione
# minima da portata (CEI-UNEL 35024/1) e la verifica della caduta di tensione
# (CEI 64-8), restituendo una riga di risultato per ciascuna linea. Utile per
# verificare un intero quadro/impianto da un foglio dati invece che una linea
# alla volta.
# ==============================================================================

import portata_cavo as pcav
import formule

# Intestazioni attese per ciascuna linea in ingresso (ordine indicativo)
COLONNE_INGRESSO = [
    "nome", "fasi", "Ib_A", "lunghezza_m", "cos_phi",
    "isolante", "posa", "T_amb", "n_circuiti", "n_parallelo",
]


def _norm_fasi(v: str) -> str:
    s = str(v).strip().lower()
    if s in ("monofase", "mono", "1", "1f"):
        return "Monofase"
    if s in ("trifase", "tri", "3", "3f"):
        return "Trifase"
    raise ValueError(f"Sistema di fase non riconosciuto: '{v}' (usare Monofase/Trifase).")


def _norm_isolante(v: str) -> str:
    s = str(v).strip().upper()
    if "PVC" in s:
        return "PVC"
    if "EPR" in s or "XLPE" in s or "G" in s:
        return "EPR"
    raise ValueError(f"Isolante non riconosciuto: '{v}' (usare PVC/EPR).")


def dimensiona_linea(linea: dict) -> dict:
    """Dimensiona una singola linea (dict con le chiavi di COLONNE_INGRESSO).

    Restituisce un dict con sezione minima, Iz, caduta [V] e [%] ed esito.
    Solleva ValueError con messaggio chiaro se i dati non sono validi.
    """
    nome = str(linea.get("nome", "")).strip() or "(senza nome)"
    fasi = _norm_fasi(linea.get("fasi", "Trifase"))
    Ib = float(linea["Ib_A"])
    lunghezza = float(linea["lunghezza_m"])
    cos_phi = float(linea.get("cos_phi", 0.9))
    isolante = _norm_isolante(linea.get("isolante", "PVC"))
    posa = str(linea.get("posa", "C")).strip().upper()
    T_amb = float(linea.get("T_amb", 30.0))
    n_circuiti = int(linea.get("n_circuiti", 1))
    n_parallelo = int(linea.get("n_parallelo", 1))

    r_port = pcav.sezione_minima_portata(Ib, isolante, posa, T_amb, n_circuiti, n_parallelo)
    sezione = r_port["sezione_mm2"]

    dv, t_lav, rho_t, k1, k2, iz_real = formule.calcola_caduta_avanzata(
        "Rame", isolante, posa, fasi, Ib, lunghezza, sezione, cos_phi,
        T_amb, r_port["Iz0_A"], n_circuiti, n_parallelo=n_parallelo,
    )

    v_ref = 230.0 if fasi == "Monofase" else 400.0
    caduta_pct = dv / v_ref * 100.0 if dv >= 0 else None

    if caduta_pct is None:
        esito = "ERRORE: T ambiente oltre limite isolante"
    elif caduta_pct > 4.0:
        esito = "Caduta fuori norma (>4%)"
    else:
        esito = "OK"

    return {
        "nome": nome,
        "fasi": fasi,
        "Ib_A": Ib,
        "lunghezza_m": lunghezza,
        "sezione_mm2": sezione,
        "Iz_A": round(r_port["Iz_A"], 1),
        "utilizzo_pct": round(r_port["tasso_utilizzo_pct"], 1),
        "caduta_V": round(dv, 2) if dv >= 0 else None,
        "caduta_pct": round(caduta_pct, 2) if caduta_pct is not None else None,
        "esito": esito,
    }


def dimensiona_batch(linee: list) -> list:
    """Dimensiona una lista di linee. Le righe con errore non interrompono le
    altre: restituiscono un dict con la chiave 'esito' contenente l'errore."""
    risultati = []
    for i, linea in enumerate(linee, start=1):
        try:
            risultati.append(dimensiona_linea(linea))
        except (ValueError, KeyError, TypeError) as e:
            risultati.append({
                "nome": str(linea.get("nome", f"riga {i}")).strip() or f"riga {i}",
                "fasi": linea.get("fasi", ""),
                "Ib_A": linea.get("Ib_A", ""),
                "lunghezza_m": linea.get("lunghezza_m", ""),
                "sezione_mm2": None, "Iz_A": None, "utilizzo_pct": None,
                "caduta_V": None, "caduta_pct": None,
                "esito": f"ERRORE: {e}",
            })
    return risultati
