# ==============================================================================
# canaline_passerelle.py — Riempimento canaline/passerelle portacavi
# ==============================================================================
#
# Verifica il grado di riempimento di una canalina o passerella portacavi a
# sezione rettangolare, a partire dai diametri esterni dei cavi posati.
# Non esiste un limite normativo unico CEI per il riempimento: la prassi
# impiantistica (rif. IEC 61537 / buona pratica installativa) raccomanda di
# restare entro circa il 50% dell'area utile per consentire la dissipazione
# termica e futuri ampliamenti.
# ==============================================================================

import math

# Soglie di riempimento indicative (buona pratica, non un limite normativo unico)
SOGLIA_OTTIMALE_PCT = 35.0
SOGLIA_MASSIMA_PCT = 50.0


def area_canalina_mm2(larghezza_mm: float, altezza_mm: float) -> float:
    if larghezza_mm <= 0 or altezza_mm <= 0:
        raise ValueError("Larghezza e altezza della canalina devono essere maggiori di zero.")
    return larghezza_mm * altezza_mm


def area_cavo_mm2(diametro_mm: float) -> float:
    if diametro_mm <= 0:
        raise ValueError("Il diametro del cavo deve essere maggiore di zero.")
    return math.pi / 4.0 * diametro_mm ** 2


def verifica_riempimento(larghezza_mm: float, altezza_mm: float, cavi: list) -> dict:
    """Verifica il riempimento di una canalina/passerella rettangolare.

    cavi : lista di tuple (diametro_esterno_mm, quantita)

    Restituisce area canalina, area totale cavi, percentuale di riempimento
    ed esito rispetto alle soglie indicative di buona pratica.
    """
    if not cavi:
        raise ValueError("Specificare almeno un cavo.")
    area_canalina = area_canalina_mm2(larghezza_mm, altezza_mm)

    area_cavi_tot = 0.0
    n_cavi_tot = 0
    for diametro_mm, quantita in cavi:
        if quantita < 1:
            raise ValueError("La quantità di ciascun cavo deve essere almeno 1.")
        area_cavi_tot += area_cavo_mm2(diametro_mm) * quantita
        n_cavi_tot += quantita

    riempimento_pct = area_cavi_tot / area_canalina * 100.0

    if riempimento_pct <= SOGLIA_OTTIMALE_PCT:
        esito = "ottimale"
    elif riempimento_pct <= SOGLIA_MASSIMA_PCT:
        esito = "accettabile"
    else:
        esito = "eccessivo"

    return {
        "area_canalina_mm2": area_canalina,
        "area_cavi_mm2": area_cavi_tot,
        "n_cavi_totale": n_cavi_tot,
        "riempimento_pct": riempimento_pct,
        "esito": esito,
    }
