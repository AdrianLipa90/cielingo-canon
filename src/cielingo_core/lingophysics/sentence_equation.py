"""Sentence equation calculator for CIELingo 0.5K.

This layer computes a bounded, auditable equation object from regional
SurfaceSolution and MeaningEquation candidates.

It is not full grammar, not SOURCE validation, not NOEMA writeback and not
runtime execution.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any

from cielingo_core.global_layer.contracts import MeaningEquation
from cielingo_core.global_layer.global_algorithm_v02 import GlobalAlgorithmV02Result, run_global_algorithm_v02
from cielingo_core.regional.base import RegionalSolveResult
from cielingo_core.regional.regional_to_global import regional_result_to_meaning_equation


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


class EquationTermKind(str, Enum):
    SLOT = "slot"
    OPERATOR = "operator"
    ROLE = "role"
    J = "j"
    RESIDUE = "residue"
    SIGNAL = "signal"


@dataclass
class SentenceEquationTerm:
    term_id: str
    kind: EquationTermKind
    symbol: str
    value: float
    source: str
    notes: list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.term_id:
            issues.append("term_id is required")
        if not self.symbol:
            issues.append("symbol is required")
        if not 0.0 <= float(self.value) <= 1.0:
            issues.append(f"{self.term_id}.value must be in [0,1]")
        return issues

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["kind"] = self.kind.value
        return out


@dataclass
class SentenceEquation:
    equation_id: str
    language_id: str
    text: str
    tokens: list[str]
    terms: list[SentenceEquationTerm]
    expression: str
    meaning_equation: MeaningEquation
    global_result: GlobalAlgorithmV02Result
    j_total: float
    closure_pressure: float
    residue_pressure: float
    source_pressure: float
    consent_pressure: float
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    notes: list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        issues: list[str] = []
        if not self.equation_id:
            issues.append("equation_id is required")
        for term in self.terms:
            issues.extend(term.validate())
        for name in ("j_total", "closure_pressure", "residue_pressure", "source_pressure", "consent_pressure"):
            if not 0.0 <= float(getattr(self, name)) <= 1.0:
                issues.append(f"{name} must be in [0,1]")
        if self.canon_allowed:
            issues.append("SentenceEquation must not grant canon")
        if self.source_promotion_allowed:
            issues.append("SentenceEquation must not promote SOURCE")
        if self.noema_writeback_allowed:
            issues.append("SentenceEquation must not write NOEMA")
        if self.current_update_allowed:
            issues.append("SentenceEquation must not update CURRENT")
        issues.extend(self.meaning_equation.validate())
        issues.extend(self.global_result.validate())
        return issues

    def to_dict(self) -> dict[str, Any]:
        return {
            "equation_id": self.equation_id,
            "language_id": self.language_id,
            "text": self.text,
            "tokens": self.tokens,
            "terms": [t.to_dict() for t in self.terms],
            "expression": self.expression,
            "meaning_equation": self.meaning_equation.to_dict(),
            "global_result": self.global_result.to_dict(),
            "j_total": self.j_total,
            "closure_pressure": self.closure_pressure,
            "residue_pressure": self.residue_pressure,
            "source_pressure": self.source_pressure,
            "consent_pressure": self.consent_pressure,
            "canon_allowed": self.canon_allowed,
            "source_promotion_allowed": self.source_promotion_allowed,
            "noema_writeback_allowed": self.noema_writeback_allowed,
            "current_update_allowed": self.current_update_allowed,
            "notes": self.notes,
        }


def _terms_from_regional_result(result: RegionalSolveResult, meaning: MeaningEquation, global_result: GlobalAlgorithmV02Result) -> list[SentenceEquationTerm]:
    terms: list[SentenceEquationTerm] = []

    slot_ids = sorted(result.surface_solution.slot_projection)
    denom = max(1, len(result.surface_solution.tokens))
    for slot_id in slot_ids:
        indices = result.surface_solution.slot_projection[slot_id]
        terms.append(SentenceEquationTerm(
            term_id=f"slot_{slot_id}",
            kind=EquationTermKind.SLOT,
            symbol=f"S[{slot_id}]",
            value=clamp01(len(indices) / denom),
            source="SurfaceSolution.slot_projection",
            notes=[f"token_indices={indices}"],
        ))

    for op in meaning.operators:
        terms.append(SentenceEquationTerm(
            term_id=f"op_{op.operator_type.value}",
            kind=EquationTermKind.OPERATOR,
            symbol=op.operator_type.value,
            value=clamp01(op.strength),
            source="MeaningEquation.operators",
        ))

    for key, value in result.surface_solution.local_j.items():
        terms.append(SentenceEquationTerm(
            term_id=f"j_{key}",
            kind=EquationTermKind.J,
            symbol=key,
            value=clamp01(float(value)),
            source="SurfaceSolution.local_j",
        ))

    immune = global_result.immune_signal
    terms.extend([
        SentenceEquationTerm(
            term_id="signal_source_confusion",
            kind=EquationTermKind.SIGNAL,
            symbol="source_confusion",
            value=1.0 if immune.source_confusion else 0.0,
            source="SemanticImmuneSignal",
        ),
        SentenceEquationTerm(
            term_id="signal_consent_bypass",
            kind=EquationTermKind.SIGNAL,
            symbol="consent_bypass_attempt",
            value=1.0 if immune.consent_bypass_attempt else 0.0,
            source="SemanticImmuneSignal",
        ),
        SentenceEquationTerm(
            term_id="signal_hallucinated_authority",
            kind=EquationTermKind.SIGNAL,
            symbol="hallucinated_authority_risk",
            value=clamp01(immune.hallucinated_authority_risk),
            source="SemanticImmuneSignal",
        ),
    ])

    return terms


def _expression_from_terms(terms: list[SentenceEquationTerm]) -> str:
    slots = [t.symbol for t in terms if t.kind == EquationTermKind.SLOT]
    ops = [t.symbol for t in terms if t.kind == EquationTermKind.OPERATOR]
    js = [t.symbol for t in terms if t.kind == EquationTermKind.J]
    signals = [t.symbol for t in terms if t.kind == EquationTermKind.SIGNAL and t.value > 0]
    return "SentenceEquation := " + " + ".join([
        "Slots(" + ",".join(slots or ["∅"]) + ")",
        "Ops(" + ",".join(ops or ["∅"]) + ")",
        "J(" + ",".join(js or ["∅"]) + ")",
        "Signals(" + ",".join(signals or ["∅"]) + ")",
    ])


def calculate_sentence_equation(result: RegionalSolveResult) -> SentenceEquation:
    """Calculate bounded sentence equation from regional result."""
    issues = result.validate()
    if issues:
        raise ValueError("; ".join(issues))

    meaning = regional_result_to_meaning_equation(result)
    global_result = run_global_algorithm_v02(meaning)
    terms = _terms_from_regional_result(result, meaning, global_result)

    j_values = [t.value for t in terms if t.kind == EquationTermKind.J]
    j_total = clamp01(sum(j_values) / max(1, len(j_values)))

    residue_pressure = clamp01(result.surface_solution.local_j.get("J_residue", 0.0))
    source_pressure = 1.0 if global_result.immune_signal.source_confusion else clamp01(result.surface_solution.local_j.get("J_source_phrase", 0.0))
    consent_pressure = 1.0 if global_result.immune_signal.consent_bypass_attempt else clamp01(result.surface_solution.local_j.get("J_imperative_force", 0.0))
    closure_pressure = clamp01((source_pressure + consent_pressure + residue_pressure) / 3.0)

    return SentenceEquation(
        equation_id="sent_eq_" + result.surface_solution.equation_id,
        language_id=result.language_id,
        text=result.text,
        tokens=list(result.segments.tokens),
        terms=terms,
        expression=_expression_from_terms(terms),
        meaning_equation=meaning,
        global_result=global_result,
        j_total=round(j_total, 6),
        closure_pressure=round(closure_pressure, 6),
        residue_pressure=round(residue_pressure, 6),
        source_pressure=round(source_pressure, 6),
        consent_pressure=round(consent_pressure, 6),
        canon_allowed=False,
        source_promotion_allowed=False,
        noema_writeback_allowed=False,
        current_update_allowed=False,
        notes=[
            "Sentence equation is computed from regional SurfaceSolution and GLOBAL v0.2.",
            "No SOURCE/canon promotion; no NOEMA writeback; no runtime execution.",
        ],
    )
