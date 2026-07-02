"""Import all card candidates into CIELingo canon and validate."""
from __future__ import annotations

import hashlib
import json
import os
import sys
from pathlib import Path

CIELINGO_CANON = Path("/tmp/noema_surface_workspace/NOEMA_LOCAL_ROOT/head/NoemaSurface/canon/cielingo")
sys.path.insert(0, str(CIELINGO_CANON / "src"))

from cielingo_core.global_layer.card_generator import generate_runtime_card
from cielingo_core.global_layer.card_validator import validate_card_dict, CardValidationResult
from cielingo_core.global_layer.card_runtime_schema import (
    CardOntologyClass, CardValidationStatus, CielingoRuntimeCard,
)
from cielingo_core.global_layer.contracts import SourceBindingType
from cielingo_core.global_layer.slot_taxonomy import SlotTaxonomyRecord, SlotFamily, SlotMode

# --- Slot mapping based on POS ---
POS_TO_SLOT: dict[str, int] = {
    "noun": 1,
    "noun_candidate": 1,
    "verb": 2,
    "verb_infinitive": 2,
    "verb_form": 2,
    "adjective": 3,
    "adjective_candidate": 3,
    "adverb": 3,
    "adverb_candidate": 3,
    "state": 3,
    "relation": 4,
    "preposition": 4,
    "conjunction": 4,
    "particle": 4,
    "pronoun": 1,
    "modal_operator": 8,
    "unknown_word_candidate": 0,
    "technical_label_or_foreign_word": 0,
    "negation": 22,
    "question": 23,
}

LANG_MAP: dict[str, str] = {
    "pl": "pl", "pl_candidate": "pl",
    "en": "en", "english": "en",
    "de": "de", "german": "de",
    "ja": "ja", "japanese": "ja",
    "fr": "fr",
    "es": "es",
    "it": "it",
    "pt": "pt",
    "ru": "ru",
    "zh": "zh",
    "ko": "ko",
}

def _norm_lang(lang: str) -> str:
    return LANG_MAP.get(lang.strip().lower(), lang.strip())


def _to_slot(pos: str | None) -> int:
    if pos is None:
        return 0
    return POS_TO_SLOT.get(pos.strip().lower(), 0)


def convert_radical_card(data: dict) -> dict | None:
    """Convert radical_cards_seed JSON to CielingoRuntimeCard dict."""
    slot = data.get("slot_id", 0)
    if not slot:
        return None
    label = data.get("label", "")
    card_id = data.get("radical_id", f"radical:{label}")
    lang = data.get("language_id", "universal")
    lemma = label.lower()
    return {
        "card_id": card_id,
        "slot_id": slot,
        "language_id": _norm_lang(lang),
        "lemma": lemma,
        "surface_forms": [lemma, label],
        "ontology_class": "unresolved",
        "function": data.get("gloss", ""),
        "validation_status": data.get("validation_status", "draft"),
        "source_binding": data.get("source_binding", "ARTIFACT_GROUNDED"),
        "canon_allowed": False,
        "runtime": {
            "operator_bindings": [],
            "semantic_mass": data.get("confidence", 0.25),
            "affective_charge": 0.0,
            "consent_effect": "none",
            "memory_effect": "none",
        },
        "notes": data.get("notes", []),
    }


def convert_debt_card(data: dict) -> dict | None:
    """Convert meaning-debt word card to CielingoRuntimeCard dict."""
    lemma = data.get("lemma", "")
    if not lemma:
        return None
    card_id = data.get("card_id", data.get("id", ""))
    surface = data.get("surface", lemma)
    pos_data = data.get("grammatical_designation", {})
    pos = pos_data.get("part_of_speech_candidate", pos_data.get("pos", "unknown"))
    lang = data.get("language", "pl_candidate")
    conf = data.get("confidence", 0.5)
    slot = _to_slot(pos)

    surface_forms = [lemma]
    if surface and surface != lemma:
        surface_forms.append(surface)

    runtime_conf = float(conf) if conf else 0.25

    return {
        "card_id": card_id,
        "slot_id": slot or 999,
        "language_id": _norm_lang(lang),
        "lemma": lemma,
        "surface_forms": surface_forms,
        "ontology_class": "unresolved",
        "function": f"{pos}",
        "validation_status": "draft",
        "source_binding": "ARTIFACT_GROUNDED",
        "canon_allowed": False,
        "runtime": {
            "operator_bindings": [],
            "semantic_mass": runtime_conf,
            "affective_charge": 0.0,
            "consent_effect": "none",
            "memory_effect": "none",
        },
        "notes": [data.get("confidence_note", ""), f"POS: {pos}"],
    }


def convert_ge40_card(data: dict) -> dict | None:
    """Convert GE_40 word card candidate to CielingoRuntimeCard dict."""
    lemma = data.get("lemma", "")
    if not lemma:
        return None
    card_id = data.get("card_id", "")
    surface = data.get("surface", lemma)
    lang = data.get("language", "en")
    conf = data.get("confidence", 0.7)
    semantic_axes = data.get("semantic_axes", [])

    # Infer POS from semantic axes or use "unknown"
    pos = "unknown"
    pos_axis_map = {
        "noun": ["entity", "object", "person", "thing", "participant"],
        "verb": ["action", "process", "event", "change"],
        "adjective": ["property", "quality", "attribute", "state"],
        "adverb": ["manner", "time", "place", "degree"],
        "preposition": ["relation", "spatial", "temporal"],
        "conjunction": ["connector", "logical"],
        "modal": ["modality", "necessity", "possibility"],
    }
    for candidate_pos, keywords in pos_axis_map.items():
        if any(k in " ".join(semantic_axes).lower() for k in keywords):
            pos = candidate_pos
            break

    slot = _to_slot(pos)

    surface_forms = [lemma]
    if surface and surface != lemma:
        surface_forms.append(surface)

    return {
        "card_id": card_id,
        "slot_id": slot or 999,
        "language_id": _norm_lang(lang),
        "lemma": lemma,
        "surface_forms": surface_forms,
        "ontology_class": "unresolved",
        "function": f"semantic_axes: {', '.join(semantic_axes)}" if semantic_axes else "",
        "validation_status": "draft",
        "source_binding": "ARTIFACT_GROUNDED",
        "canon_allowed": False,
        "runtime": {
            "operator_bindings": [],
            "semantic_mass": conf,
            "affective_charge": 0.0,
            "consent_effect": "none",
            "memory_effect": "none",
        },
        "notes": [f"confidence_band: {data.get('confidence_band', '')}", f"schema: {data.get('schema', '')}"],
    }


def convert_phasenav_card(data: dict) -> dict | None:
    """Convert phasenav word card candidate to CielingoRuntimeCard dict."""
    lemma = data.get("lemma", "")
    if not lemma:
        return None
    card_id = data.get("card_id", "")
    surface = data.get("surface", lemma)
    lang = data.get("language", "en")
    conf = data.get("candidate_confidence", data.get("confidence", 0.5))
    semantic_mass = data.get("semantic_mass", 0.25)
    semantic_axes = data.get("semantic_axes", [])

    surface_forms = [lemma]
    if surface and surface != lemma:
        surface_forms.append(surface)

    return {
        "card_id": card_id,
        "slot_id": 999,
        "language_id": _norm_lang(lang),
        "lemma": lemma,
        "surface_forms": surface_forms,
        "ontology_class": "unresolved",
        "function": f"phasenav; holonomic_viscosity: {data.get('mean_holonomic_viscosity', 0.0)}",
        "validation_status": "draft",
        "source_binding": "ARTIFACT_GROUNDED",
        "canon_allowed": False,
        "runtime": {
            "operator_bindings": [],
            "semantic_mass": float(semantic_mass) if semantic_mass else float(conf),
            "affective_charge": float(data.get("mean_phasenav_affordance", 0.0)) or 0.0,
            "consent_effect": "none",
            "memory_effect": "none",
        },
        "notes": [f"candidate_confidence: {conf}", f"base_knowledge: {data.get('base_knowledge_confidence', 0.0)}"],
    }


def run_validation(card_dict: dict) -> tuple[bool, CardValidationResult]:
    try:
        result = validate_card_dict(card_dict)
        return result.ok, result
    except Exception as e:
        return False, CardValidationResult(ok=False, card_id=card_dict.get("card_id", "?"), issues=[])


def import_cards(source_name: str, cards: list[dict], output_dir: Path) -> dict:
    """Convert, validate, and import cards. Returns summary."""
    passed: list[dict] = []
    failed: list[dict] = []
    errors: list[dict] = []

    for i, raw in enumerate(cards):
        card_id = raw.get("card_id", raw.get("id", f"{source_name}:{i}"))
        try:
            # Use generate_runtime_card to get a properly-formed CielingoRuntimeCard
            card = generate_runtime_card(
                card_id=card_id,
                slot_id=raw.get("slot_id", 0),
                language_id=raw.get("language_id", "unknown"),
                lemma=raw.get("lemma"),
                surface_forms=raw.get("surface_forms"),
                function=raw.get("function", ""),
                ontology_class=CardOntologyClass(raw.get("ontology_class", "unresolved")),
                validation_status=CardValidationStatus(raw.get("validation_status", "draft")),
                source_binding=SourceBindingType(raw.get("source_binding", "ARTIFACT_GROUNDED")),
                operator_bindings=raw.get("runtime", {}).get("operator_bindings"),
                semantic_mass=raw.get("runtime", {}).get("semantic_mass"),
                affective_charge=raw.get("runtime", {}).get("affective_charge"),
                attach_marker=True,
            )
            result = validate_card_dict(card.to_dict())
            if result.ok:
                passed.append(card.to_dict())
            else:
                failed.append({
                    "card_id": card_id,
                    "issues": [{"code": i.code, "severity": i.severity, "message": i.message} for i in result.issues],
                })
        except Exception as e:
            errors.append({"card_id": card_id, "error": str(e)})

    # Save passed cards
    if passed:
        out_path = output_dir / f"{source_name}_imported.jsonl"
        with open(out_path, "w") as f:
            for c in passed:
                f.write(json.dumps(c, sort_keys=True) + "\n")
        print(f"  -> Saved {len(passed)} passed cards to {out_path}")

    return {
        "source": source_name,
        "total": len(cards),
        "passed": len(passed),
        "failed": len(failed),
        "errors": len(errors),
        "failure_details": failed,
        "error_details": errors,
    }


def main():
    # Paths
    output_dir = CIELINGO_CANON / "cards"
    output_dir.mkdir(parents=True, exist_ok=True)

    sources_base = Path("/tmp/noema_surface_workspace/NOEMA_LOCAL_ROOT/head/NoemaSurface")

    # --- RADICAL CARDS ---
    radical_path = (
        sources_base / "runtime" / "overlays" / "CIELINGO_LINGOPHYSICS_MERGE_20260612T004326Z"
        / "imports" / "cielingo_stage0_radical_cards_en_ja_v0_1"
        / "cielingo_stage0_radical_cards_en_ja_v0_1" / "cards" / "cielingo_radicals"
        / "radical_cards_seed_v0_1.jsonl"
    )
    print("=== RADICAL CARDS ===")
    radical_cards = []
    if radical_path.exists():
        with open(radical_path) as f:
            for line in f:
                data = json.loads(line)
                converted = convert_radical_card(data)
                if converted:
                    radical_cards.append(converted)
    print(f"  Loaded {len(radical_cards)} radical cards")
    radical_result = import_cards("radical_cards", radical_cards, output_dir)

    # --- DEBT WORD CARDS ---
    debt_base = (
        sources_base / "runtime" / "overlays" / "CIELINGO_LINGOPHYSICS_MERGE_20260612T004326Z"
        / "imports" / "CIELINGO_MEANING_DEBT_WORD_CARDS_PATCH_20260529"
        / "data" / "cielingo" / "debt_word_cards"
    )
    print("\n=== DEBT WORD CARDS ===")
    debt_files = [
        "word_candidate_cards.jsonl",
        "infinitive_candidate_cards.jsonl",
        "other_pos_candidate_cards.jsonl",
    ]
    debt_cards = []
    for fname in debt_files:
        fp = debt_base / fname
        if fp.exists():
            with open(fp) as f:
                for line in f:
                    data = json.loads(line)
                    converted = convert_debt_card(data)
                    if converted:
                        debt_cards.append(converted)
            print(f"  {fname}: loaded")
    print(f"  Total debt cards: {len(debt_cards)}")
    debt_result = import_cards("debt_word_cards", debt_cards, output_dir)

    # --- GE_40 WORD CARDS (only one copy since duplicates) ---
    ge40_path = (
        sources_base / "cards" / "cielingo_candidates"
        / "20260612T231820758837Z_CIELINGO_WORD_CARD_CANDIDATES_GE_40.noema.jsonl"
    )
    print("\n=== GE_40 WORD CARDS ===")
    ge40_cards = []
    if ge40_path.exists():
        with open(ge40_path) as f:
            for line in f:
                data = json.loads(line)
                converted = convert_ge40_card(data)
                if converted:
                    ge40_cards.append(converted)
    print(f"  Loaded {len(ge40_cards)} GE_40 cards")
    ge40_result = import_cards("ge40_word_cards", ge40_cards, output_dir)

    # --- PHASENAV CARDS ---
    phasenav_path = (
        sources_base / "cards" / "cielingo_candidates"
        / "20260612T233257426513Z_CIELINGO_PHASENAV_WORD_CARD_CANDIDATES_GE_40.noema.jsonl"
    )
    print("\n=== PHASENAV CARDS ===")
    phasenav_cards = []
    if phasenav_path.exists():
        with open(phasenav_path) as f:
            for line in f:
                data = json.loads(line)
                converted = convert_phasenav_card(data)
                if converted:
                    phasenav_cards.append(converted)
    print(f"  Loaded {len(phasenav_cards)} phasenav cards")
    phasenav_result = import_cards("phasenav_cards", phasenav_cards, output_dir)

    # --- SUMMARY ---
    print("\n\n========== IMPORT SUMMARY ==========")
    all_results = [radical_result, debt_result, ge40_result, phasenav_result]
    total_input = sum(r["total"] for r in all_results)
    total_passed = sum(r["passed"] for r in all_results)
    total_failed = sum(r["failed"] for r in all_results)
    total_errors = sum(r["errors"] for r in all_results)
    print(f"Total input cards: {total_input}")
    print(f"Passed validation: {total_passed}")
    print(f"Failed validation: {total_failed}")
    print(f"Errors:            {total_errors}")

    for r in all_results:
        print(f"\n  {r['source']}: {r['passed']}/{r['total']} passed, {r['failed']} failed, {r['errors']} errors")
        if r["failed"]:
            print(f"    First 5 failures:")
            for f in r["failure_details"][:5]:
                print(f"      - {f['card_id']}: {[x['code'] for x in f['issues']]}")

    # --- CONSOLIDATE INTO ONE FILE ---
    all_passed = []
    for source_name in ["radical_cards", "debt_word_cards", "ge40_word_cards", "phasenav_cards"]:
        fp = output_dir / f"{source_name}_imported.jsonl"
        if fp.exists():
            with open(fp) as f:
                for line in f:
                    all_passed.append(json.loads(line))
    consolidated = output_dir / "CIELINGO_ALL_IMPORTED_CARDS.jsonl"
    with open(consolidated, "w") as f:
        for c in all_passed:
            f.write(json.dumps(c, sort_keys=True) + "\n")
    print(f"\nConsolidated: {len(all_passed)} cards -> {consolidated}")

    # --- SAVE REPORT ---
    report = {
        "total_input": total_input,
        "passed": total_passed,
        "failed": total_failed,
        "errors": total_errors,
        "details": [
            {k: r[k] for k in ["source", "total", "passed", "failed", "errors"]}
            for r in all_results
        ],
    }
    report_path = output_dir / "IMPORT_REPORT.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print(f"Report: {report_path}")


if __name__ == "__main__":
    main()
