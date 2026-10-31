"""Compatibility barrel for final emission text utilities.

Formatting primitives: :mod:`game.final_emission_text_formatting`
Policy vocabulary: :mod:`game.final_emission_text_policy`
Legacy semantic repair (test-only): :mod:`game.final_emission_text_legacy_semantic_repair`

BV13B: compatibility barrel for fallback wrapper and legacy re-exports only.
BV13C: import guard + FI cap (≤8) lock regrowth; formatting/policy consumers route to
canonical authority modules directly.
"""
from __future__ import annotations

from typing import Any, Dict

from game.diegetic_fallback_narration import render_global_scene_anchor_fallback
from game.final_emission_text_formatting import (
    _capitalize_sentence_fragment,
    _has_terminal_punctuation,
    _normalize_terminal_punctuation,
    _normalize_text,
    _normalize_text_preserve_paragraphs,
    _sanitize_output_text,
)
from game.final_emission_text_legacy_semantic_repair import (
    _decompress_overpacked_sentences,
    _repair_fragmentary_participial_splits,
)
from game.final_emission_text_policy import (
    _ACTION_RESULT_PATTERNS,
    _ACTION_STOPWORDS,
    _AGENCY_SUBSTITUTE_PATTERNS,
    _ANSWER_DIRECT_PATTERNS,
    _ANSWER_FILLER_PATTERNS,
    _RESPONSE_TYPE_VALUES,
)

__all__ = [
    "_ACTION_RESULT_PATTERNS",
    "_ACTION_STOPWORDS",
    "_AGENCY_SUBSTITUTE_PATTERNS",
    "_ANSWER_DIRECT_PATTERNS",
    "_ANSWER_FILLER_PATTERNS",
    "_RESPONSE_TYPE_VALUES",
    "_capitalize_sentence_fragment",
    "_decompress_overpacked_sentences",
    "_global_narrative_fallback_stock_line",
    "_has_terminal_punctuation",
    "_normalize_terminal_punctuation",
    "_normalize_text",
    "_normalize_text_preserve_paragraphs",
    "_repair_fragmentary_participial_splits",
    "_sanitize_output_text",
]


def _global_narrative_fallback_stock_line(scene: Dict[str, Any] | None, *, scene_id: str) -> str:
    alt = render_global_scene_anchor_fallback(scene, seed_key=scene_id or "fallback")
    if isinstance(alt, str) and _normalize_text(alt):
        return _normalize_terminal_punctuation(alt)
    return "For a breath, the scene holds while voices shift around you."
