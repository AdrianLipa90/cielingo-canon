"""Controlled 24-slot PL/EN/JA atlas for Phase 0.5E.

This is a constrained atlas build:
- 24 GLOBAL slots,
- PL/EN/JA cards where safe,
- explicit native-review caution for JA,
- no SOURCE default,
- no canon default,
- no semantic identity claim across languages,
- no NOEMA writeback or CURRENT update.

It is not a regional parser and does not perform morphology.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .card_generator import generate_runtime_card
from .card_runtime_schema import CardOntologyClass, CielingoRuntimeCard
from .card_validator import validate_runtime_card
from .slot_taxonomy import SlotFamily, SlotMode, SlotTaxonomyRecord
from .contracts import SourceBindingType


CONTROLLED_ATLAS_24: list[dict[str, Any]] = [
    # Epistemic / source
    {"slot_id": 5, "slot_key": "SOURCE", "family": SlotFamily.EPISTEMIC_SOURCE, "mode": SlotMode.SOURCE, "fn": "source proof provenance evidence", "ops": ["SOURCE_REQUIRED"],
     "entries": {"pl": ("źródło", ["źródło", "źródła"]), "en": ("source", ["source", "evidence source"]), "ja": ("出典", ["出典", "情報源"])}},
    {"slot_id": 6, "slot_key": "EVIDENCE", "family": SlotFamily.EPISTEMIC_SOURCE, "mode": SlotMode.SOURCE, "fn": "evidence proof source hash", "ops": ["SOURCE_REQUIRED"],
     "entries": {"pl": ("dowód", ["dowód", "dowody"]), "en": ("evidence", ["evidence", "proof"]), "ja": ("証拠", ["証拠"])}},
    {"slot_id": 7, "slot_key": "HYPOTHESIS", "family": SlotFamily.EPISTEMIC_SOURCE, "mode": SlotMode.ARGUMENT, "fn": "hypothesis candidate claim not canon", "ops": [],
     "entries": {"pl": ("hipoteza", ["hipoteza", "hipotezy"]), "en": ("hypothesis", ["hypothesis", "candidate hypothesis"]), "ja": ("仮説", ["仮説"])}},
    {"slot_id": 8, "slot_key": "CANON", "family": SlotFamily.EPISTEMIC_SOURCE, "mode": SlotMode.SOURCE, "fn": "canon source required proof gate", "ops": ["SOURCE_REQUIRED"],
     "entries": {"pl": ("kanon", ["kanon", "kanoniczny"]), "en": ("canon", ["canon", "canonical"]), "ja": ("正典", ["正典"])}},

    # Artifact / memory
    {"slot_id": 15, "slot_key": "FILE", "family": SlotFamily.ARTIFACT_MEMORY, "mode": SlotMode.ARGUMENT, "fn": "file data artifact object", "ops": [],
     "entries": {"pl": ("plik", ["plik", "pliku"]), "en": ("file", ["file", "the file"]), "ja": ("ファイル", ["ファイル"])}},
    {"slot_id": 17, "slot_key": "LOG", "family": SlotFamily.ARTIFACT_MEMORY, "mode": SlotMode.MEMORY, "fn": "log trace record evidence", "ops": [],
     "entries": {"pl": ("log", ["log", "logi"]), "en": ("log", ["log", "logs"]), "ja": ("ログ", ["ログ"])}},
    {"slot_id": 18, "slot_key": "HASH", "family": SlotFamily.ARTIFACT_MEMORY, "mode": SlotMode.MEMORY, "fn": "hash checksum proof source", "ops": ["SOURCE_REQUIRED"],
     "entries": {"pl": ("hash", ["hash", "suma kontrolna"]), "en": ("hash", ["hash", "checksum"]), "ja": ("ハッシュ", ["ハッシュ", "チェックサム"])}},
    {"slot_id": 19, "slot_key": "CURRENT", "family": SlotFamily.ARTIFACT_MEMORY, "mode": SlotMode.STATE, "fn": "current pointer state noema current", "ops": [],
     "entries": {"pl": ("bieżący", ["bieżący", "aktualny"]), "en": ("current", ["current", "current pointer"]), "ja": ("現在", ["現在", "カレント"])}},

    # Runtime action
    {"slot_id": 16, "slot_key": "CHECK_VERIFY", "family": SlotFamily.RUNTIME_ACTION, "mode": SlotMode.ACT, "fn": "verify check test action", "ops": ["ACTION_REQUEST"],
     "entries": {"pl": ("sprawdzić", ["sprawdzić", "sprawdź", "sprawdza"]), "en": ("check", ["check", "verify"]), "ja": ("確認する", ["確認する", "確認して", "検証する"])}},
    {"slot_id": 30, "slot_key": "READ", "family": SlotFamily.RUNTIME_ACTION, "mode": SlotMode.ACT, "fn": "read inspect open action", "ops": ["ACTION_REQUEST"],
     "entries": {"pl": ("czytać", ["czytać", "odczytać", "przeczytaj"]), "en": ("read", ["read", "inspect"]), "ja": ("読む", ["読む", "読んで"])}},
    {"slot_id": 31, "slot_key": "WRITE_SAVE", "family": SlotFamily.RUNTIME_ACTION, "mode": SlotMode.ACT, "fn": "write save create record action", "ops": ["ACTION_REQUEST"],
     "entries": {"pl": ("zapisać", ["zapisać", "zapisz"]), "en": ("save", ["save", "write"]), "ja": ("保存する", ["保存する", "書く"])}},
    {"slot_id": 32, "slot_key": "VALIDATE", "family": SlotFamily.RUNTIME_ACTION, "mode": SlotMode.ACT, "fn": "validate verify test action source", "ops": ["ACTION_REQUEST", "SOURCE_REQUIRED"],
     "entries": {"pl": ("walidować", ["walidować", "zweryfikować"]), "en": ("validate", ["validate", "verify"]), "ja": ("検証する", ["検証する", "確認する"])}},

    # Governance / boundary
    {"slot_id": 40, "slot_key": "CONSENT", "family": SlotFamily.GOVERNANCE_BOUNDARY, "mode": SlotMode.RELATION, "fn": "consent permission boundary gate", "ops": [],
     "entries": {"pl": ("zgoda", ["zgoda", "pozwolenie"]), "en": ("consent", ["consent", "permission"]), "ja": ("同意", ["同意", "許可"])}},
    {"slot_id": 41, "slot_key": "REFUSAL", "family": SlotFamily.GOVERNANCE_BOUNDARY, "mode": SlotMode.RELATION, "fn": "refusal deny boundary", "ops": [],
     "entries": {"pl": ("odmowa", ["odmowa", "odmówić"]), "en": ("refusal", ["refusal", "deny"]), "ja": ("拒否", ["拒否", "断る"])}},
    {"slot_id": 42, "slot_key": "PAUSE", "family": SlotFamily.GOVERNANCE_BOUNDARY, "mode": SlotMode.STATE, "fn": "pause stop hold boundary", "ops": [],
     "entries": {"pl": ("pauza", ["pauza", "wstrzymaj"]), "en": ("pause", ["pause", "hold"]), "ja": ("一時停止", ["一時停止", "保留"])}},
    {"slot_id": 43, "slot_key": "ERROR", "family": SlotFamily.GOVERNANCE_BOUNDARY, "mode": SlotMode.STATE, "fn": "error fault issue repair", "ops": [],
     "entries": {"pl": ("błąd", ["błąd", "usterka"]), "en": ("error", ["error", "fault"]), "ja": ("エラー", ["エラー", "誤り"])}},

    # Logical / relational
    {"slot_id": 22, "slot_key": "NEGATION", "family": SlotFamily.LOGICAL_OPERATOR, "mode": SlotMode.OPERATOR, "fn": "not negation deny negative operator", "ops": ["NEGATION"],
     "entries": {"pl": ("nie", ["nie"]), "en": ("not", ["not", "no"]), "ja": ("ない", ["ない", "ではない"])}},
    {"slot_id": 23, "slot_key": "QUESTION", "family": SlotFamily.LOGICAL_OPERATOR, "mode": SlotMode.OPERATOR, "fn": "question ask inquiry operator", "ops": ["QUESTION"],
     "entries": {"pl": ("pytanie", ["pytanie", "czy"]), "en": ("question", ["question", "ask"]), "ja": ("質問", ["質問", "か"])}},
    {"slot_id": 24, "slot_key": "CONDITION", "family": SlotFamily.LOGICAL_OPERATOR, "mode": SlotMode.RELATION, "fn": "condition if conditional relation", "ops": [],
     "entries": {"pl": ("jeśli", ["jeśli", "gdy"]), "en": ("if", ["if", "condition"]), "ja": ("もし", ["もし", "なら"])}},
    {"slot_id": 25, "slot_key": "AND", "family": SlotFamily.LOGICAL_OPERATOR, "mode": SlotMode.OPERATOR, "fn": "and conjunction composition", "ops": [],
     "entries": {"pl": ("i", ["i", "oraz"]), "en": ("and", ["and"]), "ja": ("と", ["と", "そして"])}},

    # Entity / affect / state
    {"slot_id": 60, "slot_key": "PERSON", "family": SlotFamily.ENTITY_PARTICIPANT, "mode": SlotMode.ARGUMENT, "fn": "person human participant agent", "ops": [],
     "entries": {"pl": ("osoba", ["osoba", "człowiek"]), "en": ("person", ["person", "human"]), "ja": ("人", ["人", "人物"])}},
    {"slot_id": 61, "slot_key": "BOOK", "family": SlotFamily.ENTITY_PARTICIPANT, "mode": SlotMode.ARGUMENT, "fn": "book text artifact", "ops": [],
     "entries": {"pl": ("książka", ["książka", "książki"]), "en": ("book", ["book", "books"]), "ja": ("本", ["本"])}},
    {"slot_id": 100, "slot_key": "PREFERENCE", "family": SlotFamily.AFFECT_VALUE, "mode": SlotMode.AFFECT, "fn": "affective preference like prefer suki operator", "ops": ["PREFERENCE"],
     "entries": {"pl": ("lubić", ["lubić", "lubi", "lubię"]), "en": ("like", ["like", "likes", "prefer"]), "ja": ("好き", ["好き", "好きです"])}},
    {"slot_id": 80, "slot_key": "UNKNOWN", "family": SlotFamily.TIME_STATE, "mode": SlotMode.STATE, "fn": "unknown unresolved unclear", "ops": [],
     "entries": {"pl": ("nieznane", ["nieznane", "nieznany"]), "en": ("unknown", ["unknown", "unresolved"]), "ja": ("不明", ["不明", "未解決"])}},
]


@dataclass
class AtlasAlignmentRecord:
    slot_id: int
    slot_key: str
    alignment_type: str
    semantic_identity_claimed: bool
    members: list[dict[str, Any]]
    residue_notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_taxonomy_records() -> list[SlotTaxonomyRecord]:
    records: list[SlotTaxonomyRecord] = []
    for spec in CONTROLLED_ATLAS_24:
        records.append(SlotTaxonomyRecord(
            slot_id=spec["slot_id"],
            slot_key=spec["slot_key"],
            slot_family=spec["family"],
            slot_mode=spec["mode"],
            global_operator_candidate=bool(spec["ops"]),
            requires_runtime_extension=True,
            requires_noema_marker=True,
            requires_consent_gate=(spec["family"] == SlotFamily.RUNTIME_ACTION),
            requires_source_gate=(spec["family"] == SlotFamily.EPISTEMIC_SOURCE and spec["mode"] == SlotMode.SOURCE) or "SOURCE_REQUIRED" in spec["ops"],
            regional_surface_required=True,
            can_be_in_blanco=True,
            source_binding_default=SourceBindingType.ARTIFACT_GROUNDED,
            canon_allowed_default=False,
            notes=["Controlled atlas 0.5E taxonomy record."],
        ))
    return records


def generate_controlled_atlas_cards() -> tuple[list[CielingoRuntimeCard], list[AtlasAlignmentRecord], list[SlotTaxonomyRecord]]:
    cards: list[CielingoRuntimeCard] = []
    alignments: list[AtlasAlignmentRecord] = []
    taxonomy = build_taxonomy_records()

    for spec in CONTROLLED_ATLAS_24:
        members: list[dict[str, Any]] = []
        for lang, (lemma, forms) in spec["entries"].items():
            card = generate_runtime_card(
                card_id=f"{lang}_{spec['slot_key'].lower()}_slot_{spec['slot_id']}_v05e",
                slot_id=spec["slot_id"],
                language_id=lang,
                lemma=lemma,
                surface_forms=forms,
                function=spec["fn"],
                ontology_class=CardOntologyClass.KOTO,
                operator_bindings=spec["ops"],
                attach_marker=True,
            )
            if lang == "ja":
                card.validation_status = card.validation_status.NEEDS_REVIEW
                card.notes.append("Japanese card requires native review before validation/canon.")
            card.notes.append("Controlled atlas 0.5E card; semantic identity across languages not claimed.")
            cards.append(card)
            members.append({
                "language_id": lang,
                "card_id": card.card_id,
                "lemma": lemma,
                "equivalence_type": "slot_correspondence",
                "needs_native_review": lang == "ja",
            })

        alignments.append(AtlasAlignmentRecord(
            slot_id=spec["slot_id"],
            slot_key=spec["slot_key"],
            alignment_type="slot_correspondence",
            semantic_identity_claimed=False,
            members=members,
            residue_notes=[
                "Shared slot_id is a comparison axis, not semantic identity.",
                "Regional holonomy and residue remain language-specific.",
            ],
        ))

    return cards, alignments, taxonomy


def validate_controlled_atlas(cards: list[CielingoRuntimeCard], alignments: list[AtlasAlignmentRecord], taxonomy: list[SlotTaxonomyRecord]) -> dict[str, Any]:
    card_results = [validate_runtime_card(card) for card in cards]
    taxonomy_issues = []
    for record in taxonomy:
        for issue in record.validate():
            taxonomy_issues.append({"slot_id": record.slot_id, "slot_key": record.slot_key, "issue": issue})

    slots: dict[int, set[str]] = {}
    for card in cards:
        slots.setdefault(card.slot_id, set()).add(card.language_id)

    missing_languages = {
        slot_id: sorted({"pl", "en", "ja"} - langs)
        for slot_id, langs in sorted(slots.items())
        if langs != {"pl", "en", "ja"}
    }

    alignment_issues = []
    for alignment in alignments:
        if alignment.semantic_identity_claimed:
            alignment_issues.append({"slot_id": alignment.slot_id, "issue": "semantic identity must not be claimed"})
        langs = {m["language_id"] for m in alignment.members}
        if langs != {"pl", "en", "ja"}:
            alignment_issues.append({"slot_id": alignment.slot_id, "issue": f"alignment missing languages {sorted({'pl','en','ja'}-langs)}"})

    ja_issues = []
    for card in cards:
        if card.language_id == "ja" and card.validation_status.value not in {"needs_review", "draft"}:
            ja_issues.append({"card_id": card.card_id, "issue": "JA must remain needs_review/draft"})

    marker_issues = []
    for card in cards:
        marker = card.runtime.noema_holonomic_marker
        if marker is None:
            marker_issues.append({"card_id": card.card_id, "issue": "missing marker"})
        elif marker.noema_current_update_allowed:
            marker_issues.append({"card_id": card.card_id, "issue": "marker allows current update"})

    invalid_cards = [result.to_dict() for result in card_results if not result.ok]

    return {
        "ok": not invalid_cards and not taxonomy_issues and not missing_languages and not alignment_issues and not ja_issues and not marker_issues,
        "slot_count": len(slots),
        "card_count": len(cards),
        "alignment_count": len(alignments),
        "taxonomy_count": len(taxonomy),
        "missing_languages_by_slot": missing_languages,
        "invalid_cards": invalid_cards,
        "taxonomy_issues": taxonomy_issues,
        "alignment_issues": alignment_issues,
        "ja_issues": ja_issues,
        "marker_issues": marker_issues,
    }
