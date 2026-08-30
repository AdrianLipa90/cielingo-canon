from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from cielingo_core.language_spaces.pl.solver import PolishRegionalSolver
from cielingo_core.lingophysics import (
    CARD_BINDING_BASIS,
    build_relation_entity_card_bindings,
    build_relation_hypergraph,
)
from cielingo_core.lingophysics.sentence_equation import calculate_sentence_equation
from cielingo_core.regional.base import CardCandidate


REPO_ROOT = Path(__file__).resolve().parents[1]


def _solve(text: str):
    return PolishRegionalSolver(REPO_ROOT).solve(text)


def test_gives_preserves_book_card_identity_without_forcing_other_entities() -> None:
    result = _solve("Daję Zosi książkę")
    graph = build_relation_hypergraph(result, equation_id="eq-gives-card")
    assert graph is not None

    receipt = build_relation_entity_card_bindings(
        result,
        graph,
        equation_id="eq-gives-card",
    )
    assert receipt is not None
    assert receipt.validate() == []
    assert len(receipt.bindings) == 1
    binding = receipt.bindings[0]
    assert binding.card_id == "concept:book"
    assert binding.slot_id == 999
    assert binding.basis == CARD_BINDING_BASIS
    assert len(receipt.unbound_entity_ids) == 1
    assert len(receipt.implicit_entity_ids) == 1
    assert receipt.ambiguous_entity_ids == ()


def test_same_slot_different_card_ids_fail_closed_as_ambiguity() -> None:
    result = _solve("Daję Zosi książkę")
    book = next(candidate for candidate in result.candidates if candidate.card_id == "concept:book")
    result.candidates.append(CardCandidate(
        card_id="concept:decoy",
        slot_id=book.slot_id,
        language_id=book.language_id,
        lemma="wabik",
        token_indices=list(book.token_indices),
        score=book.score,
        needs_native_review=False,
    ))
    graph = build_relation_hypergraph(result, equation_id="eq-ambiguous-card")
    assert graph is not None
    receipt = build_relation_entity_card_bindings(
        result,
        graph,
        equation_id="eq-ambiguous-card",
    )
    assert receipt is not None

    book_entity = next(
        entity for entity in graph.entities if entity.token_indices == tuple(book.token_indices)
    )
    assert receipt.binding_for_entity(book_entity.entity_id) is None
    assert book_entity.entity_id in receipt.ambiguous_entity_ids


def test_card_candidate_on_wrong_token_cannot_bind_entity() -> None:
    result = _solve("Daję Zosi książkę")
    book = next(candidate for candidate in result.candidates if candidate.card_id == "concept:book")
    result.candidates = [
        candidate for candidate in result.candidates if candidate.card_id != "concept:book"
    ]
    result.candidates.append(CardCandidate(
        card_id="concept:book",
        slot_id=book.slot_id,
        language_id=book.language_id,
        lemma=book.lemma,
        token_indices=[0],
        score=book.score,
        needs_native_review=False,
    ))
    graph = build_relation_hypergraph(result, equation_id="eq-wrong-token")
    assert graph is not None
    receipt = build_relation_entity_card_bindings(
        result,
        graph,
        equation_id="eq-wrong-token",
    )
    assert receipt is not None

    transferred = next(
        incidence for incidence in graph.incidences if incidence.operator_role == "transferred_object"
    )
    assert receipt.binding_for_entity(transferred.entity_id) is None
    assert transferred.entity_id in receipt.unbound_entity_ids


def test_implicit_entity_never_receives_lexical_card_binding() -> None:
    result = _solve("Daję Zosi książkę")
    graph = build_relation_hypergraph(result, equation_id="eq-implicit")
    assert graph is not None
    receipt = build_relation_entity_card_bindings(result, graph, equation_id="eq-implicit")
    assert receipt is not None

    implicit = next(entity for entity in graph.entities if entity.implicit)
    assert implicit.entity_id in receipt.implicit_entity_ids
    assert receipt.binding_for_entity(implicit.entity_id) is None


def test_sentence_equation_serializes_card_receipt_after_hypergraph() -> None:
    equation = calculate_sentence_equation(_solve("Daję Zosi książkę"))
    assert equation.relation_hypergraph is not None
    assert equation.relation_entity_card_bindings is not None
    assert equation.validate() == []

    serialized = equation.to_dict()
    assert serialized["relation_hypergraph"]["commitment"] == equation.relation_hypergraph.commitment
    assert (
        serialized["relation_entity_card_bindings"]["commitment"]
        == equation.relation_entity_card_bindings.commitment
    )
    assert list(serialized).index("relation_entity_card_bindings") > list(serialized).index(
        "relation_hypergraph"
    )


def test_non_relational_sentence_has_no_card_binding_receipt() -> None:
    equation = calculate_sentence_equation(_solve("Człowiek buduje dom."))
    assert equation.relation_hypergraph is None
    assert equation.relation_entity_card_bindings is None
    assert "relation_entity_card_bindings" not in equation.to_dict()


def test_receipt_commitment_detects_card_identity_mutation() -> None:
    equation = calculate_sentence_equation(_solve("Daję Zosi książkę"))
    receipt = equation.relation_entity_card_bindings
    assert receipt is not None and receipt.bindings

    changed_binding = replace(receipt.bindings[0], card_id="concept:mutated")
    changed = replace(receipt, bindings=(changed_binding, *receipt.bindings[1:]))
    assert "card bindings commitment mismatch" in changed.validate()


def test_receipt_requires_exact_relation_entity_partition() -> None:
    equation = calculate_sentence_equation(_solve("Daję Zosi książkę"))
    receipt = equation.relation_entity_card_bindings
    assert receipt is not None and receipt.unbound_entity_ids

    changed = replace(receipt, unbound_entity_ids=())
    equation.relation_entity_card_bindings = changed
    issues = equation.validate()
    assert "relation entity card bindings entity partition mismatch" in issues
