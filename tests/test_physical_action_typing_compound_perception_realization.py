"""PR-AQ: ordinary physical/perception language must keep existing action ownership.

Synthetic fixtures use slate-cistern / harbor-wharf vocabulary. Frontier Gate /
gate-line cases are calibration regression only.
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
from game.diegetic_fallback_narration import render_observe_perception_fallback_line
from game.exploration import resolve_exploration_action
from game.human_adjacent_focus import classify_human_adjacent_intent_family
from game.intent_parser import (
    looks_like_local_physical_movement,
    looks_like_scene_travel_destination_intent,
    parse_freeform_to_action,
    recover_actionable_explicit_world_action,
)
from game.interaction_context import (
    inspect as inspect_interaction_context,
    rebuild_active_scene_entities,
    set_social_target,
)
from game.interaction_routing import choose_interaction_route, is_world_action
from game.leads import SESSION_LEAD_REGISTRY_KEY
from game.scene_actions import normalize_scene_action
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _patch_storage

CALIBRATION_ENGINE_TERMS = (
    "frontier_gate",
    "muddy_gate_line",
    "gate_line",
    "tavern_runner",
    "notice_board",
    "missing_patrol",
    "Cinderwatch",
    "Captain Thoran",
    "guard_captain",
    "old_milestone",
    "stew",
)
GENERIC_ENGINE_FILES = (
    Path("game/intent_parser.py"),
    Path("game/human_adjacent_focus.py"),
    Path("game/interaction_routing.py"),
    Path("game/social_continuity_routing.py"),
)
T16_TEXT = "I walk a few steps along the muddy gate line and listen"
AUDIBLE_FACT = "Water can be heard dripping behind the stone wall."
WALL_FACT = "A slate cistern leans against the mossed inner wall."
STATUE_FACT = "A salt-stained statue faces the inner basin."


def _cistern_scene(*, audible: bool = False, extra=None) -> dict:
    facts = [WALL_FACT, STATUE_FACT]
    if audible:
        facts.append(AUDIBLE_FACT)
    scene = {
        "scene": {
            "id": "slate_cistern",
            "location": "Slate Cistern",
            "summary": "A quiet inner court, a cistern, and a statue.",
            "visible_facts": facts,
            "hidden_facts": ["A silver token lies under the cistern rim."],
            "discoverable_clues": [],
            "interactables": [
                {
                    "id": "basin_statue",
                    "label": "Basin statue",
                    "aliases": ["statue", "figure"],
                    "type": "investigate",
                }
            ],
            "addressables": [
                {
                    "id": "cistern_warden",
                    "name": "Cistern Warden",
                    "scene_id": "slate_cistern",
                    "kind": "npc",
                    "addressable": True,
                    "address_roles": ["warden"],
                    "aliases": [],
                }
            ],
            "exits": [
                {"label": "Eastern arch", "target_scene_id": "lantern_cut"},
            ],
        }
    }
    if extra:
        scene["scene"].update(extra)
    return scene


def _cistern_world() -> dict:
    world = default_world()
    world["npcs"] = [
        {
            "id": "cistern_warden",
            "name": "Cistern Warden",
            "location": "slate_cistern",
            "topics": [{"id": "basin", "text": "The basin is filled before second watch."}],
        }
    ]
    return world


def _seed(tmp_path, monkeypatch, scene: dict, *, world: dict | None = None):
    _patch_storage(tmp_path, monkeypatch)
    sid = scene["scene"]["id"]
    storage._save_json(storage.scene_path(sid), scene)
    storage._save_json(storage.scene_path("lantern_cut"), default_scene("lantern_cut"))
    storage._save_json(storage.scene_path("frontier_gate"), default_scene("frontier_gate"))
    storage._save_json(storage.WORLD_PATH, world or _cistern_world())
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


def _kind(data: dict) -> str:
    return str((data.get("resolution") or {}).get("kind") or "")


def _scene_id(data: dict) -> str:
    scene = data.get("scene") or {}
    if isinstance(scene, dict) and isinstance(scene.get("scene"), dict):
        return str(scene["scene"].get("id") or "")
    return str(scene.get("id") or data.get("active_scene_id") or "")


def _lead_ids() -> set[str]:
    sess = storage.load_session()
    reg = sess.get(SESSION_LEAD_REGISTRY_KEY) or {}
    return {str(k) for k in reg.keys()} if isinstance(reg, dict) else set()


def _resolve(scene: dict, text: str, session: dict | None = None):
    parsed = parse_freeform_to_action(text, scene)
    action = normalize_scene_action(parsed)
    return parsed, resolve_exploration_action(
        scene,
        session if isinstance(session, dict) else {},
        {},
        action,
        raw_player_text=text,
        list_scene_ids=lambda: ["slate_cistern", "lantern_cut"],
    )


def _complete(text: str) -> bool:
    raw = str(text or "").strip()
    if not raw or raw.endswith("…") or raw.endswith("..."):
        return False
    return raw[-1] in ".!?\""


def test_t16_combined_walk_listen_is_observe_not_none():
    scene = _cistern_scene()
    parsed, res = _resolve(scene, T16_TEXT)
    assert parsed is not None
    assert parsed.get("type") == "observe"
    assert (parsed.get("metadata") or {}).get("human_adjacent_intent_family") == "approach_listen"
    assert res["kind"] == "observe"
    assert res.get("resolved_transition") is not True
    assert res.get("target_scene_id") in (None, "")


def test_primitive_local_walk_uses_existing_custom_kind():
    text = "I walk a few steps along the wall."
    scene = _cistern_scene()
    parsed, res = _resolve(scene, text)
    assert looks_like_local_physical_movement(text) is True
    assert looks_like_scene_travel_destination_intent(text) is False
    assert parsed["type"] == "custom"
    assert (parsed.get("metadata") or {}).get("parser_lane") == "local_physical_movement"
    assert res["kind"] == "custom"
    assert res.get("resolved_transition") is not True


def test_primitive_listen_uses_existing_observe_contract():
    parsed, res = _resolve(_cistern_scene(), "I listen.")
    assert parsed["type"] == "observe"
    assert (parsed.get("metadata") or {}).get("human_adjacent_intent_family") == "listen"
    assert res["kind"] == "observe"


def test_walk_toward_is_travel_not_local_walk():
    text = "I walk toward the northern road."
    parsed = parse_freeform_to_action(text, _cistern_scene())
    assert looks_like_scene_travel_destination_intent(text) is True
    assert looks_like_local_physical_movement(text) is False
    assert parsed["type"] == "travel"
    assert not parsed.get("target_scene_id")


def test_leave_through_authored_exit_remains_travel():
    scene = _cistern_scene()
    parsed, res = _resolve(scene, "I leave through the eastern arch.")
    assert parsed["type"] in {"travel", "scene_transition"}
    assert (parsed.get("target_scene_id") or res.get("target_scene_id")) == "lantern_cut"


def test_unresolved_travel_is_not_reinterpreted_as_local_walk():
    text = "I head for the silver road."
    parsed = parse_freeform_to_action(text, _cistern_scene())
    assert looks_like_local_physical_movement(text) is False
    assert parsed["type"] == "travel"
    assert not parsed.get("target_scene_id")


def test_local_approach_does_not_leave_scene():
    parsed, res = _resolve(_cistern_scene(), "I step closer to the statue.")
    assert parsed["type"] == "custom"
    assert res.get("resolved_transition") is not True
    assert res.get("target_scene_id") in (None, "")


def test_walk_and_listen_does_not_split_into_travel():
    parsed, res = _resolve(_cistern_scene(), "I walk along the wall and listen.")
    assert parsed["type"] == "observe"
    assert res["kind"] == "observe"
    assert res.get("resolved_transition") is not True


def test_move_and_look_uses_existing_observe():
    parsed, res = _resolve(_cistern_scene(), "I step beside the doorway and look around.")
    assert parsed["type"] == "observe"
    assert res["kind"] == "observe"
    assert res.get("resolved_transition") is not True


def test_move_and_inspect_uses_existing_investigate():
    parsed, res = _resolve(_cistern_scene(), "I move closer to the statue and examine the statue.")
    assert parsed["type"] == "investigate"
    assert parsed.get("target_id") == "basin_statue"
    assert res["kind"] in {"investigate", "already_searched"}


def test_ambiguous_leave_and_inspect_does_not_split_execute():
    parsed = parse_freeform_to_action(
        "I leave through the arch and inspect the desk.",
        _cistern_scene(),
    )
    assert parsed["type"] in {"travel", "scene_transition"}
    assert parsed.get("type") != "investigate"


def test_talk_and_walk_away_is_not_local_movement():
    text = "I talk to the guard and walk away."
    assert looks_like_local_physical_movement(text) is False
    parsed = parse_freeform_to_action(text, _cistern_scene())
    assert (parsed or {}).get("metadata", {}).get("parser_lane") != "local_physical_movement"


def test_listen_vocative_is_not_perception():
    assert classify_human_adjacent_intent_family("Listen, stranger, the basin is closed.") == "none"


def test_empty_listen_fallback_is_grounded_absence():
    scene = _cistern_scene()
    parsed, res = _resolve(scene, "I listen.")
    line = render_observe_perception_fallback_line(
        scene,
        seed_key="praq|empty-listen",
        player_text="I listen.",
        resolution=res,
    )
    assert line
    assert _complete(line)
    low = line.lower()
    assert "footstep" not in low
    assert "whisper about" not in low
    assert "patrol" not in low


def test_authored_audible_fact_may_be_surfaced():
    scene = _cistern_scene(audible=True)
    parsed, res = _resolve(scene, "I listen.")
    line = render_observe_perception_fallback_line(
        scene,
        seed_key="praq|authored-listen",
        player_text="I listen.",
        resolution=res,
    )
    assert line
    assert "water" in line.lower() or "drip" in line.lower() or "heard" in line.lower()
    assert "bells ring" not in line.lower()
    assert "guards speak" not in line.lower()


def test_repeated_empty_listen_does_not_invent_new_sound():
    scene = _cistern_scene()
    first = render_observe_perception_fallback_line(
        scene,
        seed_key="praq|repeat-a",
        player_text="I listen.",
        resolution=_resolve(scene, "I listen.")[1],
    )
    second = render_observe_perception_fallback_line(
        scene,
        seed_key="praq|repeat-b",
        player_text="I listen again.",
        resolution=_resolve(scene, "I listen again.")[1],
    )
    for line in (first, second):
        assert line
        assert "new voice" not in line.lower()
        assert "someone approaches" not in line.lower()


def test_generic_engine_has_no_calibration_special_case():
    for path in GENERIC_ENGINE_FILES:
        text = path.read_text(encoding="utf-8")
        for term in CALIBRATION_ENGINE_TERMS:
            assert term not in text, f"{path} contains {term}"
        assert T16_TEXT not in text
        assert "walk a few steps along the muddy gate line and listen" not in text


def test_http_local_walk_stays_in_scene(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, _cistern_scene())
    data = _chat(monkeypatch, "I walk a few steps along the wall.", "You take a few steps along the wall.")
    assert _kind(data) == "custom"
    assert "slate_cistern" in (_scene_id(data) or storage.load_session().get("active_scene_id"))
    assert _complete(_facing(data))
    assert "kind=None" not in _facing(data)
    assert _lead_ids() == set()


def test_http_listen_empty_is_typed_and_complete(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, _cistern_scene())
    data = _chat(monkeypatch, "I listen.", "Too much crowd noise washes together; no clear words carry to you.")
    assert _kind(data) == "observe"
    facing = _facing(data)
    assert _complete(facing)
    assert "kind=None" not in facing
    assert storage.load_session().get("active_scene_id") == "slate_cistern"


def test_http_walk_listen_authored_sound(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, _cistern_scene(audible=True))
    data = _chat(
        monkeypatch,
        "I walk along the wall and listen.",
        "You edge closer and catch it clearer: water can be heard dripping behind the stone wall.",
    )
    assert _kind(data) == "observe"
    assert storage.load_session().get("active_scene_id") == "slate_cistern"
    facing = _facing(data).lower()
    assert "water" in facing or "drip" in facing
    assert "extra bell" not in facing
    assert _lead_ids() == set()


def test_http_unresolved_travel_stays_travel(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, _cistern_scene())
    data = _chat(monkeypatch, "I head for the silver road.", "That destination is not available from here.")
    assert _kind(data) == "travel"
    assert storage.load_session().get("active_scene_id") == "slate_cistern"


def test_http_explicit_exit_travel(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, _cistern_scene())
    data = _chat(monkeypatch, "I leave through the eastern arch.", "You pass through the eastern arch.")
    kind = _kind(data)
    assert kind in {"travel", "scene_transition"}
    sess = storage.load_session()
    if kind == "scene_transition":
        assert sess.get("active_scene_id") == "lantern_cut"
    else:
        assert sess.get("active_scene_id") in {"slate_cistern", "lantern_cut"}


def test_social_then_walk_listen_is_not_stale_social(tmp_path, monkeypatch):
    scene = _cistern_scene()
    world = _cistern_world()
    _seed(tmp_path, monkeypatch, scene, world=world)
    session = storage.load_session()
    rebuild_active_scene_entities(session, world, "slate_cistern", scene_envelope=scene)
    set_social_target(session, "cistern_warden")
    storage.save_session(session)
    text = "I walk a few steps and listen."
    assert is_world_action(text) is True
    recovered = recover_actionable_explicit_world_action(text, scene, session=session, world=world)
    assert recovered is not None
    assert recovered.get("type") == "observe"
    assert choose_interaction_route(text, scene=scene, session=session, world=world) != "dialogue"
    data = _chat(monkeypatch, text, "You take a few steps and listen. Nothing distinct carries.")
    assert _kind(data) == "observe"
    ctx = inspect_interaction_context(storage.load_session())
    assert ctx.get("interaction_mode") != "social" or ctx.get("active_interaction_kind") != "social"


def test_walk_listen_then_explicit_social_return(tmp_path, monkeypatch):
    scene = _cistern_scene()
    world = _cistern_world()
    _seed(tmp_path, monkeypatch, scene, world=world)
    _chat(monkeypatch, "I walk a few steps along the wall and listen.", "You walk a few steps and listen.")
    data = _chat(
        monkeypatch,
        'I turn to the Cistern Warden. "What fills the basin?"',
        'Cistern Warden says, "The basin is filled before second watch."',
    )
    assert _kind(data) in {"question", "interact", "social_probe"}
    ctx = inspect_interaction_context(storage.load_session())
    assert ctx.get("active_interaction_target_id") == "cistern_warden"


def test_http_repeated_local_walk_does_not_drift(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, _cistern_scene())
    _chat(monkeypatch, "I walk a few steps along the wall.", "You walk a few steps along the wall.")
    data = _chat(monkeypatch, "I pace beside the wall.", "You pace beside the wall.")
    assert _kind(data) == "custom"
    assert storage.load_session().get("active_scene_id") == "slate_cistern"
    assert _lead_ids() == set()


def test_frontier_t16_calibration_is_typed_observe(tmp_path, monkeypatch):
    scene = default_scene("frontier_gate")
    _seed(tmp_path, monkeypatch, scene, world=default_world())
    data = _chat(
        monkeypatch,
        T16_TEXT,
        "You walk a few steps along the muddy gate line and listen. No distinct words carry.",
    )
    assert _kind(data) == "observe"
    assert storage.load_session().get("active_scene_id") == "frontier_gate"
    facing = _facing(data)
    assert _complete(facing)
    assert "kind=None" not in facing
    assert _lead_ids() == set()
