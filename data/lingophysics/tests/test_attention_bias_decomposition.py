from src.lingophysics.attention_bias import (
    build_relation_excess_attention_bias_matrix,
    pair_bias,
    pair_bias_components,
    pair_relation_excess_bias,
)
from src.lingophysics.transformer_features import FeatureToken


RULES = {
    "weights": {
        "operator_argument_link": 0.7,
        "same_event_frame": 0.4,
        "case_role_link": 0.55,
        "phase_compatibility": 0.45,
        "conflict_penalty": 0.9,
    }
}


def tok(i, *, card_type="UNKNOWN", roles=(), features=None):
    return FeatureToken(i, f"t{i}", card_type, features or {}, tuple(roles))


def test_blanket_phase_term_is_explicit_and_relation_excess_is_zero():
    a, b = tok(0), tok(1)
    parts = pair_bias_components(a, b, RULES)
    assert parts["phase_compatibility"] == 0.45
    assert pair_bias(a, b, RULES) == 0.45
    assert pair_relation_excess_bias(a, b, RULES) == 0.0


def test_operator_argument_relation_survives_excess_projection():
    a = tok(0, card_type="OPERATOR_CARD")
    b = tok(1, card_type="CONCEPT_CARD")
    assert pair_bias(a, b, RULES) == 1.15
    assert pair_relation_excess_bias(a, b, RULES) == 0.7


def test_conflict_penalty_remains_pair_specific_excess():
    a = tok(0, features={"phase_conflict": True})
    b = tok(1)
    assert pair_bias(a, b, RULES) == -0.9
    assert pair_relation_excess_bias(a, b, RULES) == -0.9


def test_relation_excess_matrix_has_zero_diagonal():
    tokens = [
        tok(0),
        tok(1, card_type="OPERATOR_CARD"),
        tok(2, card_type="CONCEPT_CARD"),
    ]
    matrix = build_relation_excess_attention_bias_matrix(tokens, RULES)
    assert [matrix[i][i] for i in range(3)] == [0.0, 0.0, 0.0]
    assert matrix[1][2] == 0.7
