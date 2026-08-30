from __future__ import annotations

from dataclasses import replace

from cielingo_core.lingophysics.action_intent_bundle import build_polish_action_intent_bundle


def test_single_simple_action_is_candidate_only_not_authorized() -> None:
    bundle = build_polish_action_intent_bundle("Wyślij raport Adrianowi.")
    assert bundle.validate() == []
    assert bundle.gate_status == "CANDIDATE_SINGLE_ACTION"
    assert bundle.execution_authorized is False


def test_multi_action_requires_review() -> None:
    bundle = build_polish_action_intent_bundle("Zarchiwizuj raport Q4 i usuń jego starą kopię.")
    assert len(bundle.frames) == 2
    assert bundle.multi_action_detected is True
    assert bundle.gate_status == "MULTI_ACTION_REVIEW"


def test_unmodeled_coordination_requires_review() -> None:
    bundle = build_polish_action_intent_bundle("Wyślij raport Adrianowi, a kopię Zosi.")
    assert len(bundle.frames) == 1
    assert bundle.coordination_detected is True
    assert bundle.gate_status == "COORDINATION_REVIEW"


def test_negation_requires_scope_review() -> None:
    bundle = build_polish_action_intent_bundle("Nie usuwaj pliku audit.log.")
    assert bundle.gate_status == "SCOPE_REVIEW"


def test_condition_requires_scope_review() -> None:
    bundle = build_polish_action_intent_bundle("Zarchiwizuj raport Q2 jeśli audyt przeszedł.")
    assert bundle.gate_status == "SCOPE_REVIEW"


def test_missing_required_port_is_incomplete() -> None:
    bundle = build_polish_action_intent_bundle("Wyślij raport.")
    assert bundle.gate_status == "INCOMPLETE_ARGUMENTS"


def test_no_supported_action_stays_no_action() -> None:
    bundle = build_polish_action_intent_bundle("Adrian rozmawia z Zosią o geometrii.")
    assert bundle.gate_status == "NO_ACTION"


def test_bundle_commitment_detects_frame_mutation() -> None:
    bundle = build_polish_action_intent_bundle("Wyślij raport Adrianowi.")
    frame = bundle.frames[0]
    changed_frame = replace(frame, surface_text="mutated")
    changed = replace(bundle, frames=(changed_frame,))
    issues = changed.validate()
    assert "action intent frame commitment mismatch" in issues
    assert "action intent bundle commitment mismatch" in issues
