"""CIELingo genomic grammar research surface."""
from __future__ import annotations

from .deepstarr import (
    DEEPSTARR_DOI,
    DEEPSTARR_FILES,
    DeepStarrActivity,
    DeepStarrSample,
    DeepStarrSplit,
    deepstarr_manifest,
    pair_deepstarr_split,
    parse_deepstarr_activity_table,
)
from .deepstarr_benchmark import (
    DeepStarrTarget,
    run_deepstarr_regression_ablation,
)
from .experiment import (
    LabeledFeatures,
    compare_feature_sets,
    leave_one_out_nearest_neighbor,
)
from .features import (
    phase_grammar_features,
    relational_grammar_features,
    representation_feature_sets,
    sequence_kmer_features,
)
from .grammar import (
    GenomicLevel,
    GenomicRelation,
    GenomicUnit,
    HelicalPhaseModel,
    assemble_unit,
    relation_from_positions,
)
from .gremlin_pipeline import (
    FULL_AUDIT_SPECIALISTS,
    GenomicDispatch,
    GenomicGremlinPipeline,
    GenomicPipelineMode,
)
from .motifs import (
    MotifDefinition,
    MotifHit,
    reverse_complement_iupac,
    scan_motifs,
)
from .parser import GenomicParseResult, parse_genomic_grammar
from .periodicity import (
    SpacerReadout,
    fit_periodic_readout,
    scan_periods,
)
from .project import (
    CompiledGenomicSample,
    GenomicGrammarProject,
    GenomicGrammarProjectConfig,
)
from .regression import (
    RegressionExample,
    RidgeRegressionModel,
    fit_and_evaluate,
    fit_ridge,
    regression_metrics,
)
from .sequence import SequenceRecord, normalize_dna, parse_fasta
from .smith2013 import (
    SMITH2013_CLASS_COUNTS,
    SMITH2013_DOI,
    SMITH2013_PMID,
    SMITH2013_RAW_SCHEMA_STATUS,
    SMITH2013_SRA,
    SMITH2013_SUPPLEMENTARY_TABLE4_URL,
    SMITH2013_TEMPLATES,
    SMITH2013_TFBS,
    Smith2013CanonicalRow,
    Smith2013SchemaReceipt,
    SmithSRESClass,
    admit_smith2013_rows,
    class_i_spacer_readouts,
    require_verified_smith2013_schema,
    smith2013_manifest,
)

__all__ = [
    "DEEPSTARR_DOI",
    "DEEPSTARR_FILES",
    "DeepStarrActivity",
    "DeepStarrSample",
    "DeepStarrSplit",
    "deepstarr_manifest",
    "pair_deepstarr_split",
    "parse_deepstarr_activity_table",
    "DeepStarrTarget",
    "run_deepstarr_regression_ablation",
    "LabeledFeatures",
    "compare_feature_sets",
    "leave_one_out_nearest_neighbor",
    "phase_grammar_features",
    "relational_grammar_features",
    "representation_feature_sets",
    "sequence_kmer_features",
    "GenomicLevel",
    "GenomicRelation",
    "GenomicUnit",
    "HelicalPhaseModel",
    "assemble_unit",
    "relation_from_positions",
    "FULL_AUDIT_SPECIALISTS",
    "GenomicDispatch",
    "GenomicGremlinPipeline",
    "GenomicPipelineMode",
    "MotifDefinition",
    "MotifHit",
    "reverse_complement_iupac",
    "scan_motifs",
    "GenomicParseResult",
    "parse_genomic_grammar",
    "SpacerReadout",
    "fit_periodic_readout",
    "scan_periods",
    "CompiledGenomicSample",
    "GenomicGrammarProject",
    "GenomicGrammarProjectConfig",
    "RegressionExample",
    "RidgeRegressionModel",
    "fit_and_evaluate",
    "fit_ridge",
    "regression_metrics",
    "SequenceRecord",
    "normalize_dna",
    "parse_fasta",
    "SMITH2013_CLASS_COUNTS",
    "SMITH2013_DOI",
    "SMITH2013_PMID",
    "SMITH2013_RAW_SCHEMA_STATUS",
    "SMITH2013_SRA",
    "SMITH2013_SUPPLEMENTARY_TABLE4_URL",
    "SMITH2013_TEMPLATES",
    "SMITH2013_TFBS",
    "Smith2013CanonicalRow",
    "Smith2013SchemaReceipt",
    "SmithSRESClass",
    "admit_smith2013_rows",
    "class_i_spacer_readouts",
    "require_verified_smith2013_schema",
    "smith2013_manifest",
]
