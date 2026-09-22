"""Experimental CIELingo genomic grammar primitives.

This module is a computational representation for testing a biological
hypothesis. It does not assert that the hierarchy is a biological identity.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from math import isfinite, tau
from typing import Any, Mapping

SCHEMA = "CIELINGO_GENOMIC_GRAMMAR_V0_1"
DEFAULT_HELICAL_PERIOD_BP = 10.5


class GenomicTier(str, Enum):
    KAKU = "KAKU"
    RADICAL = "RADYKAŁ"
    CONCEPT = "KONCEPT"
    SENTENCE = "ZDANIE"
    PARAGRAPH = "AKAPIT"
    CHAPTER = "ROZDZIAŁ"
    BOOK = "KSIĄŻKA"


class EvidenceClass(str, Enum):
    OBSERVED = "OBSERVED"
    DERIVED = "DERIVED"
    HYPOTHESIS = "HYPOTHESIS"


TIER_ORDER = tuple(GenomicTier)


@dataclass(frozen=True)
class GenomicNode:
    node_id: str
    tier: GenomicTier
    label: str
    start_bp: int | None = None
    end_bp: int | None = None
    evidence: EvidenceClass = EvidenceClass.HYPOTHESIS
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.node_id.strip():
            raise ValueError("node_id must be non-empty")
        if not self.label.strip():
            raise ValueError("label must be non-empty")
        if (self.start_bp is None) != (self.end_bp is None):
            raise ValueError("start_bp and end_bp must be supplied together")
        if self.start_bp is not None and (self.start_bp < 0 or self.end_bp < self.start_bp):
            raise ValueError("invalid genomic interval")

    def to_dict(self) -> dict[str, Any]:
        return {
            "node_id": self.node_id,
            "tier": self.tier.value,
            "label": self.label,
            "start_bp": self.start_bp,
            "end_bp": self.end_bp,
            "evidence": self.evidence.value,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class GenomicRelation:
    source_id: str
    target_id: str
    relation_type: str = "spacing_phase"
    spacing_bp: float | None = None
    orientation: str = "unknown"
    helical_period_bp: float = DEFAULT_HELICAL_PERIOD_BP
    evidence: EvidenceClass = EvidenceClass.HYPOTHESIS
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source_id or not self.target_id:
            raise ValueError("relation endpoints must be non-empty")
        if not self.relation_type.strip():
            raise ValueError("relation_type must be non-empty")
        if not isfinite(self.helical_period_bp) or self.helical_period_bp <= 0:
            raise ValueError("helical_period_bp must be finite and > 0")
        if self.spacing_bp is not None and not isfinite(float(self.spacing_bp)):
            raise ValueError("spacing_bp must be finite")

    @property
    def phase_rad(self) -> float | None:
        if self.spacing_bp is None:
            return None
        return (tau * float(self.spacing_bp) / self.helical_period_bp) % tau

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_id": self.source_id,
            "target_id": self.target_id,
            "relation_type": self.relation_type,
            "spacing_bp": self.spacing_bp,
            "orientation": self.orientation,
            "helical_period_bp": self.helical_period_bp,
            "phase_rad": self.phase_rad,
            "evidence": self.evidence.value,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class GenomicGrammarPacket:
    sequence_id: str
    nodes: tuple[GenomicNode, ...]
    relations: tuple[GenomicRelation, ...] = ()
    evidence_refs: tuple[str, ...] = ()
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.sequence_id.strip():
            raise ValueError("sequence_id must be non-empty")
        ids = [n.node_id for n in self.nodes]
        if len(ids) != len(set(ids)):
            raise ValueError("duplicate node_id")
        known = set(ids)
        for rel in self.relations:
            if rel.source_id not in known or rel.target_id not in known:
                raise ValueError("relation endpoint is not present in nodes")

    def to_dict(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "sequence_id": self.sequence_id,
            "nodes": [n.to_dict() for n in self.nodes],
            "relations": [r.to_dict() for r in self.relations],
            "evidence_refs": list(self.evidence_refs),
            "metadata": dict(self.metadata),
            "epistemic_status": "TESTABLE_MODEL_NOT_BIOLOGICAL_IDENTITY",
        }

    def to_gremlin_task(self) -> dict[str, Any]:
        return {
            "schema": "CIELINGO_GREMLIN_GENOMIC_TASK_V0_1",
            "source": self.to_dict(),
            "hypothesis": (
                "Regulatory information may depend on relational geometry, spacing, "
                "orientation and helical phase in addition to nucleotide symbols."
            ),
            "hierarchy": [tier.value for tier in TIER_ORDER],
            "objectives": [
                "build_relation_graph",
                "separate_observation_derivation_hypothesis",
                "search_counterexamples",
                "derive_falsifiable_phase_predictions",
                "design_ablation_against_sequence_only_baseline",
            ],
            "guardrails": {
                "claim_biological_identity": False,
                "claim_phase_code_proven": False,
                "require_provenance": True,
                "prefer_falsification": True,
            },
        }
