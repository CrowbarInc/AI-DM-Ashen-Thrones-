"""Shared narrative-mode validator CTIR/resolution stubs (Cycle AL1b / AS5).

Support residue for gate, live-pipeline, and boundary suites that need minimal CTIR shells.
Validator predicate ownership stays in ``tests/test_narrative_mode_output_validator.py``.
"""
from __future__ import annotations

from typing import Any


def build_validator_narrative_mode_contract(**kwargs: Any) -> dict:
    """Minimal ``build_narrative_mode_contract`` wrapper for non-owner wiring tests."""
    from game.narrative_mode_contract import build_narrative_mode_contract

    return build_narrative_mode_contract(**kwargs)


def minimal_ctir_continuation() -> dict:
    return {"resolution": {"kind": "narrate", "requires_check": False}}


def minimal_ctir_action_outcome() -> dict:
    return {
        "resolution": {
            "kind": "skill_check",
            "requires_check": False,
            "skill_check": {"success": True, "roll": 14, "total": 18},
            "outcome_type": "search",
        }
    }


def resolution_pending_check() -> dict:
    return {"resolution": {"requires_check": True, "skill_check": {"dc": 12, "skill_id": "perception"}}}
