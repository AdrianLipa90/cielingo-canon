"""Compile bounded DNA observations into the CIELingo genomic hierarchy."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Iterable, Mapping

from .grammar import GenomicLevel, GenomicNode, GenomicRelation, Orientation

IUPAC_DNA = frozenset("ACGTRYSWKMBDHVN")


@dataclass(frozen=True)
class SequenceFeature:
    feature_id: str
    sequence: str
    start_bp: int
    orientation: Orientation = Orientation.UNKNOWN
    feature_kind: str = "motif"
    annotations: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.feature_id, str) or not self.feature_id.strip():
            raise ValueError("feature_id must be a non-empty string")
        if isinstance(self.start_bp, bool) or not isinstance(self.start_bp, int):
            raise ValueError("start_bp must be an integer")
        sequence = self.sequence.upper().strip()
        if not sequence:
            raise ValueError("sequence must be non-empty")
        invalid = sorted(set(sequence) - IUPAC_DNA)
        if invalid:
            raise ValueError(f"sequence contains unsupported IUPAC DNA symbols: {invalid}")
        object.__setattr__(self, "sequence", sequence)

    @property
    def end_bp(self) -> int:
        """Half-open genomic end coordinate."""
        return self.start_bp + len(self.sequence)


def _node_span(node: GenomicNode) -> tuple[int, int]:
    start = node.payload.get("start_bp")
    end = node.payload.get("end_bp")
    if isinstance(start, bool) or not isinstance(start, int):
        raise ValueError(f"node {node.node_id} has no integer start_bp")
    if isinstance(end, bool) or not isinstance(end, int):
        raise ValueError(f"node {node.node_id} has no integer end_bp")
    if end < start:
        raise ValueError(f"node {node.node_id} has inverted genomic span")
    return start, end


def relation_between(
    left: GenomicNode,
    right: GenomicNode,
    *,
    bp_per_turn: float = 10.5,
) -> GenomicRelation:
    left_start, left_end = _node_span(left)
    right_start, _ = _node_span(right)
    anchor_distance = right_start - left_start
    gap = right_start - left_end
    return GenomicRelation(
        distance_bp=anchor_distance,
        gap_bp=gap,
        orientation=Orientation.UNKNOWN,
        bp_per_turn=bp_per_turn,
        metadata={
            "anchor": "START_TO_START",
            "left_id": left.node_id,
            "right_id": right.node_id,
            "left_start_bp": left_start,
            "left_end_bp": left_end,
            "right_start_bp": right_start,
            "left_orientation": left.payload.get("orientation", "?"),
            "right_orientation": right.payload.get("orientation", "?"),
            "overlap_bp": max(0, -gap),
        },
    )


def radical_from_feature(
    feature: SequenceFeature,
    *,
    bp_per_turn: float = 10.5,
) -> GenomicNode:
    kakus: list[GenomicNode] = []
    for offset, base in enumerate(feature.sequence):
        position = feature.start_bp + offset
        kakus.append(
            GenomicNode(
                node_id=f"{feature.feature_id}:kaku:{offset}",
                level=GenomicLevel.KAKU,
                payload={
                    "base": base,
                    "position_bp": position,
                    "start_bp": position,
                    "end_bp": position + 1,
                    "orientation": feature.orientation.value,
                    "source_feature": feature.feature_id,
                },
            )
        )

    relations = tuple(
        GenomicRelation(
            distance_bp=1,
            gap_bp=0,
            orientation=feature.orientation,
            bp_per_turn=bp_per_turn,
            metadata={
                "anchor": "START_TO_START",
                "left_id": kakus[index].node_id,
                "right_id": kakus[index + 1].node_id,
            },
        )
        for index in range(max(0, len(kakus) - 1))
    )
    return GenomicNode(
        node_id=feature.feature_id,
        level=GenomicLevel.RADICAL,
        payload={
            "feature_kind": feature.feature_kind,
            "sequence": feature.sequence,
            "start_bp": feature.start_bp,
            "end_bp": feature.end_bp,
            "orientation": feature.orientation.value,
            "annotations": dict(feature.annotations),
        },
        children=tuple(kakus),
        relations=relations,
    )


def compose_level(
    node_id: str,
    level: GenomicLevel,
    children: Iterable[GenomicNode],
    *,
    bp_per_turn: float = 10.5,
    payload: Mapping[str, Any] | None = None,
) -> GenomicNode:
    ordered = tuple(sorted(children, key=lambda child: _node_span(child)[0]))
    if not ordered:
        raise ValueError("children must not be empty")
    starts_ends = [_node_span(child) for child in ordered]
    relations = tuple(
        relation_between(ordered[index], ordered[index + 1], bp_per_turn=bp_per_turn)
        for index in range(len(ordered) - 1)
    )
    body = dict(payload or {})
    body.update(
        {
            "start_bp": min(start for start, _ in starts_ends),
            "end_bp": max(end for _, end in starts_ends),
            "child_count": len(ordered),
        }
    )
    return GenomicNode(
        node_id=node_id,
        level=level,
        payload=body,
        children=ordered,
        relations=relations,
    )


def concept_from_features(
    concept_id: str,
    features: Iterable[SequenceFeature],
    *,
    bp_per_turn: float = 10.5,
    payload: Mapping[str, Any] | None = None,
) -> GenomicNode:
    radicals = tuple(radical_from_feature(feature, bp_per_turn=bp_per_turn) for feature in features)
    return compose_level(
        concept_id,
        GenomicLevel.CONCEPT,
        radicals,
        bp_per_turn=bp_per_turn,
        payload=payload,
    )
