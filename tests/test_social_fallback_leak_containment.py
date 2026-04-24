"""Regression: social/bounded-partial fallback must not leak engine-shaped imperatives.

Template synthesis and bare-imperative wrapping previously lived in ``game.final_emission_repairs``;
those helpers were retired from final emission (see ``docs/final_emission_debt_retirement.md``).
Diegetic lead rotation and synthesis are owned upstream; this module keeps orchestration tests only.
"""
from __future__ import annotations

import pytest

from game.campaign_state import create_fresh_session_document
from game.final_emission_repairs import repair_fallback_behavior
from game.final_emission_validators import validate_fallback_behavior
from game.interaction_context import rebuild_active_scene_entities
from game.social_exchange_emission import apply_social_exchange_retry_fallback_gm
from game.storage import load_scene

pytestmark = pytest.mark.unit


def test_final_emission_repairs_no_longer_exports_synthesis_helpers() -> None:
    import game.final_emission_repairs as fer

    for name in (
        "_synthesize_next_lead_phrase",
        "_append_next_lead_if_allowed",
        "_apply_social_fallback_leak_guard",
    ):
        assert not hasattr(fer, name), f"expected {name} removed from boundary module"


def test_repair_fallback_behavior_strip_only_does_not_append_synthesized_next_lead() -> None:
    ctr = {
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
    base = "No one commits themselves at once."
    v0 = validate_fallback_behavior(base, ctr, resolution=None)
    out, meta, _ = repair_fallback_behavior(base, ctr, v0, resolution=None, session={}, scene_id="s")
    assert out == base
    assert meta.get("fallback_behavior_next_lead_added") is False
    assert meta.get("final_emission_boundary_semantic_repair_disabled") is True


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
