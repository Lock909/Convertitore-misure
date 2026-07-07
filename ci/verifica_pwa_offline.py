# ==============================================================================
# ci/verifica_pwa_offline.py — Esegue la suite di test bridge della PWA
# offline (static/pwa_offline/test.js) in un browser headless (Playwright) e
# fallisce se un solo caso di regressione con valore atteso o un solo
# calcolatore dello smoke test non passa.
#
# Presuppone che un server statico serva già static/pwa_offline su
# http://localhost:8766 (vedi .github/workflows/ci.yml, job pwa-smoke-test).
#
# Uso: python ci/verifica_pwa_offline.py
# Uscita: 0 se tutti i test passano, 1 se ne fallisce almeno uno o se la
# pagina non arriva a mostrare i risultati entro il timeout.
# ==============================================================================

import sys

from playwright.sync_api import sync_playwright

URL = "http://localhost:8766/index.html?test=1"
TIMEOUT_MS = 120_000


def main() -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        errori_console = []
        page.on("pageerror", lambda e: errori_console.append(str(e)))
        page.goto(URL)
        try:
            page.wait_for_function(
                "document.querySelectorAll('#contenuto-calcolatore p').length >= 2",
                timeout=TIMEOUT_MS,
            )
        except Exception as e:
            print(f"La pagina non ha mostrato i risultati dei test entro {TIMEOUT_MS / 1000:.0f}s: {e}")
            browser.close()
            return 1

        paragrafi = page.eval_on_selector_all(
            "#contenuto-calcolatore p", "els => els.map(e => e.textContent)"
        )
        browser.close()

    print("\n".join(paragrafi))
    if errori_console:
        print("\nErrori JS non gestiti durante l'esecuzione:")
        for e in errori_console:
            print(f"  - {e}")
        return 1
    if any("falliti" in p.lower() for p in paragrafi):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
