"""Pure unit tests for ``tests.helpers.behavioral_gauntlet_eval``."""

from __future__ import annotations

import pytest

from tests.helpers.behavioral_gauntlet_eval import (
    SCHEMA_VERSION,
    evaluate_behavioral_gauntlet,
    evaluate_dialogue_coherence,
    evaluate_escalation_correctness,
    evaluate_neutrality,
    evaluate_reengagement_quality,
    normalize_turn_dict,
)

pytestmark = pytest.mark.unit


def test_evaluate_behavioral_gauntlet_shape_and_expected_axis_filter():
    turns = [
        {"player_text": "What do I see at the gate?", "gm_text": "Mist and a posted notice; guards watch quietly."},
        {"player_text": "I read the notice.", "gm_text": "Orders mention curfew because patrols are short-handed."},
    ]
    out = evaluate_behavioral_gauntlet(turns, expected_axis={"neutrality", "dialogue_coherence"})
    assert out["schema_version"] == SCHEMA_VERSION
    assert out["overall_passed"] is True
    assert isinstance(out.get("gameplay_validation"), dict)
    assert isinstance(out.get("dead_turn_run_report"), dict)
    assert out["dead_turn_run_report"]["dead_turn_count"] == 0
    assert out["dead_turn_run_report"]["banner"] is None
    assert out["gameplay_validation"]["run_valid"] is True
    assert set(out["axes"]) == {"dialogue_coherence", "neutrality"}
    for axis in out["axes"].values():
        assert set(axis) == {"axis", "passed", "score", "reason_codes", "summary", "evidence_turn_indexes"}
        assert axis["score"] in (0, 1, 2)
        assert isinstance(axis["reason_codes"], list)


def test_evaluate_behavioral_gauntlet_rejects_unknown_axis():
    with pytest.raises(ValueError):
        evaluate_behavioral_gauntlet([{"player_text": "Hi", "gm_text": "Hello."}], expected_axis={"not_a_real_axis"})


def test_neutrality_pass_clear():
    slices = [
        normalize_turn_dict(
            {"player_text": "What do I see?", "gm_text": "A quiet yard; a notice is posted by the door."},
            turn_index=0,
        )
    ]
    res = evaluate_neutrality(slices)
    assert res.passed and res.score == 2
    assert res.reason_codes == ("neutral_ok",)


def test_neutrality_fail_ungrounded_hostility():
    slices = [
        normalize_turn_dict(
            {
                "player_text": "I look around calmly.",
                "gm_text": "How dare you — you're a liar and a traitor, you fool.",
            },
            turn_index=0,
        )
    ]
    res = evaluate_neutrality(slices)
    assert not res.passed and res.score == 0
    assert "ungrounded_hostility" in res.reason_codes
    assert res.evidence_turn_indexes == (0,)


def test_neutrality_metadata_light_empty_strings():
    slices = [normalize_turn_dict({}, turn_index=0)]
    res = evaluate_neutrality(slices)
    assert res.passed and res.reason_codes == ("neutral_ok",)


def test_escalation_pass_proportional_hostility():
    slices = [
        normalize_turn_dict(
            {
                "player_text": "I spit in his face and swing my fist.",
                "gm_text": "He snarls and bloodies your knuckles on his jaw; the room tilts toward combat.",
            },
            turn_index=0,
        )
    ]
    res = evaluate_escalation_correctness(slices)
    assert res.passed and "escalation_proportional" in res.reason_codes


def test_escalation_fail_too_high_for_neutral_player():
    slices = [
        normalize_turn_dict(
            {
                "player_text": "I read the posted notice quietly.",
                "gm_text": "The sergeant attacks you without warning; steel flashes and blood sprays.",
            },
            turn_index=0,
        )
    ]
    res = evaluate_escalation_correctness(slices)
    assert not res.passed
    assert "escalation_too_high" in res.reason_codes


def test_escalation_fail_too_flat_for_hostile_player():
    slices = [
        normalize_turn_dict(
            {
                "player_text": "I draw my sword and threaten to kill you.",
                "gm_text": "Certainly! Anything you wish — happy to oblige with no trouble at all.",
            },
            turn_index=0,
        )
    ]
    res = evaluate_escalation_correctness(slices)
    assert not res.passed
    assert "escalation_too_flat" in res.reason_codes


def test_escalation_metadata_light_resolution_kind_only():
    slices = [
        normalize_turn_dict({"resolution_kind": "social", "player_text": "", "gm_text": ""}, turn_index=0)
    ]
    res = evaluate_escalation_correctness(slices)
    assert res.passed


def test_reengagement_pass_progress_after_clarify():
    turns = [
        {
            "player_text": "What rumors matter here?",
            "gm_text": "I need more specifics — which quarter, which night?",
        },
        {
            "player_text": "The market quarter, last night.",
            "gm_text": "Ash on the cobbles narrows it; try the east lane where a brazier still smolders.",
        },
    ]
    slices = tuple(normalize_turn_dict(row, turn_index=i) for i, row in enumerate(turns))
    res = evaluate_reengagement_quality(slices)
    assert res.passed and "reengagement_progress" in res.reason_codes


def test_reengagement_fail_adjacent_stonewall_loop():
    turns = [
        {"player_text": "Tell me about the gate.", "gm_text": "I need more specifics about what you mean."},
        {"player_text": "The north gate yesterday.", "gm_text": "Please be more specific about what you need."},
    ]
    slices = tuple(normalize_turn_dict(row, turn_index=i) for i, row in enumerate(turns))
    res = evaluate_reengagement_quality(slices)
    assert not res.passed
    assert "reengagement_loop" in res.reason_codes


def test_reengagement_metadata_light_single_turn():
    slices = (normalize_turn_dict({"player_text": "Hello?", "gm_text": "Yes?"}, turn_index=0),)
    res = evaluate_reengagement_quality(slices)
    assert res.passed and res.evidence_turn_indexes == ()


def test_coherence_pass_adjacent_consistent():
    turns = [
        {"player_text": "Who stands watch?", "gm_text": "Two guards lean on spears; mist curls low.", "scene_id": "gate"},
        {"player_text": "I nod politely.", "gm_text": "They nod back, eyes still on the road.", "scene_id": "gate"},
    ]
    slices = tuple(normalize_turn_dict(row, turn_index=i) for i, row in enumerate(turns))
    res = evaluate_dialogue_coherence(slices)
    assert res.passed and "coherence_ok" in res.reason_codes


def test_coherence_fail_speaker_drift_same_scene():
    turns = [
        {
            "player_text": "What is the policy?",
            "gm_text": "Orders are posted; curfew is strict.",
            "scene_id": "gate",
            "speaker_id": "gate_sergeant",
        },
        {
            "player_text": "And the fines?",
            "gm_text": "Coin or labor; clerk records both.",
            "scene_id": "gate",
            "speaker_id": "clerk_npc",
        },
    ]
    slices = tuple(normalize_turn_dict(row, turn_index=i) for i, row in enumerate(turns))
    res = evaluate_dialogue_coherence(slices)
    assert not res.passed
    assert "speaker_drift" in res.reason_codes


def test_coherence_fail_local_reset_phrase_after_first_turn():
    turns = [
        {"player_text": "I study the gate.", "gm_text": "Timber and iron; travelers shuffle past."},
        {"player_text": "I step closer.", "gm_text": "Welcome to the tutorial — starting fresh at the gate."},
    ]
    slices = tuple(normalize_turn_dict(row, turn_index=i) for i, row in enumerate(turns))
    res = evaluate_dialogue_coherence(slices)
    assert not res.passed
    assert "local_reset" in res.reason_codes


def test_coherence_fail_contradiction_local_gate():
    turns = [
        {"player_text": "Is there a gate?", "gm_text": "There is no gate here today; only open field."},
        {"player_text": "I walk forward.", "gm_text": "You pass through the gate into the yard beyond."},
    ]
    slices = tuple(normalize_turn_dict(row, turn_index=i) for i, row in enumerate(turns))
    res = evaluate_dialogue_coherence(slices)
    assert not res.passed
    assert "contradiction_local" in res.reason_codes


def test_coherence_metadata_light_missing_scene_and_speaker():
    turns = [
        {"player_text": "Hi", "gm_text": "Hello traveler."},
        {"player_text": "Bye", "gm_text": "Safe roads."},
    ]
    slices = tuple(normalize_turn_dict(row, turn_index=i) for i, row in enumerate(turns))
    res = evaluate_dialogue_coherence(slices)
    assert res.passed


def test_normalize_turn_dict_accepts_messages_shape():
    raw = {
        "messages": [
            {"role": "user", "content": "What do I hear?"},
            {"role": "assistant", "content": "Distant drums; no threats yet."},
        ]
    }
    sl = normalize_turn_dict(raw, turn_index=0)
    assert sl.player_text.startswith("What do I hear")
    assert "drums" in sl.gm_text.lower()


def test_neutrality_grounded_hostility_allowed():
    slices = [
        normalize_turn_dict(
            {
                "player_text": "What does the notice say?",
                "gm_text": "The captain will accuse you directly because orders demand it; the posted law is cited.",
            },
            turn_index=0,
        )
    ]
    res = evaluate_neutrality(slices)
    assert res.passed


def test_speaker_drift_allowed_with_handoff_cue():
    turns = [
        {
            "player_text": "What is the policy?",
            "gm_text": "Orders are posted; curfew is strict.",
            "scene_id": "gate",
            "speaker_id": "gate_sergeant",
        },
        {
            "player_text": "I turn to the clerk about fines.",
            "gm_text": "Coin or labor; the clerk records both.",
            "scene_id": "gate",
            "speaker_id": "clerk_npc",
        },
    ]
    slices = tuple(normalize_turn_dict(row, turn_index=i) for i, row in enumerate(turns))
    res = evaluate_dialogue_coherence(slices)
    assert res.passed
