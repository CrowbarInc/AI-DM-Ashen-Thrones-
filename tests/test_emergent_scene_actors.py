"""Emergent / narrated figures enrolled into the session addressable roster."""
from __future__ import annotations

from game.campaign_state import create_fresh_session_document
from game.interaction_context import (
    apply_conservative_emergent_enrollment_from_gm_output,
    assert_valid_speaker,
    canonical_scene_addressable_roster,
    clear_emergent_scene_actors_on_scene_change,
    enroll_emergent_scene_actor,
    extract_conservative_emergent_actor_hints,
    find_addressed_npc_id_for_turn,
    rebuild_active_scene_entities,
)

# feature: social, continuity


def _scene(sid: str = "test_gate") -> dict:
    return {"scene": {"id": sid}}


def test_enrolled_watcher_is_addressable_next_turn(monkeypatch):
    world = {"npcs": []}
    monkeypatch.setattr("game.storage.load_world", lambda: world)
    session = create_fresh_session_document()
    session["active_scene_id"] = "test_gate"
    scene = _scene("test_gate")

    hint = {
        "actor_id": "emergent_well_dressed_watcher",
        "display_name": "Well-Dressed Watcher",
        "source": "authored",
        "scene_id": "test_gate",
        "address_roles": ["watcher"],
        "aliases": ["well-dressed watcher", "watcher"],
    }
    assert enroll_emergent_scene_actor(session=session, scene=scene, actor_hint=hint) == "emergent_well_dressed_watcher"
    rebuild_active_scene_entities(session, world, "test_gate", scene_envelope=scene)

    roster = canonical_scene_addressable_roster(world, "test_gate", scene_envelope=scene, session=session)
    ids = {r["id"] for r in roster if isinstance(r, dict)}
    assert "emergent_well_dressed_watcher" in ids

    line = "Well-dressed watcher, what are you watching?"
    assert (
        find_addressed_npc_id_for_turn(line, session, world, scene) == "emergent_well_dressed_watcher"
    )
    assert assert_valid_speaker("emergent_well_dressed_watcher", session, scene_envelope=scene, world=world)


def test_extract_named_noble_hint(monkeypatch):
    world = {"npcs": []}
    monkeypatch.setattr("game.storage.load_world", lambda: world)
    session = create_fresh_session_document()
    scene = _scene("court")
    session["active_scene_id"] = "court"

    narr = "Lord Calder studies you from the balcony, expression unreadable."
    hints = extract_conservative_emergent_actor_hints(
        scene_id="court",
        narration_text=narr,
        visible_fact_strings=[],
    )
    assert hints
    assert any("calder" in str(h.get("actor_id") or "").lower() for h in hints)

    gm = {"player_facing_text": narr}
    apply_conservative_emergent_enrollment_from_gm_output(session=session, scene=scene, narration_text=narr)
    rebuild_active_scene_entities(session, world, "court", scene_envelope=scene)

    line = "Lord Calder, what do you want?"
    tid = find_addressed_npc_id_for_turn(line, session, world, scene)
    assert tid and "calder" in tid.lower()


def test_flavor_crowd_text_produces_no_hints():
    hints = extract_conservative_emergent_actor_hints(
        scene_id="market",
        narration_text="The crowd mutters about grain prices and the heat.",
        visible_fact_strings=[],
    )
    assert hints == []


def test_fresh_session_has_empty_emergent_addressables():
    doc = create_fresh_session_document()
    assert doc["scene_state"].get("emergent_addressables") == []


def test_visible_fact_promotes_watcher_without_watcher_in_narration(monkeypatch):
    world = {"npcs": []}
    monkeypatch.setattr("game.storage.load_world", lambda: world)
    session = create_fresh_session_document()
    session["active_scene_id"] = "g"
    session["scene_state"]["active_scene_id"] = "g"
    scene = {
        "scene": {
            "id": "g",
            "visible_facts": ["You notice a well-dressed watcher by the gate."],
        }
    }
    debug = apply_conservative_emergent_enrollment_from_gm_output(
        session=session,
        scene=scene,
        narration_text="The plaza is busy with merchants.",
    )
    assert debug["emergent_actor_enrolled"] is True
    assert debug["emergent_actor_id"] == "emergent_well_dressed_watcher"


def test_clear_emergent_on_scene_change(monkeypatch):
    world = {"npcs": []}
    monkeypatch.setattr("game.storage.load_world", lambda: world)
    session = create_fresh_session_document()
    scene = _scene("a")
    enroll_emergent_scene_actor(
        session=session,
        scene=scene,
        actor_hint={
            "actor_id": "emergent_x",
            "display_name": "Emergent X",
            "source": "authored",
            "scene_id": "a",
        },
    )
    assert session["scene_state"]["emergent_addressables"]
    clear_emergent_scene_actors_on_scene_change(session)
    assert session["scene_state"]["emergent_addressables"] == []
