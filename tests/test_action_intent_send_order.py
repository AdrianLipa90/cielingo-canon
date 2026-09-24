from __future__ import annotations

from cielingo_core.lingophysics.action_intent_frame import extract_polish_action_intent_frames


def _one(text: str):
    frames = extract_polish_action_intent_frames(text)
    assert len(frames) == 1
    assert frames[0].validate() == []
    return frames[0]


def test_dative_pronoun_first_is_recipient_not_object() -> None:
    frame = _one("Wyślij mu raport.")
    assert [(port.operator_role, port.entity) for port in frame.ports] == [
        ("recipient", "mu"),
        ("object", "raport"),
    ]


def test_capitalized_dative_name_first_is_recipient() -> None:
    frame = _one("Wyślij Zosi dokument, o którym mówił Adrian.")
    assert [(port.operator_role, port.entity) for port in frame.ports] == [
        ("recipient", "Zosi"),
        ("object", "dokument"),
    ]


def test_comma_ends_local_send_clause_before_followup_relation() -> None:
    frame = _one("Wyślij dokument do Anny z działu prawnego, nie do Anny z finansów.")
    object_port = next(port for port in frame.ports if port.operator_role == "object")
    recipient_port = next(port for port in frame.ports if port.operator_role == "recipient")
    assert object_port.entity == "dokument"
    assert recipient_port.entity == "Anny z działu prawnego"
    assert frame.negation_detected is True
    assert frame.scope_clear_for_execution is False
