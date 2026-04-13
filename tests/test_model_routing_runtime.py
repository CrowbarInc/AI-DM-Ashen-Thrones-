from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import openai
import pytest

import game.api as api_mod
import game.gm as gm_mod
import game.model_routing as routing_mod

pytestmark = pytest.mark.unit


def _install_openai_recorder(
    monkeypatch: pytest.MonkeyPatch,
    *,
    response_text: str,
) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []

    class _Client:
        def __init__(self, *_a: Any, **_k: Any) -> None:
            self.responses = self

        def create(self, **kwargs: Any) -> Any:
            calls.append(dict(kwargs))
            return SimpleNamespace(output_text=response_text)

    monkeypatch.setattr(openai, "OpenAI", _Client)
    return calls


def test_legacy_model_name_only_route_flows_through_call_gpt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_openai_recorder(
        monkeypatch,
        response_text='{"player_facing_text":"ok","tags":[]}',
    )
    legacy_model = "legacy-model-only-sentinel"
    monkeypatch.setattr(routing_mod, "ENABLE_MODEL_ROUTING", True)
    monkeypatch.setattr(routing_mod, "DEFAULT_MODEL_NAME", legacy_model)
    monkeypatch.setattr(routing_mod, "HIGH_PRECISION_MODEL_NAME", "high-precision-unused")
    monkeypatch.setattr(routing_mod, "RETRY_ESCALATION_MODEL_NAME", "retry-unused")

    route = routing_mod.resolve_model_route(purpose="primary_turn")
    out = gm_mod.call_gpt([{"role": "user", "content": "Hello"}], purpose="primary_turn")

    assert route.selected_model == legacy_model
    assert calls == [{"model": legacy_model, "input": [{"role": "user", "content": "Hello"}]}]
    assert out["metadata"]["selected_model"] == legacy_model


def test_call_gpt_uses_routed_selected_model_not_a_hardcoded_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_openai_recorder(
        monkeypatch,
        response_text='{"player_facing_text":"ok","tags":[]}',
    )
    monkeypatch.setattr(
        gm_mod,
        "resolve_model_route",
        lambda **_kwargs: routing_mod.ModelRouteDecision(
            selected_model="routed-selected-model",
            route_reason="unit_test_route",
            route_family="unit_test_family",
            escalation_allowed=True,
        ),
    )
    monkeypatch.setattr(routing_mod, "DEFAULT_MODEL_NAME", "wrong-if-hardcoded")

    out = gm_mod.call_gpt([{"role": "user", "content": "Hello"}], purpose="primary_turn")

    assert calls[0]["model"] == "routed-selected-model"
    assert out["metadata"]["selected_model"] == "routed-selected-model"


def test_call_gpt_attaches_route_metadata_and_merges_existing_metadata(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_openai_recorder(monkeypatch, response_text='{"ignored":true}')
    monkeypatch.setattr(
        gm_mod,
        "_safe_json",
        lambda _text: {
            "player_facing_text": "ok",
            "tags": [],
            "scene_update": None,
            "activate_scene_id": None,
            "new_scene_draft": None,
            "world_updates": None,
            "suggested_action": None,
            "debug_notes": "existing-debug",
            "metadata": {"existing": "keep"},
        },
    )
    monkeypatch.setattr(
        gm_mod,
        "resolve_model_route",
        lambda **_kwargs: routing_mod.ModelRouteDecision(
            selected_model="metadata-route-model",
            route_reason="metadata_reason",
            route_family="metadata_family",
            escalation_allowed=True,
        ),
    )

    out = gm_mod.call_gpt(
        [{"role": "user", "content": "Hello"}],
        purpose="primary_turn",
        retry_attempt=2,
    )

    assert out["metadata"] == {
        "existing": "keep",
        "selected_model": "metadata-route-model",
        "model_route_reason": "metadata_reason",
        "model_route_family": "metadata_family",
        "model_route_purpose": "primary_turn",
        "model_retry_attempt": 2,
        "model_escalated": False,
        "model_escalation_trigger": None,
    }
    assert out["debug_notes"] == (
        "existing-debug | "
        "model_route:metadata_family:metadata_reason:metadata-route-model"
    )


def test_routing_disabled_forces_default_model_name_in_call_gpt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_openai_recorder(
        monkeypatch,
        response_text='{"player_facing_text":"ok","tags":[]}',
    )
    monkeypatch.setattr(routing_mod, "ENABLE_MODEL_ROUTING", False)
    monkeypatch.setattr(routing_mod, "DEFAULT_MODEL_NAME", "routing-disabled-default")
    monkeypatch.setattr(routing_mod, "HIGH_PRECISION_MODEL_NAME", "high-precision-unused")
    monkeypatch.setattr(routing_mod, "RETRY_ESCALATION_MODEL_NAME", "retry-unused")

    out = gm_mod.call_gpt(
        [{"role": "user", "content": "Hello"}],
        purpose="strict_social",
        strict_social=True,
        retry_attempt=3,
    )

    assert calls == [
        {
            "model": "routing-disabled-default",
            "input": [{"role": "user", "content": "Hello"}],
        }
    ]
    assert out["metadata"]["selected_model"] == "routing-disabled-default"
    assert out["metadata"]["model_route_reason"] == "routing_disabled"
    assert out["metadata"]["model_route_family"] == "default"
    assert out["metadata"]["model_route_purpose"] == "strict_social"
    assert out["metadata"]["model_escalated"] is True
    assert out["metadata"]["model_escalation_trigger"] == "strict_social"


def test_call_gpt_logs_one_concise_model_route_line(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    _install_openai_recorder(
        monkeypatch,
        response_text='{"player_facing_text":"ok","tags":[]}',
    )
    monkeypatch.setattr(
        gm_mod,
        "resolve_model_route",
        lambda **_kwargs: routing_mod.ModelRouteDecision(
            selected_model="logged-model",
            route_reason="purpose_retry_escalation",
            route_family="retry_escalation",
            escalation_allowed=False,
        ),
    )

    gm_mod.call_gpt(
        [{"role": "user", "content": "Hello"}],
        purpose="retry_escalation",
        retry_attempt=1,
    )

    out = capsys.readouterr().out.strip().splitlines()
    assert out == [
        "[MODEL ROUTE] purpose=retry_escalation selected=logged-model "
        "family=retry_escalation retry=1 escalated=true"
    ]


def test_upstream_route_metadata_preservation_helper_marks_preserved() -> None:
    out = {"metadata": {"existing": "keep"}}
    source = {
        "metadata": {
            "selected_model": "route-model",
            "model_route_reason": "purpose_primary_turn",
            "model_route_family": "default",
            "model_route_purpose": "primary_turn",
            "model_retry_attempt": 0,
            "model_escalated": False,
            "model_escalation_trigger": None,
        }
    }

    api_mod._preserve_model_route_metadata(
        out,
        source,
        mark_upstream_preserved=True,
    )

    assert out["metadata"] == {
        "existing": "keep",
        "selected_model": "route-model",
        "model_route_reason": "purpose_primary_turn",
        "model_route_family": "default",
        "model_route_purpose": "primary_turn",
        "model_retry_attempt": 0,
        "model_escalated": False,
        "model_escalation_trigger": None,
        "upstream_model_route_preserved": True,
    }


def test_preserve_model_route_metadata_keeps_escalation_fields_without_fabrication() -> None:
    out = {"metadata": {"existing": "keep"}}
    source = {
        "metadata": {
            "selected_model": "retry-model",
            "model_route_reason": "purpose_retry_escalation",
            "model_route_family": "retry_escalation",
            "model_route_purpose": "retry_escalation",
            "model_retry_attempt": 1,
            "model_escalated": True,
            "model_escalation_trigger": "retry_reason:validator_voice",
        }
    }

    api_mod._preserve_model_route_metadata(out, source)

    assert out["metadata"] == {
        "existing": "keep",
        "selected_model": "retry-model",
        "model_route_reason": "purpose_retry_escalation",
        "model_route_family": "retry_escalation",
        "model_route_purpose": "retry_escalation",
        "model_retry_attempt": 1,
        "model_escalated": True,
        "model_escalation_trigger": "retry_reason:validator_voice",
    }
