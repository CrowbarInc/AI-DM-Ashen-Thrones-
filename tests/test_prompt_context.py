"""Prompt-layer exports for promoted interlocutors (Block 2 profile + hint contracts)."""
from __future__ import annotations

from game.campaign_state import create_fresh_session_document
from game.interaction_context import set_social_target
from game.prompt_context import (
    build_active_interlocutor_export,
    build_social_interlocutor_profile,
    deterministic_interlocutor_answer_style_hints,
)
from game.social import compute_social_target_profile_hints
from game.world import upsert_world_npc


import pytest

pytestmark = pytest.mark.integration

def test_prompt_context_exports_promoted_interlocutor_profile():
    session = create_fresh_session_document()
    session["active_scene_id"] = "frontier_gate"
    session["scene_state"]["active_scene_id"] = "frontier_gate"
    session["scene_state"]["promoted_actor_npc_map"]["crowd_snitch"] = "gate__crowd_snitch"

    world: dict = {"npcs": []}
    upsert_world_npc(
        world,
        {
            "id": "gate__crowd_snitch",
            "name": "Crowd snitch",
            "location": "frontier_gate",
            "role": "informant",
            "affiliation": "ash_cowl",
            "availability": "available",
            "current_agenda": "sell a name",
            "disposition": "neutral",
            "stance_toward_player": "wary",
            "information_reliability": "partial",
            "knowledge_scope": ["scene:frontier_gate", "rumor"],
            "origin_kind": "crowd_actor",
            "origin_scene_id": "frontier_gate",
            "promoted_from_actor_id": "crowd_snitch",
            "topics": [],
        },
    )
    set_social_target(session, "crowd_snitch")

    public_scene = {"id": "frontier_gate"}
    export = build_active_interlocutor_export(session, world, public_scene)
    assert export is not None
    assert export["npc_id"] == "gate__crowd_snitch"
    assert export["raw_interaction_target_id"] == "crowd_snitch"

    profile = build_social_interlocutor_profile(export)
    assert profile["npc_is_promoted"] is True
    assert profile["stance"] == "wary"
    assert profile["reliability"] == "partial"
    assert "scene:frontier_gate" in profile["knowledge_scope"]
    assert profile["agenda"] == "sell a name"
    assert profile["affiliation"] == "ash_cowl"


def test_knowledge_scope_and_reliability_change_social_hints_deterministically():
    sid = "frontier_gate"
    base_export = {
        "npc_id": "n1",
        "stance_toward_player": "neutral",
        "knowledge_scope": ["scene:frontier_gate", "patrol"],
        "origin_kind": "scene_actor",
        "promoted_from_actor_id": "actor_a",
    }
    truthful = {**base_export, "information_reliability": "truthful"}
    partial = {**base_export, "information_reliability": "partial"}
    misleading = {**base_export, "information_reliability": "misleading"}

    ht = compute_social_target_profile_hints(truthful, sid)
    hp = compute_social_target_profile_hints(partial, sid)
    hm = compute_social_target_profile_hints(misleading, sid)
    assert ht["answer_reliability_tier"] == "high"
    assert hp["answer_reliability_tier"] == "medium"
    assert hm["answer_reliability_tier"] == "low"
    assert ht["speaks_authoritatively_for_scene"] is True
    assert hm["guardedness"] == "medium"

    lines_t = deterministic_interlocutor_answer_style_hints(truthful, scene_id=sid)
    lines_p = deterministic_interlocutor_answer_style_hints(partial, scene_id=sid)
    lines_m = deterministic_interlocutor_answer_style_hints(misleading, scene_id=sid)
    assert any("INFORMATION_RELIABILITY truthful" in x for x in lines_t)
    assert any("INFORMATION_RELIABILITY partial" in x for x in lines_p)
    assert any("INFORMATION_RELIABILITY misleading" in x for x in lines_m)
    assert not any("misleading" in x for x in lines_t)
    assert not any("truthful" in x for x in lines_m)
