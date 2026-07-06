# ==============================================================================
# bump_versione_pwa.py — Incrementa la versione della PWA offline in un colpo
# solo, in tutti i punti in cui è dichiarata:
#
#   - static/pwa_offline/app.js            -> VERSIONE_APP = "N"
#   - static/pwa_offline/index.html        -> ?v=N sui tag <script>/<link>
#   - static/pwa_offline/service-worker.js -> nomi cache calc-industriale-*-vN
#
# PERCHÉ SERVE: i dispositivi con la PWA installata si aggiornano solo se
# rilevano un service-worker.js diverso. Senza bump, una modifica pubblicata
# su GitHub/Streamlit Cloud NON arriva mai ai dispositivi già installati
# (resterebbero in silenzio sulla versione in cache).
#
# USO: python bump_versione_pwa.py     (da lanciare PRIMA di ogni push)
#
# Esegue anche la verifica di sincronizzazione dei moduli Python duplicati
# (verifica_sync_offline.py) e segnala se qualcosa è fuori allineamento.
# ==============================================================================

import re
import sys
from pathlib import Path

BASE = Path(__file__).parent
CARTELLA_PWA = BASE / "static" / "pwa_offline"


def bump() -> int:
    percorso_app = CARTELLA_PWA / "app.js"
    percorso_index = CARTELLA_PWA / "index.html"
    percorso_sw = CARTELLA_PWA / "service-worker.js"

    testo_app = percorso_app.read_text(encoding="utf-8")
    testo_index = percorso_index.read_text(encoding="utf-8")
    testo_sw = percorso_sw.read_text(encoding="utf-8")

    m_app = re.search(r'VERSIONE_APP = "(\d+)"', testo_app)
    m_sw = re.search(r"calc-industriale-app-v(\d+)", testo_sw)
    if not m_app or not m_sw:
        print("ERRORE: impossibile trovare la versione corrente in app.js o service-worker.js.")
        return 1

    # I due contatori possono divergere per ragioni storiche: si riallineano
    # entrambi al successivo del più alto.
    nuova = max(int(m_app.group(1)), int(m_sw.group(1))) + 1

    testo_app = re.sub(r'VERSIONE_APP = "\d+"', f'VERSIONE_APP = "{nuova}"', testo_app)
    testo_index = re.sub(r"\?v=\d+", f"?v={nuova}", testo_index)
    testo_sw = re.sub(r"calc-industriale-app-v\d+", f"calc-industriale-app-v{nuova}", testo_sw)
    testo_sw = re.sub(r"calc-industriale-runtime-v\d+", f"calc-industriale-runtime-v{nuova}", testo_sw)

    percorso_app.write_text(testo_app, encoding="utf-8")
    percorso_index.write_text(testo_index, encoding="utf-8")
    percorso_sw.write_text(testo_sw, encoding="utf-8")

    print(f"Versione PWA portata a v{nuova} (app.js, index.html, service-worker.js).")
    print("I dispositivi installati riceveranno l'aggiornamento alla prossima apertura online.")

    # Controllo di coerenza dei moduli Python duplicati prima della pubblicazione
    import verifica_sync_offline
    esito_sync = verifica_sync_offline.verifica()
    if esito_sync != 0:
        print("\nATTENZIONE: moduli non sincronizzati — sistemare prima di pubblicare.")
    return esito_sync


if __name__ == "__main__":
    sys.exit(bump())
