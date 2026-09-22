"""CIELingo hierarchical genomic grammar primitives.

This module is a computational representation, not a claim that biological DNA
is literally a natural language. It makes the hypothesis testable by separating
symbols from relations such as spacing, orientation and helical phase.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import isfinite, pi
from typing import Any, Mapping

SCHEMA = "CIELINGO_GENOMIC_GRAMMAR_V0_1"


class GenomicLevel(str, Enum):
    KAKU = "KAKU"
    RADICAL = "RADYKAŁ"
    CONCEPT = "KONCEPT"
    SENTENCE = "ZDANIE"
    PARAGRAPH = "AKAPIT"
    CHAPTER = "ROZDZIAŁ"
    BOOK = "KSIĄŻKA"


_LEVEL_ORDER = (
    GenomicLevel.KAKU,
    GenomicLevel.RADICAL,
    GenomicLevel.CONCEPT,
    GenomicLevel.SENTENCE,
    GenomicLevel.PARAGRAPH,
    GenomicLevel.CHAPTER,
    GenomicLevel.BOOK,
)
_LEVEL_INDEX = {level: index for index, level in enumerate(_LEVEL_ORDER)}


class Orientation(str, Enum):
    FORWARD = "+"
    REVERSE = "-"
    UNKNOWN = "?"


def helical_phase(distance_bp: int, bp_per_turn: float = 10.5) -> float:
    if isinstance(distance_bp, bool) or not isinstance(distance_bp, int):
        raise ValueError("distance_bp must be an integer")
    if not isinstance(bp_per_turn, (int, float)) or isinstance(bp_per_turn, bool):
        raise ValueError("bp_per_turn must be numeric")
    turns = float(bp_per_turn)
    if not isfinite(turns) or turns <= 0.0:
        raise ValueError("bp_per_turn must be finite and positive")
    return (2.0 * pi * distance_bp / turns) % (2.0 * pi)


@dataclass(frozen=True)
class GenomicRelation:
    # Anchor-to-anchor displacement used for helical phase.
    distance_bp: int
    # Empty edge-to-edge spacing is distinct from phase displacement.
    gap_bp: int | None = None
    orientation: Orientation = Orientation.UNKNOWN
    bp_per_turn: float = 10.5
    chromatin_context: str | None = None
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        helical_phase(self.distance_bp, self.bp_per_turn)
        if self.gap_bp is not None and (
            isinstance(self.gap_bp, bool) or not isinstance(self.gap_bp, int)
        ):
            raise ValueError("gap_bp must be an integer or None")

    @property
    def delta_phase_rad(self) -> float:
        return helical_phase(self.distance_bp, self.bp_per_turn)

    def to_dict(self) -> dict[str, Any]:
        return {
            "distance_bp": self.distance_bp,
            "gap_bp": self.gap_bp,
            "orientation": self.orientation.value,
            "bp_per_turn": float(self.bp_per_turn),
            "delta_phase_rad": self.delta_phase_rad,
            "chromatin_context": self.chromatin_context,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class GenomicNode:
    node_id: str
    level: GenomicLevel
    payload: Mapping[str, Any] = field(default_factory=dict)
    children: tuple["GenomicNode", ...] = ()
    relations: tuple[GenomicRelation, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.node_id, str) or not self.node_id.strip():
            raise ValueError("node_id must be a non-empty string")
        if self.level is GenomicLevel.KAKU and self.children:
            raise ValueError("KAKU is atomic and cannot contain children")
        expected_index = _LEVEL_INDEX[self.level] - 1
        if self.children:
            if expected_index < 0:
                raise ValueError("atomic level cannot contain children")
            expected_level = _LEVEL_ORDER[expected_index]
            invalid = [child.level.value for child in self.children if child.level is not expected_level]
            if invalid:
                raise ValueError(
                    f"{self.level.value} children must be {expected_level.value}; got {invalid}"
                )
        expected_relations = max(0, len(self.children) - 1)
        if self.relations and len(self.relations) != expected_relations:
            raise ValueError(
                "relations must describe every adjacent child pair "
                f"({expected_relations} required, {len(self.relations)} supplied)"
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "node_id": self.node_id,
            "level": self.level.value,
            "payload": dict(self.payload),
            "children": [child.to_dict() for child in self.children],
            "relations": [relation.to_dict() for relation in self.relations],
        }


def hierarchy_manifest() -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "levels": [level.value for level in _LEVEL_ORDER],
        "direction": "KAKU_TO_BOOK",
        "relation_channels": [
            "distance_bp",
            "gap_bp",
            "orientation",
            "delta_phase_rad",
            "chromatin_context",
        ],
        "phase_distance_semantics": "ANCHOR_TO_ANCHOR",
        "gap_semantics": "EDGE_TO_EDGE_EMPTY_SPACING",
        "epistemic_status": "COMPUTATIONAL_HYPOTHESIS_REPRESENTATION",
    }
