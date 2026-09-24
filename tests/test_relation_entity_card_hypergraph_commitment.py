from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from cielingo_core.language_spaces.pl.solver import PolishRegionalSolver
from cielingo_core.lingophysics import (
    RelationEntityCardBindings,
    build_relation_entity_card_bindings,
    build_relation_hypergraph,
)


REPO_ROOT = Path(__file__).resolve().parents[1]


def _receipt_and_graph():
    result = PolishRegionalSolver(REPO_ROOT).solve("Daję Zosi książkę")
    graph = build_relation_hypergraph(result, equation_id="eq-card-graph-binding")
    assert graph is not None
    receipt = build_relation_entity_card_bindings(
        result,
        graph,
        equation_id="eq-card-graph-binding",
    )
    assert receipt is not None
    return receipt, graph


def test_receipt_commitment_carries_exact_relation_hypergraph_commitment() -> None:
    receipt, graph = _receipt_and_graph()
    assert receipt.relation_hypergraph_commitment == graph.commitment
    assert receipt.validate() == []
    assert receipt.validate_against_hypergraph(graph) == []


def test_rehashed_receipt_for_different_graph_commitment_fails_cross_validation() -> None:
    receipt, graph = _receipt_and_graph()
    forged = RelationEntityCardBindings.create(
        equation_id=receipt.equation_id,
        language_id=receipt.language_id,
        relation_hypergraph_commitment="a" * 64,
        bindings=receipt.bindings,
        ambiguous_entity_ids=receipt.ambiguous_entity_ids,
        unbound_entity_ids=receipt.unbound_entity_ids,
        implicit_entity_ids=receipt.implicit_entity_ids,
    )
    assert forged.validate() == []
    assert (
        "relation entity card bindings hypergraph commitment mismatch"
        in forged.validate_against_hypergraph(graph)
    )


def test_rehashed_binding_with_wrong_token_span_fails_graph_continuity() -> None:
    receipt, graph = _receipt_and_graph()
    assert receipt.bindings
    changed_binding = replace(receipt.bindings[0], token_indices=(0,))
    forged = RelationEntityCardBindings.create(
        equation_id=receipt.equation_id,
        language_id=receipt.language_id,
        relation_hypergraph_commitment=graph.commitment,
        bindings=(changed_binding, *receipt.bindings[1:]),
        ambiguous_entity_ids=receipt.ambiguous_entity_ids,
        unbound_entity_ids=receipt.unbound_entity_ids,
        implicit_entity_ids=receipt.implicit_entity_ids,
    )
    assert forged.validate() == []
    assert any(
        "token-index mismatch" in issue
        for issue in forged.validate_against_hypergraph(graph)
    )
