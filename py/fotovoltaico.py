# ==============================================================================
# fotovoltaico.py — Dimensionamento impianti fotovoltaici
# Riferimenti: CEI 0-21, norma generale dimensionamento FV
# ==============================================================================

import math


def producibilita_annua(P_picco_kWp: float, irraggiamento_kWh_m2_anno: float = 1400.0,
                         performance_ratio: float = 0.80) -> dict:
    """
    Stima della producibilità annua di un impianto fotovoltaico.

    E_anno = P_picco * (irraggiamento / 1000) * PR    [kWh/anno] (formula semplificata standard)

    Parametri
    ----------
    P_picco_kWp              : potenza di picco installata [kWp]
    irraggiamento_kWh_m2_anno: irraggiamento medio annuo sul piano dei moduli [kWh/m²/anno]
                                (Nord Italia ~1300, Centro ~1500, Sud ~1700)
    performance_ratio        : rendimento complessivo di impianto (0.75-0.85 tipico)
    """
    if P_picco_kWp <= 0 or irraggiamento_kWh_m2_anno <= 0:
        raise ValueError("P_picco e irraggiamento devono essere > 0.")
    if not (0 < performance_ratio <= 1):
        raise ValueError("Il performance ratio deve essere in (0, 1].")

    E_anno = P_picco_kWp * irraggiamento_kWh_m2_anno * performance_ratio
    ore_equivalenti = E_anno / P_picco_kWp

    return {
        "E_anno_kWh": E_anno,
        "E_mese_kWh": E_anno / 12.0,
        "ore_equivalenti_h": ore_equivalenti,
        "performance_ratio": performance_ratio,
    }


def numero_pannelli(P_picco_richiesta_kWp: float, P_pannello_Wp: float = 450.0) -> dict:
    """
    Numero di pannelli necessari per raggiungere la potenza di picco richiesta.
    """
    if P_picco_richiesta_kWp <= 0 or P_pannello_Wp <= 0:
        raise ValueError("Le potenze devono essere > 0.")

    n_pannelli = math.ceil(P_picco_richiesta_kWp * 1000.0 / P_pannello_Wp)
    P_reale_kWp = n_pannelli * P_pannello_Wp / 1000.0

    return {
        "n_pannelli": n_pannelli,
        "P_reale_kWp": P_reale_kWp,
        "P_pannello_Wp": P_pannello_Wp,
    }


def dimensiona_stringa(V_oc_pannello_V: float, n_pannelli_stringa: int,
                        V_max_inverter_V: float = 1000.0, coeff_temp_pct_C: float = -0.30,
                        T_min_C: float = -10.0) -> dict:
    """
    Verifica della tensione massima di stringa a temperatura minima (CEI 0-21 / norma costruttore).

    V_stringa(T_min) = n_pannelli * V_oc * (1 + coeff_temp/100 * (T_min - 25))
    """
    if V_oc_pannello_V <= 0 or n_pannelli_stringa < 1:
        raise ValueError("V_oc deve essere > 0 e il numero di pannelli >= 1.")

    delta_T = T_min_C - 25.0
    fattore = 1.0 + (coeff_temp_pct_C / 100.0) * delta_T
    V_stringa = n_pannelli_stringa * V_oc_pannello_V * fattore
    entro_limiti = V_stringa <= V_max_inverter_V

    return {
        "V_stringa_V": V_stringa,
        "V_max_inverter_V": V_max_inverter_V,
        "entro_limiti": entro_limiti,
        "giudizio": "OK — entro i limiti dell'inverter" if entro_limiti else "Tensione di stringa eccessiva — ridurre i pannelli in serie",
    }


def scelta_inverter(P_picco_kWp: float, rapporto_dimensionamento: float = 1.15) -> dict:
    """
    Stima della potenza nominale dell'inverter consigliata.

    P_inverter = P_picco / rapporto_dimensionamento  (DC/AC ratio tipico 1.1-1.3)
    """
    if P_picco_kWp <= 0:
        raise ValueError("P_picco deve essere > 0.")
    if rapporto_dimensionamento <= 0:
        raise ValueError("Il rapporto di dimensionamento deve essere > 0.")

    P_inverter_kW = P_picco_kWp / rapporto_dimensionamento
    return {
        "P_inverter_kW": P_inverter_kW,
        "rapporto_DC_AC": rapporto_dimensionamento,
    }


def tempo_ritorno_investimento(costo_impianto_eur: float, E_anno_kWh: float,
                                prezzo_energia_eur_kWh: float = 0.25,
                                autoconsumo_pct: float = 70.0) -> dict:
    """
    Stima semplificata del tempo di ritorno dell'investimento (payback period).
    """
    if costo_impianto_eur <= 0 or E_anno_kWh <= 0:
        raise ValueError("Costo ed energia annua devono essere > 0.")

    risparmio_anno = E_anno_kWh * (autoconsumo_pct / 100.0) * prezzo_energia_eur_kWh
    if risparmio_anno <= 0:
        raise ValueError("Il risparmio annuo calcolato è nullo: verificare i parametri.")
    payback_anni = costo_impianto_eur / risparmio_anno

    return {
        "risparmio_anno_eur": risparmio_anno,
        "payback_anni": payback_anni,
    }


IRRAGGIAMENTO_ITALIA = {
    "Nord Italia (Milano, Torino)":     1300.0,
    "Centro Italia (Roma, Firenze)":    1550.0,
    "Sud Italia (Napoli, Bari)":        1650.0,
    "Sicilia/Sardegna":                 1750.0,
}
