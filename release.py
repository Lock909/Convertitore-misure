# ==============================================================================
# release.py — Automatizza gli step meccanici di una release della PWA
# offline, per non doverli ripetere a mano (ed evitare di dimenticarne uno,
# come è già successo con la rigenerazione di gh-pages).
#
# Presuppone che tu abbia già, in quest'ordine:
#   1. Fatto le modifiche a static/pwa_offline/.
#   2. Eseguito bump_versione_pwa.py.
#   3. Aggiunto una voce "## [vNN]" in CHANGELOG.md per la nuova versione.
#   4. Committato tutto su main (git add + git commit).
#
# Da qui in poi, release.py si occupa di:
#   5. Verificare che l'albero di lavoro sia pulito.
#   6. Eseguire test_calcoli.py e verifica_sync_offline.py.
#   7. Creare il tag annotato vNN sul commit HEAD (se non esiste già).
#   8. Pushare main e il tag su origin.
#   9. Rigenerare il branch gh-pages (git subtree split) e pusharlo (force),
#      così GitHub Pages serve sempre l'ultima versione della PWA offline.
#
# Uso: python release.py
# ==============================================================================

import re
import subprocess
import sys
import unittest
from pathlib import Path

RADICE = Path(__file__).parent


def _run(cmd, check=True, **kwargs):
    print(f"$ {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=RADICE, check=check, **kwargs)


def _output(cmd):
    r = subprocess.run(cmd, cwd=RADICE, capture_output=True, text=True, check=True)
    return r.stdout.strip()


def leggi_versione() -> str:
    testo = (RADICE / "static" / "pwa_offline" / "app.js").read_text(encoding="utf-8")
    m = re.search(r'VERSIONE_APP\s*=\s*"(\d+)"', testo)
    if not m:
        sys.exit("Impossibile leggere VERSIONE_APP da static/pwa_offline/app.js.")
    return m.group(1)


def verifica_changelog(versione: str) -> None:
    testo = (RADICE / "CHANGELOG.md").read_text(encoding="utf-8")
    if f"[v{versione}]" not in testo:
        sys.exit(
            f"CHANGELOG.md non contiene una voce per v{versione}. "
            "Aggiungila e committala prima di lanciare la release."
        )


def verifica_branch_main() -> None:
    branch = _output(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if branch != "main":
        sys.exit(f"Sei sul branch '{branch}', non 'main'. Esegui la release da main.")


def verifica_albero_pulito() -> None:
    stato = _output(["git", "status", "--porcelain"])
    if stato:
        sys.exit(f"Ci sono modifiche non committate. Committale prima di rilasciare:\n{stato}")


def esegui_test() -> None:
    loader = unittest.TestLoader()
    suite = loader.discover(str(RADICE), pattern="test_calcoli.py")
    risultato = unittest.TextTestRunner(verbosity=1).run(suite)
    if not risultato.wasSuccessful():
        sys.exit("Suite di test Python fallita. Release interrotta.")
    _run([sys.executable, "verifica_sync_offline.py"])


def tag_esiste(versione: str) -> bool:
    return bool(_output(["git", "tag", "-l", f"v{versione}"]))


def main() -> None:
    versione = leggi_versione()
    print(f"Rilascio PWA offline v{versione}\n")

    verifica_branch_main()
    verifica_changelog(versione)
    verifica_albero_pulito()
    esegui_test()

    if tag_esiste(versione):
        print(f"Il tag v{versione} esiste già: salto la creazione del tag.")
    else:
        _run(["git", "tag", "-a", f"v{versione}", "-m", f"v{versione}"])

    _run(["git", "push", "origin", "main"])
    _run(["git", "push", "origin", f"v{versione}"])

    _run(["git", "branch", "-D", "gh-pages-temp"], check=False)
    _run(["git", "subtree", "split", "--prefix=static/pwa_offline", "-b", "gh-pages-temp"])
    _run(["git", "push", "origin", "gh-pages-temp:gh-pages", "--force"])
    _run(["git", "branch", "-D", "gh-pages-temp"])

    print(f"\nRelease v{versione} completata: main, tag v{versione} e gh-pages aggiornati.")


if __name__ == "__main__":
    main()
