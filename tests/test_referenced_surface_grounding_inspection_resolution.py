"""PR-AK: referenced surfaces are classified, not invented, before inspection resolves.

Synthetic fixtures use mill-loft vocabulary. Frontier Gate cases are
calibration regression only.
"""

from __future__ import annotations

import json
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
from game.exploration import resolve_exploration_action
from game.intent_parser import parse_freeform_to_action
from game.leads import SESSION_LEAD_REGISTRY_KEY
from game.perception_grounding import apply_perception_non_invention_to_gm
from game.referenced_surface import (
    AUTHORITY_AUTHORED_ABSTRACT_REFERENCE,
    AUTHORITY_AUTHORED_HIDDEN,
    AUTHORITY_AUTHORED_INTERACTABLE,
    AUTHORITY_AUTHORED_VISIBLE_FEATURE,
    AUTHORITY_UNSUPPORTED,
    classify_referenced_surface,
)
from game.scene_actions import normalize_scene_action
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _patch_storage

CALIBRATION_ENGINE_TERMS = (
    "roster",
    "roster_board",
    "guard_captain",
    "Captain Thoran",
    "frontier_gate",
    "Cinderwatch",
    "old_milestone",
    "patrol",
    "watch_command",
)
TARIFF_FACT = "Dock fees rise after the second horn."
SKYLIGHT_FACT = "A soot-stained skylight leaks pale noon light onto the loft floor."
HIDDEN_FACT = "A brass token is sealed under the grain hopper."
ABSTRACT_FACT = "I checked the shipping records this morning."
OBSERVE_STOCK = (
    "As you watch the scene, threadbare watchers and refugees cluster along the muddy gate line. "
    "A gate serjeant manages the crowd and keeps one eye on the roster board."
)
NARRATION_BELL = "A silver bell hangs nearby, catching the loft light."


def _mill_scene() -> dict:
    return {
        "scene": {
            "id": "mill_loft",
            "location": "Mill Loft",
            "summary": "A dry loft, a grain hopper, and a tariff slate.",
            "visible_facts": [
                SKYLIGHT_FACT,
                "Sacks of cracked maize lean against the hopper braces.",
                "A tariff slate hangs from a nail by the loft stair.",
            ],
            "hidden_facts": [HIDDEN_FACT],
            "discoverable_clues": [
                {"id": "tariff_slate_fees", "text": TARIFF_FACT},
            ],
            "addressables": [
                {
                    "id": "loft_clerk",
                    "name": "Loft Clerk",
                    "scene_id": "mill_loft",
                    "kind": "npc",
                    "addressable": True,
                }
            ],
            "interactables": [
                {
                    "id": "grain_hopper",
                    "label": "Grain hopper",
                    "aliases": ["hopper", "feed chute"],
                    "type": "investigate",
                },
                {
                    "id": "tariff_slate",
                    "label": "Tariff slate",
                    "aliases": ["slate", "fee slate"],
                    "type": "read",
                    "reveals_clue": "tariff_slate_fees",
                },
            ],
            "exits": [],
            "enemies": [],
            "actions": [],
        }
    }


def _mill_world() -> dict:
    world = default_world()
    world["npcs"] = [
        {
            "id": "loft_clerk",
            "name": "Loft Clerk",
            "location": "mill_loft",
            "topics": [{"id": "shipping_records", "text": ABSTRACT_FACT}],
        }
    ]
    return world


def _seed_scene_runtime(tmp_path, monkeypatch, envelope: dict, *, world: dict | None = None):
    _patch_storage(tmp_path, monkeypatch)
    sid = envelope["scene"]["id"]
    storage._save_json(storage.scene_path(sid), envelope)
    for extra_id in ("frontier_gate", "market_quarter", "old_milestone"):
        if extra_id == sid:
            continue
        storage._save_json(storage.scene_path(extra_id), default_scene(extra_id))
    storage._save_json(storage.WORLD_PATH, world if isinstance(world, dict) else default_world())
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


def _lead_ids(session: dict | None = None) -> set[str]:
    sess = session if isinstance(session, dict) else storage.load_session()
    registry = sess.get(SESSION_LEAD_REGISTRY_KEY) or {}
    if isinstance(registry, dict):
        return {str(key) for key in registry.keys()}
    return set()


def _npc_ids() -> set[str]:
    world = storage.load_world()
    rows = world.get("npcs") or []
    if isinstance(rows, dict):
        rows = list(rows.values())
    return {str(row.get("id")) for row in rows if isinstance(row, dict) and row.get("id")}


def _interactable_ids(scene_id: str) -> set[str]:
    scene = storage.load_scene(scene_id)
    inner = scene.get("scene") if isinstance(scene, dict) else {}
    return {
        str(item.get("id"))
        for item in (inner.get("interactables") or [])
        if isinstance(item, dict) and item.get("id")
    }


def test_general_authored_interactable_resolves():
    scene = _mill_scene()
    classified = classify_referenced_surface("I inspect the grain hopper.", scene)
    assert classified["authority"] == AUTHORITY_AUTHORED_INTERACTABLE
    assert classified["interactable_id"] == "grain_hopper"
    parsed = parse_freeform_to_action("I inspect the grain hopper.", scene)
    assert parsed is not None
    assert parsed.get("type") == "investigate"
    assert parsed.get("target_id") == "grain_hopper"


def test_general_visible_non_interactable_is_acknowledged_without_invention():
    scene = _mill_scene()
    classified = classify_referenced_surface("I look at the soot-stained skylight.", scene)
    assert classified["authority"] == AUTHORITY_AUTHORED_VISIBLE_FEATURE
    assert classified["inspectability"] is False
    assert SKYLIGHT_FACT in classified["visible_fact"]
    parsed = parse_freeform_to_action("I look at the soot-stained skylight.", scene)
    action = normalize_scene_action(parsed)
    res = resolve_exploration_action(scene, {}, {}, action, raw_player_text="I look at the soot-stained skylight.")
    assert res["kind"] == "investigate"
    assert res["clue_id"] is None
    assert (res.get("metadata") or {}).get("referenced_surface_authority") == AUTHORITY_AUTHORED_VISIBLE_FEATURE


def test_general_unknown_player_named_object_is_not_instantiated(tmp_path, monkeypatch):
    _seed_scene_runtime(tmp_path, monkeypatch, _mill_scene(), world=_mill_world())
    data = _chat(monkeypatch, "I inspect the ivory metronome.", OBSERVE_STOCK)
    text = _facing(data).lower()
    res = data.get("resolution") or {}
    assert res.get("kind") == "investigate"
    assert (res.get("metadata") or {}).get("referenced_surface_authority") == AUTHORITY_UNSUPPORTED
    assert "ivory metronome" not in _interactable_ids("mill_loft")
    assert "ivory" not in text or "nothing here matches" in text
    assert "metronome" not in _npc_ids()
    assert not any("ivory" in item for item in _lead_ids(data.get("session")))


def test_general_narration_only_object_does_not_gain_authority(tmp_path, monkeypatch):
    _seed_scene_runtime(tmp_path, monkeypatch, _mill_scene(), world=_mill_world())
    first = _chat(monkeypatch, "I look around.", NARRATION_BELL)
    assert (first.get("resolution") or {}).get("kind") == "observe"
    second = _chat(monkeypatch, "I inspect the silver bell.", "The silver bell is engraved with Captain Marrow and a sailing date.")
    text = _facing(second).lower()
    res = second.get("resolution") or {}
    assert res.get("kind") == "investigate"
    assert (res.get("metadata") or {}).get("referenced_surface_authority") == AUTHORITY_UNSUPPORTED
    assert "silver_bell" not in _interactable_ids("mill_loft")
    assert "captain marrow" not in text
    assert "sailing date" not in text
    assert not any("silver" in item for item in _lead_ids(second.get("session")))


def test_general_abstract_reference_does_not_become_physical(tmp_path, monkeypatch):
    scene = _mill_scene()
    world = _mill_world()
    classified = classify_referenced_surface("I inspect the shipping records.", scene, world=world)
    assert classified["authority"] == AUTHORITY_AUTHORED_ABSTRACT_REFERENCE
    ledger = classify_referenced_surface("I inspect the shipping ledger.", scene, world=world)
    assert ledger["authority"] == AUTHORITY_AUTHORED_ABSTRACT_REFERENCE
    _seed_scene_runtime(tmp_path, monkeypatch, scene, world=world)
    data = _chat(monkeypatch, "I inspect the shipping ledger.", "The ledger lists eight named crews bound for Glassport.")
    text = _facing(data).lower()
    assert "glassport" not in text
    assert "eight named" not in text
    assert "shipping_ledger" not in _interactable_ids("mill_loft")
    assert "spoken of" in text or "not a surface" in text


def test_general_readable_surface_communicates_contents(tmp_path, monkeypatch):
    _seed_scene_runtime(tmp_path, monkeypatch, _mill_scene(), world=_mill_world())
    data = _chat(monkeypatch, "I read the tariff slate.", OBSERVE_STOCK)
    text = _facing(data).lower()
    res = data.get("resolution") or {}
    assert res.get("kind") in {"investigate", "discover_clue"}
    assert res.get("clue_id") == "tariff_slate_fees" or "dock fees" in text
    assert "dock fees" in text
    assert "as you watch the scene" not in text


def test_general_hidden_object_is_not_revealed_by_naming(tmp_path, monkeypatch):
    scene = _mill_scene()
    classified = classify_referenced_surface("I inspect the brass token.", scene)
    assert classified["authority"] == AUTHORITY_AUTHORED_HIDDEN
    _seed_scene_runtime(tmp_path, monkeypatch, scene, world=_mill_world())
    data = _chat(monkeypatch, "I inspect the brass token.", "You pry up the hopper and pocket the brass token.")
    text = _facing(data).lower()
    runtime = ((data.get("session") or {}).get("scene_runtime") or {}).get("mill_loft") or {}
    revealed = runtime.get("revealed_hidden_facts") or runtime.get("hidden_facts_revealed") or []
    assert classified["hidden_fact"] == HIDDEN_FACT
    assert "brass token is sealed" not in text
    assert HIDDEN_FACT not in revealed
    assert "no such thing" in text or "nothing here matches" in text


def test_general_failed_inspection_then_observe_uses_current_scene(tmp_path, monkeypatch):
    _seed_scene_runtime(tmp_path, monkeypatch, _mill_scene(), world=_mill_world())
    first = _chat(monkeypatch, "I inspect the ivory metronome.", OBSERVE_STOCK)
    assert (first.get("resolution") or {}).get("kind") == "investigate"
    second = _chat(monkeypatch, "I look around.", "Sacks of cracked maize lean against the hopper braces.")
    text = _facing(second).lower()
    assert (second.get("resolution") or {}).get("kind") == "observe"
    assert "nothing here matches" not in text
    assert any(token in text for token in ("skylight", "maize", "hopper", "tariff", "slate", "loft"))


def test_general_authored_alias_binds(tmp_path, monkeypatch):
    scene = _mill_scene()
    classified = classify_referenced_surface("I examine the feed chute.", scene)
    assert classified["authority"] == AUTHORITY_AUTHORED_INTERACTABLE
    assert classified["interactable_id"] == "grain_hopper"
    _seed_scene_runtime(tmp_path, monkeypatch, scene, world=_mill_world())
    data = _chat(monkeypatch, "I examine the feed chute.", OBSERVE_STOCK)
    res = data.get("resolution") or {}
    assert res.get("kind") in {"investigate", "discover_clue"}
    assert (res.get("metadata") or {}).get("referenced_surface_interactable_id") == "grain_hopper" or res.get("interactable_id") == "grain_hopper"


def test_general_failed_inspection_creates_no_world_facts(tmp_path, monkeypatch):
    _seed_scene_runtime(tmp_path, monkeypatch, _mill_scene(), world=_mill_world())
    before_npcs = _npc_ids()
    before_leads = _lead_ids()
    data = _chat(monkeypatch, "I inspect the glass kiln schedule.", "The kiln schedule names four new overseers.")
    session = data.get("session") or {}
    runtime = (session.get("scene_runtime") or {}).get("mill_loft") or {}
    assert _npc_ids() == before_npcs
    assert _lead_ids(session) == before_leads
    assert "glass_kiln_schedule" not in _interactable_ids("mill_loft")
    assert "glass kiln" not in json.dumps(runtime.get("discovered_clues") or [])
    assert "four new overseers" not in _facing(data).lower()


def test_general_short_alias_does_not_steal_more_specific_visible_feature():
    scene = {
        "scene": {
            "id": "ink_hall",
            "interactables": [
                {
                    "id": "notice_plank",
                    "label": "Notice plank",
                    "aliases": ["board", "plank"],
                    "type": "investigate",
                    "reveals_clue": "plank_note",
                }
            ],
            "visible_facts": ["A clerk keeps one eye on the tally board."],
            "discoverable_clues": [{"id": "plank_note", "text": "Fees are posted in red."}],
        }
    }
    specific = classify_referenced_surface(
        "I examine the board the clerk keeps glancing at.",
        scene,
    )
    assert specific["authority"] == AUTHORITY_AUTHORED_VISIBLE_FEATURE
    assert "tally board" in specific["visible_fact"]
    generic = classify_referenced_surface("I look at the board.", scene)
    assert generic["authority"] == AUTHORITY_AUTHORED_INTERACTABLE
    assert generic["interactable_id"] == "notice_plank"


def test_frontier_gate_roster_is_visible_not_inspectable():
    scene = json.loads(Path("data/scenes/frontier_gate.json").read_text(encoding="utf-8"))
    classified = classify_referenced_surface(
        "If the watch already has a commander on this, I'll check the roster board the serjeant is watching.",
        scene,
    )
    assert classified["authority"] == AUTHORITY_AUTHORED_VISIBLE_FEATURE
    assert classified["inspectability"] is False
    assert classified["interactable_id"] == ""
    assert "roster board" in classified["visible_fact"].lower()
    serjeant_board = classify_referenced_surface(
        "I examine the board the serjeant keeps glancing at.",
        scene,
    )
    assert serjeant_board["authority"] == AUTHORITY_AUTHORED_VISIBLE_FEATURE
    assert "roster board" in serjeant_board["visible_fact"].lower()
    parsed = parse_freeform_to_action(
        "If the watch already has a commander on this, I'll check the roster board the serjeant is watching.",
        scene,
    )
    action = normalize_scene_action(parsed)
    res = resolve_exploration_action(
        scene,
        {},
        {},
        action,
        raw_player_text="If the watch already has a commander on this, I'll check the roster board the serjeant is watching.",
    )
    assert res["kind"] == "investigate"
    assert res["clue_id"] is None
    assert (res.get("metadata") or {}).get("skip_unrelated_clue_discovery") is True


def test_frontier_gate_roster_http_does_not_use_observe_stock(tmp_path, monkeypatch):
    scene = json.loads(Path("data/scenes/frontier_gate.json").read_text(encoding="utf-8"))
    _seed_scene_runtime(tmp_path, monkeypatch, scene)
    data = _chat(
        monkeypatch,
        "If the watch already has a commander on this, I'll check the roster board the serjeant is watching.",
        OBSERVE_STOCK,
    )
    text = _facing(data)
    low = text.lower()
    assert (data.get("resolution") or {}).get("kind") == "investigate"
    assert "as you watch the scene" not in low
    assert "roster board" in low
    assert "closer looking yields nothing further" in low
    assert "thoran" not in low
    assert "lirael" not in low


def test_observe_stock_replacement_keeps_notice_board_working(tmp_path, monkeypatch):
    scene = json.loads(Path("data/scenes/frontier_gate.json").read_text(encoding="utf-8"))
    _seed_scene_runtime(tmp_path, monkeypatch, scene)
    data = _chat(monkeypatch, "I read the notice board.", OBSERVE_STOCK)
    text = _facing(data).lower()
    res = data.get("resolution") or {}
    assert res.get("kind") in {"investigate", "discover_clue"}
    assert "northwest" in text or res.get("clue_id") == "notice_patrol_route"


def test_anti_overfitting_generic_engine_has_no_calibration_special_case():
    src = Path("game/referenced_surface.py").read_text(encoding="utf-8").lower()
    for term in CALIBRATION_ENGINE_TERMS:
        assert term.lower() not in src, f"referenced_surface.py contains calibration term {term}"
    perception = Path("game/perception_grounding.py").read_text(encoding="utf-8")
    start = perception.find("force_surface")
    assert start >= 0
    slice_src = perception[start : start + 800].lower()
    for term in CALIBRATION_ENGINE_TERMS:
        assert term.lower() not in slice_src, f"perception hook contains calibration term {term}"


def test_perception_hook_replaces_observe_stock_for_visible_feature():
    scene = _mill_scene()
    parsed = parse_freeform_to_action("I look at the soot-stained skylight.", scene)
    action = normalize_scene_action(parsed)
    resolution = resolve_exploration_action(scene, {}, {}, action, raw_player_text="I look at the soot-stained skylight.")
    gm = {"player_facing_text": OBSERVE_STOCK, "tags": []}
    out = apply_perception_non_invention_to_gm(
        gm,
        resolution=resolution,
        scene=scene,
        player_text="I look at the soot-stained skylight.",
    )
    text = str((out or {}).get("player_facing_text") or "").lower()
    assert "as you watch the scene" not in text
    assert "skylight" in text
    assert "closer looking yields nothing further" in text
