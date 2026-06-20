import math
import unittest

import automazione
import formule
import idraulica
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


if __name__ == "__main__":
    unittest.main()
