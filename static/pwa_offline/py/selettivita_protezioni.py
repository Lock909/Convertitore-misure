# ==============================================================================
# selettivita_protezioni.py — Coordinamento e selettività tra protezioni
# Riferimenti: CEI 64-8, IEC 60947-2
# ==============================================================================

import math


def verifica_selettivita_amperometrica(I_n_monte_A: float, I_n_valle_A: float, rapporto_minimo: float = 1.6) -> dict:
    """
    Verifica di selettività amperometrica tra due interruttori magnetotermici in cascata.

    Regola pratica: selettività garantita se I_n,monte / I_n,valle >= rapporto_minimo (tipico 1.6 - 2.0)
    """
    if I_n_monte_A <= 0 or I_n_valle_A <= 0:
        raise ValueError("Le correnti nominali devono essere > 0.")

    rapporto = I_n_monte_A / I_n_valle_A
    selettivo = rapporto >= rapporto_minimo
    return {
        "rapporto": rapporto,
        "rapporto_minimo": rapporto_minimo,
        "selettivo": selettivo,
        "giudizio": "Selettività amperometrica garantita" if selettivo else "Selettività NON garantita — aumentare il rapporto tra le taglie",
    }


def verifica_selettivita_differenziale(I_dn_monte_mA: float, I_dn_valle_mA: float, t_monte_ms: float = 0, t_valle_ms: float = 0) -> dict:
    """
    Verifica selettività tra due interruttori differenziali in cascata (CEI 64-8 §535.3).

    Selettività amperometrica: I_dn,monte >= 3 * I_dn,valle
    Selettività cronometrica (se applicabile, tipo S a monte): t_monte > t_valle
    """
    if I_dn_monte_mA <= 0 or I_dn_valle_mA <= 0:
        raise ValueError("Le correnti differenziali nominali devono essere > 0.")

    rapporto = I_dn_monte_mA / I_dn_valle_mA
    selettivita_amp = rapporto >= 3.0
    selettivita_crono = t_monte_ms > t_valle_ms if (t_monte_ms > 0 and t_valle_ms > 0) else None

    if selettivita_amp and (selettivita_crono is None or selettivita_crono):
        giudizio = "Selettività verificata"
    elif selettivita_amp:
        giudizio = "Selettività amperometrica OK, ma verificare i tempi di intervento (serve tipo S a monte)"
    else:
        giudizio = "Selettività NON garantita — il rapporto I_dn deve essere >= 3"

    return {
        "rapporto_Idn": rapporto,
        "selettivita_amperometrica": selettivita_amp,
        "selettivita_cronometrica": selettivita_crono,
        "giudizio": giudizio,
    }


def corrente_corto_circuito_minima(V_V: float, Z_guasto_ohm: float) -> dict:
    """
    Corrente di corto circuito minima per la verifica dell'intervento della protezione (CEI 64-8 §434).

    Icc_min = V / Z_guasto  (tensione di fase per guasto fase-neutro)
    """
    if V_V <= 0 or Z_guasto_ohm <= 0:
        raise ValueError("V e Z_guasto devono essere > 0.")

    Icc_min = V_V / Z_guasto_ohm
    return {
        "Icc_min_A": Icc_min,
        "V_V": V_V,
        "Z_guasto_ohm": Z_guasto_ohm,
    }


def tempo_intervento_curva(I_In: float, tipo_curva: str = "C") -> dict:
    """
    Stima del tempo di intervento magnetico in base alla curva caratteristica (IEC 60898 / 60947-2).

    tipo_curva: 'B' (3-5 In), 'C' (5-10 In), 'D' (10-20 In) — soglie di intervento magnetico
    """
    soglie = {"B": (3, 5), "C": (5, 10), "D": (10, 20), "K": (8, 14), "Z": (2, 3)}
    if tipo_curva not in soglie:
        raise ValueError(f"Tipo curva non valido. Scegli tra: {list(soglie.keys())}")

    s_min, s_max = soglie[tipo_curva]
    if I_In < s_min:
        zona = "Termica (ritardata, secondi-minuti)"
    elif I_In <= s_max:
        zona = "Zona di intervento magnetico (incertezza costruttiva)"
    else:
        zona = "Magnetica (istantanea, <0.1 s)"

    return {
        "tipo_curva": tipo_curva,
        "soglia_min_In": s_min,
        "soglia_max_In": s_max,
        "zona_intervento": zona,
        "I_In": I_In,
    }


CURVE_MAGNETOTERMICI = {
    "B (3-5 In)": "Carichi resistivi, linee lunghe — civile",
    "C (5-10 In)": "Uso generale — carichi misti, motori piccoli",
    "D (10-20 In)": "Forti correnti di spunto — motori, trasformatori",
    "K (8-14 In)": "Carichi induttivi (motori) — industriale",
    "Z (2-3 In)": "Carichi elettronici sensibili",
}
