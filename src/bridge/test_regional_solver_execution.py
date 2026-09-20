"""Regression tests for real regional solver execution in the CIELingo bridge."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bridge.cielingo_bridge import CIELingoBridge


CANON_SRC = str(Path(__file__).resolve().parent.parent)


def _expected_equation_id(language_id: str, text: str) -> str:
    return f"surface_{language_id}_" + sha256(text.encode("utf-8")).hexdigest()[:16]


def test_english_input_executes_english_solver_and_fails_loud_without_realizer() -> None:
    text = "english text"
    state = CIELingoBridge(repo_root=CANON_SRC).process(
        engine_turn_id="en_solver_execution",
        intention_text=text,
        intention_type="query",
    )
    assert state.regional_solve_result is not None
    assert state.regional_solve_result.language_id == "en"
    assert state.regional_solve_result.surface_solution.equation_id == (
        _expected_equation_id("en", text)
    )
    assert "solver: en:executed" in state.notes
    assert "response_realizer: en:not_implemented" in state.notes
    assert state.response_draft is None


def test_japanese_input_executes_japanese_solver_with_deterministic_equation_id() -> None:
    text = "japanese content"
    state = CIELingoBridge(repo_root=CANON_SRC).process(
        engine_turn_id="ja_solver_execution",
        intention_text=text,
        intention_type="query",
    )
    assert state.regional_solve_result is not None
    assert state.regional_solve_result.language_id == "ja"
    assert state.regional_solve_result.surface_solution.equation_id == (
        _expected_equation_id("ja", text)
    )
    assert "solver: ja:executed" in state.notes
    assert "response_realizer: ja:not_implemented" in state.notes
    assert state.response_draft is None


def test_polish_path_executes_solver_and_uses_registered_pl_realizer() -> None:
    text = "polish text"
    state = CIELingoBridge(repo_root=CANON_SRC).process(
        engine_turn_id="pl_solver_execution",
        intention_text=text,
        intention_type="query",
    )
    assert state.regional_solve_result is not None
    assert state.regional_solve_result.language_id == "pl"
    assert "solver: pl:executed" in state.notes
    assert state.response_draft is not None
