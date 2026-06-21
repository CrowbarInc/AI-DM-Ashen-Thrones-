"""BV13A delegate verification — text compat barrel must re-export canonical modules."""
from __future__ import annotations

import ast
from pathlib import Path

import game.final_emission_text as emission_text_compat
import game.final_emission_text_formatting as text_formatting
import game.final_emission_text_legacy_semantic_repair as text_legacy_repair
import game.final_emission_text_policy as text_policy

ROOT = Path(__file__).resolve().parents[1]
_CANONICAL_PATHS = (
    ROOT / "game" / "final_emission_text_formatting.py",
    ROOT / "game" / "final_emission_text_policy.py",
)
_COMPAT_PATH = ROOT / "game" / "final_emission_text.py"
_LEGACY_PATH = ROOT / "game" / "final_emission_text_legacy_semantic_repair.py"

_FORMATTING_SYMBOLS = (
    "_normalize_text",
    "_normalize_text_preserve_paragraphs",
    "_sanitize_output_text",
    "_normalize_terminal_punctuation",
    "_capitalize_sentence_fragment",
    "_has_terminal_punctuation",
)
_POLICY_SYMBOLS = (
    "_RESPONSE_TYPE_VALUES",
    "_ANSWER_DIRECT_PATTERNS",
    "_ANSWER_FILLER_PATTERNS",
    "_ACTION_RESULT_PATTERNS",
    "_AGENCY_SUBSTITUTE_PATTERNS",
    "_ACTION_STOPWORDS",
)
_LEGACY_SYMBOLS = (
    "_decompress_overpacked_sentences",
    "_repair_fragmentary_participial_splits",
)


def _symbol_delegates_to(compat, symbol: str, authority) -> None:
    compat_obj = getattr(compat, symbol)
    authority_obj = getattr(authority, symbol)
    assert compat_obj is authority_obj, f"{symbol} must delegate unchanged"


def test_bv13a_compat_reexports_formatting_primitives() -> None:
    for symbol in _FORMATTING_SYMBOLS:
        _symbol_delegates_to(emission_text_compat, symbol, text_formatting)


def test_bv13a_compat_reexports_policy_constants() -> None:
    for symbol in _POLICY_SYMBOLS:
        _symbol_delegates_to(emission_text_compat, symbol, text_policy)


def test_bv13a_compat_reexports_legacy_semantic_repair() -> None:
    for symbol in _LEGACY_SYMBOLS:
        _symbol_delegates_to(emission_text_compat, symbol, text_legacy_repair)


def test_bv13a_formatting_module_is_canonical_implementation() -> None:
    tree = ast.parse(_CANONICAL_PATHS[0].read_text(encoding="utf-8"), filename=str(_CANONICAL_PATHS[0]))
    defined = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert set(_FORMATTING_SYMBOLS) <= defined


def test_bv13a_policy_module_is_canonical_implementation() -> None:
    tree = ast.parse(_CANONICAL_PATHS[1].read_text(encoding="utf-8"), filename=str(_CANONICAL_PATHS[1]))
    assigned = set()
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    assigned.add(target.id)
    assert set(_POLICY_SYMBOLS) <= assigned


def test_bv13a_compat_barrel_defines_only_fallback_wrapper() -> None:
    tree = ast.parse(_COMPAT_PATH.read_text(encoding="utf-8"), filename=str(_COMPAT_PATH))
    defined = {
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert defined == {"_global_narrative_fallback_stock_line"}, defined


def test_bv13a_legacy_module_contains_no_formatting_or_policy_definitions() -> None:
    text = _LEGACY_PATH.read_text(encoding="utf-8")
    assert "def _normalize_text" not in text
    assert "_RESPONSE_TYPE_VALUES" not in text


def test_bv13a_canonical_modules_do_not_import_compat_barrel() -> None:
    for path in _CANONICAL_PATHS + (_LEGACY_PATH,):
        source = path.read_text(encoding="utf-8")
        assert "final_emission_text import" not in source
        assert "import game.final_emission_text" not in source
