"""Edge cases for interaction continuity repair + validation (Objective #14 Block #4)."""
from __future__ import annotations

import pytest

from game.interaction_continuity import (
    BRIDGE_TEMPLATES,
    _has_dialogue_presence,
    _pick_bridge_template,
    repair_interaction_continuity,
    validate_interaction_continuity,
)

pytestmark = pytest.mark.unit


def _strong_contract(*, anchor: str = "npc_melka") -> dict:
    return {
        "enabled": True,
        "continuity_strength": "strong",
        "anchored_interlocutor_id": anchor,
        "preserve_conversational_thread": True,
        "speaker_selection_contract": None,
    }


def test_multiline_same_speaker_labels_no_multi_violation_no_strip():
    c = _strong_contract()
    text = 'Guard: "Halt."\nGuard: "You can\'t pass."'
    v = validate_interaction_continuity(text, interaction_continuity_contract=c)
    assert "multi_speaker_interruption_under_continuity" not in v["violations"]
    assert "speaker_switch_without_explicit_cue" not in v["violations"]
    r = repair_interaction_continuity(text, validation=v, interaction_continuity_contract=c)
    assert r["applied"] is False


def test_short_first_quote_prefers_longer_second_on_strip():
    c = _strong_contract()
    text = 'Guard: "What?" Captain: "The eastern road is closed until dawn, and that is final."'
    v = validate_interaction_continuity(text, interaction_continuity_contract=c)
    assert v["ok"] is False
    r = repair_interaction_continuity(text, validation=v, interaction_continuity_contract=c)
    assert r["applied"] is True
    assert "eastern road" in r["repaired_text"].lower()
    assert "What?" not in r["repaired_text"]


def test_crowd_mention_without_speech_not_multi_speaker_violation():
    c = _strong_contract()
    text = "You hear shouting in the distance."
    v = validate_interaction_continuity(text, interaction_continuity_contract=c)
    assert "multi_speaker_interruption_under_continuity" not in v["violations"]
    assert "speaker_switch_without_explicit_cue" not in v["violations"]


def test_narration_with_action_verbs_not_wrapped_to_dialogue():
    c = _strong_contract()
    text = "The marshal walks to the gate and looks you over."
    v = validate_interaction_continuity(text, interaction_continuity_contract=c)
    assert "dialogue_absent_under_continuity" in v["violations"]
    r = repair_interaction_continuity(text, validation=v, interaction_continuity_contract=c)
    assert r["applied"] is False


def test_bridge_template_is_deterministic_and_from_set():
    a = _pick_bridge_template("stable-seed-text")
    b = _pick_bridge_template("stable-seed-text")
    assert a == b
    assert a in BRIDGE_TEMPLATES
    found = {_pick_bridge_template(f"probe-{i}-x") for i in range(80)}
    assert found.issubset(set(BRIDGE_TEMPLATES))
    assert len(found) >= 2


def test_strip_uncued_keeps_actionable_dialogue():
    c = _strong_contract()
    text = 'Guard: "Stay where you are."\nA sharp yell from the alley: "Run!"'
    v = validate_interaction_continuity(text, interaction_continuity_contract=c)
    assert v["ok"] is False
    r = repair_interaction_continuity(text, validation=v, interaction_continuity_contract=c)
    assert r["applied"] is True
    assert _has_dialogue_presence(r["repaired_text"])
    assert '"' in r["repaired_text"] or "\u201c" in r["repaired_text"]
