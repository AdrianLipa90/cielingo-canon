"""Experimental statistics for spacer/phase perturbation studies.

These helpers test for a periodic component in measured responses. They do not
establish a biological mechanism by themselves.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, hypot, isfinite, pi, sin
from typing import Iterable


@dataclass(frozen=True)
class HarmonicFit:
    period_bp: float
    intercept: float
    cos_coefficient: float
    sin_coefficient: float
    amplitude: float
    phase_offset_rad: float
    sse: float
    null_sse: float
    r_squared: float

    def to_dict(self) -> dict[str, float]:
        return {
            "period_bp": self.period_bp,
            "intercept": self.intercept,
            "cos_coefficient": self.cos_coefficient,
            "sin_coefficient": self.sin_coefficient,
            "amplitude": self.amplitude,
            "phase_offset_rad": self.phase_offset_rad,
            "sse": self.sse,
            "null_sse": self.null_sse,
            "r_squared": self.r_squared,
        }


@dataclass(frozen=True)
class PeriodScan:
    best: HarmonicFit
    candidates: tuple[HarmonicFit, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "best": self.best.to_dict(),
            "candidates": [fit.to_dict() for fit in self.candidates],
        }


def _finite_vector(values: Iterable[float], name: str) -> tuple[float, ...]:
    out = tuple(float(value) for value in values)
    if not out:
        raise ValueError(f"{name} must not be empty")
    if any(not isfinite(value) for value in out):
        raise ValueError(f"{name} must contain only finite values")
    return out


def _solve_3x3(matrix: list[list[float]], rhs: list[float]) -> tuple[float, float, float]:
    augmented = [list(row) + [rhs[index]] for index, row in enumerate(matrix)]
    for column in range(3):
        pivot = max(range(column, 3), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1e-12:
            raise ValueError("harmonic design matrix is singular")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        scale = augmented[column][column]
        augmented[column] = [value / scale for value in augmented[column]]
        for row in range(3):
            if row == column:
                continue
            factor = augmented[row][column]
            augmented[row] = [
                current - factor * reference
                for current, reference in zip(augmented[row], augmented[column])
            ]
    return tuple(augmented[index][3] for index in range(3))  # type: ignore[return-value]


def fit_first_harmonic(
    spacers_bp: Iterable[float],
    responses: Iterable[float],
    period_bp: float,
) -> HarmonicFit:
    x = _finite_vector(spacers_bp, "spacers_bp")
    y = _finite_vector(responses, "responses")
    if len(x) != len(y):
        raise ValueError("spacers_bp and responses must have equal length")
    if len(x) < 3:
        raise ValueError("at least three observations are required")
    period = float(period_bp)
    if not isfinite(period) or period <= 0.0:
        raise ValueError("period_bp must be finite and positive")

    omega = 2.0 * pi / period
    c = [cos(omega * value) for value in x]
    s = [sin(omega * value) for value in x]

    matrix = [
        [float(len(x)), sum(c), sum(s)],
        [sum(c), sum(value * value for value in c), sum(a * b for a, b in zip(c, s))],
        [sum(s), sum(a * b for a, b in zip(c, s)), sum(value * value for value in s)],
    ]
    rhs = [
        sum(y),
        sum(a * b for a, b in zip(y, c)),
        sum(a * b for a, b in zip(y, s)),
    ]
    intercept, cos_coeff, sin_coeff = _solve_3x3(matrix, rhs)
    predicted = [
        intercept + cos_coeff * cv + sin_coeff * sv
        for cv, sv in zip(c, s)
    ]
    sse = sum((observed - estimate) ** 2 for observed, estimate in zip(y, predicted))
    mean = sum(y) / len(y)
    null_sse = sum((value - mean) ** 2 for value in y)
    r_squared = 0.0 if null_sse <= 1e-15 else 1.0 - sse / null_sse

    return HarmonicFit(
        period_bp=period,
        intercept=intercept,
        cos_coefficient=cos_coeff,
        sin_coefficient=sin_coeff,
        amplitude=hypot(cos_coeff, sin_coeff),
        phase_offset_rad=atan2(sin_coeff, cos_coeff),
        sse=sse,
        null_sse=null_sse,
        r_squared=r_squared,
    )


def scan_periods(
    spacers_bp: Iterable[float],
    responses: Iterable[float],
    candidate_periods_bp: Iterable[float],
) -> PeriodScan:
    periods = _finite_vector(candidate_periods_bp, "candidate_periods_bp")
    if any(period <= 0.0 for period in periods):
        raise ValueError("candidate periods must be positive")
    x = tuple(spacers_bp)
    y = tuple(responses)
    fits = tuple(fit_first_harmonic(x, y, period) for period in periods)
    return PeriodScan(best=min(fits, key=lambda fit: fit.sse), candidates=fits)


def spacer_phase_design(
    start_bp: int = 0,
    stop_bp: int = 21,
    *,
    reference_period_bp: float = 10.5,
) -> list[dict[str, float | int]]:
    if isinstance(start_bp, bool) or isinstance(stop_bp, bool):
        raise ValueError("spacer bounds must be integers")
    if not isinstance(start_bp, int) or not isinstance(stop_bp, int) or stop_bp < start_bp:
        raise ValueError("require integer stop_bp >= start_bp")
    period = float(reference_period_bp)
    if not isfinite(period) or period <= 0.0:
        raise ValueError("reference_period_bp must be finite and positive")
    return [
        {
            "spacer_bp": spacer,
            "reference_phase_rad": (2.0 * pi * spacer / period) % (2.0 * pi),
        }
        for spacer in range(start_bp, stop_bp + 1)
    ]
