"""CIELingo runtime surfaces."""
from __future__ import annotations

from importlib import import_module

_EXPORTS = {
    "CardTrace": "card_trace_eeg",
    "CardTraceSnap": "card_trace_eeg",
    "create_card_trace_snap": "card_trace_eeg",
    "snap_similarity": "card_trace_eeg",
    "OrchORbitalDecision": "orchorbital_router",
    "route_orchorbital": "orchorbital_router",
    "CollatzSemanticStep": "semantic_collatz",
    "semantic_seed": "semantic_collatz",
    "semantic_collatz_route": "semantic_collatz",
    "route_summary": "semantic_collatz",
    "LNSLanguageCard": "lns_language_cards",
    "load_lns_concept_cards": "lns_language_cards",
    "load_lns_operator_cards": "lns_language_cards",
    "load_noema_index_language_cards": "lns_language_cards",
    "load_all_language_cards": "lns_language_cards",
    "language_card_inventory": "lns_language_cards",
    "search_language_cards": "lns_language_cards",
    "CardSyncState": "collatz_semantic_htri_sync",
    "synchronize_card": "collatz_semantic_htri_sync",
    "synchronization_report": "collatz_semantic_htri_sync",
    "PhaseBusNode": "htri_phase_bus",
    "PhaseBusReport": "htri_phase_bus",
    "bind_card_to_phase_bus": "htri_phase_bus",
    "phase_bus_report": "htri_phase_bus",
    "InfinitiveSeed": "infinitive_modal_potential",
    "ModalitySeed": "infinitive_modal_potential",
    "ModalMapping": "infinitive_modal_potential",
    "infinitive_modal_report": "infinitive_modal_potential",
    "load_infinitive_seeds": "infinitive_modal_potential",
    "load_modality_seeds": "infinitive_modal_potential",
    "map_infinitive_to_modalities": "infinitive_modal_potential",
    "CIELingoVector": "vector_surface",
    "VectorSurfaceReport": "vector_surface",
    "VECTOR_COMPONENTS": "vector_surface",
    "VECTOR_DIM": "vector_surface",
    "VECTOR_SCHEMA": "vector_surface",
    "select_vector_cards": "vector_surface",
    "vector_surface_report": "vector_surface",
    "vectorize_card": "vector_surface",
    "LexicalUnit": "lexical_holonomy",
    "LexicalHolonomyEdge": "lexical_holonomy",
    "WordKnowledgeNote": "lexical_holonomy",
    "LanguageCardFileRef": "lexical_holonomy",
    "extract_lexical_units": "lexical_holonomy",
    "build_lexical_holonomy_edges": "lexical_holonomy",
    "build_word_knowledge_notes": "lexical_holonomy",
    "lexical_holonomy_report": "lexical_holonomy",
    "list_language_card_files": "lexical_holonomy",
    "read_language_card_file": "lexical_holonomy",
    "ContextScalarField": "tensor_scalar_field",
}

__all__ = list(_EXPORTS)


def __getattr__(name: str):
    module_name = _EXPORTS.get(name)
    if module_name is None:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    module = import_module(f"{__name__}.{module_name}")
    value = getattr(module, name)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
