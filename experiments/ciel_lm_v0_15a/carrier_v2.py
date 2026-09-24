from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from cleaner import normalize_surface

DENOM_ORDERED_NONSELF_24 = 24 * 23


@dataclass(frozen=True)
class AnchorCard:
    card_id: str
    language_id: str
    slot_id: int
    forms: tuple[str, ...]
    operator_bindings: tuple[str, ...]


@dataclass(frozen=True)
class TokenState:
    raw: str
    normalized: str
    cards: tuple[AnchorCard, ...]
    syntax_class: str | None

    @property
    def anchor_operator(self) -> bool:
        return any(card.operator_bindings for card in self.cards)

    @property
    def anchor_concept(self) -> bool:
        return any(not card.operator_bindings for card in self.cards)

    @property
    def slots(self) -> frozenset[int]:
        return frozenset(card.slot_id for card in self.cards)


class StructuralCarrierV2:
    """Exact anchor layer plus deterministic syntax-derived typed relations."""

    def __init__(self, prereg: dict[str, Any], anchor_snapshot: dict[str, Any]):
        syntax = prereg["syntax_layer"]
        self.negation = frozenset(normalize_surface(x) for x in syntax["negation"])
        self.modal = frozenset(normalize_surface(x) for x in syntax["modal"])
        self.condition = frozenset(normalize_surface(x) for x in syntax["condition"])
        self.action = frozenset(normalize_surface(x) for x in syntax["action"])
        self.stopwords = frozenset(normalize_surface(x) for x in syntax["stopwords"])
        self.syntax_operators = self.negation | self.modal | self.condition | self.action
        self.scope_operators = self.negation | self.modal | self.condition

        cards: list[AnchorCard] = []
        for raw in anchor_snapshot["cards"]:
            if raw["language_id"] not in {"pl", "en"}:
                continue
            forms = [raw.get("lemma") or ""] + list(raw.get("surface_forms") or [])
            cards.append(
                AnchorCard(
                    card_id=str(raw["card_id"]),
                    language_id=str(raw["language_id"]),
                    slot_id=int(raw["slot_id"]),
                    forms=tuple(str(x) for x in forms if str(x).strip()),
                    operator_bindings=tuple(str(x) for x in (raw.get("operator_bindings") or [])),
                )
            )
        by_form: dict[str, list[AnchorCard]] = {}
        for card in cards:
            for form in card.forms:
                key = normalize_surface(form)
                if key:
                    by_form.setdefault(key, []).append(card)
        self.by_form = {k: tuple(sorted(v, key=lambda c: c.card_id)) for k, v in by_form.items()}
        self.anchor_cards = tuple(sorted(cards, key=lambda c: c.card_id))

    @classmethod
    def from_files(cls, prereg_path: str | Path, anchor_snapshot_path: str | Path) -> "StructuralCarrierV2":
        prereg = json.loads(Path(prereg_path).read_text(encoding="utf-8"))
        anchor = json.loads(Path(anchor_snapshot_path).read_text(encoding="utf-8"))
        return cls(prereg, anchor)

    def _syntax_class(self, norm: str) -> str | None:
        if norm in self.negation:
            return "NEGATION"
        if norm in self.modal:
            return "MODAL"
        if norm in self.condition:
            return "CONDITION"
        if norm in self.action:
            return "ACTION"
        return None

    def _state(self, raw: str) -> TokenState:
        norm = normalize_surface(raw)
        return TokenState(raw=raw, normalized=norm, cards=self.by_form.get(norm, ()), syntax_class=self._syntax_class(norm))

    def _eligible_argument(self, state: TokenState) -> bool:
        norm = state.normalized
        if len(norm) < 2 or norm in self.syntax_operators or norm in self.stopwords:
            return False
        if not any(ch.isalnum() for ch in norm):
            return False
        return True

    @staticmethod
    def _clause_boundary(raw: str) -> bool:
        return raw.strip().endswith((".", ";", ":", "!", "?"))

    def window(self, tokens: list[str]) -> dict[str, Any]:
        if len(tokens) != 24:
            raise ValueError(f"carrier-v2 requires exactly 24 tokens, got {len(tokens)}")
        states = [self._state(token) for token in tokens]
        anchor_cards = [card for state in states for card in state.cards]
        operator_bound = [card for card in anchor_cards if card.operator_bindings]

        anchor_op_edges: set[tuple[int, int]] = set()
        anchor_slot_edges: set[tuple[int, int]] = set()
        syntax_arg_edges: set[tuple[int, int]] = set()
        syntax_scope_edges: set[tuple[int, int]] = set()

        for i, a in enumerate(states):
            for j in range(i + 1, len(states)):
                b = states[j]
                if (a.anchor_operator and b.anchor_concept) or (b.anchor_operator and a.anchor_concept):
                    anchor_op_edges.add((i, j))
                if a.slots & b.slots:
                    anchor_slot_edges.add((i, j))

        for i, state in enumerate(states):
            if state.syntax_class is None:
                continue
            for j in range(i + 1, min(len(states), i + 4)):
                if self._eligible_argument(states[j]):
                    syntax_arg_edges.add((i, j))
                    break
            if state.normalized in self.scope_operators:
                for j in range(i + 1, min(len(states), i + 7)):
                    if self._eligible_argument(states[j]):
                        syntax_scope_edges.add((i, j))
                    # Frozen implementation detail: an eligible boundary token is linked first,
                    # then terminates scope. A non-eligible boundary still terminates scope.
                    if self._clause_boundary(states[j].raw):
                        break

        vector = [
            2.0 * len(anchor_op_edges) * 0.7 / DENOM_ORDERED_NONSELF_24,
            2.0 * len(anchor_slot_edges) * 0.4 / DENOM_ORDERED_NONSELF_24,
            2.0 * len(syntax_arg_edges) * 0.7 / DENOM_ORDERED_NONSELF_24,
            2.0 * len(syntax_scope_edges) * 0.35 / DENOM_ORDERED_NONSELF_24,
        ]
        anchor_nonzero = vector[0] != 0.0 or vector[1] != 0.0
        syntax_nonzero = vector[2] != 0.0 or vector[3] != 0.0
        return {
            "vector": vector,
            "nonzero": any(value != 0.0 for value in vector),
            "anchor_nonzero": anchor_nonzero,
            "syntax_nonzero": syntax_nonzero,
            "syntax_only": syntax_nonzero and not anchor_nonzero,
            "anchor_candidate_count": len(anchor_cards),
            "anchor_operator_bound_candidate_count": len(operator_bound),
            "anchor_candidate_scores": [1.0] * len(anchor_cards),
            "anchor_card_ids": [card.card_id for card in anchor_cards],
            "edge_counts": {
                "anchor_operator_argument": len(anchor_op_edges),
                "anchor_shared_slot": len(anchor_slot_edges),
                "syntax_operator_argument": len(syntax_arg_edges),
                "syntax_scope": len(syntax_scope_edges),
            },
        }
