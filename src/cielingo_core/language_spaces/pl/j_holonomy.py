"""Regional J/Kuramoto holonomy guard for CIELingo 0.5J.

Purpose:
- convert local regional grammar pressures into coherent bounded phase
  components;
- preserve the narrow SurfaceSolution ABI by storing a JSON-compatible
  holonomy report inside local_j;
- prevent ad-hoc J fields from drifting away from Kuramoto-style phase
  coupling.

This is not a physical oscillator runtime. It is a semantic-phase contract.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from math import pi
from typing import Any


ORBITAL_KURAMOTO_FREQUENCY_HZ = 7.83
OMEGA0_RAD_S = 2.0 * pi * ORBITAL_KURAMOTO_FREQUENCY_HZ


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass
class JKuramotoComponent:
    component_id: str
    pressure: float
    phase: float
    coupling: float
    residue: float = 0.0
    notes: list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.component_id:
            issues.append("component_id is required")
        for name in ("pressure", "phase", "coupling", "residue"):
            value = getattr(self, name)
            if not 0.0 <= float(value) <= 1.0:
                issues.append(f"{self.component_id}.{name} must be in [0,1]")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class JKuramotoHolonomyReport:
    schema: str = "CIELINGO_REGIONAL_J_KURAMOTO_HOLONOMY/0.5J"
    frequency_hz: float = ORBITAL_KURAMOTO_FREQUENCY_HZ
    omega0_rad_s: float = OMEGA0_RAD_S
    components: list[JKuramotoComponent] = field(default_factory=list)
    coherence_order_r: float = 0.0
    total_pressure: float = 0.0
    holonomy_warning: bool = False
    source_promotion_allowed: bool = False
    canon_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    notes: list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        issues: list[str] = []
        if abs(self.frequency_hz - ORBITAL_KURAMOTO_FREQUENCY_HZ) > 1e-9:
            issues.append("frequency_hz must remain orbital_kuramoto_frequency_hz=7.83")
        if abs(self.omega0_rad_s - OMEGA0_RAD_S) > 1e-9:
            issues.append("omega0_rad_s must equal 2*pi*7.83")
        for component in self.components:
            issues.extend(component.validate())
        for name in ("coherence_order_r", "total_pressure"):
            if not 0.0 <= float(getattr(self, name)) <= 1.0:
                issues.append(f"{name} must be in [0,1]")
        if self.source_promotion_allowed:
            issues.append("J/Kuramoto holonomy must not promote SOURCE")
        if self.canon_promotion_allowed:
            issues.append("J/Kuramoto holonomy must not promote canon")
        if self.noema_writeback_allowed:
            issues.append("J/Kuramoto holonomy must not write NOEMA")
        if self.current_update_allowed:
            issues.append("J/Kuramoto holonomy must not update CURRENT")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _component(component_id: str, pressure: float, coupling: float, residue: float = 0.0) -> JKuramotoComponent:
    pressure = clamp01(pressure)
    coupling = clamp01(coupling)
    residue = clamp01(residue)
    # Semantic phase is normalized to [0,1]; physical radian phase would be 2π*phase.
    phase = clamp01((pressure * 0.70) + (coupling * 0.20) + (residue * 0.10))
    return JKuramotoComponent(
        component_id=component_id,
        pressure=pressure,
        phase=phase,
        coupling=coupling,
        residue=residue,
        notes=["Semantic Kuramoto component; not physical runtime."],
    )


def build_pl_kuramoto_holonomy(
    *,
    word_order: float,
    case_ambiguity: float,
    negation_scope: float,
    imperative_force: float,
    source_phrase: float,
    preference_signal: float,
    residue_pressure: float,
) -> JKuramotoHolonomyReport:
    """Build a coherent bounded report from PL regional pressures."""

    components = [
        _component("pl_word_order", word_order, 0.35, residue_pressure),
        _component("pl_case_ambiguity", case_ambiguity, 0.55, residue_pressure),
        _component("pl_negation_scope", negation_scope, 0.65, residue_pressure),
        _component("pl_imperative_force", imperative_force, 0.60, residue_pressure),
        _component("pl_source_phrase", source_phrase, 0.75, residue_pressure),
        _component("pl_preference_signal", preference_signal, 0.40, residue_pressure),
    ]

    if components:
        total_pressure = clamp01(sum(c.pressure for c in components) / len(components))
        # Lightweight semantic order parameter: average phase-alignment weight.
        coherence_order_r = clamp01(sum(1.0 - abs(c.phase - total_pressure) for c in components) / len(components))
    else:
        total_pressure = 0.0
        coherence_order_r = 0.0

    report = JKuramotoHolonomyReport(
        components=components,
        coherence_order_r=round(coherence_order_r, 6),
        total_pressure=round(total_pressure, 6),
        holonomy_warning=coherence_order_r < 0.35,
        notes=[
            "orbital_kuramoto_frequency_hz=7.83",
            "omega0_rad_s=2*pi*7.83",
            "Report is semantic-phase guard, not physical oscillator runtime.",
        ],
    )
    return report

def attach_kuramoto_report_to_local_j(local_j: dict[str, float], report: JKuramotoHolonomyReport) -> dict[str, float]:
    """Return a copy of local_j with bounded numeric Kuramoto summary fields only.

    SurfaceSolution.local_j requires every value to be numeric and in [0,1].
    Physical constants such as 7.83 Hz and omega0 remain in the full report,
    which must be carried outside SurfaceSolution, e.g. RegionalSolveResult.notes.
    """
    issues = report.validate()
    if issues:
        raise ValueError("; ".join(issues))

    enriched: dict[str, float] = {k: float(v) for k, v in local_j.items()}
    enriched["J_kuramoto_order_r"] = report.coherence_order_r
    enriched["J_kuramoto_total_pressure"] = report.total_pressure
    enriched["J_holonomy_warning"] = 1.0 if report.holonomy_warning else 0.0
    return enriched
