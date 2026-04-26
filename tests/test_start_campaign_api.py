"""POST /api/start_campaign — structured opening without synthetic player lines."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

import game.api as api_mod
import game.api_turn_support as turn_support
import game.storage as st
from game.api import app, compose_state
from game.defaults import default_scene
from game.storage import load_log, load_session
from tests.test_turn_pipeline_shared import FAKE_GPT_RESPONSE

pytestmark = pytest.mark.integration

RICH_OPENING_GPT_RESPONSE = {
    **FAKE_GPT_RESPONSE,
    "player_facing_text": (
        "Rain spatters soot-dark stone across Cinderwatch's eastern gate while frayed banners snap "
        "above the muddy approach. You stand in the churned mud before the gate as refugees press "
        "shoulder to shoulder around the wagon line and guards hold the choke under shouted orders. "
        "A tavern runner weaves through the crush, calling offers of hot stew and paid rumor as the "
        "notice board waits beside the arch. The queue inches forward in fits, wagon wheels grinding "
        "through black ruts while wet canvas slaps against overloaded carts and the smell of damp wool, "
        "smoke, and sour road dust clings to everyone close enough to breathe on you. Somewhere ahead, "
        "a guard captain's voice cuts through the mutter of the crowd, sharp enough to make shoulders "
        "hunch and conversations die for a heartbeat before the pressure of bodies closes in again. "
        "To your left, a well-appointed townhouse flies noble colors above the square, clean banners "
        "staring down at the mud as if the gate's misery belongs to another city. Near the line, one "
        "threadbare watcher stands too still, eyes flicking to packs and faces instead of the arch. "
        "You can read the notice board, press the guards, approach the tavern runner, or watch the "
        "silent figure in the crush."
    ),
}

SHORT_OPENING_WITH_RICH_UPSTREAM_PREPARED_RESPONSE = {
    **FAKE_GPT_RESPONSE,
    "player_facing_text": (
        "You stand at Cinderwatch's eastern gate in the rain. Refugees crowd the wagon line "
        "while guards hold the choke."
    ),
    "upstream_prepared_emission": {
        "prepared_scene_opening_text": RICH_OPENING_GPT_RESPONSE["player_facing_text"],
    },
}


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


def _assert_scene_opening_reads_like_scene(text: str) -> None:
    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    assert len(sentences) >= 2

    lowered = text.lower()
    assert any(
        phrase in lowered
        for phrase in (
            "you stand",
            "you arrive",
            "you are",
            "you find yourself",
            "you step",
            "you wait",
        )
    )
    assert any(
        re.search(rf"\b{verb}\w*\b", lowered)
        for verb in (
            "press",
            "shout",
            "grind",
            "spatter",
            "slick",
            "drift",
            "snap",
            "call",
            "weave",
            "mutter",
        )
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
    monkeypatch.setattr("game.api.call_gpt", lambda *_a, **_k: dict(RICH_OPENING_GPT_RESPONSE))

    with TestClient(app) as client:
        assert client.post("/api/new_campaign").status_code == 200
        gate_path = st.scene_path("frontier_gate")
        gate = json.loads(gate_path.read_text(encoding="utf-8"))
        scene = gate.get("scene") if isinstance(gate.get("scene"), dict) else gate
        scene["opening_seed_facts"] = [
            "You stand in the churned mud before Cinderwatch's eastern gate as rain spatters soot-dark stone.",
            "Refugees press shoulder to shoulder around the wagon line while guards hold the choke.",
            "A tavern runner shouts offers of hot stew and paid rumor.",
            "A notice board lists new taxes, curfews, and a posted warning about a missing patrol.",
        ]
        gate_path.write_text(json.dumps(gate, indent=2), encoding="utf-8")
        sc = client.post("/api/start_campaign")
        assert sc.status_code == 200
        data = sc.json()
        assert data.get("ok") is True
        assert data.get("resolution", {}).get("kind") == "scene_opening"
        assert data.get("session", {}).get("campaign_started") is True
        assert data.get("ui", {}).get("campaign_can_start") is False
        response_text = str(data.get("gm_output", {}).get("player_facing_text") or "")
        response_debug = ((data.get("gm_output") or {}).get("metadata") or {}).get("emission_debug") or {}
        log_reload_entries = client.get("/api/log").json().get("entries") or []

    entries = load_log()
    assert len(entries) == 1
    assert len(log_reload_entries) == 1
    assert entries[0].get("resolution", {}).get("kind") == "scene_opening"
    assert entries[0].get("request", {}).get("start_campaign") is True
    gm_output = entries[0].get("gm_output") or {}
    log_text = str(gm_output.get("player_facing_text") or "")
    reload_text = str((log_reload_entries[0].get("gm_output") or {}).get("player_facing_text") or "")
    reload_debug = ((log_reload_entries[0].get("gm_output") or {}).get("metadata") or {}).get("emission_debug") or {}
    assert response_text == log_text == reload_text
    assert response_text in RICH_OPENING_GPT_RESPONSE["player_facing_text"]
    assert "You stand" in response_text
    assert len(response_text) > 800
    assert len(log_text) > 800
    assert isinstance(gm_output.get("opening_curated_facts"), list)
    assert gm_output["opening_curated_facts"]
    _assert_scene_opening_reads_like_scene(str(gm_output.get("player_facing_text") or ""))
    emission_debug = (gm_output.get("metadata") or {}).get("emission_debug") or {}
    assert emission_debug.get("gm_output_player_facing_len") == len(log_text)
    assert emission_debug.get("pre_gate_text_len", 0) > 800
    assert emission_debug.get("post_final_emission_gate_text_len", 0) > 800
    assert emission_debug.get("post_narration_state_consistency_text_len", 0) > 800
    assert emission_debug.get("narration_state_consistency_changed_text") is False
    assert emission_debug.get("narration_state_consistency_before_preview")
    assert emission_debug.get("narration_state_consistency_after_preview")
    assert emission_debug.get("final_emission_text_preview")
    assert emission_debug.get("response_payload_text_preview")
    assert emission_debug.get("log_payload_text_preview")
    assert isinstance(emission_debug.get("canonical_gm_object_id"), int)
    for field in (
        "gm_output_player_facing_len",
        "pre_gate_text_len",
        "post_final_emission_gate_text_len",
        "post_narration_state_consistency_text_len",
        "narration_state_consistency_changed_text",
        "narration_state_consistency_before_preview",
        "narration_state_consistency_after_preview",
        "final_emission_text_preview",
        "response_payload_text_preview",
        "log_payload_text_preview",
        "canonical_gm_object_id",
    ):
        assert field in reload_debug
        assert field in response_debug
    assert emission_debug.get("opening_curated_facts_present") is True
    assert emission_debug.get("opening_curated_facts_count", 0) > 0
    assert emission_debug.get("opening_curated_facts_source") in {"selector", "realization"}


def test_start_campaign_scene_opening_reconcile_cannot_shorten_rich_post_gate_text(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_data_dir(tmp_path, monkeypatch)
    monkeypatch.setattr(api_mod, "log_upstream_api_preflight_at_startup", lambda: None)
    monkeypatch.setattr("game.api.call_gpt", lambda *_a, **_k: dict(RICH_OPENING_GPT_RESPONSE))

    compressed_summary = (
        "You stand at Cinderwatch's eastern gate in the rain. Refugees crowd the wagon line, "
        "guards hold the choke, a tavern runner calls for attention, and a notice board offers "
        "possible leads."
    )

    def _shortening_reconcile(**kwargs: Any) -> dict:
        gm_output = kwargs.get("gm_output")
        if isinstance(gm_output, dict):
            gm_output["player_facing_text"] = compressed_summary
        return {
            "narration_state_mismatch_detected": True,
            "mismatch_kind": "test_forced_scene_opening_summary",
            "mismatch_repair_applied": "test_summary_overwrite",
            "mismatch_repairs_applied": ["test_summary_overwrite"],
            "repaired_discovered_clue_texts": [],
        }

    monkeypatch.setattr(turn_support, "reconcile_final_text_with_structured_state", _shortening_reconcile)

    with TestClient(app) as client:
        assert client.post("/api/new_campaign").status_code == 200
        sc = client.post("/api/start_campaign")
        assert sc.status_code == 200
        data = sc.json()

    response_text = str(data.get("gm_output", {}).get("player_facing_text") or "")
    gm_output = load_log()[0].get("gm_output") or {}
    log_text = str(gm_output.get("player_facing_text") or "")
    emission_debug = (gm_output.get("metadata") or {}).get("emission_debug") or {}

    assert response_text == log_text
    assert response_text != compressed_summary
    assert len(response_text) > 800
    assert emission_debug.get("post_final_emission_gate_text_len", 0) > 800
    assert emission_debug.get("post_narration_state_consistency_text_len", 0) > 800
    assert emission_debug.get("narration_state_consistency_changed_text") is False


def test_start_campaign_promotes_valid_upstream_prepared_scene_opening(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _patch_data_dir(tmp_path, monkeypatch)
    monkeypatch.setattr(api_mod, "log_upstream_api_preflight_at_startup", lambda: None)
    monkeypatch.setattr(
        "game.api.call_gpt",
        lambda *_a, **_k: dict(SHORT_OPENING_WITH_RICH_UPSTREAM_PREPARED_RESPONSE),
    )

    with TestClient(app) as client:
        assert client.post("/api/new_campaign").status_code == 200
        sc = client.post("/api/start_campaign")
        assert sc.status_code == 200
        data = sc.json()
        log_reload_entries = client.get("/api/log").json().get("entries") or []

    response_text = str(data.get("gm_output", {}).get("player_facing_text") or "")
    gm_output = load_log()[0].get("gm_output") or {}
    log_text = str(gm_output.get("player_facing_text") or "")
    reload_text = str((log_reload_entries[0].get("gm_output") or {}).get("player_facing_text") or "")
    emission_debug = (gm_output.get("metadata") or {}).get("emission_debug") or {}

    assert response_text == log_text == reload_text
    assert response_text in RICH_OPENING_GPT_RESPONSE["player_facing_text"]
    assert response_text != SHORT_OPENING_WITH_RICH_UPSTREAM_PREPARED_RESPONSE["player_facing_text"]
    assert "Somewhere ahead, a guard captain's voice cuts through the mutter of the crowd" in response_text
    assert len(response_text) > 800
    assert emission_debug.get("opening_upstream_prepared_present") is True
    assert emission_debug.get("opening_upstream_prepared_len", 0) > 800
    assert emission_debug.get("opening_upstream_prepared_promoted") is True
    assert emission_debug.get("opening_raw_text_source") == "upstream_prepared_emission"


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


def test_start_campaign_opening_fallback_basis_uses_journal_seed_not_visible_facts(
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
        scene["visible_facts"] = ["VISIBLE FACT SHOULD NOT APPEAR"]
        scene["journal_seed_facts"] = ["JOURNAL FACT SHOULD APPEAR"]
        gate_path.write_text(json.dumps(gate, indent=2), encoding="utf-8")

        sc = client.post("/api/start_campaign")
        assert sc.status_code == 200
        data = sc.json()

    text = str(data.get("gm_output", {}).get("player_facing_text") or "")
    assert "JOURNAL FACT SHOULD APPEAR" in text
    assert "VISIBLE FACT SHOULD NOT APPEAR" not in text

    gm_output = (load_log()[0].get("gm_output") or {})
    emission_debug = (gm_output.get("metadata") or {}).get("emission_debug") or {}
    final_meta = gm_output.get("_final_emission_meta") or {}
    assert emission_debug.get("opening_selector_source_used") == "journal_seed_facts"
    assert emission_debug.get("opening_selector_selected_facts") == ["JOURNAL FACT SHOULD APPEAR"]
    assert emission_debug.get("opening_curated_facts") == ["JOURNAL FACT SHOULD APPEAR"]
    assert final_meta.get("opening_final_fallback_basis") == ["JOURNAL FACT SHOULD APPEAR"]
    assert final_meta.get("opening_final_basis_matches_selector") is True
    if data.get("resolution", {}).get("kind") == "scene_opening":
        assert final_meta.get("opening_final_basis_matches_selector") is True


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
    prompt_text = "\n".join(
        str(msg.get("content") or "") for msg in captured[0] if isinstance(msg, dict)
    )
    assert "OPENING SCENE (STRUCTURED COMPOSITION)" in prompt_text
    assert "OPENING SCENE COMPOSITION CONTRACT" in prompt_text
    assert "BAD:" in prompt_text and "GOOD:" in prompt_text
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
