import math

def calcola_ohm(ricerca, input_1, input_2):
    if ricerca == "Tensione":
        return f"Tensione (V): {input_1 * input_2:.4f} V"
    elif ricerca == "Corrente":
        return f"Corrente (I): {input_1 / input_2:.4f} A" if input_2 != 0 else "Errore: Resistenza zero!"
    elif ricerca == "Resistenza":
        return f"Resistenza (R): {input_1 / input_2:.4f} \u03a9" if input_2 != 0 else "Errore: Corrente zero!"

def ottieni_sezioni():
    return (1.5, 2.5, 4.0, 6.0, 10.0, 16.0, 25.0, 35.0, 50.0, 70.0, 95.0, 120.0)

def ottieni_interruttori():
    return (6, 10, 16, 20, 25, 32, 40, 50, 63, 80, 100, 125)

def calcola_sezione_protezione(i_max, densita):
    sezione_teorica = i_max / densita
    sez_scelta = ottieni_sezioni()[-1]
    for s in ottieni_sezioni():
        if s >= sezione_teorica:
            sez_scelta = s
            break
    int_scelto = ottieni_interruttori()[-1]
    for val_i in ottieni_interruttori():
        if val_i >= i_max:
            int_scelto = val_i
            break
    return int_scelto, sez_scelta, sezione_teorica
