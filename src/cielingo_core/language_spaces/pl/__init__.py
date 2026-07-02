"""CIELingo Polish language space."""
from __future__ import annotations
from .canon_phrase import CanonPhraseCandidate
from .case_hints import CaseHint
from .grammar import PolishGrammarHint
from .grammar_parts import PartOfSpeech, SentencePart, MorphologyFeature, SemanticOperatorRole
from .imperative_force import ImperativeForceCandidate
from .j_holonomy import JKuramotoComponent, JKuramotoHolonomyReport
from .negation_scope import NegationScopeCandidate
from .pl_codecs import PLSurfacePlan
from .polish_j_components import PolishJComponent
from .regional_grammar_frame import TokenGrammarAnalysis, RegionalGrammarFrame
from .response_realizer import RegionalResponseDraft
from .role_inference import RoleCandidate
from .solver import PolishRegionalSolver
from .source_phrase import SourcePhraseCandidate

__all__ = ['CanonPhraseCandidate', 'CaseHint', 'PolishGrammarHint', 'PartOfSpeech', 'SentencePart', 'MorphologyFeature', 'SemanticOperatorRole', 'ImperativeForceCandidate', 'JKuramotoComponent', 'JKuramotoHolonomyReport', 'NegationScopeCandidate', 'PLSurfacePlan', 'PolishJComponent', 'TokenGrammarAnalysis', 'RegionalGrammarFrame', 'RegionalResponseDraft', 'RoleCandidate', 'PolishRegionalSolver', 'SourcePhraseCandidate']
