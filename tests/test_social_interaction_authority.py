"""Social interaction authority: persistence, reply obligation, suppression, speaker lock."""

from game.api import (
    _resolution_explicitly_breaks_social_continuity,
    _session_ongoing_social_exchange,
    _update_interaction_context_after_action,
)
from game.final_emission_gate import apply_final_emission_gate
from game.defaults import default_session, default_world
from game.interaction_context import (
    inspect as inspect_interaction_context,
    rebuild_active_scene_entities,
    set_social_target,
)
from game.prompt_context import build_narration_context, derive_narration_obligations
from game.social_exchange_emission import reconcile_strict_social_resolution_speaker


def _minimal_scene():
    # Match default_world NPC locations (frontier_gate) so rebuild_active_scene_entities keeps targets.
    return {"scene": {"id": "frontier_gate", "visible_facts": [], "discoverable_clues": []}}


def _dummy_campaign():
    return {"title": "", "premise": "", "character_role": "", "gm_guidance": [], "world_pressures": []}


def _dummy_character():
    return {"name": "Hero", "hp": {}, "ac": {}, "conditions": [], "attacks": [], "spells": {}, "skills": {}}


def test_active_target_persists_after_observe_resolution():
    """Non-social engine resolutions must not clear social continuity while engaged."""
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    set_social_target(session, "tavern_runner")
    ctx_before = inspect_interaction_context(session)

    _update_interaction_context_after_action(
        session,
        {"kind": "observe", "action_id": "wait", "prompt": "I wait."},
        scene_changed=False,
        preserve_continuity=False,
    )
    ctx = inspect_interaction_context(session)
    assert ctx["active_interaction_target_id"] == "tavern_runner"
    assert ctx["interaction_mode"] == "social"
    assert ctx["active_interaction_kind"] == "social"
    assert ctx_before["active_interaction_target_id"] == "tavern_runner"


def test_scene_transition_kind_breaks_social():
    assert _resolution_explicitly_breaks_social_continuity({"kind": "scene_transition"}) is True
    assert _resolution_explicitly_breaks_social_continuity({"kind": "question"}) is False


def test_derive_narration_obligations_reply_expected_locked_in_social():
    session_view = {
        "turn_counter": 5,
        "visited_scene_count": 2,
        "active_interaction_target_id": "rian",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
    }
    obligations = derive_narration_obligations(
        session_view,
        resolution={
            "kind": "question",
            "social": {"npc_reply_expected": False, "npc_id": "rian"},
        },
        intent={"labels": []},
        recent_log_for_prompt=[],
        scene_runtime={"momentum_exchanges_since": 5, "momentum_next_due_in": 2},
    )
    assert obligations["active_npc_reply_expected"] is True
    assert obligations["suppress_non_social_emitters"] is True
    assert obligations["scene_momentum_due"] is False


def test_build_narration_context_suppresses_uncertainty_hint_in_social():
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    session["interaction_context"] = {
        "active_interaction_target_id": "tavern_runner",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "engaged",
        "conversation_privacy": None,
        "player_position_context": None,
    }
    world = default_world()
    scene = _minimal_scene()
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)

    payload = build_narration_context(
        _dummy_campaign(),
        world,
        session,
        _dummy_character(),
        scene,
        {"in_combat": False},
        [],
        "What do you know?",
        {"kind": "question", "social": {"npc_id": "tavern_runner"}},
        {"momentum_exchanges_since": 3, "momentum_next_due_in": 2},
        public_scene=scene["scene"],
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
        uncertainty_hint={"speaker": {"role": "narrator"}, "turn_context": {}},
    )
    assert payload["uncertainty_hint"] is None
    assert payload["response_policy"]["uncertainty"]["enabled"] is False
    assert payload["response_policy"]["prefer_scene_momentum"] is False
    assert any("SOCIAL INTERACTION LOCK" in line for line in payload["instructions"])


def test_reconcile_speaker_locks_to_active_when_not_contradicted_by_vocative():
    world = default_world()
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    session["interaction_context"] = {
        "active_interaction_target_id": "tavern_runner",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "engaged",
        "conversation_privacy": None,
        "player_position_context": None,
    }
    scene = _minimal_scene()
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)

    res = {
        "kind": "question",
        "prompt": "I press the guard about the patrol route.",
        "social": {
            "npc_id": "guard_captain",
            "npc_name": "Guard Captain",
            "social_intent_class": "social_exchange",
        },
    }
    out = reconcile_strict_social_resolution_speaker(res, session, world, "frontier_gate")
    assert out["social"]["npc_id"] == "tavern_runner"


def test_final_gate_emits_social_minimal_not_ambient_scene_when_engaged():
    world = default_world()
    session = default_session()
    session["interaction_context"] = {
        "active_interaction_target_id": "tavern_runner",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "engaged",
        "conversation_privacy": None,
        "player_position_context": None,
    }
    gm = {
        "player_facing_text": "from here, no certain answer presents itself",
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    out = apply_final_emission_gate(
        gm,
        resolution={"kind": "observe", "prompt": "wait"},
        session=session,
        scene_id="frontier_gate",
        world=world,
    )
    text = str(out.get("player_facing_text") or "")
    meta = out.get("_final_emission_meta") or {}
    assert meta.get("strict_social_suppressed_non_social_turn") is True
    # Banned stock phrase is stripped; suppressed non-social turns use global narrative fallback (not NPC-owned).
    assert "from here, no certain answer presents itself" not in text.lower()
    assert "voices shift around you" in text.lower() or "for a breath" in text.lower()


def test_session_ongoing_social_exchange_helper():
    s = default_session()
    assert _session_ongoing_social_exchange(s) is False
    set_social_target(s, "npc_a")
    assert _session_ongoing_social_exchange(s) is True
