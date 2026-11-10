"""Provider-free production chat coverage for post-NPC conversational handoff.

These tests post real /api/chat turns. They do not assert a helper label in isolation.
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from game import storage
from game.api import app
from tests.helpers.storage_isolation import install
from tests.pr_play_79df3_harness import seed_gate

CLUE = "northwest mud track"
CAPTAIN = "patrol went missing near the old milestone"
HIDDEN = (
    "Ash Cowl",
    "coordinated signal",
    "written list paid for in silver",
    "noble house is watching",
)


def _env(monkeypatch):
    monkeypatch.setenv("ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT", "1")
    monkeypatch.setenv("ASHEN_DISABLE_PROVIDER_CALLS", "1")
    monkeypatch.setenv("ASHEN_DISABLE_LIVE_INTERPRETATION", "1")
    monkeypatch.setenv("ASHEN_DISABLE_EXPRESSION_GENERATION", "1")
    monkeypatch.setenv("ASHEN_DISABLE_PROVIDER_RETRIES", "1")
    monkeypatch.setenv("ASHEN_PROVIDER_REQUEST_LIMIT", "0")
    for name in (
        "ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION",
        "ASHEN_EXPERIMENTAL_DYNAMIC_NPCS",
        "ASHEN_EXPERIMENTAL_PLAYER_INITIATIVE",
        "ASHEN_EXPERIMENTAL_WORLD_IMPROVISATION",
        "OPENAI_API_KEY",
    ):
        monkeypatch.delenv(name, raising=False)
    from tests.helpers.live_model_guard import production_call_gpt

    # Provider calls stay disabled. Restoring the production wrapper lets the
    # disabled-provider sentence return without constructing an OpenAI client.
    monkeypatch.setattr("game.gm.call_gpt", production_call_gpt())
    monkeypatch.setattr("game.api.call_gpt", production_call_gpt())


def _say(client, text):
    response = client.post("/api/chat?ui_mode=player", json={"text": text})
    assert response.status_code == 200, response.text
    body = response.json()
    visible = str((body.get("gm_output") or {}).get("player_facing_text") or "")
    session = storage.load_session()
    log = storage.load_log()
    resolution = log[-1].get("resolution") if log and isinstance(log[-1], dict) else {}
    resolution = resolution if isinstance(resolution, dict) else {}
    meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    publication = session.get("last_publication") if isinstance(session.get("last_publication"), dict) else {}
    return {
        "visible": visible,
        "scene": session.get("active_scene_id"),
        "clues": set((session.get("clue_knowledge") or {}).keys()),
        "character": json.dumps(storage.load_character(), sort_keys=True),
        "kind": resolution.get("kind"),
        "publication": publication.get("visible"),
        "completed": meta.get("gameplay_publication_completed"),
        "requests": (body.get("usage") or {}).get("requests") if isinstance(body.get("usage"), dict) else None,
    }


@pytest.fixture
def client(tmp_path, monkeypatch):
    _env(monkeypatch)
    install(tmp_path)
    seed_gate(tmp_path, monkeypatch)
    http = TestClient(app)
    http.__enter__()
    try:
        yield http
    finally:
        http.__exit__(None, None, None)


def test_recorded_handoff_leaves_the_previous_npc_line(client):
    captain = _say(client, "You mentioned the patrol. What have you heard?")
    assert "Guard Captain" in captain["visible"]
    assert CAPTAIN in captain["visible"]
    assert captain["scene"] == "frontier_gate"

    approach = _say(client, "I walk over to the notice board and put a hand on the frame.")
    assert "notice board" in approach["visible"].lower()
    assert "frame" in approach["visible"].lower()
    assert "not a supported action" not in approach["visible"].lower()
    assert "not an established destination" not in approach["visible"]
    assert "have not moved" not in approach["visible"].lower()
    assert CAPTAIN not in approach["visible"]
    assert CLUE not in approach["visible"]
    assert approach["scene"] == "frontier_gate"
    assert "notice_patrol_route" not in approach["clues"]
    assert approach["publication"] == approach["visible"]
    assert approach["completed"] is not True

    reading = _say(client, "Read me the missing-patrol notice, not the tax lines.")
    assert CLUE in reading["visible"]
    assert CAPTAIN not in reading["visible"]
    assert "notice_patrol_route" in reading["clues"]
    assert reading["scene"] == "frontier_gate"
    before_copy = reading["character"]

    copying = _say(client, "I try to copy the patrol warning onto my sleeve with a bit of mud so I won't forget the wording.")
    assert "nothing was written" in copying["visible"].lower()
    assert "no established object matches" in copying["visible"].lower()
    assert "no usable writing medium" in copying["visible"].lower()
    assert CAPTAIN not in copying["visible"]
    assert copying["character"] == before_copy
    assert copying["scene"] == "frontier_gate"
    assert copying["completed"] is not True

    recall = _say(client, "What did that notice say about where the patrol was last seen?")
    assert CLUE in recall["visible"]
    assert "I cannot tell who that is addressed to" not in recall["visible"]
    assert CAPTAIN not in recall["visible"]
    assert recall["scene"] == "frontier_gate"
    for secret in HIDDEN:
        assert secret.casefold() not in recall["visible"].casefold()


def test_explicit_repetition_stays_with_the_captain(client):
    _say(client, "You mentioned the patrol. What have you heard?")
    repeated = _say(client, "Could you repeat that?")
    assert CAPTAIN in repeated["visible"]
    assert CLUE not in repeated["visible"]
    again = _say(client, "What did the captain just say?")
    assert CAPTAIN in again["visible"]
    assert CLUE not in again["visible"]
    warning = _say(client, "Tell me the warning again.")
    assert CAPTAIN in warning["visible"]
    assert "notice_patrol_route" not in warning["clues"]


def test_follow_up_can_return_to_the_captain_after_the_notice(client):
    _say(client, "You mentioned the patrol. What have you heard?")
    _say(client, "Read me the missing-patrol notice, not the tax lines.")
    asked = _say(client, "Ask the captain about the notice.")
    assert asked["scene"] == "frontier_gate"
    assert "not an established destination" not in asked["visible"]
    assert "Guard Captain" in asked["visible"] or asked["kind"] in {"question", "interact"}


def test_genuine_travel_still_changes_scene(client):
    moved = _say(client, "I follow the missing patrol rumor toward the northwest track.")
    assert moved["scene"] == "old_milestone"
    assert "Old Milestone" in moved["visible"]
    refused = _say(client, "I step back from the notice board.")
    assert refused["scene"] == "old_milestone"
    assert "not supported here" in refused["visible"]
    assert refused["completed"] is not True


def test_unknown_destination_and_unknown_object_stay_uninvented(client):
    before = _say(client, "You mentioned the patrol. What have you heard?")
    unknown_place = _say(client, "I walk to the glass observatory.")
    assert "not an established destination" in unknown_place["visible"]
    assert unknown_place["scene"] == "frontier_gate"
    assert unknown_place["clues"] == before["clues"]
    unknown_object = _say(client, "I examine the glass observatory.")
    assert CLUE not in unknown_object["visible"]
    assert unknown_object["scene"] == "frontier_gate"
    assert "notice_patrol_route" not in unknown_object["clues"] - before["clues"]


def test_hidden_notice_detail_and_unknown_patrol_color_are_not_invented(client):
    hidden = _say(client, "What is the noble agent's signal?")
    for secret in HIDDEN:
        assert secret.casefold() not in hidden["visible"].casefold()
    color = _say(client, "What color cloak was the missing patrol wearing?")
    assert CLUE not in color["visible"]
    for invented in ("crimson", "scarlet", "azure", "emerald"):
        assert invented not in color["visible"].casefold()
    assert color["scene"] == "frontier_gate"


def test_two_named_targets_are_not_collapsed_to_the_notice(client):
    _say(client, "You mentioned the patrol. What have you heard?")
    mixed = _say(client, "What do the notice board and the glass dial say?")
    assert CLUE not in mixed["visible"]
    assert "notice_patrol_route" not in mixed["clues"]
    assert mixed["scene"] == "frontier_gate"
    assert CAPTAIN not in mixed["visible"]
