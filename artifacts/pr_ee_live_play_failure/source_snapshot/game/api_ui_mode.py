"""Shared request helper for resolving UI mode (Objective #15 integration).

This module exists so API endpoints don't re-derive mode rules ad hoc.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from fastapi import Request

from game.ui_mode_policy import PLAYER_UI_MODE, UiModePolicyError, get_ui_mode_policy


def resolve_requested_ui_mode(
    request: Request | None,
    payload: Mapping[str, Any] | None = None,
) -> str:
    """Resolve requested ui_mode from query params or request payload.

    Resolution order:
    - query param: ?ui_mode=...
    - JSON/form payload key: ui_mode / uiMode (when caller provides *payload*)

    Default is fail-safe ``player``.
    Unknown modes fail closed using the canonical policy module.
    """

    mode = request.query_params.get("ui_mode") if request is not None else None
    if not mode and payload:
        raw = payload.get("ui_mode")
        if raw is None:
            raw = payload.get("uiMode")
        if isinstance(raw, str):
            mode = raw
    mode = (mode or "").strip() or PLAYER_UI_MODE
    # Canonical validation (raises UiModePolicyError for unknown).
    get_ui_mode_policy(mode)
    return mode


__all__ = ("resolve_requested_ui_mode", "UiModePolicyError")

