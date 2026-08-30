"""Additive transport packet joining SentenceEquation with named-entity identity."""

from __future__ import annotations

from dataclasses import dataclass, replace
from hashlib import sha256
import json
from typing import Any

from cielingo_core.regional.base import RegionalSolveResult
from .relation_entity_name_bindings import (
    RelationEntityNameBindings,
    build_relation_entity_name_bindings,
)
from .sentence_equation import SentenceEquation, calculate_sentence_equation


RELATION_IDENTITY_PACKET_SCHEMA = "CIEL_RELATION_IDENTITY_PACKET_V0_1"


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
class RelationIdentityPacket:
    sentence_equation: SentenceEquation
    relation_entity_name_bindings: RelationEntityNameBindings | None
    commitment: str
    candidate_only: bool = True
    schema: str = RELATION_IDENTITY_PACKET_SCHEMA

    @classmethod
    def create(
        cls,
        *,
        sentence_equation: SentenceEquation,
        relation_entity_name_bindings: RelationEntityNameBindings | None,
    ) -> "RelationIdentityPacket":
        provisional = cls(
            sentence_equation=sentence_equation,
            relation_entity_name_bindings=relation_entity_name_bindings,
            commitment="",
        )
        packet = replace(provisional, commitment=_digest(provisional.to_binding_dict()))
        issues = packet.validate()
        if issues:
            raise ValueError("; ".join(issues))
        return packet

    def validate(self) -> list[str]:
        issues = list(self.sentence_equation.validate())
        if not self.candidate_only:
            issues.append("relation identity packet must remain candidate-only")
        graph = self.sentence_equation.relation_hypergraph
        cards = self.sentence_equation.relation_entity_card_bindings
        names = self.relation_entity_name_bindings
        if names is not None:
            issues.extend(names.validate())
            if graph is None or cards is None:
                issues.append("name bindings require graph and card bindings")
            else:
                issues.extend(names.validate_against(graph, cards))
        if self.commitment != _digest(self.to_binding_dict()):
            issues.append("relation identity packet commitment mismatch")
        return issues

    def to_binding_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "sentence_equation": self.sentence_equation.to_dict(),
            "relation_entity_name_bindings": (
                None
                if self.relation_entity_name_bindings is None
                else self.relation_entity_name_bindings.to_dict()
            ),
            "candidate_only": self.candidate_only,
        }

    def to_dict(self) -> dict[str, Any]:
        return {**self.to_binding_dict(), "commitment": self.commitment}

    def to_augmented_sentence_equation(self) -> dict[str, Any]:
        payload = self.sentence_equation.to_dict()
        if self.relation_entity_name_bindings is not None:
            payload["relation_entity_name_bindings"] = self.relation_entity_name_bindings.to_dict()
        payload["relation_identity_packet_commitment"] = self.commitment
        return payload


def build_relation_identity_packet(result: RegionalSolveResult) -> RelationIdentityPacket:
    equation = calculate_sentence_equation(result)
    names = build_relation_entity_name_bindings(
        equation.relation_hypergraph,
        equation.relation_entity_card_bindings,
        equation_id=equation.equation_id,
    )
    return RelationIdentityPacket.create(
        sentence_equation=equation,
        relation_entity_name_bindings=names,
    )


__all__ = [
    "RELATION_IDENTITY_PACKET_SCHEMA",
    "RelationIdentityPacket",
    "build_relation_identity_packet",
]
