# ==============================================================================
# costanti.py — Costanti fisiche e normative
# Fonte: CEI 64-8, IEC 60228, UNEL 35024, SI
# ==============================================================================

# --- Proprietà elettriche dei conduttori a 20°C ---
RHO_RAME_20       = 0.0175   # Resistività rame [Ω·mm²/m] a 20°C
RHO_ALLUMINIO_20  = 0.0282   # Resistività alluminio [Ω·mm²/m] a 20°C

# --- Coefficiente di temperatura dei metalli ---
ALPHA_METALLI     = 0.004    # Coefficiente termico lineare [1/°C] (rame e alluminio)

# --- Parametri di linea (valori tipici cavi BT) ---
REATTANZA_INDUTTIVA_KM = 0.08   # Reattanza induttiva tipica [Ω/km] per cavi BT

# --- Conversioni di potenza ---
WATT_PER_HP    = 745.69987       # 1 HP meccanico (britannico) = 745.7 W
WATT_PER_CV    = 735.49875       # 1 CV (cavallo vapore metrico) = 735.5 W
WATT_PER_BTU_H = 0.29307107      # 1 BTU/h = 0.293 W

# --- Temperature di esercizio massime per tipo di isolante ---
TEMP_MAX_PVC  = 70.0         # °C — cavi isolati in PVC
TEMP_MAX_EPR  = 90.0         # °C — cavi in EPR / XLPE / Gomma reticolata

# --- Pressione atmosferica standard ---
PRESSIONE_ATM_PA = 101325.0  # Pa (ISO 2533)

# --- Densità e costanti fisiche ---
DENSITA_ACQUA_KG_M3 = 1000.0          # kg/m³ a 4°C (acqua pura)
GRAVITA_STD         = 9.80665          # m/s² (accelerazione di gravità standard ISO 80000)
MCA_PER_PA          = 1.0 / (DENSITA_ACQUA_KG_M3 * GRAVITA_STD)  # m.c.a. per Pascal

# --- Sezioni commerciali normalizzate [mm²] (CEI UNEL 35011) ---
SEZIONI_COMMERCIALI = (1.5, 2.5, 4.0, 6.0, 10.0, 16.0, 25.0, 35.0, 50.0, 70.0, 95.0, 120.0)

# --- Correnti nominali interruttori magnetotermici disponibili [A] ---
INTERRUTTORI_STANDARD = (6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125)

# --- Tensioni di riferimento nominali [V] ---
TENSIONE_MONOFASE = 230.0
TENSIONE_TRIFASE  = 400.0
