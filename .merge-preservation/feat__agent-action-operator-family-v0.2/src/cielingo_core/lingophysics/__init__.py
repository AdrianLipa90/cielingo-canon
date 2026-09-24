"""CIELingo lingophysics package."""
from __future__ import annotations

from . import case_port_frame as _case_port_frame
from . import operator_signatures as _operator_signatures
from .case_port_frame import CasePort, CasePortCase, CasePortFrame
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
from .action_operator_family import (
    ACTION_OPERATOR_FAMILY_VERSION,
    ACTION_OPERATOR_SIGNATURES,
    ACTION_SCOPE_BASIS,
    extract_polish_action_case_port_frames,
    install_agent_action_operator_family,
)

# Explicit additive registration before relation_hypergraph/sentence_equation import
# so all direct submodule consumers observe one typed extractor/signature registry.
install_agent_action_operator_family(_case_port_frame, _operator_signatures)
extract_polish_case_port_frames = _case_port_frame.extract_polish_case_port_frames

from .relation_entity_card_bindings import (
    CARD_BINDING_BASIS,
    RELATION_ENTITY_CARD_BINDINGS_SCHEMA,
    RelationEntityCardBinding,
    RelationEntityCardBindings,
    build_relation_entity_card_bindings,
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

__all__ = [
    'CasePort', 'CasePortCase', 'CasePortFrame', 'extract_polish_case_port_frames',
    'OPERATOR_SIGNATURES', 'OperatorPortSpec', 'OperatorSignature', 'OperatorTypingReport',
    'UniversalRoleBinding', 'get_operator_signature', 'type_case_port_frame', 'type_polish_case_port_frames',
    'ACTION_OPERATOR_FAMILY_VERSION', 'ACTION_OPERATOR_SIGNATURES', 'ACTION_SCOPE_BASIS',
    'extract_polish_action_case_port_frames', 'install_agent_action_operator_family',
    'CARD_BINDING_BASIS', 'RELATION_ENTITY_CARD_BINDINGS_SCHEMA', 'RelationEntityCardBinding',
    'RelationEntityCardBindings', 'build_relation_entity_card_bindings',
    'RELATION_HYPERGRAPH_SCHEMA', 'RelationEntityNode', 'RelationEventNode', 'RelationHypergraph',
    'RelationIncidence', 'build_relation_hypergraph',
    'SurfaceSolutionDoctor', 'SentenceEquationDoctor', 'LocalJDoctor', 'RegionalSeparationDoctor',
    'MeaningDebtDoctor', 'JCoherenceDoctor', 'SemanticNeuralStateDoctor', 'CrossLanguageAlignmentDoctor',
    'ControlledAtlasDoctor', 'SentenceCardCouplingDoctor', 'CouplingAwareAlignmentDoctor', 'MeaningLoopDoctor',
    'MeaningRepairRoutingDoctor', 'MeaningExportAndSignalDoctor', 'RuntimeBridgeDryRunDoctor', 'SelfFeedAuditDoctor',
    'RuntimeAdapterReferenceDoctor', 'RuntimeAdapterExportDoctor', 'LingophysicsDoctor',
    'EquationTermKind', 'SentenceEquationTerm', 'SentenceEquation'
]
