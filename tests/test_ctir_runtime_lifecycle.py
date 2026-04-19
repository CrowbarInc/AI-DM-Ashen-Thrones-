"""Regression: CTIR detach at resolved-turn entry, per-turn build, distinct lifecycles across turns."""

from __future__ import annotations

from typing import Any

import pytest

import game.api as api_mod
from game.api import _run_resolved_turn_pipeline
from game.ctir_runtime import SESSION_CTIR_KEY, SESSION_CTIR_STAMP_KEY, get_attached_ctir
from game.defaults import default_campaign, default_character, default_session, default_world
from game.storage import get_scene_runtime

pytestmark = pytest.mark.unit


def _pipeline_kw(*, turn_counter: int = 5) -> dict[str, Any]:
    session = default_session()
    session["turn_counter"] = turn_counter
    session["active_scene_id"] = "t_scene"
    session.setdefault("scene_runtime", {})
    world = default_world()
    scene = {
        "scene": {
            "id": "t_scene",
            "location": "Gate",
            "summary": "A checkpoint.",
            "visible_facts": [],
            "discoverable_clues": [],
            "hidden_facts": [],
            "exits": [],
            "enemies": [],
        }
    }
    resolution = {
        "kind": "observe",
        "prompt": "I watch.",
        "success": True,
        "state_changes": {},
        "metadata": {},
    }
    return {
        "campaign": default_campaign(),
        "character": default_character(),
        "session": session,
        "world": world,
        "combat": {"in_combat": False, "round": 0},
        "scene": scene,
        "recent_log": [],
        "resolution": resolution,
        "normalized_action": {"id": "look", "type": "observe"},
        "fallback_user_text": resolution["prompt"],
        "segmented_turn": None,
        "route_choice": None,
        "directed_social_entry": None,
        "latency_sink": None,
    }


def test_pipeline_detaches_ctir_before_authoritative_mutation(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stale session CTIR must be cleared before engine mutation runs."""

    def fake_mutation(**kwargs: Any) -> tuple[Any, ...]:
        session = kwargs["session"]
        assert isinstance(session, dict)
        assert session.get(SESSION_CTIR_KEY) is None
        assert session.get(SESSION_CTIR_STAMP_KEY) is None
        scene = kwargs["scene"]
        return (
            scene,
            session,
            kwargs["combat"],
            [],
            get_scene_runtime(session, scene["scene"]["id"]),
        )

    monkeypatch.setattr(api_mod, "_apply_authoritative_resolution_state_mutation", fake_mutation)
    monkeypatch.setattr(api_mod, "call_gpt", lambda *_a, **_k: {"player_facing_text": "ok", "tags": []})
    monkeypatch.setattr(api_mod, "detect_retry_failures", lambda **_k: [])
    monkeypatch.setattr(api_mod, "apply_response_policy_enforcement", lambda gm, **_k: gm)
    monkeypatch.setattr(api_mod, "build_messages", lambda *_a, **_k: [{"role": "system", "content": "x"}, {"role": "user", "content": "{}"}])

    kw = _pipeline_kw()
    session = kw["session"]
    session[SESSION_CTIR_KEY] = {"version": 1, "stale": True}
    session[SESSION_CTIR_STAMP_KEY] = "old"

    _run_resolved_turn_pipeline(**kw)

    assert isinstance(session.get(SESSION_CTIR_KEY), dict)
    assert "stale" not in session[SESSION_CTIR_KEY]


def test_two_resolved_turns_replace_ctir_not_reuse_object(monkeypatch: pytest.MonkeyPatch) -> None:
    objects: list[int] = []

    def fake_mutation(**kwargs: Any) -> tuple[Any, ...]:
        scene = kwargs["scene"]
        session = kwargs["session"]
        return scene, session, kwargs["combat"], [], get_scene_runtime(session, scene["scene"]["id"])

    monkeypatch.setattr(api_mod, "_apply_authoritative_resolution_state_mutation", fake_mutation)
    monkeypatch.setattr(api_mod, "call_gpt", lambda *_a, **_k: {"player_facing_text": "ok", "tags": []})
    monkeypatch.setattr(api_mod, "detect_retry_failures", lambda **_k: [])
    monkeypatch.setattr(api_mod, "apply_response_policy_enforcement", lambda gm, **_k: gm)
    monkeypatch.setattr(api_mod, "build_messages", lambda *_a, **_k: [{"role": "system", "content": "x"}, {"role": "user", "content": "{}"}])

    kw1 = _pipeline_kw(turn_counter=10)
    _run_resolved_turn_pipeline(**kw1)
    first = kw1["session"].get(SESSION_CTIR_KEY)
    assert isinstance(first, dict)
    objects.append(id(first))

    kw2 = _pipeline_kw(turn_counter=11)
    # Fresh session object so we do not conflate identity with session reuse
    kw2["session"] = default_session()
    kw2["session"]["turn_counter"] = 11
    kw2["session"]["active_scene_id"] = "t_scene"
    kw2["session"].setdefault("scene_runtime", {})
    kw2["scene"] = kw1["scene"]
    kw2["resolution"] = dict(kw1["resolution"])
    kw2["resolution"]["prompt"] = "Second look."

    _run_resolved_turn_pipeline(**kw2)
    second = kw2["session"].get(SESSION_CTIR_KEY)
    assert isinstance(second, dict)
    assert id(second) != id(first)
