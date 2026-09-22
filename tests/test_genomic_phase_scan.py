from __future__ import annotations

from math import cos, tau

from cielingo_core.lingophysics.genomic_phase_scan import (
    SpacingObservation, regular_period_grid, scan_periods,
)


def test_phase_scan_recovers_injected_helical_period():
    period = 10.5
    observations = [
        SpacingObservation(float(d), 2.0 + 0.01 * d + 0.8 * cos(tau * d / period + 0.4))
        for d in range(0, 81)
    ]
    best = scan_periods(observations, regular_period_grid(9.0, 12.0, 0.05))[0]
    assert abs(best.period_bp - period) <= 0.05
    assert best.incremental_r2 > 0.99
    assert best.amplitude > 0.79


def test_phase_scan_rejects_too_few_points():
    observations = [SpacingObservation(float(d), float(d)) for d in range(5)]
    try:
        scan_periods(observations, [10.5])
    except ValueError as exc:
        assert "at least six" in str(exc)
    else:
        raise AssertionError("expected fail-closed sample-size error")
