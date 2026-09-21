"""PR-AG: generalized destination-exit resolution.

Cinderwatch / old_milestone cases are calibration regression only.
Scenario-independent fixtures must not reuse that vocabulary.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from game import storage
from game.api import app
from game.defaults import default_scene, default_world
from game.exploration import resolve_exploration_action
from game.intent_parser import parse_freeform_to_action
from game.interaction_context import inspect as inspect_interaction_context
from game.narration_state_consistency import apply_stay_leave_narration_agreement_to_gm
from game.scene_actions import normalize_scene_action
from game.scene_destination_binding import resolve_authored_exit_from_player_travel
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _seed_campaign_start_storage

CALIBRATION_ENGINE_TERMS = (
    "old_milestone",
    "frontier_gate",
    "Cinderwatch",
    "notice_patrol_route",
    "Captain Thoran",
)
GENERIC_ENGINE_FILES = (
    Path("game/scene_destination_binding.py"),
    Path("game/intent_parser.py"),
    Path("game/exploration.py"),
    Path("game/narration_state_consistency.py"),
)


def _envelope(scene_id: str, exits: list[dict], **extra) -> dict:
    scene = {"id": scene_id, "location": extra.pop("location", scene_id.replace("_", " ").title()), "exits": exits}
    scene.update(extra)
    return {"scene": scene}


def _parse_and_resolve(text: str, envelope: dict, known: list[str] | None = None) -> dict:
    parsed = parse_freeform_to_action(text, envelope)
    assert parsed is not None
    action = normalize_scene_action(parsed)
    ids = known or [envelope["scene"]["id"], *[
        str(ex.get("target_scene_id") or "")
        for ex in envelope["scene"].get("exits") or []
        if isinstance(ex, dict)
    ]]
    return resolve_exploration_action(
        envelope,
        {},
        {},
        action,
        raw_player_text=text,
        list_scene_ids=lambda: [item for item in ids if item],
    )


def _target(parsed: dict | None) -> str:
    if not parsed:
        return ""
    return str(parsed.get("target_scene_id") or parsed.get("targetSceneId") or "").strip()


# ---------------------------------------------------------------------------
# Scenario-independent generalization
# ---------------------------------------------------------------------------

MOSSY = _envelope(
    "mossy_crossing",
    [
        {"label": "Take the pine trail", "target_scene_id": "hill_shrine"},
        {"label": "Take the cedar trail", "target_scene_id": "mill_pond"},
    ],
)
ORCHARD = _envelope(
    "ruined_orchard",
    [{"label": "Return to the stone bridge", "target_scene_id": "stone_bridge"}],
)
HARBOR = _envelope(
    "salt_harbor",
    [
        {"label": "Climb the watch stair", "target_scene_id": "gull_tower"},
        {"label": "Hire the ferry", "target_scene_id": "oyster_islet"},
    ],
)

EXIT_LABEL_CASES = [
    (MOSSY, "I'll take the pine trail.", "hill_shrine"),
    (MOSSY, "I follow the cedar trail.", "mill_pond"),
    (HARBOR, "I'll climb the watch stair.", "gull_tower"),
    (HARBOR, "Let's hire the ferry.", "oyster_islet"),
]
DESTINATION_CASES = [
    (MOSSY, "I'll head to the hill shrine.", "hill_shrine"),
    (MOSSY, "Let's go to the mill pond.", "mill_pond"),
    (ORCHARD, "I'm heading back toward the stone bridge.", "stone_bridge"),
    (HARBOR, "I'll go to Gull Tower.", "gull_tower"),
]
RETURN_CASES = [
    (ORCHARD, "I'll head back.", "stone_bridge"),
    (ORCHARD, "Let's go back.", "stone_bridge"),
    (ORCHARD, "I'll return to the stone bridge.", "stone_bridge"),
    (ORCHARD, "Alright. I'll head back to the bridge.", "stone_bridge"),
]


@pytest.mark.parametrize("envelope,text,expected", EXIT_LABEL_CASES)
def test_general_exit_label_resolves(envelope, text, expected):
    parsed = parse_freeform_to_action(text, envelope)
    assert _target(parsed) == expected
    resolution = _parse_and_resolve(text, envelope)
    assert resolution.get("resolved_transition") is True
    assert resolution.get("target_scene_id") == expected


@pytest.mark.parametrize("envelope,text,expected", DESTINATION_CASES)
def test_general_destination_reference_resolves(envelope, text, expected):
    parsed = parse_freeform_to_action(text, envelope)
    assert _target(parsed) == expected
    resolution = _parse_and_resolve(text, envelope)
    assert resolution.get("resolved_transition") is True
    assert resolution.get("target_scene_id") == expected


@pytest.mark.parametrize("envelope,text,expected", RETURN_CASES)
def test_general_return_back_resolves_from_authored_context(envelope, text, expected):
    parsed = parse_freeform_to_action(text, envelope)
    assert _target(parsed) == expected
    resolution = _parse_and_resolve(text, envelope)
    assert resolution.get("resolved_transition") is True
    assert resolution.get("target_scene_id") == expected


def test_multiple_exits_are_distinguished_not_defaulted():
    pine = _parse_and_resolve("I'll take the pine trail.", MOSSY)
    cedar = _parse_and_resolve("I'll take the cedar trail.", MOSSY)
    assert pine.get("target_scene_id") == "hill_shrine"
    assert cedar.get("target_scene_id") == "mill_pond"


def test_ambiguous_shared_noun_does_not_guess():
    parsed = parse_freeform_to_action("I'll take the trail.", MOSSY)
    assert _target(parsed) == ""
    if parsed:
        resolution = _parse_and_resolve("I'll take the trail.", MOSSY)
        assert resolution.get("resolved_transition") is not True


def test_unavailable_destination_is_not_invented():
    parsed = parse_freeform_to_action("I'll go to the glass observatory.", MOSSY)
    assert _target(parsed) == ""
    resolution = _parse_and_resolve("I'll go to the glass observatory.", MOSSY)
    assert resolution.get("resolved_transition") is not True
    assert resolution.get("target_scene_id") in {None, ""}


def test_question_mentioning_exit_does_not_travel():
    parsed = parse_freeform_to_action("What lies beyond the pine trail?", MOSSY)
    assert parsed is None or parsed.get("type") not in {"scene_transition", "travel"} or not _target(parsed)
    tid = resolve_authored_exit_from_player_travel(
        "What lies beyond the pine trail?",
        MOSSY["scene"]["exits"],
    )
    assert tid is None


def test_unresolved_travel_narration_does_not_claim_departure():
    gm = apply_stay_leave_narration_agreement_to_gm(
        {
            "player_facing_text": (
                "You turn away from the crossing and walk the pine trail until the shrine appears ahead."
            ),
            "tags": [],
        },
        resolution={
            "kind": "travel",
            "resolved_transition": False,
            "target_scene_id": None,
        },
        origin_scene_id="mossy_crossing",
    )
    text = str((gm or {}).get("player_facing_text") or "").lower()
    assert "not available from here" in text
    assert "shrine appears" not in text
    assert "turn away" not in text


def test_successful_transition_may_describe_departure():
    gm = apply_stay_leave_narration_agreement_to_gm(
        {"player_facing_text": "You leave along the pine trail.", "tags": []},
        resolution={
            "kind": "scene_transition",
            "resolved_transition": True,
            "target_scene_id": "hill_shrine",
            "metadata": {"parser_lane": "authored_exit_resolution"},
        },
        origin_scene_id="mossy_crossing",
    )
    text = str((gm or {}).get("player_facing_text") or "").lower()
    assert "leave" in text
    assert "not available" not in text


@pytest.mark.parametrize(
    "scene_id,label,dest_id,player",
    [
        ("amber_meadow", "Take the reed causeway", "heron_holt", "I'll take the reed causeway."),
        ("copper_switch", "Descend the service ladder", "pump_cistern", "I'll descend the service ladder."),
        ("ivory_gallery", "Pass through the velvet curtain", "echo_salon", "I'll pass through the velvet curtain."),
    ],
)
def test_parameterized_exit_labels_follow_data_not_vocabulary(scene_id, label, dest_id, player):
    envelope = _envelope(scene_id, [{"label": label, "target_scene_id": dest_id}])
    resolution = _parse_and_resolve(player, envelope, known=[scene_id, dest_id])
    assert resolution.get("resolved_transition") is True
    assert resolution.get("target_scene_id") == dest_id


@pytest.mark.parametrize(
    "scene_id,label,dest_id,player",
    [
        ("amber_meadow", "Take the reed causeway", "heron_holt", "I'll head to the heron holt."),
        ("copper_switch", "Descend the service ladder", "pump_cistern", "Let's go to the pump cistern."),
        ("ivory_gallery", "Pass through the velvet curtain", "echo_salon", "I'm heading to Echo Salon."),
    ],
)
def test_parameterized_destination_names_follow_target_ids(scene_id, label, dest_id, player):
    envelope = _envelope(scene_id, [{"label": label, "target_scene_id": dest_id}])
    resolution = _parse_and_resolve(player, envelope, known=[scene_id, dest_id])
    assert resolution.get("resolved_transition") is True
    assert resolution.get("target_scene_id") == dest_id


def test_generic_engine_files_have_no_new_cinderwatch_special_cases():
    """Hard gate: generic resolver must not encode calibration-world identifiers."""
    for path in GENERIC_ENGINE_FILES:
        text = path.read_text(encoding="utf-8")
        if path.name == "intent_parser.py":
            # Existing file already mentions some calibration fixtures in older helpers.
            # Ban only a new scene-id special case of the form current_scene == "...".
            assert 'current_scene == "old_milestone"' not in text
            assert 'current_scene == "frontier_gate"' not in text
            assert '== "old_milestone" and' not in text
            continue
        if path.name == "exploration.py":
            assert 'if current_scene' not in text
            continue
        lowered = text
        for term in CALIBRATION_ENGINE_TERMS:
            assert term not in lowered, f"{path} contains calibration term {term!r}"


# ---------------------------------------------------------------------------
# Cinderwatch regression (calibration content, not the engine contract)
# ---------------------------------------------------------------------------

def _milestone_scene() -> dict:
    return default_scene("old_milestone")


def _gate_scene() -> dict:
    return default_scene("frontier_gate")


@pytest.mark.parametrize(
    "text",
    [
        "I'll head back to the gate.",
        "I'll head back to Cinderwatch Gate.",
        "Let's go back.",
        "I'm heading back toward the frontier gate.",
        "I'll return to Cinderwatch Gate.",
    ],
)
def test_cinderwatch_natural_return_binds_authored_exit(text):
    parsed = parse_freeform_to_action(text, _milestone_scene())
    assert _target(parsed) == "frontier_gate"
    resolution = _parse_and_resolve(
        text,
        _milestone_scene(),
        known=["old_milestone", "frontier_gate"],
    )
    assert resolution.get("resolved_transition") is True
    assert resolution.get("target_scene_id") == "frontier_gate"


def test_cinderwatch_pursuit_still_binds_old_milestone():
    text = "Fine. I'll follow the missing patrol rumor along that northwest mud track."
    parsed = parse_freeform_to_action(text, _gate_scene())
    assert _target(parsed) == "old_milestone"


def _seed_at_old_milestone_http(tmp_path, monkeypatch):
    _seed_campaign_start_storage(tmp_path, monkeypatch)
    storage._save_json(storage.scene_path("frontier_gate"), _gate_scene())
    storage._save_json(storage.scene_path("old_milestone"), _milestone_scene())
    world = default_world()
    storage._save_json(storage.WORLD_PATH, world)
    session = storage.load_session()
    session["active_scene_id"] = "old_milestone"
    session["visited_scene_ids"] = ["frontier_gate", "old_milestone"]
    storage.save_session(session)


def test_http_head_back_to_the_gate_transitions(tmp_path, monkeypatch):
    _seed_at_old_milestone_http(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr(
            "game.api.call_gpt",
            lambda _messages: _gm_response(
                "You turn away from the weathered milestone and the gatehouse appears ahead."
            ),
        )
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "I'll head back to the gate."})
    assert resp.status_code == 200
    data = resp.json()
    res = data.get("resolution") or {}
    assert res.get("resolved_transition") is True
    assert res.get("target_scene_id") == "frontier_gate"
    assert data.get("session", {}).get("active_scene_id") == "frontier_gate"
    text = str((data.get("gm_output") or {}).get("player_facing_text") or "").lower()
    assert "gatehouse appears" not in text or res.get("resolved_transition") is True


def test_http_post_return_observe_stays_at_gate(tmp_path, monkeypatch):
    _seed_at_old_milestone_http(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: _gm_response("You remain at the milestone."))
        client = TestClient(app)
        first = client.post("/api/chat", json={"text": "I'll head back to the gate."})
    assert first.status_code == 200
    assert first.json().get("session", {}).get("active_scene_id") == "frontier_gate"
    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", lambda _messages: _gm_response("Rain needles the eastern gate."))
        client = TestClient(app)
        second = client.post("/api/chat", json={"text": "I look around."})
    assert second.status_code == 200
    assert second.json().get("session", {}).get("active_scene_id") == "frontier_gate"
    ctx = inspect_interaction_context(second.json().get("session") or {})
    assert str(ctx.get("active_interaction_target_id") or "") == ""


def test_http_unresolved_unavailable_place_does_not_move(tmp_path, monkeypatch):
    _seed_at_old_milestone_http(tmp_path, monkeypatch)
    with monkeypatch.context() as m:
        m.setattr(
            "game.api.call_gpt",
            lambda _messages: _gm_response("You leave the milestone and arrive at House Verevin."),
        )
        client = TestClient(app)
        resp = client.post("/api/chat", json={"text": "I'll go to House Verevin."})
    assert resp.status_code == 200
    data = resp.json()
    assert data.get("session", {}).get("active_scene_id") == "old_milestone"
    assert (data.get("resolution") or {}).get("resolved_transition") is not True
    text = str((data.get("gm_output") or {}).get("player_facing_text") or "").lower()
    assert "arrive at house verevin" not in text
    assert "you leave the milestone" not in text
