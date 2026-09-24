"""CIELingo lingophysics package."""
from __future__ import annotations

from .case_port_frame import CasePort, CasePortCase, CasePortFrame, extract_polish_case_port_frames
from .operator_signatures import (
    OPERATOR_SIGNATURES,
    OperatorPortSpec,
    OperatorSignature,
    OperatorTypingReport,
    UniversalRoleBinding,
    get_operator_signature,
    type_case_port_frame,
    type_polish_case_port_frames,
)
from .relation_hypergraph import (
    RELATION_HYPERGRAPH_SCHEMA,
    RelationEntityNode,
    RelationEventNode,
    RelationHypergraph,
    RelationIncidence,
    build_relation_hypergraph,
)
from .doctor import SurfaceSolutionDoctor, SentenceEquationDoctor, LocalJDoctor, RegionalSeparationDoctor, MeaningDebtDoctor, JCoherenceDoctor, SemanticNeuralStateDoctor, CrossLanguageAlignmentDoctor, ControlledAtlasDoctor, SentenceCardCouplingDoctor, CouplingAwareAlignmentDoctor, MeaningLoopDoctor, MeaningRepairRoutingDoctor, MeaningExportAndSignalDoctor, RuntimeBridgeDryRunDoctor, SelfFeedAuditDoctor, RuntimeAdapterReferenceDoctor, RuntimeAdapterExportDoctor, LingophysicsDoctor
from .sentence_equation import EquationTermKind, SentenceEquationTerm, SentenceEquation
from .orbital_semantics import (
    ORBITAL_SEMANTIC_VERSION,
    ORBITAL_SEMANTIC_EPISTEMIC,
    PHASE_DIMS,
    KakuState,
    OrbitalCell,
    OrbitalCellPair,
    LatentPhaseEnsemble,
    RadicalOrbital,
    ConceptOrbital,
    SemanticRelation,
    SentenceOrbital,
    hebrew_kaku,
    orbital_cell_pair,
    latent_phase_ensemble,
    phase_vector36_from_cells,
    moire_combine,
    phase_overlap,
    phase_fidelity,
    phasenav_semantic_payload,
)

__all__ = [
    'CasePort', 'CasePortCase', 'CasePortFrame', 'extract_polish_case_port_frames',
    'OPERATOR_SIGNATURES', 'OperatorPortSpec', 'OperatorSignature', 'OperatorTypingReport',
    'UniversalRoleBinding', 'get_operator_signature', 'type_case_port_frame', 'type_polish_case_port_frames',
    'RELATION_HYPERGRAPH_SCHEMA', 'RelationEntityNode', 'RelationEventNode', 'RelationHypergraph',
    'RelationIncidence', 'build_relation_hypergraph',
    'SurfaceSolutionDoctor', 'SentenceEquationDoctor', 'LocalJDoctor', 'RegionalSeparationDoctor',
    'MeaningDebtDoctor', 'JCoherenceDoctor', 'SemanticNeuralStateDoctor', 'CrossLanguageAlignmentDoctor',
    'ControlledAtlasDoctor', 'SentenceCardCouplingDoctor', 'CouplingAwareAlignmentDoctor', 'MeaningLoopDoctor',
    'MeaningRepairRoutingDoctor', 'MeaningExportAndSignalDoctor', 'RuntimeBridgeDryRunDoctor', 'SelfFeedAuditDoctor',
    'RuntimeAdapterReferenceDoctor', 'RuntimeAdapterExportDoctor', 'LingophysicsDoctor',
    'EquationTermKind', 'SentenceEquationTerm', 'SentenceEquation',
    'ORBITAL_SEMANTIC_VERSION', 'ORBITAL_SEMANTIC_EPISTEMIC', 'PHASE_DIMS',
    'KakuState', 'OrbitalCell', 'OrbitalCellPair', 'LatentPhaseEnsemble',
    'RadicalOrbital', 'ConceptOrbital', 'SemanticRelation', 'SentenceOrbital',
    'hebrew_kaku', 'orbital_cell_pair', 'latent_phase_ensemble',
    'phase_vector36_from_cells', 'moire_combine', 'phase_overlap', 'phase_fidelity',
    'phasenav_semantic_payload',
]
