"""Held-out DeepSTARR regression ablation for genomic grammar."""
from __future__ import annotations

from enum import Enum
from typing import Sequence

from .deepstarr import DeepStarrSample, DeepStarrSplit
from .project import GenomicGrammarProject
from .regression import RegressionExample, fit_and_evaluate


class DeepStarrTarget(str, Enum):
    DEV = "Dev_log2_enrichment"
    HK = "Hk_log2_enrichment"


def _target(
    sample: DeepStarrSample,
    target: DeepStarrTarget,
) -> float:
    if target is DeepStarrTarget.DEV:
        return sample.activity.dev_log2_enrichment
    return sample.activity.hk_log2_enrichment


def _compile_feature_sets(
    samples: Sequence[DeepStarrSample],
    project: GenomicGrammarProject,
    target: DeepStarrTarget,
) -> dict[str, list[RegressionExample]]:
    output: dict[str, list[RegressionExample]] = {}
    for sample in samples:
        compiled = project.compile_record(sample.sequence)
        for name, features in compiled.feature_sets.items():
            output.setdefault(name, []).append(
                RegressionExample(
                    sample_id=sample.sample_id,
                    target=_target(sample, target),
                    features=features,
                )
            )
    return output


def run_deepstarr_regression_ablation(
    train: Sequence[DeepStarrSample],
    test: Sequence[DeepStarrSample],
    project: GenomicGrammarProject,
    *,
    target: DeepStarrTarget,
    alpha: float = 1.0,
    max_features: int = 256,
) -> dict[str, object]:
    """Run three-way regression ablation with TEST held out."""

    if not train or not test:
        raise ValueError("train and test samples are required")
    if any(
        sample.split is DeepStarrSplit.TEST
        for sample in train
    ):
        raise ValueError("TEST samples cannot be used for fitting")
    if any(
        sample.split is not DeepStarrSplit.TEST
        for sample in test
    ):
        raise ValueError(
            "evaluation samples must be from the TEST split"
        )

    train_sets = _compile_feature_sets(
        train,
        project,
        target,
    )
    test_sets = _compile_feature_sets(
        test,
        project,
        target,
    )
    if set(train_sets) != set(test_sets):
        raise ValueError("train/test feature-set names differ")

    results = {
        name: fit_and_evaluate(
            train_sets[name],
            test_sets[name],
            alpha=alpha,
            max_features=max_features,
        )
        for name in sorted(train_sets)
    }

    geometry_r2 = results[
        "sequence_plus_geometry"
    ]["test"]["r2"]
    phase_r2 = results[
        "sequence_plus_phase"
    ]["test"]["r2"]

    if (
        isinstance(geometry_r2, (int, float))
        and isinstance(phase_r2, (int, float))
    ):
        delta_r2: float | None = (
            float(phase_r2) - float(geometry_r2)
        )
        positive: bool | None = delta_r2 > 0.0
    else:
        delta_r2 = None
        positive = None

    return {
        "schema": "CIELINGO_DEEPSTARR_REGRESSION_ABLATION_V0_1",
        "target": target.value,
        "results": results,
        "phase_delta_r2_over_geometry": delta_r2,
        "phase_increment_positive": positive,
        "claim_scope": (
            "held-out predictive diagnostic; not causal proof "
            "of a phase mechanism"
        ),
        "canon_allowed": False,
    }
