"""Atlas-driven sentence/card coupling v0.6B.

Couples SentenceStateSnapshot nodes to controlled atlas cards by slot_id and
language_id.

Boundary:
- coupling_candidate ≠ semantic identity;
- card link ≠ parser proof;
- slot_id = comparison/coupling axis;
- no SOURCE/canon/NOEMA/CURRENT authority;
- no runtime cognition claim.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from cielingo_core.semantic_neural.sentence_state import SentenceStateSnapshot


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


@dataclass(frozen=True)
class AtlasCardLink:
    node_id: str
    token: str
    slot_id: int
    card_id: str
    language_id: str
    lemma: str
    coupling_strength: float
    evidence: str
    limitation: str = "atlas_card_link_not_parser_proof"

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.node_id:
            issues.append("node_id is required")
        if not self.card_id:
            issues.append("card_id is required")
        if not self.language_id:
            issues.append("language_id is required")
        if not 0.0 <= float(self.coupling_strength) <= 1.0:
            issues.append("coupling_strength must be in [0,1]")
        if "not_parser_proof" not in self.limitation:
            issues.append("AtlasCardLink must state not_parser_proof limitation")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SentenceCardCouplingReport:
    report_id: str
    snapshot_id: str
    language_id: str
    text: str
    links: list[AtlasCardLink]
    unresolved_slot_ids: list[int] = field(default_factory=list)
    coupling_residue: float = 0.0
    semantic_identity_claimed: bool = False
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    runtime_cognition_claimed: bool = False
    limitation: str = "sentence_card_coupling_report_not_semantic_identity"

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.report_id:
            issues.append("report_id is required")
        if not self.snapshot_id:
            issues.append("snapshot_id is required")
        if not self.language_id:
            issues.append("language_id is required")
        for link in self.links:
            issues.extend(link.validate())
        if not 0.0 <= float(self.coupling_residue) <= 1.0:
            issues.append("coupling_residue must be in [0,1]")
        if self.semantic_identity_claimed:
            issues.append("coupling report must not claim semantic identity")
        if self.canon_allowed:
            issues.append("coupling report must not allow canon")
        if self.source_promotion_allowed:
            issues.append("coupling report must not promote SOURCE")
        if self.noema_writeback_allowed:
            issues.append("coupling report must not write NOEMA")
        if self.current_update_allowed:
            issues.append("coupling report must not update CURRENT")
        if self.runtime_cognition_claimed:
            issues.append("coupling report must not claim runtime cognition")
        if "not_semantic_identity" not in self.limitation:
            issues.append("coupling report must state not_semantic_identity limitation")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "snapshot_id": self.snapshot_id,
            "language_id": self.language_id,
            "text": self.text,
            "links": [link.to_dict() for link in self.links],
            "unresolved_slot_ids": list(self.unresolved_slot_ids),
            "coupling_residue": self.coupling_residue,
            "semantic_identity_claimed": self.semantic_identity_claimed,
            "canon_allowed": self.canon_allowed,
            "source_promotion_allowed": self.source_promotion_allowed,
            "noema_writeback_allowed": self.noema_writeback_allowed,
            "current_update_allowed": self.current_update_allowed,
            "runtime_cognition_claimed": self.runtime_cognition_claimed,
            "limitation": self.limitation,
        }

    def stable_hash(self) -> str:
        payload = json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)
        return sha256(payload.encode("utf-8")).hexdigest()


def load_atlas_cards_by_language_and_slot(cards_path: str | Path) -> dict[tuple[str, int], list[dict[str, Any]]]:
    path = Path(cards_path)
    index: dict[tuple[str, int], list[dict[str, Any]]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        key = (str(row["language_id"]), int(row["slot_id"]))
        index.setdefault(key, []).append(row)
    return index


def load_atlas_cards_by_language_and_surface(cards_path: str | Path) -> dict[tuple[str, str], list[dict[str, Any]]]:
    """Index cards by language and lemma/surface forms.

    This is a fallback coupling index. It does not prove parsing; it only creates
    card-link candidates when snapshot slot_ids are absent or non-atlas.
    """
    path = Path(cards_path)
    index: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        lang = str(row["language_id"])
        surfaces = {str(row.get("lemma", "")).lower()}
        surfaces.update(str(x).lower() for x in row.get("surface_forms", []))
        for surface in surfaces:
            if surface:
                index.setdefault((lang, surface), []).append(row)
    return index


def _make_link(node: Any, selected: dict[str, Any], *, evidence: str) -> AtlasCardLink:
    exact = evidence == "exact_surface_or_lemma_match"
    strength = clamp01((0.75 if exact else 0.45) * float(node.activation))
    return AtlasCardLink(
        node_id=node.node_id,
        token=node.token,
        slot_id=int(selected.get("slot_id")),
        card_id=str(selected.get("card_id")),
        language_id=str(selected.get("language_id")),
        lemma=str(selected.get("lemma")),
        coupling_strength=round(strength, 6),
        evidence=evidence,
    )


def build_sentence_card_coupling(
    snapshot: SentenceStateSnapshot,
    cards_path: str | Path,
) -> SentenceCardCouplingReport:
    """Build coupling candidates between snapshot nodes and controlled atlas cards.

    Coupling uses:
    1. explicit node.slot_ids when those slot_ids exist in the atlas for language;
    2. fallback token surface/lemma match against controlled atlas cards.

    Both are candidates only.
    """
    by_slot = load_atlas_cards_by_language_and_slot(cards_path)
    by_surface = load_atlas_cards_by_language_and_surface(cards_path)

    links: list[AtlasCardLink] = []
    unresolved: list[int] = []

    seen: set[tuple[str, int, str]] = set()

    for node in snapshot.nodes:
        token_lower = node.token.lower()

        # First: explicit slot axes.
        for slot_id in node.slot_ids:
            candidates = by_slot.get((snapshot.language_id, int(slot_id)), [])
            if not candidates:
                unresolved.append(int(slot_id))
                continue

            selected = candidates[0]
            for cand in candidates:
                forms = [str(x).lower() for x in cand.get("surface_forms", [])]
                lemma = str(cand.get("lemma", "")).lower()
                if token_lower == lemma or token_lower in forms:
                    selected = cand
                    break

            key = (node.node_id, int(selected.get("slot_id")), str(selected.get("card_id")))
            if key not in seen:
                seen.add(key)
                forms = [str(x).lower() for x in selected.get("surface_forms", [])]
                lemma_lower = str(selected.get("lemma", "")).lower()
                exact = token_lower == lemma_lower or token_lower in forms
                links.append(_make_link(node, selected, evidence="exact_surface_or_lemma_match" if exact else "slot_id_match_only"))

        # Second: surface fallback. This is crucial when snapshot slot_ids are
        # absent, deprecated, or from an older atlas generation.
        for cand in by_surface.get((snapshot.language_id, token_lower), []):
            key = (node.node_id, int(cand.get("slot_id")), str(cand.get("card_id")))
            if key not in seen:
                seen.add(key)
                links.append(_make_link(node, cand, evidence="exact_surface_or_lemma_match"))

    total_axes = len(links) + len(set(unresolved))
    residue = 0.0 if total_axes == 0 else clamp01(len(set(unresolved)) / total_axes)
    base = json.dumps({
        "snapshot": snapshot.snapshot_id,
        "links": [link.to_dict() for link in links],
        "unresolved": sorted(set(unresolved)),
    }, ensure_ascii=False, sort_keys=True)
    report_id = "sent_card_coupling_" + sha256(base.encode("utf-8")).hexdigest()[:16]

    return SentenceCardCouplingReport(
        report_id=report_id,
        snapshot_id=snapshot.snapshot_id,
        language_id=snapshot.language_id,
        text=snapshot.text,
        links=links,
        unresolved_slot_ids=sorted(set(unresolved)),
        coupling_residue=round(residue, 6),
        semantic_identity_claimed=False,
        canon_allowed=False,
        source_promotion_allowed=False,
        noema_writeback_allowed=False,
        current_update_allowed=False,
        runtime_cognition_claimed=False,
    )
