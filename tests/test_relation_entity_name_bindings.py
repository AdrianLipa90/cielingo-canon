from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from cielingo_core.language_spaces.pl.solver import PolishRegionalSolver
from cielingo_core.lingophysics.relation_entity_card_bindings import (
    RelationEntityCardBindings,
    build_relation_entity_card_bindings,
)
from cielingo_core.lingophysics.relation_entity_name_bindings import (
    NAME_BINDING_BASIS,
    RelationEntityNameBindings,
    build_relation_entity_name_bindings,
)
from cielingo_core.lingophysics.relation_hypergraph import build_relation_hypergraph


REPO_ROOT = Path(__file__).resolve().parents[1]


def _build(text: str, equation_id: str):
    result = PolishRegionalSolver(REPO_ROOT).solve(text)
    graph = build_relation_hypergraph(result, equation_id=equation_id)
    assert graph is not None
    cards = build_relation_entity_card_bindings(result, graph, equation_id=equation_id)
    assert cards is not None
    names = build_relation_entity_name_bindings(graph, cards, equation_id=equation_id)
    assert names is not None
    return graph, cards, names


def test_gives_binds_zosi_as_name_but_book_as_card() -> None:
    graph, cards, names = _build("Daję Zosi książkę", "eq-name-gives")
    assert cards.validate_against_hypergraph(graph) == []
    assert names.validate_against(graph, cards) == []
    assert {binding.card_id for binding in cards.bindings} == {"concept:book"}
    assert len(names.bindings) == 1
    binding = names.bindings[0]
    assert binding.source_label == "Zosi"
    assert binding.grammatical_case == "DAT"
    assert binding.operator_role == "recipient"
    assert binding.basis == NAME_BINDING_BASIS


def test_names_relation_keeps_cat_card_and_adrian_luna_names() -> None:
    graph, cards, names = _build("Adrian nazywa kota Luną", "eq-name-names")
    assert {binding.card_id for binding in cards.bindings} == {"concept:cat"}
    assert {binding.source_label for binding in names.bindings} == {"Adrian", "Luną"}
    by_label = {binding.source_label: binding for binding in names.bindings}
    assert by_label["Adrian"].grammatical_case == "NOM"
    assert by_label["Luną"].grammatical_case == "INS"


def test_card_bound_capitalized_entity_is_not_duplicated_as_name() -> None:
    graph, cards, names = _build("Graf jest połączony z geometrią", "eq-name-card-priority")
    assert {binding.card_id for binding in cards.bindings} == {"concept:graph", "concept:geometry"}
    assert names.bindings == ()


def test_implicit_subject_never_receives_name_binding() -> None:
    graph, cards, names = _build("Daję Zosi książkę", "eq-name-implicit")
    implicit_ids = {entity.entity_id for entity in graph.entities if entity.implicit}
    assert implicit_ids
    assert implicit_ids.isdisjoint({binding.entity_id for binding in names.bindings})


def test_lowercase_unbound_entity_is_not_promoted_to_name() -> None:
    graph, cards, names = _build("moduł należy do nieznanego", "eq-name-lowercase")
    assert all(binding.source_label != "nieznanego" for binding in names.bindings)


def test_rehashed_wrong_graph_commitment_fails_cross_validation() -> None:
    graph, cards, names = _build("Daję Zosi książkę", "eq-name-forged-graph")
    forged = RelationEntityNameBindings.create(
        equation_id=names.equation_id,
        language_id=names.language_id,
        relation_hypergraph_commitment="a" * 64,
        card_bindings_commitment=names.card_bindings_commitment,
        bindings=names.bindings,
    )
    assert forged.validate() == []
    assert "name bindings hypergraph commitment mismatch" in forged.validate_against(graph, cards)


def test_rehashed_wrong_card_receipt_commitment_fails_cross_validation() -> None:
    graph, cards, names = _build("Daję Zosi książkę", "eq-name-forged-card")
    forged = RelationEntityNameBindings.create(
        equation_id=names.equation_id,
        language_id=names.language_id,
        relation_hypergraph_commitment=names.relation_hypergraph_commitment,
        card_bindings_commitment="b" * 64,
        bindings=names.bindings,
    )
    assert forged.validate() == []
    assert "name bindings card receipt commitment mismatch" in forged.validate_against(graph, cards)


def test_name_binding_cannot_rescue_ambiguous_card_identity() -> None:
    graph, cards, names = _build("Daję Zosi książkę", "eq-name-ambiguous")
    assert names.bindings
    target = names.bindings[0]
    forged_cards = RelationEntityCardBindings.create(
        equation_id=cards.equation_id,
        language_id=cards.language_id,
        relation_hypergraph_commitment=cards.relation_hypergraph_commitment,
        bindings=cards.bindings,
        ambiguous_entity_ids=(*cards.ambiguous_entity_ids, target.entity_id),
        unbound_entity_ids=tuple(
            entity_id for entity_id in cards.unbound_entity_ids if entity_id != target.entity_id
        ),
        implicit_entity_ids=cards.implicit_entity_ids,
    )
    assert any(
        "cannot rescue ambiguous card identity" in issue
        for issue in names.validate_against(graph, forged_cards)
    )


def test_raw_name_binding_mutation_breaks_commitment() -> None:
    _, _, names = _build("Daję Zosi książkę", "eq-name-mutation")
    assert names.bindings
    changed = replace(names.bindings[0], source_label="Mutated")
    tampered = replace(names, bindings=(changed, *names.bindings[1:]))
    assert "name bindings commitment mismatch" in tampered.validate()
