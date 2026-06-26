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
