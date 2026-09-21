"""PR-AI: bound speaker knowledge follows NPC/topic authority, not engine omniscience.

Synthetic fixtures are unrelated to Cinderwatch. Frontier Gate cases are
calibration regression only.
"""

from __future__ import annotations

import inspect
from pathlib import Path

from fastapi.testclient import TestClient

from game import storage
from game.api import app
from game.defaults import (
    default_campaign,
    default_character,
    default_combat,
    default_conditions,
    default_scene,
    default_session,
    default_world,
)
from game.interaction_context import inspect as inspect_interaction_context
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.social import (
    apply_authored_knowledge_realization_to_gm,
    authoritative_knowledge_npc_ids_for_speaker,
    realize_authored_knowledge_answer,
    _text_communicates_authored_fact,
)
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _patch_storage

CALIBRATION_ENGINE_TERMS = (
    "guard_captain",
    "Captain Thoran",
    "frontier_gate",
    "Cinderwatch",
    "watch_command",
    "patrol",
    "notice_patrol_route",
    "old_milestone",
)
IRRIGATION_FACT = "Floodgates open at first light and close before the third bell."
BELL_FACT = "The cracked bell is scheduled for recasting after harvest."
RIVER_FACT = "Skiffs wait at the inner piles until the bar clears."
HIDDEN_FACT = "A brass token is sealed under the quay stones."
PUBLIC_CLUE = "High water is posted for the third bell."
WATCH_FACT = "Captain Thoran commands the gate watch tonight."


def _amber_scene() -> dict:
    return {
        "scene": {
            "id": "amber_quay",
            "location": "Amber Quay",
            "summary": "A quiet quay, a shrine step, and a fruit stall.",
            "visible_facts": [
                "A fruit stall leans against the quay wall.",
                "A shrine step holds a cracked bell.",
            ],
            "hidden_facts": [HIDDEN_FACT],
            "discoverable_clues": [{"id": "quay_tide_board", "text": PUBLIC_CLUE}],
            "addressables": [
                {
                    "id": "orchard_keeper",
                    "name": "Orchard Keeper",
                    "scene_id": "amber_quay",
                    "kind": "npc",
                    "addressable": True,
                    "address_roles": ["keeper"],
                    "aliases": ["grove warden"],
                },
                {
                    "id": "shrine_caretaker",
                    "name": "Shrine Caretaker",
                    "scene_id": "amber_quay",
                    "kind": "npc",
                    "addressable": True,
                    "address_roles": ["caretaker"],
                    "aliases": [],
                },
                {
                    "id": "ferry_master",
                    "name": "Ferry Master",
                    "scene_id": "amber_quay",
                    "kind": "npc",
                    "addressable": True,
                    "address_roles": ["ferry"],
                    "aliases": [],
                },
            ],
            "interactables": [
                {
                    "id": "tide_board",
                    "label": "Tide board",
                    "aliases": ["tide board", "posted water"],
                    "type": "investigate",
                    "reveals_clue": "quay_tide_board",
                }
            ],
            "exits": [],
            "enemies": [],
            "actions": [],
        }
    }


def _amber_world() -> dict:
    return {
        "npcs": [
            {
                "id": "orchard_keeper",
                "name": "Orchard Keeper",
                "location": "amber_quay",
                "aliases": ["grove warden"],
                "topics": [{"id": "irrigation_schedule", "text": IRRIGATION_FACT}],
            },
            {
                "id": "shrine_caretaker",
                "name": "Shrine Caretaker",
                "location": "amber_quay",
                "topics": [{"id": "bell_repairs", "text": BELL_FACT}],
            },
            {
                "id": "ferry_master",
                "name": "Ferry Master",
                "location": "amber_quay",
                "topics": [{"id": "river_crossings", "text": RIVER_FACT}],
            },
        ]
    }


def _session_for(world: dict, scene_id: str, scene: dict | None = None) -> dict:
    session = default_session()
    session["active_scene_id"] = scene_id
    rebuild_active_scene_entities(session, world, scene_id, scene_envelope=scene)
    return session


def _social_res(npc_id: str | None, npc_name: str | None = None) -> dict:
    social: dict = {"social_intent_class": "social_exchange", "target_resolved": bool(npc_id)}
    if npc_id:
        social["npc_id"] = npc_id
        social["npc_name"] = npc_name or npc_id.replace("_", " ").title()
    return {"kind": "question", "social": social}


def _realize(world: dict, session: dict, player_text: str, npc_id: str | None, scene: dict | None = None):
    name = None
    if npc_id:
        row = next((n for n in world.get("npcs") or [] if n.get("id") == npc_id), None)
        name = str((row or {}).get("name") or "").strip() or None
    return realize_authored_knowledge_answer(
        session=session,
        scene_id=str(((scene or {}).get("scene") or {}).get("id") or "amber_quay"),
        player_text=player_text,
        resolution=_social_res(npc_id, name),
        world=world,
        scene=scene or _amber_scene(),
    )


def _seed_amber_http(tmp_path, monkeypatch, *, world: dict | None = None, scene: dict | None = None):
    _patch_storage(tmp_path, monkeypatch)
    envelope = scene or _amber_scene()
    sid = envelope["scene"]["id"]
    storage._save_json(storage.scene_path(sid), envelope)
    storage._save_json(storage.scene_path("frontier_gate"), default_scene("frontier_gate"))
    w = default_world()
    w["npcs"] = (world or _amber_world())["npcs"]
    storage._save_json(storage.WORLD_PATH, w)
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    session = default_session()
    session["active_scene_id"] = sid
    session["visited_scene_ids"] = [sid]
    storage.save_session(session)
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")
    return sid


def _chat(monkeypatch, text: str, gm_text: str):
    monkeypatch.setattr("game.api.call_gpt", lambda _messages: _gm_response(gm_text))
    client = TestClient(app)
    resp = client.post("/api/chat", json={"text": text})
    assert resp.status_code == 200
    return resp.json()


def _facing(data: dict) -> str:
    return str((data.get("gm_output") or {}).get("player_facing_text") or "")


def test_ignorance_line_does_not_count_as_communicating_owned_fact():
    line = 'Guard Captain shakes their head. "I don\'t know."'
    assert _text_communicates_authored_fact(line, WATCH_FACT, speaker_id="guard_captain", speaker_name="Guard Captain") is False
    assert _text_communicates_authored_fact(
        'Orchard Keeper mutters, "Floodgates open at first light and close before the third bell."',
        IRRIGATION_FACT,
        speaker_id="orchard_keeper",
        speaker_name="Orchard Keeper",
    ) is True


def test_general_owned_topic_first_ask():
    world = _amber_world()
    session = _session_for(world, "amber_quay", _amber_scene())
    set_social_target(session, "orchard_keeper")
    realized = _realize(world, session, "When do the floodgates open?", "orchard_keeper")
    assert realized is not None
    text = str(realized.get("text") or realized.get("fact_text") or "")
    assert "first light" in text.lower()
    assert "i don't know" not in text.lower()


def test_general_unrelated_topic_does_not_leak():
    world = _amber_world()
    session = _session_for(world, "amber_quay", _amber_scene())
    realized = _realize(world, session, "When is the cracked bell getting recast?", "orchard_keeper")
    text = str((realized or {}).get("text") or (realized or {}).get("fact_text") or "").lower()
    assert "recasting" not in text
    assert BELL_FACT.lower() not in text


def test_general_two_npcs_separate_knowledge():
    world = _amber_world()
    session = _session_for(world, "amber_quay", _amber_scene())
    own = _realize(world, session, "When do the floodgates open?", "orchard_keeper")
    leak = _realize(world, session, "When is the cracked bell getting recast?", "orchard_keeper")
    other = _realize(world, session, "When is the cracked bell getting recast?", "shrine_caretaker")
    assert "first light" in str((own or {}).get("text") or "").lower()
    assert BELL_FACT.lower() not in str((leak or {}).get("text") or "").lower()
    assert "recasting" in str((other or {}).get("text") or "").lower()


def test_general_absent_topic_owner_is_not_selected_as_speaker():
    world = _amber_world()
    world["npcs"][0]["location"] = "mill_pond"
    session = _session_for(world, "amber_quay", _amber_scene())
    realized = _realize(world, session, "When do the floodgates open?", "shrine_caretaker")
    text = str((realized or {}).get("text") or "")
    assert "first light" not in text.lower()
    assert "Orchard Keeper" not in text


def test_general_alias_display_identity_preserves_ownership():
    world = _amber_world()
    session = _session_for(world, "amber_quay", _amber_scene())
    ids = authoritative_knowledge_npc_ids_for_speaker(
        world=world,
        session=session,
        scene_id="amber_quay",
        speaker_id="orchard_keeper",
        speaker_name="Grove Warden",
        scene=_amber_scene(),
    )
    assert "orchard_keeper" in ids
    realized = _realize(world, session, "When do the floodgates open?", "orchard_keeper")
    assert "first light" in str((realized or {}).get("text") or "").lower()


def test_general_legitimate_ignorance():
    world = _amber_world()
    session = _session_for(world, "amber_quay", _amber_scene())
    realized = _realize(world, session, "Where is the sealed brass token hidden?", "ferry_master")
    text = str((realized or {}).get("text") or (realized or {}).get("fact_text") or "").lower()
    assert "brass token" not in text
    assert HIDDEN_FACT.lower() not in text


def test_general_authorized_shared_clue_knowledge_remains_answerable():
    world = _amber_world()
    session = _session_for(world, "amber_quay", _amber_scene())
    session["clue_knowledge"] = {
        "quay_tide_board": {"text": PUBLIC_CLUE, "source_scene": "amber_quay", "presentation": "actionable"}
    }
    realized = _realize(world, session, "What high water time is posted?", "ferry_master")
    assert realized is not None
    assert "third bell" in str(realized.get("text") or realized.get("fact_text") or "").lower()


def test_general_no_speaker_does_not_invent_absent_owner():
    world = {
        "npcs": [
            {
                "id": "orchard_keeper",
                "name": "Orchard Keeper",
                "location": "mill_pond",
                "topics": [{"id": "irrigation_schedule", "text": IRRIGATION_FACT}],
            }
        ]
    }
    session = _session_for(world, "amber_quay", _amber_scene())
    realized = _realize(world, session, "When do the floodgates open?", None)
    text = str((realized or {}).get("text") or "")
    assert "Orchard Keeper" not in text
    assert "first light" not in text.lower()


def test_general_hidden_fact_not_exposed_because_speaker_is_bound():
    world = _amber_world()
    session = _session_for(world, "amber_quay", _amber_scene())
    realized = _realize(world, session, "Is a brass token sealed under the quay stones?", "orchard_keeper")
    text = str((realized or {}).get("text") or (realized or {}).get("fact_text") or "").lower()
    assert "brass token" not in text


def test_general_natural_paraphrase_reaches_owned_topic():
    world = _amber_world()
    session = _session_for(world, "amber_quay", _amber_scene())
    realized = _realize(world, session, "What hour do you open those floodgates?", "orchard_keeper")
    assert realized is not None
    assert "first light" in str(realized.get("text") or realized.get("fact_text") or "").lower()


def test_general_http_owned_topic_first_ask(tmp_path, monkeypatch):
    _seed_amber_http(tmp_path, monkeypatch)
    data = _chat(
        monkeypatch,
        'I turn to the Orchard Keeper. "When do the floodgates open?"',
        'Orchard Keeper shakes their head. "I don\'t know."',
    )
    text = _facing(data).lower()
    assert "first light" in text
    assert "i don't know" not in text
    assert inspect_interaction_context(data.get("session") or {}).get("active_interaction_target_id") == "orchard_keeper"


def test_general_http_unrelated_topic_no_leak(tmp_path, monkeypatch):
    _seed_amber_http(tmp_path, monkeypatch)
    data = _chat(
        monkeypatch,
        'I turn to the Orchard Keeper. "When is the cracked bell getting recast?"',
        'Orchard Keeper shakes their head. "I don\'t know."',
    )
    text = _facing(data).lower()
    assert "recasting" not in text
    assert inspect_interaction_context(data.get("session") or {}).get("active_interaction_target_id") == "orchard_keeper"


def test_bound_captain_first_ask_watch_command_replaces_ignorance():
    world = default_world()
    world["npcs"] = [
        {
            "id": "gate_guard",
            "name": "Gate Guard",
            "location": "frontier_gate",
            "aliases": ["guard", "watch", "watch guard"],
            "topics": [{"id": "watch_command", "text": WATCH_FACT, "clue_id": "captain_thoran_watch"}],
        },
        {
            "id": "tavern_runner",
            "name": "Tavern Runner",
            "location": "frontier_gate",
            "topics": [{"id": "stew", "text": "Hot stew and rumors for coin."}],
        },
    ]
    scene = default_scene("frontier_gate")
    session = _session_for(world, "frontier_gate", scene)
    set_social_target(session, "guard_captain")
    gm = apply_authored_knowledge_realization_to_gm(
        {"player_facing_text": 'Guard Captain shakes their head. "I don\'t know."', "tags": []},
        player_text="Who commands the watch here?",
        resolution=_social_res("guard_captain", "Guard Captain"),
        session=session,
        world=world,
        scene=scene,
        scene_id="frontier_gate",
    )
    text = str(gm.get("player_facing_text") or "")
    low = text.lower()
    assert "thoran" in low
    assert "i don't know" not in low
    assert "Guard Captain" in text


def test_bound_runner_does_not_receive_watch_command():
    world = default_world()
    world["npcs"] = [
        {
            "id": "gate_guard",
            "name": "Gate Guard",
            "location": "frontier_gate",
            "aliases": ["guard", "watch", "watch guard"],
            "topics": [{"id": "watch_command", "text": WATCH_FACT}],
        },
        {
            "id": "tavern_runner",
            "name": "Tavern Runner",
            "location": "frontier_gate",
            "topics": [{"id": "stew", "text": "Hot stew and rumors for coin."}],
        },
    ]
    scene = default_scene("frontier_gate")
    session = _session_for(world, "frontier_gate", scene)
    realized = realize_authored_knowledge_answer(
        session=session,
        scene_id="frontier_gate",
        player_text="Who commands the watch here?",
        resolution=_social_res("tavern_runner", "Tavern Runner"),
        world=world,
        scene=scene,
    )
    text = str((realized or {}).get("text") or (realized or {}).get("fact_text") or "").lower()
    assert "thoran" not in text


def test_http_bound_captain_first_ask_no_warmup(tmp_path, monkeypatch):
    _patch_storage(tmp_path, monkeypatch)
    storage._save_json(storage.scene_path("frontier_gate"), default_scene("frontier_gate"))
    storage._save_json(storage.scene_path("market_quarter"), default_scene("market_quarter"))
    world = default_world()
    world["npcs"] = [
        {
            "id": "gate_guard",
            "name": "Gate Guard",
            "location": "frontier_gate",
            "aliases": ["guard", "watch", "watch guard"],
            "topics": [{"id": "watch_command", "text": WATCH_FACT, "clue_id": "captain_thoran_watch"}],
        },
        {
            "id": "tavern_runner",
            "name": "Tavern Runner",
            "location": "frontier_gate",
            "topics": [{"id": "stew", "text": "Hot stew and rumors for coin."}],
        },
    ]
    storage._save_json(storage.WORLD_PATH, world)
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    session["visited_scene_ids"] = ["frontier_gate"]
    storage.save_session(session)
    data = _chat(
        monkeypatch,
        'I turn to the Guard Captain. "Who commands the watch here?"',
        'Guard Captain shakes their head. "I don\'t know."',
    )
    text = _facing(data)
    low = text.lower()
    assert "thoran" in low
    assert "i don't know" not in low
    assert inspect_interaction_context(data.get("session") or {}).get("active_interaction_target_id") == "guard_captain"


def test_http_bound_captain_natural_paraphrase(tmp_path, monkeypatch):
    _patch_storage(tmp_path, monkeypatch)
    storage._save_json(storage.scene_path("frontier_gate"), default_scene("frontier_gate"))
    storage._save_json(storage.scene_path("market_quarter"), default_scene("market_quarter"))
    world = default_world()
    world["npcs"] = [
        {
            "id": "gate_guard",
            "name": "Gate Guard",
            "location": "frontier_gate",
            "aliases": ["guard", "watch", "watch guard"],
            "topics": [{"id": "watch_command", "text": WATCH_FACT}],
        }
    ]
    storage._save_json(storage.WORLD_PATH, world)
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    session["visited_scene_ids"] = ["frontier_gate"]
    storage.save_session(session)
    data = _chat(
        monkeypatch,
        'I turn to the Guard Captain. "Who\'s in charge of the watch?"',
        'Guard Captain shakes their head. "I don\'t know."',
    )
    low = _facing(data).lower()
    assert "thoran" in low
    assert "i don't know" not in low


def test_generic_helpers_are_not_calibration_specific():
    src = inspect.getsource(authoritative_knowledge_npc_ids_for_speaker)
    for term in CALIBRATION_ENGINE_TERMS:
        assert term not in src
    social_path = Path("game/social.py")
    added_marker = "authoritative_knowledge_npc_ids_for_speaker"
    assert added_marker in social_path.read_text(encoding="utf-8")
