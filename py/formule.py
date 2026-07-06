# ==============================================================================
# formule.py — Calcoli elettrici (sostituisce elettrica.py)
# Normativa di riferimento: CEI 64-8, CEI UNEL 35024
# ==============================================================================

import math
from costanti import (
    RHO_RAME_20, RHO_ALLUMINIO_20, ALPHA_METALLI,
    REATTANZA_INDUTTIVA_KM, WATT_PER_HP, WATT_PER_CV, WATT_PER_BTU_H,
    TEMP_MAX_PVC, TEMP_MAX_EPR,
    SEZIONI_COMMERCIALI, INTERRUTTORI_STANDARD
)


def _valida_cos_phi(cos_phi):
    """Verifica che il fattore di potenza sia compreso tra 0 e 1."""
    if not 0.0 < cos_phi <= 1.0:
        raise ValueError("Il fattore di potenza (cos phi) deve essere compreso tra 0 e 1.")


# ------------------------------------------------------------------------------
# Legge di Ohm
# ------------------------------------------------------------------------------

def calcola_ohm(ricerca: str, input_1: float, input_2: float) -> float:
    """
    Calcola la grandezza mancante dalla Legge di Ohm (V = R·I).

    Parametri
    ----------
    ricerca : str   — 'Tensione' | 'Corrente' | 'Resistenza'
    input_1 : float — primo valore noto
    input_2 : float — secondo valore noto

    Ritorna  : float — valore calcolato
    Eccezioni: ValueError se il divisore è zero
    """
    if ricerca == "Tensione":
        return input_1 * input_2
    elif ricerca == "Corrente":
        if input_2 == 0:
            raise ValueError("R = 0: divisione impossibile.")
        return input_1 / input_2
    else:
        if input_2 == 0:
            raise ValueError("I = 0: divisione impossibile.")
        return input_1 / input_2


# ------------------------------------------------------------------------------
# Potenza elettrica e corrente assorbita
# ------------------------------------------------------------------------------

def calcola_potenza_e_corrente(sistema, volt, ampere, watt, cos_phi, calcola_cosa):
    """
    Calcola potenze (W, kW, VA, VAR, HP) oppure la corrente assorbita.

    Parametri
    ----------
    sistema      : str   — 'DC' | 'Monofase' | 'Trifase'
    volt         : float — tensione di linea [V]
    ampere       : float — corrente [A]
    watt         : float — potenza attiva [W]
    cos_phi      : float — fattore di potenza (ignorato per DC)
    calcola_cosa : str   — 'Estrai da Volt e Ampere' | 'Estrai Corrente (Ampere) da Watt'

    Ritorna
    -------
    dict con le grandezze calcolate, o None in caso di errore
    """
    fattore_trifase = math.sqrt(3) if sistema == "Trifase" else 1.0
    c_phi = 1.0 if sistema == "DC" else cos_phi

    if volt <= 0:
        return None
    if sistema != "DC":
        try:
            _valida_cos_phi(c_phi)
        except ValueError:
            return None

    if calcola_cosa == "Estrai da Volt e Ampere":
        if ampere < 0:
            return None
        p_attiva    = volt * ampere * c_phi * fattore_trifase
        p_apparente = volt * ampere * fattore_trifase
        p_reattiva  = (
            math.sqrt(max(0.0, p_apparente**2 - p_attiva**2))
            if sistema != "DC" else 0.0
        )
        return {
            "W":    p_attiva,
            "kW":   p_attiva    / 1000.0,
            "VA":   p_apparente,
            "kVA":  p_apparente / 1000.0,
            "VAR":  p_reattiva,
            "kVAR": p_reattiva  / 1000.0,
            "HP":   p_attiva    / WATT_PER_HP,
            "CV":   p_attiva    / WATT_PER_CV,
        }

    else:  # Estrai Corrente da Watt
        if watt < 0:
            return None
        denominatore = volt * c_phi * fattore_trifase
        if denominatore == 0:
            return None
        ampere_calc = watt / denominatore
        return {
            "A":   ampere_calc,
            "VA":  volt * ampere_calc * fattore_trifase,
            "kVA": (volt * ampere_calc * fattore_trifase) / 1000.0,
            "HP":  watt / WATT_PER_HP,
            "CV":  watt / WATT_PER_CV,
        }


# ------------------------------------------------------------------------------
# Convertitore potenze (kW / HP / CV / kVA / BTU/h)
# ------------------------------------------------------------------------------

def converti_potenza(valore, da_unita, a_unita, cos_phi=1.0):
    """
    Converte tra unità di potenza, incluso kVA (richiede cos_phi).

    Parametri
    ----------
    valore    : float — valore da convertire
    da_unita  : str   — unità sorgente (W, kW, MW, HP, CV, BTU/h, kVA)
    a_unita   : str   — unità destinazione
    cos_phi   : float — fattore di potenza (necessario solo con kVA)

    Ritorna
    -------
    float — valore convertito
    """
    fattori_w = {
        "W":     1.0,
        "kW":    1_000.0,
        "MW":    1_000_000.0,
        "HP":    WATT_PER_HP,
        "CV":    WATT_PER_CV,
        "BTU/h": WATT_PER_BTU_H,
        "kVA":   None,   # speciale: richiede cos_phi
    }

    unita_valide = set(fattori_w.keys())
    if da_unita not in unita_valide:
        raise ValueError(f"Unità sorgente non riconosciuta: '{da_unita}'. Valide: {sorted(unita_valide)}")
    if a_unita not in unita_valide:
        raise ValueError(f"Unità destinazione non riconosciuta: '{a_unita}'. Valide: {sorted(unita_valide)}")

    if valore < 0:
        raise ValueError("La potenza da convertire non può essere negativa.")
    if da_unita == "kVA" or a_unita == "kVA":
        _valida_cos_phi(cos_phi)

    c_phi = max(cos_phi, 0.01)   # protezione divisione per zero su kVA

    # Conversione verso Watt
    if da_unita == "kVA":
        watt = valore * 1_000.0 * c_phi
    else:
        watt = valore * fattori_w[da_unita]

    # Conversione da Watt verso destinazione
    if a_unita == "kVA":
        return watt / 1_000.0 / c_phi
    return watt / fattori_w[a_unita]


# ------------------------------------------------------------------------------
# Rifasamento industriale
# ------------------------------------------------------------------------------

def calcola_rifasamento_kvar(p_attiva_kw, cos_ini, cos_fin):
    """
    Calcola la potenza reattiva dei condensatori necessaria per correggere
    il fattore di potenza da cos_ini a cos_fin.

    Parametri
    ----------
    p_attiva_kw : float — potenza attiva dell'impianto [kW]
    cos_ini     : float — fattore di potenza attuale (es. 0.75)
    cos_fin     : float — fattore di potenza obiettivo (es. 0.95)

    Ritorna (tupla)
    ---------------
    qc_kvar : float — potenza rifasante necessaria [kVAR]
    stato   : str   — 'OK' oppure messaggio di avviso
    """
    if p_attiva_kw < 0:
        return 0.0, "Errore: la potenza attiva non può essere negativa."
    if cos_ini <= 0 or cos_fin <= 0 or cos_ini > 1 or cos_fin > 1:
        return 0.0, "Errore: fattori di potenza non validi."
    if cos_ini >= cos_fin:
        return 0.0, "Il fattore di potenza è già ottimale o superiore al target."

    tan_ini = math.tan(math.acos(cos_ini))
    tan_fin = math.tan(math.acos(cos_fin))
    qc_kvar = p_attiva_kw * (tan_ini - tan_fin)
    return qc_kvar, "OK"


# ------------------------------------------------------------------------------
# Caduta di tensione vettoriale (metodo CEI 64-8 con K1/K2)
# ------------------------------------------------------------------------------

def calcola_caduta_avanzata(
    materiale, isolante, posa,
    fasi, amp, metri, sez,
    cos_phi, temp_amb, iz_nominale, num_circuiti,
    r20_km_override=None, x_km_override=None, n_parallelo=1,
    considera_reattanza=True,
):
    """
    Calcola la caduta di tensione con correzione termica e di raggruppamento.

    Parametri
    ----------
    materiale    : str   — 'Rame' | 'Alluminio'
    isolante     : str   — stringa contenente 'PVC' oppure no (EPR/XLPE)
    posa         : str   — metodo di posa CEI
    fasi         : str   — 'Monofase' | 'Trifase'
    amp          : float — corrente di impiego Ib [A]
    metri        : float — lunghezza della linea [m]
    sez          : float — sezione del conduttore [mm²]
    cos_phi      : float — fattore di potenza
    temp_amb     : float — temperatura ambiente [°C]
    iz_nominale  : float — portata nominale da catalogo a 30°C [A] (per conduttore)
    num_circuiti : int   — numero di circuiti affiancati (per K2)
    r20_km_override : float | None — resistenza cavo a 20°C da datasheet [Ω/km].
                       Se fornita, sostituisce la resistività teorica (rho_20/sez)
                       come base per la correzione termica.
    x_km_override   : float | None — reattanza induttiva del cavo da datasheet
                       [Ω/km]. Se fornita, sostituisce la reattanza teorica fissa
                       (REATTANZA_INDUTTIVA_KM).
    n_parallelo     : int — numero di conduttori in parallelo per fase (≥ 1).
                       L'impedenza equivalente e la portata vengono divise/
                       moltiplicate di conseguenza.
    considera_reattanza : bool — se False, la reattanza X viene posta a 0 nel
                       calcolo (caduta a sola componente resistiva). Utile per
                       sezioni piccole (≤16-25 mm²) dove il contributo di X è
                       trascurabile; per sezioni grandi (≥95 mm²) è invece
                       significativo e si raccomanda di lasciarla attiva
                       (default True).

    Ritorna (tupla)
    ---------------
    dv, temp_lavoro, rho_t, k1, k2, iz_corretta
    """
    if r20_km_override is not None and r20_km_override <= 0:
        raise ValueError("La resistenza da datasheet deve essere maggiore di zero.")
    if x_km_override is not None and x_km_override < 0:
        raise ValueError("La reattanza da datasheet non può essere negativa.")
    if n_parallelo < 1:
        raise ValueError("Il numero di conduttori in parallelo deve essere almeno 1.")

    # 1. Resistività base a 20°C
    if materiale not in ("Rame", "Alluminio"):
        raise ValueError("Materiale non riconosciuto.")
    if fasi not in ("Monofase", "Trifase"):
        raise ValueError("Sistema di fase non riconosciuto.")
    if amp < 0:
        raise ValueError("La corrente di impiego non può essere negativa.")
    if metri < 0:
        raise ValueError("La lunghezza della linea non può essere negativa.")
    if sez <= 0:
        raise ValueError("La sezione del conduttore deve essere maggiore di zero.")
    if iz_nominale <= 0:
        raise ValueError("La portata nominale Iz deve essere maggiore di zero.")
    if num_circuiti < 1:
        raise ValueError("Il numero di circuiti deve essere almeno 1.")
    _valida_cos_phi(cos_phi)

    rho_20 = RHO_RAME_20 if materiale == "Rame" else RHO_ALLUMINIO_20

    # 2. Temperatura massima di esercizio dell'isolante
    temp_regime = TEMP_MAX_PVC if "PVC" in isolante else TEMP_MAX_EPR

    # 3. Coefficiente K1 — correzione per temperatura ambiente (Tabella CEI)
    tabella_k1_pvc  = {10: 1.22, 15: 1.17, 20: 1.12, 25: 1.06, 30: 1.00,
                       35: 0.94, 40: 0.87, 45: 0.79, 50: 0.71, 55: 0.61, 60: 0.50}
    tabella_k1_epr  = {10: 1.15, 15: 1.11, 20: 1.07, 25: 1.04, 30: 1.00,
                       35: 0.96, 40: 0.91, 45: 0.87, 50: 0.82, 55: 0.76, 60: 0.71}

    tabella_k1 = tabella_k1_pvc if temp_regime == TEMP_MAX_PVC else tabella_k1_epr
    chiave_k1  = int(round(temp_amb / 5.0) * 5)

    # Temperatura ambiente fuori range normativo (tabella CEI copre 10-60°C)
    if temp_amb >= temp_regime:
        # Ambiente più caldo del limite dell'isolante: cavo già fuori specifica
        # Restituiamo un valore sentinella che la UI può rilevare
        return -1.0, temp_amb, 0.0, 0.0, 0.0, 0.0

    if chiave_k1 in tabella_k1:
        k1 = tabella_k1[chiave_k1]
    else:
        # Temperatura fuori range tabella (< 10°C oppure > 60°C già gestita sopra):
        # usa il valore più vicino disponibile nella tabella
        chiave_vicina = min(tabella_k1.keys(), key=lambda k: abs(k - chiave_k1))
        k1 = tabella_k1[chiave_vicina]

    # 4. Coefficiente K2 — raggruppamento circuiti affiancati (CEI UNEL 35024)
    if num_circuiti <= 1:            k2 = 1.00
    elif num_circuiti == 2:          k2 = 0.80
    elif num_circuiti == 3:          k2 = 0.70
    elif num_circuiti == 4:          k2 = 0.65
    elif num_circuiti in (5, 6):     k2 = 0.60
    elif num_circuiti in (7, 8, 9):  k2 = 0.50
    else:                            k2 = 0.40  # 10 o più circuiti

    # 5. Portata reale dopo i declassamenti (per fase, conduttori in parallelo inclusi)
    iz_corretta    = iz_nominale * k1 * k2 * n_parallelo
    tasso_utilizzo = amp / iz_corretta if iz_corretta > 0 else 1.0

    # 6. Temperatura interna stimata del cavo
    temp_lavoro = temp_amb + (temp_regime - temp_amb) * (tasso_utilizzo ** 2)
    temp_lavoro = min(temp_lavoro, temp_regime)

    # 7. Resistività corretta alla temperatura di lavoro reale
    rho_t = rho_20 * (1.0 + ALPHA_METALLI * (temp_lavoro - 20.0))

    # 8. Calcolo vettoriale della caduta di tensione
    if r20_km_override is not None:
        # R da datasheet (riferita a 20°C): applica la stessa correzione termica
        r_km = r20_km_override * (1.0 + ALPHA_METALLI * (temp_lavoro - 20.0))
    else:
        r_km = (rho_t / sez) * 1000.0
    x_km    = (x_km_override if x_km_override is not None else REATTANZA_INDUTTIVA_KM) if considera_reattanza else 0.0
    sin_phi = math.sqrt(max(0.0, 1.0 - cos_phi**2))
    # Conduttori in parallelo per fase: l'impedenza equivalente si riduce di n_parallelo
    z_km    = ((r_km * cos_phi) + (x_km * sin_phi)) / n_parallelo
    k_fasi  = 2.0 if fasi == "Monofase" else math.sqrt(3)
    dv      = k_fasi * amp * (metri / 1000.0) * z_km

    return dv, temp_lavoro, rho_t, k1, k2, iz_corretta


# ------------------------------------------------------------------------------
# Dimensionamento protezioni (sezione cavo + interruttore)
# ------------------------------------------------------------------------------

def calcola_sezione_protezione(i_max, densita):
    """
    Determina la sezione commerciale minima e l'interruttore adeguato.

    Parametri
    ----------
    i_max   : float — corrente massima di impiego [A]
    densita : float — densità di corrente ammissibile [A/mm²]

    Ritorna (tupla)
    ---------------
    interruttore, sezione_scelta, sezione_teorica
    """
    if i_max < 0:
        raise ValueError("La corrente di impiego non può essere negativa.")
    if densita <= 0:
        raise ValueError("La densitÃ  di corrente deve essere maggiore di zero.")

    sezione_teorica = i_max / densita

    sezione_scelta = SEZIONI_COMMERCIALI[-1]
    for s in SEZIONI_COMMERCIALI:
        if s >= sezione_teorica:
            sezione_scelta = s
            break

    interruttore = INTERRUTTORI_STANDARD[-1]
    for val_i in INTERRUTTORI_STANDARD:
        if val_i >= i_max:
            interruttore = val_i
            break

    return interruttore, sezione_scelta, sezione_teorica


# ------------------------------------------------------------------------------
# Corrente di cortocircuito presunta (semplificata — IEC 60909)
# ------------------------------------------------------------------------------

def calcola_corrente_cortocircuito(
    tensione_v, potenza_trafo_kva, vcc_pct,
    materiale, sez, lunghezza_m, fasi,
    c: float = 0.95
):
    """
    Stima la corrente di cortocircuito presunta in fondo a una linea.
    Metodo semplificato (IEC 60909, fattore c = 0.95 per bassa tensione).

    Parametri
    ----------
    tensione_v        : float — tensione nominale di linea [V] (es. 400)
    potenza_trafo_kva : float — potenza nominale del trasformatore [kVA]
    vcc_pct           : float — tensione di cortocircuito trafo [%] (tipico 4-6%)
    materiale         : str   — 'Rame' | 'Alluminio'
    sez               : float — sezione conduttore [mm²]
    lunghezza_m       : float — lunghezza della linea [m]
    fasi              : str   — 'Monofase' | 'Trifase'

    Ritorna (tupla)
    ---------------
    icc_ka   : float — corrente di cc presunta [kA]
    z_tot_mo : float — impedenza totale [mΩ]
    z_trafo  : float — impedenza trafo [mΩ]
    z_cavo   : float — impedenza cavo [mΩ]
    """
    # IEC 60909 Tabella 1 — fattore di tensione c:
    #   c = 1.05  → Icc MASSIMA  (per verificare potere di interruzione interruttori)
    #   c = 0.95  → Icc MINIMA   (per coordinamento protezioni, backup protection)
    # Il valore di c viene passato dall'utente; default conservativo 0.95.

    # Impedenza del trasformatore [mΩ]
    # Ztrafo = (Vcc% / 100) × (U²_n / S_trafo)
    if tensione_v <= 0:
        raise ValueError("La tensione nominale deve essere > 0 V.")
    if potenza_trafo_kva <= 0:
        raise ValueError("La potenza del trasformatore deve essere > 0 kVA.")
    if vcc_pct <= 0:
        raise ValueError("La Vcc del trasformatore deve essere > 0%.")
    if materiale not in ("Rame", "Alluminio"):
        raise ValueError("Materiale non riconosciuto.")
    if sez <= 0:
        raise ValueError("La sezione del conduttore deve essere > 0 mm².")
    if lunghezza_m < 0:
        raise ValueError("La lunghezza della linea non può essere negativa.")
    if fasi not in ("Monofase", "Trifase"):
        raise ValueError("Sistema di fase non riconosciuto.")
    if c <= 0:
        raise ValueError("Il fattore di tensione IEC 60909 deve essere > 0.")
    z_trafo_ohm = (vcc_pct / 100.0) * (tensione_v ** 2) / (potenza_trafo_kva * 1000.0)
    z_trafo_mo  = z_trafo_ohm * 1000.0

    # Resistività base del conduttore a 20°C
    rho = RHO_RAME_20 if materiale == "Rame" else RHO_ALLUMINIO_20
    # A temperatura di cortocircuito (~160°C rame) la resistività aumenta
    # fattore correttivo conservativo: 1 + 0.004 * (160 - 20) = 1.56
    rho_cc = rho * (1.0 + ALPHA_METALLI * 140.0)

    # Impedenza del cavo [mΩ]
    k_fasi = 2.0 if fasi == "Monofase" else 1.0  # andata+ritorno per mono, solo fase per tri
    r_cavo_ohm = k_fasi * (rho_cc / sez) * lunghezza_m
    x_cavo_ohm = k_fasi * REATTANZA_INDUTTIVA_KM * (lunghezza_m / 1000.0)
    z_cavo_ohm = math.sqrt(r_cavo_ohm**2 + x_cavo_ohm**2)
    z_cavo_mo  = z_cavo_ohm * 1000.0

    z_tot_ohm = z_trafo_ohm + z_cavo_ohm
    z_tot_mo  = z_tot_ohm * 1000.0

    # Corrente di cortocircuito [kA]
    if fasi == "Trifase":
        icc = (c * tensione_v) / (math.sqrt(3) * z_tot_ohm)
    else:
        icc = (c * tensione_v) / z_tot_ohm

    return icc / 1000.0, z_tot_mo, z_trafo_mo, z_cavo_mo


# ------------------------------------------------------------------------------
# Rendimento motore: potenza uscita → ingresso → corrente assorbita
# ------------------------------------------------------------------------------

def calcola_ingresso_motore(
    p_out_kw, rendimento_pct, sistema, tensione_v, cos_phi
):
    """
    Calcola la potenza assorbita dalla rete e la corrente di linea di un motore.

    Parametri
    ----------
    p_out_kw      : float — potenza meccanica all'albero [kW]
    rendimento_pct: float — rendimento del motore [%] (es. 90.0)
    sistema       : str   — 'Monofase' | 'Trifase'
    tensione_v    : float — tensione di linea [V]
    cos_phi       : float — fattore di potenza (dalla targa motore)

    Ritorna (dict)
    ---------------
    P_in_kw, P_in_w, I_A, P_app_kva, rendimento_decimale
    """
    if p_out_kw < 0:
        return None
    if rendimento_pct <= 0 or rendimento_pct > 100:
        return None
    if tensione_v <= 0:
        return None
    try:
        _valida_cos_phi(cos_phi)
    except ValueError:
        return None

    eta = rendimento_pct / 100.0
    p_in_w   = (p_out_kw * 1000.0) / eta
    p_in_kw  = p_in_w / 1000.0

    fattore = math.sqrt(3) if sistema == "Trifase" else 1.0
    denom   = tensione_v * cos_phi * fattore
    i_a     = p_in_w / denom if denom > 0 else 0.0
    p_app   = tensione_v * i_a * fattore / 1000.0  # kVA

    return {
        "P_in_kW":  p_in_kw,
        "P_in_W":   p_in_w,
        "I_A":      i_a,
        "P_app_kVA": p_app,
        "HP_in":    p_in_w / WATT_PER_HP,
        "eta":      eta,
    }
