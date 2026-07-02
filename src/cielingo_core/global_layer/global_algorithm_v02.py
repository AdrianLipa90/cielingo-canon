"""CIELingo GLOBAL v0.2 algorithm.

Pipeline:
  MeaningEquation
  -> operator extraction
  -> MeaningAction[]
  -> MeaningBlockAction
  -> SemanticScar[]
  -> MeaningLoop
  -> SemanticImmuneSignal
  -> enriched algorithm result

This algorithm still does not parse regional grammar.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .contracts import MeaningEquation, UniversalOperatorType
from .operator_algebra import DEFAULT_OPERATORS, get_default_operator
from .meaning_action import MeaningAction, MeaningBlockAction, action_from_operator
from .meaning_loop import MeaningLoop, LoopState, evaluate_loop_state, attach_scar
from .semantic_scar import SemanticScar, ScarType
from .semantic_immune_signal import SemanticImmuneSignal, PressureType


@dataclass
class GlobalAlgorithmV02Result:
    equation_id: str
    actions: list[MeaningAction]
    block_action: MeaningBlockAction
    scars: list[SemanticScar]
    loop: MeaningLoop
    immune_signal: SemanticImmuneSignal
    card_migration_required: bool = True
    notes: list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        issues: list[str] = []
        for action in self.actions:
            issues.extend(action.validate())
        issues.extend(self.block_action.validate())
        for scar in self.scars:
            issues.extend(scar.validate())
        issues.extend(self.loop.validate())
        issues.extend(self.immune_signal.validate())
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


UNIVERSAL_TO_RELATIONAL = {
    UniversalOperatorType.QUESTION: "QUESTION",
    UniversalOperatorType.ACTION_REQUEST: "ACTION_REQUEST",
    UniversalOperatorType.SOURCE_REQUIRED: "SOURCE_REQUIRED",
    UniversalOperatorType.CANON_BLOCK: "SOURCE_REQUIRED",
    UniversalOperatorType.NEGATION: "NEGATION",
    UniversalOperatorType.CONSENT_REQUIRED: "ACTION_REQUEST",
}


def extract_operator_ids(equation: MeaningEquation) -> list[str]:
    ids: list[str] = []
    for op in equation.operators:
        mapped = UNIVERSAL_TO_RELATIONAL.get(op.operator_type)
        if mapped and mapped not in ids:
            ids.append(mapped)
    return ids


def build_actions_from_equation(equation: MeaningEquation) -> list[MeaningAction]:
    actions: list[MeaningAction] = []
    for idx, operator_id in enumerate(extract_operator_ids(equation), start=1):
        op = get_default_operator(operator_id)
        if op is None:
            continue
        slots = []
        if equation.predicate_slot is not None:
            slots.append(equation.predicate_slot)
        for value in equation.roles.values():
            if isinstance(value, int):
                slots.append(value)
            elif isinstance(value, list):
                slots.extend(v for v in value if isinstance(v, int))
        actions.append(action_from_operator(op, action_id=f"{equation.equation_id}:A{idx}", input_slots=slots))
    return actions


def detect_scars(equation: MeaningEquation, block: MeaningBlockAction) -> list[SemanticScar]:
    scars: list[SemanticScar] = []

    if block.total_source_pressure_delta > 0 and block.total_certainty_delta < 0:
        scars.append(SemanticScar(
            scar_id=f"{equation.equation_id}:scar:missing_source",
            scar_type=ScarType.MISSING_SOURCE,
            source_equation_id=equation.equation_id,
            severity=min(1.0, block.total_source_pressure_delta),
            memory_effect="repair_required",
            repair_hint="Provide SOURCE/ACK/log/hash/runtime evidence before closure or canon.",
            notes=["SOURCE_REQUIRED raised source pressure."],
        ))

    if block.total_consent_pressure_delta >= 0.45:
        scars.append(SemanticScar(
            scar_id=f"{equation.equation_id}:scar:consent_pressure",
            scar_type=ScarType.CONSENT_PRESSURE,
            source_equation_id=equation.equation_id,
            severity=min(1.0, block.total_consent_pressure_delta),
            memory_effect="candidate",
            repair_hint="Route through consent gate; do not execute directly.",
            notes=["Action request or consent-required operator detected."],
        ))

    if block.total_residue_delta >= 0.35:
        scars.append(SemanticScar(
            scar_id=f"{equation.equation_id}:scar:scope_residue",
            scar_type=ScarType.TRANSLATION_RESIDUE,
            source_equation_id=equation.equation_id,
            severity=min(1.0, block.total_residue_delta),
            memory_effect="candidate",
            repair_hint="Resolve scope/negation/operator attachment.",
            notes=["Residue delta exceeded threshold."],
        ))

    return scars


def build_immune_signal(scars: list[SemanticScar], block: MeaningBlockAction) -> SemanticImmuneSignal:
    source_confusion = any(s.scar_type == ScarType.MISSING_SOURCE for s in scars)
    consent_pressure = any(s.scar_type == ScarType.CONSENT_PRESSURE for s in scars)
    canon_attempt = source_confusion and block.total_source_pressure_delta > 0.0

    if source_confusion:
        return SemanticImmuneSignal(
            pressure_detected=True,
            pressure_type=PressureType.SOURCE_CONFUSION,
            source_confusion=True,
            canon_promotion_attempt=canon_attempt,
            consent_bypass_attempt=False,
            hallucinated_authority_risk=0.55,
            recommended_consent_state="NEEDS_PROOF",
            notes=["Source pressure without evidence creates immune warning."],
        )
    if consent_pressure:
        return SemanticImmuneSignal(
            pressure_detected=True,
            pressure_type=PressureType.CONSENT_BYPASS,
            source_confusion=False,
            canon_promotion_attempt=False,
            consent_bypass_attempt=True,
            hallucinated_authority_risk=0.15,
            recommended_consent_state="NEEDS_CONTEXT",
            notes=["Action request requires consent routing."],
        )
    return SemanticImmuneSignal(notes=["No immune pressure detected."])


def run_global_algorithm_v02(equation: MeaningEquation) -> GlobalAlgorithmV02Result:
    actions = build_actions_from_equation(equation)
    block = MeaningBlockAction(
        block_id=f"{equation.equation_id}:block",
        actions=actions,
        closes_loop=bool(actions) and all(a.residue_delta <= 0.2 for a in actions),
        notes=["Block action is the sum of local meaning actions."],
    )
    scars = detect_scars(equation, block)
    loop = MeaningLoop(
        loop_id=f"{equation.equation_id}:loop",
        input_equation_id=equation.equation_id,
        response_equation_id=None,
        closure_score=0.25 if scars else 0.55,
        contradiction_score=0.0,
        return_required=True,
        scars=[],
        notes=["Loop opened by equation."],
    )
    for scar in scars:
        loop = attach_scar(loop, scar)
    loop.loop_state = evaluate_loop_state(loop)
    immune = build_immune_signal(scars, block)
    return GlobalAlgorithmV02Result(
        equation_id=equation.equation_id,
        actions=actions,
        block_action=block,
        scars=scars,
        loop=loop,
        immune_signal=immune,
        notes=[
            "GLOBAL v0.2 is contract/evaluator only.",
            "Regional grammar and NOEMA writeback are not performed.",
        ],
    )
