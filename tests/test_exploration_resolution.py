"""Tests for deterministic exploration action resolution and /api/action exploration path."""
from game import storage
from game.api import app
from game.exploration import resolve_exploration_action, parse_exploration_intent, EXPLORATION_KINDS
from game.scene_actions import normalize_scene_action
from game.storage import get_scene_runtime
from game.defaults import default_scene, default_session, default_world, default_character, default_campaign, default_combat, default_conditions
from fastapi.testclient import TestClient
import pytest


pytestmark = pytest.mark.unit

# Canonical engine result keys from ExplorationEngineResult.to_dict()
ENGINE_RESULT_REQUIRED_KEYS = frozenset({
    "kind", "action_id", "label", "prompt", "success", "resolved_transition",
    "target_scene_id", "clue_id", "discovered_clues", "world_updates", "state_changes", "hint",
})
ENGINE_RESULT_EXTRA_KEYS = frozenset({
    "originating_scene_id", "interactable_id", "clue_text", "metadata", "skill_check",
})


def _assert_normalized_engine_result(resolution: dict, expected_kind: str, **extra_assertions) -> None:
    """Assert resolution conforms to the standardized engine result schema."""
    assert isinstance(resolution, dict), "resolution must be a dict"
    for key in ENGINE_RESULT_REQUIRED_KEYS:
        assert key in resolution, f"resolution must have '{key}'"
    assert resolution["kind"] == expected_kind
    assert isinstance(resolution["action_id"], str)
    assert isinstance(resolution["label"], str)
    assert isinstance(resolution["prompt"], str)
    assert resolution["success"] is None or isinstance(resolution["success"], bool)
    assert isinstance(resolution["resolved_transition"], bool)
    assert isinstance(resolution["discovered_clues"], list)
    assert isinstance(resolution["state_changes"], dict)
    assert isinstance(resolution["hint"], str)
    known = ENGINE_RESULT_REQUIRED_KEYS | ENGINE_RESULT_EXTRA_KEYS
    for key in resolution:
        assert key in known, f"Unexpected key in resolution: {key}"
    for k, v in extra_assertions.items():
        assert resolution.get(k) == v, f"{k}={resolution.get(k)} != {v}"


def _patch_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "BASE_DIR", tmp_path)
    monkeypatch.setattr(storage, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(storage, "WORLD_PATH", storage.DATA_DIR / "world.json")
    monkeypatch.setattr(storage, "SCENES_DIR", storage.DATA_DIR / "scenes")
    monkeypatch.setattr(storage, "CHARACTER_PATH", storage.DATA_DIR / "character.json")
    monkeypatch.setattr(storage, "CAMPAIGN_PATH", storage.DATA_DIR / "campaign.json")
    monkeypatch.setattr(storage, "SESSION_PATH", storage.DATA_DIR / "session.json")
    monkeypatch.setattr(storage, "COMBAT_PATH", storage.DATA_DIR / "combat.json")
    monkeypatch.setattr(storage, "CONDITIONS_PATH", storage.DATA_DIR / "conditions.json")
    monkeypatch.setattr(storage, "SESSION_LOG_PATH", storage.DATA_DIR / "session_log.jsonl")
    storage.SCENES_DIR.mkdir(parents=True, exist_ok=True)


def _seed_scenes_and_session(tmp_path, monkeypatch, active="scene_a", scenes=("scene_a", "scene_b")):
    _patch_storage(tmp_path, monkeypatch)
    for sid in scenes:
        s = default_scene(sid)
        s["scene"]["id"] = sid
        # Add exit from scene_a to scene_b for graph validation
        if sid == "scene_a" and "scene_b" in scenes:
            s["scene"].setdefault("exits", []).append({"label": "Go to Scene B", "target_scene_id": "scene_b"})
        storage._save_json(storage.scene_path(sid), s)
    session = default_session()
    session["active_scene_id"] = active
    session["visited_scene_ids"] = list(scenes)
    storage._save_json(storage.SESSION_PATH, session)
    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def test_scene_transition_with_known_target_activates_before_narration(tmp_path, monkeypatch):
    """Exploration action with scene_transition and known target_scene_id activates that scene before GPT is called."""
    _seed_scenes_and_session(tmp_path, monkeypatch, active="scene_a", scenes=("scene_a", "scene_b"))
    call_gpt_invoked_with_scene_id = []

    def capture_messages(messages):
        import json
        for m in messages:
            if m.get("role") == "user" and "content" in m:
                try:
                    payload = json.loads(m["content"])
                    scene = payload.get("scene", {})
                    public = scene.get("public", {})
                    sid = public.get("id")
                    if sid:
                        call_gpt_invoked_with_scene_id.append(sid)
                except Exception:
                    pass
        return {"player_facing_text": "You arrive.", "tags": [], "scene_update": None, "activate_scene_id": None, "new_scene_draft": None, "world_updates": None, "suggested_action": None, "debug_notes": ""}

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", capture_messages)
        client = TestClient(app)
        r = client.post(
            "/api/action",
            json={
                "action_type": "exploration",
                "intent": "Go to scene B",
                "exploration_action": {
                    "id": "go-scene-b",
                    "label": "Go: Scene B",
                    "type": "scene_transition",
                    "targetSceneId": "scene_b",
                    "prompt": "I go to scene B.",
                },
            },
        )
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert data.get("session", {}).get("active_scene_id") == "scene_b"
    assert data.get("scene", {}).get("scene", {}).get("id") == "scene_b"
    assert call_gpt_invoked_with_scene_id and call_gpt_invoked_with_scene_id[-1] == "scene_b"


def test_observe_engine_result_with_literal_empty_session_world():
    """Observe actions return the standardized ExplorationEngineResult schema."""
    scene = {"scene": {"id": "test", "location": "Here"}}
    action = normalize_scene_action({"id": "observe-a", "label": "Observe the area", "type": "observe", "prompt": "Look around."})
    resolution = resolve_exploration_action(scene, {}, {}, action, raw_player_text="Look around.", list_scene_ids=lambda: [])
    _assert_normalized_engine_result(resolution, "observe", resolved_transition=False)
    assert resolution["action_id"] == "observe-a"
    assert resolution["success"] is None


def test_investigate_engine_result_with_empty_discoverable_clues():
    """Investigate actions (without interactable match) return normalized engine result."""
    scene = {"scene": {"id": "test", "location": "Here", "discoverable_clues": []}}
    action = normalize_scene_action({"id": "inv-desk", "label": "Investigate the desk", "type": "investigate", "prompt": "Search the desk."})
    resolution = resolve_exploration_action(scene, {}, {}, action, raw_player_text="Search the desk.", list_scene_ids=lambda: [])
    _assert_normalized_engine_result(resolution, "investigate", resolved_transition=False)
    assert resolution["action_id"] == "inv-desk"


def test_discover_clue_engine_result_map_fragment_interactable():
    """discover_clue (investigate on interactable) returns normalized engine result with clue fields."""
    scene = {
        "scene": {
            "id": "test",
            "discoverable_clues": [{"id": "map-clue", "text": "A torn map fragment"}],
            "interactables": [{"id": "maps", "type": "investigate", "reveals_clue": "map-clue"}],
        }
    }
    action = normalize_scene_action({"id": "inv-maps", "label": "Investigate the maps", "type": "investigate", "prompt": "I investigate the maps"})
    resolution = resolve_exploration_action(scene, {}, {}, action, raw_player_text="I investigate the maps", list_scene_ids=lambda: [])
    _assert_normalized_engine_result(resolution, "discover_clue", resolved_transition=False, success=True)
    assert resolution["clue_id"] == "map-clue"
    assert resolution["clue_text"] == "A torn map fragment"
    assert resolution["discovered_clues"] == ["A torn map fragment"]
    assert resolution["state_changes"].get("clue_revealed") is True
    assert resolution.get("interactable_id") == "maps"


def test_scene_transition_engine_result_north_room_exit():
    """scene_transition with known target returns normalized engine result."""
    scene = {"scene": {"id": "gate", "exits": [{"label": "North", "target_scene_id": "north_room"}]}}
    action = normalize_scene_action({"id": "go-north", "label": "Go north", "type": "scene_transition", "targetSceneId": "north_room", "prompt": "Go north"})
    resolution = resolve_exploration_action(scene, {}, {}, action, list_scene_ids=lambda: ["gate", "north_room"])
    _assert_normalized_engine_result(resolution, "scene_transition", resolved_transition=True, success=True)
    assert resolution["target_scene_id"] == "north_room"
    assert resolution["state_changes"].get("scene_changed") is True


def test_custom_engine_result_mystery_action_id():
    """Unknown/custom actions still return a valid normalized engine result."""
    scene = {"scene": {"id": "test"}}
    action = normalize_scene_action({"id": "mystery", "label": "Do something odd", "type": "custom", "prompt": "Do something odd"})
    resolution = resolve_exploration_action(scene, {}, {}, action, list_scene_ids=lambda: [])
    _assert_normalized_engine_result(resolution, "custom")
    assert resolution["action_id"] == "mystery"
    assert resolution["resolved_transition"] is False
    assert resolution["success"] is None


def test_observe_investigate_interact_produce_structured_resolution():
    """Resolver returns structured resolution payloads for observe, investigate, interact."""
    scene = {"scene": {"id": "test", "location": "Here"}}
    session = {}
    world = {}

    for action_type, label in [("observe", "Observe the area"), ("investigate", "Investigate: the desk"), ("interact", "Gauge the mood")]:
        action = normalize_scene_action({"id": "a", "label": label, "type": action_type, "prompt": label})
        resolution = resolve_exploration_action(scene, session, world, action, raw_player_text=label, list_scene_ids=lambda: [])
        assert resolution["kind"] == action_type
        assert "hint" in resolution
        assert resolution["label"] == label
        assert resolution["prompt"] == label
        assert resolution.get("resolved_transition") is False


def test_observe_returns_normalized_engine_result():
    """Observe action returns standardized engine result schema."""
    scene = {"scene": {"id": "test", "location": "Here"}}
    session = {}
    world = {}
    action = normalize_scene_action({"id": "observe-area", "label": "Observe", "type": "observe", "prompt": "I look around."})
    resolution = resolve_exploration_action(scene, session, world, action, list_scene_ids=lambda: [])
    _assert_normalized_engine_result(resolution, "observe")
    assert resolution["action_id"] == "observe-area"
    assert resolution["resolved_transition"] is False
    assert resolution.get("success") is None


def test_investigate_returns_normalized_engine_result():
    """Investigate action returns standardized engine result schema."""
    scene = {"scene": {"id": "test", "location": "Here", "interactables": []}}
    session = {}
    world = {}
    action = normalize_scene_action({"id": "inv-desk", "label": "Investigate the desk", "type": "investigate", "prompt": "I search the desk."})
    resolution = resolve_exploration_action(scene, session, world, action, list_scene_ids=lambda: [])
    _assert_normalized_engine_result(resolution, "investigate")
    assert resolution["action_id"] == "inv-desk"
    assert resolution["resolved_transition"] is False


def test_discover_clue_returns_normalized_engine_result():
    """Discover_clue (interactable match) returns standardized engine result schema."""
    scene = {
        "scene": {
            "id": "test",
            "location": "Here",
            "interactables": [
                {"id": "maps", "type": "investigate", "reveals_clue": "clue_maps", "world_updates_on_discover": {"set_flags": {"found_maps": True}}}
            ],
            "discoverable_clues": [{"id": "clue_maps", "text": "The maps show a hidden route."}],
        }
    }
    session = {}
    world = {}
    action = normalize_scene_action({"id": "inv-maps", "label": "Investigate the maps", "type": "investigate", "prompt": "I investigate the maps"})
    resolution = resolve_exploration_action(scene, session, world, action, list_scene_ids=lambda: [])
    _assert_normalized_engine_result(resolution, "discover_clue")
    assert resolution["clue_id"] == "clue_maps"
    assert resolution["clue_text"] == "The maps show a hidden route."
    assert resolution["discovered_clues"] == ["The maps show a hidden route."]
    assert resolution["success"] is True
    assert resolution["state_changes"]["clue_revealed"] is True
    assert resolution["state_changes"]["interactable_id"] == "maps"
    assert resolution["world_updates"]["set_flags"]["found_maps"] is True


def test_scene_transition_returns_normalized_engine_result():
    """Scene transition returns standardized engine result schema."""
    scene = {"scene": {"id": "gate", "exits": [{"label": "Market", "target_scene_id": "market"}]}}
    session = {}
    world = {}
    action = normalize_scene_action({"id": "go-market", "label": "Go to Market", "type": "scene_transition", "targetSceneId": "market", "prompt": "I go to the market."})
    resolution = resolve_exploration_action(scene, session, world, action, list_scene_ids=lambda: ["gate", "market"])
    _assert_normalized_engine_result(resolution, "scene_transition")
    assert resolution["resolved_transition"] is True
    assert resolution["target_scene_id"] == "market"
    assert resolution["success"] is True
    assert resolution["state_changes"]["scene_changed"] is True


def test_custom_unknown_action_returns_normalized_engine_result():
    """Unknown/custom action type returns valid normalized engine result."""
    scene = {"scene": {"id": "test"}}
    session = {}
    world = {}
    action = normalize_scene_action({"id": "custom-act", "label": "Do something odd", "type": "custom", "prompt": "I wave my hands."})
    resolution = resolve_exploration_action(scene, session, world, action, list_scene_ids=lambda: [])
    _assert_normalized_engine_result(resolution, "custom")
    assert resolution["action_id"] == "custom-act"
    assert resolution["resolved_transition"] is False


def test_repeated_exploration_action_updates_anti_stall_runtime(tmp_path, monkeypatch):
    """Repeating the same exploration action in the same scene updates repeated_action_count and last_exploration_action_key."""
    _seed_scenes_and_session(tmp_path, monkeypatch, active="scene_a")

    def fake_gpt(messages):
        return {"player_facing_text": "You look around.", "tags": [], "scene_update": None, "activate_scene_id": None, "new_scene_draft": None, "world_updates": None, "suggested_action": None, "debug_notes": ""}

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", fake_gpt)
        client = TestClient(app)
        payload = {
            "action_type": "exploration",
            "intent": "Observe",
            "exploration_action": {"id": "observe-area", "label": "Observe the area", "type": "observe", "prompt": "I look around."},
        }
        client.post("/api/action", json=payload)
        client.post("/api/action", json=payload)

    session = storage.load_session()
    rt = get_scene_runtime(session, "scene_a")
    assert rt.get("last_exploration_action_key") == "observe-area"
    assert rt.get("repeated_action_count") == 2
    assert rt.get("last_resolution_kind") == "observe"


def test_combat_actions_still_routed_unchanged(tmp_path, monkeypatch):
    """roll_initiative is still routed to combat logic; unknown action_type returns Unsupported."""
    _seed_scenes_and_session(tmp_path, monkeypatch)

    client = TestClient(app)
    r = client.post("/api/action", json={"action_type": "roll_initiative"})
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert data.get("gm_output", {}).get("player_facing_text") == "Initiative is rolled."

    r2 = client.post("/api/action", json={"action_type": "unknown_type"})
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2.get("ok") is False
    assert "Unsupported action type" in str(data2.get("error", ""))


def test_parse_go_north_travel_north_gate_exit_in_label():
    """'go north' parses into a travel action."""
    scene = {"scene": {"id": "gate", "exits": [{"label": "North gate", "target_scene_id": "north_area"}]}}
    parsed = parse_exploration_intent("go north", scene)
    assert parsed is not None
    assert parsed.get("type") in ("travel", "scene_transition")
    assert "go" in parsed.get("label", "").lower() or "north" in parsed.get("label", "").lower()


def test_parse_investigate_notice_board_gate_no_exits():
    """'investigate the notice board' parses into investigate action."""
    scene = {"scene": {"id": "gate", "exits": []}}
    parsed = parse_exploration_intent("investigate the notice board", scene)
    assert parsed is not None
    assert parsed.get("type") == "investigate"


@pytest.mark.parametrize(
    "scene,phrase",
    [
        ({"scene": {"id": "gate"}}, "I attack the guard with my sword"),
        ({"scene": {"id": "gate"}}, "Cast magic missile at the orc"),
        ({"scene": {"id": "gate"}}, "I attack the guard"),
        ({"scene": {"id": "here", "exits": []}}, "I attack the guard"),
        ({"scene": {"id": "here", "exits": []}}, "Cast magic missile at the orc"),
    ],
)
def test_parse_exploration_intent_unrelated_phrases_return_none(scene, phrase):
    """Combat and unrelated chat do not parse as exploration."""
    assert parse_exploration_intent(phrase, scene) is None


def test_chat_investigate_desk_resolution_kind_in_gpt_messages(tmp_path, monkeypatch):
    """Chat with 'investigate the desk' routes through exploration pipeline."""
    _seed_scenes_and_session(tmp_path, monkeypatch, active="scene_a")
    resolution_seen = []

    def capture_gpt(messages):
        import json
        for m in messages:
            if m.get("role") == "user" and "content" in m:
                try:
                    payload = json.loads(m["content"])
                    res = payload.get("mechanical_resolution") or payload.get("mechanical_resolution")
                    if res and isinstance(res, dict) and res.get("kind"):
                        resolution_seen.append(res.get("kind"))
                except Exception:
                    pass
        return {"player_facing_text": "You find nothing.", "tags": [], "scene_update": None, "activate_scene_id": None, "new_scene_draft": None, "world_updates": None, "suggested_action": None, "debug_notes": ""}

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", capture_gpt)
        client = TestClient(app)
        r = client.post("/api/chat", json={"text": "investigate the desk"})
    assert r.status_code == 200
    assert r.json().get("ok") is True
    assert "investigate" in resolution_seen


def test_chat_quarterstaff_attack_mechanical_resolution_absent(tmp_path, monkeypatch):
    """Chat with unrelated text goes to GPT without exploration resolution."""
    _seed_scenes_and_session(tmp_path, monkeypatch, active="scene_a")
    gpt_called_with_none_resolution = []

    def capture_gpt(messages):
        import json
        for m in messages:
            if m.get("role") == "user" and "content" in m:
                try:
                    payload = json.loads(m["content"])
                    res = payload.get("mechanical_resolution")
                    gpt_called_with_none_resolution.append(res is None)
                except Exception:
                    pass
        return {"player_facing_text": "The guard frowns.", "tags": [], "scene_update": None, "activate_scene_id": None, "new_scene_draft": None, "world_updates": None, "suggested_action": None, "debug_notes": ""}

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", capture_gpt)
        client = TestClient(app)
        r = client.post("/api/chat", json={"text": "I attack the guard with my quarterstaff"})
    assert r.status_code == 200
    assert r.json().get("ok") is True
    assert any(gpt_called_with_none_resolution)


def test_parse_go_north_label_and_prompt_match_raw_text():
    """Free text 'go north' parses into a travel action."""
    scene = {"scene": {"id": "gate", "exits": [{"label": "North gate", "target_scene_id": "north_area"}]}}
    parsed = parse_exploration_intent("go north", scene)
    assert parsed is not None
    assert parsed.get("type") in ("travel", "scene_transition")
    assert "go north" in (parsed.get("label") or "").lower()
    assert parsed.get("prompt") == "go north"


def test_parse_investigate_label_contains_investigate_word():
    """Free text 'investigate the notice board' parses into investigate action."""
    scene = {"scene": {"id": "gate"}}
    parsed = parse_exploration_intent("investigate the notice board", scene)
    assert parsed is not None
    assert parsed.get("type") == "investigate"
    assert "investigate" in (parsed.get("label") or "").lower()


def test_chat_observe_area_resolution_kwarg_to_build_messages(tmp_path, monkeypatch):
    """When /api/chat receives exploration-style text, it routes through exploration pipeline."""
    _seed_scenes_and_session(tmp_path, monkeypatch, active="scene_a")
    build_messages_called_with_resolution = []

    def capture_build_messages(*args, **kwargs):
        # api passes resolution as the 9th positional arg to build_messages
        res = args[8] if len(args) > 8 else kwargs.get("resolution")
        build_messages_called_with_resolution.append(res)
        from game.gm import build_messages as _orig
        return _orig(*args, **kwargs)

    def fake_gpt(messages):
        return {"player_facing_text": "You look around.", "tags": [], "scene_update": None, "activate_scene_id": None, "new_scene_draft": None, "world_updates": None, "suggested_action": None, "debug_notes": ""}

    with monkeypatch.context() as m:
        m.setattr("game.api.build_messages", capture_build_messages)
        m.setattr("game.api.call_gpt", fake_gpt)
        client = TestClient(app)
        r = client.post("/api/chat", json={"text": "observe the area"})
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert len(build_messages_called_with_resolution) >= 1
    resolution = build_messages_called_with_resolution[-1]
    assert resolution is not None
    assert resolution.get("kind") == "observe"


def test_chat_captain_dialog_build_messages_not_exploration_kind(tmp_path, monkeypatch):
    """When /api/chat receives non-exploration text, it must not route as core exploration (observe/investigate/…)."""
    _seed_scenes_and_session(tmp_path, monkeypatch)
    build_messages_called_with_resolution = []

    def capture_build_messages(*args, **kwargs):
        res = args[8] if len(args) > 8 else kwargs.get("resolution")
        build_messages_called_with_resolution.append(res)

    def fake_gpt(messages):
        return {"player_facing_text": "The guard glares at you.", "tags": [], "scene_update": None, "activate_scene_id": None, "new_scene_draft": None, "world_updates": None, "suggested_action": None, "debug_notes": ""}

    with monkeypatch.context() as m:
        m.setattr("game.api.build_messages", capture_build_messages)
        m.setattr("game.api.call_gpt", fake_gpt)
        client = TestClient(app)
        r = client.post("/api/chat", json={"text": "I demand to speak with your captain"})
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert len(build_messages_called_with_resolution) >= 1
    resolution = build_messages_called_with_resolution[-1]
    exploration_kinds = ("observe", "investigate", "interact", "scene_transition", "travel", "discover_clue")
    assert resolution is None or (
        isinstance(resolution, dict) and resolution.get("kind") not in exploration_kinds
    )


def test_parse_go_north_with_exit_label_go_north():
    """Free text 'go north' parses into a travel/scene_transition action."""
    from game.exploration import parse_exploration_intent
    scene = {"scene": {"id": "gate", "exits": [{"label": "Go north", "target_scene_id": "north_area"}]}}
    parsed = parse_exploration_intent("go north", scene)
    assert parsed is not None
    assert parsed["type"] in ("travel", "scene_transition")
    assert "north" in parsed["label"].lower() or parsed["label"] == "go north"


def test_parse_investigate_notice_board_in_label_local_import():
    """Free text 'investigate the notice board' parses into investigate action."""
    from game.exploration import parse_exploration_intent
    scene = {"scene": {"id": "gate", "exits": []}}
    parsed = parse_exploration_intent("investigate the notice board", scene)
    assert parsed is not None
    assert parsed["type"] == "investigate"
    assert "notice board" in parsed["label"].lower()


def test_chat_sword_attack_calls_gpt_keeps_active_scene(tmp_path, monkeypatch):
    """Unrelated chat text (e.g. combat-like) does not get parsed as exploration; goes to GPT normally."""
    _seed_scenes_and_session(tmp_path, monkeypatch)
    call_gpt_called = []

    def capture_call(messages):
        call_gpt_called.append(True)
        return {"player_facing_text": "You strike!", "tags": [], "scene_update": None, "activate_scene_id": None, "new_scene_draft": None, "world_updates": None, "suggested_action": None, "debug_notes": ""}

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", capture_call)
        client = TestClient(app)
        r = client.post("/api/chat", json={"text": "I attack the guard with my sword."})
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert call_gpt_called
    assert data.get("session", {}).get("active_scene_id") == "scene_a"


def test_chat_observe_area_gm_build_messages_stub_receives_observe_resolution(tmp_path, monkeypatch):
    """Chat text 'observe the area' parses and routes through exploration pipeline."""
    _seed_scenes_and_session(tmp_path, monkeypatch)
    build_messages_resolution = []

    def capture_build(*args, **kwargs):
        res = args[8] if len(args) > 8 else kwargs.get("resolution")
        build_messages_resolution.append(res)
        return [{"role": "system", "content": "x"}, {"role": "user", "content": "{}"}]

    def fake_gpt(messages):
        return {"player_facing_text": "You look around.", "tags": [], "scene_update": None, "activate_scene_id": None, "new_scene_draft": None, "world_updates": None, "suggested_action": None, "debug_notes": ""}

    with monkeypatch.context() as m:
        # api holds its own reference to build_messages; patch game.api, not game.gm
        m.setattr("game.api.build_messages", capture_build)
        m.setattr("game.api.call_gpt", fake_gpt)
        client = TestClient(app)
        r = client.post("/api/chat", json={"text": "observe the area"})
    assert r.status_code == 200
    assert build_messages_resolution
    assert build_messages_resolution[0] is not None
    assert build_messages_resolution[0].get("kind") == "observe"


def test_parse_go_north_no_exits_normalizes_label_and_prompt():
    """parse_exploration_intent detects 'go north' as a travel action."""
    from game.exploration import parse_exploration_intent

    scene = {"scene": {"id": "here", "exits": []}}
    parsed = parse_exploration_intent("go north", scene)
    assert parsed is not None
    assert parsed.get("type") in ("travel", "scene_transition")
    assert parsed.get("label") == "go north"
    assert parsed.get("prompt") == "go north"


def test_chat_sword_attack_gpt_invoked(tmp_path, monkeypatch):
    """Unrelated chat (e.g. combat/attack) is not parsed as exploration and goes to GPT as before."""
    _seed_scenes_and_session(tmp_path, monkeypatch)
    call_gpt_invoked = []

    def capture(_messages):
        call_gpt_invoked.append(True)
        return {"player_facing_text": "The guard attacks!", "tags": [], "scene_update": None, "activate_scene_id": None, "new_scene_draft": None, "world_updates": None, "suggested_action": None, "debug_notes": ""}

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", capture)
        client = TestClient(app)
        r = client.post("/api/chat", json={"text": "I attack the guard with my sword."})
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    assert call_gpt_invoked


def test_chat_exploration_parsed_routes_through_exploration(tmp_path, monkeypatch):
    """Chat with exploration intent (e.g. 'observe the area') is parsed and routed through exploration pipeline."""
    _seed_scenes_and_session(tmp_path, monkeypatch)
    payloads_received = []

    def capture(messages):
        import json
        for m in messages:
            if m.get("role") == "user" and "content" in m:
                try:
                    p = json.loads(m["content"])
                    payloads_received.append(p)
                except Exception:
                    pass
        return {"player_facing_text": "You take in the scene.", "tags": [], "scene_update": None, "activate_scene_id": None, "new_scene_draft": None, "world_updates": None, "suggested_action": None, "debug_notes": ""}

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", capture)
        client = TestClient(app)
        r = client.post("/api/chat", json={"text": "observe the area"})
    assert r.status_code == 200
    assert payloads_received
    last_payload = payloads_received[-1]
    assert "resolved_exploration_action" in last_payload
    assert last_payload.get("resolution_kind") == "observe"


def test_parse_go_north_here_scene_north_room_exit():
    """'go north' parses into a travel action."""
    scene = {"scene": {"id": "here", "exits": [{"label": "North", "target_scene_id": "north_room"}]}}
    parsed = parse_exploration_intent("go north", scene)
    assert parsed is not None
    assert parsed["type"] in ("travel", "scene_transition")
    assert "go north" in parsed.get("label", "").lower() or "north" in parsed.get("label", "").lower()


def test_parse_investigate_notice_board_gate_empty_exits_investigate_in_label():
    """'investigate the notice board' parses into investigate action."""
    scene = {"scene": {"id": "gate", "exits": []}}
    parsed = parse_exploration_intent("investigate the notice board", scene)
    assert parsed is not None
    assert parsed["type"] == "investigate"
    assert "investigate" in parsed.get("label", "").lower()


def test_chat_investigate_desk_logged_resolution_kind_investigate(tmp_path, monkeypatch):
    """When /api/chat receives 'investigate the desk', it routes through exploration pipeline."""
    _seed_scenes_and_session(tmp_path, monkeypatch, active="scene_a")

    def fake_gpt(messages):
        return {"player_facing_text": "You find nothing.", "tags": [], "scene_update": None, "activate_scene_id": None, "new_scene_draft": None, "world_updates": None, "suggested_action": None, "debug_notes": ""}

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", fake_gpt)
        client = TestClient(app)
        r = client.post("/api/chat", json={"text": "investigate the desk"})
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    # Log should contain exploration resolution (routed via exploration)
    log = storage.load_log()
    assert len(log) >= 1
    last = log[-1]
    res = last.get("resolution", {})
    assert res.get("kind") == "investigate"


def test_chat_peaceful_intent_log_world_tick_not_exploration_kind(tmp_path, monkeypatch):
    """Unrelated chat text does not route through exploration; uses normal GPT flow."""
    _seed_scenes_and_session(tmp_path, monkeypatch, active="scene_a")

    def fake_gpt(messages):
        return {"player_facing_text": "The guard eyes you warily.", "tags": [], "scene_update": None, "activate_scene_id": None, "new_scene_draft": None, "world_updates": None, "suggested_action": None, "debug_notes": ""}

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", fake_gpt)
        client = TestClient(app)
        r = client.post("/api/chat", json={"text": "I tell the guard I mean no harm"})
    assert r.status_code == 200
    data = r.json()
    assert data.get("ok") is True
    # Resolution should be world_tick_events only (fallback), not exploration kind
    log = storage.load_log()
    assert len(log) >= 1
    last = log[-1]
    res = last.get("resolution", {})
    assert res.get("kind") is None
    assert "world_tick_events" in res


def test_parse_go_north_label_or_prompt_contains_go_north_phrase():
    """Free text 'go north' parses into a travel or scene_transition action."""
    scene = {"scene": {"id": "gate", "exits": [{"label": "North", "target_scene_id": "north_area"}]}}
    parsed = parse_exploration_intent("go north", scene)
    assert parsed is not None
    assert parsed["type"] in ("travel", "scene_transition")
    assert "go north" in (parsed.get("label") or "").lower() or "go north" in (parsed.get("prompt") or "").lower()


def test_parse_investigate_notice_board_gate_minimal_scene_investigate_in_label():
    """Free text 'investigate the notice board' parses into investigate action."""
    scene = {"scene": {"id": "gate"}}
    parsed = parse_exploration_intent("investigate the notice board", scene)
    assert parsed is not None
    assert parsed["type"] == "investigate"
    assert "investigate" in (parsed.get("label") or "").lower()


def test_chat_attack_mechanical_resolution_kind_not_exploration_set(tmp_path, monkeypatch):
    """Chat with non-exploration text (e.g. combat/rp) goes to GPT without exploration routing."""
    _seed_scenes_and_session(tmp_path, monkeypatch)
    result = {"routed_exploration": False}

    def capture_was_exploration(messages):
        import json
        for m in messages:
            if m.get("role") == "user" and "content" in m:
                try:
                    payload = json.loads(m["content"])
                    res = payload.get("mechanical_resolution")
                    result["routed_exploration"] = (
                        isinstance(res, dict) and res.get("kind") in ("observe", "investigate", "interact", "scene_transition", "travel", "custom")
                    )
                except Exception:
                    pass
        return {"player_facing_text": "The guard attacks.", "tags": [], "scene_update": None, "activate_scene_id": None, "new_scene_draft": None, "world_updates": None, "suggested_action": None, "debug_notes": ""}

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", capture_was_exploration)
        client = TestClient(app)
        r = client.post("/api/chat", json={"text": "I attack the guard with my sword."})
    assert r.status_code == 200
    assert r.json().get("ok") is True
    assert result["routed_exploration"] is False


def test_chat_investigate_notice_board_mechanical_resolution_investigate(tmp_path, monkeypatch):
    """Chat with 'investigate the notice board' routes through exploration pipeline."""
    _seed_scenes_and_session(tmp_path, monkeypatch)

    def capture_resolution(messages):
        import json
        for m in messages:
            if m.get("role") == "user" and "content" in m:
                try:
                    payload = json.loads(m["content"])
                    res = payload.get("mechanical_resolution")
                    if res and isinstance(res, dict):
                        capture_resolution.resolution_kind = res.get("kind")
                        capture_resolution.had_resolved_action = "resolved_exploration_action" in payload
                except Exception:
                    pass
        return {"player_facing_text": "You find a clue.", "tags": [], "scene_update": None, "activate_scene_id": None, "new_scene_draft": None, "world_updates": None, "suggested_action": None, "debug_notes": ""}

    capture_resolution.resolution_kind = None
    capture_resolution.had_resolved_action = False

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", capture_resolution)
        client = TestClient(app)
        r = client.post("/api/chat", json={"text": "investigate the notice board"})
    assert r.status_code == 200
    assert r.json().get("ok") is True
    assert capture_resolution.resolution_kind == "investigate"
    assert capture_resolution.had_resolved_action is True
