"""Controlled 48-slot PL/EN/JA atlas for Phase 0.6A.

This extends the 0.5E 24-slot atlas additively:
- 48 GLOBAL slots total,
- PL/EN/JA cards for every slot,
- explicit native-review caution for JA,
- no SOURCE default,
- no canon default,
- no semantic identity claim across languages,
- no NOEMA writeback or CURRENT update.

This is not a regional parser, not a morphology engine, and not a translation
proof. A shared slot_id remains a comparison axis only.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .card_generator import generate_runtime_card
from .card_runtime_schema import CardOntologyClass, CielingoRuntimeCard
from .card_validator import validate_runtime_card
from .controlled_atlas_24 import CONTROLLED_ATLAS_24, AtlasAlignmentRecord
from .slot_taxonomy import SlotFamily, SlotMode, SlotTaxonomyRecord
from .contracts import SourceBindingType


CONTROLLED_ATLAS_48_ADDITIONS: list[dict[str, Any]] = [
    # Epistemic refinements
    {"slot_id": 9, "slot_key": "CLAIM", "family": SlotFamily.EPISTEMIC_SOURCE, "mode": SlotMode.ARGUMENT, "fn": "claim assertion statement candidate", "ops": [],
     "entries": {"pl": ("twierdzenie", ["twierdzenie", "teza"]), "en": ("claim", ["claim", "assertion"]), "ja": ("主張", ["主張"])}},
    {"slot_id": 10, "slot_key": "UNCERTAINTY", "family": SlotFamily.EPISTEMIC_SOURCE, "mode": SlotMode.STATE, "fn": "uncertainty maybe chyba confidence", "ops": [],
     "entries": {"pl": ("chyba", ["chyba", "niepewność"]), "en": ("uncertainty", ["uncertainty", "maybe"]), "ja": ("不確実", ["不確実", "たぶん"])}},
    {"slot_id": 11, "slot_key": "LIMITATION", "family": SlotFamily.GOVERNANCE_BOUNDARY, "mode": SlotMode.STATE, "fn": "limitation boundary constraint", "ops": [],
     "entries": {"pl": ("ograniczenie", ["ograniczenie", "limit"]), "en": ("limitation", ["limitation", "constraint"]), "ja": ("制限", ["制限"])}},
    {"slot_id": 12, "slot_key": "RISK", "family": SlotFamily.GOVERNANCE_BOUNDARY, "mode": SlotMode.STATE, "fn": "risk hazard caution", "ops": [],
     "entries": {"pl": ("ryzyko", ["ryzyko"]), "en": ("risk", ["risk", "hazard"]), "ja": ("リスク", ["リスク"])}},
    {"slot_id": 13, "slot_key": "STUB", "family": SlotFamily.GOVERNANCE_BOUNDARY, "mode": SlotMode.STATE, "fn": "stub placeholder incomplete", "ops": [],
     "entries": {"pl": ("stub", ["stub", "zaślepka"]), "en": ("stub", ["stub", "placeholder"]), "ja": ("スタブ", ["スタブ"])}},
    {"slot_id": 14, "slot_key": "DEBT", "family": SlotFamily.GOVERNANCE_BOUNDARY, "mode": SlotMode.STATE, "fn": "debt unresolved repair required", "ops": [],
     "entries": {"pl": ("dług", ["dług", "zaległość"]), "en": ("debt", ["debt", "technical debt"]), "ja": ("負債", ["負債"])}},

    # Artifact/memory extensions
    {"slot_id": 20, "slot_key": "SNAPSHOT", "family": SlotFamily.ARTIFACT_MEMORY, "mode": SlotMode.MEMORY, "fn": "snapshot state capture memory candidate", "ops": [],
     "entries": {"pl": ("snap", ["snap", "migawka"]), "en": ("snapshot", ["snapshot", "state snapshot"]), "ja": ("スナップショット", ["スナップショット"])}},
    {"slot_id": 21, "slot_key": "REPORT", "family": SlotFamily.ARTIFACT_MEMORY, "mode": SlotMode.ARGUMENT, "fn": "report diagnostic record", "ops": [],
     "entries": {"pl": ("raport", ["raport"]), "en": ("report", ["report"]), "ja": ("報告", ["報告"])}},
    {"slot_id": 26, "slot_key": "TRACE", "family": SlotFamily.ARTIFACT_MEMORY, "mode": SlotMode.MEMORY, "fn": "trace audit event", "ops": [],
     "entries": {"pl": ("ślad", ["ślad", "trace"]), "en": ("trace", ["trace", "audit trace"]), "ja": ("痕跡", ["痕跡"])}},
    {"slot_id": 27, "slot_key": "MEMORY", "family": SlotFamily.ARTIFACT_MEMORY, "mode": SlotMode.MEMORY, "fn": "memory episodic snap", "ops": [],
     "entries": {"pl": ("pamięć", ["pamięć"]), "en": ("memory", ["memory"]), "ja": ("記憶", ["記憶"])}},

    # Runtime/action extensions
    {"slot_id": 33, "slot_key": "RUN_EXECUTE", "family": SlotFamily.RUNTIME_ACTION, "mode": SlotMode.ACT, "fn": "run execute command action requires consent", "ops": ["ACTION_REQUEST"],
     "entries": {"pl": ("uruchomić", ["uruchomić", "uruchom"]), "en": ("run", ["run", "execute"]), "ja": ("実行する", ["実行する"])}},
    {"slot_id": 35, "slot_key": "EXPORT_PACKAGE", "family": SlotFamily.RUNTIME_ACTION, "mode": SlotMode.ACT, "fn": "export package archive action", "ops": ["ACTION_REQUEST"],
     "entries": {"pl": ("spakować", ["spakować", "spakuj"]), "en": ("package", ["package", "export"]), "ja": ("パッケージ化", ["パッケージ化", "エクスポート"])}},
    {"slot_id": 36, "slot_key": "REPAIR", "family": SlotFamily.RUNTIME_ACTION, "mode": SlotMode.ACT, "fn": "repair fix mend action", "ops": ["ACTION_REQUEST"],
     "entries": {"pl": ("naprawić", ["naprawić", "napraw"]), "en": ("repair", ["repair", "fix"]), "ja": ("修復する", ["修復する"])}},

    # Boundary/governance extensions
    {"slot_id": 44, "slot_key": "QUARANTINE", "family": SlotFamily.GOVERNANCE_BOUNDARY, "mode": SlotMode.STATE, "fn": "quarantine isolate review", "ops": [],
     "entries": {"pl": ("kwarantanna", ["kwarantanna"]), "en": ("quarantine", ["quarantine"]), "ja": ("隔離", ["隔離"])}},
    {"slot_id": 45, "slot_key": "AUTHORITY", "family": SlotFamily.GOVERNANCE_BOUNDARY, "mode": SlotMode.RELATION, "fn": "authority permission power boundary", "ops": [],
     "entries": {"pl": ("autorytet", ["autorytet", "uprawnienie"]), "en": ("authority", ["authority", "permission"]), "ja": ("権限", ["権限"])}},
    {"slot_id": 46, "slot_key": "BOUNDARY", "family": SlotFamily.GOVERNANCE_BOUNDARY, "mode": SlotMode.RELATION, "fn": "boundary limit border", "ops": [],
     "entries": {"pl": ("granica", ["granica"]), "en": ("boundary", ["boundary", "limit"]), "ja": ("境界", ["境界"])}},

    # Logical/relational extensions
    {"slot_id": 48, "slot_key": "CAUSE", "family": SlotFamily.LOGICAL_OPERATOR, "mode": SlotMode.RELATION, "fn": "cause because reason", "ops": [],
     "entries": {"pl": ("ponieważ", ["ponieważ", "bo"]), "en": ("because", ["because", "cause"]), "ja": ("なぜなら", ["なぜなら", "原因"])}},
    {"slot_id": 49, "slot_key": "RESULT", "family": SlotFamily.LOGICAL_OPERATOR, "mode": SlotMode.RELATION, "fn": "result therefore consequence", "ops": [],
     "entries": {"pl": ("wynik", ["wynik", "skutek"]), "en": ("result", ["result", "therefore"]), "ja": ("結果", ["結果"])}},
    {"slot_id": 50, "slot_key": "RETURN", "family": SlotFamily.LOGICAL_OPERATOR, "mode": SlotMode.OPERATOR, "fn": "return loop back", "ops": [],
     "entries": {"pl": ("powrót", ["powrót", "wróć"]), "en": ("return", ["return", "loop back"]), "ja": ("戻る", ["戻る"])}},
    {"slot_id": 51, "slot_key": "COMPARE", "family": SlotFamily.LOGICAL_OPERATOR, "mode": SlotMode.RELATION, "fn": "compare align difference", "ops": [],
     "entries": {"pl": ("porównać", ["porównać", "porównaj"]), "en": ("compare", ["compare", "align"]), "ja": ("比較する", ["比較する"])}},

    # Semantic-neural/project state
    {"slot_id": 70, "slot_key": "SENTENCE", "family": SlotFamily.ENTITY_PARTICIPANT, "mode": SlotMode.ARGUMENT, "fn": "sentence utterance expression", "ops": [],
     "entries": {"pl": ("zdanie", ["zdanie"]), "en": ("sentence", ["sentence"]), "ja": ("文", ["文"])}},
    {"slot_id": 71, "slot_key": "SLOT", "family": SlotFamily.ENTITY_PARTICIPANT, "mode": SlotMode.ARGUMENT, "fn": "slot axis comparison", "ops": [],
     "entries": {"pl": ("slot", ["slot", "oś"]), "en": ("slot", ["slot", "axis"]), "ja": ("スロット", ["スロット"])}},
    {"slot_id": 72, "slot_key": "RESIDUE", "family": SlotFamily.TIME_STATE, "mode": SlotMode.STATE, "fn": "residue remainder unresolved meaning", "ops": [],
     "entries": {"pl": ("residuum", ["residuum", "pozostałość"]), "en": ("residue", ["residue", "remainder"]), "ja": ("残差", ["残差"])}},
    {"slot_id": 73, "slot_key": "COHERENCE", "family": SlotFamily.TIME_STATE, "mode": SlotMode.STATE, "fn": "coherence consistency phase", "ops": [],
     "entries": {"pl": ("koherencja", ["koherencja", "spójność"]), "en": ("coherence", ["coherence", "consistency"]), "ja": ("整合性", ["整合性"])}},
]


CONTROLLED_ATLAS_48: list[dict[str, Any]] = CONTROLLED_ATLAS_24 + CONTROLLED_ATLAS_48_ADDITIONS


def build_taxonomy_records_48() -> list[SlotTaxonomyRecord]:
    records: list[SlotTaxonomyRecord] = []
    for spec in CONTROLLED_ATLAS_48:
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
            notes=["Controlled atlas 0.6A 48-slot taxonomy record.", "slot_id is comparison axis, not semantic identity."],
        ))
    return records


def generate_controlled_atlas_48_cards() -> tuple[list[CielingoRuntimeCard], list[AtlasAlignmentRecord], list[SlotTaxonomyRecord]]:
    cards: list[CielingoRuntimeCard] = []
    alignments: list[AtlasAlignmentRecord] = []
    taxonomy = build_taxonomy_records_48()

    for spec in CONTROLLED_ATLAS_48:
        members: list[dict[str, Any]] = []
        for lang, (lemma, forms) in spec["entries"].items():
            card = generate_runtime_card(
                card_id=f"{lang}_{spec['slot_key'].lower()}_slot_{spec['slot_id']}_v06a",
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
            card.notes.append("Controlled atlas 0.6A card; semantic identity across languages not claimed.")
            card.notes.append("slot_id is a comparison axis, not equivalence proof.")
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
                "0.6A atlas expansion remains additive over 0.5E.",
            ],
        ))

    return cards, alignments, taxonomy


def validate_controlled_atlas_48(cards: list[CielingoRuntimeCard], alignments: list[AtlasAlignmentRecord], taxonomy: list[SlotTaxonomyRecord]) -> dict[str, Any]:
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
    source_or_canon_issues = []
    for card in cards:
        if card.source_binding == SourceBindingType.SOURCE:
            source_or_canon_issues.append({"card_id": card.card_id, "issue": "card source_binding SOURCE"})
        if card.canon_allowed:
            source_or_canon_issues.append({"card_id": card.card_id, "issue": "card canon_allowed true"})

    return {
        "ok": not invalid_cards and not taxonomy_issues and not missing_languages and not alignment_issues and not ja_issues and not marker_issues and not source_or_canon_issues,
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
        "source_or_canon_issues": source_or_canon_issues,
    }
