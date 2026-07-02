
"""Architecture Gap Map v1.1C.

Maps actual state vs expected state for GLOBAL -> REGIONAL -> EXPRESSIVE
and reverse codecs.

This is an audit artifact, not SOURCE/canon/NOEMA writeback.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from hashlib import sha256
import json
from typing import Any


class GapSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCKER = "blocker"


class GapType(str, Enum):
    MISSING_OBJECT = "missing_object"
    PARTIAL_IMPLEMENTATION = "partial_implementation"
    CONTRACT_ONLY = "contract_only"
    TEST_GAP = "test_gap"
    REVERSE_CODEC_MISSING = "reverse_codec_missing"


SEVERITY_WEIGHT = {
    GapSeverity.INFO: 0.10,
    GapSeverity.WARNING: 0.35,
    GapSeverity.ERROR: 0.70,
    GapSeverity.BLOCKER: 1.00,
}


@dataclass(frozen=True)
class ArchitectureGap:
    component: str
    actual_state: str
    expected_state: str
    gap_type: GapType
    severity: GapSeverity
    repair_action: str
    test_required: str
    audience: list[str] = field(default_factory=list)
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    runtime_execution_allowed: bool = False

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.component:
            issues.append("component is required")
        if not self.actual_state:
            issues.append("actual_state is required")
        if not self.expected_state:
            issues.append("expected_state is required")
        if not self.repair_action:
            issues.append("repair_action is required")
        if not self.test_required:
            issues.append("test_required is required")
        for flag, value in [
            ("canon_allowed", self.canon_allowed),
            ("source_promotion_allowed", self.source_promotion_allowed),
            ("noema_writeback_allowed", self.noema_writeback_allowed),
            ("current_update_allowed", self.current_update_allowed),
            ("runtime_execution_allowed", self.runtime_execution_allowed),
        ]:
            if value:
                issues.append(f"gap must not enable {flag}")
        return issues

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["gap_type"] = self.gap_type.value
        out["severity"] = self.severity.value
        return out

    @property
    def severity_weight(self) -> float:
        return SEVERITY_WEIGHT[self.severity]


@dataclass(frozen=True)
class ArchitectureGapReport:
    report_id: str
    phase: str
    gaps: list[ArchitectureGap]
    expected_axis: str = "GLOBAL->REGIONAL->EXPRESSIVE + reverse codecs"
    reference_kind: str = "artifact_grounded_architecture_gap_map"
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    runtime_execution_allowed: bool = False
    limitation: str = "architecture_gap_report_not_source_not_execution"

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.report_id:
            issues.append("report_id is required")
        if not self.gaps:
            issues.append("gaps must not be empty")
        for gap in self.gaps:
            issues.extend(gap.validate())
        if self.reference_kind != "artifact_grounded_architecture_gap_map":
            issues.append("wrong reference_kind")
        if self.canon_allowed:
            issues.append("gap report must not allow canon")
        if self.source_promotion_allowed:
            issues.append("gap report must not promote SOURCE")
        if self.noema_writeback_allowed:
            issues.append("gap report must not write NOEMA")
        if self.current_update_allowed:
            issues.append("gap report must not update CURRENT")
        if self.runtime_execution_allowed:
            issues.append("gap report must not allow runtime execution")
        if "not_source" not in self.limitation or "not_execution" not in self.limitation:
            issues.append("limitation must state not_source and not_execution")
        return issues

    @property
    def gap_load(self) -> float:
        """Mean weighted open-gap load in [0,1]."""
        if not self.gaps:
            return 0.0
        return round(sum(g.severity_weight for g in self.gaps) / len(self.gaps), 6)

    @property
    def blocker_count(self) -> int:
        return sum(1 for g in self.gaps if g.severity == GapSeverity.BLOCKER)

    @property
    def expected_vs_actual_delta(self) -> dict[str, Any]:
        by_type: dict[str, int] = {}
        by_audience: dict[str, int] = {}
        for gap in self.gaps:
            by_type[gap.gap_type.value] = by_type.get(gap.gap_type.value, 0) + 1
            for aud in gap.audience:
                by_audience[aud] = by_audience.get(aud, 0) + 1
        return {
            "gap_count": len(self.gaps),
            "gap_load": self.gap_load,
            "blocker_count": self.blocker_count,
            "by_type": dict(sorted(by_type.items())),
            "by_audience": dict(sorted(by_audience.items())),
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "phase": self.phase,
            "expected_axis": self.expected_axis,
            "gaps": [g.to_dict() for g in self.gaps],
            "expected_vs_actual_delta": self.expected_vs_actual_delta,
            "reference_kind": self.reference_kind,
            "canon_allowed": self.canon_allowed,
            "source_promotion_allowed": self.source_promotion_allowed,
            "noema_writeback_allowed": self.noema_writeback_allowed,
            "current_update_allowed": self.current_update_allowed,
            "runtime_execution_allowed": self.runtime_execution_allowed,
            "limitation": self.limitation,
        }

    def stable_hash(self) -> str:
        return sha256(json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def build_default_architecture_gap_report() -> ArchitectureGapReport:
    gaps = [
        ArchitectureGap(
            component="GLOBAL.CommonFunctionalFrame",
            actual_state="missing as formal object; query understanding remains heuristic",
            expected_state="typed common functional roles: entity/action/relation/operator/context",
            gap_type=GapType.MISSING_OBJECT,
            severity=GapSeverity.ERROR,
            repair_action="add common_functional_frame.py with slots, operators and calculations",
            test_required="test_common_functional_frame_contract.py",
            audience=["IT", "math", "lingual"],
        ),
        ArchitectureGap(
            component="GLOBAL reverse codec",
            actual_state="AllowedResponseContract exists; reverse global decoder is incomplete",
            expected_state="MeaningFrame/ResponseContract -> RegionalRealizationRequest",
            gap_type=GapType.REVERSE_CODEC_MISSING,
            severity=GapSeverity.ERROR,
            repair_action="add global_codecs.py with encode/decode contracts",
            test_required="test_global_regional_reverse_codecs_contract.py",
            audience=["IT", "math"],
        ),
        ArchitectureGap(
            component="REGIONAL.PL grammar parts",
            actual_state="partial PL solver and PL response realizer exist",
            expected_state="PartOfSpeech, SentencePart, MorphologyFeature and SemanticOperatorRole enums",
            gap_type=GapType.PARTIAL_IMPLEMENTATION,
            severity=GapSeverity.ERROR,
            repair_action="add grammar_parts.py and RegionalGrammarFrame",
            test_required="test_pl_grammar_parts_contract.py",
            audience=["IT", "lingual"],
        ),
        ArchitectureGap(
            component="REGIONAL.PL reverse codec",
            actual_state="PL realizer exists only for response markers",
            expected_state="CommonFunctionalFrame/ResponseContract -> PLSurfacePlan",
            gap_type=GapType.REVERSE_CODEC_MISSING,
            severity=GapSeverity.WARNING,
            repair_action="add pl_codecs.py with forward/regional and reverse surface-plan stubs",
            test_required="test_global_regional_reverse_codecs_contract.py",
            audience=["IT", "lingual"],
        ),
        ArchitectureGap(
            component="EXPRESSIVE contract",
            actual_state="StyleRenderer exists with 4 styles and marker preservation",
            expected_state="ExpressiveContract with priority, move, compression and ornamentation",
            gap_type=GapType.PARTIAL_IMPLEMENTATION,
            severity=GapSeverity.WARNING,
            repair_action="add expressive_contract.py and expressive_codecs.py",
            test_required="test_expressive_contract_preserves_markers.py",
            audience=["IT", "lingual", "investor"],
        ),
        ArchitectureGap(
            component="Theoretical PDF handoff",
            actual_state="architecture discussed in chat and code artifacts",
            expected_state="compiled PDF with stakeholder sections and mathematical definitions",
            gap_type=GapType.MISSING_OBJECT,
            severity=GapSeverity.WARNING,
            repair_action="add XeLaTeX theoretical report and rendered PDF",
            test_required="manual PDF render QA",
            audience=["investor", "IT", "math", "lingual"],
        ),
    ]
    payload = json.dumps([g.to_dict() for g in gaps], ensure_ascii=False, sort_keys=True)
    return ArchitectureGapReport(
        report_id="architecture_gap_" + sha256(payload.encode("utf-8")).hexdigest()[:16],
        phase="1.1C",
        gaps=gaps,
    )
