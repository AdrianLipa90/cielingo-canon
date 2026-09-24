"""Candidate orbital-fractal semantic grammar for CIELingo.

This module introduces an explicit layer between atomic surface symbols (KAKU)
and RADICAL states:

    KAKU -> ORBITAL_CELL chi -> RADICAL -> CONCEPT -> SENTENCE

The representation is computational and epistemically candidate-only.  Physical
terms (mass, phase, holonomy, moire) name mathematical roles and do not assert
that linguistic objects literally carry physical mass or electromagnetic gauge
fields.

Key distinction:
- conjugate channel: theta -> -theta
- antiphase channel: theta -> theta + pi
These coincide only at special phases and MUST NOT be conflated.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
import cmath
import hashlib
import json
import math
import unicodedata
from typing import Any, Iterable, Sequence

SCHEMA = "CIELINGO_ORBITAL_FRACTAL_SEMANTICS_V0_1"
VERSION = "0.1.0"
EPISTEMIC = "CANDIDATE_ONLY"

TAU = 2.0 * math.pi

class DualMode(str, Enum):
    CONJUGATE = "CONJUGATE"
    ANTIPHASE = "ANTIPHASE"

class SurfaceKind(str, Enum):
    CONSONANT = "CONSONANT"
    VOWEL = "VOWEL"
    OTHER = "OTHER"
    LATENT = "LATENT"

def wrap_phase(theta: float) -> float:
    if not math.isfinite(float(theta)):
        raise ValueError("phase must be finite")
    return (float(theta) + math.pi) % TAU - math.pi

def dual_phase(theta: float, mode: DualMode) -> tuple[float, float]:
    theta = wrap_phase(theta)
    if mode == DualMode.CONJUGATE:
        return theta, wrap_phase(-theta)
    if mode == DualMode.ANTIPHASE:
        return theta, wrap_phase(theta + math.pi)
    raise ValueError(f"unsupported dual mode: {mode}")

def phase_carrier(theta: float) -> complex:
    return cmath.exp(1j * wrap_phase(theta))

@dataclass(frozen=True)
class KakuUnit:
    """Atomic explicit surface unit.

    surface_structural_mass is a computational surface weight. For the Hebrew codec below it is
    derived from canonical gematria values, but it is not claimed to be
    physical mass.
    """
    symbol: str
    surface_structural_mass: float
    kind: SurfaceKind = SurfaceKind.OTHER
    raw_value: float | None = None

    def __post_init__(self) -> None:
        if not self.symbol:
            raise ValueError("KAKU symbol must be non-empty")
        if not math.isfinite(float(self.surface_structural_mass)) or self.surface_structural_mass < 0:
            raise ValueError("surface_structural_mass must be finite and >= 0")
    
    @property
    def scalar_mass(self) -> float:
        """Backward-readable alias; semantically this is surface_structural_mass."""
        return self.surface_structural_mass

@dataclass(frozen=True)
class OrbitalCell:
    """chi: explicit carrier between KAKU and RADICAL."""

    kaku: KakuUnit
    communication_lambda: float
    phase: float
    channel: int = 1
    latent: bool = False

    def __post_init__(self) -> None:
        if not math.isfinite(float(self.communication_lambda)):
            raise ValueError("communication_lambda must be finite")
        if self.communication_lambda < 0:
            raise ValueError("communication_lambda must be >= 0")
        if self.channel not in (-1, 1):
            raise ValueError("channel must be -1 or +1")
        wrap_phase(self.phase)

    @property
    def amplitude(self) -> complex:
        return (
            self.kaku.surface_structural_mass
            * self.communication_lambda
            * cmath.exp(1j * self.channel * wrap_phase(self.phase))
        )

    def dual(self, mode: DualMode) -> "OrbitalCell":
        p, q = dual_phase(self.phase, mode)
        target = q if abs(wrap_phase(p - self.phase)) < 1e-12 else p
        # amplitude channel remains explicit; target phase carries the dual.
        return OrbitalCell(
            kaku=self.kaku,
            communication_lambda=self.communication_lambda,
            phase=target,
            channel=self.channel,
            latent=self.latent,
        )

@dataclass(frozen=True)
class RadicalState:
    """Ordered bound state of chi cells."""

    radical_id: str
    cells: tuple[OrbitalCell, ...]
    source_language: str | None = None

    def __post_init__(self) -> None:
        if not self.radical_id:
            raise ValueError("radical_id must be non-empty")
        if not self.cells:
            raise ValueError("radical requires at least one orbital cell")

    @property
    def structural_mass(self) -> float:
        return math.fsum(c.kaku.surface_structural_mass for c in self.cells)

    @property
    def ordered_phase_moment(self) -> float:
        denom = max(1.0, math.fsum(c.kaku.surface_structural_mass for c in self.cells))
        return wrap_phase(
            math.fsum((i + 1) * c.kaku.surface_structural_mass * c.channel * c.phase
                      for i, c in enumerate(self.cells)) / denom
        )

    @property
    def carrier(self) -> complex:
        # Order is retained separately in ordered_phase_moment. The complex
        # carrier is intentionally a bounded weighted resultant.
        weights = [max(1e-15, c.kaku.surface_structural_mass * c.communication_lambda) for c in self.cells]
        z = sum(w * cmath.exp(1j * c.channel * c.phase) for w, c in zip(weights, self.cells))
        return z / math.fsum(weights)

@dataclass(frozen=True)
class ConceptState:
    concept_id: str
    radical: RadicalState
    morphology_phase: float = 0.0
    communication_lambda: float = 1.0
    gloss: str | None = None

    def __post_init__(self) -> None:
        if not self.concept_id:
            raise ValueError("concept_id must be non-empty")
        if not math.isfinite(float(self.communication_lambda)) or self.communication_lambda < 0:
            raise ValueError("communication_lambda must be finite and >= 0")
        wrap_phase(self.morphology_phase)

    @property
    def amplitude(self) -> complex:
        return (
            self.communication_lambda
            * self.radical.carrier
            * cmath.exp(1j * wrap_phase(self.morphology_phase))
        )

@dataclass(frozen=True)
class RelationEdge:
    source: str
    relation: str
    target: str
    edge_potential: float
    communication_lambda: float = 1.0

    def __post_init__(self) -> None:
        if not self.source or not self.target or not self.relation:
            raise ValueError("relation edge requires source/relation/target")
        wrap_phase(self.edge_potential)
        if not math.isfinite(float(self.communication_lambda)) or self.communication_lambda < 0:
            raise ValueError("communication_lambda must be finite and >= 0")

@dataclass(frozen=True)
class SentenceOrbit:
    sentence_id: str
    concepts: tuple[ConceptState, ...]
    relations: tuple[RelationEdge, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.sentence_id:
            raise ValueError("sentence_id must be non-empty")
        ids = [c.concept_id for c in self.concepts]
        if len(ids) != len(set(ids)):
            raise ValueError("concept ids must be unique within sentence orbit")
        known = set(ids)
        for e in self.relations:
            if e.source not in known or e.target not in known:
                raise ValueError("relation endpoint outside sentence concepts")

    @property
    def edge_potentials(self) -> tuple[float, ...]:
        """PhaseNav-compatible A_sem edge-potential packet."""
        return tuple(e.edge_potential for e in self.relations)

    @property
    def holonomy(self) -> complex:
        """Discrete U(1)-style transport exp(i sum A_e).

        This mirrors the interface expected by PhaseNav semantic_holonomy.py,
        without importing PhaseNav or asserting a physical gauge field.
        """
        return cmath.exp(1j * math.fsum(self.edge_potentials))

    @property
    def lexical_field(self) -> complex:
        if not self.concepts:
            return 0j
        return sum((i + 1) * c.amplitude for i, c in enumerate(self.concepts)) / math.fsum(
            range(1, len(self.concepts) + 1)
        )

    @property
    def relational_field(self) -> complex:
        if not self.relations:
            return 0j
        z = 0j
        denom = 0.0
        by_id = {c.concept_id: c for c in self.concepts}
        for e in self.relations:
            w = max(1e-15, e.communication_lambda)
            z += w * by_id[e.source].amplitude.conjugate() * by_id[e.target].amplitude * cmath.exp(1j * e.edge_potential)
            denom += w
        return z / denom

    @property
    def moire_state(self) -> complex:
        return self.lexical_field + self.relational_field

def moire_envelope(left: Sequence[complex], right: Sequence[complex]) -> tuple[float, ...]:
    if len(left) != len(right):
        raise ValueError("moire lattices must have equal length")
    out: list[float] = []
    for a, b in zip(left, right):
        denom = abs(a) + abs(b)
        out.append(0.0 if denom == 0 else abs(a + b) / denom)
    return tuple(out)

def latent_phase_ensemble(phases: Iterable[float]) -> dict[str, float]:
    vals = tuple(phase_carrier(p) for p in phases)
    if not vals:
        raise ValueError("latent phase ensemble must be non-empty")
    mean = sum(vals) / len(vals)
    second = math.fsum(abs(v) ** 2 for v in vals) / len(vals)
    entropy = math.log2(len(vals))
    return {
        "mean_real": float(mean.real),
        "mean_imag": float(mean.imag),
        "mean_abs": float(abs(mean)),
        "second_moment": float(second),
        "support_entropy_bits": float(entropy),
    }

# --- Hebrew codec ---------------------------------------------------------

HEBREW_GEMATRIA: dict[str, int] = {
    "א": 1, "ב": 2, "ג": 3, "ד": 4, "ה": 5, "ו": 6, "ז": 7, "ח": 8, "ט": 9,
    "י": 10, "כ": 20, "ך": 20, "ל": 30, "מ": 40, "ם": 40, "נ": 50, "ן": 50,
    "ס": 60, "ע": 70, "פ": 80, "ף": 80, "צ": 90, "ץ": 90, "ק": 100,
    "ר": 200, "ש": 300, "ת": 400,
}
HEBREW_FINAL_NORMALIZATION = {"ך": "כ", "ם": "מ", "ן": "נ", "ף": "פ", "ץ": "צ"}

# Candidate computational coordinates for common niqqud classes. These are
# NOT claims of traditional numeric values or physical phases.
_NIQQUD_ORDER = (
    "\u05b0", "\u05b1", "\u05b2", "\u05b3", "\u05b4", "\u05b5", "\u05b6",
    "\u05b7", "\u05b8", "\u05b9", "\u05ba", "\u05bb", "\u05bc",
)
HEBREW_NIQQUD_PHASE = {
    mark: wrap_phase(TAU * i / len(_NIQQUD_ORDER)) for i, mark in enumerate(_NIQQUD_ORDER)
}

def hebrew_scalar_mass(letter: str) -> float:
    value = HEBREW_GEMATRIA.get(letter)
    if value is None:
        raise KeyError(letter)
    # Bounded monotone coordinate; raw gematria remains attached to KakuUnit.
    return math.log1p(value) / math.log1p(400)

def hebrew_kaku(letter: str) -> KakuUnit:
    value = HEBREW_GEMATRIA.get(letter)
    if value is None:
        raise KeyError(letter)
    return KakuUnit(
        symbol=HEBREW_FINAL_NORMALIZATION.get(letter, letter),
        surface_structural_mass=hebrew_scalar_mass(letter),
        kind=SurfaceKind.CONSONANT,
        raw_value=float(value),
    )

def split_hebrew_graphemes(text: str) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """Return base Hebrew letters with attached combining marks."""
    out: list[tuple[str, list[str]]] = []
    for ch in unicodedata.normalize("NFD", text):
        if ch in HEBREW_GEMATRIA:
            out.append((ch, []))
        elif out and unicodedata.combining(ch):
            out[-1][1].append(ch)
    return tuple((base, tuple(marks)) for base, marks in out)

def hebrew_orbital_cells(
    text: str,
    *,
    communication_lambda: float = 1.0,
    missing_vowel_phase: float = 0.0,
) -> tuple[OrbitalCell, ...]:
    """Encode consonant skeleton with niqqud as local phase coordinates.

    If no recognized niqqud is written on a consonant, the cell is marked
    latent. `missing_vowel_phase` is only a placeholder coordinate; callers
    should use `latent_hebrew_vowel_potential()` when they need the unresolved
    potential distribution itself.
    """
    cells: list[OrbitalCell] = []
    for base, marks in split_hebrew_graphemes(text):
        phases = [HEBREW_NIQQUD_PHASE[m] for m in marks if m in HEBREW_NIQQUD_PHASE]
        latent = not phases
        phase = missing_vowel_phase if latent else wrap_phase(math.fsum(phases) / len(phases))
        cells.append(OrbitalCell(
            kaku=hebrew_kaku(base),
            communication_lambda=communication_lambda,
            phase=phase,
            latent=latent,
        ))
    return tuple(cells)

def latent_hebrew_vowel_potential() -> dict[str, float]:
    return latent_phase_ensemble(HEBREW_NIQQUD_PHASE.values())

def build_hebrew_radical(radical_id: str, text: str) -> RadicalState:
    cells = hebrew_orbital_cells(text)
    if not cells:
        raise ValueError("Hebrew radical must contain recognized consonants")
    return RadicalState(radical_id=radical_id, cells=cells, source_language="he")

def candidate_receipt(obj: SentenceOrbit | RadicalState | ConceptState) -> dict[str, Any]:
    if isinstance(obj, SentenceOrbit):
        payload = {
            "type": "sentence_orbit",
            "sentence_id": obj.sentence_id,
            "concept_ids": [c.concept_id for c in obj.concepts],
            "edge_potentials": list(obj.edge_potentials),
            "holonomy": [obj.holonomy.real, obj.holonomy.imag],
            "moire_state": [obj.moire_state.real, obj.moire_state.imag],
        }
    elif isinstance(obj, RadicalState):
        payload = {
            "type": "radical",
            "radical_id": obj.radical_id,
            "structural_mass": obj.structural_mass,
            "ordered_phase_moment": obj.ordered_phase_moment,
            "carrier": [obj.carrier.real, obj.carrier.imag],
        }
    else:
        payload = {
            "type": "concept",
            "concept_id": obj.concept_id,
            "radical_id": obj.radical.radical_id,
            "morphology_phase": obj.morphology_phase,
            "amplitude": [obj.amplitude.real, obj.amplitude.imag],
        }
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
    return {
        "schema": SCHEMA,
        "version": VERSION,
        "status": "PASS_CANDIDATE",
        "epistemic": EPISTEMIC,
        "canon_allowed": False,
        "physical_mass_claim": False,
        "physical_gauge_field_claim": False,
        "payload": payload,
        "sha256": hashlib.sha256(raw).hexdigest(),
    }

__all__ = [
    "SCHEMA", "VERSION", "EPISTEMIC", "DualMode", "SurfaceKind", "KakuUnit",
    "OrbitalCell", "RadicalState", "ConceptState", "RelationEdge", "SentenceOrbit",
    "dual_phase", "phase_carrier", "moire_envelope", "latent_phase_ensemble",
    "HEBREW_GEMATRIA", "HEBREW_NIQQUD_PHASE", "hebrew_scalar_mass", "hebrew_kaku",
    "split_hebrew_graphemes", "hebrew_orbital_cells", "latent_hebrew_vowel_potential",
    "build_hebrew_radical", "candidate_receipt",
]
