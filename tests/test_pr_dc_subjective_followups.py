"""PR-DC: ordinary experiential questions use the existing claim-only reply plan.

Closed frames only. Restricted, consequential, third-person, and travel routes
stay on their existing classifications. No provider calls.
"""
from __future__ import annotations

import json

import pytest

from game.social import _bounded_social_reply_plan_for_missing_topic
from tests.test_pr_ce_subjective_preference_classification import _assert_claim_only_subjective, _resolve
from tests.test_pr_db_speaker_grounding import (
    TURN_1,
    TURN_2,
    TURN_3,
    _bind_guard,
    _focus,
    _gate_session_scene,
    play_turn,
)

pytestmark = pytest.mark.unit

_HARMLESS = "harmless_subjective_response_permitted"

EXPERIENTIAL_PROMPTS = (
    "Does the rain make it harder to keep watch?",
    "Does it get any easier after a while?",
    "Is standing in the cold uncomfortable?",
    "Do long shifts leave you tired?",
    "Do you enjoy working at the gate?",
    "Does the noise bother you?",
    "Is the work stressful?",
    "Why do you prefer somewhere dry?",
)

THIRD_PARTY_PROMPTS = (
    "Does the baker find early mornings tiring?",
    "Does the innkeeper enjoy busy evenings?",
)

NEGATIVE_PROMPTS = (
    ("Does rain expose weaknesses in the gate?", "genuine_uncertainty"),
    ("Can smugglers enter unnoticed during storms?", "genuine_uncertainty"),
    ("Which guards abandon their posts?", "genuine_uncertainty"),
    ("Where is the secret tunnel?", "genuine_refusal"),
    ("Does the captain know the patrol's location?", "genuine_uncertainty"),
    ("Does the captain have a hidden criminal past?", "genuine_uncertainty"),
    ("Can the captain unlock the gate for me?", "genuine_uncertainty"),
    ("Will the captain waive the entry fee?", "genuine_uncertainty"),
    ("Can I persuade the captain to leave?", "genuine_uncertainty"),
    ("Does the rain reveal hidden tracks?", "genuine_uncertainty"),
    ("What defenses protect the gate?", "genuine_uncertainty"),
    ("Is the captain secretly working for another faction?", "genuine_uncertainty"),
    ("What happened to the missing patrol?", "genuine_uncertainty"),
    ("Can the captain promise me safe passage?", "genuine_uncertainty"),
    ("Does rain make it easier to assassinate the captain?", "genuine_uncertainty"),
)


def _plan(text: str, *, action_type: str = "question", attitude: str = "neutral", topic_revealed: bool = False) -> dict:
    return _bounded_social_reply_plan_for_missing_topic(
        action_type=action_type,
        player_text=text,
        npc={"disposition": attitude},
        topic_revealed=topic_revealed,
    )


@pytest.mark.parametrize("prompt", EXPERIENTIAL_PROMPTS)
def test_pr_dc_experiential_frames_are_claim_only(prompt: str) -> None:
    resolution = _resolve(prompt, role_id="guard_captain", name="Guard Captain", role="guard")
    social = resolution["social"]
    _assert_claim_only_subjective(social)
    assert social["reply_kind"] == "answer"
    assert resolution.get("state_changes") in ({}, None)


@pytest.mark.parametrize("prompt", THIRD_PARTY_PROMPTS)
def test_pr_dc_third_person_experience_stays_uncertain(prompt: str) -> None:
    plan = _plan(prompt)
    assert plan["reply_plan_kind"] == "genuine_uncertainty"
    assert plan["incidental_subjective_allowed"] is False
    assert plan["npc_speech_authority"] == "none"
    assert plan["objective_world_fact_authority"] == "none"


@pytest.mark.parametrize("prompt,expected", NEGATIVE_PROMPTS)
def test_pr_dc_negative_controls_are_not_harmless(prompt: str, expected: str) -> None:
    plan = _plan(prompt)
    assert plan["reply_plan_kind"] == expected
    assert plan["reply_plan_kind"] != _HARMLESS
    assert plan["incidental_subjective_allowed"] is False
    assert plan["npc_speech_authority"] == "none"
    assert plan["durable_state_mutation_allowed"] is False


def test_pr_dc_existing_limits_still_outrank_experiential_wording() -> None:
    refusal = _plan("Does the secret rain make it harder to keep watch?")
    assert refusal["reply_plan_kind"] == "genuine_refusal"
    hostile = _plan("Does the rain make it harder to keep watch?", attitude="hostile")
    assert hostile["reply_plan_kind"] == "genuine_refusal"
    consequential = _plan("Does the rain make it harder to prove who committed the murder?")
    assert consequential["reply_plan_kind"] == "consequential_information_request"
    authored = _plan("Does the rain make it harder to keep watch?", topic_revealed=True)
    assert authored["reply_plan_kind"] == "authoritative_answer_available"
    maneuver = _plan("Does the rain make it harder to keep watch?", action_type="persuade")
    assert maneuver["reply_plan_kind"] == "genuine_uncertainty"


def test_pr_dc_three_turn_followups_keep_guard_and_claim_only_plan() -> None:
    session, scene, world = _gate_session_scene()
    turns = [play_turn(session, scene, world, text) for text in (TURN_1, TURN_2, TURN_3)]
    for result in turns:
        social = result["resolution"]["social"]
        assert result["resolver"] == "social"
        assert result["contract_interlocutor"] == "guard_captain"
        assert result["social_npc_id"] == "guard_captain"
        assert result["social_target_resolved"] is True
        assert result["allowed_speaker_ids"] == ["guard_captain"]
        assert result["active_interaction_target_id"] == "guard_captain"
        assert result["discourse_interlocutor"] == "guard_captain"
        assert result["obligation_interlocutor"] == "guard_captain"
        _assert_claim_only_subjective(social)
    assert turns[0]["entry_reason"] == "spoken_vocative_address"
    assert turns[1]["entry_reason"] == "active_interlocutor_followup"
    assert turns[2]["entry_reason"] == "active_interlocutor_followup"


def test_pr_dc_long_shift_fatigue_is_travel_before_the_classifier() -> None:
    session, scene, world = _gate_session_scene()
    _bind_guard(session)
    _focus(session, "guard_captain", "Guard Captain")
    result = play_turn(session, scene, world, "Do long shifts leave you tired?")
    assert result["entry_reason"] == "travel_or_scene_transition_intent"
    assert result["parsed_type"] == "travel"
    assert result["reply_plan_kind"] is None
    assert result["resolver"] is None


def test_pr_dc_named_other_roles_do_not_become_harmless_captain_speech() -> None:
    session, scene, world = _gate_session_scene()
    _bind_guard(session)
    _focus(session, "guard_captain", "Guard Captain")
    baker = play_turn(session, scene, world, "Does the baker find early mornings tiring?")
    session, scene, world = _gate_session_scene()
    _bind_guard(session)
    _focus(session, "guard_captain", "Guard Captain")
    innkeeper = play_turn(session, scene, world, "Does the innkeeper enjoy busy evenings?")
    assert baker["reply_plan_kind"] != _HARMLESS
    assert innkeeper["reply_plan_kind"] == "genuine_uncertainty"
    assert innkeeper["social_npc_id"] == "guard_captain"
    assert innkeeper["allowed_speaker_ids"] == ["guard_captain"]


@pytest.mark.parametrize("player", (TURN_2, TURN_3))
@pytest.mark.parametrize(
    "label,text,expect_valid",
    [
        ("biography", "The guard captain was born in Blackharbor and served for twenty years.", False),
        ("geography", "The old milestone lies east beyond the trading crossroads.", False),
        ("hidden_information", "A secret tunnel runs beneath the gate into the keep.", False),
        ("npc_action", "The captain unlocks the gate and lets you pass.", False),
        ("discovery", "You discover a hidden map beneath the notice board.", False),
        ("certainty", "The captain confirms that bandits murdered the missing patrol.", False),
        ("state_change", "The captain gives you ten gold coins and a signed entry permit.", False),
        ("preference", 'The guard captain says, "I prefer a dry watch."', True),
        ("opinion", 'The guard captain says, "I like the square best after rain."', True),
        ("impression", 'The guard captain says, "The rain does make the watch harder for me."', True),
        ("characterization", "The guard captain shrugs and nods.", True),
    ],
)
def test_pr_dc_followup_projection_does_not_weaken_hard_validation(
    player: str, label: str, text: str, expect_valid: bool, monkeypatch
) -> None:
    import game.gm as gm
    from game.immutable_valid_response import run_preserve_if_valid
    from tests.test_pr_cw_social_context_projection import _REAL_PROJECTOR, social_request

    monkeypatch.setattr(gm, "_project_harmless_social_provider_context", _REAL_PROJECTOR)
    messages, resolution, scene, world, session = social_request(player)
    assert "provider_context_projection" in json.loads(messages[1]["content"])
    candidate = gm._safe_json(
        json.dumps({"narration": text}),
        require_structured_claims=True,
        provider_response_contract="narration_only",
    )
    sealed = run_preserve_if_valid(
        candidate,
        regenerate=None,
        resolution=resolution,
        player_text=player,
        scene=scene,
        world=world,
        session=session,
    )
    audit = sealed["metadata"]["hard_validation_attempt_1"]
    assert audit["hard_valid"] is expect_valid, (player, label, audit)
    if expect_valid:
        assert sealed["player_facing_text"] == text
    else:
        assert sealed["player_facing_text"] != text
        assert "unauthorized_resolution_decision_fact" in audit["reasons"]


def test_pr_dc_rain_followup_uses_existing_reduced_context_predicate(monkeypatch) -> None:
    import game.gm as gm
    from tests.test_pr_cw_social_context_projection import _REAL_PROJECTOR, social_request

    monkeypatch.setattr(gm, "_project_harmless_social_provider_context", _REAL_PROJECTOR)
    messages, resolution, *_rest = social_request(TURN_2)
    social = resolution["social"]
    _assert_claim_only_subjective(social)
    payload = json.loads(messages[1]["content"])
    projection = payload["provider_context_projection"]
    assert projection["selected"] is True
    assert projection["mode"] == "harmless_social_incidental_dialogue_v1"
    mechanical = payload["mechanical_resolution"]["social"]
    assert mechanical["reply_plan_kind"] == _HARMLESS
    assert mechanical["npc_speech_authority"] == "claim_only"
    assert mechanical["objective_world_fact_authority"] == "none"
