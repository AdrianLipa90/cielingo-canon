"""Reference structural residual expert for CIEL-LM v0.9."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
from typing import Mapping, Sequence

REFERENCE_FEATURE_ORDER = (
    "operator_argument_link",
    "same_event_frame",
    "case_role_link",
    "conflict_penalty",
)


class StructuralResidualError(ValueError):
    """Raised when the residual contract cannot admit an input."""


def _finite_float(value: float, name: str) -> float:
    out = float(value)
    if not math.isfinite(out):
        raise StructuralResidualError(f"{name} must be finite")
    return out


def feature_vector(
    features: Mapping[str, float],
    *,
    feature_order: Sequence[str] = REFERENCE_FEATURE_ORDER,
) -> tuple[float, ...]:
    return tuple(_finite_float(features.get(name, 0.0), name) for name in feature_order)


def logits_sha256(logits: Sequence[float]) -> str:
    values = tuple(_finite_float(value, f"logit[{i}]") for i, value in enumerate(logits))
    payload = json.dumps(values, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


@dataclass
class LinearStructuralResidualExpert:
    """Zero-initializable linear residual operating beside a frozen base LM."""

    vocab_size: int
    feature_order: tuple[str, ...]
    weights: list[list[float]]
    bias: list[float]

    @classmethod
    def zero_initialized(
        cls,
        vocab_size: int,
        feature_order: Sequence[str] = REFERENCE_FEATURE_ORDER,
    ) -> "LinearStructuralResidualExpert":
        if int(vocab_size) <= 0:
            raise StructuralResidualError("vocab_size must be positive")
        order = tuple(str(name) for name in feature_order)
        if not order or len(set(order)) != len(order):
            raise StructuralResidualError("feature_order must contain unique names")
        return cls(
            vocab_size=int(vocab_size),
            feature_order=order,
            weights=[[0.0 for _ in order] for _ in range(int(vocab_size))],
            bias=[0.0 for _ in range(int(vocab_size))],
        )

    def _validate_state(self) -> None:
        if len(self.weights) != self.vocab_size or len(self.bias) != self.vocab_size:
            raise StructuralResidualError("expert vocabulary dimensions are inconsistent")
        width = len(self.feature_order)
        for row_index, row in enumerate(self.weights):
            if len(row) != width:
                raise StructuralResidualError("expert feature dimensions are inconsistent")
            for col_index, value in enumerate(row):
                _finite_float(value, f"weights[{row_index}][{col_index}]")
        for index, value in enumerate(self.bias):
            _finite_float(value, f"bias[{index}]")

    def residual_logits(self, features: Mapping[str, float]) -> tuple[float, ...]:
        self._validate_state()
        vector = feature_vector(features, feature_order=self.feature_order)
        out = []
        for row, bias in zip(self.weights, self.bias):
            value = float(bias) + sum(weight * feature for weight, feature in zip(row, vector))
            out.append(_finite_float(value, "residual_logit"))
        return tuple(out)

    def compose_logits(
        self,
        base_logits: Sequence[float],
        features: Mapping[str, float],
        *,
        gate: float = 1.0,
    ) -> tuple[float, ...]:
        base = tuple(_finite_float(value, f"base_logit[{i}]") for i, value in enumerate(base_logits))
        if len(base) != self.vocab_size:
            raise StructuralResidualError("base logits length must equal vocab_size")
        gate_value = _finite_float(gate, "gate")
        if gate_value == 0.0:
            return base
        residual = self.residual_logits(features)
        return tuple(
            _finite_float(base_value + gate_value * residual_value, f"final_logit[{i}]")
            for i, (base_value, residual_value) in enumerate(zip(base, residual))
        )

    def train_step(
        self,
        base_logits: Sequence[float],
        features: Mapping[str, float],
        target_index: int,
        *,
        learning_rate: float,
        gate: float = 1.0,
    ) -> float:
        """Update residual parameters with one cross-entropy step."""

        self._validate_state()
        target = int(target_index)
        if target < 0 or target >= self.vocab_size:
            raise StructuralResidualError("target_index is outside vocabulary")
        lr = _finite_float(learning_rate, "learning_rate")
        if lr <= 0.0:
            raise StructuralResidualError("learning_rate must be positive")
        gate_value = _finite_float(gate, "gate")
        if gate_value == 0.0:
            raise StructuralResidualError("training gate must be nonzero")

        vector = feature_vector(features, feature_order=self.feature_order)
        logits = self.compose_logits(base_logits, features, gate=gate_value)
        peak = max(logits)
        exp_values = [math.exp(value - peak) for value in logits]
        total = sum(exp_values)
        probabilities = [value / total for value in exp_values]
        loss = -math.log(max(probabilities[target], 1e-300))

        for vocab_index, probability in enumerate(probabilities):
            grad_logit = probability - (1.0 if vocab_index == target else 0.0)
            scaled = gate_value * grad_logit
            self.bias[vocab_index] -= lr * scaled
            row = self.weights[vocab_index]
            for feature_index, feature_value in enumerate(vector):
                row[feature_index] -= lr * scaled * feature_value

        self._validate_state()
        return float(loss)

    def parameter_sha256(self) -> str:
        self._validate_state()
        payload = {
            "vocab_size": self.vocab_size,
            "feature_order": list(self.feature_order),
            "weights": self.weights,
            "bias": self.bias,
        }
        raw = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()
