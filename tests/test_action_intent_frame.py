from __future__ import annotations

from dataclasses import replace

from cielingo_core.lingophysics.action_intent_frame import extract_polish_action_intent_frames


def _one(text: str):
    frames = extract_polish_action_intent_frames(text)
    assert len(frames) == 1
    frame = frames[0]
    assert frame.validate() == []
    return frame


def test_send_report_to_dative_recipient_is_structurally_complete() -> None:
    frame = _one("Wyślij raport Adrianowi.")
    assert frame.operator == "SENDS"
    assert [(port.operator_role, port.entity) for port in frame.ports] == [
        ("object", "raport"),
        ("recipient", "Adrianowi"),
    ]
    assert frame.structurally_complete is True
    assert frame.scope_clear_for_execution is True


def test_send_document_do_recipient_preserves_adposition() -> None:
    frame = _one("Wyślij dokument do Anny.")
    recipient = next(port for port in frame.ports if port.operator_role == "recipient")
    assert recipient.entity == "Anny"
    assert recipient.adposition == "do"
    assert recipient.grammatical_case == "GEN"


def test_send_missing_recipient_remains_structurally_incomplete() -> None:
    frame = _one("Wyślij raport.")
    assert frame.structurally_complete is False
    assert frame.missing_required_roles == ("recipient",)
    assert frame.scope_clear_for_execution is False


def test_negated_delete_is_detected_but_never_scope_clear() -> None:
    frame = _one("Nie usuń pliku audit.log.")
    assert frame.operator == "DELETES"
    assert frame.negation_detected is True
    assert frame.scope_clear_for_execution is False


def test_conditional_archive_is_detected_but_never_scope_clear() -> None:
    frame = _one("Zarchiwizuj raport Q2 jeśli audyt przeszedł.")
    assert frame.operator == "ARCHIVES"
    assert frame.condition_detected is True
    assert frame.scope_clear_for_execution is False


def test_set_status_extracts_record_and_status() -> None:
    frame = _one("Zmień status rekordu 44 na approved.")
    assert frame.operator == "SETS_STATUS"
    assert {(port.operator_role, port.entity) for port in frame.ports} == {
        ("record", "44"),
        ("status", "approved"),
    }
    assert frame.structurally_complete is True


def test_approve_supplier_extracts_supplier_port() -> None:
    frame = _one("Zatwierdź S7.")
    assert frame.operator == "APPROVES_SUPPLIER"
    assert frame.ports[0].operator_role == "supplier"
    assert frame.ports[0].entity == "S7"


def test_create_contract_extracts_counterparty_after_z() -> None:
    frame = _one("Utwórz kontrakt z S5.")
    assert frame.operator == "CREATES_CONTRACT"
    assert frame.ports[0].operator_role == "counterparty"
    assert frame.ports[0].entity == "S5"
    assert frame.ports[0].adposition == "z"


def test_first_send_clause_does_not_consume_copy_clause() -> None:
    frame = _one("Wyślij raport Adrianowi, a kopię Zosi.")
    assert [(port.operator_role, port.entity) for port in frame.ports] == [
        ("object", "raport"),
        ("recipient", "Adrianowi"),
    ]


def test_commitment_detects_port_mutation() -> None:
    frame = _one("Wyślij raport Adrianowi.")
    changed_port = replace(frame.ports[0], entity="umowę")
    tampered = replace(frame, ports=(changed_port, *frame.ports[1:]))
    assert "action intent frame commitment mismatch" in tampered.validate()
