"""BHC2: gate live-upstream manual flows using cached preflight only."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

import game.api as api_mod
import game.api_upstream_preflight as pre
import game.storage as st
from game.api import app
from game.defaults import default_scene
from game.upstream_dependent_run_gate import compute_upstream_dependent_run_gate

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _reset_preflight_cache():
    pre.reset_upstream_api_preflight_cache_for_tests()
    yield
    pre.reset_upstream_api_preflight_cache_for_tests()


def _unhealthy_status() -> dict[str, Any]:
    return {
        "ok": False,
        "health_class": "insufficient_quota",
        "retryable": False,
        "status_code": 429,
        "error_code": "insufficient_quota",
        "message_excerpt": "quota",
        "checked_at": "2026-04-12T00:00:00Z",
        "invalidates_upstream_dependent_runs": True,
    }


def test_gate_healthy_from_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT", raising=False)

    class _Client:
        def __init__(self, *_a: Any, **_k: Any) -> None:
            pass

        class responses:
            @staticmethod
            def create(**_kwargs: Any) -> object:
                return object()

    pre.run_upstream_api_preflight(api_key="sk-test", model="m", client_factory=lambda _k: _Client())
    g = compute_upstream_dependent_run_gate()
    assert g["preflight_available"] is True
    assert g["upstream_runtime_healthy"] is True
    assert g["startup_run_valid"] is True
    assert g["manual_testing_blocked"] is False
    assert g["block_reason"] is None
    assert g["preflight_health_class"] == "healthy"


def test_gate_unhealthy_from_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT", raising=False)
    pre._set_latest_upstream_api_preflight(_unhealthy_status())
    g = compute_upstream_dependent_run_gate()
    assert g["manual_testing_blocked"] is True
    assert g["startup_run_valid"] is False
    assert g["upstream_runtime_healthy"] is False
    assert g["block_reason"] == "upstream_unhealthy_preflight"
    assert g["preflight_health_class"] == "insufficient_quota"


def test_gate_preflight_skipped_no_false_healthy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT", "1")
    g = compute_upstream_dependent_run_gate()
    assert g["preflight_available"] is False
    assert g["upstream_runtime_healthy"] is None
    assert g["startup_run_valid"] is False
    assert g["manual_testing_blocked"] is False
    assert g["block_reason"] == "preflight_skipped_by_env"


def test_new_campaign_blocked_before_reset_when_preflight_unhealthy(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT", raising=False)
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
        (st.SCENES_DIR / f"{sid}.json").write_text(json.dumps(default_scene(sid), indent=2), encoding="utf-8")

    def fake_log() -> None:
        pre._set_latest_upstream_api_preflight(_unhealthy_status())

    monkeypatch.setattr(api_mod, "log_upstream_api_preflight_at_startup", fake_log)

    with TestClient(app) as client:
        before = client.get("/api/state")
        assert before.status_code == 200
        rid_before = (before.json().get("public_state") or {}).get("campaign_run_id")
        r = client.post("/api/new_campaign")
        assert r.status_code == 503
        after = client.get("/api/state")
        assert after.status_code == 200
        rid_after = (after.json().get("public_state") or {}).get("campaign_run_id")
    body = r.json()
    assert body.get("ok") is False
    assert body.get("upstream_dependent_run_gate", {}).get("manual_testing_blocked") is True
    op = body.get("upstream_dependent_run_gate_operator") or {}
    assert op.get("upstream_gate_disposition") == "blocked_unhealthy_preflight"
    assert op.get("compact_banner") and "BLOCKED" in str(op.get("compact_banner"))
    assert "credit" in str(op.get("action_hint", "")).lower() or "recharge" in str(op.get("action_hint", "")).lower()
    assert rid_after == rid_before


def test_new_campaign_ok_includes_gate_when_preflight_skipped_default(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Default pytest env skips preflight; new campaign still works with explicit not-checked gate."""
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
        (st.SCENES_DIR / f"{sid}.json").write_text(json.dumps(default_scene(sid), indent=2), encoding="utf-8")

    monkeypatch.setattr(api_mod, "log_upstream_api_preflight_at_startup", lambda: None)

    with TestClient(app) as client:
        r = client.post("/api/new_campaign")
    assert r.status_code == 200
    data = r.json()
    assert data.get("status") == "ok"
    g = data.get("upstream_dependent_run_gate") or {}
    assert g.get("preflight_available") is False
    assert g.get("upstream_runtime_healthy") is None
    assert g.get("startup_run_valid") is False
    op = data.get("upstream_dependent_run_gate_operator") or {}
    assert op.get("gameplay_conclusions_valid") is False
    if pre.upstream_api_preflight_disabled_by_env():
        assert op.get("upstream_gate_disposition") == "preflight_skipped_by_env"
        assert op.get("compact_banner") and "skipped by env" in str(op.get("compact_banner"))
    else:
        assert op.get("upstream_gate_disposition") == "preflight_not_checked"
        assert op.get("compact_banner") and "not checked" in str(op.get("compact_banner"))


def test_manual_gauntlet_main_exits_immediately_when_preflight_unhealthy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pre._set_latest_upstream_api_preflight(_unhealthy_status())
    root = Path(__file__).resolve().parents[1]
    tool = root / "tools" / "run_manual_gauntlet.py"
    spec = importlib.util.spec_from_file_location("run_manual_gauntlet_tool_bhc2", tool)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_manual_gauntlet_tool_bhc2"] = mod
    spec.loader.exec_module(mod)
    monkeypatch.setattr(sys, "argv", ["prog", "--gauntlet", "g1"])
    assert mod.main() == 1


def test_playability_validation_main_exits_before_chat_when_unhealthy(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    pre._set_latest_upstream_api_preflight(_unhealthy_status())
    root = Path(__file__).resolve().parents[1]
    tool = root / "tools" / "run_playability_validation.py"
    spec = importlib.util.spec_from_file_location("run_playability_validation_tool_bhc2", tool)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["run_playability_validation_tool_bhc2"] = mod
    spec.loader.exec_module(mod)
    art = tmp_path / "pv"
    rc = mod.main(["--scenario", "p1_direct_answer", "--artifact-dir", str(art)])
    assert rc == 1
    assert not (art.exists() and any(art.iterdir()))


def test_lifespan_emits_upstream_gate_operator_line(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """FastAPI startup prints BHC3 operator summary derived from the gate (no ad hoc route logic)."""
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
        (st.SCENES_DIR / f"{sid}.json").write_text(json.dumps(default_scene(sid), indent=2), encoding="utf-8")

    monkeypatch.setattr(api_mod, "log_upstream_api_preflight_at_startup", lambda: None)
    capsys.readouterr()
    with TestClient(app) as client:
        assert client.get("/api/state").status_code == 200
    out = capsys.readouterr().out
    assert "[upstream_dependent_run_gate]" in out


def test_startup_log_skips_second_probe_when_cache_warm(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT", raising=False)

    class _Client:
        def __init__(self, *_a: Any, **_k: Any) -> None:
            pass

        class responses:
            @staticmethod
            def create(**_kwargs: Any) -> object:
                return object()

    pre.run_upstream_api_preflight(api_key="sk-t", model="m", client_factory=lambda _k: _Client())
    capsys.readouterr()
    pre.log_upstream_api_preflight_at_startup()
    out = capsys.readouterr().out
    assert "using in-process cache" in out
