from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
import unicodedata
from typing import Any, Iterable

FEATURE_ORDER = (
    "operator_argument_link",
    "same_event_frame",
    "case_role_link",
    "conflict_penalty",
)
WEIGHTS = {
    "operator_argument_link": 0.7,
    "same_event_frame": 0.4,
    "case_role_link": 0.55,
    "conflict_penalty": -0.9,
}
_EDGE = re.compile(r"^[^\w]+|[^\w-]+$", flags=re.UNICODE)


def normalize_surface(value: str) -> str:
    s = unicodedata.normalize("NFKC", str(value)).casefold().strip()
    return _EDGE.sub("", s)


@dataclass(frozen=True)
class Card:
    card_id: str
    language_id: str
    slot_id: int
    forms: tuple[str, ...]
    operator_bindings: tuple[str, ...]
    roles: tuple[str, ...]
    case_gauge: str | None
    phase_conflict: bool


@dataclass(frozen=True)
class TokenState:
    surface: str
    cards: tuple[Card, ...]

    @property
    def operator_token(self) -> bool:
        return any(c.operator_bindings for c in self.cards)

    @property
    def concept_token(self) -> bool:
        return any(not c.operator_bindings for c in self.cards)

    @property
    def slots(self) -> frozenset[int]:
        return frozenset(c.slot_id for c in self.cards)

    @property
    def roles(self) -> frozenset[str]:
        return frozenset(r for c in self.cards for r in c.roles)

    @property
    def has_case_gauge(self) -> bool:
        return any(bool(c.case_gauge) for c in self.cards)

    @property
    def phase_conflict(self) -> bool:
        return any(c.phase_conflict for c in self.cards)


class ExactMultilingualCarrier:
    """PL+EN controlled-atlas carrier with exact whole-token matching only."""

    def __init__(self, cards: Iterable[Card]):
        selected = tuple(c for c in cards if c.language_id in {"pl", "en"})
        self.cards = selected
        by_form: dict[str, list[Card]] = {}
        for card in selected:
            for form in card.forms:
                nf = normalize_surface(form)
                if nf:
                    by_form.setdefault(nf, []).append(card)
        self.by_form = {k: tuple(sorted(v, key=lambda c: c.card_id)) for k, v in by_form.items()}

    @classmethod
    def from_jsonl(cls, path: str | Path) -> "ExactMultilingualCarrier":
        cards: list[Card] = []
        with Path(path).open("r", encoding="utf-8") as fh:
            for line in fh:
                if not line.strip():
                    continue
                raw = json.loads(line)
                if raw.get("language_id") not in {"pl", "en"}:
                    continue
                forms = [raw.get("lemma", "")]
                forms.extend(raw.get("surface_forms") or [])
                runtime = raw.get("runtime") or {}
                roles_raw = raw.get("roles") or runtime.get("roles") or []
                if isinstance(roles_raw, str):
                    roles_raw = [roles_raw]
                case_gauge = raw.get("case_gauge") or runtime.get("case_gauge")
                phase_conflict = bool(raw.get("phase_conflict") or runtime.get("phase_conflict"))
                cards.append(Card(
                    card_id=str(raw["card_id"]),
                    language_id=str(raw["language_id"]),
                    slot_id=int(raw["slot_id"]),
                    forms=tuple(str(x) for x in forms if str(x).strip()),
                    operator_bindings=tuple(str(x) for x in (runtime.get("operator_bindings") or [])),
                    roles=tuple(str(x) for x in roles_raw),
                    case_gauge=None if case_gauge is None else str(case_gauge),
                    phase_conflict=phase_conflict,
                ))
        return cls(cards)

    def token_state(self, token: str) -> TokenState:
        key = normalize_surface(token)
        return TokenState(surface=token, cards=self.by_form.get(key, ()))

    def window(self, tokens: list[str]) -> dict[str, Any]:
        if len(tokens) != 24:
            raise ValueError(f"carrier requires exactly 24 tokens, got {len(tokens)}")
        states = [self.token_state(t) for t in tokens]
        candidate_cards = [c for st in states for c in st.cards]
        operator_bound = [c for c in candidate_cards if c.operator_bindings]
        sums = [0.0, 0.0, 0.0, 0.0]
        denom = len(states) * (len(states) - 1)
        for i, a in enumerate(states):
            for j, b in enumerate(states):
                if i == j:
                    continue
                op_arg = (a.operator_token and b.concept_token) ^ (b.operator_token and a.concept_token)
                same_frame = bool(a.slots & b.slots)
                case_role = (a.has_case_gauge or b.has_case_gauge) and bool(a.roles | b.roles)
                conflict = a.phase_conflict or b.phase_conflict
                sums[0] += WEIGHTS["operator_argument_link"] if op_arg else 0.0
                sums[1] += WEIGHTS["same_event_frame"] if same_frame else 0.0
                sums[2] += WEIGHTS["case_role_link"] if case_role else 0.0
                sums[3] += WEIGHTS["conflict_penalty"] if conflict else 0.0
        vector = [x / denom for x in sums]
        return {
            "vector": vector,
            "candidate_count": len(candidate_cards),
            "operator_bound_candidate_count": len(operator_bound),
            "candidate_scores": [1.0] * len(candidate_cards),
            "card_ids": [c.card_id for c in candidate_cards],
        }
