"""Minimal dependency-free diagnostics for representation ablations."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence


@dataclass(frozen=True)
class LabeledFeatures:
    sample_id: str
    label: str
    features: Mapping[str, float]

    def __post_init__(self) -> None:
        if not self.sample_id.strip() or not self.label.strip():
            raise ValueError("sample_id and label must be non-empty")


def _distance(
    left: Mapping[str, float],
    right: Mapping[str, float],
) -> float:
    keys = set(left) | set(right)
    return math.sqrt(
        sum(
            (float(left.get(key, 0.0)) - float(right.get(key, 0.0))) ** 2
            for key in keys
        )
    )


def leave_one_out_nearest_neighbor(
    samples: Sequence[LabeledFeatures],
) -> dict[str, object]:
    """Dependency-free diagnostic, not a biological validation metric."""

    if len(samples) < 2:
        raise ValueError("at least two samples are required")
    if len({sample.sample_id for sample in samples}) != len(samples):
        raise ValueError("sample_id values must be unique")

    predictions: list[dict[str, object]] = []
    correct = 0
    for index, sample in enumerate(samples):
        candidates = [
            other
            for other_index, other in enumerate(samples)
            if other_index != index
        ]
        nearest = min(
            candidates,
            key=lambda other: (
                _distance(sample.features, other.features),
                other.sample_id,
            ),
        )
        distance = _distance(sample.features, nearest.features)
        predictions.append(
            {
                "sample_id": sample.sample_id,
                "true_label": sample.label,
                "predicted_label": nearest.label,
                "nearest_sample_id": nearest.sample_id,
                "distance": distance,
            }
        )
        correct += int(nearest.label == sample.label)

    return {
        "schema": "CIELINGO_GENOMIC_REPRESENTATION_BENCH_V0_1",
        "method": "LEAVE_ONE_OUT_1NN_DIAGNOSTIC",
        "accuracy": correct / len(samples),
        "n": len(samples),
        "predictions": predictions,
        "claim_scope": "representation diagnostic only; not biological validation",
    }


def compare_feature_sets(
    feature_sets: Mapping[str, Sequence[LabeledFeatures]],
) -> dict[str, object]:
    if not feature_sets:
        raise ValueError("feature_sets must be non-empty")
    results = {
        name: leave_one_out_nearest_neighbor(samples)
        for name, samples in sorted(feature_sets.items())
    }
    return {
        "schema": "CIELINGO_GENOMIC_REPRESENTATION_COMPARISON_V0_1",
        "results": results,
        "winner_declared": False,
        "interpretation_required": True,
    }
