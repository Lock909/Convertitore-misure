# ==============================================================================
# cuscinetti.py — Durata a fatica dei cuscinetti a rotolamento (ISO 281)
# ==============================================================================

import math


def durata_l10(C_kN: float, P_kN: float, tipo: str = "sfere") -> dict:
    """
    Durata nominale L10 di un cuscinetto a rotolamento (ISO 281).

    L10 = (C/P)^p   [milioni di giri]

    p = 3   per cuscinetti a sfere
    p = 10/3 per cuscinetti a rulli

    Parametri
    ----------
    C_kN : capacità di carico dinamico di base [kN] (da catalogo)
    P_kN : carico dinamico equivalente applicato [kN]
    tipo : 'sfere' o 'rulli'
    """
    if C_kN <= 0 or P_kN <= 0:
        raise ValueError("C e P devono essere > 0.")

    esponenti = {"sfere": 3.0, "rulli": 10.0 / 3.0}
    if tipo not in esponenti:
        raise ValueError("Tipo non valido. Scegli tra: 'sfere', 'rulli'.")

    p = esponenti[tipo]
    L10_milioni_giri = (C_kN / P_kN) ** p

    return {
        "L10_milioni_giri": L10_milioni_giri,
        "p": p,
        "tipo": tipo,
    }


def durata_ore(L10_milioni_giri: float, n_rpm: float) -> dict:
    """
    Conversione della durata L10 da milioni di giri a ore di funzionamento.

    L10h = (L10 * 10^6) / (60 * n)
    """
    if L10_milioni_giri <= 0 or n_rpm <= 0:
        raise ValueError("L10 e n devono essere > 0.")

    L10h = (L10_milioni_giri * 1.0e6) / (60.0 * n_rpm)

    return {
        "L10h": L10h,
        "L10h_anni_8h_die_250gg": L10h / (8.0 * 250.0),
        "n_rpm": n_rpm,
    }


def carico_dinamico_equivalente(forze: list, frazioni_tempo: list, esponente: float = 3.0) -> dict:
    """
    Carico dinamico equivalente per un ciclo di carico variabile (ISO 281).

    P_eq = (Sum(q_i * F_i^p))^(1/p)

    Parametri
    ----------
    forze          : lista dei carichi applicati in ciascuna fase [kN]
    frazioni_tempo : lista delle frazioni di tempo per ciascuna fase (somma = 1)
    esponente      : 3 per sfere, 10/3 per rulli
    """
    if len(forze) != len(frazioni_tempo):
        raise ValueError("Le liste forze e frazioni_tempo devono avere la stessa lunghezza.")
    if not forze:
        raise ValueError("Inserire almeno una fase di carico.")
    if abs(sum(frazioni_tempo) - 1.0) > 0.01:
        raise ValueError("La somma delle frazioni di tempo deve essere 1.0.")

    somma = sum(q * (F ** esponente) for F, q in zip(forze, frazioni_tempo))
    P_eq = somma ** (1.0 / esponente)

    return {
        "P_eq_kN": P_eq,
        "esponente": esponente,
    }


def fattore_durata_richiesta(L10h_richiesta: float, n_rpm: float) -> dict:
    """
    Capacità di carico dinamico minima richiesta per raggiungere una durata target.

    Restituisce il rapporto C/P minimo necessario.
    """
    if L10h_richiesta <= 0 or n_rpm <= 0:
        raise ValueError("L10h_richiesta e n devono essere > 0.")

    L10_milioni_giri = (L10h_richiesta * 60.0 * n_rpm) / 1.0e6
    rapporto_CP_sfere = L10_milioni_giri ** (1.0 / 3.0)
    rapporto_CP_rulli = L10_milioni_giri ** (3.0 / 10.0)

    return {
        "L10_milioni_giri": L10_milioni_giri,
        "rapporto_CP_sfere": rapporto_CP_sfere,
        "rapporto_CP_rulli": rapporto_CP_rulli,
    }
