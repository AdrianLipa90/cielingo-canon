"""Cross-language alignment harness v0.5Q.

Compares regional SentenceEquation / SurfaceSolution outputs across PL/EN/JA.

Boundary:
    alignment_candidate ≠ semantic identity.
    slot_id = comparison axis, not proof of equivalence.
    no SOURCE/canon/NOEMA/CURRENT authority.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from cielingo_core.language_spaces.pl.sentence_equation import solve_pl_sentence_equation
from cielingo_core.language_spaces.en.sentence_equation import solve_en_sentence_equation
from cielingo_core.language_spaces.ja.sentence_equation import solve_ja_sentence_equation
from cielingo_core.semantic_neural.sentence_state import SentenceStateSnapshot, build_sentence_state_snapshot
from cielingo_core.semantic_neural.atlas_coupling import SentenceCardCouplingReport, build_sentence_card_coupling


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True)
class AlignmentResidue:
    residue_type: str
    description: str
    severity: float
    limitation: str = "alignment_residue_not_failure"

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.residue_type:
            issues.append("residue_type is required")
        if not self.description:
            issues.append("description is required")
        if not 0.0 <= float(self.severity) <= 1.0:
            issues.append("severity must be in [0,1]")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LanguageAlignmentCandidate:
    alignment_id: str
    language_pair: tuple[str, str]
    source_text: str
    target_text: str
    shared_slot_ids: list[int]
    source_only_slot_ids: list[int]
    target_only_slot_ids: list[int]
    j_distance: float
    token_count_delta: int
    residue: list[AlignmentResidue] = field(default_factory=list)
    confidence: float = 0.0
    semantic_identity_claimed: bool = False
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    limitation: str = "alignment_candidate_not_semantic_identity"

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.alignment_id:
            issues.append("alignment_id is required")
        if len(self.language_pair) != 2:
            issues.append("language_pair must have length 2")
        if not 0.0 <= float(self.j_distance) <= 1.0:
            issues.append("j_distance must be in [0,1]")
        if not 0.0 <= float(self.confidence) <= 1.0:
            issues.append("confidence must be in [0,1]")
        for item in self.residue:
            issues.extend(item.validate())
        if self.semantic_identity_claimed:
            issues.append("alignment must not claim semantic identity")
        if self.canon_allowed:
            issues.append("alignment must not allow canon")
        if self.source_promotion_allowed:
            issues.append("alignment must not promote SOURCE")
        if self.noema_writeback_allowed:
            issues.append("alignment must not write NOEMA")
        if self.current_update_allowed:
            issues.append("alignment must not update CURRENT")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "alignment_id": self.alignment_id,
            "language_pair": list(self.language_pair),
            "source_text": self.source_text,
            "target_text": self.target_text,
            "shared_slot_ids": list(self.shared_slot_ids),
            "source_only_slot_ids": list(self.source_only_slot_ids),
            "target_only_slot_ids": list(self.target_only_slot_ids),
            "j_distance": self.j_distance,
            "token_count_delta": self.token_count_delta,
            "residue": [item.to_dict() for item in self.residue],
            "confidence": self.confidence,
            "semantic_identity_claimed": self.semantic_identity_claimed,
            "canon_allowed": self.canon_allowed,
            "source_promotion_allowed": self.source_promotion_allowed,
            "noema_writeback_allowed": self.noema_writeback_allowed,
            "current_update_allowed": self.current_update_allowed,
            "limitation": self.limitation,
        }


@dataclass(frozen=True)
class CrossLanguageAlignmentReport:
    report_id: str
    candidates: list[LanguageAlignmentCandidate]
    snapshots: dict[str, SentenceStateSnapshot]
    limitation: str = "cross_language_alignment_report_not_translation_proof"
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.report_id:
            issues.append("report_id is required")
        for candidate in self.candidates:
            issues.extend(candidate.validate())
        for lang, snapshot in self.snapshots.items():
            if hasattr(snapshot, "validate"):
                issues.extend(snapshot.validate())
            else:
                issues.append(f"snapshot {lang} missing validate()")
        if self.canon_allowed:
            issues.append("report must not allow canon")
        if self.source_promotion_allowed:
            issues.append("report must not promote SOURCE")
        if self.noema_writeback_allowed:
            issues.append("report must not write NOEMA")
        if self.current_update_allowed:
            issues.append("report must not update CURRENT")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "snapshots": {lang: snapshot.to_dict() for lang, snapshot in sorted(self.snapshots.items())},
            "limitation": self.limitation,
            "canon_allowed": self.canon_allowed,
            "source_promotion_allowed": self.source_promotion_allowed,
            "noema_writeback_allowed": self.noema_writeback_allowed,
            "current_update_allowed": self.current_update_allowed,
        }

    def stable_hash(self) -> str:
        payload = json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)
        return sha256(payload.encode("utf-8")).hexdigest()


def _slot_ids(snapshot: SentenceStateSnapshot) -> set[int]:
    out: set[int] = set()
    for node in snapshot.nodes:
        out.update(int(slot_id) for slot_id in node.slot_ids)
    return out


def _j_distance(a: SentenceStateSnapshot, b: SentenceStateSnapshot) -> float:
    keys = set(a.j_vector.values) | set(b.j_vector.values)
    if not keys:
        return 0.0
    total = 0.0
    for key in keys:
        total += abs(float(a.j_vector.values.get(key, 0.0)) - float(b.j_vector.values.get(key, 0.0)))
    return clamp01(total / len(keys))


def _candidate(a_lang: str, a_text: str, a: SentenceStateSnapshot, b_lang: str, b_text: str, b: SentenceStateSnapshot) -> LanguageAlignmentCandidate:
    a_slots = _slot_ids(a)
    b_slots = _slot_ids(b)
    shared = sorted(a_slots & b_slots)
    a_only = sorted(a_slots - b_slots)
    b_only = sorted(b_slots - a_slots)
    jdist = _j_distance(a, b)
    token_delta = abs(len(a.tokens) - len(b.tokens))

    residue: list[AlignmentResidue] = []
    if not shared:
        residue.append(AlignmentResidue("slot_residue", "No shared slot_id comparison axis detected.", 0.75))
    if a_only or b_only:
        residue.append(AlignmentResidue("slot_divergence", "Some slot_id axes are present only on one side.", clamp01((len(a_only) + len(b_only)) / 8.0)))
    if jdist > 0.45:
        residue.append(AlignmentResidue("j_distance", "J-vector distance is high; alignment remains weak.", jdist))
    if token_delta:
        residue.append(AlignmentResidue("surface_length_delta", "Surface token counts differ.", clamp01(token_delta / 8.0)))
    if a_lang == "ja" or b_lang == "ja":
        residue.append(AlignmentResidue("native_review_residue", "JA alignment requires native/regional review before promotion.", 0.55))

    confidence = clamp01(0.25 + 0.15 * len(shared) - 0.25 * jdist - 0.05 * token_delta)
    alignment_id = "align_" + sha256(json.dumps({
        "a_lang": a_lang, "b_lang": b_lang, "a_text": a_text, "b_text": b_text,
        "shared": shared, "a_only": a_only, "b_only": b_only, "jdist": jdist,
    }, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:16]

    return LanguageAlignmentCandidate(
        alignment_id=alignment_id,
        language_pair=(a_lang, b_lang),
        source_text=a_text,
        target_text=b_text,
        shared_slot_ids=shared,
        source_only_slot_ids=a_only,
        target_only_slot_ids=b_only,
        j_distance=round(jdist, 6),
        token_count_delta=token_delta,
        residue=residue,
        confidence=round(confidence, 6),
        semantic_identity_claimed=False,
        canon_allowed=False,
        source_promotion_allowed=False,
        noema_writeback_allowed=False,
        current_update_allowed=False,
    )


def build_cross_language_alignment_report(texts: dict[str, str], repo_root: str | Path) -> CrossLanguageAlignmentReport:
    """Build a PL/EN/JA cross-language alignment report.

    Input keys may include pl, en, ja. Missing languages are simply omitted.
    """
    repo = Path(repo_root)
    equations: dict[str, Any] = {}
    if "pl" in texts:
        equations["pl"] = solve_pl_sentence_equation(texts["pl"], repo)
    if "en" in texts:
        equations["en"] = solve_en_sentence_equation(texts["en"], repo)
    if "ja" in texts:
        equations["ja"] = solve_ja_sentence_equation(texts["ja"], repo)

    snapshots = {lang: build_sentence_state_snapshot(eq, notes=[]) for lang, eq in equations.items()}

    candidates: list[LanguageAlignmentCandidate] = []
    langs = sorted(snapshots)
    for i, a_lang in enumerate(langs):
        for b_lang in langs[i + 1:]:
            candidates.append(_candidate(a_lang, texts[a_lang], snapshots[a_lang], b_lang, texts[b_lang], snapshots[b_lang]))

    report_id = "cross_align_" + sha256(json.dumps(texts, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    return CrossLanguageAlignmentReport(report_id=report_id, candidates=candidates, snapshots=snapshots)



@dataclass(frozen=True)
class CouplingAwareAlignmentCandidate:
    """Alignment candidate enriched by atlas sentence/card coupling.

    This remains a candidate. It does not assert semantic identity, translation
    proof, SOURCE/canon authority, NOEMA writeback, or CURRENT update.
    """

    alignment_id: str
    language_pair: tuple[str, str]
    source_text: str
    target_text: str
    shared_slot_ids: list[int]
    shared_card_slot_ids: list[int]
    shared_card_lemmas: list[str]
    source_only_card_slot_ids: list[int]
    target_only_card_slot_ids: list[int]
    j_distance: float
    card_coupling_distance: float
    residue: list[AlignmentResidue] = field(default_factory=list)
    confidence: float = 0.0
    semantic_identity_claimed: bool = False
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    limitation: str = "coupling_aware_alignment_candidate_not_semantic_identity"

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.alignment_id:
            issues.append("alignment_id is required")
        if len(self.language_pair) != 2:
            issues.append("language_pair must have length 2")
        if not 0.0 <= float(self.j_distance) <= 1.0:
            issues.append("j_distance must be in [0,1]")
        if not 0.0 <= float(self.card_coupling_distance) <= 1.0:
            issues.append("card_coupling_distance must be in [0,1]")
        if not 0.0 <= float(self.confidence) <= 1.0:
            issues.append("confidence must be in [0,1]")
        for item in self.residue:
            issues.extend(item.validate())
        if self.semantic_identity_claimed:
            issues.append("coupling-aware alignment must not claim semantic identity")
        if self.canon_allowed:
            issues.append("coupling-aware alignment must not allow canon")
        if self.source_promotion_allowed:
            issues.append("coupling-aware alignment must not promote SOURCE")
        if self.noema_writeback_allowed:
            issues.append("coupling-aware alignment must not write NOEMA")
        if self.current_update_allowed:
            issues.append("coupling-aware alignment must not update CURRENT")
        if "not_semantic_identity" not in self.limitation:
            issues.append("coupling-aware alignment must state not_semantic_identity limitation")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "alignment_id": self.alignment_id,
            "language_pair": list(self.language_pair),
            "source_text": self.source_text,
            "target_text": self.target_text,
            "shared_slot_ids": list(self.shared_slot_ids),
            "shared_card_slot_ids": list(self.shared_card_slot_ids),
            "shared_card_lemmas": list(self.shared_card_lemmas),
            "source_only_card_slot_ids": list(self.source_only_card_slot_ids),
            "target_only_card_slot_ids": list(self.target_only_card_slot_ids),
            "j_distance": self.j_distance,
            "card_coupling_distance": self.card_coupling_distance,
            "residue": [item.to_dict() for item in self.residue],
            "confidence": self.confidence,
            "semantic_identity_claimed": self.semantic_identity_claimed,
            "canon_allowed": self.canon_allowed,
            "source_promotion_allowed": self.source_promotion_allowed,
            "noema_writeback_allowed": self.noema_writeback_allowed,
            "current_update_allowed": self.current_update_allowed,
            "limitation": self.limitation,
        }


@dataclass(frozen=True)
class CouplingAwareCrossLanguageAlignmentReport:
    report_id: str
    candidates: list[CouplingAwareAlignmentCandidate]
    snapshots: dict[str, SentenceStateSnapshot]
    coupling_reports: dict[str, SentenceCardCouplingReport]
    limitation: str = "coupling_aware_cross_language_alignment_report_not_translation_proof"
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.report_id:
            issues.append("report_id is required")
        for candidate in self.candidates:
            issues.extend(candidate.validate())
        for lang, snapshot in self.snapshots.items():
            if hasattr(snapshot, "validate"):
                issues.extend(snapshot.validate())
            else:
                issues.append(f"snapshot {lang} missing validate()")
        for lang, coupling in self.coupling_reports.items():
            if hasattr(coupling, "validate"):
                issues.extend(coupling.validate())
            else:
                issues.append(f"coupling report {lang} missing validate()")
        if self.canon_allowed:
            issues.append("coupling-aware report must not allow canon")
        if self.source_promotion_allowed:
            issues.append("coupling-aware report must not promote SOURCE")
        if self.noema_writeback_allowed:
            issues.append("coupling-aware report must not write NOEMA")
        if self.current_update_allowed:
            issues.append("coupling-aware report must not update CURRENT")
        if "not_translation_proof" not in self.limitation:
            issues.append("coupling-aware report must state not_translation_proof limitation")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "candidates": [candidate.to_dict() for candidate in self.candidates],
            "snapshots": {lang: snapshot.to_dict() for lang, snapshot in sorted(self.snapshots.items())},
            "coupling_reports": {lang: report.to_dict() for lang, report in sorted(self.coupling_reports.items())},
            "limitation": self.limitation,
            "canon_allowed": self.canon_allowed,
            "source_promotion_allowed": self.source_promotion_allowed,
            "noema_writeback_allowed": self.noema_writeback_allowed,
            "current_update_allowed": self.current_update_allowed,
        }

    def stable_hash(self) -> str:
        payload = json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)
        return sha256(payload.encode("utf-8")).hexdigest()


def _coupled_slot_ids(report: SentenceCardCouplingReport) -> set[int]:
    return {int(link.slot_id) for link in report.links}


def _coupled_lemmas_by_slot(report: SentenceCardCouplingReport) -> dict[int, set[str]]:
    out: dict[int, set[str]] = {}
    for link in report.links:
        out.setdefault(int(link.slot_id), set()).add(str(link.lemma).lower())
    return out


def _coupling_aware_candidate(
    a_lang: str,
    a_text: str,
    a_snapshot: SentenceStateSnapshot,
    a_coupling: SentenceCardCouplingReport,
    b_lang: str,
    b_text: str,
    b_snapshot: SentenceStateSnapshot,
    b_coupling: SentenceCardCouplingReport,
) -> CouplingAwareAlignmentCandidate:
    a_snapshot_slots = _slot_ids(a_snapshot)
    b_snapshot_slots = _slot_ids(b_snapshot)
    shared_snapshot = sorted(a_snapshot_slots & b_snapshot_slots)

    a_card_slots = _coupled_slot_ids(a_coupling)
    b_card_slots = _coupled_slot_ids(b_coupling)
    shared_card = sorted(a_card_slots & b_card_slots)
    a_only = sorted(a_card_slots - b_card_slots)
    b_only = sorted(b_card_slots - a_card_slots)

    a_lemmas = _coupled_lemmas_by_slot(a_coupling)
    b_lemmas = _coupled_lemmas_by_slot(b_coupling)
    shared_lemmas: list[str] = []
    for slot_id in shared_card:
        for lemma in sorted(a_lemmas.get(slot_id, set()) | b_lemmas.get(slot_id, set())):
            shared_lemmas.append(f"{slot_id}:{lemma}")

    jdist = _j_distance(a_snapshot, b_snapshot)
    total_card_axes = len(shared_card) + len(a_only) + len(b_only)
    card_distance = 0.0 if total_card_axes == 0 else clamp01((len(a_only) + len(b_only)) / total_card_axes)

    residue: list[AlignmentResidue] = []
    if not shared_card:
        residue.append(AlignmentResidue("card_coupling_residue", "No shared atlas card slot coupling detected.", 0.75))
    if a_only or b_only:
        residue.append(AlignmentResidue("card_slot_divergence", "Atlas-coupled slot axes differ between languages.", card_distance))
    if jdist > 0.45:
        residue.append(AlignmentResidue("j_distance", "J-vector distance is high.", jdist))
    if a_lang == "ja" or b_lang == "ja":
        residue.append(AlignmentResidue("native_review_residue", "JA coupling-aware alignment requires native/regional review.", 0.55))

    confidence = clamp01(0.25 + 0.12 * len(shared_snapshot) + 0.18 * len(shared_card) - 0.25 * jdist - 0.25 * card_distance)
    alignment_id = "coupled_align_" + sha256(json.dumps({
        "a_lang": a_lang,
        "b_lang": b_lang,
        "a_text": a_text,
        "b_text": b_text,
        "shared_snapshot": shared_snapshot,
        "shared_card": shared_card,
        "a_only": a_only,
        "b_only": b_only,
        "jdist": jdist,
        "card_distance": card_distance,
    }, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:16]

    return CouplingAwareAlignmentCandidate(
        alignment_id=alignment_id,
        language_pair=(a_lang, b_lang),
        source_text=a_text,
        target_text=b_text,
        shared_slot_ids=shared_snapshot,
        shared_card_slot_ids=shared_card,
        shared_card_lemmas=shared_lemmas,
        source_only_card_slot_ids=a_only,
        target_only_card_slot_ids=b_only,
        j_distance=round(jdist, 6),
        card_coupling_distance=round(card_distance, 6),
        residue=residue,
        confidence=round(confidence, 6),
        semantic_identity_claimed=False,
        canon_allowed=False,
        source_promotion_allowed=False,
        noema_writeback_allowed=False,
        current_update_allowed=False,
    )


def build_coupling_aware_cross_language_alignment_report(
    texts: dict[str, str],
    repo_root: str | Path,
    cards_path: str | Path | None = None,
) -> CouplingAwareCrossLanguageAlignmentReport:
    """Build coupling-aware PL/EN/JA cross-language alignment report."""
    repo = Path(repo_root)
    if cards_path is None:
        cards_path = repo / "cards" / "generated_examples" / "controlled_48_slot_runtime_cards_v0_6a.jsonl"

    equations: dict[str, Any] = {}
    if "pl" in texts:
        equations["pl"] = solve_pl_sentence_equation(texts["pl"], repo)
    if "en" in texts:
        equations["en"] = solve_en_sentence_equation(texts["en"], repo)
    if "ja" in texts:
        equations["ja"] = solve_ja_sentence_equation(texts["ja"], repo)

    snapshots = {lang: build_sentence_state_snapshot(eq, notes=[]) for lang, eq in equations.items()}
    coupling_reports = {lang: build_sentence_card_coupling(snapshot, cards_path) for lang, snapshot in snapshots.items()}

    candidates: list[CouplingAwareAlignmentCandidate] = []
    langs = sorted(snapshots)
    for i, a_lang in enumerate(langs):
        for b_lang in langs[i + 1:]:
            candidates.append(_coupling_aware_candidate(
                a_lang,
                texts[a_lang],
                snapshots[a_lang],
                coupling_reports[a_lang],
                b_lang,
                texts[b_lang],
                snapshots[b_lang],
                coupling_reports[b_lang],
            ))

    report_id = "coupled_cross_align_" + sha256(json.dumps(texts, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()[:16]
    return CouplingAwareCrossLanguageAlignmentReport(
        report_id=report_id,
        candidates=candidates,
        snapshots=snapshots,
        coupling_reports=coupling_reports,
        canon_allowed=False,
        source_promotion_allowed=False,
        noema_writeback_allowed=False,
        current_update_allowed=False,
    )
