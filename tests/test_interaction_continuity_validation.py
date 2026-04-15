"""Downstream interaction-continuity validation and enforcement coverage."""
from __future__ import annotations

import pytest

from game.final_emission_gate import _attach_interaction_continuity_validation
from game.interaction_continuity import validate_interaction_continuity

pytestmark = pytest.mark.unit


def _strong_contract(*, anchor: str = "npc_melka") -> dict:
    return {
        "enabled": True,
        "continuity_strength": "strong",
        "anchored_interlocutor_id": anchor,
        "preserve_conversational_thread": True,
        "speaker_selection_contract": None,
    }


def _soft_contract() -> dict:
    return {
        "enabled": True,
        "continuity_strength": "soft",
        "anchored_interlocutor_id": "",
        "preserve_conversational_thread": True,
        "speaker_selection_contract": None,
    }


def _assert_validation_shape(v: dict) -> None:
    assert set(v.keys()) == {
        "ok",
        "enabled",
        "continuity_strength",
        "violations",
        "warnings",
        "facts",
        "debug",
    }
    assert isinstance(v["violations"], list)
    assert isinstance(v["warnings"], list)
    assert isinstance(v["facts"], dict)
    assert isinstance(v["debug"], dict)
    for k in (
        "anchored_interlocutor_id",
        "anchor_required",
        "speaker_switch_detected",
        "explicit_switch_cue_present",
        "thread_drop_detected",
        "narrator_bridge_present",
        "multi_speaker_pattern_present",
        "dialogue_presence",
    ):
        assert k in v["facts"]
    assert "speaker_labels_detected" in v["debug"]
    assert "cue_labels" in v["debug"]
    assert "reason_path" in v["debug"]


def test_validation_is_inert_when_contract_missing_or_invalid():
    v = validate_interaction_continuity("any", interaction_continuity_contract=None)
    _assert_validation_shape(v)
    assert v["ok"] is True
    assert v["enabled"] is False
    assert v["continuity_strength"] == "none"
    assert v["violations"] == []

    v2 = validate_interaction_continuity(
        "any",
        interaction_continuity_contract={"enabled": True, "continuity_strength": "bogus"},
    )
    assert v2["enabled"] is False
    assert v2["violations"] == []

    v3 = validate_interaction_continuity(
        "any",
        interaction_continuity_contract={"enabled": "yes", "continuity_strength": "strong"},
    )
    assert v3["enabled"] is False


def test_validation_is_inert_when_contract_disabled():
    c = {**_strong_contract(), "enabled": False}
    v = validate_interaction_continuity('"Hello," she says.', interaction_continuity_contract=c)
    assert v["ok"] is True
    assert v["enabled"] is False
    assert v["violations"] == []


def test_validation_accepts_single_anchored_dialogue_under_strong_continuity():
    c = _strong_contract()
    text = '"The east road is watched," Melka says, holding your gaze.'
    v = validate_interaction_continuity(text, interaction_continuity_contract=c)
    _assert_validation_shape(v)
    assert v["ok"] is True
    assert v["enabled"] is True
    assert v["continuity_strength"] == "strong"
    assert v["violations"] == []
    assert v["facts"]["dialogue_presence"] is True
    assert v["facts"]["anchor_required"] is True


def test_validation_flags_pure_narration_under_strong_continuity():
    c = _strong_contract()
    text = (
        "The weather shifted and clouds gathered over the market square while distant bells "
        "marked the turning of the watch, indifferent to the question still hanging between you."
    )
    v = validate_interaction_continuity(text, interaction_continuity_contract=c)
    assert v["ok"] is False
    assert "dialogue_absent_under_continuity" in v["violations"]
    assert "anchored_interlocutor_dropped" in v["violations"]
    assert "conversational_thread_dropped" in v["violations"]


def test_validation_flags_uncued_multi_speaker_interruption_under_strong_continuity():
    c = _strong_contract()
    text = 'Someone from the crowd shouts, "Watch out!"'
    v = validate_interaction_continuity(text, interaction_continuity_contract=c)
    assert v["ok"] is False
    assert "multi_speaker_interruption_under_continuity" in v["violations"]
    assert "speaker_switch_without_explicit_cue" in v["violations"]


def test_validation_allows_explicit_handoff_under_strong_continuity():
    c = _strong_contract()
    text = (
        'A voice from the crowd cuts in before Melka can answer. "Watch out!" the stranger snaps.'
    )
    v = validate_interaction_continuity(text, interaction_continuity_contract=c)
    assert "speaker_switch_without_explicit_cue" not in v["violations"]
    assert "multi_speaker_interruption_under_continuity" not in v["violations"]


def test_validation_allows_soft_narrator_bridge_with_warning_only():
    c = _soft_contract()
    text = 'Nearby, the air shifts. Melka says, "Yes—we move at dusk."'
    v = validate_interaction_continuity(text, interaction_continuity_contract=c)
    assert v["ok"] is True
    assert "narrator_bridge_used" in v["warnings"]


def test_validation_flags_detached_exposition_under_soft_continuity():
    c = _soft_contract()
    text = (
        "The regional economy depends on tolls, wayposts, and seasonal trade convoys moving "
        "between jurisdictions, a fact recorded in dry ledgers that never mention your question."
    )
    v = validate_interaction_continuity(
        text,
        interaction_continuity_contract=c,
        response_type_contract={"required_response_type": "dialogue"},
    )
    assert v["ok"] is False
    assert "context_continuity_missing" in v["violations"]


def test_validation_flags_multi_speaker_labels_under_strong_continuity():
    c = _strong_contract()
    text = 'Guard: "Halt."\nMerchant: "Wait—he is with me."'
    v = validate_interaction_continuity(text, interaction_continuity_contract=c)
    assert "multi_speaker_interruption_under_continuity" in v["violations"]


def test_emission_gate_attaches_interaction_continuity_validation_metadata():
    out: dict = {
        "player_facing_text": "The scene holds.",
        "_final_emission_meta": {},
        "metadata": {},
        "response_policy": {"interaction_continuity": _strong_contract()},
    }
    resolution = {"metadata": {"emission_debug": {}}}
    _attach_interaction_continuity_validation(
        out,
        resolution_for_contracts=resolution,
        eff_resolution=None,
        session=None,
    )
    icv = out["metadata"]["emission_debug"]["interaction_continuity_validation"]
    _assert_validation_shape(icv)
    assert out["_final_emission_meta"]["interaction_continuity_validation"] is icv
    assert resolution["metadata"]["emission_debug"]["interaction_continuity_validation"] is icv
