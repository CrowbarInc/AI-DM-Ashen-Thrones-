"""PR-AM: explicit grounded world action overrides stale social capture.

Synthetic fixtures use harbor-wharf vocabulary. Frontier Gate / notice-board
cases are calibration regression only.
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
    inspect as inspect_interaction_context,
    rebuild_active_scene_entities,
    resolve_directed_social_entry,
    set_social_target,
)
from game.interaction_routing import choose_interaction_route, is_world_action
from game.leads import SESSION_LEAD_REGISTRY_KEY
from game.referenced_surface import (
    AUTHORITY_AUTHORED_INTERACTABLE,
    AUTHORITY_AUTHORED_VISIBLE_FEATURE,
    AUTHORITY_UNSUPPORTED,
    classify_referenced_surface,
)
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _patch_storage

CALIBRATION_ENGINE_TERMS = (
    "notice_board",
    "tavern_runner",
    "stew",
    "roster_board",
    "guard_captain",
    "Captain Thoran",
    "frontier_gate",
    "Cinderwatch",
    "patrol",
    "old_milestone",
)
SILT_FACT = "The silt line rose two marks after the last spring tide."
PILING_FACT = "A salt-stained piling leans from the low tide line."
WARDEN_TOPIC = "The inner lamps are trimmed before the second flood."
CLERK_TOPIC = "Berth three keeps a chit under the weigh-hook."
T13_TEXT = "I glance back at the notice board after that."


def _wharf_scene() -> dict:
    return {
        "scene": {
            "id": "harbor_wharf",
            "location": "Harbor Wharf",
            "summary": "A wet quay, a tide marker, and a brass plaque.",
            "visible_facts": [
                PILING_FACT,
                "Lamp-oil smoke hangs over the quay.",
            ],
            "hidden_facts": [],
            "discoverable_clues": [{"id": "plaque_silt", "text": SILT_FACT}],
            "addressables": [
                {
                    "id": "lamp_warden",
                    "name": "Lamp Warden",
                    "scene_id": "harbor_wharf",
                    "kind": "npc",
                    "addressable": True,
                },
                {
                    "id": "tide_clerk",
                    "name": "Tide Clerk",
                    "scene_id": "harbor_wharf",
                    "kind": "npc",
                    "addressable": True,
                },
            ],
            "interactables": [
                {
                    "id": "tide_marker",
                    "label": "Tide marker",
                    "aliases": ["marker", "tide post"],
                    "type": "investigate",
                },
                {
                    "id": "brass_plaque",
                    "label": "Brass plaque",
                    "aliases": ["plaque", "inscription"],
                    "type": "read",
                    "reveals_clue": "plaque_silt",
                },
            ],
            "exits": [
                {"label": "Climb the quay stair", "target_scene_id": "lantern_cut"},
            ],
            "enemies": [],
            "actions": [],
        }
    }


def _wharf_world() -> dict:
    world = default_world()
    world["npcs"] = [
        {
            "id": "lamp_warden",
            "name": "Lamp Warden",
            "location": "harbor_wharf",
            "topics": [{"id": "silt_schedule", "text": WARDEN_TOPIC}],
        },
        {
            "id": "tide_clerk",
            "name": "Tide Clerk",
            "location": "harbor_wharf",
            "topics": [{"id": "berth_chit", "text": CLERK_TOPIC}],
        },
    ]
    return world


def _lantern_cut_scene() -> dict:
    return {
        "scene": {
            "id": "lantern_cut",
            "location": "Lantern Cut",
            "summary": "A narrow stair above the quay.",
            "visible_facts": ["A cut stair climbs away from the water."],
            "hidden_facts": [],
            "discoverable_clues": [],
            "interactables": [],
            "exits": [{"label": "Return to the quay", "target_scene_id": "harbor_wharf"}],
            "enemies": [],
            "actions": [],
        }
    }


def _engaged_wharf(npc_id: str = "lamp_warden") -> tuple[dict, dict, dict]:
    scene = _wharf_scene()
    world = _wharf_world()
    session = default_session()
    session["active_scene_id"] = "harbor_wharf"
    session["visited_scene_ids"] = ["harbor_wharf"]
    rebuild_active_scene_entities(session, world, "harbor_wharf", scene_envelope=scene)
    set_social_target(session, npc_id)
    return session, scene, world


def _seed_wharf_http(tmp_path, monkeypatch, *, npc_id: str = "lamp_warden"):
    _patch_storage(tmp_path, monkeypatch)
    scene = _wharf_scene()
    world = _wharf_world()
    storage._save_json(storage.scene_path("harbor_wharf"), scene)
    storage._save_json(storage.scene_path("lantern_cut"), _lantern_cut_scene())
    storage._save_json(storage.scene_path("frontier_gate"), default_scene("frontier_gate"))
    storage._save_json(storage.WORLD_PATH, world)
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    session = default_session()
    session["active_scene_id"] = "harbor_wharf"
    session["visited_scene_ids"] = ["harbor_wharf"]
    rebuild_active_scene_entities(session, world, "harbor_wharf", scene_envelope=scene)
    set_social_target(session, npc_id)
    storage.save_session(session)
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")
    return session, scene, world


def _chat(monkeypatch, text: str, gm_text: str):
    monkeypatch.setattr("game.api.call_gpt", lambda _messages: _gm_response(gm_text))
    client = TestClient(app)
    resp = client.post("/api/chat", json={"text": text})
    assert resp.status_code == 200
    return resp.json()


def _facing(data: dict) -> str:
    return str((data.get("gm_output") or {}).get("player_facing_text") or "")


def _lead_ids(session: dict | None = None) -> set[str]:
    sess = session if isinstance(session, dict) else storage.load_session()
    registry = sess.get(SESSION_LEAD_REGISTRY_KEY) or {}
    if isinstance(registry, dict):
        return {str(key) for key in registry.keys()}
    return set()


def _ctx(data: dict) -> dict:
    return inspect_interaction_context(data.get("session") or {})


def test_general_inspect_overrides_bound_interlocutor():
    session, scene, world = _engaged_wharf()
    text = "I inspect the tide marker."
    parsed = parse_freeform_to_action(text, scene, session=session, world=world)
    assert parsed is not None
    assert parsed.get("type") == "investigate"
    assert parsed.get("target_id") == "tide_marker"
    entry = resolve_directed_social_entry(
        session=session, scene=scene, world=world, segmented_turn=None, raw_text=text
    )
    assert entry.get("should_route_social") is False
    assert choose_interaction_route(text, scene=scene, session=session, world=world) != "dialogue"
    recovered = recover_actionable_explicit_world_action(text, scene, session=session, world=world)
    assert recovered is not None
    assert recovered.get("type") == "investigate"
    assert recovered.get("target_id") == "tide_marker"


def test_general_read_overrides_bound_interlocutor_and_keeps_contents():
    session, scene, world = _engaged_wharf()
    text = "I read the brass plaque."
    classified = classify_referenced_surface(text, scene, world=world)
    assert classified["authority"] == AUTHORITY_AUTHORED_INTERACTABLE
    parsed = parse_freeform_to_action(text, scene, session=session, world=world)
    assert parsed is not None
    assert parsed.get("type") == "investigate"
    assert parsed.get("target_id") == "brass_plaque"
    entry = resolve_directed_social_entry(
        session=session, scene=scene, world=world, segmented_turn=None, raw_text=text
    )
    assert entry.get("should_route_social") is False


def test_general_visible_non_interactable_is_not_social_probe():
    session, scene, world = _engaged_wharf()
    text = "I examine the salt-stained piling."
    classified = classify_referenced_surface(text, scene, world=world)
    assert classified["authority"] == AUTHORITY_AUTHORED_VISIBLE_FEATURE
    parsed = parse_freeform_to_action(text, scene, session=session, world=world)
    assert parsed is not None
    assert parsed.get("type") == "investigate"
    entry = resolve_directed_social_entry(
        session=session, scene=scene, world=world, segmented_turn=None, raw_text=text
    )
    assert entry.get("should_route_social") is False


def test_general_movement_still_overrides_social_lock():
    session, scene, world = _engaged_wharf()
    text = "I'll climb the quay stair."
    parsed = parse_freeform_to_action(text, scene, session=session, world=world)
    assert parsed is not None
    assert parsed.get("type") in {"scene_transition", "travel"}
    assert (parsed.get("target_scene_id") or parsed.get("targetSceneId")) == "lantern_cut"
    entry = resolve_directed_social_entry(
        session=session, scene=scene, world=world, segmented_turn=None, raw_text=text
    )
    assert entry.get("should_route_social") is False


def test_general_ambiguous_why_stays_social():
    session, scene, world = _engaged_wharf()
    text = "Why?"
    assert looks_like_explicit_world_object_action(text) is False
    assert recover_actionable_explicit_world_action(text, scene, session=session, world=world) is None
    assert choose_interaction_route(text, scene=scene, session=session, world=world) == "dialogue"
    entry = resolve_directed_social_entry(
        session=session, scene=scene, world=world, segmented_turn=None, raw_text=text
    )
    assert entry.get("should_route_social") is True
    assert entry.get("target_actor_id") == "lamp_warden"


def test_general_explicit_same_npc_question_stays_social():
    session, scene, world = _engaged_wharf()
    text = "When are the inner lamps trimmed?"
    assert looks_like_explicit_world_object_action(text) is False
    assert choose_interaction_route(text, scene=scene, session=session, world=world) == "dialogue"
    entry = resolve_directed_social_entry(
        session=session, scene=scene, world=world, segmented_turn=None, raw_text=text
    )
    assert entry.get("should_route_social") is True
    assert entry.get("target_actor_id") == "lamp_warden"


def test_general_explicit_other_npc_address_is_not_stolen_by_stale_bind():
    session, scene, world = _engaged_wharf("lamp_warden")
    text = 'I turn to the Tide Clerk. "Where is the berth chit kept?"'
    entry = resolve_directed_social_entry(
        session=session, scene=scene, world=world, segmented_turn=None, raw_text=text
    )
    assert entry.get("should_route_social") is True
    assert entry.get("target_actor_id") == "tide_clerk"


def test_general_unsupported_object_is_not_social_and_not_instantiated():
    session, scene, world = _engaged_wharf()
    text = "I inspect the glass orrery."
    classified = classify_referenced_surface(text, scene, world=world)
    assert classified["authority"] == AUTHORITY_UNSUPPORTED
    parsed = parse_freeform_to_action(text, scene, session=session, world=world)
    assert parsed is not None
    assert parsed.get("type") == "investigate"
    assert parsed.get("target_id") != "lamp_warden"
    entry = resolve_directed_social_entry(
        session=session, scene=scene, world=world, segmented_turn=None, raw_text=text
    )
    assert entry.get("should_route_social") is False


def test_general_conversational_tail_does_not_grant_social_ownership():
    session, scene, world = _engaged_wharf()
    text = "I inspect the tide marker after that."
    parsed = parse_freeform_to_action(text, scene, session=session, world=world)
    assert parsed is not None
    assert parsed.get("type") == "investigate"
    assert parsed.get("target_id") == "tide_marker"
    entry = resolve_directed_social_entry(
        session=session, scene=scene, world=world, segmented_turn=None, raw_text=text
    )
    assert entry.get("should_route_social") is False
    assert is_world_action(text) is True


def test_glance_at_parses_as_targeted_investigate_not_untargeted_observe():
    session, scene, world = _engaged_wharf()
    text = "I glance back at the tide marker after that."
    parsed = parse_freeform_to_action(text, scene, session=session, world=world)
    assert parsed is not None
    assert parsed.get("type") == "investigate"
    assert parsed.get("target_id") == "tide_marker"
    assert looks_like_explicit_world_object_action(text) is True
    assert is_world_action(text) is True


def test_http_inspect_while_bound_is_not_social_probe(tmp_path, monkeypatch):
    _seed_wharf_http(tmp_path, monkeypatch)
    data = _chat(monkeypatch, "I inspect the tide marker.", "The warden keeps talking about the flood lamps.")
    res = data.get("resolution") or {}
    assert res.get("kind") == "investigate"
    assert res.get("kind") != "social_probe"
    assert "flood lamps" not in _facing(data).lower() or res.get("kind") == "investigate"
    ctx = _ctx(data)
    assert ctx.get("active_interaction_target_id") != "lamp_warden" or ctx.get("interaction_mode") != "social"


def test_http_read_while_bound_communicates_authored_contents(tmp_path, monkeypatch):
    _seed_wharf_http(tmp_path, monkeypatch)
    data = _chat(monkeypatch, "I read the brass plaque.", "The warden mutters about trimmed lamps.")
    res = data.get("resolution") or {}
    assert res.get("kind") in {"investigate", "discover_clue", "already_searched"}
    assert res.get("kind") != "social_probe"
    low = _facing(data).lower()
    assert "silt" in low or "two marks" in low or "spring tide" in low
    assert "trimmed" not in low
    assert "plaque_silt" in _lead_ids(data.get("session") or {}) or SILT_FACT.lower() in low


def test_http_class_b_visible_feature_is_not_swallowed_by_social(tmp_path, monkeypatch):
    _seed_wharf_http(tmp_path, monkeypatch)
    data = _chat(monkeypatch, "I examine the salt-stained piling.", WARDEN_TOPIC)
    res = data.get("resolution") or {}
    assert res.get("kind") == "investigate"
    assert res.get("kind") != "social_probe"
    assert (res.get("metadata") or {}).get("referenced_surface_authority") == AUTHORITY_AUTHORED_VISIBLE_FEATURE
    low = _facing(data).lower()
    assert "second flood" not in low
    assert "piling" in low or "nothing further" in low or "closer" in low


def test_http_leave_while_bound_still_moves(tmp_path, monkeypatch):
    _seed_wharf_http(tmp_path, monkeypatch)
    data = _chat(monkeypatch, "I'll climb the quay stair.", WARDEN_TOPIC)
    res = data.get("resolution") or {}
    assert res.get("kind") == "scene_transition"
    assert data.get("session", {}).get("active_scene_id") == "lantern_cut"
    assert _ctx(data).get("active_interaction_target_id") in (None, "")


def test_http_why_stays_with_bound_speaker(tmp_path, monkeypatch):
    _seed_wharf_http(tmp_path, monkeypatch)
    data = _chat(monkeypatch, "Why?", f'Lamp Warden says, "{WARDEN_TOPIC}"')
    res = data.get("resolution") or {}
    assert res.get("kind") in {"question", "social_probe"}
    assert _ctx(data).get("active_interaction_target_id") == "lamp_warden"


def test_http_explicit_same_npc_question_stays_social(tmp_path, monkeypatch):
    _seed_wharf_http(tmp_path, monkeypatch)
    data = _chat(
        monkeypatch,
        "When are the inner lamps trimmed?",
        'Lamp Warden says, "I will not speak of that."',
    )
    res = data.get("resolution") or {}
    assert res.get("kind") in {"question", "social_probe"}
    assert _ctx(data).get("active_interaction_target_id") == "lamp_warden"
    assert "second flood" in _facing(data).lower()


def test_http_explicit_other_npc_is_not_stolen(tmp_path, monkeypatch):
    _seed_wharf_http(tmp_path, monkeypatch, npc_id="lamp_warden")
    data = _chat(
        monkeypatch,
        'I turn to the Tide Clerk. "Where is the berth chit kept?"',
        'Lamp Warden says, "Ask me about lamps."',
    )
    res = data.get("resolution") or {}
    assert res.get("kind") in {"question", "social_probe"}
    assert _ctx(data).get("active_interaction_target_id") == "tide_clerk"
    assert "weigh-hook" in _facing(data).lower()
    assert "ask me about lamps" not in _facing(data).lower()


def test_http_unsupported_object_fail_closed_not_social(tmp_path, monkeypatch):
    _seed_wharf_http(tmp_path, monkeypatch)
    data = _chat(monkeypatch, "I inspect the glass orrery.", WARDEN_TOPIC)
    res = data.get("resolution") or {}
    assert res.get("kind") == "investigate"
    assert res.get("kind") != "social_probe"
    assert (res.get("metadata") or {}).get("referenced_surface_authority") == AUTHORITY_UNSUPPORTED
    scene = storage.load_scene("harbor_wharf")
    ids = {
        str(item.get("id"))
        for item in ((scene.get("scene") or {}).get("interactables") or [])
        if isinstance(item, dict)
    }
    assert "glass_orrery" not in ids
    assert "orrery" not in _facing(data).lower() or "nothing here matches" in _facing(data).lower()
    assert not any("orrery" in item for item in _lead_ids(data.get("session") or {}))


def test_http_world_action_then_explicit_social_return(tmp_path, monkeypatch):
    _seed_wharf_http(tmp_path, monkeypatch)
    first = _chat(monkeypatch, "I inspect the tide marker.", "The marker is wet wood.")
    assert (first.get("resolution") or {}).get("kind") == "investigate"
    assert (first.get("resolution") or {}).get("kind") != "social_probe"
    second = _chat(
        monkeypatch,
        "I ask the Lamp Warden about the silt schedule.",
        'Lamp Warden says, "I will not speak of that."',
    )
    res = second.get("resolution") or {}
    assert res.get("kind") in {"question", "social_probe"}
    assert _ctx(second).get("active_interaction_target_id") == "lamp_warden"
    assert "second flood" in _facing(second).lower()


def test_http_stale_topic_does_not_mutate_world_action(tmp_path, monkeypatch):
    _seed_wharf_http(tmp_path, monkeypatch)
    first = _chat(
        monkeypatch,
        "When are the inner lamps trimmed?",
        'Lamp Warden says, "I will not speak of that."',
    )
    assert _ctx(first).get("active_interaction_target_id") == "lamp_warden"
    second = _chat(monkeypatch, "I inspect the tide marker after that.", WARDEN_TOPIC)
    res = second.get("resolution") or {}
    assert res.get("kind") == "investigate"
    assert res.get("kind") != "social_probe"
    assert "second flood" not in _facing(second).lower()


def test_http_t13_glance_back_at_notice_board_is_world_action(tmp_path, monkeypatch):
    _patch_storage(tmp_path, monkeypatch)
    from tests.test_stay_leave_social_lock_override import _gate_scene, _gate_world

    scene = _gate_scene()
    world = _gate_world()
    storage._save_json(storage.scene_path("frontier_gate"), scene)
    storage._save_json(storage.WORLD_PATH, world)
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    session["visited_scene_ids"] = ["frontier_gate"]
    rebuild_active_scene_entities(session, world, "frontier_gate", scene_envelope=scene)
    set_social_target(session, "tavern_runner")
    storage.save_session(session)
    data = _chat(monkeypatch, T13_TEXT, "Tavern Runner mutters, Word is, the missing patrol was last seen.")
    res = data.get("resolution") or {}
    assert res.get("kind") != "social_probe"
    assert res.get("kind") in {"investigate", "discover_clue", "already_searched"}
    assert "mutters" not in _facing(data).lower()
    assert "word is" not in _facing(data).lower()


def test_anti_overfitting_generic_helpers_have_no_calibration_special_case():
    import inspect as pyinspect

    from game import intent_parser

    helper_src = "\n".join(
        [
            pyinspect.getsource(intent_parser.looks_like_explicit_world_object_action),
            pyinspect.getsource(intent_parser.recover_actionable_explicit_world_action),
        ]
    )
    lowered = helper_src.lower()
    for term in CALIBRATION_ENGINE_TERMS:
        assert term.lower() not in lowered, f"new helper contains calibration term {term}"
    assert "after that" not in lowered
    assert "notice board" not in lowered
    assert "tavern runner" not in lowered
