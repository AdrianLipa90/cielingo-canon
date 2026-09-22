from __future__ import annotations

import pytest

from cielingo_core.genomic import (
    GenomicLevel,
    Orientation,
    SequenceFeature,
    compose_level,
    concept_from_features,
    radical_from_feature,
)


def test_feature_compiles_to_radical_and_kaku_sequence() -> None:
    feature = SequenceFeature("motif-a", "ACGT", 100, Orientation.FORWARD)
    radical = radical_from_feature(feature, bp_per_turn=10.0)

    assert radical.level is GenomicLevel.RADICAL
    assert [node.payload["base"] for node in radical.children] == list("ACGT")
    assert [node.payload["position_bp"] for node in radical.children] == [100, 101, 102, 103]
    assert len(radical.relations) == 3
    assert radical.payload["end_bp"] == 104


def test_feature_accepts_iupac_and_rejects_non_dna_symbols() -> None:
    feature = SequenceFeature("ambiguous", "ARYN", 0)
    assert feature.sequence == "ARYN"
    with pytest.raises(ValueError, match="unsupported IUPAC"):
        SequenceFeature("bad", "ACGTZ", 0)


def test_features_compile_to_concept_with_explicit_spacing() -> None:
    left = SequenceFeature("left", "ACGT", 100, Orientation.FORWARD)
    right = SequenceFeature("right", "TATA", 110, Orientation.REVERSE)
    concept = concept_from_features("concept-1", [right, left], bp_per_turn=10.0)

    assert concept.level is GenomicLevel.CONCEPT
    assert [child.node_id for child in concept.children] == ["left", "right"]
    relation = concept.relations[0]
    assert relation.distance_bp == 6
    assert relation.metadata["left_orientation"] == "+"
    assert relation.metadata["right_orientation"] == "-"


def test_compose_level_builds_next_hierarchy_stage() -> None:
    a = concept_from_features("c1", [SequenceFeature("m1", "AAA", 0)])
    b = concept_from_features("c2", [SequenceFeature("m2", "CCC", 20)])
    sentence = compose_level("sentence-1", GenomicLevel.SENTENCE, [b, a])

    assert sentence.level is GenomicLevel.SENTENCE
    assert sentence.payload["start_bp"] == 0
    assert sentence.payload["end_bp"] == 23
    assert sentence.relations[0].distance_bp == 17
