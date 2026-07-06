@echo off
rem ============================================================================
rem avvia_calcolatore_offline.bat - Avvia il Calcolatore Industriale offline.
rem
rem Doppio click su questo file: parte un piccolo server locale e si apre il
rem browser su http://localhost:8766.
rem
rem IMPORTANTE - come funziona la modalita' offline:
rem   1) Il PRIMO avvio richiede internet (scarica il motore di calcolo
rem      Python/Pyodide, circa 15 MB, poi resta in cache).
rem   2) Attendi che in alto compaia "Pronto - funziona offline".
rem   3) (Facoltativo) Clicca "Installa app" per averla come applicazione.
rem   4) Dai successivi avvii l'app funziona anche SENZA internet:
rem      il browser la serve dalla propria cache.
rem ============================================================================
cd /d "%~dp0"
start "" "http://localhost:8766"
python -m http.server 8766 --directory static/pwa_offline
