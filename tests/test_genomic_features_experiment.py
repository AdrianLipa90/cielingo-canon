from __future__ import annotations

from cielingo_core.genomics import (
    LabeledFeatures,
    MotifDefinition,
    SequenceRecord,
    compare_feature_sets,
    leave_one_out_nearest_neighbor,
    parse_genomic_grammar,
    phase_grammar_features,
    representation_feature_sets,
    sequence_kmer_features,
)


def _parsed(sequence: str):
    return parse_genomic_grammar(
        SequenceRecord("r", sequence),
        [
            MotifDefinition("A3", "AAA", False),
            MotifDefinition("C3", "CCC", False),
        ],
        max_relation_distance_bp=40,
    )


def test_feature_sets_keep_baseline_separate_from_phase_channel():
    parsed = _parsed("AAACCCAAAAAACCC")
    feature_sets = representation_feature_sets(parsed, k=2)
    assert set(feature_sets) == {"sequence_only", "sequence_plus_phase"}
    assert set(feature_sets["sequence_only"]) <= set(
        feature_sets["sequence_plus_phase"]
    )

    phase = phase_grammar_features(parsed)
    assert any(key.endswith("phase_cos") for key in phase)
    assert not any(
        "phase_" in key
        for key in sequence_kmer_features(parsed.record.sequence)
    )


def test_spacing_changes_phase_features_for_same_motif_vocabulary():
    first = _parsed("AAACCC")
    second = _parsed("AAA" + "T" * 5 + "CCC")
    assert phase_grammar_features(first) != phase_grammar_features(second)


def test_representation_benchmark_is_diagnostic_and_declares_no_winner():
    baseline = [
        LabeledFeatures("a1", "A", {"x": 0.0}),
        LabeledFeatures("a2", "A", {"x": 0.1}),
        LabeledFeatures("b1", "B", {"x": 10.0}),
        LabeledFeatures("b2", "B", {"x": 10.1}),
    ]
    augmented = [
        LabeledFeatures(
            sample.sample_id,
            sample.label,
            {
                **sample.features,
                "phase": 0.0 if sample.label == "A" else 1.0,
            },
        )
        for sample in baseline
    ]
    result = compare_feature_sets(
        {
            "sequence_only": baseline,
            "sequence_plus_phase": augmented,
        }
    )
    assert result["winner_declared"] is False
    assert (
        result["results"]["sequence_only"]["method"]
        == "LEAVE_ONE_OUT_1NN_DIAGNOSTIC"
    )
    assert leave_one_out_nearest_neighbor(baseline)["n"] == 4
