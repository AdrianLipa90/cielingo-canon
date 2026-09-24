"""IUPAC motif definitions and deterministic motif scanning."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .sequence import normalize_dna

IUPAC: dict[str, frozenset[str]] = {
    "A": frozenset("A"),
    "C": frozenset("C"),
    "G": frozenset("G"),
    "T": frozenset("T"),
    "R": frozenset("AG"),
    "Y": frozenset("CT"),
    "S": frozenset("GC"),
    "W": frozenset("AT"),
    "K": frozenset("GT"),
    "M": frozenset("AC"),
    "B": frozenset("CGT"),
    "D": frozenset("AGT"),
    "H": frozenset("ACT"),
    "V": frozenset("ACG"),
    "N": frozenset("ACGT"),
}

COMPLEMENT = {
    "A": "T",
    "C": "G",
    "G": "C",
    "T": "A",
    "R": "Y",
    "Y": "R",
    "S": "S",
    "W": "W",
    "K": "M",
    "M": "K",
    "B": "V",
    "D": "H",
    "H": "D",
    "V": "B",
    "N": "N",
}


@dataclass(frozen=True)
class MotifDefinition:
    motif_id: str
    pattern: str
    scan_reverse: bool = True

    def __post_init__(self) -> None:
        motif_id = self.motif_id.strip()
        pattern = self.pattern.strip().upper()
        if not motif_id:
            raise ValueError("motif_id must be non-empty")
        if not pattern or set(pattern) - set(IUPAC):
            raise ValueError("motif pattern must use DNA IUPAC symbols")
        object.__setattr__(self, "motif_id", motif_id)
        object.__setattr__(self, "pattern", pattern)


@dataclass(frozen=True)
class MotifHit:
    motif_id: str
    pattern: str
    start: int
    end: int
    strand: str
    matched_sequence: str

    @property
    def center_bp(self) -> float:
        return (self.start + self.end - 1) / 2.0

    def to_dict(self) -> dict[str, object]:
        return {
            "motif_id": self.motif_id,
            "pattern": self.pattern,
            "start": self.start,
            "end": self.end,
            "strand": self.strand,
            "matched_sequence": self.matched_sequence,
            "center_bp": self.center_bp,
        }


def reverse_complement_iupac(pattern: str) -> str:
    value = pattern.strip().upper()
    if not value or set(value) - set(IUPAC):
        raise ValueError("pattern must use DNA IUPAC symbols")
    return "".join(COMPLEMENT[symbol] for symbol in reversed(value))


def _matches(window: str, pattern: str) -> bool:
    # Conservative ambiguity handling: a sequence symbol matches only when every
    # base it could represent is admitted by the motif symbol.
    return all(IUPAC[base] <= IUPAC[symbol] for base, symbol in zip(window, pattern))


def scan_motifs(
    sequence: str,
    motifs: Sequence[MotifDefinition],
) -> tuple[MotifHit, ...]:
    seq = normalize_dna(sequence)
    hits: list[MotifHit] = []

    for motif in motifs:
        variants = [("+", motif.pattern)]
        reverse = reverse_complement_iupac(motif.pattern)
        if motif.scan_reverse and reverse != motif.pattern:
            variants.append(("-", reverse))

        seen: set[tuple[str, int, int, str]] = set()
        for strand, query in variants:
            width = len(query)
            for start in range(0, len(seq) - width + 1):
                window = seq[start : start + width]
                if not _matches(window, query):
                    continue
                key = (motif.motif_id, start, start + width, strand)
                if key in seen:
                    continue
                seen.add(key)
                hits.append(
                    MotifHit(
                        motif_id=motif.motif_id,
                        pattern=motif.pattern,
                        start=start,
                        end=start + width,
                        strand=strand,
                        matched_sequence=window,
                    )
                )

    hits.sort(key=lambda hit: (hit.start, hit.end, hit.motif_id, hit.strand))
    return tuple(hits)
