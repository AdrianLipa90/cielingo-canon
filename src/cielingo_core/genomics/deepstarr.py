"""Adapter for the public DeepSTARR train/validation/test dataset."""
from __future__ import annotations

import csv
from dataclasses import dataclass
from enum import Enum
import io
import math

from .sequence import SequenceRecord, parse_fasta

DEEPSTARR_DOI = "10.5281/zenodo.5502060"
DEEPSTARR_SOURCE_REPO = "bernardo-de-almeida/DeepSTARR"
DEEPSTARR_SOURCE_COMMIT = "b02e460c7581934bb6c8910e53be04da10688781"

DEEPSTARR_FILES = {
    "Train": {
        "fasta": "Sequences_Train.fa",
        "fasta_md5": "fe474a31c23db2daf7dc4d1fc49a8e5a",
        "activity": "Sequences_activity_Train.txt",
        "activity_md5": "4e65afa021fd426c74dbf24c31b8bbf9",
    },
    "Val": {
        "fasta": "Sequences_Val.fa",
        "fasta_md5": "9d1a0e5c9228aa033378af93074109e6",
        "activity": "Sequences_activity_Val.txt",
        "activity_md5": "5f30e863b2239e4f9ade6e7b81b3ff3c",
    },
    "Test": {
        "fasta": "Sequences_Test.fa",
        "fasta_md5": "c2d831a6e2cfb9345fa5e52de76bb453",
        "activity": "Sequences_activity_Test.txt",
        "activity_md5": "011690ca80cf967d56fefd0c1386419f",
    },
}


class DeepStarrSplit(str, Enum):
    TRAIN = "Train"
    VAL = "Val"
    TEST = "Test"


@dataclass(frozen=True)
class DeepStarrActivity:
    dev_log2_enrichment: float
    hk_log2_enrichment: float

    def __post_init__(self) -> None:
        if (
            not math.isfinite(self.dev_log2_enrichment)
            or not math.isfinite(self.hk_log2_enrichment)
        ):
            raise ValueError("DeepSTARR activities must be finite")


@dataclass(frozen=True)
class DeepStarrSample:
    sample_id: str
    sequence: SequenceRecord
    activity: DeepStarrActivity
    split: DeepStarrSplit
    row_index: int

    def to_dict(self) -> dict[str, object]:
        return {
            "sample_id": self.sample_id,
            "sequence": self.sequence.sequence,
            "split": self.split.value,
            "row_index": self.row_index,
            "Dev_log2_enrichment": self.activity.dev_log2_enrichment,
            "Hk_log2_enrichment": self.activity.hk_log2_enrichment,
            "provenance": {
                "doi": DEEPSTARR_DOI,
                "alignment": "ROW_ORDER",
                "source_repo": DEEPSTARR_SOURCE_REPO,
                "source_commit": DEEPSTARR_SOURCE_COMMIT,
            },
        }


def parse_deepstarr_activity_table(
    text: str,
) -> tuple[DeepStarrActivity, ...]:
    if not isinstance(text, str) or not text.strip():
        raise ValueError("activity table must be non-empty")

    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    required = {
        "Dev_log2_enrichment",
        "Hk_log2_enrichment",
    }
    if reader.fieldnames is None or not required <= set(reader.fieldnames):
        raise ValueError(
            "activity table must contain Dev_log2_enrichment "
            "and Hk_log2_enrichment"
        )

    rows: list[DeepStarrActivity] = []
    for index, row in enumerate(reader):
        try:
            dev = float(row["Dev_log2_enrichment"])
            hk = float(row["Hk_log2_enrichment"])
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"invalid DeepSTARR activity at row {index}"
            ) from exc
        rows.append(
            DeepStarrActivity(
                dev_log2_enrichment=dev,
                hk_log2_enrichment=hk,
            )
        )

    if not rows:
        raise ValueError("activity table contains no data rows")
    return tuple(rows)


def pair_deepstarr_split(
    fasta_text: str,
    activity_text: str,
    *,
    split: DeepStarrSplit,
) -> tuple[DeepStarrSample, ...]:
    """Pair FASTA and activity rows positionally, matching the source loader."""

    sequences = parse_fasta(fasta_text)
    activities = parse_deepstarr_activity_table(activity_text)

    if len(sequences) != len(activities):
        raise ValueError(
            "DeepSTARR FASTA/activity row count mismatch: "
            f"{len(sequences)} != {len(activities)}"
        )

    return tuple(
        DeepStarrSample(
            sample_id=sequence.record_id,
            sequence=sequence,
            activity=activity,
            split=split,
            row_index=index,
        )
        for index, (sequence, activity) in enumerate(
            zip(sequences, activities)
        )
    )


def deepstarr_manifest(
    split: DeepStarrSplit,
) -> dict[str, object]:
    return {
        "schema": "CIELINGO_DEEPSTARR_ADAPTER_V0_1",
        "dataset": "DeepSTARR",
        "doi": DEEPSTARR_DOI,
        "split": split.value,
        "files": dict(DEEPSTARR_FILES[split.value]),
        "alignment": "FASTA_AND_ACTIVITY_ROWS_ARE_POSITIONALLY_ALIGNED",
        "source_loader": "DeepSTARR/DeepSTARR_training.ipynb",
        "source_repo": DEEPSTARR_SOURCE_REPO,
        "source_commit": DEEPSTARR_SOURCE_COMMIT,
    }
