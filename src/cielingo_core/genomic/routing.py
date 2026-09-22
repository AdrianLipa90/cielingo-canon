"""GREMLIN routing requests for CIELingo genomic grammar nodes.

This module asks OCTOPUS to select the appropriate specialists. It does not
hard-code a route mask and does not grant mutation authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .grammar import GenomicLevel, GenomicNode

SCHEMA = "CIELINGO_GENOMIC_GREMLIN_ROUTING_V0_1"

_REQUIREMENTS: dict[GenomicLevel, tuple[str, ...]] = {
    GenomicLevel.KAKU: (
        "local symbol integrity",
        "position and phase consistency",
        "anomaly detection",
    ),
    GenomicLevel.RADICAL: (
        "motif structure",
        "local relation pattern",
        "similarity and contradiction scan",
    ),
    GenomicLevel.CONCEPT: (
        "spacing and orientation relations",
        "helical phase pattern",
        "dependency and contradiction audit",
    ),
    GenomicLevel.SENTENCE: (
        "regulatory-module hypothesis",
        "derivation and falsifiable test targets",
        "evidence audit",
    ),
    GenomicLevel.PARAGRAPH: (
        "local chromatin context",
        "cross-module dependency and memory comparison",
        "evidence and provenance audit",
    ),
    GenomicLevel.CHAPTER: (
        "domain-scale structure",
        "cross-region relation and duplicate scan",
        "decomposition and validation planning",
    ),
    GenomicLevel.BOOK: (
        "genome-scale synthesis",
        "cross-level consistency",
        "provenance, falsifiability and unresolved-gate audit",
    ),
}


@dataclass(frozen=True)
class GenomicGremlinRequest:
    schema: str
    tool: str
    arguments: dict[str, Any]
    authority: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": self.schema,
            "tool": self.tool,
            "arguments": self.arguments,
            "authority": self.authority,
        }


def analysis_requirements(level: GenomicLevel) -> tuple[str, ...]:
    return _REQUIREMENTS[level]


def build_octopus_request(
    node: GenomicNode,
    *,
    max_species: int = 7,
    min_score: float = 2.0,
    relative_cutoff: float = 0.45,
) -> GenomicGremlinRequest:
    if isinstance(max_species, bool) or not isinstance(max_species, int) or max_species < 1:
        raise ValueError("max_species must be a positive integer")
    requirements = analysis_requirements(node.level)
    query = (
        f"Analyze CIELingo genomic grammar level {node.level.value}. "
        + "; ".join(requirements)
        + ". Keep sequence facts separate from relational/phase hypotheses."
    )
    payload = {
        "query": query,
        "domain": "genomic_grammar",
        "cielingo_level": node.level.value,
        "node_id": node.node_id,
        "analysis_requirements": list(requirements),
        "node": node.to_dict(),
        "epistemic_boundary": {
            "representation_is_hypothesis": True,
            "sequence_only_baseline_required": True,
            "phase_claim_requires_empirical_test": True,
        },
    }
    return GenomicGremlinRequest(
        schema=SCHEMA,
        tool="gremlin_route",
        arguments={
            "payload": payload,
            "max_species": max_species,
            "min_score": float(min_score),
            "relative_cutoff": float(relative_cutoff),
        },
        authority={
            "force_species_route": False,
            "mutation_allowed": False,
            "canon_allowed": False,
            "noema_writeback_allowed": False,
        },
    )


def routing_manifest() -> dict[str, Any]:
    return {
        "schema": SCHEMA,
        "router": "gremlin_route/OCTOPUS",
        "route_policy": "DYNAMIC_AUDITABLE_NO_FORCED_SPECIES",
        "levels": {
            level.value: list(requirements)
            for level, requirements in _REQUIREMENTS.items()
        },
        "authority": {
            "mutation_allowed": False,
            "canon_allowed": False,
            "noema_writeback_allowed": False,
        },
    }
