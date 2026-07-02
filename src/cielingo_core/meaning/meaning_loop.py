
"""MeaningLoop / SemanticScar integration v0.7A.

Integrates sentence-card coupling and coupling-aware cross-language alignment
with explicit closure/debt/scar diagnostics.

Boundaries:
- SemanticScar is a diagnostic trace, not punishment;
- MeaningLoop is a closure/debt model, not memory writeback;
- no SOURCE/canon/NOEMA/CURRENT authority.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha256
import json
from typing import Any


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


class LoopState(str, Enum):
    OPEN = "open"
    CLOSING = "closing"
    CLOSED = "closed"
    SCARRED = "scarred"
    FAILED = "failed"


class SemanticScarType(str, Enum):
    MISSING_SOURCE = "missing_source"
    TRANSLATION_RESIDUE = "translation_residue"
    COUPLING_RESIDUE = "coupling_residue"
    AUTHORITY_LEAK = "authority_leak"
    FALSE_CLOSURE = "false_closure"
    UNRESOLVED_SLOT = "unresolved_slot"
    NATIVE_REVIEW_REQUIRED = "native_review_required"


@dataclass(frozen=True)
class SemanticScar:
    scar_id: str
    scar_type: SemanticScarType
    source_ref: str
    severity: float
    memory_effect: str
    repair_hint: str
    source_binding: str = "artifact_grounded"
    canon_allowed: bool = False
    noema_writeback_allowed: bool = False
    limitation: str = "semantic_scar_diagnostic_trace_not_memory_write"

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.scar_id:
            issues.append("scar_id is required")
        if not 0.0 <= float(self.severity) <= 1.0:
            issues.append("severity must be in [0,1]")
        if self.canon_allowed:
            issues.append("SemanticScar must not allow canon")
        if self.noema_writeback_allowed:
            issues.append("SemanticScar must not write NOEMA")
        if "not_memory_write" not in self.limitation:
            issues.append("SemanticScar must state not_memory_write limitation")
        return issues

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["scar_type"] = self.scar_type.value
        return out


@dataclass(frozen=True)
class MeaningLoop:
    loop_id: str
    input_ref: str
    response_ref: str | None
    loop_state: LoopState
    closure_score: float
    contradiction_score: float
    residue_score: float
    return_required: bool
    scars: list[SemanticScar] = field(default_factory=list)
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    limitation: str = "meaning_loop_closure_model_not_memory_writeback"

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.loop_id:
            issues.append("loop_id is required")
        if not self.input_ref:
            issues.append("input_ref is required")
        for name in ["closure_score", "contradiction_score", "residue_score"]:
            value = getattr(self, name)
            if not 0.0 <= float(value) <= 1.0:
                issues.append(f"{name} must be in [0,1]")
        for scar in self.scars:
            issues.extend(scar.validate())
        if self.canon_allowed:
            issues.append("MeaningLoop must not allow canon")
        if self.source_promotion_allowed:
            issues.append("MeaningLoop must not promote SOURCE")
        if self.noema_writeback_allowed:
            issues.append("MeaningLoop must not write NOEMA")
        if self.current_update_allowed:
            issues.append("MeaningLoop must not update CURRENT")
        if "not_memory_writeback" not in self.limitation:
            issues.append("MeaningLoop must state not_memory_writeback limitation")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "loop_id": self.loop_id,
            "input_ref": self.input_ref,
            "response_ref": self.response_ref,
            "loop_state": self.loop_state.value,
            "closure_score": self.closure_score,
            "contradiction_score": self.contradiction_score,
            "residue_score": self.residue_score,
            "return_required": self.return_required,
            "scars": [scar.to_dict() for scar in self.scars],
            "canon_allowed": self.canon_allowed,
            "source_promotion_allowed": self.source_promotion_allowed,
            "noema_writeback_allowed": self.noema_writeback_allowed,
            "current_update_allowed": self.current_update_allowed,
            "limitation": self.limitation,
        }

    def stable_hash(self) -> str:
        payload = json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True)
        return sha256(payload.encode("utf-8")).hexdigest()


def _scar(scar_type: SemanticScarType, source_ref: str, severity: float, repair_hint: str, memory_effect: str = "repair_required") -> SemanticScar:
    base = json.dumps({
        "scar_type": scar_type.value,
        "source_ref": source_ref,
        "severity": round(clamp01(severity), 6),
        "repair_hint": repair_hint,
    }, ensure_ascii=False, sort_keys=True)
    return SemanticScar(
        scar_id="scar_" + sha256(base.encode("utf-8")).hexdigest()[:16],
        scar_type=scar_type,
        source_ref=source_ref,
        severity=round(clamp01(severity), 6),
        memory_effect=memory_effect,
        repair_hint=repair_hint,
        source_binding="artifact_grounded",
        canon_allowed=False,
        noema_writeback_allowed=False,
    )


def build_meaning_loop_from_coupling_alignment(
    *,
    input_ref: str,
    coupling_report: Any | None = None,
    alignment_report: Any | None = None,
    source_required: bool = False,
    source_present: bool = False,
) -> MeaningLoop:
    """Build a meaning loop from coupling/alignment diagnostics.

    This function does not write memory. It only returns a diagnostic object.
    """
    scars: list[SemanticScar] = []
    residue_score = 0.0
    contradiction_score = 0.0

    if coupling_report is not None:
        residue = float(getattr(coupling_report, "coupling_residue", 0.0))
        residue_score = max(residue_score, clamp01(residue))
        if residue > 0:
            scars.append(_scar(SemanticScarType.COUPLING_RESIDUE, getattr(coupling_report, "report_id", "coupling_report"), residue, "Resolve or classify uncoupled slot axes."))

        for flag in ["semantic_identity_claimed", "canon_allowed", "source_promotion_allowed", "noema_writeback_allowed", "current_update_allowed", "runtime_cognition_claimed"]:
            if getattr(coupling_report, flag, False) is True:
                contradiction_score = max(contradiction_score, 1.0)
                scars.append(_scar(SemanticScarType.AUTHORITY_LEAK, getattr(coupling_report, "report_id", "coupling_report"), 1.0, f"Force {flag}=False."))

    if alignment_report is not None:
        for candidate in list(getattr(alignment_report, "candidates", []) or []):
            for residue in list(getattr(candidate, "residue", []) or []):
                rtype = getattr(residue, "residue_type", "")
                sev = float(getattr(residue, "severity", 0.0))
                residue_score = max(residue_score, clamp01(sev))
                if rtype == "native_review_residue":
                    scars.append(_scar(SemanticScarType.NATIVE_REVIEW_REQUIRED, getattr(candidate, "alignment_id", "alignment_candidate"), sev, "Keep JA/native-review residue before promotion.", memory_effect="candidate"))
                elif "coupling" in rtype or "slot" in rtype or "j_distance" in rtype:
                    scars.append(_scar(SemanticScarType.TRANSLATION_RESIDUE, getattr(candidate, "alignment_id", "alignment_candidate"), sev, "Treat alignment as candidate; do not promote to identity.", memory_effect="candidate"))

            for flag in ["semantic_identity_claimed", "canon_allowed", "source_promotion_allowed", "noema_writeback_allowed", "current_update_allowed"]:
                if getattr(candidate, flag, False) is True:
                    contradiction_score = max(contradiction_score, 1.0)
                    scars.append(_scar(SemanticScarType.FALSE_CLOSURE, getattr(candidate, "alignment_id", "alignment_candidate"), 1.0, f"Block false closure through {flag}."))

        for flag in ["canon_allowed", "source_promotion_allowed", "noema_writeback_allowed", "current_update_allowed"]:
            if getattr(alignment_report, flag, False) is True:
                contradiction_score = max(contradiction_score, 1.0)
                scars.append(_scar(SemanticScarType.AUTHORITY_LEAK, getattr(alignment_report, "report_id", "alignment_report"), 1.0, f"Force report {flag}=False."))

    if source_required and not source_present:
        residue_score = max(residue_score, 0.8)
        scars.append(_scar(SemanticScarType.MISSING_SOURCE, input_ref, 0.8, "Attach verifiable source or keep answer as hypothesis."))

    closure_score = clamp01(1.0 - max(residue_score, contradiction_score))
    if contradiction_score >= 1.0:
        state = LoopState.FAILED
    elif scars:
        state = LoopState.SCARRED if residue_score >= 0.55 else LoopState.CLOSING
    else:
        state = LoopState.CLOSED

    base = json.dumps({
        "input_ref": input_ref,
        "coupling": getattr(coupling_report, "report_id", None),
        "alignment": getattr(alignment_report, "report_id", None),
        "source_required": source_required,
        "source_present": source_present,
        "scar_ids": [scar.scar_id for scar in scars],
    }, ensure_ascii=False, sort_keys=True)
    return MeaningLoop(
        loop_id="meaning_loop_" + sha256(base.encode("utf-8")).hexdigest()[:16],
        input_ref=input_ref,
        response_ref=getattr(alignment_report, "report_id", None) or getattr(coupling_report, "report_id", None),
        loop_state=state,
        closure_score=round(closure_score, 6),
        contradiction_score=round(contradiction_score, 6),
        residue_score=round(residue_score, 6),
        return_required=bool(scars),
        scars=scars,
        canon_allowed=False,
        source_promotion_allowed=False,
        noema_writeback_allowed=False,
        current_update_allowed=False,
    )
