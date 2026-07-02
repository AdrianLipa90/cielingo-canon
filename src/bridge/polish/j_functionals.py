"""Language J-functionals for Polish CIELingo runtime."""
from __future__ import annotations

import math
from typing import Any

from .grammar_algorithms import analyze_polish_sentence
from .holonomies import compute_holonomy_report

KAPPA_INFO = math.log(2.0) / (24.0 * math.pi)


def _bounded_penalty(x: float) -> float:
    return max(0.0, min(1.0, float(x)))


def compute_language_j_functional(text: str, repo_root: str = ".") -> dict[str, Any]:
    """Compute a diagnostic Polish-language J-functional.

    Status: fallback diagnostic. Components are normalized penalties; the final
    J is a mean component penalty modulated by κ_info = ln(2)/(24π), so the
    raw score remains inspectable and the formal constant is not hidden.
    """
    analysis = analyze_polish_sentence(text, repo_root=repo_root)
    hol = compute_holonomy_report(analysis)

    unresolved_penalty = len(analysis["unresolved_tokens"]) / max(1, len(analysis["tokens"]))
    valency_penalty = 0.0 if analysis["valency"]["status"] == "PASS" else 1.0
    grammar_penalty = 0.0 if analysis["grammar_status"] == "PASS" else 0.75
    semantic_mass_mean = float(analysis["semantic_mass"]["mean"])
    semantic_mass_cost = 1.0 - semantic_mass_mean
    holonomy_cost = 1.0 - float(hol["holonomy_preservation_score"])
    punctuation_cost = 0.0 if any(t.get("pos") == "punctuation" for t in analysis["tokens"]) else 0.15

    components = {
        "unresolved_penalty": _bounded_penalty(unresolved_penalty),
        "valency_penalty": _bounded_penalty(valency_penalty),
        "grammar_penalty": _bounded_penalty(grammar_penalty),
        "semantic_mass_cost": _bounded_penalty(semantic_mass_cost),
        "holonomy_cost": _bounded_penalty(holonomy_cost),
        "punctuation_cost": _bounded_penalty(punctuation_cost),
    }
    raw_mean = sum(components.values()) / len(components)
    j_language = raw_mean * (1.0 + KAPPA_INFO)
    return {
        "schema": "cielingo/polish-language-j-functional/v0.1",
        "text": text,
        "kappa_info": KAPPA_INFO,
        "components": components,
        "raw_mean_penalty": raw_mean,
        "J_language": j_language,
        "analysis": analysis,
        "holonomy": hol,
        "status": "PASS" if j_language < 0.55 and analysis["grammar_status"] == "PASS" else "REVIEW",
        "epistemic_boundary": {
            "fallback_diagnostic": True,
            "not_full_polish_parser": True,
            "requires_human_linguistic_review_for_canon": True,
        },
    }


__all__ = ["KAPPA_INFO", "compute_language_j_functional"]
