from __future__ import annotations

import pytest

from cielingo_core.genomics import (
    RegressionExample,
    fit_and_evaluate,
    fit_ridge,
    regression_metrics,
)


def test_ridge_fits_linear_signal_and_uses_train_statistics_only():
    train = [
        RegressionExample(
            f"t{i}",
            1.0 + 2.0 * i,
            {"x": float(i)},
        )
        for i in range(5)
    ]
    test = [
        RegressionExample("e5", 11.0, {"x": 5.0}),
        RegressionExample("e6", 13.0, {"x": 6.0}),
    ]

    result = fit_and_evaluate(
        train,
        test,
        alpha=1e-6,
    )
    assert result["test"]["r2"] is not None
    assert result["test"]["r2"] > 0.999
    assert (
        result["model"]["schema"]
        == "CIELINGO_RIDGE_MODEL_V0_1"
    )


def test_ridge_rejects_leakage_and_feature_explosion():
    example = RegressionExample(
        "same",
        1.0,
        {"x": 1.0},
    )
    with pytest.raises(ValueError, match="leakage"):
        fit_and_evaluate([example], [example])

    many = RegressionExample(
        "x",
        0.0,
        {
            f"f{i}": float(i)
            for i in range(4)
        },
    )
    with pytest.raises(
        ValueError,
        match="exceeds max_features",
    ):
        fit_ridge([many], max_features=3)


def test_constant_target_uses_none_instead_of_nan_r2():
    train = [
        RegressionExample("a", 2.0, {"x": 0.0}),
        RegressionExample("b", 2.0, {"x": 1.0}),
    ]
    model = fit_ridge(train)
    metrics = regression_metrics(model, train)
    assert metrics["r2"] is None
