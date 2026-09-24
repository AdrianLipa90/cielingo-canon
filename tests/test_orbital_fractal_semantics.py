from __future__ import annotations
import math
import unittest

from cielingo_core.lingophysics.orbital_fractal_semantics import (
    ConceptState,
    DualMode,
    KakuUnit,
    OrbitalCell,
    RadicalState,
    RelationEdge,
    SentenceOrbit,
    SurfaceKind,
    build_hebrew_radical,
    dual_phase,
    hebrew_orbital_cells,
    latent_hebrew_vowel_potential,
    moire_envelope,
)

class OrbitalFractalSemanticsTests(unittest.TestCase):
    def test_conjugate_and_antiphase_are_distinct(self):
        theta = 0.37
        c = dual_phase(theta, DualMode.CONJUGATE)
        a = dual_phase(theta, DualMode.ANTIPHASE)
        self.assertAlmostEqual(c[1], -theta, places=12)
        self.assertAlmostEqual(abs(((a[1]-theta+math.pi)%(2*math.pi))-math.pi), math.pi, places=12)
        self.assertNotAlmostEqual(c[1], a[1], places=6)

    def test_orbital_cell_between_kaku_and_radical(self):
        k = KakuUnit("X", 0.5, SurfaceKind.CONSONANT)
        cell = OrbitalCell(k, 0.8, 0.25)
        radical = RadicalState("r", (cell,))
        self.assertGreater(abs(cell.amplitude), 0)
        self.assertAlmostEqual(radical.structural_mass, 0.5)

    def test_radical_order_changes_phase_moment(self):
        a = OrbitalCell(KakuUnit("A", 0.2), 1.0, 0.1)
        b = OrbitalCell(KakuUnit("B", 0.8), 1.0, 0.9)
        r1 = RadicalState("r1", (a,b))
        r2 = RadicalState("r2", (b,a))
        self.assertNotAlmostEqual(r1.ordered_phase_moment, r2.ordered_phase_moment)

    def test_sentence_holonomy_matches_exp_sum(self):
        r = RadicalState("r",(OrbitalCell(KakuUnit("A",0.5),1.0,0.2),))
        a = ConceptState("a", r, 0.1)
        b = ConceptState("b", r, -0.3)
        edges=(RelationEdge("a","REL","b",0.25), RelationEdge("b","REL","a",-0.10))
        s=SentenceOrbit("s",(a,b),edges)
        expected=complex(math.cos(0.15), math.sin(0.15))
        self.assertAlmostEqual(s.holonomy.real, expected.real, places=12)
        self.assertAlmostEqual(s.holonomy.imag, expected.imag, places=12)

    def test_moire_envelope_bounds(self):
        out=moire_envelope((1+0j,1j),(1+0j,-1j))
        self.assertAlmostEqual(out[0],1.0)
        self.assertAlmostEqual(out[1],0.0)

    def test_hebrew_final_forms_normalized(self):
        r=build_hebrew_radical("mlk","מלך")
        self.assertEqual([c.kaku.symbol for c in r.cells],["מ","ל","כ"])
        self.assertEqual([c.kaku.raw_value for c in r.cells],[40.0,30.0,20.0])

    def test_niqqud_changes_phase_not_consonant_mass(self):
        plain=hebrew_orbital_cells("מלך")
        vocal=hebrew_orbital_cells("מֶלֶךְ")
        self.assertEqual([c.kaku.raw_value for c in plain],[c.kaku.raw_value for c in vocal])
        self.assertTrue(all(c.latent for c in plain))
        self.assertTrue(any(not c.latent for c in vocal))
        self.assertNotEqual([c.phase for c in plain],[c.phase for c in vocal])

    def test_latent_vowel_potential_nonzero_with_low_mean(self):
        p=latent_hebrew_vowel_potential()
        self.assertAlmostEqual(p["second_moment"],1.0,places=12)
        self.assertGreater(p["support_entropy_bits"],3.0)
        self.assertLess(p["mean_abs"],1e-12)

    def test_sentence_rejects_unknown_relation_endpoint(self):
        r=RadicalState("r",(OrbitalCell(KakuUnit("A",0.5),1.0,0.2),))
        a=ConceptState("a",r)
        with self.assertRaises(ValueError):
            SentenceOrbit("s",(a,),(RelationEdge("a","R","missing",0.0),))

if __name__ == "__main__":
    unittest.main()
