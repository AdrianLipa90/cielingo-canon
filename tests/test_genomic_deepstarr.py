from __future__ import annotations

import pytest

from cielingo_core.genomics import (
    DeepStarrSplit,
    deepstarr_manifest,
    pair_deepstarr_split,
    parse_deepstarr_activity_table,
)


def test_deepstarr_adapter_preserves_full_fasta_header_and_row_order():
    fasta = (
        ">chr2R:1-250 enhancer A\nACGT\n"
        ">chr2R:251-500 enhancer B\nTGCA"
    )
    table = (
        "Dev_log2_enrichment\tHk_log2_enrichment\n"
        "1.5\t-0.5\n"
        "2.0\t0.25\n"
    )

    samples = pair_deepstarr_split(
        fasta,
        table,
        split=DeepStarrSplit.TEST,
    )

    assert [sample.sample_id for sample in samples] == [
        "chr2R:1-250 enhancer A",
        "chr2R:251-500 enhancer B",
    ]
    assert samples[0].activity.dev_log2_enrichment == 1.5
    assert samples[1].row_index == 1
    assert (
        samples[0].to_dict()["provenance"]["alignment"]
        == "ROW_ORDER"
    )


def test_deepstarr_adapter_rejects_schema_and_length_mismatch():
    with pytest.raises(ValueError, match="must contain"):
        parse_deepstarr_activity_table("x\ty\n1\t2\n")

    with pytest.raises(ValueError, match="row count mismatch"):
        pair_deepstarr_split(
            ">a\nAAAA\n>b\nCCCC",
            (
                "Dev_log2_enrichment\tHk_log2_enrichment\n"
                "1\t2\n"
            ),
            split=DeepStarrSplit.TEST,
        )


def test_deepstarr_manifest_pins_public_dataset_and_checksums():
    manifest = deepstarr_manifest(DeepStarrSplit.TEST)
    assert manifest["doi"] == "10.5281/zenodo.5502060"
    assert (
        manifest["files"]["fasta_md5"]
        == "c2d831a6e2cfb9345fa5e52de76bb453"
    )
    assert (
        manifest["alignment"]
        == "FASTA_AND_ACTIVITY_ROWS_ARE_POSITIONALLY_ALIGNED"
    )
