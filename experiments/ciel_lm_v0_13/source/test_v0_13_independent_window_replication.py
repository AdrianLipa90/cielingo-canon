import hashlib
from ciel_lm_text.v0_13_runner import (
    PARENT_VALIDATION_STARTS,
    PREREG_GITHUB_BLOB_SHA,
    SEEDS,
    VALIDATION_STARTS,
    carrier_preflight_v13,
)
from ciel_lm_text.v0_12d_runner import source_manifest_sha, split_registered


def test_v0_13_source_manifest_exact():
    assert source_manifest_sha() == "b7dc41d5a2f074244e4fb0a581bb9df1ca186e5bd7a5ea21ad873b6bace59fe3"


def test_v0_13_validation_starts_disjoint_and_frozen():
    assert not (set(VALIDATION_STARTS) & set(PARENT_VALIDATION_STARTS))
    payload = '[' + ','.join(str(x) for x in VALIDATION_STARTS) + ']'
    assert hashlib.sha256(payload.encode()).hexdigest() == "4793d2f1d052b2de601c83e2754517d83df62cb2a14e712628a1a09b06e5b9a8"


def test_v0_13_seed_set_frozen():
    payload = '[' + ','.join(str(x) for x in SEEDS) + ']'
    assert hashlib.sha256(payload.encode()).hexdigest() == "77e0067eb554c28134223079dd572e2e16fc1df3a431a2354ce8e0128e8f2eb3"
    assert len(set(SEEDS)) == 12


def test_v0_13_carrier_admission_exact():
    tr, va = split_registered()
    c = carrier_preflight_v13(tr.split(), va.split())
    assert c['validation']['nonzero'] == 13
    assert c['validation']['unique'] == 4
    assert c['validation']['candidates'] == 44
    assert c['validation']['operator_bound'] == 29
    assert c['validation']['all_candidate_scores_exact'] is True
    assert c['training']['nonzero'] == 52
