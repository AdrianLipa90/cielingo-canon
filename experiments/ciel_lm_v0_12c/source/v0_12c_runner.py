from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import random
import time
from pathlib import Path

import torch
import torch.nn.functional as F

from ciel_lm_text.tokenizer import WordTokenizer
from ciel_lm_text.model import TinyCielLM, ModelConfig
from ciel_lm_text.corpus import _strings, _clean
from ciel_lm_text.residual import (
    BiasFreeStructuralResidual,
    relation_feature_vector,
    carrier_diagnostics,
    tensor_sha256_state_dict,
)

ROOT = Path(__file__).resolve().parents[2]
VENDOR = ROOT / "vendor"

SCHEMA = "CIEL_LM_V0_12C_SOURCE_WITNESSED_REEXECUTION_REPORT_V1"
EXPERIMENT_NAMESPACE = "CIEL_LM_V0_12C_SOURCE_WITNESSED_REEXECUTION"
SCIENTIFIC_NAMESPACE = "CIEL_LM_V0_12_SUPPORT_PRESERVING_RELATION_TEST"
PREREG_GITHUB_BLOB_SHA = "cbe473106c76eefc355456eb03ab53e4d0b3d821"
SOURCE_MANIFEST_SHA256 = "b7dc41d5a2f074244e4fb0a581bb9df1ca186e5bd7a5ea21ad873b6bace59fe3"

HELDOUT_FILES = [
    "cielingo/docs/architecture/CIELINGO_REGIONAL_LANGUAGE_SEPARATION_REFACTOR_v0_5L.md",
    "cielingo/docs/architecture/DOCTOR_2_LINGOPHYSICS_DOCTOR_v0_1.md",
    "cielingo/docs/architecture/CIELINGO_GLOBAL_FILESENSE_EXECUTION_v0_4.md",
    "cielingo/docs/beta_knot/BETA_KNOT_DOCTOR_PLACEMENT_DECISION_v0_2.md",
    "cielingo/docs/architecture/CIELINGO_0_5L_FIX_NOEMA_SURFACE_LS_ROUTER_TEST_v0_1.md",
    "cielingo/docs/architecture/CIELINGO_CARD_MIGRATION_POLICY_v0_2.md",
    "cielingo/docs/architecture/CONTROLLED_48_SLOT_ATLAS_DOCTOR_HARDENING_v0_6A.md",
]
SEEDS = [
    1983284250, 2335476171, 468047153, 1778730716,
    1618077513, 2495858501, 3177070224, 1659852898,
    1179621353, 2859991481, 2120589209, 2031268836,
]

BASE = dict(
    block_size=24,
    d_model=96,
    n_heads=4,
    n_layers=2,
    dropout=0.1,
    learning_rate=4e-4,
    training_steps=120,
    weight_decay=0.01,
    grad_clip_norm=1.0,
)
RESIDUAL = dict(learning_rate=4e-4, training_steps=120, weight_decay=0.0)
TOKENIZER = dict(min_freq=1, max_vocab=5000)

V0_12A_EXPECTED = {
    "validation": {
        "windows": 16,
        "nonzero": 13,
        "unique": 7,
        "candidates": 58,
        "operator_bound": 32,
        "components": [13, 4, 0, 0],
    },
    "training": {
        "windows": 64,
        "nonzero": 52,
        "unique": 22,
        "candidates": 280,
        "operator_bound": 174,
        "components": [52, 27, 0, 0],
    },
}


def sha_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_files() -> list[Path]:
    return sorted(
        list((VENDOR / "cielingo" / "corpus").glob("*.json"))
        + list((VENDOR / "cielingo" / "docs").rglob("*.md"))
        + list((VENDOR / "lingophysics" / "docs").rglob("*.md"))
    )


def source_manifest() -> dict[str, str]:
    return {p.relative_to(VENDOR).as_posix(): sha_file(p) for p in source_files()}


def source_manifest_sha() -> str:
    payload = json.dumps(source_manifest(), sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def clean_text(path: Path) -> str:
    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        vals = [_clean(s) for s in _strings(data) if len(s.strip()) > 1]
        return "\n".join(v for v in vals if v)
    return _clean(path.read_text(encoding="utf-8", errors="ignore"))


def split_registered() -> tuple[str, str]:
    fs = source_files()
    if len(fs) != 56:
        raise RuntimeError(f"SOURCE_COUNT_MISMATCH:{len(fs)}")
    got_manifest = source_manifest_sha()
    if got_manifest != SOURCE_MANIFEST_SHA256:
        raise RuntimeError(f"SOURCE_MANIFEST_SHA_MISMATCH:{got_manifest}")
    held = set(HELDOUT_FILES)
    train, validation, seen = [], [], set()
    for path in fs:
        rel = path.relative_to(VENDOR).as_posix()
        seen.add(rel)
        (validation if rel in held else train).append(clean_text(path))
    if not held.issubset(seen):
        raise RuntimeError(f"HELDOUT_MISSING:{sorted(held - seen)}")
    return "\n".join(train), "\n".join(validation)


def spaced_starts(n: int, block_size: int, count: int) -> list[int]:
    max_start = max(0, n - block_size)
    starts = sorted(set(round(i * max_start / (count - 1)) for i in range(count)))
    if len(starts) != count:
        raise RuntimeError(f"START_COUNT_MISMATCH:{len(starts)}!={count}")
    return starts


def carrier_stats(tokens: list[str], starts: list[int], block_size: int = 24) -> dict:
    rows = [carrier_diagnostics(tokens[s:s + block_size]) for s in starts]
    nonzero = [r for r in rows if not iszero(r["vector"])]
    return {
        "windows": len(rows),
        "nonzero": len(nonzero),
        "unique": len({tuple(round(float(x), 15) for x in r["vector"]) for r in nonzero}),
        "candidates": sum(r["candidate_count"] for r in rows),
        "operator_bound": sum(r["operator_bound_candidate_count"] for r in rows),
        "components": [sum(abs(float(r["vector"][i])) > 1e-15 for r in rows) for i in range(4)],
        "all_candidate_scores_exact": all(r["all_candidate_scores_exact"] for r in rows),
        "rows": rows,
    }


def carrier_preflight(train_raw: list[str], validation_raw: list[str]) -> dict:
    validation_starts = spaced_starts(len(validation_raw), 24, 16)
    training_starts = spaced_starts(len(train_raw), 24, 64)
    validation = carrier_stats(validation_raw, validation_starts)
    training = carrier_stats(train_raw, training_starts)
    for key, got in (("validation", validation), ("training", training)):
        for field, expected in V0_12A_EXPECTED[key].items():
            if got[field] != expected:
                raise RuntimeError(
                    f"CARRIER_REPLAY_MISMATCH:{key}:{field}:{got[field]}!={expected}"
                )
        if not got["all_candidate_scores_exact"]:
            raise RuntimeError(f"NONEXACT_CARRIER_SCORE:{key}")
    return {
        "status": "PASS",
        "validation": {k: validation[k] for k in (*V0_12A_EXPECTED["validation"], "all_candidate_scores_exact")},
        "training": {k: training[k] for k in (*V0_12A_EXPECTED["training"], "all_candidate_scores_exact")},
        "validation_starts": validation_starts,
        "training_probe_starts": training_starts,
    }


def example(ids: list[int], start: int, block_size: int):
    q = ids[start:start + block_size + 1]
    if len(q) != block_size + 1:
        raise RuntimeError("SHORT_EXAMPLE")
    return q[:-1], q[1:]


def state_hash(model) -> str:
    return tensor_sha256_state_dict(model.state_dict())


def train_base(seed: int, ids: list[int], starts: list[int], cfg: ModelConfig):
    torch.manual_seed(seed)
    model = TinyCielLM(cfg)
    opt = torch.optim.AdamW(
        model.parameters(),
        lr=BASE["learning_rate"],
        weight_decay=BASE["weight_decay"],
    )
    torch.manual_seed(seed + 100000)
    for start in starts:
        xids, yids = example(ids, start, cfg.block_size)
        x = torch.tensor([xids])
        y = torch.tensor([yids])
        model.train()
        opt.zero_grad(set_to_none=True)
        _, loss = model(x, targets=y)
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), BASE["grad_clip_norm"])
        opt.step()
    model.eval()
    for p in model.parameters():
        p.requires_grad_(False)
    return model


def samples(model, ids: list[int], raw: list[str], starts: list[int], block_size: int):
    out = []
    with torch.no_grad():
        for start in starts:
            xids, yids = example(ids, start, block_size)
            logits, _ = model(torch.tensor([xids]))
            out.append((
                logits[0].detach().clone(),
                torch.tensor(yids, dtype=torch.long),
                raw[start:start + block_size],
            ))
    return out


def features(sample_rows) -> list[list[float]]:
    return [relation_feature_vector(tokens) for _, _, tokens in sample_rows]


def iszero(feature) -> bool:
    return all(abs(float(x)) <= 1e-15 for x in feature)


def _hash_order(indices: list[int], seed: int, split: str) -> list[int]:
    return sorted(
        indices,
        key=lambda i: hashlib.sha256(
            f"{SCIENTIFIC_NAMESPACE}|{seed}|{split}|{i}".encode()
        ).hexdigest(),
    )


def mask_preserving_shuffle(fs: list[list[float]], seed: int, split: str):
    destinations = [i for i, f in enumerate(fs) if not iszero(f)]
    sources = _hash_order(destinations, seed, split)
    out = [list(f) for f in fs]
    for destination, source in zip(sorted(destinations), sources):
        out[destination] = list(fs[source])
    if [i for i, f in enumerate(out) if not iszero(f)] != sorted(destinations):
        raise RuntimeError("MASK_SUPPORT_CHANGED")
    for i, f in enumerate(fs):
        if iszero(f) and not iszero(out[i]):
            raise RuntimeError("ZERO_SUPPORT_VIOLATION")
    return out, sources


def full_shuffle(fs: list[list[float]], seed: int, split: str):
    order = _hash_order(list(range(len(fs))), seed, split)
    return [list(fs[j]) for j in order], order


def train_residual(vocab_size: int, sample_rows, fs: list[list[float]]):
    expert = BiasFreeStructuralResidual(vocab_size)
    opt = torch.optim.AdamW(
        expert.parameters(),
        lr=RESIDUAL["learning_rate"],
        weight_decay=RESIDUAL["weight_decay"],
    )
    if len(sample_rows) != RESIDUAL["training_steps"]:
        raise RuntimeError("RESIDUAL_TRAINING_STEP_COUNT_MISMATCH")
    for (base_logits, targets, _), fv in zip(sample_rows, fs):
        f = torch.tensor(fv, dtype=torch.float32)
        opt.zero_grad(set_to_none=True)
        logits = base_logits + expert(f)[None, :]
        loss = F.cross_entropy(logits, targets)
        loss.backward()
        opt.step()
    return expert


def eval_nll(sample_rows, fs=None, expert=None):
    vals, correct, total = [], 0, 0
    with torch.no_grad():
        for i, (base_logits, targets, _) in enumerate(sample_rows):
            logits = base_logits
            if expert is not None:
                f = torch.tensor(fs[i], dtype=torch.float32)
                logits = base_logits + expert(f)[None, :]
            vals.append(float(F.cross_entropy(logits, targets)))
            correct += int((logits.argmax(-1) == targets).sum())
            total += targets.numel()
    nll = sum(vals) / len(vals)
    return {
        "nll": nll,
        "perplexity": math.exp(min(20, nll)),
        "top1_accuracy": correct / total,
        "tokens": total,
    }


def exact_signflip(ds: list[float]) -> float:
    obs = sum(ds) / len(ds)
    ge = total = 0
    for signs in itertools.product((-1.0, 1.0), repeat=len(ds)):
        stat = sum(s * d for s, d in zip(signs, ds)) / len(ds)
        total += 1
        if stat >= obs - 1e-15:
            ge += 1
    return ge / total


def leave_one_out(ds: list[float]) -> list[float]:
    return [sum(ds[:i] + ds[i + 1:]) / (len(ds) - 1) for i in range(len(ds))]


def self_test() -> dict:
    fs = [[0, 0, 0, 0], [.1, 0, 0, 0], [.2, .01, 0, 0], [0, 0, 0, 0], [.3, 0, 0, 0]]
    masked, _ = mask_preserving_shuffle(fs, 1983284250, "validation")
    assert iszero(masked[0]) and iszero(masked[3])
    assert [i for i, f in enumerate(masked) if not iszero(f)] == [1, 2, 4]

    torch.manual_seed(1)
    expert = BiasFreeStructuralResidual(9)
    base = torch.randn(24, 9)
    f = torch.tensor([.2, .1, 0, 0.])
    assert torch.equal(base, base + expert(f)[None, :])
    opt = torch.optim.AdamW(expert.parameters(), lr=RESIDUAL["learning_rate"], weight_decay=0.0)
    targets = torch.arange(24) % 9
    for _ in range(3):
        opt.zero_grad(set_to_none=True)
        loss = F.cross_entropy(base + expert(f)[None, :], targets)
        loss.backward()
        opt.step()
    assert torch.equal(expert(torch.zeros(4)), torch.zeros(9))
    assert torch.equal(base, base + expert(torch.zeros(4))[None, :])
    return {"status": "PASS", "mask_support": [iszero(x) for x in masked]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), sort_keys=True))
        return

    train_text, validation_text = split_registered()
    train_raw = train_text.split()
    validation_raw = validation_text.split()
    carrier = carrier_preflight(train_raw, validation_raw)

    tokenizer = WordTokenizer.build(
        train_text,
        min_freq=TOKENIZER["min_freq"],
        max_vocab=TOKENIZER["max_vocab"],
    )
    train_ids = tokenizer.encode(train_text)
    validation_ids = tokenizer.encode(validation_text)
    if len(train_ids) != len(train_raw) or len(validation_ids) != len(validation_raw):
        raise RuntimeError("TOKEN_ALIGNMENT_LENGTH_MISMATCH")

    validation_starts = carrier["validation_starts"]
    rows = []
    for seed in SEEDS:
        rng = random.Random(seed + 9000)
        max_train_start = max(0, len(train_ids) - BASE["block_size"] - 2)
        train_starts = [rng.randint(0, max_train_start) for _ in range(BASE["training_steps"])]
        cfg = ModelConfig(
            vocab_size=tokenizer.vocab_size,
            block_size=BASE["block_size"],
            d_model=BASE["d_model"],
            n_heads=BASE["n_heads"],
            n_layers=BASE["n_layers"],
            dropout=BASE["dropout"],
            structural_weight=0.0,
        )
        t0 = time.time()
        base = train_base(seed, train_ids, train_starts, cfg)
        base_hash = state_hash(base)
        train_samples = samples(base, train_ids, train_raw, train_starts, BASE["block_size"])
        validation_samples = samples(base, validation_ids, validation_raw, validation_starts, BASE["block_size"])
        real_train = features(train_samples)
        real_validation = features(validation_samples)
        mask_train, mask_train_order = mask_preserving_shuffle(real_train, seed, "train")
        mask_validation, mask_validation_order = mask_preserving_shuffle(real_validation, seed, "validation")
        full_train, full_train_order = full_shuffle(real_train, seed, "train")
        full_validation, full_validation_order = full_shuffle(real_validation, seed, "validation")

        zero_init_expert = BiasFreeStructuralResidual(tokenizer.vocab_size)
        zero_init_exact = all(
            torch.equal(bl, bl + zero_init_expert(torch.tensor(fv, dtype=torch.float32))[None, :])
            for bl, _, _ in validation_samples
            for fv in ([0.0, 0.0, 0.0, 0.0],)
        )

        real_expert = train_residual(tokenizer.vocab_size, train_samples, real_train)
        mask_expert = train_residual(tokenizer.vocab_size, train_samples, mask_train)
        full_expert = train_residual(tokenizer.vocab_size, train_samples, full_train)
        base_hash_after = state_hash(base)
        zero = torch.zeros(4)
        zero_post = all(
            torch.equal(expert(zero), torch.zeros(tokenizer.vocab_size))
            for expert in (real_expert, mask_expert, full_expert)
        )

        base_metrics = eval_nll(validation_samples)
        real_metrics = eval_nll(validation_samples, real_validation, real_expert)
        mask_metrics = eval_nll(validation_samples, mask_validation, mask_expert)
        full_metrics = eval_nll(validation_samples, full_validation, full_expert)
        row = {
            "seed": seed,
            "base": base_metrics,
            "real": real_metrics,
            "mask_preserving": mask_metrics,
            "full_shuffle": full_metrics,
            "delta_semantic": mask_metrics["nll"] - real_metrics["nll"],
            "delta_base": base_metrics["nll"] - real_metrics["nll"],
            "delta_localization": full_metrics["nll"] - mask_metrics["nll"],
            "base_hash": base_hash,
            "base_hash_after": base_hash_after,
            "base_hash_unchanged": base_hash == base_hash_after,
            "zero_init_exact": zero_init_exact,
            "zero_post_exact": zero_post,
            "real_residual_sha256": real_expert.parameter_sha256(),
            "mask_residual_sha256": mask_expert.parameter_sha256(),
            "full_residual_sha256": full_expert.parameter_sha256(),
            "train_mask_source_order": mask_train_order,
            "validation_mask_source_order": mask_validation_order,
            "train_full_source_order": full_train_order,
            "validation_full_source_order": full_validation_order,
            "elapsed_seconds": time.time() - t0,
        }
        rows.append(row)
        print(json.dumps({
            "seed": seed,
            "delta_semantic": row["delta_semantic"],
            "delta_base": row["delta_base"],
            "delta_localization": row["delta_localization"],
            "base_hash_unchanged": row["base_hash_unchanged"],
            "zero_post_exact": row["zero_post_exact"],
        }, sort_keys=True), flush=True)

    delta_semantic = [r["delta_semantic"] for r in rows]
    delta_base = [r["delta_base"] for r in rows]
    delta_localization = [r["delta_localization"] for r in rows]
    loo_semantic = leave_one_out(delta_semantic)
    p_semantic = exact_signflip(delta_semantic)
    invariants = (
        carrier["status"] == "PASS"
        and all(r["base_hash_unchanged"] and r["zero_init_exact"] and r["zero_post_exact"] for r in rows)
    )
    checks = {
        "mean_delta_semantic_positive": sum(delta_semantic) / len(delta_semantic) > 0,
        "positive_delta_semantic_seeds_ge_9": sum(d > 0 for d in delta_semantic) >= 9,
        "signflip_p_semantic_le_0_05": p_semantic <= 0.05,
        "min_loo_semantic_positive": min(loo_semantic) > 0,
        "all_invariants_pass": invariants,
    }
    status = "PASS_SEMANTIC_VECTOR_SPECIFICITY_CANDIDATE" if all(checks.values()) else "BLOCK_SEMANTIC_VECTOR_SPECIFICITY"
    report = {
        "schema": SCHEMA,
        "status": status,
        "experiment_namespace": EXPERIMENT_NAMESPACE,
        "scientific_hypothesis_namespace": SCIENTIFIC_NAMESPACE,
        "prereg_github_blob_sha": PREREG_GITHUB_BLOB_SHA,
        "source_manifest_sha256": source_manifest_sha(),
        "carrier_preflight": carrier,
        "train_tokens": len(train_ids),
        "validation_tokens": len(validation_ids),
        "vocab_size": tokenizer.vocab_size,
        "rows": rows,
        "aggregate": {
            "mean_delta_semantic": sum(delta_semantic) / len(delta_semantic),
            "positive_delta_semantic_seeds": sum(d > 0 for d in delta_semantic),
            "signflip_p_semantic": p_semantic,
            "leave_one_out_semantic": loo_semantic,
            "min_leave_one_out_semantic": min(loo_semantic),
            "mean_delta_base": sum(delta_base) / len(delta_base),
            "positive_delta_base_seeds": sum(d > 0 for d in delta_base),
            "mean_delta_localization": sum(delta_localization) / len(delta_localization),
            "positive_delta_localization_seeds": sum(d > 0 for d in delta_localization),
            "checks": checks,
        },
        "independent_replication_required_after_pass": True,
        "canon_allowed": False,
    }
    out = ROOT / "evidence" / "V0_12C_SOURCE_WITNESSED_REEXECUTION_REPORT.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"status": status, **report["aggregate"]}, indent=2), flush=True)


if __name__ == "__main__":
    main()
