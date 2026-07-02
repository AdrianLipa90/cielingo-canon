"""
Intention / Information Operator normalization for CIELingo / ApocalypOS / NOEMA.

Purpose
-------
Represent a metric family as an operator approximation:

    O_I ~= O_0 + delta O_zeta

where O_0 is the stable baseline operator and delta O_zeta is a bounded
zeta-information fluctuation branch. This is used to classify duplicate,
near-duplicate and calibrated-variant metrics without destroying provenance.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from enum import Enum
from math import tanh
from typing import Dict, Iterable, List, Optional


class MetricClass(str, Enum):
    EXACT_DUPLICATE = "exact_duplicate"
    SAME_OPERATOR_ZETA_MARGIN = "same_operator_zeta_margin"
    CALIBRATED_VARIANT = "calibrated_variant"
    LEGACY_STATIC_SEED = "legacy_static_seed"
    LEGACY_RESEARCH_DATASET = "legacy_research_dataset"
    DIVERGENT_OPERATOR = "divergent_operator"


@dataclass(frozen=True)
class OperatorApproximationResult:
    file_a: str
    file_b: Optional[str]
    classification: MetricClass
    baseline_operator: str
    fluctuation_operator: str
    max_abs_diff: float
    zeta_margin: float
    normalized_residue: float
    doctor_action: str
    canonical_pointer: str
    preserve: bool

    def to_dict(self) -> Dict[str, object]:
        d = asdict(self)
        d["classification"] = self.classification.value
        return d


def heisenberg_schrodinger_softclip(x: float, bound: float = 1.0) -> float:
    """Smooth limiter: linear near zero, bounded near +/- bound."""
    if bound <= 0:
        bound = 1.0
    return bound * tanh(x / bound)


def zeta_information_margin(max_abs_diff: float, scale: float = 1e-6) -> float:
    """Return a bounded fluctuation envelope for metric equivalence.

    For demo metrics, differences below ~1e-6 are treated as small zeta-level
    fluctuations rather than separate operators. The output is dimensionless.
    """
    return abs(heisenberg_schrodinger_softclip(max_abs_diff / max(scale, 1e-15), 1.0))


def classify_metric_pair(
    file_a: str,
    file_b: str,
    max_abs_diff: float,
    canonical_pointer: str,
    calibrated_threshold: float = 1e-6,
    same_operator_threshold: float = 1e-8,
) -> OperatorApproximationResult:
    """Classify metric pair using O_I ~= O_0 + delta O_zeta."""
    margin = zeta_information_margin(max_abs_diff)
    if max_abs_diff == 0:
        klass = MetricClass.EXACT_DUPLICATE
        action = "merge_by_canonical_pointer"
        preserve = False
    elif max_abs_diff <= same_operator_threshold:
        klass = MetricClass.SAME_OPERATOR_ZETA_MARGIN
        action = "normalize_as_same_operator_with_zeta_margin"
        preserve = False
    elif max_abs_diff <= calibrated_threshold:
        klass = MetricClass.CALIBRATED_VARIANT
        action = "preserve_as_delta_O_zeta_branch"
        preserve = True
    else:
        klass = MetricClass.DIVERGENT_OPERATOR
        action = "do_not_merge_manual_review"
        preserve = True
    return OperatorApproximationResult(
        file_a=file_a,
        file_b=file_b,
        classification=klass,
        baseline_operator="O_0",
        fluctuation_operator="delta_O_zeta",
        max_abs_diff=float(max_abs_diff),
        zeta_margin=float(margin),
        normalized_residue=float(max_abs_diff / max(calibrated_threshold, 1e-15)),
        doctor_action=action,
        canonical_pointer=canonical_pointer,
        preserve=preserve,
    )


def classify_legacy_file(file_path: str, reason: str) -> OperatorApproximationResult:
    return OperatorApproximationResult(
        file_a=file_path,
        file_b=None,
        classification=MetricClass.LEGACY_STATIC_SEED,
        baseline_operator="O_legacy_seed",
        fluctuation_operator="delta_O_zeta_not_current_runtime",
        max_abs_diff=0.0,
        zeta_margin=0.0,
        normalized_residue=0.0,
        doctor_action=f"tag_legacy_exclude_from_current_runtime_aggregation: {reason}",
        canonical_pointer=file_path,
        preserve=True,
    )
