"""BU3: manifest-driven gate delegator governance helper locks."""

from __future__ import annotations

import inspect

import pytest

from tests.helpers import gate_delegator_governance as gdg
from tests.helpers.gate_delegator_governance import (
    GATE,
    NON_STRICT_STACK,
    TERMINAL_PIPELINE,
    assert_gate_lacks,
    assert_owner_callable,
    function_source,
    game_import_fan_out_from_source,
    module_source,
)

pytestmark = pytest.mark.unit


def test_gate_delegator_governance_manifest_covers_core_modules() -> None:
    required = {
        GATE,
        NON_STRICT_STACK,
        TERMINAL_PIPELINE,
        "game.final_emission_visibility_fallback",
        "game.final_emission_opening_fallback",
    }
    assert required <= set(gdg.GAME_MODULE_PATHS)


def test_function_source_matches_runtime_inspect_for_gate_entry() -> None:
    ast_src = function_source(GATE, "apply_final_emission_gate")
    runtime_src = gdg.inspect_function_source(GATE, "apply_final_emission_gate")
    assert ast_src.strip() == runtime_src.strip()
    assert "run_non_strict_layer_stack(" in ast_src


def test_delegator_regression_router_has_no_direct_game_imports() -> None:
    delegator_path = gdg.repo_root() / "tests/test_final_emission_gate_delegator_regression.py"
    src = delegator_path.read_text(encoding="utf-8")
    assert game_import_fan_out_from_source(src) == frozenset()


def test_governance_helper_still_catches_removed_gate_delegator() -> None:
    assert_gate_lacks("_run_non_strict_layer_stack")
    assert_owner_callable(NON_STRICT_STACK, "run_non_strict_layer_stack")
    gate_src = function_source(GATE, "apply_final_emission_gate")
    assert "run_non_strict_layer_stack(" in gate_src
    assert "_run_non_strict_layer_stack" not in gate_src


def test_governance_helper_still_catches_visibility_terminal_wiring() -> None:
    tp_src = function_source(TERMINAL_PIPELINE, "run_gate_terminal_enforcement_pipeline")
    assert "apply_visibility_enforcement(" in tp_src
    assert "feg._apply_visibility_enforcement" not in tp_src
    assert_gate_lacks("_apply_visibility_enforcement")


def test_gate_delegator_governance_helper_exports_are_manifest_driven() -> None:
    assert "GAME_MODULE_PATHS" in inspect.getsource(gdg)
    assert callable(gdg.load_game_module)
    assert callable(gdg.function_source)
