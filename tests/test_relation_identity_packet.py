from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from cielingo_core.language_spaces.pl.solver import PolishRegionalSolver
from cielingo_core.lingophysics.relation_identity_packet import build_relation_identity_packet


REPO_ROOT = Path(__file__).resolve().parents[1]


def _packet(text: str):
    result = PolishRegionalSolver(REPO_ROOT).solve(text)
    return build_relation_identity_packet(result)


def test_packet_preserves_card_and_name_identity_without_mutating_sentence_equation_abi() -> None:
    packet = _packet("Daję Zosi książkę")
    assert packet.validate() == []
    equation = packet.sentence_equation
    assert equation.relation_hypergraph is not None
    assert equation.relation_entity_card_bindings is not None
    assert packet.relation_entity_name_bindings is not None
    assert {binding.card_id for binding in equation.relation_entity_card_bindings.bindings} == {"concept:book"}
    assert {binding.source_label for binding in packet.relation_entity_name_bindings.bindings} == {"Zosi"}
    assert not hasattr(equation, "relation_entity_name_bindings")


def test_augmented_sentence_equation_carries_name_receipt_after_existing_equation_serialization() -> None:
    packet = _packet("Adrian rozmawia z Zosią o geometrii")
    payload = packet.to_augmented_sentence_equation()
    assert payload["relation_hypergraph"]["commitment"] == packet.sentence_equation.relation_hypergraph.commitment
    assert payload["relation_entity_card_bindings"]["commitment"] == packet.sentence_equation.relation_entity_card_bindings.commitment
    assert payload["relation_entity_name_bindings"]["commitment"] == packet.relation_entity_name_bindings.commitment
    assert payload["relation_identity_packet_commitment"] == packet.commitment


def test_card_bound_graph_and_geometry_do_not_create_name_bindings() -> None:
    packet = _packet("Graf jest połączony z geometrią")
    assert packet.relation_entity_name_bindings is not None
    assert packet.relation_entity_name_bindings.bindings == ()


def test_packet_commitment_detects_name_receipt_mutation() -> None:
    packet = _packet("Daję Zosi książkę")
    names = packet.relation_entity_name_bindings
    assert names is not None and names.bindings
    changed_binding = replace(names.bindings[0], source_label="Mutated")
    changed_names = replace(names, bindings=(changed_binding, *names.bindings[1:]))
    changed_packet = replace(packet, relation_entity_name_bindings=changed_names)
    issues = changed_packet.validate()
    assert "name bindings commitment mismatch" in issues
    assert "relation identity packet commitment mismatch" in issues
