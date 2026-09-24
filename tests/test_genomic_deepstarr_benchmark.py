from __future__ import annotations

import pytest

from cielingo_core.genomics import (
    DeepStarrActivity,
    DeepStarrSample,
    DeepStarrSplit,
    DeepStarrTarget,
    GenomicGrammarProject,
    GenomicGrammarProjectConfig,
    MotifDefinition,
    SequenceRecord,
    run_deepstarr_regression_ablation,
)


def _sample(
    sample_id,
    sequence,
    dev,
    hk,
    split,
):
    return DeepStarrSample(
        sample_id=sample_id,
        sequence=SequenceRecord(sample_id, sequence),
        activity=DeepStarrActivity(dev, hk),
        split=split,
        row_index=0,
    )


def _project():
    return GenomicGrammarProject(
        GenomicGrammarProjectConfig(
            motifs=(
                MotifDefinition("A3", "AAA", False),
                MotifDefinition("C3", "CCC", False),
            ),
            max_relation_distance_bp=30.0,
        )
    )


def test_deepstarr_regression_keeps_test_split_held_out():
    train = [
        _sample(
            "tr1",
            "AAACCCAAAA",
            0.1,
            0.2,
            DeepStarrSplit.TRAIN,
        ),
        _sample(
            "tr2",
            "AAATCCCAAA",
            0.3,
            0.4,
            DeepStarrSplit.TRAIN,
        ),
        _sample(
            "tr3",
            "AAATTTCCC",
            0.8,
            0.7,
            DeepStarrSplit.VAL,
        ),
        _sample(
            "tr4",
            "AAATTTTCCC",
            1.0,
            0.9,
            DeepStarrSplit.VAL,
        ),
    ]
    test = [
        _sample(
            "te1",
            "AAATTTTTCCC",
            1.2,
            1.0,
            DeepStarrSplit.TEST,
        ),
        _sample(
            "te2",
            "AAATTTTTTCCC",
            1.4,
            1.1,
            DeepStarrSplit.TEST,
        ),
        _sample(
            "te3",
            "AAATTTTTTTCCC",
            1.6,
            1.2,
            DeepStarrSplit.TEST,
        ),
    ]

    result = run_deepstarr_regression_ablation(
        train,
        test,
        _project(),
        target=DeepStarrTarget.DEV,
        alpha=0.1,
    )

    assert set(result["results"]) == {
        "sequence_only",
        "sequence_plus_geometry",
        "sequence_plus_phase",
    }
    assert result["target"] == "Dev_log2_enrichment"
    assert result["canon_allowed"] is False
    assert result["claim_scope"].startswith(
        "held-out predictive diagnostic"
    )


def test_deepstarr_regression_rejects_test_leakage_into_fit():
    leaked = [
        _sample(
            "x",
            "AAACCC",
            1.0,
            1.0,
            DeepStarrSplit.TEST,
        )
    ]
    with pytest.raises(
        ValueError,
        match="cannot be used for fitting",
    ):
        run_deepstarr_regression_ablation(
            leaked,
            leaked,
            _project(),
            target=DeepStarrTarget.HK,
        )
