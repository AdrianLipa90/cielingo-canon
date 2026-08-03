from cielingo_core.generation.canonical_lingophysics_adapter import _normalise_tokens


def test_token_normalization_strips_whitespace_without_trimming_letters() -> None:
    assert _normalise_tokens(["kot\t", "teren\n", "dom."]) == [
        "kot",
        "teren",
        "dom",
    ]
