from __future__ import annotations

from dataclasses import replace

from cielingo_core.lingophysics.action_operator_family import _ACTION_ANCHORS
from cielingo_core.lingophysics.action_scope_condition import (
    ACTION_ANCHORS,
    build_action_scope_condition_receipt,
)


def _status(text: str) -> str:
    return build_action_scope_condition_receipt(text).status


def test_scope_safe_affirmative_single_action() -> None:
    receipt = build_action_scope_condition_receipt("Wyślij dokument Zosi")
    assert receipt.status == "SCOPE_SAFE"
    assert receipt.scope_safe is True
    assert receipt.validate() == []


def test_negation_blocks_scope() -> None:
    assert _status("Nie wyślij dokument Zosi") == "NEGATED"


def test_condition_blocks_scope() -> None:
    assert _status("Jeśli masz zgodę, wyślij dokument Zosi") == "CONDITIONAL"


def test_delay_blocks_scope() -> None:
    assert _status("Dopiero jutro wyślij dokument Zosi") == "DELAYED"


def test_qualifier_blocks_scope() -> None:
    assert _status("Chyba wyślij dokument Zosi") == "QUALIFIED"


def test_multi_action_blocks_scope() -> None:
    assert _status("Wyślij dokument Zosi i usuń plik") == "MULTI_ACTION"


def test_non_action_is_not_scope_safe() -> None:
    receipt = build_action_scope_condition_receipt("Człowiek buduje dom")
    assert receipt.status == "NOT_ACTION"
    assert receipt.scope_safe is False


def test_commitment_detects_status_mutation() -> None:
    receipt = build_action_scope_condition_receipt("Nie wyślij dokument Zosi")
    changed = replace(receipt, status="SCOPE_SAFE")
    assert "action scope commitment mismatch" in changed.validate()


def test_scope_anchor_registry_matches_action_family() -> None:
    assert ACTION_ANCHORS == _ACTION_ANCHORS
