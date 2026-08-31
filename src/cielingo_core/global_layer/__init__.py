"""CIELingo global_layer package.

Public symbols are resolved lazily so importing one GLOBAL component does not
initialize unrelated semantic/runtime modules.
"""
from __future__ import annotations

from importlib import import_module

_EXPORTS = {
    "FieldPolicy": "card_field_policy",
    "CardFieldRule": "card_field_policy",
    "CardMigrationDecision": "card_migration_policy",
    "CardOntologyClass": "card_runtime_schema",
    "CardValidationStatus": "card_runtime_schema",
    "ConsentEffect": "card_runtime_schema",
    "MemoryEffect": "card_runtime_schema",
    "RiskProfile": "card_runtime_schema",
    "ResidueProfile": "card_runtime_schema",
    "NoemaHolonomicMarker": "card_runtime_schema",
    "RuntimeCardExtension": "card_runtime_schema",
    "CielingoRuntimeCard": "card_runtime_schema",
    "ValidationSeverity": "card_validator",
    "CardValidationIssue": "card_validator",
    "CardValidationResult": "card_validator",
    "FunctionalRole": "common_functional_frame",
    "FunctionalOperator": "common_functional_frame",
    "FunctionalSlot": "common_functional_frame",
    "ContextFrame": "common_functional_frame",
    "CommonFunctionalFrame": "common_functional_frame",
    "ValidationStatus": "concept_validation_matrix",
    "ConceptValidationRow": "concept_validation_matrix",
    "ConceptValidationMatrix": "concept_validation_matrix",
    "SourceBindingType": "contracts",
    "EntryStatus": "contracts",
    "UniversalRole": "contracts",
    "UniversalOperatorType": "contracts",
    "LexicalSlot": "contracts",
    "LanguageSlotEntry": "contracts",
    "UniversalOperator": "contracts",
    "MeaningEquation": "contracts",
    "SlotProjection": "contracts",
    "AlignmentResidue": "contracts",
    "SurfaceSolution": "contracts",
    "HolonomicJReport": "contracts",
    "ApocalypOSLinguisticSignal": "contracts",
    "AtlasAlignmentRecord": "controlled_atlas_24",
    "GenerativeAuditResult": "generative_audit",
    "GenerativeAuditReport": "generative_audit",
    "GlobalAlgorithmV02Result": "global_algorithm_v02",
    "GlobalEncodeReport": "global_codecs",
    "RegionalRealizationRequest": "global_codecs",
    "GlobalDryTestReference": "global_dry_test_reference",
    "IntentionActionScaling": "intention_action_scaling",
    "IntentionType": "intention_frame",
    "IntentionFrame": "intention_frame",
    "PhaseBand": "j_decomposition",
    "JDecomposition": "j_decomposition",
    "LingophysicalState": "lingophysics_algorithm",
    "MeaningAction": "meaning_action",
    "MeaningBlockAction": "meaning_action",
    "LoopState": "meaning_loop",
    "MeaningLoop": "meaning_loop",
    "GlobalSignalSeverity": "meaning_signal_bridge",
    "GlobalMeaningSignal": "meaning_signal_bridge",
    "OperatorKind": "operator_algebra",
    "OperatorDomain": "operator_algebra",
    "RelationalOperator": "operator_algebra",
    "StyleRegister": "paraphrase_style",
    "ParaphraseCandidate": "paraphrase_style",
    "ParaphraseStyleProbeReport": "paraphrase_style",
    "QueryIntention": "query_generation",
    "QueryUnderstandingResult": "query_generation",
    "DraftAnswerCandidate": "query_generation",
    "QueryGenerationDryRunReport": "query_generation",
    "ResidueType": "residue_taxonomy",
    "TypedResidue": "residue_taxonomy",
    "AllowedResponseContract": "response_contract",
    "RuntimeAdapterReferenceExportBundle": "runtime_adapter_export",
    "RuntimeAdapterAction": "runtime_adapter_interface",
    "RuntimeAdapterReference": "runtime_adapter_interface",
    "RuntimeDryRunDecision": "runtime_bridge_dry_run",
    "RuntimeBridgeDryRunResult": "runtime_bridge_dry_run",
    "SelfFeedAuditEventKind": "self_feed_audit",
    "SelfFeedAuditEvent": "self_feed_audit",
    "SelfFeedAuditLog": "self_feed_audit",
    "RuntimeDryRunExportBundle": "self_feed_audit",
    "PressureType": "semantic_immune_signal",
    "SemanticImmuneSignal": "semantic_immune_signal",
    "ScarType": "semantic_scar",
    "SemanticScar": "semantic_scar",
    "SlotFamily": "slot_taxonomy",
    "SlotMode": "slot_taxonomy",
    "SlotTaxonomyRecord": "slot_taxonomy",
    "TrilingualAlignmentRecord": "trilingual_card_seed",
}

__all__ = list(_EXPORTS)


def __getattr__(name: str):
    """Resolve and cache a public GLOBAL symbol on first access."""
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(f"{__name__}.{module_name}")
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
