# ==============================================================================
# gruppo_frigo.py — Gruppi frigoriferi e pompe di calore: COP/EER reale,
# limite teorico di Carnot e rendimento di secondo principio.
# ==============================================================================

_ZERO_KELVIN_C = -273.15


def _in_kelvin(T_C: float) -> float:
    if T_C <= _ZERO_KELVIN_C:
        raise ValueError("Temperatura non fisica (sotto lo zero assoluto).")
    return T_C - _ZERO_KELVIN_C


def cop_pompa_di_calore(Q_utile_kW: float, P_elettrica_kW: float) -> dict:
    """COP reale in riscaldamento: COP = Q_utile / P_elettrica."""
    if Q_utile_kW <= 0:
        raise ValueError("La potenza termica utile deve essere > 0 kW.")
    if P_elettrica_kW <= 0:
        raise ValueError("La potenza elettrica assorbita deve essere > 0 kW.")
    COP = Q_utile_kW / P_elettrica_kW
    return {"COP": COP, "Q_utile_kW": Q_utile_kW, "P_elettrica_kW": P_elettrica_kW}


def eer_raffrescamento(Q_frigorifera_kW: float, P_elettrica_kW: float) -> dict:
    """EER reale in raffrescamento: EER = Q_frigorifera / P_elettrica."""
    if Q_frigorifera_kW <= 0:
        raise ValueError("La potenza frigorifera deve essere > 0 kW.")
    if P_elettrica_kW <= 0:
        raise ValueError("La potenza elettrica assorbita deve essere > 0 kW.")
    EER = Q_frigorifera_kW / P_elettrica_kW
    return {"EER": EER, "Q_frigorifera_kW": Q_frigorifera_kW, "P_elettrica_kW": P_elettrica_kW}


def cop_carnot_riscaldamento(T_calda_C: float, T_fredda_C: float) -> dict:
    """
    Limite teorico di Carnot per una pompa di calore in riscaldamento:
    COP_Carnot = T_calda / (T_calda - T_fredda), temperature assolute [K].
    """
    T_H = _in_kelvin(T_calda_C)
    T_C = _in_kelvin(T_fredda_C)
    if T_H <= T_C:
        raise ValueError("La temperatura calda deve essere > della temperatura fredda.")
    COP_Carnot = T_H / (T_H - T_C)
    return {"COP_Carnot": COP_Carnot, "T_calda_C": T_calda_C, "T_fredda_C": T_fredda_C}


def eer_carnot_raffrescamento(T_calda_C: float, T_fredda_C: float) -> dict:
    """
    Limite teorico di Carnot per un frigorifero/raffrescatore:
    EER_Carnot = T_fredda / (T_calda - T_fredda), temperature assolute [K].
    """
    T_H = _in_kelvin(T_calda_C)
    T_C = _in_kelvin(T_fredda_C)
    if T_H <= T_C:
        raise ValueError("La temperatura calda deve essere > della temperatura fredda.")
    EER_Carnot = T_C / (T_H - T_C)
    return {"EER_Carnot": EER_Carnot, "T_calda_C": T_calda_C, "T_fredda_C": T_fredda_C}


def rendimento_secondo_principio(COP_reale: float, COP_carnot: float) -> dict:
    """Rendimento exergetico (di secondo principio): rapporto tra prestazione
    reale e limite teorico di Carnot — tipicamente 0.4-0.6 per macchine reali."""
    if COP_reale <= 0:
        raise ValueError("Il COP/EER reale deve essere > 0.")
    if COP_carnot <= 0:
        raise ValueError("Il COP/EER di Carnot deve essere > 0.")
    if COP_reale > COP_carnot:
        raise ValueError("Il COP/EER reale non può superare il limite teorico di Carnot.")
    eta = COP_reale / COP_carnot
    return {"eta_secondo_principio": eta, "eta_secondo_principio_pct": eta * 100.0, "COP_reale": COP_reale, "COP_carnot": COP_carnot}


def dimensionamento_completo_riscaldamento(
    Q_utile_kW: float,
    P_elettrica_kW: float,
    T_calda_C: float,
    T_fredda_C: float,
) -> dict:
    """Valutazione completa di una pompa di calore in riscaldamento in
    un'unica chiamata: COP reale, COP di Carnot e rendimento di secondo principio."""
    reale = cop_pompa_di_calore(Q_utile_kW, P_elettrica_kW)
    carnot = cop_carnot_riscaldamento(T_calda_C, T_fredda_C)
    eta = rendimento_secondo_principio(reale["COP"], carnot["COP_Carnot"])

    risultato = {}
    risultato.update(reale)
    risultato.update(carnot)
    risultato["eta_secondo_principio"] = eta["eta_secondo_principio"]
    risultato["eta_secondo_principio_pct"] = eta["eta_secondo_principio_pct"]
    return risultato
