"""Integration tests: CTIR build point, ordering vs prompt construction, retry stability."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

import game.api as api_mod
import game.ctir as ctir_mod
from game.api import _build_gpt_narration_from_authoritative_state, _run_resolved_turn_pipeline
from game.ctir_runtime import (
    SESSION_CTIR_KEY,
    build_runtime_ctir_for_narration,
    detach_ctir,
    ensure_ctir_for_turn,
    get_attached_ctir,
)
from game.defaults import default_campaign, default_character, default_session, default_world
from game.storage import get_scene_runtime

pytestmark = pytest.mark.unit


def _fake_gm(text: str = "Narration ok.") -> dict[str, Any]:
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


def _narration_base_kwargs() -> dict[str, Any]:
    session = default_session()
    session["turn_counter"] = 7
    session["active_scene_id"] = "t_scene"
    session.setdefault("scene_runtime", {})
    world = default_world()
    scene = {
        "scene": {
            "id": "t_scene",
            "location": "Gate",
            "summary": "A checkpoint.",
            "visible_facts": ["Rain."],
            "discoverable_clues": [],
            "hidden_facts": [],
            "exits": [],
            "enemies": [],
        }
    }
    resolution = {
        "kind": "observe",
        "prompt": "I watch the gate.",
        "success": True,
        "state_changes": {"observed_gate": True},
        "metadata": {},
    }
    return {
        "campaign": default_campaign(),
        "world": world,
        "session": session,
        "character": default_character(),
        "scene": scene,
        "combat": {"in_combat": False, "round": 0},
        "recent_log": [],
        "user_text": resolution["prompt"],
        "resolution": resolution,
        "scene_runtime": get_scene_runtime(session, "t_scene"),
        "segmented_turn": None,
        "route_choice": None,
        "directed_social_entry": None,
        "response_type_contract": None,
        "latency_sink": None,
        "normalized_action": {"id": "look", "type": "observe", "label": "Look", "prompt": resolution["prompt"]},
    }


def test_ctir_attached_after_mutation_before_prompt_construction(monkeypatch: pytest.MonkeyPatch) -> None:
    order: list[str] = []

    def fake_mutation(**kwargs: Any) -> tuple[Any, ...]:
        order.append("mutation")
        scene = kwargs["scene"]
        session = kwargs["session"]
        combat = kwargs["combat"]
        resolution = kwargs["resolution"]
        rt = get_scene_runtime(session, scene["scene"]["id"])
        return scene, session, combat, [], rt

    def fake_build_messages(*args: Any, **kwargs: Any) -> list[dict[str, str]]:
        order.append("prompt")
        sess = args[2]
        assert isinstance(sess, dict)
        assert isinstance(sess.get(SESSION_CTIR_KEY), dict)
        return [{"role": "system", "content": "x"}, {"role": "user", "content": "{}"}]

    monkeypatch.setattr(api_mod, "_apply_authoritative_resolution_state_mutation", fake_mutation)
    monkeypatch.setattr(api_mod, "call_gpt", lambda *_a, **_k: _fake_gm())
    monkeypatch.setattr(api_mod, "detect_retry_failures", lambda **_k: [])
    monkeypatch.setattr(api_mod, "apply_response_policy_enforcement", lambda gm, **_k: gm)
    monkeypatch.setattr(api_mod, "build_messages", fake_build_messages)

    kw = _narration_base_kwargs()
    _run_resolved_turn_pipeline(
        campaign=kw["campaign"],
        character=kw["character"],
        session=kw["session"],
        world=kw["world"],
        combat=kw["combat"],
        scene=kw["scene"],
        recent_log=kw["recent_log"],
        resolution=kw["resolution"],
        normalized_action=kw["normalized_action"],
        fallback_user_text=kw["user_text"],
        latency_sink=None,
    )

    assert order == ["mutation", "prompt"]


def test_ctir_single_build_reused_across_api_retry_loop(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []
    orig = ctir_mod.build_ctir

    def counting_build_ctir(**kwargs: Any) -> dict[str, Any]:
        calls.append(1)
        return orig(**kwargs)

    monkeypatch.setattr(ctir_mod, "build_ctir", counting_build_ctir)

    def fake_call_gpt(_messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
        if len(fake_call_gpt.invocations) == 0:  # type: ignore[attr-defined]
            fake_call_gpt.invocations.append(1)  # type: ignore[attr-defined]
            return _fake_gm("TRIGGER_VALIDATOR_RETRY")
        return _fake_gm("He answers plainly.")

    fake_call_gpt.invocations = []  # type: ignore[attr-defined]

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
    monkeypatch.setattr(api_mod, "apply_response_policy_enforcement", lambda gm, **_k: gm)
    monkeypatch.setattr(api_mod, "build_retry_prompt_for_failure", lambda *_a, **_k: "retry steer")

    kw = _narration_base_kwargs()
    out = _build_gpt_narration_from_authoritative_state(**kw)

    assert len(calls) == 1
    assert "answers" in str(out.get("player_facing_text") or "").lower() or out.get("player_facing_text")
    ct1 = get_attached_ctir(kw["session"])
    assert ct1 is not None
    assert ct1 is get_attached_ctir(kw["session"])


def test_get_attached_ctir_returns_same_object_as_ensure_reentry() -> None:
    sess: dict[str, Any] = {}
    stamp = "s1"

    def builder() -> dict[str, Any]:
        return build_runtime_ctir_for_narration(
            turn_id=1,
            scene_id="a",
            player_input="x",
            builder_source="test.ensure",
            resolution={"kind": "k"},
            normalized_action=None,
            combat=None,
            session=None,
        )

    a = ensure_ctir_for_turn(sess, turn_stamp=stamp, builder=builder)
    b = ensure_ctir_for_turn(sess, turn_stamp=stamp, builder=builder)
    assert a is b


def test_prompt_and_message_layers_do_not_reference_ctir() -> None:
    """CTIR construction stays in the API/runtime seam, not prompt_context / message assembly."""
    root = Path(__file__).resolve().parents[1] / "game"
    for rel in ("prompt_context.py", "gm.py"):
        blob = (root / rel).read_text(encoding="utf-8")
        assert "build_ctir" not in blob
        assert "from game.ctir import" not in blob
        assert "import game.ctir\n" not in blob
        assert "import game.ctir\r\n" not in blob


def test_runtime_ctir_slices_are_bounded_no_session_blob() -> None:
    huge_session = default_session()
    huge_session["rogue_huge"] = {str(i): i for i in range(200)}
    c = build_runtime_ctir_for_narration(
        turn_id=0,
        scene_id="s",
        player_input="p",
        builder_source="test",
        resolution={"kind": "observe", "world_tick_events": [{"id": "e1"}]},
        normalized_action=None,
        combat={"in_combat": False},
        session=huge_session,
    )
    dumped = str(c)
    assert "rogue_huge" not in dumped
    assert SESSION_CTIR_KEY not in dumped


def test_detach_clears_attachment() -> None:
    s: dict[str, Any] = {}
    ensure_ctir_for_turn(
        s,
        turn_stamp="x",
        builder=lambda: build_runtime_ctir_for_narration(
            turn_id=0,
            scene_id=None,
            player_input="a",
            builder_source="t",
            resolution={"kind": "z"},
            normalized_action=None,
            combat=None,
            session=None,
        ),
    )
    assert get_attached_ctir(s) is not None
    detach_ctir(s)
    assert get_attached_ctir(s) is None
