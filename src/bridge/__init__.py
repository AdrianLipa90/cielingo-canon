"""CIELingo runtime surfaces."""
from __future__ import annotations

__all__ = []

# Optional imports with graceful degradation
try:
    from .card_trace_eeg import CardTrace, CardTraceSnap, create_card_trace_snap, snap_similarity
    __all__.extend(["CardTrace", "CardTraceSnap", "create_card_trace_snap", "snap_similarity"])
except ImportError:
    pass

try:
    from .orchorbital_router import OrchORbitalDecision, route_orchorbital
    __all__.extend(["OrchORbitalDecision", "route_orchorbital"])
except ImportError:
    pass

try:
    from .semantic_collatz import CollatzSemanticStep, route_summary, semantic_collatz_route, semantic_seed
    __all__.extend(["CollatzSemanticStep", "semantic_seed", "semantic_collatz_route", "route_summary"])
except ImportError:
    pass

try:
    from .lns_language_cards import (
        LNSLanguageCard,
        language_card_inventory,
        load_all_language_cards,
        load_lns_concept_cards,
        load_lns_operator_cards,
        load_noema_index_language_cards,
        search_language_cards,
    )
    __all__.extend(["LNSLanguageCard", "load_lns_concept_cards", "load_lns_operator_cards", "load_noema_index_language_cards", "load_all_language_cards", "language_card_inventory", "search_language_cards"])
except ImportError:
    pass

try:
    from .collatz_semantic_htri_sync import CardSyncState, synchronize_card, synchronization_report
    __all__.extend(["CardSyncState", "synchronize_card", "synchronization_report"])
except ImportError:
    pass

try:
    from .htri_phase_bus import PhaseBusNode, PhaseBusReport, bind_card_to_phase_bus, phase_bus_report
    __all__.extend(["PhaseBusNode", "PhaseBusReport", "bind_card_to_phase_bus", "phase_bus_report"])
except ImportError:
    pass

try:
    from .infinitive_modal_potential import (
        InfinitiveSeed,
        ModalitySeed,
        ModalMapping,
        infinitive_modal_report,
        load_infinitive_seeds,
        load_modality_seeds,
        map_infinitive_to_modalities,
    )
    __all__.extend(["InfinitiveSeed", "ModalitySeed", "ModalMapping", "infinitive_modal_report", "load_infinitive_seeds", "load_modality_seeds", "map_infinitive_to_modalities"])
except ImportError:
    pass

try:
    from .vector_surface import (
        CIELingoVector,
        VectorSurfaceReport,
        VECTOR_COMPONENTS,
        VECTOR_DIM,
        VECTOR_SCHEMA,
        select_vector_cards,
        vector_surface_report,
        vectorize_card,
    )
    __all__.extend(["CIELingoVector", "VectorSurfaceReport", "VECTOR_COMPONENTS", "VECTOR_DIM", "VECTOR_SCHEMA", "select_vector_cards", "vector_surface_report", "vectorize_card"])
except ImportError:
    pass

try:
    from .lexical_holonomy import (
        LexicalUnit,
        LexicalHolonomyEdge,
        WordKnowledgeNote,
        LanguageCardFileRef,
        extract_lexical_units,
        build_lexical_holonomy_edges,
        build_word_knowledge_notes,
        lexical_holonomy_report,
        list_language_card_files,
        read_language_card_file,
    )
    __all__.extend(["LexicalUnit", "LexicalHolonomyEdge", "WordKnowledgeNote", "LanguageCardFileRef", "extract_lexical_units", "build_lexical_holonomy_edges", "build_word_knowledge_notes", "lexical_holonomy_report", "list_language_card_files", "read_language_card_file"])
except ImportError:
    pass

try:
    from .tensor_scalar_field import (
        ContextScalarField,
        TensorScalarWordState,
        TensorScalarReport,
        tensor_scalar_state_from_card,
        tensor_scalar_report,
    )
    __all__.extend(["ContextScalarField"])
except ImportError:
    pass
