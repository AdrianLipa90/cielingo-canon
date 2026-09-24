from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from cielingo_core.regional.simple_solver_utils import match_cards_to_tokens


EXPECTED_CARD_IDS = {
    "concept:book",
    "concept:cat",
    "concept:geometry",
    "concept:module",
    "concept:system",
    "concept:graph",
    "concept:report",
    "concept:document",
    "concept:contract",
    "concept:file",
    "concept:record",
    "concept:supplier",
    "concept:company",
    "concept:certificate",
}


def _overlay_rows() -> list[dict]:
    root = Path(__file__).resolve().parents[1]
    path = root / "cards/generated_examples/agent_tool_runtime_cards_v0_1.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_overlay_has_one_pl_and_one_en_card_per_shared_identity() -> None:
    rows = _overlay_rows()
    by_id: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        by_id[row["card_id"]].add(row["language_id"])
        assert row["slot_id"] == 999
        assert row["canon_allowed"] is False
        assert row["validation_status"] == "draft"

    assert set(by_id) == EXPECTED_CARD_IDS
    assert all(languages == {"pl", "en"} for languages in by_id.values())
    assert len(rows) == 2 * len(EXPECTED_CARD_IDS)


def test_polish_inflected_surface_maps_to_shared_book_identity() -> None:
    pl_cards = [row for row in _overlay_rows() if row["language_id"] == "pl"]
    candidates = match_cards_to_tokens(pl_cards, ["Daj", "Zosi", "książkę"], "pl")
    book = [candidate for candidate in candidates if candidate.card_id == "concept:book"]
    assert len(book) == 1
    assert book[0].token_indices == [2]


def test_polish_instrumental_geometry_surface_is_covered() -> None:
    pl_cards = [row for row in _overlay_rows() if row["language_id"] == "pl"]
    candidates = match_cards_to_tokens(pl_cards, ["geometrią"], "pl")
    assert [candidate.card_id for candidate in candidates] == ["concept:geometry"]


def test_english_surface_uses_same_card_identity() -> None:
    en_cards = [row for row in _overlay_rows() if row["language_id"] == "en"]
    candidates = match_cards_to_tokens(en_cards, ["book"], "en")
    assert [candidate.card_id for candidate in candidates] == ["concept:book"]
