import math
import pytest

from cielingo_core.orbital_semantics.hebrew_codec import (
    MATRES_CANDIDATES,
    VOWEL_MARKS,
    analyze_hebrew_surface,
    bind_radical,
    consonant_skeleton,
    latent_vowel_receipt,
)
from cielingo_core.orbital_semantics.grammar import SemanticConnectionEdge
from cielingo_core.orbital_semantics.phasenav_bridge import build_phasenav_handoff


def test_unvocalized_hebrew_is_latent_not_phase_zero():
    surface = analyze_hebrew_surface("מלך")
    assert surface.consonantal_skeleton == "מלכ"
    assert surface.explicit_vowel_slots == 0
    assert surface.latent_vowel_slots == 3
    assert all(slot.is_latent for slot in surface.slots)
    rec = latent_vowel_receipt()
    assert rec.count == len(VOWEL_MARKS)
    assert rec.mean_abs < 1e-12
    assert math.isclose(rec.second_moment, 1.0, abs_tol=1e-12)


def test_vocalization_changes_phase_not_consonantal_mass():
    noun = analyze_hebrew_surface("מֶלֶךְ")
    verb = analyze_hebrew_surface("מָלַךְ")
    assert noun.consonantal_skeleton == verb.consonantal_skeleton == "מלכ"
    assert [s.carrier.structural_mass for s in noun.slots] == [
        s.carrier.structural_mass for s in verb.slots
    ]
    noun_phases = [None if s.explicit_cell is None else s.explicit_cell.effective_phase_rad for s in noun.slots]
    verb_phases = [None if s.explicit_cell is None else s.explicit_cell.effective_phase_rad for s in verb.slots]
    assert noun_phases != verb_phases


def test_final_letters_are_normalized_for_structural_matching():
    assert consonant_skeleton("מלך") == "מלכ"
    binding = bind_radical("מלכ", "מֶלֶךְ")
    assert binding.radical_positions == (0, 1, 2)


def test_radical_must_be_ordered_subsequence():
    with pytest.raises(ValueError):
        bind_radical("כתב", "מֶלֶךְ")


def test_matres_are_candidates_not_automatic_vowels():
    surface = analyze_hebrew_surface("יין")
    assert surface.slots[0].carrier.symbol in MATRES_CANDIDATES
    assert surface.slots[0].is_latent


def test_phasenav_handoff_keeps_lambda_outside_u1_input():
    edges = (
        SemanticConnectionEdge("e1", 0.2, 0.5),
        SemanticConnectionEdge("e2", -0.4, 0.25),
    )
    handoff = build_phasenav_handoff("p", edges)
    assert handoff.phase_potentials_rad == (0.2, -0.4)
    assert math.isclose(handoff.lambda_path_gain, 0.125)
    assert math.isclose(
        math.hypot(handoff.composite_transport_real, handoff.composite_transport_imag),
        0.125,
        abs_tol=1e-12,
    )
    assert handoff.canon_allowed is False
    assert handoff.physical_gauge_claim is False
