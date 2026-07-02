"""Doctor contracts for CIELingo.

This module is deliberately contract-only. It does not implement PL grammar,
runtime connectors, external NOEMA writeback, canon promotion, or SOURCE promotion.

Core rule:
    Doctor diagnoses and recommends.
    Doctor does not canonize.
    Doctor does not write external NOEMA SoT.
    Doctor does not become runtime authority.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


def clamp01(value: float) -> float:
    """Clamp a scalar to the closed [0,1] interval."""
    return max(0.0, min(1.0, float(value)))


class ImplementationStatus(str, Enum):
    """Epistemic implementation state of a feature or finding."""

    IMPLEMENTED = "implemented"
    STUB = "stub"
    LIMITATION = "limitation"
    RISK = "risk"
    DEBT = "debt"
    QUARANTINED = "quarantined"
    NEEDS_REVIEW = "needs_review"


class DoctorSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    BLOCKER = "blocker"


class DoctorLayer(str, Enum):
    LINGOPHYSICS = "lingophysics"
    NOEMA_SURFACE = "noema_surface"
    GLOBAL_LAYER = "global_layer"
    LANGUAGE_SPACE = "language_space"
    BRIDGE = "bridge"
    RUNTIME = "runtime"
    UNKNOWN = "unknown"


class RepairActionKind(str, Enum):
    NONE = "none"
    ADD_TEST = "add_test"
    ADD_CONTRACT = "add_contract"
    MARK_STUB = "mark_stub"
    MARK_LIMITATION = "mark_limitation"
    MARK_RISK = "mark_risk"
    MARK_DEBT = "mark_debt"
    QUARANTINE = "quarantine"
    REFACTOR = "refactor"
    BLOCK_PROMOTION = "block_promotion"


@dataclass(frozen=True)
class RepairCandidate:
    action_kind: RepairActionKind
    description: str
    target_path: str | None = None
    required_before_merge: bool = False

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.description:
            issues.append("RepairCandidate.description is required")
        return issues

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["action_kind"] = self.action_kind.value
        return out


@dataclass(frozen=True)
class QuarantineCandidate:
    reason: str
    target: str
    release_condition: str
    severity: DoctorSeverity = DoctorSeverity.WARNING

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.reason:
            issues.append("QuarantineCandidate.reason is required")
        if not self.target:
            issues.append("QuarantineCandidate.target is required")
        if not self.release_condition:
            issues.append("QuarantineCandidate.release_condition is required")
        return issues

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["severity"] = self.severity.value
        return out


@dataclass(frozen=True)
class DebtEntry:
    debt_id: str
    description: str
    target: str
    repayment_condition: str
    hidden: bool = False

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.debt_id:
            issues.append("DebtEntry.debt_id is required")
        if not self.description:
            issues.append("DebtEntry.description is required")
        if not self.target:
            issues.append("DebtEntry.target is required")
        if not self.repayment_condition:
            issues.append("DebtEntry.repayment_condition is required")
        if self.hidden:
            issues.append("hidden debt is forbidden")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Limitation:
    limitation_id: str
    description: str
    affected_scope: str
    consequence: str

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.limitation_id:
            issues.append("Limitation.limitation_id is required")
        if not self.description:
            issues.append("Limitation.description is required")
        if not self.affected_scope:
            issues.append("Limitation.affected_scope is required")
        if not self.consequence:
            issues.append("Limitation.consequence is required")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RiskFlag:
    risk_id: str
    description: str
    affected_layer: DoctorLayer
    mitigation: str
    severity: DoctorSeverity = DoctorSeverity.WARNING

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.risk_id:
            issues.append("RiskFlag.risk_id is required")
        if not self.description:
            issues.append("RiskFlag.description is required")
        if not self.mitigation:
            issues.append("RiskFlag.mitigation is required")
        return issues

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["affected_layer"] = self.affected_layer.value
        out["severity"] = self.severity.value
        return out


@dataclass(frozen=True)
class StubMarker:
    stub_id: str
    description: str
    target: str
    expected_replacement: str

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.stub_id:
            issues.append("StubMarker.stub_id is required")
        if not self.description:
            issues.append("StubMarker.description is required")
        if not self.target:
            issues.append("StubMarker.target is required")
        if not self.expected_replacement:
            issues.append("StubMarker.expected_replacement is required")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class DoctorFinding:
    finding_id: str
    layer: DoctorLayer
    severity: DoctorSeverity
    status: ImplementationStatus
    title: str
    description: str
    target: str
    confidence: float
    evidence: list[str] = field(default_factory=list)
    limitations: list[Limitation] = field(default_factory=list)
    risks: list[RiskFlag] = field(default_factory=list)
    debts: list[DebtEntry] = field(default_factory=list)
    stubs: list[StubMarker] = field(default_factory=list)
    repair_candidates: list[RepairCandidate] = field(default_factory=list)
    quarantine_candidates: list[QuarantineCandidate] = field(default_factory=list)
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_write_allowed: bool = False
    runtime_authority: bool = False

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.finding_id:
            issues.append("DoctorFinding.finding_id is required")
        if not self.title:
            issues.append("DoctorFinding.title is required")
        if not self.description:
            issues.append("DoctorFinding.description is required")
        if not self.target:
            issues.append("DoctorFinding.target is required")
        if not 0.0 <= float(self.confidence) <= 1.0:
            issues.append("DoctorFinding.confidence must be in [0,1]")
        if self.canon_allowed:
            issues.append("DoctorFinding must not allow canon")
        if self.source_promotion_allowed:
            issues.append("DoctorFinding must not promote SOURCE")
        if self.noema_write_allowed:
            issues.append("DoctorFinding must not write external NOEMA")
        if self.runtime_authority:
            issues.append("DoctorFinding must not become runtime authority")

        for item in self.limitations:
            issues.extend(item.validate())
        for item in self.risks:
            issues.extend(item.validate())
        for item in self.debts:
            issues.extend(item.validate())
        for item in self.stubs:
            issues.extend(item.validate())
        for item in self.repair_candidates:
            issues.extend(item.validate())
        for item in self.quarantine_candidates:
            issues.extend(item.validate())

        if self.status == ImplementationStatus.STUB and not self.stubs:
            issues.append("status=STUB requires at least one StubMarker")
        if self.status == ImplementationStatus.LIMITATION and not self.limitations:
            issues.append("status=LIMITATION requires at least one Limitation")
        if self.status == ImplementationStatus.RISK and not self.risks:
            issues.append("status=RISK requires at least one RiskFlag")
        if self.status == ImplementationStatus.DEBT and not self.debts:
            issues.append("status=DEBT requires at least one DebtEntry")
        if self.status == ImplementationStatus.QUARANTINED and not self.quarantine_candidates:
            issues.append("status=QUARANTINED requires at least one QuarantineCandidate")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "finding_id": self.finding_id,
            "layer": self.layer.value,
            "severity": self.severity.value,
            "status": self.status.value,
            "title": self.title,
            "description": self.description,
            "target": self.target,
            "confidence": clamp01(self.confidence),
            "evidence": list(self.evidence),
            "limitations": [x.to_dict() for x in self.limitations],
            "risks": [x.to_dict() for x in self.risks],
            "debts": [x.to_dict() for x in self.debts],
            "stubs": [x.to_dict() for x in self.stubs],
            "repair_candidates": [x.to_dict() for x in self.repair_candidates],
            "quarantine_candidates": [x.to_dict() for x in self.quarantine_candidates],
            "canon_allowed": self.canon_allowed,
            "source_promotion_allowed": self.source_promotion_allowed,
            "noema_write_allowed": self.noema_write_allowed,
            "runtime_authority": self.runtime_authority,
        }


@dataclass(frozen=True)
class DoctorReport:
    report_id: str
    doctor_id: str
    target: str
    findings: list[DoctorFinding]
    summary: str
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_write_allowed: bool = False
    runtime_authority: bool = False

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.report_id:
            issues.append("DoctorReport.report_id is required")
        if not self.doctor_id:
            issues.append("DoctorReport.doctor_id is required")
        if not self.target:
            issues.append("DoctorReport.target is required")
        if not self.summary:
            issues.append("DoctorReport.summary is required")
        if self.canon_allowed:
            issues.append("DoctorReport must not allow canon")
        if self.source_promotion_allowed:
            issues.append("DoctorReport must not promote SOURCE")
        if self.noema_write_allowed:
            issues.append("DoctorReport must not write external NOEMA")
        if self.runtime_authority:
            issues.append("DoctorReport must not become runtime authority")
        for finding in self.findings:
            issues.extend(finding.validate())
        return issues

    @property
    def has_blockers(self) -> bool:
        return any(f.severity == DoctorSeverity.BLOCKER for f in self.findings)

    @property
    def debts(self) -> list[DebtEntry]:
        out: list[DebtEntry] = []
        for finding in self.findings:
            out.extend(finding.debts)
        return out

    @property
    def stubs(self) -> list[StubMarker]:
        out: list[StubMarker] = []
        for finding in self.findings:
            out.extend(finding.stubs)
        return out

    @property
    def limitations(self) -> list[Limitation]:
        out: list[Limitation] = []
        for finding in self.findings:
            out.extend(finding.limitations)
        return out

    @property
    def risks(self) -> list[RiskFlag]:
        out: list[RiskFlag] = []
        for finding in self.findings:
            out.extend(finding.risks)
        return out

    def no_hidden_debt_check(self) -> list[str]:
        issues: list[str] = []
        for debt in self.debts:
            issues.extend(debt.validate())
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "doctor_id": self.doctor_id,
            "target": self.target,
            "summary": self.summary,
            "findings": [f.to_dict() for f in self.findings],
            "has_blockers": self.has_blockers,
            "stubs": [s.to_dict() for s in self.stubs],
            "limitations": [l.to_dict() for l in self.limitations],
            "risks": [r.to_dict() for r in self.risks],
            "debts": [d.to_dict() for d in self.debts],
            "canon_allowed": self.canon_allowed,
            "source_promotion_allowed": self.source_promotion_allowed,
            "noema_write_allowed": self.noema_write_allowed,
            "runtime_authority": self.runtime_authority,
        }


def empty_pass_report(report_id: str, doctor_id: str, target: str, summary: str) -> DoctorReport:
    """Construct an explicit empty pass report.

    This is useful when a doctor checked a target and found no stubs, limitations,
    risks, or debts. It must still be explicit.
    """
    return DoctorReport(
        report_id=report_id,
        doctor_id=doctor_id,
        target=target,
        findings=[],
        summary=summary,
        canon_allowed=False,
        source_promotion_allowed=False,
        noema_write_allowed=False,
        runtime_authority=False,
    )
