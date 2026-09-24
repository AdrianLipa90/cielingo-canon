from __future__ import annotations

import json
from pathlib import Path
import torch

from ciel_lm_text import v0_12c_runner as core

SCHEMA = "CIEL_LM_V0_12D_WINDOW_ALIGNED_SOURCE_WITNESSED_REPORT_V1"
EXPERIMENT_NAMESPACE = "CIEL_LM_V0_12D_WINDOW_ALIGNED_SOURCE_WITNESSED"
SCIENTIFIC_NAMESPACE = core.SCIENTIFIC_NAMESPACE
PREREG_GITHUB_BLOB_SHA = "f509f66dd10df801bd946244207f361bcc82ec86"
SEEDS = [
    2146355770, 4209406639, 296633338, 1264981445,
    904540590, 3582976692, 3744929710, 1045778742,
    3593201550, 2018169425, 1153673219, 759882036,
]
SOURCE_MANIFEST_SHA256 = core.SOURCE_MANIFEST_SHA256
V0_12A_EXPECTED = core.V0_12A_EXPECTED


def validation_samples_internal(model, ids: list[int], raw: list[str], starts: list[int], carrier_block_size: int = 24):
    """Each admitted 24-token carrier window yields its 23 internal next-token transitions."""
    out = []
    with torch.no_grad():
        for start in starts:
            window_ids = ids[start:start + carrier_block_size]
            window_raw = raw[start:start + carrier_block_size]
            if len(window_ids) != carrier_block_size or len(window_raw) != carrier_block_size:
                raise RuntimeError("SHORT_CARRIER_WINDOW")
            xids, yids = window_ids[:-1], window_ids[1:]
            if len(xids) != 23 or len(yids) != 23:
                raise RuntimeError("VALIDATION_TRANSITION_COUNT_MISMATCH")
            logits, _ = model(torch.tensor([xids]))
            out.append((logits[0].detach().clone(), torch.tensor(yids, dtype=torch.long), window_raw))
    return out


_original_samples = core.samples


def _window_aligned_samples(model, ids, raw, starts, block_size):
    # Frozen V0.12D protocol: the 16 registered validation starts use 24-token
    # carrier windows and 23 internal LM transitions. Training still uses the
    # original 25-token slice -> 24 shifted targets.
    if len(starts) == 16:
        return validation_samples_internal(model, ids, raw, starts, block_size)
    return _original_samples(model, ids, raw, starts, block_size)


def _bind_protocol() -> None:
    core.SCHEMA = SCHEMA
    core.EXPERIMENT_NAMESPACE = EXPERIMENT_NAMESPACE
    core.PREREG_GITHUB_BLOB_SHA = PREREG_GITHUB_BLOB_SHA
    core.SEEDS = list(SEEDS)
    core.samples = _window_aligned_samples


def main() -> None:
    _bind_protocol()
    old = core.ROOT / "evidence" / "V0_12C_SOURCE_WITNESSED_REEXECUTION_REPORT.json"
    new = core.ROOT / "evidence" / "V0_12D_WINDOW_ALIGNED_SOURCE_WITNESSED_REPORT.json"
    if old.exists():
        old.unlink()
    core.main()
    if old.exists():
        old.replace(new)


# Re-export frozen helpers used by the conformance tests.
carrier_preflight = core.carrier_preflight
source_manifest_sha = core.source_manifest_sha
split_registered = core.split_registered
mask_preserving_shuffle = core.mask_preserving_shuffle
full_shuffle = core.full_shuffle
iszero = core.iszero


if __name__ == "__main__":
    main()
