# ==============================================================================
# trasduttori_pressione.py — Trasduttori di pressione con uscita 4-20 mA
# ==============================================================================

import math


# Range commerciali più comuni [bar fondo scala]
RANGE_COMMERCIALI_BAR = [10.0, 20.0, 30.0, 40.0, 50.0]


def ma_a_pressione(corrente_mA: float, fondo_scala_bar: float, P_min_bar: float = 0.0) -> dict:
    """
    Conversione segnale 4-20 mA in pressione, per trasduttore lineare.

    P = P_min + (I - 4) / (20 - 4) * (FS - P_min)

    Parametri
    ----------
    corrente_mA     : segnale di corrente misurato [mA] (4-20)
    fondo_scala_bar : pressione di fondo scala del trasduttore [bar]
    P_min_bar       : pressione minima (corrispondente a 4 mA), tipicamente 0
    """
    if not (4.0 <= corrente_mA <= 20.0):
        raise ValueError("La corrente deve essere compresa tra 4 e 20 mA.")
    if fondo_scala_bar <= P_min_bar:
        raise ValueError("Il fondo scala deve essere maggiore di P_min.")

    pct = (corrente_mA - 4.0) / 16.0
    P_bar = P_min_bar + pct * (fondo_scala_bar - P_min_bar)

    return {
        "P_bar": P_bar,
        "P_kPa": P_bar * 100.0,
        "P_mca": P_bar * 10.1972,
        "percentuale_FS": pct * 100.0,
    }


def pressione_a_ma(P_bar: float, fondo_scala_bar: float, P_min_bar: float = 0.0) -> dict:
    """
    Conversione pressione in segnale 4-20 mA per trasduttore lineare (funzione inversa).
    """
    if fondo_scala_bar <= P_min_bar:
        raise ValueError("Il fondo scala deve essere maggiore di P_min.")
    if not (P_min_bar <= P_bar <= fondo_scala_bar):
        raise ValueError(f"La pressione deve essere compresa tra {P_min_bar} e {fondo_scala_bar} bar.")

    pct = (P_bar - P_min_bar) / (fondo_scala_bar - P_min_bar)
    I_mA = 4.0 + pct * 16.0

    return {
        "I_mA": I_mA,
        "percentuale_FS": pct * 100.0,
    }


def errore_misura_trasduttore(I_misurata_mA: float, I_teorica_mA: float, fondo_scala_bar: float,
                               accuratezza_pct_FS: float = 0.5) -> dict:
    """
    Errore di misura del trasduttore rispetto al valore teorico, con verifica dell'accuratezza dichiarata.
    """
    if fondo_scala_bar <= 0:
        raise ValueError("Il fondo scala deve essere > 0.")

    errore_mA = I_misurata_mA - I_teorica_mA
    errore_pct_FS = abs(errore_mA) / 16.0 * 100.0
    P_teorica = ma_a_pressione(I_teorica_mA, fondo_scala_bar)["P_bar"]
    P_misurata = ma_a_pressione(I_misurata_mA, fondo_scala_bar)["P_bar"]

    entro_accuratezza = errore_pct_FS <= accuratezza_pct_FS

    return {
        "errore_mA": errore_mA,
        "errore_pct_FS": errore_pct_FS,
        "errore_bar": P_misurata - P_teorica,
        "entro_accuratezza": entro_accuratezza,
        "giudizio": "Entro l'accuratezza dichiarata" if entro_accuratezza else "Fuori tolleranza — verificare taratura",
    }


def caduta_tensione_loop_4_20(R_carico_ohm: float, lunghezza_cavo_m: float,
                               sezione_cavo_mm2: float = 0.75, V_alimentazione_V: float = 24.0,
                               rho_rame_ohm_mm2_m: float = 0.0178) -> dict:
    """
    Verifica della tensione disponibile al trasduttore in un loop 4-20 mA in corrente costante,
    considerando la resistenza del cavo di alimentazione (andata + ritorno) e del carico (R_shunt/PLC).

    Al massimo della scala (20 mA) la caduta di tensione sul cavo è massima.
    """
    if R_carico_ohm < 0 or lunghezza_cavo_m <= 0 or sezione_cavo_mm2 <= 0:
        raise ValueError("R_carico deve essere >= 0; lunghezza e sezione devono essere > 0.")

    R_cavo_ohm = rho_rame_ohm_mm2_m * (2.0 * lunghezza_cavo_m) / sezione_cavo_mm2
    I_max_A = 0.020  # 20 mA
    V_caduta_cavo = I_max_A * R_cavo_ohm
    V_caduta_carico = I_max_A * R_carico_ohm
    V_residua_trasduttore = V_alimentazione_V - V_caduta_cavo - V_caduta_carico

    # La maggior parte dei trasduttori 4-20mA a 2 fili richiede almeno 10-12V residui
    sufficiente = V_residua_trasduttore >= 12.0

    return {
        "R_cavo_ohm": R_cavo_ohm,
        "V_caduta_cavo_V": V_caduta_cavo,
        "V_caduta_carico_V": V_caduta_carico,
        "V_residua_trasduttore_V": V_residua_trasduttore,
        "sufficiente": sufficiente,
        "giudizio": "Tensione residua sufficiente" if sufficiente else "Tensione residua INSUFFICIENTE — aumentare sezione cavo o alimentazione",
    }
