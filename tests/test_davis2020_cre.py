from __future__ import annotations

import pytest

from cielingo_core.lingophysics.davis2020_cre import parse_design_csv_line, parse_design_name


REAL_PUBLIC_NAME = (
    "subpool3_2BS 0 bp spacing flank-con-con-flank_dist_130_"
    "scramble pGL4.29 Promega 1-63 + 1-87"
)


def test_parse_real_davis_spacing_distance_name() -> None:
    row = parse_design_name(REAL_PUBLIC_NAME)
    assert row.subpool == 3
    assert row.architecture == "2BS"
    assert row.spacing_bp == 0
    assert row.promoter_distance_bp == 130
    assert row.site_tokens == ("con", "con")
    assert row.is_spacing_distance_series is True
    meta = row.to_relational_metadata()
    assert meta["evidence_class"] == "DERIVED_FROM_PUBLIC_DESIGN_NAME"


def test_parse_csv_line_preserves_sequence_without_interpreting_expression() -> None:
    row = parse_design_csv_line(REAL_PUBLIC_NAME + ",ACGTACGTNN")
    assert row.sequence == "ACGTACGTNN"
    assert row.to_relational_metadata()["sequence_available"] is True


def test_malformed_name_fails_closed() -> None:
    with pytest.raises(ValueError, match="unsupported Davis CRE design name"):
        parse_design_name("subpool3_unknown")
