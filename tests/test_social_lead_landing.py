"""Structured persistence for socially revealed leads (apply_socially_revealed_leads)."""
from __future__ import annotations

from game.clues import apply_socially_revealed_leads, get_all_known_clue_ids, get_clue_presentation
from game.defaults import default_character, default_world
from game.social import resolve_social_action
from game.storage import get_scene_runtime


def _resolution_question_with_topic(*, clue_id: str | None, text: str, leads_to_scene: str | None = None) -> dict:
    topic: dict = {"id": "t1", "text": text}
    if clue_id:
        topic["clue_id"] = clue_id
    if leads_to_scene:
        topic["leads_to_scene"] = leads_to_scene
    return {
        "kind": "question",
        "action_id": "q",
        "label": "Ask",
        "prompt": "Ask",
        "success": True,
        "resolved_transition": False,
        "target_scene_id": None,
        "clue_id": clue_id,
        "discovered_clues": [text],
        "world_updates": None,
        "state_changes": {"topic_revealed": True},
        "hint": "h",
        "social": {
            "npc_id": "runner",
            "npc_name": "Runner",
            "target_resolved": True,
            "topic_revealed": topic,
        },
        "requires_check": False,
    }


def test_social_lead_lands_discovered_clue_id_and_event():
    session: dict = {}
    world = default_world()
    world.setdefault("event_log", [])
    scene_id = "gate"
    res = _resolution_question_with_topic(clue_id="east_lanes", text="East road is dangerous.", leads_to_scene=None)

    added = apply_socially_revealed_leads(session, scene_id, world, res)

    assert "east_lanes" in added or "East road is dangerous." in added
    assert "east_lanes" in get_all_known_clue_ids(session)
    rt = get_scene_runtime(session, scene_id)
    assert "east_lanes" in (rt.get("discovered_clue_ids") or [])
    assert any(
        isinstance(e, dict) and e.get("type") == "social_lead_revealed" and e.get("clue_id") == "east_lanes"
        for e in world.get("event_log") or []
    )
    meta = res.get("metadata") if isinstance(res.get("metadata"), dict) else {}
    ll = meta.get("lead_landing") if isinstance(meta.get("lead_landing"), dict) else {}
    assert "east_lanes" in (ll.get("revealed_lead_ids") or [])
    assert "event_log" in (ll.get("lead_write_targets") or [])


def test_social_lead_idempotent_no_duplicate_event():
    session: dict = {}
    world = default_world()
    world.setdefault("event_log", [])
    scene_id = "gate"
    res = _resolution_question_with_topic(clue_id="dup_clue", text="Same story.")

    apply_socially_revealed_leads(session, scene_id, world, res)
    apply_socially_revealed_leads(session, scene_id, world, res)

    events = [e for e in world.get("event_log") or [] if isinstance(e, dict) and e.get("type") == "social_lead_revealed" and e.get("clue_id") == "dup_clue"]
    assert len(events) == 1
    meta = res.get("metadata") if isinstance(res.get("metadata"), dict) else {}
    ll = meta.get("lead_landing") if isinstance(meta.get("lead_landing"), dict) else {}
    assert "dup_clue" in (ll.get("already_known_lead_ids") or [])


def test_social_topic_without_clue_id_gets_stable_synthetic_id():
    session: dict = {}
    world = default_world()
    world.setdefault("event_log", [])
    scene_id = "gate"
    res = _resolution_question_with_topic(clue_id=None, text="Rumor at the crossroads.")
    res["clue_id"] = None
    res["discovered_clues"] = ["Rumor at the crossroads."]

    apply_socially_revealed_leads(session, scene_id, world, res)

    syn = "social_gate_runner_t1"
    assert syn in get_all_known_clue_ids(session)
    assert syn in (get_scene_runtime(session, scene_id).get("discovered_clue_ids") or [])


def test_social_lead_with_leads_to_scene_adds_pending_and_actionable():
    session: dict = {}
    world = default_world()
    world.setdefault("event_log", [])
    scene_id = "gate"
    res = _resolution_question_with_topic(
        clue_id="to_milestone",
        text="They were seen toward the old milestone.",
        leads_to_scene="old_milestone",
    )

    apply_socially_revealed_leads(session, scene_id, world, res)

    rt = get_scene_runtime(session, scene_id)
    pending = rt.get("pending_leads") or []
    assert any(isinstance(p, dict) and p.get("clue_id") == "to_milestone" for p in pending)
    assert get_clue_presentation(session, clue_id="to_milestone") == "actionable"
    meta = res.get("metadata") if isinstance(res.get("metadata"), dict) else {}
    ll = meta.get("lead_landing") if isinstance(meta.get("lead_landing"), dict) else {}
    assert "to_milestone" in (ll.get("actionable_lead_ids") or [])


def test_resolve_social_plus_apply_persists_like_pipeline():
    world = default_world()
    world["npcs"] = [
        {
            "id": "runner",
            "name": "Tavern Runner",
            "location": "gate",
            "topics": [{"id": "patrol", "text": "Patrol vanished east.", "clue_id": "patrol_vanish"}],
        }
    ]
    scene = {"scene": {"id": "gate"}}
    session: dict = {}
    action = {
        "id": "question-runner",
        "type": "question",
        "label": "Ask",
        "prompt": "Ask the runner.",
        "target_id": "runner",
    }
    resolution = resolve_social_action(
        scene, session, world, action, character=default_character(), turn_counter=1
    )
    apply_socially_revealed_leads(session, "gate", world, resolution)

    assert "patrol_vanish" in get_all_known_clue_ids(session)
    assert "patrol_vanish" in (get_scene_runtime(session, "gate").get("discovered_clue_ids") or [])
