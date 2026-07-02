"""Polish linguistic holonomies for CIELingo."""
from __future__ import annotations

from typing import Any


def word_order_holonomy(tokens: list[dict[str, Any]]) -> dict[str, Any]:
    """Estimate whether Polish case marking preserves roles under word-order shifts."""
    nouns = [t for t in tokens if t.get("pos") == "noun"]
    has_cases = all(t.get("case") for t in nouns)
    subject = [t for t in tokens if t.get("sentence_part") == "subject"]
    obj = [t for t in tokens if t.get("sentence_part") == "object"]
    return {
        "operator": "word_order_holonomy",
        "case_marking_present": bool(has_cases),
        "subject_count": len(subject),
        "object_count": len(obj),
        "meaning_preservation_candidate": bool(has_cases and subject and obj),
        "focus_change_expected": True,
    }


def negation_holonomy(tokens: list[dict[str, Any]]) -> dict[str, Any]:
    negated = any(t.get("operator") == "negation" for t in tokens)
    return {
        "operator": "negation_holonomy",
        "negated": negated,
        "phase_inversion": 1.0 if negated else 0.0,
        "scope_requires_resolution": negated,
    }


def punctuation_holonomy(tokens: list[dict[str, Any]]) -> dict[str, Any]:
    marks = [t["surface"] for t in tokens if t.get("pos") == "punctuation"]
    closure = "." in marks or "!" in marks or "?" in marks
    open_loop = "…" in marks
    return {
        "operator": "punctuation_holonomy",
        "marks": marks,
        "cycle_closed": closure and not open_loop,
        "open_loop": open_loop,
    }


def compute_holonomy_report(analysis: dict[str, Any]) -> dict[str, Any]:
    tokens = analysis.get("tokens", [])
    reports = [word_order_holonomy(tokens), negation_holonomy(tokens), punctuation_holonomy(tokens)]
    preservation = sum(1 for r in reports if r.get("meaning_preservation_candidate") or r.get("cycle_closed") or not r.get("scope_requires_resolution", False)) / len(reports)
    return {
        "schema": "cielingo/polish-holonomy-report/v0.1",
        "reports": reports,
        "holonomy_preservation_score": float(preservation),
    }


__all__ = ["word_order_holonomy", "negation_holonomy", "punctuation_holonomy", "compute_holonomy_report"]
