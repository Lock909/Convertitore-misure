# ==============================================================================
# mark_vie.py — Riferimento e calcolatori per GE Mark VIe / Mark VI / ToolboxST
# Fonti: GEH-6721_Vol_I (System Guide, architettura/ridondanza),
#        GEH-6721G Vol II (System Guide, schede I/O e specifiche)
# Nota: dati tecnici (canali, range, derating) tratti dai manuali pubblici
#       GE Vernova citati. I valori di MTBF/MTBFO complessivi del sistema
#       reale richiedono lo strumento Exida exSILentia (IEC 61508) — le
#       formule qui sono un modello semplificato a scopo didattico.
# ==============================================================================

import math

# ------------------------------------------------------------------
# 1. Riferimento schede I/O (GEH-6721G Vol II — sintesi funzionale)
# ------------------------------------------------------------------
SCHEDE_IO = {
    "CPCI":     {"nome": "Mark VIe Controller", "funzione": "Controllore principale (processore + alimentazione integrata)", "canali": "-"},
    "PAIC":     {"nome": "Analog Input/Output", "funzione": "I/O analogico: 10 ingressi + 2 uscite, ±5V/±10V/0-20mA/1-5mA", "canali": "12 (10 AI + 2 AO)"},
    "TBAI":     {"nome": "Analog Input/Output (terminal board)", "funzione": "Scheda terminale per PAIC", "canali": "12"},
    "STAI":     {"nome": "Simplex Analog Input", "funzione": "Variante semplice (simplex) per ingressi analogici", "canali": "12"},
    "PAMB":     {"nome": "Acoustic Monitoring Input", "funzione": "Monitoraggio acustico (rilevamento perdite/cavitazione)", "canali": "8"},
    "PAMC":     {"nome": "Acoustic Monitoring Input", "funzione": "Monitoraggio acustico, variante C", "canali": "8"},
    "PAOC":     {"nome": "Analog Output", "funzione": "Uscite analogiche dedicate", "canali": "8"},
    "TBAO":     {"nome": "Analog Output (terminal board)", "funzione": "Scheda terminale per PAOC", "canali": "8"},
    "PCAA":     {"nome": "Core Analog Module", "funzione": "Modulo analogico core (acquisizione centralizzata)", "canali": "-"},
    "PDIA":     {"nome": "Discrete Input", "funzione": "Ingressi digitali con isolamento di gruppo", "canali": "24"},
    "TBCI":     {"nome": "Contact Input con Group Isolation", "funzione": "Ingressi a contatto isolati a gruppo, 125/24/48 Vdc", "canali": "24"},
    "TICI":     {"nome": "Contact Input con Point Isolation", "funzione": "Ingressi a contatto con isolamento punto-punto", "canali": "24"},
    "STCI":     {"nome": "Simplex Contact Input", "funzione": "Ingressi a contatto, variante simplex", "canali": "24"},
    "PDIO":     {"nome": "Discrete Input/Output", "funzione": "I/O digitale combinato", "canali": "variabile"},
    "PDOA":     {"nome": "Discrete Output", "funzione": "Uscite digitali", "canali": "variabile"},
    "TRLYH1B":  {"nome": "Relay Output con Coil Sensing", "funzione": "Uscita a relè con monitoraggio bobina", "canali": "12"},
    "TRLYH1C":  {"nome": "Relay Output con Contact Sensing", "funzione": "Uscita a relè con monitoraggio contatto", "canali": "12"},
    "TRLYH1D":  {"nome": "Relay Output con Solenoid Integrity Sensing", "funzione": "Uscita relè con verifica integrità solenoide", "canali": "12"},
    "TRLYH1E":  {"nome": "Solid-State Relay Output", "funzione": "Uscita a relè a stato solido", "canali": "12"},
    "TRLYH1F":  {"nome": "Relay Output con TMR Contact Voting", "funzione": "Uscita relè con voting di contatto TMR (1E/2E/3E)", "canali": "12"},
    "SRLY":     {"nome": "Simplex Relay Output", "funzione": "Uscita relè semplice", "canali": "12"},
    "PEFV":     {"nome": "Electric Fuel Valve Gateway", "funzione": "Gateway per valvole combustibile elettriche", "canali": "-"},
    "PGEN":     {"nome": "Turbine-Generator Monitor Pack", "funzione": "Monitoraggio tensione/frequenza generatore e bus", "canali": "3 ingressi velocità + tensione gen/bus"},
    "PHRA":     {"nome": "HART Enabled Analog I/O", "funzione": "I/O analogico con comunicazione HART integrata", "canali": "-"},
    "PPRF":     {"nome": "PROFIBUS Master Gateway", "funzione": "Gateway master PROFIBUS DP", "canali": "-"},
    "PPRO":     {"nome": "Emergency Turbine Protection", "funzione": "Protezione di emergenza turbina (velocità/sovravelocità)", "canali": "3 ingressi velocità (2 Hz - 20 kHz)"},
    "TREA":     {"nome": "Turbine Emergency Trip", "funzione": "Scheda di trip di emergenza turbina", "canali": "-"},
    "SPRO":     {"nome": "Emergency Protection (simplex)", "funzione": "Protezione di emergenza, variante simplex", "canali": "-"},
    "PRTD":     {"nome": "RTD Input", "funzione": "Ingressi RTD (Pt100/Pt1000, Cu10, Ni120)", "canali": "8 per pacco (16 per scheda)"},
    "TRTD":     {"nome": "RTD Input (terminal board)", "funzione": "Scheda terminale per PRTD", "canali": "16"},
    "PSCA":     {"nome": "Serial Communication I/O", "funzione": "Comunicazione seriale (Modbus, ecc.)", "canali": "-"},
    "PSFD":     {"nome": "Flame Detector Power Supply", "funzione": "Alimentazione per rivelatori di fiamma", "canali": "-"},
    "PSVO":     {"nome": "Servo Control", "funzione": "Controllo servovalvole (uscite voted TMR)", "canali": "-"},
    "TSVC":     {"nome": "Servo Input/Output", "funzione": "Scheda terminale per PSVO", "canali": "-"},
    "PTCC":     {"nome": "Thermocouple Input", "funzione": "Ingressi termocoppia E/J/K/S/T(/B/N/R)", "canali": "12 per pacco"},
    "TBTC":     {"nome": "Thermocouple Input (terminal board)", "funzione": "Scheda terminale per PTCC", "canali": "12"},
    "PTUR":     {"nome": "Primary Turbine Protection", "funzione": "Protezione primaria turbina (velocità dedicata)", "canali": "-"},
    "TRPG":     {"nome": "Turbine Primary Trip", "funzione": "Scheda di trip primario turbina", "canali": "-"},
    "PVIB":     {"nome": "Vibration Monitor", "funzione": "Monitoraggio vibrazioni: proximity, seismic, velomitor, accelerometro, Keyphasor", "canali": "13 probe"},
    "TVBA":     {"nome": "Vibration Input (terminal board)", "funzione": "Scheda terminale per PVIB", "canali": "13"},
    "PDM":      {"nome": "Power Distribution Modules", "funzione": "Distribuzione alimentazione di sistema", "canali": "-"},
    "JGPA":     {"nome": "Ground and Power Board", "funzione": "Distribuzione masse e alimentazioni ausiliarie 24Vdc", "canali": "24 GND + 12 uscite 24Vdc"},
}

# ------------------------------------------------------------------
# 2. Architetture di ridondanza (GEH-6721 Vol I §1.6)
# ------------------------------------------------------------------
ARCHITETTURE_RIDONDANZA = {
    "Simplex": {
        "controllori": 1,
        "reti_ionet": 1,
        "descrizione": "Un solo controllore, una IONet. Nessuna ridondanza; nessuna riparazione online di funzioni critiche.",
    },
    "Dual": {
        "controllori": 2,
        "reti_ionet": 2,
        "descrizione": "Due controllori (R/S), due IONet, I/O singolo o TMR fanned. Entrambi i controllori ricevono gli ingressi; "
                       "ognuno trasmette in uscita sulla propria rete. Le variabili di stato sono sincronizzate (state exchange).",
    },
    "TMR": {
        "controllori": 3,
        "reti_ionet": 3,
        "descrizione": "Tre controllori (R/S/T), tre IONet, voting di stato a 2 su 3 (2oo3) tra i controllori. "
                       "Massima disponibilità e rilevamento guasti; nessun tempo di failover richiesto per continuare l'operazione.",
    },
}

# Opzioni di ridondanza I/O (Vol I §1.6.2)
RIDONDANZA_IO = {
    "SPDN (Single Pack Dual Network)": "Un solo pacco I/O su due reti — ridondanza di rete, acquisizione singola.",
    "2SPSN (Two Single Pack, Single Network)": "Due pacchi I/O indipendenti, due sensori, due reti — piena ridondanza sensore/rete.",
    "DPDN (Dual Pack, Dual Network)": "Due pacchi su scheda fanned, due reti — solo per ingressi.",
    "TPDN (Triple Pack, Dual Network)": "Tre pacchi, voting hardware in uscita, usato tipicamente in sistemi dual.",
    "TPTN (Triple Pack, Triple Network)": "Tre pacchi, tre reti — massima integrità, voting in controllore (sistemi TMR).",
    "Hot Backup": "Due pacchi, un solo attivo verso il gateway — failover automatico.",
}

# ------------------------------------------------------------------
# 3. Terminologia ControlST / ToolboxST
# ------------------------------------------------------------------
TERMINOLOGIA_TOOLBOXST = {
    "ControlST": "Suite software GE che comprende ToolboxST, WorkstationST e il firmware dei controllori Mark VIe.",
    "ToolboxST": "Applicazione di configurazione/programmazione: definisce I/O, blocchi applicativi, variabili e download verso il controllore.",
    "WorkstationST": "Applicazione HMI/SCADA per operatore (visualizzazione, trend, allarmi).",
    "ToolboxST Trender": "Strumento di trend/storico per allarmi e variabili live.",
    "CIMPLICITY": "Interfaccia utente GE per la visualizzazione di allarmi live e storici.",
    "UDH (Unit Data Highway)": "Rete di controllo a livello unità che collega controllori, HMI e storici.",
    "IONet": "Rete Ethernet dedicata tra controllore e pacchi I/O (una per ogni canale ridondante R/S/T).",
    "BPPB / BPPC": "Revisioni della scheda processore comune ai pacchi I/O Mark VIe (BPPC è l'evoluzione di BPPB).",
    "State Exchange": "Sincronizzazione delle variabili di stato interne tra controllori ridondanti (Dual/TMR) a ogni frame.",
    "Frame Rate": "Frequenza di scansione del controllore (tipicamente 100 Hz per Mark VIe).",
}

# ------------------------------------------------------------------
# 3bis. Concetti di programmazione ToolboxST
# Fonte: GEI-100746 ControlST Release Notes (cita esplicitamente la struttura
# a capitoli del manuale GEH-6700 "ToolboxST User Guide for Mark VIe", non
# incluso tra i documenti disponibili — qui sono riportati solo i concetti e
# i riferimenti di capitolo confermati dalle release notes, non il contenuto
# procedurale del manuale stesso).
# ------------------------------------------------------------------
CONCETTI_PROGRAMMAZIONE_TOOLBOXST = {
    "Task": "Contenitore applicativo di primo livello che organizza l'esecuzione di Programmi e User Block nel controllore.",
    "User Block": "Blocco funzione riutilizzabile definito dall'utente; supporta proprietà come Description, Category, Enable "
                  "ed è organizzato in una Library Container.",
    "Library Container": "Contenitore di librerie di User Block condivisibili tra progetti; il comando 'Update All Uses' "
                          "propaga le modifiche di un blocco a tutte le istanze (Instancing from Definition, Cap. 3).",
    "Block Diagram Editor (Blockware)": "Editor grafico a blocchi e fili (wire) per collegare ingressi/uscite/variabili; "
                                         "la logica è organizzata in 'logic sheet' (foglio logico) con formato pagina configurabile.",
    "Variable Rail": "Elemento grafico dell'editor a blocchi che raggruppa i collegamenti verso una variabile comune su un foglio logico.",
    "Sequential Function Chart (SFC)": "Linguaggio a sequenza (norma IEC 61131-3): diagramma di Step/Transition/Azione "
                                        "per logiche sequenziali; supporta operazioni online e pubblicazione su pagina EGD (Cap. 5).",
    "RUNG": "Blocco di logica booleana in stile ladder all'interno di un foglio logico ToolboxST.",
    "Global Variable / Program Variable / Pin Variable": "Livelli di scope delle variabili: globali (intero sistema), "
                                                           "di programma, o locali a un pin di blocco.",
    "Is Critical": "Proprietà di una variabile program/pin: se vera, genera un errore di build se la variabile non è "
                    "scritta o non pilota un ingresso — utile per individuare logiche di trip incomplete.",
    "Watch Window": "Finestra di monitoraggio live delle variabili; importabile/esportabile in formato .csv o .watch (Cap. 6/5/3 secondo prodotto).",
    "Where Used": "Funzione di ricerca che individua tutti i riferimenti (connessioni, librerie) a una variabile globale nel progetto.",
    "Compare Device / Compare to Controller": "Confronto tra la configurazione offline (ToolboxST) e quella effettivamente caricata nel controllore.",
    "Coding Practices Report": "Report di verifica buone pratiche: variabili non scritte, scritture multiple, "
                               "uscite multiple assegnate, I/O non utilizzati (GEH-6700 Cap. 6 — Reports).",
    "Auto-reconfiguration": "Funzione che ricarica automaticamente la configurazione su un pacco I/O sostituito, "
                            "senza intervento dell'utente, abilitabile dal Property Editor (General Tab).",
    "CMS (Configuration Management System)": "Sistema di versionamento/repository delle configurazioni ToolboxST "
                                              "(checkout, 'Getting the Latest Version', 'Adding a System to a Repository').",
    "Incremental Download": "Download verso il controllore delle sole modifiche rispetto all'ultima configurazione caricata "
                            "(più rapido di un download completo).",
    "System Download (full / baseload)": "Trasferimento completo dell'applicazione e dei parametri di baseload al controllore.",
    "Hardware Cabinet": "Rappresentazione nell'albero ToolboxST dell'armadio fisico contenente i pacchi I/O; "
                         "supporta drag-and-drop per la configurazione e la duplicazione.",
}

# Mappa di struttura del manuale GEH-6700 "ToolboxST User Guide for Mark VIe"
# (capitoli confermati dalle cross-reference di GEI-100746, manuale stesso non disponibile)
STRUTTURA_GEH6700_TOOLBOXST = {
    "Capitolo 2": "System Editor Menus, System Information Editor, SecurityST (ruoli e privilegi utente)",
    "Capitolo 3": "Library Container Editor (librerie di User Block, Instancing from Definition)",
    "Capitolo 5": "Sequential Function Chart (SFC) — creazione, Transition, End Transition, operazioni online, pubblicazione EGD",
    "Capitolo 6": "General Tab, Mark VIe Menus, Upgrading Modules, Hardware Tab, Reports, Watch Windows, Auto-reconfiguration",
    "Capitolo 11": "Configuration Management System (CMS) — versionamento e repository",
}

# ------------------------------------------------------------------
# 4. Specifiche tecniche schede selezionate (per i calcolatori)
# ------------------------------------------------------------------

# PAIC — Analog Input/Output (GEH-6721G p.43)
PAIC_SPAN = {
    "0-20 mA (canali 1-8)":  (0.0, 20.0, "mA"),
    "1-5 V dc (canali 1-8)": (1.0, 5.0, "V"),
    "±5 V dc (canali 1-8)":  (-5.0, 5.0, "V"),
    "±10 V dc (canali 1-8)": (-10.0, 10.0, "V"),
    "0-20 mA (canali 9-10)": (0.0, 20.0, "mA"),
    "±1 mA (canali 9-10)":   (-1.0, 1.0, "mA"),
}
PAIC_RISOLUZIONE_BIT = 16
PAIC_ACCURATEZZA_PCT_FS = 0.1

# TBCI — Contact Input con Group Isolation (GEH-6721G p.191)
TBCI_SPECS = {
    "H1 (125 Vdc)": {"V_nom": 125.0, "V_min": 100.0, "V_max": 145.0,
                      "I_normale_mA": 2.5, "I_alta_mA": 10.0},
    "H2 (24 Vdc)":  {"V_nom": 24.0, "V_min": 18.5, "V_max": 32.0,
                      "I_normale_mA": 2.5, "I_alta_mA": 9.9},
    "H3 (48 Vdc)":  {"V_nom": 48.0, "V_min": 32.0, "V_max": 64.0,
                      "I_normale_mA": 2.5, "I_alta_mA": 10.0},
}

# TRLYH1x — derating corrente relè vs temperatura (GEH-6721G p.260)
TRLY_DERATING = {
    "1E (115 Vac)": {"I_max_A": 10.0, "T_a_Imax_C": 25.0, "I_min_A": 6.0, "T_a_Imin_C": 65.0, "MTBF_anni": 50.0},
    "2E (24 Vdc)":  {"I_max_A": 10.0, "T_a_Imax_C": 40.0, "I_min_A": 7.0, "T_a_Imin_C": 65.0, "MTBF_anni": 37.0},
    "3E (125 Vdc)": {"I_max_A": 3.0,  "T_a_Imax_C": 40.0, "I_min_A": 2.0, "T_a_Imin_C": 65.0, "MTBF_anni": 47.0},
}


# ------------------------------------------------------------------
# 5. Calcolatori
# ------------------------------------------------------------------

def risoluzione_adc(span_min: float, span_max: float, bit: int = 16) -> dict:
    """Risoluzione (LSB) di un convertitore A/D dato lo span e il numero di bit."""
    if span_max <= span_min:
        raise ValueError("span_max deve essere > span_min.")
    if bit <= 0:
        raise ValueError("bit deve essere > 0.")
    livelli = 2 ** bit
    lsb = (span_max - span_min) / livelli
    return {"lsb": lsb, "livelli": livelli, "span": span_max - span_min}


def scala_paic(valore_pct: float, span_key: str) -> dict:
    """
    Conversione percentuale di scala (0-100%) in valore fisico per un canale PAIC,
    secondo gli span disponibili (GEH-6721G).
    """
    if span_key not in PAIC_SPAN:
        raise ValueError(f"Span non riconosciuto: {span_key}. Disponibili: {list(PAIC_SPAN)}")
    if not (0.0 <= valore_pct <= 100.0):
        raise ValueError("valore_pct deve essere tra 0 e 100.")

    v_min, v_max, unita = PAIC_SPAN[span_key]
    valore = v_min + (valore_pct / 100.0) * (v_max - v_min)
    res = risoluzione_adc(v_min, v_max, PAIC_RISOLUZIONE_BIT)

    return {
        "valore": valore,
        "unita": unita,
        "lsb": res["lsb"],
        "accuratezza_assoluta": (v_max - v_min) * PAIC_ACCURATEZZA_PCT_FS / 100.0,
    }


def voting_tmr_mediano(v1: float, v2: float, v3: float, tolleranza: float = 0.0) -> dict:
    """
    Voting a 2 su 3 (2oo3) per valori analogici TMR — selezione del valore mediano
    (Mark VIe usa SIFT — Software Implemented Fault Tolerance — per i segnali fanned/voted).

    tolleranza : soglia assoluta oltre la quale un canale è segnalato come sospetto
                 (differenza rispetto al valore mediano)
    """
    valori = sorted([v1, v2, v3])
    mediano = valori[1]
    scarti = {"v1": abs(v1 - mediano), "v2": abs(v2 - mediano), "v3": abs(v3 - mediano)}
    canali_sospetti = [k for k, d in scarti.items() if d > tolleranza] if tolleranza > 0 else []

    return {
        "valore_votato": mediano,
        "scarti": scarti,
        "disaccordo": max(scarti.values()) > tolleranza if tolleranza > 0 else (len(set(valori)) > 1),
        "canali_sospetti": canali_sospetti,
    }


def mtbf_serie(mtbf_list_anni: list) -> dict:
    """
    MTBF risultante di componenti in serie (logica simplex: il sistema fallisce
    se fallisce uno qualsiasi dei componenti).

    1/MTBF_sys = Σ (1/MTBF_i)
    """
    if not mtbf_list_anni or any(m <= 0 for m in mtbf_list_anni):
        raise ValueError("Tutti gli MTBF devono essere > 0.")

    inv_sum = sum(1.0 / m for m in mtbf_list_anni)
    mtbf_sys = 1.0 / inv_sum

    return {"MTBF_sistema_anni": mtbf_sys, "n_componenti": len(mtbf_list_anni)}


def disponibilita_tmr_2oo3(mtbf_canale_anni: float, mttr_ore: float = 4.0) -> dict:
    """
    Stima semplificata (modello binomiale standard per ridondanza k-su-n) della
    indisponibilità di un canale TMR votato 2oo3, rispetto al canale singolo.

    Nota: questo è un modello didattico semplificato. Il calcolo certificato
    IEC 61508 del sistema reale richiede lo strumento Exida exSILentia
    (Markov model), come indicato in GEH-6721 Vol I §1.7.1.

    p = indisponibilità del singolo canale = MTTR / MTBF
    U_TMR ≈ 3·p²·(1-p) + p³   (probabilità che ≥ 2 canali su 3 siano guasti)
    MTBF_TMR ≈ MTTR / U_TMR
    """
    if mtbf_canale_anni <= 0 or mttr_ore <= 0:
        raise ValueError("MTBF e MTTR devono essere > 0.")

    mtbf_canale_ore = mtbf_canale_anni * 8760.0
    p = mttr_ore / mtbf_canale_ore
    U_tmr = 3.0 * p**2 * (1.0 - p) + p**3
    mtbf_tmr_ore = mttr_ore / U_tmr if U_tmr > 0 else float("inf")
    mtbf_tmr_anni = mtbf_tmr_ore / 8760.0

    return {
        "indisponibilita_canale": p,
        "indisponibilita_sistema_TMR": U_tmr,
        "MTBF_canale_anni": mtbf_canale_anni,
        "MTBF_sistema_TMR_anni": mtbf_tmr_anni,
        "fattore_miglioramento": mtbf_tmr_anni / mtbf_canale_anni,
    }


def corrente_assorbita_tbci(tipo: str, n_circuiti_normali: int = 21, n_circuiti_alta: int = 3) -> dict:
    """
    Corrente e potenza assorbita da una scheda TBCI (24 canali contatto),
    secondo le specifiche GEH-6721G (i primi 21 circuiti a corrente normale,
    gli ultimi 3 a corrente elevata).
    """
    if tipo not in TBCI_SPECS:
        raise ValueError(f"Tipo non riconosciuto: {tipo}. Disponibili: {list(TBCI_SPECS)}")
    if n_circuiti_normali < 0 or n_circuiti_alta < 0:
        raise ValueError("Il numero di circuiti deve essere >= 0.")

    spec = TBCI_SPECS[tipo]
    I_tot_mA = n_circuiti_normali * spec["I_normale_mA"] + n_circuiti_alta * spec["I_alta_mA"]
    P_tot_W = I_tot_mA / 1000.0 * spec["V_nom"]

    return {
        "I_totale_mA": I_tot_mA,
        "P_totale_W": P_tot_W,
        "V_nominale": spec["V_nom"],
        "n_circuiti_totali": n_circuiti_normali + n_circuiti_alta,
    }


def corrente_derating_relay_trly(tipo: str, T_amb_C: float) -> dict:
    """
    Corrente massima ammissibile per un relè TRLYH1x in funzione della
    temperatura ambiente, con derating lineare (GEH-6721G p.260).
    """
    if tipo not in TRLY_DERATING:
        raise ValueError(f"Tipo non riconosciuto: {tipo}. Disponibili: {list(TRLY_DERATING)}")

    spec = TRLY_DERATING[tipo]
    T1, I1 = spec["T_a_Imax_C"], spec["I_max_A"]
    T2, I2 = spec["T_a_Imin_C"], spec["I_min_A"]

    if T_amb_C <= T1:
        I_amm = I1
    elif T_amb_C >= T2:
        I_amm = I2
    else:
        frac = (T_amb_C - T1) / (T2 - T1)
        I_amm = I1 - frac * (I1 - I2)

    return {
        "I_ammissibile_A": I_amm,
        "T_amb_C": T_amb_C,
        "MTBF_relay_anni": spec["MTBF_anni"],
    }
