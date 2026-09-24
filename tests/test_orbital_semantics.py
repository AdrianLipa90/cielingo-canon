from __future__ import annotations

import math

import pytest

from cielingo_core.lingophysics.orbital_semantics import (
    ConceptOrbital,
    RadicalOrbital,
    SemanticRelation,
    SentenceOrbital,
    hebrew_kaku,
    latent_phase_ensemble,
    orbital_cell_pair,
    phase_fidelity,
    phasenav_semantic_payload,
)


def radical(symbols: str, phases: tuple[float, ...]) -> RadicalOrbital:
    cells = [
        orbital_cell_pair(hebrew_kaku(symbol), phase, 0.9).plus
        for symbol, phase in zip(symbols, phases)
    ]
    return RadicalOrbital.build(cells)


def test_hebrew_final_forms_preserve_standard_numeric_seed() -> None:
    assert hebrew_kaku("מ").numeric_value == 40
    assert hebrew_kaku("ם").numeric_value == 40
    assert hebrew_kaku("ם").normalized_symbol == "מ"


def test_phase_counterphase_pair_is_complex_conjugate() -> None:
    pair = orbital_cell_pair(hebrew_kaku("מ"), 0.73, 0.8)
    assert pair.minus.complex_state == pytest.approx(pair.plus.complex_state.conjugate())
    assert pair.plus.chirality == 1
    assert pair.minus.chirality == -1


def test_latent_vowel_has_zero_mean_but_nonzero_potential() -> None:
    latent = latent_phase_ensemble(13)
    assert abs(latent.expectation) < 1e-12
    assert latent.second_moment == pytest.approx(1.0)
    assert latent.entropy_bits == pytest.approx(math.log2(13))
    assert latent.zero_mean


def test_radical_is_order_sensitive() -> None:
    a = radical("מלכ", (0.1, 0.4, -0.2))
    b = radical("כלמ", (-0.2, 0.4, 0.1))
    assert phase_fidelity(a.phase36, b.phase36) < 0.999


def test_morphology_changes_concept_orbit_without_changing_radical() -> None:
    r = radical("מלכ", (0.1, 0.4, -0.2))
    king = ConceptOrbital.build("melech", r, morphology_phase=0.3)
    ruled = ConceptOrbital.build("malach", r, morphology_phase=-0.7)
    assert king.radical == ruled.radical
    assert phase_fidelity(king.phase36, ruled.phase36) < 0.999


def test_sentence_separates_bag_from_order() -> None:
    r = radical("מלכ", (0.1, 0.4, -0.2))
    a = ConceptOrbital.build("a", r, morphology_phase=0.2)
    b = ConceptOrbital.build("b", r, morphology_phase=-0.6)
    ab = SentenceOrbital.build((a, b))
    ba = SentenceOrbital.build((b, a))
    assert phase_fidelity(ab.bag_phase36, ba.bag_phase36) == pytest.approx(1.0)
    assert phase_fidelity(ab.phase36, ba.phase36) < 0.999


def test_typed_relation_changes_sentence_not_lexical_channel() -> None:
    r = radical("מלכ", (0.1, 0.4, -0.2))
    a = ConceptOrbital.build("a", r, morphology_phase=0.2)
    b = ConceptOrbital.build("b", r, morphology_phase=-0.6)
    x = SentenceOrbital.build(
        (a, b),
        (SemanticRelation(0, 1, "ACTS_ON", 0.3, 0.8),),
    )
    y = SentenceOrbital.build(
        (a, b),
        (SemanticRelation(0, 1, "CONTRASTS_WITH", 0.3, 0.8),),
    )
    assert phase_fidelity(x.lexical_phase36, y.lexical_phase36) == pytest.approx(1.0)
    assert phase_fidelity(x.phase36, y.phase36) < 0.999


def test_phasenav_payload_keeps_authority_boundary() -> None:
    r = radical("מלכ", (0.1, 0.4, -0.2))
    a = ConceptOrbital.build("a", r, morphology_phase=0.2)
    b = ConceptOrbital.build("b", r, morphology_phase=-0.6)
    payload = phasenav_semantic_payload("he:test", a.phase36, b.phase36, (0.1, -0.2))
    assert len(payload["left_phase36"]) == 36
    assert len(payload["right_phase36"]) == 36
    assert payload["authority"] == "CANDIDATE_ONLY"
    assert payload["canon_allowed"] is False
    assert payload["physical_mass_claim"] is False
    assert payload["physical_gauge_field_claim"] is False
    assert payload["aharonov_bohm_binding_claim"] is False
