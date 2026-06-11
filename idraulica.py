# ==============================================================================
# idraulica.py — Conversioni di unità di misura industriali
# Tutte le grandezze usano l'unità SI come perno interno.
# ==============================================================================

from costanti import PRESSIONE_ATM_PA, DENSITA_ACQUA_KG_M3, GRAVITA_STD, MCA_PER_PA


def ottieni_categorie():
    """
    Restituisce il dizionario delle grandezze supportate con i fattori di
    conversione verso l'unità SI base.
    La temperatura è 'Special' perché usa formule non lineari.
    """
    return {
        # ------------------------------------------------------------------ #
        "Pressione": {
            # Perno: Pascal (Pa)
            "pa":   1.0,
            "hpa":  100.0,
            "kpa":  1_000.0,
            "mpa":  1_000_000.0,
            "mbar": 100.0,
            "bar":  100_000.0,
            "bara": 100_000.0,
            "barg": 100_000.0,      # relativa → serve offset P_atm
            "atm":  101_325.0,
            "psi":  6_894.757,
            "psia": 6_894.757,
            "psig": 6_894.757,      # relativa → serve offset P_atm
            "mmhg": 133.322387,
            "torr": 133.322368,
            "mca":  1.0 / MCA_PER_PA,                    # ≈ 9806.65 Pa  (= rho_acqua * g)
        },
        # ------------------------------------------------------------------ #
        "Portata volumetrica": {
            # Perno: m³/s
            "m3/s":  1.0,
            "m3/h":  1.0 / 3_600.0,
            "l/s":   0.001,
            "l/min": 0.001 / 60.0,
            "l/h":   0.001 / 3_600.0,
            "gpm":   6.30902e-5,    # galloni USA/minuto
        },
        # ------------------------------------------------------------------ #
        "Portata massica": {
            # Perno: kg/s
            "kg/s": 1.0,
            "kg/h": 1.0 / 3_600.0,
            "g/s":  0.001,
            "t/h":  1_000.0 / 3_600.0,
            "lb/s": 0.45359237,
            "lb/h": 0.45359237 / 3_600.0,
        },
        # ------------------------------------------------------------------ #
        "Lunghezza": {
            # Perno: metro (m)
            "m":  1.0,
            "mm": 0.001,
            "cm": 0.01,
            "km": 1_000.0,
            "in": 0.0254,
            "ft": 0.3048,
            "yd": 0.9144,
            "mile": 1_609.344,
        },
        # ------------------------------------------------------------------ #
        "Superficie": {
            # Perno: m²
            # NOTA: cm² = 1e-4 m², mm² = 1e-6 m² (errori comuni nei convertitori online)
            "m2":    1.0,
            "cm2":   1e-4,
            "mm2":   1e-6,
            "km2":   1e6,
            "in2":   6.4516e-4,
            "ft2":   0.09290304,
            "yd2":   0.83612736,
            "ettaro": 10_000.0,
            "acre":  4_046.856,
        },
        # ------------------------------------------------------------------ #
        "Volume": {
            # Perno: m³
            "m3":     1.0,
            "l":      0.001,
            "dl":     0.0001,
            "cl":     0.00001,
            "ml":     0.000001,
            "cm3":    0.000001,
            "gal_us": 3.785411784e-3,
            "gal_uk": 4.54609e-3,
            "cu_ft":  0.028316847,
            "cu_in":  1.6387064e-5,
            "bbl":    0.158987295,  # barile petrolio
        },
        # ------------------------------------------------------------------ #
        "Densità": {
            # Perno: kg/m³
            "kg/m3":  1.0,
            "g/cm3":  1_000.0,
            "g/l":    1.0,
            "kg/l":   1_000.0,
            "lb/ft3": 16.018463,
            "lb/in3": 27_679.904,
        },
        # ------------------------------------------------------------------ #
        "Forza": {
            # Perno: Newton (N)
            "n":   1.0,
            "kn":  1_000.0,
            "mn":  1_000_000.0,
            "kgf": 9.80665,
            "tf":  9_806.65,        # tonnellata-forza
            "lbf": 4.44822,
            "ozf": 0.27801385,
        },
        # ------------------------------------------------------------------ #
        "Massa": {
            # Perno: kilogrammo (kg)
            "kg":   1.0,
            "g":    0.001,
            "mg":   0.000001,
            "t":    1_000.0,
            "lb":   0.45359237,
            "oz":   0.02834952,
            "slug": 14.593903,
        },
        # ------------------------------------------------------------------ #
        "Coppia torcente": {
            # Perno: Newton·metro (N·m)
            "n*m":    1.0,
            "kn*m":   1_000.0,
            "kgf*m":  9.80665,
            "kgf*cm": 0.0980665,
            "lbf*ft": 1.355818,
            "lbf*in": 0.112985,
        },
        # ------------------------------------------------------------------ #
        "Energia": {
            # Perno: Joule (J)
            "j":    1.0,
            "kj":   1_000.0,
            "mj":   1_000_000.0,
            "cal":  4.1868,
            "kcal": 4_186.8,
            "kwh":  3_600_000.0,
            "mwh":  3_600_000_000.0,
            "btu":  1_055.056,
            "ev":   1.60217663e-19,
        },
        # ------------------------------------------------------------------ #
        "Potenza": {
            # Perno: Watt (W)
            "w":     1.0,
            "kw":    1_000.0,
            "mw":    1_000_000.0,
            "hp":    745.69987,
            "cv":    735.49875,
            "btu/h": 0.29307107,
            "kcal/h": 4_186.8 / 3_600.0,
        },
        # ------------------------------------------------------------------ #
        "Velocità": {
            # Perno: m/s
            "m/s":  1.0,
            "km/h": 1.0 / 3.6,
            "mph":  0.44704,
            "knot": 0.514444,
            "ft/s": 0.3048,
            "m/min": 1.0 / 60.0,
        },
        # ------------------------------------------------------------------ #
        "Accelerazione": {
            # Perno: m/s²
            "m/s2":    1.0,
            "g_force": 9.80665,
            "ft/s2":   0.3048,
            "cm/s2":   0.01,
            "gal":     0.01,        # Gal (unità sismologica) = 1 cm/s²
        },
        # ------------------------------------------------------------------ #
        "Angolo": {
            # Perno: radiante (rad)
            "rad":  1.0,
            "deg":  3.14159265358979 / 180.0,
            "grad": 3.14159265358979 / 200.0,
            "turn": 2.0 * 3.14159265358979,
            "arcmin": 3.14159265358979 / 10_800.0,
            "arcsec": 3.14159265358979 / 648_000.0,
        },
        # ------------------------------------------------------------------ #
        "Temperatura": {
            # Perno: speciale (vedi _a_kelvin / _da_kelvin)
            "c": "Special",
            "f": "Special",
            "k": "Special",
            "r": "Special",     # Rankine
        },
    }


# ------------------------------------------------------------------------------
# Conversione temperatura (funzioni di supporto interne)
# ------------------------------------------------------------------------------

def _a_kelvin(valore, unita):
    """Converte qualsiasi unità di temperatura in Kelvin."""
    if unita == "c":
        return valore + 273.15
    if unita == "f":
        return (valore - 32.0) * 5.0 / 9.0 + 273.15
    if unita == "r":
        return valore * 5.0 / 9.0         # Rankine → Kelvin
    return valore                          # già in Kelvin


def _da_kelvin(kelvin, unita):
    """Converte da Kelvin verso l'unità di destinazione."""
    if unita == "c":
        return kelvin - 273.15
    if unita == "f":
        return (kelvin - 273.15) * 9.0 / 5.0 + 32.0
    if unita == "r":
        return kelvin * 9.0 / 5.0         # Kelvin → Rankine
    return kelvin                          # rimane in Kelvin


# ------------------------------------------------------------------------------
# Funzione principale di conversione
# ------------------------------------------------------------------------------

def esegui_conversione(cat, from_u, to_u, val):
    """
    Converte 'val' dall'unità 'from_u' all'unità 'to_u' per la grandezza 'cat'.

    Parametri
    ----------
    cat    : str   — chiave grandezza (es. 'Pressione')
    from_u : str   — unità sorgente (es. 'bar')
    to_u   : str   — unità destinazione (es. 'psi')
    val    : float — valore da convertire

    Ritorna
    -------
    float — valore convertito
    """
    categories = ottieni_categorie()

    if cat == "Temperatura":
        kelvin = _a_kelvin(val, from_u)
        return _da_kelvin(kelvin, to_u)

    elif cat == "Pressione":
        # Converti in Pascal assoluti
        pascal_assoluti = val * categories[cat][from_u]
        if from_u in ("barg", "psig"):
            pascal_assoluti += PRESSIONE_ATM_PA

        # Converti verso l'unità di destinazione
        if to_u in ("barg", "psig"):
            pascal_assoluti -= PRESSIONE_ATM_PA
        return pascal_assoluti / categories[cat][to_u]

    else:
        # Grandezze lineari: conversione diretta via SI
        return (val * categories[cat][from_u]) / categories[cat][to_u]
