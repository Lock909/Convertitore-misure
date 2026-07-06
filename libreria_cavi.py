# ==============================================================================
# libreria_cavi.py — Libreria di cavi commerciali tipici con parametri reali
# ==============================================================================
#
# Fornisce, per famiglie di cavo commerciali comuni in ambito industriale
# italiano, la resistenza in corrente continua a 20°C (R20) per sezione
# secondo IEC 60228 (valori massimi per conduttori flessibili classe 2) e una
# reattanza induttiva tipica per cavi in bassa tensione. Permette di
# precompilare i campi "datasheet" di Caduta di Tensione e Portata Cavo senza
# dover cercare manualmente i valori sul datasheet del produttore.
#
# I valori sono rappresentativi: per un progetto formale fare sempre
# riferimento al datasheet del cavo effettivamente installato.
# ==============================================================================

# Resistenza in c.c. a 20°C [Ω/km] — conduttore rame flessibile, IEC 60228 classe 2
R20_OHM_KM_IEC60228 = {
    1.5: 12.1, 2.5: 7.41, 4: 4.61, 6: 3.08, 10: 1.83, 16: 1.15,
    25: 0.727, 35: 0.524, 50: 0.387, 70: 0.268, 95: 0.193, 120: 0.153,
}

# Reattanza induttiva tipica per cavi multipolari in bassa tensione [Ω/km]
X_OHM_KM_TIPICA = 0.08

# Famiglie di cavo commerciali → isolante equivalente (per derivare K1/K2 e Iz0)
CAVI_COMMERCIALI = {
    "N1VV-K / FROR (PVC, multipolare)": "PVC",
    "FG16OR16 / FG7OR (EPR/HEPR, multipolare)": "EPR",
}


def lista_cavi_commerciali() -> list:
    return list(CAVI_COMMERCIALI.keys())


def lista_sezioni_libreria() -> list:
    return sorted(R20_OHM_KM_IEC60228.keys())


def parametri_cavo(nome_cavo: str, sezione: float) -> dict:
    """Parametri reali (isolante, R20, X) di un cavo commerciale a una data sezione."""
    if nome_cavo not in CAVI_COMMERCIALI:
        raise ValueError(f"Cavo commerciale non riconosciuto: {nome_cavo}.")
    if sezione not in R20_OHM_KM_IEC60228:
        raise ValueError(f"Sezione {sezione} mm² non presente in libreria.")
    return {
        "isolante": CAVI_COMMERCIALI[nome_cavo],
        "R20_ohm_km": R20_OHM_KM_IEC60228[sezione],
        "X_ohm_km": X_OHM_KM_TIPICA,
    }
