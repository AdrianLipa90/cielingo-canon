from dataclasses import dataclass
from typing import Iterable, Dict, List

@dataclass(frozen=True)
class MetricFamily:
    family_id: str
    classification: str
    scale_levels: str
    max_residue: float = 0.0

@dataclass(frozen=True)
class AggregationDecision:
    family_id: str
    action: str
    current_runtime_included: bool
    normalized_weight: float

class MetricsNormalizationDoctor:
    """Operator-aware metric aggregation doctor.

    Implements O_I ~= O_0 + delta O_zeta policy:
    exact duplicates become canonical pointers, same-operator variants are
    aggregated inside zeta margin, calibrated variants remain branches,
    and legacy/research datasets are provenance, not current runtime inputs.
    """
    POLICY = {
        "exact_duplicate": ("canonical_pointer_only", False, 0.0),
        "same_operator_zeta_margin": ("normalize_with_zeta_margin", True, 0.35),
        "calibrated_variant": ("preserve_delta_O_zeta_branch", True, 0.75),
        "cross_scale_result": ("cross_reference_only", False, 0.65),
        "legacy_demo_metric": ("exclude_from_current_runtime", False, 0.15),
        "legacy_static_seed": ("seed_only", False, 0.25),
        "legacy_research_dataset": ("provenance_only", False, 0.20),
    }
    def decide(self, family: MetricFamily) -> AggregationDecision:
        action, include, base = self.POLICY.get(family.classification, self.POLICY["cross_scale_result"])
        weight = min(1.0, max(0.0, base + max(0.0, family.max_residue)))
        return AggregationDecision(family.family_id, action, include, weight)
    def aggregate(self, families: Iterable[MetricFamily]) -> Dict[str, object]:
        decisions: List[AggregationDecision] = [self.decide(f) for f in families]
        return {
            "family_count": len(decisions),
            "current_runtime_included": sum(1 for d in decisions if d.current_runtime_included),
            "excluded_or_reference": sum(1 for d in decisions if not d.current_runtime_included),
            "mean_weight": sum(d.normalized_weight for d in decisions) / max(1, len(decisions)),
            "decisions": [d.__dict__ for d in decisions],
        }
