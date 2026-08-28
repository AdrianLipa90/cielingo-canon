from __future__ import annotations
import json, re
from pathlib import Path
from typing import Any
from cielingo_core.regional.base import CardCandidate

_BOUNDARY_PUNCTUATION = " \t\r\n.,!?;:%()[]{}<>\"'„”«»—–-"


def _normalize_card_token(value: str) -> str:
    """Normalize one surface token for exact atlas binding.

    The binder strips boundary punctuation only. It deliberately does not
    perform substring, stemming, or fuzzy matching.
    """
    return str(value).strip().strip(_BOUNDARY_PUNCTUATION).casefold()


def _load_jsonl_language(path: Path, language_id: str) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("language_id") == language_id:
            rows.append(row)
    return rows


def _generate_controlled_48_language(language_id: str) -> list[dict[str, Any]]:
    """Materialize the checked-in 48-slot atlas generator in memory.

    This keeps the generator as the source of truth when a generated JSONL
    artifact is not checked into the repository.
    """
    from cielingo_core.global_layer.controlled_atlas_48 import (
        generate_controlled_atlas_48_cards,
    )

    cards, _, _ = generate_controlled_atlas_48_cards()
    return [card.to_dict() for card in cards if card.language_id == language_id]


def load_atlas_cards(repo_root: Path, language_id: str) -> list[dict[str, Any]]:
    generated_examples = repo_root / "cards/generated_examples"

    # Frozen v0.8 priority: controlled 48 -> controlled 24 -> trilingual.
    # Current repository source contains the deterministic 48-slot generator
    # even when its generated JSONL artifact is absent, so use that generator
    # before falling back to older materialized atlases.
    controlled_48 = generated_examples / "controlled_48_slot_runtime_cards_v0_6a.jsonl"
    rows = _load_jsonl_language(controlled_48, language_id)
    if rows:
        return rows

    rows = _generate_controlled_48_language(language_id)
    if rows:
        return rows

    for path in (
        generated_examples / "controlled_24_slot_runtime_cards_v0_5e.jsonl",
        generated_examples / "trilingual_runtime_cards_v0_3b.jsonl",
    ):
        rows = _load_jsonl_language(path, language_id)
        if rows:
            return rows
    return []


def simple_space_segment(text: str) -> list[str]:
    return [t for t in re.split(r"\s+", text.strip()) if t]


def japanese_segment_known_forms(text: str, cards: list[dict[str, Any]]) -> list[str]:
    # Keep spaces when provided, otherwise use known forms. Not a real morphological analyzer.
    if " " in text:
        return [t for t in text.split() if t]
    forms = sorted({str(f) for c in cards for f in c.get("surface_forms", []) if f}, key=len, reverse=True)
    tokens, rest = [], text.strip()
    while rest:
        match = next((f for f in forms if rest.startswith(f)), None)
        if match:
            tokens.append(match); rest = rest[len(match):]
        else:
            tokens.append(rest[0]); rest = rest[1:]
    return tokens


def match_cards_to_tokens(cards: list[dict[str, Any]], tokens: list[str], language_id: str) -> list[CardCandidate]:
    candidates = []
    for card in cards:
        forms = [str(card.get("lemma") or "")] + [str(f) for f in card.get("surface_forms", [])]
        normalized_forms = {_normalize_card_token(f) for f in forms if _normalize_card_token(f)}
        if not normalized_forms:
            continue
        for i, tok in enumerate(tokens):
            token_norm = _normalize_card_token(tok)
            if not token_norm or token_norm not in normalized_forms:
                continue
            runtime = card.get("runtime", {}) or {}
            validation_status = card.get("validation_status")
            validation_status = getattr(validation_status, "value", validation_status)
            candidates.append(CardCandidate(
                card_id=card["card_id"], slot_id=int(card["slot_id"]), language_id=language_id,
                lemma=card.get("lemma"), token_indices=[i],
                operator_bindings=list(runtime.get("operator_bindings", []) or []),
                score=1.0,
                needs_native_review=(language_id == "ja") or validation_status == "needs_review",
            ))
    seen, out = set(), []
    for c in candidates:
        key = (c.card_id, tuple(c.token_indices))
        if key not in seen:
            seen.add(key); out.append(c)
    return out


def build_projection(candidates: list[CardCandidate]) -> dict[int, list[int]]:
    projection = {}
    for c in candidates:
        projection.setdefault(c.slot_id, [])
        for idx in c.token_indices:
            if idx not in projection[c.slot_id]:
                projection[c.slot_id].append(idx)
    return projection


def build_local_j(word_order: float, morph_particle: float, scope: float, residue: float) -> dict[str, float]:
    return {"J_word_order": word_order, "J_morphology_or_particle": morph_particle, "J_scope": scope, "J_residue": residue}
