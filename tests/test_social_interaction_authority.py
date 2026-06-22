from tests.helpers.replay_fem_read_smoke import final_emission_meta_from_output
"""Social interaction authority coverage for continuity, routing, and downstream emission behavior."""

from game.api import (
    _resolution_explicitly_breaks_social_continuity,
    _session_ongoing_social_exchange,
    _update_interaction_context_after_action,
)
from game.final_emission_runtime import finalize_player_facing_emission as apply_final_emission_gate
from game.defaults import default_session, default_world
from game.interaction_context import (
    inspect as inspect_interaction_context,
    rebuild_active_scene_entities,
    set_social_target,
)
from game.social_exchange_policy import reconcile_strict_social_resolution_speaker


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


def test_reconcile_preserves_ambiguous_generic_guard_without_promotion():
    """BX4: bare ``guard`` with multiple roster guard rows must not promote to guard_captain."""
    from game.interaction_context import rebuild_active_scene_entities, resolve_authoritative_social_target
    from game.storage import load_scene
    from copy import deepcopy

    world = {"npcs": []}
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    session["interaction_context"] = {}
    scene = load_scene("frontier_gate")
    st = dict(session["scene_state"])
    st["active_scene_id"] = "frontier_gate"
    st["active_entities"] = ["guard_captain", "tavern_runner", "refugee", "threadbare_watcher", "gate_sentry"]
    st["entity_presence"] = {eid: "active" for eid in st["active_entities"]}
    gate_sentry = {
        "id": "gate_sentry",
        "name": "Gate Sentry",
        "scene_id": "frontier_gate",
        "kind": "scene_actor",
        "addressable": True,
        "address_priority": 0,
        "address_roles": ["guard", "sentry"],
        "aliases": [],
    }
    sc = deepcopy(scene.get("scene") or {})
    addr = list(sc.get("addressables") or [])
    addr.append(gate_sentry)
    sc["addressables"] = addr
    st["emergent_addressables"] = [gate_sentry]
    scene = {"scene": sc, "scene_state": dict(st)}
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)
    st_live = session.setdefault("scene_state", {})
    if isinstance(st_live, dict):
        st_live["emergent_addressables"] = [gate_sentry]

    player_text = "Tell me guard, who posted that notice?"
    auth = resolve_authoritative_social_target(
        session,
        world,
        "frontier_gate",
        player_text=player_text,
        merged_player_prompt=player_text,
        scene_envelope=scene,
        allow_first_roster_fallback=False,
    )
    assert auth.get("target_resolved") is False

    res = {
        "kind": "question",
        "prompt": player_text,
        "social": {"social_intent_class": "social_exchange"},
    }
    out = reconcile_strict_social_resolution_speaker(res, session, world, "frontier_gate")
    assert out.get("social", {}).get("npc_id") in (None, "")
    em = out.get("metadata", {}).get("emission_debug", {})
    assert "speaker_selection_contract" not in em


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
    meta = final_emission_meta_from_output(out)
    assert meta.get("strict_social_suppressed_non_social_turn") is True
    # Banned stock phrase is stripped; suppressed non-social turns use global narrative fallback (not NPC-owned).
    assert "from here, no certain answer presents itself" not in text.lower()
    assert "voices shift around you" in text.lower() or "for a breath" in text.lower()


def test_session_ongoing_social_exchange_helper():
    s = default_session()
    assert _session_ongoing_social_exchange(s) is False
    set_social_target(s, "npc_a")
    assert _session_ongoing_social_exchange(s) is True
