"""Session module: playthrough state management and reset.

Runtime fields live in ``session.json``; campaign/world/scene templates are separate
(see ``game/campaign_state.py`` for layering). Reset replaces the runtime document
with ``create_fresh_session_document()`` — it does not wipe bootstrap files.
"""
from __future__ import annotations

from typing import Any, Dict

from game.campaign_state import create_fresh_session_document


def reset_session_state(session: Dict[str, Any]) -> Dict[str, Any]:
    """Replace *runtime* session fields with a fresh dict graph.

    Does not touch campaign.json, world.json, or scene JSONs. Stale keys are
    removed via ``clear()`` so prior playthrough-only fields cannot leak.

    For a full New Campaign (session + combat + world playthrough + log), use
    :func:`game.campaign_reset.apply_new_campaign_hard_reset` — ``world.json``
    must be cleared separately or contamination persists across session replacement.
    """
    fresh = create_fresh_session_document()
    session.clear()
    session.update(fresh)
    print("[SESSION RESET] runtime state cleared")
    return session
