"""PR-AS: observation may repeat a relevant fact, but must not restack unused stock.

Synthetic fixtures use kiln / quay / yard vocabulary. Frontier Gate is
calibration residue only, not a production special case.
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
    OBSERVE_NOTHING_NEW_FALLBACK_LINE,
    is_targeted_perception,
    observe_nothing_new_fallback_line,
    render_observe_perception_fallback_line,
)
from game.exploration import resolve_exploration_action
from game.intent_parser import parse_freeform_to_action
from game.perception_grounding import (
    apply_perception_non_invention_to_gm,
    classify_perception_invention,
    record_perception_visible_facts,
)
from game.scene_actions import normalize_scene_action
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _patch_storage

LANTERN_FACT = "A cracked lantern hangs above the kiln door."
ASH_FACT = "Cold ash sits unused in the grate."
SLATE_FACT = "A cracked slate tile has fallen beside the grate."
QUAY_RAIL_FACT = "Lantern hooks hang empty along the rail."
WATER_FACT = "Water can be heard behind the kiln wall."
BOARD_FACT = "A slate roster board names the night berth order."


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
    visible_facts=[LANTERN_FACT, ASH_FACT],
    hidden_facts=["A hidden stream rushes through a tunnel beneath the wall."],
    addressables=[],
    exits=[],
)
KILN_CHANGED = _envelope(
    "ember_kiln",
    location="Ember Kiln Alcove",
    summary="A cold kiln stands in a brick alcove.",
    visible_facts=[LANTERN_FACT, ASH_FACT, SLATE_FACT],
    addressables=[],
    exits=[],
)
KILN_WATER = _envelope(
    "ember_kiln",
    location="Ember Kiln Alcove",
    visible_facts=[LANTERN_FACT, ASH_FACT, WATER_FACT],
    addressables=[],
    exits=[],
)
QUAY = _envelope(
    "brass_quay",
    location="Brass Quay",
    summary="A deserted quay leans over black water.",
    visible_facts=[QUAY_RAIL_FACT, BOARD_FACT],
    addressables=[],
    exits=[],
)


def _resolve(scene: dict, text: str):
    parsed = parse_freeform_to_action(text, scene)
    action = normalize_scene_action(parsed)
    res = resolve_exploration_action(
        scene,
        {},
        {},
        action,
        raw_player_text=text,
        list_scene_ids=lambda: [scene["scene"]["id"]],
    )
    return parsed, res


def _complete(text: str) -> bool:
    raw = str(text or "").strip()
    if not raw or raw.endswith("…") or raw.endswith("..."):
        return False
    return raw[-1] in ".!?\""


def _seed(tmp_path, monkeypatch, envelope: dict):
    _patch_storage(tmp_path, monkeypatch)
    sid = envelope["scene"]["id"]
    storage._save_json(storage.scene_path(sid), envelope)
    storage._save_json(storage.scene_path("frontier_gate"), default_scene("frontier_gate"))
    storage._save_json(storage.scene_path("market_quarter"), default_scene("market_quarter"))
    storage._save_json(storage.scene_path("old_milestone"), default_scene("old_milestone"))
    storage._save_json(storage.WORLD_PATH, default_world())
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


def test_first_untargeted_observe_surfaces_authoritative_facts():
    line = render_observe_perception_fallback_line(
        KILN, seed_key="pras|first", player_text="I look around."
    )
    assert line
    low = line.lower()
    assert "lantern" in low or "ash" in low
    assert "hidden stream" not in low
    assert _complete(line)


def test_repeated_untargeted_observe_does_not_restack_same_stock():
    first = render_observe_perception_fallback_line(
        KILN, seed_key="pras|rep1", player_text="I look around."
    )
    second = render_observe_perception_fallback_line(
        KILN,
        seed_key="pras|rep2",
        player_text="I look around again.",
        recent_narration=first,
    )
    assert first
    assert "lantern" in first.lower() or "ash" in first.lower()
    assert second == observe_nothing_new_fallback_line()
    assert "lantern" not in second.lower()
    assert "ash" not in second.lower()


def test_targeted_observe_may_repeat_previously_seen_fact():
    first = render_observe_perception_fallback_line(
        QUAY, seed_key="pras|tgt1", player_text="I look around."
    )
    targeted = render_observe_perception_fallback_line(
        QUAY,
        seed_key="pras|tgt2",
        player_text="I look at the roster board.",
        recent_narration=first,
    )
    assert "board" in targeted.lower() or "berth" in targeted.lower()
    assert targeted != observe_nothing_new_fallback_line()


def test_empty_listen_does_not_pull_visual_stock():
    parsed, res = _resolve(KILN, "I listen.")
    assert parsed["type"] == "observe"
    line = render_observe_perception_fallback_line(
        KILN, seed_key="pras|listen", player_text="I listen.", resolution=res
    )
    assert line and _complete(line)
    low = line.lower()
    assert "lantern" not in low
    assert "grate" not in low
    assert "whisper" not in low
    assert "hidden stream" not in low


def test_empty_listen_without_resolution_still_avoids_visual_stock():
    line = render_observe_perception_fallback_line(
        KILN, seed_key="pras|listen-bare", player_text="I listen for whispers."
    )
    assert line
    low = line.lower()
    assert "lantern" not in low
    assert "grate" not in low
    assert "whisper" not in low


def test_changed_world_surfaces_new_authoritative_fact():
    first = render_observe_perception_fallback_line(
        KILN, seed_key="pras|chg1", player_text="I look around."
    )
    changed = render_observe_perception_fallback_line(
        KILN_CHANGED,
        seed_key="pras|chg2",
        player_text="I look around.",
        recent_narration=first,
        new_visible_facts=[SLATE_FACT],
    )
    assert "slate" in changed.lower()
    assert changed != first
    assert "hidden stream" not in changed.lower()


def test_nothing_new_does_not_invent():
    first = render_observe_perception_fallback_line(
        KILN, seed_key="pras|inv1", player_text="I look around."
    )
    again = render_observe_perception_fallback_line(
        KILN,
        seed_key="pras|inv2",
        player_text="I look around again.",
        recent_narration=first,
    )
    assert again == OBSERVE_NOTHING_NEW_FALLBACK_LINE
    verdict = classify_perception_invention(
        again,
        {
            "visible_facts": [LANTERN_FACT, ASH_FACT],
            "hidden_facts": ["A hidden stream rushes through a tunnel beneath the wall."],
            "present_npcs": [],
            "discovered_clue_texts": [],
            "undiscovered_clue_texts": [],
        },
        resolution={"kind": "observe"},
    )
    assert verdict["unsupported"] is False
    assert "whisper" not in again.lower()
    assert "stream" not in again.lower()


def test_suppression_does_not_hide_later_targeted_fact():
    first = render_observe_perception_fallback_line(
        QUAY, seed_key="pras|hide1", player_text="I look around."
    )
    nothing = render_observe_perception_fallback_line(
        QUAY,
        seed_key="pras|hide2",
        player_text="I look around again.",
        recent_narration=first,
    )
    later = render_observe_perception_fallback_line(
        QUAY,
        seed_key="pras|hide3",
        player_text="I look at the roster board.",
        recent_narration=nothing,
    )
    assert nothing == observe_nothing_new_fallback_line()
    assert "board" in later.lower() or "berth" in later.lower()


def test_nothing_new_line_is_complete_and_playable():
    line = observe_nothing_new_fallback_line()
    assert _complete(line)
    assert "whisper" not in line.lower()
    assert is_targeted_perception("I look at the roster board.", QUAY) is True
    assert is_targeted_perception("I look around again.", KILN) is False


def test_authorized_listen_still_realizes_audible_fact():
    parsed, res = _resolve(KILN_WATER, "I listen.")
    line = render_observe_perception_fallback_line(
        KILN_WATER, seed_key="pras|water", player_text="I listen.", resolution=res
    )
    assert "water" in line.lower() or "heard" in line.lower()
    assert "lantern" not in line.lower()


def test_apply_replaces_listen_visual_stock_even_when_authorized():
    session = default_session()
    session["active_scene_id"] = "ember_kiln"
    gm = {
        "player_facing_text": f"As you watch the scene, {LANTERN_FACT} {ASH_FACT}",
        "tags": [],
        "metadata": {},
    }
    out = apply_perception_non_invention_to_gm(
        gm,
        resolution={
            "kind": "observe",
            "metadata": {
                "human_adjacent_intent_family": "listen",
                "human_adjacent_diegetic_null": True,
            },
        },
        session=session,
        world={"npcs": []},
        scene=KILN,
        player_text="I listen for whispers.",
    )
    text = str(out["player_facing_text"]).lower()
    assert "lantern" not in text
    assert "grate" not in text
    assert "whisper" not in text
    assert _complete(out["player_facing_text"])


def test_apply_replaces_repeated_untargeted_stock_bundle(monkeypatch):
    session = default_session()
    session["active_scene_id"] = "ember_kiln"
    record_perception_visible_facts(session, "ember_kiln", [LANTERN_FACT, ASH_FACT])
    first = render_observe_perception_fallback_line(
        KILN, seed_key="pras|http1", player_text="I look around."
    )
    monkeypatch.setattr(
        "game.perception_grounding.collect_recent_player_facing_narration",
        lambda **_kwargs: first,
    )
    gm = {"player_facing_text": first, "tags": [], "metadata": {}}
    out = apply_perception_non_invention_to_gm(
        gm,
        resolution={"kind": "observe"},
        session=session,
        world={"npcs": []},
        scene=KILN,
        player_text="I look around again.",
    )
    assert out["player_facing_text"] == observe_nothing_new_fallback_line()


def test_http_repeated_observe_and_targeted_followup(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch, KILN)
    session = storage.load_session()
    session["turn_counter"] = 2
    storage.save_session(session)
    first = _chat(
        monkeypatch,
        "I look around.",
        f"As you watch the scene, {LANTERN_FACT} {ASH_FACT}",
    )
    first_text = _facing(first)
    assert "lantern" in first_text.lower() or "ash" in first_text.lower()
    again = _chat(
        monkeypatch,
        "I look around again.",
        f"As you watch the scene, {LANTERN_FACT} {ASH_FACT}",
    )
    again_text = _facing(again)
    assert again_text == observe_nothing_new_fallback_line()
    targeted = _chat(
        monkeypatch,
        "I look at the cracked lantern.",
        f"You notice {LANTERN_FACT}",
    )
    assert "lantern" in _facing(targeted).lower()
    listen = _chat(monkeypatch, "I listen.", "Soft anxious whispers drift about a missing patrol.")
    listen_text = _facing(listen).lower()
    assert "whisper" not in listen_text
    assert "lantern" not in listen_text
    assert _complete(_facing(listen))


def test_generic_engine_has_no_frontier_gate_special_case():
    text = Path("game/diegetic_fallback_narration.py").read_text(encoding="utf-8")
    lowered = text.lower()
    assert "threadbare watchers" not in lowered
    assert "frontier_gate" not in lowered
    assert "muddy gate line" not in lowered
    assert "gate serjeant" not in lowered
