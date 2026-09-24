"""High-level runner for the CIELingo genomic-grammar experiment."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Sequence

from .experiment import LabeledFeatures, compare_feature_sets
from .features import representation_feature_sets
from .motifs import MotifDefinition
from .parser import GenomicParseResult, parse_genomic_grammar
from .sequence import SequenceRecord, parse_fasta


@dataclass(frozen=True)
class GenomicGrammarProjectConfig:
    motifs: tuple[MotifDefinition, ...]
    helical_repeat_bp: float = 10.5
    max_relation_distance_bp: float = 80.0
    kmer_k: int = 2
    distance_bin_bp: float = 10.0

    def __post_init__(self) -> None:
        if not self.motifs:
            raise ValueError("at least one motif definition is required")
        if self.kmer_k < 1:
            raise ValueError("kmer_k must be positive")
        if self.max_relation_distance_bp <= 0.0:
            raise ValueError("max_relation_distance_bp must be positive")
        if self.distance_bin_bp <= 0.0:
            raise ValueError("distance_bin_bp must be positive")


@dataclass(frozen=True)
class CompiledGenomicSample:
    record: SequenceRecord
    parsed: GenomicParseResult
    feature_sets: Mapping[str, Mapping[str, float]]

    def analysis_unit(self):
        if self.parsed.sentence is None:
            raise ValueError("sample has no motif-derived SENTENCE unit")
        return self.parsed.sentence


class GenomicGrammarProject:
    """Compile FASTA records into auditable grammar/feature ablations."""

    def __init__(self, config: GenomicGrammarProjectConfig):
        self.config = config

    def compile_record(
        self,
        record: SequenceRecord,
    ) -> CompiledGenomicSample:
        parsed = parse_genomic_grammar(
            record,
            self.config.motifs,
            helical_repeat_bp=self.config.helical_repeat_bp,
            max_relation_distance_bp=self.config.max_relation_distance_bp,
        )
        feature_sets = representation_feature_sets(
            parsed,
            k=self.config.kmer_k,
            distance_bin_bp=self.config.distance_bin_bp,
        )
        return CompiledGenomicSample(
            record=record,
            parsed=parsed,
            feature_sets=feature_sets,
        )

    def compile_fasta(
        self,
        text: str,
    ) -> tuple[CompiledGenomicSample, ...]:
        return tuple(
            self.compile_record(record)
            for record in parse_fasta(text)
        )

    def labeled_feature_sets(
        self,
        samples: Sequence[CompiledGenomicSample],
        labels: Mapping[str, str],
    ) -> dict[str, list[LabeledFeatures]]:
        if not samples:
            raise ValueError("at least one compiled sample is required")

        sample_ids = {sample.record.record_id for sample in samples}
        if set(labels) != sample_ids:
            raise ValueError("labels must match compiled sample ids exactly")

        names = set(samples[0].feature_sets)
        if any(set(sample.feature_sets) != names for sample in samples):
            raise ValueError(
                "all samples must expose the same feature-set names"
            )

        return {
            name: [
                LabeledFeatures(
                    sample_id=sample.record.record_id,
                    label=labels[sample.record.record_id],
                    features=sample.feature_sets[name],
                )
                for sample in samples
            ]
            for name in sorted(names)
        }

    def evaluate_ablation(
        self,
        samples: Sequence[CompiledGenomicSample],
        labels: Mapping[str, str],
    ) -> dict[str, object]:
        result = compare_feature_sets(
            self.labeled_feature_sets(samples, labels)
        )
        return {
            **result,
            "project_schema": "CIELINGO_GENOMIC_GRAMMAR_PROJECT_V0_1",
            "feature_order": [
                "sequence_only",
                "sequence_plus_geometry",
                "sequence_plus_phase",
            ],
            "phase_increment_test": (
                "sequence_plus_phase vs sequence_plus_geometry"
            ),
            "canon_allowed": False,
        }
