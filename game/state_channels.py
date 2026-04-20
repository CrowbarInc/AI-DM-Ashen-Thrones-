"""Runtime channel vocabulary and key-based projection for state payloads.

This module is **boundary enforcement**, not state ownership: it classifies
top-level mapping keys for separation between player/public surfaces, debug
telemetry, and author/internal scaffolding. Callers decide when to project or
assert; this layer stays free of world mutation, I/O, and gate/API imports.

Classification is **key- and name-shape-based only** (no value inspection, no
secret inference). Unknown keys are treated as **public** unless they match
debug or author rules — debug/author rules are conservative extensions over an
implicit public complement.
"""

from __future__ import annotations

from typing import Any, Callable, Mapping

# --- Channel vocabulary (string tags for cross-layer contracts / logging) ---

PUBLIC_CHANNEL = "public"
DEBUG_CHANNEL = "debug"
AUTHOR_CHANNEL = "author"


class ChannelSeparationError(ValueError):
    """Raised when a payload mixes channels in a forbidden way (e.g. debug keys in a GPT prompt bundle)."""


# --- Explicit sets (conservative; extend here as ownership hardens) ---

_DEBUG_EXACT_KEYS = frozenset(
    {
        "_final_emission_meta",
        "stage_diff_telemetry",
        "dead_turn",
        "reason_codes",
    }
)

_DEBUG_KEY_SUFFIXES: tuple[str, ...] = (
    "_debug",
    "_trace",
    "_telemetry",
)

_DEBUG_KEY_PREFIXES: tuple[str, ...] = (
    "debug_",
    "telemetry_",
)

# Evaluator / observability roots (top-level only; no value inspection).
_DEBUG_EVALUATOR_KEYS = frozenset(
    {
        "narrative_authenticity_eval",
        "playability_eval",
    }
)

_AUTHOR_EXACT_KEYS = frozenset(
    {
        "author_notes",
        "planner_graph",
        "planner_state",
        "internal_state",
    }
)

_AUTHOR_KEY_SUFFIXES: tuple[str, ...] = (
    "_author",
    "_internal",
    "_planner",
    "_scaffold",
    "_hidden",
)

_AUTHOR_KEY_PREFIXES: tuple[str, ...] = (
    "author_",
    "internal_",
    "planner_",
    "hidden_",
)


def _str_key(key: Any) -> str:
    if isinstance(key, str):
        return key
    return str(key)


def is_debug_key(key: str) -> bool:
    k = _str_key(key)
    if k in _DEBUG_EXACT_KEYS:
        return True
    if k in _DEBUG_EVALUATOR_KEYS:
        return True
    lowered = k.lower()
    for p in _DEBUG_KEY_PREFIXES:
        if lowered.startswith(p):
            return True
    for s in _DEBUG_KEY_SUFFIXES:
        if k.endswith(s):
            return True
    # Observability-oriented evaluator roots / suffixes (top-level only).
    if lowered.startswith("evaluator_"):
        return True
    if lowered.endswith("_evaluator_meta") or lowered.endswith("_evaluator_output"):
        return True
    return False


def is_author_key(key: str) -> bool:
    k = _str_key(key)
    if k in _AUTHOR_EXACT_KEYS:
        return True
    lowered = k.lower()
    for p in _AUTHOR_KEY_PREFIXES:
        if lowered.startswith(p):
            return True
    for s in _AUTHOR_KEY_SUFFIXES:
        if k.endswith(s):
            return True
    return False


def is_public_key(key: str) -> bool:
    """True when *key* is neither debug nor author (implicit public complement)."""
    return not is_debug_key(key) and not is_author_key(key)


def _project(
    payload: Mapping[str, Any] | None,
    predicate: Callable[[str], bool],
) -> dict[str, Any]:
    if not payload:
        return {}
    out: dict[str, Any] = {}
    for raw_k, v in payload.items():
        k = _str_key(raw_k)
        if predicate(k):
            out[k] = v
    return out


def project_public_payload(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return a shallow copy containing only **public** top-level keys."""
    return _project(payload, is_public_key)


def project_debug_payload(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return a shallow copy containing only **debug** top-level keys."""
    return _project(payload, is_debug_key)


def project_author_payload(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return a shallow copy containing only **author** top-level keys."""
    return _project(payload, is_author_key)


def strip_non_public_payload(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Strip debug and author keys; same result as :func:`project_public_payload`."""
    return project_public_payload(payload)


def assert_no_debug_keys_in_prompt_payload(payload: Mapping[str, Any] | None) -> None:
    """Fail closed if any top-level key is classified as debug (GPT prompt / grounding input)."""
    if not payload:
        return
    bad = sorted(k for k in payload if is_debug_key(_str_key(k)))
    if bad:
        raise ChannelSeparationError(
            f"prompt payload contains debug-classified keys: {bad!r} "
            f"(channels: use {PUBLIC_CHANNEL!r} only for model input surfaces)"
        )


def assert_no_author_keys_in_player_output(payload: Mapping[str, Any] | None) -> None:
    """Fail closed if any top-level key is classified as author (player-visible output)."""
    if not payload:
        return
    bad = sorted(k for k in payload if is_author_key(_str_key(k)))
    if bad:
        raise ChannelSeparationError(
            f"player output contains author-classified keys: {bad!r}"
        )


# Explicit exports for static checkers / readers
__all__ = (
    "PUBLIC_CHANNEL",
    "DEBUG_CHANNEL",
    "AUTHOR_CHANNEL",
    "ChannelSeparationError",
    "is_public_key",
    "is_debug_key",
    "is_author_key",
    "project_public_payload",
    "project_debug_payload",
    "project_author_payload",
    "strip_non_public_payload",
    "assert_no_debug_keys_in_prompt_payload",
    "assert_no_author_keys_in_player_output",
)
