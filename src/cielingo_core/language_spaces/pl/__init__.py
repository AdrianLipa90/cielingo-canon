"""CIELingo Polish language space."""
from __future__ import annotations

from importlib import import_module

__all__ = [
    'CanonPhraseCandidate', 'CaseHint', 'PolishGrammarHint', 'PartOfSpeech',
    'SentencePart', 'MorphologyFeature', 'SemanticOperatorRole',
    'ImperativeForceCandidate', 'JKuramotoComponent', 'JKuramotoHolonomyReport',
    'NegationScopeCandidate', 'PLSurfacePlan', 'PolishJComponent',
    'TokenGrammarAnalysis', 'RegionalGrammarFrame', 'RegionalResponseDraft',
    'RoleCandidate', 'PolishRegionalSolver', 'SourcePhraseCandidate'
]

_EXPORTS = {
    'CanonPhraseCandidate': ('.canon_phrase', 'CanonPhraseCandidate'),
    'CaseHint': ('.case_hints', 'CaseHint'),
    'PolishGrammarHint': ('.grammar', 'PolishGrammarHint'),
    'PartOfSpeech': ('.grammar_parts', 'PartOfSpeech'),
    'SentencePart': ('.grammar_parts', 'SentencePart'),
    'MorphologyFeature': ('.grammar_parts', 'MorphologyFeature'),
    'SemanticOperatorRole': ('.grammar_parts', 'SemanticOperatorRole'),
    'ImperativeForceCandidate': ('.imperative_force', 'ImperativeForceCandidate'),
    'JKuramotoComponent': ('.j_holonomy', 'JKuramotoComponent'),
    'JKuramotoHolonomyReport': ('.j_holonomy', 'JKuramotoHolonomyReport'),
    'NegationScopeCandidate': ('.negation_scope', 'NegationScopeCandidate'),
    'PLSurfacePlan': ('.pl_codecs', 'PLSurfacePlan'),
    'PolishJComponent': ('.polish_j_components', 'PolishJComponent'),
    'TokenGrammarAnalysis': ('.regional_grammar_frame', 'TokenGrammarAnalysis'),
    'RegionalGrammarFrame': ('.regional_grammar_frame', 'RegionalGrammarFrame'),
    'RegionalResponseDraft': ('.response_realizer', 'RegionalResponseDraft'),
    'RoleCandidate': ('.role_inference', 'RoleCandidate'),
    'PolishRegionalSolver': ('.solver', 'PolishRegionalSolver'),
    'SourcePhraseCandidate': ('.source_phrase', 'SourcePhraseCandidate'),
}


def __getattr__(name: str):
    target = _EXPORTS.get(name)
    if target is None:
        raise AttributeError(name)
    module_name, attr = target
    module = import_module(module_name, __name__)
    value = getattr(module, attr)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
