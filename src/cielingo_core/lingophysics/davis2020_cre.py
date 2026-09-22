"""Deterministic adapter for the Davis et al. 2020 CRE design library."""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

SCHEMA = "CIELINGO_DAVIS2020_CRE_DESIGN_V0_1"

_DESIGN_RE = re.compile(
    r"^subpool(?P<subpool>\d+)_"
    r"(?P<architecture>\S+)\s+"
    r"(?P<spacing>\d+)\s+bp spacing\s+"
    r"(?P<context>.+?)_dist_(?P<distance>\d+)_(?P<background>.+)$"
)


@dataclass(frozen=True)
class DavisCreDesign:
    raw_name: str
    subpool: int
    architecture: str
    spacing_bp: int
    promoter_distance_bp: int
    context: str
    site_tokens: tuple[str, ...]
    background: str
    sequence: str | None = None

    @property
    def is_spacing_distance_series(self) -> bool:
        return self.subpool == 3 and self.architecture == "2BS"

    def to_relational_metadata(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA,
            "dataset": "Davis2020_CRE_MPRA",
            "subpool": self.subpool,
            "architecture": self.architecture,
            "spacing_bp": self.spacing_bp,
            "promoter_distance_bp": self.promoter_distance_bp,
            "context": self.context,
            "site_tokens": list(self.site_tokens),
            "background": self.background,
            "sequence_available": self.sequence is not None,
            "evidence_class": "DERIVED_FROM_PUBLIC_DESIGN_NAME",
        }


def parse_design_name(name: str) -> DavisCreDesign:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("design name must be a non-empty string")
    raw = name.strip()
    match = _DESIGN_RE.match(raw)
    if match is None:
        raise ValueError("unsupported Davis CRE design name")
    context = match.group("context")
    tokens = tuple(token for token in context.split("-") if token and token != "flank")
    return DavisCreDesign(
        raw_name=raw,
        subpool=int(match.group("subpool")),
        architecture=match.group("architecture"),
        spacing_bp=int(match.group("spacing")),
        promoter_distance_bp=int(match.group("distance")),
        context=context,
        site_tokens=tokens,
        background=match.group("background"),
    )


def parse_design_csv_line(line: str) -> DavisCreDesign:
    if not isinstance(line, str) or "," not in line:
        raise ValueError("expected one name,sequence CSV row")
    name, sequence = line.rstrip("\r\n").split(",", 1)
    sequence = sequence.strip().upper()
    if not sequence or any(base not in "ACGTN" for base in sequence):
        raise ValueError("sequence must contain only A/C/G/T/N")
    design = parse_design_name(name)
    return DavisCreDesign(
        raw_name=design.raw_name,
        subpool=design.subpool,
        architecture=design.architecture,
        spacing_bp=design.spacing_bp,
        promoter_distance_bp=design.promoter_distance_bp,
        context=design.context,
        site_tokens=design.site_tokens,
        background=design.background,
        sequence=sequence,
    )
