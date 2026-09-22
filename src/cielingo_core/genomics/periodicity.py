"""Periodicity diagnostics for spacer-dependent genomic readouts."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Sequence


@dataclass(frozen=True)
class SpacerReadout:
    spacer_bp: float
    value: float

    def __post_init__(self) -> None:
        if not math.isfinite(self.spacer_bp) or not math.isfinite(self.value):
            raise ValueError("spacer_bp and value must be finite")


def _solve3(
    matrix: list[list[float]],
    vector: list[float],
) -> tuple[float, float, float]:
    augmented = [
        row[:] + [vector[index]]
        for index, row in enumerate(matrix)
    ]
    for column in range(3):
        pivot = max(
            range(column, 3),
            key=lambda row: abs(augmented[row][column]),
        )
        if abs(augmented[pivot][column]) < 1e-12:
            raise ValueError("periodic fit is singular")
        augmented[column], augmented[pivot] = (
            augmented[pivot],
            augmented[column],
        )

        scale = augmented[column][column]
        augmented[column] = [
            value / scale
            for value in augmented[column]
        ]

        for row in range(3):
            if row == column:
                continue
            factor = augmented[row][column]
            augmented[row] = [
                augmented[row][index]
                - factor * augmented[column][index]
                for index in range(4)
            ]

    return (
        augmented[0][3],
        augmented[1][3],
        augmented[2][3],
    )


def fit_periodic_readout(
    readouts: Sequence[SpacerReadout],
    period_bp: float,
) -> dict[str, float]:
    """Fit intercept + cosine + sine for one candidate period."""

    if len(readouts) < 3:
        raise ValueError("at least three readouts are required")
    if not math.isfinite(period_bp) or period_bp <= 0.0:
        raise ValueError("period_bp must be finite and positive")

    rows: list[tuple[float, float, float]] = []
    values: list[float] = []
    for point in readouts:
        angle = 2.0 * math.pi * point.spacer_bp / period_bp
        rows.append((1.0, math.cos(angle), math.sin(angle)))
        values.append(point.value)

    matrix = [
        [
            sum(row[left] * row[right] for row in rows)
            for right in range(3)
        ]
        for left in range(3)
    ]
    vector = [
        sum(row[index] * value for row, value in zip(rows, values))
        for index in range(3)
    ]
    intercept, cosine, sine = _solve3(matrix, vector)
    predictions = [
        intercept + cosine * row[1] + sine * row[2]
        for row in rows
    ]
    sse = sum(
        (value - prediction) ** 2
        for value, prediction in zip(values, predictions)
    )
    amplitude = math.hypot(cosine, sine)
    phase = math.atan2(-sine, cosine)

    return {
        "period_bp": period_bp,
        "intercept": intercept,
        "cosine": cosine,
        "sine": sine,
        "amplitude": amplitude,
        "phase_rad": phase,
        "sse": sse,
    }


def scan_periods(
    readouts: Sequence[SpacerReadout],
    *,
    min_period_bp: float = 8.0,
    max_period_bp: float = 13.0,
    step_bp: float = 0.05,
) -> dict[str, object]:
    """Search a period grid without fixing a DNA helical repeat in advance."""

    if (
        min_period_bp <= 0.0
        or max_period_bp <= min_period_bp
        or step_bp <= 0.0
    ):
        raise ValueError("invalid period scan bounds")

    fits: list[dict[str, float]] = []
    period = min_period_bp
    while period <= max_period_bp + step_bp * 0.25:
        try:
            fits.append(fit_periodic_readout(readouts, period))
        except ValueError:
            pass
        period += step_bp

    if not fits:
        raise ValueError("no nonsingular periodic fits")

    best = min(
        fits,
        key=lambda fit: (fit["sse"], fit["period_bp"]),
    )
    return {
        "schema": "CIELINGO_GENOMIC_PERIOD_SCAN_V0_1",
        "best_fit": best,
        "fits": fits,
        "model": "intercept + A*cos(2pi*d/P) + B*sin(2pi*d/P)",
        "claim_scope": (
            "periodicity diagnostic only; biological interpretation "
            "requires external validation"
        ),
    }
