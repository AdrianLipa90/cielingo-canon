"""Adapted Polish regional solver for CIELingo 0.5O.

Adds Polish v0.2 regional diagnostics:
- case_hint candidates, not full cases;
- role_candidate objects, not final semantic roles;
- negation-scope candidates, not complete logical scope;
- imperative/action-force candidates, not runtime authorization;
- source_required candidates, not SOURCE;
- canon_attempt/canon_block candidates, not canon;
- bounded PL J components, not physical Kuramoto measurements.

This is still not a full Polish parser or morphology engine.
"""

from __future__ import annotations

from pathlib import Path

from cielingo_core.global_layer.contracts import SurfaceSolution
from cielingo_core.regional.base import RegionalSolveResult, SurfaceSegments
from cielingo_core.regional.simple_solver_utils import (
    build_local_j,
    build_projection,
    load_atlas_cards,
    match_cards_to_tokens,
    simple_space_segment,
)
from cielingo_core.language_spaces.pl.grammar import analyze_polish_tokens
from cielingo_core.language_spaces.pl.j_holonomy import build_pl_kuramoto_holonomy, attach_kuramoto_report_to_local_j
from cielingo_core.language_spaces.pl.case_hints import case_hints_to_notes, infer_case_hints
from cielingo_core.language_spaces.pl.canon_phrase import canon_phrases_to_notes, detect_canon_phrases
from cielingo_core.language_spaces.pl.imperative_force import detect_imperative_force, imperative_force_to_notes
from cielingo_core.language_spaces.pl.negation_scope import detect_negation_scope, negation_scope_to_notes
from cielingo_core.language_spaces.pl.polish_j_components import compute_polish_j_components, polish_j_components_to_notes
from cielingo_core.language_spaces.pl.role_inference import infer_role_candidates, role_candidates_to_notes
from cielingo_core.language_spaces.pl.source_phrase import detect_source_phrases, source_phrases_to_notes


def _pl_v02_diagnostics(tokens: list[str]) -> tuple[list[dict[str, object]], dict[str, float]]:
    """Compute PL v0.2 diagnostic notes and bounded local_j.

    All outputs are candidates/hints. Nothing here promotes SOURCE, canon,
    runtime action, or physical Kuramoto measurement.
    """
    case_hints = infer_case_hints(tokens)
    role_candidates = infer_role_candidates(tokens)
    negations = detect_negation_scope(tokens)
    imperatives = detect_imperative_force(tokens)
    source_phrases = detect_source_phrases(tokens)
    canon_phrases = detect_canon_phrases(tokens)

    notes: list[dict[str, object]] = []
    notes.extend(case_hints_to_notes(case_hints))
    notes.extend(role_candidates_to_notes(role_candidates))
    notes.extend(negation_scope_to_notes(negations))
    notes.extend(imperative_force_to_notes(imperatives))
    notes.extend(source_phrases_to_notes(source_phrases))
    notes.extend(canon_phrases_to_notes(canon_phrases))

    local_j = compute_polish_j_components(
        case_hint_count=len(case_hints),
        role_candidate_count=len(role_candidates),
        negation_count=len(negations),
        imperative_count=len(imperatives),
        source_count=len(source_phrases),
        canon_count=len(canon_phrases),
    )
    notes.extend(polish_j_components_to_notes(local_j))
    notes.append({
        "kind": "pl_v02_limitation",
        "status": "limitation",
        "description": "PL v0.2 emits hints/candidates only, not full grammatical parsing.",
    })
    return notes, local_j


class PolishRegionalSolver:
    language_id = "pl"

    def __init__(self, repo_root: str | Path):
        self.repo_root = Path(repo_root)
        self.cards = load_atlas_cards(self.repo_root, self.language_id)

    def segment(self, text: str) -> SurfaceSegments:
        return SurfaceSegments(
            language_id=self.language_id,
            text=text,
            tokens=simple_space_segment(text),
            notes=["Whitespace segmentation + PL local grammar hints; no full morphology."],
        )

    def solve(self, text: str) -> RegionalSolveResult:
        segments = self.segment(text)
        candidates = match_cards_to_tokens(self.cards, segments.tokens, self.language_id)
        slot_projection = build_projection(candidates)
        grammar = analyze_polish_tokens(segments.tokens)
        pl_v02_notes, pl_v02_local_j = _pl_v02_diagnostics(segments.tokens)

        residue_pressure = 0.10
        if grammar.case_hints:
            residue_pressure = max(residue_pressure, 0.35)
        if grammar.residues:
            residue_pressure = max(residue_pressure, max(r.get("j_weight", 0.0) for r in grammar.residues))

        scope_pressure = 0.20
        if grammar.negation_indices:
            scope_pressure = max(scope_pressure, 0.45)
        if grammar.source_phrase_indices and grammar.negation_indices:
            scope_pressure = max(scope_pressure, 0.60)

        imperative_force = 0.60 if grammar.imperative_indices else 0.25

        local_j = build_local_j(
            word_order=0.40,
            morph_particle=0.60 if grammar.case_hints else 0.35,
            scope=scope_pressure,
            residue=residue_pressure,
        )
        local_j["J_imperative_force"] = imperative_force
        local_j["J_source_phrase"] = 0.70 if grammar.source_phrase_indices else 0.10
        local_j["J_case_ambiguity"] = 0.55 if grammar.case_hints else 0.15

        # SurfaceSolution ABI is intentionally narrow. Regional details stay
        # in local_j and RegionalSolveResult.notes, not as new SurfaceSolution fields.
        local_j["J_pl_negation_detected"] = 1.0 if grammar.negation_indices else 0.0
        local_j["J_pl_case_hints_detected"] = 1.0 if grammar.case_hints else 0.0
        local_j["J_pl_preference_detected"] = 1.0 if grammar.preference_indices else 0.0

        # PL v0.2 bounded components. These are named separately from older J keys.
        for key, value in pl_v02_local_j.items():
            local_j[f"J_{key}"] = value

        confidence = 0.30
        if candidates:
            confidence = 0.65
        if grammar.imperative_indices or grammar.preference_indices or grammar.source_phrase_indices:
            confidence = max(confidence, 0.72)
        if pl_v02_local_j.get("pl_imperative_force_pressure", 0.0) > 0.0 or pl_v02_local_j.get("pl_source_phrase_pressure", 0.0) > 0.0:
            confidence = max(confidence, 0.72)

        kuramoto_report = build_pl_kuramoto_holonomy(
            word_order=local_j["J_word_order"],
            case_ambiguity=local_j["J_case_ambiguity"],
            negation_scope=local_j["J_scope"],
            imperative_force=local_j["J_imperative_force"],
            source_phrase=local_j["J_source_phrase"],
            preference_signal=local_j["J_pl_preference_detected"],
            residue_pressure=local_j["J_residue"],
        )
        local_j = attach_kuramoto_report_to_local_j(local_j, kuramoto_report)

        solution = SurfaceSolution(
            language_id=self.language_id,
            equation_id="surface_pl_" + str(abs(hash(text)) % 10_000_000),
            tokens=segments.tokens,
            slot_projection=slot_projection,
            local_j=local_j,
            confidence=confidence,
        )
        return RegionalSolveResult(
            language_id=self.language_id,
            text=text,
            segments=segments,
            candidates=candidates,
            surface_solution=solution,
            notes=[
                "PL adapted solver: grammar hints are regional residue, not GLOBAL grammar.",
                "PL local_j is normalized through J/Kuramoto holonomy guard.",
                "PL v0.2 diagnostics are hints/candidates, not full parser output.",
                {"pl_grammar_hint": grammar.to_dict(), "regional_residue": grammar.residues, "j_kuramoto_report": kuramoto_report.to_dict()},
                {"pl_v02_diagnostics": pl_v02_notes},
            ],
        )
