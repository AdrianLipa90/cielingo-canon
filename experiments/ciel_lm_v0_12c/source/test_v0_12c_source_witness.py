import hashlib
import json
from pathlib import Path

import torch

from ciel_lm_text.residual import BiasFreeStructuralResidual, carrier_diagnostics
from ciel_lm_text.v0_12c_runner import (
    SCIENTIFIC_NAMESPACE,
    SOURCE_MANIFEST_SHA256,
    V0_12A_EXPECTED,
    carrier_preflight,
    full_shuffle,
    iszero,
    mask_preserving_shuffle,
    source_manifest_sha,
    split_registered,
)


def test_source_manifest_exact():
    assert source_manifest_sha() == SOURCE_MANIFEST_SHA256


def test_v0_12a_carrier_replay_exact():
    tr, va = split_registered()
    got = carrier_preflight(tr.split(), va.split())
    assert got["validation"]["nonzero"] == 13
    assert got["validation"]["unique"] == 7
    assert got["validation"]["candidates"] == 58
    assert got["validation"]["operator_bound"] == 32
    assert got["training"]["nonzero"] == 52
    assert got["training"]["unique"] == 22
    assert got["training"]["candidates"] == 280
    assert got["training"]["operator_bound"] == 174


def test_mask_shuffle_preserves_zero_support_and_uses_hypothesis_namespace():
    fs = [[0,0,0,0],[.1,0,0,0],[.2,.01,0,0],[0,0,0,0],[.3,0,0,0]]
    out, src = mask_preserving_shuffle(fs, 1983284250, "validation")
    assert [iszero(x) for x in out] == [iszero(x) for x in fs]
    dst = [1,2,4]
    expected = sorted(dst, key=lambda i: hashlib.sha256(
        f"{SCIENTIFIC_NAMESPACE}|1983284250|validation|{i}".encode()
    ).hexdigest())
    assert src == expected


def test_full_shuffle_is_deterministic():
    fs = [[0,0,0,0],[.1,0,0,0],[.2,.01,0,0]]
    a, oa = full_shuffle(fs, 7, "validation")
    b, ob = full_shuffle(fs, 7, "validation")
    assert a == b and oa == ob


def test_bias_free_residual_zero_invariant_after_training():
    torch.manual_seed(7)
    expert = BiasFreeStructuralResidual(11)
    opt = torch.optim.AdamW(expert.parameters(), lr=4e-4, weight_decay=0.0)
    f = torch.tensor([.2,.1,0,0.])
    base = torch.randn(24,11)
    y = torch.arange(24) % 11
    for _ in range(4):
        opt.zero_grad(set_to_none=True)
        loss = torch.nn.functional.cross_entropy(base + expert(f)[None,:], y)
        loss.backward(); opt.step()
    assert torch.equal(expert(torch.zeros(4)), torch.zeros(11))


def test_exact_carrier_has_no_fuzzy_scores():
    row = carrier_diagnostics(["source", "run", "unrelated"])
    assert row["all_candidate_scores_exact"] is True
