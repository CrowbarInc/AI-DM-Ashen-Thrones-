"""OF2-F: opening + structured start seams, transcript honesty, and bad-opener regressions.

Locks UX1/OF1 shared helpers and first-turn prompt stack without adding new orchestration.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

import game.api as api_mod
import game.storage as st
from game.api import (
    _complete_opening_turn_persistence_like_chat,
    _opening_scene_normalized_action_and_resolution,
    app,
)
from game.defaults import default_scene, default_world
from game.storage import load_log, load_session
from tests.test_turn_pipeline_shared import FAKE_GPT_RESPONSE as TURN_FAKE_GPT

pytestmark = pytest.mark.integration

# Exact / near-exact failure markers from the contaminated-opener class (regression targets).
_BAD_OPENER_MARKERS = (
    "Guard Captain indicates",
    "Tavern Runner shouts",
    "controls patrol assignments tonight",
)


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


def _write_scenes_default(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, *, frontier_overrides: dict | None = None) -> None:
    _patch_data_dir(tmp_path, monkeypatch)
    for sid in ("frontier_gate", "market_quarter", "old_milestone"):
        scene = default_scene(sid)
        if sid == "frontier_gate" and frontier_overrides:
            scene["scene"].update(frontier_overrides)
        (st.SCENES_DIR / f"{sid}.json").write_text(json.dumps(scene, indent=2), encoding="utf-8")


def _frontier_visible_facts_mixed() -> list[str]:
    return [
        "Rain beads on soot-dark stone; refugee families queue along the muddy approach while wagon wheels rut the lane.",
        "Smoke dulls the lanterns under the arch; soot streaks the gatehouse mortar and ash rides the wind.",
        "Guard Captain indicates the western tally changed at noon without banner notice.",
        "Tavern Runner shouts wagon-clearance prices over splintering crate noise.",
        "Captain Thoran controls patrol assignments tonight; riders string spare mounts by the guard stables.",
    ]


def _assert_prompt_rejects_bad_opener_class(payload: dict) -> None:
    """Assert diegetic opening fields only (exclude instructional prohibition strings)."""
    ob = payload.get("opening_scene_realization") or {}
    assert ob.get("opening_mode") is True
    contract = ob.get("contract") or {}
    basis = contract.get("narration_basis_visible_facts") or []
    anchors = contract.get("sensory_anchors") or []
    ambient = contract.get("ambient_motion") or []
    vis = (payload.get("narration_visibility") or {}).get("visible_facts") or []
    diegetic = " ".join(str(x) for x in (*basis, *anchors, *ambient, *vis)).lower()
    for m in _BAD_OPENER_MARKERS:
        assert m.lower() not in diegetic, f"diegetic opening fields leaked failure marker: {m!r}"
    assert "captain thoran" not in diegetic
    joined = " ".join(str(x) for x in basis).lower()
    assert "patrol assignments" not in joined
    assert "captain thoran" not in joined
    assert "tavern runner" not in joined
    assert "guard captain" not in joined
    assert any(
        tok in diegetic
        for tok in ("rain", "smoke", "soot", "mud", "wagon", "refugee", "lantern", "arch", "gate")
    ), "opening basis should foreground observable scene texture"


def test_start_campaign_prompt_basis_filters_bad_opener_class(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_scenes_default(monkeypatch, tmp_path, frontier_overrides={"visible_facts": _frontier_visible_facts_mixed()})
    monkeypatch.setattr(api_mod, "log_upstream_api_preflight_at_startup", lambda: None)
    world = default_world()
    world["npcs"] = []
    st.WORLD_PATH.write_text(json.dumps(world, indent=2), encoding="utf-8")

    captured: list[Any] = []

    def _spy(messages: list, **_kwargs: Any) -> dict:
        captured.append(messages)
        return dict(TURN_FAKE_GPT)

    monkeypatch.setattr("game.api.call_gpt", _spy)

    with TestClient(app) as client:
        assert client.post("/api/new_campaign").status_code == 200
        assert client.post("/api/start_campaign").status_code == 200

    assert captured
    user_msg = captured[0][1]
    assert isinstance(user_msg, dict) and isinstance(user_msg.get("content"), str)
    payload = json.loads(user_msg["content"])
    assert "opening_scene_realization" in payload
    assert "opening_narration_obligations" in payload
    assert payload["opening_narration_obligations"].get("opening_mode") is True
    _assert_prompt_rejects_bad_opener_class(payload)


def test_chat_begin_campaign_prompt_matches_of1_stack(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Chat-triggered opening uses the same prompt contract fields as structured start."""
    _write_scenes_default(monkeypatch, tmp_path, frontier_overrides={"visible_facts": _frontier_visible_facts_mixed()})
    monkeypatch.setattr(api_mod, "log_upstream_api_preflight_at_startup", lambda: None)
    world = default_world()
    world["npcs"] = []
    st.WORLD_PATH.write_text(json.dumps(world, indent=2), encoding="utf-8")

    captured: list[Any] = []

    def _spy(messages: list, **_kwargs: Any) -> dict:
        captured.append(messages)
        return dict(TURN_FAKE_GPT)

    monkeypatch.setattr("game.api.call_gpt", _spy)

    with TestClient(app) as client:
        assert client.post("/api/new_campaign").status_code == 200
        assert client.post("/api/chat", json={"text": "Begin the campaign."}).status_code == 200

    assert captured
    payload = json.loads(captured[0][1]["content"])
    _assert_prompt_rejects_bad_opener_class(payload)


def test_sparse_opening_basis_does_not_reintroduce_curated_bad_lines(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """OF1: empty/sparse basis is allowed; obligations stay on; prompt must not echo curated contamination."""
    contaminated_only = [
        "Captain Thoran controls patrol assignments tonight; the western post is short-handed.",
        "Lord Aldric knows the hidden truth of the throne conspiracy.",
    ]
    _write_scenes_default(monkeypatch, tmp_path, frontier_overrides={"visible_facts": contaminated_only})
    monkeypatch.setattr(api_mod, "log_upstream_api_preflight_at_startup", lambda: None)
    world = default_world()
    world["npcs"] = []
    st.WORLD_PATH.write_text(json.dumps(world, indent=2), encoding="utf-8")

    captured: list[Any] = []

    def _spy(messages: list, **_kwargs: Any) -> dict:
        captured.append(messages)
        return dict(TURN_FAKE_GPT)

    monkeypatch.setattr("game.api.call_gpt", _spy)

    with TestClient(app) as client:
        assert client.post("/api/new_campaign").status_code == 200
        assert client.post("/api/start_campaign").status_code == 200

    payload = json.loads(captured[0][1]["content"])
    assert payload["opening_narration_obligations"].get("opening_mode") is True
    assert payload["opening_narration_obligations"].get("opener_style") == "scene_establishing"
    vis = (payload.get("narration_visibility") or {}).get("visible_facts") or []
    joined_vis = " ".join(str(x) for x in vis).lower()
    contract = (payload.get("opening_scene_realization") or {}).get("contract") or {}
    basis = contract.get("narration_basis_visible_facts") or []
    joined_basis = " ".join(str(x) for x in basis).lower()
    assert "patrol assignments" not in joined_vis and "patrol assignments" not in joined_basis
    assert "captain thoran" not in joined_vis and "captain thoran" not in joined_basis
    assert "lord aldric" not in joined_vis and "lord aldric" not in joined_basis


def test_contaminated_gm_opening_emission_scrubs_operational_backstage(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Transcript-level: Thoran/patrol-assignment backstage must not ship; safe texture, terminal social, or explicit fallback is acceptable."""
    _write_scenes_default(monkeypatch, tmp_path, frontier_overrides={"visible_facts": _frontier_visible_facts_mixed()})
    monkeypatch.setattr(api_mod, "log_upstream_api_preflight_at_startup", lambda: None)
    world = default_world()
    world["npcs"] = []
    st.WORLD_PATH.write_text(json.dumps(world, indent=2), encoding="utf-8")

    bad = (
        "Guard Captain indicates you should hold. Tavern Runner shouts for coin. "
        "Captain Thoran controls patrol assignments tonight. "
        "Rain slicks soot-dark stone while refugees drag toward the wagons."
    )

    monkeypatch.setattr("game.api.call_gpt", lambda *_a, **_k: {"player_facing_text": bad, "tags": [], "scene_update": None, "activate_scene_id": None, "new_scene_draft": None, "world_updates": None, "suggested_action": None, "debug_notes": ""})

    with TestClient(app) as client:
        assert client.post("/api/new_campaign").status_code == 200
        r = client.post("/api/start_campaign")
        assert r.status_code == 200
        gm = r.json().get("gm_output") or {}
        text = gm.get("player_facing_text") or ""
    low = str(text).lower()
    assert "captain thoran" not in low
    assert "patrol assignments" not in low
    assert "controls patrol assignments tonight" not in low
    scene_texture = any(tok in low for tok in ("rain", "soot", "mud", "wagon", "refugee", "lantern", "gate", "smoke"))
    strict_social_terminal = "tavern runner" in low and (
        "frown" in low or "grimace" in low or "that's all" in low or "all i've got" in low
    )
    # C2: contaminated upstream may be rejected; pipeline can emit explicit nonsocial minimal fallback instead of minting scene prose.
    explicit_nonsocial_fallback = (
        gm.get("final_route") == "nonsocial_fallback_minimal"
        or gm.get("fallback_kind") == "nonsocial_empty_resolution_repair"
        or any(str(t) == "nonsocial_empty_resolution_repair" for t in (gm.get("tags") or []))
    )
    assert scene_texture or strict_social_terminal or explicit_nonsocial_fallback


def test_opening_scene_normalized_action_internal_vs_chat_parity() -> None:
    scene = default_scene("frontier_gate")
    internal_norm, internal_res = _opening_scene_normalized_action_and_resolution(
        scene=scene, player_text=None, internal_bootstrap=True
    )
    chat_norm, chat_res = _opening_scene_normalized_action_and_resolution(
        scene=scene, player_text="Begin the campaign.", internal_bootstrap=False
    )
    assert internal_norm["id"] == chat_norm["id"] == "campaign_start_opening_scene"
    assert internal_norm["type"] == chat_norm["type"] == "scene_opening"
    assert internal_res["action_id"] == chat_res["action_id"] == "campaign_start_opening_scene"
    assert internal_res["kind"] == chat_res["kind"] == "scene_opening"
    assert internal_res["target_scene_id"] == chat_res["target_scene_id"] == "frontier_gate"
    assert internal_res["prompt"] == "" and internal_res["label"] == "start_campaign"
    assert chat_res["prompt"].strip() == "Begin the campaign."
    assert chat_norm["prompt"].strip() == "Begin the campaign."


def test_first_chat_non_opening_does_not_mark_campaign_started(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_scenes_default(monkeypatch, tmp_path)
    monkeypatch.setattr(api_mod, "log_upstream_api_preflight_at_startup", lambda: None)
    monkeypatch.setattr("game.api.call_gpt", lambda *_a, **_k: dict(TURN_FAKE_GPT))

    with TestClient(app) as client:
        assert client.post("/api/new_campaign").status_code == 200
        st0 = client.get("/api/state").json()
        public0 = st0["public_state"]
        assert public0["ui"]["campaign_can_start"] is True
        assert public0["ui"]["campaign_started"] is False
        assert client.post("/api/chat", json={"text": "I look around quietly."}).status_code == 200
        st1 = client.get("/api/state").json()
        public1 = st1["public_state"]
        assert public1["ui"]["campaign_started"] is False
        assert public1["ui"]["campaign_can_start"] is False


def test_start_then_chat_keeps_campaign_started_true(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_scenes_default(monkeypatch, tmp_path)
    monkeypatch.setattr(api_mod, "log_upstream_api_preflight_at_startup", lambda: None)
    monkeypatch.setattr("game.api.call_gpt", lambda *_a, **_k: dict(TURN_FAKE_GPT))

    with TestClient(app) as client:
        assert client.post("/api/new_campaign").status_code == 200
        assert client.post("/api/start_campaign").status_code == 200
        assert client.post("/api/chat", json={"text": "I nod to the nearest guard."}).status_code == 200
        st = client.get("/api/state").json()
    assert st["public_state"]["ui"]["campaign_started"] is True
    assert load_session().get("campaign_started") is True


def test_start_and_chat_opening_share_log_and_started_semantics(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Both paths: one transcript row, campaign_started True, resolution scene_opening (parity tail)."""

    def run_start_channel(*, use_http_start: bool) -> dict:
        _write_scenes_default(monkeypatch, tmp_path)
        monkeypatch.setattr(api_mod, "log_upstream_api_preflight_at_startup", lambda: None)
        monkeypatch.setattr("game.api.call_gpt", lambda *_a, **_k: dict(TURN_FAKE_GPT))
        with TestClient(app) as client:
            assert client.post("/api/new_campaign").status_code == 200
            if use_http_start:
                r = client.post("/api/start_campaign")
            else:
                r = client.post("/api/chat", json={"text": "Start the campaign."})
            assert r.status_code == 200
            data = r.json()
        entries = load_log()
        assert len(entries) == 1
        assert entries[0].get("resolution", {}).get("kind") == "scene_opening"
        sess = load_session()
        assert sess.get("campaign_started") is True
        assert sess.get("turn_counter") == 1
        return data

    a = run_start_channel(use_http_start=True)
    b = run_start_channel(use_http_start=False)
    assert a.get("session", {}).get("campaign_started") is True
    assert b.get("session", {}).get("campaign_started") is True


def test_failed_start_leaves_turn_counter_and_log_clean(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_scenes_default(monkeypatch, tmp_path)
    monkeypatch.setattr(api_mod, "log_upstream_api_preflight_at_startup", lambda: None)

    def _boom(**_kwargs: Any) -> tuple[Any, ...]:
        raise RuntimeError("simulated pipeline failure")

    monkeypatch.setattr("game.api._run_resolved_turn_pipeline", _boom)

    with TestClient(app, raise_server_exceptions=True) as client:
        assert client.post("/api/new_campaign").status_code == 200
        with pytest.raises(RuntimeError):
            client.post("/api/start_campaign")

    sess = load_session()
    assert sess.get("campaign_started") in (False, None)
    assert int(sess.get("turn_counter", 0) or 0) == 0
    assert load_log() == []


def test_transcript_first_row_is_gm_not_bootstrap_player_line(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _write_scenes_default(monkeypatch, tmp_path)
    monkeypatch.setattr(api_mod, "log_upstream_api_preflight_at_startup", lambda: None)
    monkeypatch.setattr("game.api.call_gpt", lambda *_a, **_k: dict(TURN_FAKE_GPT))

    with TestClient(app) as client:
        assert client.post("/api/new_campaign").status_code == 200
        assert client.post("/api/start_campaign").status_code == 200

    ent = load_log()[0]
    assert ent.get("request", {}).get("start_campaign") is True
    assert (ent.get("log_meta") or {}).get("bootstrap_intent") == "start_campaign"
    gm = ent.get("gm_output") or {}
    assert gm.get("player_facing_text")
