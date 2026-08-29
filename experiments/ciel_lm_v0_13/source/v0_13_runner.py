from __future__ import annotations

import argparse
import json

from ciel_lm_text import v0_12d_runner as parent

core = parent.core

SCHEMA = "CIEL_LM_V0_13_INDEPENDENT_WINDOW_REPLICATION_REPORT_V1"
EXPERIMENT_NAMESPACE = "CIEL_LM_V0_13_INDEPENDENT_WINDOW_REPLICATION"
PREREG_GITHUB_BLOB_SHA = "7d9ef6ad411de5399ab8e82d748982cdd36bd700"
SEEDS = [
    2346014545, 4188294876, 1128939504, 3184819618,
    1551236951, 3595945826, 2539003182, 1520253702,
    643343601, 3532260309, 2705133989, 2990254709,
]
VALIDATION_STARTS = [47, 121, 150, 160, 203, 232, 270, 291, 301, 333, 369, 391, 415, 422, 423, 487]
PARENT_VALIDATION_STARTS = [0, 36, 73, 109, 146, 182, 219, 255, 292, 328, 365, 401, 438, 474, 511, 547]
EXPECTED_VALIDATION_CARRIER = {
    "windows": 16,
    "nonzero": 13,
    "unique": 4,
    "candidates": 44,
    "operator_bound": 29,
    "components": [13, 3, 0, 0],
}


def carrier_preflight_v13(train_raw: list[str], validation_raw: list[str]) -> dict:
    if set(VALIDATION_STARTS) & set(PARENT_VALIDATION_STARTS):
        raise RuntimeError("VALIDATION_STARTS_NOT_DISJOINT")
    validation = core.carrier_stats(validation_raw, VALIDATION_STARTS, 24)
    training_starts = core.spaced_starts(len(train_raw), 24, 64)
    training = core.carrier_stats(train_raw, training_starts, 24)
    for field, expected in EXPECTED_VALIDATION_CARRIER.items():
        if validation[field] != expected:
            raise RuntimeError(f"V0_13_CARRIER_REPLAY_MISMATCH:{field}:{validation[field]}!={expected}")
    if not validation["all_candidate_scores_exact"]:
        raise RuntimeError("V0_13_NONEXACT_CARRIER_SCORE")
    for field, expected in core.V0_12A_EXPECTED["training"].items():
        if training[field] != expected:
            raise RuntimeError(f"PARENT_TRAIN_CARRIER_MISMATCH:{field}:{training[field]}!={expected}")
    if not training["all_candidate_scores_exact"]:
        raise RuntimeError("PARENT_TRAIN_NONEXACT_CARRIER_SCORE")
    return {
        "status": "PASS",
        "validation": {k: validation[k] for k in (*EXPECTED_VALIDATION_CARRIER, "all_candidate_scores_exact")},
        "training": {k: training[k] for k in (*core.V0_12A_EXPECTED["training"], "all_candidate_scores_exact")},
        "validation_starts": list(VALIDATION_STARTS),
        "training_probe_starts": training_starts,
    }


def _bind_protocol() -> None:
    parent._bind_protocol()
    core.SCHEMA = SCHEMA
    core.EXPERIMENT_NAMESPACE = EXPERIMENT_NAMESPACE
    core.PREREG_GITHUB_BLOB_SHA = PREREG_GITHUB_BLOB_SHA
    core.SEEDS = list(SEEDS)
    core.carrier_preflight = carrier_preflight_v13
    core.samples = parent._window_aligned_samples


def self_test() -> dict:
    _bind_protocol()
    base = core.self_test()
    train_text, validation_text = core.split_registered()
    carrier = carrier_preflight_v13(train_text.split(), validation_text.split())
    assert carrier["validation"]["nonzero"] == 13
    assert carrier["validation"]["unique"] == 4
    return {
        "status": "PASS",
        "core_self_test": base["status"],
        "validation_nonzero": carrier["validation"]["nonzero"],
        "validation_unique": carrier["validation"]["unique"],
        "starts_disjoint": not bool(set(VALIDATION_STARTS) & set(PARENT_VALIDATION_STARTS)),
    }


def main() -> None:
    _bind_protocol()
    old = core.ROOT / "evidence" / "V0_12C_SOURCE_WITNESSED_REEXECUTION_REPORT.json"
    new = core.ROOT / "evidence" / "V0_13_INDEPENDENT_WINDOW_REPLICATION_REPORT.json"
    if old.exists():
        old.unlink()
    core.main()
    if old.exists():
        old.replace(new)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), sort_keys=True))
    else:
        main()
