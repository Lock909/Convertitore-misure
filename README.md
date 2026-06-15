# Convertitore Calcolatore

Applicazione Streamlit per conversioni industriali, calcoli elettrici e utility PLC.

## Requisiti

- Python 3.14
- `streamlit>=1.36,<2`

## Installazione

```bash
pip install -r requirements.txt
```

## Avvio

Dalla cartella del progetto:

```bash
streamlit run web.py
```

Se vuoi usare un interprete Python specifico:

```bash
python -m streamlit run web.py
```

## Test

Compilazione rapida dei file:

```bash
python -m py_compile automazione.py costanti.py formule.py idraulica.py web.py test_calcoli.py
```

Esecuzione test:

```bash
python -m unittest -v test_calcoli.py
```

## Moduli principali

- `idraulica.py`: conversioni di unita
- `formule.py`: calcoli elettrici
- `automazione.py`: utility PLC e scalature
- `web.py`: interfaccia Streamlit
- `test_calcoli.py`: test automatici principali

## Note

- I test automatici attuali coprono i calcoli principali e diversi casi limite.
- La UI e stata ripulita per evitare problemi di codifica nei testi.
- Per il deploy online conviene sempre pubblicare tutti i file insieme per evitare disallineamenti tra moduli.
