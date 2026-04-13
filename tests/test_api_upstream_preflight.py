"""Upstream API preflight classification, caching, and startup logging."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
import pytest
from openai import APIStatusError, AuthenticationError, InternalServerError, PermissionDeniedError

from game import api_upstream_preflight as pre
from game.api_upstream_preflight import (
    compute_api_runtime_health_from_exception,
    format_upstream_api_preflight_startup_lines,
    get_latest_upstream_api_preflight,
    log_upstream_api_preflight_at_startup,
    run_upstream_api_preflight,
)
import game.gm as gm_mod

pytestmark = pytest.mark.unit


def _resp(status: int) -> httpx.Response:
    return httpx.Response(status, request=httpx.Request("POST", "https://api.openai.com/v1/responses"))


@pytest.fixture(autouse=True)
def _reset_preflight_cache():
    pre.reset_upstream_api_preflight_cache_for_tests()
    yield
    pre.reset_upstream_api_preflight_cache_for_tests()


def test_preflight_healthy_mocked_upstream(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT", raising=False)

    class _Client:
        def __init__(self, *_a: Any, **_k: Any) -> None:
            pass

        class responses:
            @staticmethod
            def create(**_kwargs: Any) -> object:
                return object()

    st = run_upstream_api_preflight(api_key="sk-test", model="gpt-4o-mini", client_factory=lambda _k: _Client())
    assert st["ok"] is True
    assert st["health_class"] == "healthy"
    assert st["invalidates_upstream_dependent_runs"] is False
    cached = get_latest_upstream_api_preflight()
    assert cached is not None
    assert cached["health_class"] == "healthy"


def test_preflight_defaults_to_configured_default_model(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT", raising=False)
    captured: list[dict[str, Any]] = []
    monkeypatch.setattr(pre, "DEFAULT_MODEL_NAME", "default-route-model")

    class _Client:
        def __init__(self, *_a: Any, **_k: Any) -> None:
            pass

        class responses:
            @staticmethod
            def create(**kwargs: Any) -> object:
                captured.append(dict(kwargs))
                return object()

    run_upstream_api_preflight(api_key="sk-test", client_factory=lambda _k: _Client())

    assert captured
    assert captured[0]["model"] == "default-route-model"


def test_preflight_insufficient_quota_classified(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT", raising=False)
    exc = APIStatusError(
        "quota",
        response=_resp(429),
        body={"error": {"code": "insufficient_quota", "message": "You exceeded your current quota."}},
    )

    class _Client:
        def __init__(self, *_a: Any, **_k: Any) -> None:
            pass

        class responses:
            @staticmethod
            def create(**_kwargs: Any) -> None:
                raise exc

    st = run_upstream_api_preflight(api_key="sk-test", model="m", client_factory=lambda _k: _Client())
    assert st["ok"] is False
    assert st["health_class"] == "insufficient_quota"
    assert st["invalidates_upstream_dependent_runs"] is True
    assert st["error_code"] == "insufficient_quota"
    assert get_latest_upstream_api_preflight() == st


def test_compute_health_auth_failure_sdk(monkeypatch: pytest.MonkeyPatch) -> None:
    exc = AuthenticationError(
        "bad key",
        response=_resp(401),
        body={"error": {"code": "invalid_api_key", "message": "Incorrect API key"}},
    )
    st = compute_api_runtime_health_from_exception(exc, checked_at="2026-01-01T00:00:00Z")
    assert st["health_class"] == "auth_failure"
    assert st["retryable"] is False


def test_compute_health_permission_denied_sdk() -> None:
    exc = PermissionDeniedError(
        "no access",
        response=_resp(403),
        body={"error": {"message": "Forbidden"}},
    )
    st = compute_api_runtime_health_from_exception(exc, checked_at="2026-01-01T00:00:00Z")
    assert st["health_class"] == "permission_failure"


def test_compute_health_model_access_from_classification() -> None:
    class _Exc(Exception):
        def __init__(self, *, code: str | None = None, status: int | None = None, msg: str = "") -> None:
            super().__init__(msg)
            self.code = code
            self.status_code = status

    exc = _Exc(code="model_not_found", status=404, msg="Model not found")
    st = compute_api_runtime_health_from_exception(exc, checked_at="2026-01-01T00:00:00Z")
    assert st["health_class"] == "model_access_failure"


def test_compute_health_transient_internal_server() -> None:
    exc = InternalServerError(
        "boom",
        response=_resp(503),
        body={"error": {"message": "The server had an error"}},
    )
    st = compute_api_runtime_health_from_exception(exc, checked_at="2026-01-01T00:00:00Z")
    assert st["health_class"] == "transient_upstream_failure"
    assert st["retryable"] is True


def test_startup_logging_uses_canonical_preflight(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    monkeypatch.delenv("ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT", raising=False)

    def fake_run(**_kwargs: Any) -> dict[str, Any]:
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

    monkeypatch.setattr(pre, "run_upstream_api_preflight", fake_run)
    log_upstream_api_preflight_at_startup()
    err = capsys.readouterr().out
    assert "insufficient_quota" in err
    assert "MANUAL / gameplay runs" in err
    assert "OPENAI API PREFLIGHT" in err


def test_preflight_healthy_does_not_mutate_call_gpt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT", raising=False)
    before = gm_mod.call_gpt

    class _Client:
        def __init__(self, *_a: Any, **_k: Any) -> None:
            pass

        class responses:
            @staticmethod
            def create(**_kwargs: Any) -> object:
                return object()

    run_upstream_api_preflight(api_key="sk-test", model="m", client_factory=lambda _k: _Client())
    assert gm_mod.call_gpt is before
    calls: list[int] = []

    def fake_gpt(_messages: list[dict[str, str]]) -> dict[str, Any]:
        calls.append(1)
        return {"player_facing_text": "ok", "tags": [], "scene_update": None, "activate_scene_id": None, "new_scene_draft": None, "world_updates": None, "suggested_action": None, "debug_notes": "", "metadata": {}}

    monkeypatch.setattr(gm_mod, "call_gpt", fake_gpt)
    out = gm_mod.call_gpt([])
    assert calls == [1]
    assert out.get("player_facing_text") == "ok"


def test_format_startup_lines_include_invalidates_flag() -> None:
    lines = format_upstream_api_preflight_startup_lines(
        {
            "ok": False,
            "health_class": "unknown_failure",
            "retryable": None,
            "status_code": None,
            "error_code": None,
            "message_excerpt": "x",
            "checked_at": "t",
            "invalidates_upstream_dependent_runs": True,
        }
    )
    assert any("invalidates_upstream_dependent_runs=True" in ln for ln in lines)


def test_lifespan_calls_preflight_when_not_skipped(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """``TestClient`` lifespan invokes preflight unless skip env is set."""
    import json

    import game.api as api_mod
    import game.storage as st
    from fastapi.testclient import TestClient
    from game.api import app
    from game.defaults import default_scene

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
        path = st.SCENES_DIR / f"{sid}.json"
        path.write_text(json.dumps(default_scene(sid), indent=2), encoding="utf-8")

    called: list[int] = []

    def fake_log() -> None:
        called.append(1)

    monkeypatch.setenv("ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT", "0")
    monkeypatch.setattr(api_mod, "log_upstream_api_preflight_at_startup", fake_log)

    with TestClient(app):
        pass
    assert called == [1]
