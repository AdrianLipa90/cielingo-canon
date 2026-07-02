"""Trilingual runtime-card seed for CIELingo v0.3b.

Produces aligned PL/EN/JA cards over shared global slot_id values.

Important:
- alignment is slot correspondence, not semantic identity;
- Japanese entries remain draft / native-review candidates;
- NOEMA holonomic markers are public-safe commitments, not writeback;
- SOURCE and canon are never default.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .card_generator import generate_runtime_card
from .card_runtime_schema import CardOntologyClass, CielingoRuntimeCard
from .card_validator import validate_runtime_card


TRILINGUAL_SLOT_SEED: list[dict[str, Any]] = [
    {
        "slot_id": 5,
        "anchor": "SOURCE",
        "function": "source proof hash evidence provenance",
        "entries": {
            "pl": {"lemma": "źródło", "forms": ["źródło", "źródła"]},
            "en": {"lemma": "source", "forms": ["source", "evidence source"]},
            "ja": {"lemma": "出典", "forms": ["出典", "情報源"], "needs_native_review": True},
        },
    },
    {
        "slot_id": 15,
        "anchor": "FILE",
        "function": "file data artifact object",
        "entries": {
            "pl": {"lemma": "plik", "forms": ["plik", "pliku"]},
            "en": {"lemma": "file", "forms": ["file", "the file"]},
            "ja": {"lemma": "ファイル", "forms": ["ファイル"], "needs_native_review": True},
        },
    },
    {
        "slot_id": 16,
        "anchor": "CHECK_VERIFY",
        "function": "verify check test action",
        "entries": {
            "pl": {"lemma": "sprawdzić", "forms": ["sprawdzić", "sprawdź", "sprawdza"]},
            "en": {"lemma": "check", "forms": ["check", "verify"]},
            "ja": {"lemma": "確認する", "forms": ["確認する", "確認して", "検証する"], "needs_native_review": True},
        },
    },
    {
        "slot_id": 22,
        "anchor": "NEGATION",
        "function": "not negation deny negative operator",
        "entries": {
            "pl": {"lemma": "nie", "forms": ["nie"]},
            "en": {"lemma": "not", "forms": ["not", "do not", "no"]},
            "ja": {"lemma": "ない", "forms": ["ない", "しない", "ではない"], "needs_native_review": True},
        },
    },
    {
        "slot_id": 23,
        "anchor": "QUESTION",
        "function": "question ask inquiry operator",
        "entries": {
            "pl": {"lemma": "pytanie", "forms": ["pytanie", "czy", "dlaczego", "jak"]},
            "en": {"lemma": "question", "forms": ["question", "ask", "what", "why", "how"]},
            "ja": {"lemma": "質問", "forms": ["質問", "か", "何", "なぜ", "どう"], "needs_native_review": True},
        },
    },
    {
        "slot_id": 100,
        "anchor": "PREFERENCE",
        "function": "affective preference like prefer suki operator",
        "entries": {
            "pl": {"lemma": "lubić", "forms": ["lubić", "lubi", "lubię"]},
            "en": {"lemma": "like", "forms": ["like", "likes", "prefer"]},
            "ja": {"lemma": "好き", "forms": ["好き", "好きです"], "needs_native_review": True},
        },
    },
]


@dataclass
class TrilingualAlignmentRecord:
    slot_id: int
    anchor: str
    alignment_type: str
    semantic_identity_claimed: bool
    members: list[dict[str, Any]]
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def generate_trilingual_runtime_cards() -> tuple[list[CielingoRuntimeCard], list[TrilingualAlignmentRecord]]:
    cards: list[CielingoRuntimeCard] = []
    alignments: list[TrilingualAlignmentRecord] = []

    for spec in TRILINGUAL_SLOT_SEED:
        members: list[dict[str, Any]] = []
        for lang, entry in spec["entries"].items():
            card = generate_runtime_card(
                card_id=f"{lang}_{spec['anchor'].lower()}_slot_{spec['slot_id']}_v03b",
                slot_id=spec["slot_id"],
                language_id=lang,
                lemma=entry["lemma"],
                surface_forms=entry["forms"],
                function=spec["function"],
                ontology_class=CardOntologyClass.KOTO,
                attach_marker=True,
            )
            if lang == "ja":
                card.notes.append("Japanese draft: needs native review before canon.")
            cards.append(card)
            members.append({
                "language_id": lang,
                "card_id": card.card_id,
                "lemma": card.lemma,
                "equivalence_type": "slot_correspondence",
                "needs_native_review": bool(entry.get("needs_native_review", False)),
            })

        alignments.append(TrilingualAlignmentRecord(
            slot_id=spec["slot_id"],
            anchor=spec["anchor"],
            alignment_type="slot_correspondence",
            semantic_identity_claimed=False,
            members=members,
            notes=[
                "Shared slot_id is a comparison axis, not identity.",
                "Local holonomy and residue remain language-specific.",
            ],
        ))

    return cards, alignments


def validate_trilingual_runtime_cards(cards: list[CielingoRuntimeCard]) -> dict[str, Any]:
    results = [validate_runtime_card(card) for card in cards]
    slots: dict[int, set[str]] = {}
    for card in cards:
        slots.setdefault(card.slot_id, set()).add(card.language_id)

    missing = {
        slot_id: sorted({"pl", "en", "ja"} - langs)
        for slot_id, langs in sorted(slots.items())
        if langs != {"pl", "en", "ja"}
    }

    return {
        "ok": all(r.ok for r in results) and not missing,
        "card_count": len(cards),
        "slot_count": len(slots),
        "missing_languages_by_slot": missing,
        "invalid_cards": [r.to_dict() for r in results if not r.ok],
        "warning_count": sum(len([i for i in r.issues if i.severity.value == "WARN"]) for r in results),
    }
