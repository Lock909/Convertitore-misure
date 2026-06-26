# ==============================================================================
# portata_cavo.py — Portata e sezione minima cavi (CEI-UNEL 35024/1)
# ==============================================================================
#
# Determina la sezione minima di un cavo in rame a partire dalla corrente di
# impiego Ib, dal metodo di posa, dalla temperatura ambiente e dal numero di
# circuiti raggruppati, secondo lo schema CEI-UNEL 35024/1 (IEC 60364-5-52).
#
# I valori Iz0 sono portate di base [A] a 30 °C, conduttore in RAME, con
# 3 conduttori attivi caricati (caso trifase, conservativo). Sono valori
# rappresentativi della tabella CEI-UNEL 35024/1: per il dimensionamento
# formale va consultata la tabella ufficiale relativa al cavo specifico.
# ==============================================================================

# Portate di base Iz0 [A] — rame, 30 °C, 3 conduttori caricati
# Chiave esterna: (isolante, metodo di posa)
IZ0_CEI_UNEL = {
    ("PVC", "B1"): {1.5: 15.5, 2.5: 21, 4: 28, 6: 36, 10: 50, 16: 68, 25: 89, 35: 110, 50: 134, 70: 171, 95: 207, 120: 239},
    ("PVC", "B2"): {1.5: 15, 2.5: 20, 4: 27, 6: 34, 10: 46, 16: 62, 25: 80, 35: 99, 50: 118, 70: 149, 95: 179, 120: 206},
    ("PVC", "C"):  {1.5: 17.5, 2.5: 24, 4: 32, 6: 41, 10: 57, 16: 76, 25: 96, 35: 119, 50: 144, 70: 184, 95: 223, 120: 259},
    ("PVC", "E"):  {1.5: 18.5, 2.5: 25, 4: 34, 6: 43, 10: 60, 16: 80, 25: 101, 35: 126, 50: 153, 70: 196, 95: 238, 120: 276},
    ("EPR", "B1"): {1.5: 20, 2.5: 27, 4: 37, 6: 48, 10: 66, 16: 89, 25: 118, 35: 145, 50: 175, 70: 224, 95: 271, 120: 314},
    ("EPR", "B2"): {1.5: 19.5, 2.5: 26, 4: 35, 6: 44, 10: 60, 16: 80, 25: 105, 35: 128, 50: 154, 70: 194, 95: 233, 120: 268},
    ("EPR", "C"):  {1.5: 23, 2.5: 31, 4: 42, 6: 54, 10: 75, 16: 100, 25: 127, 35: 158, 50: 192, 70: 246, 95: 298, 120: 346},
    ("EPR", "E"):  {1.5: 24, 2.5: 33, 4: 45, 6: 58, 10: 80, 16: 107, 25: 135, 35: 169, 50: 207, 70: 268, 95: 328, 120: 383},
}

# Descrizione dei metodi di posa di riferimento (CEI 64-8 / IEC 60364-5-52)
METODI_POSA = {
    "B1": "Conduttori in tubo (protettivo) a parete o incassato",
    "B2": "Cavo multipolare in tubo (protettivo) a parete o incassato",
    "C":  "Cavo (mono/multipolare) a vista a parete o su passerella non perforata",
    "E":  "Cavo multipolare in aria libera / passerella perforata",
}

# K1 — fattore di correzione per temperatura ambiente (diverso da 30 °C)
_K1_PVC = {10: 1.22, 15: 1.17, 20: 1.12, 25: 1.06, 30: 1.00,
           35: 0.94, 40: 0.87, 45: 0.79, 50: 0.71, 55: 0.61, 60: 0.50}
_K1_EPR = {10: 1.15, 15: 1.11, 20: 1.07, 25: 1.04, 30: 1.00,
           35: 0.96, 40: 0.91, 45: 0.87, 50: 0.82, 55: 0.76, 60: 0.71}

# K2 — fattore di raggruppamento (circuiti affiancati, CEI-UNEL 35024)
_K2_RAGGRUPPAMENTO = {1: 1.00, 2: 0.80, 3: 0.70, 4: 0.65, 5: 0.60, 6: 0.60,
                      7: 0.50, 8: 0.50, 9: 0.50}


def lista_isolanti() -> list:
    return ["PVC", "EPR"]


def lista_metodi_posa() -> list:
    return list(METODI_POSA.keys())


def lista_sezioni_disponibili() -> list:
    return sorted(IZ0_CEI_UNEL[("PVC", "B1")].keys())


def _k1(isolante: str, T_amb: float) -> float:
    tab = _K1_PVC if isolante == "PVC" else _K1_EPR
    chiave = int(round(T_amb / 5.0) * 5)
    if chiave in tab:
        return tab[chiave]
    chiave_vicina = min(tab.keys(), key=lambda k: abs(k - chiave))
    return tab[chiave_vicina]


def _k2(n_circuiti: int) -> float:
    if n_circuiti <= 1:
        return 1.00
    return _K2_RAGGRUPPAMENTO.get(n_circuiti, 0.40)  # 10+ circuiti


def portata_corretta(sezione: float, isolante: str, posa: str,
                     T_amb: float = 30.0, n_circuiti: int = 1) -> dict:
    """Portata effettiva Iz di una sezione data, con i declassamenti applicati.

    sezione    : sezione commerciale [mm²]
    isolante   : "PVC" | "EPR"
    posa       : "B1" | "B2" | "C" | "E"
    T_amb      : temperatura ambiente [°C]
    n_circuiti : numero di circuiti raggruppati
    """
    chiave = (isolante, posa)
    if chiave not in IZ0_CEI_UNEL:
        raise ValueError(f"Combinazione isolante/posa non disponibile: {isolante}/{posa}.")
    tabella = IZ0_CEI_UNEL[chiave]
    if sezione not in tabella:
        raise ValueError(f"Sezione {sezione} mm² non in tabella per {isolante}/{posa}.")

    iz0 = tabella[sezione]
    k1 = _k1(isolante, T_amb)
    k2 = _k2(int(n_circuiti))
    iz = iz0 * k1 * k2
    return {
        "sezione_mm2": sezione,
        "Iz0_A": iz0,
        "K1": k1,
        "K2": k2,
        "Iz_A": iz,
        "isolante": isolante,
        "posa": posa,
    }


def sezione_minima_portata(Ib: float, isolante: str, posa: str,
                           T_amb: float = 30.0, n_circuiti: int = 1,
                           n_parallelo: int = 1) -> dict:
    """Sezione minima il cui Iz declassato è ≥ Ib (corrente di impiego).

    n_parallelo : numero di conduttori in parallelo per fase (≥ 1). La corrente
                  di impiego viene ripartita equamente fra i conduttori in
                  parallelo, e la portata totale risulta moltiplicata di
                  conseguenza.

    Restituisce la sezione scelta, la sua portata effettiva e il tasso di
    utilizzo. Solleva ValueError se nessuna sezione in tabella è sufficiente.
    """
    if Ib <= 0:
        raise ValueError("La corrente di impiego Ib deve essere > 0.")
    if n_parallelo < 1:
        raise ValueError("Il numero di conduttori in parallelo deve essere almeno 1.")
    chiave = (isolante, posa)
    if chiave not in IZ0_CEI_UNEL:
        raise ValueError(f"Combinazione isolante/posa non disponibile: {isolante}/{posa}.")

    k1 = _k1(isolante, T_amb)
    k2 = _k2(int(n_circuiti))
    if k1 <= 0 or k2 <= 0:
        raise ValueError("Coefficiente di declassamento nullo: condizioni fuori campo.")

    ib_per_conduttore = Ib / n_parallelo
    # Portata di base minima richiesta perché Iz0·K1·K2 ≥ Ib per conduttore
    iz0_richiesto = ib_per_conduttore / (k1 * k2)

    tabella = IZ0_CEI_UNEL[chiave]
    for sez in sorted(tabella.keys()):
        if tabella[sez] >= iz0_richiesto:
            iz_per_conduttore = tabella[sez] * k1 * k2
            iz_tot = iz_per_conduttore * n_parallelo
            return {
                "sezione_mm2": sez,
                "Ib_A": Ib,
                "Iz0_A": tabella[sez],
                "Iz0_richiesto_A": iz0_richiesto,
                "K1": k1,
                "K2": k2,
                "Iz_A": iz_tot,
                "n_parallelo": n_parallelo,
                "tasso_utilizzo_pct": Ib / iz_tot * 100.0,
                "isolante": isolante,
                "posa": posa,
            }

    sez_max = max(tabella.keys())
    raise ValueError(
        f"Nessuna sezione in tabella (max {sez_max:.0f} mm²) è sufficiente per "
        f"Ib={Ib:.1f} A nelle condizioni date (serve Iz0 ≥ {iz0_richiesto:.1f} A per conduttore). "
        f"Usare più conduttori in parallelo o un metodo di posa più favorevole."
    )


def verifica_cavo_personalizzato(Ib: float, iz0_datasheet: float, isolante: str,
                                 T_amb: float = 30.0, n_circuiti: int = 1,
                                 n_parallelo: int = 1) -> dict:
    """Verifica l'idoneità di un cavo specifico (Iz0 da datasheet del produttore)
    a portare la corrente di impiego Ib, applicando i declassamenti K1/K2.

    A differenza di sezione_minima_portata, qui la portata di base Iz0 non viene
    presa dalla tabella CEI-UNEL ma fornita direttamente dall'utente (es. cavo
    speciale, schermato, o dato di targa del produttore).

    n_parallelo : numero di conduttori in parallelo per fase (≥ 1); Iz0 è la
                  portata del singolo conduttore, la portata totale viene
                  moltiplicata di conseguenza.
    """
    if Ib <= 0:
        raise ValueError("La corrente di impiego Ib deve essere > 0.")
    if iz0_datasheet <= 0:
        raise ValueError("La portata Iz0 da datasheet deve essere > 0.")
    if n_parallelo < 1:
        raise ValueError("Il numero di conduttori in parallelo deve essere almeno 1.")

    k1 = _k1(isolante, T_amb)
    k2 = _k2(int(n_circuiti))
    if k1 <= 0 or k2 <= 0:
        raise ValueError("Coefficiente di declassamento nullo: condizioni fuori campo.")

    iz = iz0_datasheet * k1 * k2 * n_parallelo
    return {
        "Ib_A": Ib,
        "Iz0_A": iz0_datasheet,
        "K1": k1,
        "K2": k2,
        "Iz_A": iz,
        "n_parallelo": n_parallelo,
        "tasso_utilizzo_pct": Ib / iz * 100.0,
        "idoneo": iz >= Ib,
        "isolante": isolante,
    }
