"""BV16C — terminal pipeline owner-module test seams (tests only).

Monkeypatch hooks for finalize-tail delegates must target canonical owner modules,
not ``game.final_emission_terminal_pipeline`` namespace bindings.
"""
from __future__ import annotations

from typing import Any, Callable

import game.final_emission_acceptance_quality as acceptance_quality
import game.final_emission_repairs as emission_repairs
import game.final_emission_visibility_fallback as visibility_fallback
import game.interaction_continuity as interaction_continuity


def visibility_enforcement_noop(out: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    return out


def patch_visibility_enforcement_noop(monkeypatch: Any) -> None:
    monkeypatch.setattr(visibility_fallback, "apply_visibility_enforcement", visibility_enforcement_noop)


def patch_visibility_enforcement(
    monkeypatch: Any,
    hook: Callable[..., Any],
) -> None:
    monkeypatch.setattr(visibility_fallback, "apply_visibility_enforcement", hook)
