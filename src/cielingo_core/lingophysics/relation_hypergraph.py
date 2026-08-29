"""Typed n-ary relation-event hypergraph for CIELingo Lingophysics."""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
import string
from typing import Any

from cielingo_core.regional.base import RegionalSolveResult
from .case_port_frame import extract_polish_case_port_frames
from .operator_signatures import get_operator_signature, type_case_port_frame


RELATION_HYPERGRAPH_SCHEMA = "CIEL_RELATION_HYPERGRAPH_V0_1"
_HEX = frozenset(string.hexdigits)


def _bounded01(value: float) -> bool:
    return 0.0 <= float(value) <= 1.0


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(char in _HEX for char in value)


def _digest(payload: Any) -> str:
    return sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


@dataclass(frozen=True)
class RelationEntityNode:
    entity_id: str
    label: str
    token_indices: tuple[int, ...]
    surface_form: str
    implicit: bool
    confidence: float
    candidate_only: bool = True

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.entity_id:
            issues.append("entity_id is required")
        if not self.label:
            issues.append("entity label is required")
        if any(index < 0 for index in self.token_indices):
            issues.append("entity token_indices must be non-negative")
        if self.implicit != (len(self.token_indices) == 0):
            issues.append("entity implicit flag must match token-index absence")
        if not _bounded01(self.confidence):
            issues.append("entity confidence must be in [0,1]")
        if not self.candidate_only:
            issues.append("relation entity v0.1 must remain candidate-only")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "label": self.label,
            "token_indices": list(self.token_indices),
            "surface_form": self.surface_form,
            "implicit": self.implicit,
            "confidence": self.confidence,
            "candidate_only": self.candidate_only,
        }


@dataclass(frozen=True)
class RelationEventNode:
    event_id: str
    operator: str
    relation_family: str
    directional: bool
    symmetric: bool
    source_frame_id: str
    signature_id: str
    signature_commitment: str
    confidence: float
    candidate_only: bool = True

    def validate(self) -> list[str]:
        issues: list[str] = []
        for name in (
            "event_id",
            "operator",
            "relation_family",
            "source_frame_id",
            "signature_id",
        ):
            if not str(getattr(self, name)).strip():
                issues.append(f"{name} is required")
        if self.directional and self.symmetric:
            issues.append("relation event cannot be both directional and symmetric")
        if not _is_sha256(self.signature_commitment):
            issues.append("relation event signature_commitment must be SHA-256")
        if not _bounded01(self.confidence):
            issues.append("relation event confidence must be in [0,1]")
        if not self.candidate_only:
            issues.append("relation event v0.1 must remain candidate-only")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_id": self.event_id,
            "operator": self.operator,
            "relation_family": self.relation_family,
            "directional": self.directional,
            "symmetric": self.symmetric,
            "source_frame_id": self.source_frame_id,
            "signature_id": self.signature_id,
            "signature_commitment": self.signature_commitment,
            "confidence": self.confidence,
            "candidate_only": self.candidate_only,
        }


@dataclass(frozen=True)
class RelationIncidence:
    incidence_id: str
    event_id: str
    entity_id: str
    source_frame_id: str
    grammatical_case: str
    operator_role: str
    token_indices: tuple[int, ...]
    adposition: str | None
    universal_role: str | None
    normalization_basis: str | None
    confidence: float
    candidate_only: bool = True

    def validate(self) -> list[str]:
        issues: list[str] = []
        for name in (
            "incidence_id",
            "event_id",
            "entity_id",
            "source_frame_id",
            "grammatical_case",
            "operator_role",
        ):
            if not str(getattr(self, name)).strip():
                issues.append(f"{name} is required")
        if any(index < 0 for index in self.token_indices):
            issues.append("incidence token_indices must be non-negative")
        if (self.universal_role is None) != (self.normalization_basis is None):
            issues.append("universal_role and normalization_basis must be present together")
        if not _bounded01(self.confidence):
            issues.append("incidence confidence must be in [0,1]")
        if not self.candidate_only:
            issues.append("relation incidence v0.1 must remain candidate-only")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "incidence_id": self.incidence_id,
            "event_id": self.event_id,
            "entity_id": self.entity_id,
            "source_frame_id": self.source_frame_id,
            "grammatical_case": self.grammatical_case,
            "operator_role": self.operator_role,
            "token_indices": list(self.token_indices),
            "adposition": self.adposition,
            "universal_role": self.universal_role,
            "normalization_basis": self.normalization_basis,
            "confidence": self.confidence,
            "candidate_only": self.candidate_only,
        }


@dataclass(frozen=True)
class RelationHypergraph:
    equation_id: str
    language_id: str
    entities: tuple[RelationEntityNode, ...]
    events: tuple[RelationEventNode, ...]
    incidences: tuple[RelationIncidence, ...]
    commitment: str
    candidate_only: bool = True
    schema: str = RELATION_HYPERGRAPH_SCHEMA

    @classmethod
    def create(
        cls,
        *,
        equation_id: str,
        language_id: str,
        entities: tuple[RelationEntityNode, ...] | list[RelationEntityNode],
        events: tuple[RelationEventNode, ...] | list[RelationEventNode],
        incidences: tuple[RelationIncidence, ...] | list[RelationIncidence],
    ) -> "RelationHypergraph":
        provisional = cls(
            equation_id=equation_id,
            language_id=language_id,
            entities=tuple(entities),
            events=tuple(events),
            incidences=tuple(incidences),
            commitment="",
        )
        graph = replace(provisional, commitment=_digest(provisional.to_binding_dict()))
        issues = graph.validate()
        if issues:
            raise ValueError("; ".join(issues))
        return graph

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.equation_id:
            issues.append("relation hypergraph equation_id is required")
        if not self.language_id:
            issues.append("relation hypergraph language_id is required")
        if not self.events:
            issues.append("relation hypergraph requires at least one event")
        if not self.entities:
            issues.append("relation hypergraph requires at least one entity")
        if not self.incidences:
            issues.append("relation hypergraph requires at least one incidence")
        if not self.candidate_only:
            issues.append("relation hypergraph v0.1 must remain candidate-only")

        entity_ids = [entity.entity_id for entity in self.entities]
        event_ids = [event.event_id for event in self.events]
        incidence_ids = [incidence.incidence_id for incidence in self.incidences]
        if len(set(entity_ids)) != len(entity_ids):
            issues.append("relation hypergraph entity IDs must be unique")
        if len(set(event_ids)) != len(event_ids):
            issues.append("relation hypergraph event IDs must be unique")
        if len(set(incidence_ids)) != len(incidence_ids):
            issues.append("relation hypergraph incidence IDs must be unique")

        entity_set = set(entity_ids)
        event_set = set(event_ids)
        event_by_id = {event.event_id: event for event in self.events}
        entity_by_id = {entity.entity_id: entity for entity in self.entities}
        event_incidence_count = {event_id: 0 for event_id in event_ids}

        for entity in self.entities:
            issues.extend(entity.validate())
        for event in self.events:
            issues.extend(event.validate())
        for incidence in self.incidences:
            issues.extend(incidence.validate())
            if incidence.event_id not in event_set:
                issues.append(f"incidence {incidence.incidence_id} has unknown event")
                continue
            if incidence.entity_id not in entity_set:
                issues.append(f"incidence {incidence.incidence_id} has unknown entity")
                continue
            event_incidence_count[incidence.event_id] += 1
            event = event_by_id[incidence.event_id]
            entity = entity_by_id[incidence.entity_id]
            if incidence.source_frame_id != event.source_frame_id:
                issues.append(f"incidence {incidence.incidence_id} source frame mismatch")
            if incidence.token_indices != entity.token_indices:
                issues.append(f"incidence {incidence.incidence_id} entity token-index mismatch")

        for event_id, count in event_incidence_count.items():
            if count == 0:
                issues.append(f"relation event {event_id} has no incidences")

        if not _is_sha256(self.commitment):
            issues.append("relation hypergraph commitment must be SHA-256")
        elif self.commitment != _digest(self.to_binding_dict()):
            issues.append("relation hypergraph commitment mismatch")
        return issues

    def events_for_entity(self, entity_id: str) -> tuple[RelationEventNode, ...]:
        event_ids = {
            incidence.event_id
            for incidence in self.incidences
            if incidence.entity_id == entity_id
        }
        return tuple(event for event in self.events if event.event_id in event_ids)

    def incidences_for_event(self, event_id: str) -> tuple[RelationIncidence, ...]:
        return tuple(
            incidence for incidence in self.incidences if incidence.event_id == event_id
        )

    def to_binding_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "equation_id": self.equation_id,
            "language_id": self.language_id,
            "entities": [entity.to_dict() for entity in self.entities],
            "events": [event.to_dict() for event in self.events],
            "incidences": [incidence.to_dict() for incidence in self.incidences],
            "candidate_only": self.candidate_only,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.to_binding_dict(), "commitment": self.commitment}


def _entity_id(
    equation_id: str,
    label: str,
    token_indices: tuple[int, ...],
) -> str:
    key = {
        "equation_id": equation_id,
        "label": label,
        "token_indices": list(token_indices),
    }
    return "entity:" + _digest(key)[:24]


def build_relation_hypergraph(
    result: RegionalSolveResult,
    *,
    equation_id: str,
) -> RelationHypergraph | None:
    """Build an n-ary typed relation IR from signature-valid CasePortFrames."""
    if result.language_id != "pl":
        return None

    frames = extract_polish_case_port_frames(result.text, list(result.segments.tokens))
    entities_by_id: dict[str, RelationEntityNode] = {}
    events: list[RelationEventNode] = []
    incidences: list[RelationIncidence] = []

    for frame in frames:
        report = type_case_port_frame(frame)
        signature = get_operator_signature(frame.operator)
        if (
            not report.valid
            or signature is None
            or not report.signature_id
            or not report.signature_commitment
        ):
            continue

        event_id = "event:" + _digest({
            "equation_id": equation_id,
            "frame_id": frame.frame_id,
            "operator": frame.operator,
            "signature_commitment": report.signature_commitment,
        })[:24]
        events.append(RelationEventNode(
            event_id=event_id,
            operator=frame.operator,
            relation_family=signature.relation_family,
            directional=signature.directional,
            symmetric=signature.symmetric,
            source_frame_id=frame.frame_id,
            signature_id=report.signature_id,
            signature_commitment=report.signature_commitment,
            confidence=float(frame.confidence),
            candidate_only=True,
        ))

        normalized = {
            (
                binding.grammatical_case,
                binding.operator_role,
                binding.entity,
                binding.token_indices,
            ): binding
            for binding in report.universal_roles
        }

        for position, port in enumerate(frame.ports):
            entity_id = _entity_id(equation_id, port.entity, port.token_indices)
            entity = RelationEntityNode(
                entity_id=entity_id,
                label=port.entity,
                token_indices=port.token_indices,
                surface_form=port.surface_form,
                implicit=len(port.token_indices) == 0,
                confidence=float(port.confidence),
                candidate_only=True,
            )
            previous = entities_by_id.get(entity_id)
            if previous is None:
                entities_by_id[entity_id] = entity
            elif previous != entity:
                raise ValueError("relation entity identity collision")

            normalized_role = normalized.get(
                (port.grammatical_case, port.operator_role, port.entity, port.token_indices)
            )
            incidences.append(RelationIncidence(
                incidence_id=f"{event_id}:port:{position}",
                event_id=event_id,
                entity_id=entity_id,
                source_frame_id=frame.frame_id,
                grammatical_case=port.grammatical_case.value,
                operator_role=port.operator_role,
                token_indices=port.token_indices,
                adposition=port.adposition,
                universal_role=(
                    normalized_role.universal_role.value if normalized_role else None
                ),
                normalization_basis=(
                    normalized_role.normalization_basis if normalized_role else None
                ),
                confidence=float(port.confidence),
                candidate_only=True,
            ))

    if not events:
        return None
    return RelationHypergraph.create(
        equation_id=equation_id,
        language_id=result.language_id,
        entities=list(entities_by_id.values()),
        events=events,
        incidences=incidences,
    )


__all__ = [
    "RELATION_HYPERGRAPH_SCHEMA",
    "RelationEntityNode",
    "RelationEventNode",
    "RelationHypergraph",
    "RelationIncidence",
    "build_relation_hypergraph",
]
