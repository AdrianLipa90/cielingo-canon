from __future__ import annotations

import math
from typing import Sequence


def euclidean_distance(a: Sequence[float], b: Sequence[float]) -> float:
    if len(a) != len(b):
        raise ValueError("vectors must have equal length")
    return math.sqrt(sum((x-y)**2 for x, y in zip(a, b)))


def grammar_curvature_seed(vector: Sequence[float]) -> float:
    if not vector:
        return 0.0
    mean = sum(vector) / len(vector)
    return math.sqrt(sum((x - mean) ** 2 for x in vector) / len(vector))


def cross_language_compatible(distance: float, epsilon_cross: float = 0.75) -> bool:
    return distance < epsilon_cross


TAU = 2.0 * math.pi


def wrapped_phase_delta(a: float, b: float) -> float:
    """Shortest signed angular displacement b-a in [-pi, pi)."""
    left = float(a)
    right = float(b)
    if not math.isfinite(left) or not math.isfinite(right):
        raise ValueError("phases must be finite")
    return (right - left + math.pi) % TAU - math.pi


def circular_phase_distance(a: Sequence[float], b: Sequence[float]) -> float:
    """RMS distance on S1 coordinates; use instead of Euclidean phase distance."""
    if len(a) != len(b):
        raise ValueError("phase vectors must have equal length")
    if not a:
        return 0.0
    deltas = [wrapped_phase_delta(x, y) for x, y in zip(a, b)]
    return math.sqrt(sum(d*d for d in deltas) / len(deltas))


def orbital_cell_distance(
    left: Sequence[float],
    right: Sequence[float],
    *,
    weights: Sequence[float] = (1.0, 1.0, 1.0),
) -> float:
    """Distance for (structural_mass, phase, lambda) candidate coordinates.

    The phase coordinate is circular; mass and Lambda remain ordinary scalar
    coordinates. This is a computational metric, not a physical line element.
    """
    if len(left) != 3 or len(right) != 3:
        raise ValueError("orbital cell coordinates must be (mass, phase, lambda)")
    if len(weights) != 3:
        raise ValueError("weights must contain three values")
    w = [float(x) for x in weights]
    if any((not math.isfinite(x) or x < 0.0) for x in w) or sum(w) <= 0.0:
        raise ValueError("weights must be finite, non-negative, and non-zero")

    dm = float(right[0]) - float(left[0])
    dp = wrapped_phase_delta(float(left[1]), float(right[1]))
    dl = float(right[2]) - float(left[2])
    if not all(math.isfinite(x) for x in (dm, dp, dl)):
        raise ValueError("orbital coordinates must be finite")
    components = (dm, dp, dl)
    return math.sqrt(sum(weight*x*x for weight, x in zip(w, components)) / sum(w))
