from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import zipfile

from cleaner import tokens_from_markdown_bytes
from carrier import Card, ExactMultilingualCarrier

EXPECTED_ARCHIVE_SHA = "fef25a4cb20380483fec5b3e84ad8a2d1465e6a53ecf6dfd9ec42ec67d82e9ef"
EXPECTED_UNIVERSE_SHA = "9d5530ece47dc8132d2e015ab0f0c7d7e75155ee75ba2744ad602d1acde63d88"
EXPECTED_ATLAS_SHA = "c3eaf295517fa8116528de150be8ec434b8fa2565ca84d7f946c21ef2d651050"
HELDOUT = (
    "docs/operations/README.md",
    "docs/object_cards/satellites/SAT-P3-0001.md",
    "docs/integration/SAPIENS_SURFACE_BINDING.md",
    "docs/MASTER_PLAN_4_ALL_AGENTS_ATTENTION.md",
    "docs/operations/OFFLINE_DEPENDENCY_BUNDLE_V1.md",
    "docs/architecture/POST_MERGE_RECONCILIATION.md",
    "docs/integration/ORBITAL_INFRASTRUCTURE_RULES.md",
)


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def rounded_starts(token_count: int, block: int, n: int) -> list[int]:
    max_start = max(0, token_count - block)
    starts = sorted(set(round(i * max_start / (n - 1)) for i in range(n))) if n > 1 else [0]
    if len(starts) != n:
        raise RuntimeError(f"WINDOW_START_COLLISION:{len(starts)}:{n}:{token_count}")
    return starts


def extract_root_docs(archive: Path) -> dict[str, bytes]:
    if sha256_bytes(archive.read_bytes()) != EXPECTED_ARCHIVE_SHA:
        raise RuntimeError("SOURCE_ARCHIVE_SHA_MISMATCH")
    with zipfile.ZipFile(archive) as z:
        if z.testzip() is not None:
            raise RuntimeError("SOURCE_ARCHIVE_TESTZIP_FAIL")
        roots = sorted({n.split("/docs/", 1)[0] for n in z.namelist() if "/docs/" in n and n.endswith(".md")})
        candidates: list[tuple[str, dict[str, bytes]]] = []
        for root in roots:
            prefix = root + "/docs/"
            mapping = {}
            for n in z.namelist():
                if n.startswith(prefix) and n.endswith(".md"):
                    rel = n[len(root)+1:]
                    mapping[rel] = z.read(n)
            if len(mapping) == 109 and all(h in mapping for h in HELDOUT):
                candidates.append((root, mapping))
        if len(candidates) != 1:
            raise RuntimeError(f"SOURCE_ROOT_RESOLUTION_FAIL:{[(r,len(m)) for r,m in candidates]}")
        return candidates[0][1]


def universe_sha(docs: dict[str, bytes]) -> str:
    mapping = {p: sha256_bytes(raw) for p, raw in sorted(docs.items())}
    payload = json.dumps(mapping, sort_keys=True, separators=(",", ":")).encode()
    return sha256_bytes(payload)


def build_streams(docs: dict[str, bytes]) -> tuple[list[str], list[str]]:
    train: list[str] = []
    valid: list[str] = []
    held = set(HELDOUT)
    for path in sorted(docs):
        toks = tokens_from_markdown_bytes(docs[path])
        (valid if path in held else train).extend(toks)
    return train, valid


def summarize(carrier: ExactMultilingualCarrier, tokens: list[str], n: int) -> dict:
    starts = rounded_starts(len(tokens), 24, n)
    rows = []
    for st in starts:
        row = carrier.window(tokens[st:st+24])
        row["start"] = st
        rows.append(row)
    nz = [r for r in rows if any(abs(x) > 0.0 for x in r["vector"])]
    unique_nz = {tuple(round(float(x), 15) for x in r["vector"]) for r in nz}
    scores = [s for r in rows for s in r["candidate_scores"]]
    return {
        "windows": n,
        "starts": starts,
        "nonzero_relation_windows": len(nz),
        "unique_nonzero_vectors": len(unique_nz),
        "total_exact_candidates": sum(r["candidate_count"] for r in rows),
        "operator_bound_candidates": sum(r["operator_bound_candidate_count"] for r in rows),
        "all_candidate_scores_exact": all(s == 1.0 for s in scores),
        "rows": rows,
    }


def self_test() -> dict:
    cards = [
        Card("op","en",1,("run",),("RUN",),(),None,False),
        Card("concept","en",2,("source",),(),(),None,False),
        Card("frame_a","en",7,("alpha",),(),(),None,False),
        Card("frame_b","pl",7,("beta",),(),(),None,False),
    ]
    c = ExactMultilingualCarrier(cards)
    toks = ["run","source","alpha","beta"] + [f"x{i}" for i in range(20)]
    r = c.window(toks)
    assert r["candidate_count"] == 4
    assert r["operator_bound_candidate_count"] == 1
    assert r["candidate_scores"] == [1.0] * 4
    assert r["vector"][0] > 0.0 and r["vector"][1] > 0.0
    assert r["vector"][2] == 0.0 and r["vector"][3] == 0.0
    assert c.window(["unknown"] * 24)["vector"] == [0.0,0.0,0.0,0.0]
    return {"status":"PASS","vector":r["vector"]}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive")
    ap.add_argument("--atlas")
    ap.add_argument("--output")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        print(json.dumps(self_test(), sort_keys=True)); return
    if not (args.archive and args.atlas and args.output):
        raise SystemExit("--archive --atlas --output required")
    archive = Path(args.archive); atlas = Path(args.atlas)
    if sha256_bytes(atlas.read_bytes()) != EXPECTED_ATLAS_SHA:
        raise SystemExit("ATLAS_SHA_MISMATCH")
    docs = extract_root_docs(archive)
    u = universe_sha(docs)
    if u != EXPECTED_UNIVERSE_SHA or len(docs) != 109:
        raise SystemExit(f"SOURCE_UNIVERSE_MISMATCH:{len(docs)}:{u}")
    train, valid = build_streams(docs)
    carrier = ExactMultilingualCarrier.from_jsonl(atlas)
    validation = summarize(carrier, valid, 16)
    training = summarize(carrier, train, 64)
    gate = {
        "source_hashes": u == EXPECTED_UNIVERSE_SHA,
        "all_candidate_scores_exact": validation["all_candidate_scores_exact"] and training["all_candidate_scores_exact"],
        "validation_nonzero_relation_windows": validation["nonzero_relation_windows"] >= 8,
        "training_nonzero_relation_windows": training["nonzero_relation_windows"] >= 16,
        "unique_nonzero_validation_vectors": validation["unique_nonzero_vectors"] >= 2,
    }
    report = {
        "schema":"CIEL_LM_V0_14A_R3_CARRIER_REPORT_V1",
        "status":"PASS_CARRIER_ADMISSION" if all(gate.values()) else "BLOCK_CARRIER_ADMISSION",
        "source_archive_sha256":EXPECTED_ARCHIVE_SHA,
        "source_universe_sha256":u,
        "candidate_count":len(docs),
        "heldout_files":list(HELDOUT),
        "train_tokens":len(train),
        "validation_tokens":len(valid),
        "training":training,
        "validation":validation,
        "gate":gate,
        "lm_quality_outcome_observed":False,
        "canon_allowed":False,
    }
    Path(args.output).write_text(json.dumps(report, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print(json.dumps({"status":report["status"],"train_nonzero":training["nonzero_relation_windows"],"validation_nonzero":validation["nonzero_relation_windows"],"validation_unique_nonzero":validation["unique_nonzero_vectors"]},sort_keys=True))

if __name__ == "__main__":
    main()
