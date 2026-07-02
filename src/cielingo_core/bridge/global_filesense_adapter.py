"""GLOBAL execution through FileSense surface.

Pipeline:
  query
  -> FileSense card search
  -> operator extraction from runtime cards
  -> MeaningEquation construction
  -> GLOBAL v0.2 evaluation
  -> FileSenseGlobalResult

This is not regional parsing. It is a fast evidence/card retrieval layer that
feeds GLOBAL candidate evaluation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from cielingo_core.global_layer.contracts import (
    MeaningEquation,
    SourceBindingType,
    UniversalOperator,
    UniversalOperatorType,
    UniversalRole,
)
from cielingo_core.global_layer.global_algorithm_v02 import GlobalAlgorithmV02Result, run_global_algorithm_v02
from .filesense_surface import FileSenseReport, FileSenseSurface


OPERATOR_TO_UNIVERSAL = {
    "QUESTION": UniversalOperatorType.QUESTION,
    "ACTION_REQUEST": UniversalOperatorType.ACTION_REQUEST,
    "SOURCE_REQUIRED": UniversalOperatorType.SOURCE_REQUIRED,
    "NEGATION": UniversalOperatorType.NEGATION,
    "PREFERENCE": UniversalOperatorType.UNCERTAINTY,  # affective operator, not yet a native UniversalOperatorType
}


@dataclass
class FileSenseGlobalResult:
    query: str
    card_candidates: list[dict[str, Any]]
    equation: MeaningEquation
    global_result: GlobalAlgorithmV02Result
    filesense_report: FileSenseReport
    noema_writeback_performed: bool = False
    current_update_performed: bool = False
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "card_candidates": self.card_candidates,
            "equation": self.equation.to_dict(),
            "global_result": self.global_result.to_dict(),
            "filesense_report": self.filesense_report.to_dict(),
            "noema_writeback_performed": self.noema_writeback_performed,
            "current_update_performed": self.current_update_performed,
            "notes": self.notes,
        }


def operators_from_cards(cards: list[dict[str, Any]]) -> list[str]:
    ops: list[str] = []
    for card in cards:
        runtime = card.get("runtime", {}) or {}
        for op in runtime.get("operator_bindings", []) or []:
            if op not in ops:
                ops.append(op)
    return ops


def slots_from_cards(cards: list[dict[str, Any]]) -> list[int]:
    slots: list[int] = []
    for card in cards:
        slot_id = card.get("slot_id")
        if isinstance(slot_id, int) and slot_id not in slots:
            slots.append(slot_id)
    return slots


def build_equation_from_filesense(query: str, cards: list[dict[str, Any]]) -> MeaningEquation:
    slots = slots_from_cards(cards)
    ops = operators_from_cards(cards)

    universal_ops: list[UniversalOperator] = []
    for op in ops:
        u = OPERATOR_TO_UNIVERSAL.get(op)
        if u is not None:
            universal_ops.append(UniversalOperator(operator_type=u, scope=["filesense_candidate"], strength=0.75))

    # Defensive defaults: if a source card is matched, block canon until proof.
    if "SOURCE_REQUIRED" in ops:
        universal_ops.append(UniversalOperator(operator_type=UniversalOperatorType.CANON_BLOCK, scope=["source"], strength=1.0))

    predicate_slot = slots[0] if slots else None
    roles: dict[UniversalRole, int | list[int] | str] = {}
    if slots:
        roles[UniversalRole.CLAIM] = slots if len(slots) > 1 else slots[0]
    else:
        roles[UniversalRole.CLAIM] = "unresolved_query"

    return MeaningEquation(
        equation_id="eq_filesense_" + str(abs(hash(query)) % 10_000_000),
        predicate_slot=predicate_slot,
        roles=roles,
        operators=universal_ops,
        source_binding=SourceBindingType.HYPOTHESIS,
        canon_allowed=False,
        pragmatics={"filesense_candidate": 0.6},
    )


def run_filesense_global(query: str, root: str | Path) -> FileSenseGlobalResult:
    surface = FileSenseSurface(root)
    cards = surface.search_cards(query)
    report = surface.search(query, max_hits=25, globs=["*.jsonl", "*.md", "*.py"])
    equation = build_equation_from_filesense(query, cards)
    global_result = run_global_algorithm_v02(equation)
    return FileSenseGlobalResult(
        query=query,
        card_candidates=cards[:10],
        equation=equation,
        global_result=global_result,
        filesense_report=report,
        notes=[
            "FileSense used as fast grep/index layer.",
            "No NOEMA writeback or CURRENT update performed.",
            "Result is GLOBAL candidate evaluation, not SOURCE.",
        ],
    )
