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
from .doctor import SurfaceSolutionDoctor, SentenceEquationDoctor, LocalJDoctor, RegionalSeparationDoctor, MeaningDebtDoctor, JCoherenceDoctor, SemanticNeuralStateDoctor, CrossLanguageAlignmentDoctor, ControlledAtlasDoctor, SentenceCardCouplingDoctor, CouplingAwareAlignmentDoctor, MeaningLoopDoctor, MeaningRepairRoutingDoctor, MeaningExportAndSignalDoctor, RuntimeBridgeDryRunDoctor, SelfFeedAuditDoctor, RuntimeAdapterReferenceDoctor, RuntimeAdapterExportDoctor, LingophysicsDoctor
from .sentence_equation import EquationTermKind, SentenceEquationTerm, SentenceEquation

__all__ = [
    'CasePort', 'CasePortCase', 'CasePortFrame', 'extract_polish_case_port_frames',
    'OPERATOR_SIGNATURES', 'OperatorPortSpec', 'OperatorSignature', 'OperatorTypingReport',
    'UniversalRoleBinding', 'get_operator_signature', 'type_case_port_frame', 'type_polish_case_port_frames',
    'SurfaceSolutionDoctor', 'SentenceEquationDoctor', 'LocalJDoctor', 'RegionalSeparationDoctor',
    'MeaningDebtDoctor', 'JCoherenceDoctor', 'SemanticNeuralStateDoctor', 'CrossLanguageAlignmentDoctor',
    'ControlledAtlasDoctor', 'SentenceCardCouplingDoctor', 'CouplingAwareAlignmentDoctor', 'MeaningLoopDoctor',
    'MeaningRepairRoutingDoctor', 'MeaningExportAndSignalDoctor', 'RuntimeBridgeDryRunDoctor', 'SelfFeedAuditDoctor',
    'RuntimeAdapterReferenceDoctor', 'RuntimeAdapterExportDoctor', 'LingophysicsDoctor',
    'EquationTermKind', 'SentenceEquationTerm', 'SentenceEquation'
]
