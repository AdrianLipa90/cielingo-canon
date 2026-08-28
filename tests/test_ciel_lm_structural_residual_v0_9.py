import math

import pytest

from cielingo_core.generation.structural_residual import (
    LinearStructuralResidualExpert,
    StructuralResidualError,
    logits_sha256,
)


FEATURES = {
    "operator_argument_link": 1.0,
    "same_event_frame": 0.5,
    "case_role_link": 0.25,
    "conflict_penalty": 0.0,
}


def test_zero_init_reproduces_base_logits_exactly():
    base = (0.5, -0.2, 1.7)
    expert = LinearStructuralResidualExpert.zero_initialized(3)
    assert expert.compose_logits(base, FEATURES) == base


def test_training_mutates_expert_while_base_logits_remain_identical():
    base = (0.5, -0.2, 1.7)
    base_hash = logits_sha256(base)
    expert = LinearStructuralResidualExpert.zero_initialized(3)
    expert_hash_before = expert.parameter_sha256()

    loss = expert.train_step(base, FEATURES, 1, learning_rate=0.1)

    assert math.isfinite(loss)
    assert expert.parameter_sha256() != expert_hash_before
    assert logits_sha256(base) == base_hash
    assert base == (0.5, -0.2, 1.7)


def test_zero_gate_reproduces_base_after_expert_training():
    base = (0.5, -0.2, 1.7)
    expert = LinearStructuralResidualExpert.zero_initialized(3)
    expert.train_step(base, FEATURES, 1, learning_rate=0.1)
    assert expert.compose_logits(base, FEATURES, gate=0.0) == base


def test_nonfinite_inputs_fail_closed():
    expert = LinearStructuralResidualExpert.zero_initialized(3)
    with pytest.raises(StructuralResidualError):
        expert.compose_logits((float("nan"), 0.0, 0.0), FEATURES)
    with pytest.raises(StructuralResidualError):
        expert.compose_logits((0.0, 0.0, 0.0), {**FEATURES, "case_role_link": float("inf")})


def test_dimensions_are_explicit_and_validated():
    expert = LinearStructuralResidualExpert.zero_initialized(3)
    with pytest.raises(StructuralResidualError):
        expert.compose_logits((0.0, 0.0), FEATURES)
    with pytest.raises(StructuralResidualError):
        LinearStructuralResidualExpert.zero_initialized(0)
