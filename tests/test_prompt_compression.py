"""Secondary integration coverage for prompt assembly and compression.

Direct prompt-contract semantics, exported policy bundles, and prompt-facing
helper ownership live in ``tests/test_prompt_context.py``. This module keeps
downstream serialization and compression checks once those contracts are already
owned upstream.
"""
from __future__ import annotations

import importlib
import json

from game.gm import build_messages
from game.storage import get_scene_runtime


import pytest

pytestmark = pytest.mark.integration

_prompt_context = importlib.import_module("game.prompt_context")
MAX_GM_GUIDANCE = _prompt_context.MAX_GM_GUIDANCE
MAX_RECENT_EVENTS = _prompt_context.MAX_RECENT_EVENTS
MAX_RECENT_LOG = _prompt_context.MAX_RECENT_LOG
build_narration_context = _prompt_context.build_narration_context

def _dummy_campaign():
    return {
        "title": "Test Campaign",
        "premise": "A test premise.",
        "character_role": "A test role.",
        "gm_guidance": ["g1", "g2", "g3", "g4", "g5"],
        "world_pressures": ["p1", "p2", "p3", "p4"],
        "magic_style": "Rare and mysterious.",
    }


def _dummy_world():
    return {
        "settlements": [{"id": "s1", "name": "City"}],
        "factions": [{"id": "f1", "name": "Faction A"}, {"id": "f2", "name": "Faction B"}],
        "event_log": [
            {"type": "event", "text": "Event 1"},
            {"type": "event", "text": "Event 2"},
        ],
        "world_state": {"flags": {"flag1": True}, "counters": {"c1": 5}, "clocks": {}},
    }


def _dummy_session():
    return {"active_scene_id": "frontier_gate", "response_mode": "standard", "turn_counter": 10}


def _dummy_character():
    return {"name": "Galinor", "hp": {"current": 8, "max": 8}, "ac": {"normal": 12}}


def _dummy_scene():
    return {
        "scene": {
            "id": "frontier_gate",
            "location": "Gate District",
            "summary": "A crowded gate.",
            "visible_facts": ["Fact 1", "Fact 2"],
            "discoverable_clues": [{"id": "c1", "text": "A discoverable clue."}],
            "hidden_facts": ["A secret motivation."],
            "exits": [],
            "enemies": [],
        }
    }


def _dummy_public_scene():
    return {
        "id": "frontier_gate",
        "location": "Gate District",
        "summary": "A crowded gate.",
        "visible_facts": ["Fact 1", "Fact 2"],
        "exits": [],
        "enemies": [],
    }


def test_compressed_prompt_context_keeps_world_summary_without_full_dump():
    """Compressed context keeps summarized world data instead of a full world dump."""
    ctx = build_narration_context(
        _dummy_campaign(),
        _dummy_world(),
        _dummy_session(),
        _dummy_character(),
        _dummy_scene(),
        {"in_combat": False},
        [],
        "Look around.",
        None,
        {},
        public_scene=_dummy_public_scene(),
        discoverable_clues=[],
        gm_only_hidden_facts=["A secret motivation."],
        gm_only_discoverable_locked=["A discoverable clue."],
        discovered_clue_records=[],
        undiscovered_clue_records=[{"id": "c1", "text": "A discoverable clue."}],
        pending_leads=[],
        intent={"labels": ["general"], "allow_discoverable_clues": False},
        world_state_view={"flags": {"flag1": True}, "counters": {"c1": 5}, "clocks_summary": []},
        mode_instruction="Narration mode: standard.",
        recent_log_for_prompt=[],
    )
    assert "world" in ctx
    world = ctx["world"]
    assert "recent_events" in world
    assert "faction_names" in world
    assert "world_state" in world
    assert world["faction_names"] == ["Faction A", "Faction B"]
    assert world["recent_events"] == ["Event 1", "Event 2"]
    obligations = ctx["narration_obligations"]
    assert obligations["is_opening_scene"] is False
    assert obligations["avoid_input_echo"] is True


def test_compressed_prompt_context_carries_engine_result_and_public_scene_summary():
    """Compressed context carries engine results and public scene summary fields."""
    resolution = {"kind": "observe", "action_id": "observe", "label": "Observe", "prompt": "I look around."}
    ctx = build_narration_context(
        _dummy_campaign(),
        {},
        _dummy_session(),
        _dummy_character(),
        _dummy_scene(),
        {"in_combat": False},
        [],
        "I look around.",
        resolution,
        {},
        public_scene=_dummy_public_scene(),
        discoverable_clues=[],
        gm_only_hidden_facts=[],
        gm_only_discoverable_locked=[],
        discovered_clue_records=[],
        undiscovered_clue_records=[],
        pending_leads=[],
        intent={"labels": ["observation"]},
        world_state_view={"flags": {}, "counters": {}, "clocks_summary": []},
        mode_instruction="Standard.",
        recent_log_for_prompt=[],
    )
    assert ctx["mechanical_resolution"] == resolution
    assert ctx["scene"]["public"]["summary"] == "A crowded gate."
    assert ctx["scene"]["public"]["visible_facts"] == ["Fact 1", "Fact 2"]
    assert ctx["player_input"] == "I look around."


def test_hidden_facts_not_exposed_in_public_section():
    """Hidden facts appear only in gm_only; never in public or discoverable_clues."""
    ctx = build_narration_context(
        _dummy_campaign(),
        {},
        _dummy_session(),
        _dummy_character(),
        _dummy_scene(),
        {"in_combat": False},
        [],
        "Look around.",
        None,
        {},
        public_scene=_dummy_public_scene(),
        discoverable_clues=[],
        gm_only_hidden_facts=["A secret motivation.", "Another secret."],
        gm_only_discoverable_locked=["A discoverable clue."],
        discovered_clue_records=[],
        undiscovered_clue_records=[{"id": "c1", "text": "A discoverable clue."}],
        pending_leads=[],
        intent={"labels": ["general"]},
        world_state_view={"flags": {}, "counters": {}, "clocks_summary": []},
        mode_instruction="Standard.",
        recent_log_for_prompt=[],
    )
    assert "public" in ctx["scene"]
    public_str = json.dumps(ctx["scene"]["public"])
    assert "A secret motivation." not in public_str
    assert "Another secret." not in public_str
    assert ctx["scene"]["gm_only"]["hidden_facts"] == ["A secret motivation.", "Another secret."]


def test_build_messages_produces_compressed_payload():
    """build_messages uses compression; payload has compressed campaign/world/session."""
    campaign = _dummy_campaign()
    world = _dummy_world()
    session = {"active_scene_id": "", "scene_runtime": {}}
    char = _dummy_character()
    combat = {"in_combat": False}
    recent_log = []
    scene = _dummy_scene()
    scene_rt = get_scene_runtime(session, "frontier_gate")
    msgs = build_messages(
        campaign, world, session, char, scene, combat, recent_log,
        "Look around.", None, scene_runtime=scene_rt,
    )
    payload = json.loads(msgs[1]["content"])
    assert len(payload["campaign"]["gm_guidance"]) <= MAX_GM_GUIDANCE
    assert payload["campaign"]["title"] == "Test Campaign"
    assert "world" in payload
    assert "recent_events" in payload["world"] or "world_state" in payload["world"]
    assert "active_scene_id" in payload["session"]
    assert "debug_traces" not in payload["session"]
    assert "chat_history" not in payload["session"]


def test_build_messages_preserves_player_input_text_with_embedded_dialogue():
    """Serialized payload preserves the player's raw wording, including quoted speech."""
    campaign = _dummy_campaign()
    world = _dummy_world()
    session = {"active_scene_id": "", "scene_runtime": {}}
    char = _dummy_character()
    combat = {"in_combat": False}
    scene = _dummy_scene()
    scene_rt = get_scene_runtime(session, "frontier_gate")
    user_text = 'Galinor asks, "Who signed this order?" while examining the notice board.'

    msgs = build_messages(
        campaign,
        world,
        session,
        char,
        scene,
        combat,
        [],
        user_text,
        None,
        scene_runtime=scene_rt,
    )
    payload = json.loads(msgs[1]["content"])
    assert payload["player_input"] == user_text
    assert '"Who signed this order?"' in payload["player_input"]


def test_compressed_prompt_context_handles_missing_optional_data():
    """Compressed context stays shape-safe when optional inputs are missing or empty."""
    ctx = build_narration_context(
        {},
        None,
        None,
        None,
        {},
        None,
        None,
        "",
        None,
        None,
        public_scene={"id": "", "location": "", "summary": "", "visible_facts": [], "exits": [], "enemies": []},
        discoverable_clues=[],
        gm_only_hidden_facts=[],
        gm_only_discoverable_locked=[],
        discovered_clue_records=[],
        undiscovered_clue_records=[],
        pending_leads=[],
        intent={"labels": ["general"]},
        world_state_view={"flags": {}, "counters": {}, "clocks_summary": []},
        mode_instruction="Standard.",
        recent_log_for_prompt=[],
    )
    assert ctx is not None
    assert "campaign" in ctx
    assert "world" in ctx
    assert "session" in ctx
    assert "scene" in ctx
    assert "mechanical_resolution" in ctx
    assert ctx["scene"]["gm_only"]["hidden_facts"] == []


def test_recent_log_trimmed_to_limit():
    """Recent log is limited to MAX_RECENT_LOG entries with trimmed snippets."""
    recent = [
        {
            "log_meta": {"player_input": f"Player said {i}"},
            "gm_output": {"player_facing_text": f"GM response {i} " * 50},
        }
        for i in range(10)
    ]
    ctx = build_narration_context(
        _dummy_campaign(),
        {},
        _dummy_session(),
        _dummy_character(),
        _dummy_scene(),
        {"in_combat": False},
        recent,
        "Test",
        None,
        {},
        public_scene=_dummy_public_scene(),
        discoverable_clues=[],
        gm_only_hidden_facts=[],
        gm_only_discoverable_locked=[],
        discovered_clue_records=[],
        undiscovered_clue_records=[],
        pending_leads=[],
        intent={"labels": ["general"]},
        world_state_view={"flags": {}, "counters": {}, "clocks_summary": []},
        mode_instruction="Standard.",
        recent_log_for_prompt=recent,
    )
    assert len(ctx["recent_log"]) <= MAX_RECENT_LOG
    for entry in ctx["recent_log"]:
        assert "player_input" in entry
        assert "gm_snippet" in entry
        assert len(entry["gm_snippet"]) <= 200


def test_world_events_limited():
    """World recent_events limited to MAX_RECENT_EVENTS."""
    world = {
        "event_log": [{"text": f"Event {i}"} for i in range(20)],
        "factions": [],
        "world_state": {},
    }
    ctx = build_narration_context(
        _dummy_campaign(),
        world,
        _dummy_session(),
        _dummy_character(),
        _dummy_scene(),
        {"in_combat": False},
        [],
        "Test",
        None,
        {},
        public_scene=_dummy_public_scene(),
        discoverable_clues=[],
        gm_only_hidden_facts=[],
        gm_only_discoverable_locked=[],
        discovered_clue_records=[],
        undiscovered_clue_records=[],
        pending_leads=[],
        intent={"labels": ["general"]},
        world_state_view={"flags": {}, "counters": {}, "clocks_summary": []},
        mode_instruction="Standard.",
        recent_log_for_prompt=[],
    )
    assert len(ctx["world"]["recent_events"]) <= MAX_RECENT_EVENTS


def test_compressed_prompt_context_carries_opening_scene_obligation():
    session = {
        "active_scene_id": "frontier_gate",
        "response_mode": "standard",
        "turn_counter": 0,
        "visited_scene_ids": [],
    }
    ctx = build_narration_context(
        _dummy_campaign(),
        _dummy_world(),
        session,
        _dummy_character(),
        _dummy_scene(),
        {"in_combat": False},
        [],
        "Galinor steps through the gate.",
        None,
        {},
        public_scene=_dummy_public_scene(),
        discoverable_clues=[],
        gm_only_hidden_facts=[],
        gm_only_discoverable_locked=[],
        discovered_clue_records=[],
        undiscovered_clue_records=[],
        pending_leads=[],
        intent={"labels": ["general"]},
        world_state_view={"flags": {}, "counters": {}, "clocks_summary": []},
        mode_instruction="Standard.",
        recent_log_for_prompt=[],
    )
    obligations = ctx["narration_obligations"]
    assert obligations["is_opening_scene"] is True
    assert obligations["must_advance_scene"] is False


def test_compressed_prompt_context_carries_arrival_bridge_guidance():
    resolution = {
        "kind": "scene_transition",
        "action_id": "go-market",
        "label": "Go: Market",
        "prompt": "Galinor heads to the market.",
        "resolved_transition": True,
        "target_scene_id": "market_quarter",
    }
    ctx = build_narration_context(
        _dummy_campaign(),
        _dummy_world(),
        _dummy_session(),
        _dummy_character(),
        _dummy_scene(),
        {"in_combat": False},
        [],
        "Galinor heads to the market.",
        resolution,
        {},
        public_scene=_dummy_public_scene(),
        discoverable_clues=[],
        gm_only_hidden_facts=[],
        gm_only_discoverable_locked=[],
        discovered_clue_records=[],
        undiscovered_clue_records=[],
        pending_leads=[],
        intent={"labels": ["travel"]},
        world_state_view={"flags": {}, "counters": {}, "clocks_summary": []},
        mode_instruction="Standard.",
        recent_log_for_prompt=[],
    )
    obligations = ctx["narration_obligations"]
    assert obligations["must_advance_scene"] is True
    instructions = " ".join(ctx.get("instructions", [])).lower()
    assert "must_advance_scene" in instructions
    assert "arrival" in instructions
    assert "brief bridge from the prior location" in instructions


def test_compressed_prompt_context_only_adds_transition_bridge_when_scene_changes():
    no_transition_ctx = build_narration_context(
        _dummy_campaign(),
        _dummy_world(),
        _dummy_session(),
        _dummy_character(),
        _dummy_scene(),
        {"in_combat": False},
        [],
        "Galinor checks the notice board.",
        None,
        {},
        public_scene=_dummy_public_scene(),
        discoverable_clues=[],
        gm_only_hidden_facts=[],
        gm_only_discoverable_locked=[],
        discovered_clue_records=[],
        undiscovered_clue_records=[],
        pending_leads=[],
        intent={"labels": ["general"]},
        world_state_view={"flags": {}, "counters": {}, "clocks_summary": []},
        mode_instruction="Standard.",
        recent_log_for_prompt=[],
    )
    no_transition_instructions = " ".join(no_transition_ctx.get("instructions", [])).lower()
    assert "brief bridge from the prior location" not in no_transition_instructions

    transition_resolution = {
        "kind": "scene_transition",
        "action_id": "go-crossroads",
        "label": "Go to the crossroads",
        "prompt": "Galinor heads to the crossroads.",
        "resolved_transition": True,
        "target_scene_id": "crossroads",
    }
    transition_ctx = build_narration_context(
        _dummy_campaign(),
        _dummy_world(),
        _dummy_session(),
        _dummy_character(),
        _dummy_scene(),
        {"in_combat": False},
        [],
        "Galinor heads to the crossroads.",
        transition_resolution,
        {},
        public_scene=_dummy_public_scene(),
        discoverable_clues=[],
        gm_only_hidden_facts=[],
        gm_only_discoverable_locked=[],
        discovered_clue_records=[],
        undiscovered_clue_records=[],
        pending_leads=[],
        intent={"labels": ["travel"]},
        world_state_view={"flags": {}, "counters": {}, "clocks_summary": []},
        mode_instruction="Standard.",
        recent_log_for_prompt=[],
    )
    transition_instructions = " ".join(transition_ctx.get("instructions", [])).lower()
    assert "brief bridge from the prior location" in transition_instructions


def test_compressed_prompt_context_carries_active_npc_reply_flags():
    session = {
        "active_scene_id": "frontier_gate",
        "response_mode": "standard",
        "turn_counter": 4,
        "interaction_context": {
            "active_interaction_target_id": "guard_captain",
            "active_interaction_kind": "social",
            "interaction_mode": "social",
        },
    }
    resolution = {
        "kind": "question",
        "action_id": "ask-guard",
        "label": "Question the guard",
        "prompt": 'Galinor asks, "Who signed this order?"',
        "social": {"target_id": "guard_captain"},
        "requires_check": False,
    }
    ctx = build_narration_context(
        _dummy_campaign(),
        _dummy_world(),
        session,
        _dummy_character(),
        _dummy_scene(),
        {"in_combat": False},
        [],
        'Galinor asks, "Who signed this order?"',
        resolution,
        {},
        public_scene=_dummy_public_scene(),
        discoverable_clues=[],
        gm_only_hidden_facts=[],
        gm_only_discoverable_locked=[],
        discovered_clue_records=[],
        undiscovered_clue_records=[],
        pending_leads=[],
        intent={"labels": ["social_probe"]},
        world_state_view={"flags": {}, "counters": {}, "clocks_summary": []},
        mode_instruction="Standard.",
        recent_log_for_prompt=[],
    )
    obligations = ctx["narration_obligations"]
    assert obligations["should_answer_active_npc"] is True
    assert obligations["active_npc_reply_expected"] is True


def test_compressed_prompt_context_preserves_explicit_social_reply_signal():
    session = {
        "active_scene_id": "frontier_gate",
        "response_mode": "standard",
        "turn_counter": 6,
        "interaction_context": {
            "active_interaction_target_id": "guard_captain",
            "active_interaction_kind": "social",
            "interaction_mode": "social",
        },
    }
    resolution = {
        "kind": "question",
        "action_id": "ask-guard",
        "label": "Question the guard",
        "prompt": "I'm listening. Continue.",
        "social": {
            "npc_id": "guard_captain",
            "npc_reply_expected": True,
            "reply_kind": "explanation",
        },
        "requires_check": False,
    }
    ctx = build_narration_context(
        _dummy_campaign(),
        _dummy_world(),
        session,
        _dummy_character(),
        _dummy_scene(),
        {"in_combat": False},
        [],
        "I'm listening. Continue.",
        resolution,
        {},
        public_scene=_dummy_public_scene(),
        discoverable_clues=[],
        gm_only_hidden_facts=[],
        gm_only_discoverable_locked=[],
        discovered_clue_records=[],
        undiscovered_clue_records=[],
        pending_leads=[],
        intent={"labels": ["social_probe"]},
        world_state_view={"flags": {}, "counters": {}, "clocks_summary": []},
        mode_instruction="Standard.",
        recent_log_for_prompt=[],
    )
    obligations = ctx["narration_obligations"]
    assert obligations["active_npc_reply_expected"] is True
    assert obligations["active_npc_reply_kind"] == "explanation"


def test_compressed_prompt_context_carries_refusal_guidance_without_stalling():
    session = {
        "active_scene_id": "frontier_gate",
        "response_mode": "standard",
        "turn_counter": 7,
        "interaction_context": {
            "active_interaction_target_id": "guard_captain",
            "active_interaction_kind": "social",
            "interaction_mode": "social",
        },
    }
    resolution = {
        "kind": "question",
        "action_id": "ask-guard",
        "label": "Question the guard",
        "prompt": 'Galinor asks, "Where are they headed?"',
        "social": {
            "npc_id": "guard_captain",
            "npc_reply_expected": True,
            "reply_kind": "refusal",
        },
        "requires_check": False,
    }
    ctx = build_narration_context(
        _dummy_campaign(),
        _dummy_world(),
        session,
        _dummy_character(),
        _dummy_scene(),
        {"in_combat": False},
        [],
        'Galinor asks, "Where are they headed?"',
        resolution,
        {},
        public_scene=_dummy_public_scene(),
        discoverable_clues=[],
        gm_only_hidden_facts=[],
        gm_only_discoverable_locked=[],
        discovered_clue_records=[],
        undiscovered_clue_records=[],
        pending_leads=[],
        intent={"labels": ["social_probe"]},
        world_state_view={"flags": {}, "counters": {}, "clocks_summary": []},
        mode_instruction="Standard.",
        recent_log_for_prompt=[],
    )
    obligations = ctx["narration_obligations"]
    instructions = " ".join(ctx.get("instructions", [])).lower()
    assert obligations["active_npc_reply_kind"] == "refusal"
    assert "rather than empty stalling" in instructions


def test_build_messages_serializes_turn_summary_without_rewriting_player_input():
    resolution = {
        "kind": "question",
        "action_id": "ask-guard",
        "label": "Question the guard",
        "prompt": 'Galinor asks, "Who signed this order?"',
        "social": {"target_id": "guard_captain"},
        "requires_check": False,
    }
    user_text = 'Galinor asks, "Who signed this order?" while examining the notice board.'
    scene_rt = get_scene_runtime({"active_scene_id": "", "scene_runtime": {}}, "frontier_gate")
    msgs = build_messages(
        _dummy_campaign(),
        _dummy_world(),
        {"active_scene_id": "", "scene_runtime": {}},
        _dummy_character(),
        _dummy_scene(),
        {"in_combat": False},
        [],
        user_text,
        resolution,
        scene_runtime=scene_rt,
    )
    payload = json.loads(msgs[1]["content"])
    turn_summary = payload["turn_summary"]

    assert turn_summary["action_descriptor"] == "Question the guard"
    assert turn_summary["resolution_kind"] == "question"
    assert turn_summary["raw_player_input"] == user_text
    assert payload["player_input"] == user_text
