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


if __name__ == "__main__":
    unittest.main()
