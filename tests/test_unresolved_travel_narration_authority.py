"""PR-BF: unresolved travel must not be narrated as a successful transition.

Cinderwatch / frontier_gate cases are calibration residue only.
The engine contract is destination-independent.
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
from game.exploration import resolve_exploration_action
from game.final_emission_scene_emit_integrity import (
    _SCENE_EMIT_INTEGRITY_SAFE_FALLBACK_LINE,
    _collect_scene_emit_integrity_failure_reasons,
    _scene_emit_integrity_global_fallback_selection,
)
from game.intent_parser import (
    looks_like_local_physical_movement,
    parse_freeform_to_action,
)
from game.narration_state_consistency import (
    apply_destination_arrival_realization_to_gm,
    apply_stay_leave_narration_agreement_to_gm,
)
from game.scene_actions import normalize_scene_action
from game.upstream_response_repairs import _action_result_summary
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _patch_storage

HISTORICAL_T6 = "I'll go chase that closed western cart road you mentioned."
HISTORICAL_T6_GM = (
    "The muddy lane west of the gate stretches thin and quiet, slick with recent rain "
    "and marked by ruts where carts once passed. You set off briskly, the glint of "
    "lanterns fading behind you as the Cinderwatch gate district recedes into the mist. "
    "The closed western cart road you aim…"
)
CALIBRATION_ENGINE_TERMS = (
    "old_milestone",
    "frontier_gate",
    "Cinderwatch",
    "western cart road",
)
GENERIC_ENGINE_FILES = (
    Path("game/narration_state_consistency.py"),
    Path("game/final_emission_scene_emit_integrity.py"),
    Path("game/exploration.py"),
    Path("game/upstream_response_repairs.py"),
)


def _envelope(scene_id: str, exits: list[dict], **extra) -> dict:
    scene = default_scene(scene_id)
    inner = scene["scene"]
    inner["id"] = scene_id
    inner["location"] = extra.pop("location", scene_id.replace("_", " ").title())
    inner["exits"] = exits
    inner.update(extra)
    return scene


MOSSY = _envelope(
    "mossy_crossing",
    [
        {"label": "Take the pine trail", "target_scene_id": "hill_shrine"},
        {"label": "Take the cedar trail", "target_scene_id": "mill_pond"},
    ],
    location="Mossy Crossing",
    summary="Two wet trails split beside a moss-slick marker stone.",
    visible_facts=["A moss-slick marker stone leans at the fork.", "Pine needles mat the northern path."],
)
SHRINE = _envelope(
    "hill_shrine",
    [{"label": "Return to the crossing", "target_scene_id": "mossy_crossing"}],
    location="Hill Shrine",
    summary="A low shrine sits above the pine trail.",
    visible_facts=["A stone basin holds rainwater.", "Pine incense chars in a cracked dish."],
)


def _resolve(text: str, envelope: dict, known: list[str] | None = None) -> dict:
    parsed = parse_freeform_to_action(text, envelope)
    action = normalize_scene_action(parsed)
    ids = known or [
        envelope["scene"]["id"],
        *[
            str(ex.get("target_scene_id") or "")
            for ex in envelope["scene"].get("exits") or []
            if isinstance(ex, dict)
        ],
    ]
    return resolve_exploration_action(
        envelope,
        {"active_scene_id": envelope["scene"]["id"], "turn_counter": 3},
        {},
        action,
        raw_player_text=text,
        list_scene_ids=lambda: [item for item in ids if item],
    )


def _seed_mossy(tmp_path, monkeypatch) -> None:
    _patch_storage(tmp_path, monkeypatch)
    storage._save_json(storage.scene_path("mossy_crossing"), MOSSY)
    storage._save_json(storage.scene_path("hill_shrine"), SHRINE)
    storage._save_json(storage.scene_path("mill_pond"), default_scene("mill_pond"))
    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    session = default_session()
    session["active_scene_id"] = "mossy_crossing"
    session["visited_scene_ids"] = ["mossy_crossing"]
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


def test_historical_t6_set_off_is_not_treated_as_departure():
    gm = apply_stay_leave_narration_agreement_to_gm(
        {"player_facing_text": HISTORICAL_T6_GM, "tags": []},
        resolution={"kind": "travel", "resolved_transition": False, "target_scene_id": None},
        origin_scene_id="frontier_gate",
    )
    text = str((gm or {}).get("player_facing_text") or "")
    assert text == "That destination is not available from here."
    assert "set off" not in text.lower()
    assert "recedes" not in text.lower()


def test_unresolved_travel_does_not_receive_arrival_scene_stock():
    gm = apply_destination_arrival_realization_to_gm(
        {"player_facing_text": "the scene answers with an immediate change", "tags": []},
        resolution={"kind": "travel", "resolved_transition": False, "target_scene_id": None},
        scene=MOSSY,
        player_text="I'll go to the glass observatory.",
    )
    text = str((gm or {}).get("player_facing_text") or "").lower()
    assert "new ground" not in text
    assert "destination_arrival_realization" not in ((gm or {}).get("tags") or [])


def test_successful_travel_may_still_receive_destination_stock():
    gm = apply_destination_arrival_realization_to_gm(
        {"player_facing_text": "the scene answers with an immediate change", "tags": []},
        resolution={
            "kind": "scene_transition",
            "resolved_transition": True,
            "target_scene_id": "hill_shrine",
        },
        scene=SHRINE,
        player_text="I'll take the pine trail.",
    )
    text = str((gm or {}).get("player_facing_text") or "").lower()
    assert "shrine" in text or "basin" in text or "incense" in text
    assert "destination_arrival_realization" in ((gm or {}).get("tags") or [])


def test_integrity_fallback_uses_safe_line_when_travel_is_unresolved():
    resolution = {"kind": "travel", "resolved_transition": False, "target_scene_id": None}
    reasons, _named = _collect_scene_emit_integrity_failure_reasons(
        authoritative_resolution=resolution,
        session={"active_scene_id": "mossy_crossing"},
        scene=MOSSY,
        scene_id="mossy_crossing",
    )
    assert "unresolved_travel" in reasons
    selected = _scene_emit_integrity_global_fallback_selection(
        MOSSY,
        "mossy_crossing",
        authoritative_resolution=resolution,
        session={"active_scene_id": "mossy_crossing"},
        world=None,
        res_kind="travel",
        response_type_required="action_outcome",
    )
    assert selected.text == _SCENE_EMIT_INTEGRITY_SAFE_FALLBACK_LINE
    assert "new ground" not in selected.text.lower()


def test_integrity_fallback_keeps_arrival_stock_after_successful_transition():
    resolution = {
        "kind": "scene_transition",
        "resolved_transition": True,
        "target_scene_id": "hill_shrine",
    }
    reasons, _named = _collect_scene_emit_integrity_failure_reasons(
        authoritative_resolution=resolution,
        session={"active_scene_id": "hill_shrine"},
        scene=SHRINE,
        scene_id="hill_shrine",
    )
    assert "unresolved_travel" not in reasons
    selected = _scene_emit_integrity_global_fallback_selection(
        SHRINE,
        "hill_shrine",
        authoritative_resolution=resolution,
        session={"active_scene_id": "hill_shrine"},
        world=None,
        res_kind="scene_transition",
        response_type_required="action_outcome",
    )
    assert selected.text != _SCENE_EMIT_INTEGRITY_SAFE_FALLBACK_LINE
    low = selected.text.lower()
    assert "shrine" in low or "basin" in low or "incense" in low or "hill shrine" in low


def test_unresolved_hint_does_not_license_current_scene_stock():
    resolution = _resolve("I'll go to the glass observatory.", MOSSY)
    assert resolution.get("resolved_transition") is not True
    hint = str(resolution.get("hint") or "").lower()
    assert "do not imply" in hint
    assert "current scene and intent" not in hint


def test_action_result_summary_does_not_claim_position_change_when_unresolved():
    assert _action_result_summary(
        {"kind": "travel", "resolved_transition": False}
    ) == "the attempt meets resistance"
    assert "position" in _action_result_summary(
        {"kind": "scene_transition", "resolved_transition": True, "target_scene_id": "hill_shrine"}
    )


def test_valid_authored_transition_mutates_scene(tmp_path, monkeypatch):
    _seed_mossy(tmp_path, monkeypatch)
    data = _chat(monkeypatch, "I'll take the pine trail.", "You climb the pine trail to the shrine.")
    res = data.get("resolution") or {}
    assert res.get("resolved_transition") is True
    assert res.get("target_scene_id") == "hill_shrine"
    assert storage.load_session().get("active_scene_id") == "hill_shrine"
    facing = _facing(data).lower()
    assert "not available from here" not in facing
    assert "way stays unfinished" not in facing
    assert facing.strip()


def test_unknown_destination_does_not_change_scene_or_imply_arrival(tmp_path, monkeypatch):
    _seed_mossy(tmp_path, monkeypatch)
    data = _chat(
        monkeypatch,
        "I'll go to the glass observatory.",
        "You arrive at the glass observatory and the dome opens.",
    )
    res = data.get("resolution") or {}
    assert res.get("kind") == "travel"
    assert res.get("resolved_transition") is not True
    assert storage.load_session().get("active_scene_id") == "mossy_crossing"
    facing = _facing(data).lower()
    assert "arrive" not in facing
    assert "dome" not in facing
    assert "new ground" not in facing


def test_ambiguous_trail_does_not_guess_or_arrive(tmp_path, monkeypatch):
    _seed_mossy(tmp_path, monkeypatch)
    data = _chat(monkeypatch, "I'll take the trail.", "You walk the trail until the shrine appears ahead.")
    res = data.get("resolution") or {}
    assert res.get("resolved_transition") is not True
    assert storage.load_session().get("active_scene_id") == "mossy_crossing"
    facing = _facing(data).lower()
    assert "shrine appears" not in facing
    assert "new ground" not in facing


def test_local_movement_is_not_failed_scene_travel():
    text = "I step closer."
    assert looks_like_local_physical_movement(text) is True
    parsed = parse_freeform_to_action(text, MOSSY)
    assert (parsed or {}).get("type") == "custom"
    resolution = _resolve(text, MOSSY)
    assert resolution.get("kind") == "custom"
    assert resolution.get("resolved_transition") is not True


def test_observe_is_not_travel(tmp_path, monkeypatch):
    _seed_mossy(tmp_path, monkeypatch)
    data = _chat(monkeypatch, "I look around.", "A moss-slick marker stone leans at the fork.")
    res = data.get("resolution") or {}
    assert res.get("kind") == "observe"
    assert storage.load_session().get("active_scene_id") == "mossy_crossing"


def test_http_historical_t6_does_not_narrate_departure(tmp_path, monkeypatch):
    _patch_storage(tmp_path, monkeypatch)
    gate = default_scene("frontier_gate")
    storage._save_json(storage.scene_path("frontier_gate"), gate)
    storage._save_json(storage.scene_path("old_milestone"), default_scene("old_milestone"))
    storage._save_json(storage.scene_path("market_quarter"), default_scene("market_quarter"))
    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    session["visited_scene_ids"] = ["frontier_gate"]
    storage.save_session(session)
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")
    data = _chat(monkeypatch, HISTORICAL_T6, HISTORICAL_T6_GM)
    res = data.get("resolution") or {}
    assert res.get("kind") == "travel"
    assert res.get("resolved_transition") is not True
    assert storage.load_session().get("active_scene_id") == "frontier_gate"
    facing = _facing(data).lower()
    assert "set off" not in facing
    assert "recedes" not in facing
    assert "new ground" not in facing


def test_generic_engine_files_have_no_calibration_destination_special_cases():
    for path in GENERIC_ENGINE_FILES:
        text = path.read_text(encoding="utf-8")
        for term in CALIBRATION_ENGINE_TERMS:
            assert term not in text, f"{path} contains calibration term {term!r}"
