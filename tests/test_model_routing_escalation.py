from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import openai
import pytest

import game.api as api_mod
import game.gm as gm_mod
import game.model_routing as routing_mod
from game.api import _build_gpt_narration_from_authoritative_state
from game.defaults import default_campaign, default_character, default_session, default_world
from game.storage import get_scene_runtime

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


def _install_model_names(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    names = {
        "default": "default-route-model",
        "high_precision": "high-precision-route-model",
        "retry": "retry-route-model",
    }
    monkeypatch.setattr(routing_mod, "ENABLE_MODEL_ROUTING", True)
    monkeypatch.setattr(routing_mod, "DEFAULT_MODEL_NAME", names["default"])
    monkeypatch.setattr(routing_mod, "HIGH_PRECISION_MODEL_NAME", names["high_precision"])
    monkeypatch.setattr(routing_mod, "RETRY_ESCALATION_MODEL_NAME", names["retry"])
    return names


def _gm_payload(text: str = "The checkpoint holds steady.") -> dict[str, Any]:
    return {
        "player_facing_text": text,
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
        "metadata": {},
    }


def _retryable_upstream_error_payload() -> dict[str, Any]:
    out = _gm_payload("The game master is temporarily unavailable. Please try again.")
    out["tags"] = ["error", "gpt_api_error:server_error", "gpt_api_error_retryable"]
    out["metadata"] = {
        "upstream_api_error": {
            "failure_class": "server_error",
            "retryable": True,
            "status_code": 503,
            "error_code": None,
            "message_excerpt": "temporary outage",
        }
    }
    return out


def _routed_upstream_error_payload(
    *,
    selected_model: str,
    route_reason: str,
    route_family: str,
    purpose: str,
    retry_attempt: int,
    escalation_trigger: str | None,
) -> dict[str, Any]:
    out = _retryable_upstream_error_payload()
    out["metadata"] = {
        **(out.get("metadata") if isinstance(out.get("metadata"), dict) else {}),
        "selected_model": selected_model,
        "model_route_reason": route_reason,
        "model_route_family": route_family,
        "model_route_purpose": purpose,
        "model_retry_attempt": retry_attempt,
        "model_escalated": escalation_trigger is not None,
        "model_escalation_trigger": escalation_trigger,
    }
    out["debug_notes"] = f"model_route:{route_family}:{route_reason}:{selected_model}"
    if escalation_trigger:
        out["debug_notes"] += f" | model_escalated:{escalation_trigger}"
    return out


def _narration_kwargs() -> dict[str, Any]:
    session = default_session()
    session["active_scene_id"] = "t_scene"
    session.setdefault("scene_runtime", {})
    world = default_world()
    scene = {
        "scene": {
            "id": "t_scene",
            "location": "Gate",
            "summary": "A checkpoint in the rain.",
            "visible_facts": ["Rain darkens the flagstones."],
            "discoverable_clues": [],
            "hidden_facts": [],
            "exits": [],
            "enemies": [],
        }
    }
    resolution = {
        "kind": "observe",
        "prompt": "I watch the gate.",
        "metadata": {},
    }
    return {
        "campaign": default_campaign(),
        "world": world,
        "session": session,
        "character": default_character(),
        "scene": scene,
        "combat": {"in_combat": False},
        "recent_log": [],
        "user_text": resolution["prompt"],
        "resolution": resolution,
        "scene_runtime": get_scene_runtime(session, "t_scene"),
        "segmented_turn": None,
        "route_choice": None,
        "directed_social_entry": None,
        "response_type_contract": None,
        "latency_sink": None,
    }


def test_strict_social_turn_selects_high_precision_model_and_marks_escalation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_openai_recorder(
        monkeypatch,
        response_text='{"player_facing_text":"ok","tags":[]}',
    )
    names = _install_model_names(monkeypatch)

    out = gm_mod.call_gpt(
        [{"role": "user", "content": "Hello"}],
        purpose="strict_social",
        strict_social=True,
    )

    assert calls[0]["model"] == names["high_precision"]
    assert out["metadata"]["selected_model"] == names["high_precision"]
    assert out["metadata"]["model_route_purpose"] == "strict_social"
    assert out["metadata"]["model_escalated"] is True
    assert out["metadata"]["model_escalation_trigger"] == "strict_social"
    assert "model_escalated:strict_social" in out["debug_notes"]


def test_retry_attempt_one_selects_retry_model_and_uses_retry_attempt_trigger(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_openai_recorder(
        monkeypatch,
        response_text='{"player_facing_text":"ok","tags":[]}',
    )
    names = _install_model_names(monkeypatch)

    out = gm_mod.call_gpt(
        [{"role": "user", "content": "Hello"}],
        purpose="retry_escalation",
        retry_attempt=1,
    )

    assert calls[0]["model"] == names["retry"]
    assert out["metadata"]["selected_model"] == names["retry"]
    assert out["metadata"]["model_route_purpose"] == "retry_escalation"
    assert out["metadata"]["model_retry_attempt"] == 1
    assert out["metadata"]["model_escalated"] is True
    assert out["metadata"]["model_escalation_trigger"] == "retry_attempt"
    assert "model_escalated:retry_attempt" in out["debug_notes"]


def test_retry_reason_selects_retry_escalation_metadata_trigger(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_openai_recorder(
        monkeypatch,
        response_text='{"player_facing_text":"ok","tags":[]}',
    )
    names = _install_model_names(monkeypatch)

    out = gm_mod.call_gpt(
        [{"role": "user", "content": "Hello"}],
        purpose="retry_escalation",
        retry_reason="validator_voice",
    )

    assert calls[0]["model"] == names["retry"]
    assert out["metadata"]["selected_model"] == names["retry"]
    assert out["metadata"]["model_escalated"] is True
    assert out["metadata"]["model_escalation_trigger"] == "retry_reason:validator_voice"
    assert "model_escalated:retry_reason:validator_voice" in out["debug_notes"]


def test_primary_turn_stays_on_default_model_without_escalation_debug_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_openai_recorder(
        monkeypatch,
        response_text='{"player_facing_text":"ok","tags":[]}',
    )
    names = _install_model_names(monkeypatch)

    out = gm_mod.call_gpt(
        [{"role": "user", "content": "Hello"}],
        purpose="primary_turn",
    )

    assert calls[0]["model"] == names["default"]
    assert out["metadata"]["selected_model"] == names["default"]
    assert out["metadata"]["model_route_purpose"] == "primary_turn"
    assert out["metadata"]["model_escalated"] is False
    assert out["metadata"]["model_escalation_trigger"] is None
    assert "model_escalated:" not in out["debug_notes"]


def test_force_high_precision_marks_metadata_and_debug_trigger(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = _install_openai_recorder(
        monkeypatch,
        response_text='{"player_facing_text":"ok","tags":[]}',
    )
    names = _install_model_names(monkeypatch)

    out = gm_mod.call_gpt(
        [{"role": "user", "content": "Hello"}],
        purpose="primary_turn",
        force_high_precision=True,
    )

    assert calls[0]["model"] == names["high_precision"]
    assert out["metadata"]["selected_model"] == names["high_precision"]
    assert out["metadata"]["model_escalated"] is True
    assert out["metadata"]["model_escalation_trigger"] == "force_high_precision"
    assert "model_escalated:force_high_precision" in out["debug_notes"]


def test_api_initial_strict_social_call_passes_strict_social_route_kwargs(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, Any]] = []

    def fake_call_gpt(messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
        calls.append({"messages": list(messages), **kwargs})
        return _gm_payload()

    monkeypatch.setattr(api_mod, "call_gpt", fake_call_gpt)
    monkeypatch.setattr(api_mod, "detect_retry_failures", lambda **_kwargs: [])
    monkeypatch.setattr(api_mod, "apply_response_policy_enforcement", lambda gm, **_kwargs: gm)
    monkeypatch.setattr(api_mod, "_session_social_authority", lambda _session: True)
    monkeypatch.setattr(api_mod, "strict_social_emission_will_apply", lambda *_a, **_k: False)

    _build_gpt_narration_from_authoritative_state(**_narration_kwargs())

    assert len(calls) == 1
    assert calls[0]["purpose"] == "strict_social"
    assert calls[0]["strict_social"] is True
    assert calls[0]["retry_attempt"] == 0
    assert calls[0]["retry_reason"] is None


def test_api_retry_loop_passes_retry_escalation_reason_and_attempt(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, Any]] = []

    def fake_call_gpt(messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
        calls.append({"messages": list(messages), **kwargs})
        if len(calls) == 1:
            return _gm_payload("TRIGGER_VALIDATOR_RETRY")
        return _gm_payload("Captain Veyra answers the question directly.")

    def fake_detect_retry_failures(*, gm_reply: dict[str, Any], **_kwargs: Any) -> list[dict[str, Any]]:
        if "TRIGGER_VALIDATOR_RETRY" in str(gm_reply.get("player_facing_text") or ""):
            return [
                {
                    "failure_class": "validator_voice",
                    "priority": 20,
                    "reasons": ["validator_voice:as_an_ai"],
                }
            ]
        return []

    monkeypatch.setattr(api_mod, "call_gpt", fake_call_gpt)
    monkeypatch.setattr(api_mod, "detect_retry_failures", fake_detect_retry_failures)
    monkeypatch.setattr(api_mod, "apply_response_policy_enforcement", lambda gm, **_kwargs: gm)
    monkeypatch.setattr(api_mod, "build_retry_prompt_for_failure", lambda *_a, **_k: "Retry target: validator_voice.")

    _build_gpt_narration_from_authoritative_state(**_narration_kwargs())

    assert len(calls) == 2
    assert calls[0]["purpose"] == "primary_turn"
    assert calls[1]["purpose"] == "retry_escalation"
    assert calls[1]["retry_attempt"] == 1
    assert calls[1]["retry_reason"] == "validator_voice"
    assert calls[1]["strict_social"] is False


def test_api_retryable_upstream_retry_passes_attempt_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, Any]] = []

    def fake_call_gpt(messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
        calls.append({"messages": list(messages), **kwargs})
        if len(calls) == 1:
            return _retryable_upstream_error_payload()
        return _gm_payload("Captain Veyra keeps watch at the gate.")

    monkeypatch.setattr(api_mod, "call_gpt", fake_call_gpt)
    monkeypatch.setattr(api_mod, "detect_retry_failures", lambda **_kwargs: [])
    monkeypatch.setattr(api_mod, "apply_response_policy_enforcement", lambda gm, **_kwargs: gm)

    _build_gpt_narration_from_authoritative_state(**_narration_kwargs())

    assert len(calls) == 2
    assert calls[0]["purpose"] == "primary_turn"
    assert calls[1]["purpose"] == "retry_escalation"
    assert calls[1]["retry_attempt"] == 1
    assert calls[1]["retry_reason"] == "server_error"


def test_strict_social_route_metadata_survives_upstream_fast_fallback_when_preserved(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, Any]] = []
    names = _install_model_names(monkeypatch)

    def fake_call_gpt(messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
        calls.append({"messages": list(messages), **kwargs})
        return _routed_upstream_error_payload(
            selected_model=names["high_precision"],
            route_reason="purpose_strict_social",
            route_family="high_precision",
            purpose="strict_social",
            retry_attempt=0,
            escalation_trigger="strict_social",
        )

    kwargs = _narration_kwargs()
    kwargs["route_choice"] = "dialogue"
    kwargs["resolution"] = {
        "kind": "",
        "prompt": "Runner, what did you see?",
        "metadata": {},
    }

    monkeypatch.setattr(api_mod, "call_gpt", fake_call_gpt)
    monkeypatch.setattr(api_mod, "detect_retry_failures", lambda **_kwargs: [])
    monkeypatch.setattr(api_mod, "apply_response_policy_enforcement", lambda gm, **_kwargs: gm)
    monkeypatch.setattr(api_mod, "_session_social_authority", lambda _session: True)
    monkeypatch.setattr(api_mod, "strict_social_emission_will_apply", lambda *_a, **_k: False)

    out = _build_gpt_narration_from_authoritative_state(**kwargs)

    assert len(calls) == 1
    assert calls[0]["purpose"] == "strict_social"
    assert out["metadata"]["selected_model"] == names["high_precision"]
    assert out["metadata"]["model_route_reason"] == "purpose_strict_social"
    assert out["metadata"]["model_route_family"] == "high_precision"
    assert out["metadata"]["model_route_purpose"] == "strict_social"
    assert out["metadata"]["model_retry_attempt"] == 0
    assert out["metadata"]["model_escalated"] is True
    assert out["metadata"]["model_escalation_trigger"] == "strict_social"
    assert out["metadata"]["upstream_model_route_preserved"] is True


def test_retry_escalation_metadata_survives_retry_loop_upstream_fast_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[dict[str, Any]] = []
    names = _install_model_names(monkeypatch)

    def fake_call_gpt(messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
        calls.append({"messages": list(messages), **kwargs})
        if len(calls) == 1:
            return _gm_payload("TRIGGER_VALIDATOR_RETRY")
        return _routed_upstream_error_payload(
            selected_model=names["retry"],
            route_reason="purpose_retry_escalation",
            route_family="retry_escalation",
            purpose="retry_escalation",
            retry_attempt=1,
            escalation_trigger="retry_reason:validator_voice",
        )

    def fake_detect_retry_failures(*, gm_reply: dict[str, Any], **_kwargs: Any) -> list[dict[str, Any]]:
        if "TRIGGER_VALIDATOR_RETRY" in str(gm_reply.get("player_facing_text") or ""):
            return [
                {
                    "failure_class": "validator_voice",
                    "priority": 20,
                    "reasons": ["validator_voice:as_an_ai"],
                }
            ]
        return []

    monkeypatch.setattr(api_mod, "call_gpt", fake_call_gpt)
    monkeypatch.setattr(api_mod, "detect_retry_failures", fake_detect_retry_failures)
    monkeypatch.setattr(api_mod, "apply_response_policy_enforcement", lambda gm, **_kwargs: gm)
    monkeypatch.setattr(api_mod, "build_retry_prompt_for_failure", lambda *_a, **_k: "Retry target: validator_voice.")

    out = _build_gpt_narration_from_authoritative_state(**_narration_kwargs())

    assert len(calls) == 2
    assert calls[0]["purpose"] == "primary_turn"
    assert calls[1]["purpose"] == "retry_escalation"
    assert calls[1]["retry_attempt"] == 1
    assert calls[1]["retry_reason"] == "validator_voice"
    assert out["metadata"]["selected_model"] == names["retry"]
    assert out["metadata"]["model_route_reason"] == "purpose_retry_escalation"
    assert out["metadata"]["model_route_family"] == "retry_escalation"
    assert out["metadata"]["model_route_purpose"] == "retry_escalation"
    assert out["metadata"]["model_retry_attempt"] == 1
    assert out["metadata"]["model_escalated"] is True
    assert out["metadata"]["model_escalation_trigger"] == "retry_reason:validator_voice"
    assert out["metadata"]["upstream_model_route_preserved"] is True
