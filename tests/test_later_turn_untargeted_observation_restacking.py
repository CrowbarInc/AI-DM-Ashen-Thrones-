"""PR-AW: later untargeted look-around must not restack unchanged scene stock.

Synthetic fixtures use kiln / quay vocabulary. Frontier Gate is calibration
residue only, not a production special case.
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
from game.diegetic_fallback_narration import (
    observe_nothing_new_fallback_line,
    render_observe_perception_fallback_line,
)
from game.perception_grounding import (
    collect_recent_player_facing_narration,
    observation_recent_use_should_record,
    remember_completed_perception_turn,
)
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _patch_storage

LANTERN = "A cracked lantern hangs above the kiln door."
ASH = "Cold ash sits unused in the grate."
SLATE = "A cracked slate tile has fallen beside the grate."
FEE = "Dock fees rise after the second horn."
QUAY_RAIL = "Lantern hooks hang empty along the rail."
BOARD = "A slate roster board names the night berth order."
STOCK = f"As you watch the scene, {LANTERN} {ASH}"
QUAY_STOCK = f"As you watch the scene, {QUAY_RAIL} {BOARD}"


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
    summary="A cold kiln stands in a brick alcove.",
    visible_facts=[LANTERN, ASH],
    hidden_facts=["A hidden stream rushes through a tunnel beneath the wall."],
    discoverable_clues=[{"id": "fee_slate", "text": FEE}],
    interactables=[
        {
            "id": "fee_slate",
            "label": "Fee slate",
            "aliases": ["slate", "board"],
            "type": "investigate",
            "reveals_clue": "fee_slate",
            "description": FEE,
        }
    ],
    addressables=[
        {
            "id": "night_porter",
            "name": "Night Porter",
            "scene_id": "ember_kiln",
            "kind": "npc",
            "addressable": True,
            "aliases": ["porter"],
        }
    ],
    exits=[],
)
QUAY = _envelope(
    "brass_quay",
    location="Brass Quay",
    summary="A deserted quay leans over black water.",
    visible_facts=[QUAY_RAIL, BOARD],
    hidden_facts=[],
    discoverable_clues=[],
    interactables=[],
    addressables=[
        {
            "id": "lamp_clerk",
            "name": "Lamp Clerk",
            "scene_id": "brass_quay",
            "kind": "npc",
            "addressable": True,
            "aliases": ["clerk"],
        }
    ],
    exits=[],
)


def _complete(text: str) -> bool:
    raw = str(text or "").strip()
    if not raw or raw.endswith("…") or raw.endswith("..."):
        return False
    return raw[-1] in '.!?"'


def _seed(tmp_path, monkeypatch, envelope: dict, world: dict | None = None) -> str:
    _patch_storage(tmp_path, monkeypatch)
    sid = envelope["scene"]["id"]
    storage._save_json(storage.scene_path(sid), envelope)
    for extra_id in ("frontier_gate", "market_quarter", "old_milestone"):
        if extra_id != sid:
            storage._save_json(storage.scene_path(extra_id), default_scene(extra_id))
    storage._save_json(storage.WORLD_PATH, world if world is not None else default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    session = default_session()
    session["active_scene_id"] = sid
    session["visited_scene_ids"] = [sid]
    session["turn_counter"] = 2
    storage.save_session(session)
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")
    return sid


def _kiln_world() -> dict:
    return {
        "npcs": [
            {
                "id": "night_porter",
                "name": "Night Porter",
                "location": "ember_kiln",
                "aliases": ["porter"],
                "topics": [{"id": "mash_exists", "text": "The mash kettle is cold tonight."}],
            }
        ]
    }


def _quay_world() -> dict:
    return {
        "npcs": [
            {
                "id": "lamp_clerk",
                "name": "Lamp Clerk",
                "location": "brass_quay",
                "aliases": ["clerk"],
                "topics": [{"id": "hooks_exist", "text": "The rail hooks stay empty after the last berth."}],
            }
        ]
    }


def _chat(monkeypatch, text: str, gm_text: str) -> dict:
    monkeypatch.setattr("game.api.call_gpt", lambda _messages: _gm_response(gm_text))
    client = TestClient(app)
    resp = client.post("/api/chat", json={"text": text})
    assert resp.status_code == 200
    return resp.json()


def _facing(data: dict) -> str:
    return str((data.get("gm_output") or {}).get("player_facing_text") or "")


def _has_stock(text: str, *needles: str) -> bool:
    low = str(text or "").lower()
    return any(needle.lower() in low for needle in needles)


def test_remember_ignores_social_and_investigate_overwrite():
    session = default_session()
    sid = "ember_kiln"
    remember_completed_perception_turn(
        session,
        sid,
        KILN,
        STOCK,
        resolution={"kind": "observe"},
        player_text="I look around.",
    )
    prior = collect_recent_player_facing_narration(session=session, scene_id=sid)
    assert "lantern" in prior.lower()
    remember_completed_perception_turn(
        session,
        sid,
        KILN,
        'Night Porter says, "The mash kettle is cold tonight."',
        resolution={"kind": "question"},
        player_text="I ask the night porter whether the mash is still hot.",
    )
    remember_completed_perception_turn(
        session,
        sid,
        KILN,
        f"You inspect the fee slate. {FEE}",
        resolution={"kind": "discover_clue"},
        player_text="I inspect the fee slate.",
    )
    recent = collect_recent_player_facing_narration(session=session, scene_id=sid)
    assert recent == prior
    assert "lantern" in recent.lower()
    assert "mash" not in recent.lower()
    assert "dock fees" not in recent.lower()


def test_remember_keeps_stock_narration_on_nothing_new_and_listen():
    session = default_session()
    sid = "ember_kiln"
    remember_completed_perception_turn(
        session,
        sid,
        KILN,
        STOCK,
        resolution={"kind": "observe"},
        player_text="I look around.",
    )
    remember_completed_perception_turn(
        session,
        sid,
        KILN,
        observe_nothing_new_fallback_line(),
        resolution={"kind": "observe"},
        player_text="I look around again.",
    )
    remember_completed_perception_turn(
        session,
        sid,
        KILN,
        "A dozen half-conversations brush past your ears; none sharpens enough to follow.",
        resolution={
            "kind": "observe",
            "metadata": {"human_adjacent_intent_family": "listen"},
        },
        player_text="I listen.",
    )
    recent = collect_recent_player_facing_narration(session=session, scene_id=sid)
    assert "lantern" in recent.lower()
    assert recent != observe_nothing_new_fallback_line()


def test_stamp_eligibility_is_untargeted_visual_observe_only():
    assert observation_recent_use_should_record(
        resolution={"kind": "observe"},
        player_text="I look around.",
        scene=KILN,
    )
    assert observation_recent_use_should_record(
        resolution={"kind": "question"},
        player_text="I ask the night porter whether the mash is still hot.",
        scene=KILN,
    ) is False
    assert observation_recent_use_should_record(
        resolution={"kind": "discover_clue"},
        player_text="I inspect the fee slate.",
        scene=KILN,
    ) is False
    assert observation_recent_use_should_record(
        resolution={"kind": "investigate"},
        player_text="I inspect the fee slate.",
        scene=KILN,
    ) is False
    assert observation_recent_use_should_record(
        resolution={
            "kind": "observe",
            "metadata": {"human_adjacent_intent_family": "listen"},
        },
        player_text="I listen.",
        scene=KILN,
    ) is False
    assert observation_recent_use_should_record(
        resolution={"kind": "observe"},
        player_text="I look at the cracked lantern.",
        scene=KILN,
    ) is False


def test_observe_observe_still_nothing_new(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, KILN, _kiln_world())
    first = _facing(_chat(monkeypatch, "I look around.", STOCK))
    assert _has_stock(first, "lantern", "ash")
    again = _facing(_chat(monkeypatch, "I look around again.", STOCK))
    assert again == observe_nothing_new_fallback_line()
    assert not _has_stock(again, "lantern", "ash", "grate")


def test_observe_social_observe_does_not_restack(tmp_path, monkeypatch):
    sid = _seed(tmp_path, monkeypatch, KILN, _kiln_world())
    first = _facing(_chat(monkeypatch, "I look around.", STOCK))
    assert _has_stock(first, "lantern", "ash")
    social = _facing(
        _chat(
            monkeypatch,
            "I ask the night porter whether the mash is still hot.",
            'Night Porter says, "The mash kettle is cold tonight."',
        )
    )
    assert "mash" in social.lower()
    recent = collect_recent_player_facing_narration(
        session=storage.load_session(), scene_id=sid
    )
    assert _has_stock(recent, "lantern", "ash")
    assert "mash" not in recent.lower()
    later = _facing(_chat(monkeypatch, "I look around.", STOCK))
    assert later == observe_nothing_new_fallback_line()


def test_observe_investigate_observe_does_not_restack(tmp_path, monkeypatch):
    sid = _seed(tmp_path, monkeypatch, KILN, _kiln_world())
    _chat(monkeypatch, "I look around.", STOCK)
    inspected = _facing(
        _chat(monkeypatch, "I inspect the fee slate.", f"You read the slate. {FEE}")
    )
    assert "dock fees" in inspected.lower() or "horn" in inspected.lower()
    recent = collect_recent_player_facing_narration(
        session=storage.load_session(), scene_id=sid
    )
    assert _has_stock(recent, "lantern", "ash")
    later = _facing(_chat(monkeypatch, "I look around.", STOCK))
    assert later == observe_nothing_new_fallback_line()


def test_observe_social_investigate_observe_does_not_restack(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, KILN, _kiln_world())
    _chat(monkeypatch, "I look around.", STOCK)
    _chat(
        monkeypatch,
        "I ask the night porter whether the mash is still hot.",
        'Night Porter says, "The mash kettle is cold tonight."',
    )
    _chat(monkeypatch, "I inspect the fee slate.", f"You read the slate. {FEE}")
    later = _facing(_chat(monkeypatch, "I look around.", STOCK))
    assert later == observe_nothing_new_fallback_line()


def test_observe_listen_observe_does_not_restack(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, KILN, _kiln_world())
    _chat(monkeypatch, "I look around.", STOCK)
    listen = _facing(_chat(monkeypatch, "I listen.", "Soft anxious whispers drift about a missing patrol."))
    assert "whisper" not in listen.lower()
    assert "lantern" not in listen.lower()
    assert _complete(listen)
    later = _facing(_chat(monkeypatch, "I look around.", STOCK))
    assert later == observe_nothing_new_fallback_line()


def test_targeted_observe_may_repeat_after_intervening_turns(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, KILN, _kiln_world())
    _chat(monkeypatch, "I look around.", STOCK)
    _chat(
        monkeypatch,
        "I ask the night porter whether the mash is still hot.",
        'Night Porter says, "The mash kettle is cold tonight."',
    )
    targeted = _facing(
        _chat(monkeypatch, "I look at the cracked lantern.", f"You notice {LANTERN}")
    )
    assert "lantern" in targeted.lower()
    assert targeted != observe_nothing_new_fallback_line()


def test_new_visible_fact_can_surface_after_intervening_turns(tmp_path, monkeypatch):
    sid = _seed(tmp_path, monkeypatch, KILN, _kiln_world())
    first = _facing(_chat(monkeypatch, "I look around.", STOCK))
    assert not _has_stock(first, "slate tile")
    _chat(
        monkeypatch,
        "I ask the night porter whether the mash is still hot.",
        'Night Porter says, "The mash kettle is cold tonight."',
    )
    stored = storage._load_json(storage.scene_path(sid), KILN)
    stored["scene"]["visible_facts"] = [LANTERN, ASH, SLATE]
    storage._save_json(storage.scene_path(sid), stored)
    later = _facing(
        _chat(
            monkeypatch,
            "I look around.",
            f"As you watch the scene, {SLATE} {LANTERN}",
        )
    )
    assert "slate" in later.lower()
    assert later != observe_nothing_new_fallback_line()
    assert "hidden stream" not in later.lower()


def test_scene_change_can_resurface_appropriate_observation(tmp_path, monkeypatch):
    sid = _seed(tmp_path, monkeypatch, KILN, _kiln_world())
    _chat(monkeypatch, "I look around.", STOCK)
    _chat(monkeypatch, "I inspect the fee slate.", f"You read the slate. {FEE}")
    stored = storage._load_json(storage.scene_path(sid), KILN)
    stored["scene"]["visible_facts"] = [SLATE]
    storage._save_json(storage.scene_path(sid), stored)
    later = _facing(_chat(monkeypatch, "I look around.", f"As you watch the scene, {SLATE}"))
    assert "slate" in later.lower()
    assert later != observe_nothing_new_fallback_line()


def test_social_before_first_observe_still_surfaces_stock(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, KILN, _kiln_world())
    _chat(
        monkeypatch,
        "I ask the night porter whether the mash is still hot.",
        'Night Porter says, "The mash kettle is cold tonight."',
    )
    first = _facing(_chat(monkeypatch, "I look around.", STOCK))
    assert _has_stock(first, "lantern", "ash")
    assert first != observe_nothing_new_fallback_line()


def test_nothing_new_does_not_permanently_hide_targeted_fact(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, KILN, _kiln_world())
    _chat(monkeypatch, "I look around.", STOCK)
    _chat(
        monkeypatch,
        "I ask the night porter whether the mash is still hot.",
        'Night Porter says, "The mash kettle is cold tonight."',
    )
    later = _facing(_chat(monkeypatch, "I look around.", STOCK))
    assert later == observe_nothing_new_fallback_line()
    targeted = _facing(
        _chat(monkeypatch, "I look at the cracked lantern.", f"You notice {LANTERN}")
    )
    assert "lantern" in targeted.lower()


def test_quay_generalization_social_does_not_restack(tmp_path, monkeypatch):
    sid = _seed(tmp_path, monkeypatch, QUAY, _quay_world())
    first = _facing(_chat(monkeypatch, "I look around.", QUAY_STOCK))
    assert _has_stock(first, "hooks", "board", "berth")
    _chat(
        monkeypatch,
        "I ask the lamp clerk whether the hooks are still empty.",
        'Lamp Clerk says, "The rail hooks stay empty after the last berth."',
    )
    recent = collect_recent_player_facing_narration(
        session=storage.load_session(), scene_id=sid
    )
    assert _has_stock(recent, "hooks", "board", "berth")
    later = _facing(_chat(monkeypatch, "I look around.", QUAY_STOCK))
    assert later == observe_nothing_new_fallback_line()
    targeted = _facing(
        _chat(monkeypatch, "I look at the roster board.", f"You notice {BOARD}")
    )
    assert "board" in targeted.lower() or "berth" in targeted.lower()


def test_fallback_nothing_new_still_uses_recent_stock_narration():
    first = render_observe_perception_fallback_line(
        KILN, seed_key="praw|unit1", player_text="I look around."
    )
    later = render_observe_perception_fallback_line(
        KILN,
        seed_key="praw|unit2",
        player_text="I look around.",
        recent_narration=first,
    )
    assert later == observe_nothing_new_fallback_line()


def test_generic_engine_has_no_frontier_gate_special_case():
    text = (
        Path("game/perception_grounding.py").read_text(encoding="utf-8")
        + Path("game/diegetic_fallback_narration.py").read_text(encoding="utf-8")
    )
    lowered = text.lower()
    assert "threadbare watchers" not in lowered
    assert "frontier_gate" not in lowered
    assert "muddy gate line" not in lowered
    assert "gate serjeant" not in lowered
    helper = Path("game/perception_grounding.py").read_text(encoding="utf-8")
    assert "observation_recent_use_should_record" in helper
