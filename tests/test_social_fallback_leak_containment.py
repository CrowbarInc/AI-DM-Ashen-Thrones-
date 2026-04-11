"""Regression: social/bounded-partial fallback must not leak engine-shaped imperatives or recycle identical leads."""
from __future__ import annotations

import pytest

from game.campaign_state import create_fresh_session_document
from game.final_emission_repairs import (
    _append_next_lead_if_allowed,
    _fallback_lead_tail_should_block,
    _record_fallback_lead_tail,
    _synthesize_next_lead_phrase,
    _apply_social_fallback_leak_guard,
)
from game.interaction_context import rebuild_active_scene_entities
from game.social_exchange_emission import apply_social_exchange_retry_fallback_gm
from game.storage import load_scene

pytestmark = pytest.mark.unit


def _minimal_contract_require_lead() -> dict:
    return {
        "enabled": True,
        "uncertainty_active": True,
        "uncertainty_sources": ["unknown_feasibility"],
        "uncertainty_mode": "procedural_insufficiency",
        "allowed_behaviors": {
            "ask_clarifying_question": False,
            "hedge_appropriately": True,
            "provide_partial_information": True,
        },
        "disallowed_behaviors": {},
        "diegetic_only": True,
        "max_clarifying_questions": 0,
        "prefer_partial_over_question": True,
        "require_partial_to_state_known_edge": False,
        "require_partial_to_state_unknown_edge": True,
        "require_partial_to_offer_next_lead": True,
        "allowed_hedge_forms": ["Hard to tell, but"],
        "forbidden_hedge_forms": [],
        "allowed_authority_bases": ["rumor_marked_as_rumor"],
        "forbidden_authority_bases": [],
    }


def test_synthesize_next_lead_is_diegetic_not_bare_imperative() -> None:
    ctr = _minimal_contract_require_lead()
    resolution = {
        "kind": "question",
        "prompt": "Can I bribe the watch here?",
        "social": {"npc_id": "tavern_runner", "npc_name": "Tavern Runner"},
    }
    out = _synthesize_next_lead_phrase(ctr, resolution, "Can I bribe the watch here?", variant=0)
    low = out.lower()
    assert not low.startswith("press ")
    assert not low.startswith("ask ")
    assert not low.startswith("check ")
    assert '"' in out
    assert "tavern runner" in low or "says" in low or "mutter" in low


def test_fallback_lead_tail_blocks_after_two_identical_emissions() -> None:
    session: dict = {}
    resolution = {
        "kind": "question",
        "prompt": "Who was the buyer?",
        "social": {"npc_id": "tavern_runner", "npc_name": "Tavern Runner"},
    }
    ctr = _minimal_contract_require_lead()
    lead = _synthesize_next_lead_phrase(ctr, resolution, "Who was the buyer?", variant=0)
    assert lead
    _record_fallback_lead_tail(session, "frontier_gate", resolution, lead)
    assert not _fallback_lead_tail_should_block(session, "frontier_gate", resolution, lead)
    _record_fallback_lead_tail(session, "frontier_gate", resolution, lead)
    assert _fallback_lead_tail_should_block(session, "frontier_gate", resolution, lead)


def test_append_next_lead_rotates_variant_when_same_lead_repeated_in_session() -> None:
    """After two identical synthesized leads for the same anchor, the next append must not recycle variant 0."""
    session: dict = {}
    resolution = {
        "kind": "question",
        "prompt": "same topic",
        "social": {"npc_id": "tavern_runner", "npc_name": "Tavern Runner"},
    }
    ctr = _minimal_contract_require_lead()
    base = "No one commits themselves at once."
    lead_v0 = _synthesize_next_lead_phrase(ctr, resolution, "same topic", variant=0)
    _record_fallback_lead_tail(session, "frontier_gate", resolution, lead_v0)
    _record_fallback_lead_tail(session, "frontier_gate", resolution, lead_v0)
    text, patch = _append_next_lead_if_allowed(
        base,
        contract=ctr,
        source_text="",
        resolution=resolution,
        session=session,
        scene_id="frontier_gate",
    )
    assert lead_v0 not in text
    assert "patrol sergeant" in text.lower()
    assert patch.get("fallback_behavior_next_lead_added") is True


def test_social_fallback_leak_guard_wraps_bare_press_line() -> None:
    resolution = {
        "kind": "question",
        "prompt": "x",
        "social": {"npc_id": "tavern_runner", "npc_name": "Tavern Runner"},
    }
    raw = 'Tavern Runner shrugs. Press the patrol sergeant for what the watch will actually allow on the street.'
    out = _apply_social_fallback_leak_guard(raw, resolution)
    assert 'Press the patrol sergeant' in out
    assert 'someone nearby says' in out.lower() or 'tavern runner says' in out.lower()


def test_apply_social_exchange_retry_fallback_gm_standard_mode_adds_payload() -> None:
    session = create_fresh_session_document()
    session["active_scene_id"] = "frontier_gate"
    session["scene_state"]["active_scene_id"] = "frontier_gate"
    session["response_mode"] = "standard"
    st = session["scene_state"]
    st["active_entities"] = ["tavern_runner"]
    st.setdefault("entity_presence", {})
    st["entity_presence"].update({e: "active" for e in st["active_entities"]})
    world = {
        "npcs": [
            {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate"},
        ]
    }
    scene = load_scene("frontier_gate")
    scene["scene_state"] = dict(st)
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)
    resolution = {
        "kind": "question",
        "prompt": "What do you know?",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "tavern_runner",
            "npc_name": "Tavern Runner",
            "target_resolved": True,
        },
    }
    gm = {"player_facing_text": "", "tags": []}
    out = apply_social_exchange_retry_fallback_gm(
        gm,
        player_text="What do you know?",
        session=session,
        world=world,
        resolution=resolution,
        scene_id="frontier_gate",
    )
    txt = str(out.get("player_facing_text") or "")
    assert len(txt.split()) >= 18
    assert '"' in txt


def test_deterministic_retry_fallback_social_line_has_no_engine_press_phrase() -> None:
    """Simulates retry exhaustion after model failure: output must not include legacy hard-coded press line."""
    from game.gm import apply_deterministic_retry_fallback

    session = create_fresh_session_document()
    session["active_scene_id"] = "frontier_gate"
    session["scene_state"]["active_scene_id"] = "frontier_gate"
    st = session["scene_state"]
    st["active_entities"] = ["tavern_runner"]
    st.setdefault("entity_presence", {})
    st["entity_presence"].update({e: "active" for e in st["active_entities"]})
    world = {
        "npcs": [
            {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate"},
        ]
    }
    scene = load_scene("frontier_gate")
    scene["scene_state"] = dict(st)
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)
    session["interaction_context"] = {
        "active_interaction_target_id": "tavern_runner",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "focused",
    }
    resolution = {
        "kind": "question",
        "prompt": "What can I get for three silver?",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "tavern_runner",
            "npc_name": "Tavern Runner",
            "target_resolved": True,
        },
    }
    gm = {"player_facing_text": "", "tags": []}
    failure = {"failure_class": "unresolved_question", "reasons": ["quota"]}
    out = apply_deterministic_retry_fallback(
        gm,
        failure=failure,
        player_text="What can I get for three silver?",
        scene_envelope={"scene": {"id": "frontier_gate"}},
        session=session,
        world=world,
        resolution=resolution,
    )
    low = str(out.get("player_facing_text") or "").lower()
    assert "press the patrol sergeant for what the watch will actually allow" not in low
