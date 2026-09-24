from __future__ import annotations

from math import pi

import pytest

from cielingo_core.genomic import (
    GenomicLevel,
    GenomicNode,
    GenomicRelation,
    Orientation,
    helical_phase,
    hierarchy_manifest,
)


def test_helical_phase_wraps_one_turn() -> None:
    assert helical_phase(21, 10.5) == pytest.approx(0.0)
    assert helical_phase(5, 10.0) == pytest.approx(pi)


def test_relation_separates_anchor_distance_from_empty_gap() -> None:
    relation = GenomicRelation(
        distance_bp=10,
        gap_bp=6,
        orientation=Orientation.FORWARD,
        bp_per_turn=10.0,
        chromatin_context="accessible",
    )
    encoded = relation.to_dict()
    assert encoded["gap_bp"] == 6
    assert encoded["delta_phase_rad"] == pytest.approx(0.0)


def test_kaku_to_radical_relation_is_explicit() -> None:
    left = GenomicNode("k1", GenomicLevel.KAKU, {"base": "A", "position": 100})
    right = GenomicNode("k2", GenomicLevel.KAKU, {"base": "G", "position": 105})
    relation = GenomicRelation(
        distance_bp=5,
        gap_bp=4,
        orientation=Orientation.FORWARD,
        bp_per_turn=10.0,
        chromatin_context="accessible",
    )
    radical = GenomicNode(
        "r1",
        GenomicLevel.RADICAL,
        {"motif": "example"},
        children=(left, right),
        relations=(relation,),
    )

    encoded = radical.to_dict()
    assert encoded["level"] == "RADYKAŁ"
    assert encoded["relations"][0]["delta_phase_rad"] == pytest.approx(pi)


def test_hierarchy_rejects_skipped_levels() -> None:
    kaku = GenomicNode("k1", GenomicLevel.KAKU)
    with pytest.raises(ValueError, match="children must be RADYKAŁ"):
        GenomicNode("c1", GenomicLevel.CONCEPT, children=(kaku,))


def test_relations_cover_adjacent_children() -> None:
    k1 = GenomicNode("k1", GenomicLevel.KAKU)
    k2 = GenomicNode("k2", GenomicLevel.KAKU)
    k3 = GenomicNode("k3", GenomicLevel.KAKU)
    with pytest.raises(ValueError, match="relations must describe every adjacent child pair"):
        GenomicNode(
            "r1",
            GenomicLevel.RADICAL,
            children=(k1, k2, k3),
            relations=(GenomicRelation(1),),
        )


def test_manifest_names_the_full_cielingo_hierarchy() -> None:
    manifest = hierarchy_manifest()
    assert manifest["levels"] == [
        "KAKU",
        "RADYKAŁ",
        "KONCEPT",
        "ZDANIE",
        "AKAPIT",
        "ROZDZIAŁ",
        "KSIĄŻKA",
    ]
    assert manifest["phase_distance_semantics"] == "ANCHOR_TO_ANCHOR"
    assert manifest["epistemic_status"] == "COMPUTATIONAL_HYPOTHESIS_REPRESENTATION"
