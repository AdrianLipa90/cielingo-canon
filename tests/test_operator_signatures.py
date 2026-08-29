from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from cielingo_core.global_layer.contracts import UniversalRole
from cielingo_core.language_spaces.pl.solver import PolishRegionalSolver
from cielingo_core.lingophysics import (
    CasePort,
    CasePortCase,
    CasePortFrame,
    get_operator_signature,
    type_case_port_frame,
)
from cielingo_core.lingophysics.sentence_equation import EquationTermKind, calculate_sentence_equation


REPO_ROOT = Path(__file__).resolve().parents[1]


def _frame(text: str):
    from cielingo_core.lingophysics import extract_polish_case_port_frames

    frames = extract_polish_case_port_frames(text)
    assert len(frames) == 1
    return frames[0]


def _note_map(notes: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for item in notes:
        if "=" in item:
            key, value = item.split("=", 1)
            out[key] = value
    return out


def test_all_reference_case_frames_match_operator_signatures() -> None:
    examples = [
        "Informacja jest związana z geometrią",
        "Moduł należy do systemu",
        "Rozmawiam o geometrii z Zosią",
        "Nazwałem cię Zosią",
        "Daję Zosi książkę",
        "Adrian opisuje teorię o geometrii",
        "Zosiu, spójrz tutaj",
    ]
    for text in examples:
        report = type_case_port_frame(_frame(text))
        assert report.signature_known is True
        assert report.valid is True
        assert report.missing_ports == ()
        assert report.unexpected_ports == ()
        assert report.adposition_mismatches == ()


def test_transfer_signature_normalizes_operator_roles_to_universal_roles() -> None:
    report = type_case_port_frame(_frame("Daję Zosi książkę"))
    by_role = {binding.operator_role: binding for binding in report.universal_roles}
    assert by_role["giver"].universal_role is UniversalRole.AGENT
    assert by_role["recipient"].universal_role is UniversalRole.RECIPIENT
    assert by_role["transferred_object"].universal_role is UniversalRole.THEME
    assert by_role["recipient"].grammatical_case is CasePortCase.DAT


def test_instrumental_case_is_not_normalized_by_case_alone() -> None:
    named = type_case_port_frame(_frame("Nazwałem cię Zosią"))
    connected = type_case_port_frame(_frame("Informacja jest związana z geometrią"))
    assert all(binding.grammatical_case is not CasePortCase.INS for binding in named.universal_roles)
    assert all(binding.grammatical_case is not CasePortCase.INS for binding in connected.universal_roles)
    assert all(binding.universal_role is not UniversalRole.INSTRUMENT for binding in named.universal_roles)
    assert all(binding.universal_role is not UniversalRole.INSTRUMENT for binding in connected.universal_roles)


def test_wrong_adposition_fails_closed_and_suppresses_universal_roles() -> None:
    frame = _frame("Rozmawiam o geometrii z Zosią")
    ports = list(frame.ports)
    idx = next(i for i, port in enumerate(ports) if port.operator_role == "topic")
    ports[idx] = replace(ports[idx], adposition="z")
    tampered = replace(frame, ports=tuple(ports))
    report = type_case_port_frame(tampered)
    assert report.signature_known is True
    assert report.valid is False
    assert report.adposition_mismatches
    assert report.universal_roles == ()


def test_unexpected_case_role_pair_fails_closed() -> None:
    frame = _frame("Informacja jest związana z geometrią")
    alien = CasePort(
        grammatical_case=CasePortCase.DAT,
        operator_role="recipient",
        entity="Zosi",
        token_indices=(0,),
        surface_form="Zosi",
        confidence=0.9,
    )
    tampered = replace(frame, ports=frame.ports + (alien,))
    report = type_case_port_frame(tampered)
    assert report.valid is False
    assert "DAT:recipient" in report.unexpected_ports
    assert report.universal_roles == ()


def test_unknown_operator_fails_closed() -> None:
    frame = CasePortFrame(
        frame_id="unknown-frame",
        language_id="pl",
        operator="UNKNOWN_RELATION",
        ports=(
            CasePort(
                grammatical_case=CasePortCase.NOM,
                operator_role="entity",
                entity="A",
                token_indices=(0,),
                surface_form="A",
            ),
        ),
        surface_text="A",
        evidence_basis="TEST",
    )
    report = type_case_port_frame(frame)
    assert report.signature_known is False
    assert report.valid is False
    assert report.signature_id is None
    assert report.universal_roles == ()


def test_signature_commitment_is_stable_and_operator_specific() -> None:
    gives = get_operator_signature("GIVES")
    names = get_operator_signature("NAMES")
    assert gives is not None and names is not None
    assert len(gives.signature_commitment) == 64
    assert gives.signature_commitment == get_operator_signature("gives").signature_commitment
    assert gives.signature_commitment != names.signature_commitment


def test_sentence_equation_carries_signature_gate_and_optional_universal_role() -> None:
    result = PolishRegionalSolver(REPO_ROOT).solve("Daję Zosi książkę")
    equation = calculate_sentence_equation(result)
    role_terms = [term for term in equation.terms if term.kind is EquationTermKind.ROLE]
    assert len(role_terms) == 3
    notes = {_note_map(term.notes)["operator_role"]: _note_map(term.notes) for term in role_terms}
    assert all(note["signature_known"] == "true" for note in notes.values())
    assert all(note["signature_valid"] == "true" for note in notes.values())
    assert notes["giver"]["universal_role"] == "AGENT"
    assert notes["recipient"]["universal_role"] == "RECIPIENT"
    assert notes["transferred_object"]["universal_role"] == "THEME"
    assert all(len(note["signature_commitment"]) == 64 for note in notes.values())
    assert equation.validate() == []


def test_symmetric_relation_is_explicit_in_signature_not_in_case() -> None:
    connected = get_operator_signature("CONNECTED_WITH")
    gives = get_operator_signature("GIVES")
    assert connected is not None and gives is not None
    assert connected.symmetric is True
    assert connected.directional is False
    assert gives.symmetric is False
    assert gives.directional is True
