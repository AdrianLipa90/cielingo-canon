"""Loss-aware card-identity receipts for relation-hypergraph entities."""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
import string
from typing import Any

from cielingo_core.regional.base import CardCandidate, RegionalSolveResult
from .relation_hypergraph import RelationEntityNode, RelationHypergraph


RELATION_ENTITY_CARD_BINDINGS_SCHEMA = "CIEL_RELATION_ENTITY_CARD_BINDINGS_V0_1"
CARD_BINDING_BASIS = "REGIONAL_CARD_CANDIDATE_TOKEN_CONTINUITY"
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


@dataclass(frozen=True)
class RelationEntityCardBinding:
    binding_id: str
    entity_id: str
    card_id: str
    slot_id: int
    language_id: str
    lemma: str | None
    token_indices: tuple[int, ...]
    score: float
    needs_native_review: bool
    basis: str = CARD_BINDING_BASIS
    candidate_only: bool = True

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.binding_id:
            issues.append("card binding binding_id is required")
        if not self.entity_id:
            issues.append("card binding entity_id is required")
        if not self.card_id:
            issues.append("card binding card_id is required")
        if self.slot_id <= 0:
            issues.append("card binding slot_id must be positive")
        if not self.language_id:
            issues.append("card binding language_id is required")
        if not self.token_indices:
            issues.append("card binding token_indices must be non-empty")
        if any(index < 0 for index in self.token_indices):
            issues.append("card binding token_indices must be non-negative")
        if not _bounded01(self.score):
            issues.append("card binding score must be in [0,1]")
        if not isinstance(self.needs_native_review, bool):
            issues.append("card binding needs_native_review must be boolean")
        if self.basis != CARD_BINDING_BASIS:
            issues.append("card binding basis mismatch")
        if not self.candidate_only:
            issues.append("card binding v0.1 must remain candidate-only")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "binding_id": self.binding_id,
            "entity_id": self.entity_id,
            "card_id": self.card_id,
            "slot_id": self.slot_id,
            "language_id": self.language_id,
            "lemma": self.lemma,
            "token_indices": list(self.token_indices),
            "score": self.score,
            "needs_native_review": self.needs_native_review,
            "basis": self.basis,
            "candidate_only": self.candidate_only,
        }


@dataclass(frozen=True)
class RelationEntityCardBindings:
    equation_id: str
    language_id: str
    relation_hypergraph_commitment: str
    bindings: tuple[RelationEntityCardBinding, ...]
    ambiguous_entity_ids: tuple[str, ...]
    unbound_entity_ids: tuple[str, ...]
    implicit_entity_ids: tuple[str, ...]
    commitment: str
    candidate_only: bool = True
    schema: str = RELATION_ENTITY_CARD_BINDINGS_SCHEMA

    @classmethod
    def create(
        cls,
        *,
        equation_id: str,
        language_id: str,
        relation_hypergraph_commitment: str,
        bindings: tuple[RelationEntityCardBinding, ...] | list[RelationEntityCardBinding],
        ambiguous_entity_ids: tuple[str, ...] | list[str] = (),
        unbound_entity_ids: tuple[str, ...] | list[str] = (),
        implicit_entity_ids: tuple[str, ...] | list[str] = (),
    ) -> "RelationEntityCardBindings":
        provisional = cls(
            equation_id=equation_id,
            language_id=language_id,
            relation_hypergraph_commitment=relation_hypergraph_commitment,
            bindings=tuple(bindings),
            ambiguous_entity_ids=tuple(ambiguous_entity_ids),
            unbound_entity_ids=tuple(unbound_entity_ids),
            implicit_entity_ids=tuple(implicit_entity_ids),
            commitment="",
        )
        receipt = replace(provisional, commitment=_digest(provisional.to_binding_dict()))
        issues = receipt.validate()
        if issues:
            raise ValueError("; ".join(issues))
        return receipt

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.equation_id:
            issues.append("card bindings equation_id is required")
        if not self.language_id:
            issues.append("card bindings language_id is required")
        if not _is_sha256(self.relation_hypergraph_commitment):
            issues.append("card bindings relation_hypergraph_commitment must be SHA-256")
        if not self.candidate_only:
            issues.append("card bindings v0.1 must remain candidate-only")

        binding_ids = [binding.binding_id for binding in self.bindings]
        bound_entity_ids = [binding.entity_id for binding in self.bindings]
        if len(set(binding_ids)) != len(binding_ids):
            issues.append("card binding IDs must be unique")
        if len(set(bound_entity_ids)) != len(bound_entity_ids):
            issues.append("an entity may have at most one admitted card binding")

        for binding in self.bindings:
            issues.extend(binding.validate())
            if binding.language_id != self.language_id:
                issues.append(f"card binding {binding.binding_id} language mismatch")

        partitions = {
            "bound": set(bound_entity_ids),
            "ambiguous": set(self.ambiguous_entity_ids),
            "unbound": set(self.unbound_entity_ids),
            "implicit": set(self.implicit_entity_ids),
        }
        raw_partitions = {
            "ambiguous": self.ambiguous_entity_ids,
            "unbound": self.unbound_entity_ids,
            "implicit": self.implicit_entity_ids,
        }
        for name, values in raw_partitions.items():
            if len(set(values)) != len(values):
                issues.append(f"card bindings {name} entity IDs must be unique")
            if any(not str(value).strip() for value in values):
                issues.append(f"card bindings {name} entity IDs must be non-empty")

        names = tuple(partitions)
        for index, left_name in enumerate(names):
            for right_name in names[index + 1 :]:
                if partitions[left_name] & partitions[right_name]:
                    issues.append(
                        f"card bindings entity partition overlap: {left_name}/{right_name}"
                    )

        if not _is_sha256(self.commitment):
            issues.append("card bindings commitment must be SHA-256")
        elif self.commitment != _digest(self.to_binding_dict()):
            issues.append("card bindings commitment mismatch")
        return issues

    def validate_against_hypergraph(self, graph: RelationHypergraph) -> list[str]:
        """Validate exact graph↔card-receipt continuity without inferring identity."""
        issues: list[str] = []
        if self.equation_id != graph.equation_id:
            issues.append("relation entity card bindings equation_id mismatch")
        if self.language_id != graph.language_id:
            issues.append("relation entity card bindings language mismatch")
        if self.relation_hypergraph_commitment != graph.commitment:
            issues.append("relation entity card bindings hypergraph commitment mismatch")

        graph_by_id = {entity.entity_id: entity for entity in graph.entities}
        graph_entity_ids = set(graph_by_id)
        receipt_entity_ids = (
            {binding.entity_id for binding in self.bindings}
            | set(self.ambiguous_entity_ids)
            | set(self.unbound_entity_ids)
            | set(self.implicit_entity_ids)
        )
        if receipt_entity_ids != graph_entity_ids:
            issues.append("relation entity card bindings entity partition mismatch")

        for binding in self.bindings:
            entity = graph_by_id.get(binding.entity_id)
            if entity is None:
                issues.append(f"card binding {binding.binding_id} references unknown entity")
                continue
            if entity.implicit:
                issues.append(f"card binding {binding.binding_id} cannot bind implicit entity")
            if binding.token_indices != entity.token_indices:
                issues.append(f"card binding {binding.binding_id} token-index mismatch")

        for entity_id in self.implicit_entity_ids:
            entity = graph_by_id.get(entity_id)
            if entity is None or not entity.implicit:
                issues.append("card bindings implicit partition contains explicit/unknown entity")
        for entity_id in (
            set(self.ambiguous_entity_ids) | set(self.unbound_entity_ids)
        ):
            entity = graph_by_id.get(entity_id)
            if entity is not None and entity.implicit:
                issues.append("card bindings explicit partition contains implicit entity")
        return issues

    def binding_for_entity(self, entity_id: str) -> RelationEntityCardBinding | None:
        matches = [binding for binding in self.bindings if binding.entity_id == entity_id]
        if len(matches) > 1:
            raise ValueError("multiple admitted card bindings for entity")
        return matches[0] if matches else None

    def to_binding_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "equation_id": self.equation_id,
            "language_id": self.language_id,
            "relation_hypergraph_commitment": self.relation_hypergraph_commitment,
            "bindings": [binding.to_dict() for binding in self.bindings],
            "ambiguous_entity_ids": list(self.ambiguous_entity_ids),
            "unbound_entity_ids": list(self.unbound_entity_ids),
            "implicit_entity_ids": list(self.implicit_entity_ids),
            "candidate_only": self.candidate_only,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.to_binding_dict(), "commitment": self.commitment}


def _matching_candidates(
    entity: RelationEntityNode,
    result: RegionalSolveResult,
) -> list[CardCandidate]:
    return [
        candidate
        for candidate in result.candidates
        if candidate.language_id == result.language_id
        and tuple(candidate.token_indices) == entity.token_indices
    ]


def _select_candidate(candidates: list[CardCandidate]) -> CardCandidate:
    return sorted(
        candidates,
        key=lambda candidate: (
            -float(candidate.score),
            int(candidate.slot_id),
            str(candidate.lemma or ""),
            bool(candidate.needs_native_review),
        ),
    )[0]


def build_relation_entity_card_bindings(
    result: RegionalSolveResult,
    relation_hypergraph: RelationHypergraph | None,
    *,
    equation_id: str,
) -> RelationEntityCardBindings | None:
    """Bind explicit relation entities to exact regional card-candidate evidence.

    Identity is admitted only through exact token-index continuity and one distinct
    ``card_id``. ``slot_id`` is preserved as provenance but is never used to
    establish identity. Ambiguity is recorded and fails closed for that entity.
    """
    if relation_hypergraph is None:
        return None
    if relation_hypergraph.equation_id != equation_id:
        raise ValueError("relation hypergraph equation_id mismatch")
    if relation_hypergraph.language_id != result.language_id:
        raise ValueError("relation hypergraph language mismatch")

    bindings: list[RelationEntityCardBinding] = []
    ambiguous: list[str] = []
    unbound: list[str] = []
    implicit: list[str] = []

    for entity in relation_hypergraph.entities:
        if entity.implicit:
            implicit.append(entity.entity_id)
            continue

        candidates = _matching_candidates(entity, result)
        by_card_id: dict[str, list[CardCandidate]] = {}
        for candidate in candidates:
            by_card_id.setdefault(candidate.card_id, []).append(candidate)

        if not by_card_id:
            unbound.append(entity.entity_id)
            continue
        if len(by_card_id) != 1:
            ambiguous.append(entity.entity_id)
            continue

        card_id, same_identity = next(iter(by_card_id.items()))
        selected = _select_candidate(same_identity)
        binding_id = "cardbind:" + _digest({
            "equation_id": equation_id,
            "entity_id": entity.entity_id,
            "card_id": card_id,
            "token_indices": list(entity.token_indices),
        })[:24]
        bindings.append(RelationEntityCardBinding(
            binding_id=binding_id,
            entity_id=entity.entity_id,
            card_id=card_id,
            slot_id=int(selected.slot_id),
            language_id=selected.language_id,
            lemma=selected.lemma,
            token_indices=entity.token_indices,
            score=float(selected.score),
            needs_native_review=bool(selected.needs_native_review),
            basis=CARD_BINDING_BASIS,
            candidate_only=True,
        ))

    receipt = RelationEntityCardBindings.create(
        equation_id=equation_id,
        language_id=result.language_id,
        relation_hypergraph_commitment=relation_hypergraph.commitment,
        bindings=bindings,
        ambiguous_entity_ids=ambiguous,
        unbound_entity_ids=unbound,
        implicit_entity_ids=implicit,
    )
    issues = receipt.validate_against_hypergraph(relation_hypergraph)
    if issues:
        raise ValueError("; ".join(issues))
    return receipt


__all__ = [
    "CARD_BINDING_BASIS",
    "RELATION_ENTITY_CARD_BINDINGS_SCHEMA",
    "RelationEntityCardBinding",
    "RelationEntityCardBindings",
    "build_relation_entity_card_bindings",
]
