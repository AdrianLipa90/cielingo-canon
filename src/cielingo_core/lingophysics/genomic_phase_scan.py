"""Dependency-free phase-period scan for genomic spacing experiments.

This is a screening statistic, not a causal test. It compares a linear-spacing
baseline against a baseline plus sinusoidal phase terms for candidate periods.
Held-out validation and biological controls remain mandatory.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, hypot, isfinite, sin, tau
from typing import Iterable, Sequence

SCHEMA = "CIELINGO_GENOMIC_PHASE_SCAN_V0_1"


@dataclass(frozen=True)
class SpacingObservation:
    spacing_bp: float
    response: float

    def __post_init__(self) -> None:
        if not isfinite(float(self.spacing_bp)) or not isfinite(float(self.response)):
            raise ValueError("spacing and response must be finite")


@dataclass(frozen=True)
class PeriodFit:
    period_bp: float
    baseline_sse: float
    phase_sse: float
    incremental_r2: float
    amplitude: float
    phase_offset_rad: float
    coefficients: tuple[float, ...]

    def to_dict(self) -> dict[str, float | list[float]]:
        return {
            "period_bp": self.period_bp,
            "baseline_sse": self.baseline_sse,
            "phase_sse": self.phase_sse,
            "incremental_r2": self.incremental_r2,
            "amplitude": self.amplitude,
            "phase_offset_rad": self.phase_offset_rad,
            "coefficients": list(self.coefficients),
        }


def _solve(a: list[list[float]], b: list[float]) -> list[float]:
    n = len(b)
    m = [list(row) + [float(rhs)] for row, rhs in zip(a, b)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[pivot][col]) < 1e-12:
            raise ValueError("singular design matrix")
        m[col], m[pivot] = m[pivot], m[col]
        scale = m[col][col]
        m[col] = [x / scale for x in m[col]]
        for row in range(n):
            if row == col:
                continue
            factor = m[row][col]
            m[row] = [x - factor * y for x, y in zip(m[row], m[col])]
    return [m[i][-1] for i in range(n)]


def _ols(design: Sequence[Sequence[float]], y: Sequence[float]) -> tuple[list[float], float]:
    if len(design) != len(y) or not y:
        raise ValueError("design and response must be non-empty and aligned")
    width = len(design[0])
    if width == 0 or any(len(row) != width for row in design):
        raise ValueError("invalid design matrix")
    xtx = [[0.0] * width for _ in range(width)]
    xty = [0.0] * width
    for row, target in zip(design, y):
        for i in range(width):
            xty[i] += row[i] * target
            for j in range(width):
                xtx[i][j] += row[i] * row[j]
    beta = _solve(xtx, xty)
    residuals = [target - sum(c * x for c, x in zip(beta, row)) for row, target in zip(design, y)]
    return beta, sum(r * r for r in residuals)


def fit_period(observations: Sequence[SpacingObservation], period_bp: float) -> PeriodFit:
    if len(observations) < 6:
        raise ValueError("at least six observations are required")
    if not isfinite(float(period_bp)) or period_bp <= 0:
        raise ValueError("period_bp must be finite and > 0")
    x = [float(o.spacing_bp) for o in observations]
    y = [float(o.response) for o in observations]
    baseline = [[1.0, d] for d in x]
    _, baseline_sse = _ols(baseline, y)
    phase_design = [
        [1.0, d, cos(tau * d / period_bp), sin(tau * d / period_bp)]
        for d in x
    ]
    beta, phase_sse = _ols(phase_design, y)
    if baseline_sse <= 1e-15:
        incremental_r2 = 0.0 if phase_sse <= 1e-15 else float("-inf")
    else:
        incremental_r2 = 1.0 - phase_sse / baseline_sse
    c, s = beta[2], beta[3]
    return PeriodFit(
        period_bp=float(period_bp),
        baseline_sse=baseline_sse,
        phase_sse=phase_sse,
        incremental_r2=incremental_r2,
        amplitude=hypot(c, s),
        phase_offset_rad=atan2(-s, c),
        coefficients=tuple(beta),
    )


def scan_periods(
    observations: Sequence[SpacingObservation],
    periods_bp: Iterable[float],
) -> list[PeriodFit]:
    fits = [fit_period(observations, float(period)) for period in periods_bp]
    if not fits:
        raise ValueError("period scan requires at least one candidate period")
    return sorted(fits, key=lambda fit: (fit.phase_sse, -fit.incremental_r2, fit.period_bp))


def regular_period_grid(start_bp: float = 8.0, stop_bp: float = 13.0, step_bp: float = 0.05) -> list[float]:
    if step_bp <= 0 or stop_bp < start_bp:
        raise ValueError("invalid period grid")
    count = int(round((stop_bp - start_bp) / step_bp))
    return [start_bp + i * step_bp for i in range(count + 1)]
