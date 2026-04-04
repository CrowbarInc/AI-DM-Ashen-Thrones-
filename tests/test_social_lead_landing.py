"""Structured persistence for socially revealed leads (apply_socially_revealed_leads)."""
from __future__ import annotations

from game.clues import (
    apply_social_narration_lead_supplements,
    apply_socially_revealed_leads,
    ensure_scene_has_minimum_actionable_lead,
    extract_actionable_social_leads,
    get_all_known_clue_ids,
    get_clue_presentation,
    record_discovered_clue,
)
from game.leads import SESSION_LEAD_REGISTRY_KEY, ensure_lead_registry, get_lead
from game.defaults import default_character, default_world
from game.social import (
    apply_social_lead_discussion_tracking,
    get_npc_lead_discussion,
    resolve_social_action,
)
from game.storage import add_pending_lead, get_scene_runtime, load_scene


import pytest

pytestmark = pytest.mark.integration

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
    p = next(p for p in pending if isinstance(p, dict) and p.get("clue_id") == "to_milestone")
    assert p.get("authoritative_lead_id") == "to_milestone"
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


def test_npc_lead_discussion_first_intro_creates_record():
    session: dict = {"turn_counter": 1}
    scene_id = "gate"
    world = default_world()
    res = _resolution_question_with_topic(clue_id="east_lanes", text="East road is dangerous.")
    apply_socially_revealed_leads(session, scene_id, world, res)

    updates = apply_social_lead_discussion_tracking(
        session=session,
        scene_id=scene_id,
        resolution=res,
        player_text="What did they see on the east lanes?",
    )

    rec = get_npc_lead_discussion(session, scene_id, "runner", "east_lanes")
    assert rec is not None
    assert rec.get("npc_id") == "runner"
    assert rec.get("lead_id") == "east_lanes"
    assert rec.get("first_discussed_turn") == 1
    assert rec.get("last_discussed_turn") == 1
    assert rec.get("mention_count") == 1
    assert rec.get("last_scene_id") == scene_id
    assert isinstance(updates, list) and updates


def test_npc_lead_discussion_repeat_mention_updates_turn_and_count():
    session: dict = {"turn_counter": 4}
    scene_id = "gate"
    world = default_world()
    res = _resolution_question_with_topic(clue_id="east_lanes", text="East road is dangerous.")
    apply_socially_revealed_leads(session, scene_id, world, res)
    apply_social_lead_discussion_tracking(session=session, scene_id=scene_id, resolution=res, player_text="Any road rumors?")

    session["turn_counter"] = 5
    res2 = _resolution_question_with_topic(clue_id="east_lanes", text="Same road, same warning.")
    apply_socially_revealed_leads(session, scene_id, world, res2)
    apply_social_lead_discussion_tracking(
        session=session,
        scene_id=scene_id,
        resolution=res2,
        player_text="Tell me that lane warning again.",
    )

    rec = get_npc_lead_discussion(session, scene_id, "runner", "east_lanes")
    assert rec is not None
    assert rec.get("mention_count") == 2
    assert rec.get("first_discussed_turn") == 4
    assert rec.get("last_discussed_turn") == 5


def test_npc_lead_discussion_explicit_upgrades_from_hint():
    session: dict = {"turn_counter": 8}
    scene_id = "gate"
    res_hint = _resolution_question_with_topic(clue_id="patrol_vanish", text="A patrol may have vanished.")
    apply_social_lead_discussion_tracking(
        session=session,
        scene_id=scene_id,
        resolution=res_hint,
        player_text="Any patrol rumors?",
    )

    session["turn_counter"] = 9
    res_explicit = _resolution_question_with_topic(
        clue_id="patrol_vanish",
        text="The patrol vanished east of the old milestone.",
        leads_to_scene="old_milestone",
    )
    res_explicit["metadata"] = {"lead_landing": {"revealed_lead_ids": ["patrol_vanish"]}}
    apply_social_lead_discussion_tracking(
        session=session,
        scene_id=scene_id,
        resolution=res_explicit,
        player_text="Where exactly did they vanish?",
    )

    rec = get_npc_lead_discussion(session, scene_id, "runner", "patrol_vanish")
    assert rec is not None
    assert rec.get("disclosure_level") == "explicit"


def test_npc_lead_discussion_does_not_downgrade_explicit_to_hint():
    session: dict = {"turn_counter": 12}
    scene_id = "gate"
    res_explicit = _resolution_question_with_topic(
        clue_id="patrol_vanish",
        text="The patrol vanished east of the old milestone.",
    )
    res_explicit["metadata"] = {"lead_landing": {"revealed_lead_ids": ["patrol_vanish"]}}
    apply_social_lead_discussion_tracking(
        session=session,
        scene_id=scene_id,
        resolution=res_explicit,
        player_text="What happened to the patrol?",
    )

    session["turn_counter"] = 13
    res_hint = _resolution_question_with_topic(clue_id="patrol_vanish", text="People whisper about that patrol.")
    apply_social_lead_discussion_tracking(
        session=session,
        scene_id=scene_id,
        resolution=res_hint,
        player_text="Any whispers?",
    )

    rec = get_npc_lead_discussion(session, scene_id, "runner", "patrol_vanish")
    assert rec is not None
    assert rec.get("disclosure_level") == "explicit"


def test_npc_lead_discussion_skips_without_grounded_npc():
    session: dict = {"turn_counter": 3}
    scene_id = "gate"
    res = _resolution_question_with_topic(clue_id="east_lanes", text="East road is dangerous.")
    res["social"]["npc_id"] = None
    res["social"]["target_resolved"] = False

    updates = apply_social_lead_discussion_tracking(
        session=session,
        scene_id=scene_id,
        resolution=res,
        player_text="Tell me about east lanes.",
    )

    assert updates == []
    assert get_npc_lead_discussion(session, scene_id, "runner", "east_lanes") is None


def test_npc_lead_discussion_acknowledgement_marks_on_followup_same_npc_lead():
    session: dict = {"turn_counter": 20}
    scene_id = "gate"
    world = default_world()
    res = _resolution_question_with_topic(clue_id="missing_patrol", text="A patrol went missing east.")
    apply_socially_revealed_leads(session, scene_id, world, res)
    apply_social_lead_discussion_tracking(
        session=session,
        scene_id=scene_id,
        resolution=res,
        player_text="Any patrol rumors?",
    )

    session["turn_counter"] = 21
    res2 = _resolution_question_with_topic(clue_id="missing_patrol", text="Same missing patrol thread.")
    apply_socially_revealed_leads(session, scene_id, world, res2)
    apply_social_lead_discussion_tracking(
        session=session,
        scene_id=scene_id,
        resolution=res2,
        player_text="What about that missing patrol exactly?",
    )

    rec = get_npc_lead_discussion(session, scene_id, "runner", "missing_patrol")
    assert rec is not None
    assert rec.get("player_acknowledged") is True
    assert rec.get("player_acknowledged_turn") == 21


def test_npc_lead_discussion_repeat_continuity_updates_storage_fields():
    session: dict = {"turn_counter": 30}
    scene_id = "gate"
    world = default_world()
    res1 = _resolution_question_with_topic(clue_id="lead_smuggler_drop", text="A smuggler drop happens at dusk.")
    apply_socially_revealed_leads(session, scene_id, world, res1)
    apply_social_lead_discussion_tracking(
        session=session,
        scene_id=scene_id,
        resolution=res1,
        player_text="What is the smuggler drop?",
    )

    session["turn_counter"] = 31
    res2 = _resolution_question_with_topic(
        clue_id="lead_smuggler_drop",
        text="Same drop point, same dusk timing.",
    )
    apply_socially_revealed_leads(session, scene_id, world, res2)
    apply_social_lead_discussion_tracking(
        session=session,
        scene_id=scene_id,
        resolution=res2,
        player_text="And what happens after dusk at that drop?",
    )

    rec = get_npc_lead_discussion(session, scene_id, "runner", "lead_smuggler_drop")
    assert rec is not None
    assert rec.get("mention_count") == 2
    assert rec.get("first_discussed_turn") == 30
    assert rec.get("last_discussed_turn") == 31


def test_npc_lead_discussion_explicit_upgrade_persists_across_later_hinted_mentions():
    session: dict = {"turn_counter": 40}
    scene_id = "gate"
    world = default_world()
    res_hint = _resolution_question_with_topic(clue_id="missing_patrol", text="People whisper about a missing patrol.")
    apply_socially_revealed_leads(session, scene_id, world, res_hint)
    apply_social_lead_discussion_tracking(
        session=session,
        scene_id=scene_id,
        resolution=res_hint,
        player_text="Any patrol rumors?",
    )

    session["turn_counter"] = 41
    res_explicit = _resolution_question_with_topic(
        clue_id="missing_patrol",
        text="The missing patrol was last seen near the old milestone.",
        leads_to_scene="old_milestone",
    )
    apply_socially_revealed_leads(session, scene_id, world, res_explicit)
    apply_social_lead_discussion_tracking(
        session=session,
        scene_id=scene_id,
        resolution=res_explicit,
        player_text="Where were they last seen?",
    )

    session["turn_counter"] = 42
    res_hint_again = _resolution_question_with_topic(
        clue_id="missing_patrol",
        text="Locals still whisper about that patrol.",
    )
    apply_socially_revealed_leads(session, scene_id, world, res_hint_again)
    apply_social_lead_discussion_tracking(
        session=session,
        scene_id=scene_id,
        resolution=res_hint_again,
        player_text="Any new whispers?",
    )

    rec = get_npc_lead_discussion(session, scene_id, "runner", "missing_patrol")
    assert rec is not None
    assert rec.get("mention_count") == 3
    assert rec.get("disclosure_level") == "explicit"
    assert rec.get("last_discussed_turn") == 42


def test_npc_lead_discussion_strict_npc_scoping_for_same_lead():
    session: dict = {"turn_counter": 50}
    scene_id = "gate"
    world = default_world()

    res_a1 = _resolution_question_with_topic(clue_id="gate_watch", text="The gate watch rotates at dusk.")
    apply_socially_revealed_leads(session, scene_id, world, res_a1)
    apply_social_lead_discussion_tracking(
        session=session,
        scene_id=scene_id,
        resolution=res_a1,
        player_text="Tell me about the gate watch.",
    )

    session["turn_counter"] = 51
    res_a2 = _resolution_question_with_topic(clue_id="gate_watch", text="Same watch, same rotation.")
    apply_socially_revealed_leads(session, scene_id, world, res_a2)
    apply_social_lead_discussion_tracking(
        session=session,
        scene_id=scene_id,
        resolution=res_a2,
        player_text="What about that watch rotation exactly?",
    )

    session["turn_counter"] = 52
    res_b = _resolution_question_with_topic(clue_id="gate_watch", text="Captain confirms the same watch schedule.")
    res_b["social"]["npc_id"] = "guard_captain"
    res_b["social"]["npc_name"] = "Guard Captain"
    apply_socially_revealed_leads(session, scene_id, world, res_b)
    apply_social_lead_discussion_tracking(
        session=session,
        scene_id=scene_id,
        resolution=res_b,
        player_text="What does the captain say about it?",
    )

    rec_runner = get_npc_lead_discussion(session, scene_id, "runner", "gate_watch")
    rec_captain = get_npc_lead_discussion(session, scene_id, "guard_captain", "gate_watch")
    assert rec_runner is not None
    assert rec_captain is not None
    assert rec_runner.get("player_acknowledged") is True
    assert rec_captain.get("player_acknowledged") is False
    assert rec_runner.get("mention_count") == 2
    assert rec_captain.get("mention_count") == 1

    bucket = get_scene_runtime(session, scene_id).get("npc_lead_discussions") or {}
    assert "runner" in bucket and "guard_captain" in bucket
    assert isinstance(bucket["runner"], dict) and isinstance(bucket["guard_captain"], dict)
    assert "gate_watch" in bucket["runner"] and "gate_watch" in bucket["guard_captain"]


def test_topic_text_old_milestone_creates_extracted_lead():
    session: dict = {}
    world = default_world()
    world.setdefault("event_log", [])
    scene_id = "frontier_gate"
    res = {
        "kind": "question",
        "action_id": "q",
        "label": "Ask",
        "prompt": "Ask",
        "success": True,
        "resolved_transition": False,
        "target_scene_id": None,
        "clue_id": "missing_patrol",
        "discovered_clues": ["A patrol went missing near the old milestone."],
        "world_updates": None,
        "state_changes": {"topic_revealed": True},
        "hint": "h",
        "social": {
            "npc_id": "guard_captain",
            "npc_name": "Captain",
            "target_resolved": True,
            "topic_revealed": {
                "id": "patrol",
                "text": "A patrol went missing near the old milestone.",
                "clue_id": "missing_patrol",
            },
        },
        "requires_check": False,
    }
    apply_socially_revealed_leads(session, scene_id, world, res, scene={"scene": {"id": scene_id}})
    lid = "lead_frontier_gate_old_milestone"
    assert lid in get_all_known_clue_ids(session)
    rt = get_scene_runtime(session, scene_id)
    assert any(isinstance(p, dict) and p.get("clue_id") == lid for p in (rt.get("pending_leads") or []))
    assert get_clue_presentation(session, clue_id=lid) == "actionable"


def test_topic_text_guards_and_town_crier_create_leads():
    session: dict = {}
    world = default_world()
    for text, slug in (
        ("The watch says to speak with the guards at the barbican.", "guards"),
        ("If you need the decree read aloud, find the town crier by the well.", "town_crier"),
    ):
        res = {
            "kind": "question",
            "success": True,
            "requires_check": False,
            "clue_id": "rumor_gate",
            "discovered_clues": [text],
            "social": {
                "npc_id": "runner",
                "npc_name": "Runner",
                "target_resolved": True,
                "topic_revealed": {
                    "id": slug,
                    "text": text,
                    "clue_id": "rumor_gate",
                },
            },
        }
        apply_socially_revealed_leads(session, "frontier_gate", world, res, scene={"scene": {"id": "frontier_gate"}})
        lid = f"lead_frontier_gate_{slug}"
        assert lid in get_all_known_clue_ids(session)
        rt = get_scene_runtime(session, "frontier_gate")
        assert any(isinstance(p, dict) and p.get("clue_id") == lid for p in (rt.get("pending_leads") or []))


def test_structured_fact_scene_id_without_regex_creates_lead():
    """Tier B: clue_id equals a known scene file id → scene lead without phrase match."""
    session: dict = {}
    world = default_world()
    res = {
        "kind": "question",
        "success": True,
        "requires_check": False,
        "clue_id": "old_milestone",
        "discovered_clues": ["Proceed east when ready."],
        "social": {
            "npc_id": "runner",
            "target_resolved": True,
            "topic_revealed": {
                "id": "brief",
                "text": "Proceed east when ready.",
                "clue_id": "old_milestone",
            },
        },
    }
    apply_socially_revealed_leads(session, "frontier_gate", world, res, scene={"scene": {"id": "frontier_gate"}})
    lid = "lead_frontier_gate_old_milestone"
    assert lid in get_all_known_clue_ids(session)


def test_add_pending_lead_dedupes_by_authoritative_lead_id_and_merges_targets():
    session: dict = {}
    scene_id = "gate"
    add_pending_lead(
        session,
        scene_id,
        {
            "clue_id": "first_clue",
            "text": "Same thread",
            "authoritative_lead_id": "registry_one",
            "leads_to_scene": "old_milestone",
        },
    )
    add_pending_lead(
        session,
        scene_id,
        {
            "clue_id": "second_clue",
            "text": "Same thread",
            "authoritative_lead_id": "registry_one",
            "leads_to_npc": "guards",
        },
    )
    rt = get_scene_runtime(session, scene_id)
    rows = [p for p in (rt.get("pending_leads") or []) if isinstance(p, dict)]
    assert len(rows) == 1
    assert rows[0].get("authoritative_lead_id") == "registry_one"
    assert rows[0].get("leads_to_scene") == "old_milestone"
    assert rows[0].get("leads_to_npc") == "guards"


def test_add_pending_lead_legacy_still_dedupes_by_clue_id_only():
    session: dict = {}
    scene_id = "gate"
    add_pending_lead(
        session,
        scene_id,
        {"clue_id": "only_clue", "text": "A", "leads_to_scene": "s1"},
    )
    added_again = add_pending_lead(
        session,
        scene_id,
        {"clue_id": "only_clue", "text": "B", "leads_to_scene": "s2"},
    )
    assert added_again is False
    rt = get_scene_runtime(session, scene_id)
    assert len([p for p in (rt.get("pending_leads") or []) if isinstance(p, dict)]) == 1


def test_duplicate_social_resolution_does_not_duplicate_extracted_pending():
    session: dict = {}
    world = default_world()
    res = {
        "kind": "question",
        "success": True,
        "requires_check": False,
        "clue_id": "missing_patrol",
        "discovered_clues": ["A patrol went missing near the old milestone."],
        "social": {
            "npc_id": "guard_captain",
            "target_resolved": True,
            "topic_revealed": {
                "id": "patrol",
                "text": "A patrol went missing near the old milestone.",
                "clue_id": "missing_patrol",
            },
        },
    }
    apply_socially_revealed_leads(session, "frontier_gate", world, res, scene={"scene": {"id": "frontier_gate"}})
    apply_socially_revealed_leads(session, "frontier_gate", world, res, scene={"scene": {"id": "frontier_gate"}})
    rt = get_scene_runtime(session, "frontier_gate")
    lid = "lead_frontier_gate_old_milestone"
    matches = [p for p in (rt.get("pending_leads") or []) if isinstance(p, dict) and p.get("clue_id") == lid]
    assert len(matches) == 1


def test_narration_old_trading_crossroads_creates_lead():
    session: dict = {}
    world = default_world()
    world.setdefault("event_log", [])
    scene_id = "frontier_gate"
    res = _resolution_question_with_topic(clue_id="stew_clue", text="Hot stew and rumors for coin.")
    apply_socially_revealed_leads(session, scene_id, world, res, scene={"scene": {"id": scene_id}})
    narr = (
        "The runner leans in. If you want the real thread, ask around the old trading crossroads—"
        "voices loosen there after dark."
    )
    apply_social_narration_lead_supplements(session, scene_id, world, res, narr, {"scene": {"id": scene_id}})
    lid = "lead_frontier_gate_old_trading_crossroads"
    assert lid in get_all_known_clue_ids(session)
    rt = get_scene_runtime(session, scene_id)
    assert any(isinstance(p, dict) and p.get("clue_id") == lid for p in (rt.get("pending_leads") or []))
    ll = res.get("metadata", {}).get("lead_landing", {})
    assert lid in (ll.get("extracted_lead_ids") or [])
    assert ll.get("extracted_from_text") is True
    assert ll.get("extracted_from_reconciled_text") is True


def test_narration_lead_idempotent_no_duplicate_pending():
    session: dict = {}
    world = default_world()
    res = _resolution_question_with_topic(clue_id="base", text="Gate business.")
    narr = "You might speak with the guards if you want the watch's side."
    apply_socially_revealed_leads(session, "gate", world, res, scene={"scene": {"id": "gate"}})
    apply_social_narration_lead_supplements(session, "gate", world, res, narr, {"scene": {"id": "gate"}})
    apply_social_narration_lead_supplements(session, "gate", world, res, narr, {"scene": {"id": "gate"}})
    rt = get_scene_runtime(session, "gate")
    lid = "lead_gate_guards"
    matches = [p for p in (rt.get("pending_leads") or []) if isinstance(p, dict) and p.get("clue_id") == lid]
    assert len(matches) == 1


def test_flavor_only_narration_does_not_create_pattern_lead():
    session: dict = {}
    world = default_world()
    res = _resolution_question_with_topic(clue_id="stew_only", text="Hot stew and rumors for coin.")
    apply_socially_revealed_leads(session, "frontier_gate", world, res)
    apply_social_narration_lead_supplements(
        session,
        "frontier_gate",
        world,
        res,
        "The runner ladles thick stew and counts coins without meeting your eyes.",
        {"scene": {"id": "frontier_gate"}},
    )
    lead_prefix = [x for x in get_all_known_clue_ids(session) if str(x).startswith("lead_frontier_gate_")]
    assert lead_prefix == []


def test_frontier_gate_minimum_actionable_lead_from_exit_when_social_pending_empty():
    session: dict = {}
    world = default_world()
    scene = load_scene("frontier_gate")
    res = _resolution_question_with_topic(clue_id="stew_clue", text="Stew's hot; coin buys a bowl.")
    apply_socially_revealed_leads(session, "frontier_gate", world, res, scene=scene)
    narr = "The runner ladles stew in silence, eyes on the gate line."
    apply_social_narration_lead_supplements(session, "frontier_gate", world, res, narr, scene)
    dbg = ensure_scene_has_minimum_actionable_lead(
        scene_id="frontier_gate",
        session=session,
        scene=scene,
        resolution=res,
        gm_output={"player_facing_text": narr},
        world=world,
    )
    assert dbg is not None
    assert dbg.get("minimum_actionable_lead_enforced") is True
    # Authored discoverable_clues (old milestone) win before generic investigative exits.
    assert dbg.get("enforced_lead_source") == "discoverable_clue"
    assert dbg.get("enforced_lead_id") == "lead_frontier_gate_old_milestone"
    rt = get_scene_runtime(session, "frontier_gate")
    pending = rt.get("pending_leads") or []
    assert any(
        isinstance(p, dict) and p.get("leads_to_scene") == "old_milestone" for p in pending
    )
    meta = res.get("metadata") if isinstance(res.get("metadata"), dict) else {}
    mal = meta.get("minimum_actionable_lead") if isinstance(meta.get("minimum_actionable_lead"), dict) else {}
    assert mal.get("minimum_actionable_lead_enforced") is True
    assert meta.get("minimum_actionable_lead_enforced") is True
    assert meta.get("enforced_lead_source") == "discoverable_clue"


def test_minimum_actionable_lead_skips_when_pending_already_actionable():
    session: dict = {}
    world = default_world()
    scene = load_scene("frontier_gate")
    add_pending_lead(
        session,
        "frontier_gate",
        {"clue_id": "existing", "text": "Already have a thread", "leads_to_scene": "old_milestone"},
    )
    res = _resolution_question_with_topic(clue_id="stew_clue", text="More stew talk.")
    apply_socially_revealed_leads(session, "frontier_gate", world, res, scene=scene)
    dbg = ensure_scene_has_minimum_actionable_lead(
        scene_id="frontier_gate",
        session=session,
        scene=scene,
        resolution=res,
        gm_output={"player_facing_text": "Quiet nod."},
        world=world,
    )
    assert dbg is not None
    assert dbg.get("minimum_actionable_lead_enforced") is False
    rt = get_scene_runtime(session, "frontier_gate")
    assert len([p for p in (rt.get("pending_leads") or []) if isinstance(p, dict)]) == 1


def test_minimum_actionable_lead_double_call_does_not_duplicate_pending():
    session: dict = {}
    world = default_world()
    scene = load_scene("frontier_gate")
    res = _resolution_question_with_topic(clue_id="stew_clue", text="Stew's hot; coin buys a bowl.")
    apply_socially_revealed_leads(session, "frontier_gate", world, res, scene=scene)
    narr = "The runner ladles stew in silence, eyes on the gate line."
    apply_social_narration_lead_supplements(session, "frontier_gate", world, res, narr, scene)
    gm_out = {"player_facing_text": narr}
    dbg1 = ensure_scene_has_minimum_actionable_lead(
        scene_id="frontier_gate",
        session=session,
        scene=scene,
        resolution=res,
        gm_output=gm_out,
        world=world,
    )
    dbg2 = ensure_scene_has_minimum_actionable_lead(
        scene_id="frontier_gate",
        session=session,
        scene=scene,
        resolution=res,
        gm_output=gm_out,
        world=world,
    )
    assert dbg1 and dbg1.get("minimum_actionable_lead_enforced") is True
    assert dbg2 and dbg2.get("minimum_actionable_lead_enforced") is False
    rt = get_scene_runtime(session, "frontier_gate")
    milestone_pending = [
        p
        for p in (rt.get("pending_leads") or [])
        if isinstance(p, dict) and p.get("leads_to_scene") == "old_milestone"
    ]
    assert len(milestone_pending) == 1


def test_minimum_actionable_lead_not_injected_for_non_hub_scene():
    session: dict = {}
    world = default_world()
    scene = {"scene": {"id": "gate", "exits": [], "discoverable_clues": [], "mode": "social"}}
    res = _resolution_question_with_topic(clue_id="x", text="A rumor.")
    assert (
        ensure_scene_has_minimum_actionable_lead(
            scene_id="gate",
            session=session,
            scene=scene,
            resolution=res,
            gm_output={"player_facing_text": "They whisper."},
            world=world,
        )
        is None
    )


def test_extract_actionable_social_leads_public_shape():
    res = {
        "kind": "question",
        "clue_id": "c1",
        "discovered_clues": [],
        "social": {
            "npc_id": "n1",
            "topic_revealed": {
                "id": "t1",
                "text": "Seen toward the old milestone.",
                "clue_id": "c1",
                "leads_to_scene": "old_milestone",
            },
        },
    }
    leads = extract_actionable_social_leads(
        scene_id="frontier_gate",
        npc_id="n1",
        topic_payload=res["social"]["topic_revealed"],
        social_resolution=res,
        player_facing_text=None,
        scene=None,
        session=None,
        primary_clue_id="c1",
        extraction_pass="topic",
    )
    assert len(leads) >= 1
    L = leads[0]
    assert {
        "lead_id",
        "kind",
        "label",
        "source_scene_id",
        "source_npc_id",
        "target_scene_id",
        "target_npc_id",
        "rumor_text",
        "evidence_text",
    }.issubset(L.keys())


def test_extracted_social_lead_creates_authoritative_registry_row():
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}, "turn_counter": 1}
    world = default_world()
    world.setdefault("event_log", [])
    scene_id = "frontier_gate"
    res = {
        "kind": "question",
        "success": True,
        "requires_check": False,
        "clue_id": "missing_patrol",
        "discovered_clues": ["A patrol went missing near the old milestone."],
        "social": {
            "npc_id": "guard_captain",
            "target_resolved": True,
            "topic_revealed": {
                "id": "patrol",
                "text": "A patrol went missing near the old milestone.",
                "clue_id": "missing_patrol",
            },
        },
    }
    apply_socially_revealed_leads(session, scene_id, world, res, scene={"scene": {"id": scene_id}})
    lid = "lead_frontier_gate_old_milestone"
    row = get_lead(session, lid)
    assert row is not None
    assert lid in (row.get("evidence_clue_ids") or [])
    assert "social" in (row.get("discovery_source") or "")


def test_repeated_social_landing_does_not_duplicate_authoritative_lead():
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}, "turn_counter": 1}
    world = default_world()
    res = {
        "kind": "question",
        "success": True,
        "requires_check": False,
        "clue_id": "missing_patrol",
        "discovered_clues": ["A patrol went missing near the old milestone."],
        "social": {
            "npc_id": "guard_captain",
            "target_resolved": True,
            "topic_revealed": {
                "id": "patrol",
                "text": "A patrol went missing near the old milestone.",
                "clue_id": "missing_patrol",
            },
        },
    }
    apply_socially_revealed_leads(session, "frontier_gate", world, res, scene={"scene": {"id": "frontier_gate"}})
    reg_size_after_first = len(ensure_lead_registry(session))
    apply_socially_revealed_leads(session, "frontier_gate", world, res, scene={"scene": {"id": "frontier_gate"}})
    assert len(ensure_lead_registry(session)) == reg_size_after_first


def test_lead_landing_metadata_reports_authoritative_outcomes():
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}, "turn_counter": 1}
    world = default_world()
    res = {
        "kind": "question",
        "success": True,
        "requires_check": False,
        "clue_id": "to_milestone",
        "discovered_clues": ["They were seen toward the old milestone."],
        "social": {
            "npc_id": "runner",
            "target_resolved": True,
            "topic_revealed": {
                "id": "t1",
                "text": "They were seen toward the old milestone.",
                "clue_id": "to_milestone",
                "leads_to_scene": "old_milestone",
            },
        },
    }
    apply_socially_revealed_leads(session, "gate", world, res)
    ll = res["metadata"]["lead_landing"]
    auth_ids = (
        (ll.get("authoritative_created_ids") or [])
        + (ll.get("authoritative_updated_ids") or [])
        + (ll.get("authoritative_unchanged_ids") or [])
    )
    assert "to_milestone" in auth_ids
    assert isinstance(ll.get("authoritative_promoted_ids"), list)

    apply_socially_revealed_leads(session, "gate", world, res)
    ll2 = res["metadata"]["lead_landing"]
    second_pass = (ll2.get("authoritative_updated_ids") or []) + (ll2.get("authoritative_unchanged_ids") or [])
    assert "to_milestone" in second_pass


def test_clue_discovery_then_social_extract_updates_same_authoritative_row():
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}, "turn_counter": 1}
    world = default_world()
    world.setdefault("event_log", [])
    world["clues"] = {
        "gate_hint": {
            "canonical_lead_id": "unified_thread",
            "leads_to_scene": "old_milestone",
            "type": "investigation",
        }
    }
    record_discovered_clue(
        session,
        "frontier_gate",
        "gate_hint",
        clue_text="Watch papers cite the old milestone route.",
        world=world,
    )
    assert get_lead(session, "unified_thread") is not None
    assert len(ensure_lead_registry(session)) == 1

    res = {
        "kind": "question",
        "success": True,
        "requires_check": False,
        "clue_id": "gate_hint",
        "discovered_clues": ["The captain confirms: old milestone."],
        "social": {
            "npc_id": "guard_captain",
            "target_resolved": True,
            "topic_revealed": {
                "id": "cap",
                "text": "The captain confirms: old milestone.",
                "clue_id": "old_milestone",
            },
        },
    }
    apply_socially_revealed_leads(session, "frontier_gate", world, res, scene={"scene": {"id": "frontier_gate"}})

    assert len(ensure_lead_registry(session)) == 1
    row = get_lead(session, "unified_thread")
    assert row is not None
    ev = row.get("evidence_clue_ids") or []
    assert "gate_hint" in ev
    assert "lead_frontier_gate_old_milestone" in ev


_SCENE_FLAG_MINIMUM_ACTIONABLE = "ensure_minimum_actionable_lead_after_social"

_LEAD_LANDING_LIST_KEYS = (
    "revealed_lead_ids",
    "already_known_lead_ids",
    "actionable_lead_ids",
    "lead_write_targets",
    "extracted_lead_ids",
    "extracted_lead_sources",
    "authoritative_created_ids",
    "authoritative_updated_ids",
    "authoritative_unchanged_ids",
    "authoritative_promoted_ids",
)


def _assert_lists_deduped(ll: dict, keys: tuple[str, ...]) -> None:
    for k in keys:
        xs = ll.get(k) or []
        assert isinstance(xs, list)
        assert len(xs) == len(list(dict.fromkeys(xs)))


def test_apply_socially_revealed_leads_reentrancy_one_authoritative_one_pending_idempotent_events():
    """Same resolution twice: one registry row, one compat pending per authoritative id, stable event log."""
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}, "turn_counter": 1}
    world = default_world()
    world.setdefault("event_log", [])
    res = {
        "kind": "question",
        "success": True,
        "requires_check": False,
        "clue_id": "missing_patrol",
        "discovered_clues": ["A patrol went missing near the old milestone."],
        "social": {
            "npc_id": "guard_captain",
            "target_resolved": True,
            "topic_revealed": {
                "id": "patrol",
                "text": "A patrol went missing near the old milestone.",
                "clue_id": "missing_patrol",
            },
        },
    }
    auth_id = "lead_frontier_gate_old_milestone"
    apply_socially_revealed_leads(session, "frontier_gate", world, res, scene={"scene": {"id": "frontier_gate"}})
    reg_after_first = len(ensure_lead_registry(session))
    events_after_first = list(world.get("event_log") or [])
    apply_socially_revealed_leads(session, "frontier_gate", world, res, scene={"scene": {"id": "frontier_gate"}})
    assert len(ensure_lead_registry(session)) == reg_after_first
    assert get_lead(session, auth_id) is not None
    rt = get_scene_runtime(session, "frontier_gate")
    pending = [p for p in (rt.get("pending_leads") or []) if isinstance(p, dict)]
    by_auth = [p for p in pending if p.get("authoritative_lead_id") == auth_id]
    assert len(by_auth) == 1
    assert by_auth[0].get("clue_id") == auth_id
    actionable_dupes = [p for p in pending if p.get("clue_id") == auth_id]
    assert len(actionable_dupes) == 1
    assert world.get("event_log") == events_after_first
    revealed = [
        e
        for e in world.get("event_log") or []
        if isinstance(e, dict) and e.get("type") == "social_lead_revealed" and e.get("clue_id") == "missing_patrol"
    ]
    assert len(revealed) == 1


def test_narration_supplement_twice_same_text_metadata_lists_stay_deduped():
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}, "turn_counter": 1}
    world = default_world()
    scene_id = "frontier_gate"
    scene = {"scene": {"id": scene_id}}
    res = _resolution_question_with_topic(clue_id="stew_clue", text="Hot stew and rumors for coin.")
    apply_socially_revealed_leads(session, scene_id, world, res, scene=scene)
    narr = (
        "The runner leans in. If you want the real thread, ask around the old trading crossroads—"
        "voices loosen there after dark."
    )
    apply_social_narration_lead_supplements(session, scene_id, world, res, narr, scene)
    ll1 = dict(res["metadata"]["lead_landing"])
    reg_after_first = len(ensure_lead_registry(session))
    apply_social_narration_lead_supplements(session, scene_id, world, res, narr, scene)
    ll2 = res["metadata"]["lead_landing"]
    lid = "lead_frontier_gate_old_trading_crossroads"
    assert get_lead(session, lid) is not None
    assert len(ensure_lead_registry(session)) == reg_after_first
    row = get_lead(session, lid)
    assert row is not None
    rt = get_scene_runtime(session, scene_id)
    cross = [p for p in (rt.get("pending_leads") or []) if isinstance(p, dict) and p.get("clue_id") == lid]
    assert len(cross) == 1
    _assert_lists_deduped(ll2, _LEAD_LANDING_LIST_KEYS)
    assert set(ll2.get("extracted_lead_ids") or []) == set(ll1.get("extracted_lead_ids") or [])
    assert set(ll2.get("extracted_lead_sources") or []) == set(ll1.get("extracted_lead_sources") or [])
    for k in (
        "authoritative_created_ids",
        "authoritative_updated_ids",
        "authoritative_unchanged_ids",
        "authoritative_promoted_ids",
    ):
        xs = ll2.get(k) or []
        assert len(xs) == len(list(dict.fromkeys(xs)))


def test_ensure_minimum_actionable_skips_after_normal_social_landing_no_extra_rows():
    """Actionable pending from apply_socially_revealed_leads: safety rail is a no-op."""
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}, "turn_counter": 1}
    world = default_world()
    scene = {
        "scene": {
            "id": "custom_hub",
            "exits": [],
            "discoverable_clues": [],
            _SCENE_FLAG_MINIMUM_ACTIONABLE: True,
        }
    }
    res = _resolution_question_with_topic(
        clue_id="to_milestone",
        text="They were seen toward the old milestone.",
        leads_to_scene="old_milestone",
    )
    apply_socially_revealed_leads(session, "custom_hub", world, res, scene=scene)
    reg_n = len(ensure_lead_registry(session))
    rt = get_scene_runtime(session, "custom_hub")
    pending_n = len([p for p in (rt.get("pending_leads") or []) if isinstance(p, dict)])
    dbg = ensure_scene_has_minimum_actionable_lead(
        scene_id="custom_hub",
        session=session,
        scene=scene,
        resolution=res,
        gm_output={"player_facing_text": "They nod toward the east road."},
        world=world,
    )
    assert dbg is not None
    assert dbg.get("minimum_actionable_lead_enforced") is False
    assert len(ensure_lead_registry(session)) == reg_n
    rt2 = get_scene_runtime(session, "custom_hub")
    assert len([p for p in (rt2.get("pending_leads") or []) if isinstance(p, dict)]) == pending_n
    mal = res.get("metadata", {}).get("minimum_actionable_lead", {})
    assert mal.get("minimum_actionable_lead_enforced") is False


def test_first_pass_lead_landing_metadata_shape_actionable_matches_pending():
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}, "turn_counter": 1}
    world = default_world()
    res = {
        "kind": "question",
        "success": True,
        "requires_check": False,
        "clue_id": "to_milestone",
        "discovered_clues": ["They were seen toward the old milestone."],
        "social": {
            "npc_id": "runner",
            "target_resolved": True,
            "topic_revealed": {
                "id": "t1",
                "text": "They were seen toward the old milestone.",
                "clue_id": "to_milestone",
                "leads_to_scene": "old_milestone",
            },
        },
    }
    apply_socially_revealed_leads(session, "gate", world, res)
    ll = res["metadata"]["lead_landing"]
    assert set(_LEAD_LANDING_LIST_KEYS).issubset(ll.keys())
    assert "extracted_from_text" in ll and isinstance(ll["extracted_from_text"], bool)
    assert "extracted_from_reconciled_text" in ll and isinstance(ll["extracted_from_reconciled_text"], bool)
    _assert_lists_deduped(ll, _LEAD_LANDING_LIST_KEYS)
    assert SESSION_LEAD_REGISTRY_KEY in (ll.get("lead_write_targets") or [])
    assert "to_milestone" in (ll.get("authoritative_created_ids") or []) or "to_milestone" in (
        ll.get("authoritative_updated_ids") or []
    ) or "to_milestone" in (ll.get("authoritative_unchanged_ids") or [])
    actionable = ll.get("actionable_lead_ids") or []
    rt = get_scene_runtime(session, "gate")
    pending_ids = [p.get("clue_id") for p in (rt.get("pending_leads") or []) if isinstance(p, dict)]
    for aid in actionable:
        assert aid in pending_ids


def test_canonical_extracted_sibling_collapses_evidence_uses_one_extracted_trigger_cid():
    """Design: among extracted siblings sharing one registry id, only the canonical extracted row supplies trigger/evidence.

    Other extracted sibling clue ids must not appear on the authoritative lead row (primary clue discovery may still add its own trigger).
    """
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}, "turn_counter": 1}
    world = default_world()
    world["clues"] = {
        "primary_x": {"canonical_lead_id": "merged_auth"},
        "old_milestone": {"canonical_lead_id": "merged_auth"},
        "lead_frontier_gate_guards": {"canonical_lead_id": "merged_auth"},
    }
    res = {
        "kind": "question",
        "success": True,
        "requires_check": False,
        "clue_id": "primary_x",
        "discovered_clues": ["If you need help, speak with the guards at the barbican."],
        "social": {
            "npc_id": "runner",
            "target_resolved": True,
            "topic_revealed": {
                "id": "t1",
                "text": "A patrol went missing near the old milestone.",
                "clue_id": "primary_x",
            },
        },
    }
    apply_socially_revealed_leads(session, "frontier_gate", world, res, scene={"scene": {"id": "frontier_gate"}})
    ext = res["metadata"]["lead_landing"]["extracted_lead_ids"]
    assert "lead_frontier_gate_old_milestone" in ext
    assert "lead_frontier_gate_guards" in ext
    row = get_lead(session, "merged_auth")
    assert row is not None
    ev = row.get("evidence_clue_ids") or []
    assert "lead_frontier_gate_guards" not in ev
    assert "lead_frontier_gate_old_milestone" in ev


def test_social_extract_reinforced_second_disclosure_one_registry_row():
    session: dict = {"scene_runtime": {}, "clue_knowledge": {}, "turn_counter": 1}
    world = default_world()
    res1 = {
        "kind": "question",
        "success": True,
        "requires_check": False,
        "clue_id": "missing_patrol",
        "discovered_clues": ["A patrol went missing near the old milestone."],
        "social": {
            "npc_id": "guard_captain",
            "target_resolved": True,
            "topic_revealed": {
                "id": "patrol",
                "text": "A patrol went missing near the old milestone.",
                "clue_id": "missing_patrol",
            },
        },
    }
    apply_socially_revealed_leads(session, "frontier_gate", world, res1, scene={"scene": {"id": "frontier_gate"}})
    reg_after_first = len(ensure_lead_registry(session))
    res2 = {
        "kind": "question",
        "success": True,
        "requires_check": False,
        "clue_id": "missing_patrol",
        "discovered_clues": [
            "A patrol went missing near the old milestone. Fresh hoofprints marked the east verge."
        ],
        "social": {
            "npc_id": "guard_captain",
            "target_resolved": True,
            "topic_revealed": {
                "id": "patrol",
                "text": "A patrol went missing near the old milestone. Fresh hoofprints marked the east verge.",
                "clue_id": "missing_patrol",
            },
        },
    }
    apply_socially_revealed_leads(session, "frontier_gate", world, res2, scene={"scene": {"id": "frontier_gate"}})
    assert len(ensure_lead_registry(session)) == reg_after_first
    row = get_lead(session, "lead_frontier_gate_old_milestone")
    assert row is not None
