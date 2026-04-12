"""Multi-turn behavioral smoke tests over ``evaluate_behavioral_gauntlet`` (deterministic, no model calls)."""

from __future__ import annotations

import pytest

from tests.helpers.behavioral_gauntlet_eval import SCHEMA_VERSION, evaluate_behavioral_gauntlet
from tests.helpers.transcript_runner import snapshot_from_chat_payload

pytestmark = [pytest.mark.integration, pytest.mark.regression]


def _chat_payload(*, gm_text: str, scene_id: str | None = "frontier_gate") -> dict:
    """Minimal ``chat`` return shape for :func:`snapshot_from_chat_payload` (no I/O, no GPT)."""
    scene_block: dict = {}
    if scene_id:
        scene_block = {"scene": {"id": scene_id}}
    return {
        "gm_output": {"player_facing_text": gm_text},
        "scene": {"scene": scene_block.get("scene", {})},
        "session": {"scene_state": {}},
        "resolution": None,
        "journal": None,
        "world": None,
    }


# --- Layer A: direct behavioral smoke slices (simplified rows) ---


def test_behavioral_smoke_neutrality_passes_for_calm_bounded_reply():
    turns = [
        {
            "player_text": "What do I see at the gate?",
            "gm_text": "Mist and a posted notice; guards watch quietly without challenging you.",
        }
    ]
    result = evaluate_behavioral_gauntlet(turns)
    assert result["schema_version"] == SCHEMA_VERSION
    ax = result["axes"]["neutrality"]
    assert ax["passed"] is True
    assert "neutral_ok" in ax["reason_codes"]


def test_behavioral_smoke_neutrality_fails_for_ungrounded_hostility():
    turns = [
        {
            "player_text": "Where is the clerk’s window?",
            "gm_text": "How dare you — you're a liar and a traitor, you fool.",
        }
    ]
    result = evaluate_behavioral_gauntlet(turns)
    assert result["schema_version"] == SCHEMA_VERSION
    ax = result["axes"]["neutrality"]
    assert ax["passed"] is False
    assert "ungrounded_hostility" in ax["reason_codes"]


def test_behavioral_smoke_escalation_passes_when_pressure_is_proportional():
    turns = [
        {
            "player_text": "I curse you and draw steel — this ends now.",
            "gm_text": "He snarls and blood hammers in your skull as he attacks you; the room tilts toward combat.",
        }
    ]
    result = evaluate_behavioral_gauntlet(turns)
    assert result["schema_version"] == SCHEMA_VERSION
    ax = result["axes"]["escalation_correctness"]
    assert ax["passed"] is True
    assert "escalation_proportional" in ax["reason_codes"]


def test_behavioral_smoke_escalation_fails_when_neutral_input_jumps_to_threat():
    turns = [
        {
            "player_text": "I read the posted notice quietly.",
            "gm_text": "The sergeant attacks you without warning; steel flashes and blood sprays.",
        }
    ]
    result = evaluate_behavioral_gauntlet(turns)
    assert result["schema_version"] == SCHEMA_VERSION
    ax = result["axes"]["escalation_correctness"]
    assert ax["passed"] is False
    assert "escalation_too_high" in ax["reason_codes"]


def test_behavioral_smoke_reengagement_passes_when_followup_advances_exchange():
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
    result = evaluate_behavioral_gauntlet(turns)
    assert result["schema_version"] == SCHEMA_VERSION
    ax = result["axes"]["reengagement_quality"]
    assert ax["passed"] is True
    assert "reengagement_progress" in ax["reason_codes"]


def test_behavioral_smoke_reengagement_fails_for_repeat_dead_end():
    turns = [
        {"player_text": "Tell me about the gate.", "gm_text": "I need more specifics about what you mean."},
        {"player_text": "The north gate yesterday.", "gm_text": "Please be more specific about what you need."},
    ]
    result = evaluate_behavioral_gauntlet(turns)
    assert result["schema_version"] == SCHEMA_VERSION
    ax = result["axes"]["reengagement_quality"]
    assert ax["passed"] is False
    assert "reengagement_loop" in ax["reason_codes"]


def test_behavioral_smoke_dialogue_coherence_passes_for_same_thread_same_speaker():
    turns = [
        {
            "player_text": "Who stands watch?",
            "gm_text": "Two guards lean on spears; mist curls low.",
            "scene_id": "gate",
            "speaker_id": "watch_captain",
        },
        {
            "player_text": "I nod politely.",
            "gm_text": "They nod back, eyes still on the road.",
            "scene_id": "gate",
            "speaker_id": "watch_captain",
        },
    ]
    result = evaluate_behavioral_gauntlet(turns)
    assert result["schema_version"] == SCHEMA_VERSION
    ax = result["axes"]["dialogue_coherence"]
    assert ax["passed"] is True
    assert "coherence_ok" in ax["reason_codes"]


def test_behavioral_smoke_dialogue_coherence_fails_for_speaker_or_thread_reset():
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
    result = evaluate_behavioral_gauntlet(turns)
    assert result["schema_version"] == SCHEMA_VERSION
    ax = result["axes"]["dialogue_coherence"]
    assert ax["passed"] is False
    assert set(ax["reason_codes"]) & {"speaker_drift", "local_reset", "contradiction_local"}


def test_behavioral_smoke_expected_axis_single_axis_slice():
    turns = [
        {"player_text": "What do I hear?", "gm_text": "Distant drums; no threats yet."},
    ]
    result = evaluate_behavioral_gauntlet(turns, expected_axis={"neutrality"})
    assert result["schema_version"] == SCHEMA_VERSION
    assert set(result["axes"]) == {"neutrality"}
    assert result["overall_passed"] == result["axes"]["neutrality"]["passed"]


def test_behavioral_smoke_metadata_light_sparse_rows_still_evaluate():
    """Smoke-level check that thin rows still run through the public evaluator."""
    turns = [{"player_text": "Hi", "gm_text": "Hello traveler.", "metadata": {}}]
    result = evaluate_behavioral_gauntlet(turns)
    assert result["schema_version"] == SCHEMA_VERSION
    assert "axes" in result and "overall_passed" in result
    assert set(result["axes"]) == {"dialogue_coherence", "escalation_correctness", "neutrality", "reengagement_quality"}
    for name in result["axes"]:
        assert result["axes"][name]["axis"] == name


# --- Layer B: compatibility bridge (transcript snapshot shape) ---


def test_behavioral_smoke_accepts_gauntlet_style_transcript_slice():
    slice_rows = [
        snapshot_from_chat_payload(
            0,
            "What do I see along the road?",
            _chat_payload(gm_text="Mist and a quiet watch post; nothing escalates yet."),
        ),
        snapshot_from_chat_payload(
            1,
            "I step closer to read the notice.",
            _chat_payload(gm_text="Welcome to the tutorial — starting fresh at the gate."),
        ),
    ]
    result = evaluate_behavioral_gauntlet(slice_rows)
    assert result["schema_version"] == "behavioral_gauntlet_eval.v1"
    assert result["axes"]["dialogue_coherence"]["passed"] is False
    assert "local_reset" in result["axes"]["dialogue_coherence"]["reason_codes"]
    assert result["overall_passed"] is False
