
"""Polish regional grammar parts v1.1D.

This module intentionally separates:
- PartOfSpeech: what a token is locally.
- SentencePart: what role it plays in Polish syntax.
- MorphologyFeature: inflectional/morphological descriptors.
- SemanticOperatorRole: bridge roles toward GLOBAL, not identical to POS.
"""

from __future__ import annotations

from enum import Enum


class PartOfSpeech(str, Enum):
    NOUN = "noun"
    VERB = "verb"
    ADJECTIVE = "adjective"
    ADVERB = "adverb"
    PRONOUN = "pronoun"
    NUMERAL = "numeral"
    PREPOSITION = "preposition"
    CONJUNCTION = "conjunction"
    PARTICLE = "particle"
    INTERJECTION = "interjection"
    PREDICATIVE = "predicative"
    INFINITIVE = "infinitive"
    PARTICIPLE = "participle"
    GERUND = "gerund"
    PUNCTUATION = "punctuation"
    UNKNOWN = "unknown"


class SentencePart(str, Enum):
    SUBJECT = "subject"
    PREDICATE = "predicate"
    OBJECT = "object"
    ATTRIBUTE = "attribute"
    ADVERBIAL = "adverbial"
    PREDICATIVE_COMPLEMENT = "predicative_complement"
    VOCATIVE = "vocative"
    APPOSITION = "apposition"
    PARENTHETICAL = "parenthetical"
    NEGATION_OPERATOR = "negation_operator"
    QUESTION_OPERATOR = "question_operator"
    IMPERATIVE_OPERATOR = "imperative_operator"
    SOURCE_OPERATOR = "source_operator"
    CANON_OPERATOR = "canon_operator"
    MODAL_OPERATOR = "modal_operator"
    CONJUNCTION = "conjunction"
    PUNCTUATION_BOUNDARY = "punctuation_boundary"
    UNKNOWN_ROLE = "unknown_role"


class MorphologyFeature(str, Enum):
    NOMINATIVE = "nominative"
    GENITIVE = "genitive"
    DATIVE = "dative"
    ACCUSATIVE = "accusative"
    INSTRUMENTAL = "instrumental"
    LOCATIVE = "locative"
    VOCATIVE = "vocative"

    SINGULAR = "singular"
    PLURAL = "plural"

    MASCULINE = "masculine"
    FEMININE = "feminine"
    NEUTER = "neuter"

    FIRST = "first"
    SECOND = "second"
    THIRD = "third"

    PRESENT = "present"
    PAST = "past"
    FUTURE = "future"

    PERFECTIVE = "perfective"
    IMPERFECTIVE = "imperfective"

    INDICATIVE = "indicative"
    IMPERATIVE = "imperative"
    CONDITIONAL = "conditional"

    ACTIVE = "active"
    PASSIVE = "passive"

    POSITIVE = "positive"
    COMPARATIVE = "comparative"
    SUPERLATIVE = "superlative"

    UNKNOWN = "unknown"


class SemanticOperatorRole(str, Enum):
    # Legacy 1.1C public values kept for regression compatibility.
    NEGATION = "negation"
    SOURCE_REQUIRED = "source_required"
    CANON_ATTEMPT = "canon_attempt"
    RUNTIME_ATTEMPT = "runtime_attempt"

    NONE = "NONE"
    NEGATION_OPERATOR = "NEGATION_OPERATOR"
    QUESTION_OPERATOR = "QUESTION_OPERATOR"
    SOURCE_OPERATOR = "SOURCE_OPERATOR"
    MISSING_SOURCE_OPERATOR = "MISSING_SOURCE_OPERATOR"
    PROOF_OPERATOR = "PROOF_OPERATOR"
    CANON_OPERATOR = "CANON_OPERATOR"
    AUTHORITY_PROMOTION_ATTEMPT = "AUTHORITY_PROMOTION_ATTEMPT"
    RUNTIME_ACTION_ATTEMPT = "RUNTIME_ACTION_ATTEMPT"
    MODALITY_OPERATOR = "MODALITY_OPERATOR"
    REPAIR_OPERATOR = "REPAIR_OPERATOR"
    UNCERTAINTY_OPERATOR = "UNCERTAINTY_OPERATOR"


PL_CRITICAL_MARKERS = {
    "brak źródła",
    "nie SOURCE",
    "nie canon",
    "nie dowód",
    "dry-run",
    "nie wykonuję runtime",
    "nie CURRENT",
    "nie ACTIVE",
    "nie PASS",
}


def is_part_of_speech(value: str) -> bool:
    return value in {item.value for item in PartOfSpeech}


def is_sentence_part(value: str) -> bool:
    return value in {item.value for item in SentencePart}


def is_morphology_feature(value: str) -> bool:
    return value in {item.value for item in MorphologyFeature}


# ---------------------------------------------------------------------------
# 1.1C compatibility API
# ---------------------------------------------------------------------------

def classify_pl_token_part_of_speech(token: str) -> PartOfSpeech:
    low = token.lower().strip(".,?!:;")
    if low in {"nie", "czy"}:
        return PartOfSpeech.PARTICLE
    if low in {"i", "oraz", "albo", "lub"}:
        return PartOfSpeech.CONJUNCTION
    if low in {"trzeba", "można", "warto"}:
        return PartOfSpeech.PREDICATIVE
    if low.endswith(("ać", "eć", "ić", "yć")):
        return PartOfSpeech.INFINITIVE
    if low in {"kanonizuj", "sprawdź", "podaj", "ustaw", "zapisz", "wykonaj", "jest", "oznacza", "analizuje"}:
        return PartOfSpeech.VERB
    if low in {"szybko", "wolno"}:
        return PartOfSpeech.ADVERB
    if low in {"trudne", "regionalnym"}:
        return PartOfSpeech.ADJECTIVE
    if low in {"to"}:
        return PartOfSpeech.PRONOUN
    if token in {".", "?", "!", ",", ";", ":"}:
        return PartOfSpeech.PUNCTUATION
    if low:
        return PartOfSpeech.NOUN
    return PartOfSpeech.UNKNOWN


def classify_pl_semantic_operator_role(token: str) -> SemanticOperatorRole:
    low = token.lower().strip(".,?!:;")
    if low == "nie":
        return SemanticOperatorRole.NEGATION
    if low in {"źródło", "źródła", "brak", "dowód"}:
        return SemanticOperatorRole.SOURCE_REQUIRED
    if low in {"kanonizuj", "kanon", "canon", "kanonizacja"}:
        return SemanticOperatorRole.CANON_ATTEMPT
    if low in {"sprawdź", "podaj", "ustaw", "zapisz", "wykonaj", "uruchom"}:
        return SemanticOperatorRole.RUNTIME_ATTEMPT
    return SemanticOperatorRole.NONE


def sentence_part_from_pos_and_operator(pos: PartOfSpeech, operator: SemanticOperatorRole) -> SentencePart:
    if operator in {SemanticOperatorRole.NEGATION, SemanticOperatorRole.NEGATION_OPERATOR}:
        return SentencePart.NEGATION_OPERATOR
    if operator in {SemanticOperatorRole.SOURCE_REQUIRED, SemanticOperatorRole.SOURCE_OPERATOR, SemanticOperatorRole.MISSING_SOURCE_OPERATOR}:
        return SentencePart.SOURCE_OPERATOR
    if operator in {SemanticOperatorRole.CANON_ATTEMPT, SemanticOperatorRole.CANON_OPERATOR, SemanticOperatorRole.AUTHORITY_PROMOTION_ATTEMPT}:
        return SentencePart.CANON_OPERATOR
    if operator in {SemanticOperatorRole.RUNTIME_ATTEMPT, SemanticOperatorRole.RUNTIME_ACTION_ATTEMPT}:
        return SentencePart.IMPERATIVE_OPERATOR
    if pos == PartOfSpeech.VERB:
        return SentencePart.PREDICATE
    if pos == PartOfSpeech.ADJECTIVE:
        return SentencePart.ATTRIBUTE
    if pos == PartOfSpeech.ADVERB:
        return SentencePart.ADVERBIAL
    if pos == PartOfSpeech.CONJUNCTION:
        return SentencePart.CONJUNCTION
    if pos == PartOfSpeech.PUNCTUATION:
        return SentencePart.PUNCTUATION_BOUNDARY
    if pos == PartOfSpeech.NOUN:
        return SentencePart.OBJECT
    return SentencePart.UNKNOWN_ROLE
