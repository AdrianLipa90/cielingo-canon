"""Global lingophysical algorithm v0.1.

This module establishes the language-independent algorithmic layer:

- words are slots or operators,
- grammar binds operators,
- sentence is an equation over slots/operators,
- language is a regional solver,
- meaning is relational solution plus residue.

The implementation here is intentionally small: it provides a deterministic
contract-level computation for phase 1, not a full natural-language parser.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .contracts import (
    AlignmentResidue,
    ApocalypOSLinguisticSignal,
    HolonomicJReport,
    MeaningEquation,
    SourceBindingType,
    SurfaceSolution,
    UniversalOperatorType,
    UniversalRole,
)


@dataclass
class LingophysicalState:
    """Normalized global state emitted by the algorithm."""

    equation: MeaningEquation
    surface_solutions: list[SurfaceSolution] = field(default_factory=list)
    residues: list[AlignmentResidue] = field(default_factory=list)
    j_report: HolonomicJReport | None = None
    signal: ApocalypOSLinguisticSignal | None = None
    notes: list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        issues: list[str] = []
        issues.extend(self.equation.validate())
        for sol in self.surface_solutions:
            issues.extend(sol.validate())
        for residue in self.residues:
            issues.extend(residue.validate())
        if self.j_report is not None:
            issues.extend(self.j_report.validate())
        if self.signal is not None:
            issues.extend(self.signal.validate())
        return issues


def collect_operator_flags(equation: MeaningEquation) -> dict[str, bool]:
    """Collapse universal operators into runtime-relevant flags."""

    types = {operator.operator_type for operator in equation.operators}
    return {
        "negated": UniversalOperatorType.NEGATION in types,
        "question": UniversalOperatorType.QUESTION in types,
        "source_required": UniversalOperatorType.SOURCE_REQUIRED in types,
        "canon_block": UniversalOperatorType.CANON_BLOCK in types,
        "consent_required": UniversalOperatorType.CONSENT_REQUIRED in types,
        "action_request": UniversalOperatorType.ACTION_REQUEST in types,
        "refusal": UniversalOperatorType.REFUSAL in types,
        "pause": UniversalOperatorType.PAUSE in types,
        "simulation_boundary": UniversalOperatorType.SIMULATION_BOUNDARY in types,
        "uncertainty": UniversalOperatorType.UNCERTAINTY in types,
    }


def compute_global_structure_j(equation: MeaningEquation) -> float:
    """Compute simple structural pressure of a global equation.

    High when predicate or core roles are missing. This is not regional
    grammar; it only checks the equation skeleton.
    """

    pressure = 0.0
    if equation.predicate_slot is None:
        pressure += 0.35
    if not equation.roles:
        pressure += 0.30
    if UniversalRole.PATIENT not in equation.roles and UniversalRole.THEME not in equation.roles:
        pressure += 0.10
    if equation.source_binding == SourceBindingType.UNKNOWN:
        pressure += 0.15
    return min(1.0, pressure)


def compute_residue_j(residues: list[AlignmentResidue]) -> float:
    """Aggregate preserved residue without treating it as error."""

    if not residues:
        return 0.0
    return min(1.0, sum(r.j_weight for r in residues) / max(1, len(residues)))


def compute_surface_j(surface_solutions: list[SurfaceSolution]) -> tuple[float, dict[str, dict[str, float]]]:
    """Aggregate surface/local J while preserving local language components."""

    if not surface_solutions:
        return 0.0, {}
    local_components: dict[str, dict[str, float]] = {}
    total = 0.0
    count = 0
    for sol in surface_solutions:
        local_components[sol.language_id] = dict(sol.local_j)
        for value in sol.local_j.values():
            total += float(value)
            count += 1
    surface_j = min(1.0, total / max(1, count))
    return surface_j, local_components


def compute_holonomic_j(
    equation: MeaningEquation,
    surface_solutions: list[SurfaceSolution] | None = None,
    residues: list[AlignmentResidue] | None = None,
) -> HolonomicJReport:
    """Compute global J report from equation + regional solutions.

    Local components are included but not overwritten or normalized away.
    """

    surface_solutions = surface_solutions or []
    residues = residues or []
    flags = collect_operator_flags(equation)
    J_surface, local_components = compute_surface_j(surface_solutions)

    return HolonomicJReport(
        J_global_structure=compute_global_structure_j(equation),
        J_slot_alignment=0.0,
        J_residue=compute_residue_j(residues),
        J_source=0.7 if flags["source_required"] else 0.0,
        J_canon=0.8 if flags["canon_block"] else 0.0,
        J_consent=0.6 if flags["consent_required"] or flags["action_request"] else 0.0,
        J_surface=J_surface,
        local_components=local_components,
    )


def recommend_mode(j_report: HolonomicJReport, flags: dict[str, bool]) -> str:
    """Derive a conservative ApocalypOS-facing recommendation."""

    if flags["refusal"] or flags["pause"]:
        return "hold"
    if j_report.J_source >= 0.7 and j_report.J_canon >= 0.8:
        return "hold"
    if j_report.J_total >= 2.2:
        return "safe"
    if j_report.J_total >= 1.2:
        return "hold"
    return "standard"


def build_signal(
    equation: MeaningEquation,
    j_report: HolonomicJReport,
    residues: list[AlignmentResidue] | None = None,
    unresolved_slots: list[int] | None = None,
    in_blanco_slots: list[int] | None = None,
) -> ApocalypOSLinguisticSignal:
    """Build runtime signal. It is not execution."""

    residues = residues or []
    unresolved_slots = unresolved_slots or []
    in_blanco_slots = in_blanco_slots or []
    flags = collect_operator_flags(equation)

    J_lingo = min(1.0, j_report.J_total / 3.0)
    return ApocalypOSLinguisticSignal(
        equation_id=equation.equation_id,
        J_lingo=J_lingo,
        source_required=flags["source_required"],
        canon_allowed=False,
        consent_pressure=0.6 if flags["consent_required"] or flags["action_request"] else 0.0,
        residue_count=len(residues),
        unresolved_slots=unresolved_slots,
        in_blanco_slots=in_blanco_slots,
        recommended_mode=recommend_mode(j_report, flags),
        notes=[
            "GLOBAL signal only; no runtime execution.",
            "SOURCE and canon are never granted by default.",
        ],
    )


def run_global_lingophysics(
    equation: MeaningEquation,
    surface_solutions: list[SurfaceSolution] | None = None,
    residues: list[AlignmentResidue] | None = None,
    unresolved_slots: list[int] | None = None,
    in_blanco_slots: list[int] | None = None,
) -> LingophysicalState:
    """Run the phase-1 global algorithm over a prepared equation."""

    surface_solutions = surface_solutions or []
    residues = residues or []
    j_report = compute_holonomic_j(equation, surface_solutions, residues)
    signal = build_signal(equation, j_report, residues, unresolved_slots, in_blanco_slots)
    state = LingophysicalState(
        equation=equation,
        surface_solutions=surface_solutions,
        residues=residues,
        j_report=j_report,
        signal=signal,
        notes=[
            "Sentence treated as relational equation.",
            "Regional surface solvers are outside GLOBAL.",
        ],
    )
    return state
