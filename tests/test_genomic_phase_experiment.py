from __future__ import annotations

from math import cos, pi

import pytest

from cielingo_core.genomic import fit_first_harmonic, scan_periods, spacer_phase_design


def test_harmonic_fit_recovers_clean_periodic_signal() -> None:
    spacers = list(range(0, 32))
    responses = [
        2.0 + 0.8 * cos(2.0 * pi * spacer / 10.5 - 0.35)
        for spacer in spacers
    ]
    fit = fit_first_harmonic(spacers, responses, 10.5)

    assert fit.amplitude == pytest.approx(0.8, abs=1e-9)
    assert fit.r_squared == pytest.approx(1.0, abs=1e-10)
    assert fit.sse == pytest.approx(0.0, abs=1e-10)


def test_period_scan_can_select_period_without_fixing_it() -> None:
    spacers = list(range(0, 42))
    responses = [
        1.0 + 0.6 * cos(2.0 * pi * spacer / 10.5 + 0.2)
        for spacer in spacers
    ]
    scan = scan_periods(spacers, responses, [9.5, 10.0, 10.5, 11.0, 11.5])

    assert scan.best.period_bp == 10.5
    assert scan.best.r_squared > 0.999999


def test_spacer_design_is_explicitly_reference_phase_only() -> None:
    design = spacer_phase_design(0, 10, reference_period_bp=10.0)
    assert design[0]["reference_phase_rad"] == pytest.approx(0.0)
    assert design[5]["reference_phase_rad"] == pytest.approx(pi)
