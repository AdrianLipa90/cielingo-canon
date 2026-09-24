from __future__ import annotations
import json, re
from pathlib import Path
from typing import Any
from cielingo_core.regional.base import CardCandidate

_ATLAS_RELATIVE_PATHS = (
    "cards/generated_examples/controlled_24_slot_runtime_cards_v0_5e.jsonl",
    "cards/generated_examples/trilingual_runtime_cards_v0_3b.jsonl",
    "cards/generated_examples/agent_tool_runtime_cards_v0_1.jsonl",
)

def load_atlas_cards(repo_root: Path, language_id: str) -> list[dict[str, Any]]:
    """Load all available runtime-atlas layers for one language.

    Earlier layers have deterministic precedence when the same ``card_id`` is
    repeated. Distinct card identities from later layers are additive. This is
    intentionally a layered composition, not a first-existing-file fallback.
    """
    rows: list[dict[str, Any]] = []
    seen_card_ids: set[str] = set()
    for relative_path in _ATLAS_RELATIVE_PATHS:
        path = repo_root / relative_path
        if not path.exists():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("language_id") != language_id:
                continue
            card_id = str(row.get("card_id") or "").strip()
            if card_id and card_id in seen_card_ids:
                continue
            rows.append(row)
            if card_id:
                seen_card_ids.add(card_id)
    return rows

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
        forms = [f for f in forms if f]
        for i, tok in enumerate(tokens):
            tl = tok.lower()
            for form in forms:
                fl = form.lower()
                if tl == fl or fl in tl or tl in fl:
                    runtime = card.get("runtime", {}) or {}
                    candidates.append(CardCandidate(
                        card_id=card["card_id"], slot_id=int(card["slot_id"]), language_id=language_id,
                        lemma=card.get("lemma"), token_indices=[i],
                        operator_bindings=list(runtime.get("operator_bindings", []) or []),
                        score=1.0 if tl == fl else 0.75,
                        needs_native_review=(language_id == "ja") or card.get("validation_status") == "needs_review",
                    ))
                    break
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
