from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from cielingo_core.global_layer import MeaningRoleBinding, MeaningRoleMultimap, UniversalRole
from cielingo_core.language_spaces.pl.solver import PolishRegionalSolver
from cielingo_core.lingophysics.sentence_equation import EquationTermKind, calculate_sentence_equation


REPO_ROOT = Path(__file__).resolve().parents[1]
SIG = "a" * 64


def _binding(binding_id: str, entity: str) -> MeaningRoleBinding:
    return MeaningRoleBinding(
        binding_id=binding_id,
        universal_role=UniversalRole.AGENT,
        entity=entity,
        operator="TEST_RELATION",
        operator_role="actor",
        grammatical_case="NOM",
        token_indices=(0,),
        source_frame_id="frame-test",
        signature_id="TEST_RELATION@0.1.0",
        signature_commitment=SIG,
        normalization_basis="TEST_OPERATOR_ROLE_AS_AGENT",
        confidence=0.9,
    )


def test_role_multimap_preserves_multiple_bindings_for_same_universal_role() -> None:
    multimap = MeaningRoleMultimap.create(
        equation_id="eq-test",
        bindings=[_binding("b1", "A"), _binding("b2", "B")],
    )
    agents = multimap.by_role(UniversalRole.AGENT)
    assert [binding.entity for binding in agents] == ["A", "B"]
    assert len(multimap.commitment) == 64
    assert multimap.validate() == []


def test_role_multimap_commitment_detects_mutation() -> None:
    multimap = MeaningRoleMultimap.create(
        equation_id="eq-test",
        bindings=[_binding("b1", "A")],
    )
    mutated = replace(multimap, bindings=(_binding("b1", "B"),))
    assert "role multimap commitment mismatch" in mutated.validate()


def test_duplicate_binding_ids_are_rejected() -> None:
    first = _binding("duplicate", "A")
    second = _binding("duplicate", "B")
    try:
        MeaningRoleMultimap.create(equation_id="eq-test", bindings=[first, second])
    except ValueError as exc:
        assert "binding IDs must be unique" in str(exc)
    else:
        raise AssertionError("duplicate binding IDs must fail closed")


def test_gives_sentence_equation_emits_lossless_global_role_multimap() -> None:
    result = PolishRegionalSolver(REPO_ROOT).solve("Daję Zosi książkę")
    equation = calculate_sentence_equation(result)
    assert equation.role_multimap is not None
    multimap = equation.role_multimap
    assert multimap.validate() == []
    assert [binding.entity for binding in multimap.by_role(UniversalRole.AGENT)] == ["ja"]
    assert [binding.entity for binding in multimap.by_role(UniversalRole.RECIPIENT)] == ["Zosi"]
    assert [binding.entity for binding in multimap.by_role(UniversalRole.THEME)] == ["książkę"]
    assert all(binding.operator == "GIVES" for binding in multimap.bindings)
    assert all(binding.signature_id == "GIVES@0.1.0" for binding in multimap.bindings)
    assert all(len(binding.signature_commitment) == 64 for binding in multimap.bindings)
    serialized = equation.to_dict()
    assert serialized["role_multimap"]["commitment"] == multimap.commitment
    assert equation.validate() == []


def test_non_normalized_relation_keeps_case_roles_without_fake_global_role() -> None:
    result = PolishRegionalSolver(REPO_ROOT).solve("Informacja jest związana z geometrią")
    equation = calculate_sentence_equation(result)
    role_terms = [term for term in equation.terms if term.kind is EquationTermKind.ROLE]
    assert len(role_terms) == 2
    assert equation.role_multimap is None
    assert "role_multimap" not in equation.to_dict()
    assert equation.validate() == []
