import math
import unittest

import automazione
import formule
import idraulica
import fulmini
import batterie_piombo as bpb
import misuratori_portata as mport
import antincendio as ai
import atex
import vaso_espansione as vesp
import illuminazione_emergenza as ie
import gruppo_frigo as gf
import vibrazioni
import pneumatica
import trasmissioni
import pompe
import strumentazione
import resistenza_materiali as rm
import scambiatori
import perdite_carico
import motore_asincrono
import bulloneria
import illuminotecnica as il
import trasformatore as trafo
import circuito_rlc as rlc
import armonie_thd as thd
import batterie_ups as bat
import isolamento_termico as iso_t
import serbatoi
import valvole_controllo as valvole
import rumore_industriale as rumore
import dissipatore as diss
import nastri_trasportatori as nastri
import impianto_terra as terra
import selettivita_protezioni as selet
import fotovoltaico as fv
import gruppo_elettrogeno as ge
import cuscinetti as cus
import molle
import ruote_dentate as rd
import perdite_carico_distribuite as pcd
import trasduttori_pressione as tp
import quadro_elettrico as qe
import rifasamento_condensatori as rifas
import caduta_tensione_bt as cadbt
import tubazione_pressione as tubp
import avviamento_motore as avv
import alberi_torsione as alb
import saldature as sald
import condotte_hvac as hvac
import performance_level as pl_iso
import mark_vie as mv
import portata_cavo as pcav
import grado_protezione_ip as gip
import costi_energetici as ce
import libreria_cavi as libcavi
import canaline_passerelle as canp
import riferimento_rapido as rifr
import batch_cavi
import batterie_litio as blit
import componenti_passivi as cpas
import backup_compat


class TestAutomazione(unittest.TestCase):
    def test_lista_cpu_rx3i_contains_known_model(self):
        self.assertIn("IC695CPE305 (5 MB)", automazione.lista_cpu_rx3i())

    def test_scalatura_lineare(self):
        valore, stato = automazione.esegui_scalatura(16000, 0, 32000, 0, 100)
        self.assertEqual(stato, "OK")
        self.assertAlmostEqual(valore, 50.0, places=6)

    def test_scalatura_wire_break(self):
        valore, stato = automazione.esegui_scalatura(6000, 6400, 32000, 0, 100)
        self.assertEqual(stato, "ROTTURA_CAVO")
        self.assertEqual(valore, 0.0)

    def test_componi_word_da_bits(self):
        bits = [1] + [0] * 14 + [1]
        self.assertEqual(automazione.componi_word_da_bits(bits), 32769)


class TestFormule(unittest.TestCase):
    def test_converti_potenza_kw_to_hp(self):
        hp = formule.converti_potenza(1.0, "kW", "HP")
        self.assertAlmostEqual(hp, 1000.0 / 745.69987, places=6)

    def test_calcola_rifasamento(self):
        qc_kvar, stato = formule.calcola_rifasamento_kvar(50.0, 0.75, 0.95)
        self.assertEqual(stato, "OK")
        self.assertGreater(qc_kvar, 0.0)

    def test_corrente_cortocircuito_positive(self):
        icc_ka, z_tot, z_trafo, z_cavo = formule.calcola_corrente_cortocircuito(
            400.0, 400.0, 4.0, "Rame", 50.0, 50.0, "Trifase"
        )
        self.assertGreater(icc_ka, 0.0)
        self.assertGreater(z_tot, 0.0)
        self.assertGreater(z_trafo, 0.0)
        self.assertGreater(z_cavo, 0.0)

    def test_converti_potenza_negative_raises(self):
        with self.assertRaises(ValueError):
            formule.converti_potenza(-1.0, "kW", "HP")

    def test_caduta_invalid_sezione_raises(self):
        with self.assertRaises(ValueError):
            formule.calcola_caduta_avanzata(
                "Rame", "PVC (70Â°C)", "Metodo C", "Trifase",
                16.0, 50.0, 0.0, 0.85, 30.0, 20.0, 1
            )

    def test_sezione_protezione_invalid_densita_raises(self):
        with self.assertRaises(ValueError):
            formule.calcola_sezione_protezione(16.0, 0.0)

    def test_caduta_con_r_x_datasheet(self):
        dv, t_lav, rho_t, k1, k2, iz_real = formule.calcola_caduta_avanzata(
            "Rame", "PVC (70°C)", "Metodo C", "Trifase",
            16.0, 50.0, 4.0, 0.85, 30.0, 32.0, 1,
            r20_km_override=4.61, x_km_override=0.08,
        )
        self.assertGreater(dv, 0.0)

    def test_caduta_datasheet_diversa_da_teorica(self):
        comuni = ("Rame", "PVC (70°C)", "Metodo C", "Trifase", 16.0, 50.0, 4.0, 0.85, 30.0, 32.0, 1)
        dv_teorica = formule.calcola_caduta_avanzata(*comuni)[0]
        dv_datasheet = formule.calcola_caduta_avanzata(*comuni, r20_km_override=10.0, x_km_override=0.5)[0]
        self.assertNotAlmostEqual(dv_teorica, dv_datasheet)

    def test_caduta_r_datasheet_non_valida_raises(self):
        with self.assertRaises(ValueError):
            formule.calcola_caduta_avanzata(
                "Rame", "PVC (70°C)", "Metodo C", "Trifase",
                16.0, 50.0, 4.0, 0.85, 30.0, 32.0, 1,
                r20_km_override=0.0,
            )

    def test_caduta_x_datasheet_negativa_raises(self):
        with self.assertRaises(ValueError):
            formule.calcola_caduta_avanzata(
                "Rame", "PVC (70°C)", "Metodo C", "Trifase",
                16.0, 50.0, 4.0, 0.85, 30.0, 32.0, 1,
                x_km_override=-0.1,
            )

    def test_caduta_conduttori_in_parallelo_riduce_perdita(self):
        # Con corrente bassa (utilizzo trascurabile) la temperatura di lavoro
        # resta ~costante, quindi la caduta si riduce quasi esattamente a metà.
        comuni = ("Rame", "PVC (70°C)", "Metodo C", "Trifase", 1.0, 50.0, 4.0, 0.85, 30.0, 32.0, 1)
        dv_singolo = formule.calcola_caduta_avanzata(*comuni, n_parallelo=1)[0]
        dv_doppio = formule.calcola_caduta_avanzata(*comuni, n_parallelo=2)[0]
        self.assertAlmostEqual(dv_doppio, dv_singolo / 2.0, places=3)

    def test_caduta_parallelo_aumenta_portata_totale(self):
        comuni = ("Rame", "PVC (70°C)", "Metodo C", "Trifase", 32.0, 50.0, 4.0, 0.85, 30.0, 32.0, 1)
        iz_singolo = formule.calcola_caduta_avanzata(*comuni, n_parallelo=1)[5]
        iz_doppio = formule.calcola_caduta_avanzata(*comuni, n_parallelo=2)[5]
        self.assertAlmostEqual(iz_doppio, iz_singolo * 2.0)

    def test_caduta_n_parallelo_non_valido_raises(self):
        with self.assertRaises(ValueError):
            formule.calcola_caduta_avanzata(
                "Rame", "PVC (70°C)", "Metodo C", "Trifase",
                16.0, 50.0, 4.0, 0.85, 30.0, 32.0, 1,
                n_parallelo=0,
            )

    def test_caduta_considera_reattanza_false_riduce_caduta(self):
        comuni = ("Rame", "PVC (70°C)", "Metodo C", "Trifase", 16.0, 50.0, 4.0, 0.85, 30.0, 32.0, 1)
        dv_con_x = formule.calcola_caduta_avanzata(*comuni, considera_reattanza=True)[0]
        dv_senza_x = formule.calcola_caduta_avanzata(*comuni, considera_reattanza=False)[0]
        self.assertLess(dv_senza_x, dv_con_x)

    def test_caduta_considera_reattanza_false_equivale_x_zero(self):
        comuni = ("Rame", "PVC (70°C)", "Metodo C", "Trifase", 16.0, 50.0, 4.0, 0.85, 30.0, 32.0, 1)
        dv_senza_x = formule.calcola_caduta_avanzata(*comuni, considera_reattanza=False)[0]
        dv_x_zero = formule.calcola_caduta_avanzata(*comuni, x_km_override=0.0, considera_reattanza=True)[0]
        self.assertAlmostEqual(dv_senza_x, dv_x_zero)

    def test_potenza_e_corrente_dc(self):
        res = formule.calcola_potenza_e_corrente(
            "DC", 24.0, 10.0, 0.0, 1.0, "Estrai da Volt e Ampere"
        )
        self.assertIsNotNone(res)
        self.assertAlmostEqual(res["W"], 240.0, places=6)
        self.assertAlmostEqual(res["VA"], 240.0, places=6)

    def test_ingresso_motore_invalid_cos_phi_returns_none(self):
        res = formule.calcola_ingresso_motore(11.0, 92.0, "Trifase", 400.0, 1.2)
        self.assertIsNone(res)


class TestIdraulica(unittest.TestCase):
    def test_conversione_pressione_bar_psi(self):
        psi = idraulica.esegui_conversione("Pressione", "bar", "psi", 1.0)
        self.assertAlmostEqual(psi, 14.5038, places=3)

    def test_conversione_temperatura(self):
        fahrenheit = idraulica.esegui_conversione("Temperatura", "c", "f", 100.0)
        self.assertAlmostEqual(fahrenheit, 212.0, places=6)

    def test_conversione_barg_to_bara(self):
        bara = idraulica.esegui_conversione("Pressione", "barg", "bara", 0.0)
        self.assertAlmostEqual(bara, 1.01325, places=5)

    def test_temperatura_sotto_zero_assoluto_raises(self):
        with self.assertRaises(ValueError):
            idraulica.esegui_conversione("Temperatura", "c", "k", -300.0)

    def test_categoria_non_valida_raises(self):
        with self.assertRaises(ValueError):
            idraulica.esegui_conversione("Rumore", "db", "db", 10.0)

    def test_conversione_lunghezza(self):
        feet = idraulica.esegui_conversione("Lunghezza", "m", "ft", 1.0)
        self.assertAlmostEqual(feet, 3.28084, places=5)


class TestVibrazioni(unittest.TestCase):
    def test_conversione_velocita_rms(self):
        # 10 mm/s RMS a 50 Hz → spostamento pk-pk noto
        r = vibrazioni.converti_grandezze_vibrazionali("velocita_rms_mms", 10.0, 50.0)
        omega = 2 * math.pi * 50.0
        d_pk_atteso = (10.0 * math.sqrt(2)) / omega
        self.assertAlmostEqual(r["spostamento_pk_mm"], d_pk_atteso, places=8)
        self.assertAlmostEqual(r["velocita_rms_mms"], 10.0, places=6)

    def test_conversione_spostamento_pkpk(self):
        r = vibrazioni.converti_grandezze_vibrazionali("spostamento_pkpk_mm", 1.0, 100.0)
        self.assertAlmostEqual(r["spostamento_pkpk_mm"], 1.0, places=8)
        self.assertAlmostEqual(r["spostamento_pk_mm"], 0.5, places=8)

    def test_conversione_freq_zero_raises(self):
        with self.assertRaises(ValueError):
            vibrazioni.converti_grandezze_vibrazionali("velocita_rms_mms", 5.0, 0.0)

    def test_conversione_unita_imperiali_e_db(self):
        # Caso di riferimento incrociato con DLI Watchman VibCon (60 Hz, 1.36 mm/s RMS):
        # tutte le grandezze tranne adb_iso coincidono con l'output del programma a 3+
        # cifre significative (adb_iso: 114.2 calcolato vs 114.4 mostrato da VibCon — la
        # formula usa i riferimenti standard ISO 1683, lo scarto è verosimilmente un
        # arrotondamento interno di quel programma, non riproducibile senza il sorgente).
        r = vibrazioni.converti_grandezze_vibrazionali("velocita_rms_mms", 1.36, 60.0)
        self.assertAlmostEqual(r["velocita_rms_ins"], 0.0535, places=4)
        self.assertAlmostEqual(r["velocita_pk_ins"], 0.0757, places=4)
        self.assertAlmostEqual(r["accelerazione_rms_g"], 0.0523, places=4)
        self.assertAlmostEqual(r["accelerazione_rms_fts2"], 1.68, places=2)
        self.assertAlmostEqual(r["accelerazione_rms_ins2"], 20.2, places=1)
        self.assertAlmostEqual(r["spostamento_pkpk_mils"], 0.402, places=3)
        self.assertAlmostEqual(r["vdb_iso"], 122.7, places=1)
        self.assertAlmostEqual(r["frequenza_cpm"], 3600.0, places=6)

    def test_conversione_db_none_per_valore_zero(self):
        r = vibrazioni.converti_grandezze_vibrazionali("velocita_rms_mms", 0.0, 50.0)
        self.assertIsNone(r["vdb_iso"])
        self.assertIsNone(r["adb_iso"])

    def test_iso10816_zona_a(self):
        zona, colore, _, _ = vibrazioni.classifica_iso10816(0.5, "Classe I — Piccole macchine < 15 kW")
        self.assertEqual(zona, "A")
        self.assertEqual(colore, "Verde")

    def test_iso10816_zona_d(self):
        zona, _, _, _ = vibrazioni.classifica_iso10816(5.0, "Classe I — Piccole macchine < 15 kW")
        self.assertEqual(zona, "D")

    def test_frequenza_naturale_non_smorzata(self):
        r = vibrazioni.calcola_frequenza_naturale(10000.0, 10.0)
        fn_attesa = (1 / (2 * math.pi)) * math.sqrt(10000.0 / 10.0)
        self.assertAlmostEqual(r["fn_hz"], fn_attesa, places=8)
        self.assertAlmostEqual(r["fd_hz"], fn_attesa, places=8)

    def test_frequenza_naturale_smorzata(self):
        r = vibrazioni.calcola_frequenza_naturale(10000.0, 10.0, zeta=0.1)
        self.assertLess(r["fd_hz"], r["fn_hz"])
        self.assertAlmostEqual(r["Q"], 5.0, places=6)

    def test_frequenza_naturale_k_zero_raises(self):
        with self.assertRaises(ValueError):
            vibrazioni.calcola_frequenza_naturale(0.0, 10.0)

    def test_velocita_critica(self):
        r = vibrazioni.calcola_velocita_critica(1.0)
        nc_attesa = (30 / math.pi) * math.sqrt(9.80665 / 0.001)
        self.assertAlmostEqual(r["Nc_rpm"], nc_attesa, places=4)
        self.assertLess(r["zona_proibita_bassa"], r["Nc_rpm"])
        self.assertGreater(r["zona_proibita_alta"], r["Nc_rpm"])

    def test_velocita_critica_delta_zero_raises(self):
        with self.assertRaises(ValueError):
            vibrazioni.calcola_velocita_critica(0.0)

    def test_squilibrio_iso1940(self):
        r = vibrazioni.calcola_squilibrio_iso1940(10.0, 100.0, 1500.0, 2.5)
        omega = 2 * math.pi * 1500.0 / 60.0
        e_max = 2.5 / omega
        self.assertAlmostEqual(r["e_max_mm"], e_max, places=8)
        self.assertAlmostEqual(r["U_max_gmm"], 10.0 * 1000.0 * e_max, places=4)

    def test_squilibrio_massa_zero_raises(self):
        with self.assertRaises(ValueError):
            vibrazioni.calcola_squilibrio_iso1940(0.0, 100.0, 1500.0, 2.5)


class TestPneumatica(unittest.TestCase):
    def test_converti_portata_round_trip(self):
        r = pneumatica.converti_portata(100.0, 6.0, 20.0)
        self.assertGreater(r["Qn_nl_min"], r["Qr_l_min"])  # a 6 bar il volume reale è minore

    def test_converti_portata_a_zero_bar(self):
        r = pneumatica.converti_portata(100.0, 0.0, 20.0)
        self.assertAlmostEqual(r["Qn_nl_min"], r["Qr_l_min"], places=4)

    def test_caduta_pressione_positiva(self):
        r = pneumatica.caduta_pressione_tubazione(200.0, 20.0, 25.0, 6.0)
        self.assertGreater(r["dP_mbar"], 0.0)
        self.assertGreater(r["velocita_ms"], 0.0)

    def test_serbatoio(self):
        r = pneumatica.dimensiona_serbatoio(300.0, 30.0, 8.0, 6.0)
        self.assertGreater(r["V_litri"], 0.0)

    def test_potenza_compressore(self):
        r = pneumatica.potenza_compressore(500.0, 0.0, 8.0, 0.75)
        self.assertGreater(r["P_kW"], 0.0)
        self.assertGreater(r["T_out_C"], 20.0)

    def test_portata_negativa_raises(self):
        with self.assertRaises(ValueError):
            pneumatica.converti_portata(-1.0, 6.0)


class TestTrasmissioni(unittest.TestCase):
    def test_trasmissione_semplice(self):
        r = trasmissioni.calcola_trasmissione(1450.0, 10.0, 3.0, 0.97)
        self.assertAlmostEqual(r["n2_rpm"], 1450.0 / 3.0, places=6)
        self.assertAlmostEqual(r["T2_nm"], 10.0 * 3.0 * 0.97, places=6)
        self.assertLess(r["P_out_kW"], r["P_in_kW"])

    def test_riduttore_2_stadi(self):
        r = trasmissioni.calcola_riduttore_multistadio(1450.0, 10.0, [{"i": 3.0}, {"i": 4.0}])
        self.assertAlmostEqual(r["i_tot"], 12.0, places=6)
        self.assertAlmostEqual(r["n_out_rpm"], 1450.0 / 12.0, places=4)

    def test_geometria_cinghia(self):
        r = trasmissioni.calcola_geometria_cinghia(100.0, 200.0, 400.0)
        self.assertAlmostEqual(r["i"], 2.0, places=6)
        self.assertGreater(r["L_cinghia_mm"], 0.0)

    def test_ptc_T_n(self):
        r = trasmissioni.converti_ptc("T_n", 10.0, 1450.0)
        omega = 2 * math.pi * 1450.0 / 60.0
        self.assertAlmostEqual(r["P_kW"], 10.0 * omega / 1000.0, places=6)


class TestPompe(unittest.TestCase):
    def test_punto_lavoro(self):
        r = pompe.calcola_punto_lavoro(30.0, 20.0, 22.0, 10.0, 20.0, 25.0)
        # Verifica che H_pompa(Q*) ≈ H_impianto(Q*)
        H_p = 30.0 - r["k_pompa"] * r["Q_star_m3h"]**2
        H_i = 10.0 + r["k_impianto"] * r["Q_star_m3h"]**2
        self.assertAlmostEqual(H_p, H_i, places=4)

    def test_potenza_pompa(self):
        r = pompe.calcola_potenza_pompa(20.0, 25.0, 0.75)
        self.assertGreater(r["P_ass_kW"], r["P_id_kW"])

    def test_npsh_positivo(self):
        r = pompe.calcola_npsh_disponibile(1.013, 0.023, 3.0, 1.5, 0.5)
        self.assertGreater(r["NPSH_d_m"], 0.0)

    def test_ns_classificazione(self):
        r = pompe.calcola_ns(1450.0, 0.005, 25.0)
        self.assertGreater(r["ns"], 0.0)
        self.assertIn("centrifug", r["tipo"].lower())


class TestStrumentazione(unittest.TestCase):
    def test_ma_tensione_250ohm(self):
        r = strumentazione.converti_ma_tensione(20.0, 250.0)
        self.assertAlmostEqual(r["tensione_V"], 5.0, places=6)

    def test_ma_tensione_4ma(self):
        r = strumentazione.converti_ma_tensione(4.0, 250.0)
        self.assertAlmostEqual(r["tensione_V"], 1.0, places=6)
        self.assertAlmostEqual(r["pct_4_20"], 0.0, places=6)

    def test_termocoppia_K_0mV(self):
        r = strumentazione.termocoppia_mv_a_gradi(0.0, "K")
        self.assertAlmostEqual(r["temperatura_C"], 0.0, places=1)

    def test_termocoppia_fuori_range_raises(self):
        with self.assertRaises(ValueError):
            strumentazione.termocoppia_mv_a_gradi(100.0, "K")

    def test_pt100_round_trip(self):
        T_in = 100.0
        R = strumentazione.pt100_t_a_r(T_in)
        r = strumentazione.pt100_r_a_t(R)
        self.assertAlmostEqual(r["temperatura_C"], T_in, places=3)

    def test_pt100_0gradi(self):
        R = strumentazione.pt100_t_a_r(0.0)
        self.assertAlmostEqual(R, 100.0, places=4)

    def test_errore_misura(self):
        r = strumentazione.calcola_errore_misura(75.0, 100.0, 0.5)
        self.assertAlmostEqual(r["errore_assoluto"], 0.5, places=6)
        self.assertAlmostEqual(r["errore_relativo_pct"], 0.5 / 75.0 * 100.0, places=4)

    # --- RTD generalizzato Pt1000 + CJC termocoppia (consolidamento) ---
    def test_pt1000_round_trip(self):
        R = strumentazione.pt100_t_a_r(100.0, R0=1000.0)
        self.assertAlmostEqual(R, 1385.05, places=2)
        self.assertAlmostEqual(strumentazione.pt100_r_a_t(R, R0=1000.0)["temperatura_C"], 100.0, places=3)

    def test_tc_diretta_punti_noti(self):
        self.assertAlmostEqual(strumentazione._tc_emf_diretta(1000.0, "K"), 41.276, places=3)
        self.assertAlmostEqual(strumentazione._tc_emf_diretta(0.0, "K"), 0.0, places=3)
        self.assertAlmostEqual(strumentazione._tc_emf_diretta(300.0, "J"), 16.327, places=3)

    def test_tc_diretta_T_E_punti_noti(self):
        # valori di riferimento NIST ITS-90
        self.assertAlmostEqual(strumentazione._tc_emf_diretta(100.0, "T"), 4.279, places=3)
        self.assertAlmostEqual(strumentazione._tc_emf_diretta(400.0, "T"), 20.872, places=3)
        self.assertAlmostEqual(strumentazione._tc_emf_diretta(-200.0, "T"), -5.603, places=3)
        self.assertAlmostEqual(strumentazione._tc_emf_diretta(200.0, "E"), 13.421, places=3)
        self.assertAlmostEqual(strumentazione._tc_emf_diretta(1000.0, "E"), 76.373, places=3)
        self.assertAlmostEqual(strumentazione._tc_emf_diretta(-200.0, "E"), -8.825, places=3)

    def test_tc_cjc_inversa(self):
        # f.e.m. a giunto caldo 500 °C con giunto freddo 25 °C, poi ricostruzione
        for tipo in ("K", "J", "T", "E"):
            t_caldo = 300.0   # entro il campo di tutti i tipi (T arriva a 400 °C)
            v = strumentazione.termocoppia_gradi_a_mv(t_caldo, tipo, t_giunto_rif_C=25.0)["mv"]
            r = strumentazione.termocoppia_mv_a_gradi(v, tipo, t_giunto_rif_C=25.0)
            self.assertAlmostEqual(r["temperatura_C"], t_caldo, places=1, msg=tipo)

    def test_tc_cjc_tipo_sconosciuto(self):
        with self.assertRaises(ValueError):
            strumentazione.termocoppia_mv_a_gradi(10.0, "S", t_giunto_rif_C=25.0)

    # --- Taratura ---
    def test_taratura_lineare(self):
        # strumento che legge letto = 1.01*rif + 0.5
        punti = [(0.0, 0.5), (50.0, 51.0), (100.0, 101.5)]
        r = strumentazione.taratura(punti, grado=1)
        self.assertAlmostEqual(r["R2"], 1.0, places=6)
        # correzione riporta la lettura al valore vero
        self.assertAlmostEqual(strumentazione.applica_taratura(r["coeff"], 101.5), 100.0, places=3)

    def test_taratura_punti_insufficienti(self):
        with self.assertRaises(ValueError):
            strumentazione.taratura([(0.0, 0.0)], grado=2)

    def test_taratura_polinomiale(self):
        punti = [(0, 0.0), (25, 24.0), (50, 47.5), (75, 71.0), (100, 95.0)]
        r = strumentazione.taratura(punti, grado=2)
        self.assertEqual(len(r["coeff"]), 3)
        self.assertGreater(r["R2"], 0.99)

    def test_interpola_taratura(self):
        tab = [(0.0, 0.1), (50.0, 50.2), (100.0, 100.4)]
        self.assertAlmostEqual(strumentazione.interpola_taratura(tab, 25.0)["valore"], 25.15, places=3)
        r = strumentazione.interpola_taratura(tab, 120.0, estrapola=True)
        self.assertTrue(r["fuori_campo"])
        with self.assertRaises(ValueError):
            strumentazione.interpola_taratura(tab, 120.0, estrapola=False)

    def test_caratterizza_rtd(self):
        r = strumentazione.caratterizza_rtd([(0.0, 100.0), (100.0, 138.51)])
        self.assertAlmostEqual(r["R0_effettivo"], 100.0, places=2)
        self.assertAlmostEqual(r["alpha_effettivo"], 0.0038510, places=5)

    def test_caratterizza_offset_tc(self):
        # f.e.m. teoriche esatte -> offset nullo
        v100 = strumentazione._tc_emf_diretta(100.0, "K")
        v500 = strumentazione._tc_emf_diretta(500.0, "K")
        r = strumentazione.caratterizza_offset_tc([(100.0, v100), (500.0, v500)], "K")
        self.assertAlmostEqual(r["offset_medio_mV"], 0.0, places=6)

    def test_guida_misura_struttura(self):
        self.assertIn("RTD Pt100/Pt1000 (IEC 60751)", strumentazione.GUIDA_MISURA)
        self.assertTrue(all(isinstance(v, list) and v for v in strumentazione.GUIDA_MISURA.values()))


class TestResistenzaMateriali(unittest.TestCase):
    def test_sezione_rettangolare(self):
        r = rm.sezione_rettangolare(50.0, 100.0)
        self.assertAlmostEqual(r["A_mm2"], 5000.0, places=4)
        self.assertAlmostEqual(r["I_mm4"], 50.0 * 100.0**3 / 12.0, places=4)

    def test_sezione_cerchio(self):
        r = rm.sezione_cerchio_pieno(50.0)
        self.assertAlmostEqual(r["A_mm2"], math.pi * 50.0**2 / 4.0, places=4)

    def test_trave_appoggiata_cc(self):
        r = rm.calcola_trave("Appoggiata — carico centrale concentrato",
                              2000.0, F_N=5000.0, I_mm4=4166667.0, W_mm3=83333.0)
        self.assertAlmostEqual(r["M_max_Nmm"], 5000.0 * 2000.0 / 4.0, places=0)

    def test_trave_sbalzo_qu(self):
        r = rm.calcola_trave("A sbalzo — carico distribuito uniforme",
                              1000.0, q_N_mm=2.0, I_mm4=1e6, W_mm3=2e4)
        self.assertAlmostEqual(r["M_max_Nmm"], 2.0 * 1000.0**2 / 2.0, places=0)

    def test_trazione(self):
        r = rm.calcola_trazione_compressione(10000.0, 100.0, 210000.0, 500.0, 160.0)
        self.assertAlmostEqual(r["sigma_mpa"], 100.0, places=4)
        self.assertTrue(r["verificata"])

    def test_trazione_supera_ammissibile(self):
        r = rm.calcola_trazione_compressione(20000.0, 100.0, 210000.0, 500.0, 160.0)
        self.assertFalse(r["verificata"])


class TestScambiatori(unittest.TestCase):
    def test_bilancio_termico_q(self):
        r = scambiatori.bilancio_termico(1.0, 4180.0, 90.0, 60.0)
        self.assertAlmostEqual(r["Q_kW"], 1.0 * 4180.0 * 30.0 / 1000.0, places=3)

    def test_bilancio_termico_cold_out(self):
        r = scambiatori.bilancio_termico(1.0, 4180.0, 90.0, 60.0, m_c=1.2, cp_c=4180.0)
        dT_c = r["delta_T_c"]
        self.assertAlmostEqual(dT_c, (1.0 * 4180.0 * 30.0) / (1.2 * 4180.0), places=4)

    def test_lmtd_controcorrente(self):
        r = scambiatori.lmtd(90.0, 60.0, 20.0, 50.0)
        dT1 = 90.0 - 50.0   # 40
        dT2 = 60.0 - 20.0   # 40
        self.assertAlmostEqual(r["LMTD_K"], 40.0, places=3)  # equal deltas → LMTD = dT

    def test_lmtd_unequal(self):
        r = scambiatori.lmtd(90.0, 60.0, 20.0, 45.0)
        dT1, dT2 = 90 - 45, 60 - 20
        expected = (dT1 - dT2) / math.log(dT1 / dT2)
        self.assertAlmostEqual(r["LMTD_K"], expected, places=4)

    def test_area_da_lmtd(self):
        r = scambiatori.area_da_lmtd(100000.0, 500.0, 40.0)
        self.assertAlmostEqual(r["A_m2"], 100000.0 / (500.0 * 40.0), places=6)

    def test_ntu_effectiveness_basic(self):
        r = scambiatori.ntu_effectiveness(4180.0, 5016.0, 90.0, 20.0, 500.0, 2.0)
        self.assertTrue(0 < r["epsilon"] < 1)
        self.assertAlmostEqual(r["Q_kW"], r["epsilon"] * r["C_min"] * (90.0 - 20.0) / 1000.0, places=4)

    def test_bilancio_error_on_wrong_temps(self):
        with self.assertRaises(ValueError):
            scambiatori.bilancio_termico(1.0, 4180.0, 60.0, 90.0)   # T_out > T_in


class TestPerditeCaricho(unittest.TestCase):
    def test_perdita_raccordo_basic(self):
        r = perdite_carico.perdita_raccordo(1.0, 2.0, 1000.0)
        expected_dP = 0.5 * 1000.0 * 4.0
        self.assertAlmostEqual(r["dP_Pa"], expected_dP, places=4)

    def test_perdita_raccordo_zero_velocity(self):
        r = perdite_carico.perdita_raccordo(5.0, 0.0, 1000.0)
        self.assertEqual(r["dP_Pa"], 0.0)

    def test_perdita_totale_sum(self):
        raccordi = [{"nome": "Curva 90° — raggio largo (R/D ≥ 1.5)", "n": 2},
                    {"nome": "Valvola a sfera — completamente aperta", "n": 1}]
        r = perdite_carico.perdita_totale(raccordi, 1.5, 1000.0)
        K_expected = 2 * 0.30 + 0.05
        self.assertAlmostEqual(r["K_tot"], K_expected, places=6)

    def test_allargamento_brusco(self):
        r = perdite_carico.perdita_allargamento_brusco(2.0, 50.0, 100.0)
        A1 = math.pi * 50.0**2 / 4.0
        A2 = math.pi * 100.0**2 / 4.0
        v2 = 2.0 * A1 / A2
        expected = 0.5 * 1000.0 * (2.0 - v2)**2
        self.assertAlmostEqual(r["dP_Pa"], expected, places=4)

    def test_restringimento_brusco(self):
        r = perdite_carico.perdita_restringimento_brusco(3.0, 100.0, 50.0)
        self.assertGreater(r["dP_Pa"], 0)

    def test_lunghezza_equivalente(self):
        Leq = perdite_carico.lunghezza_equivalente(1.0, 50.0, 0.02)
        self.assertAlmostEqual(Leq, 1.0 * 0.05 / 0.02, places=6)


class TestMotoreAsincrono(unittest.TestCase):
    def test_velocita_sincrona_4poli(self):
        self.assertAlmostEqual(motore_asincrono.velocita_sincrona(4), 1500.0, places=4)

    def test_velocita_sincrona_2poli(self):
        self.assertAlmostEqual(motore_asincrono.velocita_sincrona(2), 3000.0, places=4)

    def test_da_targa_coppia(self):
        r = motore_asincrono.da_targa(11.0, 1455.0, 400.0, 0.85, 91.0)
        omega = 2.0 * math.pi * 1455.0 / 60.0
        self.assertAlmostEqual(r["T_n_nm"], 11000.0 / omega, places=3)

    def test_da_targa_scorrimento(self):
        r = motore_asincrono.da_targa(11.0, 1455.0, 400.0, 0.85, 91.0)
        self.assertAlmostEqual(r["s_n_pct"], (1500 - 1455) / 1500 * 100, places=4)

    def test_confronto_classi_ie_ordering(self):
        r = motore_asincrono.confronto_classi_ie(11.0)
        self.assertGreater(r["IE3"]["eta_pct"], r["IE2"]["eta_pct"])
        self.assertGreater(r["IE4"]["eta_pct"], r["IE3"]["eta_pct"])

    def test_confronto_classi_ie_risparmio(self):
        r = motore_asincrono.confronto_classi_ie(11.0, 8000.0, 0.15)
        self.assertGreater(r["IE3"]["risparmio_vs_IE1"], 0)

    def test_da_targa_invalid_power(self):
        with self.assertRaises(ValueError):
            motore_asincrono.da_targa(-1.0, 1450.0, 400.0, 0.85, 91.0)


class TestBulloneria(unittest.TestCase):
    def test_calcola_serraggio_m12_88(self):
        r = bulloneria.calcola_serraggio("M12", "8.8", "Lubrificato (olio/grasso comune)")
        # F_p = 0.70 * 640 * 84.3 = 37.785 kN
        self.assertAlmostEqual(r["F_p_kN"], 0.70 * 640 * 84.3 / 1000.0, places=2)

    def test_coppia_serraggio_m12(self):
        r = bulloneria.calcola_serraggio("M12", "8.8", "Lubrificato (olio/grasso comune)")
        # M_a = k * d * F_p = 0.15 * 0.012 * 37785
        self.assertAlmostEqual(r["M_a_Nm"], 0.15 * 0.012 * r["F_p_N"], places=2)

    def test_verifica_bullone_ok(self):
        r = bulloneria.verifica_bullone("M12", "8.8", 5000.0, 0.0, 1.5)
        self.assertTrue(r["verificata"])
        self.assertAlmostEqual(r["sigma_t_mpa"], 5000.0 / 84.3, places=3)

    def test_verifica_bullone_fail(self):
        r = bulloneria.verifica_bullone("M6", "4.6", 50000.0, 0.0, 1.0)
        self.assertFalse(r["verificata"])

    def test_dimensiona_flangia(self):
        r = bulloneria.dimensiona_flangia(100000.0, "M12", "8.8", "Lubrificato (olio/grasso comune)")
        self.assertGreater(r["n_bulloni"], 0)
        self.assertGreaterEqual(r["n_bulloni"] * r["F_p_bullone"], 100000.0)

    def test_lista_classi(self):
        self.assertIn("8.8", bulloneria.lista_classi())
        self.assertIn("12.9", bulloneria.lista_classi())


class TestIlluminotecnica(unittest.TestCase):
    def test_numero_lampade_basic(self):
        r = il.calcola_numero_lampade(500.0, 100.0, 4000.0, 0.80, 0.55)
        N_teorico = (500.0 * 100.0) / (4000.0 * 0.80 * 0.55)
        self.assertEqual(r["N_corpi"], math.ceil(N_teorico))

    def test_em_effettivo_geq_required(self):
        r = il.calcola_numero_lampade(500.0, 100.0, 4000.0, 0.80, 0.55)
        self.assertGreaterEqual(r["Em_effettivo"], 500.0 - 1e-9)

    def test_room_index(self):
        r = il.calcola_room_index(10.0, 8.0, 3.5, 0.85)
        Hm = 3.5 - 0.85
        k_expected = (10.0 * 8.0) / (Hm * (10.0 + 8.0))
        self.assertAlmostEqual(r["k"], k_expected, places=6)

    def test_potenza_illuminazione(self):
        r = il.calcola_potenza_illuminazione(20, 36.0, 100.0)
        self.assertAlmostEqual(r["LENI_W_m2"], 20 * 36.0 / 100.0, places=6)

    def test_calcola_mf(self):
        r = il.calcola_mf(0.85, 0.97, 0.88, 0.92)
        self.assertAlmostEqual(r["MF"], 0.85 * 0.97 * 0.88 * 0.92, places=6)

    def test_mf_classificazione_buono(self):
        r = il.calcola_mf(0.95, 0.99, 0.95, 0.98)
        self.assertEqual(r["classificazione"], "Buono")

    def test_requisiti_ambiente(self):
        r = il.requisiti_ambiente("Ufficio generale")
        self.assertEqual(r["Em_lux"], 500)


class TestTrasformatore(unittest.TestCase):
    def test_rapporto(self):
        r = trafo.calcola_trasformatore(630, 10000, 400, 1350, 7600)
        self.assertAlmostEqual(r["rapporto_a"], 10000/400, places=3)

    def test_eta_nom(self):
        r = trafo.calcola_trasformatore(630, 10000, 400, 1350, 7600)
        self.assertGreater(r["eta_nom_pct"], 95.0)
        self.assertLessEqual(r["eta_nom_pct"], 100.0)

    def test_beta_opt(self):
        r = trafo.calcola_trasformatore(630, 10000, 400, 1350, 7600)
        self.assertAlmostEqual(r["beta_opt"], math.sqrt(1350/7600), places=4)

    def test_icc(self):
        r = trafo.calcola_trasformatore(100, 400, 230, 300, 1500, V_cc_pct=4.0, trifase=False)
        self.assertGreater(r["I_cc_A"], 0)

    def test_rendimento_vs_carico_length(self):
        rv = trafo.rendimento_vs_carico(630, 1350, 7600, 0.85, 20)
        self.assertEqual(len(rv["beta"]), 20)

    def test_dV_pct_positive(self):
        r = trafo.calcola_trasformatore(630, 10000, 400, 1350, 7600)
        self.assertGreater(r["dV_pct"], 0)

    def test_errore_tensioni_uguali(self):
        with self.assertRaises(ValueError):
            trafo.calcola_trasformatore(100, 0, 400, 300, 1500)


class TestCircuitoRLC(unittest.TestCase):
    def test_serie_risonanza(self):
        r = rlc.risonanza_serie(0.1, 100e-6)
        self.assertAlmostEqual(r["f0_Hz"], 1/(2*math.pi*math.sqrt(0.1*100e-6)), places=1)

    def test_serie_induttivo(self):
        # f=100 Hz, sopra risonanza (f0≈50 Hz con L=0.1, C=100e-6)
        r = rlc.impedenza_serie(100, 0.1, 100e-6, 100)
        self.assertEqual(r["tipo"], "Induttivo")

    def test_serie_capacitivo(self):
        # f=10 Hz, sotto risonanza -> Capacitivo
        r = rlc.impedenza_serie(100, 0.1, 100e-6, 10)
        self.assertEqual(r["tipo"], "Capacitivo")

    def test_parallelo_keys(self):
        r = rlc.impedenza_parallelo(1000, 0.1, 10e-6, 50)
        self.assertIn("Z_ohm", r)
        self.assertIn("phi_deg", r)

    def test_risposta_freq_length(self):
        r = rlc.risposta_frequenza(100, 0.1, 100e-6, 1, 10000, "serie", 50)
        self.assertEqual(len(r["f_Hz"]), 51)

    def test_risonanza_parallelo(self):
        r = rlc.risonanza_parallelo(0.1, 100e-6)
        self.assertAlmostEqual(r["f0_Hz"], 1/(2*math.pi*math.sqrt(0.1*100e-6)), places=1)


class TestArmonieTHD(unittest.TestCase):
    def test_thd_solo_fondamentale(self):
        r = thd.calcola_thd(230, {3: 0.001})
        self.assertAlmostEqual(r["THD_pct"], 0.001/230*100, delta=0.001)

    def test_thd_terza(self):
        r = thd.calcola_thd(100, {3: 10})
        self.assertAlmostEqual(r["THD_pct"], 10.0, places=3)

    def test_rms_totale(self):
        r = thd.calcola_thd(100, {3: 10, 5: 5})
        expected = math.sqrt(100**2 + 10**2 + 5**2)
        self.assertAlmostEqual(r["rms_totale"], expected, places=3)

    def test_giudizio_keys(self):
        r = thd.calcola_thd(230, {3: 5})
        self.assertIn("giudizio_ieee", r)

    def test_forma_onda_length(self):
        r = thd.forma_onda_armonica(230, {3: 10}, 50, 1, 100)
        self.assertGreaterEqual(len(r["t_ms"]), 100)

    def test_contributo_ordinato(self):
        r = thd.calcola_thd(100, {3: 30, 5: 20})
        self.assertIn(3, r["contributi"])
        self.assertIn(5, r["contributi"])


class TestBatterieUPS(unittest.TestCase):
    def test_autonomia(self):
        r = bat.calcola_autonomia(100, 48, 2000, 0.92, 0.80)
        self.assertGreater(r["t_autonomia_h"], 0)

    def test_autonomia_formula(self):
        r = bat.calcola_autonomia(100, 48, 100*48*0.80*0.92, 0.92, 0.80)
        self.assertAlmostEqual(r["t_autonomia_h"], 1.0, places=2)

    def test_dimensionamento(self):
        r = bat.dimensiona_banco(3000, 1.0, 48, 0.92, 0.80)
        self.assertGreater(r["C_nominale_Ah"], 0)

    def test_corrente_carica(self):
        r = bat.corrente_carica(100)
        self.assertAlmostEqual(r["I_C1_A"], 100.0, places=3)
        self.assertAlmostEqual(r["I_C10_A"], 10.0, places=3)

    def test_correzione_temperatura(self):
        r = bat.correzione_temperatura(100, 0, "piombo")
        self.assertLess(r["C_corretta_Ah"], 100)

    def test_tipo_sconosciuto_fallback(self):
        # Tipo non valido usa fallback (nessun errore, usa coeff Pb-acido)
        r = bat.correzione_temperatura(100, 25, "uranio")
        self.assertIn("C_corretta_Ah", r)
        self.assertEqual(r["C_corretta_Ah"], 100.0)


class TestIsolamentoTermico(unittest.TestCase):
    def _strato(self):
        return [{"nome": "Polistirene", "spessore_m": 0.10, "lambda_W_mK": 0.036}]

    def test_perdita_parete(self):
        r = iso_t.perdita_parete_piana(20, -5, self._strato(), 0.13, 0.04)
        self.assertGreater(r["U_W_m2K"], 0)
        self.assertLess(r["U_W_m2K"], 2.0)

    def test_U_doppio_strato(self):
        strati = [
            {"nome": "Mattone", "spessore_m": 0.20, "lambda_W_mK": 0.72},
            {"nome": "Polistirene", "spessore_m": 0.10, "lambda_W_mK": 0.036},
        ]
        r = iso_t.perdita_parete_piana(20, -5, strati, 0.13, 0.04)
        self.assertLess(r["U_W_m2K"], 0.4)

    def test_perdita_tubo(self):
        strati = [{"nome": "Lana di roccia", "spessore_m": 0.05, "lambda_W_mK": 0.040}]
        r = iso_t.perdita_tubo_cilindrico(80, 20, 100, strati, 10.0, 0.05, 0.04)
        self.assertGreater(r["Q_W"], 0)

    def test_temperatura_rugiada(self):
        T_rug = iso_t.temperatura_rugiada(20, 50)
        self.assertAlmostEqual(T_rug, 9.27, delta=0.5)

    def test_verifica_condensa(self):
        r = iso_t.verifica_condensa(5.0, 20.0, 80.0)
        self.assertTrue(r["rischio_condensa"])

    def test_no_condensa(self):
        r = iso_t.verifica_condensa(18.0, 20.0, 50.0)
        self.assertFalse(r["rischio_condensa"])


class TestSerbatoi(unittest.TestCase):
    def test_volume_cilindro(self):
        r = serbatoi.volume_geometrico("cilindro_vert", D_m=1.0, H_m=2.0)
        self.assertAlmostEqual(r, math.pi/4 * 1.0**2 * 2.0, places=5)

    def test_volume_sfera(self):
        r = serbatoi.volume_geometrico("sfera", D_m=1.0)
        self.assertAlmostEqual(r, math.pi/6, places=5)

    def test_pressione_fondo(self):
        r = serbatoi.pressione_fondo(10.0)
        self.assertAlmostEqual(r["P_mca"], 10.0, places=3)

    def test_portata_torricelli(self):
        r = serbatoi.portata_torricelli(1.0, 50.0)
        self.assertGreater(r["Q_m3h"], 0)

    def test_tempo_svuotamento(self):
        r = serbatoi.tempo_svuotamento(1.0, 2.0, 50.0, 0.62, math.pi/4*1**2)
        self.assertGreater(r["t_svuotamento_s"], 0)

    def test_tempo_riempimento(self):
        r = serbatoi.tempo_riempimento(10.0, 5.0)
        self.assertAlmostEqual(r["t_h"], 2.0, places=5)


class TestValvoleControllo(unittest.TestCase):
    def test_kv_liquido(self):
        r = valvole.cv_liquido(10.0, 1.0)
        self.assertAlmostEqual(r["Kv"], 10.0, places=3)

    def test_cv_vs_kv(self):
        r = valvole.cv_liquido(10.0, 1.0)
        self.assertAlmostEqual(r["Cv"], r["Kv"]/0.865, places=4)

    def test_kv_gas_non_choked(self):
        # P2=4 > P_cr=P1/2=3 -> non choked
        r = valvole.cv_gas(500, 6.0, 4.0, 293.15, 1.0)
        self.assertGreater(r["Kv"], 0)
        self.assertFalse(r["choked_flow"])

    def test_choked_flow(self):
        r = valvole.cv_gas(500, 6.0, 2.0, 293.15, 1.0)
        self.assertTrue(r["choked_flow"])

    def test_cavitazione_sigma(self):
        r = valvole.verifica_cavitazione(6.0, 1.0, 0.5)
        self.assertAlmostEqual(r["sigma"], (6.0 - 0.5)/(6.0 - 1.0), places=5)

    def test_cavitazione_bassa(self):
        r = valvole.verifica_cavitazione(10.0, 8.0, 0.023)
        self.assertEqual(r["rischio"], "BASSA")


class TestRumoreIndustriale(unittest.TestCase):
    def test_somma_due_uguali(self):
        r = rumore.somma_livelli_db([80.0, 80.0])
        self.assertAlmostEqual(r["L_tot_dB"], 83.01, delta=0.02)

    def test_somma_una_sorgente(self):
        r = rumore.somma_livelli_db([90.0])
        self.assertAlmostEqual(r["L_tot_dB"], 90.0, places=5)

    def test_lex_8h_calcolo(self):
        r = rumore.lex_8h([480], [87.0])
        self.assertAlmostEqual(r["LEX_8h_dBA"], 87.0, places=3)

    def test_lex_8h_dpi(self):
        r = rumore.lex_8h([480], [90.0])
        self.assertTrue(r["dpi_obbligo"])

    def test_attenuazione_dpi(self):
        r = rumore.attenuazione_dpi(30, 95.0)
        self.assertAlmostEqual(r["L_eff_dBA"], 70.0, places=3)

    def test_attenuazione_distanza_doppio(self):
        r = rumore.attenuazione_distanza(90.0, 1.0, 2.0)
        self.assertAlmostEqual(r["delta_dB"], 6.02, delta=0.02)


class TestDissipatore(unittest.TestCase):
    def test_tj_base(self):
        r = diss.temperatura_giunzione(50, 25, 1.5, 0.5, 2.0)
        self.assertAlmostEqual(r["Tj_C"], 25 + 50*(1.5+0.5+2.0), places=3)

    def test_tj_senza_dissipatore(self):
        r = diss.temperatura_giunzione(10, 25, 2.0, 0.3)
        self.assertAlmostEqual(r["Tj_C"], 25 + 10*(2.0+0.3), places=3)

    def test_rsa_necessario(self):
        r = diss.rsa_necessario(50, 150, 40, 1.5, 0.5)
        expected = (150-40)/50 - 1.5 - 0.5
        self.assertAlmostEqual(r["R_sa_max_CW"], expected, places=5)

    def test_potenza_max(self):
        r = diss.potenza_max_dissipabile(150, 40, 1.5, 0.5, 2.0)
        self.assertAlmostEqual(r["P_max_W"], (150-40)/(1.5+0.5+2.0), places=5)

    def test_curva_derating_length(self):
        r = diss.curva_derating(100, 150, 100, 20)
        self.assertEqual(len(r["T_amb_C"]), 21)

    def test_rsa_impossibile(self):
        with self.assertRaises(ValueError):
            diss.rsa_necessario(100, 50, 40, 2.0, 1.0)


class TestNastriTrasportatori(unittest.TestCase):
    def test_portata_massica_keys(self):
        r = nastri.portata_massica(0.8, 1.5, 800)
        self.assertIn("Q_m3h", r)
        self.assertIn("Q_th", r)

    def test_portata_positiva(self):
        r = nastri.portata_massica(0.8, 1.5, 800)
        self.assertGreater(r["Q_m3h"], 0)

    def test_portata_inclinata_minore(self):
        r0 = nastri.portata_massica(0.8, 1.5, 800, inclinazione_deg=0)
        r15 = nastri.portata_massica(0.8, 1.5, 800, inclinazione_deg=15)
        self.assertLess(r15["Q_th_eff"], r0["Q_th"])

    def test_potenza_motore_keys(self):
        r = nastri.potenza_motore(200, 50, 5, 0.85)
        self.assertIn("P_motore_kW", r)
        self.assertGreater(r["P_motore_kW"], 0)

    def test_tensione_nastro(self):
        r = nastri.tensione_nastro(15000, 1.5)
        self.assertAlmostEqual(r["F_periferica_N"], 10000.0, places=0)

    def test_angolo_secco(self):
        r = nastri.angolo_max_inclinazione(800, "secco")
        self.assertEqual(r["angolo_tipico_deg"], 18)

    def test_input_non_valido(self):
        with self.assertRaises(ValueError):
            nastri.portata_massica(0, 1.5, 800)


class TestImpiantoTerra(unittest.TestCase):
    def test_resistenza_picchetto(self):
        r = terra.resistenza_dispersore_picchetto(2.0, 100.0)
        self.assertGreater(r["R_ohm"], 0)

    def test_picchetti_paralleli(self):
        r1 = terra.resistenza_dispersore_picchetto(2.0, 100.0)
        r2 = terra.resistenza_picchetti_paralleli(r1["R_ohm"], 4)
        self.assertLess(r2["R_eq_ohm"], r1["R_ohm"])

    def test_sezione_minima_pe(self):
        r = terra.sezione_minima_pe(1000, 0.5)
        self.assertAlmostEqual(r["S_mm2_minima"], (1000**2*0.5)**0.5/143.0, places=5)

    def test_verifica_tensione_contatto_conforme(self):
        r = terra.verifica_tensione_contatto(20, 0.5)
        self.assertTrue(r["conforme"])

    def test_verifica_tensione_contatto_non_conforme(self):
        r = terra.verifica_tensione_contatto(100, 1.0)
        self.assertFalse(r["conforme"])

    def test_coordinamento_tt(self):
        r = terra.coordinamento_tt(20, 0.3)
        self.assertTrue(r["conforme"])


class TestSelettivitaProtezioni(unittest.TestCase):
    def test_selettivita_amperometrica_ok(self):
        r = selet.verifica_selettivita_amperometrica(100, 40)
        self.assertTrue(r["selettivo"])

    def test_selettivita_amperometrica_no(self):
        r = selet.verifica_selettivita_amperometrica(50, 40)
        self.assertFalse(r["selettivo"])

    def test_selettivita_differenziale_ok(self):
        r = selet.verifica_selettivita_differenziale(300, 30)
        self.assertTrue(r["selettivita_amperometrica"])

    def test_icc_minima(self):
        r = selet.corrente_corto_circuito_minima(230, 0.5)
        self.assertAlmostEqual(r["Icc_min_A"], 460.0, places=3)

    def test_tempo_intervento_curva_c(self):
        r = selet.tempo_intervento_curva(7, "C")
        self.assertEqual(r["zona_intervento"], "Zona di intervento magnetico (incertezza costruttiva)")

    def test_curva_non_valida(self):
        with self.assertRaises(ValueError):
            selet.tempo_intervento_curva(7, "X")


class TestFotovoltaico(unittest.TestCase):
    def test_producibilita(self):
        r = fv.producibilita_annua(6.0, 1400, 0.80)
        self.assertAlmostEqual(r["E_anno_kWh"], 6720.0, places=3)

    def test_numero_pannelli(self):
        r = fv.numero_pannelli(6.0, 450)
        self.assertEqual(r["n_pannelli"], 14)

    def test_dimensiona_stringa(self):
        r = fv.dimensiona_stringa(45.0, 20)
        self.assertIn("V_stringa_V", r)

    def test_scelta_inverter(self):
        r = fv.scelta_inverter(6.0, 1.2)
        self.assertAlmostEqual(r["P_inverter_kW"], 5.0, places=3)

    def test_payback(self):
        r = fv.tempo_ritorno_investimento(8000, 6720, 0.25, 70)
        self.assertGreater(r["payback_anni"], 0)

    def test_irraggiamento_invalido(self):
        with self.assertRaises(ValueError):
            fv.producibilita_annua(6.0, -100)


class TestGruppoElettrogeno(unittest.TestCase):
    def test_potenza_spunto(self):
        r = ge.potenza_spunto_motore(15, 0.85, 6.0, 0.90)
        self.assertGreater(r["S_spunto_kVA"], r["S_nom_kVA"])

    def test_dimensiona_gruppo(self):
        r = ge.dimensiona_gruppo([10, 20, 5])
        self.assertEqual(r["P_tot_kW"], 35)
        self.assertGreater(r["S_gruppo_kVA"], 0)

    def test_autonomia_serbatoio(self):
        r = ge.autonomia_serbatoio(500, 50)
        self.assertGreater(r["t_autonomia_h"], 0)

    def test_serbatoio_per_autonomia(self):
        r = ge.serbatoio_per_autonomia(50, 10)
        self.assertGreater(r["V_necessario_L"], 0)

    def test_lista_vuota(self):
        with self.assertRaises(ValueError):
            ge.dimensiona_gruppo([])


class TestCuscinetti(unittest.TestCase):
    def test_durata_l10_sfere(self):
        r = cus.durata_l10(25, 5, "sfere")
        self.assertAlmostEqual(r["L10_milioni_giri"], 125.0, places=3)

    def test_durata_l10_rulli(self):
        r = cus.durata_l10(25, 5, "rulli")
        self.assertAlmostEqual(r["L10_milioni_giri"], 5.0**(10.0/3.0), places=3)

    def test_durata_ore(self):
        r = cus.durata_ore(100, 1500)
        self.assertAlmostEqual(r["L10h"], 100e6/(60*1500), places=2)

    def test_carico_dinamico_equivalente(self):
        r = cus.carico_dinamico_equivalente([5, 10], [0.5, 0.5])
        self.assertGreater(r["P_eq_kN"], 5)
        self.assertLess(r["P_eq_kN"], 10)

    def test_tipo_non_valido(self):
        with self.assertRaises(ValueError):
            cus.durata_l10(25, 5, "quadrati")


class TestMolle(unittest.TestCase):
    def test_costante_elastica(self):
        r = molle.molla_compressione(2.0, 20.0, 10)
        self.assertGreater(r["k_N_mm"], 0)

    def test_indice_molla(self):
        r = molle.molla_compressione(2.0, 20.0, 10)
        self.assertAlmostEqual(r["indice_molla_C"], 10.0, places=3)

    def test_tensione_torsionale(self):
        r = molle.tensione_torsionale_molla(100, 2.0, 20.0)
        self.assertGreater(r["tau_MPa"], 0)

    def test_frequenza_naturale(self):
        r = molle.frequenza_naturale_molla(2.0, 1.0)
        self.assertGreater(r["f_Hz"], 0)

    def test_molla_torsione(self):
        r = molle.molla_torsione(2.0, 20.0, 10)
        self.assertGreater(r["k_theta_Nmm_rad"], 0)

    def test_indice_invalido(self):
        with self.assertRaises(ValueError):
            molle.tensione_torsionale_molla(100, 20.0, 20.0)


class TestRuoteDentate(unittest.TestCase):
    def test_geometria(self):
        r = rd.geometria_ruota(3, 20)
        self.assertEqual(r["d_primitivo_mm"], 60)

    def test_modulo_minimo(self):
        r = rd.modulo_minimo_lewis(50, 20, 10, 200)
        self.assertGreater(r["m_minimo_mm"], 0)

    def test_verifica_flessione(self):
        r = rd.verifica_flessione_lewis(50, 3, 20, 24)
        self.assertGreater(r["sigma_flessione_MPa"], 0)

    def test_rapporto_trasmissione(self):
        r = rd.rapporto_trasmissione_ruote(20, 60)
        self.assertAlmostEqual(r["tau"], 3.0, places=3)
        self.assertTrue(r["riduzione"])

    def test_denti_invalidi(self):
        with self.assertRaises(ValueError):
            rd.geometria_ruota(3, 0)


class TestPerditeCaricoDistribuite(unittest.TestCase):
    def test_reynolds(self):
        r = pcd.numero_reynolds(2.0, 100.0)
        self.assertAlmostEqual(r["Re"], 2.0*0.1/1e-6, places=2)

    def test_fattore_attrito_laminare(self):
        r = pcd.fattore_attrito_swamee_jain(1000, 0.001)
        self.assertAlmostEqual(r["f_darcy"], 64.0/1000, places=5)
        self.assertEqual(r["regime"], "Laminare")

    def test_fattore_attrito_turbolento(self):
        r = pcd.fattore_attrito_swamee_jain(100000, 0.001)
        self.assertEqual(r["regime"], "Turbolento")
        self.assertGreater(r["f_darcy"], 0)

    def test_perdita_distribuita(self):
        r = pcd.perdita_distribuita(50, 100, 100)
        self.assertGreater(r["dP_bar"], 0)

    def test_diametro_da_velocita(self):
        r = pcd.diametro_da_velocita_max(50, 2.0)
        self.assertGreater(r["D_minimo_mm"], 0)

    def test_input_invalido(self):
        with self.assertRaises(ValueError):
            pcd.perdita_distribuita(-1, 100, 100)


class TestTrasduttoriPressione(unittest.TestCase):
    def test_ma_a_pressione_centro_scala(self):
        r = tp.ma_a_pressione(12.0, 20.0)
        self.assertAlmostEqual(r["P_bar"], 10.0, places=3)

    def test_ma_a_pressione_minimo(self):
        r = tp.ma_a_pressione(4.0, 20.0)
        self.assertAlmostEqual(r["P_bar"], 0.0, places=5)

    def test_ma_a_pressione_massimo(self):
        r = tp.ma_a_pressione(20.0, 20.0)
        self.assertAlmostEqual(r["P_bar"], 20.0, places=3)

    def test_pressione_a_ma_inversa(self):
        r1 = tp.ma_a_pressione(15.0, 30.0)
        r2 = tp.pressione_a_ma(r1["P_bar"], 30.0)
        self.assertAlmostEqual(r2["I_mA"], 15.0, places=3)

    def test_corrente_fuori_range(self):
        with self.assertRaises(ValueError):
            tp.ma_a_pressione(3.0, 20.0)

    def test_caduta_tensione_loop(self):
        r = tp.caduta_tensione_loop_4_20(250, 100)
        self.assertTrue(r["sufficiente"])


class TestQuadroElettrico(unittest.TestCase):
    def test_potenza_dissipata(self):
        r = qe.potenza_dissipata_componenti({"plc": 8, "io": 3})
        self.assertEqual(r["P_tot_W"], 11)

    def test_superficie_quadro(self):
        r = qe.superficie_quadro(0.6, 0.8, 0.3)
        self.assertGreater(r["A_tot_m2"], 0)

    def test_superficie_a_parete_minore(self):
        r1 = qe.superficie_quadro(0.6, 0.8, 0.3, installato_a_parete=False)
        r2 = qe.superficie_quadro(0.6, 0.8, 0.3, installato_a_parete=True)
        self.assertLess(r2["A_tot_m2"], r1["A_tot_m2"])

    def test_aumento_temperatura(self):
        r = qe.aumento_temperatura_quadro(50, 2.0)
        self.assertGreater(r["delta_T_K"], 0)

    def test_verifica_temperatura_conforme(self):
        r = qe.verifica_temperatura_quadro(50, 2.0, 30)
        self.assertTrue(r["conforme"])

    def test_componenti_vuoti(self):
        with self.assertRaises(ValueError):
            qe.potenza_dissipata_componenti({})


class TestRifasamentoCondensatori(unittest.TestCase):
    def test_potenza_reattiva_attuale(self):
        r = rifas.potenza_reattiva_attuale(50, 0.72)
        self.assertAlmostEqual(r["Q_kvar"], 50 * math.tan(math.acos(0.72)), places=4)

    def test_potenza_reattiva_cos_phi_invalido(self):
        with self.assertRaises(ValueError):
            rifas.potenza_reattiva_attuale(50, 1.5)

    def test_kvar_necessari(self):
        r = rifas.kvar_necessari(50, 0.72, 0.95)
        self.assertGreater(r["Q_c_kvar"], 0)
        self.assertGreaterEqual(r["Q_c_kvar_arrotondato"], r["Q_c_kvar"])

    def test_kvar_necessari_target_minore_errore(self):
        with self.assertRaises(ValueError):
            rifas.kvar_necessari(50, 0.95, 0.72)

    def test_capacita_condensatori_triangolo(self):
        r = rifas.capacita_condensatori(30, 400, "triangolo")
        self.assertGreater(r["C_per_fase_uF"], 0)

    def test_capacita_condensatori_stella_maggiore_di_triangolo(self):
        r_tri = rifas.capacita_condensatori(30, 400, "triangolo")
        r_st = rifas.capacita_condensatori(30, 400, "stella")
        self.assertGreater(r_st["C_per_fase_uF"], r_tri["C_per_fase_uF"])

    def test_verifica_rifasamento(self):
        r = rifas.verifica_rifasamento(50, 0.72, 30)
        self.assertGreater(r["cos_phi_risultante"], 0.72)
        self.assertLess(r["I_dopo_A"], r["I_prima_A"])


class TestCadutaTensioneBT(unittest.TestCase):
    def test_caduta_tensione_trifase(self):
        r = cadbt.caduta_tensione_trifase(20, 50, 16, 0.9)
        self.assertGreater(r["dV_V"], 0)
        self.assertTrue(r["conforme_5pct"])

    def test_caduta_tensione_monofase(self):
        r = cadbt.caduta_tensione_monofase(16, 30, 4, 0.9)
        self.assertGreater(r["dV_pct"], 0)

    def test_caduta_tensione_valori_invalidi(self):
        with self.assertRaises(ValueError):
            cadbt.caduta_tensione_trifase(-5, 50, 16, 0.9)

    def test_sezione_da_caduta_max(self):
        r = cadbt.sezione_da_caduta_max(10, 400, 50, 3.0, 0.9, "trifase")
        self.assertIn(r["S_mm2_normalizzata"], cadbt.SEZIONI_NORMALIZZATE_MM2)
        self.assertGreaterEqual(r["S_mm2_normalizzata"], r["S_mm2_calcolata"])

    def test_sezione_da_caduta_max_monofase(self):
        r = cadbt.sezione_da_caduta_max(3, 230, 30, 3.0, 0.9, "monofase")
        self.assertGreater(r["S_mm2_normalizzata"], 0)

    def test_giudizio_alta_caduta(self):
        r = cadbt.caduta_tensione_trifase(100, 200, 4, 0.9)
        self.assertFalse(r["conforme_5pct"])


class TestTubazionePressione(unittest.TestCase):
    def test_spessore_minimo(self):
        r = tubp.spessore_minimo(10, 48.3, 150)
        self.assertGreater(r["t_min_mm"], r["t_calc_mm"])
        self.assertGreaterEqual(r["t_normalizzato_mm"], r["t_min_mm"])

    def test_spessore_minimo_valori_invalidi(self):
        with self.assertRaises(ValueError):
            tubp.spessore_minimo(-1, 48.3, 150)

    def test_pressione_ammissibile(self):
        r = tubp.pressione_ammissibile(4.0, 48.3, 150)
        self.assertGreater(r["P_amm_bar"], 0)

    def test_pressione_ammissibile_spessore_insufficiente(self):
        with self.assertRaises(ValueError):
            tubp.pressione_ammissibile(0.5, 48.3, 150, c_corrosione_mm=1.0)

    def test_verifica_tubazione_conforme(self):
        r = tubp.verifica_tubazione(10, 48.3, 5.0, 150)
        self.assertTrue(r["conforme"])

    def test_verifica_tubazione_non_conforme(self):
        r = tubp.verifica_tubazione(50, 48.3, 1.6, 150)
        self.assertFalse(r["conforme"])

    def test_round_trip_pressione_spessore(self):
        sp = tubp.spessore_minimo(10, 100, 150)
        pr = tubp.pressione_ammissibile(sp["t_normalizzato_mm"], 100, 150)
        self.assertGreaterEqual(pr["P_amm_bar"], 10)


class TestAvviamentoMotore(unittest.TestCase):
    def test_correnti_motore(self):
        r = avv.correnti_motore(11, 400, 0.85, 0.92, 6.0)
        self.assertAlmostEqual(r["I_avviamento_A"], r["I_nominale_A"] * 6.0, places=4)

    def test_correnti_motore_valori_invalidi(self):
        with self.assertRaises(ValueError):
            avv.correnti_motore(-1, 400, 0.85, 0.92)

    def test_coppia_motore(self):
        r = avv.coppia_motore(15, 1450, 1.5)
        self.assertAlmostEqual(r["M_avviamento_Nm"], r["M_nominale_Nm"] * 1.5, places=4)

    def test_caduta_tensione_avviamento_conforme(self):
        r = avv.caduta_tensione_avviamento(50, 5, 400)
        self.assertTrue(r["ammissibile"])

    def test_caduta_tensione_avviamento_non_conforme(self):
        r = avv.caduta_tensione_avviamento(500, 50, 400)
        self.assertFalse(r["ammissibile"])

    def test_metodi_avviamento(self):
        r = avv.metodi_avviamento(11, 400, 0.85, 0.92)
        self.assertIn("Diretto (DOL)", r["metodi"])
        self.assertIn("Stella-Triangolo (Y-Δ)", r["metodi"])
        self.assertLess(r["metodi"]["Stella-Triangolo (Y-Δ)"]["I_avviamento_A"], r["I_avviamento_diretto_A"])


class TestAlberiTorsione(unittest.TestCase):
    def test_momento_torcente(self):
        r = alb.momento_torcente(15, 1450)
        self.assertGreater(r["Mt_Nm"], 0)

    def test_momento_torcente_invalido(self):
        with self.assertRaises(ValueError):
            alb.momento_torcente(-15, 1450)

    def test_diametro_minimo_torsione(self):
        r = alb.diametro_minimo_torsione(100, 30)
        self.assertGreaterEqual(r["d_normalizzato_mm"], r["d_min_mm"])

    def test_tensioni_albero(self):
        r = alb.tensioni_albero(100, 80, 40)
        self.assertGreater(r["sigma_eq_MPa"], 0)
        self.assertGreater(r["sigma_eq_MPa"], r["tau_MPa"])

    def test_fattore_sicurezza_statico(self):
        r = alb.fattore_sicurezza_statico(100, 80, 40, 490)
        self.assertGreater(r["n_statico"], 0)

    def test_verifica_goodman(self):
        r = alb.verifica_goodman(120, 80, 700, 350)
        self.assertGreater(r["n_Goodman"], 0)
        self.assertGreater(r["n_Gerber"], r["n_Goodman"])

    def test_verifica_goodman_invalido(self):
        with self.assertRaises(ValueError):
            alb.verifica_goodman(120, 80, 0, 350)


class TestSaldature(unittest.TestCase):
    def test_resistenza_ammissibile_cordone(self):
        r = sald.resistenza_ammissibile_cordone("S235")
        self.assertGreater(r["f_vwd_MPa"], 0)

    def test_resistenza_ammissibile_acciaio_invalido(self):
        with self.assertRaises(ValueError):
            sald.resistenza_ammissibile_cordone("X999")

    def test_gola_minima(self):
        r = sald.gola_minima(10)
        self.assertGreaterEqual(r["a_min_mm"], 3.0)

    def test_verifica_cordone_taglio_conforme(self):
        r = sald.verifica_cordone_taglio(30, 5, 100, "S235")
        self.assertTrue(r["conforme"])

    def test_verifica_cordone_taglio_non_conforme(self):
        r = sald.verifica_cordone_taglio(500, 3, 50, "S235")
        self.assertFalse(r["conforme"])

    def test_verifica_cordone_normale(self):
        r = sald.verifica_cordone_normale(20, 5, 100, acciaio="S355")
        self.assertGreater(r["sigma_perp_MPa"], 0)

    def test_cordone_a_doppio_T(self):
        r = sald.cordone_a_doppio_T(40, 6, 80, acciaio="S275")
        self.assertIn("conforme", r)


class TestCondotteHVAC(unittest.TestCase):
    def test_proprieta_aria(self):
        r = hvac.proprieta_aria(20)
        self.assertGreater(r["rho_kg_m3"], 1.0)
        self.assertLess(r["rho_kg_m3"], 1.3)

    def test_diametro_idraulico_rettangolare(self):
        Dh = hvac.diametro_idraulico_rettangolare(400, 300)
        self.assertAlmostEqual(Dh, 2 * 400 * 300 / (400 + 300), places=4)

    def test_perdita_carico_condotta_circolare(self):
        r = hvac.perdita_carico_condotta(2000, 315, 20)
        self.assertEqual(r["regime"], "Turbolento")
        self.assertGreater(r["dP_Pa_tot"], 0)

    def test_perdita_carico_condotta_rettangolare(self):
        r = hvac.perdita_carico_condotta(2000, 0.0, 20, forma="rettangolare", a_mm=400, b_mm=300)
        self.assertGreater(r["dP_Pa_tot"], 0)

    def test_perdita_carico_valori_invalidi(self):
        with self.assertRaises(ValueError):
            hvac.perdita_carico_condotta(-100, 315, 20)

    def test_dimensiona_condotta_circolare(self):
        r = hvac.dimensiona_condotta_circolare(2000, 8.0)
        self.assertGreaterEqual(r["D_normalizzato_mm"], r["D_min_mm"])

    def test_dimensiona_condotta_rettangolare(self):
        r = hvac.dimensiona_condotta_rettangolare(2000, 1.5, 8.0)
        self.assertAlmostEqual(r["b_mm"] / r["a_mm"], r["rapporto_lati"], places=2)


class TestPerformanceLevel(unittest.TestCase):
    def test_calcola_PL_categoria_3(self):
        r = pl_iso.calcola_PL(30, 90, "3")
        self.assertEqual(r["PL"], "d")
        self.assertEqual(r["SIL"], "SIL 2")

    def test_calcola_PL_categoria_B(self):
        r = pl_iso.calcola_PL(5, 0, "B")
        self.assertEqual(r["PL"], "a")

    def test_calcola_PL_categoria_invalida(self):
        with self.assertRaises(ValueError):
            pl_iso.calcola_PL(30, 90, "9")

    def test_calcola_PL_MTTFd_invalido(self):
        with self.assertRaises(ValueError):
            pl_iso.calcola_PL(-1, 90, "3")

    def test_MTTFd_da_B10d(self):
        r = pl_iso.MTTFd_da_B10d(2_000_000, 500_000)
        self.assertAlmostEqual(r["MTTFd_anni"], 2_000_000 / (0.1 * 500_000), places=2)

    def test_MTTFd_da_B10d_limitato_100_anni(self):
        r = pl_iso.MTTFd_da_B10d(100_000_000, 100)
        self.assertEqual(r["MTTFd_anni"], 100.0)
        self.assertNotEqual(r["nota"], "")

    def test_verifica_PLr_conforme(self):
        r = pl_iso.verifica_PLr("d", "c")
        self.assertTrue(r["conforme"])

    def test_verifica_PLr_non_conforme(self):
        r = pl_iso.verifica_PLr("b", "d")
        self.assertFalse(r["conforme"])

    def test_verifica_PLr_invalido(self):
        with self.assertRaises(ValueError):
            pl_iso.verifica_PLr("z", "d")


class TestMarkVIe(unittest.TestCase):
    def test_risoluzione_adc(self):
        r = mv.risoluzione_adc(-10.0, 10.0, 16)
        self.assertAlmostEqual(r["lsb"], 20.0 / 65536, places=8)

    def test_risoluzione_adc_invalida(self):
        with self.assertRaises(ValueError):
            mv.risoluzione_adc(10.0, -10.0)

    def test_scala_paic_centro_scala(self):
        r = mv.scala_paic(50, "0-20 mA (canali 1-8)")
        self.assertAlmostEqual(r["valore"], 10.0, places=4)

    def test_scala_paic_span_invalido(self):
        with self.assertRaises(ValueError):
            mv.scala_paic(50, "span inesistente")

    def test_scala_paic_pct_fuori_range(self):
        with self.assertRaises(ValueError):
            mv.scala_paic(150, "0-20 mA (canali 1-8)")

    def test_scala_paic_bipolare(self):
        r = mv.scala_paic(0, "±10 V dc (canali 1-8)")
        self.assertAlmostEqual(r["valore"], -10.0, places=4)

    def test_voting_tmr_concordanza(self):
        r = mv.voting_tmr_mediano(100.0, 100.0, 100.0)
        self.assertEqual(r["valore_votato"], 100.0)
        self.assertFalse(r["disaccordo"])

    def test_voting_tmr_mediano_corretto(self):
        r = mv.voting_tmr_mediano(98.0, 105.0, 100.0)
        self.assertEqual(r["valore_votato"], 100.0)

    def test_voting_tmr_canale_sospetto(self):
        r = mv.voting_tmr_mediano(100.0, 100.2, 90.0, tolleranza=1.0)
        self.assertIn("v3", r["canali_sospetti"])
        self.assertTrue(r["disaccordo"])

    def test_mtbf_serie(self):
        r = mv.mtbf_serie([50, 37, 47])
        self.assertLess(r["MTBF_sistema_anni"], min(50, 37, 47))

    def test_mtbf_serie_invalido(self):
        with self.assertRaises(ValueError):
            mv.mtbf_serie([50, -1])

    def test_disponibilita_tmr_2oo3(self):
        r = mv.disponibilita_tmr_2oo3(50, 4.0)
        self.assertGreater(r["MTBF_sistema_TMR_anni"], r["MTBF_canale_anni"])
        self.assertGreater(r["fattore_miglioramento"], 1.0)

    def test_disponibilita_tmr_invalida(self):
        with self.assertRaises(ValueError):
            mv.disponibilita_tmr_2oo3(-5, 4.0)

    def test_corrente_assorbita_tbci(self):
        r = mv.corrente_assorbita_tbci("H1 (125 Vdc)", 21, 3)
        self.assertAlmostEqual(r["I_totale_mA"], 21 * 2.5 + 3 * 10.0, places=4)
        self.assertEqual(r["n_circuiti_totali"], 24)

    def test_corrente_assorbita_tbci_tipo_invalido(self):
        with self.assertRaises(ValueError):
            mv.corrente_assorbita_tbci("X999")

    def test_derating_relay_sotto_soglia(self):
        r = mv.corrente_derating_relay_trly("1E (115 Vac)", 20)
        self.assertEqual(r["I_ammissibile_A"], 10.0)

    def test_derating_relay_sopra_soglia(self):
        r = mv.corrente_derating_relay_trly("1E (115 Vac)", 70)
        self.assertEqual(r["I_ammissibile_A"], 6.0)

    def test_derating_relay_interpolato(self):
        r = mv.corrente_derating_relay_trly("1E (115 Vac)", 45)
        self.assertTrue(6.0 < r["I_ammissibile_A"] < 10.0)

    def test_derating_relay_tipo_invalido(self):
        with self.assertRaises(ValueError):
            mv.corrente_derating_relay_trly("X999", 45)

    def test_schede_io_non_vuoto(self):
        self.assertGreater(len(mv.SCHEDE_IO), 30)
        self.assertIn("PAIC", mv.SCHEDE_IO)
        self.assertIn("PVIB", mv.SCHEDE_IO)

    def test_architetture_ridondanza(self):
        self.assertIn("TMR", mv.ARCHITETTURE_RIDONDANZA)
        self.assertEqual(mv.ARCHITETTURE_RIDONDANZA["TMR"]["controllori"], 3)
        self.assertEqual(mv.ARCHITETTURE_RIDONDANZA["Simplex"]["controllori"], 1)

    def test_suite_controlst_doc_validi(self):
        # ogni componente deve puntare a un documento esistente nella raccolta
        self.assertGreater(len(mv.SUITE_CONTROLST_WORKSTATIONST), 20)
        for nome, info in mv.SUITE_CONTROLST_WORKSTATIONST.items():
            self.assertIn(info["doc"], mv.DOCUMENTI_CONTROLST, nome)

    def test_documento_componente(self):
        r = mv.documento_componente("Trender")
        self.assertEqual(r["documento"], "GEI-100795")
        self.assertEqual(r["documento_rev"], "GEI-100795T")
        self.assertEqual(r["pagine"], 48)
        # sezioni capitolo->pagina presenti e con pagine valide
        self.assertTrue(r["sezioni"])
        for titolo, pag in r["sezioni"]:
            self.assertIsInstance(titolo, str)
            self.assertTrue(1 <= pag <= r["pagine"])

    def test_sezioni_componenti_pagine_valide(self):
        # ogni sezione deve riferirsi a una pagina entro il numero di pagine del doc
        for nome in mv.SEZIONI_COMPONENTI:
            ref = mv.documento_componente(nome)
            for titolo, pag in ref["sezioni"]:
                self.assertTrue(1 <= pag <= ref["pagine"], (nome, titolo, pag, ref["pagine"]))

    def test_documento_componente_senza_revisione(self):
        # GEI-100829 ha rev '-' -> documento_rev senza suffisso
        r = mv.documento_componente("GSM 3.0 Server (GE Standard Messages)")
        self.assertNotIn("-", r["documento_rev"].replace("GEH-", "").replace("GEI-", ""))

    def test_documento_componente_invalido(self):
        with self.assertRaises(ValueError):
            mv.documento_componente("Componente inesistente")

    def test_componenti_per_categoria(self):
        cat = mv.componenti_per_categoria()
        self.assertIn("Comunicazione OPC", cat)
        # tutti i componenti devono comparire una sola volta nei gruppi
        totale = sum(len(v) for v in cat.values())
        self.assertEqual(totale, len(mv.SUITE_CONTROLST_WORKSTATIONST))

    # --- RTD IEC 60751 ---
    def test_rtd_resistenza_punti_noti(self):
        # valori di riferimento Pt100 (IEC 60751)
        self.assertAlmostEqual(mv.rtd_resistenza(0)["R_ohm"], 100.000, places=3)
        self.assertAlmostEqual(mv.rtd_resistenza(100)["R_ohm"], 138.505, places=3)
        self.assertAlmostEqual(mv.rtd_resistenza(-100)["R_ohm"], 60.256, places=3)
        self.assertAlmostEqual(mv.rtd_resistenza(850)["R_ohm"], 390.481, places=3)

    def test_rtd_andata_ritorno(self):
        for t in (-200, -50, 0, 250, 600, 850):
            R = mv.rtd_resistenza(t)["R_ohm"]
            self.assertAlmostEqual(mv.rtd_temperatura(R)["temp_C"], t, places=4)

    def test_rtd_pt1000(self):
        self.assertAlmostEqual(mv.rtd_resistenza(0, R0=1000.0)["R_ohm"], 1000.0, places=2)

    def test_rtd_fuori_campo(self):
        with self.assertRaises(ValueError):
            mv.rtd_resistenza(900)

    # --- Termocoppie ITS-90 ---
    def test_termocoppia_K_punti_noti(self):
        self.assertAlmostEqual(mv.termocoppia_mv("K", 0)["mV_assoluto_rif0"], 0.000, places=3)
        self.assertAlmostEqual(mv.termocoppia_mv("K", 100)["mV_assoluto_rif0"], 4.096, places=3)
        self.assertAlmostEqual(mv.termocoppia_mv("K", 1000)["mV_assoluto_rif0"], 41.276, places=3)
        self.assertAlmostEqual(mv.termocoppia_mv("K", -200)["mV_assoluto_rif0"], -5.891, places=3)

    def test_termocoppia_J_punti_noti(self):
        self.assertAlmostEqual(mv.termocoppia_mv("J", 100)["mV_assoluto_rif0"], 5.269, places=3)
        self.assertAlmostEqual(mv.termocoppia_mv("J", 300)["mV_assoluto_rif0"], 16.327, places=3)
        self.assertAlmostEqual(mv.termocoppia_mv("J", 700)["mV_assoluto_rif0"], 39.132, places=3)

    def test_termocoppia_andata_ritorno(self):
        for tipo in ("J", "K"):
            for t in (50, 250, 600):
                v = mv.termocoppia_mv(tipo, t)["mV_assoluto_rif0"]
                self.assertAlmostEqual(mv.termocoppia_temp(tipo, v)["temp_C"], t, places=2)

    def test_termocoppia_cjc(self):
        # con CJC: misura a giunto freddo 25 °C deve ricostruire il giunto caldo
        v = mv.termocoppia_mv("K", 500, temp_giunto_freddo_C=25.0)["mV"]
        self.assertAlmostEqual(mv.termocoppia_temp("K", v, temp_giunto_freddo_C=25.0)["temp_C"], 500.0, places=2)

    def test_termocoppia_tipo_invalido(self):
        with self.assertRaises(ValueError):
            mv.termocoppia_mv("Z", 100)

    # --- Diagnostica 4-20 mA (NE43) ---
    def test_ne43_stati(self):
        self.assertFalse(mv.diagnostica_loop_420(3.5)["valido"])
        self.assertFalse(mv.diagnostica_loop_420(21.5)["valido"])
        self.assertTrue(mv.diagnostica_loop_420(12.0)["valido"])
        self.assertFalse(mv.diagnostica_loop_420(0.05)["valido"])

    def test_ne43_scalatura(self):
        r = mv.diagnostica_loop_420(12.0, 0.0, 200.0)
        self.assertAlmostEqual(r["valore_processo"], 100.0, places=6)
        self.assertAlmostEqual(r["percentuale"], 50.0, places=6)

    # --- Velocità / sovravelocità turbina ---
    def test_velocita_frequenza_andata_ritorno(self):
        f = mv.frequenza_da_velocita(3000, 60)["freq_hz"]
        self.assertAlmostEqual(f, 3000.0, places=6)
        self.assertAlmostEqual(mv.velocita_da_frequenza(f, 60)["rpm"], 3000.0, places=6)

    def test_trip_sovravelocita(self):
        r = mv.trip_sovravelocita(3000, 60, 110)
        self.assertAlmostEqual(r["rpm_trip"], 3300.0, places=6)
        self.assertAlmostEqual(r["freq_trip_hz"], 3300.0, places=6)
        self.assertAlmostEqual(r["margine_rpm"], 300.0, places=6)

    def test_trip_soglia_invalida(self):
        with self.assertRaises(ValueError):
            mv.trip_sovravelocita(3000, 60, 95)

    # --- Troubleshooting ---
    def test_troubleshooting_doc_validi(self):
        self.assertGreaterEqual(len(mv.TROUBLESHOOTING), 10)
        for v in mv.TROUBLESHOOTING:
            self.assertIn(v["doc"], mv.DOCUMENTI_CONTROLST, v["sintomo"])
            self.assertTrue(1 <= v["pagina"] <= mv.DOCUMENTI_CONTROLST[v["doc"]]["pagine"])

    def test_troubleshooting_ricerca(self):
        self.assertEqual(len(mv.cerca_troubleshooting("")), len(mv.TROUBLESHOOTING))
        self.assertTrue(all("opc" in f"{v['sintomo']} {v['componente']} {v['dove']}".lower()
                            for v in mv.cerca_troubleshooting("OPC")))

    # --- Checklist commissioning ---
    def test_checklist_commissioning_struttura(self):
        self.assertGreaterEqual(len(mv.CHECKLIST_COMMISSIONING), 5)
        for blocco in mv.CHECKLIST_COMMISSIONING:
            self.assertIn("fase", blocco)
            self.assertIn("voci", blocco)
            self.assertTrue(blocco["voci"])

    def test_checklist_commissioning_flat_id_univoci(self):
        flat = mv.checklist_commissioning_flat()
        ids = [v["id"] for v in flat]
        self.assertEqual(len(ids), len(set(ids)))
        n_voci_tot = sum(len(b["voci"]) for b in mv.CHECKLIST_COMMISSIONING)
        self.assertEqual(len(flat), n_voci_tot)
        for v in flat:
            self.assertIn("fase", v)
            self.assertIn("voce", v)

    # --- Loading IONet ---
    def test_loading_ionet_base(self):
        r = mv.loading_ionet(8, canali_medi_per_pacco=16.0, frame_rate_hz=100.0, banda_rete_mbps=100.0)
        self.assertGreater(r["utilizzo_pct"], 0.0)
        self.assertLess(r["utilizzo_pct"], 100.0)
        self.assertEqual(r["n_pacchi_io"], 8)

    def test_loading_ionet_cresce_con_pacchi(self):
        r1 = mv.loading_ionet(4)
        r2 = mv.loading_ionet(8)
        self.assertGreater(r2["utilizzo_pct"], r1["utilizzo_pct"])
        self.assertAlmostEqual(r2["utilizzo_pct"], r1["utilizzo_pct"] * 2.0, places=4)

    def test_loading_ionet_margine_raccomandato(self):
        r_basso = mv.loading_ionet(2, canali_medi_per_pacco=16.0)
        self.assertTrue(r_basso["entro_margine_raccomandato"])
        r_alto = mv.loading_ionet(500, canali_medi_per_pacco=16.0)
        self.assertFalse(r_alto["entro_margine_raccomandato"])
        self.assertGreater(r_alto["utilizzo_pct"], r_alto["margine_raccomandato_pct"])

    def test_loading_ionet_n_pacchi_max_raccomandato_coerente(self):
        r = mv.loading_ionet(4, canali_medi_per_pacco=16.0)
        r_al_limite = mv.loading_ionet(r["n_pacchi_max_raccomandato"], canali_medi_per_pacco=16.0)
        self.assertLessEqual(r_al_limite["utilizzo_pct"], r["margine_raccomandato_pct"])

    def test_loading_ionet_validazioni(self):
        with self.assertRaises(ValueError):
            mv.loading_ionet(0)
        with self.assertRaises(ValueError):
            mv.loading_ionet(4, canali_medi_per_pacco=0)
        with self.assertRaises(ValueError):
            mv.loading_ionet(4, frame_rate_hz=0)
        with self.assertRaises(ValueError):
            mv.loading_ionet(4, banda_rete_mbps=0)


class TestPortataCavo(unittest.TestCase):
    def test_sezione_minima_base(self):
        # Ib=30 A, PVC posa C, 30°C, 1 circuito → 4 mm² (Iz0=32 ≥ 30)
        r = pcav.sezione_minima_portata(30, "PVC", "C", 30, 1)
        self.assertEqual(r["sezione_mm2"], 4)
        self.assertGreaterEqual(r["Iz_A"], 30)
        self.assertAlmostEqual(r["K1"], 1.0)
        self.assertAlmostEqual(r["K2"], 1.0)

    def test_declassamento_aumenta_sezione(self):
        # Stesso Ib ma 50°C e 3 circuiti → sezione necessariamente maggiore
        base = pcav.sezione_minima_portata(30, "PVC", "C", 30, 1)
        declas = pcav.sezione_minima_portata(30, "PVC", "C", 50, 3)
        self.assertGreater(declas["sezione_mm2"], base["sezione_mm2"])
        self.assertLess(declas["K1"], 1.0)
        self.assertLess(declas["K2"], 1.0)

    def test_epr_piu_capace_di_pvc(self):
        pvc = pcav.sezione_minima_portata(95, "PVC", "C", 30, 1)
        epr = pcav.sezione_minima_portata(95, "EPR", "C", 30, 1)
        self.assertLessEqual(epr["sezione_mm2"], pvc["sezione_mm2"])

    def test_utilizzo_sempre_sotto_100(self):
        # La sezione scelta deve sempre garantire Iz ≥ Ib (utilizzo ≤ 100%)
        for ib in (5, 16, 32, 63, 100):
            r = pcav.sezione_minima_portata(ib, "EPR", "E", 30, 1)
            self.assertLessEqual(r["tasso_utilizzo_pct"], 100.0)

    def test_ib_non_valido(self):
        with self.assertRaises(ValueError):
            pcav.sezione_minima_portata(0, "PVC", "C", 30, 1)

    def test_corrente_eccessiva_solleva_errore(self):
        with self.assertRaises(ValueError):
            pcav.sezione_minima_portata(5000, "PVC", "B2", 30, 1)

    def test_portata_corretta_coerente(self):
        v = pcav.portata_corretta(16, "EPR", "C", 30, 1)
        self.assertEqual(v["Iz0_A"], pcav.IZ0_CEI_UNEL[("EPR", "C")][16])
        self.assertAlmostEqual(v["Iz_A"], v["Iz0_A"])  # K1=K2=1 a 30°C, 1 circuito

    def test_tabelle_complete(self):
        # Ogni combinazione isolante/posa copre tutte le sezioni commerciali
        sez_attese = {1.5, 2.5, 4, 6, 10, 16, 25, 35, 50, 70, 95, 120}
        for chiave, tab in pcav.IZ0_CEI_UNEL.items():
            self.assertEqual(set(tab.keys()), sez_attese, chiave)

    def test_cavo_personalizzato_idoneo(self):
        r = pcav.verifica_cavo_personalizzato(25, 30, "PVC", 30, 1)
        self.assertTrue(r["idoneo"])
        self.assertAlmostEqual(r["Iz_A"], 30.0)
        self.assertAlmostEqual(r["tasso_utilizzo_pct"], 25 / 30 * 100.0)

    def test_cavo_personalizzato_non_idoneo(self):
        r = pcav.verifica_cavo_personalizzato(40, 30, "PVC", 30, 1)
        self.assertFalse(r["idoneo"])
        self.assertLess(r["Iz_A"], r["Ib_A"])

    def test_cavo_personalizzato_declassamento(self):
        r = pcav.verifica_cavo_personalizzato(20, 30, "PVC", 50, 3)
        self.assertAlmostEqual(r["K1"], 0.71)
        self.assertAlmostEqual(r["K2"], 0.70)
        self.assertAlmostEqual(r["Iz_A"], 30 * 0.71 * 0.70)

    def test_cavo_personalizzato_input_non_valido(self):
        with self.assertRaises(ValueError):
            pcav.verifica_cavo_personalizzato(0, 30, "PVC")
        with self.assertRaises(ValueError):
            pcav.verifica_cavo_personalizzato(20, 0, "PVC")

    def test_sezione_minima_con_parallelo(self):
        r1 = pcav.sezione_minima_portata(60, "PVC", "C", 30, 1, n_parallelo=1)
        r2 = pcav.sezione_minima_portata(60, "PVC", "C", 30, 1, n_parallelo=2)
        # con 2 conduttori in parallelo basta una sezione minore o uguale
        self.assertLessEqual(r2["sezione_mm2"], r1["sezione_mm2"])
        self.assertAlmostEqual(r2["Iz_A"], r2["Iz0_A"] * r2["K1"] * r2["K2"] * 2)

    def test_cavo_personalizzato_con_parallelo(self):
        r = pcav.verifica_cavo_personalizzato(50, 30, "PVC", 30, 1, n_parallelo=2)
        self.assertAlmostEqual(r["Iz_A"], 60.0)
        self.assertTrue(r["idoneo"])

    def test_n_parallelo_non_valido_raises(self):
        with self.assertRaises(ValueError):
            pcav.sezione_minima_portata(20, "PVC", "C", 30, 1, n_parallelo=0)
        with self.assertRaises(ValueError):
            pcav.verifica_cavo_personalizzato(20, 30, "PVC", 30, 1, n_parallelo=0)

    def test_lista_sezioni_disponibili(self):
        self.assertEqual(pcav.lista_sezioni_disponibili(),
                         sorted(pcav.IZ0_CEI_UNEL[("PVC", "B1")].keys()))


class TestGradoProtezioneIP(unittest.TestCase):
    def test_ip65(self):
        r = gip.decodifica_ip("IP65")
        self.assertEqual(r["prima_cifra"], "6")
        self.assertEqual(r["seconda_cifra"], "5")
        self.assertIn("polvere", r["prima_titolo"].lower())
        self.assertEqual(r["lettere"], [])

    def test_x_non_specificata(self):
        r = gip.decodifica_ip("IP2X")
        self.assertEqual(r["seconda_titolo"], "Non specificata")
        r2 = gip.decodifica_ip("IPX7")
        self.assertEqual(r2["prima_titolo"], "Non specificata")
        self.assertEqual(r2["seconda_cifra"], "7")

    def test_lettere_addizionali_e_supplementari(self):
        r = gip.decodifica_ip("IP54CW")
        tipi = {L[0]: L[1] for L in r["lettere"]}
        self.assertEqual(tipi["C"], "addizionale")
        self.assertEqual(tipi["W"], "supplementare")

    def test_case_insensitive_e_spazi(self):
        self.assertEqual(gip.decodifica_ip("ip 6 8")["codice"], "IP68")

    def test_codici_non_validi(self):
        for bad in ["65", "IP9", "IP6Z", "IP65Q"]:
            with self.assertRaises(ValueError, msg=bad):
                gip.decodifica_ip(bad)

    def test_ik_energie_monotone(self):
        valori = list(gip.IK_ENERGIA_JOULE.values())
        self.assertEqual(valori, sorted(valori))
        self.assertEqual(gip.IK_ENERGIA_JOULE["IK10"], 20.0)


class TestCostiEnergetici(unittest.TestCase):
    def test_costo_annuo(self):
        r = ce.costo_annuo(10, 2000, 0.25)
        self.assertEqual(r["energia_kWh_anno"], 20000)
        self.assertEqual(r["costo_eur_anno"], 5000)

    def test_confronto_risparmio(self):
        r = ce.confronto_efficientamento(12, 10, 4000, 0.20, 800)
        self.assertEqual(r["risparmio_kWh_anno"], 8000)
        self.assertAlmostEqual(r["risparmio_eur_anno"], 1600)
        self.assertAlmostEqual(r["payback_anni"], 0.5)
        self.assertTrue(r["conveniente"])

    def test_nessun_risparmio_payback_infinito(self):
        r = ce.confronto_efficientamento(10, 12, 5000, 0.2, 500)
        self.assertEqual(r["payback_anni"], float("inf"))
        self.assertFalse(r["conveniente"])

    def test_extra_zero_payback_zero(self):
        r = ce.confronto_efficientamento(12, 10, 4000, 0.2, 0)
        self.assertEqual(r["payback_anni"], 0.0)

    def test_potenza_motore(self):
        self.assertAlmostEqual(ce.potenza_assorbita_motore(22, 90), 22 / 0.9)

    def test_motore_ie_piu_efficiente_risparmia(self):
        r = ce.confronto_motore_ie(22, 89.8, 93.0, 6000, 0.22, 600)
        self.assertGreater(r["P_assorbita_prima_kW"], r["P_assorbita_dopo_kW"])
        self.assertGreater(r["risparmio_eur_anno"], 0)
        self.assertGreater(r["risparmio_co2_kg_anno"], 0)

    def test_rendimento_non_valido(self):
        with self.assertRaises(ValueError):
            ce.potenza_assorbita_motore(10, 0)
        with self.assertRaises(ValueError):
            ce.potenza_assorbita_motore(10, 120)


class TestLibreriaCavi(unittest.TestCase):
    def test_lista_cavi_commerciali(self):
        self.assertIn("N1VV-K / FROR (PVC, multipolare)", libcavi.lista_cavi_commerciali())
        self.assertIn("FG16OR16 / FG7OR (EPR/HEPR, multipolare)", libcavi.lista_cavi_commerciali())

    def test_parametri_cavo_pvc(self):
        p = libcavi.parametri_cavo("N1VV-K / FROR (PVC, multipolare)", 4)
        self.assertEqual(p["isolante"], "PVC")
        self.assertAlmostEqual(p["R20_ohm_km"], 4.61)
        self.assertAlmostEqual(p["X_ohm_km"], 0.08)

    def test_parametri_cavo_epr(self):
        p = libcavi.parametri_cavo("FG16OR16 / FG7OR (EPR/HEPR, multipolare)", 16)
        self.assertEqual(p["isolante"], "EPR")
        self.assertAlmostEqual(p["R20_ohm_km"], 1.15)

    def test_cavo_non_riconosciuto_raises(self):
        with self.assertRaises(ValueError):
            libcavi.parametri_cavo("Cavo inesistente", 4)

    def test_sezione_non_in_libreria_raises(self):
        with self.assertRaises(ValueError):
            libcavi.parametri_cavo("N1VV-K / FROR (PVC, multipolare)", 999)

    def test_lista_sezioni_libreria_ordinata(self):
        sez = libcavi.lista_sezioni_libreria()
        self.assertEqual(sez, sorted(sez))
        self.assertEqual(set(sez), set(libcavi.R20_OHM_KM_IEC60228.keys()))


class TestCanalinePasserelle(unittest.TestCase):
    def test_area_canalina(self):
        self.assertAlmostEqual(canp.area_canalina_mm2(100, 50), 5000.0)

    def test_area_canalina_non_valida_raises(self):
        with self.assertRaises(ValueError):
            canp.area_canalina_mm2(0, 50)

    def test_area_cavo(self):
        self.assertAlmostEqual(canp.area_cavo_mm2(10), math.pi / 4.0 * 100.0)

    def test_verifica_riempimento_ottimale(self):
        # area canalina 100x100=10000mm2, 4 cavi diametro 20mm -> area ~1256mm2 -> 12.6%
        r = canp.verifica_riempimento(100, 100, [(20, 4)])
        self.assertEqual(r["n_cavi_totale"], 4)
        self.assertEqual(r["esito"], "ottimale")
        self.assertLess(r["riempimento_pct"], canp.SOGLIA_OTTIMALE_PCT)

    def test_verifica_riempimento_eccessivo(self):
        r = canp.verifica_riempimento(50, 50, [(40, 4)])
        self.assertEqual(r["esito"], "eccessivo")
        self.assertGreater(r["riempimento_pct"], canp.SOGLIA_MASSIMA_PCT)

    def test_verifica_riempimento_nessun_cavo_raises(self):
        with self.assertRaises(ValueError):
            canp.verifica_riempimento(100, 100, [])

    def test_verifica_riempimento_quantita_non_valida_raises(self):
        with self.assertRaises(ValueError):
            canp.verifica_riempimento(100, 100, [(10, 0)])


class TestRiferimentoRapido(unittest.TestCase):
    def test_lista_colori(self):
        colori = rifr.lista_colori()
        self.assertIn("Giallo-Verde", colori)
        self.assertIn("Blu chiaro", colori)

    def test_sezioni_normalizzate_ordinate(self):
        sez = rifr.SEZIONI_CAVO_NORMALIZZATE_MM2
        self.assertEqual(sez, sorted(sez))

    def test_diametro_esterno_indicativo_coerente_con_sezioni(self):
        for sez in rifr.DIAMETRO_ESTERNO_INDICATIVO_MM:
            self.assertIn(sez, rifr.SEZIONI_CAVO_NORMALIZZATE_MM2)


class TestBatchCavi(unittest.TestCase):
    def _linea(self, **kw):
        base = {
            "nome": "L1", "fasi": "Trifase", "Ib_A": 16.0, "lunghezza_m": 30.0,
            "cos_phi": 0.9, "isolante": "PVC", "posa": "C", "T_amb": 30.0,
            "n_circuiti": 1, "n_parallelo": 1,
        }
        base.update(kw)
        return base

    def test_dimensiona_linea_ok(self):
        r = batch_cavi.dimensiona_linea(self._linea(Ib_A=16.0, lunghezza_m=10.0))
        self.assertIsNotNone(r["sezione_mm2"])
        self.assertGreaterEqual(r["Iz_A"], 16.0)
        self.assertEqual(r["esito"], "OK")

    def test_dimensiona_linea_caduta_fuori_norma(self):
        # linea lunga con Ib alta -> caduta sopra 4%
        r = batch_cavi.dimensiona_linea(self._linea(Ib_A=20.0, lunghezza_m=200.0))
        self.assertEqual(r["esito"], "Caduta fuori norma (>4%)")
        self.assertGreater(r["caduta_pct"], 4.0)

    def test_norm_fasi(self):
        self.assertEqual(batch_cavi._norm_fasi("mono"), "Monofase")
        self.assertEqual(batch_cavi._norm_fasi("3"), "Trifase")
        with self.assertRaises(ValueError):
            batch_cavi._norm_fasi("xyz")

    def test_norm_isolante(self):
        self.assertEqual(batch_cavi._norm_isolante("PVC (70°C)"), "PVC")
        self.assertEqual(batch_cavi._norm_isolante("XLPE"), "EPR")

    def test_dimensiona_batch_continua_su_errore(self):
        linee = [
            self._linea(nome="buona"),
            self._linea(nome="cattiva", fasi="boh"),
        ]
        res = batch_cavi.dimensiona_batch(linee)
        self.assertEqual(len(res), 2)
        self.assertEqual(res[0]["esito"], "OK")
        self.assertTrue(res[1]["esito"].startswith("ERRORE"))


class TestBatterieLitio(unittest.TestCase):
    def test_ocv_estremi(self):
        self.assertAlmostEqual(blit.ocv_per_soc(100), 4.20)
        self.assertAlmostEqual(blit.ocv_per_soc(0), 3.00)
        self.assertAlmostEqual(blit.ocv_per_soc(150), 4.20)
        self.assertAlmostEqual(blit.ocv_per_soc(-10), 3.00)

    def test_ocv_monotona_decrescente(self):
        valori = [blit.ocv_per_soc(s) for s in range(0, 101, 5)]
        self.assertEqual(valori, sorted(valori))

    def test_capacita_effettiva_si_riduce_con_c_rate(self):
        c_basso = blit.capacita_effettiva_ah(10.0, 0.2)
        c_alto = blit.capacita_effettiva_ah(10.0, 2.0)
        self.assertGreater(c_basso, c_alto)

    def test_capacita_effettiva_invalida(self):
        with self.assertRaises(ValueError):
            blit.capacita_effettiva_ah(0, 1.0)
        with self.assertRaises(ValueError):
            blit.capacita_effettiva_ah(10.0, 0)

    def test_curva_scarica_struttura(self):
        r = blit.curva_scarica(10.0, c_rate=1.0, n_celle_serie=4, n_celle_parallelo=2, n_punti=20)
        self.assertEqual(len(r["soc_pct"]), 20)
        self.assertEqual(len(r["tensione_pacco_V"]), 20)
        self.assertGreater(r["tensione_iniziale_V"], r["tensione_finale_V"])
        self.assertGreater(r["t_autonomia_h"], 0)

    def test_curva_scarica_c_rate_alto_riduce_autonomia_e_tensione(self):
        basso = blit.curva_scarica(10.0, c_rate=0.2, n_celle_serie=4)
        alto = blit.curva_scarica(10.0, c_rate=2.0, n_celle_serie=4)
        self.assertGreater(basso["t_autonomia_h"], alto["t_autonomia_h"])
        self.assertGreater(basso["tensione_finale_V"], alto["tensione_finale_V"])

    def test_curva_scarica_validazioni(self):
        with self.assertRaises(ValueError):
            blit.curva_scarica(10.0, n_celle_serie=0)
        with self.assertRaises(ValueError):
            blit.curva_scarica(10.0, soc_finale_pct=100)
        with self.assertRaises(ValueError):
            blit.curva_scarica(10.0, R_int_cella_ohm=-1)
        with self.assertRaises(ValueError):
            blit.curva_scarica(10.0, n_punti=1)

    def test_confronto_c_rate(self):
        c = blit.confronto_c_rate(10.0, [0.2, 1.0, 2.0], n_celle_serie=4)
        self.assertEqual(set(c.keys()), {0.2, 1.0, 2.0})
        self.assertGreater(c[0.2]["t_autonomia_h"], c[2.0]["t_autonomia_h"])

    def test_confronto_c_rate_lista_vuota(self):
        with self.assertRaises(ValueError):
            blit.confronto_c_rate(10.0, [])


class TestComponentiPassivi(unittest.TestCase):
    def test_decodifica_colori_4_bande(self):
        r = cpas.decodifica_colori_resistore(["Marrone", "Nero", "Rosso", "Oro"])
        self.assertEqual(r["valore_ohm"], 1000)
        self.assertEqual(r["tolleranza_pct"], 5.0)
        self.assertAlmostEqual(r["valore_min_ohm"], 950.0)
        self.assertAlmostEqual(r["valore_max_ohm"], 1050.0)

    def test_decodifica_colori_5_bande(self):
        r = cpas.decodifica_colori_resistore(["Marrone", "Rosso", "Arancione", "Arancione", "Marrone"])
        self.assertEqual(r["valore_ohm"], 123000)
        self.assertEqual(r["tolleranza_pct"], 1.0)

    def test_decodifica_colori_3_bande_tolleranza_implicita(self):
        r = cpas.decodifica_colori_resistore(["Marrone", "Nero", "Rosso"])
        self.assertEqual(r["valore_ohm"], 1000)
        self.assertEqual(r["tolleranza_pct"], 20.0)
        self.assertNotIn("coeff_temperatura_ppm_C", r)

    def test_decodifica_colori_6_bande_con_coeff_temperatura(self):
        r = cpas.decodifica_colori_resistore(["Marrone", "Nero", "Nero", "Rosso", "Oro", "Marrone"])
        self.assertEqual(r["valore_ohm"], 10000)
        self.assertEqual(r["tolleranza_pct"], 5.0)
        self.assertEqual(r["coeff_temperatura_ppm_C"], 100)

    def test_decodifica_colori_numero_bande_non_valido(self):
        with self.assertRaises(ValueError):
            cpas.decodifica_colori_resistore(["Marrone", "Nero"])
        with self.assertRaises(ValueError):
            cpas.decodifica_colori_resistore(["Marrone"] * 7)

    def test_colori_da_resistenza_3_bande_round_trip(self):
        r = cpas.colori_da_resistenza(1000, 3)
        self.assertEqual(r["tolleranza_pct"], 20.0)
        dec = cpas.decodifica_colori_resistore(r["colori"])
        self.assertEqual(dec["valore_ohm"], 1000)

    def test_colori_da_resistenza_6_bande_round_trip(self):
        r = cpas.colori_da_resistenza(10000, 6, 5.0, 100)
        dec = cpas.decodifica_colori_resistore(r["colori"])
        self.assertEqual(dec["valore_ohm"], 10000)
        self.assertEqual(dec["coeff_temperatura_ppm_C"], 100)

    def test_colori_da_resistenza_6_bande_senza_coeff_temp(self):
        with self.assertRaises(ValueError):
            cpas.colori_da_resistenza(10000, 6, 5.0)  # coeff_temp_ppm_C mancante

    def test_colori_da_resistenza_6_bande_coeff_temp_non_standard(self):
        with self.assertRaises(ValueError):
            cpas.colori_da_resistenza(10000, 6, 5.0, 999)

    def test_decodifica_colori_invalida(self):
        with self.assertRaises(ValueError):
            cpas.decodifica_colori_resistore(["Marrone", "Nero", "Rosso", "Inesistente"])
        with self.assertRaises(ValueError):
            cpas.decodifica_colori_resistore(["Marrone", "Nero", "Rosso", "Nero"])  # Nero non valido come tolleranza

    def test_colori_da_resistenza_round_trip(self):
        for valore in (1000, 4700, 220, 56000, 1_000_000):
            r = cpas.colori_da_resistenza(valore, 4, 5.0)
            dec = cpas.decodifica_colori_resistore(r["colori"])
            self.assertEqual(dec["valore_ohm"], valore)

    def test_colori_da_resistenza_5_bande_round_trip(self):
        r = cpas.colori_da_resistenza(123000, 5, 1.0)
        dec = cpas.decodifica_colori_resistore(r["colori"])
        self.assertEqual(dec["valore_ohm"], 123000)

    def test_colori_da_resistenza_validazioni(self):
        with self.assertRaises(ValueError):
            cpas.colori_da_resistenza(0, 4, 5.0)
        with self.assertRaises(ValueError):
            cpas.colori_da_resistenza(1000, 7, 5.0)  # numero di bande non valido
        with self.assertRaises(ValueError):
            cpas.colori_da_resistenza(1000, 4, 3.0)  # tolleranza senza colore associato

    def test_valore_normalizzato_e_esatto(self):
        r = cpas.valore_normalizzato_e(47000, "E12")
        self.assertAlmostEqual(r["valore_normalizzato"], 47000)
        self.assertAlmostEqual(r["scostamento_pct"], 0.0)

    def test_valore_normalizzato_e_approssima(self):
        r = cpas.valore_normalizzato_e(53, "E24")
        self.assertAlmostEqual(r["valore_normalizzato"], 51.0)

    def test_valore_normalizzato_e_cambio_decade(self):
        # Vicino al limite superiore della decade: deve poter salire alla decade successiva
        r = cpas.valore_normalizzato_e(96, "E12")
        self.assertAlmostEqual(r["valore_normalizzato"], 100.0)

    def test_valore_normalizzato_e_validazioni(self):
        with self.assertRaises(ValueError):
            cpas.valore_normalizzato_e(0, "E12")
        with self.assertRaises(ValueError):
            cpas.valore_normalizzato_e(100, "E999")

    def test_resistori_serie(self):
        r = cpas.resistori_serie([100, 220, 330])
        self.assertEqual(r["valore_equivalente"], 650)

    def test_resistori_parallelo(self):
        r = cpas.resistori_parallelo([1000, 1000])
        self.assertAlmostEqual(r["valore_equivalente"], 500.0)

    def test_resistori_parallelo_tre_valori(self):
        r = cpas.resistori_parallelo([100, 200, 300])
        self.assertAlmostEqual(1.0 / r["valore_equivalente"], 1/100 + 1/200 + 1/300)

    def test_induttori_serie_e_parallelo(self):
        self.assertAlmostEqual(cpas.induttori_serie([1e-3, 2e-3])["valore_equivalente"], 3e-3)
        self.assertAlmostEqual(cpas.induttori_parallelo([1e-3, 1e-3])["valore_equivalente"], 0.5e-3)

    def test_condensatori_serie_e_parallelo(self):
        # Opposto rispetto a resistori/induttori: la serie usa la media armonica
        self.assertAlmostEqual(cpas.condensatori_serie([10e-6, 10e-6])["valore_equivalente"], 5e-6)
        self.assertAlmostEqual(cpas.condensatori_parallelo([10e-6, 22e-6])["valore_equivalente"], 32e-6)

    def test_validazioni_liste_vuote_o_negative(self):
        with self.assertRaises(ValueError):
            cpas.resistori_serie([])
        with self.assertRaises(ValueError):
            cpas.resistori_parallelo([100, -50])
        with self.assertRaises(ValueError):
            cpas.condensatori_serie([0])

    # ---- LED — resistenza di limitazione ----

    def test_resistenza_limitazione_led(self):
        r = cpas.resistenza_limitazione_led(9, 2, 20)
        self.assertAlmostEqual(r["resistenza_ohm"], 350.0)
        self.assertAlmostEqual(r["potenza_dissipata_W"], 0.14)
        self.assertEqual(r["potenza_consigliata_W"], 0.5)

    def test_resistenza_limitazione_led_validazioni(self):
        with self.assertRaises(ValueError):
            cpas.resistenza_limitazione_led(5, 6, 20)  # Vf >= Vcc
        with self.assertRaises(ValueError):
            cpas.resistenza_limitazione_led(0, 2, 20)
        with self.assertRaises(ValueError):
            cpas.resistenza_limitazione_led(9, 2, 0)

    # ---- Partitore di tensione ----

    def test_partitore_tensione_vout(self):
        r = cpas.partitore_tensione_vout(12, 1000, 2000)
        self.assertAlmostEqual(r["v_out"], 8.0)
        self.assertAlmostEqual(r["corrente_mA"], 4.0)

    def test_partitore_tensione_r2_round_trip(self):
        r = cpas.partitore_tensione_r2(12, 4, 1000)
        self.assertAlmostEqual(r["r2_ohm"], 500.0)
        verifica = cpas.partitore_tensione_vout(12, 1000, r["r2_ohm"])
        self.assertAlmostEqual(verifica["v_out"], 4.0)

    def test_partitore_tensione_validazioni(self):
        with self.assertRaises(ValueError):
            cpas.partitore_tensione_r2(12, 15, 1000)  # Vout > Vin
        with self.assertRaises(ValueError):
            cpas.partitore_tensione_vout(12, 0, 1000)

    # ---- Costante di tempo RC/RL ----

    def test_costante_di_tempo_rc(self):
        r = cpas.costante_di_tempo("RC", 1000, 1e-6)
        self.assertAlmostEqual(r["tau_s"], 0.001)
        self.assertAlmostEqual(r["percentuale_a_5tau"], 99.326, places=2)

    def test_costante_di_tempo_rl(self):
        r = cpas.costante_di_tempo("RL", 10, 0.1)
        self.assertAlmostEqual(r["tau_s"], 0.01)

    def test_costante_di_tempo_percentuale_alta_richiede_piu_tempo(self):
        basso = cpas.costante_di_tempo("RC", 1000, 1e-6, 50)
        alto = cpas.costante_di_tempo("RC", 1000, 1e-6, 95)
        self.assertGreater(alto["tempo_target_s"], basso["tempo_target_s"])

    def test_costante_di_tempo_validazioni(self):
        with self.assertRaises(ValueError):
            cpas.costante_di_tempo("XX", 100, 1e-6)
        with self.assertRaises(ValueError):
            cpas.costante_di_tempo("RC", 100, 1e-6, 100)

    # ---- Ponte di Wheatstone ----

    def test_wheatstone_resistenza_incognita(self):
        r = cpas.wheatstone_resistenza_incognita(100, 200, 150)
        self.assertAlmostEqual(r["rx_ohm"], 300.0)

    def test_wheatstone_validazioni(self):
        with self.assertRaises(ValueError):
            cpas.wheatstone_resistenza_incognita(0, 1, 1)

    # ---- AWG <-> mm² ----

    def test_awg_a_mm2_valori_noti(self):
        r = cpas.awg_a_mm2(0)
        self.assertAlmostEqual(r["diametro_mm"], 8.251, places=2)

    def test_awg_mm2_round_trip(self):
        r = cpas.mm2_a_awg(2.5)
        self.assertEqual(r["awg_piu_vicino"], 13)
        ritorno = cpas.awg_a_mm2(r["awg_piu_vicino"])
        self.assertAlmostEqual(ritorno["area_mm2"], 2.5, delta=0.3)

    def test_awg_validazioni(self):
        with self.assertRaises(ValueError):
            cpas.awg_a_mm2(100)
        with self.assertRaises(ValueError):
            cpas.mm2_a_awg(0)

    # ---- Resistori SMD ----

    def test_decodifica_smd_standard_3_cifre(self):
        r = cpas.decodifica_smd_standard("103")
        self.assertAlmostEqual(r["valore_ohm"], 10000.0)

    def test_decodifica_smd_standard_4_cifre(self):
        r = cpas.decodifica_smd_standard("1002")
        self.assertAlmostEqual(r["valore_ohm"], 10000.0)

    def test_decodifica_smd_standard_notazione_r(self):
        self.assertAlmostEqual(cpas.decodifica_smd_standard("4R7")["valore_ohm"], 4.7)
        self.assertAlmostEqual(cpas.decodifica_smd_standard("R47")["valore_ohm"], 0.47)

    def test_decodifica_smd_standard_validazioni(self):
        with self.assertRaises(ValueError):
            cpas.decodifica_smd_standard("12345")
        with self.assertRaises(ValueError):
            cpas.decodifica_smd_standard("")

    def test_decodifica_smd_eia96(self):
        r = cpas.decodifica_smd_eia96("01A")
        self.assertAlmostEqual(r["valore_ohm"], 1.0)
        r2 = cpas.decodifica_smd_eia96("68C")
        self.assertAlmostEqual(r2["valore_ohm"], 499.0)

    def test_decodifica_smd_eia96_validazioni(self):
        with self.assertRaises(ValueError):
            cpas.decodifica_smd_eia96("99A")  # indice fuori range 1-96
        with self.assertRaises(ValueError):
            cpas.decodifica_smd_eia96("01Q")  # lettera non riconosciuta


class TestBackupCompat(unittest.TestCase):
    _PROGETTI_STREAMLIT = {
        "Cantiere A": [
            {"strumento": "Legge di Ohm", "timestamp": "2026-07-01 10:30:00",
             "dati": {"Tensione [V]": 230, "Corrente [A]": 10, "Note": "quadro QE01"}},
            {"strumento": "Caduta di Tensione", "timestamp": "2026-07-01 11:00:00",
             "dati": {"Caduta [V]": 9.67}},
        ],
    }

    def test_esporta_formato_pwa(self):
        b = backup_compat.esporta_progetti_per_pwa(self._PROGETTI_STREAMLIT)
        self.assertEqual(b["tipo"], "backup-calcolatore-industriale")
        self.assertEqual(b["cronologia"], [])
        voci = b["progetti"]["Cantiere A"]
        self.assertEqual(len(voci), 2)
        self.assertEqual(voci[0]["titolo"], "Legge di Ohm")
        self.assertEqual(voci[0]["timestamp"], "2026-07-01T10:30:00")
        self.assertEqual(voci[0]["nota"], "quadro QE01")
        self.assertNotIn("Note", voci[0]["output"])  # la nota esce dai dati e diventa campo dedicato
        self.assertNotIn("nota", voci[1])  # la voce senza nota non ha il campo

    def test_esporta_id_deterministici(self):
        b1 = backup_compat.esporta_progetti_per_pwa(self._PROGETTI_STREAMLIT)
        b2 = backup_compat.esporta_progetti_per_pwa(self._PROGETTI_STREAMLIT)
        ids1 = [v["id"] for v in b1["progetti"]["Cantiere A"]]
        ids2 = [v["id"] for v in b2["progetti"]["Cantiere A"]]
        self.assertEqual(ids1, ids2)
        self.assertEqual(len(set(ids1)), 2)  # id distinti tra voci diverse

    def test_importa_backup_pwa(self):
        backup = {
            "tipo": "backup-calcolatore-industriale", "versione": 1,
            "progetti": {"Impianto B": [
                {"id": "x1", "timestamp": "2026-07-02T09:15:00.000Z", "titolo": "Rifasamento",
                 "input": {"p_attiva_kw": 100}, "output": {"qc_kvar": 55.32}, "nota": "da verificare"},
            ]},
        }
        projects = {}
        n = backup_compat.importa_backup_pwa(backup, projects)
        self.assertEqual(n, 1)
        voce = projects["Impianto B"][0]
        self.assertEqual(voce["strumento"], "Rifasamento")
        self.assertEqual(voce["timestamp"], "2026-07-02 09:15:00")
        self.assertEqual(voce["dati"]["input.p_attiva_kw"], 100)
        self.assertEqual(voce["dati"]["qc_kvar"], 55.32)
        self.assertEqual(voce["dati"]["Note"], "da verificare")

    def test_importa_non_duplica(self):
        backup = {
            "tipo": "backup-calcolatore-industriale",
            "progetti": {"P": [{"id": "a", "timestamp": "2026-07-02T09:00:00", "titolo": "X",
                                "input": {}, "output": {"v": 1}}]},
        }
        projects = {}
        self.assertEqual(backup_compat.importa_backup_pwa(backup, projects), 1)
        self.assertEqual(backup_compat.importa_backup_pwa(backup, projects), 0)  # secondo import: 0 aggiunte
        self.assertEqual(len(projects["P"]), 1)

    def test_importa_valori_annidati_come_json(self):
        backup = {
            "tipo": "backup-calcolatore-industriale",
            "progetti": {"P": [{"id": "b", "timestamp": "2026-07-02T09:00:00", "titolo": "Batteria",
                                "input": {}, "output": {"soc_pct": [100, 90, 80]}}]},
        }
        projects = {}
        backup_compat.importa_backup_pwa(backup, projects)
        self.assertEqual(projects["P"][0]["dati"]["soc_pct"], "[100, 90, 80]")

    def test_importa_rifiuta_file_non_valido(self):
        with self.assertRaises(ValueError):
            backup_compat.importa_backup_pwa({"tipo": "altro"}, {})
        with self.assertRaises(ValueError):
            backup_compat.importa_backup_pwa("non un dict", {})

    def test_round_trip_streamlit_pwa_streamlit(self):
        b = backup_compat.esporta_progetti_per_pwa(self._PROGETTI_STREAMLIT)
        projects = {}
        n = backup_compat.importa_backup_pwa(b, projects)
        self.assertEqual(n, 2)
        voce = projects["Cantiere A"][0]
        self.assertEqual(voce["strumento"], "Legge di Ohm")
        self.assertEqual(voce["timestamp"], "2026-07-01 10:30:00")
        self.assertEqual(voce["dati"]["Note"], "quadro QE01")
        self.assertEqual(voce["dati"]["Tensione [V]"], 230)

    # ---- Filtro RC/RL — frequenza di taglio ----

    def test_frequenza_taglio_rc(self):
        r = cpas.frequenza_taglio_rc_rl("RC", 1000, 1e-6)
        self.assertAlmostEqual(r["fc_Hz"], 159.155, places=2)

    def test_frequenza_taglio_rl(self):
        r = cpas.frequenza_taglio_rc_rl("RL", 1000, 0.1)
        self.assertAlmostEqual(r["fc_Hz"], 1591.55, places=1)

    def test_frequenza_taglio_validazioni(self):
        with self.assertRaises(ValueError):
            cpas.frequenza_taglio_rc_rl("XX", 100, 1e-6)
        with self.assertRaises(ValueError):
            cpas.frequenza_taglio_rc_rl("RC", 0, 1e-6)

    # ---- Amplificatore operazionale ----

    def test_guadagno_op_amp_invertente(self):
        r = cpas.guadagno_op_amp("Invertente", 1000, 10000)
        self.assertAlmostEqual(r["guadagno"], -10.0)
        self.assertAlmostEqual(r["guadagno_dB"], 20.0)

    def test_guadagno_op_amp_non_invertente(self):
        r = cpas.guadagno_op_amp("Non invertente", 1000, 10000)
        self.assertAlmostEqual(r["guadagno"], 11.0)

    def test_guadagno_op_amp_validazioni(self):
        with self.assertRaises(ValueError):
            cpas.guadagno_op_amp("Boh", 1000, 1000)
        with self.assertRaises(ValueError):
            cpas.guadagno_op_amp("Invertente", 0, 1000)

    # ---- Diodo Zener ----

    def test_diodo_zener_regolatore_ok(self):
        r = cpas.diodo_zener_regolatore(12, 5.1, 220, 1000)
        self.assertAlmostEqual(r["i_totale_mA"], 31.3636, places=3)
        self.assertAlmostEqual(r["i_carico_mA"], 5.1)
        self.assertAlmostEqual(r["i_zener_mA"], 26.2636, places=3)
        self.assertTrue(r["regolazione_ok"])

    def test_diodo_zener_regolatore_non_regola(self):
        r = cpas.diodo_zener_regolatore(6, 5.1, 1000, 100)
        self.assertFalse(r["regolazione_ok"])
        self.assertLess(r["i_zener_mA"], 0)

    def test_diodo_zener_regolatore_validazioni(self):
        with self.assertRaises(ValueError):
            cpas.diodo_zener_regolatore(5, 6, 100, 100)  # Vz >= Vin
        with self.assertRaises(ValueError):
            cpas.diodo_zener_regolatore(12, 5.1, 0, 1000)


class TestFulmini(unittest.TestCase):
    def test_area_raccolta_equivalente(self):
        r = fulmini.area_raccolta_equivalente(20.0, 15.0, 10.0)
        # Ad = L*W + 2*(3H)*(L+W) + pi*(3H)^2
        atteso = 20 * 15 + 2 * 30 * 35 + math.pi * 30**2
        self.assertAlmostEqual(r["Ad_m2"], atteso, places=4)

    def test_area_raccolta_validazioni(self):
        with self.assertRaises(ValueError):
            fulmini.area_raccolta_equivalente(0, 10, 5)

    def test_frequenza_fulmini_prevista(self):
        r = fulmini.frequenza_fulmini_prevista(2.0, 5227.433388, 1.0)
        self.assertAlmostEqual(r["Nd_fulmini_anno"], 0.010454867, places=6)

    def test_valuta_necessita_protezione_necessaria(self):
        r = fulmini.valuta_necessita_protezione(0.010454867, 1e-3)
        self.assertTrue(r["protezione_necessaria"])
        self.assertAlmostEqual(r["efficienza_richiesta"], 0.904347, places=4)

    def test_valuta_necessita_protezione_non_necessaria(self):
        r = fulmini.valuta_necessita_protezione(1e-4, 1e-3)
        self.assertFalse(r["protezione_necessaria"])

    def test_livello_protezione_da_efficienza(self):
        r = fulmini.livello_protezione_da_efficienza(0.904347)
        self.assertEqual(r["livello"], "II")

    def test_livello_protezione_lpl_iv_sufficiente(self):
        r = fulmini.livello_protezione_da_efficienza(0.5)
        self.assertEqual(r["livello"], "IV")

    def test_livello_protezione_oltre_lpl_i(self):
        r = fulmini.livello_protezione_da_efficienza(0.99)
        self.assertEqual(r["livello"], "I")
        self.assertFalse(r["raggiungibile_con_lps"])

    def test_parametri_lps(self):
        r = fulmini.parametri_lps("II")
        self.assertEqual(r["raggio_sfera_rotolante_m"], 30)
        self.assertEqual(r["lato_maglia_m"], 10)

    def test_parametri_lps_non_valido(self):
        with self.assertRaises(ValueError):
            fulmini.parametri_lps("V")

    def test_valutazione_lps_completa(self):
        r = fulmini.valutazione_lps(20.0, 15.0, 10.0, 2.0, 1.0, 1e-3)
        self.assertAlmostEqual(r["Ad_m2"], 5227.433388, places=4)
        self.assertTrue(r["protezione_necessaria"])
        self.assertEqual(r["livello"], "II")
        self.assertEqual(r["raggio_sfera_rotolante_m"], 30)

    def test_valutazione_lps_non_necessaria_senza_livello(self):
        r = fulmini.valutazione_lps(5.0, 5.0, 3.0, 0.5, 1.0, 1e-3)
        self.assertFalse(r["protezione_necessaria"])
        self.assertNotIn("livello", r)


class TestBatteriePiombo(unittest.TestCase):
    def test_fattore_temperatura_valori_tabella(self):
        self.assertAlmostEqual(bpb.fattore_temperatura_piombo(25.0), 1.00)
        self.assertAlmostEqual(bpb.fattore_temperatura_piombo(20.0), 1.04)
        self.assertAlmostEqual(bpb.fattore_temperatura_piombo(0.0), 1.59)
        self.assertAlmostEqual(bpb.fattore_temperatura_piombo(40.0), 0.87)

    def test_fattore_temperatura_saturazione(self):
        self.assertAlmostEqual(bpb.fattore_temperatura_piombo(-10.0), 1.59)
        self.assertAlmostEqual(bpb.fattore_temperatura_piombo(50.0), 0.87)

    def test_fattore_temperatura_interpolazione(self):
        # a meta' tra 20 (1.04) e 25 (1.00) -> 1.02
        self.assertAlmostEqual(bpb.fattore_temperatura_piombo(22.5), 1.02, places=6)

    def test_numero_celle_serie(self):
        r = bpb.numero_celle_serie(48.0, 2.0)
        self.assertEqual(r["n_celle"], 24)
        self.assertAlmostEqual(r["V_bus_effettiva"], 48.0)

    def test_numero_celle_serie_arrotonda_per_eccesso(self):
        r = bpb.numero_celle_serie(49.0, 2.0)
        self.assertEqual(r["n_celle"], 25)

    def test_tensione_fine_scarica(self):
        r = bpb.tensione_fine_scarica(24, 1.75)
        self.assertAlmostEqual(r["V_fine_scarica_bus"], 42.0)

    def test_capacita_effettiva_scarica(self):
        r = bpb.capacita_effettiva_scarica(100.0, 0.5, 1.3)
        self.assertAlmostEqual(r["C_eff_Ah"], 50.09130066684767, places=4)
        self.assertLess(r["C_eff_Ah"], 100.0)

    def test_capacita_effettiva_scarica_10h_uguale_nominale(self):
        r = bpb.capacita_effettiva_scarica(100.0, 10.0, 1.3)
        self.assertAlmostEqual(r["C_eff_Ah"], 100.0, places=6)

    def test_dimensionamento_completo(self):
        r = bpb.dimensionamento_completo(5000.0, 0.5, 48.0, 0.90, 0.80, 1.25, 20.0, 0.10)
        self.assertEqual(r["n_celle"], 24)
        self.assertAlmostEqual(r["V_fine_scarica_bus"], 42.0)
        self.assertAlmostEqual(r["C_nominale_Ah"], 90.4224537037037, places=4)
        self.assertAlmostEqual(r["Ah_corretti_temperatura"], 94.03935185185185, places=4)
        self.assertAlmostEqual(r["I_carica_A"], 9.403935185185185, places=4)

    def test_dimensionamento_completo_usa_batterie_ups_per_base(self):
        # La base (C_nominale_Ah) deve coincidere con batterie_ups.dimensiona_banco,
        # per evitare due formule diverse per lo stesso calcolo nell'app.
        base = bat.dimensiona_banco(5000.0, 0.5, 48.0, eta_inverter=0.90, DOD=0.80, fattore_invecchiamento=1.25)
        r = bpb.dimensionamento_completo(5000.0, 0.5, 48.0, 0.90, 0.80, 1.25, 20.0, 0.10)
        self.assertAlmostEqual(r["C_nominale_Ah"], base["C_nominale_Ah"], places=9)


class TestMisuratoriPortata(unittest.TestCase):
    def test_portata_diaframma_iso5167(self):
        r = mport.portata_diaframma_iso5167(250, 100, 0.5, 1000, 0.6, 1.0)
        self.assertAlmostEqual(r["Q_m3h"], 30.972980931545575, places=6)
        self.assertAlmostEqual(r["v_ms"], 1.0954451150103324, places=6)
        self.assertAlmostEqual(r["d_foro_mm"], 50.0)

    def test_portata_diaframma_validazioni(self):
        with self.assertRaises(ValueError):
            mport.portata_diaframma_iso5167(0, 100, 0.5, 1000)
        with self.assertRaises(ValueError):
            mport.portata_diaframma_iso5167(250, 0, 0.5, 1000)
        with self.assertRaises(ValueError):
            mport.portata_diaframma_iso5167(250, 100, 0.05, 1000)
        with self.assertRaises(ValueError):
            mport.portata_diaframma_iso5167(250, 100, 0.9, 1000)
        with self.assertRaises(ValueError):
            mport.portata_diaframma_iso5167(250, 100, 0.5, 0)

    def test_portata_turbina(self):
        r = mport.portata_turbina(50, 100)
        self.assertAlmostEqual(r["Q_lmin"], 30.0)
        self.assertAlmostEqual(r["Q_m3h"], 1.8)

    def test_portata_turbina_validazioni(self):
        with self.assertRaises(ValueError):
            mport.portata_turbina(0, 100)
        with self.assertRaises(ValueError):
            mport.portata_turbina(50, 0)

    def test_portata_elettromagnetico(self):
        r = mport.portata_elettromagnetico(2.0, 100)
        self.assertAlmostEqual(r["Q_m3h"], 56.54866776461628, places=6)
        self.assertAlmostEqual(r["A_m2"], 0.007853981633974483, places=9)

    def test_numero_reynolds_turbolento(self):
        r = mport.numero_reynolds(2.0, 100, 1000, 0.001)
        self.assertAlmostEqual(r["Re"], 200000.0, places=3)
        self.assertEqual(r["regime"], "turbolento")
        self.assertTrue(r["valido_iso5167"])

    def test_numero_reynolds_laminare(self):
        r = mport.numero_reynolds(0.001, 10, 1000, 0.001)
        self.assertEqual(r["regime"], "laminare")
        self.assertFalse(r["valido_iso5167"])

    def test_verifica_velocita_consigliata_nel_range(self):
        r = mport.verifica_velocita_consigliata(2.0, "acqua")
        self.assertTrue(r["nel_range"])

    def test_verifica_velocita_consigliata_fuori_range(self):
        r = mport.verifica_velocita_consigliata(10.0, "acqua")
        self.assertFalse(r["nel_range"])

    def test_verifica_velocita_tipo_non_valido(self):
        with self.assertRaises(ValueError):
            mport.verifica_velocita_consigliata(2.0, "mercurio")

    def test_valuta_diaframma(self):
        r = mport.valuta_diaframma(250, 100, 0.5, 1000, 0.001, 0.6, 1.0, "acqua")
        self.assertAlmostEqual(r["Q_m3h"], 30.972980931545575, places=6)
        self.assertAlmostEqual(r["Re"], 109544.51150103324, places=3)
        self.assertEqual(r["regime"], "turbolento")
        self.assertTrue(r["valido_iso5167"])
        self.assertTrue(r["nel_range"])


class TestAntincendio(unittest.TestCase):
    def test_portata_rete_totale(self):
        r = ai.portata_rete_totale("idrante_UNI45", 2)
        self.assertAlmostEqual(r["Q_tot_lmin"], 360.0)
        self.assertAlmostEqual(r["Q_tot_m3h"], 21.6)
        self.assertEqual(r["n_contemporanei"], 3)
        self.assertEqual(r["durata_min"], 60)

    def test_portata_rete_totale_validazioni(self):
        with self.assertRaises(ValueError):
            ai.portata_rete_totale("idrante_UNI999", 2)
        with self.assertRaises(ValueError):
            ai.portata_rete_totale("idrante_UNI45", 5)

    def test_volume_riserva_idrica(self):
        r = ai.volume_riserva_idrica(360.0, 60)
        self.assertAlmostEqual(r["V_m3"], 21.6)
        self.assertAlmostEqual(r["V_l"], 21600.0)

    def test_volume_riserva_validazioni(self):
        with self.assertRaises(ValueError):
            ai.volume_riserva_idrica(0, 60)
        with self.assertRaises(ValueError):
            ai.volume_riserva_idrica(360, 0)

    def test_prevalenza_pompa(self):
        r = ai.prevalenza_pompa(2.0, 15.0, 0.3, 0.5)
        self.assertAlmostEqual(r["H_geodetica_bar"], 1.4710208884966167, places=6)
        self.assertAlmostEqual(r["H_pompa_bar"], 4.271020888496617, places=6)
        self.assertAlmostEqual(r["H_pompa_m"], 43.5516, places=3)

    def test_prevalenza_pompa_validazioni(self):
        with self.assertRaises(ValueError):
            ai.prevalenza_pompa(0, 15.0)
        with self.assertRaises(ValueError):
            ai.prevalenza_pompa(2.0, -1.0)

    def test_numero_protezioni_area(self):
        r = ai.numero_protezioni_area(5000, 45)
        self.assertEqual(r["n_protezioni_stimato"], 3)

    def test_numero_protezioni_area_minimo_uno(self):
        r = ai.numero_protezioni_area(100, 45)
        self.assertEqual(r["n_protezioni_stimato"], 1)

    def test_dimensionamento_completo(self):
        r = ai.dimensionamento_completo("idrante_UNI45", 2, 15.0, 0.3, 0.5)
        self.assertAlmostEqual(r["Q_tot_lmin"], 360.0)
        self.assertAlmostEqual(r["V_m3"], 21.6)
        self.assertAlmostEqual(r["H_pompa_bar"], 4.271020888496617, places=6)


class TestAtex(unittest.TestCase):
    def test_categoria_minima_gas(self):
        r = atex.categoria_minima_gas(1)
        self.assertEqual(r["categoria_minima"], "2G")
        self.assertEqual(r["epl_minimo"], "Gb")

    def test_categoria_minima_gas_invalida(self):
        with self.assertRaises(ValueError):
            atex.categoria_minima_gas(3)

    def test_categoria_minima_polveri(self):
        r = atex.categoria_minima_polveri(21)
        self.assertEqual(r["categoria_minima"], "2D")
        self.assertEqual(r["epl_minimo"], "Db")

    def test_categoria_minima_polveri_invalida(self):
        with self.assertRaises(ValueError):
            atex.categoria_minima_polveri(23)

    def test_classe_temperatura(self):
        r = atex.classe_temperatura(280)
        self.assertEqual(r["classe_temperatura"], "T3")
        self.assertAlmostEqual(r["T_max_superficie_C"], 200.0)

    def test_classe_temperatura_alta(self):
        r = atex.classe_temperatura(500)
        self.assertEqual(r["classe_temperatura"], "T1")

    def test_classe_temperatura_troppo_bassa(self):
        with self.assertRaises(ValueError):
            atex.classe_temperatura(80)

    def test_marcatura_atex_gas(self):
        r = atex.marcatura_atex(1, "IIB", 280)
        self.assertEqual(r["marcatura_indicativa"], "II 2G Ex IIB T3 Gb")
        self.assertEqual(r["gruppo_gas"], "IIB")

    def test_marcatura_atex_polveri(self):
        r = atex.marcatura_atex(21)
        self.assertEqual(r["marcatura_indicativa"], "II 2D Ex Db")
        self.assertNotIn("gruppo_gas", r)

    def test_marcatura_atex_zona_invalida(self):
        with self.assertRaises(ValueError):
            atex.marcatura_atex(5)

    def test_marcatura_atex_gruppo_gas_invalido(self):
        with self.assertRaises(ValueError):
            atex.marcatura_atex(1, "IID")


class TestVasoEspansione(unittest.TestCase):
    def test_coefficiente_dilatazione(self):
        r = vesp.coefficiente_dilatazione(80)
        self.assertAlmostEqual(r["e"], 0.0289)

    def test_coefficiente_dilatazione_interpolato(self):
        r = vesp.coefficiente_dilatazione(45)
        self.assertAlmostEqual(r["e"], 0.01)

    def test_coefficiente_dilatazione_saturazione(self):
        self.assertAlmostEqual(vesp.coefficiente_dilatazione(5)["e"], 0.0003)
        self.assertAlmostEqual(vesp.coefficiente_dilatazione(150)["e"], 0.0435)

    def test_volume_espansione(self):
        r = vesp.volume_espansione(500, 80)
        self.assertAlmostEqual(r["Ve_l"], 14.45)

    def test_fattore_utilizzo_vaso(self):
        r = vesp.fattore_utilizzo_vaso(1.5, 3.0)
        self.assertAlmostEqual(r["Fu"], 0.375)

    def test_fattore_utilizzo_vaso_validazioni(self):
        with self.assertRaises(ValueError):
            vesp.fattore_utilizzo_vaso(-1, 3.0)
        with self.assertRaises(ValueError):
            vesp.fattore_utilizzo_vaso(3.0, 3.0)

    def test_pressione_statica_da_altezza(self):
        r = vesp.pressione_statica_da_altezza(15)
        self.assertAlmostEqual(r["P_statica_bar"], 1.4710208884966167, places=6)

    def test_volume_vaso_nominale(self):
        r = vesp.volume_vaso_nominale(500, 80, 1.5, 3.0)
        self.assertAlmostEqual(r["Vn_l"], 38.53333333333333, places=6)
        self.assertAlmostEqual(r["Ve_l"], 14.45)
        self.assertAlmostEqual(r["Fu"], 0.375)


class TestIlluminazioneEmergenza(unittest.TestCase):
    def test_verifica_via_esodo_conforme(self):
        r = ie.verifica_via_esodo(1.5, 0.8)
        self.assertTrue(r["conforme"])

    def test_verifica_via_esodo_non_conforme(self):
        r = ie.verifica_via_esodo(0.8, 0.3)
        self.assertFalse(r["conforme"])

    def test_verifica_area_aperta(self):
        self.assertTrue(ie.verifica_area_aperta(0.6)["conforme"])
        self.assertFalse(ie.verifica_area_aperta(0.4)["conforme"])

    def test_illuminamento_minimo_area_rischio_sopra_soglia(self):
        r = ie.illuminamento_minimo_area_rischio(300)
        self.assertAlmostEqual(r["E_minimo_richiesto_lux"], 30.0)

    def test_illuminamento_minimo_area_rischio_sotto_soglia(self):
        r = ie.illuminamento_minimo_area_rischio(100)
        self.assertAlmostEqual(r["E_minimo_richiesto_lux"], 15.0)

    def test_verifica_uniformita_conforme(self):
        r = ie.verifica_uniformita(20, 1)
        self.assertTrue(r["conforme"])
        self.assertAlmostEqual(r["rapporto"], 20.0)

    def test_verifica_uniformita_non_conforme(self):
        r = ie.verifica_uniformita(45, 1)
        self.assertFalse(r["conforme"])

    def test_verifica_uniformita_validazioni(self):
        with self.assertRaises(ValueError):
            ie.verifica_uniformita(1, 5)

    def test_autonomia_minima_richiesta(self):
        r = ie.autonomia_minima_richiesta("affollamento_elevato")
        self.assertAlmostEqual(r["autonomia_minima_h"], 2.0)

    def test_autonomia_minima_tipo_non_valido(self):
        with self.assertRaises(ValueError):
            ie.autonomia_minima_richiesta("inesistente")


class TestGruppoFrigo(unittest.TestCase):
    def test_cop_pompa_di_calore(self):
        r = gf.cop_pompa_di_calore(10, 3)
        self.assertAlmostEqual(r["COP"], 3.3333333333333335, places=6)

    def test_eer_raffrescamento(self):
        r = gf.eer_raffrescamento(8, 2.5)
        self.assertAlmostEqual(r["EER"], 3.2)

    def test_cop_carnot_riscaldamento(self):
        r = gf.cop_carnot_riscaldamento(45, 5)
        self.assertAlmostEqual(r["COP_Carnot"], 7.95375, places=4)

    def test_eer_carnot_raffrescamento(self):
        r = gf.eer_carnot_raffrescamento(35, 7)
        self.assertAlmostEqual(r["EER_Carnot"], 10.005357142857141, places=4)

    def test_cop_carnot_validazioni(self):
        with self.assertRaises(ValueError):
            gf.cop_carnot_riscaldamento(5, 45)

    def test_rendimento_secondo_principio(self):
        r = gf.rendimento_secondo_principio(3.3333333333333335, 7.95375)
        self.assertAlmostEqual(r["eta_secondo_principio_pct"], 41.90895280004191, places=4)

    def test_rendimento_secondo_principio_oltre_carnot(self):
        with self.assertRaises(ValueError):
            gf.rendimento_secondo_principio(9.0, 7.95375)

    def test_dimensionamento_completo_riscaldamento(self):
        r = gf.dimensionamento_completo_riscaldamento(10, 3, 45, 5)
        self.assertAlmostEqual(r["COP"], 3.3333333333333335, places=6)
        self.assertAlmostEqual(r["COP_Carnot"], 7.95375, places=4)
        self.assertAlmostEqual(r["eta_secondo_principio_pct"], 41.90895280004192, places=4)


if __name__ == "__main__":
    unittest.main()
