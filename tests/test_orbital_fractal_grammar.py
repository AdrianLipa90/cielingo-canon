import math
import pytest

from cielingo_core.orbital_semantics.grammar import (
    KakuState, OrbitalCell, OrbitalLevel, OrbitalUnit, PhaseBranch,
    SemanticConnectionEdge, dual_cells, lambda_path_gain, latent_phase_ensemble,
    moire_pair, phasenav_holonomy_input, path_transport,
)


def test_orbital_cell_is_required_between_kaku_and_radical():
    k = OrbitalUnit("k", OrbitalLevel.KAKU)
    with pytest.raises(ValueError):
        OrbitalUnit("r", OrbitalLevel.RADICAL, children=(k,))
    chi = OrbitalUnit("chi", OrbitalLevel.ORBITAL_CELL, children=(k,))
    r = OrbitalUnit("r", OrbitalLevel.RADICAL, children=(chi,))
    assert r.children[0].level == OrbitalLevel.ORBITAL_CELL


def test_conjugate_and_counterphase_are_not_conflated():
    k = KakuState("k", "א", 1.0)
    c = OrbitalCell("c", k, 0.37, PhaseBranch.PLUS, 1.0)
    conj = c.conjugate()
    anti = c.counterphase()
    assert math.isclose(conj.effective_phase_rad, -0.37, abs_tol=1e-12)
    expected = ((0.37 + math.pi + math.pi) % (2*math.pi)) - math.pi
    assert math.isclose(anti.effective_phase_rad, expected, abs_tol=1e-12)
    assert not math.isclose(conj.effective_phase_rad, anti.effective_phase_rad, abs_tol=1e-9)


def test_counterphase_cancels_equal_orbit_without_erasing_input_power():
    k = KakuState("k", "ב", 2.0)
    c = OrbitalCell("c", k, 0.7, PhaseBranch.PLUS, 0.8)
    anti = c.counterphase()
    rec = moire_pair(c, anti)
    assert rec.resultant_abs < 1e-12
    assert rec.input_power > 0.0
    assert rec.cancellation_ratio < 1e-12


def test_conjugate_pair_is_complex_conjugate():
    k = KakuState("k", "מ", 3.0)
    plus, minus = dual_cells(k, 1.1, lambda_coupling=0.4)
    assert abs(minus.amplitude - plus.amplitude.conjugate()) < 1e-12


def test_uniform_latent_phase_ensemble_zero_mean_nonzero_potential():
    n = 13
    rec = latent_phase_ensemble([2*math.pi*k/n for k in range(n)])
    assert rec.mean_abs < 1e-12
    assert math.isclose(rec.second_moment, 1.0, abs_tol=1e-12)
    assert math.isclose(rec.entropy_bits, math.log2(13), abs_tol=1e-12)


def test_lambda_is_separate_from_u1_holonomy_input():
    edges = [
        SemanticConnectionEdge("e1", 0.2, 0.5),
        SemanticConnectionEdge("e2", -0.4, 0.25),
    ]
    assert phasenav_holonomy_input(edges) == (0.2, -0.4)
    assert math.isclose(lambda_path_gain(edges), 0.125)
    z = path_transport(edges)
    assert math.isclose(abs(z), 0.125, abs_tol=1e-12)
    assert math.isclose(math.atan2(z.imag, z.real), -0.2, abs_tol=1e-12)


def test_negative_structural_mass_rejected():
    with pytest.raises(ValueError):
        KakuState("k", "א", -1.0)


def test_negative_lambda_rejected():
    k = KakuState("k", "א", 1.0)
    with pytest.raises(ValueError):
        OrbitalCell("c", k, 0.0, lambda_coupling=-0.1)


def test_lambda_path_gain_overflow_fails_closed():
    edges = [
        SemanticConnectionEdge("e1", 0.1, 1e308),
        SemanticConnectionEdge("e2", -0.1, 1e308),
    ]
    with pytest.raises(OverflowError):
        lambda_path_gain(edges)
    with pytest.raises(OverflowError):
        path_transport(edges)


def test_orbital_cell_amplitude_overflow_fails_closed():
    k = KakuState("k-big", "א", 1e308)
    cell = OrbitalCell("c-big", k, 0.0, lambda_coupling=1e308)
    with pytest.raises(OverflowError):
        _ = cell.amplitude
