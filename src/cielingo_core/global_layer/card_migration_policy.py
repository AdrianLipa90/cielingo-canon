"""Card migration policy for CIELingo GLOBAL v0.2.

Existing cards do not need to be destroyed. They need an additive runtime
extension so a word/card can act as a semantic operator, not only a lexical
entry.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


REQUIRED_RUNTIME_FIELDS = {
    "operator_bindings": "Which global operators this card can realize.",
    "semantic_mass": "Magnitude of semantic contribution.",
    "affective_charge": "Valence/intensity effect.",
    "consent_effect": "Whether card can request/block/require consent.",
    "memory_effect": "Whether card requests memory/scar/snap candidate.",
    "risk_profile": "Semantic/hallucination/consent risk.",
    "residue_profile": "Expected residue categories and weights.",
}


@dataclass
class CardMigrationDecision:
    required: bool
    reason: str
    additive_only: bool = True
    required_fields: dict[str, str] = field(default_factory=lambda: dict(REQUIRED_RUNTIME_FIELDS))
    forbidden_changes: list[str] = field(default_factory=lambda: [
        "do not delete existing slot_id",
        "do not merge language-local cards into global cards",
        "do not set SOURCE by default",
        "do not set canon_allowed by default",
        "do not overwrite native-review flags",
    ])

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def recommend_card_migration() -> CardMigrationDecision:
    return CardMigrationDecision(
        required=True,
        reason=(
            "GLOBAL v0.2 introduces MeaningAction, MeaningLoop and SemanticScar. "
            "Cards must therefore expose runtime/operator effects, not only lexical surface data."
        ),
    )
