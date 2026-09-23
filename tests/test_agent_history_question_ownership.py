"""PR-BC: directed actor/history questions are not inspect of the mentioned surface.

Undirected ``who last read`` remains inspect (fail-closed residue). Genuine
read/inspect/content questions stay investigation. No last-reader fact is added.
"""
from __future__ import annotations

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
from game.intent_parser import (
    looks_like_explicit_world_object_action,
    parse_freeform_to_action,
    recover_actionable_explicit_world_action,
)
from game.interaction_context import (
    addressed_information_request_starts_before,
    find_addressed_npc_id_for_turn,
    resolve_directed_social_entry,
)
from game.interaction_routing import choose_interaction_route, is_directed_dialogue
from game.social import classify_social_followup_dimension, parse_social_intent
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _patch_storage

SLATE = "Charcoal ticks mark yesterday's kiln loads."
MANIFEST = "Berth four lists dry cedar and lamp oil."
INVENTED_IDENTITY = 'Night Porter says, "Mira from the dock office checked it after the second bell."'
INVENTED_TIME = 'Night Porter mutters, "Word is, they were due to leave sometime before dawn."'
INVENTED_PROVENANCE = 'Night Porter says, "It came up from the south quay last week."'
GENERIC_ENGINE_FILES = (
    Path("game/interaction_context.py"),
    Path("game/intent_parser.py"),
)


def _envelope(scene_id: str, **extra) -> dict:
    scene = default_scene(scene_id)
    inner = scene["scene"]
    inner["id"] = scene_id
    inner["location"] = extra.pop("location", scene_id.replace("_", " ").title())
    inner.update(extra)
    return scene


KILN = _envelope(
    "ember_kiln",
    location="Ember Kiln Alcove",
    summary="A brick kiln, a tally slate, and a night porter.",
    visible_facts=["A tally slate hangs by the kiln door.", "A sealed crate sits under the eaves."],
    discoverable_clues=[{"id": "tally_slate_marks", "text": SLATE}],
    interactables=[
        {
            "id": "tally_slate",
            "label": "Tally slate",
            "aliases": ["slate", "tally slate"],
            "type": "investigate",
            "reveals_clue": "tally_slate_marks",
        }
    ],
    addressables=[
        {
            "id": "night_porter",
            "name": "Night Porter",
            "scene_id": "ember_kiln",
            "kind": "npc",
            "addressable": True,
            "aliases": ["porter", "guard"],
        }
    ],
    exits=[],
)
KILN_EMPTY = _envelope(
    "ember_kiln",
    location="Ember Kiln Alcove",
    summary="A brick kiln and a tally slate.",
    visible_facts=["A tally slate hangs by the kiln door."],
    discoverable_clues=[{"id": "tally_slate_marks", "text": SLATE}],
    interactables=[
        {
            "id": "tally_slate",
            "label": "Tally slate",
            "aliases": ["slate", "tally slate"],
            "type": "investigate",
            "reveals_clue": "tally_slate_marks",
        }
    ],
    addressables=[],
    exits=[],
)
CEDAR = _envelope(
    "cedar_wharf",
    location="Cedar Wharf",
    summary="A cargo manifest hangs by the clerk's hook.",
    visible_facts=["A cargo manifest hangs by the clerk's hook."],
    discoverable_clues=[{"id": "cargo_manifest_berth", "text": MANIFEST}],
    interactables=[
        {
            "id": "cargo_manifest",
            "label": "Cargo manifest",
            "aliases": ["manifest", "cargo list"],
            "type": "investigate",
            "reveals_clue": "cargo_manifest_berth",
        }
    ],
    addressables=[
        {
            "id": "dock_clerk",
            "name": "Dock Clerk",
            "scene_id": "cedar_wharf",
            "kind": "npc",
            "addressable": True,
            "aliases": ["clerk"],
        }
    ],
    exits=[],
)


def _world_for(scene: dict) -> dict:
    world = default_world()
    sid = scene["scene"]["id"]
    npcs = []
    for row in scene["scene"].get("addressables") or []:
        if isinstance(row, dict) and row.get("kind") == "npc":
            npcs.append(
                {
                    "id": row.get("id"),
                    "name": row.get("name"),
                    "location": sid,
                    "aliases": row.get("aliases") or [],
                }
            )
    world["npcs"] = npcs
    return world


def _session(scene_id: str) -> dict:
    session = default_session()
    session["active_scene_id"] = scene_id
    session["visited_scene_ids"] = [scene_id]
    return session


def _ctx(scene: dict):
    return _session(scene["scene"]["id"]), scene, _world_for(scene)


def _entry(text: str, scene: dict):
    session, _, world = _ctx(scene)
    return resolve_directed_social_entry(
        session=session, scene=scene, world=world, segmented_turn=None, raw_text=text
    )


def _seed(tmp_path, monkeypatch, scene: dict) -> None:
    _patch_storage(tmp_path, monkeypatch)
    sid = scene["scene"]["id"]
    storage._save_json(storage.scene_path(sid), scene)
    for extra_id in ("frontier_gate", "market_quarter", "old_milestone"):
        if extra_id != sid:
            storage._save_json(storage.scene_path(extra_id), default_scene(extra_id))
    storage._save_json(storage.WORLD_PATH, _world_for(scene))
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    session = _session(sid)
    session["turn_counter"] = 2
    storage.save_session(session)
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def _chat(monkeypatch, text: str, gm_text: str) -> dict:
    monkeypatch.setattr("game.api.call_gpt", lambda _messages: _gm_response(gm_text))
    client = TestClient(app)
    resp = client.post("/api/chat", json={"text": text})
    assert resp.status_code == 200
    return resp.json()


def _facing(data: dict) -> str:
    return str((data.get("gm_output") or {}).get("player_facing_text") or "")


def _kind(data: dict) -> str:
    return str((data.get("resolution") or {}).get("kind") or "")


def test_imperative_read_and_inspect_remain_investigation():
    session, scene, world = _ctx(KILN)
    for text in ("Read the tally slate.", "Inspect the tally slate.", "Look over the tally slate."):
        parsed = parse_freeform_to_action(text, scene, session=session, world=world)
        assert parsed is not None, text
        assert parsed.get("type") == "investigate", text
        if "look over" not in text.lower():
            assert parsed.get("target_id") == "tally_slate", text
            assert looks_like_explicit_world_object_action(text) is True, text
        assert _entry(text, scene).get("should_route_social") is False, text


def test_content_question_remains_investigation():
    session, scene, world = _ctx(KILN_EMPTY)
    text = "What does the tally slate say?"
    parsed = parse_freeform_to_action(text, scene, session=session, world=world)
    assert parsed is not None
    assert parsed.get("type") == "investigate"
    assert (parsed.get("metadata") or {}).get("parser_lane") == "interactable_content_question"


def test_undirected_who_last_read_remains_inspect_residue():
    session, scene, world = _ctx(KILN_EMPTY)
    text = "Who last read the tally slate?"
    parsed = parse_freeform_to_action(text, scene, session=session, world=world)
    assert parsed is not None
    assert parsed.get("type") == "investigate"
    assert parsed.get("target_id") == "tally_slate"
    assert recover_actionable_explicit_world_action(text, scene, session=session, world=world) is None
    assert _entry(text, KILN_EMPTY).get("should_route_social") is False
    assert classify_social_followup_dimension(text) == "identity"


def test_undirected_who_last_read_does_not_bind_sole_npc():
    text = "Who last read that tally slate?"
    session, scene, world = _ctx(KILN)
    assert find_addressed_npc_id_for_turn(text, session, world, scene) == "night_porter"
    assert _entry(text, KILN).get("should_route_social") is False
    assert is_directed_dialogue(text, scene=scene, session=session, world=world) is False
    parsed = parse_freeform_to_action(text, scene, session=session, world=world)
    assert parsed is not None
    assert parsed.get("type") == "investigate"


def test_when_history_question_empty_stays_inspect_residue():
    session, scene, world = _ctx(KILN_EMPTY)
    text = "When was the tally slate last read?"
    parsed = parse_freeform_to_action(text, scene, session=session, world=world)
    assert parsed is not None
    assert parsed.get("type") == "investigate"
    assert classify_social_followup_dimension(text) == "time"


def test_non_inspect_verb_who_questions_are_not_investigation():
    session, scene, world = _ctx(KILN_EMPTY)
    for text in ("Who wrote this notice?", "Who put this here?", "Who moved this crate?", "Where did this notice come from?"):
        parsed = parse_freeform_to_action(text, scene, session=session, world=world)
        assert parsed is None or parsed.get("type") != "investigate", text


def test_vocative_who_read_is_social_not_inspect():
    session, scene, world = _ctx(KILN)
    text = "Night Porter, who last read the tally slate?"
    assert addressed_information_request_starts_before(text, text.lower().find("read")) is True
    assert looks_like_explicit_world_object_action(text) is False
    assert recover_actionable_explicit_world_action(text, scene, session=session, world=world) is None
    entry = _entry(text, KILN)
    assert entry.get("should_route_social") is True
    assert entry.get("target_actor_id") == "night_porter"
    assert is_directed_dialogue(text, scene=scene, session=session, world=world) is True
    assert choose_interaction_route(text, scene=scene, session=session, world=world) == "dialogue"
    assert classify_social_followup_dimension(text) == "identity"


def test_ask_who_read_is_social_without_question_mark():
    session, scene, world = _ctx(KILN)
    text = "Ask the guard who read this."
    assert looks_like_explicit_world_object_action(text) is False
    assert recover_actionable_explicit_world_action(text, scene, session=session, world=world) is None
    social = parse_social_intent(text, scene, world)
    assert social is None or social.get("type") == "question"
    entry = _entry(text, KILN)
    assert entry.get("should_route_social") is True
    assert entry.get("target_actor_id") == "night_porter"
    assert choose_interaction_route(text, scene=scene, session=session, world=world) == "dialogue"


def test_i_ask_who_last_read_is_social():
    session, scene, world = _ctx(KILN)
    text = "I ask the night porter who last read that tally slate."
    assert looks_like_explicit_world_object_action(text) is False
    assert recover_actionable_explicit_world_action(text, scene, session=session, world=world) is None
    social = parse_social_intent(text, scene, world)
    assert social is None or social.get("type") == "question"
    entry = _entry(text, KILN)
    assert entry.get("should_route_social") is True
    assert entry.get("target_actor_id") == "night_porter"


def test_inspect_then_ask_still_escapes_to_world_action():
    text = "I inspect the tally slate, then I ask who last read it."
    assert looks_like_explicit_world_object_action(text) is True
    assert _entry(text, KILN).get("should_route_social") is False


def test_cedar_generalization_ask_who_read_manifest():
    session, scene, world = _ctx(CEDAR)
    text = "Ask the dock clerk who read this cargo manifest."
    assert looks_like_explicit_world_object_action(text) is False
    social = parse_social_intent(text, scene, world)
    assert social is None or social.get("type") == "question"
    entry = _entry(text, CEDAR)
    assert entry.get("should_route_social") is True
    assert entry.get("target_actor_id") == "dock_clerk"
    read = parse_freeform_to_action("Read the cargo manifest.", scene, session=session, world=world)
    assert read is not None
    assert read.get("type") == "investigate"
    assert read.get("target_id") == "cargo_manifest"


def test_http_imperative_read_still_inspects(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, KILN)
    data = _chat(monkeypatch, "Read the tally slate.", "Invented last-reader Mira.")
    assert _kind(data) in {"investigate", "discover_clue"}
    text = _facing(data).lower()
    assert "charcoal ticks" in text
    assert "mira" not in text


def test_http_undirected_who_last_read_stays_inspect(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, KILN_EMPTY)
    data = _chat(monkeypatch, "Who last read the tally slate?", INVENTED_IDENTITY)
    assert _kind(data) in {"investigate", "discover_clue"}
    text = _facing(data).lower()
    assert "mira" not in text
    assert "dock office" not in text


def test_http_directed_who_read_is_social_absence(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, KILN)
    data = _chat(monkeypatch, "Night Porter, who last read the tally slate?", INVENTED_IDENTITY)
    assert _kind(data) in {"question", "social_probe"}
    text = _facing(data).lower()
    assert "mira" not in text
    assert "dock office" not in text
    assert "second bell" not in text
    assert "charcoal ticks" not in text


def test_http_ask_who_read_generalizes_at_cedar(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, CEDAR)
    data = _chat(monkeypatch, "Ask the dock clerk who read this cargo manifest.", INVENTED_IDENTITY)
    assert _kind(data) in {"question", "social_probe"}
    text = _facing(data).lower()
    assert "mira" not in text
    assert "dock office" not in text
    assert "berth four" not in text


def test_http_directed_when_does_not_invent_time(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, KILN)
    data = _chat(monkeypatch, "Night Porter, when was the tally slate last read?", INVENTED_TIME)
    assert _kind(data) in {"question", "social_probe"}
    text = _facing(data).lower()
    assert "before dawn" not in text
    assert "dawn" not in text


def test_http_directed_provenance_does_not_invent_origin(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, KILN)
    data = _chat(monkeypatch, "Night Porter, where did this notice come from?", INVENTED_PROVENANCE)
    assert _kind(data) in {"question", "social_probe"}
    text = _facing(data).lower()
    assert "south quay" not in text
    assert "last week" not in text


def test_http_existing_checked_board_social_still_binds(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, KILN)
    data = _chat(
        monkeypatch,
        "I step back to the night porter and ask who last checked that board.",
        INVENTED_IDENTITY,
    )
    assert _kind(data) in {"question", "social_probe"}
    assert "mira" not in _facing(data).lower()


def test_generic_engine_has_no_tally_slate_special_case():
    for rel in GENERIC_ENGINE_FILES:
        lowered = rel.read_text(encoding="utf-8").lower()
        assert "tally slate" not in lowered
        assert "who last read that" not in lowered
        assert "frontier_gate" not in lowered
        assert "notice_board" not in lowered
