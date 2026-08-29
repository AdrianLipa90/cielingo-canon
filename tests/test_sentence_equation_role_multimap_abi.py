from __future__ import annotations

import inspect

from cielingo_core.lingophysics.sentence_equation import SentenceEquation


def test_role_multimap_is_append_only_sentence_equation_field() -> None:
    names = list(inspect.signature(SentenceEquation).parameters)
    assert names[-6:] == [
        "canon_allowed",
        "source_promotion_allowed",
        "noema_writeback_allowed",
        "current_update_allowed",
        "notes",
        "role_multimap",
    ]
    assert names[-1] == "role_multimap"
