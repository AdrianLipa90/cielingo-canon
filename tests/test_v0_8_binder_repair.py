from pathlib import Path

from cielingo_core.regional.simple_solver_utils import (
    load_atlas_cards,
    match_cards_to_tokens,
)


ROOT = Path(__file__).resolve().parents[1]


def test_pl_loader_resolves_controlled_48_slot_atlas() -> None:
    cards = load_atlas_cards(ROOT, "pl")
    assert len(cards) == 48
    assert len({int(card["slot_id"]) for card in cards}) == 48


def test_short_substring_z_does_not_bind_cards() -> None:
    cards = load_atlas_cards(ROOT, "pl")
    assert match_cards_to_tokens(cards, ["z"], "pl") == []


def test_informacja_does_not_bind_conjunction_i() -> None:
    cards = load_atlas_cards(ROOT, "pl")
    candidates = match_cards_to_tokens(cards, ["informacja"], "pl")
    assert all(candidate.card_id != "pl_and_slot_25_v06a" for candidate in candidates)


def test_boundary_punctuation_preserves_exact_source_match() -> None:
    cards = load_atlas_cards(ROOT, "pl")
    candidates = match_cards_to_tokens(cards, ["źródło,"], "pl")
    assert any(
        candidate.card_id == "pl_source_slot_5_v06a" and candidate.score == 1.0
        for candidate in candidates
    )


def test_matcher_emits_only_exact_score_candidates() -> None:
    cards = load_atlas_cards(ROOT, "pl")
    candidates = match_cards_to_tokens(
        cards,
        ["źródło,", "twierdzenie", "napraw", "ponieważ", "informacja"],
        "pl",
    )
    assert candidates
    assert all(candidate.score == 1.0 for candidate in candidates)
