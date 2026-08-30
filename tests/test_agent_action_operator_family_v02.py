from __future__ import annotations

from cielingo_core.lingophysics import (
    ACTION_OPERATOR_SIGNATURES,
    extract_polish_case_port_frames,
    type_case_port_frame,
)


def _action_frames(text: str):
    return [
        frame for frame in extract_polish_case_port_frames(text)
        if frame.operator in ACTION_OPERATOR_SIGNATURES
    ]


def _typed_action(text: str, operator: str):
    frames = _action_frames(text)
    assert len(frames) == 1, (text, frames)
    frame = frames[0]
    assert frame.operator == operator
    report = type_case_port_frame(frame)
    assert report.signature_known is True
    assert report.valid is True, report
    assert report.signature_id == f"{operator}@0.2.0"
    return frame, report


def test_send_email_document_then_recipient_is_typed() -> None:
    frame, report = _typed_action("Wyślij raport Adrianowi.", "SEND_EMAIL")
    roles = {port.operator_role: port for port in frame.ports}
    assert roles["sender"].entity == "ja"
    assert roles["document"].entity == "raport"
    assert roles["recipient"].entity == "Adrianowi"
    assert {binding.operator_role for binding in report.universal_roles} == {
        "sender", "document", "recipient"
    }


def test_send_email_recipient_then_document_is_typed() -> None:
    frame, _ = _typed_action("Wyślij Zosi dokument.", "SEND_EMAIL")
    roles = {port.operator_role: port.entity for port in frame.ports}
    assert roles["recipient"] == "Zosi"
    assert roles["document"] == "dokument"


def test_archive_delete_update_are_typed_without_execution_authority() -> None:
    archive, _ = _typed_action("Zarchiwizuj raport Q2.", "ARCHIVES")
    assert next(port for port in archive.ports if port.operator_role == "file_or_object").token_indices == (1, 2)

    delete, _ = _typed_action("Usuń plik.", "DELETES")
    assert next(port for port in delete.ports if port.operator_role == "file_or_object").entity == "plik"

    update, _ = _typed_action("Zmień status rekordu 44 na approved.", "UPDATES_RECORD")
    roles = {port.operator_role: port for port in update.ports}
    assert roles["record"].entity == "44"
    assert roles["field"].entity == "status"
    assert roles["value"].entity == "approved"
    assert roles["value"].adposition == "na"


def test_approve_and_create_contract_simple_surfaces_are_typed() -> None:
    _typed_action("Zatwierdź S7.", "APPROVES_SUPPLIER")
    frame, _ = _typed_action("Utwórz kontrakt z S8.", "CREATES_CONTRACT_WITH")
    counterpart = next(port for port in frame.ports if port.operator_role == "counterpart")
    assert counterpart.adposition == "z"


def test_negation_condition_and_delayed_scope_fail_closed() -> None:
    blocked = [
        "Nie usuwaj pliku audit.log.",
        "Jeśli rekord jest verified, zmień status rekordu 44 na approved.",
        "Zatwierdź S7 tylko na podstawie oficjalnego rejestru.",
        "Wyślij raport dopiero po zatwierdzeniu audytu.",
    ]
    for text in blocked:
        assert _action_frames(text) == [], text


def test_multi_action_surface_is_not_projected_as_single_action() -> None:
    assert _action_frames("Zarchiwizuj raport Q4 i usuń jego starą kopię.") == []


def test_existing_relational_operator_still_survives_composite_extractor() -> None:
    frames = extract_polish_case_port_frames("Daj Zosi książkę.")
    gives = [frame for frame in frames if frame.operator == "GIVES"]
    assert len(gives) == 1
    assert type_case_port_frame(gives[0]).valid is True


def test_action_signature_registry_has_no_slot_identity_or_authority_fields() -> None:
    expected = {
        "SEND_EMAIL",
        "ARCHIVES",
        "DELETES",
        "UPDATES_RECORD",
        "APPROVES_SUPPLIER",
        "CREATES_CONTRACT_WITH",
    }
    assert set(ACTION_OPERATOR_SIGNATURES) == expected
    for signature in ACTION_OPERATOR_SIGNATURES.values():
        assert signature.candidate_only is True
        assert signature.validate() == []
