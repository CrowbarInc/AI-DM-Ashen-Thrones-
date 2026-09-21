"""PR-AH: grounded observation and non-invention.

Synthetic fixtures are unrelated to Cinderwatch. Frontier Gate cases are
calibration regression only.
"""
from __future__ import annotations

from pathlib import Path

import pytest
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
from game.leads import SESSION_LEAD_REGISTRY_KEY
from game.perception_grounding import (
    apply_perception_non_invention_to_gm,
    build_perception_evidence_surface,
    classify_perception_invention,
)
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _patch_storage

CALIBRATION_ENGINE_TERMS = (
    "frontier_gate",
    "old_milestone",
    "Cinderwatch",
    "Captain Thoran",
    "notice_patrol_route",
)
GENERIC_ENGINE_FILES = (
    Path("game/perception_grounding.py"),
    Path("game/final_emission_non_strict_stack.py"),
)
PRESSURE_STOCK_FILES = (
    Path("game/final_emission_passive_scene_pressure.py"),
    Path("game/response_policy_enforcement.py"),
    Path("game/gm.py"),
)


def _envelope(scene_id: str, **extra) -> dict:
    scene = default_scene(scene_id)
    inner = scene["scene"]
    inner["id"] = scene_id
    inner["location"] = extra.pop("location", scene_id.replace("_", " ").title())
    inner.update(extra)
    return scene


SLATE = _envelope(
    "slate_cistern",
    location="Slate Cistern Yard",
    summary="A weathered cistern stands in standing rainwater beside mossy steps.",
    visible_facts=[
        "A weathered cistern stands in standing rainwater.",
        "Moss darkens the flooded stone steps.",
        "Broken pails lean against the cistern rim.",
    ],
    hidden_facts=["A silver token is wedged under the cistern lip."],
    discoverable_clues=[],
    interactables=[
        {
            "id": "cistern_rim",
            "label": "Cistern rim",
            "aliases": ["rim", "cistern", "stone rim"],
            "type": "investigate",
        }
    ],
    addressables=[],
    exits=[],
    enemies=[],
    actions=[],
)
WHARF = _envelope(
    "lantern_wharf",
    location="Lantern Wharf",
    summary="A deserted ferry post leans over black water.",
    visible_facts=[
        "A deserted ferry post leans over black water.",
        "A tide mark is carved into the ferry post.",
        "Lantern hooks hang empty along the rail.",
    ],
    hidden_facts=[],
    discoverable_clues=[
        {
            "id": "wharf_tide_mark",
            "text": "The carved tide mark sits a hand higher than last season's stain.",
        }
    ],
    interactables=[
        {
            "id": "ferry_post",
            "label": "Ferry post",
            "aliases": ["post", "tide mark", "carved mark"],
            "type": "investigate",
            "reveals_clue": "wharf_tide_mark",
        }
    ],
    addressables=[],
    exits=[],
)
ORCHARD = _envelope(
    "copper_orchard",
    location="Copper Orchard Wall",
    summary="A low orchard wall holds a row of frost-bitten quince.",
    visible_facts=[
        "A low orchard wall holds frost-bitten quince.",
        "Wasp nests cling under the coping stones.",
    ],
    hidden_facts=["A cellar hatch is packed with leaves behind the wall."],
    addressables=[
        {
            "id": "orchard_keeper",
            "name": "Orchard Keeper",
            "scene_id": "copper_orchard",
            "kind": "npc",
            "addressable": True,
        }
    ],
    interactables=[],
    exits=[],
)


def _seed_scene_runtime(tmp_path, monkeypatch, envelope: dict, *, world_npcs: list | None = None):
    _patch_storage(tmp_path, monkeypatch)
    sid = envelope["scene"]["id"]
    storage._save_json(storage.scene_path(sid), envelope)
    storage._save_json(storage.scene_path("frontier_gate"), default_scene("frontier_gate"))
    storage._save_json(storage.scene_path("market_quarter"), default_scene("market_quarter"))
    storage._save_json(storage.scene_path("old_milestone"), default_scene("old_milestone"))
    world = default_world()
    if world_npcs is not None:
        world["npcs"] = world_npcs
    storage._save_json(storage.WORLD_PATH, world)
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


def _npc_ids() -> set[str]:
    world = storage.load_world()
    rows = world.get("npcs") or []
    if isinstance(rows, dict):
        rows = list(rows.values())
    out = set()
    for row in rows:
        if isinstance(row, dict) and row.get("id"):
            out.add(str(row["id"]))
    return out


def _lead_ids(session: dict | None = None) -> set[str]:
    sess = session if isinstance(session, dict) else storage.load_session()
    registry = sess.get(SESSION_LEAD_REGISTRY_KEY) or {}
    if isinstance(registry, dict):
        return {str(key) for key in registry.keys()}
    return set()


CONFRONTATION = (
    'A stranger cuts through the crowd and stops at your shoulder. '
    '"You\'re asking the wrong questions out loud," they murmur. '
    '"Walk with me if you want the next name."'
)
INSCRIPTION = (
    "The cistern rim is covered in faded inscriptions and worn numbers "
    "hinting at forgotten distance markers."
)


def test_general_grounded_observe_uses_visible_facts(tmp_path, monkeypatch):
    _seed_scene_runtime(tmp_path, monkeypatch, SLATE)
    data = _chat(monkeypatch, "I look around.", "Rain beads along the weathered cistern while moss darkens the flooded steps.")
    text = _facing(data).lower()
    assert data.get("session", {}).get("active_scene_id") == "slate_cistern"
    assert (data.get("resolution") or {}).get("kind") == "observe"
    assert "cistern" in text or "moss" in text or "pails" in text
    assert "stranger" not in text
    assert "walk with me" not in text
    assert inspect_interaction_context(data.get("session") or {}).get("active_interaction_target_id") in (None, "")


def test_general_npc_absence_rejects_stranger_confrontation(tmp_path, monkeypatch):
    _seed_scene_runtime(tmp_path, monkeypatch, SLATE, world_npcs=[])
    data = _chat(monkeypatch, "I look around.", CONFRONTATION)
    text = _facing(data).lower()
    assert "walk with me" not in text
    assert "stops at your shoulder" not in text
    assert inspect_interaction_context(data.get("session") or {}).get("active_interaction_target_id") in (None, "")
    assert "stranger" not in _npc_ids()
    assert _facing(data).strip()


def test_general_authorized_npc_remains_describable():
    evidence = build_perception_evidence_surface(
        scene=ORCHARD,
        session=default_session(),
        world={"npcs": [{"id": "orchard_keeper", "name": "Orchard Keeper", "location": "copper_orchard"}]},
        resolution={"kind": "observe"},
    )
    text = "The orchard keeper stands by the frost-bitten quince, watching the wall."
    verdict = classify_perception_invention(text, evidence, resolution={"kind": "observe"})
    assert verdict["unsupported"] is False
    assert "orchard keeper" in " ".join(evidence["present_npc_texts"]).lower()


def test_general_physical_evidence_absence_rejects_inscription():
    evidence = build_perception_evidence_surface(
        scene=SLATE,
        session=default_session(),
        world={"npcs": []},
        resolution={"kind": "investigate"},
    )
    verdict = classify_perception_invention(INSCRIPTION, evidence, resolution={"kind": "investigate"})
    assert verdict["unsupported"] is True
    assert any(flag.startswith("physical_evidence:inscription") for flag in verdict["flags"])


def test_general_authorized_physical_evidence_survives():
    evidence = build_perception_evidence_surface(
        scene=WHARF,
        session=default_session(),
        world={"npcs": []},
        resolution={"kind": "observe"},
    )
    text = "The ferry post bears a carved tide mark just above the black water."
    verdict = classify_perception_invention(text, evidence, resolution={"kind": "observe"})
    assert verdict["unsupported"] is False


def test_general_hidden_fact_stays_hidden_on_observe():
    evidence = build_perception_evidence_surface(
        scene=SLATE,
        session=default_session(),
        world={"npcs": []},
        resolution={"kind": "observe"},
    )
    leak = "A silver token is wedged under the cistern lip, waiting for a careful hand."
    verdict = classify_perception_invention(leak, evidence, resolution={"kind": "observe"})
    assert verdict["unsupported"] is True
    assert "hidden_fact" in verdict["flags"]


def test_general_discoverable_fact_can_be_spoken_after_discovery(tmp_path, monkeypatch):
    _seed_scene_runtime(tmp_path, monkeypatch, WHARF)
    data = _chat(
        monkeypatch,
        "I examine the ferry post.",
        "The carved tide mark sits a hand higher than last season's stain.",
    )
    text = _facing(data).lower()
    assert "tide mark" in text
    assert "inscriptions" not in text
    res = data.get("resolution") or {}
    assert res.get("kind") in {"investigate", "discover_clue"}


def test_general_no_state_from_rejected_prose(tmp_path, monkeypatch):
    _seed_scene_runtime(tmp_path, monkeypatch, SLATE, world_npcs=[])
    first = _chat(monkeypatch, "I look around.", CONFRONTATION)
    session = first.get("session") or {}
    runtime = (session.get("scene_runtime") or {}).get("slate_cistern") or {}
    leads = runtime.get("recent_contextual_leads") or []
    for lead in leads:
        subject = str((lead or {}).get("subject") or "").lower()
        assert "stranger" not in subject
    assert "stranger" not in _npc_ids()
    assert not any("narration_ctx" in item for item in _lead_ids(session))
    second = _chat(monkeypatch, "I glance around again.", "Moss darkens the flooded stone steps beside the cistern.")
    text = _facing(second).lower()
    assert "walk with me" not in text
    assert "next name" not in text
    assert inspect_interaction_context(second.get("session") or {}).get("active_interaction_target_id") in (None, "")


def test_general_presentational_freedom_allows_nonidentical_wording():
    evidence = build_perception_evidence_surface(
        scene=SLATE,
        session=default_session(),
        world={"npcs": []},
        resolution={"kind": "observe"},
    )
    first = "Rain beads along the weathered cistern while moss darkens the flooded steps."
    second = "Standing water laps the cistern, and the mossy steps stay slick."
    assert classify_perception_invention(first, evidence, resolution={"kind": "observe"})["unsupported"] is False
    assert classify_perception_invention(second, evidence, resolution={"kind": "observe"})["unsupported"] is False
    assert first != "A weathered cistern stands in standing rainwater."


def test_general_fail_closed_response_is_useful_not_blank():
    gm = apply_perception_non_invention_to_gm(
        {"player_facing_text": CONFRONTATION, "tags": []},
        resolution={"kind": "observe", "prompt": "I look around."},
        session=default_session(),
        world={"npcs": []},
        scene=SLATE,
        player_text="I look around.",
    )
    text = str((gm or {}).get("player_facing_text") or "").strip()
    assert text
    assert "walk with me" not in text.lower()
    assert "cistern" in text.lower() or "moss" in text.lower() or "pails" in text.lower()


def test_frontier_gate_post_return_observe_does_not_invent_confrontation(tmp_path, monkeypatch):
    _patch_storage(tmp_path, monkeypatch)
    storage._save_json(storage.scene_path("frontier_gate"), default_scene("frontier_gate"))
    storage._save_json(storage.scene_path("old_milestone"), default_scene("old_milestone"))
    storage._save_json(storage.scene_path("market_quarter"), default_scene("market_quarter"))
    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    session["visited_scene_ids"] = ["frontier_gate", "old_milestone"]
    storage.save_session(session)
    data = _chat(
        monkeypatch,
        "I look around.",
        'threadbare watchers remain clustered along the gate cuts through the crowd and stops at your shoulder. '
        '"You\'re asking the wrong questions out loud," they murmur. "Walk with me if you want the next name."',
    )
    text = _facing(data).lower()
    assert data.get("session", {}).get("active_scene_id") == "frontier_gate"
    assert "walk with me" not in text
    assert "next name" not in text
    assert "board, runner, or road" not in text
    assert inspect_interaction_context(data.get("session") or {}).get("active_interaction_target_id") in (None, "")
    follow = _chat(monkeypatch, "I read the notice board again.", "The missing patrol was last seen taking the northwest mud track past the crates.")
    follow_text = _facing(follow).lower()
    assert "patrol" in follow_text or "notice" in follow_text or "track" in follow_text
    assert "walk with me" not in follow_text


def test_milestone_examine_does_not_keep_invented_inscription(tmp_path, monkeypatch):
    _patch_storage(tmp_path, monkeypatch)
    storage._save_json(storage.scene_path("old_milestone"), default_scene("old_milestone"))
    storage._save_json(storage.scene_path("frontier_gate"), default_scene("frontier_gate"))
    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    session = default_session()
    session["active_scene_id"] = "old_milestone"
    session["visited_scene_ids"] = ["old_milestone"]
    storage.save_session(session)
    data = _chat(
        monkeypatch,
        "I examine the weathered stone.",
        "The faded inscriptions are nearly illegible, but worn symbols and numbers hint at forgotten distance markers.",
    )
    text = _facing(data).lower()
    assert "inscription" not in text
    assert "prints" in text or "milestone" in text or "mud" in text


def test_anti_overfitting_generic_engine_has_no_cinderwatch_special_cases():
    for path in GENERIC_ENGINE_FILES:
        text = path.read_text(encoding="utf-8")
        for term in CALIBRATION_ENGINE_TERMS:
            assert term not in text, f"{path} contains calibration term {term!r}"
    for path in PRESSURE_STOCK_FILES:
        text = path.read_text(encoding="utf-8")
        assert "Walk with me if you want the next name" not in text
        assert "Board, runner, or road" not in text
        assert "Standing still won't help that patrol" not in text
        assert "if scene == " not in text
        assert '== "frontier_gate"' not in text
