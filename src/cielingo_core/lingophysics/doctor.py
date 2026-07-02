"""Lingophysics Doctor for CIELingo.

This module diagnoses lingophysics objects. It does not parse Polish grammar,
does not promote SOURCE/canon, does not write NOEMA, and does not become runtime
authority.

Primary target:
    language / lingophysics / semantic-neural diagnostics.

No-hidden-debt rule:
    stubs, limitations, risks and debt must be explicit DoctorFinding objects.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import ast
from typing import Any

from cielingo_core.doctor.contracts import (
    DebtEntry,
    DoctorFinding,
    DoctorLayer,
    DoctorReport,
    DoctorSeverity,
    ImplementationStatus,
    Limitation,
    QuarantineCandidate,
    RepairActionKind,
    RepairCandidate,
    RiskFlag,
    StubMarker,
    empty_pass_report,
)


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _finding(
    finding_id: str,
    title: str,
    description: str,
    target: str,
    severity: DoctorSeverity = DoctorSeverity.WARNING,
    status: ImplementationStatus = ImplementationStatus.RISK,
    confidence: float = 0.8,
    evidence: list[str] | None = None,
    limitations: list[Limitation] | None = None,
    risks: list[RiskFlag] | None = None,
    debts: list[DebtEntry] | None = None,
    stubs: list[StubMarker] | None = None,
    repairs: list[RepairCandidate] | None = None,
    quarantines: list[QuarantineCandidate] | None = None,
) -> DoctorFinding:
    return DoctorFinding(
        finding_id=finding_id,
        layer=DoctorLayer.LINGOPHYSICS,
        severity=severity,
        status=status,
        title=title,
        description=description,
        target=target,
        confidence=confidence,
        evidence=evidence or [],
        limitations=limitations or [],
        risks=risks or [],
        debts=debts or [],
        stubs=stubs or [],
        repair_candidates=repairs or [],
        quarantine_candidates=quarantines or [],
        canon_allowed=False,
        source_promotion_allowed=False,
        noema_write_allowed=False,
        runtime_authority=False,
    )


class SurfaceSolutionDoctor:
    """Diagnose SurfaceSolution ABI and scalar local_j boundaries."""

    doctor_id = "surface_solution_doctor"

    def diagnose(self, surface_solution: Any, target: str = "SurfaceSolution") -> DoctorReport:
        findings: list[DoctorFinding] = []

        required_attrs = ["equation_id", "tokens", "slot_projection", "local_j"]
        for attr in required_attrs:
            if not hasattr(surface_solution, attr):
                findings.append(_finding(
                    finding_id=f"missing_attr_{attr}",
                    title=f"Missing SurfaceSolution attribute: {attr}",
                    description=f"SurfaceSolution-compatible object must expose {attr}.",
                    target=target,
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.95,
                    risks=[RiskFlag(
                        risk_id=f"risk_missing_attr_{attr}",
                        description=f"Missing {attr} breaks SurfaceSolution ABI.",
                        affected_layer=DoctorLayer.LINGOPHYSICS,
                        mitigation="Restore ABI or wrap object before passing to lingophysics.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                    repairs=[RepairCandidate(
                        action_kind=RepairActionKind.REFACTOR,
                        description=f"Add or adapt {attr} explicitly; do not hide it in notes.",
                        target_path=target,
                        required_before_merge=True,
                    )],
                ))

        local_j = getattr(surface_solution, "local_j", {})
        if not isinstance(local_j, dict):
            findings.append(_finding(
                finding_id="local_j_not_dict",
                title="local_j is not a dict",
                description="SurfaceSolution.local_j must be a dictionary of scalar signals.",
                target=target,
                severity=DoctorSeverity.BLOCKER,
                status=ImplementationStatus.RISK,
                confidence=0.95,
                risks=[RiskFlag(
                    risk_id="risk_local_j_not_dict",
                    description="Non-dict local_j breaks J signal inspection.",
                    affected_layer=DoctorLayer.LINGOPHYSICS,
                    mitigation="Convert local_j to dict[str, float].",
                    severity=DoctorSeverity.BLOCKER,
                )],
            ))
        else:
            for key, value in local_j.items():
                if not _is_number(value) or not 0.0 <= float(value) <= 1.0:
                    findings.append(_finding(
                        finding_id=f"local_j_out_of_bounds_{key}",
                        title=f"local_j value invalid: {key}",
                        description="Every local_j value must be numeric and inside [0,1].",
                        target=f"{target}.local_j.{key}",
                        severity=DoctorSeverity.BLOCKER,
                        status=ImplementationStatus.RISK,
                        confidence=0.99,
                        evidence=[f"{key}={value!r}"],
                        risks=[RiskFlag(
                            risk_id=f"risk_invalid_local_j_{key}",
                            description="Invalid local_j can corrupt J/Kuramoto coherence and ABI.",
                            affected_layer=DoctorLayer.LINGOPHYSICS,
                            mitigation="Move non-scalar reports to RegionalSolveResult.notes and normalize scalar signals.",
                            severity=DoctorSeverity.BLOCKER,
                        )],
                        repairs=[RepairCandidate(
                            action_kind=RepairActionKind.REFACTOR,
                            description="Keep local_j scalar; move reports/constants to notes.",
                            target_path=target,
                            required_before_merge=True,
                        )],
                    ))

        # Detect known forbidden ad-hoc attributes when present on objects.
        for forbidden in ["regional_residue", "j_kuramoto_report"]:
            if hasattr(surface_solution, forbidden):
                findings.append(_finding(
                    finding_id=f"forbidden_surface_attr_{forbidden}",
                    title=f"Forbidden SurfaceSolution extension: {forbidden}",
                    description="Regional metadata must not be added ad hoc to SurfaceSolution.",
                    target=f"{target}.{forbidden}",
                    severity=DoctorSeverity.ERROR,
                    status=ImplementationStatus.DEBT,
                    confidence=0.9,
                    debts=[DebtEntry(
                        debt_id=f"debt_forbidden_surface_attr_{forbidden}",
                        description=f"{forbidden} must be moved out of SurfaceSolution.",
                        target=f"{target}.{forbidden}",
                        repayment_condition="Move to RegionalSolveResult.notes or a documented metadata channel.",
                        hidden=False,
                    )],
                    repairs=[RepairCandidate(
                        action_kind=RepairActionKind.REFACTOR,
                        description=f"Move {forbidden} into RegionalSolveResult.notes.",
                        target_path=target,
                        required_before_merge=True,
                    )],
                ))

        report = DoctorReport(
            report_id="surface_solution_doctor_report",
            doctor_id=self.doctor_id,
            target=target,
            findings=findings,
            summary="SurfaceSolution ABI and local_j diagnostic report.",
        )
        return report


class SentenceEquationDoctor:
    """Diagnose SentenceEquation authority boundaries and validation issues."""

    doctor_id = "sentence_equation_doctor"

    def diagnose(self, sentence_equation: Any, target: str = "SentenceEquation") -> DoctorReport:
        findings: list[DoctorFinding] = []

        if hasattr(sentence_equation, "validate"):
            validation_issues = list(sentence_equation.validate())
            for idx, issue in enumerate(validation_issues):
                findings.append(_finding(
                    finding_id=f"sentence_equation_validation_{idx}",
                    title="SentenceEquation validation issue",
                    description=str(issue),
                    target=target,
                    severity=DoctorSeverity.ERROR,
                    status=ImplementationStatus.RISK,
                    confidence=0.95,
                    evidence=[str(issue)],
                    risks=[RiskFlag(
                        risk_id=f"risk_sentence_validation_{idx}",
                        description="SentenceEquation failed its own validation.",
                        affected_layer=DoctorLayer.LINGOPHYSICS,
                        mitigation="Fix underlying equation object before merge.",
                        severity=DoctorSeverity.ERROR,
                    )],
                ))
        else:
            findings.append(_finding(
                finding_id="sentence_equation_missing_validate",
                title="SentenceEquation missing validate()",
                description="SentenceEquation-like object should expose validate().",
                target=target,
                severity=DoctorSeverity.WARNING,
                status=ImplementationStatus.LIMITATION,
                confidence=0.7,
                limitations=[Limitation(
                    limitation_id="lim_no_sentence_validate",
                    description="Cannot run native SentenceEquation validation.",
                    affected_scope=target,
                    consequence="Doctor can only inspect authority flags heuristically.",
                )],
            ))

        for flag in ["canon_allowed", "source_promotion_allowed", "noema_writeback_allowed", "current_update_allowed"]:
            if getattr(sentence_equation, flag, False) is True:
                findings.append(_finding(
                    finding_id=f"forbidden_authority_{flag}",
                    title=f"Forbidden SentenceEquation authority flag: {flag}",
                    description="SentenceEquation must not grant canon/SOURCE/NOEMA/CURRENT authority.",
                    target=f"{target}.{flag}",
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.99,
                    risks=[RiskFlag(
                        risk_id=f"risk_forbidden_authority_{flag}",
                        description=f"{flag}=True violates epistemic boundary.",
                        affected_layer=DoctorLayer.LINGOPHYSICS,
                        mitigation="Force flag false and move authority decision to external gate.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                    repairs=[RepairCandidate(
                        action_kind=RepairActionKind.BLOCK_PROMOTION,
                        description=f"Block {flag} on SentenceEquation.",
                        target_path=target,
                        required_before_merge=True,
                    )],
                ))

        return DoctorReport(
            report_id="sentence_equation_doctor_report",
            doctor_id=self.doctor_id,
            target=target,
            findings=findings,
            summary="SentenceEquation validation and authority-boundary diagnostic report.",
        )


class LocalJDoctor:
    """Focused local_j diagnostic."""

    doctor_id = "local_j_doctor"

    def diagnose(self, local_j: dict[str, Any], target: str = "local_j") -> DoctorReport:
        findings: list[DoctorFinding] = []
        if not isinstance(local_j, dict):
            findings.append(_finding(
                finding_id="local_j_input_not_dict",
                title="local_j input is not dict",
                description="LocalJDoctor expects dict[str, number].",
                target=target,
                severity=DoctorSeverity.BLOCKER,
                status=ImplementationStatus.RISK,
                confidence=0.95,
                risks=[RiskFlag(
                    risk_id="risk_local_j_input_not_dict",
                    description="Cannot inspect J signals.",
                    affected_layer=DoctorLayer.LINGOPHYSICS,
                    mitigation="Pass a dict[str, float].",
                    severity=DoctorSeverity.BLOCKER,
                )],
            ))
        else:
            for key, value in local_j.items():
                if not _is_number(value) or not 0.0 <= float(value) <= 1.0:
                    findings.append(_finding(
                        finding_id=f"local_j_invalid_{key}",
                        title=f"Invalid local_j scalar: {key}",
                        description="local_j values must be numeric and in [0,1].",
                        target=f"{target}.{key}",
                        severity=DoctorSeverity.BLOCKER,
                        status=ImplementationStatus.RISK,
                        confidence=0.99,
                        evidence=[f"{key}={value!r}"],
                        risks=[RiskFlag(
                            risk_id=f"risk_local_j_invalid_{key}",
                            description="Invalid scalar can break coherence guards.",
                            affected_layer=DoctorLayer.LINGOPHYSICS,
                            mitigation="Normalize to [0,1] or move non-scalar data to notes.",
                            severity=DoctorSeverity.BLOCKER,
                        )],
                    ))

        return DoctorReport(
            report_id="local_j_doctor_report",
            doctor_id=self.doctor_id,
            target=target,
            findings=findings,
            summary="local_j boundedness diagnostic report.",
        )


class RegionalSeparationDoctor:
    """Diagnose cross-language import leakage in language_spaces."""

    doctor_id = "regional_separation_doctor"

    def diagnose_repo(self, repo_root: str | Path) -> DoctorReport:
        repo = Path(repo_root)
        findings: list[DoctorFinding] = []
        base = repo / "src" / "cielingo_core" / "language_spaces"
        if not base.exists():
            findings.append(_finding(
                finding_id="language_spaces_missing",
                title="language_spaces directory missing",
                description="Regional separation requires src/cielingo_core/language_spaces.",
                target=str(base),
                severity=DoctorSeverity.BLOCKER,
                status=ImplementationStatus.RISK,
                confidence=0.95,
                risks=[RiskFlag(
                    risk_id="risk_language_spaces_missing",
                    description="Cannot enforce PL/EN/JA separation.",
                    affected_layer=DoctorLayer.LANGUAGE_SPACE,
                    mitigation="Restore language_spaces hierarchy.",
                    severity=DoctorSeverity.BLOCKER,
                )],
            ))
            return DoctorReport(
                report_id="regional_separation_doctor_report",
                doctor_id=self.doctor_id,
                target=str(base),
                findings=findings,
                summary="Regional separation diagnostic report.",
            )

        for lang in ["pl", "en", "ja"]:
            lang_dir = base / lang
            if not lang_dir.exists():
                findings.append(_finding(
                    finding_id=f"language_space_missing_{lang}",
                    title=f"Missing language space: {lang}",
                    description="Each language must have its own regional space.",
                    target=str(lang_dir),
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.95,
                    risks=[RiskFlag(
                        risk_id=f"risk_language_space_missing_{lang}",
                        description=f"Missing {lang} breaks regional language separation.",
                        affected_layer=DoctorLayer.LANGUAGE_SPACE,
                        mitigation=f"Restore language_spaces/{lang}.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                ))
                continue

            forbidden = [f"cielingo_core.language_spaces.{other}" for other in ["pl", "en", "ja"] if other != lang]
            for path in sorted(lang_dir.rglob("*.py")):
                try:
                    tree = ast.parse(path.read_text(encoding="utf-8"))
                except SyntaxError as exc:
                    findings.append(_finding(
                        finding_id=f"syntax_error_{lang}_{path.name}",
                        title="Syntax error in language space",
                        description=str(exc),
                        target=str(path),
                        severity=DoctorSeverity.BLOCKER,
                        status=ImplementationStatus.RISK,
                        confidence=0.95,
                        risks=[RiskFlag(
                            risk_id=f"risk_syntax_error_{lang}_{path.name}",
                            description="Cannot audit imports due to syntax error.",
                            affected_layer=DoctorLayer.LANGUAGE_SPACE,
                            mitigation="Fix syntax before merge.",
                            severity=DoctorSeverity.BLOCKER,
                        )],
                    ))
                    continue

                imports: list[str] = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.ImportFrom) and node.module:
                        imports.append(node.module)
                    elif isinstance(node, ast.Import):
                        imports.extend(alias.name for alias in node.names)

                for imp in imports:
                    for bad in forbidden:
                        if imp.startswith(bad):
                            findings.append(_finding(
                                finding_id=f"cross_language_import_{lang}_{path.stem}",
                                title="Cross-language import detected",
                                description=f"{lang} imports forbidden module {imp}.",
                                target=str(path),
                                severity=DoctorSeverity.BLOCKER,
                                status=ImplementationStatus.RISK,
                                confidence=0.99,
                                evidence=[f"import={imp}", f"forbidden={bad}"],
                                risks=[RiskFlag(
                                    risk_id=f"risk_cross_language_import_{lang}_{path.stem}",
                                    description="Cross-language imports can mix regional holonomies.",
                                    affected_layer=DoctorLayer.LANGUAGE_SPACE,
                                    mitigation="Move shared code to common contracts or keep paths separated.",
                                    severity=DoctorSeverity.BLOCKER,
                                )],
                            ))

        return DoctorReport(
            report_id="regional_separation_doctor_report",
            doctor_id=self.doctor_id,
            target=str(base),
            findings=findings,
            summary="Regional language-space separation diagnostic report.",
        )


class MeaningDebtDoctor:
    """Diagnose explicitness of debt/stub/risk/limitation language in plans."""

    doctor_id = "meaning_debt_doctor"

    def diagnose_text(self, text: str, target: str = "text") -> DoctorReport:
        findings: list[DoctorFinding] = []
        lowered = text.lower()
        risky_words = ["todo", "later", "temporary", "hack", "placeholder"]
        for word in risky_words:
            if word in lowered and not any(marker in lowered for marker in ["debt", "stub", "limitation", "risk"]):
                findings.append(_finding(
                    finding_id=f"unclassified_debt_word_{word}",
                    title=f"Unclassified possible debt marker: {word}",
                    description="Potential debt/stub language appears without explicit classification.",
                    target=target,
                    severity=DoctorSeverity.WARNING,
                    status=ImplementationStatus.DEBT,
                    confidence=0.65,
                    evidence=[word],
                    debts=[DebtEntry(
                        debt_id=f"debt_unclassified_{word}",
                        description=f"Text contains '{word}' without explicit stub/limitation/risk/debt classification.",
                        target=target,
                        repayment_condition="Classify as STUB/LIMITATION/RISK/DEBT or remove.",
                        hidden=False,
                    )],
                ))

        return DoctorReport(
            report_id="meaning_debt_doctor_report",
            doctor_id=self.doctor_id,
            target=target,
            findings=findings,
            summary="Meaning-debt explicitness diagnostic report.",
        )


class JCoherenceDoctor:
    """Diagnose J/Kuramoto metadata boundary.

    This is deliberately conservative: it checks that scalar J-like values stay in
    local_j, while non-scalar reports/constants are treated as metadata/notes.
    """

    doctor_id = "j_coherence_doctor"

    def diagnose(self, local_j: dict[str, Any], notes: list[Any] | None = None, target: str = "J/coherence") -> DoctorReport:
        findings: list[DoctorFinding] = []
        findings.extend(LocalJDoctor().diagnose(local_j, target=f"{target}.local_j").findings)

        notes_text = " ".join(str(x) for x in (notes or []))
        if ("omega0" in notes_text or "frequency_hz" in notes_text or "kuramoto" in notes_text.lower()) and not notes:
            findings.append(_finding(
                finding_id="kuramoto_metadata_missing",
                title="Kuramoto metadata not available",
                description="Kuramoto/full phase data should be in notes/metadata, not local_j.",
                target=target,
                severity=DoctorSeverity.WARNING,
                status=ImplementationStatus.LIMITATION,
                confidence=0.6,
                limitations=[Limitation(
                    limitation_id="lim_kuramoto_metadata",
                    description="Cannot verify full Kuramoto report without notes.",
                    affected_scope=target,
                    consequence="Only scalar local_j can be inspected.",
                )],
            ))

        if isinstance(local_j, dict):
            for key in local_j:
                if any(token in key.lower() for token in ["omega", "frequency_hz", "kuramoto_report"]):
                    findings.append(_finding(
                        finding_id=f"j_metadata_in_local_j_{key}",
                        title="Metadata-like key in local_j",
                        description="Kuramoto constants/reports should not live in local_j.",
                        target=f"{target}.local_j.{key}",
                        severity=DoctorSeverity.ERROR,
                        status=ImplementationStatus.RISK,
                        confidence=0.8,
                        risks=[RiskFlag(
                            risk_id=f"risk_j_metadata_in_local_j_{key}",
                            description="Metadata in local_j can violate scalar J contract.",
                            affected_layer=DoctorLayer.LINGOPHYSICS,
                            mitigation="Move metadata to RegionalSolveResult.notes.",
                            severity=DoctorSeverity.ERROR,
                        )],
                    ))

        return DoctorReport(
            report_id="j_coherence_doctor_report",
            doctor_id=self.doctor_id,
            target=target,
            findings=findings,
            summary="J/Kuramoto scalar/metadata boundary diagnostic report.",
        )




class SemanticNeuralStateDoctor:
    """Diagnose semantic-neural sentence-state scaffold objects.

    This doctor protects the scaffold boundary:
    - CardOscillatorState is not a biological neuron.
    - JVectorState is not a physical measurement.
    - SentenceStateSnapshot is not runtime cognition.
    - stable_hash is local commitment only, not external NOEMA/Merkle proof.
    """

    doctor_id = "semantic_neural_state_doctor"

    def diagnose_snapshot(self, snapshot: Any, target: str = "SentenceStateSnapshot") -> DoctorReport:
        findings: list[DoctorFinding] = []

        if hasattr(snapshot, "validate"):
            for idx, issue in enumerate(snapshot.validate()):
                findings.append(_finding(
                    finding_id=f"semantic_snapshot_validation_{idx}",
                    title="SentenceStateSnapshot validation issue",
                    description=str(issue),
                    target=target,
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.98,
                    risks=[RiskFlag(
                        risk_id=f"risk_semantic_snapshot_validation_{idx}",
                        description="Invalid semantic-neural snapshot can corrupt downstream state reasoning.",
                        affected_layer=DoctorLayer.LINGOPHYSICS,
                        mitigation="Fix snapshot bounds/authority flags before alignment or memory use.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                    repairs=[RepairCandidate(
                        action_kind=RepairActionKind.REFACTOR,
                        description="Repair SentenceStateSnapshot so validate() returns no issues.",
                        target_path=target,
                        required_before_merge=True,
                    )],
                ))
        else:
            findings.append(_finding(
                finding_id="semantic_snapshot_missing_validate",
                title="SentenceStateSnapshot missing validate()",
                description="Semantic-neural state object must expose validate().",
                target=target,
                severity=DoctorSeverity.BLOCKER,
                status=ImplementationStatus.RISK,
                confidence=0.9,
                risks=[RiskFlag(
                    risk_id="risk_semantic_snapshot_missing_validate",
                    description="Doctor cannot verify bounds or authority flags without validate().",
                    affected_layer=DoctorLayer.LINGOPHYSICS,
                    mitigation="Use SentenceStateSnapshot contract or adapter.",
                    severity=DoctorSeverity.BLOCKER,
                )],
            ))

        # Explicit authority leakage checks. These are checked even if validate() exists.
        for flag in ["source_promotion_allowed", "canon_allowed", "noema_writeback_allowed", "current_update_allowed"]:
            if getattr(snapshot, flag, False) is True:
                findings.append(_finding(
                    finding_id=f"semantic_snapshot_authority_leak_{flag}",
                    title=f"Semantic-neural snapshot authority leak: {flag}",
                    description="SentenceStateSnapshot must not promote SOURCE/canon, write NOEMA, or update CURRENT.",
                    target=f"{target}.{flag}",
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.99,
                    risks=[RiskFlag(
                        risk_id=f"risk_semantic_snapshot_authority_leak_{flag}",
                        description=f"{flag}=True violates semantic-neural scaffold boundary.",
                        affected_layer=DoctorLayer.LINGOPHYSICS,
                        mitigation="Force authority flag false; route authority to explicit external gate.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                    repairs=[RepairCandidate(
                        action_kind=RepairActionKind.BLOCK_PROMOTION,
                        description=f"Block {flag} on SentenceStateSnapshot.",
                        target_path=target,
                        required_before_merge=True,
                    )],
                ))

        limitation = getattr(snapshot, "limitation", "")
        if "not_runtime_cognition" not in str(limitation):
            findings.append(_finding(
                finding_id="semantic_snapshot_missing_runtime_limitation",
                title="SentenceStateSnapshot missing runtime-cognition limitation",
                description="Snapshot must explicitly state that it is not runtime cognition.",
                target=f"{target}.limitation",
                severity=DoctorSeverity.WARNING,
                status=ImplementationStatus.LIMITATION,
                confidence=0.8,
                limitations=[Limitation(
                    limitation_id="lim_semantic_snapshot_not_runtime",
                    description="Runtime-cognition boundary is not explicit on snapshot.",
                    affected_scope=target,
                    consequence="Downstream modules could overclaim scaffold status.",
                )],
                repairs=[RepairCandidate(
                    action_kind=RepairActionKind.MARK_LIMITATION,
                    description="Add semantic_neural_sentence_state_scaffold_not_runtime_cognition limitation.",
                    target_path=target,
                    required_before_merge=False,
                )],
            ))

        # Node checks: hidden neuron overclaim and scalar bounds.
        nodes = list(getattr(snapshot, "nodes", []) or [])
        for idx, node in enumerate(nodes):
            if hasattr(node, "validate"):
                for issue_idx, issue in enumerate(node.validate()):
                    findings.append(_finding(
                        finding_id=f"semantic_node_validation_{idx}_{issue_idx}",
                        title="CardOscillatorState validation issue",
                        description=str(issue),
                        target=f"{target}.nodes[{idx}]",
                        severity=DoctorSeverity.BLOCKER,
                        status=ImplementationStatus.RISK,
                        confidence=0.98,
                        risks=[RiskFlag(
                            risk_id=f"risk_semantic_node_validation_{idx}_{issue_idx}",
                            description="Invalid card oscillator state can corrupt semantic-neural snapshot.",
                            affected_layer=DoctorLayer.LINGOPHYSICS,
                            mitigation="Bound activation/phase/semantic_mass/residue in [0,1].",
                            severity=DoctorSeverity.BLOCKER,
                        )],
                    ))
            node_limitation = getattr(node, "limitation", "")
            if "not_biological_neuron" not in str(node_limitation):
                findings.append(_finding(
                    finding_id=f"semantic_node_missing_neuron_limitation_{idx}",
                    title="CardOscillatorState missing non-neuron limitation",
                    description="Card oscillator must not claim biological-neuron identity.",
                    target=f"{target}.nodes[{idx}].limitation",
                    severity=DoctorSeverity.WARNING,
                    status=ImplementationStatus.LIMITATION,
                    confidence=0.8,
                    limitations=[Limitation(
                        limitation_id=f"lim_card_not_neuron_{idx}",
                        description="Card oscillator limitation missing.",
                        affected_scope=f"{target}.nodes[{idx}]",
                        consequence="Node could be overinterpreted as biological neuron.",
                    )],
                ))

        j_vector = getattr(snapshot, "j_vector", None)
        if j_vector is None:
            findings.append(_finding(
                finding_id="semantic_snapshot_missing_j_vector",
                title="SentenceStateSnapshot missing JVectorState",
                description="Snapshot requires explicit JVectorState.",
                target=f"{target}.j_vector",
                severity=DoctorSeverity.BLOCKER,
                status=ImplementationStatus.RISK,
                confidence=0.95,
                risks=[RiskFlag(
                    risk_id="risk_semantic_snapshot_missing_j_vector",
                    description="Missing JVectorState prevents phase/J diagnostics.",
                    affected_layer=DoctorLayer.LINGOPHYSICS,
                    mitigation="Provide JVectorState with bounded scalar values.",
                    severity=DoctorSeverity.BLOCKER,
                )],
            ))
        else:
            if hasattr(j_vector, "validate"):
                for idx, issue in enumerate(j_vector.validate()):
                    findings.append(_finding(
                        finding_id=f"semantic_j_vector_validation_{idx}",
                        title="JVectorState validation issue",
                        description=str(issue),
                        target=f"{target}.j_vector",
                        severity=DoctorSeverity.BLOCKER,
                        status=ImplementationStatus.RISK,
                        confidence=0.98,
                        risks=[RiskFlag(
                            risk_id=f"risk_semantic_j_vector_validation_{idx}",
                            description="Invalid JVectorState can corrupt phase/J reasoning.",
                            affected_layer=DoctorLayer.LINGOPHYSICS,
                            mitigation="Keep every J scalar numeric and in [0,1].",
                            severity=DoctorSeverity.BLOCKER,
                        )],
                    ))
            limitation = getattr(j_vector, "limitation", "")
            if "not_physical_measurement" not in str(limitation):
                findings.append(_finding(
                    finding_id="semantic_j_vector_missing_measurement_limitation",
                    title="JVectorState missing non-physical-measurement limitation",
                    description="JVectorState must not claim physical measurement.",
                    target=f"{target}.j_vector.limitation",
                    severity=DoctorSeverity.WARNING,
                    status=ImplementationStatus.LIMITATION,
                    confidence=0.8,
                    limitations=[Limitation(
                        limitation_id="lim_j_vector_not_physical_measurement",
                        description="JVectorState physical-measurement boundary missing.",
                        affected_scope=f"{target}.j_vector",
                        consequence="J vector could be overclaimed as physical measurement.",
                    )],
                ))

        return DoctorReport(
            report_id="semantic_neural_state_doctor_report",
            doctor_id=self.doctor_id,
            target=target,
            findings=findings,
            summary="Semantic-neural sentence-state scaffold diagnostic report.",
        )



class CrossLanguageAlignmentDoctor:
    """Diagnose cross-language alignment reports.

    This doctor protects the boundary:
    - alignment_candidate is not semantic identity;
    - slot_id is a comparison axis, not equivalence proof;
    - cross-language report is not translation proof;
    - JA alignment requires native/regional review residue.
    """

    doctor_id = "cross_language_alignment_doctor"

    def diagnose_candidate(self, candidate: Any, target: str = "LanguageAlignmentCandidate") -> DoctorReport:
        findings: list[DoctorFinding] = []

        if hasattr(candidate, "validate"):
            for idx, issue in enumerate(candidate.validate()):
                findings.append(_finding(
                    finding_id=f"alignment_candidate_validation_{idx}",
                    title="Alignment candidate validation issue",
                    description=str(issue),
                    target=target,
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.98,
                    risks=[RiskFlag(
                        risk_id=f"risk_alignment_candidate_validation_{idx}",
                        description="Invalid alignment candidate can falsely imply cross-language equivalence.",
                        affected_layer=DoctorLayer.LINGOPHYSICS,
                        mitigation="Repair candidate bounds/authority flags before use.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                    repairs=[RepairCandidate(
                        action_kind=RepairActionKind.REFACTOR,
                        description="Repair LanguageAlignmentCandidate so validate() returns no issues.",
                        target_path=target,
                        required_before_merge=True,
                    )],
                ))
        else:
            findings.append(_finding(
                finding_id="alignment_candidate_missing_validate",
                title="Alignment candidate missing validate()",
                description="Alignment candidate must expose validate().",
                target=target,
                severity=DoctorSeverity.BLOCKER,
                status=ImplementationStatus.RISK,
                confidence=0.95,
                risks=[RiskFlag(
                    risk_id="risk_alignment_candidate_missing_validate",
                    description="Cannot verify alignment candidate boundaries.",
                    affected_layer=DoctorLayer.LINGOPHYSICS,
                    mitigation="Use LanguageAlignmentCandidate contract or adapter.",
                    severity=DoctorSeverity.BLOCKER,
                )],
            ))

        for flag in ["semantic_identity_claimed", "canon_allowed", "source_promotion_allowed", "noema_writeback_allowed", "current_update_allowed"]:
            if getattr(candidate, flag, False) is True:
                findings.append(_finding(
                    finding_id=f"alignment_authority_leak_{flag}",
                    title=f"Alignment authority/identity leak: {flag}",
                    description="Alignment candidate must not claim identity, SOURCE/canon authority, NOEMA writeback, or CURRENT update.",
                    target=f"{target}.{flag}",
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.99,
                    risks=[RiskFlag(
                        risk_id=f"risk_alignment_authority_leak_{flag}",
                        description=f"{flag}=True violates cross-language alignment boundary.",
                        affected_layer=DoctorLayer.LINGOPHYSICS,
                        mitigation="Force flag false and keep result as alignment_candidate.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                    repairs=[RepairCandidate(
                        action_kind=RepairActionKind.BLOCK_PROMOTION,
                        description=f"Block {flag} on alignment candidate.",
                        target_path=target,
                        required_before_merge=True,
                    )],
                ))

        limitation = getattr(candidate, "limitation", "")
        if "not_semantic_identity" not in str(limitation):
            findings.append(_finding(
                finding_id="alignment_missing_identity_limitation",
                title="Alignment candidate missing semantic-identity limitation",
                description="Alignment candidate must explicitly say it is not semantic identity.",
                target=f"{target}.limitation",
                severity=DoctorSeverity.WARNING,
                status=ImplementationStatus.LIMITATION,
                confidence=0.85,
                limitations=[Limitation(
                    limitation_id="lim_alignment_not_identity",
                    description="Semantic identity boundary is not explicit.",
                    affected_scope=target,
                    consequence="Downstream code could overclaim alignment.",
                )],
                repairs=[RepairCandidate(
                    action_kind=RepairActionKind.MARK_LIMITATION,
                    description="Add alignment_candidate_not_semantic_identity limitation.",
                    target_path=target,
                    required_before_merge=False,
                )],
            ))

        pair = tuple(getattr(candidate, "language_pair", ()) or ())
        if "ja" in pair:
            residues = list(getattr(candidate, "residue", []) or [])
            has_native_review = any(getattr(r, "residue_type", "") == "native_review_residue" for r in residues)
            if not has_native_review:
                findings.append(_finding(
                    finding_id="ja_alignment_missing_native_review_residue",
                    title="JA alignment missing native-review residue",
                    description="JA cross-language alignment must preserve native/regional review residue.",
                    target=f"{target}.residue",
                    severity=DoctorSeverity.ERROR,
                    status=ImplementationStatus.RISK,
                    confidence=0.9,
                    risks=[RiskFlag(
                        risk_id="risk_ja_alignment_without_native_review",
                        description="JA alignment without review residue can be over-promoted.",
                        affected_layer=DoctorLayer.LINGOPHYSICS,
                        mitigation="Add native_review_residue for JA pairs.",
                        severity=DoctorSeverity.ERROR,
                    )],
                ))

        return DoctorReport(
            report_id="cross_language_alignment_candidate_doctor_report",
            doctor_id=self.doctor_id,
            target=target,
            findings=findings,
            summary="Cross-language alignment candidate diagnostic report.",
        )

    def diagnose_report(self, report: Any, target: str = "CrossLanguageAlignmentReport") -> DoctorReport:
        findings: list[DoctorFinding] = []

        if hasattr(report, "validate"):
            for idx, issue in enumerate(report.validate()):
                findings.append(_finding(
                    finding_id=f"alignment_report_validation_{idx}",
                    title="Cross-language alignment report validation issue",
                    description=str(issue),
                    target=target,
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.98,
                    risks=[RiskFlag(
                        risk_id=f"risk_alignment_report_validation_{idx}",
                        description="Invalid alignment report can corrupt cross-language state.",
                        affected_layer=DoctorLayer.LINGOPHYSICS,
                        mitigation="Repair report before merge or export.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                ))
        else:
            findings.append(_finding(
                finding_id="alignment_report_missing_validate",
                title="Cross-language alignment report missing validate()",
                description="Alignment report must expose validate().",
                target=target,
                severity=DoctorSeverity.BLOCKER,
                status=ImplementationStatus.RISK,
                confidence=0.95,
                risks=[RiskFlag(
                    risk_id="risk_alignment_report_missing_validate",
                    description="Cannot verify report boundaries.",
                    affected_layer=DoctorLayer.LINGOPHYSICS,
                    mitigation="Use CrossLanguageAlignmentReport contract or adapter.",
                    severity=DoctorSeverity.BLOCKER,
                )],
            ))

        for flag in ["canon_allowed", "source_promotion_allowed", "noema_writeback_allowed", "current_update_allowed"]:
            if getattr(report, flag, False) is True:
                findings.append(_finding(
                    finding_id=f"alignment_report_authority_leak_{flag}",
                    title=f"Alignment report authority leak: {flag}",
                    description="Alignment report must not grant SOURCE/canon/NOEMA/CURRENT authority.",
                    target=f"{target}.{flag}",
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.99,
                    risks=[RiskFlag(
                        risk_id=f"risk_alignment_report_authority_leak_{flag}",
                        description=f"{flag}=True violates cross-language report boundary.",
                        affected_layer=DoctorLayer.LINGOPHYSICS,
                        mitigation="Force flag false; keep report diagnostic-only.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                ))

        limitation = getattr(report, "limitation", "")
        if "not_translation_proof" not in str(limitation):
            findings.append(_finding(
                finding_id="alignment_report_missing_translation_proof_limitation",
                title="Alignment report missing translation-proof limitation",
                description="Report must explicitly say it is not translation proof.",
                target=f"{target}.limitation",
                severity=DoctorSeverity.WARNING,
                status=ImplementationStatus.LIMITATION,
                confidence=0.85,
                limitations=[Limitation(
                    limitation_id="lim_alignment_report_not_translation_proof",
                    description="Translation-proof boundary missing.",
                    affected_scope=target,
                    consequence="Report could be overclaimed as translation proof.",
                )],
            ))

        for idx, candidate in enumerate(list(getattr(report, "candidates", []) or [])):
            candidate_report = self.diagnose_candidate(candidate, target=f"{target}.candidates[{idx}]")
            findings.extend(candidate_report.findings)

        return DoctorReport(
            report_id="cross_language_alignment_report_doctor_report",
            doctor_id=self.doctor_id,
            target=target,
            findings=findings,
            summary="Cross-language alignment report diagnostic report.",
        )



class ControlledAtlasDoctor:
    """Diagnose controlled atlas artifacts.

    This doctor protects atlas boundaries:
    - exact expected slot/card/alignment/taxonomy counts;
    - no SOURCE default;
    - no canon default;
    - no semantic identity claim across languages;
    - JA entries remain native-review candidates;
    - NOEMA markers cannot update CURRENT.
    """

    doctor_id = "controlled_atlas_doctor"

    def diagnose_validation_result(
        self,
        result: dict[str, Any],
        *,
        expected_slots: int,
        expected_cards: int,
        expected_alignments: int,
        expected_taxonomy: int,
        target: str = "controlled_atlas_validation",
    ) -> DoctorReport:
        findings: list[DoctorFinding] = []

        expected = {
            "slot_count": expected_slots,
            "card_count": expected_cards,
            "alignment_count": expected_alignments,
            "taxonomy_count": expected_taxonomy,
        }
        for key, value in expected.items():
            observed = result.get(key)
            if observed != value:
                findings.append(_finding(
                    finding_id=f"atlas_count_mismatch_{key}",
                    title=f"Atlas count mismatch: {key}",
                    description=f"Expected {key}={value}, observed {observed}.",
                    target=f"{target}.{key}",
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.99,
                    evidence=[f"expected={value}", f"observed={observed}"],
                    risks=[RiskFlag(
                        risk_id=f"risk_atlas_count_mismatch_{key}",
                        description="Atlas count mismatch can hide accidental over-generation or missing slots.",
                        affected_layer=DoctorLayer.GLOBAL_LAYER,
                        mitigation="Regenerate atlas to exact controlled count before merge.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                    repairs=[RepairCandidate(
                        action_kind=RepairActionKind.REFACTOR,
                        description=f"Repair atlas generation until {key}={value}.",
                        target_path=target,
                        required_before_merge=True,
                    )],
                ))

        issue_keys = [
            "missing_languages_by_slot",
            "invalid_cards",
            "taxonomy_issues",
            "alignment_issues",
            "ja_issues",
            "marker_issues",
            "source_or_canon_issues",
        ]
        for key in issue_keys:
            issues = result.get(key)
            if issues:
                findings.append(_finding(
                    finding_id=f"atlas_validation_issues_{key}",
                    title=f"Atlas validation issues: {key}",
                    description=f"Atlas validation reported non-empty {key}.",
                    target=f"{target}.{key}",
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.98,
                    evidence=[repr(issues)[:500]],
                    risks=[RiskFlag(
                        risk_id=f"risk_atlas_validation_issues_{key}",
                        description=f"Non-empty {key} violates atlas boundary.",
                        affected_layer=DoctorLayer.GLOBAL_LAYER,
                        mitigation="Fix cards/taxonomy/alignment/markers before merge.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                ))

        if result.get("ok") is not True:
            findings.append(_finding(
                finding_id="atlas_validation_not_ok",
                title="Atlas validation result not OK",
                description="Controlled atlas validation must return ok=true.",
                target=f"{target}.ok",
                severity=DoctorSeverity.BLOCKER,
                status=ImplementationStatus.RISK,
                confidence=0.99,
                risks=[RiskFlag(
                    risk_id="risk_atlas_validation_not_ok",
                    description="Atlas cannot be promoted if validation is not OK.",
                    affected_layer=DoctorLayer.GLOBAL_LAYER,
                    mitigation="Repair atlas and rerun validation.",
                    severity=DoctorSeverity.BLOCKER,
                )],
            ))

        return DoctorReport(
            report_id="controlled_atlas_validation_doctor_report",
            doctor_id=self.doctor_id,
            target=target,
            findings=findings,
            summary="Controlled atlas validation diagnostic report.",
        )

    def diagnose_card_rows(self, rows: list[dict[str, Any]], *, expected_slots: int, expected_cards: int, target: str = "controlled_atlas_cards") -> DoctorReport:
        findings: list[DoctorFinding] = []
        if len(rows) != expected_cards:
            findings.append(_finding(
                finding_id="atlas_card_count_mismatch",
                title="Atlas card count mismatch",
                description=f"Expected {expected_cards} card rows, observed {len(rows)}.",
                target=target,
                severity=DoctorSeverity.BLOCKER,
                status=ImplementationStatus.RISK,
                confidence=0.99,
                risks=[RiskFlag(
                    risk_id="risk_atlas_card_count_mismatch",
                    description="Card count mismatch can indicate missing languages or accidental extra slots.",
                    affected_layer=DoctorLayer.GLOBAL_LAYER,
                    mitigation="Regenerate cards to exact expected count.",
                    severity=DoctorSeverity.BLOCKER,
                )],
            ))

        slots: dict[int, set[str]] = {}
        for row in rows:
            slots.setdefault(int(row.get("slot_id", -1)), set()).add(str(row.get("language_id")))
            if row.get("source_binding") == "SOURCE":
                findings.append(_finding(
                    finding_id=f"atlas_card_source_binding_source_{row.get('card_id')}",
                    title="Atlas card uses SOURCE binding",
                    description="Cards must not be SOURCE by default.",
                    target=str(row.get("card_id")),
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.99,
                    risks=[RiskFlag(
                        risk_id="risk_atlas_card_source_binding_source",
                        description="SOURCE binding by default violates epistemic boundary.",
                        affected_layer=DoctorLayer.GLOBAL_LAYER,
                        mitigation="Set source_binding to ARTIFACT_GROUNDED or lower.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                ))
            if row.get("canon_allowed") is True:
                findings.append(_finding(
                    finding_id=f"atlas_card_canon_allowed_{row.get('card_id')}",
                    title="Atlas card allows canon",
                    description="Cards must not allow canon by default.",
                    target=str(row.get("card_id")),
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.99,
                    risks=[RiskFlag(
                        risk_id="risk_atlas_card_canon_allowed",
                        description="canon_allowed=true by default violates canon boundary.",
                        affected_layer=DoctorLayer.GLOBAL_LAYER,
                        mitigation="Force canon_allowed=false.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                ))
            marker = (row.get("runtime") or {}).get("noema_holonomic_marker") or {}
            if marker.get("noema_current_update_allowed") is True:
                findings.append(_finding(
                    finding_id=f"atlas_marker_current_update_{row.get('card_id')}",
                    title="Atlas card marker allows CURRENT update",
                    description="NOEMA marker must not update CURRENT.",
                    target=str(row.get("card_id")),
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.99,
                    risks=[RiskFlag(
                        risk_id="risk_atlas_marker_current_update",
                        description="Marker CURRENT update violates NOEMA boundary.",
                        affected_layer=DoctorLayer.GLOBAL_LAYER,
                        mitigation="Set noema_current_update_allowed=false.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                ))

        if len(slots) != expected_slots:
            findings.append(_finding(
                finding_id="atlas_slot_count_from_cards_mismatch",
                title="Atlas slot count from cards mismatch",
                description=f"Expected {expected_slots} slots from card rows, observed {len(slots)}.",
                target=target,
                severity=DoctorSeverity.BLOCKER,
                status=ImplementationStatus.RISK,
                confidence=0.99,
                risks=[RiskFlag(
                    risk_id="risk_atlas_slot_count_from_cards_mismatch",
                    description="Slot count mismatch can indicate hidden accidental atlas expansion.",
                    affected_layer=DoctorLayer.GLOBAL_LAYER,
                    mitigation="Repair card rows to exact expected slots.",
                    severity=DoctorSeverity.BLOCKER,
                )],
            ))

        for slot_id, langs in slots.items():
            if langs != {"pl", "en", "ja"}:
                findings.append(_finding(
                    finding_id=f"atlas_slot_language_coverage_{slot_id}",
                    title="Atlas slot language coverage mismatch",
                    description=f"Slot {slot_id} has languages {sorted(langs)} instead of PL/EN/JA.",
                    target=f"{target}.slot_{slot_id}",
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.95,
                    risks=[RiskFlag(
                        risk_id=f"risk_atlas_slot_language_coverage_{slot_id}",
                        description="Every controlled atlas slot must have PL/EN/JA rows.",
                        affected_layer=DoctorLayer.GLOBAL_LAYER,
                        mitigation="Add missing language rows or quarantine slot.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                ))

        return DoctorReport(
            report_id="controlled_atlas_card_rows_doctor_report",
            doctor_id=self.doctor_id,
            target=target,
            findings=findings,
            summary="Controlled atlas card-row diagnostic report.",
        )

    def diagnose_alignment_rows(self, rows: list[dict[str, Any]], *, expected_alignments: int, target: str = "controlled_atlas_alignment") -> DoctorReport:
        findings: list[DoctorFinding] = []
        if len(rows) != expected_alignments:
            findings.append(_finding(
                finding_id="atlas_alignment_count_mismatch",
                title="Atlas alignment count mismatch",
                description=f"Expected {expected_alignments} alignment rows, observed {len(rows)}.",
                target=target,
                severity=DoctorSeverity.BLOCKER,
                status=ImplementationStatus.RISK,
                confidence=0.99,
                risks=[RiskFlag(
                    risk_id="risk_atlas_alignment_count_mismatch",
                    description="Alignment count mismatch can hide missing or extra slot correspondence.",
                    affected_layer=DoctorLayer.GLOBAL_LAYER,
                    mitigation="Regenerate alignments to exact expected count.",
                    severity=DoctorSeverity.BLOCKER,
                )],
            ))

        for row in rows:
            if row.get("semantic_identity_claimed") is True:
                findings.append(_finding(
                    finding_id=f"atlas_alignment_semantic_identity_{row.get('slot_id')}",
                    title="Atlas alignment claims semantic identity",
                    description="Atlas alignment must remain slot_correspondence only.",
                    target=f"{target}.slot_{row.get('slot_id')}",
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.99,
                    risks=[RiskFlag(
                        risk_id="risk_atlas_alignment_semantic_identity",
                        description="Semantic identity claim violates cross-language boundary.",
                        affected_layer=DoctorLayer.GLOBAL_LAYER,
                        mitigation="Set semantic_identity_claimed=false and keep residue notes.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                ))
            notes = " ".join(row.get("residue_notes") or [])
            if "comparison axis" not in notes:
                findings.append(_finding(
                    finding_id=f"atlas_alignment_missing_axis_note_{row.get('slot_id')}",
                    title="Atlas alignment missing comparison-axis residue note",
                    description="Alignment should explicitly say slot_id is a comparison axis.",
                    target=f"{target}.slot_{row.get('slot_id')}",
                    severity=DoctorSeverity.WARNING,
                    status=ImplementationStatus.LIMITATION,
                    confidence=0.8,
                    limitations=[Limitation(
                        limitation_id=f"lim_atlas_alignment_axis_note_{row.get('slot_id')}",
                        description="Comparison-axis limitation missing.",
                        affected_scope=f"slot {row.get('slot_id')}",
                        consequence="Downstream code may overclaim equivalence.",
                    )],
                ))

        return DoctorReport(
            report_id="controlled_atlas_alignment_rows_doctor_report",
            doctor_id=self.doctor_id,
            target=target,
            findings=findings,
            summary="Controlled atlas alignment-row diagnostic report.",
        )



class SentenceCardCouplingDoctor:
    """Diagnose atlas-driven sentence/card coupling reports.

    Protects:
    - coupling_candidate is not semantic identity;
    - card link is not parser proof;
    - report is not runtime cognition or memory writeback.
    """

    doctor_id = "sentence_card_coupling_doctor"

    def diagnose_report(self, report: Any, target: str = "SentenceCardCouplingReport") -> DoctorReport:
        findings: list[DoctorFinding] = []

        if hasattr(report, "validate"):
            for idx, issue in enumerate(report.validate()):
                findings.append(_finding(
                    finding_id=f"sentence_card_coupling_validation_{idx}",
                    title="Sentence-card coupling validation issue",
                    description=str(issue),
                    target=target,
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.98,
                    risks=[RiskFlag(
                        risk_id=f"risk_sentence_card_coupling_validation_{idx}",
                        description="Invalid coupling report can overclaim parser/semantic identity.",
                        affected_layer=DoctorLayer.LINGOPHYSICS,
                        mitigation="Repair coupling report before downstream use.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                    repairs=[RepairCandidate(
                        action_kind=RepairActionKind.REFACTOR,
                        description="Repair SentenceCardCouplingReport so validate() returns no issues.",
                        target_path=target,
                        required_before_merge=True,
                    )],
                ))
        else:
            findings.append(_finding(
                finding_id="sentence_card_coupling_missing_validate",
                title="Sentence-card coupling report missing validate()",
                description="Coupling report must expose validate().",
                target=target,
                severity=DoctorSeverity.BLOCKER,
                status=ImplementationStatus.RISK,
                confidence=0.95,
                risks=[RiskFlag(
                    risk_id="risk_sentence_card_coupling_missing_validate",
                    description="Cannot verify coupling boundaries.",
                    affected_layer=DoctorLayer.LINGOPHYSICS,
                    mitigation="Use SentenceCardCouplingReport contract or adapter.",
                    severity=DoctorSeverity.BLOCKER,
                )],
            ))

        for flag in [
            "semantic_identity_claimed",
            "canon_allowed",
            "source_promotion_allowed",
            "noema_writeback_allowed",
            "current_update_allowed",
            "runtime_cognition_claimed",
        ]:
            if getattr(report, flag, False) is True:
                findings.append(_finding(
                    finding_id=f"sentence_card_coupling_authority_leak_{flag}",
                    title=f"Sentence-card coupling authority/claim leak: {flag}",
                    description="Coupling report must not claim identity/runtime or grant SOURCE/canon/NOEMA/CURRENT authority.",
                    target=f"{target}.{flag}",
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.99,
                    risks=[RiskFlag(
                        risk_id=f"risk_sentence_card_coupling_authority_leak_{flag}",
                        description=f"{flag}=True violates sentence/card coupling boundary.",
                        affected_layer=DoctorLayer.LINGOPHYSICS,
                        mitigation="Force flag false and keep report diagnostic-only.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                ))

        links = list(getattr(report, "links", []) or [])
        for idx, link in enumerate(links):
            if hasattr(link, "validate"):
                for issue_idx, issue in enumerate(link.validate()):
                    findings.append(_finding(
                        finding_id=f"atlas_card_link_validation_{idx}_{issue_idx}",
                        title="AtlasCardLink validation issue",
                        description=str(issue),
                        target=f"{target}.links[{idx}]",
                        severity=DoctorSeverity.BLOCKER,
                        status=ImplementationStatus.RISK,
                        confidence=0.95,
                        risks=[RiskFlag(
                            risk_id=f"risk_atlas_card_link_validation_{idx}_{issue_idx}",
                            description="Invalid card link can overclaim parser proof.",
                            affected_layer=DoctorLayer.LINGOPHYSICS,
                            mitigation="Repair card link bounds and limitation.",
                            severity=DoctorSeverity.BLOCKER,
                        )],
                    ))

        residue = getattr(report, "coupling_residue", 0.0)
        if isinstance(residue, (int, float)) and float(residue) > 0.0:
            findings.append(_finding(
                finding_id="sentence_card_coupling_residue_present",
                title="Sentence-card coupling residue present",
                description="Some slot axes could not be coupled to atlas cards.",
                target=f"{target}.coupling_residue",
                severity=DoctorSeverity.WARNING,
                status=ImplementationStatus.LIMITATION,
                confidence=0.8,
                evidence=[f"coupling_residue={residue}"],
                limitations=[Limitation(
                    limitation_id="lim_sentence_card_coupling_residue",
                    description="Coupling residue indicates incomplete atlas link coverage for this sentence.",
                    affected_scope=target,
                    consequence="Downstream state must treat coupling as partial.",
                )],
            ))

        return DoctorReport(
            report_id="sentence_card_coupling_doctor_report",
            doctor_id=self.doctor_id,
            target=target,
            findings=findings,
            summary="Sentence/card atlas coupling diagnostic report.",
        )



class CouplingAwareAlignmentDoctor:
    """Diagnose coupling-aware cross-language alignment.

    Protects:
    - coupling-aware alignment is not semantic identity;
    - coupling-aware report is not translation proof;
    - card coupling does not grant SOURCE/canon/NOEMA/CURRENT authority.
    """

    doctor_id = "coupling_aware_alignment_doctor"

    def diagnose_candidate(self, candidate: Any, target: str = "CouplingAwareAlignmentCandidate") -> DoctorReport:
        findings: list[DoctorFinding] = []
        if hasattr(candidate, "validate"):
            for idx, issue in enumerate(candidate.validate()):
                findings.append(_finding(
                    finding_id=f"coupling_aware_alignment_candidate_validation_{idx}",
                    title="Coupling-aware alignment candidate validation issue",
                    description=str(issue),
                    target=target,
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.98,
                    risks=[RiskFlag(
                        risk_id=f"risk_coupling_aware_alignment_candidate_validation_{idx}",
                        description="Invalid coupling-aware candidate can falsely imply semantic identity.",
                        affected_layer=DoctorLayer.LINGOPHYSICS,
                        mitigation="Repair candidate before downstream use.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                ))
        else:
            findings.append(_finding(
                finding_id="coupling_aware_alignment_candidate_missing_validate",
                title="Coupling-aware candidate missing validate()",
                description="Candidate must expose validate().",
                target=target,
                severity=DoctorSeverity.BLOCKER,
                status=ImplementationStatus.RISK,
                confidence=0.95,
                risks=[RiskFlag(
                    risk_id="risk_coupling_aware_alignment_candidate_missing_validate",
                    description="Cannot verify candidate boundary.",
                    affected_layer=DoctorLayer.LINGOPHYSICS,
                    mitigation="Use CouplingAwareAlignmentCandidate contract.",
                    severity=DoctorSeverity.BLOCKER,
                )],
            ))

        for flag in ["semantic_identity_claimed", "canon_allowed", "source_promotion_allowed", "noema_writeback_allowed", "current_update_allowed"]:
            if getattr(candidate, flag, False) is True:
                findings.append(_finding(
                    finding_id=f"coupling_aware_alignment_authority_leak_{flag}",
                    title=f"Coupling-aware alignment authority/identity leak: {flag}",
                    description="Coupling-aware alignment must not claim identity or grant SOURCE/canon/NOEMA/CURRENT authority.",
                    target=f"{target}.{flag}",
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.99,
                    risks=[RiskFlag(
                        risk_id=f"risk_coupling_aware_alignment_authority_leak_{flag}",
                        description=f"{flag}=True violates coupling-aware alignment boundary.",
                        affected_layer=DoctorLayer.LINGOPHYSICS,
                        mitigation="Force flag false.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                ))

        if "ja" in tuple(getattr(candidate, "language_pair", ()) or ()):
            residues = list(getattr(candidate, "residue", []) or [])
            if not any(getattr(r, "residue_type", "") == "native_review_residue" for r in residues):
                findings.append(_finding(
                    finding_id="coupling_aware_ja_missing_native_review_residue",
                    title="JA coupling-aware alignment missing native-review residue",
                    description="JA coupling-aware alignment must preserve native/regional review residue.",
                    target=f"{target}.residue",
                    severity=DoctorSeverity.ERROR,
                    status=ImplementationStatus.RISK,
                    confidence=0.9,
                    risks=[RiskFlag(
                        risk_id="risk_coupling_aware_ja_without_native_review",
                        description="JA coupling-aware alignment without review residue can be over-promoted.",
                        affected_layer=DoctorLayer.LINGOPHYSICS,
                        mitigation="Add native_review_residue for JA pairs.",
                        severity=DoctorSeverity.ERROR,
                    )],
                ))

        return DoctorReport(
            report_id="coupling_aware_alignment_candidate_doctor_report",
            doctor_id=self.doctor_id,
            target=target,
            findings=findings,
            summary="Coupling-aware alignment candidate diagnostic report.",
        )

    def diagnose_report(self, report: Any, target: str = "CouplingAwareCrossLanguageAlignmentReport") -> DoctorReport:
        findings: list[DoctorFinding] = []
        if hasattr(report, "validate"):
            for idx, issue in enumerate(report.validate()):
                findings.append(_finding(
                    finding_id=f"coupling_aware_alignment_report_validation_{idx}",
                    title="Coupling-aware alignment report validation issue",
                    description=str(issue),
                    target=target,
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.98,
                    risks=[RiskFlag(
                        risk_id=f"risk_coupling_aware_alignment_report_validation_{idx}",
                        description="Invalid report can corrupt cross-language coupling state.",
                        affected_layer=DoctorLayer.LINGOPHYSICS,
                        mitigation="Repair report before use.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                ))
        else:
            findings.append(_finding(
                finding_id="coupling_aware_alignment_report_missing_validate",
                title="Coupling-aware alignment report missing validate()",
                description="Report must expose validate().",
                target=target,
                severity=DoctorSeverity.BLOCKER,
                status=ImplementationStatus.RISK,
                confidence=0.95,
                risks=[RiskFlag(
                    risk_id="risk_coupling_aware_alignment_report_missing_validate",
                    description="Cannot verify report boundaries.",
                    affected_layer=DoctorLayer.LINGOPHYSICS,
                    mitigation="Use CouplingAwareCrossLanguageAlignmentReport contract.",
                    severity=DoctorSeverity.BLOCKER,
                )],
            ))

        for flag in ["canon_allowed", "source_promotion_allowed", "noema_writeback_allowed", "current_update_allowed"]:
            if getattr(report, flag, False) is True:
                findings.append(_finding(
                    finding_id=f"coupling_aware_alignment_report_authority_leak_{flag}",
                    title=f"Coupling-aware report authority leak: {flag}",
                    description="Report must not grant SOURCE/canon/NOEMA/CURRENT authority.",
                    target=f"{target}.{flag}",
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.99,
                    risks=[RiskFlag(
                        risk_id=f"risk_coupling_aware_alignment_report_authority_leak_{flag}",
                        description=f"{flag}=True violates coupling-aware report boundary.",
                        affected_layer=DoctorLayer.LINGOPHYSICS,
                        mitigation="Force flag false.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                ))

        for idx, candidate in enumerate(list(getattr(report, "candidates", []) or [])):
            candidate_report = self.diagnose_candidate(candidate, target=f"{target}.candidates[{idx}]")
            findings.extend(candidate_report.findings)

        return DoctorReport(
            report_id="coupling_aware_alignment_report_doctor_report",
            doctor_id=self.doctor_id,
            target=target,
            findings=findings,
            summary="Coupling-aware alignment report diagnostic report.",
        )



class MeaningLoopDoctor:
    """Diagnose MeaningLoop/SemanticScar objects."""

    doctor_id = "meaning_loop_doctor"

    def diagnose_loop(self, loop: Any, target: str = "MeaningLoop") -> DoctorReport:
        findings: list[DoctorFinding] = []
        if hasattr(loop, "validate"):
            for idx, issue in enumerate(loop.validate()):
                findings.append(_finding(
                    finding_id=f"meaning_loop_validation_{idx}",
                    title="MeaningLoop validation issue",
                    description=str(issue),
                    target=target,
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.98,
                    risks=[RiskFlag(
                        risk_id=f"risk_meaning_loop_validation_{idx}",
                        description="Invalid MeaningLoop can hide false closure or authority leakage.",
                        affected_layer=DoctorLayer.LINGOPHYSICS,
                        mitigation="Repair MeaningLoop before downstream use.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                ))
        else:
            findings.append(_finding(
                finding_id="meaning_loop_missing_validate",
                title="MeaningLoop missing validate()",
                description="MeaningLoop must expose validate().",
                target=target,
                severity=DoctorSeverity.BLOCKER,
                status=ImplementationStatus.RISK,
                confidence=0.95,
                risks=[RiskFlag(
                    risk_id="risk_meaning_loop_missing_validate",
                    description="Cannot verify loop closure/debt boundaries.",
                    affected_layer=DoctorLayer.LINGOPHYSICS,
                    mitigation="Use MeaningLoop contract.",
                    severity=DoctorSeverity.BLOCKER,
                )],
            ))

        for flag in ["canon_allowed", "source_promotion_allowed", "noema_writeback_allowed", "current_update_allowed"]:
            if getattr(loop, flag, False) is True:
                findings.append(_finding(
                    finding_id=f"meaning_loop_authority_leak_{flag}",
                    title=f"MeaningLoop authority leak: {flag}",
                    description="MeaningLoop must not grant SOURCE/canon/NOEMA/CURRENT authority.",
                    target=f"{target}.{flag}",
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.99,
                    risks=[RiskFlag(
                        risk_id=f"risk_meaning_loop_authority_leak_{flag}",
                        description=f"{flag}=True violates MeaningLoop boundary.",
                        affected_layer=DoctorLayer.LINGOPHYSICS,
                        mitigation="Force flag false.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                ))

        scars = list(getattr(loop, "scars", []) or [])
        if scars and getattr(loop, "return_required", False) is not True:
            findings.append(_finding(
                finding_id="meaning_loop_scars_without_return_required",
                title="MeaningLoop has scars but return_required is false",
                description="Scarred loops must explicitly require return/repair.",
                target=f"{target}.return_required",
                severity=DoctorSeverity.ERROR,
                status=ImplementationStatus.RISK,
                confidence=0.9,
                risks=[RiskFlag(
                    risk_id="risk_meaning_loop_scar_without_return",
                    description="Scars without return_required can hide repair debt.",
                    affected_layer=DoctorLayer.LINGOPHYSICS,
                    mitigation="Set return_required=true or classify scars differently.",
                    severity=DoctorSeverity.ERROR,
                )],
            ))

        return DoctorReport(
            report_id="meaning_loop_doctor_report",
            doctor_id=self.doctor_id,
            target=target,
            findings=findings,
            summary="MeaningLoop/SemanticScar diagnostic report.",
        )



class MeaningRepairRoutingDoctor:
    """Diagnose MeaningRepairRoutingReport / MeaningRepairCandidate."""

    doctor_id = "meaning_repair_routing_doctor"

    def diagnose_report(self, report: Any, target: str = "MeaningRepairRoutingReport") -> DoctorReport:
        findings: list[DoctorFinding] = []
        if hasattr(report, "validate"):
            for idx, issue in enumerate(report.validate()):
                findings.append(_finding(
                    finding_id=f"meaning_repair_routing_validation_{idx}",
                    title="MeaningRepairRouting validation issue",
                    description=str(issue),
                    target=target,
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.98,
                    risks=[RiskFlag(
                        risk_id=f"risk_meaning_repair_routing_validation_{idx}",
                        description="Invalid routing can hide execution/authority leakage.",
                        affected_layer=DoctorLayer.LINGOPHYSICS,
                        mitigation="Repair routing report before downstream use.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                ))
        else:
            findings.append(_finding(
                finding_id="meaning_repair_routing_missing_validate",
                title="MeaningRepairRouting missing validate()",
                description="Routing report must expose validate().",
                target=target,
                severity=DoctorSeverity.BLOCKER,
                status=ImplementationStatus.RISK,
                confidence=0.95,
                risks=[RiskFlag(
                    risk_id="risk_meaning_repair_routing_missing_validate",
                    description="Cannot verify repair routing boundaries.",
                    affected_layer=DoctorLayer.LINGOPHYSICS,
                    mitigation="Use MeaningRepairRoutingReport contract.",
                    severity=DoctorSeverity.BLOCKER,
                )],
            ))

        for flag in ["executes_runtime_action", "canon_allowed", "source_promotion_allowed", "noema_writeback_allowed", "current_update_allowed"]:
            if getattr(report, flag, False) is True:
                findings.append(_finding(
                    finding_id=f"meaning_repair_routing_authority_leak_{flag}",
                    title=f"MeaningRepairRouting authority/execution leak: {flag}",
                    description="Repair routing must not execute or grant SOURCE/canon/NOEMA/CURRENT authority.",
                    target=f"{target}.{flag}",
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.99,
                    risks=[RiskFlag(
                        risk_id=f"risk_meaning_repair_routing_authority_leak_{flag}",
                        description=f"{flag}=True violates repair routing boundary.",
                        affected_layer=DoctorLayer.LINGOPHYSICS,
                        mitigation="Force flag false.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                ))

        unresolved = list(getattr(report, "unresolved_scar_ids", []) or [])
        if unresolved:
            findings.append(_finding(
                finding_id="meaning_repair_routing_unresolved_scars",
                title="Repair routing has unresolved scars",
                description="Some scars did not produce repair candidates.",
                target=f"{target}.unresolved_scar_ids",
                severity=DoctorSeverity.WARNING,
                status=ImplementationStatus.LIMITATION,
                confidence=0.85,
                evidence=[repr(unresolved)],
                limitations=[Limitation(
                    limitation_id="lim_repair_routing_unresolved_scars",
                    description="Unresolved scars require manual classification or route extension.",
                    affected_scope=target,
                    consequence="Loop cannot be considered fully routed.",
                )],
            ))

        return DoctorReport(
            report_id="meaning_repair_routing_doctor_report",
            doctor_id=self.doctor_id,
            target=target,
            findings=findings,
            summary="MeaningLoop repair routing diagnostic report.",
        )



class MeaningExportAndSignalDoctor:
    """Diagnose MeaningLoop export bundles and global meaning signals."""

    doctor_id = "meaning_export_and_signal_doctor"

    def diagnose(self, obj: Any, target: str = "MeaningExportOrSignal") -> DoctorReport:
        findings: list[DoctorFinding] = []
        if hasattr(obj, "validate"):
            for idx, issue in enumerate(obj.validate()):
                findings.append(_finding(
                    finding_id=f"meaning_export_signal_validation_{idx}",
                    title="Meaning export/signal validation issue",
                    description=str(issue),
                    target=target,
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.98,
                    risks=[RiskFlag(
                        risk_id=f"risk_meaning_export_signal_validation_{idx}",
                        description="Invalid export/signal can hide authority or execution leakage.",
                        affected_layer=DoctorLayer.GLOBAL_LAYER,
                        mitigation="Repair object before export or bridge use.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                ))
        else:
            findings.append(_finding(
                finding_id="meaning_export_signal_missing_validate",
                title="Meaning export/signal missing validate()",
                description="Object must expose validate().",
                target=target,
                severity=DoctorSeverity.BLOCKER,
                status=ImplementationStatus.RISK,
                confidence=0.95,
                risks=[RiskFlag(
                    risk_id="risk_meaning_export_signal_missing_validate",
                    description="Cannot verify export/signal boundaries.",
                    affected_layer=DoctorLayer.GLOBAL_LAYER,
                    mitigation="Use typed export/signal contract.",
                    severity=DoctorSeverity.BLOCKER,
                )],
            ))
        for flag in ["canon_allowed", "source_promotion_allowed", "noema_writeback_allowed", "current_update_allowed", "runtime_execution_allowed"]:
            if getattr(obj, flag, False) is True:
                findings.append(_finding(
                    finding_id=f"meaning_export_signal_authority_leak_{flag}",
                    title=f"Meaning export/signal authority leak: {flag}",
                    description="Export/signal must not grant SOURCE/canon/NOEMA/CURRENT/runtime execution authority.",
                    target=f"{target}.{flag}",
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.99,
                    risks=[RiskFlag(
                        risk_id=f"risk_meaning_export_signal_authority_leak_{flag}",
                        description=f"{flag}=True violates export/signal boundary.",
                        affected_layer=DoctorLayer.GLOBAL_LAYER,
                        mitigation="Force flag false.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                ))
        return DoctorReport(
            report_id="meaning_export_and_signal_doctor_report",
            doctor_id=self.doctor_id,
            target=target,
            findings=findings,
            summary="Meaning export/global signal diagnostic report.",
        )



class RuntimeBridgeDryRunDoctor:
    """Diagnose RuntimeBridgeDryRunResult."""

    doctor_id = "runtime_bridge_dry_run_doctor"

    def diagnose(self, result: Any, target: str = "RuntimeBridgeDryRunResult") -> DoctorReport:
        findings: list[DoctorFinding] = []
        if hasattr(result, "validate"):
            for idx, issue in enumerate(result.validate()):
                findings.append(_finding(
                    finding_id=f"runtime_bridge_dry_run_validation_{idx}",
                    title="RuntimeBridgeDryRun validation issue",
                    description=str(issue),
                    target=target,
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.98,
                    risks=[RiskFlag(
                        risk_id=f"risk_runtime_bridge_dry_run_validation_{idx}",
                        description="Invalid dry-run result can hide runtime/authority leakage.",
                        affected_layer=DoctorLayer.GLOBAL_LAYER,
                        mitigation="Repair dry-run result before any bridge integration.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                ))
        else:
            findings.append(_finding(
                finding_id="runtime_bridge_dry_run_missing_validate",
                title="RuntimeBridgeDryRun missing validate()",
                description="Dry-run result must expose validate().",
                target=target,
                severity=DoctorSeverity.BLOCKER,
                status=ImplementationStatus.RISK,
                confidence=0.95,
                risks=[RiskFlag(
                    risk_id="risk_runtime_bridge_dry_run_missing_validate",
                    description="Cannot verify dry-run boundaries.",
                    affected_layer=DoctorLayer.GLOBAL_LAYER,
                    mitigation="Use RuntimeBridgeDryRunResult contract.",
                    severity=DoctorSeverity.BLOCKER,
                )],
            ))

        for flag in ["executed_runtime_action", "canon_allowed", "source_promotion_allowed", "noema_writeback_allowed", "current_update_allowed"]:
            if getattr(result, flag, False) is True:
                findings.append(_finding(
                    finding_id=f"runtime_bridge_dry_run_authority_leak_{flag}",
                    title=f"RuntimeBridgeDryRun authority/execution leak: {flag}",
                    description="Dry-run result must not execute or grant SOURCE/canon/NOEMA/CURRENT authority.",
                    target=f"{target}.{flag}",
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.99,
                    risks=[RiskFlag(
                        risk_id=f"risk_runtime_bridge_dry_run_authority_leak_{flag}",
                        description=f"{flag}=True violates dry-run boundary.",
                        affected_layer=DoctorLayer.GLOBAL_LAYER,
                        mitigation="Force flag false.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                ))

        return DoctorReport(
            report_id="runtime_bridge_dry_run_doctor_report",
            doctor_id=self.doctor_id,
            target=target,
            findings=findings,
            summary="Runtime bridge dry-run diagnostic report.",
        )



class SelfFeedAuditDoctor:
    """Diagnose self-feed audit logs and dry-run export bundles."""

    doctor_id = "self_feed_audit_doctor"

    def diagnose(self, obj: Any, target: str = "SelfFeedAuditOrExport") -> DoctorReport:
        findings: list[DoctorFinding] = []
        if hasattr(obj, "validate"):
            for idx, issue in enumerate(obj.validate()):
                findings.append(_finding(
                    finding_id=f"self_feed_audit_validation_{idx}",
                    title="Self-feed audit/export validation issue",
                    description=str(issue),
                    target=target,
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.98,
                    risks=[RiskFlag(
                        risk_id=f"risk_self_feed_audit_validation_{idx}",
                        description="Invalid self-feed audit/export can hide execution or authority leakage.",
                        affected_layer=DoctorLayer.GLOBAL_LAYER,
                        mitigation="Repair audit/export before publication or bridge use.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                ))
        else:
            findings.append(_finding(
                finding_id="self_feed_audit_missing_validate",
                title="Self-feed audit/export missing validate()",
                description="Object must expose validate().",
                target=target,
                severity=DoctorSeverity.BLOCKER,
                status=ImplementationStatus.RISK,
                confidence=0.95,
                risks=[RiskFlag(
                    risk_id="risk_self_feed_audit_missing_validate",
                    description="Cannot verify self-feed audit/export boundaries.",
                    affected_layer=DoctorLayer.GLOBAL_LAYER,
                    mitigation="Use typed self-feed audit/export contract.",
                    severity=DoctorSeverity.BLOCKER,
                )],
            ))

        for flag in ["executed_runtime_action", "canon_allowed", "source_promotion_allowed", "noema_writeback_allowed", "current_update_allowed"]:
            if getattr(obj, flag, False) is True:
                findings.append(_finding(
                    finding_id=f"self_feed_audit_authority_leak_{flag}",
                    title=f"Self-feed audit/export authority leak: {flag}",
                    description="Self-feed audit/export must not execute or grant SOURCE/canon/NOEMA/CURRENT authority.",
                    target=f"{target}.{flag}",
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.99,
                    risks=[RiskFlag(
                        risk_id=f"risk_self_feed_audit_authority_leak_{flag}",
                        description=f"{flag}=True violates self-feed audit/export boundary.",
                        affected_layer=DoctorLayer.GLOBAL_LAYER,
                        mitigation="Force flag false.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                ))

        return DoctorReport(
            report_id="self_feed_audit_doctor_report",
            doctor_id=self.doctor_id,
            target=target,
            findings=findings,
            summary="Self-feed audit/export diagnostic report.",
        )



class RuntimeAdapterReferenceDoctor:
    """Diagnose runtime adapter references and global dry-test references."""

    doctor_id = "runtime_adapter_reference_doctor"

    def diagnose(self, obj: Any, target: str = "RuntimeAdapterOrGlobalReference") -> DoctorReport:
        findings: list[DoctorFinding] = []
        if hasattr(obj, "validate"):
            for idx, issue in enumerate(obj.validate()):
                findings.append(_finding(
                    finding_id=f"runtime_adapter_reference_validation_{idx}",
                    title="Runtime adapter/global reference validation issue",
                    description=str(issue),
                    target=target,
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.98,
                    risks=[RiskFlag(
                        risk_id=f"risk_runtime_adapter_reference_validation_{idx}",
                        description="Invalid reference can hide execution or SOURCE/canon promotion.",
                        affected_layer=DoctorLayer.GLOBAL_LAYER,
                        mitigation="Repair reference object before use.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                ))
        else:
            findings.append(_finding(
                finding_id="runtime_adapter_reference_missing_validate",
                title="Runtime adapter/global reference missing validate()",
                description="Reference object must expose validate().",
                target=target,
                severity=DoctorSeverity.BLOCKER,
                status=ImplementationStatus.RISK,
                confidence=0.95,
                risks=[RiskFlag(
                    risk_id="risk_runtime_adapter_reference_missing_validate",
                    description="Cannot verify reference boundaries.",
                    affected_layer=DoctorLayer.GLOBAL_LAYER,
                    mitigation="Use typed reference contract.",
                    severity=DoctorSeverity.BLOCKER,
                )],
            ))

        for flag in ["executes_runtime_action", "canon_allowed", "source_promotion_allowed", "noema_writeback_allowed", "current_update_allowed", "runtime_execution_allowed"]:
            if getattr(obj, flag, False) is True:
                findings.append(_finding(
                    finding_id=f"runtime_adapter_reference_authority_leak_{flag}",
                    title=f"Runtime adapter/global reference authority leak: {flag}",
                    description="Reference must not execute or grant SOURCE/canon/NOEMA/CURRENT authority.",
                    target=f"{target}.{flag}",
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.99,
                    risks=[RiskFlag(
                        risk_id=f"risk_runtime_adapter_reference_authority_leak_{flag}",
                        description=f"{flag}=True violates reference boundary.",
                        affected_layer=DoctorLayer.GLOBAL_LAYER,
                        mitigation="Force flag false.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                ))

        return DoctorReport(
            report_id="runtime_adapter_reference_doctor_report",
            doctor_id=self.doctor_id,
            target=target,
            findings=findings,
            summary="Runtime adapter/global reference diagnostic report.",
        )



class RuntimeAdapterExportDoctor:
    """Diagnose RuntimeAdapterReferenceExportBundle."""

    doctor_id = "runtime_adapter_export_doctor"

    def diagnose(self, bundle: Any, target: str = "RuntimeAdapterReferenceExportBundle") -> DoctorReport:
        findings: list[DoctorFinding] = []
        if hasattr(bundle, "validate"):
            for idx, issue in enumerate(bundle.validate()):
                findings.append(_finding(
                    finding_id=f"runtime_adapter_export_validation_{idx}",
                    title="Runtime adapter export validation issue",
                    description=str(issue),
                    target=target,
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.98,
                    risks=[RiskFlag(
                        risk_id=f"risk_runtime_adapter_export_validation_{idx}",
                        description="Invalid runtime adapter export can hide SOURCE/canon/runtime leakage.",
                        affected_layer=DoctorLayer.GLOBAL_LAYER,
                        mitigation="Repair export bundle before publication.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                ))
        else:
            findings.append(_finding(
                finding_id="runtime_adapter_export_missing_validate",
                title="Runtime adapter export missing validate()",
                description="Runtime adapter export must expose validate().",
                target=target,
                severity=DoctorSeverity.BLOCKER,
                status=ImplementationStatus.RISK,
                confidence=0.95,
                risks=[RiskFlag(
                    risk_id="risk_runtime_adapter_export_missing_validate",
                    description="Cannot verify runtime adapter export boundaries.",
                    affected_layer=DoctorLayer.GLOBAL_LAYER,
                    mitigation="Use RuntimeAdapterReferenceExportBundle contract.",
                    severity=DoctorSeverity.BLOCKER,
                )],
            ))

        for flag in ["canon_allowed", "source_promotion_allowed", "noema_writeback_allowed", "current_update_allowed", "runtime_execution_allowed"]:
            if getattr(bundle, flag, False) is True:
                findings.append(_finding(
                    finding_id=f"runtime_adapter_export_authority_leak_{flag}",
                    title=f"Runtime adapter export authority leak: {flag}",
                    description="Runtime adapter export must not grant SOURCE/canon/NOEMA/CURRENT/runtime authority.",
                    target=f"{target}.{flag}",
                    severity=DoctorSeverity.BLOCKER,
                    status=ImplementationStatus.RISK,
                    confidence=0.99,
                    risks=[RiskFlag(
                        risk_id=f"risk_runtime_adapter_export_authority_leak_{flag}",
                        description=f"{flag}=True violates runtime adapter export boundary.",
                        affected_layer=DoctorLayer.GLOBAL_LAYER,
                        mitigation="Force flag false.",
                        severity=DoctorSeverity.BLOCKER,
                    )],
                ))

        return DoctorReport(
            report_id="runtime_adapter_export_doctor_report",
            doctor_id=self.doctor_id,
            target=target,
            findings=findings,
            summary="Runtime adapter reference export diagnostic report.",
        )

@dataclass
class LingophysicsDoctor:
    """Thin aggregator for lingophysics diagnostics.

    It aggregates reports; it does not own truth or runtime authority.
    """

    doctor_id: str = "lingophysics_doctor"

    def diagnose_sentence_equation(self, sentence_equation: Any, target: str = "SentenceEquation") -> DoctorReport:
        return SentenceEquationDoctor().diagnose(sentence_equation, target=target)

    def diagnose_surface_solution(self, surface_solution: Any, target: str = "SurfaceSolution") -> DoctorReport:
        return SurfaceSolutionDoctor().diagnose(surface_solution, target=target)

    def diagnose_local_j(self, local_j: dict[str, Any], target: str = "local_j") -> DoctorReport:
        return LocalJDoctor().diagnose(local_j, target=target)

    def diagnose_regional_separation(self, repo_root: str | Path) -> DoctorReport:
        return RegionalSeparationDoctor().diagnose_repo(repo_root)

    def diagnose_meaning_debt_text(self, text: str, target: str = "text") -> DoctorReport:
        return MeaningDebtDoctor().diagnose_text(text, target=target)

    def diagnose_j_coherence(self, local_j: dict[str, Any], notes: list[Any] | None = None, target: str = "J/coherence") -> DoctorReport:
        return JCoherenceDoctor().diagnose(local_j, notes=notes, target=target)

    def diagnose_semantic_neural_snapshot(self, snapshot: Any, target: str = "SentenceStateSnapshot") -> DoctorReport:
        return SemanticNeuralStateDoctor().diagnose_snapshot(snapshot, target=target)

    def diagnose_cross_language_alignment_candidate(self, candidate: Any, target: str = "LanguageAlignmentCandidate") -> DoctorReport:
        return CrossLanguageAlignmentDoctor().diagnose_candidate(candidate, target=target)

    def diagnose_cross_language_alignment_report(self, report: Any, target: str = "CrossLanguageAlignmentReport") -> DoctorReport:
        return CrossLanguageAlignmentDoctor().diagnose_report(report, target=target)

    def diagnose_controlled_atlas_validation(
        self,
        result: dict[str, Any],
        *,
        expected_slots: int,
        expected_cards: int,
        expected_alignments: int,
        expected_taxonomy: int,
        target: str = "controlled_atlas_validation",
    ) -> DoctorReport:
        return ControlledAtlasDoctor().diagnose_validation_result(
            result,
            expected_slots=expected_slots,
            expected_cards=expected_cards,
            expected_alignments=expected_alignments,
            expected_taxonomy=expected_taxonomy,
            target=target,
        )

    def diagnose_controlled_atlas_cards(self, rows: list[dict[str, Any]], *, expected_slots: int, expected_cards: int, target: str = "controlled_atlas_cards") -> DoctorReport:
        return ControlledAtlasDoctor().diagnose_card_rows(rows, expected_slots=expected_slots, expected_cards=expected_cards, target=target)

    def diagnose_controlled_atlas_alignments(self, rows: list[dict[str, Any]], *, expected_alignments: int, target: str = "controlled_atlas_alignment") -> DoctorReport:
        return ControlledAtlasDoctor().diagnose_alignment_rows(rows, expected_alignments=expected_alignments, target=target)

    def diagnose_sentence_card_coupling(self, report: Any, target: str = "SentenceCardCouplingReport") -> DoctorReport:
        return SentenceCardCouplingDoctor().diagnose_report(report, target=target)

    def diagnose_coupling_aware_alignment_candidate(self, candidate: Any, target: str = "CouplingAwareAlignmentCandidate") -> DoctorReport:
        return CouplingAwareAlignmentDoctor().diagnose_candidate(candidate, target=target)

    def diagnose_coupling_aware_alignment_report(self, report: Any, target: str = "CouplingAwareCrossLanguageAlignmentReport") -> DoctorReport:
        return CouplingAwareAlignmentDoctor().diagnose_report(report, target=target)

    def diagnose_meaning_loop(self, loop: Any, target: str = "MeaningLoop") -> DoctorReport:
        return MeaningLoopDoctor().diagnose_loop(loop, target=target)

    def diagnose_meaning_repair_routing(self, report: Any, target: str = "MeaningRepairRoutingReport") -> DoctorReport:
        return MeaningRepairRoutingDoctor().diagnose_report(report, target=target)

    def diagnose_meaning_export_or_signal(self, obj: Any, target: str = "MeaningExportOrSignal") -> DoctorReport:
        return MeaningExportAndSignalDoctor().diagnose(obj, target=target)

    def diagnose_runtime_bridge_dry_run(self, result: Any, target: str = "RuntimeBridgeDryRunResult") -> DoctorReport:
        return RuntimeBridgeDryRunDoctor().diagnose(result, target=target)

    def diagnose_self_feed_audit_or_export(self, obj: Any, target: str = "SelfFeedAuditOrExport") -> DoctorReport:
        return SelfFeedAuditDoctor().diagnose(obj, target=target)

    def diagnose_runtime_adapter_or_global_reference(self, obj: Any, target: str = "RuntimeAdapterOrGlobalReference") -> DoctorReport:
        return RuntimeAdapterReferenceDoctor().diagnose(obj, target=target)

    def diagnose_runtime_adapter_export(self, bundle: Any, target: str = "RuntimeAdapterReferenceExportBundle") -> DoctorReport:
        return RuntimeAdapterExportDoctor().diagnose(bundle, target=target)
