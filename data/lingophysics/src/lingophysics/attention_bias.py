from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
import json

try:
    import yaml
except Exception:  # pragma: no cover
    yaml = None

from .transformer_features import FeatureToken


def load_bias_rules(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    text = p.read_text(encoding="utf-8")
    if p.suffix.lower() in {".yaml", ".yml"}:
        if yaml is None:
            raise RuntimeError("PyYAML is required for YAML bias rules.")
        return yaml.safe_load(text)
    return json.loads(text)


def operator_argument_link(a: FeatureToken, b: FeatureToken) -> bool:
    return (a.card_type == "OPERATOR_CARD" and b.card_type == "CONCEPT_CARD") or (b.card_type == "OPERATOR_CARD" and a.card_type == "CONCEPT_CARD")


def case_role_link(a: FeatureToken, b: FeatureToken) -> bool:
    return bool(a.features.get("case_gauge") or b.features.get("case_gauge")) and bool(set(a.roles) | set(b.roles))


def phase_compatible(a: FeatureToken, b: FeatureToken) -> bool:
    return not (a.features.get("phase_conflict") or b.features.get("phase_conflict"))


def pair_bias_components(a: FeatureToken, b: FeatureToken, rules: Dict[str, Any]) -> Dict[str, float]:
    """Return the additive CIEL bias terms for one token pair.

    The decomposition preserves v1.9 ``pair_bias`` semantics while exposing
    the common ``phase_compatibility`` term separately from typed relational
    evidence. It is a diagnostic/experimental interface; existing pair-bias
    behavior remains unchanged.
    """
    if a.token_id == b.token_id:
        return {
            "operator_argument_link": 0.0,
            "same_event_frame": 0.0,
            "case_role_link": 0.0,
            "phase_compatibility": 0.0,
            "conflict_penalty": 0.0,
        }

    w = rules["weights"]
    compatible = phase_compatible(a, b)
    components = {
        "operator_argument_link": float(w.get("operator_argument_link", 0.0)) if operator_argument_link(a, b) else 0.0,
        "same_event_frame": float(w.get("same_event_frame", 0.0)) if set(a.roles) & set(b.roles) else 0.0,
        "case_role_link": float(w.get("case_role_link", 0.0)) if case_role_link(a, b) else 0.0,
        "phase_compatibility": float(w.get("phase_compatibility", 0.0)) if compatible else 0.0,
        "conflict_penalty": -float(w.get("conflict_penalty", 0.0)) if not compatible else 0.0,
    }
    return {key: round(value, 6) for key, value in components.items()}


def pair_bias(a: FeatureToken, b: FeatureToken, rules: Dict[str, Any]) -> float:
    return round(sum(pair_bias_components(a, b, rules).values()), 6)


def pair_relation_excess_bias(a: FeatureToken, b: FeatureToken, rules: Dict[str, Any]) -> float:
    """Return typed relation/conflict excess without the common phase term.

    This function does not replace :func:`pair_bias`. It exposes an explicit
    relation-only diagnostic channel for controlled downstream experiments.
    Pair-specific conflict penalties are retained.
    """
    components = pair_bias_components(a, b, rules)
    return round(
        sum(value for key, value in components.items() if key != "phase_compatibility"),
        6,
    )


def build_attention_bias_matrix(tokens: List[FeatureToken], rules: Dict[str, Any]) -> List[List[float]]:
    return [[pair_bias(a, b, rules) for b in tokens] for a in tokens]


def has_positive_structural_bias(matrix: List[List[float]]) -> bool:
    return any(cell > 0 for row in matrix for cell in row)


def build_relation_excess_attention_bias_matrix(tokens: List[FeatureToken], rules: Dict[str, Any]) -> List[List[float]]:
    """Build the diagnostic typed-relation/conflict excess matrix."""
    return [[pair_relation_excess_bias(a, b, rules) for b in tokens] for a in tokens]
