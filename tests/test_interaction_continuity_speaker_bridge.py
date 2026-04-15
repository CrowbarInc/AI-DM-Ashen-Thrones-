"""Downstream speaker-bridge behavior coverage.

Validates how bridge-related continuity behavior appears in final outputs.

Does NOT own:

* gate-step ordering
* bridge application logic
* repair semantics
"""
from __future__ import annotations

import pytest

from game.interaction_continuity import repair_interaction_continuity, validate_interaction_continuity

pytestmark = pytest.mark.unit

_LIVE_MALFORMED = 'South road." Tavern Runner nods once. "Old Millstone.'


def _ssc_locked_tavern_runner() -> dict:
    return {
        "continuity_locked": True,
        "primary_speaker_id": "tavern_runner",
        "primary_speaker_name": "Tavern Runner",
        "allowed_speaker_ids": ["tavern_runner"],
        "speaker_switch_allowed": False,
    }


def _strong_ic_with_ssc() -> dict:
    return {
        "enabled": True,
        "continuity_strength": "strong",
        "anchored_interlocutor_id": "tavern_runner",
        "preserve_conversational_thread": True,
        "speaker_selection_contract": _ssc_locked_tavern_runner(),
    }


def test_malformed_dialogue_output_preserves_continuity_constraints_without_repair():
    ic = _strong_ic_with_ssc()
    base = validate_interaction_continuity(_LIVE_MALFORMED, interaction_continuity_contract=ic)
    assert base["ok"] is True
    repair = repair_interaction_continuity(_LIVE_MALFORMED, validation=base, interaction_continuity_contract=ic)
    assert repair["applied"] is False


def test_output_exhibits_continuity_repaired_structure_for_bridge_shaped_failure():
    ic = _strong_ic_with_ssc()
    v = validate_interaction_continuity(_LIVE_MALFORMED, interaction_continuity_contract=ic)
    assert v["ok"] is True
    v["ok"] = False
    v["violations"] = list(v["violations"]) + ["malformed_speaker_attribution_under_continuity"]
    v.setdefault("debug", {})["speaker_binding_reason_code"] = "speaker_binding_mismatch"

    r = repair_interaction_continuity(_LIVE_MALFORMED, validation=v, interaction_continuity_contract=ic)
    assert r["applied"] is True
    assert r["repair_type"] == "repair_malformed_speaker_attribution"
    assert "Tavern Runner" in r["repaired_text"]
    assert "Old Millstone" in r["repaired_text"]
    assert "South road" in r["repaired_text"]
    assert "malformed explicit attribution salvaged" in " ".join(r["strategy_notes"]).lower()


def test_output_preserves_continuity_constraints_when_anchor_is_not_canonical():
    ic = _strong_ic_with_ssc()
    unrecoverable = 'South road." Stranger waits. "Old Millstone.'
    v = validate_interaction_continuity(unrecoverable, interaction_continuity_contract=ic)
    assert v["ok"] is True
    v["ok"] = False
    v["violations"] = list(v["violations"]) + ["malformed_speaker_attribution_under_continuity"]
    v.setdefault("debug", {})["speaker_binding_reason_code"] = "speaker_binding_mismatch"

    r = repair_interaction_continuity(unrecoverable, validation=v, interaction_continuity_contract=ic)
    assert r["applied"] is False
    assert r["repair_type"] is None
    assert r["repaired_text"] == unrecoverable
