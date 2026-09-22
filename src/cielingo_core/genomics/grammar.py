"""CIELingo genomic grammar primitives.

This is a computational representation hypothesis, not a claim that biological
DNA is literally a natural language. It models symbolic content together with
spacing, orientation and helical phase so the hypothesis can be tested against
sequence-only baselines.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from hashlib import sha256
import json
import math
from typing import Any, Mapping, Sequence

SCHEMA = "CIELINGO_GENOMIC_GRAMMAR_V0_1"
TAU = 2.0 * math.pi


class GenomicLevel(IntEnum):
    KAKU = 0
    RADICAL = 1
    CONCEPT = 2
    SENTENCE = 3
    PARAGRAPH = 4
    CHAPTER = 5
    BOOK = 6


@dataclass(frozen=True)
class HelicalPhaseModel:
    """Simple baseline phase model with a configurable helical repeat."""

    helical_repeat_bp: float = 10.5

    def __post_init__(self) -> None:
        if not math.isfinite(self.helical_repeat_bp) or self.helical_repeat_bp <= 0.0:
            raise ValueError("helical_repeat_bp must be finite and positive")

    def phase(self, position_bp: float) -> float:
        if not math.isfinite(position_bp):
            raise ValueError("position_bp must be finite")
        return (TAU * position_bp / self.helical_repeat_bp) % TAU

    def relative_phase(self, left_bp: float, right_bp: float) -> float:
        return (self.phase(right_bp) - self.phase(left_bp)) % TAU


@dataclass(frozen=True)
class GenomicRelation:
    source_id: str
    target_id: str
    distance_bp: float
    relative_phase_rad: float
    orientation: str = "unspecified"
    chromatin_context: str | None = None

    def __post_init__(self) -> None:
        if not self.source_id or not self.target_id:
            raise ValueError("source_id and target_id are required")
        if not math.isfinite(self.distance_bp):
            raise ValueError("distance_bp must be finite")
        if not math.isfinite(self.relative_phase_rad):
            raise ValueError("relative_phase_rad must be finite")

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "distance_bp": self.distance_bp,
            "relative_phase_rad": self.relative_phase_rad % TAU,
            "orientation": self.orientation,
            "chromatin_context": self.chromatin_context,
        }


@dataclass(frozen=True)
class GenomicUnit:
    unit_id: str
    level: GenomicLevel
    payload: Mapping[str, Any] = field(default_factory=dict)
    children: tuple["GenomicUnit", ...] = field(default_factory=tuple)
    relations: tuple[GenomicRelation, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        if not self.unit_id:
            raise ValueError("unit_id is required")
        expected_child_level = int(self.level) - 1
        if self.level == GenomicLevel.KAKU and self.children:
            raise ValueError("KAKU is atomic and cannot contain children")
        for child in self.children:
            if int(child.level) != expected_child_level:
                raise ValueError(
                    f"{self.level.name} children must be {GenomicLevel(expected_child_level).name}"
                )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "unit_id": self.unit_id,
            "level": self.level.name,
            "payload": dict(self.payload),
            "children": [child.to_dict() for child in self.children],
            "relations": [relation.to_dict() for relation in self.relations],
            "epistemic_status": "COMPUTATIONAL_HYPOTHESIS",
            "biological_equivalence_claim": False,
        }

    def semantic_signature(self) -> str:
        encoded = json.dumps(
            self.to_dict(), sort_keys=True, separators=(",", ":"), ensure_ascii=False
        ).encode("utf-8")
        return sha256(encoded).hexdigest()


def relation_from_positions(
    source_id: str,
    target_id: str,
    source_position_bp: float,
    target_position_bp: float,
    *,
    phase_model: HelicalPhaseModel | None = None,
    orientation: str = "unspecified",
    chromatin_context: str | None = None,
) -> GenomicRelation:
    model = phase_model or HelicalPhaseModel()
    return GenomicRelation(
        source_id=source_id,
        target_id=target_id,
        distance_bp=target_position_bp - source_position_bp,
        relative_phase_rad=model.relative_phase(source_position_bp, target_position_bp),
        orientation=orientation,
        chromatin_context=chromatin_context,
    )


def assemble_unit(
    unit_id: str,
    level: GenomicLevel,
    children: Sequence[GenomicUnit],
    *,
    payload: Mapping[str, Any] | None = None,
    relations: Sequence[GenomicRelation] = (),
) -> GenomicUnit:
    """Construct one grammar level with strict adjacent-level composition."""

    return GenomicUnit(
        unit_id=unit_id,
        level=level,
        payload=payload or {},
        children=tuple(children),
        relations=tuple(relations),
    )
