"""Dependency-free ridge regression for held-out genomic ablations."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Mapping, Sequence


@dataclass(frozen=True)
class RegressionExample:
    sample_id: str
    target: float
    features: Mapping[str, float]

    def __post_init__(self) -> None:
        if not self.sample_id.strip():
            raise ValueError("sample_id must be non-empty")
        if not math.isfinite(self.target):
            raise ValueError("target must be finite")
        for key, value in self.features.items():
            if not isinstance(key, str) or not key:
                raise ValueError("feature names must be non-empty strings")
            if not math.isfinite(float(value)):
                raise ValueError(f"feature {key!r} must be finite")


@dataclass(frozen=True)
class RidgeRegressionModel:
    feature_names: tuple[str, ...]
    feature_means: tuple[float, ...]
    feature_scales: tuple[float, ...]
    coefficients: tuple[float, ...]
    target_mean: float
    alpha: float

    def predict_one(self, features: Mapping[str, float]) -> float:
        total = self.target_mean
        for name, mean, scale, coefficient in zip(
            self.feature_names,
            self.feature_means,
            self.feature_scales,
            self.coefficients,
        ):
            value = float(features.get(name, 0.0))
            standardized = 0.0 if scale == 0.0 else (value - mean) / scale
            total += coefficient * standardized
        return total

    def to_dict(self) -> dict[str, object]:
        return {
            "schema": "CIELINGO_RIDGE_MODEL_V0_1",
            "feature_names": list(self.feature_names),
            "feature_means": list(self.feature_means),
            "feature_scales": list(self.feature_scales),
            "coefficients": list(self.coefficients),
            "target_mean": self.target_mean,
            "alpha": self.alpha,
        }


def _solve(
    matrix: list[list[float]],
    vector: list[float],
) -> list[float]:
    size = len(vector)
    if size == 0:
        return []

    augmented = [
        matrix[index][:] + [vector[index]]
        for index in range(size)
    ]
    for column in range(size):
        pivot = max(
            range(column, size),
            key=lambda row: abs(augmented[row][column]),
        )
        if abs(augmented[pivot][column]) < 1e-12:
            raise ValueError("ridge system is singular")
        augmented[column], augmented[pivot] = (
            augmented[pivot],
            augmented[column],
        )

        scale = augmented[column][column]
        augmented[column] = [
            value / scale
            for value in augmented[column]
        ]

        for row in range(size):
            if row == column:
                continue
            factor = augmented[row][column]
            if factor == 0.0:
                continue
            augmented[row] = [
                augmented[row][index]
                - factor * augmented[column][index]
                for index in range(size + 1)
            ]

    return [augmented[index][size] for index in range(size)]


def fit_ridge(
    examples: Sequence[RegressionExample],
    *,
    alpha: float = 1.0,
    max_features: int = 256,
) -> RidgeRegressionModel:
    if not examples:
        raise ValueError("at least one training example is required")
    if not math.isfinite(alpha) or alpha <= 0.0:
        raise ValueError("alpha must be finite and positive")
    if max_features < 1:
        raise ValueError("max_features must be positive")

    sample_ids = [example.sample_id for example in examples]
    if len(sample_ids) != len(set(sample_ids)):
        raise ValueError("training sample ids must be unique")

    feature_names = tuple(
        sorted(
            {
                key
                for example in examples
                for key in example.features
            }
        )
    )
    if len(feature_names) > max_features:
        raise ValueError(
            f"feature count {len(feature_names)} exceeds "
            f"max_features={max_features}"
        )

    count = float(len(examples))
    means: list[float] = []
    scales: list[float] = []
    for name in feature_names:
        values = [
            float(example.features.get(name, 0.0))
            for example in examples
        ]
        mean = sum(values) / count
        variance = sum(
            (value - mean) ** 2
            for value in values
        ) / count
        means.append(mean)
        scales.append(
            math.sqrt(variance) if variance > 1e-24 else 0.0
        )

    target_mean = sum(example.target for example in examples) / count
    if not feature_names:
        return RidgeRegressionModel(
            feature_names=(),
            feature_means=(),
            feature_scales=(),
            coefficients=(),
            target_mean=target_mean,
            alpha=float(alpha),
        )

    rows: list[list[float]] = []
    centered_targets: list[float] = []
    for example in examples:
        rows.append(
            [
                0.0
                if scale == 0.0
                else (
                    float(example.features.get(name, 0.0)) - mean
                ) / scale
                for name, mean, scale in zip(
                    feature_names,
                    means,
                    scales,
                )
            ]
        )
        centered_targets.append(example.target - target_mean)

    dimension = len(feature_names)
    matrix = [
        [
            sum(
                row[left] * row[right]
                for row in rows
            )
            + (alpha if left == right else 0.0)
            for right in range(dimension)
        ]
        for left in range(dimension)
    ]
    vector = [
        sum(
            row[index] * target
            for row, target in zip(rows, centered_targets)
        )
        for index in range(dimension)
    ]
    coefficients = _solve(matrix, vector)

    return RidgeRegressionModel(
        feature_names=feature_names,
        feature_means=tuple(means),
        feature_scales=tuple(scales),
        coefficients=tuple(coefficients),
        target_mean=target_mean,
        alpha=float(alpha),
    )


def regression_metrics(
    model: RidgeRegressionModel,
    examples: Sequence[RegressionExample],
) -> dict[str, object]:
    if not examples:
        raise ValueError("at least one evaluation example is required")

    actual = [example.target for example in examples]
    predicted = [
        model.predict_one(example.features)
        for example in examples
    ]
    count = len(actual)

    residuals = [
        observed - prediction
        for observed, prediction in zip(actual, predicted)
    ]
    mse = sum(
        residual * residual
        for residual in residuals
    ) / count
    mae = sum(abs(residual) for residual in residuals) / count

    actual_mean = sum(actual) / count
    total_variance = sum(
        (observed - actual_mean) ** 2
        for observed in actual
    )
    residual_ss = sum(
        residual * residual
        for residual in residuals
    )
    r2 = (
        1.0 - residual_ss / total_variance
        if total_variance > 0.0
        else None
    )

    predicted_mean = sum(predicted) / count
    covariance = sum(
        (observed - actual_mean) * (prediction - predicted_mean)
        for observed, prediction in zip(actual, predicted)
    )
    predicted_ss = sum(
        (prediction - predicted_mean) ** 2
        for prediction in predicted
    )
    pearson = (
        covariance / math.sqrt(total_variance * predicted_ss)
        if total_variance > 0.0 and predicted_ss > 0.0
        else None
    )

    return {
        "n": count,
        "rmse": math.sqrt(mse),
        "mae": mae,
        "r2": r2,
        "pearson": pearson,
    }


def fit_and_evaluate(
    train: Sequence[RegressionExample],
    test: Sequence[RegressionExample],
    *,
    alpha: float = 1.0,
    max_features: int = 256,
) -> dict[str, object]:
    train_ids = {example.sample_id for example in train}
    test_ids = {example.sample_id for example in test}
    overlap = sorted(train_ids & test_ids)
    if overlap:
        raise ValueError(f"train/test sample leakage: {overlap[0]}")

    model = fit_ridge(
        train,
        alpha=alpha,
        max_features=max_features,
    )
    return {
        "schema": "CIELINGO_RIDGE_REGRESSION_V0_1",
        "alpha": alpha,
        "feature_count": len(model.feature_names),
        "train": regression_metrics(model, train),
        "test": regression_metrics(model, test),
        "model": model.to_dict(),
    }
