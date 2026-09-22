"""Fail-closed study contract for Smith et al. Nature Genetics 2013.

The public paper and supplementary-file location are pinned here. The raw
Supplementary Table 4 workbook schema is intentionally NOT guessed: callers
must provide a verified schema/provenance receipt before canonical rows are
admitted for phase analysis.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import math
from typing import Mapping, Sequence

from .periodicity import SpacerReadout

SMITH2013_DOI = "10.1038/ng.2713"
SMITH2013_PMID = "23892608"
SMITH2013_SRA = "SRP018414"
SMITH2013_SUPPLEMENTARY_TABLE4_URL = (
    "https://media.springernature.com/original/"
    "springer-static/esm/art%3A10.1038%2Fng.2713/"
    "MediaObjects/41588_2013_BFng2713_MOESM50_ESM.xlsx"
)
SMITH2013_RAW_SCHEMA_STATUS = "SCHEMA_UNVERIFIED_BINARY_XLSX"

SMITH2013_CLASS_COUNTS = {
    "I": 533,
    "II": 1797,
    "III": 2636,
}
SMITH2013_TOTAL_SRES = 4966
SMITH2013_TFBS = (
    "AHR/ARNT",
    "CEBPA",
    "FOXA1",
    "GATA4",
    "HNF1A",
    "HNF4A",
    "NR2F2",
    "ONECUT1",
    "PPARA",
    "RXRA",
    "TFAP2C",
    "XBP1",
)
SMITH2013_TEMPLATES = {
    "template_1": "hg19 chr9:83712599-83712766",
    "template_2": "hg19 chr2:211153238-211153405",
}


class SmithSRESClass(str, Enum):
    I = "I"
    II = "II"
    III = "III"


@dataclass(frozen=True)
class Smith2013SchemaReceipt:
    """Evidence that raw Supplementary Table 4 columns were actually inspected."""

    source_uri: str
    source_sha256: str
    verified: bool
    canonical_fields: frozenset[str] = field(default_factory=frozenset)
    notes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.source_uri, str) or not self.source_uri.strip():
            raise ValueError("source_uri must be non-empty")
        if not isinstance(self.source_sha256, str) or len(self.source_sha256.strip()) != 64:
            raise ValueError("source_sha256 must be a 64-character digest")


@dataclass(frozen=True)
class Smith2013CanonicalRow:
    """Normalized row admitted only after verified raw-schema inspection."""

    sres_id: str
    class_id: SmithSRESClass
    template_id: str
    expression: float
    motif_ids: tuple[str, ...]
    copy_number: int
    uniform_spacing_bp: float | None = None

    def __post_init__(self) -> None:
        if not self.sres_id.strip():
            raise ValueError("sres_id must be non-empty")
        if not self.template_id.strip():
            raise ValueError("template_id must be non-empty")
        if not math.isfinite(self.expression) or not 0.0 <= self.expression <= 1.0:
            raise ValueError("expression must be finite and in [0, 1]")
        if self.copy_number < 1:
            raise ValueError("copy_number must be positive")
        if not self.motif_ids or any(not motif.strip() for motif in self.motif_ids):
            raise ValueError("motif_ids must be non-empty")
        if self.uniform_spacing_bp is not None:
            if (
                not math.isfinite(self.uniform_spacing_bp)
                or self.uniform_spacing_bp < 0.0
            ):
                raise ValueError("uniform_spacing_bp must be finite and non-negative")


_REQUIRED_CANONICAL_FIELDS = frozenset(
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


def require_verified_smith2013_schema(
    receipt: Smith2013SchemaReceipt,
) -> None:
    if receipt.source_uri != SMITH2013_SUPPLEMENTARY_TABLE4_URL:
        raise PermissionError("Smith2013 source URI is not the pinned Supplementary Table 4")
    if receipt.verified is not True:
        raise PermissionError(
            "Smith2013 raw XLSX schema is unverified; canonical import is fail-closed"
        )
    missing = sorted(_REQUIRED_CANONICAL_FIELDS - receipt.canonical_fields)
    if missing:
        raise PermissionError(
            "Smith2013 schema receipt lacks canonical fields: " + ", ".join(missing)
        )


def admit_smith2013_rows(
    rows: Sequence[Smith2013CanonicalRow],
    receipt: Smith2013SchemaReceipt,
) -> tuple[Smith2013CanonicalRow, ...]:
    """Admit normalized rows only after explicit raw-schema verification."""

    require_verified_smith2013_schema(receipt)
    admitted = tuple(rows)
    if not admitted:
        raise ValueError("at least one Smith2013 row is required")
    ids = [row.sres_id for row in admitted]
    if len(ids) != len(set(ids)):
        raise ValueError("Smith2013 canonical sres_id values must be unique")
    return admitted


def class_i_spacer_readouts(
    rows: Sequence[Smith2013CanonicalRow],
    *,
    motif_id: str,
    copy_number: int,
    template_id: str,
) -> tuple[SpacerReadout, ...]:
    """Extract a composition-matched Class-I spacing series.

    This intentionally fixes motif identity, copy number and template before
    varying spacing. Missing spacing metadata fails loudly.
    """

    motif = motif_id.strip()
    template = template_id.strip()
    if not motif or not template:
        raise ValueError("motif_id and template_id must be non-empty")
    if copy_number < 1:
        raise ValueError("copy_number must be positive")

    selected = [
        row
        for row in rows
        if row.class_id is SmithSRESClass.I
        and row.copy_number == copy_number
        and row.template_id == template
        and tuple(dict.fromkeys(row.motif_ids)) == (motif,)
    ]
    if not selected:
        raise ValueError("no composition-matched Smith2013 Class-I rows")

    if any(row.uniform_spacing_bp is None for row in selected):
        raise ValueError(
            "selected Smith2013 Class-I rows lack verified uniform_spacing_bp"
        )

    selected.sort(key=lambda row: (float(row.uniform_spacing_bp), row.sres_id))
    return tuple(
        SpacerReadout(
            spacer_bp=float(row.uniform_spacing_bp),
            value=row.expression,
        )
        for row in selected
    )


def smith2013_manifest() -> dict[str, object]:
    return {
        "schema": "CIELINGO_SMITH2013_SPACING_MANIFEST_V0_1",
        "study": "Massively parallel decoding of mammalian regulatory sequences supports a flexible organizational model",
        "doi": SMITH2013_DOI,
        "pmid": SMITH2013_PMID,
        "sra_accession": SMITH2013_SRA,
        "supplementary_table_4": SMITH2013_SUPPLEMENTARY_TABLE4_URL,
        "raw_schema_status": SMITH2013_RAW_SCHEMA_STATUS,
        "class_counts": dict(SMITH2013_CLASS_COUNTS),
        "total_sres": SMITH2013_TOTAL_SRES,
        "tfbs": list(SMITH2013_TFBS),
        "templates": dict(SMITH2013_TEMPLATES),
        "class_i_contract": {
            "count": SMITH2013_CLASS_COUNTS["I"],
            "homotypic": True,
            "copy_numbers": [1, 2, 4, 8],
            "spacing_varied": True,
        },
        "import_gate": "VERIFIED_RAW_XLSX_SCHEMA_RECEIPT_REQUIRED",
        "canon_allowed": False,
    }
