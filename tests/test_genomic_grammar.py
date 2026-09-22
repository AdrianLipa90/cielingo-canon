from __future__ import annotations

import math

import pytest

from cielingo_core.genomics import (
    GenomicLevel,
    GenomicUnit,
    HelicalPhaseModel,
    assemble_unit,
    relation_from_positions,
)


def test_phase_periodicity_tracks_configured_helical_repeat():
    model = HelicalPhaseModel(10.5)
    assert model.relative_phase(0.0, 10.5) == pytest.approx(0.0, abs=1e-12)
    assert model.relative_phase(0.0, 5.25) == pytest.approx(math.pi, abs=1e-12)


def test_strict_hierarchy_kaku_to_radical_to_concept():
    k1 = GenomicUnit("k1", GenomicLevel.KAKU, {"symbol": "A", "position_bp": 0})
    k2 = GenomicUnit("k2", GenomicLevel.KAKU, {"symbol": "T", "position_bp": 5.25})
    relation = relation_from_positions("k1", "k2", 0.0, 5.25, orientation="same")
    radical = assemble_unit("r1", GenomicLevel.RADICAL, [k1, k2], relations=[relation])
    concept = assemble_unit("c1", GenomicLevel.CONCEPT, [radical])
    assert concept.children[0].children[0].level is GenomicLevel.KAKU
    assert relation.relative_phase_rad == pytest.approx(math.pi, abs=1e-12)


def test_skipped_hierarchy_level_is_rejected():
    kaku = GenomicUnit("k", GenomicLevel.KAKU)
    with pytest.raises(ValueError, match="RADICAL"):
        assemble_unit("c", GenomicLevel.CONCEPT, [kaku])


def test_signature_is_deterministic_and_relationally_sensitive():
    k1 = GenomicUnit("k1", GenomicLevel.KAKU, {"symbol": "A"})
    k2 = GenomicUnit("k2", GenomicLevel.KAKU, {"symbol": "T"})
    r1 = relation_from_positions("k1", "k2", 0.0, 10.5)
    r2 = relation_from_positions("k1", "k2", 0.0, 5.25)
    u1 = assemble_unit("r", GenomicLevel.RADICAL, [k1, k2], relations=[r1])
    u2 = assemble_unit("r", GenomicLevel.RADICAL, [k1, k2], relations=[r2])
    assert u1.semantic_signature() == u1.semantic_signature()
    assert u1.semantic_signature() != u2.semantic_signature()
    assert u1.to_dict()["biological_equivalence_claim"] is False
