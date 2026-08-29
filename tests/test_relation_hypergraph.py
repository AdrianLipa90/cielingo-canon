from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from cielingo_core.language_spaces.pl.solver import PolishRegionalSolver
from cielingo_core.lingophysics import build_relation_hypergraph
from cielingo_core.lingophysics.sentence_equation import calculate_sentence_equation


REPO_ROOT = Path(__file__).resolve().parents[1]


def _solve(text: str):
    return PolishRegionalSolver(REPO_ROOT).solve(text)


def test_gives_builds_one_nary_event_with_three_typed_incidences() -> None:
    result = _solve("Daję Zosi książkę")
    graph = build_relation_hypergraph(result, equation_id="eq-gives")
    assert graph is not None
    assert graph.validate() == []
    assert len(graph.events) == 1
    assert len(graph.entities) == 3
    assert len(graph.incidences) == 3

    event = graph.events[0]
    assert event.operator == "GIVES"
    assert event.directional is True
    assert event.symmetric is False
    incidences = graph.incidences_for_event(event.event_id)
    by_role = {incidence.operator_role: incidence for incidence in incidences}
    assert by_role["giver"].grammatical_case == "NOM"
    assert by_role["recipient"].grammatical_case == "DAT"
    assert by_role["transferred_object"].grammatical_case == "ACC"
    assert by_role["giver"].universal_role == "AGENT"
    assert by_role["recipient"].universal_role == "RECIPIENT"
    assert by_role["transferred_object"].universal_role == "THEME"


def test_implicit_first_person_is_preserved_as_entity_node() -> None:
    graph = build_relation_hypergraph(_solve("Daję Zosi książkę"), equation_id="eq-gives")
    assert graph is not None
    implicit = [entity for entity in graph.entities if entity.implicit]
    assert len(implicit) == 1
    assert implicit[0].label == "ja"
    assert implicit[0].token_indices == ()
    event_ids = [event.event_id for event in graph.events_for_entity(implicit[0].entity_id)]
    assert event_ids == [graph.events[0].event_id]


def test_connected_with_is_symmetric_event_without_fake_instrument_role() -> None:
    graph = build_relation_hypergraph(
        _solve("Informacja jest związana z geometrią"),
        equation_id="eq-connected",
    )
    assert graph is not None
    event = graph.events[0]
    assert event.operator == "CONNECTED_WITH"
    assert event.symmetric is True
    assert event.directional is False
    incidences = graph.incidences_for_event(event.event_id)
    assert {incidence.grammatical_case for incidence in incidences} == {"NOM", "INS"}
    assert all(incidence.universal_role is None for incidence in incidences)
    assert all(incidence.normalization_basis is None for incidence in incidences)


def test_names_keeps_assigned_name_as_operator_role_not_instrument() -> None:
    graph = build_relation_hypergraph(_solve("Nazwałem cię Zosią"), equation_id="eq-names")
    assert graph is not None
    assigned = next(
        incidence for incidence in graph.incidences if incidence.operator_role == "assigned_name"
    )
    assert assigned.grammatical_case == "INS"
    assert assigned.universal_role is None
    assert assigned.normalization_basis is None


def test_hypergraph_commitment_detects_event_mutation() -> None:
    graph = build_relation_hypergraph(_solve("Daję Zosi książkę"), equation_id="eq-gives")
    assert graph is not None
    changed_event = replace(graph.events[0], operator="TAKES")
    changed = replace(graph, events=(changed_event,))
    assert "relation hypergraph commitment mismatch" in changed.validate()


def test_hypergraph_rejects_dangling_incidence() -> None:
    graph = build_relation_hypergraph(_solve("Daję Zosi książkę"), equation_id="eq-gives")
    assert graph is not None
    dangling = replace(graph.incidences[0], entity_id="entity:missing")
    changed = replace(graph, incidences=(dangling, *graph.incidences[1:]))
    issues = changed.validate()
    assert any("unknown entity" in issue for issue in issues)


def test_sentence_equation_serializes_relation_hypergraph_additively() -> None:
    equation = calculate_sentence_equation(_solve("Daję Zosi książkę"))
    assert equation.relation_hypergraph is not None
    assert equation.relation_hypergraph.validate() == []
    serialized = equation.to_dict()
    assert serialized["relation_hypergraph"]["commitment"] == equation.relation_hypergraph.commitment
    assert equation.validate() == []


def test_non_relational_legacy_sentence_does_not_gain_hypergraph_field() -> None:
    equation = calculate_sentence_equation(_solve("Człowiek buduje dom."))
    assert equation.relation_hypergraph is None
    assert "relation_hypergraph" not in equation.to_dict()
    assert equation.validate() == []
