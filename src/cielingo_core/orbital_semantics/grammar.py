"""Orbital-fractal semantic grammar candidate for CIELingo.

Computational representation only. Structural mass, phase, coupling, and holonomy
names are mathematical roles and do not assert physical mass, electromagnetic
Aharonov--Bohm coupling, or a physical gauge field in language.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, IntEnum
import cmath
import math
from typing import Any, Mapping, Sequence

TAU = 2.0 * math.pi
SCHEMA = "CIELINGO_ORBITAL_FRACTAL_GRAMMAR_V0_1"


def wrap_pi(x: float) -> float:
    if not math.isfinite(x):
        raise ValueError("phase must be finite")
    return (float(x) + math.pi) % TAU - math.pi


class OrbitalLevel(IntEnum):
    KAKU = 0
    ORBITAL_CELL = 1
    RADICAL = 2
    CONCEPT = 3
    SENTENCE = 4
    PARAGRAPH = 5
    CHAPTER = 6
    BOOK = 7


class PhaseBranch(str, Enum):
    PLUS = "PLUS"
    MINUS = "MINUS"


@dataclass(frozen=True)
class KakuState:
    kaku_id: str
    symbol: str
    structural_mass: float
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.kaku_id or not self.symbol:
            raise ValueError("kaku_id and symbol are required")
        m = float(self.structural_mass)
        if not math.isfinite(m) or m < 0.0:
            raise ValueError("structural_mass must be finite and non-negative")


@dataclass(frozen=True)
class OrbitalCell:
    cell_id: str
    carrier: KakuState
    base_phase_rad: float
    branch: PhaseBranch = PhaseBranch.PLUS
    lambda_coupling: float = 1.0
    payload: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.cell_id:
            raise ValueError("cell_id is required")
        if not math.isfinite(float(self.base_phase_rad)):
            raise ValueError("base_phase_rad must be finite")
        lam = float(self.lambda_coupling)
        if not math.isfinite(lam) or lam < 0.0:
            raise ValueError("lambda_coupling must be finite and non-negative")

    @property
    def effective_phase_rad(self) -> float:
        sign = 1.0 if self.branch is PhaseBranch.PLUS else -1.0
        return wrap_pi(sign * float(self.base_phase_rad))

    @property
    def amplitude(self) -> complex:
        r = float(self.carrier.structural_mass) * float(self.lambda_coupling)
        return r * cmath.exp(1j * self.effective_phase_rad)

    def conjugate(self, *, cell_id: str | None = None) -> "OrbitalCell":
        """Return the +/-phi conjugate branch. This is NOT counterphase."""
        branch = PhaseBranch.MINUS if self.branch is PhaseBranch.PLUS else PhaseBranch.PLUS
        return OrbitalCell(
            cell_id=cell_id or f"{self.cell_id}:conjugate",
            carrier=self.carrier,
            base_phase_rad=self.base_phase_rad,
            branch=branch,
            lambda_coupling=self.lambda_coupling,
            payload={**dict(self.payload), "transform": "CONJUGATE"},
        )

    def counterphase(self, *, cell_id: str | None = None) -> "OrbitalCell":
        """Return a pi-shifted cell. Counterphase is distinct from conjugation."""
        effective = wrap_pi(self.effective_phase_rad + math.pi)
        return OrbitalCell(
            cell_id=cell_id or f"{self.cell_id}:counterphase",
            carrier=self.carrier,
            base_phase_rad=effective,
            branch=PhaseBranch.PLUS,
            lambda_coupling=self.lambda_coupling,
            payload={**dict(self.payload), "transform": "COUNTERPHASE"},
        )


def dual_cells(
    carrier: KakuState,
    base_phase_rad: float,
    *,
    lambda_coupling: float = 1.0,
    stem: str | None = None,
) -> tuple[OrbitalCell, OrbitalCell]:
    stem = stem or carrier.kaku_id
    plus = OrbitalCell(f"{stem}:chi+", carrier, base_phase_rad, PhaseBranch.PLUS, lambda_coupling)
    minus = OrbitalCell(f"{stem}:chi-", carrier, base_phase_rad, PhaseBranch.MINUS, lambda_coupling)
    return plus, minus


@dataclass(frozen=True)
class MoireReceipt:
    resultant: complex
    resultant_abs: float
    input_power: float
    phase_delta_rad: float
    cancellation_ratio: float


def moire_pair(left: OrbitalCell, right: OrbitalCell) -> MoireReceipt:
    z = left.amplitude + right.amplitude
    power = abs(left.amplitude) ** 2 + abs(right.amplitude) ** 2
    denom = abs(left.amplitude) + abs(right.amplitude)
    ratio = abs(z) / denom if denom else 0.0
    delta = wrap_pi(right.effective_phase_rad - left.effective_phase_rad)
    return MoireReceipt(z, abs(z), power, delta, ratio)


@dataclass(frozen=True)
class LatentPhaseReceipt:
    mean: complex
    mean_abs: float
    second_moment: float
    entropy_bits: float
    count: int


def latent_phase_ensemble(phases_rad: Sequence[float]) -> LatentPhaseReceipt:
    phases = tuple(float(x) for x in phases_rad)
    if not phases:
        raise ValueError("at least one latent phase is required")
    if not all(math.isfinite(x) for x in phases):
        raise ValueError("latent phases must be finite")
    amps = tuple(cmath.exp(1j * x) for x in phases)
    mean = sum(amps, 0j) / len(amps)
    second = sum(abs(z) ** 2 for z in amps) / len(amps)
    return LatentPhaseReceipt(mean, abs(mean), second, math.log2(len(amps)), len(amps))


@dataclass(frozen=True)
class OrbitalUnit:
    unit_id: str
    level: OrbitalLevel
    payload: Mapping[str, Any] = field(default_factory=dict)
    children: tuple["OrbitalUnit", ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.unit_id:
            raise ValueError("unit_id is required")
        if self.level == OrbitalLevel.KAKU and self.children:
            raise ValueError("KAKU is atomic")
        expected = int(self.level) - 1
        for child in self.children:
            if int(child.level) != expected:
                raise ValueError(
                    f"{self.level.name} children must be {OrbitalLevel(expected).name}; "
                    "direct KAKU->RADICAL composition is intentionally rejected"
                )


def assemble_orbital_unit(
    unit_id: str,
    level: OrbitalLevel,
    children: Sequence[OrbitalUnit],
    *,
    payload: Mapping[str, Any] | None = None,
) -> OrbitalUnit:
    return OrbitalUnit(unit_id, level, payload or {}, tuple(children))


@dataclass(frozen=True)
class SemanticConnectionEdge:
    edge_id: str
    phase_potential_rad: float
    lambda_coupling: float = 1.0

    def __post_init__(self) -> None:
        if not self.edge_id:
            raise ValueError("edge_id is required")
        if not math.isfinite(float(self.phase_potential_rad)):
            raise ValueError("phase_potential_rad must be finite")
        lam = float(self.lambda_coupling)
        if not math.isfinite(lam) or lam < 0.0:
            raise ValueError("lambda_coupling must be finite and non-negative")


def phasenav_holonomy_input(edges: Sequence[SemanticConnectionEdge]) -> tuple[float, ...]:
    """Return ONLY U(1) phase potentials for PhaseNav A_sem/W_sem transport."""
    return tuple(float(e.phase_potential_rad) for e in edges)


def lambda_path_gain(edges: Sequence[SemanticConnectionEdge]) -> float:
    """Independent communication/coupling envelope, deliberately outside U(1)."""
    if not edges:
        return 1.0
    out = 1.0
    for edge in edges:
        out *= float(edge.lambda_coupling)
    return out


def path_transport(edges: Sequence[SemanticConnectionEdge]) -> complex:
    theta = math.fsum(phasenav_holonomy_input(edges))
    return lambda_path_gain(edges) * cmath.exp(1j * theta)


__all__ = [
    "SCHEMA", "TAU", "OrbitalLevel", "PhaseBranch", "KakuState", "OrbitalCell",
    "dual_cells", "MoireReceipt", "moire_pair", "LatentPhaseReceipt",
    "latent_phase_ensemble", "OrbitalUnit", "assemble_orbital_unit",
    "SemanticConnectionEdge", "phasenav_holonomy_input", "lambda_path_gain",
    "path_transport", "wrap_pi",
]
