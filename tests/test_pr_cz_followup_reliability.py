"""PR-CZ conversational follow-up reliability. Deterministic, no provider calls."""
from __future__ import annotations

import json

import pytest

import game.gm as gm
from game.discourse_state import DISCOURSE_FOCUS_KEY, SLOT_INTERLOCUTOR
from game.immutable_valid_response import run_preserve_if_valid
from game.ordinary_semantic_ownership import select_ordinary_resolver
from game.resolution_contract import construct_resolution_contract
from tests.test_pr_cw_social_context_projection import POSITIVE_CONTROLS, social_request


PR_CY_RETRY = (
    "The guard captain blinks, water dripping from their helmet's brim, and their gaze "
    "flickers briefly to the frayed banners overhead, then back to the crowded queue. "
    "They seem to bear the rain's discomfort with silent endurance, a flicker of misery "
    "perhaps, but no clear sign that it hampers or aids their vigilance."
)


def _focus(npc_id: str, label: str = "Guard Captain", scene_id: str = "frontier_gate") -> dict:
    return {
        "active_scene_id": scene_id,
        DISCOURSE_FOCUS_KEY: {
            "version": 1,
            "scene_id": scene_id,
            SLOT_INTERLOCUTOR: {
                "id": npc_id,
                "label": label,
                "kind": "interlocutor",
                "scene_id": scene_id,
                "source": "resolution_contract",
            },
        },
    }


def _contract_route(text: str, session: dict) -> dict:
    contract = construct_resolution_contract(
        player_text=text,
        session=session,
        scene_id=str(session.get("active_scene_id") or "frontier_gate"),
    ).as_dict()
    resolver, family = select_ordinary_resolver(contract)
    return {"contract": contract, "resolver": resolver, "family": family}


def _seal(text: str, *, player: str = "Does the rain make it harder to keep watch?") -> dict:
    _messages, resolution, scene, world, session = social_request(player)
    candidate = gm._safe_json(
        json.dumps({"narration": text}),
        require_structured_claims=True,
        provider_response_contract="narration_only",
    )
    return run_preserve_if_valid(
        candidate,
        regenerate=None,
        resolution=resolution,
        player_text=player,
        scene=scene,
        world=world,
        session=session,
    )


def test_pr_cz_discourse_focus_recovers_guard_captain_for_followup_question() -> None:
    route = _contract_route(
        "Does the rain make it harder to keep watch?",
        _focus("guard_captain"),
    )
    contract = route["contract"]
    assert route["resolver"] == "social"
    assert contract["operation"] == "ask"
    assert contract["interlocutor_id"] == "guard_captain"
    assert contract["discourse_ref"]["type"] == "interlocutor"


def test_pr_cz_baker_clarification_uses_same_discourse_interlocutor() -> None:
    route = _contract_route("Why?", _focus("baker", label="Baker"))
    assert route["resolver"] == "social"
    assert route["contract"]["interlocutor_id"] == "baker"


def test_pr_cz_explicit_switch_overrides_prior_discourse_interlocutor() -> None:
    route = _contract_route("Tavern Runner, what have you heard?", _focus("guard_captain"))
    contract = route["contract"]
    assert route["resolver"] == "social"
    assert contract["interlocutor_id"] != "guard_captain"


def test_pr_cz_scene_transition_does_not_recover_stale_discourse_interlocutor() -> None:
    session = _focus("guard_captain", scene_id="frontier_gate")
    session["active_scene_id"] = "inner_keep"
    route = _contract_route("Does the rain make it harder to keep watch?", session)
    assert route["contract"].get("interlocutor_id") in (None, "")


def test_pr_cz_replay_retry_candidate_accepts_harmless_qualified_observation() -> None:
    sealed = _seal(PR_CY_RETRY)
    audit = sealed["metadata"]["hard_validation_attempt_1"]
    assert audit["hard_valid"] is True, audit
    assert "unsupported_narrator_lead" not in audit["reasons"]
    assert sealed["player_facing_text"] == PR_CY_RETRY


@pytest.mark.parametrize(
    "text",
    [
        "The guard captain was born in Blackharbor and served for twenty years.",
        "A secret tunnel may run beneath the gate into the keep.",
        "The captain unlocks the gate and lets you pass.",
        "You discover a hidden map beneath the notice board.",
        "The captain confirms that bandits murdered the missing patrol.",
    ],
)
def test_pr_cz_authority_violations_still_reject(text: str) -> None:
    sealed = _seal(text, player=POSITIVE_CONTROLS[0][2])
    audit = sealed["metadata"]["hard_validation_attempt_1"]
    assert audit["hard_valid"] is False, (text, audit)
    assert "unauthorized_resolution_decision_fact" in audit["reasons"]
    assert sealed["player_facing_text"] != text
