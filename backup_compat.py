# ==============================================================================
# backup_compat.py — Conversione dei progetti salvati tra il formato dell'app
# Streamlit (data/device_prefs/*.json, chiave "projects") e il formato di
# backup della versione offline/PWA ("backup-calcolatore-industriale").
#
# Permette di esportare i progetti da una versione e importarli nell'altra con
# lo stesso file JSON. Le due app salvano voci con struttura diversa:
#
#   Streamlit: {"strumento": str, "dati": {etichetta: valore}, "timestamp": "YYYY-MM-DD HH:MM:SS"}
#   PWA:       {"id": str, "timestamp": ISO-8601, "titolo": str,
#               "input": {...}, "output": {...}, "nota": str (opzionale)}
#
# La conversione è per consultazione/archivio: le voci importate si leggono e
# si esportano normalmente, ma il pulsante "riapri questo calcolo" della PWA
# funziona solo per le voci nate nella PWA (le voci Streamlit non hanno un
# calcId corrispondente).
# ==============================================================================

import json
import hashlib
from datetime import datetime

TIPO_BACKUP = "backup-calcolatore-industriale"
_FORMATO_TS_STREAMLIT = "%Y-%m-%d %H:%M:%S"


def _ts_streamlit_a_iso(ts: str) -> str:
    """'2026-07-02 15:30:00' -> '2026-07-02T15:30:00' (parse JS-compatibile)."""
    try:
        return datetime.strptime(ts, _FORMATO_TS_STREAMLIT).isoformat()
    except (ValueError, TypeError):
        return datetime.now().isoformat()


def _iso_a_ts_streamlit(iso: str) -> str:
    """ISO-8601 (anche con 'Z') -> formato timestamp Streamlit."""
    try:
        return datetime.fromisoformat(str(iso).replace("Z", "+00:00")).strftime(_FORMATO_TS_STREAMLIT)
    except (ValueError, TypeError):
        return datetime.now().strftime(_FORMATO_TS_STREAMLIT)


def _id_deterministico(nome_progetto: str, voce: dict) -> str:
    """Id stabile per una voce Streamlit: esportando due volte lo stesso backup
    si ottengono gli stessi id, così l'import nella PWA non crea duplicati."""
    firma = json.dumps([nome_progetto, voce.get("strumento"), voce.get("timestamp"),
                        voce.get("dati")], ensure_ascii=False, sort_keys=True, default=str)
    return "web_" + hashlib.sha1(firma.encode("utf-8")).hexdigest()[:16]


def esporta_progetti_per_pwa(projects: dict) -> dict:
    """Converte i progetti Streamlit nel formato di backup della PWA.

    projects : dict come in _load_device_data()["projects"]
    Ritorna il dict pronto per json.dumps (stesso schema del backup PWA).
    """
    progetti_pwa = {}
    for nome, voci in (projects or {}).items():
        convertite = []
        for voce in voci:
            dati = dict(voce.get("dati") or {})
            nota = dati.pop("Note", None)
            nuova = {
                "id": _id_deterministico(nome, voce),
                "timestamp": _ts_streamlit_a_iso(voce.get("timestamp", "")),
                "titolo": voce.get("strumento", "Calcolo"),
                "input": {},
                "output": dati,
            }
            if nota:
                nuova["nota"] = str(nota)
            convertite.append(nuova)
        progetti_pwa[nome] = convertite

    return {
        "tipo": TIPO_BACKUP,
        "versione": 1,
        "esportatoIl": datetime.now().isoformat(),
        "cronologia": [],  # la cronologia Streamlit (ultimi strumenti usati) non è un elenco di calcoli
        "progetti": progetti_pwa,
    }


def _valore_piatto(v):
    """Valori annidati (liste/dict, es. curve batteria) -> stringa JSON compatta,
    così la voce resta leggibile e riesportabile dall'app Streamlit."""
    if isinstance(v, (list, dict)):
        return json.dumps(v, ensure_ascii=False)
    return v


def importa_backup_pwa(backup: dict, projects: dict) -> int:
    """Unisce i progetti di un backup PWA nei progetti Streamlit (modifica
    `projects` sul posto). Ritorna il numero di voci aggiunte.

    Le voci già presenti (stesso strumento e stesso timestamp nello stesso
    progetto) non vengono duplicate. Solleva ValueError se il file non è un
    backup riconosciuto.
    """
    if not isinstance(backup, dict) or backup.get("tipo") != TIPO_BACKUP:
        raise ValueError("Il file non sembra un backup di questa app (campo 'tipo' mancante o errato).")

    aggiunte = 0
    for nome, voci in (backup.get("progetti") or {}).items():
        dest = projects.setdefault(nome, [])
        firme = {(d.get("strumento"), d.get("timestamp")) for d in dest}
        for voce in voci:
            dati = {}
            for k, v in (voce.get("input") or {}).items():
                dati[f"input.{k}"] = _valore_piatto(v)
            for k, v in (voce.get("output") or {}).items():
                dati[k] = _valore_piatto(v)
            if voce.get("nota"):
                dati["Note"] = str(voce["nota"])
            ts = _iso_a_ts_streamlit(voce.get("timestamp"))
            strumento = voce.get("titolo") or "Calcolo (import offline)"
            if (strumento, ts) in firme:
                continue
            dest.append({"strumento": strumento, "dati": dati, "timestamp": ts})
            firme.add((strumento, ts))
            aggiunte += 1
    return aggiunte
