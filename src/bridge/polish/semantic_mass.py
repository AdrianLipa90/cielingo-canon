"""Semantic mass utilities for Polish CIELingo cards."""
from __future__ import annotations

from typing import Any
import math

from .linguistic_database import PolishLinguisticDatabase


def semantic_mass_scalar(mass: dict[str, float]) -> float:
    if not mass:
        return 0.0
    vals = [max(0.0, min(1.0, float(v))) for v in mass.values()]
    return float(sum(vals) / len(vals))


def utterance_semantic_mass(tokens: list[str], db: PolishLinguisticDatabase) -> dict[str, Any]:
    rows = []
    for tok in tokens:
        mass = db.semantic_mass(tok)
        rows.append({"surface": tok, "mass": mass, "scalar": semantic_mass_scalar(mass)})
    if not rows:
        return {"mean": 0.0, "tokens": []}
    return {"mean": float(sum(r["scalar"] for r in rows) / len(rows)), "tokens": rows}


__all__ = ["semantic_mass_scalar", "utterance_semantic_mass"]
