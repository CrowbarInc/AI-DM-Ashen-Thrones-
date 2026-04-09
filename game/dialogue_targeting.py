"""Vocative-facing targeting helpers (thin compatibility surface).

Implementations live in :mod:`game.interaction_context` next to roster construction and
:func:`~game.interaction_context.match_generic_role_address` to avoid import cycles.

**Not here:** precedence-ordered authoritative binding — use
:func:`game.interaction_context.resolve_authoritative_social_target` (explicit target →
declared switch → spoken vocative → comma vocative → generic role → continuity → substring,
etc.). Import from this module only when you need vocative parsing without pulling the full
interaction-context API.
"""
from __future__ import annotations

from game.interaction_context import (
    line_opens_with_comma_vocative,
    npc_id_from_substring_line,
    npc_id_from_vocative_line,
    resolve_spoken_vocative_target,
)

__all__ = [
    "line_opens_with_comma_vocative",
    "npc_id_from_substring_line",
    "npc_id_from_vocative_line",
    "resolve_spoken_vocative_target",
]
