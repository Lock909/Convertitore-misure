# ==============================================================================
# costi_energetici.py — Costi energetici e payback di un intervento di
#                       efficientamento (motori IE, illuminazione LED, ecc.)
# ==============================================================================

# Fattore di emissione indicativo della rete elettrica italiana [kg CO2 / kWh].
# Valore di riferimento medio: usare il dato ufficiale ISPRA dell'anno per
# rendicontazioni formali.
FATTORE_CO2_KG_KWH_DEFAULT = 0.39


def costo_annuo(potenza_kW: float, ore_anno: float, tariffa_eur_kWh: float) -> dict:
    """Energia e costo annuo di un'utenza a potenza assorbita costante."""
    if potenza_kW < 0 or ore_anno < 0 or tariffa_eur_kWh < 0:
        raise ValueError("Potenza, ore e tariffa devono essere ≥ 0.")
    energia_kWh = potenza_kW * ore_anno
    return {
        "energia_kWh_anno": energia_kWh,
        "costo_eur_anno": energia_kWh * tariffa_eur_kWh,
    }


def confronto_efficientamento(P_prima_kW: float, P_dopo_kW: float,
                              ore_anno: float, tariffa_eur_kWh: float,
                              extra_investimento_eur: float = 0.0,
                              fattore_co2_kg_kWh: float = FATTORE_CO2_KG_KWH_DEFAULT) -> dict:
    """Confronto fra una soluzione esistente e una più efficiente.

    P_prima_kW, P_dopo_kW : potenza elettrica assorbita prima/dopo [kW]
    ore_anno              : ore di funzionamento annue [h]
    tariffa_eur_kWh       : costo dell'energia [€/kWh]
    extra_investimento_eur: sovracosto della soluzione efficiente [€]
    fattore_co2_kg_kWh    : fattore di emissione [kg CO2/kWh]

    Restituisce risparmi annui (energia, denaro, CO2) e tempo di ritorno.
    """
    if min(P_prima_kW, P_dopo_kW, ore_anno, tariffa_eur_kWh) < 0:
        raise ValueError("Tutti i valori di potenza/ore/tariffa devono essere ≥ 0.")
    if extra_investimento_eur < 0:
        raise ValueError("Il sovracosto investimento deve essere ≥ 0.")

    e_prima = P_prima_kW * ore_anno
    e_dopo = P_dopo_kW * ore_anno
    risparmio_kWh = e_prima - e_dopo
    risparmio_eur = risparmio_kWh * tariffa_eur_kWh
    risparmio_co2 = risparmio_kWh * fattore_co2_kg_kWh

    # Tempo di ritorno semplice (senza attualizzazione)
    if risparmio_eur > 0 and extra_investimento_eur > 0:
        payback_anni = extra_investimento_eur / risparmio_eur
    elif extra_investimento_eur == 0:
        payback_anni = 0.0
    else:
        payback_anni = float("inf")  # nessun risparmio: non si rientra mai

    return {
        "energia_prima_kWh": e_prima,
        "energia_dopo_kWh": e_dopo,
        "costo_prima_eur": e_prima * tariffa_eur_kWh,
        "costo_dopo_eur": e_dopo * tariffa_eur_kWh,
        "risparmio_kWh_anno": risparmio_kWh,
        "risparmio_eur_anno": risparmio_eur,
        "risparmio_co2_kg_anno": risparmio_co2,
        "extra_investimento_eur": extra_investimento_eur,
        "payback_anni": payback_anni,
        "conveniente": risparmio_eur > 0,
    }


def potenza_assorbita_motore(P_mecc_kW: float, rendimento_pct: float) -> float:
    """Potenza elettrica assorbita da un motore data la potenza meccanica
    all'albero e il rendimento [%]."""
    if P_mecc_kW < 0:
        raise ValueError("La potenza meccanica deve essere ≥ 0.")
    if not (0 < rendimento_pct <= 100):
        raise ValueError("Il rendimento deve essere in (0, 100] %.")
    return P_mecc_kW / (rendimento_pct / 100.0)


def confronto_motore_ie(P_mecc_kW: float, eta_prima_pct: float, eta_dopo_pct: float,
                        ore_anno: float, tariffa_eur_kWh: float,
                        extra_investimento_eur: float = 0.0,
                        fattore_co2_kg_kWh: float = FATTORE_CO2_KG_KWH_DEFAULT) -> dict:
    """Confronto fra due motori a parità di potenza all'albero ma rendimento
    diverso (es. sostituzione IE2 → IE3/IE4)."""
    P_prima = potenza_assorbita_motore(P_mecc_kW, eta_prima_pct)
    P_dopo = potenza_assorbita_motore(P_mecc_kW, eta_dopo_pct)
    r = confronto_efficientamento(P_prima, P_dopo, ore_anno, tariffa_eur_kWh,
                                  extra_investimento_eur, fattore_co2_kg_kWh)
    r["P_assorbita_prima_kW"] = P_prima
    r["P_assorbita_dopo_kW"] = P_dopo
    return r
