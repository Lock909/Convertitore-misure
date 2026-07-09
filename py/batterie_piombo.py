# ==============================================================================
# batterie_piombo.py — Complementi avanzati per il dimensionamento di banchi
# batterie al piombo (VRLA/AGM) per UPS statiche (rif. pratica IEEE 485 /
# EN 50272-2, dati tipici dei costruttori).
#
# Per il dimensionamento di base (Ah richiesti da DOD/invecchiamento) e per
# le correnti di carica multi-rate si usa direttamente batterie_ups.py: qui
# ci sono solo i complementi che quel modulo non copre — correzione IEEE 485
# per temperatura (più precisa della semplice correzione lineare di
# batterie_ups.correzione_temperatura), numero di celle in serie, tensione
# di fine scarica e capacità effettiva secondo la legge di Peukert.
# ==============================================================================

import math

import batterie_ups

_V_CELLA_NOMINALE = 2.0    # V per cella Pb-acido (6 celle = blocco 12V tipico)
_V_FINE_SCARICA_CELLA = 1.75  # V/cella, soglia di fine scarica tipica per UPS

# Fattore di correzione capacità per temperatura ambiente (riferito a 25°C),
# valori tipici da guide costruttore/IEEE 485 per VRLA — la capacità
# disponibile diminuisce alle basse temperature, quindi serve più Ah nominali
# per compensare: Ah_corretti = Ah_calcolati_a_25°C * fattore_temperatura(T).
_FATTORE_TEMPERATURA_TABELLA = [
    (0, 1.59), (5, 1.35), (10, 1.19), (15, 1.11), (20, 1.04),
    (25, 1.00), (30, 0.96), (35, 0.91), (40, 0.87),
]


def fattore_temperatura_piombo(T_amb_C: float) -> float:
    """
    Fattore moltiplicativo di correzione della capacità per temperatura ambiente
    (interpolazione sulla tabella tipica VRLA/IEEE 485, riferita a 25°C = 1.00).
    Fuori dal campo tabellato (0-40°C) satura al valore estremo più vicino.
    """
    tab = _FATTORE_TEMPERATURA_TABELLA
    if T_amb_C <= tab[0][0]:
        return tab[0][1]
    if T_amb_C >= tab[-1][0]:
        return tab[-1][1]
    for (t_lo, f_lo), (t_hi, f_hi) in zip(tab, tab[1:]):
        if t_lo <= T_amb_C <= t_hi:
            frac = (T_amb_C - t_lo) / (t_hi - t_lo)
            return f_lo + frac * (f_hi - f_lo)
    return 1.0


def numero_celle_serie(V_bus_dc: float, V_cella_nominale: float = _V_CELLA_NOMINALE) -> dict:
    """Numero di celle in serie (arrotondato per eccesso) per ottenere la tensione di bus richiesta."""
    if V_bus_dc <= 0 or V_cella_nominale <= 0:
        raise ValueError("Le tensioni devono essere > 0 V.")
    n = math.ceil(V_bus_dc / V_cella_nominale)
    return {
        "n_celle": n,
        "V_bus_effettiva": n * V_cella_nominale,
        "V_cella_nominale": V_cella_nominale,
    }


def tensione_fine_scarica(n_celle: int, V_fine_cella: float = _V_FINE_SCARICA_CELLA) -> dict:
    """Tensione di bus alla soglia di fine scarica (allarme batteria scarica)."""
    if n_celle < 1:
        raise ValueError("Il numero di celle deve essere >= 1.")
    if V_fine_cella <= 0:
        raise ValueError("La tensione di fine scarica per cella deve essere > 0 V.")
    return {
        "V_fine_scarica_bus": n_celle * V_fine_cella,
        "n_celle": n_celle,
        "V_fine_cella": V_fine_cella,
    }


def capacita_effettiva_scarica(C_nom_10h_Ah: float, t_scarica_h: float, k_peukert: float = 1.3) -> dict:
    """
    Capacità realmente disponibile per un tempo di scarica diverso dalle 10h
    nominali (legge di Peukert). Il Pb-acido ha un effetto Peukert marcato
    (k tipico 1.2-1.4): a scariche rapide (poche decine di minuti, tipiche UPS)
    la capacità utile è sensibilmente inferiore a quella nominale a 10h.
    """
    if C_nom_10h_Ah <= 0:
        raise ValueError("La capacità nominale deve essere > 0 Ah.")
    if t_scarica_h <= 0:
        raise ValueError("Il tempo di scarica deve essere > 0 h.")

    I_nom_10h = C_nom_10h_Ah / 10.0
    I_t = I_nom_10h * (10.0 / t_scarica_h) ** (1.0 / k_peukert)
    C_eff_Ah = I_t * t_scarica_h
    return {
        "C_eff_Ah": C_eff_Ah,
        "I_scarica_A": I_t,
        "t_scarica_h": t_scarica_h,
        "C_nom_10h_Ah": C_nom_10h_Ah,
        "k_peukert": k_peukert,
    }


def dimensionamento_completo(
    P_carico_W: float,
    t_autonomia_h: float,
    V_bus_dc: float,
    rendimento_inverter: float = 0.90,
    DOD: float = 0.80,
    fattore_invecchiamento: float = 1.25,
    T_amb_C: float = 20.0,
    tasso_carica_c: float = 0.10,
) -> dict:
    """
    Dimensionamento completo di un banco VRLA/AGM in un'unica chiamata: si
    appoggia a batterie_ups.dimensiona_banco() per la capacità di base (da
    DOD e invecchiamento) e applica sopra la correzione IEEE 485 per
    temperatura, il numero di celle in serie, la tensione di fine scarica e
    la corrente di carica boost.
    """
    base = batterie_ups.dimensiona_banco(
        P_carico_W, t_autonomia_h, V_bus_dc,
        eta_inverter=rendimento_inverter, DOD=DOD,
        fattore_invecchiamento=fattore_invecchiamento,
    )
    f_temp = fattore_temperatura_piombo(T_amb_C)
    Ah_corretti = base["C_nominale_Ah"] * f_temp

    r_celle = numero_celle_serie(V_bus_dc)
    r_fine = tensione_fine_scarica(r_celle["n_celle"])

    if tasso_carica_c <= 0:
        raise ValueError("Il tasso di carica deve essere > 0.")

    risultato = {}
    risultato.update(base)
    risultato["fattore_temperatura"] = f_temp
    risultato["T_amb_C"] = T_amb_C
    risultato["Ah_corretti_temperatura"] = Ah_corretti
    risultato.update(r_celle)
    risultato.update(r_fine)
    risultato["I_carica_A"] = Ah_corretti * tasso_carica_c
    risultato["tasso_carica_c"] = tasso_carica_c
    return risultato
