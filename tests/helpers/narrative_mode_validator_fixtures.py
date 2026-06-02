"""Shared narrative-mode validator CTIR/resolution stubs (Cycle AL1b).

Support residue for gate and live-pipeline suites that need minimal CTIR shells.
Validator predicate ownership stays in ``tests/test_narrative_mode_output_validator.py``.
"""
from __future__ import annotations


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
