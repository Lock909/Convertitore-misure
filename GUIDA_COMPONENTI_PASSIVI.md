# Guida al modulo `componenti_passivi.py`

Questo documento spiega come usare le funzioni del modulo `componenti_passivi.py`,
che raccoglie i calcoli su resistori, condensatori, induttori e alcuni componenti
elettronici di base (LED, amplificatori operazionali, diodi zener).

## Dove si trova e come è organizzato

Il modulo esiste in **due copie identiche**, mantenute sincronizzate:

- `componenti_passivi.py` — usato dall'app principale Streamlit (`web.py`)
- `static/pwa_offline/py/componenti_passivi.py` — usato dalla PWA offline tramite Pyodide (via `static/pwa_offline/py/bridge.py`)

Dopo ogni modifica a uno dei due file, esegui dalla root del progetto:

```
python verifica_sync_offline.py
```

Se segnala una divergenza, copia il file corretto sull'altro percorso (il
messaggio d'errore suggerisce il comando `cp` da usare).

## Uso base da Python

```python
import componenti_passivi as cp

r = cp.resistori_serie([100, 220, 330])
print(r["valore_equivalente"])   # 650.0
```

Ogni funzione di calcolo:
- accetta parametri con nomi espliciti (niente argomenti posizionali ambigui);
- ritorna un **dict** con chiavi descrittive (mai una tupla nuda);
- solleva **`ValueError`** con un messaggio in italiano se i parametri non sono validi (es. valori negativi, tipo non riconosciuto). Va sempre intercettata con `try/except ValueError` quando il valore viene da un input utente.

---

## 1. Codice colori resistori

### `lista_colori_resistore() -> list`
Ritorna i 12 nomi di colore validi per le bande (Nero, Marrone, Rosso, ... Oro, Argento).

### `lista_colori_coeff_temperatura() -> list`
Ritorna i colori validi per la sesta banda (coefficiente di temperatura), usata solo nelle resistenze a 6 bande.

### `decodifica_colori_resistore(colori: list) -> dict`
Decodifica una sequenza di bande colore in un valore ohmico. Supporta **3, 4, 5 o 6 bande**:

| Bande | Struttura                                            | Tolleranza banda |
|-------|-------------------------------------------------------|------------------|
| 3     | cifra, cifra, moltiplicatore                          | implicita ±20%   |
| 4     | cifra, cifra, moltiplicatore, tolleranza               | esplicita        |
| 5     | cifra, cifra, cifra, moltiplicatore, tolleranza         | esplicita        |
| 6     | cifra, cifra, cifra, moltiplicatore, tolleranza, coeff. temp. | esplicita  |

**Esempio:**
```python
cp.decodifica_colori_resistore(["Marrone", "Nero", "Rosso", "Oro"])
# {'valore_ohm': 1000, 'tolleranza_pct': 5.0, 'valore_min_ohm': 950.0,
#  'valore_max_ohm': 1050.0, 'n_bande': 4}
```

### `colori_da_resistenza(valore_ohm, n_bande=4, tolleranza_pct=5.0, coeff_temp_ppm_C=None) -> dict`
Operazione inversa: dato un valore in Ω, trova le bande colore corrispondenti.
- `tolleranza_pct` deve corrispondere a un colore standard (10, 5, 2, 1, 0.5, 0.25, 0.1, 0.05%); ignorata se `n_bande=3`.
- `coeff_temp_ppm_C` obbligatorio solo se `n_bande=6` (valori validi: 1, 5, 10, 15, 20, 25, 50, 100, 250 ppm/°C).

```python
cp.colori_da_resistenza(1000, n_bande=4, tolleranza_pct=5.0)
# {'colori': ['Marrone', 'Nero', 'Rosso', 'Oro'], 'valore_arrotondato_ohm': 1000, 'tolleranza_pct': 5.0}
```

---

## 2. Serie di valori normalizzati (IEC 60063)

### `lista_serie_e() -> list`
Ritorna i nomi delle serie disponibili: `E6, E12, E24, E48, E96`.

### `valore_normalizzato_e(valore, serie="E12") -> dict`
Trova il valore commerciale normalizzato più vicino a un valore qualsiasi
(funziona per resistori, condensatori o induttori: lavora solo sulla mantissa
decimale, indipendente dall'unità).

```python
cp.valore_normalizzato_e(53, "E24")
# {'valore_originale': 53, 'valore_normalizzato': 51.0, 'serie': 'E24',
#  'tolleranza_tipica_pct': 5.0, 'scostamento_pct': -3.77}
```

---

## 3. Combinazioni serie/parallelo

Sei funzioni, tutte con la stessa forma: accettano una **lista di valori** di
lunghezza qualsiasi (minimo 1) e ritornano `{"valore_equivalente": ...}`.

| Funzione                        | Componente  | Formula serie        | Formula parallelo     |
|----------------------------------|-------------|-----------------------|-------------------------|
| `resistori_serie` / `_parallelo` | Resistori Ω | somma diretta         | somma armonica          |
| `induttori_serie` / `_parallelo` | Induttori H | somma diretta         | somma armonica          |
| `condensatori_serie` / `_parallelo` | Condensatori F | somma armonica    | somma diretta            |

**Nota:** i condensatori si comportano in modo *opposto* a resistori/induttori
(la serie usa la formula che per gli altri due è quella del parallelo, e viceversa).

```python
cp.resistori_serie([100, 220, 330])          # {'valore_equivalente': 650.0}
cp.resistori_parallelo([1000, 1000])         # {'valore_equivalente': 500.0}
cp.condensatori_serie([10e-6, 10e-6])        # {'valore_equivalente': 5e-6}
```

---

## 4. LED — resistenza di limitazione

### `resistenza_limitazione_led(v_alimentazione, v_forward_led, corrente_ma) -> dict`
Calcola la resistenza in serie per limitare la corrente in un LED: `R = (Vcc - Vf) / I`.

```python
cp.resistenza_limitazione_led(9, 2, 20)
# {'resistenza_ohm': 350.0, 'potenza_dissipata_W': 0.14, 'potenza_consigliata_W': 0.5}
```
`potenza_consigliata_W` è la taglia commerciale (0.125 → 10 W) con margine di sicurezza doppio rispetto alla potenza reale dissipata.

---

## 5. Partitore di tensione resistivo

### `partitore_tensione_vout(v_in, r1_ohm, r2_ohm) -> dict`
`Vout = Vin · R2/(R1+R2)`. Ritorna anche la corrente nel partitore e il rapporto R2/(R1+R2).

### `partitore_tensione_r2(v_in, v_out, r1_ohm) -> dict`
Operazione inversa: dato R1 e una Vout desiderata, calcola R2.

```python
cp.partitore_tensione_vout(12, 1000, 2000)   # {'v_out': 8.0, 'corrente_mA': 4.0, 'rapporto': 0.667}
cp.partitore_tensione_r2(12, 4, 1000)        # {'r2_ohm': 500.0, 'corrente_mA': 8.0}
```

---

## 6. Costante di tempo RC / RL

### `costante_di_tempo(tipo, resistenza_ohm, c_o_l, percentuale_target=63.2) -> dict`
`tipo` è `"RC"` (`c_o_l` = capacità in Farad) oppure `"RL"` (`c_o_l` = induttanza in Henry).
Calcola τ e il tempo necessario per raggiungere `percentuale_target`% del valore finale in carica.

```python
cp.costante_di_tempo("RC", 1000, 1e-6, 90)
# {'tau_s': 0.001, 'tempo_target_s': 0.0023, 'tempo_5tau_s': 0.005, 'percentuale_a_5tau': 99.33}
```

---

## 7. Filtro RC / RL — frequenza di taglio

### `frequenza_taglio_rc_rl(tipo, resistenza_ohm, c_o_l) -> dict`
Diversa dalla costante di tempo: questa è la risposta **in frequenza** (-3 dB), non nel tempo.
`fc_RC = 1/(2πRC)`, `fc_RL = R/(2πL)`. Stessa fc sia in configurazione passa-basso che passa-alto.

```python
cp.frequenza_taglio_rc_rl("RC", 1000, 1e-6)   # {'fc_Hz': 159.15, 'omega_rad_s': 1000.0}
```

---

## 8. Ponte di Wheatstone

### `wheatstone_resistenza_incognita(r1_ohm, r2_ohm, r3_ohm) -> dict`
Condizione di equilibrio (nessuna corrente nel galvanometro): `R1·Rx = R2·R3` → `Rx = R2·R3/R1`.
R1 è il braccio in serie alla resistenza incognita; R2 e R3 sono i bracci di rapporto noti.

```python
cp.wheatstone_resistenza_incognita(100, 200, 150)   # {'rx_ohm': 300.0}
```

---

## 9. Amplificatore operazionale — guadagno

### `guadagno_op_amp(configurazione, r1_ohm, r2_ohm) -> dict`
`configurazione` è `"Invertente"` (Av = -R2/R1) oppure `"Non invertente"` (Av = 1 + R2/R1).

```python
cp.guadagno_op_amp("Invertente", 1000, 10000)   # {'guadagno': -10.0, 'guadagno_dB': 20.0}
```

---

## 10. Diodo Zener — regolatore shunt

### `diodo_zener_regolatore(v_alimentazione, v_zener, r_serie_ohm, r_carico_ohm) -> dict`
Analizza un regolatore shunt classico: resistenza serie che limita la corrente
totale, zener in parallelo al carico che stabilizza la tensione d'uscita a Vz.

```python
cp.diodo_zener_regolatore(12, 5.1, 220, 1000)
# {'i_totale_mA': 31.36, 'i_carico_mA': 5.1, 'i_zener_mA': 26.26,
#  'p_zener_W': 0.134, 'regolazione_ok': True}
```
Se `regolazione_ok` è `False`, la corrente di zener risulterebbe negativa: il
regolatore non riesce a stabilizzare (serve ridurre la resistenza serie o
quella di carico).

---

## 11. Convertitore AWG ↔ mm²

### `awg_a_mm2(awg) -> dict`
Diametro e sezione dato il calibro AWG (formula standard, valida per AWG -3 ... 40; -3 = "0000").

### `mm2_a_awg(area_mm2) -> dict`
Operazione inversa: calibro AWG più vicino a una sezione data (con arrotondamento all'intero).

```python
cp.awg_a_mm2(24)     # {'awg': 24, 'diametro_mm': 0.511, 'area_mm2': 0.2047}
cp.mm2_a_awg(2.5)     # {'area_mm2': 2.5, 'diametro_mm': 1.784, 'awg_esatto': 13.21, 'awg_piu_vicino': 13}
```

---

## 12. Resistori SMD

### `decodifica_smd_standard(codice: str) -> dict`
Marcatura a 3 o 4 cifre, oppure notazione con `R` al posto della virgola:
- 3 cifre: `"103"` = 10 × 10³ = 10 000 Ω
- 4 cifre: `"1002"` = 100 × 10² = 10 000 Ω
- notazione R: `"4R7"` = 4.7 Ω, `"R47"` = 0.47 Ω

### `decodifica_smd_eia96(codice: str) -> dict`
Marcatura EIA-96: 2 cifre (indice 01-96 nella serie E96) + 1 lettera moltiplicatore.
Lettere: `Z=×0.001, R/Y=×0.01, X/S=×0.1, A=×1, B/H=×10, C=×100, D=×1000, E=×10000, F=×100000`.

```python
cp.decodifica_smd_standard("103")   # {'valore_ohm': 10000.0, 'formato': '3 cifre'}
cp.decodifica_smd_eia96("68C")      # {'valore_ohm': 499.0, 'mantissa_e96': 4.99, 'moltiplicatore': 100.0}
```

---

## Come sono esposte nell'app

- **Streamlit (`web.py`)**: sezione *Calcoli Elettrici → Componenti Passivi*, con un `st.radio` che seleziona la sotto-modalità (una per ciascun gruppo sopra).
- **PWA offline (`static/pwa_offline/`)**: ogni funzione ha un adattatore JSON-friendly in `static/pwa_offline/py/bridge.py` (stesso nome, parametri convertiti a stringa/float) e una voce dichiarativa in `static/pwa_offline/calcolatori.js` (categoria "Componenti") che genera automaticamente il form.

Per aggiungere una nuova funzione di calcolo in futuro:
1. Scrivila in `componenti_passivi.py` (root) seguendo lo stile esistente (dict in ingresso/uscita, `ValueError` per input non validi).
2. Copiala in `static/pwa_offline/py/componenti_passivi.py` (o esegui `cp componenti_passivi.py static/pwa_offline/py/componenti_passivi.py`).
3. Esegui `python verifica_sync_offline.py` per confermare che i due file siano identici.
4. Aggiungi la funzione UI in `web.py` (sezione Componenti Passivi) e la funzione bridge + voce in `static/pwa_offline/py/bridge.py` / `static/pwa_offline/calcolatori.js`.
5. Aggiungi i test in `test_calcoli.py` (classe `TestComponentiPassivi`) e, se vuoi coprire anche il percorso Pyodide, un caso in `static/pwa_offline/test.js` (visibile con `?test=1`).
