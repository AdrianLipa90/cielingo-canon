from __future__ import annotations

from cielingo_core.lingophysics.case_port_frame import extract_polish_case_port_frames
from cielingo_core.lingophysics.operator_signatures import type_case_port_frame


def _typed_one(text: str):
    frames = extract_polish_case_port_frames(text)
    assert len(frames) == 1, (text, frames)
    frame = frames[0]
    report = type_case_port_frame(frame)
    assert report.valid is True, report
    return frame, report


def test_imperative_gives_variant_is_typed() -> None:
    frame, report = _typed_one("Daj Zosi książkę.")
    assert frame.operator == "GIVES"
    roles = {port.operator_role: port for port in frame.ports}
    assert roles["giver"].entity == "ja"
    assert roles["giver"].basis == "IMPLICIT_PERSON_FROM_IMPERATIVE"
    assert roles["recipient"].entity == "Zosi"
    assert roles["transferred_object"].entity == "książkę"
    assert {binding.operator_role for binding in report.universal_roles} == {
        "giver", "recipient", "transferred_object"
    }


def test_present_tense_names_variant_is_typed() -> None:
    frame, _ = _typed_one("Adrian nazywa kota Luną.")
    assert frame.operator == "NAMES"
    roles = {port.operator_role: port.entity for port in frame.ports}
    assert roles == {"namer": "Adrian", "entity_named": "kota", "assigned_name": "Luną"}


def test_speaks_about_accepts_z_then_o_order() -> None:
    frame, _ = _typed_one("Adrian rozmawia z Zosią o geometrii.")
    assert frame.operator == "SPEAKS_ABOUT"
    roles = {port.operator_role: port for port in frame.ports}
    assert roles["speaker"].entity == "Adrian"
    assert roles["interlocutor"].adposition == "z"
    assert roles["topic"].adposition == "o"


def test_connected_with_accepts_polaczony_variant() -> None:
    frame, _ = _typed_one("Graf jest połączony z geometrią.")
    assert frame.operator == "CONNECTED_WITH"
    assert frame.evidence_basis == "EXPLICIT_COPULA_PARTICIPLE_Z_PATTERN"


def test_existing_reference_forms_remain_typed() -> None:
    examples = [
        "Daję Zosi książkę",
        "Nazwałem cię Zosią",
        "Rozmawiam o geometrii z Zosią",
        "Informacja jest związana z geometrią",
        "Moduł należy do systemu",
    ]
    for text in examples:
        _typed_one(text)
