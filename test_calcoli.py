import math
import unittest

import automazione
import formule
import idraulica


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


if __name__ == "__main__":
    unittest.main()
