"""PR-CM world-progression controls and the known lead-subject diagnostic.

These tests stub the provider. They do not add clocks, schedulers, or
interruption templates. The diagnostic at the bottom records a malformed
lead subject and does not define the passive-pressure contract.
"""
from __future__ import annotations

import copy

import pytest
from fastapi.testclient import TestClient

from game import storage
from game.api import app
from game.gm import _extract_visible_figure_candidate, _scene_momentum_due, extract_contextual_leads_from_text
from game.immutable_valid_response import validate_generated_response
from game.response_policy_enforcement import _pick_passive_pressure_source, _render_passive_pressure_beat
from tests.helpers.replay_fem_read_smoke import read_turn_debug_notes
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _seed_shared_world

pytestmark = pytest.mark.integration

_LAMP = "The lamp stays steady over the desk."
_OBSOLETE_INTERRUPTION_PHRASES = (
    "cuts through the crowd",
    "stops at your shoulder",
    "comes straight to you",
    "squares up to you",
    "breaks the silence first",
    "if you're moving on this, move now",
    "ask me now",
)
_FALLBACK_LINE = "As you watch the scene, a guard leans near the checkpoint, watching the road."


def _event_texts(events) -> list[str]:
    texts: list[str] = []
    for event in events or []:
        if isinstance(event, str) and event.strip():
            texts.append(event.strip())
        elif isinstance(event, dict):
            text = str(event.get("text") or "").strip()
            if text:
                texts.append(text)
    return texts


def _hold_factions(*, pressure: int = 0, agenda: int = 0, verevin_pressure: int | None = None) -> None:
    world = storage.load_world()
    for row in world.get("factions") or []:
        if not isinstance(row, dict):
            continue
        row["pressure"] = pressure
        row["agenda_progress"] = agenda
        if verevin_pressure is not None and row.get("id") == "house_verevin":
            row["pressure"] = verevin_pressure
    world["projects"] = []
    world["event_log"] = []
    storage._save_json(storage.WORLD_PATH, world)


def _player_text(data: dict) -> str:
    return str((data.get("gm_output") or {}).get("player_facing_text") or "")


def _install_wait_stubs(monkeypatch, line: str) -> None:
    monkeypatch.setattr("game.api.call_gpt", lambda _messages: _gm_response(line))
    monkeypatch.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
    monkeypatch.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)


def _assert_no_invented_interruption(text: str) -> None:
    low = text.lower()
    for phrase in _OBSOLETE_INTERRUPTION_PHRASES:
        assert phrase not in low
    assert '"' not in text


def _post_wait(client: TestClient, text: str = "I wait."):
    response = client.post("/api/chat", json={"text": text})
    assert response.status_code == 200
    return response.json()


def test_quiet_wait_with_no_due_world_event_keeps_narration(tmp_path, monkeypatch):
    """Control A. No threshold and no mobile agenda. Quiet waiting stays quiet."""
    _seed_shared_world(tmp_path, monkeypatch)
    _hold_factions()
    with monkeypatch.context() as m:
        _install_wait_stubs(m, _LAMP)
        data = _post_wait(TestClient(app))

    text = _player_text(data)
    assert text == _LAMP
    assert not _event_texts((data.get("resolution") or {}).get("world_tick_events"))
    assert not _event_texts(storage.load_world().get("event_log"))
    session = storage.load_session()
    assert (session.get("clocks") or {}).get("time_pressure") == 1
    assert session.get("current_date") == "Day 1"
    assert "passive_scene_pressure" not in ((data.get("gm_output") or {}).get("tags") or [])
    _assert_no_invented_interruption(text)
    npcs = [npc for npc in storage.load_world().get("npcs") or [] if isinstance(npc, dict)]
    assert {npc.get("id") for npc in npcs} == {"guard_captain", "tavern_runner"}
    assert all(npc.get("location") == "frontier_gate" for npc in npcs)


def test_faction_threshold_wait_records_event_without_narrating_it(tmp_path, monkeypatch):
    """Control B. A seeded threshold is stored. Valid narration is not overwritten."""
    _seed_shared_world(tmp_path, monkeypatch)
    _hold_factions(verevin_pressure=2)
    with monkeypatch.context() as m:
        _install_wait_stubs(m, _LAMP)
        data = _post_wait(TestClient(app))

    text = _player_text(data)
    tick_texts = _event_texts((data.get("resolution") or {}).get("world_tick_events"))
    assert tick_texts == ["House Verevin's pressure mounts."]
    assert _event_texts(storage.load_world().get("event_log")) == ["House Verevin's pressure mounts."]
    factions = {
        row.get("id"): int(row.get("pressure") or 0)
        for row in storage.load_world().get("factions") or []
        if isinstance(row, dict)
    }
    assert factions["house_verevin"] == 3
    assert factions["ash_cowl"] == 1
    assert factions["ordo_pyric"] == 1
    assert text == _LAMP
    assert "house verevin" not in text.lower()
    assert "passive_scene_pressure" not in ((data.get("gm_output") or {}).get("tags") or [])


def test_seeded_mobile_npc_moves_offscreen_on_wait(tmp_path, monkeypatch):
    """Control C. An existing mobile agenda moves. The player line does not announce it."""
    _seed_shared_world(tmp_path, monkeypatch)
    _hold_factions()
    world = storage.load_world()
    for npc in world.get("npcs") or []:
        if isinstance(npc, dict) and npc.get("id") == "tavern_runner":
            npc["availability"] = "mobile"
            npc["agenda_move_to_scene_id"] = "scene_investigate"
    storage._save_json(storage.WORLD_PATH, world)

    with monkeypatch.context() as m:
        _install_wait_stubs(m, _LAMP)
        data = _post_wait(TestClient(app))

    tick_texts = _event_texts((data.get("resolution") or {}).get("world_tick_events"))
    assert "Tavern Runner moves off-screen to scene_investigate." in tick_texts
    moved = {
        npc.get("id"): npc.get("location")
        for npc in storage.load_world().get("npcs") or []
        if isinstance(npc, dict)
    }
    assert moved["tavern_runner"] == "scene_investigate"
    assert moved["guard_captain"] == "frontier_gate"
    assert _player_text(data) == _LAMP
    assert "tavern runner" not in _player_text(data).lower()
    assert {npc.get("id") for npc in storage.load_world().get("npcs") or []} == {
        "guard_captain",
        "tavern_runner",
    }


def test_repeated_quiet_waits_ground_stall_without_a_new_event(tmp_path, monkeypatch):
    """Control D. Repeated passive turns advance pressure and ground the stall."""
    _seed_shared_world(tmp_path, monkeypatch)
    _hold_factions()
    scene = storage.load_scene("scene_investigate")
    facts = list((scene.get("scene") or {}).get("visible_facts") or [])
    with monkeypatch.context() as m:
        _install_wait_stubs(m, _LAMP)
        client = TestClient(app)
        first = _post_wait(client, "I wait.")
        after_first = storage.load_session()
        assert _scene_momentum_due(after_first, "scene_investigate") is True
        second = _post_wait(client, "I hold position and watch.")

    assert (storage.load_session().get("clocks") or {}).get("time_pressure") == 2
    assert not _event_texts((first.get("resolution") or {}).get("world_tick_events"))
    assert not _event_texts((second.get("resolution") or {}).get("world_tick_events"))
    assert not _event_texts(storage.load_world().get("event_log"))
    text = _player_text(second)
    assert _LAMP.lower() not in text.lower()
    assert any(str(fact).split(",")[0].lower() in text.lower() for fact in facts)
    _assert_no_invented_interruption(text)
    assert "passive_scene_pressure" in ((second.get("gm_output") or {}).get("tags") or [])
    notes = read_turn_debug_notes(second)
    assert "passive_scene_pressure:" in notes
    assert "streak=2" in notes
    runtime = (storage.load_session().get("scene_runtime") or {}).get("scene_investigate") or {}
    assert runtime.get("passive_action_streak") == 2
    verdict = validate_generated_response(
        text,
        player_text="I hold position and watch.",
        resolution=second.get("resolution"),
        authored_corpus=" ".join(str(fact) for fact in facts),
    )
    assert verdict.get("hard_valid") is True


def test_diagnostic_scene_stall_fallback_stores_guard_lead_subject(tmp_path, monkeypatch):
    """Regression guard for the PR-CN extractor repair."""
    candidate = _extract_visible_figure_candidate(_FALLBACK_LINE)
    assert candidate is not None
    assert candidate.get("subject") == "guard"
    assert candidate.get("kind") == "visible_suspicious_figure"
    extracted = extract_contextual_leads_from_text(_FALLBACK_LINE)
    assert any(
        item.get("kind") == "visible_suspicious_figure" and item.get("subject") == "guard"
        for item in extracted
    )
    assert not any(str(item.get("subject") or "") == "as you" for item in extracted if isinstance(item, dict))

    _seed_shared_world(tmp_path, monkeypatch)
    scene = copy.deepcopy(storage.load_scene("scene_investigate"))
    scene.pop("_is_canon", None)
    scene["scene"]["visible_facts"] = [
        "A guard leans near the checkpoint, watching the road.",
        "A missing patrol notice curls in the damp beside him.",
    ]
    storage.save_scene(scene)
    captured: list[list] = []
    phase = {"line": "The damp air hangs over the gate as everyone watches everyone else."}

    def _gpt(messages):
        captured.append(messages)
        return _gm_response(phase["line"])

    with monkeypatch.context() as m:
        m.setattr("game.api.call_gpt", _gpt)
        m.setattr("game.api.parse_social_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_exploration_intent", lambda *_args, **_kwargs: None)
        m.setattr("game.api.parse_intent", lambda *_args, **_kwargs: None)
        client = TestClient(app)
        assert client.post("/api/chat", json={"text": "I wait."}).status_code == 200
        second = client.post("/api/chat", json={"text": "I hold position and watch."})
        assert second.status_code == 200
        phase["line"] = "Rain continues to bead on the stone."
        third = client.post("/api/chat", json={"text": "I wait."})
        assert third.status_code == 200

    session = storage.load_session()
    runtime = (session.get("scene_runtime") or {}).get("scene_investigate") or {}
    leads = [lead for lead in (runtime.get("recent_contextual_leads") or []) if isinstance(lead, dict)]
    malformed = [
        lead
        for lead in leads
        if lead.get("kind") == "visible_suspicious_figure" and str(lead.get("subject") or "") == "as you"
    ]
    assert not malformed, leads
    guard_leads = [
        lead
        for lead in leads
        if lead.get("kind") == "visible_suspicious_figure" and str(lead.get("subject") or "") == "guard"
    ]
    assert guard_leads, leads
    npc_ids = {npc.get("id") for npc in storage.load_world().get("npcs") or [] if isinstance(npc, dict)}
    assert npc_ids == {"guard_captain", "tavern_runner"}
    assert "as you" not in npc_ids
    facts = list((storage.load_scene("scene_investigate").get("scene") or {}).get("visible_facts") or [])
    assert facts[0] == "A guard leans near the checkpoint, watching the road."

    source = _pick_passive_pressure_source(
        {"recent_contextual_leads": leads, "visible_facts": facts},
        {},
    )
    assert source.get("source") == "lead_figure"
    assert source.get("subject") == "guard"
    _kind, beat = _render_passive_pressure_beat(
        source=source,
        scene_snapshot={"visible_facts": facts, "recent_contextual_leads": leads},
        passive_streak=3,
        scene_envelope=storage.load_scene("scene_investigate"),
    )
    assert "shadow as you" not in beat.lower()
    assert "guard" in beat.lower()

    third_text = _player_text(third.json())
    assert third_text == "Rain continues to bead on the stone."
    assert "shadow as you" not in third_text.lower()
    lead_key = str(guard_leads[0].get("key") or "")
    assert lead_key
    assert lead_key.lower() in str(captured[-1]).lower()
    reloaded = storage.load_session()
    reloaded_leads = ((reloaded.get("scene_runtime") or {}).get("scene_investigate") or {}).get(
        "recent_contextual_leads"
    ) or []
    assert not any(str(lead.get("subject") or "") == "as you" for lead in reloaded_leads if isinstance(lead, dict))
    assert any(str(lead.get("subject") or "") == "guard" for lead in reloaded_leads if isinstance(lead, dict))
