"""Polish J components v0.2.

Maps PL surface diagnostics into bounded scalar J components. These are not
physical Kuramoto measurements.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any


@dataclass(frozen=True)
class PolishJComponent:
    key: str
    value: float
    evidence: str
    limitation: str = "j_component_not_physical_measurement"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def compute_polish_j_components(
    *,
    case_hint_count: int = 0,
    role_candidate_count: int = 0,
    negation_count: int = 0,
    imperative_count: int = 0,
    source_count: int = 0,
    canon_count: int = 0,
) -> dict[str, float]:
    """Return bounded scalar local_j candidates."""
    return {
        "pl_case_hint_density": clamp01(case_hint_count / 6.0),
        "pl_role_candidate_density": clamp01(role_candidate_count / 8.0),
        "pl_negation_scope_pressure": clamp01(negation_count / 3.0),
        "pl_imperative_force_pressure": clamp01(imperative_count / 3.0),
        "pl_source_phrase_pressure": clamp01(source_count / 3.0),
        "pl_canon_phrase_pressure": clamp01(canon_count / 3.0),
    }


def polish_j_components_to_notes(components: dict[str, float]) -> list[dict[str, Any]]:
    return [
        {
            "kind": "polish_j_component",
            "key": key,
            "value": value,
            "limitation": "j_component_not_physical_kuramoto_measurement",
        }
        for key, value in sorted(components.items())
    ]
