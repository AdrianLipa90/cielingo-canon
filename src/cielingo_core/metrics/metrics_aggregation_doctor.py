from __future__ import annotations
from dataclasses import dataclass
from typing import Literal

Decision = Literal[
    "normalize_or_pointer_update",
    "preserve_delta_branch",
    "exclude_runtime_preserve_provenance",
    "run_reference_probe",
    "crossref_only",
]

@dataclass(frozen=True)
class MetricsAggregationFinding:
    region: str
    card_count: int
    family_count: int
    runtime_reference_count: int
    decision: Decision
    doctor_route: str

class MetricsAggregationDoctor:
    def decide_region(self, region: str) -> tuple[Decision, str]:
        if region in {"R_CANONICAL_POINTERS", "R_ZETA_MARGIN_NORMALIZATION"}:
            return "normalize_or_pointer_update", "metrics_normalization_doctor"
        if region == "R_CALIBRATED_VARIANTS":
            return "preserve_delta_branch", "delta_O_zeta_branch"
        if region.startswith("R_LEGACY"):
            return "exclude_runtime_preserve_provenance", "legacy_provenance_quarantine_soft"
        if region.startswith("R_RUNTIME"):
            return "run_reference_probe", "noema_runtime_reference_lane"
        return "crossref_only", "cross_scale_reference_lane"
