"""Polish CIELingo linguistic surface.

This package is a runtime adapter over the existing lingophysics LNS resources.
"""
from .linguistic_database import PolishLinguisticDatabase, load_polish_database
from .grammar_algorithms import analyze_polish_sentence
from .j_functionals import compute_language_j_functional
