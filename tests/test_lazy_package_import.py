"""Regression tests for lazy CIELingo package boundaries."""
from __future__ import annotations

import importlib
import sys


def _purge_cielingo() -> None:
    for name in list(sys.modules):
        if name == "cielingo_core" or name.startswith("cielingo_core."):
            sys.modules.pop(name, None)


def test_cielingo_core_subpackages_are_lazy() -> None:
    _purge_cielingo()
    package = importlib.import_module("cielingo_core")

    assert "cielingo_core.alignment" not in sys.modules

    alignment = package.alignment

    assert alignment.__name__ == "cielingo_core.alignment"
    assert "cielingo_core.alignment" in sys.modules


def test_global_layer_public_exports_are_lazy() -> None:
    _purge_cielingo()
    global_layer = importlib.import_module("cielingo_core.global_layer")

    assert "cielingo_core.global_layer.query_generation" not in sys.modules
    assert "cielingo_core.global_layer.intention_frame" not in sys.modules

    intention_frame = global_layer.IntentionFrame

    assert intention_frame.__name__ == "IntentionFrame"
    assert "cielingo_core.global_layer.intention_frame" in sys.modules
    assert "cielingo_core.global_layer.query_generation" not in sys.modules


def test_response_contract_type_hint_does_not_load_query_generation() -> None:
    _purge_cielingo()

    response_contract = importlib.import_module(
        "cielingo_core.global_layer.response_contract"
    )

    assert response_contract.AllowedResponseContract is not None
    assert "cielingo_core.global_layer.query_generation" not in sys.modules
