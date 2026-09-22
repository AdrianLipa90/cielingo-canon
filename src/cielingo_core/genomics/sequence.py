"""Sequence parsing and normalization for CIELingo genomic grammar."""
from __future__ import annotations

from dataclasses import dataclass

DNA_IUPAC = frozenset("ACGTRYSWKMBDHVN")


def normalize_dna(sequence: str) -> str:
    if not isinstance(sequence, str):
        raise ValueError("sequence must be a string")
    normalized = "".join(sequence.split()).upper()
    if not normalized:
        raise ValueError("sequence must be non-empty")
    bad = sorted(set(normalized) - DNA_IUPAC)
    if bad:
        raise ValueError(
            "sequence contains unsupported DNA symbols: " + ",".join(bad)
        )
    return normalized


@dataclass(frozen=True)
class SequenceRecord:
    record_id: str
    sequence: str

    def __post_init__(self) -> None:
        record_id = self.record_id.strip()
        if not record_id:
            raise ValueError("record_id must be non-empty")
        object.__setattr__(self, "record_id", record_id)
        object.__setattr__(self, "sequence", normalize_dna(self.sequence))


def parse_fasta(text: str) -> tuple[SequenceRecord, ...]:
    """Parse raw DNA or FASTA text into normalized immutable records."""

    if not isinstance(text, str) or not text.strip():
        raise ValueError("FASTA text must be non-empty")
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        raise ValueError("FASTA text must be non-empty")

    if not lines[0].startswith(">"):
        return (SequenceRecord("sequence_1", "".join(lines)),)

    records: list[SequenceRecord] = []
    current_id: str | None = None
    chunks: list[str] = []

    def flush() -> None:
        nonlocal current_id, chunks
        if current_id is None:
            return
        if not chunks:
            raise ValueError(f"FASTA record {current_id!r} has no sequence")
        records.append(SequenceRecord(current_id, "".join(chunks)))

    for line in lines:
        if line.startswith(">"):
            flush()
            current_id = line[1:].strip()
            chunks = []
            if not current_id:
                raise ValueError("FASTA header must contain a record id")
        else:
            if current_id is None:
                raise ValueError("FASTA sequence encountered before header")
            chunks.append(line)

    flush()
    if not records:
        raise ValueError("FASTA contained no records")

    ids = [record.record_id for record in records]
    if len(ids) != len(set(ids)):
        raise ValueError("FASTA record ids must be unique")
    return tuple(records)
