"""Typed CIELingo -> PhaseNav semantic-holonomy handoff candidate."""
from __future__ import annotations

from dataclasses import asdict, dataclass
import math
from typing import Any, Sequence

from .grammar import (
    SCHEMA as ORBITAL_GRAMMAR_SCHEMA,
    SemanticConnectionEdge,
    lambda_path_gain,
    path_transport,
    phasenav_holonomy_input,
)

BRIDGE_SCHEMA = "CIELINGO_PHASENAV_HOLONOMY_HANDOFF_V0_1"


@dataclass(frozen=True)
class PhaseNavHolonomyHandoff:
    path_id: str
    phase_potentials_rad: tuple[float, ...]
    lambda_path_gain: float
    composite_transport_real: float
    composite_transport_imag: float
    source_schema: str = ORBITAL_GRAMMAR_SCHEMA
    schema: str = BRIDGE_SCHEMA
    authority: str = "CANDIDATE_ONLY"
    canon_allowed: bool = False
    physical_gauge_claim: bool = False

    def __post_init__(self) -> None:
        if not self.path_id:
            raise ValueError("path_id is required")
        if not all(math.isfinite(x) for x in self.phase_potentials_rad):
            raise ValueError("phase potentials must be finite")
        if not math.isfinite(self.lambda_path_gain) or self.lambda_path_gain < 0.0:
            raise ValueError("lambda_path_gain must be finite and non-negative")
        if not all(math.isfinite(x) for x in (
            self.composite_transport_real,
            self.composite_transport_imag,
        )):
            raise ValueError("composite transport must be finite")

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_phasenav_handoff(
    path_id: str,
    edges: Sequence[SemanticConnectionEdge],
) -> PhaseNavHolonomyHandoff:
    """Keep U(1) phase input and Lambda amplitude envelope explicitly separate."""
    phases = phasenav_holonomy_input(edges)
    lam = lambda_path_gain(edges)
    transport = path_transport(edges)
    return PhaseNavHolonomyHandoff(
        path_id=path_id,
        phase_potentials_rad=phases,
        lambda_path_gain=lam,
        composite_transport_real=float(transport.real),
        composite_transport_imag=float(transport.imag),
    )


__all__ = ["BRIDGE_SCHEMA", "PhaseNavHolonomyHandoff", "build_phasenav_handoff"]
