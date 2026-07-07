# ==============================================================================
# bridge.py — Adattatore JSON-friendly tra l'app offline (JS) e i moduli di
# calcolo puro-Python già usati dall'app Streamlit (formule, portata_cavo,
# batterie_litio). Ogni funzione accetta/ritorna solo dict con tipi semplici
# (str, float, int, bool, list), così il lato JS non deve conoscere tuple o
# eccezioni Python: in caso di errore ritorna sempre {"errore": "..."}.
# ==============================================================================

import math

import formule
import portata_cavo
import batterie_litio
import mark_vie
import riferimento_rapido
import grado_protezione_ip
import motore_asincrono
import canaline_passerelle
import componenti_passivi
import trasformatore
import circuito_rlc
import armonie_thd
import batterie_ups
import impianto_terra
import selettivita_protezioni
import fotovoltaico
import gruppo_elettrogeno
import quadro_elettrico
import rifasamento_condensatori
import caduta_tensione_bt
import avviamento_motore
import dissipatore
import illuminotecnica
import libreria_cavi
import batch_cavi
import costi_energetici
import vibrazioni
import resistenza_materiali
import bulloneria
import cuscinetti
import molle
import ruote_dentate
import alberi_torsione
import saldature
import trasmissioni
import nastri_trasportatori
import pompe
import perdite_carico
import perdite_carico_distribuite
import scambiatori
import isolamento_termico
import condotte_hvac
import serbatoi
import valvole_controllo
import tubazione_pressione
import pneumatica
import trasduttori_pressione
import rumore_industriale
import performance_level
import automazione
import idraulica


def _err(msg: str) -> dict:
    return {"errore": msg}


def _sanifica(valore):
    """Sostituisce inf/nan (non rappresentabili in JSON/JS) con simboli leggibili,
    ricorsivamente nei dict/liste annidati."""
    if isinstance(valore, float):
        if math.isinf(valore):
            return "∞" if valore > 0 else "-∞"
        if math.isnan(valore):
            return "—"
        return valore
    if isinstance(valore, dict):
        return {k: _sanifica(v) for k, v in valore.items()}
    if isinstance(valore, list):
        return [_sanifica(v) for v in valore]
    return valore


def ohm(ricerca, input_1, input_2):
    try:
        valore = formule.calcola_ohm(ricerca, float(input_1), float(input_2))
        return {"valore": valore}
    except ValueError as e:
        return _err(str(e))


def potenza_corrente(sistema, volt, ampere, watt, cos_phi, calcola_cosa):
    r = formule.calcola_potenza_e_corrente(
        sistema, float(volt), float(ampere), float(watt), float(cos_phi), calcola_cosa
    )
    if r is None:
        return _err("Parametri non validi (controlla tensione, corrente/potenza e cos φ).")
    return r


def conversione_potenza(valore, da_unita, a_unita, cos_phi):
    try:
        r = formule.converti_potenza(float(valore), da_unita, a_unita, float(cos_phi))
        return {"valore": r}
    except ValueError as e:
        return _err(str(e))


def rifasamento(p_attiva_kw, cos_ini, cos_fin):
    qc_kvar, stato = formule.calcola_rifasamento_kvar(float(p_attiva_kw), float(cos_ini), float(cos_fin))
    if stato != "OK":
        return _err(stato)
    return {"qc_kvar": qc_kvar}


def caduta_tensione(materiale, isolante, posa, fasi, amp, metri, sez,
                     cos_phi, temp_amb, iz_nominale, num_circuiti, n_parallelo,
                     considera_reattanza):
    try:
        dv, t_lav, rho_t, k1, k2, iz_corr = formule.calcola_caduta_avanzata(
            materiale, isolante, posa, fasi, float(amp), float(metri), float(sez),
            float(cos_phi), float(temp_amb), float(iz_nominale), int(num_circuiti),
            n_parallelo=int(n_parallelo), considera_reattanza=bool(considera_reattanza),
        )
        if dv < 0:
            return _err("Temperatura ambiente fuori specifica per l'isolante scelto: il cavo è già fuori limite termico.")
        tensione_rif = 230.0 if fasi == "Monofase" else 400.0
        return {
            "caduta_V": dv,
            "caduta_pct": dv / tensione_rif * 100.0,
            "temp_lavoro_C": t_lav,
            "K1": k1,
            "K2": k2,
            "Iz_corretta_A": iz_corr,
        }
    except ValueError as e:
        return _err(str(e))


def sezione_protezione(i_max, densita):
    try:
        interruttore, sez_scelta, sez_teorica = formule.calcola_sezione_protezione(float(i_max), float(densita))
        return {"interruttore_A": interruttore, "sezione_scelta_mm2": sez_scelta, "sezione_teorica_mm2": sez_teorica}
    except ValueError as e:
        return _err(str(e))


def corto_circuito(tensione_v, potenza_trafo_kva, vcc_pct, materiale, sez, lunghezza_m, fasi, c):
    try:
        icc, z_tot, z_trafo, z_cavo = formule.calcola_corrente_cortocircuito(
            float(tensione_v), float(potenza_trafo_kva), float(vcc_pct),
            materiale, float(sez), float(lunghezza_m), fasi, float(c),
        )
        return {"icc_kA": icc, "z_tot_mOhm": z_tot, "z_trafo_mOhm": z_trafo, "z_cavo_mOhm": z_cavo}
    except ValueError as e:
        return _err(str(e))


def ingresso_motore(p_out_kw, rendimento_pct, sistema, tensione_v, cos_phi):
    r = formule.calcola_ingresso_motore(float(p_out_kw), float(rendimento_pct), sistema, float(tensione_v), float(cos_phi))
    if r is None:
        return _err("Parametri non validi (controlla rendimento, tensione e cos φ).")
    return r


def portata_sezione_minima(Ib, isolante, posa, T_amb, n_circuiti, n_parallelo):
    try:
        return portata_cavo.sezione_minima_portata(
            float(Ib), isolante, posa, float(T_amb), int(n_circuiti), int(n_parallelo)
        )
    except ValueError as e:
        return _err(str(e))


def portata_verifica_cavo(Ib, iz0_datasheet, isolante, T_amb, n_circuiti, n_parallelo):
    try:
        return portata_cavo.verifica_cavo_personalizzato(
            float(Ib), float(iz0_datasheet), isolante, float(T_amb), int(n_circuiti), int(n_parallelo)
        )
    except ValueError as e:
        return _err(str(e))


def batteria_curva_scarica(C_nom_Ah, c_rate, n_celle_serie, n_celle_parallelo,
                            R_int_cella_ohm, soc_finale_pct, n_punti):
    try:
        r = batterie_litio.curva_scarica(
            float(C_nom_Ah), float(c_rate), int(n_celle_serie), int(n_celle_parallelo),
            float(R_int_cella_ohm), float(soc_finale_pct), 1.05, int(n_punti),
        )
        return r
    except ValueError as e:
        return _err(str(e))


def liste_portata_cavo():
    return {
        "isolanti": portata_cavo.lista_isolanti(),
        "metodi_posa": portata_cavo.lista_metodi_posa(),
        "sezioni": portata_cavo.lista_sezioni_disponibili(),
    }


# ------------------------------------------------------------------ Mark VIe

def rtd_resistenza(temp_C, R0):
    try:
        return mark_vie.rtd_resistenza(float(temp_C), float(R0))
    except ValueError as e:
        return _err(str(e))


def rtd_temperatura(R_ohm, R0):
    try:
        return mark_vie.rtd_temperatura(float(R_ohm), float(R0))
    except ValueError as e:
        return _err(str(e))


def termocoppia_mv(tipo, temp_giunto_caldo_C, temp_giunto_freddo_C):
    try:
        return mark_vie.termocoppia_mv(tipo, float(temp_giunto_caldo_C), float(temp_giunto_freddo_C))
    except ValueError as e:
        return _err(str(e))


def termocoppia_temp(tipo, mV_misurati, temp_giunto_freddo_C):
    try:
        return mark_vie.termocoppia_temp(tipo, float(mV_misurati), float(temp_giunto_freddo_C))
    except ValueError as e:
        return _err(str(e))


def voting_tmr_mediano(v1, v2, v3, tolleranza):
    return mark_vie.voting_tmr_mediano(float(v1), float(v2), float(v3), float(tolleranza))


def disponibilita_tmr_2oo3(mtbf_canale_anni, mttr_ore):
    try:
        return mark_vie.disponibilita_tmr_2oo3(float(mtbf_canale_anni), float(mttr_ore))
    except ValueError as e:
        return _err(str(e))


def corrente_assorbita_tbci(tipo, n_circuiti_normali, n_circuiti_alta):
    try:
        return mark_vie.corrente_assorbita_tbci(tipo, int(n_circuiti_normali), int(n_circuiti_alta))
    except ValueError as e:
        return _err(str(e))


def corrente_derating_relay_trly(tipo, T_amb_C):
    try:
        return mark_vie.corrente_derating_relay_trly(tipo, float(T_amb_C))
    except ValueError as e:
        return _err(str(e))


def loading_ionet(n_pacchi_io, canali_medi_per_pacco, frame_rate_hz, banda_rete_mbps,
                   overhead_byte, byte_per_canale):
    try:
        return mark_vie.loading_ionet(
            int(n_pacchi_io), float(canali_medi_per_pacco), float(frame_rate_hz),
            float(banda_rete_mbps), float(overhead_byte), float(byte_per_canale),
        )
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Riferimento rapido

def colori_conduttori():
    return dict(riferimento_rapido.COLORI_CONDUTTORI)


def glossario():
    return riferimento_rapido.glossario()


def sezioni_normalizzate():
    return {"sezioni_mm2": riferimento_rapido.SEZIONI_CAVO_NORMALIZZATE_MM2}


def decodifica_ip(codice):
    try:
        return grado_protezione_ip.decodifica_ip(codice)
    except ValueError as e:
        return _err(str(e))


def ik_energia():
    return dict(grado_protezione_ip.IK_ENERGIA_JOULE)


def ip_esempi_uso():
    return dict(grado_protezione_ip.IP_ESEMPI_USO)


def confronto_classi_ie(P_kw, ore_anno, costo_kwh):
    try:
        return motore_asincrono.confronto_classi_ie(float(P_kw), float(ore_anno), float(costo_kwh))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Canaline / passerelle

def riempimento_canalina(larghezza_mm, altezza_mm, d1, q1, d2, q2, d3, q3):
    try:
        cavi = [(float(d), int(q)) for d, q in [(d1, q1), (d2, q2), (d3, q3)] if float(q) > 0]
        if not cavi:
            return _err("Specificare almeno un cavo con quantità > 0.")
        return canaline_passerelle.verifica_riempimento(float(larghezza_mm), float(altezza_mm), cavi)
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Componenti passivi

def decodifica_colori_resistore(c1, c2, c3, moltiplicatore, tolleranza, coeff_temp, n_bande):
    try:
        n_bande = int(n_bande)
        if n_bande == 3:
            colori = [c1, c2, moltiplicatore]
        elif n_bande == 4:
            colori = [c1, c2, moltiplicatore, tolleranza]
        elif n_bande == 5:
            colori = [c1, c2, c3, moltiplicatore, tolleranza]
        else:
            colori = [c1, c2, c3, moltiplicatore, tolleranza, coeff_temp]
        return componenti_passivi.decodifica_colori_resistore(colori)
    except ValueError as e:
        return _err(str(e))


def colori_da_resistenza(valore_ohm, n_bande, tolleranza_pct, coeff_temp_ppm_C):
    try:
        n_bande = int(n_bande)
        coeff = float(coeff_temp_ppm_C) if n_bande == 6 else None
        return componenti_passivi.colori_da_resistenza(float(valore_ohm), n_bande, float(tolleranza_pct), coeff)
    except ValueError as e:
        return _err(str(e))


def resistori_induttori_combinazione(tipo, combinazione, valori):
    try:
        vals = [float(v) for v in valori if float(v) > 0]
        if tipo == "Resistori":
            r = componenti_passivi.resistori_serie(vals) if combinazione == "Serie" else componenti_passivi.resistori_parallelo(vals)
        else:
            r = componenti_passivi.induttori_serie(vals) if combinazione == "Serie" else componenti_passivi.induttori_parallelo(vals)
        r["n_componenti"] = len(vals)
        return r
    except ValueError as e:
        return _err(str(e))


def condensatori_combinazione(combinazione, valori_uF):
    try:
        valori_f = [float(v) * 1e-6 for v in valori_uF if float(v) > 0]
        r = componenti_passivi.condensatori_serie(valori_f) if combinazione == "Serie" else componenti_passivi.condensatori_parallelo(valori_f)
        r["valore_equivalente_uF"] = r["valore_equivalente"] * 1e6
        r["n_componenti"] = len(valori_f)
        return r
    except ValueError as e:
        return _err(str(e))


def valore_normalizzato_e(valore, serie):
    try:
        return componenti_passivi.valore_normalizzato_e(float(valore), serie)
    except ValueError as e:
        return _err(str(e))


def resistenza_limitazione_led(v_alimentazione, v_forward_led, corrente_ma):
    try:
        return componenti_passivi.resistenza_limitazione_led(float(v_alimentazione), float(v_forward_led), float(corrente_ma))
    except ValueError as e:
        return _err(str(e))


def partitore_tensione_vout(v_in, r1_ohm, r2_ohm):
    try:
        return componenti_passivi.partitore_tensione_vout(float(v_in), float(r1_ohm), float(r2_ohm))
    except ValueError as e:
        return _err(str(e))


def partitore_tensione_r2(v_in, v_out, r1_ohm):
    try:
        return componenti_passivi.partitore_tensione_r2(float(v_in), float(v_out), float(r1_ohm))
    except ValueError as e:
        return _err(str(e))


def costante_di_tempo(tipo, resistenza_ohm, c_o_l, percentuale_target):
    try:
        return componenti_passivi.costante_di_tempo(tipo, float(resistenza_ohm), float(c_o_l), float(percentuale_target))
    except ValueError as e:
        return _err(str(e))


def wheatstone_resistenza_incognita(r1_ohm, r2_ohm, r3_ohm):
    try:
        return componenti_passivi.wheatstone_resistenza_incognita(float(r1_ohm), float(r2_ohm), float(r3_ohm))
    except ValueError as e:
        return _err(str(e))


def awg_a_mm2(awg):
    try:
        return componenti_passivi.awg_a_mm2(float(awg))
    except ValueError as e:
        return _err(str(e))


def mm2_a_awg(area_mm2):
    try:
        return componenti_passivi.mm2_a_awg(float(area_mm2))
    except ValueError as e:
        return _err(str(e))


def decodifica_smd_standard(codice):
    try:
        return componenti_passivi.decodifica_smd_standard(codice)
    except ValueError as e:
        return _err(str(e))


def decodifica_smd_eia96(codice):
    try:
        return componenti_passivi.decodifica_smd_eia96(codice)
    except ValueError as e:
        return _err(str(e))


def lista_colori_resistore():
    return {"colori": componenti_passivi.lista_colori_resistore()}


def frequenza_taglio_rc_rl(tipo, resistenza_ohm, c_o_l):
    try:
        return componenti_passivi.frequenza_taglio_rc_rl(tipo, float(resistenza_ohm), float(c_o_l))
    except ValueError as e:
        return _err(str(e))


def guadagno_op_amp(configurazione, r1_ohm, r2_ohm):
    try:
        return componenti_passivi.guadagno_op_amp(configurazione, float(r1_ohm), float(r2_ohm))
    except ValueError as e:
        return _err(str(e))


def diodo_zener_regolatore(v_alimentazione, v_zener, r_serie_ohm, r_carico_ohm):
    try:
        return componenti_passivi.diodo_zener_regolatore(
            float(v_alimentazione), float(v_zener), float(r_serie_ohm), float(r_carico_ohm)
        )
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Trasformatore

def trasformatore_calcola(S_kVA, V1_V, V2_V, P_ferro_W, P_rame_W, V_cc_pct, I0_pct, cos_phi, sistema):
    try:
        r = trasformatore.calcola_trasformatore(
            float(S_kVA), float(V1_V), float(V2_V), float(P_ferro_W), float(P_rame_W),
            float(V_cc_pct), float(I0_pct), float(cos_phi), trifase=(sistema == "Trifase"),
        )
        return _sanifica(r)
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Circuito RLC

def rlc_impedenza(configurazione, R, L_mH, C_uF, f):
    try:
        L_H = float(L_mH) / 1000.0
        C_F = float(C_uF) / 1e6
        if configurazione == "Serie":
            r = circuito_rlc.impedenza_serie(float(R), L_H, C_F, float(f))
        else:
            r = circuito_rlc.impedenza_parallelo(float(R), L_H, C_F, float(f))
        return _sanifica(r)
    except ValueError as e:
        return _err(str(e))


def rlc_risonanza(configurazione, L_mH, C_uF, R):
    try:
        L_H = float(L_mH) / 1000.0
        C_F = float(C_uF) / 1e6
        if configurazione == "Serie":
            r = circuito_rlc.risonanza_serie(L_H, C_F, float(R))
        else:
            r = circuito_rlc.risonanza_parallelo(L_H, C_F, float(R) if float(R) > 0 else float("inf"))
        return _sanifica(r)
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Armoniche / THD

def thd_calcola(fondamentale_rms, h3, h5, h7, h9, h11, h13):
    try:
        armoniche = {}
        for ordine, ampiezza in ((3, h3), (5, h5), (7, h7), (9, h9), (11, h11), (13, h13)):
            if float(ampiezza) > 0:
                armoniche[ordine] = float(ampiezza)
        if not armoniche:
            return _err("Inserire almeno un'armonica con ampiezza > 0.")
        r = armonie_thd.calcola_thd(float(fondamentale_rms), armoniche)
        # I contributi annidati vengono compattati in stringhe leggibili
        r["contributi"] = {
            f"h{ordine}": f"{c['pct_fondamentale']:.1f}% della fondamentale"
            for ordine, c in r["contributi"].items()
        }
        return _sanifica(r)
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Batterie / UPS

def ups_autonomia(C_Ah, V_nom_V, P_carico_W, eta_inverter, DOD):
    try:
        return _sanifica(batterie_ups.calcola_autonomia(
            float(C_Ah), float(V_nom_V), float(P_carico_W), float(eta_inverter), float(DOD)))
    except ValueError as e:
        return _err(str(e))


def ups_dimensiona_banco(P_carico_W, t_autonomia_h, V_banco_V, eta_inverter, DOD, fattore_invecchiamento):
    try:
        return _sanifica(batterie_ups.dimensiona_banco(
            float(P_carico_W), float(t_autonomia_h), float(V_banco_V),
            float(eta_inverter), float(DOD), float(fattore_invecchiamento)))
    except ValueError as e:
        return _err(str(e))


def ups_corrente_carica(C_Ah):
    try:
        return _sanifica(batterie_ups.corrente_carica(float(C_Ah)))
    except ValueError as e:
        return _err(str(e))


def ups_correzione_temperatura(C_Ah_nominale, T_C, tipo):
    try:
        return _sanifica(batterie_ups.correzione_temperatura(float(C_Ah_nominale), float(T_C), tipo))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Impianto di terra

def terra_picchetto(L_m, rho_ohm_m, d_m):
    try:
        return _sanifica(impianto_terra.resistenza_dispersore_picchetto(
            float(L_m), float(rho_ohm_m), float(d_m)))
    except ValueError as e:
        return _err(str(e))


def terra_picchetti_paralleli(R_singolo_ohm, n, coeff_riduzione):
    try:
        return _sanifica(impianto_terra.resistenza_picchetti_paralleli(
            float(R_singolo_ohm), int(n), float(coeff_riduzione)))
    except ValueError as e:
        return _err(str(e))


def terra_sezione_pe(I_g_A, t_s, k):
    try:
        return _sanifica(impianto_terra.sezione_minima_pe(float(I_g_A), float(t_s), float(k)))
    except ValueError as e:
        return _err(str(e))


def terra_tensione_contatto(R_terra_ohm, I_g_A, UTp_V):
    try:
        return _sanifica(impianto_terra.verifica_tensione_contatto(
            float(R_terra_ohm), float(I_g_A), float(UTp_V)))
    except ValueError as e:
        return _err(str(e))


def terra_coordinamento_tt(R_terra_ohm, I_dn_A, UTp_V):
    try:
        return _sanifica(impianto_terra.coordinamento_tt(
            float(R_terra_ohm), float(I_dn_A), float(UTp_V)))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Selettività protezioni

def selettivita_amperometrica(I_n_monte_A, I_n_valle_A, rapporto_minimo):
    try:
        return _sanifica(selettivita_protezioni.verifica_selettivita_amperometrica(
            float(I_n_monte_A), float(I_n_valle_A), float(rapporto_minimo)))
    except ValueError as e:
        return _err(str(e))


def selettivita_differenziale(I_dn_monte_mA, I_dn_valle_mA, t_monte_ms, t_valle_ms):
    try:
        return _sanifica(selettivita_protezioni.verifica_selettivita_differenziale(
            float(I_dn_monte_mA), float(I_dn_valle_mA), float(t_monte_ms), float(t_valle_ms)))
    except ValueError as e:
        return _err(str(e))


def selettivita_icc_minima(V_V, Z_guasto_ohm):
    try:
        return _sanifica(selettivita_protezioni.corrente_corto_circuito_minima(
            float(V_V), float(Z_guasto_ohm)))
    except ValueError as e:
        return _err(str(e))


def selettivita_tempo_intervento(I_In, tipo_curva):
    try:
        return _sanifica(selettivita_protezioni.tempo_intervento_curva(float(I_In), tipo_curva))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Fotovoltaico

def fv_producibilita_annua(P_picco_kWp, irraggiamento_kWh_m2_anno, performance_ratio):
    try:
        return _sanifica(fotovoltaico.producibilita_annua(
            float(P_picco_kWp), float(irraggiamento_kWh_m2_anno), float(performance_ratio)))
    except ValueError as e:
        return _err(str(e))


def fv_numero_pannelli(P_picco_richiesta_kWp, P_pannello_Wp):
    try:
        return _sanifica(fotovoltaico.numero_pannelli(float(P_picco_richiesta_kWp), float(P_pannello_Wp)))
    except ValueError as e:
        return _err(str(e))


def fv_dimensiona_stringa(V_oc_pannello_V, n_pannelli_stringa, V_max_inverter_V, coeff_temp_pct_C, T_min_C):
    try:
        return _sanifica(fotovoltaico.dimensiona_stringa(
            float(V_oc_pannello_V), int(n_pannelli_stringa), float(V_max_inverter_V),
            float(coeff_temp_pct_C), float(T_min_C)))
    except ValueError as e:
        return _err(str(e))


def fv_scelta_inverter(P_picco_kWp, rapporto_dimensionamento):
    try:
        return _sanifica(fotovoltaico.scelta_inverter(float(P_picco_kWp), float(rapporto_dimensionamento)))
    except ValueError as e:
        return _err(str(e))


def fv_tempo_ritorno(costo_impianto_eur, E_anno_kWh, prezzo_energia_eur_kWh, autoconsumo_pct):
    try:
        return _sanifica(fotovoltaico.tempo_ritorno_investimento(
            float(costo_impianto_eur), float(E_anno_kWh), float(prezzo_energia_eur_kWh), float(autoconsumo_pct)))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Gruppo elettrogeno

def ge_potenza_spunto(P_kW, cos_phi, fattore_spunto, eta):
    try:
        return _sanifica(gruppo_elettrogeno.potenza_spunto_motore(
            float(P_kW), float(cos_phi), float(fattore_spunto), float(eta)))
    except ValueError as e:
        return _err(str(e))


def ge_dimensiona_gruppo(carichi_kW, cos_phi_medio, fattore_contemporaneita, margine_sicurezza):
    try:
        valori = [float(v) for v in carichi_kW if float(v) > 0]
        return _sanifica(gruppo_elettrogeno.dimensiona_gruppo(
            valori, float(cos_phi_medio), float(fattore_contemporaneita), float(margine_sicurezza)))
    except ValueError as e:
        return _err(str(e))


def ge_autonomia_serbatoio(V_serbatoio_L, P_kW, consumo_specifico_L_kWh, fattore_carico):
    try:
        return _sanifica(gruppo_elettrogeno.autonomia_serbatoio(
            float(V_serbatoio_L), float(P_kW), float(consumo_specifico_L_kWh), float(fattore_carico)))
    except ValueError as e:
        return _err(str(e))


def ge_serbatoio_per_autonomia(P_kW, t_autonomia_h, consumo_specifico_L_kWh, fattore_carico):
    try:
        return _sanifica(gruppo_elettrogeno.serbatoio_per_autonomia(
            float(P_kW), float(t_autonomia_h), float(consumo_specifico_L_kWh), float(fattore_carico)))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Quadro elettrico

def quadro_potenza_dissipata(potenze_W):
    try:
        valori = [float(v) for v in potenze_W if float(v) > 0]
        componenti = {f"Componente {i+1}": v for i, v in enumerate(valori)}
        return _sanifica(quadro_elettrico.potenza_dissipata_componenti(componenti))
    except ValueError as e:
        return _err(str(e))


def quadro_aumento_temperatura(P_diss_W, superficie_m2, k_trasmissione):
    try:
        return _sanifica(quadro_elettrico.aumento_temperatura_quadro(
            float(P_diss_W), float(superficie_m2), float(k_trasmissione)))
    except ValueError as e:
        return _err(str(e))


def quadro_superficie(larghezza_m, altezza_m, profondita_m, installato_a_parete):
    try:
        return _sanifica(quadro_elettrico.superficie_quadro(
            float(larghezza_m), float(altezza_m), float(profondita_m), bool(installato_a_parete)))
    except ValueError as e:
        return _err(str(e))


def quadro_portata_ventilazione(P_diss_W, delta_T_max_K):
    try:
        return _sanifica(quadro_elettrico.portata_ventilazione_forzata(float(P_diss_W), float(delta_T_max_K)))
    except ValueError as e:
        return _err(str(e))


def quadro_verifica_temperatura(P_diss_W, superficie_m2, T_amb_C, T_max_componenti_C, k_trasmissione):
    try:
        return _sanifica(quadro_elettrico.verifica_temperatura_quadro(
            float(P_diss_W), float(superficie_m2), float(T_amb_C),
            float(T_max_componenti_C), float(k_trasmissione)))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Rifasamento condensatori

def rifc_potenza_reattiva_attuale(P_kW, cos_phi):
    try:
        return _sanifica(rifasamento_condensatori.potenza_reattiva_attuale(float(P_kW), float(cos_phi)))
    except ValueError as e:
        return _err(str(e))


def rifc_kvar_necessari(P_kW, cos_phi_attuale, cos_phi_target):
    try:
        return _sanifica(rifasamento_condensatori.kvar_necessari(
            float(P_kW), float(cos_phi_attuale), float(cos_phi_target)))
    except ValueError as e:
        return _err(str(e))


def rifc_capacita_condensatori(Q_c_kvar, V_linea_V, collegamento):
    try:
        return _sanifica(rifasamento_condensatori.capacita_condensatori(
            float(Q_c_kvar), float(V_linea_V), collegamento))
    except ValueError as e:
        return _err(str(e))


def rifc_verifica_rifasamento(P_kW, cos_phi_attuale, Q_aggiunta_kvar, V_V):
    try:
        return _sanifica(rifasamento_condensatori.verifica_rifasamento(
            float(P_kW), float(cos_phi_attuale), float(Q_aggiunta_kvar), float(V_V)))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Caduta di tensione BT

def cdbt_monofase(I_A, L_m, S_mm2, cos_phi, conduttore):
    try:
        return _sanifica(caduta_tensione_bt.caduta_tensione_monofase(
            float(I_A), float(L_m), float(S_mm2), float(cos_phi), conduttore))
    except ValueError as e:
        return _err(str(e))


def cdbt_trifase(I_A, L_m, S_mm2, cos_phi, conduttore):
    try:
        return _sanifica(caduta_tensione_bt.caduta_tensione_trifase(
            float(I_A), float(L_m), float(S_mm2), float(cos_phi), conduttore))
    except ValueError as e:
        return _err(str(e))


def cdbt_sezione_da_caduta_max(P_kW, V_V, L_m, dV_pct_max, cos_phi, tipo, conduttore):
    try:
        return _sanifica(caduta_tensione_bt.sezione_da_caduta_max(
            float(P_kW), float(V_V), float(L_m), float(dV_pct_max), float(cos_phi), tipo, conduttore))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Avviamento motore

def avv_correnti_motore(P_kW, V_V, cos_phi, eta, Ia_In):
    try:
        return _sanifica(avviamento_motore.correnti_motore(
            float(P_kW), float(V_V), float(cos_phi), float(eta), float(Ia_In)))
    except ValueError as e:
        return _err(str(e))


def avv_coppia_motore(P_kW, n_rpm, Ma_Mn):
    try:
        return _sanifica(avviamento_motore.coppia_motore(float(P_kW), float(n_rpm), float(Ma_Mn)))
    except ValueError as e:
        return _err(str(e))


def avv_caduta_tensione(I_avv_A, Z_rete_mohm, V_nom_V):
    try:
        return _sanifica(avviamento_motore.caduta_tensione_avviamento(
            float(I_avv_A), float(Z_rete_mohm), float(V_nom_V)))
    except ValueError as e:
        return _err(str(e))


def avv_metodi_avviamento(P_kW, V_V, cos_phi, eta):
    try:
        r = avviamento_motore.metodi_avviamento(float(P_kW), float(V_V), float(cos_phi), float(eta))
        piatto = {
            "I_nominale_A": r["I_nominale_A"],
            "I_avviamento_diretto_A": r["I_avviamento_diretto_A"],
        }
        for nome, dati in r["metodi"].items():
            piatto[nome] = (
                f"I={dati['I_avviamento_A']:.1f} A (×{dati['fattore_corrente']:g} In), "
                f"coppia ×{dati['fattore_coppia']:.2f} — {dati['note']}"
            )
        return _sanifica(piatto)
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Dissipatore

def diss_temperatura_giunzione(P_W, T_amb_C, R_jc, R_cs, R_sa_presente, R_sa):
    try:
        r_sa = float(R_sa) if bool(R_sa_presente) else None
        return _sanifica(dissipatore.temperatura_giunzione(
            float(P_W), float(T_amb_C), float(R_jc), float(R_cs), r_sa))
    except ValueError as e:
        return _err(str(e))


def diss_rsa_necessario(P_W, Tj_max_C, T_amb_C, R_jc, R_cs):
    try:
        return _sanifica(dissipatore.rsa_necessario(
            float(P_W), float(Tj_max_C), float(T_amb_C), float(R_jc), float(R_cs)))
    except ValueError as e:
        return _err(str(e))


def diss_potenza_max_dissipabile(Tj_max_C, T_amb_C, R_jc, R_cs, R_sa_presente, R_sa):
    try:
        r_sa = float(R_sa) if bool(R_sa_presente) else None
        return _sanifica(dissipatore.potenza_max_dissipabile(
            float(Tj_max_C), float(T_amb_C), float(R_jc), float(R_cs), r_sa))
    except ValueError as e:
        return _err(str(e))


def diss_curva_derating(P_max_25C, Tj_max_C, T_amb_max_C):
    try:
        return _sanifica(dissipatore.curva_derating(
            float(P_max_25C), float(Tj_max_C), float(T_amb_max_C)))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Illuminotecnica

def illum_lista_ambienti():
    return {"ambienti": illuminotecnica.lista_ambienti()}


def illum_requisiti_ambiente(ambiente):
    try:
        return _sanifica(illuminotecnica.requisiti_ambiente(ambiente))
    except ValueError as e:
        return _err(str(e))


def illum_numero_lampade(Em_lux, A_m2, phi_corpo_lm, MF, UF):
    try:
        return _sanifica(illuminotecnica.calcola_numero_lampade(
            float(Em_lux), float(A_m2), float(phi_corpo_lm), float(MF), float(UF)))
    except ValueError as e:
        return _err(str(e))


def illum_room_index(L_m, W_m, H_m, h_lavoro_m):
    try:
        return _sanifica(illuminotecnica.calcola_room_index(
            float(L_m), float(W_m), float(H_m), float(h_lavoro_m)))
    except ValueError as e:
        return _err(str(e))


def illum_potenza_illuminazione(N_corpi, P_corpo_W, A_m2):
    try:
        return _sanifica(illuminotecnica.calcola_potenza_illuminazione(
            int(N_corpi), float(P_corpo_W), float(A_m2)))
    except ValueError as e:
        return _err(str(e))


def illum_mf(LMF, LSF, LLMF, RSMF):
    try:
        return _sanifica(illuminotecnica.calcola_mf(float(LMF), float(LSF), float(LLMF), float(RSMF)))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Libreria cavi

def libcavi_liste():
    return {
        "cavi": libreria_cavi.lista_cavi_commerciali(),
        "sezioni": libreria_cavi.lista_sezioni_libreria(),
    }


def libcavi_parametri_cavo(nome_cavo, sezione):
    try:
        return _sanifica(libreria_cavi.parametri_cavo(nome_cavo, float(sezione)))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Batch cavi (singola linea)

def batch_dimensiona_linea(nome, fasi, Ib_A, lunghezza_m, cos_phi, isolante, posa, T_amb, n_circuiti, n_parallelo):
    try:
        linea = {
            "nome": nome, "fasi": fasi, "Ib_A": float(Ib_A), "lunghezza_m": float(lunghezza_m),
            "cos_phi": float(cos_phi), "isolante": isolante, "posa": posa,
            "T_amb": float(T_amb), "n_circuiti": int(n_circuiti), "n_parallelo": int(n_parallelo),
        }
        return _sanifica(batch_cavi.dimensiona_linea(linea))
    except (ValueError, KeyError, TypeError) as e:
        return _err(str(e))


# ------------------------------------------------------------------ Costi energetici

def costi_costo_annuo(potenza_kW, ore_anno, tariffa_eur_kWh):
    try:
        return _sanifica(costi_energetici.costo_annuo(float(potenza_kW), float(ore_anno), float(tariffa_eur_kWh)))
    except ValueError as e:
        return _err(str(e))


def costi_confronto_efficientamento(P_prima_kW, P_dopo_kW, ore_anno, tariffa_eur_kWh, extra_investimento_eur):
    try:
        return _sanifica(costi_energetici.confronto_efficientamento(
            float(P_prima_kW), float(P_dopo_kW), float(ore_anno), float(tariffa_eur_kWh),
            float(extra_investimento_eur)))
    except ValueError as e:
        return _err(str(e))


def costi_confronto_motore_ie(P_mecc_kW, eta_prima_pct, eta_dopo_pct, ore_anno, tariffa_eur_kWh, extra_investimento_eur):
    try:
        return _sanifica(costi_energetici.confronto_motore_ie(
            float(P_mecc_kW), float(eta_prima_pct), float(eta_dopo_pct),
            float(ore_anno), float(tariffa_eur_kWh), float(extra_investimento_eur)))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Vibrazioni

def vib_converti_grandezze(grandezza_in, valore, frequenza_hz):
    try:
        return _sanifica(vibrazioni.converti_grandezze_vibrazionali(
            grandezza_in, float(valore), float(frequenza_hz)))
    except ValueError as e:
        return _err(str(e))


def vib_classifica_iso10816(velocita_rms_mms, classe):
    try:
        zona, colore, descr, lim = vibrazioni.classifica_iso10816(float(velocita_rms_mms), classe)
        return _sanifica({
            "zona": zona, "colore": colore, "descrizione": descr,
            "limite_A_mms": lim["A"], "limite_B_mms": lim["B"], "limite_C_mms": lim["C"],
        })
    except ValueError as e:
        return _err(str(e))


def vib_frequenza_naturale(k_nm, m_kg, zeta):
    try:
        return _sanifica(vibrazioni.calcola_frequenza_naturale(float(k_nm), float(m_kg), float(zeta)))
    except ValueError as e:
        return _err(str(e))


def vib_velocita_critica(delta_mm):
    try:
        return _sanifica(vibrazioni.calcola_velocita_critica(float(delta_mm)))
    except ValueError as e:
        return _err(str(e))


def vib_squilibrio_iso1940(massa_kg, raggio_corr_mm, velocita_rpm, grado_nome):
    try:
        grado_g = vibrazioni.valore_grado_iso1940(grado_nome)
        if grado_g is None:
            return _err(f"Grado ISO 1940 non riconosciuto: '{grado_nome}'.")
        return _sanifica(vibrazioni.calcola_squilibrio_iso1940(
            float(massa_kg), float(raggio_corr_mm), float(velocita_rpm), grado_g))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Resistenza materiali

def rm_trazione_compressione(F_N, A_mm2, E_mpa, L_mm, sigma_amm_mpa):
    try:
        return _sanifica(resistenza_materiali.calcola_trazione_compressione(
            float(F_N), float(A_mm2), float(E_mpa), float(L_mm), float(sigma_amm_mpa)))
    except ValueError as e:
        return _err(str(e))


def rm_sezione_rettangolare(b_mm, h_mm):
    try:
        return _sanifica(resistenza_materiali.sezione_rettangolare(float(b_mm), float(h_mm)))
    except ValueError as e:
        return _err(str(e))


def rm_sezione_cerchio(d_mm):
    try:
        return _sanifica(resistenza_materiali.sezione_cerchio_pieno(float(d_mm)))
    except ValueError as e:
        return _err(str(e))


def rm_sezione_tubo(D_mm, d_mm):
    try:
        return _sanifica(resistenza_materiali.sezione_tubo(float(D_mm), float(d_mm)))
    except ValueError as e:
        return _err(str(e))


def rm_sezione_doppio_t(h_mm, b_mm, tw_mm, tf_mm):
    try:
        return _sanifica(resistenza_materiali.sezione_hea_ipn(
            float(h_mm), float(b_mm), float(tw_mm), float(tf_mm)))
    except ValueError as e:
        return _err(str(e))


def rm_trave(schema, L_mm, F_N, q_N_mm, I_mm4, W_mm3, E_mpa, sigma_amm_mpa):
    try:
        return _sanifica(resistenza_materiali.calcola_trave(
            schema, float(L_mm), float(F_N), float(q_N_mm), float(I_mm4), float(W_mm3),
            float(E_mpa), float(sigma_amm_mpa)))
    except ValueError as e:
        return _err(str(e))


def rm_verifica_flessione(M_max_nm, W_mm3, sigma_amm_mpa):
    try:
        return _sanifica(resistenza_materiali.verifica_flessione(
            float(M_max_nm), float(W_mm3), float(sigma_amm_mpa)))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Bulloneria

def bull_serraggio(diametro, classe, lubrificazione, nu_precarico, FS):
    try:
        return _sanifica(bulloneria.calcola_serraggio(
            diametro, classe, lubrificazione, float(nu_precarico), float(FS)))
    except ValueError as e:
        return _err(str(e))


def bull_verifica(diametro, classe, F_trazione_N, F_taglio_N, FS, n_piani_taglio):
    try:
        return _sanifica(bulloneria.verifica_bullone(
            diametro, classe, float(F_trazione_N), float(F_taglio_N), float(FS), int(n_piani_taglio)))
    except ValueError as e:
        return _err(str(e))


def bull_dimensiona_flangia(F_totale_N, diametro, classe, lubrificazione, nu_precarico, FS):
    try:
        return _sanifica(bulloneria.dimensiona_flangia(
            float(F_totale_N), diametro, classe, lubrificazione, float(nu_precarico), float(FS)))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Cuscinetti

def cusc_durata(C_kN, P_kN, tipo, n_rpm):
    try:
        r1 = cuscinetti.durata_l10(float(C_kN), float(P_kN), tipo)
        r2 = cuscinetti.durata_ore(r1["L10_milioni_giri"], float(n_rpm))
        return _sanifica({**r1, **r2})
    except ValueError as e:
        return _err(str(e))


def cusc_carico_equivalente(forze, frazioni_tempo, esponente):
    try:
        return _sanifica(cuscinetti.carico_dinamico_equivalente(
            [float(v) for v in forze], [float(v) for v in frazioni_tempo], float(esponente)))
    except ValueError as e:
        return _err(str(e))


def cusc_fattore_durata_richiesta(L10h_richiesta, n_rpm):
    try:
        return _sanifica(cuscinetti.fattore_durata_richiesta(float(L10h_richiesta), float(n_rpm)))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Molle

def molle_compressione(d_filo_mm, D_medio_mm, n_spire_attive, G_MPa):
    try:
        return _sanifica(molle.molla_compressione(
            float(d_filo_mm), float(D_medio_mm), float(n_spire_attive), float(G_MPa)))
    except ValueError as e:
        return _err(str(e))


def molle_tensione_torsionale(F_N, d_filo_mm, D_medio_mm):
    try:
        return _sanifica(molle.tensione_torsionale_molla(float(F_N), float(d_filo_mm), float(D_medio_mm)))
    except ValueError as e:
        return _err(str(e))


def molle_frequenza_naturale(k_N_mm, massa_kg):
    try:
        return _sanifica(molle.frequenza_naturale_molla(float(k_N_mm), float(massa_kg)))
    except ValueError as e:
        return _err(str(e))


def molle_torsione(d_filo_mm, D_medio_mm, n_spire_attive, E_MPa):
    try:
        return _sanifica(molle.molla_torsione(
            float(d_filo_mm), float(D_medio_mm), float(n_spire_attive), float(E_MPa)))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Ruote dentate

def ruote_geometria(modulo_mm, n_denti, angolo_pressione_deg):
    try:
        return _sanifica(ruote_dentate.geometria_ruota(
            float(modulo_mm), int(n_denti), float(angolo_pressione_deg)))
    except ValueError as e:
        return _err(str(e))


def ruote_modulo_minimo_lewis(coppia_Nm, n_denti, b_m_rapporto, sigma_amm_MPa, Y_lewis, Kv):
    try:
        return _sanifica(ruote_dentate.modulo_minimo_lewis(
            float(coppia_Nm), int(n_denti), float(b_m_rapporto), float(sigma_amm_MPa),
            float(Y_lewis), float(Kv)))
    except ValueError as e:
        return _err(str(e))


def ruote_verifica_flessione_lewis(coppia_Nm, modulo_mm, n_denti, b_mm, Y_lewis, Kv):
    try:
        return _sanifica(ruote_dentate.verifica_flessione_lewis(
            float(coppia_Nm), float(modulo_mm), int(n_denti), float(b_mm), float(Y_lewis), float(Kv)))
    except ValueError as e:
        return _err(str(e))


def ruote_rapporto_trasmissione(z1, z2):
    try:
        return _sanifica(ruote_dentate.rapporto_trasmissione_ruote(int(z1), int(z2)))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Alberi a torsione

def alb_momento_torcente(P_kW, n_rpm):
    try:
        return _sanifica(alberi_torsione.momento_torcente(float(P_kW), float(n_rpm)))
    except ValueError as e:
        return _err(str(e))


def alb_diametro_minimo_torsione(Mt_Nm, tau_amm_MPa):
    try:
        return _sanifica(alberi_torsione.diametro_minimo_torsione(float(Mt_Nm), float(tau_amm_MPa)))
    except ValueError as e:
        return _err(str(e))


def alb_tensioni(Mt_Nm, Mf_Nm, d_mm):
    try:
        return _sanifica(alberi_torsione.tensioni_albero(float(Mt_Nm), float(Mf_Nm), float(d_mm)))
    except ValueError as e:
        return _err(str(e))


def alb_fattore_sicurezza_statico(Mt_Nm, Mf_Nm, d_mm, materiale):
    try:
        mat = alberi_torsione.MATERIALI_ALBERI.get(materiale)
        if mat is None:
            return _err(f"Materiale non riconosciuto: '{materiale}'.")
        return _sanifica(alberi_torsione.fattore_sicurezza_statico(
            float(Mt_Nm), float(Mf_Nm), float(d_mm), mat["Re_MPa"]))
    except ValueError as e:
        return _err(str(e))


def alb_verifica_goodman(sigma_m_MPa, sigma_a_MPa, materiale):
    try:
        mat = alberi_torsione.MATERIALI_ALBERI.get(materiale)
        if mat is None:
            return _err(f"Materiale non riconosciuto: '{materiale}'.")
        return _sanifica(alberi_torsione.verifica_goodman(
            float(sigma_m_MPa), float(sigma_a_MPa), mat["Rm_MPa"], mat["sigma_f_MPa"]))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Saldature

def sald_resistenza_ammissibile(acciaio):
    try:
        return _sanifica(saldature.resistenza_ammissibile_cordone(acciaio))
    except ValueError as e:
        return _err(str(e))


def sald_gola_minima(t_min_pezzi_mm):
    try:
        return _sanifica(saldature.gola_minima(float(t_min_pezzi_mm)))
    except ValueError as e:
        return _err(str(e))


def sald_verifica_taglio(F_kN, a_mm, L_mm, acciaio):
    try:
        return _sanifica(saldature.verifica_cordone_taglio(float(F_kN), float(a_mm), float(L_mm), acciaio))
    except ValueError as e:
        return _err(str(e))


def sald_verifica_normale(F_kN, a_mm, L_mm, angolo_deg, acciaio):
    try:
        return _sanifica(saldature.verifica_cordone_normale(
            float(F_kN), float(a_mm), float(L_mm), float(angolo_deg), acciaio))
    except ValueError as e:
        return _err(str(e))


def sald_doppio_t(F_kN, a_mm, larghezza_mm, acciaio):
    try:
        return _sanifica(saldature.cordone_a_doppio_T(float(F_kN), float(a_mm), float(larghezza_mm), acciaio))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Trasmissioni

def trasm_stadio_singolo(n1_rpm, T1_nm, i, eta):
    try:
        return _sanifica(trasmissioni.calcola_trasmissione(float(n1_rpm), float(T1_nm), float(i), float(eta)))
    except ValueError as e:
        return _err(str(e))


def trasm_riduttore_multistadio(n_in_rpm, T_in_nm, rapporti_i, rendimenti_eta):
    try:
        if len(rapporti_i) != len(rendimenti_eta):
            return _err("Le liste rapporti_i e rendimenti_eta devono avere lo stesso numero di stadi.")
        stadi = [{"i": float(i), "eta": float(e)} for i, e in zip(rapporti_i, rendimenti_eta)]
        return _sanifica(trasmissioni.calcola_riduttore_multistadio(float(n_in_rpm), float(T_in_nm), stadi))
    except ValueError as e:
        return _err(str(e))


def trasm_geometria_cinghia(d1_mm, d2_mm, C_mm):
    try:
        return _sanifica(trasmissioni.calcola_geometria_cinghia(float(d1_mm), float(d2_mm), float(C_mm)))
    except ValueError as e:
        return _err(str(e))


def trasm_converti_ptc(grandezza_nota, val1, val2):
    try:
        return _sanifica(trasmissioni.converti_ptc(grandezza_nota, float(val1), float(val2)))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Nastri trasportatori

def nastri_portata_massica(B_m, v_ms, rho_bulk_kg_m3, angolo_surcharge_deg, inclinazione_deg):
    try:
        return _sanifica(nastri_trasportatori.portata_massica(
            float(B_m), float(v_ms), float(rho_bulk_kg_m3),
            float(angolo_surcharge_deg), float(inclinazione_deg)))
    except ValueError as e:
        return _err(str(e))


def nastri_potenza_motore(Q_th, L_m, H_m, eta_trasmissione, f_attrito,
                           massa_nastro_presente, massa_nastro_kg_m):
    try:
        m_nas = float(massa_nastro_kg_m) if bool(massa_nastro_presente) else None
        return _sanifica(nastri_trasportatori.potenza_motore(
            float(Q_th), float(L_m), float(H_m), float(eta_trasmissione), float(f_attrito), m_nas))
    except ValueError as e:
        return _err(str(e))


def nastri_tensione(P_motore_W, v_ms, D_puleggia_presente, D_puleggia_mm):
    try:
        d_pul = float(D_puleggia_mm) if bool(D_puleggia_presente) else None
        return _sanifica(nastri_trasportatori.tensione_nastro(float(P_motore_W), float(v_ms), d_pul))
    except ValueError as e:
        return _err(str(e))


def nastri_angolo_max_inclinazione(rho_bulk_kg_m3, tipo):
    try:
        return _sanifica(nastri_trasportatori.angolo_max_inclinazione(float(rho_bulk_kg_m3), tipo))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Pompe

def pompe_punto_lavoro(H0, Q_nom, H_nom, H_statica, Q_imp, H_imp):
    try:
        r = pompe.calcola_punto_lavoro(
            float(H0), float(Q_nom), float(H_nom), float(H_statica), float(Q_imp), float(H_imp))
        r.pop("Q_graf", None)
        r.pop("H_pompa_graf", None)
        r.pop("H_imp_graf", None)
        return _sanifica(r)
    except ValueError as e:
        return _err(str(e))


def pompe_potenza(Q_m3h, H_m, eta_pompa, rho_kg_m3):
    try:
        return _sanifica(pompe.calcola_potenza_pompa(float(Q_m3h), float(H_m), float(eta_pompa), float(rho_kg_m3)))
    except ValueError as e:
        return _err(str(e))


def pompe_npsh_disponibile(P_asp_bar_a, P_vap_bar_a, H_asp_m, v_asp_ms, perdite_asp_m):
    try:
        return _sanifica(pompe.calcola_npsh_disponibile(
            float(P_asp_bar_a), float(P_vap_bar_a), float(H_asp_m), float(v_asp_ms), float(perdite_asp_m)))
    except ValueError as e:
        return _err(str(e))


def pompe_ns(n_rpm, Q_m3s, H_m):
    try:
        return _sanifica(pompe.calcola_ns(float(n_rpm), float(Q_m3s), float(H_m)))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Perdite di carico concentrate

def perdcar_singolo_raccordo(nome_raccordo, v_ms, rho_kg_m3):
    try:
        K = perdite_carico.k_raccordo(nome_raccordo)
        r = perdite_carico.perdita_raccordo(K, float(v_ms), float(rho_kg_m3))
        r["raccordo"] = nome_raccordo
        return _sanifica(r)
    except ValueError as e:
        return _err(str(e))


def perdcar_lunghezza_equivalente(K, D_mm, lambda_f):
    try:
        return _sanifica({"L_eq_m": perdite_carico.lunghezza_equivalente(float(K), float(D_mm), float(lambda_f))})
    except ValueError as e:
        return _err(str(e))


def perdcar_allargamento_brusco(v1_ms, D1_mm, D2_mm, rho_kg_m3):
    try:
        return _sanifica(perdite_carico.perdita_allargamento_brusco(
            float(v1_ms), float(D1_mm), float(D2_mm), float(rho_kg_m3)))
    except ValueError as e:
        return _err(str(e))


def perdcar_restringimento_brusco(v2_ms, D1_mm, D2_mm, rho_kg_m3):
    try:
        return _sanifica(perdite_carico.perdita_restringimento_brusco(
            float(v2_ms), float(D1_mm), float(D2_mm), float(rho_kg_m3)))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Perdite di carico distribuite

def pcd_perdita_distribuita(Q_m3h, D_mm, L_m, rugosita_mm, nu_m2_s, rho_kg_m3):
    try:
        return _sanifica(perdite_carico_distribuite.perdita_distribuita(
            float(Q_m3h), float(D_mm), float(L_m), float(rugosita_mm), float(nu_m2_s), float(rho_kg_m3)))
    except ValueError as e:
        return _err(str(e))


def pcd_numero_reynolds(v_ms, D_mm, nu_m2_s):
    try:
        return _sanifica(perdite_carico_distribuite.numero_reynolds(float(v_ms), float(D_mm), float(nu_m2_s)))
    except ValueError as e:
        return _err(str(e))


def pcd_fattore_attrito(Re, rugosita_relativa):
    try:
        return _sanifica(perdite_carico_distribuite.fattore_attrito_swamee_jain(float(Re), float(rugosita_relativa)))
    except ValueError as e:
        return _err(str(e))


def pcd_diametro_da_velocita_max(Q_m3h, v_max_ms):
    try:
        return _sanifica(perdite_carico_distribuite.diametro_da_velocita_max(float(Q_m3h), float(v_max_ms)))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Scambiatori di calore

def scamb_bilancio_termico(m_h, cp_h, T_h_in, T_h_out, m_c, cp_c):
    try:
        return _sanifica(scambiatori.bilancio_termico(
            float(m_h), float(cp_h), float(T_h_in), float(T_h_out), float(m_c), float(cp_c)))
    except ValueError as e:
        return _err(str(e))


def scamb_lmtd(T_h_in, T_h_out, T_c_in, T_c_out, configurazione):
    try:
        return _sanifica(scambiatori.lmtd(float(T_h_in), float(T_h_out), float(T_c_in), float(T_c_out), configurazione))
    except ValueError as e:
        return _err(str(e))


def scamb_area_da_lmtd(Q_W, U_W_m2K, LMTD_K, F):
    try:
        return _sanifica(scambiatori.area_da_lmtd(float(Q_W), float(U_W_m2K), float(LMTD_K), float(F)))
    except ValueError as e:
        return _err(str(e))


def scamb_ntu_effectiveness(C_h, C_c, T_h_in, T_c_in, U_W_m2K, A_m2, configurazione):
    try:
        return _sanifica(scambiatori.ntu_effectiveness(
            float(C_h), float(C_c), float(T_h_in), float(T_c_in), float(U_W_m2K), float(A_m2), configurazione))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Isolamento termico

def isol_parete_piana(T_int_C, T_est_C, spessori_m, lambda_W_mK, R_si, R_se):
    try:
        if len(spessori_m) != len(lambda_W_mK):
            return _err("Le liste spessori_m e lambda_W_mK devono avere lo stesso numero di strati.")
        strati = [{"nome": f"Strato {i+1}", "spessore_m": float(s), "lambda_W_mK": float(l)}
                  for i, (s, l) in enumerate(zip(spessori_m, lambda_W_mK))]
        r = isolamento_termico.perdita_parete_piana(float(T_int_C), float(T_est_C), strati, float(R_si), float(R_se))
        r.pop("strati", None)
        return _sanifica(r)
    except ValueError as e:
        return _err(str(e))


def isol_tubo_cilindrico(T_fluid_C, T_amb_C, D_int_mm, spessori_m, lambda_W_mK, L_m, R_si, R_se):
    try:
        if len(spessori_m) != len(lambda_W_mK):
            return _err("Le liste spessori_m e lambda_W_mK devono avere lo stesso numero di strati.")
        strati = [{"nome": f"Strato {i+1}", "spessore_m": float(s), "lambda_W_mK": float(l)}
                  for i, (s, l) in enumerate(zip(spessori_m, lambda_W_mK))]
        return _sanifica(isolamento_termico.perdita_tubo_cilindrico(
            float(T_fluid_C), float(T_amb_C), float(D_int_mm), strati, float(L_m), float(R_si), float(R_se)))
    except ValueError as e:
        return _err(str(e))


def isol_verifica_condensa(T_sup_C, T_amb_C, UR_pct):
    try:
        return _sanifica(isolamento_termico.verifica_condensa(float(T_sup_C), float(T_amb_C), float(UR_pct)))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Condotte HVAC

def hvac_proprieta_aria(T_C, P_Pa):
    try:
        return _sanifica(condotte_hvac.proprieta_aria(float(T_C), float(P_Pa)))
    except ValueError as e:
        return _err(str(e))


def hvac_diametro_idraulico_rettangolare(a_mm, b_mm):
    try:
        return _sanifica({"Dh_mm": condotte_hvac.diametro_idraulico_rettangolare(float(a_mm), float(b_mm))})
    except ValueError as e:
        return _err(str(e))


def hvac_perdita_carico_condotta(Q_m3h, Dh_mm, L_m, forma, a_mm, b_mm, rugosita_mm, T_C):
    try:
        return _sanifica(condotte_hvac.perdita_carico_condotta(
            float(Q_m3h), float(Dh_mm), float(L_m), forma, float(a_mm), float(b_mm),
            float(rugosita_mm), float(T_C)))
    except ValueError as e:
        return _err(str(e))


def hvac_dimensiona_circolare(Q_m3h, v_max_ms):
    try:
        return _sanifica(condotte_hvac.dimensiona_condotta_circolare(float(Q_m3h), float(v_max_ms)))
    except ValueError as e:
        return _err(str(e))


def hvac_dimensiona_rettangolare(Q_m3h, rapporto_lati, v_max_ms):
    try:
        return _sanifica(condotte_hvac.dimensiona_condotta_rettangolare(
            float(Q_m3h), float(rapporto_lati), float(v_max_ms)))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Serbatoi

def serb_volume_geometrico(forma, D_m, H_m, L_m, W_m):
    try:
        if forma == "cilindro_vert":
            dim = {"D_m": float(D_m), "H_m": float(H_m)}
        elif forma == "cilindro_oriz":
            dim = {"D_m": float(D_m), "L_m": float(L_m)}
        elif forma == "parallelepipedo":
            dim = {"L_m": float(L_m), "W_m": float(W_m), "H_m": float(H_m)}
        elif forma == "cono":
            dim = {"D_m": float(D_m), "H_m": float(H_m)}
        elif forma == "sfera":
            dim = {"D_m": float(D_m)}
        else:
            return _err(f"Forma non riconosciuta: '{forma}'.")
        V_m3 = serbatoi.volume_geometrico(forma, **dim)
        return _sanifica({"V_m3": V_m3, "V_litri": V_m3 * 1000.0, "forma": forma})
    except (ValueError, KeyError) as e:
        return _err(str(e))


def serb_pressione_fondo(H_m, rho_kg_m3):
    try:
        return _sanifica(serbatoi.pressione_fondo(float(H_m), float(rho_kg_m3)))
    except ValueError as e:
        return _err(str(e))


def serb_portata_torricelli(H_m, D_foro_mm, Cd, rho_kg_m3):
    try:
        return _sanifica(serbatoi.portata_torricelli(float(H_m), float(D_foro_mm), float(Cd), float(rho_kg_m3)))
    except ValueError as e:
        return _err(str(e))


def serb_tempo_svuotamento(V_m3, H_m, D_foro_mm, Cd, A_serbatoio_presente, A_serbatoio_m2):
    try:
        A = float(A_serbatoio_m2) if bool(A_serbatoio_presente) else None
        return _sanifica(serbatoi.tempo_svuotamento(float(V_m3), float(H_m), float(D_foro_mm), float(Cd), A))
    except ValueError as e:
        return _err(str(e))


def serb_tempo_riempimento(V_m3, Q_m3h):
    try:
        return _sanifica(serbatoi.tempo_riempimento(float(V_m3), float(Q_m3h)))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Valvole di controllo

def valv_cv_liquido(Q_m3h, dP_bar, SG):
    try:
        return _sanifica(valvole_controllo.cv_liquido(float(Q_m3h), float(dP_bar), float(SG)))
    except ValueError as e:
        return _err(str(e))


def valv_cv_gas(Q_Nm3h, P1_bar_a, P2_bar_a, T_K, SG_gas):
    try:
        return _sanifica(valvole_controllo.cv_gas(
            float(Q_Nm3h), float(P1_bar_a), float(P2_bar_a), float(T_K), float(SG_gas)))
    except ValueError as e:
        return _err(str(e))


def valv_verifica_cavitazione(P1_bar_a, P2_bar_a, P_vap_bar_a):
    try:
        return _sanifica(valvole_controllo.verifica_cavitazione(
            float(P1_bar_a), float(P2_bar_a), float(P_vap_bar_a)))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Tubazioni in pressione

def tubp_spessore_minimo(materiale, DN, P_bar, E_giunzione, c_corrosione_mm, y):
    try:
        mat = tubazione_pressione.MATERIALI_TUBI.get(materiale)
        Do = tubazione_pressione.TABELLA_DN_DO_MM.get(int(DN))
        if mat is None:
            return _err(f"Materiale non riconosciuto: '{materiale}'.")
        if Do is None:
            return _err(f"DN non riconosciuto: '{DN}'.")
        r = tubazione_pressione.spessore_minimo(
            float(P_bar), Do, mat["f_MPa"], float(E_giunzione), float(c_corrosione_mm), float(y))
        r["D_esterno_mm"] = Do
        return _sanifica(r)
    except ValueError as e:
        return _err(str(e))


def tubp_pressione_ammissibile(materiale, DN, t_mm, E_giunzione, c_corrosione_mm, y):
    try:
        mat = tubazione_pressione.MATERIALI_TUBI.get(materiale)
        Do = tubazione_pressione.TABELLA_DN_DO_MM.get(int(DN))
        if mat is None:
            return _err(f"Materiale non riconosciuto: '{materiale}'.")
        if Do is None:
            return _err(f"DN non riconosciuto: '{DN}'.")
        return _sanifica(tubazione_pressione.pressione_ammissibile(
            float(t_mm), Do, mat["f_MPa"], float(E_giunzione), float(c_corrosione_mm), float(y)))
    except ValueError as e:
        return _err(str(e))


def tubp_verifica_tubazione(materiale, DN, P_bar, t_adottato_mm, E_giunzione, c_corrosione_mm):
    try:
        mat = tubazione_pressione.MATERIALI_TUBI.get(materiale)
        Do = tubazione_pressione.TABELLA_DN_DO_MM.get(int(DN))
        if mat is None:
            return _err(f"Materiale non riconosciuto: '{materiale}'.")
        if Do is None:
            return _err(f"DN non riconosciuto: '{DN}'.")
        return _sanifica(tubazione_pressione.verifica_tubazione(
            float(P_bar), Do, float(t_adottato_mm), mat["f_MPa"], float(E_giunzione), float(c_corrosione_mm)))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Pneumatica

def pneu_converti_portata(Qn_nl_min, P_bar_g, T_C):
    try:
        return _sanifica(pneumatica.converti_portata(float(Qn_nl_min), float(P_bar_g), float(T_C)))
    except ValueError as e:
        return _err(str(e))


def pneu_caduta_pressione_tubazione(Qn_nl_min, L_m, D_mm, P_bar_g, T_C, rugosita_mm):
    try:
        return _sanifica(pneumatica.caduta_pressione_tubazione(
            float(Qn_nl_min), float(L_m), float(D_mm), float(P_bar_g), float(T_C), float(rugosita_mm)))
    except ValueError as e:
        return _err(str(e))


def pneu_dimensiona_serbatoio(Qc_nl_min, t_s, P_max_bar_g, P_min_bar_g):
    try:
        return _sanifica(pneumatica.dimensiona_serbatoio(
            float(Qc_nl_min), float(t_s), float(P_max_bar_g), float(P_min_bar_g)))
    except ValueError as e:
        return _err(str(e))


def pneu_potenza_compressore(Qn_nl_min, P1_bar_g, P2_bar_g, eta_tot, n_stadi):
    try:
        return _sanifica(pneumatica.potenza_compressore(
            float(Qn_nl_min), float(P1_bar_g), float(P2_bar_g), float(eta_tot), int(n_stadi)))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Trasduttori di pressione

def trasd_ma_a_pressione(corrente_mA, fondo_scala_bar, P_min_bar):
    try:
        return _sanifica(trasduttori_pressione.ma_a_pressione(
            float(corrente_mA), float(fondo_scala_bar), float(P_min_bar)))
    except ValueError as e:
        return _err(str(e))


def trasd_pressione_a_ma(P_bar, fondo_scala_bar, P_min_bar):
    try:
        return _sanifica(trasduttori_pressione.pressione_a_ma(
            float(P_bar), float(fondo_scala_bar), float(P_min_bar)))
    except ValueError as e:
        return _err(str(e))


def trasd_errore_misura(I_misurata_mA, I_teorica_mA, fondo_scala_bar, accuratezza_pct_FS):
    try:
        return _sanifica(trasduttori_pressione.errore_misura_trasduttore(
            float(I_misurata_mA), float(I_teorica_mA), float(fondo_scala_bar), float(accuratezza_pct_FS)))
    except ValueError as e:
        return _err(str(e))


def trasd_caduta_tensione_loop(R_carico_ohm, lunghezza_cavo_m, sezione_cavo_mm2, V_alimentazione_V):
    try:
        return _sanifica(trasduttori_pressione.caduta_tensione_loop_4_20(
            float(R_carico_ohm), float(lunghezza_cavo_m), float(sezione_cavo_mm2), float(V_alimentazione_V)))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Rumore industriale

def rumore_somma_livelli(livelli_db):
    try:
        return _sanifica(rumore_industriale.somma_livelli_db([float(v) for v in livelli_db]))
    except ValueError as e:
        return _err(str(e))


def rumore_lex_8h(T_esposizioni_min, L_esposizioni_dBA):
    try:
        if len(T_esposizioni_min) != len(L_esposizioni_dBA):
            return _err("Le liste T_esposizioni_min e L_esposizioni_dBA devono avere la stessa lunghezza.")
        return _sanifica(rumore_industriale.lex_8h(
            [float(v) for v in T_esposizioni_min], [float(v) for v in L_esposizioni_dBA]))
    except ValueError as e:
        return _err(str(e))


def rumore_attenuazione_dpi(SNR_dB, L_amb_dBA):
    try:
        return _sanifica(rumore_industriale.attenuazione_dpi(float(SNR_dB), float(L_amb_dBA)))
    except ValueError as e:
        return _err(str(e))


def rumore_attenuazione_distanza(L_sorgente_dB, d1_m, d2_m):
    try:
        return _sanifica(rumore_industriale.attenuazione_distanza(float(L_sorgente_dB), float(d1_m), float(d2_m)))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Performance Level / SIL

def pl_calcola_PL(MTTFd_anni, DCavg_pct, categoria):
    try:
        return _sanifica(performance_level.calcola_PL(float(MTTFd_anni), float(DCavg_pct), categoria))
    except ValueError as e:
        return _err(str(e))


def pl_mttfd_da_b10d(B10d_cicli, n_operazioni_anno):
    try:
        return _sanifica(performance_level.MTTFd_da_B10d(float(B10d_cicli), float(n_operazioni_anno)))
    except ValueError as e:
        return _err(str(e))


def pl_verifica_plr(PL_raggiunto, PLr_richiesto):
    try:
        return _sanifica(performance_level.verifica_PLr(PL_raggiunto, PLr_richiesto))
    except ValueError as e:
        return _err(str(e))


# ------------------------------------------------------------------ Automazione PLC

def automz_scalatura(val_grezzo, in_min, in_max, out_min, out_max, abilita_clamp):
    valore, stato = automazione.esegui_scalatura(
        float(val_grezzo), float(in_min), float(in_max), float(out_min), float(out_max), bool(abilita_clamp))
    return _sanifica({"valore_scalato": valore, "stato": stato})


def automz_scalatura_inversa(val_engineering, in_min, in_max, out_min, out_max):
    valore, stato = automazione.esegui_scalatura_inversa(
        float(val_engineering), float(in_min), float(in_max), float(out_min), float(out_max))
    return _sanifica({"valore_raw": valore, "stato": stato})


def automz_esplosione_bits(valore_int):
    try:
        return _sanifica({"bits": automazione.calcola_esplosione_bits(int(valore_int))})
    except ValueError as e:
        return _err(str(e))


def automz_componi_word(bits):
    try:
        return _sanifica({"word": automazione.componi_word_da_bits([int(round(b)) for b in bits])})
    except ValueError as e:
        return _err(str(e))


def automz_limiti_memoria(prefisso, start_idx, quantita, tipo_var):
    try:
        return _sanifica({"range": automazione.calcola_limiti_memoria_rx3i(
            prefisso, int(start_idx), int(quantita), tipo_var)})
    except ValueError as e:
        return _err(str(e))


def automz_info_tipo_dato(tipo):
    dim, cat, vmin, vmax = automazione.info_tipo_dato(tipo)
    return _sanifica({"dimensione": dim, "categoria": cat, "min": vmin, "max": vmax})


# ------------------------------------------------------------------ Conversione unità (generico)

def conv_lista_categorie():
    return {"categorie": list(idraulica.ottieni_categorie().keys())}


def conv_lista_unita(categoria):
    cats = idraulica.ottieni_categorie()
    if categoria not in cats:
        return _err(f"Categoria non riconosciuta: '{categoria}'.")
    return {"unita": list(cats[categoria].keys())}


def conv_esegui_tutte(categoria, da_unita, valore):
    cats = idraulica.ottieni_categorie()
    if categoria not in cats:
        return _err(f"Categoria non riconosciuta: '{categoria}'.")
    if da_unita not in cats[categoria]:
        return _err(f"Unità sorgente non valida: '{da_unita}'.")
    try:
        valore = float(valore)
    except (TypeError, ValueError):
        return _err("Il valore deve essere numerico.")

    risultati = {}
    for u in cats[categoria].keys():
        try:
            risultati[u] = idraulica.esegui_conversione(categoria, da_unita, u, valore)
        except ValueError:
            risultati[u] = None
    return _sanifica({"risultati": risultati})
