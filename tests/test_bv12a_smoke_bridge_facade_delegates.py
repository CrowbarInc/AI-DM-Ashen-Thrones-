"""BV12A delegate verification — smoke bridge domain facades must delegate without new logic."""
from __future__ import annotations

import ast
from pathlib import Path

import tests.helpers.fallback_bridge_smoke as fallback_bridge_smoke
import tests.helpers.gate_integration_smoke as gate_integration_smoke
import tests.helpers.gate_orchestration_smoke as gate_orchestration_smoke
import tests.helpers.replay_fem_read_smoke as replay_fem_read_smoke
import tests.helpers.replay_smoke_assertions as replay_smoke_assertions

ROOT = Path(__file__).resolve().parents[1]
_DOMAIN_FACADE_PATHS = (
    ROOT / "tests" / "helpers" / "replay_fem_read_smoke.py",
    ROOT / "tests" / "helpers" / "gate_orchestration_smoke.py",
)
_COMPAT_FACADE_PATHS = (
    ROOT / "tests" / "helpers" / "replay_smoke_assertions.py",
    ROOT / "tests" / "helpers" / "gate_integration_smoke.py",
)
_FALLBACK_FACADE_PATH = ROOT / "tests" / "helpers" / "fallback_bridge_smoke.py"


def _function_delegates_to(module, symbol: str, authority) -> None:
    facade_fn = getattr(module, symbol)
    authority_fn = getattr(authority, symbol)
    assert facade_fn is authority_fn, f"{symbol} must delegate to authority unchanged"


def test_bv12a_replay_compat_barrel_reexports_domain_facade() -> None:
    for symbol in ("final_emission_meta_from_output", "read_turn_debug_notes"):
        _function_delegates_to(replay_smoke_assertions, symbol, replay_fem_read_smoke)


def test_bv12a_gate_compat_barrel_reexports_domain_facade() -> None:
    for symbol in ("apply_final_emission_gate_consumer", "gm_response_stub"):
        _function_delegates_to(gate_integration_smoke, symbol, gate_orchestration_smoke)


def test_bv12a_fallback_bridge_reexports_domain_facades() -> None:
    _function_delegates_to(
        fallback_bridge_smoke,
        "final_emission_meta_from_output",
        replay_fem_read_smoke,
    )
    _function_delegates_to(
        fallback_bridge_smoke,
        "apply_final_emission_gate_consumer",
        gate_orchestration_smoke,
    )


def test_bv12a_gate_orchestration_uses_replay_fem_read_not_compat_barrel() -> None:
    gate_source = Path(gate_orchestration_smoke.__file__).read_text(encoding="utf-8")
    assert "from tests.helpers.replay_fem_read_smoke import final_emission_meta_from_output" in gate_source
    assert "replay_smoke_assertions" not in gate_source


def test_bv12a_domain_facade_registry_surfaces_are_diagnostic_only() -> None:
    replay_surface = replay_fem_read_smoke.replay_fem_read_smoke_surface()
    gate_surface = gate_orchestration_smoke.gate_orchestration_smoke_surface()
    fallback_surface = fallback_bridge_smoke.fallback_bridge_smoke_surface()
    assert replay_surface["facade"] == "tests.helpers.replay_fem_read_smoke"
    assert gate_surface["facade"] == "tests.helpers.gate_orchestration_smoke"
    assert fallback_surface["facade"] == "tests.helpers.fallback_bridge_smoke"


def test_bv12a_compat_facades_contain_no_function_definitions() -> None:
    for path in _COMPAT_FACADE_PATHS:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        defined = {
            node.name
            for node in tree.body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_")
        }
        assert not defined, f"{path.name} must be re-export-only; found {defined!r}"


def test_bv12a_fallback_facade_contains_no_function_definitions() -> None:
    tree = ast.parse(_FALLBACK_FACADE_PATH.read_text(encoding="utf-8"), filename=str(_FALLBACK_FACADE_PATH))
    defined = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and not node.name.startswith("_")
    }
    assert defined == {"fallback_bridge_smoke_surface"}, defined


def test_bv12a_domain_facades_do_not_duplicate_replay_projection_logic() -> None:
    forbidden_fragments = ("golden_replay", "failure_classifier", "classifier_bucket")
    for path in _DOMAIN_FACADE_PATHS:
        text = path.read_text(encoding="utf-8").lower()
        for fragment in forbidden_fragments:
            assert fragment not in text, f"{path.name} must not embed replay projection logic ({fragment})"
