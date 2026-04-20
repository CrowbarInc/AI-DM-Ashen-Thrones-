from game.final_emission_meta import read_final_emission_meta_dict
"""Social interaction authority coverage for continuity, routing, and downstream emission behavior."""

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
from game.social_exchange_emission import reconcile_strict_social_resolution_speaker


import pytest

pytestmark = pytest.mark.integration

def _minimal_scene():
    # Match default_world NPC locations (frontier_gate) so rebuild_active_scene_entities keeps targets.
    return {"scene": {"id": "frontier_gate", "visible_facts": [], "discoverable_clues": []}}


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
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("strict_social_suppressed_non_social_turn") is True
    # Banned stock phrase is stripped; suppressed non-social turns use global narrative fallback (not NPC-owned).
    assert "from here, no certain answer presents itself" not in text.lower()
    assert "voices shift around you" in text.lower() or "for a breath" in text.lower()


def test_session_ongoing_social_exchange_helper():
    s = default_session()
    assert _session_ongoing_social_exchange(s) is False
    set_social_target(s, "npc_a")
    assert _session_ongoing_social_exchange(s) is True
