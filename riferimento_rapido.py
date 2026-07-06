# ==============================================================================
# riferimento_rapido.py — Tabelle di consultazione rapida (non calcoli)
# ==============================================================================
#
# Dati di riferimento veloce per uso elettrico/industriale: colori dei
# conduttori (CEI 64-8), sezioni cavo normalizzate, e — tramite gli import
# dagli altri moduli — classi IE motori e classi IP/IK. Nessun calcolo: solo
# lookup per consultazione rapida da banco o in campo.
# ==============================================================================

# Colori normalizzati dei conduttori in impianti BT (CEI 64-8 / CEI-UNEL 00722)
COLORI_CONDUTTORI = {
    "Giallo-Verde": "Conduttore di protezione (PE) — esclusivo, non utilizzabile per altre funzioni",
    "Blu chiaro": "Neutro (N) — esclusivo nei sistemi polifase con neutro distribuito",
    "Nero": "Fase (L1/L2/L3) in impianti civili/industriali",
    "Marrone": "Fase (L1/L2/L3) — comune nei cavi bipolari/tripolari",
    "Grigio": "Fase (L1/L2/L3)",
    "Viola": "Fase, ammesso ma meno comune (es. circuiti ausiliari)",
    "Rosso": "Fase in alcuni standard non-CEI (es. cablaggi quadro a norma IEC industriale nordamericana) — evitare confusione con neutro CEI",
}

# Sezioni cavo commerciali normalizzate (rame), uso generale BT — IEC 60228
SEZIONI_CAVO_NORMALIZZATE_MM2 = [
    0.5, 0.75, 1.0, 1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120, 150, 185, 240, 300, 400,
]

# Diametri esterni approssimativi di cavi unipolari (anima + isolante PVC),
# valori indicativi per stima rapida di riempimento canalina/passerella.
DIAMETRO_ESTERNO_INDICATIVO_MM = {
    1.5: 3.5, 2.5: 4.0, 4: 4.6, 6: 5.2, 10: 6.5, 16: 7.8, 25: 9.5,
    35: 11.0, 50: 13.0, 70: 15.5, 95: 18.0, 120: 20.0, 150: 22.5, 185: 25.5, 240: 29.0,
}


def lista_colori() -> list:
    return list(COLORI_CONDUTTORI.keys())


# ==============================================================================
# Glossario — termini e acronimi usati nei vari calcolatori dell'app, raccolti
# in un unico punto di consultazione.
# ==============================================================================
GLOSSARIO = {
    "cos φ (fattore di potenza)": "Rapporto tra potenza attiva e potenza apparente. Vale 1 per carichi puramente resistivi; scende con carichi induttivi (motori, trasformatori).",
    "Ib (corrente di impiego)": "Corrente che il circuito deve effettivamente portare in servizio normale, usata per dimensionare cavo e protezione.",
    "Iz / Iz0": "Iz0 è la portata di base di un cavo a 30°C da tabella (CEI-UNEL 35024/1). Iz è la portata reale dopo i declassamenti K1/K2.",
    "K1": "Fattore di correzione della portata per temperatura ambiente diversa da 30°C (cresce se più freddo, scende se più caldo).",
    "K2": "Fattore di correzione della portata per raggruppamento di più circuiti affiancati (scende all'aumentare dei circuiti).",
    "IP (grado di protezione)": "Codice IEC 60529 a due cifre che indica la protezione di un involucro contro corpi solidi (1ª cifra) e liquidi (2ª cifra). Es. IP65.",
    "IK (grado di protezione agli urti)": "Codice IEC 62262 che indica l'energia d'urto meccanico che un involucro è in grado di sopportare, da IK00 a IK10.",
    "IE (classe di efficienza motori)": "Classificazione IEC 60034-30-1 del rendimento dei motori asincroni: IE1 (standard) fino a IE4 (super premium).",
    "TMR (Triple Modular Redundant)": "Architettura di controllo con tre canali identici che elaborano lo stesso segnale in parallelo, usata nei sistemi Mark VIe per alta disponibilità.",
    "2oo3 (voting 2 su 3)": "Logica di voting TMR: il sistema considera valido un segnale se almeno 2 dei 3 canali sono concordi; il valore mediano viene usato come riferimento.",
    "MTBF (Mean Time Between Failures)": "Tempo medio tra due guasti successivi di un componente o sistema, espresso tipicamente in anni o ore.",
    "MTTR (Mean Time To Repair)": "Tempo medio necessario per riparare/ripristinare un componente dopo un guasto.",
    "RTD (Resistance Temperature Detector)": "Sensore di temperatura basato sulla variazione di resistenza con la temperatura (es. Pt100: 100 Ω a 0°C, IEC 60751).",
    "ITS-90": "International Temperature Scale of 1990 — scala di riferimento usata per le curve normalizzate delle termocoppie.",
    "NAMUR NE43": "Raccomandazione che definisce le soglie standard di guasto (sotto/sovra-range) per segnali analogici 4-20 mA.",
    "IONet": "Rete Ethernet dedicata allo scambio dati tra i pacchi I/O e i controllori in un sistema Mark VIe.",
    "TBCI": "Scheda Mark VIe per ingressi di contatto (contact input) con isolamento di gruppo.",
    "TRLY / TRLYH1x": "Modulo relè Mark VIe usato per comandi e segnalazioni on/off verso il campo.",
    "PAIC": "Scheda Mark VIe di ingresso/uscita analogica (Process Analog Input/Output Card).",
    "c (fattore di tensione IEC 60909)": "Fattore applicato alla tensione nominale nel calcolo della corrente di cortocircuito: 1.05 per la Icc massima, 0.95 per la Icc minima.",
    "CEI 64-8": "Norma italiana per la progettazione, realizzazione e verifica degli impianti elettrici utilizzatori a bassa tensione.",
    "CEI-UNEL 35024/1": "Norma che fornisce le tabelle di portata dei cavi in funzione di isolante, posa e raggruppamento.",
    "IEC 60909": "Norma internazionale per il calcolo delle correnti di cortocircuito nei sistemi trifase.",
    "kVAR / rifasamento": "Potenza reattiva dei condensatori necessaria per portare il fattore di potenza di un impianto verso 1 (rifasamento).",
    "Vcc% (tensione di cortocircuito trafo)": "Percentuale della tensione nominale del trasformatore che, applicata al primario, fa circolare la corrente nominale con il secondario in corto: definisce la sua impedenza interna.",
    "SOC (State of Charge)": "Stato di carica di una batteria, espresso in percentuale della capacità nominale.",
    "C-rate": "Corrente di carica/scarica di una batteria espressa come multiplo della capacità nominale (1C = scarica completa in 1 ora).",
    "Effetto/legge di Peukert": "Modello empirico secondo cui la capacità realmente disponibile di una batteria diminuisce all'aumentare del C-rate di scarica.",
}


def glossario() -> dict:
    return dict(GLOSSARIO)
