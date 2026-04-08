from __future__ import annotations

import pytest

from game.response_type_gating import derive_response_type_contract


pytestmark = pytest.mark.unit


def _social_context() -> dict:
    return {
        "active_interaction_target_id": "runner",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "engaged",
    }


def test_dialogue_lock_question_requires_dialogue_contract() -> None:
    contract = derive_response_type_contract(
        segmented_turn={"spoken_text": "Who attacked them?"},
        normalized_action={
            "type": "question",
            "target_id": "runner",
            "targetEntityId": "runner",
        },
        resolution={
            "kind": "question",
            "prompt": "Who attacked them?",
            "requires_check": False,
            "social": {
                "social_intent_class": "social_exchange",
                "npc_id": "runner",
                "target_resolved": True,
            },
        },
        interaction_context=_social_context(),
        route_choice="dialogue",
        directed_social_entry={"should_route_social": True, "target_actor_id": "runner"},
        raw_player_text="Who attacked them?",
    ).to_dict()

    assert contract["required_response_type"] == "dialogue"
    assert contract["source_route"] == "social"
    assert contract["strict_target_id"] == "runner"
    assert contract["strict_dialogue_expected"] is True
    assert contract["strict_answer_expected"] is True
    assert contract["allow_escalation"] is False


def test_adjudication_question_requires_answer_contract() -> None:
    contract = derive_response_type_contract(
        segmented_turn={"adjudication_question_text": "Is Sleight of Hand needed?"},
        normalized_action=None,
        resolution={
            "kind": "adjudication_query",
            "prompt": "Is Sleight of Hand needed?",
            "adjudication": {
                "category": "roll_requirement_query",
                "answer_type": "check_required",
            },
            "requires_check": True,
        },
        interaction_context={"interaction_mode": "none"},
        route_choice=None,
        directed_social_entry=None,
        raw_player_text="Is Sleight of Hand needed?",
    ).to_dict()

    assert contract["required_response_type"] == "answer"
    assert contract["source_route"] == "adjudication"
    assert contract["strict_answer_expected"] is True
    assert contract["allow_escalation"] is False


def test_open_social_solicitation_skips_social_question_guard() -> None:
    contract = derive_response_type_contract(
        segmented_turn=None,
        normalized_action={"type": "question"},
        resolution={
            "kind": "question",
            "prompt": "Anyone up for a chat?",
            "requires_check": False,
            "social": {
                "social_intent_class": "social_exchange",
                "npc_id": None,
                "target_resolved": False,
                "open_social_solicitation": True,
                "npc_reply_expected": False,
                "reply_kind": "reaction",
            },
        },
        interaction_context={"interaction_mode": "none"},
        route_choice="dialogue",
        directed_social_entry={
            "should_route_social": True,
            "target_actor_id": None,
            "reason": "open_social_solicitation",
        },
        raw_player_text="Anyone up for a chat?",
    ).to_dict()

    assert "social_question_guard" not in contract["debug_reasons"]
    assert contract["allow_escalation"] is True


def test_world_action_requires_action_outcome_and_preserves_agency() -> None:
    contract = derive_response_type_contract(
        segmented_turn=None,
        normalized_action={"type": "investigate"},
        resolution={
            "kind": "investigate",
            "prompt": "I investigate the desk.",
            "requires_check": False,
        },
        interaction_context={"interaction_mode": "activity"},
        route_choice="action",
        directed_social_entry=None,
        raw_player_text="I investigate the desk.",
    ).to_dict()

    assert contract["required_response_type"] == "action_outcome"
    assert contract["source_route"] == "exploration"
    assert contract["action_must_preserve_agency"] is True
    assert contract["allow_escalation"] is False


def test_action_route_without_resolution_still_requires_action_outcome() -> None:
    contract = derive_response_type_contract(
        segmented_turn=None,
        normalized_action=None,
        resolution=None,
        interaction_context={"interaction_mode": "none"},
        route_choice="action",
        directed_social_entry=None,
        raw_player_text="I travel to the checkpoint.",
    ).to_dict()

    assert contract["required_response_type"] == "action_outcome"
    assert contract["source_route"] == "exploration"
    assert contract["action_must_preserve_agency"] is True
    assert contract["allow_escalation"] is False
