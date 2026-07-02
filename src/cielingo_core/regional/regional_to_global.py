from __future__ import annotations
from cielingo_core.global_layer.contracts import MeaningEquation, SourceBindingType, UniversalOperator, UniversalOperatorType, UniversalRole
from cielingo_core.regional.base import RegionalSolveResult

OPERATOR_TO_UNIVERSAL = {
    "QUESTION": UniversalOperatorType.QUESTION,
    "ACTION_REQUEST": UniversalOperatorType.ACTION_REQUEST,
    "SOURCE_REQUIRED": UniversalOperatorType.SOURCE_REQUIRED,
    "NEGATION": UniversalOperatorType.NEGATION,
}

def regional_result_to_meaning_equation(result: RegionalSolveResult) -> MeaningEquation:
    operator_ids = []
    for c in result.candidates:
        for op in c.operator_bindings:
            if op not in operator_ids:
                operator_ids.append(op)
    ops = [UniversalOperator(operator_type=OPERATOR_TO_UNIVERSAL[o], scope=["regional_candidate"], strength=0.70)
           for o in operator_ids if o in OPERATOR_TO_UNIVERSAL]
    if "SOURCE_REQUIRED" in operator_ids:
        ops.append(UniversalOperator(operator_type=UniversalOperatorType.CANON_BLOCK, scope=["source"], strength=1.0))
    slots = sorted(result.surface_solution.slot_projection)
    return MeaningEquation(
        equation_id="eq_from_" + result.surface_solution.equation_id,
        predicate_slot=slots[0] if slots else None,
        roles={UniversalRole.CLAIM: slots if slots else "unresolved_surface"},
        operators=ops,
        source_binding=SourceBindingType.HYPOTHESIS,
        canon_allowed=False,
        pragmatics={"regional_candidate": 0.60},
    )
