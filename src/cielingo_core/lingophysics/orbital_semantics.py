"""Candidate orbital-fractal semantic grammar primitives for CIELingo.

This module implements a computational representation only.

Terminology such as "structural mass", "phase", "holonomy" and the
Aharonov-Bohm-inspired phase analogy must not be read as a claim that linguistic
states are literal physical masses, electromagnetic potentials, or gauge fields.

The candidate hierarchy is:

    KAKU -> chi(+/-) -> RADICAL -> CONCEPT -> SENTENCE

chi(+/-) is the missing local orbital cell between an atomic written carrier and
a composed radical/root.  The +/- pair is complex-conjugate phase/counterphase.
The representation is script-agnostic; the kana phase/counterphase analogy is an
inspiration only and does not change the frozen Japanese language policy.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import math
from typing import Sequence

ORBITAL_SEMANTIC_VERSION = "0.1.0"
ORBITAL_SEMANTIC_EPISTEMIC = "CHYBA"
PHASE_DIMS = 36
_EPS = 1e-12

HEBREW_FINAL_TO_BASE = {
    "ך": "כ",
    "ם": "מ",
    "ן": "נ",
    "ף": "פ",
    "ץ": "צ",
}

HEBREW_STANDARD_GEMATRIA = {
    "א": 1, "ב": 2, "ג": 3, "ד": 4, "ה": 5, "ו": 6, "ז": 7, "ח": 8, "ט": 9,
    "י": 10, "כ": 20, "ל": 30, "מ": 40, "נ": 50, "ס": 60, "ע": 70, "פ": 80,
    "צ": 90, "ק": 100, "ר": 200, "ש": 300, "ת": 400,
}


def wrap_phase(value: float) -> float:
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("phase must be finite")
    return math.atan2(math.sin(value), math.cos(value))


def _finite_unit_interval(value: float, name: str) -> float:
    value = float(value)
    if not math.isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be finite and in [0,1]")
    return value


def _phase_of(re: float, im: float) -> float:
    if abs(re) <= _EPS and abs(im) <= _EPS:
        return 0.0
    return math.atan2(im, re)


def _validate_phase36(values: Sequence[float]) -> tuple[float, ...]:
    out = tuple(wrap_phase(x) for x in values)
    if len(out) != PHASE_DIMS:
        raise ValueError(f"phase vector must have {PHASE_DIMS} components")
    return out


@dataclass(frozen=True)
class KakuState:
    """Atomic written carrier.

    structural_mass is a dimensionless computational weight.  It is not a
    physical mass. numeric_value may preserve a source-specific numerical code
    such as conventional Hebrew gematria.
    """

    symbol: str
    normalized_symbol: str
    structural_mass: float
    numeric_value: float | None = None
    source_system: str = "generic"
    epistemic: str = ORBITAL_SEMANTIC_EPISTEMIC

    def __post_init__(self) -> None:
        if not isinstance(self.symbol, str) or not self.symbol:
            raise ValueError("symbol must be non-empty")
        if not isinstance(self.normalized_symbol, str) or not self.normalized_symbol:
            raise ValueError("normalized_symbol must be non-empty")
        mass = float(self.structural_mass)
        if not math.isfinite(mass) or mass <= 0.0:
            raise ValueError("structural_mass must be finite and > 0")
        if self.numeric_value is not None and not math.isfinite(float(self.numeric_value)):
            raise ValueError("numeric_value must be finite")


def hebrew_kaku(symbol: str) -> KakuState:
    """Build a Hebrew KAKU using ordinary gematria as one structural seed.

    The numerical value is preserved exactly while structural_mass is log-scaled
    to a dimensionless (0,1] computational weight.  This does not assert that
    gematria is physical mass or that it encodes lexical meaning.
    """

    if not isinstance(symbol, str) or len(symbol) != 1:
        raise ValueError("hebrew_kaku expects exactly one Hebrew consonant letter")
    base = HEBREW_FINAL_TO_BASE.get(symbol, symbol)
    try:
        value = HEBREW_STANDARD_GEMATRIA[base]
    except KeyError as exc:
        raise ValueError(f"unsupported Hebrew consonant: {symbol!r}") from exc
    mass = math.log1p(value) / math.log1p(400.0)
    return KakuState(
        symbol=symbol,
        normalized_symbol=base,
        structural_mass=mass,
        numeric_value=float(value),
        source_system="hebrew_standard_gematria_seed",
    )


@dataclass(frozen=True)
class OrbitalCell:
    """Local chi state between KAKU and RADICAL."""

    kaku: KakuState
    semantic_phase: float
    communication_lambda: float
    chirality: int
    epistemic: str = ORBITAL_SEMANTIC_EPISTEMIC
    canon_allowed: bool = False

    def __post_init__(self) -> None:
        wrap_phase(self.semantic_phase)
        _finite_unit_interval(self.communication_lambda, "communication_lambda")
        if self.chirality not in (-1, 1):
            raise ValueError("chirality must be +1 or -1")
        if self.canon_allowed:
            raise ValueError("candidate OrbitalCell cannot grant canon")

    @property
    def amplitude(self) -> float:
        return float(self.kaku.structural_mass) * float(self.communication_lambda)

    @property
    def complex_state(self) -> complex:
        theta = self.chirality * wrap_phase(self.semantic_phase)
        return self.amplitude * complex(math.cos(theta), math.sin(theta))

    def conjugate(self) -> "OrbitalCell":
        return OrbitalCell(
            kaku=self.kaku,
            semantic_phase=self.semantic_phase,
            communication_lambda=self.communication_lambda,
            chirality=-self.chirality,
        )


@dataclass(frozen=True)
class OrbitalCellPair:
    plus: OrbitalCell
    minus: OrbitalCell

    def __post_init__(self) -> None:
        if self.plus.chirality != 1 or self.minus.chirality != -1:
            raise ValueError("pair must contain + and - chirality")
        if self.plus.kaku != self.minus.kaku:
            raise ValueError("phase/counterphase pair must share KAKU")
        if abs(self.plus.complex_state.conjugate() - self.minus.complex_state) > 1e-12:
            raise ValueError("phase/counterphase pair must be complex conjugates")


def orbital_cell_pair(
    kaku: KakuState,
    semantic_phase: float,
    communication_lambda: float = 1.0,
) -> OrbitalCellPair:
    plus = OrbitalCell(kaku, wrap_phase(semantic_phase), communication_lambda, 1)
    return OrbitalCellPair(plus=plus, minus=plus.conjugate())


@dataclass(frozen=True)
class LatentPhaseEnsemble:
    """Unresolved phase with zero mean carrier but non-zero potential."""

    phases: tuple[float, ...]
    expectation: complex
    second_moment: float
    entropy_bits: float

    @property
    def zero_mean(self) -> bool:
        return abs(self.expectation) <= 1e-12


def latent_phase_ensemble(cardinality: int = 13) -> LatentPhaseEnsemble:
    """Uniform unresolved phase ensemble.

    Equally spaced phases give approximately zero complex expectation while
    retaining unit second moment and positive entropy.  This is the precise
    computational sense in which an unwritten vowel can be represented as
    "zero mean, non-zero potential"; it is not a zeta-function claim.
    """

    n = int(cardinality)
    if n < 2:
        raise ValueError("cardinality must be >= 2")
    phases = tuple(2.0 * math.pi * k / n for k in range(n))
    states = tuple(complex(math.cos(p), math.sin(p)) for p in phases)
    expectation = sum(states, 0j) / n
    second_moment = math.fsum(abs(z) ** 2 for z in states) / n
    return LatentPhaseEnsemble(
        phases=phases,
        expectation=expectation,
        second_moment=second_moment,
        entropy_bits=math.log2(n),
    )


def phase_vector36_from_cells(cells: Sequence[OrbitalCell]) -> tuple[float, ...]:
    cells = tuple(cells)
    if not cells:
        raise ValueError("at least one orbital cell is required")
    out: list[float] = []
    for dim in range(PHASE_DIMS):
        re_terms: list[float] = []
        im_terms: list[float] = []
        for position, cell in enumerate(cells):
            positional = 2.0 * math.pi * (position + 1) * (dim + 1) / PHASE_DIMS
            z = cell.complex_state * complex(math.cos(positional), math.sin(positional))
            re_terms.append(z.real)
            im_terms.append(z.imag)
        out.append(_phase_of(math.fsum(re_terms), math.fsum(im_terms)))
    return tuple(out)


@dataclass(frozen=True)
class RadicalOrbital:
    cells: tuple[OrbitalCell, ...]
    phase36: tuple[float, ...]
    epistemic: str = ORBITAL_SEMANTIC_EPISTEMIC
    canon_allowed: bool = False

    @classmethod
    def build(cls, cells: Sequence[OrbitalCell]) -> "RadicalOrbital":
        cell_tuple = tuple(cells)
        if not cell_tuple:
            raise ValueError("radical requires at least one orbital cell")
        return cls(cells=cell_tuple, phase36=phase_vector36_from_cells(cell_tuple))


@dataclass(frozen=True)
class ConceptOrbital:
    label: str
    radical: RadicalOrbital
    morphology_phase: float
    communication_lambda: float
    phase36: tuple[float, ...]
    epistemic: str = ORBITAL_SEMANTIC_EPISTEMIC
    canon_allowed: bool = False

    @classmethod
    def build(
        cls,
        label: str,
        radical: RadicalOrbital,
        morphology_phase: float = 0.0,
        communication_lambda: float = 1.0,
    ) -> "ConceptOrbital":
        if not isinstance(label, str) or not label.strip():
            raise ValueError("concept label must be non-empty")
        lam = _finite_unit_interval(communication_lambda, "communication_lambda")
        phi = wrap_phase(morphology_phase)
        phase36 = tuple(
            wrap_phase(base + phi * ((dim + 1) / PHASE_DIMS))
            for dim, base in enumerate(radical.phase36)
        )
        return cls(
            label=label.strip(),
            radical=radical,
            morphology_phase=phi,
            communication_lambda=lam,
            phase36=phase36,
        )


@dataclass(frozen=True)
class SemanticRelation:
    source: int
    target: int
    relation_type: str
    edge_potential: float
    communication_lambda: float = 1.0

    def __post_init__(self) -> None:
        if self.source < 0 or self.target < 0 or self.source == self.target:
            raise ValueError("relation endpoints must be distinct non-negative indices")
        if not isinstance(self.relation_type, str) or not self.relation_type.strip():
            raise ValueError("relation_type must be non-empty")
        wrap_phase(self.edge_potential)
        _finite_unit_interval(self.communication_lambda, "communication_lambda")


def _stable_relation_phase(relation_type: str) -> float:
    digest = hashlib.sha256(relation_type.strip().casefold().encode("utf-8")).digest()
    raw = int.from_bytes(digest[:8], "big") / float(2**64)
    return 2.0 * math.pi * raw


def _mean_phase(vectors: Sequence[Sequence[float]]) -> tuple[float, ...]:
    vectors = tuple(_validate_phase36(v) for v in vectors)
    if not vectors:
        raise ValueError("at least one phase vector is required")
    out = []
    for dim in range(PHASE_DIMS):
        re = math.fsum(math.cos(v[dim]) for v in vectors)
        im = math.fsum(math.sin(v[dim]) for v in vectors)
        out.append(_phase_of(re, im))
    return tuple(out)


def _ordered_phase(concepts: Sequence[ConceptOrbital]) -> tuple[float, ...]:
    concepts = tuple(concepts)
    if not concepts:
        raise ValueError("sentence requires at least one concept")
    out = []
    for dim in range(PHASE_DIMS):
        re_terms = []
        im_terms = []
        for position, concept in enumerate(concepts):
            shift = 2.0 * math.pi * (position + 1) * (dim + 1) / (
                PHASE_DIMS * max(1, len(concepts))
            )
            theta = concept.phase36[dim] + shift
            amp = concept.communication_lambda
            re_terms.append(amp * math.cos(theta))
            im_terms.append(amp * math.sin(theta))
        out.append(_phase_of(math.fsum(re_terms), math.fsum(im_terms)))
    return tuple(out)


def _syntax_phase(
    relations: Sequence[SemanticRelation],
    concept_count: int,
) -> tuple[float, ...] | None:
    relations = tuple(relations)
    if not relations:
        return None
    for rel in relations:
        if rel.source >= concept_count or rel.target >= concept_count:
            raise ValueError("relation endpoint exceeds concept count")
    out = []
    for dim in range(PHASE_DIMS):
        re_terms = []
        im_terms = []
        for rel in relations:
            type_phase = _stable_relation_phase(rel.relation_type)
            endpoint_phase = (
                2.0
                * math.pi
                * (rel.source + 1)
                * (rel.target + 1)
                * (dim + 1)
                / (PHASE_DIMS * max(1, concept_count))
            )
            theta = wrap_phase(rel.edge_potential + type_phase + endpoint_phase)
            re_terms.append(rel.communication_lambda * math.cos(theta))
            im_terms.append(rel.communication_lambda * math.sin(theta))
        out.append(_phase_of(math.fsum(re_terms), math.fsum(im_terms)))
    return tuple(out)


def moire_combine(
    structural: Sequence[float],
    realization: Sequence[float],
    realization_weight: float = 1.0,
) -> tuple[float, ...]:
    left = _validate_phase36(structural)
    right = _validate_phase36(realization)
    weight = _finite_unit_interval(realization_weight, "realization_weight")
    out = []
    for a, b in zip(left, right):
        re = math.cos(a) + weight * math.cos(b)
        im = math.sin(a) + weight * math.sin(b)
        out.append(_phase_of(re, im))
    return tuple(out)


@dataclass(frozen=True)
class SentenceOrbital:
    concepts: tuple[ConceptOrbital, ...]
    relations: tuple[SemanticRelation, ...]
    bag_phase36: tuple[float, ...]
    lexical_phase36: tuple[float, ...]
    syntax_phase36: tuple[float, ...] | None
    phase36: tuple[float, ...]
    epistemic: str = ORBITAL_SEMANTIC_EPISTEMIC
    canon_allowed: bool = False

    @classmethod
    def build(
        cls,
        concepts: Sequence[ConceptOrbital],
        relations: Sequence[SemanticRelation] = (),
    ) -> "SentenceOrbital":
        concepts = tuple(concepts)
        relations = tuple(relations)
        if not concepts:
            raise ValueError("sentence requires at least one concept")
        bag = _mean_phase([c.phase36 for c in concepts])
        lexical = _ordered_phase(concepts)
        syntax = _syntax_phase(relations, len(concepts))
        if syntax is None:
            phase = lexical
        else:
            weight = math.fsum(r.communication_lambda for r in relations) / len(relations)
            phase = moire_combine(lexical, syntax, weight)
        return cls(
            concepts=concepts,
            relations=relations,
            bag_phase36=bag,
            lexical_phase36=lexical,
            syntax_phase36=syntax,
            phase36=phase,
        )


def phase_overlap(left: Sequence[float], right: Sequence[float]) -> complex:
    left36 = _validate_phase36(left)
    right36 = _validate_phase36(right)
    re = math.fsum(math.cos(b - a) for a, b in zip(left36, right36)) / PHASE_DIMS
    im = math.fsum(math.sin(b - a) for a, b in zip(left36, right36)) / PHASE_DIMS
    return complex(re, im)


def phase_fidelity(left: Sequence[float], right: Sequence[float]) -> float:
    return abs(phase_overlap(left, right)) ** 2


def phasenav_semantic_payload(
    path_id: str,
    left_phase36: Sequence[float],
    right_phase36: Sequence[float],
    edge_potentials: Sequence[float],
) -> dict[str, object]:
    """Emit a dependency-free payload for PhaseNav semantic U(1) holonomy.

    PhaseNav remains the authority for U(1) transport and closed-loop invariants.
    CIELingo only constructs the linguistic state and declared edge potentials.
    """

    if not isinstance(path_id, str) or not path_id.strip():
        raise ValueError("path_id must be non-empty")
    edges = tuple(wrap_phase(x) for x in edge_potentials)
    return {
        "schema": "CIELINGO_ORBITAL_SEMANTIC_PHASENAV_PAYLOAD_V0_1",
        "version": ORBITAL_SEMANTIC_VERSION,
        "path_id": path_id.strip(),
        "left_phase36": list(_validate_phase36(left_phase36)),
        "right_phase36": list(_validate_phase36(right_phase36)),
        "edge_potentials": list(edges),
        "epistemic": ORBITAL_SEMANTIC_EPISTEMIC,
        "authority": "CANDIDATE_ONLY",
        "canon_allowed": False,
        "physical_mass_claim": False,
        "physical_gauge_field_claim": False,
        "aharonov_bohm_binding_claim": False,
    }


__all__ = [
    "ORBITAL_SEMANTIC_VERSION",
    "ORBITAL_SEMANTIC_EPISTEMIC",
    "PHASE_DIMS",
    "HEBREW_FINAL_TO_BASE",
    "HEBREW_STANDARD_GEMATRIA",
    "KakuState",
    "OrbitalCell",
    "OrbitalCellPair",
    "LatentPhaseEnsemble",
    "RadicalOrbital",
    "ConceptOrbital",
    "SemanticRelation",
    "SentenceOrbital",
    "hebrew_kaku",
    "orbital_cell_pair",
    "latent_phase_ensemble",
    "phase_vector36_from_cells",
    "moire_combine",
    "phase_overlap",
    "phase_fidelity",
    "phasenav_semantic_payload",
]
