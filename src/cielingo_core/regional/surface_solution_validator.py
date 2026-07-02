from __future__ import annotations
from dataclasses import asdict, dataclass, field
from typing import Any
from cielingo_core.global_layer.contracts import SurfaceSolution

@dataclass
class SurfaceSolutionValidationReport:
    ok: bool
    language_id: str
    issues: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    def to_dict(self) -> dict[str, Any]: return asdict(self)

def validate_surface_solution(solution: SurfaceSolution) -> SurfaceSolutionValidationReport:
    issues = list(solution.validate())
    warnings = []
    n = len(solution.tokens)
    for slot_id, indices in solution.slot_projection.items():
        for idx in indices:
            if idx < 0 or idx >= n:
                issues.append(f"slot {slot_id} token index out of range: {idx}")
    if not solution.tokens: warnings.append("surface solution has no tokens")
    if not solution.slot_projection: warnings.append("surface solution has no slot projections")
    if solution.confidence < 0.25: warnings.append("low regional confidence")
    return SurfaceSolutionValidationReport(ok=not issues, language_id=solution.language_id, issues=issues, warnings=warnings)
