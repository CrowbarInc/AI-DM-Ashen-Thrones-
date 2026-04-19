"""Regression: retry-stable CTIR stamp reuse; rebuild when stamp changes."""

from __future__ import annotations

from typing import Any

import pytest

import game.api as api_mod
import game.ctir as ctir_mod
from game.api import _build_gpt_narration_from_authoritative_state
from game.ctir_runtime import build_runtime_ctir_for_narration, detach_ctir, ensure_ctir_for_turn, get_attached_ctir
from game.defaults import default_campaign, default_character, default_session, default_world
from game.storage import get_scene_runtime

pytestmark = pytest.mark.unit


def _narration_kw() -> dict[str, Any]:
    session = default_session()
    session["turn_counter"] = 3
    session["active_scene_id"] = "t_scene"
    session.setdefault("scene_runtime", {})
    world = default_world()
    scene = {
        "scene": {
            "id": "t_scene",
            "location": "Yard",
            "summary": "Open ground.",
            "visible_facts": [],
            "discoverable_clues": [],
            "hidden_facts": [],
            "exits": [],
            "enemies": [],
        }
    }
    resolution = {"kind": "observe", "prompt": "Look around.", "success": True, "metadata": {}}
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
        "normalized_action": {"type": "observe"},
    }


def test_ensure_ctir_same_stamp_does_not_invoke_builder_twice() -> None:
    sess: dict[str, Any] = {}
    calls = 0

    def builder() -> dict[str, Any]:
        nonlocal calls
        calls += 1
        return build_runtime_ctir_for_narration(
            turn_id=1,
            scene_id="s",
            player_input="x",
            builder_source="test.retry_stability",
            resolution={"kind": "observe"},
            normalized_action=None,
            combat=None,
            session=None,
        )

    a = ensure_ctir_for_turn(sess, turn_stamp="stamp-a", builder=builder)
    b = ensure_ctir_for_turn(sess, turn_stamp="stamp-a", builder=builder)
    assert calls == 1
    assert a is b


def test_ensure_ctir_new_stamp_rebuilds() -> None:
    sess: dict[str, Any] = {}
    calls = 0

    def builder() -> dict[str, Any]:
        nonlocal calls
        calls += 1
        return build_runtime_ctir_for_narration(
            turn_id=calls,
            scene_id="s",
            player_input="x",
            builder_source="test.retry_stability",
            resolution={"kind": "observe"},
            normalized_action=None,
            combat=None,
            session=None,
        )

    first = ensure_ctir_for_turn(sess, turn_stamp="one", builder=builder)
    second = ensure_ctir_for_turn(sess, turn_stamp="two", builder=builder)
    assert calls == 2
    assert first is not second


def test_api_retry_loop_single_ctir_build(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []
    orig = ctir_mod.build_ctir

    def counting_build_ctir(**kwargs: Any) -> dict[str, Any]:
        calls.append(1)
        return orig(**kwargs)

    monkeypatch.setattr(ctir_mod, "build_ctir", counting_build_ctir)

    def fake_call_gpt(_messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
        if not getattr(fake_call_gpt, "done", False):  # type: ignore[attr-defined]
            fake_call_gpt.done = True  # type: ignore[attr-defined]
            return {"player_facing_text": "TRIGGER_VALIDATOR_RETRY", "tags": []}
        return {"player_facing_text": "Final line.", "tags": []}

    fake_call_gpt.done = False  # type: ignore[attr-defined]

    def fake_detect_retry_failures(*, gm_reply: dict[str, Any], **_kwargs: Any) -> list[dict[str, Any]]:
        if "TRIGGER_VALIDATOR_RETRY" in str(gm_reply.get("player_facing_text") or ""):
            return [{"failure_class": "validator_voice", "priority": 20, "reasons": ["validator_voice"]}]
        return []

    monkeypatch.setattr(api_mod, "call_gpt", fake_call_gpt)
    monkeypatch.setattr(api_mod, "detect_retry_failures", fake_detect_retry_failures)
    monkeypatch.setattr(api_mod, "apply_response_policy_enforcement", lambda gm, **_k: gm)
    monkeypatch.setattr(api_mod, "build_retry_prompt_for_failure", lambda *_a, **_k: "retry steer")

    kw = _narration_kw()
    _build_gpt_narration_from_authoritative_state(**kw)
    assert len(calls) == 1
    assert get_attached_ctir(kw["session"]) is not None


def test_detach_before_ensure_allows_explicit_rebuild_same_session() -> None:
    sess: dict[str, Any] = {}
    built = ensure_ctir_for_turn(
        sess,
        turn_stamp="a",
        builder=lambda: build_runtime_ctir_for_narration(
            turn_id=0,
            scene_id=None,
            player_input="p",
            builder_source="t",
            resolution={"kind": "x"},
            normalized_action=None,
            combat=None,
            session=None,
        ),
    )
    detach_ctir(sess)
    again = ensure_ctir_for_turn(
        sess,
        turn_stamp="a",
        builder=lambda: build_runtime_ctir_for_narration(
            turn_id=0,
            scene_id=None,
            player_input="p",
            builder_source="t",
            resolution={"kind": "y"},
            normalized_action=None,
            combat=None,
            session=None,
        ),
    )
    assert built is not again
    assert get_attached_ctir(sess)["resolution"]["kind"] == "y"
