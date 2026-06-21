"""BV14A delegate verification — social_exchange_emission compat barrel re-exports domain modules."""
from __future__ import annotations

import ast
from pathlib import Path

import game.social_exchange_emission as emission_compat
import game.social_exchange_fallback_catalog as fallback_catalog
import game.social_exchange_policy as social_policy
import game.social_exchange_projection as social_projection
import game.social_exchange_validation as social_validation

ROOT = Path(__file__).resolve().parents[1]
_CANONICAL_PATHS = (
    ROOT / "game" / "social_exchange_fallback_catalog.py",
    ROOT / "game" / "social_exchange_policy.py",
    ROOT / "game" / "social_exchange_validation.py",
    ROOT / "game" / "social_exchange_projection.py",
)
_COMPAT_PATH = ROOT / "game" / "social_exchange_emission.py"

_FALLBACK_SYMBOLS = (
    "minimal_social_emergency_fallback_line",
    "select_strict_social_emergency_fallback_line",
    "deterministic_social_fallback_line",
    "build_open_social_solicitation_recovery",
)

_POLICY_SYMBOLS = (
    "strict_social_emission_will_apply",
    "merged_player_prompt_for_gate",
    "effective_strict_social_resolution_for_emission",
    "should_apply_strict_social_exchange_emission",
)

_VALIDATION_SYMBOLS = (
    "is_route_illegal_global_or_sanitizer_fallback_text",
    "replacement_is_route_legal_social",
    "social_final_emission_malformed_player_echo",
)

_PROJECTION_SYMBOLS = (
    "log_final_emission_decision",
    "log_final_emission_trace",
    "stamp_strict_social_deterministic_fallback_family",
    "project_strict_social_replace_realization_family",
)


def _symbol_delegates_to(compat, symbol: str, authority) -> None:
    compat_obj = getattr(compat, symbol)
    authority_obj = getattr(authority, symbol)
    assert compat_obj is authority_obj, f"{symbol} must delegate unchanged"


def test_bv14a_compat_reexports_fallback_catalog() -> None:
    for symbol in _FALLBACK_SYMBOLS:
        _symbol_delegates_to(emission_compat, symbol, fallback_catalog)


def test_bv14a_compat_reexports_policy() -> None:
    for symbol in _POLICY_SYMBOLS:
        _symbol_delegates_to(emission_compat, symbol, social_policy)


def test_bv14a_compat_reexports_validation() -> None:
    for symbol in _VALIDATION_SYMBOLS:
        _symbol_delegates_to(emission_compat, symbol, social_validation)


def test_bv14a_compat_reexports_projection() -> None:
    for symbol in _PROJECTION_SYMBOLS:
        _symbol_delegates_to(emission_compat, symbol, social_projection)


def test_bv14a_canonical_modules_do_not_import_compat_barrel() -> None:
    for path in _CANONICAL_PATHS:
        source = path.read_text(encoding="utf-8")
        assert "social_exchange_emission import" not in source or "hard_reject_social_exchange_text" in source
        assert "import game.social_exchange_emission" not in source or path.name == "social_exchange_validation.py"


def test_bv14a_compat_barrel_retains_composition_authority() -> None:
    tree = ast.parse(_COMPAT_PATH.read_text(encoding="utf-8"), filename=str(_COMPAT_PATH))
    defined = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert "build_final_strict_social_response" in defined
    assert "hard_reject_social_exchange_text" in defined
    assert "apply_strict_social_sentence_ownership_filter" in defined
