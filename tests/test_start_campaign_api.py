"""POST /api/start_campaign — structured opening without synthetic player lines."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

import game.api as api_mod
import game.storage as st
from game.api import app, compose_state
from game.defaults import default_scene
from game.storage import load_log, load_session
from tests.test_turn_pipeline_shared import FAKE_GPT_RESPONSE

pytestmark = pytest.mark.integration


def _patch_data_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    base = tmp_path
    monkeypatch.setattr(st, "BASE_DIR", base)
    monkeypatch.setattr(st, "DATA_DIR", base / "data")
    monkeypatch.setattr(st, "SCENES_DIR", st.DATA_DIR / "scenes")
    monkeypatch.setattr(st, "CHARACTER_PATH", st.DATA_DIR / "character.json")
    monkeypatch.setattr(st, "CAMPAIGN_PATH", st.DATA_DIR / "campaign.json")
    monkeypatch.setattr(st, "SESSION_PATH", st.DATA_DIR / "session.json")
    monkeypatch.setattr(st, "WORLD_PATH", st.DATA_DIR / "world.json")
    monkeypatch.setattr(st, "COMBAT_PATH", st.DATA_DIR / "combat.json")
    monkeypatch.setattr(st, "CONDITIONS_PATH", st.DATA_DIR / "conditions.json")
    monkeypatch.setattr(st, "SESSION_LOG_PATH", st.DATA_DIR / "session_log.jsonl")
    st.DATA_DIR.mkdir(parents=True, exist_ok=True)
    st.SCENES_DIR.mkdir(parents=True, exist_ok=True)
    for sid in ("frontier_gate", "market_quarter", "old_milestone"):
        (st.SCENES_DIR / f"{sid}.json").write_text(
            json.dumps(default_scene(sid), indent=2), encoding="utf-8"
        )


def test_compose_state_ui_campaign_flags_fresh_vs_started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_data_dir(tmp_path, monkeypatch)
    monkeypatch.setattr(api_mod, "log_upstream_api_preflight_at_startup", lambda: None)

    with TestClient(app) as client:
        assert client.post("/api/new_campaign").status_code == 200
        st0 = client.get("/api/state").json()
        public0 = st0["public_state"]
        assert public0["ui"]["campaign_can_start"] is True
        assert public0["ui"]["campaign_started"] is False
        monkeypatch.setattr("game.api.call_gpt", lambda *_a, **_k: dict(FAKE_GPT_RESPONSE))
        assert client.post("/api/start_campaign").status_code == 200
        st1 = compose_state()
        assert st1["ui"]["campaign_can_start"] is False
        assert st1["ui"]["campaign_started"] is True


def test_new_campaign_leaves_log_empty_and_no_gm_payload(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_data_dir(tmp_path, monkeypatch)
    monkeypatch.setattr(api_mod, "log_upstream_api_preflight_at_startup", lambda: None)

    with TestClient(app) as client:
        nc = client.post("/api/new_campaign")
        assert nc.status_code == 200
        body = nc.json()
        assert body.get("status") == "ok"
        assert "gm_output" not in body
        assert client.get("/api/log").json().get("entries") == []


def test_start_campaign_emits_opening_and_sets_started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_data_dir(tmp_path, monkeypatch)
    monkeypatch.setattr(api_mod, "log_upstream_api_preflight_at_startup", lambda: None)
    monkeypatch.setattr("game.api.call_gpt", lambda *_a, **_k: dict(FAKE_GPT_RESPONSE))

    with TestClient(app) as client:
        assert client.post("/api/new_campaign").status_code == 200
        sc = client.post("/api/start_campaign")
        assert sc.status_code == 200
        data = sc.json()
        assert data.get("ok") is True
        assert data.get("resolution", {}).get("kind") == "scene_opening"
        assert data.get("session", {}).get("campaign_started") is True
        assert data.get("ui", {}).get("campaign_can_start") is False

    entries = load_log()
    assert len(entries) == 1
    assert entries[0].get("resolution", {}).get("kind") == "scene_opening"
    assert entries[0].get("request", {}).get("start_campaign") is True
    gm_output = entries[0].get("gm_output") or {}
    assert isinstance(gm_output.get("opening_curated_facts"), list)
    assert gm_output["opening_curated_facts"]
    emission_debug = (gm_output.get("metadata") or {}).get("emission_debug") or {}
    assert emission_debug.get("opening_curated_facts_present") is True
    assert emission_debug.get("opening_curated_facts_count", 0) > 0
    assert emission_debug.get("opening_curated_facts_source") in {"selector", "realization"}


def test_start_campaign_frontier_gate_uses_journal_seed_facts_when_opening_seed_absent(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_data_dir(tmp_path, monkeypatch)
    monkeypatch.setattr(api_mod, "log_upstream_api_preflight_at_startup", lambda: None)
    monkeypatch.setattr("game.api.call_gpt", lambda *_a, **_k: dict(FAKE_GPT_RESPONSE))

    with TestClient(app) as client:
        assert client.post("/api/new_campaign").status_code == 200
        gate_path = st.scene_path("frontier_gate")
        gate = json.loads(gate_path.read_text(encoding="utf-8"))
        scene = gate.get("scene") if isinstance(gate.get("scene"), dict) else gate
        scene.pop("opening_seed_facts", None)
        scene.pop("campaign_spine_opening_facts", None)
        scene.pop("spine_opening_facts", None)
        gate_path.write_text(json.dumps(gate, indent=2), encoding="utf-8")

        sc = client.post("/api/start_campaign")
        assert sc.status_code == 200

    entries = load_log()
    gm_output = entries[0].get("gm_output") or {}
    emission_debug = (gm_output.get("metadata") or {}).get("emission_debug") or {}
    assert emission_debug.get("opening_curated_facts_count", 0) > 0


def test_start_campaign_log_has_no_begin_player_line(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_data_dir(tmp_path, monkeypatch)
    monkeypatch.setattr(api_mod, "log_upstream_api_preflight_at_startup", lambda: None)
    monkeypatch.setattr("game.api.call_gpt", lambda *_a, **_k: dict(FAKE_GPT_RESPONSE))

    with TestClient(app) as client:
        client.post("/api/new_campaign")
        assert client.post("/api/start_campaign").status_code == 200

    blob = st.SESSION_LOG_PATH.read_text(encoding="utf-8")
    assert "Begin" not in blob
    assert "begin the campaign" not in blob.lower()


def test_second_start_campaign_rejected(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_data_dir(tmp_path, monkeypatch)
    monkeypatch.setattr(api_mod, "log_upstream_api_preflight_at_startup", lambda: None)
    monkeypatch.setattr("game.api.call_gpt", lambda *_a, **_k: dict(FAKE_GPT_RESPONSE))

    with TestClient(app) as client:
        client.post("/api/new_campaign")
        assert client.post("/api/start_campaign").status_code == 200
        r2 = client.post("/api/start_campaign")
        assert r2.status_code == 409
        assert r2.json().get("status") == "already_started"

    assert len(load_log()) == 1


def test_start_campaign_prompt_includes_opening_contract_fields(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_data_dir(tmp_path, monkeypatch)
    monkeypatch.setattr(api_mod, "log_upstream_api_preflight_at_startup", lambda: None)
    captured: list[Any] = []

    def _spy(messages: list, **_kwargs: Any) -> dict:
        captured.append(messages)
        return dict(FAKE_GPT_RESPONSE)

    monkeypatch.setattr("game.api.call_gpt", _spy)

    with TestClient(app) as client:
        client.post("/api/new_campaign")
        assert client.post("/api/start_campaign").status_code == 200

    assert captured
    user_msg = captured[0][1]
    assert isinstance(user_msg, dict) and isinstance(user_msg.get("content"), str)
    payload = json.loads(user_msg["content"])
    assert "opening_scene_realization" in payload
    assert "opening_narration_obligations" in payload
    assert payload.get("opening_curated_facts")


def test_play_ui_bootstrap_copy_and_no_gm_ready_placeholder() -> None:
    root = Path(__file__).resolve().parents[1]
    app_js = (root / "static" / "app.js").read_text(encoding="utf-8")
    assert "GM ready" not in app_js
    assert "Fresh campaign loaded" in app_js
    assert "campaign_can_start" in app_js
    assert "startCampaignBusy" in app_js
    assert "campaignBootstrapPanel" in app_js
    assert "updateCampaignBootstrapUI" in app_js


def test_failed_start_campaign_does_not_mark_started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _patch_data_dir(tmp_path, monkeypatch)
    monkeypatch.setattr(api_mod, "log_upstream_api_preflight_at_startup", lambda: None)

    def _boom(**_kwargs: Any) -> tuple[Any, ...]:
        raise RuntimeError("simulated pipeline failure")

    monkeypatch.setattr("game.api._run_resolved_turn_pipeline", _boom)

    with TestClient(app, raise_server_exceptions=True) as client:
        client.post("/api/new_campaign")
        with pytest.raises(RuntimeError):
            client.post("/api/start_campaign")

    sess = load_session()
    assert sess.get("campaign_started") in (False, None)
    assert load_log() == []
