# ==============================================================================
# verifica_sync_offline.py — Confronta i file duplicati tra la root del
# progetto e static/pwa_offline/, per rilevare divergenze accidentali quando
# si modifica un file su un solo lato (es. si aggiorna formule.py ma ci si
# dimentica di ricopiarlo nella cartella della PWA offline).
#
# Uso: python verifica_sync_offline.py
# Uscita: 0 se tutto sincronizzato, 1 se trova almeno una divergenza.
#
# Nota: bridge.py non è incluso nel confronto perché esiste solo lato PWA
# (è l'adattatore JSON-friendly verso Pyodide, non ha un equivalente nella
# root del progetto).
# ==============================================================================

import sys
from pathlib import Path

RADICE = Path(__file__).parent
CARTELLA_OFFLINE = RADICE / "static" / "pwa_offline" / "py"

# File duplicati che non sono moduli .py sotto py/ (percorso relativo alla
# root del progetto -> percorso relativo a static/pwa_offline/).
ALTRI_FILE_DUPLICATI = [
    ("CHANGELOG.md", "CHANGELOG.md"),
]

MODULI_DUPLICATI = [
    "costanti.py",
    "formule.py",
    "portata_cavo.py",
    "batterie_litio.py",
    "strumentazione.py",
    "mark_vie.py",
    "grado_protezione_ip.py",
    "motore_asincrono.py",
    "canaline_passerelle.py",
    "riferimento_rapido.py",
    "componenti_passivi.py",
    "trasformatore.py",
    "circuito_rlc.py",
    "armonie_thd.py",
    "batterie_ups.py",
    "impianto_terra.py",
    "selettivita_protezioni.py",
    "fotovoltaico.py",
    "gruppo_elettrogeno.py",
    "quadro_elettrico.py",
    "rifasamento_condensatori.py",
    "caduta_tensione_bt.py",
    "avviamento_motore.py",
    "dissipatore.py",
    "illuminotecnica.py",
    "libreria_cavi.py",
    "batch_cavi.py",
    "costi_energetici.py",
    "vibrazioni.py",
    "resistenza_materiali.py",
    "bulloneria.py",
    "cuscinetti.py",
    "molle.py",
    "ruote_dentate.py",
    "alberi_torsione.py",
    "saldature.py",
    "trasmissioni.py",
    "nastri_trasportatori.py",
    "pompe.py",
    "perdite_carico.py",
    "perdite_carico_distribuite.py",
    "scambiatori.py",
    "isolamento_termico.py",
    "condotte_hvac.py",
    "serbatoi.py",
    "valvole_controllo.py",
    "tubazione_pressione.py",
    "pneumatica.py",
    "trasduttori_pressione.py",
    "rumore_industriale.py",
    "performance_level.py",
    "automazione.py",
    "idraulica.py",
    "fulmini.py",
    "batterie_piombo.py",
    "misuratori_portata.py",
    "antincendio.py",
]


def verifica() -> int:
    divergenze = []
    mancanti = []

    for nome in MODULI_DUPLICATI:
        percorso_radice = RADICE / nome
        percorso_offline = CARTELLA_OFFLINE / nome

        if not percorso_radice.exists():
            mancanti.append(f"{nome}: manca nella root del progetto ({percorso_radice})")
            continue
        if not percorso_offline.exists():
            mancanti.append(f"{nome}: manca in static/pwa_offline/py/ ({percorso_offline})")
            continue

        contenuto_radice = percorso_radice.read_text(encoding="utf-8")
        contenuto_offline = percorso_offline.read_text(encoding="utf-8")
        if contenuto_radice != contenuto_offline:
            divergenze.append(nome)

    for nome_radice, nome_offline in ALTRI_FILE_DUPLICATI:
        percorso_radice = RADICE / nome_radice
        percorso_offline = RADICE / "static" / "pwa_offline" / nome_offline

        if not percorso_radice.exists():
            mancanti.append(f"{nome_radice}: manca nella root del progetto ({percorso_radice})")
            continue
        if not percorso_offline.exists():
            mancanti.append(f"{nome_radice}: manca in static/pwa_offline/ ({percorso_offline})")
            continue

        contenuto_radice = percorso_radice.read_text(encoding="utf-8")
        contenuto_offline = percorso_offline.read_text(encoding="utf-8")
        if contenuto_radice != contenuto_offline:
            divergenze.append(nome_radice)

    totale = len(MODULI_DUPLICATI) + len(ALTRI_FILE_DUPLICATI)
    if not divergenze and not mancanti:
        print(f"OK — {totale} file sincronizzati tra root e static/pwa_offline/.")
        return 0

    percorso_offline_di = {nome: f"static/pwa_offline/py/{nome}" for nome in MODULI_DUPLICATI}
    percorso_offline_di.update({n_radice: f"static/pwa_offline/{n_offline}" for n_radice, n_offline in ALTRI_FILE_DUPLICATI})

    if mancanti:
        print("File mancanti:")
        for m in mancanti:
            print(f"  - {m}")
    if divergenze:
        print("File DIVERGENTI (contenuto diverso tra root e static/pwa_offline/):")
        for d in divergenze:
            print(f"  - {d}")
        print("\nPer risincronizzare, copia il file aggiornato nell'altra posizione, es.:")
        for d in divergenze:
            print(f"  cp \"{d}\" \"{percorso_offline_di[d]}\"    # (o viceversa, a seconda di quale versione è quella corretta)")

    return 1


if __name__ == "__main__":
    sys.exit(verifica())
