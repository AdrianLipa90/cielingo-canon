from __future__ import annotations

import math

from cielingo_core.genomics import (
    SpacerReadout,
    fit_periodic_readout,
    scan_periods,
)


def test_fit_periodic_readout_recovers_clean_signal():
    points = [
        SpacerReadout(
            float(distance),
            1.2 + 0.7 * math.cos(
                2 * math.pi * distance / 10.5 + 0.3
            ),
        )
        for distance in range(0, 43)
    ]
    fit = fit_periodic_readout(points, 10.5)
    assert fit["sse"] < 1e-20
    assert abs(fit["amplitude"] - 0.7) < 1e-10


def test_period_scan_recovers_synthetic_helical_period_without_fixing_it():
    points = [
        SpacerReadout(
            float(distance),
            0.4 + 0.9 * math.cos(
                2 * math.pi * distance / 10.5 - 0.2
            ),
        )
        for distance in range(0, 43)
    ]
    result = scan_periods(
        points,
        min_period_bp=9.0,
        max_period_bp=12.0,
        step_bp=0.05,
    )
    assert abs(result["best_fit"]["period_bp"] - 10.5) <= 0.051
    assert (
        "biological interpretation requires external validation"
        in result["claim_scope"]
    )
