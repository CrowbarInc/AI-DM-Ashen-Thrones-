"""Shared Block S/T/U + golden direct-seam equivalence fixtures (Cycle AS6).

Import from here — not from ``tests/test_block_s_speaker_local_rebind_equivalence.py``.
"""
from __future__ import annotations

from typing import Any


def locked_runner_contract() -> dict[str, Any]:
    """Continuity-locked contract matching ``runner_strict_bundle`` NPC id ``runner``."""
    return {
        "primary_speaker_id": "runner",
        "primary_speaker_name": "Tavern Runner",
        "allowed_speaker_ids": ["runner"],
        "continuity_locked": True,
        "speaker_switch_allowed": False,
        "speaker_switch_reason": "block_s",
        "generic_fallback_forbidden": False,
        "offscene_speakers_forbidden": True,
        "interruption_allowed": True,
        "interruption_requires_scene_event": False,
        "debug": {"contract_missing": False},
    }


def stub_strict_social_details() -> dict[str, Any]:
    """Minimal strict-social build stub metadata for finalize-stack equivalence runs."""
    return {
        "used_internal_fallback": False,
        "final_emitted_source": "block_s_stub",
        "rejection_reasons": [],
        "deterministic_attempted": False,
        "deterministic_passed": False,
        "fallback_pool": "none",
        "fallback_kind": "none",
        "route_illegal_intercepted": False,
    }
