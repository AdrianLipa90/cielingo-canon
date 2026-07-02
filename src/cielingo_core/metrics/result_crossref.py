from __future__ import annotations
from dataclasses import dataclass
from typing import Iterable, Sequence

SCALE_LEVELS = {"volumetric", "physical", "semantic", "temporal", "holonomic", "runtime", "unclassified"}

@dataclass(frozen=True)
class ResultCrossRefFamily:
    family_id: str
    operator_family: str
    canonical_pointer: str
    members: tuple[str, ...]
    classifications: tuple[str, ...]
    scale_levels: tuple[str, ...]
    max_abs_diff: float
    max_normalized_residue: float
    preserve_branch: bool
    doctor_action: str


def validate_family(family: ResultCrossRefFamily) -> bool:
    if not family.family_id or not family.canonical_pointer or not family.members:
        return False
    if family.canonical_pointer not in family.members:
        # Canonical can point to a preferred analysis file not always member in future registries,
        # but current 1.2AC requires membership for audit safety.
        return False
    if not set(family.scale_levels).issubset(SCALE_LEVELS):
        return False
    if family.max_abs_diff < 0 or family.max_normalized_residue < 0:
        return False
    return True


def should_merge(family: ResultCrossRefFamily) -> bool:
    return family.doctor_action == "merge_exact_duplicates_by_canonical_pointer"


def should_preserve_branch(family: ResultCrossRefFamily) -> bool:
    return family.preserve_branch or "calibrated_variant" in family.classifications


def cross_scale(family: ResultCrossRefFamily) -> bool:
    return len(set(family.scale_levels)) > 1
