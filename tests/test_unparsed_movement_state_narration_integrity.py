"""PR-BL: unparsed or unsuccessful movement must not narrate or commit a transition.

The success signal is resolved_transition (or an equivalent transition flag).
Parser coverage may improve. Integrity does not depend on it.
"""
from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from game import storage
from game.api import _apply_post_gm_updates, app
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
from game.narration_state_consistency import (
    _UNRESOLVED_TRAVEL_TERMINAL,
    apply_stay_leave_narration_agreement_to_gm,
    omit_unowned_transition_scene_update,
    text_asserts_unowned_spatial_transition,
)
from game.scene_actions import normalize_scene_action
from game.scene_destination_binding import extract_travel_destination_phrase
from tests.helpers.turn_pipeline_http_fixtures import _patch_storage

FRONTIER = json.loads(Path("data/scenes/frontier_gate.json").read_text(encoding="utf-8"))


def _envelope(scene_id: str, exits: list[dict], **extra) -> dict:
    scene = default_scene(scene_id)
    inner = scene["scene"]
    inner["id"] = scene_id
    inner["location"] = extra.pop("location", scene_id.replace("_", " ").title())
    inner["exits"] = exits
    inner.update(extra)
    return scene


FERRY = _envelope(
    "ferry_landing",
    [{"label": "Take the stone stair", "target_scene_id": "bell_loft"}],
    location="Ferry Landing",
    summary="A wet landing and a stone stair.",
    visible_facts=["A mooring ring is bolted to the landing."],
    discoverable_clues=[{"id": "stair_clue", "text": "The stone stair climbs to the bell loft."}],
    mode="social",
)
LOFT = _envelope(
    "bell_loft",
    [{"label": "Return to the landing", "target_scene_id": "ferry_landing"}],
    location="Bell Loft",
    summary="A bell loft above the stair.",
    visible_facts=["A bronze bell hangs over the loft."],
)


def _parse(text: str, envelope: dict = FERRY) -> dict | None:
    act = parse_freeform_to_action(text, envelope)
    return act if isinstance(act, dict) else None


def _resolve(text: str, envelope: dict) -> dict:
    parsed = parse_freeform_to_action(text, envelope)
    action = normalize_scene_action(parsed)
    ids = [envelope["scene"]["id"]]
    ids.extend(
        str(ex.get("target_scene_id") or "")
        for ex in envelope["scene"].get("exits") or []
        if isinstance(ex, dict)
    )
    return resolve_exploration_action(
        envelope,
        {"active_scene_id": envelope["scene"]["id"], "turn_counter": 3},
        {},
        action,
        raw_player_text=text,
        list_scene_ids=lambda: [item for item in ids if item],
    )


def test_directional_proceed_reaches_travel_without_compass_exit_bind():
    act = _parse("I proceed northwest.")
    assert act is not None
    assert act.get("type") == "travel"
    assert not act.get("target_scene_id")
    assert extract_travel_destination_phrase("I proceed northwest.") == "northwest"
    resolution = _resolve("I proceed northwest.", FERRY)
    assert resolution.get("kind") == "travel"
    assert resolution.get("resolved_transition") is not True
    assert resolution.get("target_scene_id") in (None, "")


def test_contextual_directional_proceed_stays_unresolved_travel():
    text = "Inclined to take this matter into my own hands, I proceed North-West, as the runner directed."
    act = _parse(text, FRONTIER)
    assert act is not None
    assert act.get("type") == "travel"
    assert act.get("target_scene_id") != "old_milestone"
    resolution = _resolve(text, FRONTIER)
    assert resolution.get("resolved_transition") is not True
    assert resolution.get("target_scene_id") in (None, "")


def test_existing_follow_exit_still_transitions():
    mud = _parse("I follow the northwest mud track.", FRONTIER)
    rumor = _parse("I follow the missing patrol rumor.", FRONTIER)
    assert mud is not None and mud.get("type") == "scene_transition"
    assert mud.get("target_scene_id") == "old_milestone"
    assert rumor is not None and rumor.get("target_scene_id") == "old_milestone"
    resolved = _resolve("I follow the missing patrol rumor.", FRONTIER)
    assert resolved.get("resolved_transition") is True
    assert resolved.get("target_scene_id") == "old_milestone"


def test_bare_compass_head_stays_unresolved_travel():
    act = _parse("I'll head northwest.", FRONTIER)
    assert act is not None
    assert act.get("type") == "travel"
    assert not act.get("target_scene_id")
    resolution = _resolve("I'll head northwest.", FRONTIER)
    assert resolution.get("resolved_transition") is not True


def test_named_destination_proceed_uses_existing_exit():
    act = _parse("I proceed toward the bell loft.")
    assert act is not None
    assert act.get("type") == "scene_transition"
    assert act.get("target_scene_id") == "bell_loft"
    milestone = _parse("I go to the old milestone.", FRONTIER)
    assert milestone is not None
    assert milestone.get("type") == "scene_transition"
    assert milestone.get("target_scene_id") == "old_milestone"


def test_local_movement_and_nonspatial_proceed_are_not_scene_travel():
    local = _parse("I walk a few steps closer to the crates.")
    assert local is not None
    assert local.get("type") == "custom"
    assert (local.get("metadata") or {}).get("parser_lane") == "local_physical_movement"
    beside = _parse("I move beside the notice board.")
    assert beside is not None and beside.get("type") == "custom"
    assert _parse("I proceed with the inspection.") is None
    assert _parse("I proceed with caution.") is None
    question = _parse("I proceed to question the guard.")
    assert question is None or question.get("type") != "travel"
    assert question is None or question.get("type") != "scene_transition"


def test_ownerless_false_arrival_is_not_emitted():
    narration = (
        "Turning north, the directions lead you past the landing. "
        "The ferry road stretches ahead. Your steps into the uncertain stretch beyond the district."
    )
    assert text_asserts_unowned_spatial_transition(narration) is True
    gm = apply_stay_leave_narration_agreement_to_gm(
        {"player_facing_text": narration, "tags": []},
        resolution=None,
    )
    text = str((gm or {}).get("player_facing_text") or "")
    assert text == _UNRESOLVED_TRAVEL_TERMINAL
    assert "stretches ahead" not in text.lower()
    assert "lead you past" not in text.lower()


def test_ownerless_false_scene_update_is_not_adopted():
    proposed = {
        "visible_facts_add": ["You have reached the north ferry road beyond the landing."],
        "discoverable_clues_add": ["A snapped signal cloth lies along that road."],
        "hidden_facts_add": ["Someone watches the road from the trees."],
        "mode": "exploration",
    }
    resolution = {"kind": None, "resolved_transition": None, "target_scene_id": None}
    kept = omit_unowned_transition_scene_update(proposed, resolution)
    assert kept is not None
    assert kept.get("visible_facts_add") == []
    assert kept.get("discoverable_clues_add") == []
    assert kept.get("hidden_facts_add") == []
    assert "mode" not in kept

    session = {"scene_runtime": {}, "runtime_scene_overlays": {}, "clue_knowledge": {}}
    gm = {
        "player_facing_text": "You have reached the north ferry road.",
        "tags": [],
        "scene_update": proposed,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    scene_out, _, _, _, _ = _apply_post_gm_updates(
        gm, FERRY, session, {"event_log": []}, {"in_combat": False}, resolution=resolution
    )
    blob = json.dumps(scene_out)
    overlay = json.dumps(session.get("runtime_scene_overlays") or {})
    assert "signal cloth" not in blob.lower()
    assert "signal cloth" not in overlay.lower()
    assert "north ferry road" not in blob.lower()
    assert scene_out["scene"]["id"] == "ferry_landing"
    assert scene_out["scene"].get("mode") != "exploration"


def test_same_scene_update_survives_when_no_transition_occurred():
    proposed = {"visible_facts_add": ["The mooring ring has worked loose."]}
    resolution = {"kind": "custom", "resolved_transition": False, "target_scene_id": None}
    kept = omit_unowned_transition_scene_update(proposed, resolution)
    assert kept == proposed
    session = {"scene_runtime": {}, "runtime_scene_overlays": {}, "clue_knowledge": {}}
    gm = {
        "player_facing_text": "You step closer to the mooring ring.",
        "tags": [],
        "scene_update": proposed,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
    }
    scene_out, _, _, _, _ = _apply_post_gm_updates(
        gm, FERRY, session, {"event_log": []}, {"in_combat": False}, resolution=resolution
    )
    assert "The mooring ring has worked loose." in scene_out["scene"]["visible_facts"]


def test_local_movement_narration_is_not_rewritten():
    text = "You step closer to the notice board."
    gm = apply_stay_leave_narration_agreement_to_gm(
        {"player_facing_text": text, "tags": []},
        resolution={"kind": "custom", "resolved_transition": False, "metadata": {"parser_lane": "local_physical_movement"}},
    )
    assert (gm or {}).get("player_facing_text") == text
    for allowed in (
        "You move beside the gate.",
        "You cross to the other side of the room.",
        "You walk a few steps closer to the crates.",
    ):
        assert text_asserts_unowned_spatial_transition(allowed) is False


def test_successful_transition_keeps_destination_narration():
    narration = "You follow the stone stair and arrive at the bell loft. The bronze bell hangs overhead."
    gm = apply_stay_leave_narration_agreement_to_gm(
        {"player_facing_text": narration, "tags": []},
        resolution={
            "kind": "scene_transition",
            "resolved_transition": True,
            "target_scene_id": "bell_loft",
            "metadata": {"parser_lane": "actionable_stay_leave_or_pursuit"},
        },
        origin_scene_id="ferry_landing",
    )
    text = str((gm or {}).get("player_facing_text") or "")
    assert text == narration
    assert _UNRESOLVED_TRAVEL_TERMINAL not in text
    decorative = {
        "visible_facts_add": ["Rain beads on the bronze bell."],
        "mode": "exploration",
    }
    kept = omit_unowned_transition_scene_update(
        decorative,
        {"kind": "scene_transition", "resolved_transition": True, "target_scene_id": "bell_loft"},
    )
    assert kept == decorative


def _seed_ferry(tmp_path, monkeypatch) -> None:
    _patch_storage(tmp_path, monkeypatch)
    storage._save_json(storage.scene_path("ferry_landing"), FERRY)
    storage._save_json(storage.scene_path("bell_loft"), LOFT)
    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    session = default_session()
    session["active_scene_id"] = "ferry_landing"
    session["visited_scene_ids"] = ["ferry_landing"]
    storage.save_session(session)
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")


def test_human_shaped_cascade_does_not_commit_destination_b(tmp_path, monkeypatch):
    _seed_ferry(tmp_path, monkeypatch)
    false_arrival = (
        "You leave the landing behind. The north road stretches ahead, "
        "and you arrive at the cedar mill."
    )

    def _gpt(_messages):
        return {
            "player_facing_text": false_arrival,
            "tags": [],
            "scene_update": {
                "visible_facts_add": ["You have reached the cedar mill road."],
                "discoverable_clues_add": ["A snapped signal cloth lies at the cedar mill."],
                "hidden_facts_add": ["A watcher stands past the cedar mill."],
                "mode": "exploration",
            },
            "activate_scene_id": "bell_loft",
            "new_scene_draft": {"id": "cedar_mill", "location": "Cedar Mill", "summary": "Invented."},
            "world_updates": None,
            "suggested_action": None,
            "debug_notes": "",
        }

    monkeypatch.setattr("game.api.call_gpt", _gpt)
    client = TestClient(app)
    resp = client.post("/api/chat", json={"text": "I proceed north."})
    assert resp.status_code == 200
    data = resp.json()
    resolution = data.get("resolution") or {}
    assert resolution.get("resolved_transition") is not True
    session = storage.load_session()
    assert session.get("active_scene_id") == "ferry_landing"
    assert "bell_loft" not in (session.get("visited_scene_ids") or [])
    facing = str((data.get("gm_output") or {}).get("player_facing_text") or "").lower()
    assert "cedar mill" not in facing
    assert "arrive" not in facing
    overlay = json.dumps(session.get("runtime_scene_overlays") or {}).lower()
    assert "signal cloth" not in overlay
    assert "cedar mill" not in overlay
    assert "watcher stands" not in overlay
