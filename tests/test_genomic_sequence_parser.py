from __future__ import annotations

import math

import pytest

from cielingo_core.genomics import (
    GenomicLevel,
    MotifDefinition,
    SequenceRecord,
    normalize_dna,
    parse_fasta,
    parse_genomic_grammar,
    reverse_complement_iupac,
    scan_motifs,
)


def test_parse_fasta_and_normalize_fail_loud():
    records = parse_fasta(">x description\nACGT\nACGT\n>y\nTTAA")
    assert [(r.record_id, r.sequence) for r in records] == [
        ("x description", "ACGTACGT"),
        ("y", "TTAA"),
    ]
    with pytest.raises(ValueError, match="unsupported DNA symbols"):
        normalize_dna("ACGU")


def test_iupac_and_reverse_strand_matching():
    motif = MotifDefinition("m", "ARY")
    assert reverse_complement_iupac("ARY") == "RYT"
    hits = scan_motifs("AATAGT", [motif])
    assert any(hit.motif_id == "m" for hit in hits)


def test_parser_builds_kaku_radical_concept_sentence_and_phase_edges():
    record = SequenceRecord("r", "AAACCCAAAAAACCC")
    motifs = [
        MotifDefinition("A3", "AAA", scan_reverse=False),
        MotifDefinition("C3", "CCC", scan_reverse=False),
    ]
    parsed = parse_genomic_grammar(
        record,
        motifs,
        helical_repeat_bp=10.5,
        max_relation_distance_bp=20,
    )
    assert parsed.sentence is not None
    assert parsed.sentence.level is GenomicLevel.SENTENCE
    assert all(
        radical.level is GenomicLevel.RADICAL
        for radical in parsed.radicals
    )
    assert all(
        kaku.level is GenomicLevel.KAKU
        for radical in parsed.radicals
        for kaku in radical.children
    )
    assert parsed.relations
    first = parsed.relations[0]
    assert 0.0 <= first.relative_phase_rad < 2 * math.pi
    assert parsed.to_dict()["epistemic_status"] == "COMPUTATIONAL_HYPOTHESIS"
    assert parsed.to_dict()["biological_equivalence_claim"] is False


def test_relation_cutoff_splits_components():
    record = SequenceRecord("r", "AAATTTTTTTTTTTTTTTTTTAAA")
    motifs = [MotifDefinition("A3", "AAA", scan_reverse=False)]
    parsed = parse_genomic_grammar(
        record,
        motifs,
        max_relation_distance_bp=5,
    )
    assert len(parsed.radicals) == 2
    assert len(parsed.relations) == 0
    assert len(parsed.concepts) == 2
