"""Graph-bound candidate identity receipts for relation named entities."""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
import string
from typing import Any

from .relation_entity_card_bindings import RelationEntityCardBindings
from .relation_hypergraph import RelationHypergraph


RELATION_ENTITY_NAME_BINDINGS_SCHEMA = "CIEL_RELATION_ENTITY_NAME_BINDINGS_V0_1"
NAME_BINDING_BASIS = "CAPITALIZED_RELATION_ENTITY_WITHOUT_CARD_ID"
_HEX = frozenset(string.hexdigits)


def _digest(payload: Any) -> str:
    return sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(char in _HEX for char in value)


def _bounded01(value: float) -> bool:
    return 0.0 <= float(value) <= 1.0


def _looks_like_named_entity(label: str) -> bool:
    text = str(label).strip()
    first_alpha = next((char for char in text if char.isalpha()), "")
    return bool(first_alpha and first_alpha.isupper())


@dataclass(frozen=True)
class RelationEntityNameBinding:
    binding_id: str
    entity_id: str
    source_label: str
    surface_form: str
    grammatical_case: str
    operator_role: str
    token_indices: tuple[int, ...]
    confidence: float
    basis: str = NAME_BINDING_BASIS
    candidate_only: bool = True

    def validate(self) -> list[str]:
        issues: list[str] = []
        for name in (
            "binding_id",
            "entity_id",
            "source_label",
            "surface_form",
            "grammatical_case",
            "operator_role",
        ):
            if not str(getattr(self, name)).strip():
                issues.append(f"name binding {name} is required")
        if not self.token_indices:
            issues.append("name binding token_indices must be non-empty")
        if any(index < 0 for index in self.token_indices):
            issues.append("name binding token_indices must be non-negative")
        if not _bounded01(self.confidence):
            issues.append("name binding confidence must be in [0,1]")
        if self.basis != NAME_BINDING_BASIS:
            issues.append("name binding basis mismatch")
        if not self.candidate_only:
            issues.append("name binding v0.1 must remain candidate-only")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "binding_id": self.binding_id,
            "entity_id": self.entity_id,
            "source_label": self.source_label,
            "surface_form": self.surface_form,
            "grammatical_case": self.grammatical_case,
            "operator_role": self.operator_role,
            "token_indices": list(self.token_indices),
            "confidence": self.confidence,
            "basis": self.basis,
            "candidate_only": self.candidate_only,
        }


@dataclass(frozen=True)
class RelationEntityNameBindings:
    equation_id: str
    language_id: str
    relation_hypergraph_commitment: str
    card_bindings_commitment: str
    bindings: tuple[RelationEntityNameBinding, ...]
    commitment: str
    candidate_only: bool = True
    schema: str = RELATION_ENTITY_NAME_BINDINGS_SCHEMA

    @classmethod
    def create(
        cls,
        *,
        equation_id: str,
        language_id: str,
        relation_hypergraph_commitment: str,
        card_bindings_commitment: str,
        bindings: tuple[RelationEntityNameBinding, ...] | list[RelationEntityNameBinding],
    ) -> "RelationEntityNameBindings":
        provisional = cls(
            equation_id=equation_id,
            language_id=language_id,
            relation_hypergraph_commitment=relation_hypergraph_commitment,
            card_bindings_commitment=card_bindings_commitment,
            bindings=tuple(bindings),
            commitment="",
        )
        receipt = replace(provisional, commitment=_digest(provisional.to_binding_dict()))
        issues = receipt.validate()
        if issues:
            raise ValueError("; ".join(issues))
        return receipt

    def validate(self) -> list[str]:
        issues: list[str] = []
        if self.schema != RELATION_ENTITY_NAME_BINDINGS_SCHEMA:
            issues.append("name bindings schema mismatch")
        if not self.equation_id or not self.language_id:
            issues.append("name bindings equation/language are required")
        if not _is_sha256(self.relation_hypergraph_commitment):
            issues.append("name bindings relation_hypergraph_commitment must be SHA-256")
        if not _is_sha256(self.card_bindings_commitment):
            issues.append("name bindings card_bindings_commitment must be SHA-256")
        if not self.candidate_only:
            issues.append("name bindings v0.1 must remain candidate-only")
        ids = [binding.binding_id for binding in self.bindings]
        entity_ids = [binding.entity_id for binding in self.bindings]
        if len(set(ids)) != len(ids):
            issues.append("name binding IDs must be unique")
        if len(set(entity_ids)) != len(entity_ids):
            issues.append("an entity may have at most one name binding")
        for binding in self.bindings:
            issues.extend(binding.validate())
        if not _is_sha256(self.commitment):
            issues.append("name bindings commitment must be SHA-256")
        elif self.commitment != _digest(self.to_binding_dict()):
            issues.append("name bindings commitment mismatch")
        return issues

    def validate_against(
        self,
        graph: RelationHypergraph,
        cards: RelationEntityCardBindings,
    ) -> list[str]:
        issues: list[str] = []
        if self.equation_id != graph.equation_id or self.equation_id != cards.equation_id:
            issues.append("name bindings equation_id mismatch")
        if self.language_id != graph.language_id or self.language_id != cards.language_id:
            issues.append("name bindings language mismatch")
        if self.relation_hypergraph_commitment != graph.commitment:
            issues.append("name bindings hypergraph commitment mismatch")
        if self.card_bindings_commitment != cards.commitment:
            issues.append("name bindings card receipt commitment mismatch")
        if cards.relation_hypergraph_commitment != graph.commitment:
            issues.append("name bindings require card receipt bound to exact graph")

        graph_by_id = {entity.entity_id: entity for entity in graph.entities}
        card_bound = {binding.entity_id for binding in cards.bindings}
        card_ambiguous = set(cards.ambiguous_entity_ids)
        card_implicit = set(cards.implicit_entity_ids)
        incidences_by_entity: dict[str, list[Any]] = {}
        for incidence in graph.incidences:
            incidences_by_entity.setdefault(incidence.entity_id, []).append(incidence)

        for binding in self.bindings:
            entity = graph_by_id.get(binding.entity_id)
            if entity is None:
                issues.append(f"name binding {binding.binding_id} references unknown entity")
                continue
            if entity.implicit or binding.entity_id in card_implicit:
                issues.append(f"name binding {binding.binding_id} cannot bind implicit entity")
            if binding.entity_id in card_bound:
                issues.append(f"name binding {binding.binding_id} overlaps admitted card identity")
            if binding.entity_id in card_ambiguous:
                issues.append(f"name binding {binding.binding_id} cannot rescue ambiguous card identity")
            if binding.token_indices != entity.token_indices:
                issues.append(f"name binding {binding.binding_id} token-index mismatch")
            attached = incidences_by_entity.get(binding.entity_id, [])
            matches = [
                incidence
                for incidence in attached
                if incidence.grammatical_case == binding.grammatical_case
                and incidence.operator_role == binding.operator_role
                and incidence.token_indices == binding.token_indices
            ]
            if len(matches) != 1:
                issues.append(f"name binding {binding.binding_id} incidence continuity mismatch")
        return issues

    def binding_for_entity(self, entity_id: str) -> RelationEntityNameBinding | None:
        matches = [binding for binding in self.bindings if binding.entity_id == entity_id]
        if len(matches) > 1:
            raise ValueError("multiple admitted name bindings for entity")
        return matches[0] if matches else None

    def to_binding_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "equation_id": self.equation_id,
            "language_id": self.language_id,
            "relation_hypergraph_commitment": self.relation_hypergraph_commitment,
            "card_bindings_commitment": self.card_bindings_commitment,
            "bindings": [binding.to_dict() for binding in self.bindings],
            "candidate_only": self.candidate_only,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.to_binding_dict(), "commitment": self.commitment}


def build_relation_entity_name_bindings(
    graph: RelationHypergraph | None,
    cards: RelationEntityCardBindings | None,
    *,
    equation_id: str,
) -> RelationEntityNameBindings | None:
    """Admit bounded proper-name candidates after card identity has been evaluated."""
    if graph is None or cards is None:
        return None
    if graph.equation_id != equation_id or cards.equation_id != equation_id:
        raise ValueError("name binding equation_id mismatch")
    if cards.relation_hypergraph_commitment != graph.commitment:
        raise ValueError("name bindings require exact graph/card continuity")

    card_bound = {binding.entity_id for binding in cards.bindings}
    card_ambiguous = set(cards.ambiguous_entity_ids)
    card_implicit = set(cards.implicit_entity_ids)
    incidences_by_entity: dict[str, list[Any]] = {}
    for incidence in graph.incidences:
        incidences_by_entity.setdefault(incidence.entity_id, []).append(incidence)

    bindings: list[RelationEntityNameBinding] = []
    for entity in graph.entities:
        if entity.implicit or entity.entity_id in card_implicit:
            continue
        if entity.entity_id in card_bound or entity.entity_id in card_ambiguous:
            continue
        if not _looks_like_named_entity(entity.label):
            continue
        attached = incidences_by_entity.get(entity.entity_id, [])
        unique_ports = {
            (incidence.grammatical_case, incidence.operator_role, incidence.token_indices)
            for incidence in attached
        }
        if len(unique_ports) != 1:
            continue
        grammatical_case, operator_role, token_indices = next(iter(unique_ports))
        binding_id = "namebind:" + _digest({
            "equation_id": equation_id,
            "entity_id": entity.entity_id,
            "source_label": entity.label,
            "grammatical_case": grammatical_case,
            "operator_role": operator_role,
            "token_indices": list(token_indices),
        })[:24]
        bindings.append(RelationEntityNameBinding(
            binding_id=binding_id,
            entity_id=entity.entity_id,
            source_label=entity.label,
            surface_form=entity.surface_form,
            grammatical_case=grammatical_case,
            operator_role=operator_role,
            token_indices=token_indices,
            confidence=float(entity.confidence),
            candidate_only=True,
        ))

    receipt = RelationEntityNameBindings.create(
        equation_id=equation_id,
        language_id=graph.language_id,
        relation_hypergraph_commitment=graph.commitment,
        card_bindings_commitment=cards.commitment,
        bindings=bindings,
    )
    issues = receipt.validate_against(graph, cards)
    if issues:
        raise ValueError("; ".join(issues))
    return receipt


__all__ = [
    "NAME_BINDING_BASIS",
    "RELATION_ENTITY_NAME_BINDINGS_SCHEMA",
    "RelationEntityNameBinding",
    "RelationEntityNameBindings",
    "build_relation_entity_name_bindings",
]
