from __future__ import annotations

import pytest

from cielingo_core.genomics import (
    SMITH2013_SUPPLEMENTARY_TABLE4_URL,
    Smith2013CanonicalRow,
    Smith2013SchemaReceipt,
    SmithSRESClass,
    admit_smith2013_rows,
    class_i_spacer_readouts,
    smith2013_manifest,
)


FIELDS = frozenset(
    {
        "sres_id",
        "class_id",
        "template_id",
        "expression",
        "motif_ids",
        "copy_number",
        "uniform_spacing_bp",
    }
)


def receipt(*, verified=True, fields=FIELDS):
    return Smith2013SchemaReceipt(
        source_uri=SMITH2013_SUPPLEMENTARY_TABLE4_URL,
        source_sha256="a" * 64,
        verified=verified,
        canonical_fields=fields,
    )


def row(identifier, spacing, expression):
    return Smith2013CanonicalRow(
        sres_id=identifier,
        class_id=SmithSRESClass.I,
        template_id="template_1",
        expression=expression,
        motif_ids=("HNF1A", "HNF1A"),
        copy_number=2,
        uniform_spacing_bp=spacing,
    )


def test_manifest_pins_verified_study_metadata_without_guessing_xlsx_schema():
    manifest = smith2013_manifest()
    assert manifest["doi"] == "10.1038/ng.2713"
    assert manifest["sra_accession"] == "SRP018414"
    assert manifest["total_sres"] == 4966
    assert manifest["class_counts"] == {
        "I": 533,
        "II": 1797,
        "III": 2636,
    }
    assert manifest["raw_schema_status"] == "SCHEMA_UNVERIFIED_BINARY_XLSX"
    assert manifest["import_gate"] == "VERIFIED_RAW_XLSX_SCHEMA_RECEIPT_REQUIRED"
    assert manifest["canon_allowed"] is False


def test_import_is_fail_closed_until_real_raw_schema_is_verified():
    rows = [row("s1", 5.0, 0.2)]
    with pytest.raises(PermissionError, match="unverified"):
        admit_smith2013_rows(rows, receipt(verified=False))

    with pytest.raises(PermissionError, match="lacks canonical fields"):
        admit_smith2013_rows(
            rows,
            receipt(fields=FIELDS - {"uniform_spacing_bp"}),
        )


def test_class_i_spacing_series_fixes_composition_and_template():
    rows = admit_smith2013_rows(
        [
            row("s10", 10.0, 0.8),
            row("s05", 5.0, 0.3),
            Smith2013CanonicalRow(
                sres_id="other",
                class_id=SmithSRESClass.I,
                template_id="template_2",
                expression=0.9,
                motif_ids=("HNF1A", "HNF1A"),
                copy_number=2,
                uniform_spacing_bp=7.0,
            ),
        ],
        receipt(),
    )
    readouts = class_i_spacer_readouts(
        rows,
        motif_id="HNF1A",
        copy_number=2,
        template_id="template_1",
    )
    assert [point.spacer_bp for point in readouts] == [5.0, 10.0]
    assert [point.value for point in readouts] == [0.3, 0.8]


def test_class_i_spacing_series_rejects_unverified_missing_spacing():
    rows = [
        Smith2013CanonicalRow(
            sres_id="s1",
            class_id=SmithSRESClass.I,
            template_id="template_1",
            expression=0.5,
            motif_ids=("FOXA1", "FOXA1"),
            copy_number=2,
            uniform_spacing_bp=None,
        )
    ]
    with pytest.raises(ValueError, match="lack verified"):
        class_i_spacer_readouts(
            rows,
            motif_id="FOXA1",
            copy_number=2,
            template_id="template_1",
        )
