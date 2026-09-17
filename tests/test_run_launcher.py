from __future__ import annotations

import importlib
import sys

import pytest


pytestmark = pytest.mark.unit


def test_run_module_imports_without_openai_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "")
    sys.modules.pop("run", None)

    launcher = importlib.import_module("run")

    assert callable(launcher.main)


def test_run_main_reaches_uvicorn_with_expected_asgi_target(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-launcher-secret")
    monkeypatch.setenv("UVICORN_RELOAD", "false")
    launcher = importlib.import_module("run")
    calls: list[dict[str, object]] = []

    def fake_run(app: str, **kwargs: object) -> None:
        calls.append({"app": app, **kwargs})

    monkeypatch.setattr(launcher.uvicorn, "run", fake_run)

    launcher.main()

    assert calls == [
        {
            "app": "game.api:app",
            "host": "127.0.0.1",
            "port": 8000,
            "reload": False,
        }
    ]
    out = capsys.readouterr().out
    assert "OPENAI_API_KEY configured: True" in out
    assert "sk-test-launcher-secret" not in out


def test_run_main_missing_api_key_reports_lazy_preflight_behavior(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "")
    monkeypatch.delenv("ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT", raising=False)
    launcher = importlib.import_module("run")
    monkeypatch.setattr(launcher.uvicorn, "run", lambda *_args, **_kwargs: None)

    launcher.main()

    out = capsys.readouterr().out
    assert "OPENAI_API_KEY configured: False" in out
    assert "FastAPI startup preflight will report this" in out
    assert "ImportError" not in out
