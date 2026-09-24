from __future__ import annotations

import pytest

from cielingo_core.genomics import (
    GenomicGrammarProject,
    GenomicGrammarProjectConfig,
    MotifDefinition,
)


def _project() -> GenomicGrammarProject:
    return GenomicGrammarProject(
        GenomicGrammarProjectConfig(
            motifs=(
                MotifDefinition("A3", "AAA", False),
                MotifDefinition("C3", "CCC", False),
            ),
            max_relation_distance_bp=30.0,
        )
    )


def test_project_compiles_multirecord_fasta_into_three_ablation_surfaces():
    samples = _project().compile_fasta(
        ">a\nAAACCC\n>b\nAAATTTTTCCC"
    )
    assert len(samples) == 2
    assert set(samples[0].feature_sets) == {
        "sequence_only",
        "sequence_plus_geometry",
        "sequence_plus_phase",
    }
    assert samples[0].analysis_unit().payload["motif_hit_count"] >= 2


def test_project_requires_exact_labels_and_never_promotes_canon():
    project = _project()
    samples = project.compile_fasta(
        ">a1\nAAACCC\n"
        ">a2\nAAATCCC\n"
        ">b1\nAAATTTTTCCC\n"
        ">b2\nAAATTTTTTCCC"
    )

    with pytest.raises(ValueError, match="labels must match"):
        project.evaluate_ablation(samples, {"a1": "A"})

    result = project.evaluate_ablation(
        samples,
        {
            "a1": "A",
            "a2": "A",
            "b1": "B",
            "b2": "B",
        },
    )
    assert result["winner_declared"] is False
    assert (
        result["phase_increment_test"]
        == "sequence_plus_phase vs sequence_plus_geometry"
    )
    assert result["canon_allowed"] is False
