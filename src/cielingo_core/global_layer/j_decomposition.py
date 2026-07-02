"""GLOBAL 0.5C J decomposition scaffold.

This module formalizes J as a decomposition of pressures/charges.
It is not a proof engine and never grants SOURCE or canon.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any

from .contracts import SourceBindingType


class PhaseBand(str, Enum):
    BIF = "BIF"
    CRYS = "CRYS"
    MANI = "MANI"
    OTHER = "OTHER"
    UNKNOWN = "UNKNOWN"


def _bounded01(value: float) -> bool:
    return 0.0 <= float(value) <= 1.0


@dataclass
class JDecomposition:
    baseline_charge: float = 0.0
    harmonic_correction: float = 0.0
    closure_penalty: float = 0.0
    residue_pressure: float = 0.0
    source_pressure: float = 0.0
    consent_pressure: float = 0.0
    phase_band: PhaseBand | None = None
    source_binding: SourceBindingType = SourceBindingType.HYPOTHESIS
    canon_allowed: bool = False
    notes: list[str] | None = None

    @property
    def total_j(self) -> float:
        return round(
            self.baseline_charge
            + self.harmonic_correction
            + self.closure_penalty
            + self.residue_pressure
            + self.source_pressure
            + self.consent_pressure,
            6,
        )

    def validate(self) -> list[str]:
        issues: list[str] = []
        for name in (
            "baseline_charge",
            "harmonic_correction",
            "closure_penalty",
            "residue_pressure",
            "source_pressure",
            "consent_pressure",
        ):
            if not _bounded01(getattr(self, name)):
                issues.append(f"{name} must be in [0, 1]")
        if self.source_binding == SourceBindingType.SOURCE:
            issues.append("JDecomposition must not grant SOURCE")
        if self.canon_allowed:
            issues.append("JDecomposition must not grant canon")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def classify_phase_band_from_pressure(total_j: float) -> PhaseBand:
    """Contract classifier only. It is not mathematical proof."""
    if total_j < 0.20:
        return PhaseBand.BIF
    if total_j < 0.50:
        return PhaseBand.CRYS
    if total_j < 0.80:
        return PhaseBand.MANI
    return PhaseBand.OTHER


def build_j_decomposition(
    *,
    baseline_charge: float = 0.0,
    harmonic_correction: float = 0.0,
    closure_penalty: float = 0.0,
    residue_pressure: float = 0.0,
    source_pressure: float = 0.0,
    consent_pressure: float = 0.0,
) -> JDecomposition:
    jd = JDecomposition(
        baseline_charge=baseline_charge,
        harmonic_correction=harmonic_correction,
        closure_penalty=closure_penalty,
        residue_pressure=residue_pressure,
        source_pressure=source_pressure,
        consent_pressure=consent_pressure,
        canon_allowed=False,
        source_binding=SourceBindingType.HYPOTHESIS,
    )
    jd.phase_band = classify_phase_band_from_pressure(min(1.0, jd.total_j))
    return jd
