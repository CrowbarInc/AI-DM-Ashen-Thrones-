from __future__ import annotations

import importlib

import dotenv
import pytest

import game.api_upstream_preflight as pre_mod
import game.config as config_mod

pytestmark = pytest.mark.unit


def _config_snapshot_for_env(**env: str | None) -> dict[str, object]:
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(dotenv, "load_dotenv", lambda *args, **kwargs: None)
        for name in (
            "OPENAI_API_KEY",
            "MODEL_NAME",
            "DEFAULT_MODEL_NAME",
            "HIGH_PRECISION_MODEL_NAME",
            "RETRY_ESCALATION_MODEL_NAME",
            "ENABLE_MODEL_ROUTING",
        ):
            mp.delenv(name, raising=False)
        for name, value in env.items():
            if value is None:
                mp.delenv(name, raising=False)
            else:
                mp.setenv(name, value)
        cfg = importlib.reload(config_mod)
        pre = importlib.reload(pre_mod)
        snapshot = {
            "MODEL_NAME": cfg.MODEL_NAME,
            "DEFAULT_MODEL_NAME": cfg.DEFAULT_MODEL_NAME,
            "HIGH_PRECISION_MODEL_NAME": cfg.HIGH_PRECISION_MODEL_NAME,
            "RETRY_ESCALATION_MODEL_NAME": cfg.RETRY_ESCALATION_MODEL_NAME,
            "ENABLE_MODEL_ROUTING": cfg.ENABLE_MODEL_ROUTING,
            "PREFLIGHT_DEFAULT_MODEL_NAME": pre.DEFAULT_MODEL_NAME,
        }
    importlib.reload(config_mod)
    importlib.reload(pre_mod)
    return snapshot


def test_high_precision_falls_back_to_default_and_routing_flag_parses_false() -> None:
    snapshot = _config_snapshot_for_env(
        OPENAI_API_KEY="sk-test",
        DEFAULT_MODEL_NAME="default-sentinel",
        HIGH_PRECISION_MODEL_NAME=None,
        RETRY_ESCALATION_MODEL_NAME="retry-sentinel",
        ENABLE_MODEL_ROUTING="false",
    )

    assert snapshot["DEFAULT_MODEL_NAME"] == "default-sentinel"
    assert snapshot["HIGH_PRECISION_MODEL_NAME"] == "default-sentinel"
    assert snapshot["RETRY_ESCALATION_MODEL_NAME"] == "retry-sentinel"
    assert snapshot["ENABLE_MODEL_ROUTING"] is False
    assert snapshot["PREFLIGHT_DEFAULT_MODEL_NAME"] == "default-sentinel"


def test_retry_escalation_falls_back_to_high_precision_model() -> None:
    snapshot = _config_snapshot_for_env(
        OPENAI_API_KEY="sk-test",
        DEFAULT_MODEL_NAME="default-sentinel",
        HIGH_PRECISION_MODEL_NAME="high-precision-sentinel",
        RETRY_ESCALATION_MODEL_NAME=None,
    )

    assert snapshot["DEFAULT_MODEL_NAME"] == "default-sentinel"
    assert snapshot["HIGH_PRECISION_MODEL_NAME"] == "high-precision-sentinel"
    assert snapshot["RETRY_ESCALATION_MODEL_NAME"] == "high-precision-sentinel"


def test_legacy_model_name_only_env_remains_backward_compatible() -> None:
    snapshot = _config_snapshot_for_env(
        OPENAI_API_KEY="sk-test",
        MODEL_NAME="legacy-model-sentinel",
        DEFAULT_MODEL_NAME=None,
        HIGH_PRECISION_MODEL_NAME=None,
        RETRY_ESCALATION_MODEL_NAME=None,
    )

    assert snapshot["MODEL_NAME"] == "legacy-model-sentinel"
    assert snapshot["DEFAULT_MODEL_NAME"] == "legacy-model-sentinel"
    assert snapshot["HIGH_PRECISION_MODEL_NAME"] == "legacy-model-sentinel"
    assert snapshot["RETRY_ESCALATION_MODEL_NAME"] == "legacy-model-sentinel"
    assert snapshot["PREFLIGHT_DEFAULT_MODEL_NAME"] == "legacy-model-sentinel"
