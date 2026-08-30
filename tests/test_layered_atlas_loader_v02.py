from __future__ import annotations

import json
from pathlib import Path

from cielingo_core.regional.simple_solver_utils import load_atlas_cards


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
        encoding="utf-8",
    )


def test_loader_composes_all_existing_layers_with_first_source_precedence(tmp_path: Path) -> None:
    generated = tmp_path / "cards/generated_examples"
    _write_jsonl(
        generated / "controlled_24_slot_runtime_cards_v0_5e.jsonl",
        [
            {"card_id": "rad_entity", "slot_id": 1, "language_id": "universal", "lemma": "entity"},
            {"card_id": "concept:shared", "slot_id": 4, "language_id": "pl", "lemma": "pierwszy"},
        ],
    )
    _write_jsonl(
        generated / "trilingual_runtime_cards_v0_3b.jsonl",
        [
            {"card_id": "concept:shared", "slot_id": 999, "language_id": "pl", "lemma": "drugi"},
            {"card_id": "concept:work", "slot_id": 2, "language_id": "pl", "lemma": "praca"},
            {"card_id": "concept:work", "slot_id": 2, "language_id": "en", "lemma": "work"},
        ],
    )
    _write_jsonl(
        generated / "agent_tool_runtime_cards_v0_1.jsonl",
        [
            {"card_id": "concept:book", "slot_id": 999, "language_id": "pl", "lemma": "książka"},
            {"card_id": "concept:book", "slot_id": 999, "language_id": "en", "lemma": "book"},
        ],
    )

    pl_cards = load_atlas_cards(tmp_path, "pl")
    assert [card["card_id"] for card in pl_cards] == [
        "concept:shared",
        "concept:work",
        "concept:book",
    ]
    assert pl_cards[0]["lemma"] == "pierwszy"

    en_cards = load_atlas_cards(tmp_path, "en")
    assert [card["card_id"] for card in en_cards] == ["concept:work", "concept:book"]


def test_loader_returns_empty_when_no_runtime_atlas_layer_exists(tmp_path: Path) -> None:
    assert load_atlas_cards(tmp_path, "pl") == []
