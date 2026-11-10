"""Session-scoped publication of an already validated investigation sentence.

No provider calls. Deterministic resolution and saved authority stay in place.
"""
import json

import pytest
from fastapi.testclient import TestClient

from game import api, storage
from game import integrated_investigation_narration as integrated
from game import quarantined_investigation_narration as q
from tests.helpers.turn_pipeline_http_fixtures import _gm_response
from tests.test_pr_play_52_quarantined_integration import _facing, _forbid_provider, _seed
from tests.test_pr_play_57_integrated_narration import ROUTE

NOTICE = "I examine the notice board."
BARREL = "I examine the rain barrel."
REPEAT = "I examine the notice board again."
LOOK = "I look around the gate."
UNSAFE = "You find a silver key beneath the board."


def _post(client, text):
    response = client.post("/api/chat?ui_mode=player", json={"text": text})
    assert response.status_code == 200, response.text[:500]
    return response.json()


def _session(texts):
    """One app session. Starlette's portal can raise after the response is done."""
    client = TestClient(api.app)
    client.__enter__()
    try:
        return [_post(client, text) for text in texts]
    finally:
        try:
            client.__exit__(None, None, None)
        except Exception:
            pass


def _bind(monkeypatch, session_id):
    monkeypatch.setenv(q.GATE_ENV, "1")
    monkeypatch.setenv(q.MODE_ENV, "integrated")
    monkeypatch.setenv(q.PUBLICATION_ENV, "1")
    monkeypatch.setenv(q.PUBLICATION_SESSION_ENV, session_id)
    monkeypatch.delenv(q.LIVE_ENV, raising=False)
    monkeypatch.delenv(q.FAULT_ENV, raising=False)
    monkeypatch.delenv(q.SAMPLE_ENV, raising=False)


def _authority():
    session = storage.load_session()
    overlay = (session.get("runtime_scene_overlays") or {}).get("frontier_gate") or {}
    character = storage.load_character()
    return {
        "scene": session.get("active_scene_id"),
        "player": character.get("id"),
        "hp": character.get("hp"),
        "inventory": character.get("inventory"),
        "equipment": character.get("equipment"),
        "clues": overlay.get("discovered_clues"),
        "npcs": session.get("npc_runtime"),
        "quests": session.get("quest_journal"),
        "conditions": storage.load_conditions() if storage.CONDITIONS_PATH.exists() else None,
        "combat": storage.load_combat(),
    }


def test_publication_requires_the_bound_session(tmp_path, monkeypatch):
    calls = _forbid_provider(monkeypatch)
    original = integrated.run_integrated_hook
    monkeypatch.setattr(
        integrated, "run_integrated_hook",
        lambda value: original(value, generator=q._Replay(ROUTE, "")),
    )
    _seed(tmp_path / "off", monkeypatch, "frontier_gate")
    monkeypatch.delenv(q.PUBLICATION_ENV, raising=False)
    q.clear_evidence()
    hidden = _session([NOTICE])[0]
    _seed(tmp_path / "other", monkeypatch, "frontier_gate")
    other_id = storage.load_session()["campaign_run_id"]
    _bind(monkeypatch, "different-session")
    q.clear_evidence()
    foreign = _session([NOTICE])[0]
    _seed(tmp_path / "bound", monkeypatch, "frontier_gate")
    bound_id = storage.load_session()["campaign_run_id"]
    _bind(monkeypatch, bound_id)
    q.clear_evidence()
    published = _session([NOTICE])[0]
    assert _facing({"body": hidden}) == _facing({"body": foreign})
    assert _facing({"body": published}) == ROUTE
    assert "metadata" not in published["gm_output"]
    assert storage.load_log()[-1]["gm_output"]["metadata"]["experimental_integrated_narration"] == "published"
    assert q.evidence_records()[-1]["player_facing_published"] is True
    assert q.evidence_records()[-1]["validation"]["decision"] == "PASS"
    assert other_id != bound_id
    assert calls["openai"] == 0


@pytest.mark.parametrize("sample,fault", [
    ("unsafe", ""),
    ("empty", ""),
    ("malformed", ""),
    ("stub", ""),
    ("stub", "timeout"),
    ("stub", "provider_error"),
])
def test_rejected_narration_stays_off_the_response(tmp_path, monkeypatch, sample, fault):
    _forbid_provider(monkeypatch)
    _seed(tmp_path / "base", monkeypatch, "frontier_gate")
    monkeypatch.delenv(q.GATE_ENV, raising=False)
    baseline = _session([NOTICE])[0]
    _seed(tmp_path / "fault", monkeypatch, "frontier_gate")
    _bind(monkeypatch, storage.load_session()["campaign_run_id"])
    monkeypatch.setenv(q.SAMPLE_ENV, sample)
    monkeypatch.setenv(q.FAULT_ENV, fault)
    q.clear_evidence()
    before = _authority()
    rejected = _session([NOTICE])[0]
    assert _facing({"body": rejected}) == _facing({"body": baseline})
    assert UNSAFE not in _facing({"body": rejected})
    assert "experimental_integrated_narration" not in (rejected["gm_output"].get("metadata") or {})
    record = q.evidence_records()[-1]
    assert record.get("player_facing_published") is not True
    assert record.get("used_fallback") is True
    after = _authority()
    assert after["clues"] == before["clues"] or after["clues"] == [ROUTE]
    assert after["inventory"] == before["inventory"]
    assert after["hp"] == before["hp"]
    assert after["combat"]["in_combat"] is False


def test_rejected_provider_text_uses_the_engine_sentence(tmp_path, monkeypatch):
    _forbid_provider(monkeypatch)
    monkeypatch.setattr(api, "call_gpt", lambda *args, **kwargs: _gm_response(
        "Provider calls are disabled for this run, so no live narration was generated."))
    _seed(tmp_path, monkeypatch, "frontier_gate")
    _bind(monkeypatch, storage.load_session()["campaign_run_id"])
    monkeypatch.setenv(q.SAMPLE_ENV, "unsafe")
    q.clear_evidence()
    body = _session([BARREL])[0]
    text = body["gm_output"]["player_facing_text"]
    assert "silver key" not in text.casefold()
    assert "Provider calls are disabled" not in text
    assert "no new clue is established" in text.casefold()
    assert q.evidence_records()[-1].get("player_facing_published") is not True
    assert "metadata" not in body["gm_output"]
    assert storage.load_log()[-1]["gm_output"]["metadata"]["experimental_integrated_narration"] == "fallback"


def test_four_actions_keep_authority_and_recover(tmp_path, monkeypatch):
    _forbid_provider(monkeypatch)
    monkeypatch.setattr(api, "call_gpt", lambda *args, **kwargs: _gm_response(
        "You examine the evidence. " + ROUTE))
    actions = [NOTICE, BARREL, REPEAT, LOOK]
    _seed(tmp_path / "plain", monkeypatch, "frontier_gate")
    monkeypatch.delenv(q.PUBLICATION_ENV, raising=False)
    monkeypatch.delenv(q.GATE_ENV, raising=False)
    plain = _session(actions)
    plain_authority = _authority()
    _seed(tmp_path / "live", monkeypatch, "frontier_gate")
    _bind(monkeypatch, storage.load_session()["campaign_run_id"])
    original = integrated.run_integrated_hook

    def generate(value):
        text = str(value.get("player_text") or "")
        if "again" in text:
            prose = "You examine the board again and nothing new is established. " + ROUTE
        elif "barrel" in text or "look around" in text:
            prose = "No new clue is established. " + ROUTE
        else:
            prose = ROUTE
        return original(value, generator=q._Replay(prose, ""))

    monkeypatch.setattr(integrated, "run_integrated_hook", generate)
    q.clear_evidence()
    played = _session(actions)
    assert [item["gm_output"]["player_facing_text"] for item in played] != [
        item["gm_output"]["player_facing_text"] for item in plain]
    assert played[0]["gm_output"]["player_facing_text"] == ROUTE
    assert "nothing new" in played[2]["gm_output"]["player_facing_text"].casefold()
    assert ROUTE in played[2]["gm_output"]["player_facing_text"]
    authority = _authority()
    assert authority["clues"] == plain_authority["clues"] == [ROUTE]
    assert authority["inventory"] == plain_authority["inventory"]
    assert authority["hp"] == plain_authority["hp"]
    assert authority["npcs"] == plain_authority["npcs"]
    assert authority["scene"] == "frontier_gate"
    published = [row.get("player_facing_published") is True for row in q.evidence_records()]
    # A repeat is a direct engine recall, not the accepted AI candidate.
    assert published == [True, True, False, True]
    repeat = q.evidence_records()[2]['publication']
    assert repeat['owner'] == 'engine' and repeat['invariant'] == 'PASS'
    assert ROUTE in repeat['final_text']
    decisions = [row["validation"]["decision"] for row in q.evidence_records()]
    assert decisions == ["PASS", "PASS", "PASS", "PASS"]

    _seed(tmp_path / "recover", monkeypatch, "frontier_gate")
    _bind(monkeypatch, storage.load_session()["campaign_run_id"])
    monkeypatch.setattr(integrated, "run_integrated_hook", original)
    q.clear_evidence()
    monkeypatch.setenv(q.SAMPLE_ENV, "unsafe")
    failed = _session([NOTICE])[0]
    monkeypatch.delenv(q.SAMPLE_ENV, raising=False)
    monkeypatch.setattr(
        integrated, "run_integrated_hook",
        lambda value: original(value, generator=q._Replay(
            "You examine the board again and nothing new is established. " + ROUTE, "")),
    )
    continued = _session([REPEAT])[0]
    assert UNSAFE not in failed["gm_output"]["player_facing_text"]
    assert q.evidence_records()[0].get("player_facing_published") is not True
    assert continued["gm_output"]["player_facing_text"].startswith("You examine the notice board again")
    assert ROUTE in continued["gm_output"]["player_facing_text"]
    assert _authority()["clues"] == [ROUTE]
    assert json.dumps(_authority()).count("silver key") == 0
