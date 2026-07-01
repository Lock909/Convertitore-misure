# ==============================================================================
# mark_vie.py — Riferimento e calcolatori per GE Mark VIe / Mark VI / ToolboxST
# Fonti: GEH-6721_Vol_I (System Guide, architettura/ridondanza),
#        GEH-6721G Vol II (System Guide, schede I/O e specifiche),
#        manuali ControlST/WorkstationST (GEH-67xx / GEI-100xxx / GHT-200030)
#        della cartella Documentation/ — citati per ciascun componente.
# Nota: dati tecnici (canali, range, derating) tratti dai manuali pubblici
#       GE Vernova citati. I valori di MTBF/MTBFO complessivi del sistema
#       reale richiedono lo strumento Exida exSILentia (IEC 61508) — le
#       formule qui sono un modello semplificato a scopo didattico.
# ==============================================================================

import math

import strumentazione as _stru   # fonte unica per le curve RTD/termocoppia (IEC 60751 / ITS-90)

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
# 3ter. Suite software ControlST / WorkstationST — catalogo componenti
# Fonti: manuali GE Vernova / GE Energy presenti nella cartella
#        Documentation/ (codice GEH/GEI + revisione citati per ciascuno).
# WorkstationST è la piattaforma software lato operatore della famiglia
# Mark VIe: raccoglie i dati dai componenti ControlST e li espone a
# client di allarme, server OPC, storici (Historian) e gateway di campo.
# Le descrizioni sintetizzano la sezione "Overview" del rispettivo manuale.
# ------------------------------------------------------------------

# Indice dei documenti effettivamente disponibili nella raccolta Documentation/
# (codice senza suffisso revisione -> titolo, revisione, n. pagine)
DOCUMENTI_CONTROLST = {
    "GEH-6757":   {"titolo": "WorkstationST GSM 3.0 — User Guide",                         "rev": "C",  "pagine": 62},
    "GEH-6759":   {"titolo": "WorkstationST Application Mark V Feature — System Guide",     "rev": "D",  "pagine": 176},
    "GEH-6760":   {"titolo": "WorkstationST GSM 3.0 — Application Guide",                   "rev": "E",  "pagine": 102},
    "GEI-100620": {"titolo": "WorkstationST Alarm Viewer — Instruction Guide",             "rev": "W",  "pagine": 119},
    "GEI-100621": {"titolo": "WorkstationST OPC DA Server — Instruction Guide",            "rev": "P",  "pagine": 53},
    "GEI-100622": {"titolo": "EGD Configuration Server",                                   "rev": "B",  "pagine": 8},
    "GEI-100623": {"titolo": "WorkstationST Service — Instruction Guide",                  "rev": "M",  "pagine": 34},
    "GEI-100624": {"titolo": "WorkstationST OPC AE Server",                                "rev": "J",  "pagine": 34},
    "GEI-100626": {"titolo": "WorkstationST Alarm Server — Instruction Guide",             "rev": "K",  "pagine": 22},
    "GEI-100627": {"titolo": "WorkstationST Recorder — User Guide",                        "rev": "F",  "pagine": 8},
    "GEI-100628": {"titolo": "WorkstationST Historian — Instruction Guide",               "rev": "F",  "pagine": 32},
    "GEI-100629": {"titolo": "WorkstationST HMI Configuration — User Guide",              "rev": "C",  "pagine": 13},
    "GEI-100661": {"titolo": "WorkstationST Web View — Instruction Guide",                "rev": "D",  "pagine": 12},
    "GEI-100662": {"titolo": "HART Message Server",                                        "rev": "A",  "pagine": 34},
    "GEI-100693": {"titolo": "WorkstationST Network Monitor — Instruction Guide",          "rev": "N",  "pagine": 71},
    "GEI-100696": {"titolo": "WorkstationST Modbus Feature — Instruction Guide",           "rev": "E",  "pagine": 47},
    "GEI-100697": {"titolo": "WorkstationST/CIMPLICITY Advanced Viewer Integration",       "rev": "N",  "pagine": 95},
    "GEI-100746": {"titolo": "ControlST Release Notes",                                    "rev": "HG", "pagine": 546},
    "GEI-100752": {"titolo": "Historian Report Configuration — Instruction Guide",         "rev": "C",  "pagine": 27},
    "GEI-100753": {"titolo": "Historian Report Post-installation — Instruction Guide",     "rev": "D",  "pagine": 11},
    "GEI-100757": {"titolo": "WorkstationST Device Manager Gateway — Instruction Guide",   "rev": "H",  "pagine": 100},
    "GEI-100795": {"titolo": "Trender — Instruction Guide",                                "rev": "T",  "pagine": 48},
    "GEI-100828": {"titolo": "WorkstationST OPC UA Server — Instruction Guide",            "rev": "G",  "pagine": 16},
    "GEI-100829": {"titolo": "WorkstationST Application Mark V Feature GSM Server",        "rev": "-",  "pagine": 66},
    "GEI-100834": {"titolo": "WorkstationST Control System Health — Instruction Guide",    "rev": "P",  "pagine": 177},
    "GEI-100853": {"titolo": "WorkstationST Mark V Ethernet Global Data (EGD)",            "rev": "A",  "pagine": 10},
    "GHT-200030": {"titolo": "How to Enable Adobe PDF Full-Text Search for ControlST Documentation", "rev": "B", "pagine": 7},
}

# Componenti della suite, raggruppati per categoria funzionale.
# Ogni voce: {categoria, funzione, doc} dove 'doc' è la chiave in DOCUMENTI_CONTROLST.
SUITE_CONTROLST_WORKSTATIONST = {
    "WorkstationST Service": {
        "categoria": "Infrastruttura e servizi",
        "funzione": "Scarica la configurazione ToolboxST sulla workstation, avvia/arresta le altre Feature WorkstationST "
                    "e fornisce accesso alle informazioni di controllo e diagnostica delle Feature.",
        "doc": "GEI-100623",
    },
    "Alarm Server": {
        "categoria": "Allarmi ed eventi",
        "funzione": "Raccoglie i dati da tutti i componenti monitorati e li rende disponibili ai client di allarme, "
                    "fungendo da livello di normalizzazione dei dati di allarme.",
        "doc": "GEI-100626",
    },
    "Alarm Viewer": {
        "categoria": "Allarmi ed eventi",
        "funzione": "Visualizza e gestisce allarmi ed eventi live e storici con funzioni avanzate di filtro e ordinamento.",
        "doc": "GEI-100620",
    },
    "OPC DA Server": {
        "categoria": "Comunicazione OPC",
        "funzione": "Server OPC Data Access: espone i dati in tempo reale a client OPC di terze parti.",
        "doc": "GEI-100621",
    },
    "OPC AE Server": {
        "categoria": "Comunicazione OPC",
        "funzione": "Server OPC Alarms & Events: espone allarmi ed eventi in tempo reale a client OPC.",
        "doc": "GEI-100624",
    },
    "OPC UA Server": {
        "categoria": "Comunicazione OPC",
        "funzione": "Server OPC Unified Architecture (dati e sottoscrizioni allarmi/eventi), con condivisione "
                    "dei certificati tra client e server.",
        "doc": "GEI-100828",
    },
    "Historian": {
        "categoria": "Dati storici e trend",
        "funzione": "Configura Historian di terze parti per la raccolta di dati a lungo termine; il client OPC "
                    "dell'Historian legge i dati dall'OPC DA Server del WorkstationST.",
        "doc": "GEI-100628",
    },
    "Historian Report (Configuration)": {
        "categoria": "Dati storici e trend",
        "funzione": "Genera report periodici e on-demand dai dati archiviati nell'Historian (script Perl + interfaccia "
                    "ODBC PI o OLE DB Proficy).",
        "doc": "GEI-100752",
    },
    "Historian Report (Post-installation)": {
        "categoria": "Dati storici e trend",
        "funzione": "Procedure da completare dopo l'installazione del pacchetto Historian Report per renderlo operativo.",
        "doc": "GEI-100753",
    },
    "Recorder": {
        "categoria": "Dati storici e trend",
        "funzione": "Raccoglie dati storici dagli altri componenti ToolboxST in file .dcaST (Data Collection and Analysis), "
                    "accessibili dal Trender.",
        "doc": "GEI-100627",
    },
    "Trender": {
        "categoria": "Dati storici e trend",
        "funzione": "Strumento di trend e analisi per recuperare e visualizzare i dati catturati (live e storici).",
        "doc": "GEI-100795",
    },
    "Modbus Feature": {
        "categoria": "Comunicazione di campo / fieldbus",
        "funzione": "Feature Modbus configurata via ToolboxST: supporta comunicazione seriale ed Ethernet, in modalità "
                    "master e slave.",
        "doc": "GEI-100696",
    },
    "HART Message Server (HMS)": {
        "categoria": "Comunicazione di campo / fieldbus",
        "funzione": "Bridge tra il software Asset Management System (AMS) e i pacchi PHRA che ospitano i dispositivi HART "
                    "nel controllo Mark VIe; emula un multiplexer hardware per ogni PHRA.",
        "doc": "GEI-100662",
    },
    "Device Manager Gateway": {
        "categoria": "Comunicazione di campo / fieldbus",
        "funzione": "Gateway tra l'asset management system e i dispositivi di campo FOUNDATION Fieldbus, HART e PROFIBUS.",
        "doc": "GEI-100757",
    },
    "EGD Configuration Server": {
        "categoria": "Comunicazione di campo / fieldbus",
        "funzione": "Servizio Windows che risponde ai messaggi di configurazione EGD (comandi Get/Put, revisione e stato); "
                    "archivia i file XML definiti dalle specifiche del protocollo EGD.",
        "doc": "GEI-100622",
    },
    "HMI Configuration": {
        "categoria": "HMI e visualizzazione",
        "funzione": "Feature HMI Config e HMI File Utility (scheda HMI Config di ToolboxST): esegue l'Importer per "
                    "importare device, variabili e altri dati in un database CIMPLICITY.",
        "doc": "GEI-100629",
    },
    "WorkstationST/CIMPLICITY Advanced Viewer Integration": {
        "categoria": "HMI e visualizzazione",
        "funzione": "Integrazione tra WorkstationST e CIMPLICITY HMI/SCADA per configurazione e flusso dati runtime "
                    "(server e viewer CIMPLICITY).",
        "doc": "GEI-100697",
    },
    "Web View": {
        "categoria": "HMI e visualizzazione",
        "funzione": "Funzione Web del WorkstationST che permette a un On Site Monitor (OSM) di pubblicare configurazione "
                    "e dati in tempo reale come insieme di pagine Web.",
        "doc": "GEI-100661",
    },
    "Network Monitor": {
        "categoria": "Diagnostica rete e salute sistema",
        "funzione": "Monitora la salute della rete NetworkST, degli switch e delle singole porte di rete.",
        "doc": "GEI-100693",
    },
    "Control System Health (CSH)": {
        "categoria": "Diagnostica rete e salute sistema",
        "funzione": "Visualizza la salute dei vari componenti su Unit Data Highway (UDH), Plant Data Highway (PDH) e IONet.",
        "doc": "GEI-100834",
    },
    "GSM 3.0 Server (GE Standard Messages)": {
        "categoria": "Integrazione DCS / Mark V",
        "funzione": "I GE Standard Messages (GSM) sono messaggi a livello applicativo elaborati da un gateway verso il DCS; "
                    "il GSM server richiede l'accesso a un Alarm Server. (User Guide GEH-6757, Application Guide GEH-6760, "
                    "server Mark V Feature GEI-100829).",
        "doc": "GEH-6757",
    },
    "WorkstationST Application — Mark V Feature": {
        "categoria": "Integrazione DCS / Mark V",
        "funzione": "System Guide della feature che porta le funzioni della suite ControlST sopra i controllori Mark V.",
        "doc": "GEH-6759",
    },
    "Mark V Ethernet Global Data (EGD)": {
        "categoria": "Integrazione DCS / Mark V",
        "funzione": "Ponte di dati real-time bidirezionale tra Mark V (ARCNET) e le EGD Pages dei controllori Mark VI/VIe "
                    "(Ethernet).",
        "doc": "GEI-100853",
    },
    "ControlST Release Notes": {
        "categoria": "Suite e documentazione",
        "funzione": "Note di rilascio della suite ControlST: versioni, funzionalità e riferimenti di capitolo al manuale "
                    "GEH-6700 (ToolboxST User Guide).",
        "doc": "GEI-100746",
    },
    "ControlST Documentation Global Search": {
        "categoria": "Suite e documentazione",
        "funzione": "Procedura per abilitare la ricerca full-text Adobe sull'intera documentazione ControlST.",
        "doc": "GHT-200030",
    },
}


# Sezioni/capitoli chiave di ciascun componente, con pagina del PDF.
# Estratti dai bookmark (outline) dei manuali nella cartella Documentation/.
# Formato: nome_componente -> [(titolo_sezione, pagina_pdf), ...]
SEZIONI_COMPONENTI = {
    "WorkstationST Service": [
        ("1 Introduction", 6), ("2 WorkstationST Features", 6),
        ("4 Start and Stop WorkstationST Service", 9), ("5 Configuration Files Data Flow", 10),
    ],
    "Alarm Server": [
        ("1 Introduction", 4), ("2 Alarm Routing", 5),
        ("5 Alarm Types", 9), ("7 Redundant Alarm Servers", 10),
    ],
    "Alarm Viewer": [
        ("1 Introduction", 5), ("6 Operation", 11),
        ("7 Advanced Features", 15), ("8 Live Alarms", 16),
    ],
    "OPC DA Server": [
        ("1 Introduction", 4), ("3 Variable Names", 5),
        ("3.5 OPC DA Server Variable Configuration", 8), ("6 OPC DA Client Privileges", 13),
    ],
    "OPC AE Server": [
        ("Introduction", 4), ("Alarm and Event Routing", 4),
        ("Configuring the OPC AE Server", 11), ("Configuring DCOM", 14),
    ],
    "OPC UA Server": [
        ("1 Overview", 4), ("2 OPC UA Communication", 4),
        ("3 Client Privileges", 10), ("6 Historical Data Access", 13),
    ],
    "Historian": [
        ("1 Overview", 4), ("2 Configure Historian", 5),
        ("3 Configure Variables for Data Collection", 9), ("4 Configure Historian Reports", 15),
    ],
    "Historian Report (Configuration)": [
        ("1 Introduction", 6), ("4 Report Configuration", 8),
        ("5 Automatic Report Generation", 20), ("6 Web Browser Interface", 24),
    ],
    "Historian Report (Post-installation)": [
        ("1 Introduction", 4), ("2 Install Proficy-based Historian OLE DB", 5),
        ("3 Install PI ODBC", 8),
    ],
    "Recorder": [
        ("1 Introduction", 4), ("2 Capture Buffer", 5),
        ("4 Trip Log", 5), ("8 Appendix: Supported Collections by Component", 8),
    ],
    "Trender": [
        ("1 Overview", 4), ("2 Data Sources", 7), ("3 Concepts", 29),
    ],
    "Modbus Feature": [
        ("Overview", 4), ("Configuration", 5),
        ("Modbus Properties", 15), ("Scaling", 21),
    ],
    "HART Message Server (HMS)": [
        ("Introduction", 3), ("HMS Configuration", 5),
        ("HMS Monitoring", 13), ("Troubleshooting", 20),
    ],
    "Device Manager Gateway": [
        ("1 Overview", 9), ("2 Third-party Asset Management Software", 11),
        ("2.3 Configuration (Quick Start)", 15), ("4 Device Manager Gateway Security", 57),
    ],
    "EGD Configuration Server": [
        ("Introduction", 5), ("Installation", 5), ("Typical EGD Files", 6),
    ],
    "HMI Configuration": [
        ("Introduction", 3), ("HMI Configuration", 3), ("Hmi File Util", 8),
    ],
    "WorkstationST/CIMPLICITY Advanced Viewer Integration": [
        ("1 Introduction", 5), ("2 Configuration", 7), ("3 CimEdit", 21),
    ],
    "Web View": [
        ("1 Introduction", 3), ("2 Enabling WorkstationST Web", 3),
        ("7 Appendix A .NET Framework Registration in IIS", 12),
    ],
    "Network Monitor": [
        ("1 Introduction", 4), ("2 Configuration", 5),
        ("3 Alarms", 23), ("4 Switch Management Network Support", 25),
    ],
    "Control System Health (CSH)": [
        ("1 Overview", 7), ("2 CSH Server", 12), ("3 Network Configuration", 23),
    ],
    "GSM 3.0 Server (GE Standard Messages)": [
        ("Chapter 1 Overview", 5), ("Chapter 2 Configuration", 7), ("Chapter 3 Runtime", 31),
    ],
    "WorkstationST Application — Mark V Feature": [
        ("Mark V", 9), ("Mark V Controller", 9),
    ],
    "Mark V Ethernet Global Data (EGD)": [
        ("1 Overview", 3), ("2 Data File Configuration", 4), ("3 Import to ToolboxST", 8),
    ],
    "ControlST Release Notes": [
        ("1 Introduction", 19), ("2 V07.09.07 Release Notes", 21),
        ("2.2 V07.09 Suite Components", 22),
    ],
    "ControlST Documentation Global Search": [
        ("Install and Enable Windows Search Service", 1), ("Search Documentation", 7),
    ],
}


def documento_componente(nome_componente: str) -> dict:
    """
    Restituisce il riferimento documentale completo (codice, revisione, titolo,
    pagine) associato a un componente della suite ControlST/WorkstationST.
    """
    if nome_componente not in SUITE_CONTROLST_WORKSTATIONST:
        raise ValueError(f"Componente non riconosciuto: {nome_componente}. "
                         f"Disponibili: {list(SUITE_CONTROLST_WORKSTATIONST)}")
    comp = SUITE_CONTROLST_WORKSTATIONST[nome_componente]
    doc_code = comp["doc"]
    doc = DOCUMENTI_CONTROLST[doc_code]
    rev = f"{doc_code}{doc['rev']}" if doc["rev"] not in ("-", "") else doc_code
    return {
        "componente": nome_componente,
        "categoria": comp["categoria"],
        "funzione": comp["funzione"],
        "documento": doc_code,
        "documento_rev": rev,
        "titolo": doc["titolo"],
        "pagine": doc["pagine"],
        "sezioni": SEZIONI_COMPONENTI.get(nome_componente, []),
    }


def componenti_per_categoria() -> dict:
    """Raggruppa i componenti della suite per categoria funzionale (per la UI)."""
    out: dict = {}
    for nome, info in SUITE_CONTROLST_WORKSTATIONST.items():
        out.setdefault(info["categoria"], []).append(nome)
    return out


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


# ==============================================================================
# 6. Sensori di processo — conversioni per schede PRTD e PTCC
# ==============================================================================

# ------------------------------------------------------------------
# 6.1 RTD (PRTD) e 6.2 Termocoppie (PTCC)
# Le curve sensore (IEC 60751 / NIST ITS-90) sono definite UNA SOLA VOLTA in
# strumentazione.py. Qui restano sottili adattatori che conservano l'API storica
# usata dalla sezione Mark VIe della UI e dai test (consolidamento, niente
# matematica duplicata).
# ------------------------------------------------------------------
RTD_RANGE_C = _stru.RTD_RANGE_C
TC_ITS90 = _stru.TC_ITS90_DIRETTA   # alias retro-compatibile (tipi K, J)


def rtd_resistenza(temp_C: float, R0: float = 100.0) -> dict:
    """Resistenza RTD al platino (IEC 60751) — delega a strumentazione.pt100_t_a_r."""
    return {"R_ohm": _stru.pt100_t_a_r(temp_C, R0), "R0": R0, "temp_C": temp_C}


def rtd_temperatura(R_ohm: float, R0: float = 100.0) -> dict:
    """Temperatura da resistenza RTD (IEC 60751) — delega a strumentazione.pt100_r_a_t."""
    if R_ohm <= 0:
        raise ValueError("R_ohm deve essere > 0.")
    t = _stru.pt100_r_a_t(R_ohm, R0)["temperatura_C"]
    return {"temp_C": t, "R_ohm": R_ohm, "R0": R0}


def termocoppia_mv(tipo: str, temp_giunto_caldo_C: float, temp_giunto_freddo_C: float = 0.0) -> dict:
    """F.e.m. termocoppia con CJC (ITS-90) — delega a strumentazione.termocoppia_gradi_a_mv."""
    r = _stru.termocoppia_gradi_a_mv(temp_giunto_caldo_C, tipo, temp_giunto_freddo_C)
    return {
        "mV": r["mv"],
        "mV_assoluto_rif0": r["mv_assoluto_rif0"],
        "tipo": r["tipo"],
        "T_giunto_caldo_C": temp_giunto_caldo_C,
        "T_giunto_freddo_C": temp_giunto_freddo_C,
    }


def termocoppia_temp(tipo: str, mV_misurati: float, temp_giunto_freddo_C: float = 0.0) -> dict:
    """
    Temperatura del giunto caldo da f.e.m. misurata, con CJC. Inversione per
    bisezione sul polinomio diretto ITS-90 di strumentazione (curva non duplicata).
    """
    tipo_u = tipo.upper()
    if tipo_u not in _stru.TC_ITS90_DIRETTA:
        raise ValueError(f"Tipo termocoppia non riconosciuto: {tipo}. Disponibili: {list(_stru.TC_ITS90_DIRETTA)}")
    spec = _stru.TC_ITS90_DIRETTA[tipo_u]
    v_target = mV_misurati + _stru._tc_emf_diretta(temp_giunto_freddo_C, tipo_u)

    lo, hi = spec["range_C"]
    f_lo = _stru._tc_emf_diretta(lo, tipo_u) - v_target
    f_hi = _stru._tc_emf_diretta(hi, tipo_u) - v_target
    if f_lo * f_hi > 0:
        raise ValueError(f"F.e.m. {v_target:.3f} mV fuori campo per tipo {tipo_u} {spec['range_mV']} mV.")

    for _ in range(200):
        mid = 0.5 * (lo + hi)
        f_mid = _stru._tc_emf_diretta(mid, tipo_u) - v_target
        if abs(f_mid) < 1e-9 or (hi - lo) < 1e-7:
            break
        if f_lo * f_mid <= 0:
            hi = mid
        else:
            lo, f_lo = mid, f_mid
    return {
        "temp_C": 0.5 * (lo + hi),
        "tipo": tipo_u,
        "mV_misurati": mV_misurati,
        "T_giunto_freddo_C": temp_giunto_freddo_C,
    }


# ------------------------------------------------------------------
# 6.3 Diagnostica segnale 4–20 mA (NAMUR NE43)
# Soglie standard per segnalazione guasti sui loop analogici (PAIC/PHRA).
# ------------------------------------------------------------------
NAMUR_NE43 = {
    "guasto_basso_max_mA": 3.6,   # ≤ 3.6 mA -> sotto-range / rottura sensore
    "valido_min_mA": 3.8,
    "valido_max_mA": 20.5,
    "guasto_alto_min_mA": 21.0,   # ≥ 21.0 mA -> sovra-range / corto
}


def diagnostica_loop_420(corrente_mA: float, span_min: float = 0.0, span_max: float = 100.0) -> dict:
    """
    Diagnostica di un loop 4–20 mA secondo NAMUR NE43 e scalatura del valore
    di processo. Riconosce rottura cavo, sotto/sovra-range e zona valida.
    """
    if span_max <= span_min:
        raise ValueError("span_max deve essere > span_min.")

    if corrente_mA <= 0.1:
        stato = "Cavo interrotto / nessun segnale (≈0 mA)"
        valido = False
    elif corrente_mA <= NAMUR_NE43["guasto_basso_max_mA"]:
        stato = "GUASTO: sotto-range / rottura sensore (≤3.6 mA)"
        valido = False
    elif corrente_mA >= NAMUR_NE43["guasto_alto_min_mA"]:
        stato = "GUASTO: sovra-range / corto circuito (≥21 mA)"
        valido = False
    elif corrente_mA < NAMUR_NE43["valido_min_mA"] or corrente_mA > NAMUR_NE43["valido_max_mA"]:
        stato = "Zona di allerta (oltre 4–20 mA ma entro soglie NE43)"
        valido = True
    else:
        stato = "Segnale valido (4–20 mA)"
        valido = True

    pct = (corrente_mA - 4.0) / 16.0 * 100.0
    valore = span_min + (pct / 100.0) * (span_max - span_min)
    return {
        "stato": stato,
        "valido": valido,
        "percentuale": pct,
        "valore_processo": valore,
        "corrente_mA": corrente_mA,
    }


# ==============================================================================
# 7. Protezione velocità turbina — schede PTUR / PPRO / PGEN
# Ingressi velocità a riluttanza/MPU da ruota fonica, campo 2 Hz – 20 kHz
# (GEH-6721G — Primary/Emergency Turbine Protection).
# ==============================================================================
PTUR_FREQ_RANGE_HZ = (2.0, 20000.0)


def velocita_da_frequenza(freq_hz: float, n_denti: int) -> dict:
    """Velocità di rotazione [rpm] dalla frequenza impulsi di una ruota fonica."""
    if freq_hz < 0 or n_denti <= 0:
        raise ValueError("freq_hz ≥ 0 e n_denti > 0 richiesti.")
    rpm = freq_hz * 60.0 / n_denti
    return {
        "rpm": rpm,
        "freq_hz": freq_hz,
        "n_denti": n_denti,
        "in_campo_sensore": PTUR_FREQ_RANGE_HZ[0] <= freq_hz <= PTUR_FREQ_RANGE_HZ[1],
    }


def frequenza_da_velocita(rpm: float, n_denti: int) -> dict:
    """Frequenza impulsi [Hz] da velocità [rpm] e numero di denti della ruota fonica."""
    if rpm < 0 or n_denti <= 0:
        raise ValueError("rpm ≥ 0 e n_denti > 0 richiesti.")
    freq = rpm / 60.0 * n_denti
    return {
        "freq_hz": freq,
        "rpm": rpm,
        "n_denti": n_denti,
        "in_campo_sensore": PTUR_FREQ_RANGE_HZ[0] <= freq <= PTUR_FREQ_RANGE_HZ[1],
    }


def trip_sovravelocita(rpm_nominale: float, n_denti: int, soglia_trip_pct: float = 110.0) -> dict:
    """
    Punto di trip di sovravelocità: velocità e frequenza impulsi di trip dato
    il setpoint in % della velocità nominale (tipicamente 110 % per turbine GE).
    """
    if rpm_nominale <= 0 or n_denti <= 0:
        raise ValueError("rpm_nominale > 0 e n_denti > 0 richiesti.")
    if soglia_trip_pct <= 100.0:
        raise ValueError("La soglia di trip deve essere > 100% della nominale.")

    rpm_trip = rpm_nominale * soglia_trip_pct / 100.0
    f_nom = rpm_nominale / 60.0 * n_denti
    f_trip = rpm_trip / 60.0 * n_denti
    return {
        "rpm_nominale": rpm_nominale,
        "rpm_trip": rpm_trip,
        "freq_nominale_hz": f_nom,
        "freq_trip_hz": f_trip,
        "margine_rpm": rpm_trip - rpm_nominale,
        "soglia_trip_pct": soglia_trip_pct,
        "freq_trip_in_campo_sensore": PTUR_FREQ_RANGE_HZ[0] <= f_trip <= PTUR_FREQ_RANGE_HZ[1],
    }


# ==============================================================================
# 8. Matrice di troubleshooting — sintomo → componente → dove guardare
# Tutte le voci rimandano a sezioni effettivamente presenti nei manuali
# della cartella Documentation/ (codice in DOCUMENTI_CONTROLST, pagina PDF).
# ==============================================================================
TROUBLESHOOTING = [
    {"sintomo": "Una Feature WorkstationST non parte o è in errore",
     "componente": "WorkstationST Service",
     "dove": "Stato delle Feature nel WorkstationST Status Monitor; Detail Log",
     "doc": "GEI-100623", "sezione": "3 WorkstationST Configuration and Monitoring", "pagina": 9},
    {"sintomo": "Allarmi mancanti o non instradati ai client",
     "componente": "Alarm Server",
     "dove": "Diagnostic Messages e Log Files dell'Alarm Server",
     "doc": "GEI-100626", "sezione": "11 Diagnostic Messages", "pagina": 21},
    {"sintomo": "Client OPC UA non si connette / errori di certificato",
     "componente": "OPC UA Server",
     "dove": "Sezione Troubleshooting e Application Certificate Sharing",
     "doc": "GEI-100828", "sezione": "2.5 Troubleshooting", "pagina": 9},
    {"sintomo": "Dati HART non visibili nell'Asset Management System",
     "componente": "HART Message Server (HMS)",
     "dove": "Troubleshooting, Normal Operating Conditions e Message Log Files",
     "doc": "GEI-100662", "sezione": "Troubleshooting", "pagina": 20},
    {"sintomo": "Switch o porta di rete segnalata in allarme / link down",
     "componente": "Network Monitor",
     "dove": "Network Status and Troubleshooting; tabella stato switch/porte",
     "doc": "GEI-100693", "sezione": "2.6 Network Status and Troubleshooting", "pagina": 15},
    {"sintomo": "Comunicazione GSM verso DCS interrotta o con warning",
     "componente": "GSM 3.0 Server",
     "dove": "Error and Warning Messages; diagnostica GSM Spy e Detail Log",
     "doc": "GEH-6757", "sezione": "Error and Warning Messages", "pagina": 22},
    {"sintomo": "Variabili non aggiornate / non trovate nel Trender",
     "componente": "Trender",
     "dove": "Variable Status e selezione Data Sources",
     "doc": "GEI-100795", "sezione": "2.8 Variable Status", "pagina": 28},
    {"sintomo": "Dispositivi fieldbus non raggiungibili dal gateway",
     "componente": "Device Manager Gateway",
     "dove": "Monitor Status del gateway",
     "doc": "GEI-100757", "sezione": "2.4 Monitor Status", "pagina": 29},
    {"sintomo": "Import HMI/CIMPLICITY fallito o dati mancanti",
     "componente": "HMI Configuration",
     "dove": "HMI Importer Error and Log Files",
     "doc": "GEI-100629", "sezione": "HMI Importer Error and Log Files", "pagina": 7},
    {"sintomo": "Report storico non generato o con errori",
     "componente": "Historian Report",
     "dove": "Report Errors e configurazione automatica",
     "doc": "GEI-100752", "sezione": "6.2 Report Errors", "pagina": 27},
    {"sintomo": "Scambio dati EGD Mark V ↔ Mark VIe non funzionante",
     "componente": "Mark V Ethernet Global Data (EGD)",
     "dove": "Error Logs e configurazione file ToEGD/FromEGD",
     "doc": "GEI-100853", "sezione": "2.3 Error Logs", "pagina": 7},
]


def cerca_troubleshooting(testo: str) -> list:
    """Filtra la matrice di troubleshooting per testo libero (sintomo/componente/dove)."""
    t = (testo or "").lower()
    if not t:
        return list(TROUBLESHOOTING)
    return [v for v in TROUBLESHOOTING
            if t in f"{v['sintomo']} {v['componente']} {v['dove']} {v['doc']} {v['sezione']}".lower()]


# ==============================================================================
# 9. Checklist di commissioning — sequenza generale di buona pratica per un
# sistema di controllo turbina Mark VI/VIe (verifiche pre-avviamento, I/O,
# ridondanza, protezioni, logica applicativa). Sequenza didattica basata sulle
# normali fasi di commissioning di un DCS/TCS industriale; per la procedura
# di dettaglio del singolo impianto fare riferimento alle istruzioni di
# commissioning specifiche del progetto e ai manuali GEH-6721 Vol. I/II.
# ==============================================================================
CHECKLIST_COMMISSIONING = [
    {
        "fase": "1. Verifiche preliminari",
        "voci": [
            "Documentazione as-built (schemi elettrici, I/O list, application code) disponibile e in revisione corrente",
            "Tutte le alimentazioni di campo e di armadio isolate/etichettate prima dei lavori su cablaggio",
            "Continuità e isolamento dei cavi di campo verificati (megaohmetro dove applicabile)",
            "Messa a terra di armadio, schermi cavo e barra di terra strumentale verificata",
            "Backup della configurazione ToolboxST corrente effettuato prima di qualsiasi download",
        ],
    },
    {
        "fase": "2. Accensione e diagnostica di base",
        "voci": [
            "Sequenza di power-up rispettata (alimentazioni ausiliarie prima dei controllori/pacchi I/O)",
            "Tensioni di alimentazione di ciascun pacco I/O entro range (es. TBCI H1/H2/H3) verificate",
            "LED diagnostici di controllori e pacchi I/O in stato normale (nessun guasto/health bit attivo)",
            "Comunicazione IONet tra controllore e tutti i pacchi I/O stabilita (nessun pacco offline)",
            "Orologio di sistema e versione firmware/ToolboxST coerenti su tutti i nodi",
        ],
    },
    {
        "fase": "3. Verifica punto-per-punto I/O",
        "voci": [
            "Ingressi analogici (PAIC/PHRA): loop check 4-20 mA / 0-10 V con simulatore, confronto con Watch Window",
            "RTD/Termocoppie (PRTD/PTCC): verifica con simulatore di resistenza/f.e.m. e confronto temperatura attesa",
            "Ingressi digitali (TBCI/TICI): forzatura contatto di campo e verifica stato in ToolboxST",
            "Uscite digitali/relè (TRLYH1x): comando da Watch Window e verifica continuità/azionamento a bordo macchina",
            "Uscite analogiche e servovalvole (PSVO): verifica corsa e linearità su tutto il campo di uscita",
            "Tutti i punti I/O coperti dalla I/O list di progetto e nessun punto 'non cablato' lasciato senza nota",
        ],
    },
    {
        "fase": "4. Ridondanza e voting",
        "voci": [
            "Architettura realizzata (Simplex/Dual/TMR) corrisponde a quanto da progetto",
            "State exchange tra controllori ridondanti verificato (nessun disaccordo in condizioni statiche)",
            "Simulazione di guasto/scollegamento di un canale: voting 2oo3 o failover Dual eseguito senza upset di processo",
            "Reinserimento a caldo di un canale precedentemente guasto verificato (auto-reconfiguration pacchi I/O)",
            "Switch di rete IONet ridondanti verificati singolarmente (spegnimento di un percorso senza perdita di controllo)",
        ],
    },
    {
        "fase": "5. Protezioni di sicurezza",
        "voci": [
            "Catena di trip di emergenza (PPRO/TREA) provata con segnale simulato, indipendentemente dalla protezione primaria",
            "Catena di trip primario (PTUR/TRPG) provata con segnale simulato",
            "Soglia di sovravelocità verificata sui tre canali voting (valore e tempo di risposta)",
            "Prova di trip manuale (pulsante/comando operatore) verificata end-to-end fino all'attuatore finale",
            "Tempi di risposta della catena di trip misurati e confrontati con i requisiti di progetto",
        ],
    },
    {
        "fase": "6. Logica applicativa e HMI",
        "voci": [
            "Sequenze di avviamento/arresto verificate passo-passo in modalità manuale/assistita",
            "Interblocchi e permessi (permissive) verificati forzando le condizioni di blocco",
            "Allarmi critici generati e visualizzati correttamente su WorkstationST/HMI, con instradamento corretto",
            "Storicizzazione (Historian/Trender) attiva sulle variabili di processo principali",
            "Coding Practices Report eseguito in ToolboxST e anomalie residue chiuse o giustificate",
        ],
    },
    {
        "fase": "7. Chiusura commissioning",
        "voci": [
            "Tutte le non conformità aperte durante le prove tracciate e chiuse (o accettate con firma)",
            "Configurazione finale ToolboxST scaricata, verificata con Compare to Controller e archiviata (CMS)",
            "Documentazione as-built aggiornata con le modifiche emerse in fase di commissioning",
            "Checklist firmata dal responsabile di commissioning e dal cliente/utente finale",
        ],
    },
]


def checklist_commissioning_flat() -> list:
    """Versione 'piatta' della checklist, con un id stabile per voce (fase_idx, voce_idx),
    utile per la persistenza dello stato di completamento nella UI."""
    out = []
    for fi, blocco in enumerate(CHECKLIST_COMMISSIONING):
        for vi, voce in enumerate(blocco["voci"]):
            out.append({"id": f"{fi}_{vi}", "fase": blocco["fase"], "voce": voce})
    return out


# ==============================================================================
# 10. Loading rete IONet — stima semplificata del traffico ciclico I/O
# Modello didattico: ogni pacco I/O scambia con il controllore un piccolo
# datagramma Ethernet a ogni frame di scansione (tipicamente 100 Hz per
# Mark VIe, GEH-6721 Vol. I). Non è il modello di traffico certificato GE
# (che dipende da dettagli di protocollo non pubblici); utile per una stima
# di massima del margine di banda disponibile su una IONet a 100 Mbps.
# ==============================================================================
IONET_BANDA_TIPICA_MBPS = 100.0
IONET_OVERHEAD_BYTE = 64        # intestazioni Ethernet/IP/UDP tipiche di un datagramma ciclico
IONET_BYTE_PER_CANALE = 4.0     # stima dati utili per canale I/O (valore + stato)
IONET_UTILIZZO_RACCOMANDATO_PCT = 40.0  # margine ingegneristico tipico per traffico ciclico + diagnostica/burst


def loading_ionet(
    n_pacchi_io: int,
    canali_medi_per_pacco: float = 16.0,
    frame_rate_hz: float = 100.0,
    banda_rete_mbps: float = IONET_BANDA_TIPICA_MBPS,
    overhead_byte: float = IONET_OVERHEAD_BYTE,
    byte_per_canale: float = IONET_BYTE_PER_CANALE,
) -> dict:
    """
    Stima il carico (% di banda occupata) su una rete IONet dato il numero di
    pacchi I/O collegati, i canali medi per pacco e il frame rate di scansione.

    bytes_per_pacco_per_frame = overhead + canali_medi_per_pacco * byte_per_canale
    bit_rate_totale = bytes_per_pacco_per_frame * 8 * frame_rate_hz * n_pacchi_io
    utilizzo_pct = bit_rate_totale / banda_rete
    """
    if n_pacchi_io <= 0:
        raise ValueError("Il numero di pacchi I/O deve essere > 0.")
    if canali_medi_per_pacco <= 0:
        raise ValueError("I canali medi per pacco devono essere > 0.")
    if frame_rate_hz <= 0 or banda_rete_mbps <= 0:
        raise ValueError("Frame rate e banda di rete devono essere > 0.")

    bytes_per_pacco = overhead_byte + canali_medi_per_pacco * byte_per_canale
    bit_rate_per_pacco_bps = bytes_per_pacco * 8.0 * frame_rate_hz
    bit_rate_totale_bps = bit_rate_per_pacco_bps * n_pacchi_io
    banda_bps = banda_rete_mbps * 1.0e6
    utilizzo_pct = bit_rate_totale_bps / banda_bps * 100.0

    n_pacchi_max_raccomandato = math.floor(
        (banda_bps * IONET_UTILIZZO_RACCOMANDATO_PCT / 100.0) / bit_rate_per_pacco_bps
    ) if bit_rate_per_pacco_bps > 0 else 0

    return {
        "bytes_per_pacco_per_frame": round(bytes_per_pacco, 1),
        "bit_rate_totale_Mbps": round(bit_rate_totale_bps / 1.0e6, 3),
        "utilizzo_pct": round(utilizzo_pct, 2),
        "entro_margine_raccomandato": utilizzo_pct <= IONET_UTILIZZO_RACCOMANDATO_PCT,
        "margine_raccomandato_pct": IONET_UTILIZZO_RACCOMANDATO_PCT,
        "n_pacchi_max_raccomandato": max(n_pacchi_max_raccomandato, 0),
        "n_pacchi_io": n_pacchi_io,
    }
