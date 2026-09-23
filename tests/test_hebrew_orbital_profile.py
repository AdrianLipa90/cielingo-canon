from __future__ import annotations

import json
from pathlib import Path

from cielingo_core.language_spaces.policy import (
    default_probe_languages,
    get_language_trajectory,
)

ROOT = Path(__file__).resolve().parents[1]


def test_hebrew_is_research_candidate_not_default_probe() -> None:
    cfg = get_language_trajectory("he")
    assert cfg.priority == "research"
    assert cfg.growth_mode == "research_candidate"
    assert cfg.new_feature_growth_allowed is True
    assert cfg.default_probe_enabled is False
    assert cfg.requires_review_before_expansion is True
    assert "he" not in default_probe_languages()


def test_embedded_lingophysics_has_resolved_hebrew_profile() -> None:
    path = (
        ROOT
        / "data"
        / "lingophysics"
        / "data"
        / "language_families"
        / "language_profile_specialization_v2_3.json"
    )
    profiles = json.loads(path.read_text(encoding="utf-8"))["profiles"]
    he = profiles["language:he:standard"]
    assert he["family"] == "family:semitic"
    assert he["priority"] == "research_candidate"
    assert "root_pattern_analyzer" in he["required_modules"]
    assert "orbital_cell_chi" in he["required_modules"]
    assert "vowel_phase_mapper" in he["required_modules"]
    assert "semantic_holonomy_adapter" in he["required_modules"]


def test_hebrew_family_pointer_resolves_to_standard_candidate_profile() -> None:
    family_path = (
        ROOT
        / "data"
        / "lingophysics"
        / "data"
        / "language_families"
        / "language_family_grammar_profiles_v2_3.json"
    )
    families = json.loads(family_path.read_text(encoding="utf-8"))["families"]
    semitic = next(f for f in families if f["id"] == "family:semitic")
    he = next(x for x in semitic["languages"] if x["code"] == "he")
    assert he["profile"] == "language:he:standard"


def test_japanese_freeze_is_unchanged() -> None:
    cfg = get_language_trajectory("ja")
    assert cfg.priority == "parked"
    assert cfg.growth_mode == "temporarily_frozen"
    assert cfg.new_feature_growth_allowed is False
    assert cfg.default_probe_enabled is False
    assert cfg.requires_review_before_expansion is True
