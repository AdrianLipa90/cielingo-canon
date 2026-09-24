import math

from src.lingophysics.grammar_math import (
    circular_phase_distance,
    euclidean_distance,
    orbital_cell_distance,
    wrapped_phase_delta,
)


def test_circular_phase_distance_respects_wrap_boundary():
    eps = 1e-4
    circular = circular_phase_distance([eps], [2*math.pi-eps])
    linear = euclidean_distance([eps], [2*math.pi-eps])
    assert circular < 3*eps
    assert linear > 6.0


def test_wrapped_phase_delta_counterphase_is_pi_magnitude():
    assert math.isclose(abs(wrapped_phase_delta(0.0, math.pi)), math.pi, abs_tol=1e-12)


def test_orbital_cell_distance_separates_circular_phase_from_scalar_channels():
    d = orbital_cell_distance(
        (0.4, 1e-5, 0.8),
        (0.4, 2*math.pi-1e-5, 0.8),
    )
    assert d < 1e-4
