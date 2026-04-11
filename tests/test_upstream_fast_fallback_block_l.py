"""Block L regressions: non-retryable upstream classification, fast fallback, metadata preservation."""

from __future__ import annotations

from typing import Any

import pytest

import game.api as game_api_module
from game.api import (
    MANUAL_PLAY_MAX_CALL_GPT,
    _attach_resolution_contract_metadata_to_gm_output,
    _build_gpt_narration_from_authoritative_state,
    _synthetic_manual_play_gpt_budget_gm,
)
from game.defaults import default_campaign, default_character, default_session, default_world
from game.fallback_provenance_debug import METADATA_KEY, realign_fallback_provenance_selector_to_current_text
from game.final_emission_gate import apply_final_emission_gate
from game.gm import _classify_upstream_gpt_error
from game.storage import get_scene_runtime

pytestmark = pytest.mark.unit


def test_classify_model_and_quota_errors_are_nonretryable() -> None:
    class _Exc(Exception):
        def __init__(self, *, code: str | None = None, status: int | None = None, msg: str = ""):
            super().__init__(msg)
            self.code = code
            self.status_code = status

    q = _classify_upstream_gpt_error(_Exc(code="insufficient_quota", status=429, msg="quota"))
    assert q["failure_class"] == "insufficient_quota"
    assert q["retryable"] is False

    m = _classify_upstream_gpt_error(_Exc(code="model_not_found", status=404, msg="x"))
    assert m["failure_class"] == "model_not_found"
    assert m["retryable"] is False

    inv = _classify_upstream_gpt_error(_Exc(code="invalid_request_error", status=400, msg="bad"))
    assert inv["failure_class"] == "invalid_request"
    assert inv["retryable"] is False

    key = _classify_upstream_gpt_error(_Exc(code=None, status=None, msg="Incorrect API key provided"))
    assert key["failure_class"] == "invalid_api_key"
    assert key["retryable"] is False


def test_classify_transient_server_error_retryable() -> None:
    class _Exc(Exception):
        status_code = 503

    r = _classify_upstream_gpt_error(_Exc("unavailable"))
    assert r["failure_class"] == "server_error"
    assert r["retryable"] is True


def test_attach_resolution_contract_metadata_merges_block_jk_keys() -> None:
    gm: dict[str, Any] = {"metadata": {"upstream_api_error": {"failure_class": "insufficient_quota"}}}
    resolution = {
        "metadata": {
            "human_adjacent_intent_family": "listen",
            "implicit_focus_resolution": "speaking_group",
            "implicit_focus_anchor_fact": "A cluster murmurs.",
            "parser_lane": "human_adjacent_observe",
            "nearby_group_continuity_carryover": True,
        }
    }
    _attach_resolution_contract_metadata_to_gm_output(gm, resolution)
    md = gm["metadata"]
    assert md["human_adjacent_intent_family"] == "listen"
    assert md["implicit_focus_resolution"] == "speaking_group"
    assert md["nearby_group_continuity_carryover"] is True


def test_retry_loop_upstream_error_goes_straight_to_fast_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []

    def fake_gpt(_messages: list[dict[str, str]]) -> dict[str, Any]:
        calls.append(len(_messages))
        if len(calls) == 1:
            return {
                "player_facing_text": "TRIGGER_RETRY_LINE holds while the gate crowd churns.",
                "tags": [],
                "scene_update": None,
                "activate_scene_id": None,
                "new_scene_draft": None,
                "world_updates": None,
                "suggested_action": None,
                "debug_notes": "",
                "metadata": {},
            }
        return {
            "player_facing_text": "The game master is temporarily unavailable. Please try again.",
            "tags": ["error", "gpt_api_error:insufficient_quota", "gpt_api_error_nonretryable"],
            "scene_update": None,
            "activate_scene_id": None,
            "new_scene_draft": None,
            "world_updates": None,
            "suggested_action": None,
            "debug_notes": "quota",
            "metadata": {
                "upstream_api_error": {
                    "failure_class": "insufficient_quota",
                    "retryable": False,
                    "status_code": 429,
                    "error_code": "insufficient_quota",
                    "message_excerpt": "x",
                }
            },
        }

    def fake_detect_retry_failures(*, gm_reply: dict, **_kwargs: Any) -> list[dict[str, Any]]:
        if "TRIGGER_RETRY_LINE" in str(gm_reply.get("player_facing_text") or ""):
            return [
                {
                    "failure_class": "scene_stall",
                    "priority": 40,
                    "reasons": ["synthetic_block_l_retry_trigger"],
                }
            ]
        return []

    monkeypatch.setattr("game.api.call_gpt", fake_gpt)
    monkeypatch.setattr("game.api.detect_retry_failures", fake_detect_retry_failures)

    session = default_session()
    session["active_scene_id"] = "t_scene"
    session.setdefault("scene_runtime", {})
    world = default_world()
    scene = {
        "scene": {
            "id": "t_scene",
            "location": "Gate",
            "summary": "A checkpoint.",
            "visible_facts": ["A knot of patrons keeps their voices low."],
            "discoverable_clues": [],
            "hidden_facts": [],
            "exits": [],
            "enemies": [],
        }
    }
    resolution = {
        "kind": "observe",
        "prompt": "I listen in on the patrons.",
        "metadata": {
            "human_adjacent_intent_family": "listen",
            "implicit_focus_resolution": "speaking_group",
            "implicit_focus_anchor_fact": "A knot of patrons keeps their voices low.",
            "parser_lane": "human_adjacent_observe",
        },
    }

    out = _build_gpt_narration_from_authoritative_state(
        campaign=default_campaign(),
        world=world,
        session=session,
        character=default_character(),
        scene=scene,
        combat={"in_combat": False},
        recent_log=[],
        user_text=resolution["prompt"],
        resolution=resolution,
        scene_runtime=get_scene_runtime(session, "t_scene"),
        segmented_turn=None,
        route_choice=None,
        directed_social_entry=None,
        response_type_contract=None,
        latency_sink=None,
    )

    assert len(calls) == 2
    tags = [str(t) for t in (out.get("tags") or []) if isinstance(t, str)]
    assert "upstream_api_fast_fallback" in tags
    prov = (out.get("metadata") or {}).get(METADATA_KEY) or {}
    assert prov.get("source") == "fallback"
    assert prov.get("selector_player_facing_text")
    md = out.get("metadata") or {}
    assert md.get("human_adjacent_intent_family") == "listen"
    assert md.get("implicit_focus_resolution") == "speaking_group"

    gated = apply_final_emission_gate(
        dict(out),
        resolution=resolution,
        session=session,
        scene_id="t_scene",
        world=world,
    )
    gprov = (gated.get("metadata") or {}).get(METADATA_KEY) or {}
    assert gprov.get("gate_exit_vs_selector_match") is True


def test_transient_first_call_retry_still_attempts_second_call(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[int] = []

    def fake_gpt(_messages: list[dict[str, str]]) -> dict[str, Any]:
        calls.append(1)
        if len(calls) == 1:
            return {
                "player_facing_text": "The game master is temporarily unavailable. Please try again.",
                "tags": ["error", "gpt_api_error:server_error", "gpt_api_error_retryable"],
                "scene_update": None,
                "activate_scene_id": None,
                "new_scene_draft": None,
                "world_updates": None,
                "suggested_action": None,
                "debug_notes": "503",
                "metadata": {
                    "upstream_api_error": {
                        "failure_class": "server_error",
                        "retryable": True,
                        "status_code": 503,
                        "error_code": None,
                        "message_excerpt": "x",
                    }
                },
            }
        return {
            "player_facing_text": (
                "Captain Veyra folds her arms and watches the road while rain beads on the checkpoint slate."
            ),
            "tags": [],
            "scene_update": None,
            "activate_scene_id": None,
            "new_scene_draft": None,
            "world_updates": None,
            "suggested_action": None,
            "debug_notes": "",
            "metadata": {},
        }

    monkeypatch.setattr("game.api.call_gpt", fake_gpt)
    monkeypatch.setattr("game.api.detect_retry_failures", lambda **_k: [])
    monkeypatch.setattr(
        "game.api.apply_response_policy_enforcement",
        lambda gm, **_kwargs: gm,
    )

    session = default_session()
    session["active_scene_id"] = "t_scene"
    world = default_world()
    scene = {
        "scene": {
            "id": "t_scene",
            "location": "Gate",
            "summary": "Rain at the gate.",
            "visible_facts": ["Rain darkens the flagstones."],
            "discoverable_clues": [],
            "hidden_facts": [],
            "exits": [],
            "enemies": [],
        }
    }
    resolution = {"kind": "observe", "prompt": "I watch the rain.", "metadata": {}}

    out = _build_gpt_narration_from_authoritative_state(
        campaign=default_campaign(),
        world=world,
        session=session,
        character=default_character(),
        scene=scene,
        combat={"in_combat": False},
        recent_log=[],
        user_text=resolution["prompt"],
        resolution=resolution,
        scene_runtime=get_scene_runtime(session, "t_scene"),
        segmented_turn=None,
        route_choice=None,
        directed_social_entry=None,
        response_type_contract=None,
        latency_sink=None,
    )

    assert len(calls) == 2
    assert "upstream_api_fast_fallback" not in [str(t) for t in (out.get("tags") or [])]
    assert "checkpoint" in str(out.get("player_facing_text") or "").lower()


def test_gpt_budget_synthetic_is_nonretryable() -> None:
    g = _synthetic_manual_play_gpt_budget_gm()
    err = (g.get("metadata") or {}).get("upstream_api_error") or {}
    assert err.get("retryable") is False
    assert err.get("failure_class") == "manual_play_gpt_budget_exceeded"


def test_manual_play_max_gpt_constant_covers_nominal_turn(monkeypatch: pytest.MonkeyPatch) -> None:
    assert MANUAL_PLAY_MAX_CALL_GPT >= 4


def test_manual_play_gpt_budget_zero_skips_call_gpt(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(game_api_module, "MANUAL_PLAY_MAX_CALL_GPT", 0)
    invoked: list[bool] = []

    def boom(_messages: list[dict[str, str]]) -> dict[str, Any]:
        invoked.append(True)
        raise AssertionError("call_gpt must not run when budget is exhausted before first call")

    monkeypatch.setattr("game.api.call_gpt", boom)
    monkeypatch.setattr("game.api.detect_retry_failures", lambda **_k: [])

    session = default_session()
    session["active_scene_id"] = "t_scene"
    world = default_world()
    scene = {
        "scene": {
            "id": "t_scene",
            "location": "Gate",
            "summary": "A checkpoint.",
            "visible_facts": ["Rain darkens the flagstones."],
            "discoverable_clues": [],
            "hidden_facts": [],
            "exits": [],
            "enemies": [],
        }
    }
    resolution = {"kind": "observe", "prompt": "I watch.", "metadata": {}}

    out = _build_gpt_narration_from_authoritative_state(
        campaign=default_campaign(),
        world=world,
        session=session,
        character=default_character(),
        scene=scene,
        combat={"in_combat": False},
        recent_log=[],
        user_text=resolution["prompt"],
        resolution=resolution,
        scene_runtime=get_scene_runtime(session, "t_scene"),
        segmented_turn=None,
        route_choice=None,
        directed_social_entry=None,
        response_type_contract=None,
        latency_sink=None,
    )

    assert not invoked
    tags = [str(t) for t in (out.get("tags") or []) if isinstance(t, str)]
    assert "upstream_api_fast_fallback" in tags
    assert (out.get("metadata") or {}).get("upstream_api_error", {}).get("failure_class") == "manual_play_gpt_budget_exceeded"


def test_realign_fallback_provenance_selector_refreshes_fingerprint() -> None:
    from game.fallback_provenance_debug import attach_upstream_fast_fallback_provenance, fingerprint_player_facing

    gm: dict[str, Any] = {
        "player_facing_text": "BAD_SELECTOR_LINE",
        "tags": ["upstream_api_fast_fallback"],
        "metadata": {},
    }
    attach_upstream_fast_fallback_provenance(gm)
    prov0 = (gm.get("metadata") or {}).get(METADATA_KEY) or {}
    fp0 = str(prov0.get("content_fingerprint") or "")
    repaired = "Rain steadies on the checkpoint; the gate crowd holds its breath."
    realign_fallback_provenance_selector_to_current_text(gm, text=repaired, reason="test")
    prov1 = (gm.get("metadata") or {}).get(METADATA_KEY) or {}
    assert prov1.get("selector_player_facing_text") == repaired
    assert str(prov1.get("content_fingerprint") or "") == fingerprint_player_facing(repaired)
    assert fp0 and fp0 != prov1.get("content_fingerprint")
