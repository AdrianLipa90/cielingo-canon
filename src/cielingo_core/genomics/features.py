"""Feature projections for sequence/geometry/phase ablations."""
from __future__ import annotations

from collections import Counter, defaultdict
import math

from .parser import GenomicParseResult
from .sequence import normalize_dna


def sequence_kmer_features(
    sequence: str,
    *,
    k: int = 2,
) -> dict[str, float]:
    seq = normalize_dna(sequence)
    if k < 1:
        raise ValueError("k must be positive")
    if len(seq) < k:
        return {}

    counts = Counter(seq[i : i + k] for i in range(len(seq) - k + 1))
    denominator = float(sum(counts.values()))
    return {
        f"seq:k{k}:{token}": count / denominator
        for token, count in sorted(counts.items())
    }


def relational_grammar_features(
    parsed: GenomicParseResult,
    *,
    distance_bin_bp: float = 10.0,
    include_phase: bool = True,
) -> dict[str, float]:
    """Project motif vocabulary and geometry, optionally adding phase."""

    if distance_bin_bp <= 0.0:
        raise ValueError("distance_bin_bp must be positive")

    output: dict[str, float] = defaultdict(float)
    hit_by_radical = {
        radical.unit_id: hit
        for radical, hit in zip(parsed.radicals, parsed.hits)
    }

    for hit in parsed.hits:
        output[f"motif:{hit.motif_id}:count"] += 1.0
        output[f"motif:{hit.motif_id}:strand:{hit.strand}"] += 1.0

    for relation in parsed.relations:
        left = hit_by_radical[relation.source_id]
        right = hit_by_radical[relation.target_id]
        pair = "|".join(sorted((left.motif_id, right.motif_id)))
        distance_bin = int(abs(relation.distance_bp) // distance_bin_bp)

        output[f"pair:{pair}:distance_bin:{distance_bin}"] += 1.0
        output[f"pair:{pair}:orientation:{relation.orientation}"] += 1.0

        if include_phase:
            output[f"pair:{pair}:phase_cos"] += math.cos(
                relation.relative_phase_rad
            )
            output[f"pair:{pair}:phase_sin"] += math.sin(
                relation.relative_phase_rad
            )

    return dict(sorted(output.items()))


def phase_grammar_features(
    parsed: GenomicParseResult,
    *,
    distance_bin_bp: float = 10.0,
) -> dict[str, float]:
    return relational_grammar_features(
        parsed,
        distance_bin_bp=distance_bin_bp,
        include_phase=True,
    )


def representation_feature_sets(
    parsed: GenomicParseResult,
    *,
    k: int = 2,
    distance_bin_bp: float = 10.0,
) -> dict[str, dict[str, float]]:
    """Return nested ablations that isolate phase from ordinary geometry."""

    baseline = sequence_kmer_features(parsed.record.sequence, k=k)

    geometry = dict(baseline)
    geometry.update(
        relational_grammar_features(
            parsed,
            distance_bin_bp=distance_bin_bp,
            include_phase=False,
        )
    )

    phase = dict(baseline)
    phase.update(
        relational_grammar_features(
            parsed,
            distance_bin_bp=distance_bin_bp,
            include_phase=True,
        )
    )

    return {
        "sequence_only": baseline,
        "sequence_plus_geometry": geometry,
        "sequence_plus_phase": phase,
    }
