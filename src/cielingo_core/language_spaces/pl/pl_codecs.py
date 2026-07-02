
"""PL regional grammar codecs v1.1D.

Forward:
    PL surface -> RegionalGrammarFrame -> CommonFunctionalFrame candidate

Reverse:
    RegionalRealizationRequest / response contract -> PLSurfacePlan

This is still a deterministic scaffold, not a full Polish parser.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from hashlib import sha256
import json
import re
from typing import Any

from cielingo_core.global_layer.common_functional_frame import (
    CommonFunctionalFrame,
    ContextFrame,
    FunctionalOperator,
    FunctionalRole,
    FunctionalSlot,
)
from cielingo_core.global_layer.response_contract import AllowedResponseContract
from cielingo_core.language_spaces.pl.grammar_parts import (
    MorphologyFeature,
    PartOfSpeech,
    SemanticOperatorRole,
    SentencePart,
)
from cielingo_core.language_spaces.pl.regional_grammar_frame import (
    RegionalGrammarFrame,
    TokenGrammarAnalysis,
)


_TOKEN_RE = re.compile(r"[A-Za-zĄĆĘŁŃÓŚŹŻąćęłńóśźż0-9_=-]+|[?.!,;:]")


LEXICON: dict[str, dict[str, Any]] = {
    "nie": {"lemma": "nie", "pos": PartOfSpeech.PARTICLE, "part": SentencePart.NEGATION_OPERATOR, "role": SemanticOperatorRole.NEGATION_OPERATOR, "morph": [], "conf": 0.99},
    "czy": {"lemma": "czy", "pos": PartOfSpeech.PARTICLE, "part": SentencePart.QUESTION_OPERATOR, "role": SemanticOperatorRole.QUESTION_OPERATOR, "morph": [], "conf": 0.99},
    "to": {"lemma": "to", "pos": PartOfSpeech.PRONOUN, "part": SentencePart.SUBJECT, "role": SemanticOperatorRole.NONE, "morph": [], "conf": 0.8},
    "jest": {"lemma": "być", "pos": PartOfSpeech.VERB, "part": SentencePart.PREDICATE, "role": SemanticOperatorRole.NONE, "morph": [MorphologyFeature.PRESENT, MorphologyFeature.THIRD, MorphologyFeature.SINGULAR], "conf": 0.9},
    "źródło": {"lemma": "źródło", "pos": PartOfSpeech.NOUN, "part": SentencePart.SOURCE_OPERATOR, "role": SemanticOperatorRole.SOURCE_OPERATOR, "morph": [MorphologyFeature.NOMINATIVE, MorphologyFeature.SINGULAR, MorphologyFeature.NEUTER], "conf": 0.92},
    "źródła": {"lemma": "źródło", "pos": PartOfSpeech.NOUN, "part": SentencePart.SOURCE_OPERATOR, "role": SemanticOperatorRole.SOURCE_OPERATOR, "morph": [MorphologyFeature.GENITIVE, MorphologyFeature.SINGULAR, MorphologyFeature.NEUTER], "conf": 0.88},
    "brak": {"lemma": "brak", "pos": PartOfSpeech.NOUN, "part": SentencePart.SOURCE_OPERATOR, "role": SemanticOperatorRole.MISSING_SOURCE_OPERATOR, "morph": [MorphologyFeature.NOMINATIVE, MorphologyFeature.SINGULAR, MorphologyFeature.MASCULINE], "conf": 0.86},
    "kanonizuj": {"lemma": "kanonizować", "pos": PartOfSpeech.VERB, "part": SentencePart.IMPERATIVE_OPERATOR, "role": SemanticOperatorRole.AUTHORITY_PROMOTION_ATTEMPT, "morph": [MorphologyFeature.IMPERATIVE, MorphologyFeature.SECOND, MorphologyFeature.SINGULAR], "conf": 0.95},
    "sprawdź": {"lemma": "sprawdzić", "pos": PartOfSpeech.VERB, "part": SentencePart.IMPERATIVE_OPERATOR, "role": SemanticOperatorRole.RUNTIME_ACTION_ATTEMPT, "morph": [MorphologyFeature.IMPERATIVE, MorphologyFeature.SECOND, MorphologyFeature.SINGULAR, MorphologyFeature.PERFECTIVE], "conf": 0.95},
    "podaj": {"lemma": "podać", "pos": PartOfSpeech.VERB, "part": SentencePart.IMPERATIVE_OPERATOR, "role": SemanticOperatorRole.RUNTIME_ACTION_ATTEMPT, "morph": [MorphologyFeature.IMPERATIVE, MorphologyFeature.SECOND, MorphologyFeature.SINGULAR, MorphologyFeature.PERFECTIVE], "conf": 0.95},
    "plik": {"lemma": "plik", "pos": PartOfSpeech.NOUN, "part": SentencePart.OBJECT, "role": SemanticOperatorRole.NONE, "morph": [MorphologyFeature.ACCUSATIVE, MorphologyFeature.SINGULAR, MorphologyFeature.MASCULINE], "conf": 0.78},
    "wynik": {"lemma": "wynik", "pos": PartOfSpeech.NOUN, "part": SentencePart.OBJECT, "role": SemanticOperatorRole.NONE, "morph": [MorphologyFeature.ACCUSATIVE, MorphologyFeature.SINGULAR, MorphologyFeature.MASCULINE], "conf": 0.78},
    "hipotezy": {"lemma": "hipoteza", "pos": PartOfSpeech.NOUN, "part": SentencePart.OBJECT, "role": SemanticOperatorRole.NONE, "morph": [MorphologyFeature.GENITIVE, MorphologyFeature.SINGULAR, MorphologyFeature.FEMININE], "conf": 0.78},
    "hipotezę": {"lemma": "hipoteza", "pos": PartOfSpeech.NOUN, "part": SentencePart.OBJECT, "role": SemanticOperatorRole.NONE, "morph": [MorphologyFeature.ACCUSATIVE, MorphologyFeature.SINGULAR, MorphologyFeature.FEMININE], "conf": 0.78},
    "oznacza": {"lemma": "oznaczać", "pos": PartOfSpeech.VERB, "part": SentencePart.PREDICATE, "role": SemanticOperatorRole.NONE, "morph": [MorphologyFeature.PRESENT, MorphologyFeature.THIRD, MorphologyFeature.SINGULAR, MorphologyFeature.IMPERFECTIVE], "conf": 0.82},
    "model": {"lemma": "model", "pos": PartOfSpeech.NOUN, "part": SentencePart.SUBJECT, "role": SemanticOperatorRole.NONE, "morph": [MorphologyFeature.NOMINATIVE, MorphologyFeature.SINGULAR, MorphologyFeature.MASCULINE], "conf": 0.84},
    "szybko": {"lemma": "szybko", "pos": PartOfSpeech.ADVERB, "part": SentencePart.ADVERBIAL, "role": SemanticOperatorRole.NONE, "morph": [], "conf": 0.88},
    "analizuje": {"lemma": "analizować", "pos": PartOfSpeech.VERB, "part": SentencePart.PREDICATE, "role": SemanticOperatorRole.NONE, "morph": [MorphologyFeature.PRESENT, MorphologyFeature.THIRD, MorphologyFeature.SINGULAR, MorphologyFeature.IMPERFECTIVE], "conf": 0.86},
    "trudne": {"lemma": "trudny", "pos": PartOfSpeech.ADJECTIVE, "part": SentencePart.ATTRIBUTE, "role": SemanticOperatorRole.NONE, "morph": [MorphologyFeature.ACCUSATIVE, MorphologyFeature.SINGULAR, MorphologyFeature.NEUTER, MorphologyFeature.POSITIVE], "conf": 0.72},
    "zdanie": {"lemma": "zdanie", "pos": PartOfSpeech.NOUN, "part": SentencePart.OBJECT, "role": SemanticOperatorRole.NONE, "morph": [MorphologyFeature.ACCUSATIVE, MorphologyFeature.SINGULAR, MorphologyFeature.NEUTER], "conf": 0.75},
    "dowód": {"lemma": "dowód", "pos": PartOfSpeech.NOUN, "part": SentencePart.OBJECT, "role": SemanticOperatorRole.PROOF_OPERATOR, "morph": [MorphologyFeature.NOMINATIVE, MorphologyFeature.SINGULAR, MorphologyFeature.MASCULINE], "conf": 0.82},
    "trzeba": {"lemma": "trzeba", "pos": PartOfSpeech.PREDICATIVE, "part": SentencePart.MODAL_OPERATOR, "role": SemanticOperatorRole.MODALITY_OPERATOR, "morph": [], "conf": 0.9},
    "dodać": {"lemma": "dodać", "pos": PartOfSpeech.INFINITIVE, "part": SentencePart.PREDICATE, "role": SemanticOperatorRole.REPAIR_OPERATOR, "morph": [MorphologyFeature.PERFECTIVE], "conf": 0.86},
    "test": {"lemma": "test", "pos": PartOfSpeech.NOUN, "part": SentencePart.OBJECT, "role": SemanticOperatorRole.NONE, "morph": [MorphologyFeature.ACCUSATIVE, MorphologyFeature.SINGULAR, MorphologyFeature.MASCULINE], "conf": 0.78},
    "cielingo": {"lemma": "CIELingo", "pos": PartOfSpeech.NOUN, "part": SentencePart.SUBJECT, "role": SemanticOperatorRole.NONE, "morph": [MorphologyFeature.NOMINATIVE, MorphologyFeature.SINGULAR, MorphologyFeature.NEUTER], "conf": 0.8},
    "regionalnym": {"lemma": "regionalny", "pos": PartOfSpeech.ADJECTIVE, "part": SentencePart.ATTRIBUTE, "role": SemanticOperatorRole.NONE, "morph": [MorphologyFeature.INSTRUMENTAL, MorphologyFeature.SINGULAR, MorphologyFeature.MASCULINE, MorphologyFeature.POSITIVE], "conf": 0.72},
    "solverem": {"lemma": "solver", "pos": PartOfSpeech.NOUN, "part": SentencePart.PREDICATIVE_COMPLEMENT, "role": SemanticOperatorRole.NONE, "morph": [MorphologyFeature.INSTRUMENTAL, MorphologyFeature.SINGULAR, MorphologyFeature.MASCULINE], "conf": 0.74},
    "i": {"lemma": "i", "pos": PartOfSpeech.CONJUNCTION, "part": SentencePart.CONJUNCTION, "role": SemanticOperatorRole.NONE, "morph": [], "conf": 0.96},
    ".": {"lemma": ".", "pos": PartOfSpeech.PUNCTUATION, "part": SentencePart.PUNCTUATION_BOUNDARY, "role": SemanticOperatorRole.NONE, "morph": [], "conf": 1.0},
    "?": {"lemma": "?", "pos": PartOfSpeech.PUNCTUATION, "part": SentencePart.PUNCTUATION_BOUNDARY, "role": SemanticOperatorRole.NONE, "morph": [], "conf": 1.0},
}


ROLE_MAP = {
    SentencePart.SUBJECT: FunctionalRole.ENTITY,
    SentencePart.OBJECT: FunctionalRole.ENTITY,
    SentencePart.PREDICATIVE_COMPLEMENT: FunctionalRole.ENTITY,
    SentencePart.PREDICATE: FunctionalRole.ACTION,
    SentencePart.IMPERATIVE_OPERATOR: FunctionalRole.ACTION,
    SentencePart.ATTRIBUTE: FunctionalRole.QUALITY,
    SentencePart.ADVERBIAL: FunctionalRole.MODIFIER,
    SentencePart.CONJUNCTION: FunctionalRole.RELATION,
    SentencePart.NEGATION_OPERATOR: FunctionalRole.OPERATOR,
    SentencePart.QUESTION_OPERATOR: FunctionalRole.OPERATOR,
    SentencePart.SOURCE_OPERATOR: FunctionalRole.OPERATOR,
    SentencePart.CANON_OPERATOR: FunctionalRole.OPERATOR,
    SentencePart.MODAL_OPERATOR: FunctionalRole.OPERATOR,
    SentencePart.PUNCTUATION_BOUNDARY: FunctionalRole.BOUNDARY,
}


OPERATOR_MAP = {
    SemanticOperatorRole.NONE: FunctionalOperator.NONE,
    SemanticOperatorRole.NEGATION_OPERATOR: FunctionalOperator.NEGATION,
    SemanticOperatorRole.QUESTION_OPERATOR: FunctionalOperator.QUESTION,
    SemanticOperatorRole.SOURCE_OPERATOR: FunctionalOperator.SOURCE,
    SemanticOperatorRole.MISSING_SOURCE_OPERATOR: FunctionalOperator.SOURCE,
    SemanticOperatorRole.PROOF_OPERATOR: FunctionalOperator.SOURCE,
    SemanticOperatorRole.CANON_OPERATOR: FunctionalOperator.CANON,
    SemanticOperatorRole.AUTHORITY_PROMOTION_ATTEMPT: FunctionalOperator.AUTHORITY,
    SemanticOperatorRole.RUNTIME_ACTION_ATTEMPT: FunctionalOperator.RUNTIME,
    SemanticOperatorRole.MODALITY_OPERATOR: FunctionalOperator.MODAL,
    SemanticOperatorRole.REPAIR_OPERATOR: FunctionalOperator.REPAIR,
    SemanticOperatorRole.UNCERTAINTY_OPERATOR: FunctionalOperator.MODAL,
}


@dataclass(frozen=True)
class PLSurfacePlan:
    plan_id: str
    language_id: str
    answer_kind: str
    surface_text: str
    required_markers: list[str]
    preserved_markers: list[str]
    missing_markers: list[str]
    canon_allowed: bool = False
    source_promotion_allowed: bool = False
    noema_writeback_allowed: bool = False
    current_update_allowed: bool = False
    runtime_execution_allowed: bool = False
    limitation: str = "pl_surface_plan_not_source_not_execution"

    def validate(self) -> list[str]:
        issues: list[str] = []
        if self.language_id != "pl":
            issues.append("PLSurfacePlan expects language_id=pl")
        if not self.surface_text:
            issues.append("surface_text is required")
        if self.missing_markers:
            issues.append(f"missing required markers: {self.missing_markers}")
        if self.canon_allowed:
            issues.append("PLSurfacePlan must not allow canon")
        if self.source_promotion_allowed:
            issues.append("PLSurfacePlan must not promote SOURCE")
        if self.noema_writeback_allowed:
            issues.append("PLSurfacePlan must not write NOEMA")
        if self.current_update_allowed:
            issues.append("PLSurfacePlan must not update CURRENT")
        if self.runtime_execution_allowed:
            issues.append("PLSurfacePlan must not allow runtime execution")
        if "not_source" not in self.limitation or "not_execution" not in self.limitation:
            issues.append("limitation must state not_source and not_execution")
        return issues

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def stable_hash(self) -> str:
        return sha256(json.dumps(self.to_dict(), ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()


def tokenize_pl(text: str) -> list[str]:
    return _TOKEN_RE.findall(text)


def analyze_pl_token(token: str) -> TokenGrammarAnalysis:
    key = token.lower()
    spec = LEXICON.get(key)
    if spec is None:
        return TokenGrammarAnalysis(
            token=token,
            lemma=key,
            part_of_speech=PartOfSpeech.UNKNOWN,
            sentence_part=SentencePart.UNKNOWN_ROLE,
            morphology=[MorphologyFeature.UNKNOWN],
            semantic_operator_role=SemanticOperatorRole.NONE,
            confidence=0.2,
            notes=["lexicon_miss"],
        )
    return TokenGrammarAnalysis(
        token=token,
        lemma=spec["lemma"],
        part_of_speech=spec["pos"],
        sentence_part=spec["part"],
        morphology=list(spec.get("morph", [])),
        semantic_operator_role=spec.get("role", SemanticOperatorRole.NONE),
        confidence=float(spec.get("conf", 0.5)),
        notes=[],
    )


def solve_pl_regional_grammar(text: str) -> RegionalGrammarFrame:
    tokens = [analyze_pl_token(token) for token in tokenize_pl(text)]
    residue = [f"unknown:{t.token}" for t in tokens if t.part_of_speech == PartOfSpeech.UNKNOWN]
    syntax_path = [t.sentence_part.value for t in tokens if t.sentence_part != SentencePart.PUNCTUATION_BOUNDARY]
    confidence = sum(t.confidence for t in tokens) / len(tokens) if tokens else 0.0
    payload = json.dumps({"text": text, "tokens": [t.to_dict() for t in tokens]}, ensure_ascii=False, sort_keys=True)
    return RegionalGrammarFrame(
        frame_id="pl_regional_frame_" + sha256(payload.encode("utf-8")).hexdigest()[:16],
        language_id="pl",
        surface_text=text,
        tokens=tokens,
        syntax_path=syntax_path,
        regional_residue=residue,
        confidence=round(confidence, 6),
        canon_allowed=False,
        source_promotion_allowed=False,
        noema_writeback_allowed=False,
        current_update_allowed=False,
        runtime_execution_allowed=False,
    )


def encode_pl_regional_to_common(frame: RegionalGrammarFrame) -> CommonFunctionalFrame:
    slots: list[FunctionalSlot] = []
    for idx, token in enumerate(frame.tokens):
        role = ROLE_MAP.get(token.sentence_part, FunctionalRole.CONTEXT)
        weight = 0.9
        if role == FunctionalRole.OPERATOR:
            weight = 0.85
        elif role == FunctionalRole.ACTION:
            weight = 0.8
        elif role == FunctionalRole.ENTITY:
            weight = 0.7
        elif role == FunctionalRole.QUALITY:
            weight = 0.55
        elif role == FunctionalRole.MODIFIER:
            weight = 0.45
        elif role == FunctionalRole.BOUNDARY:
            weight = 0.25

        operator = OPERATOR_MAP.get(token.semantic_operator_role, FunctionalOperator.NONE)
        slots.append(FunctionalSlot(
            token=token.token,
            role=role,
            operators=[operator],
            weight=weight,
            source_index=idx,
        ))

    authority_risk = 0.0
    if any(t.semantic_operator_role == SemanticOperatorRole.AUTHORITY_PROMOTION_ATTEMPT for t in frame.tokens):
        authority_risk = max(authority_risk, 0.85)
    if any(t.semantic_operator_role == SemanticOperatorRole.RUNTIME_ACTION_ATTEMPT for t in frame.tokens):
        authority_risk = max(authority_risk, 0.65)

    source_status = "source_required_candidate" if any(
        t.semantic_operator_role in {SemanticOperatorRole.SOURCE_OPERATOR, SemanticOperatorRole.MISSING_SOURCE_OPERATOR}
        for t in frame.tokens
    ) else "not_requested"
    intention = "command" if any(t.sentence_part == SentencePart.IMPERATIVE_OPERATOR for t in frame.tokens) else "ask" if any(t.sentence_part == SentencePart.QUESTION_OPERATOR for t in frame.tokens) else "assert"

    context = ContextFrame(
        intention=intention,
        language_hint="pl",
        source_status=source_status,
        authority_risk=round(authority_risk, 6),
        runtime_request=any(t.semantic_operator_role == SemanticOperatorRole.RUNTIME_ACTION_ATTEMPT for t in frame.tokens),
        uncertainty_required=source_status == "source_required_candidate",
    )
    payload = json.dumps({
        "frame_id": frame.frame_id,
        "slots": [s.to_dict() for s in slots],
        "context": context.to_dict(),
    }, ensure_ascii=False, sort_keys=True)
    return CommonFunctionalFrame(
        frame_id="common_frame_from_pl_" + sha256(payload.encode("utf-8")).hexdigest()[:16],
        slots=slots,
        context=context,
        boundary_markers=[],
        canon_allowed=False,
        source_promotion_allowed=False,
        noema_writeback_allowed=False,
        current_update_allowed=False,
        runtime_execution_allowed=False,
    )

def decode_contract_to_pl_surface_plan(contract: AllowedResponseContract) -> PLSurfacePlan:
    kind = contract.answer_kind
    if kind == "source_missing_hypothesis":
        text = "Brak źródła. To pozostaje hipoteza robocza: nie SOURCE, nie canon."
    elif kind == "runtime_dry_run_refusal":
        text = "To jest dry-run. Nie wykonuję runtime, nie CURRENT, nie ACTIVE."
    elif kind == "alignment_candidate_explanation":
        text = "To jest kandydat dopasowania. Marker: nie dowód, nie semantic identity."
    elif kind == "repair_required":
        text = "repair_required: brak domknięcia. Wynik to nie PASS."
    else:
        text = "draft_answer_candidate: tekst roboczy. To nie SOURCE i nie canon."

    preserved = [m for m in contract.required_markers if m.lower() in text.lower()]
    missing = [m for m in contract.required_markers if m.lower() not in text.lower()]
    payload = json.dumps({"contract": contract.contract_id, "text": text, "missing": missing}, ensure_ascii=False, sort_keys=True)
    return PLSurfacePlan(
        plan_id="pl_surface_plan_" + sha256(payload.encode("utf-8")).hexdigest()[:16],
        language_id="pl",
        answer_kind=kind,
        surface_text=text,
        required_markers=list(contract.required_markers),
        preserved_markers=preserved,
        missing_markers=missing,
        canon_allowed=False,
        source_promotion_allowed=False,
        noema_writeback_allowed=False,
        current_update_allowed=False,
        runtime_execution_allowed=False,
    )


# ---------------------------------------------------------------------------
# 1.1C compatibility API
# ---------------------------------------------------------------------------

def encode_pl_text_to_regional_frame(text: str) -> RegionalGrammarFrame:
    """Compatibility wrapper for v1.1C tests.

    Returns a RegionalGrammarFrame but maps selected operator roles to legacy
    public values expected by 1.1C tests.
    """
    frame = solve_pl_regional_grammar(text)
    legacy_tokens = []
    for token in frame.tokens:
        role = token.semantic_operator_role
        if role == SemanticOperatorRole.NEGATION_OPERATOR:
            role = SemanticOperatorRole.NEGATION
        elif role in {SemanticOperatorRole.SOURCE_OPERATOR, SemanticOperatorRole.MISSING_SOURCE_OPERATOR, SemanticOperatorRole.PROOF_OPERATOR}:
            role = SemanticOperatorRole.SOURCE_REQUIRED
        elif role == SemanticOperatorRole.AUTHORITY_PROMOTION_ATTEMPT:
            role = SemanticOperatorRole.CANON_ATTEMPT
        elif role == SemanticOperatorRole.RUNTIME_ACTION_ATTEMPT:
            role = SemanticOperatorRole.RUNTIME_ATTEMPT
        legacy_tokens.append(TokenGrammarAnalysis(
            token=token.token,
            lemma=token.lemma,
            part_of_speech=token.part_of_speech,
            sentence_part=token.sentence_part,
            morphology=token.morphology,
            semantic_operator_role=role,
            confidence=token.confidence,
            notes=list(token.notes) + ["compat_1_1c"],
        ))
    return RegionalGrammarFrame(
        frame_id=frame.frame_id + "_compat",
        language_id=frame.language_id,
        surface_text=frame.surface_text,
        tokens=legacy_tokens,
        syntax_path=frame.syntax_path,
        regional_residue=frame.regional_residue,
        confidence=frame.confidence,
        canon_allowed=False,
        source_promotion_allowed=False,
        noema_writeback_allowed=False,
        current_update_allowed=False,
        runtime_execution_allowed=False,
    )


def decode_common_frame_to_pl_surface_plan(frame: CommonFunctionalFrame, request) -> PLSurfacePlan:
    """Compatibility wrapper for 1.1C reverse-codec contract.

    The CommonFunctionalFrame is used as context only in this scaffold.
    """
    class _ContractLike:
        contract_id = getattr(request, "request_id", "regional_request")
        answer_kind = getattr(request, "answer_kind", "draft_text_generation")
        required_markers = list(getattr(request, "required_markers", []))
        forbidden_claims = list(getattr(request, "forbidden_claims", []))
        severity = getattr(request, "severity", "info")
    return decode_contract_to_pl_surface_plan(_ContractLike())
