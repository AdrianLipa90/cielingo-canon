"""Native CIELingo semantic-planning and surface-generation lanes."""

from .canonical_lingophysics_adapter import CanonicalLingophysicsRoundTripAdapter
from .dual_native_surface_endpoint import (
    DUAL_SURFACE_PLAN_SCHEMA,
    DualNativeSurfaceGenerationEndpoint,
)
from .hashing import canonical_sha256, is_sha256
from .native_surface_endpoint import (
    CandidateProposal,
    DeterministicSurfaceBackend,
    LanguageBackend,
    NativeSurfaceGenerationEndpoint,
    RoundTripEvidence,
    RoundTripValidator,
)
from .native_roundtrip import (
    CielingoLingophysicsRoundTripValidator,
    LingophysicsRoundTripAdapter,
    LingophysicsRoundTripVerdict,
    RegionalSolver,
    semantic_payload_text,
)
from .planned_roundtrip import PlannedLingophysicsRoundTripAdapter
from .response_semantics import (
    NativeResponseSemanticPlanner,
    NativeResponseSemanticPlannerEndpoint,
    RESPONSE_PLAN_RECEIPT_SCHEMA,
    RESPONSE_PLAN_REQUEST_SCHEMA,
    RESPONSE_PLAN_RESULT_SCHEMA,
    RESPONSE_PLAN_SCHEMA,
    ResponsePlanningError,
    ResponseSemanticPlan,
    SemanticEvidence,
    SemanticProposition,
    parse_response_semantic_plan,
)
from .structural_residual import (
    LinearStructuralResidualExpert,
    REFERENCE_FEATURE_ORDER,
    StructuralResidualError,
    feature_vector,
    logits_sha256,
)

__all__ = [
    "CandidateProposal",
    "CanonicalLingophysicsRoundTripAdapter",
    "CielingoLingophysicsRoundTripValidator",
    "DUAL_SURFACE_PLAN_SCHEMA",
    "DeterministicSurfaceBackend",
    "DualNativeSurfaceGenerationEndpoint",
    "LanguageBackend",
    "LinearStructuralResidualExpert",
    "LingophysicsRoundTripAdapter",
    "LingophysicsRoundTripVerdict",
    "NativeResponseSemanticPlanner",
    "NativeResponseSemanticPlannerEndpoint",
    "NativeSurfaceGenerationEndpoint",
    "PlannedLingophysicsRoundTripAdapter",
    "REFERENCE_FEATURE_ORDER",
    "RESPONSE_PLAN_RECEIPT_SCHEMA",
    "RESPONSE_PLAN_REQUEST_SCHEMA",
    "RESPONSE_PLAN_RESULT_SCHEMA",
    "RESPONSE_PLAN_SCHEMA",
    "RegionalSolver",
    "ResponsePlanningError",
    "ResponseSemanticPlan",
    "RoundTripEvidence",
    "RoundTripValidator",
    "SemanticEvidence",
    "SemanticProposition",
    "StructuralResidualError",
    "canonical_sha256",
    "feature_vector",
    "is_sha256",
    "logits_sha256",
    "parse_response_semantic_plan",
    "semantic_payload_text",
]
