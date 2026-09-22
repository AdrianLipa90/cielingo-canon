"""Compile sequence/motif observations into CIELingo genomic grammar."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .grammar import (
    GenomicLevel,
    GenomicRelation,
    GenomicUnit,
    HelicalPhaseModel,
    assemble_unit,
    relation_from_positions,
)
from .motifs import MotifDefinition, MotifHit, scan_motifs
from .sequence import SequenceRecord


@dataclass(frozen=True)
class GenomicParseResult:
    record: SequenceRecord
    hits: tuple[MotifHit, ...]
    radicals: tuple[GenomicUnit, ...]
    relations: tuple[GenomicRelation, ...]
    concepts: tuple[GenomicUnit, ...]
    sentence: GenomicUnit | None
    max_relation_distance_bp: float

    def to_dict(self) -> dict[str, object]:
        return {
            "record": {
                "record_id": self.record.record_id,
                "sequence_length": len(self.record.sequence),
            },
            "hits": [hit.to_dict() for hit in self.hits],
            "radicals": [radical.to_dict() for radical in self.radicals],
            "relations": [relation.to_dict() for relation in self.relations],
            "concepts": [concept.to_dict() for concept in self.concepts],
            "sentence": None if self.sentence is None else self.sentence.to_dict(),
            "max_relation_distance_bp": self.max_relation_distance_bp,
            "epistemic_status": "COMPUTATIONAL_HYPOTHESIS",
            "biological_equivalence_claim": False,
        }


def _hit_id(hit: MotifHit, index: int) -> str:
    return (
        f"radical:{hit.motif_id}:{hit.start}:{hit.end}:{hit.strand}:{index}"
    )


def _kaku_for_hit(hit: MotifHit, radical_id: str) -> tuple[GenomicUnit, ...]:
    return tuple(
        GenomicUnit(
            unit_id=f"{radical_id}:kaku:{hit.start + offset}",
            level=GenomicLevel.KAKU,
            payload={
                "symbol": base,
                "position_bp": hit.start + offset,
                "strand": hit.strand,
            },
        )
        for offset, base in enumerate(hit.matched_sequence)
    )


def _build_radicals(hits: Sequence[MotifHit]) -> tuple[GenomicUnit, ...]:
    radicals: list[GenomicUnit] = []
    for index, hit in enumerate(hits):
        radical_id = _hit_id(hit, index)
        radicals.append(
            assemble_unit(
                radical_id,
                GenomicLevel.RADICAL,
                _kaku_for_hit(hit, radical_id),
                payload={
                    "motif_id": hit.motif_id,
                    "pattern": hit.pattern,
                    "start": hit.start,
                    "end": hit.end,
                    "strand": hit.strand,
                    "matched_sequence": hit.matched_sequence,
                    "center_bp": hit.center_bp,
                },
            )
        )
    return tuple(radicals)


def _orientation(left: MotifHit, right: MotifHit) -> str:
    if left.strand == right.strand == "+":
        return "co_forward"
    if left.strand == right.strand == "-":
        return "co_reverse"
    return "opposed"


def _build_relations(
    hits: Sequence[MotifHit],
    radicals: Sequence[GenomicUnit],
    phase_model: HelicalPhaseModel,
    max_distance_bp: float,
) -> tuple[GenomicRelation, ...]:
    relations: list[GenomicRelation] = []
    for left_index, left in enumerate(hits):
        for right_index in range(left_index + 1, len(hits)):
            right = hits[right_index]
            distance = right.center_bp - left.center_bp
            if abs(distance) > max_distance_bp:
                continue
            relations.append(
                relation_from_positions(
                    radicals[left_index].unit_id,
                    radicals[right_index].unit_id,
                    left.center_bp,
                    right.center_bp,
                    phase_model=phase_model,
                    orientation=_orientation(left, right),
                )
            )
    return tuple(relations)


def _connected_components(
    radicals: Sequence[GenomicUnit],
    relations: Sequence[GenomicRelation],
) -> tuple[tuple[int, ...], ...]:
    if not radicals:
        return ()

    index = {radical.unit_id: i for i, radical in enumerate(radicals)}
    adjacency = [set() for _ in radicals]
    for relation in relations:
        left = index[relation.source_id]
        right = index[relation.target_id]
        adjacency[left].add(right)
        adjacency[right].add(left)

    seen: set[int] = set()
    components: list[tuple[int, ...]] = []
    for start in range(len(radicals)):
        if start in seen:
            continue
        stack = [start]
        component: list[int] = []
        seen.add(start)
        while stack:
            node = stack.pop()
            component.append(node)
            for neighbor in sorted(adjacency[node]):
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        components.append(tuple(sorted(component)))
    return tuple(components)


def _build_concepts(
    radicals: Sequence[GenomicUnit],
    relations: Sequence[GenomicRelation],
) -> tuple[GenomicUnit, ...]:
    concepts: list[GenomicUnit] = []
    for concept_index, component in enumerate(
        _connected_components(radicals, relations)
    ):
        children = tuple(radicals[i] for i in component)
        child_ids = {child.unit_id for child in children}
        edges = tuple(
            relation
            for relation in relations
            if relation.source_id in child_ids and relation.target_id in child_ids
        )
        concepts.append(
            assemble_unit(
                f"concept:{concept_index}",
                GenomicLevel.CONCEPT,
                children,
                payload={
                    "component_size": len(children),
                    "relation_count": len(edges),
                },
                relations=edges,
            )
        )
    return tuple(concepts)


def parse_genomic_grammar(
    record: SequenceRecord,
    motifs: Sequence[MotifDefinition],
    *,
    helical_repeat_bp: float = 10.5,
    max_relation_distance_bp: float = 80.0,
) -> GenomicParseResult:
    """Compile one DNA record into a candidate KAKU→SENTENCE representation."""

    if max_relation_distance_bp <= 0.0:
        raise ValueError("max_relation_distance_bp must be positive")

    hits = scan_motifs(record.sequence, motifs)
    radicals = _build_radicals(hits)
    phase_model = HelicalPhaseModel(helical_repeat_bp)
    relations = _build_relations(
        hits,
        radicals,
        phase_model,
        max_relation_distance_bp,
    )
    concepts = _build_concepts(radicals, relations)

    sentence: GenomicUnit | None = None
    if concepts:
        sentence = assemble_unit(
            f"sentence:{record.record_id}",
            GenomicLevel.SENTENCE,
            concepts,
            payload={
                "record_id": record.record_id,
                "sequence_length": len(record.sequence),
                "motif_hit_count": len(hits),
                "relation_count": len(relations),
                "helical_repeat_bp": helical_repeat_bp,
                "interpretation": (
                    "candidate regulatory sentence representation; "
                    "not biological equivalence"
                ),
            },
        )

    return GenomicParseResult(
        record=record,
        hits=hits,
        radicals=radicals,
        relations=relations,
        concepts=concepts,
        sentence=sentence,
        max_relation_distance_bp=float(max_relation_distance_bp),
    )
