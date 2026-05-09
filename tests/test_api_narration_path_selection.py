"""API narration path-selection snapshots for the manual-play GPT builder."""
from __future__ import annotations

from typing import Any

import pytest

import game.api as api_mod
from game.api import _build_gpt_narration_from_authoritative_state
from game.defaults import default_campaign, default_character, default_session, default_world
from game.realization_authority import FALLBACK_FAMILIES
from game.realization_provenance import (
    GPT_BUDGET_OR_PROVIDER_FAILURE,
    REALIZATION_FALLBACK_FAMILY_FIELD,
    RETRY_TERMINAL_FALLBACK,
)
from game.storage import get_scene_runtime

pytestmark = pytest.mark.unit


def _scene() -> dict[str, Any]:
    return {
        "scene": {
            "id": "t_scene",
            "location": "Gate Yard",
            "summary": "A guarded yard.",
            "visible_facts": ["Rain darkens the flagstones."],
            "discoverable_clues": [],
            "hidden_facts": [],
            "exits": [],
            "enemies": [],
        }
    }


def _base_kw(*, resolution: dict[str, Any] | None = None) -> dict[str, Any]:
    session = default_session()
    session["turn_counter"] = 7
    session["active_scene_id"] = "t_scene"
    session.setdefault("scene_runtime", {})
    res = resolution or {
        "kind": "observe",
        "prompt": "I watch the gate.",
        "success": True,
        "metadata": {"human_adjacent_intent_family": "watch"},
    }
    return {
        "campaign": default_campaign(),
        "world": default_world(),
        "session": session,
        "character": default_character(),
        "scene": _scene(),
        "combat": {"in_combat": False},
        "recent_log": [],
        "user_text": str(res.get("prompt") or "I wait."),
        "resolution": res,
        "scene_runtime": get_scene_runtime(session, "t_scene"),
        "segmented_turn": None,
        "route_choice": None,
        "directed_social_entry": None,
        "response_type_contract": None,
        "latency_sink": None,
        "normalized_action": {"type": str(res.get("kind") or "observe")},
    }


def _gm(text: str, *, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "player_facing_text": text,
        "tags": [],
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "",
        "metadata": dict(metadata or {}),
    }


def _route_source(out: dict[str, Any]) -> str:
    md = out.get("metadata") if isinstance(out.get("metadata"), dict) else {}
    fem = out.get("_final_emission_meta") if isinstance(out.get("_final_emission_meta"), dict) else {}
    seam = md.get("narration_seam") if isinstance(md.get("narration_seam"), dict) else {}
    return str(
        fem.get("final_emitted_source")
        or md.get("final_emitted_source")
        or seam.get("path_kind")
        or ""
    )


def _assert_known_family(out: dict[str, Any], expected: str | None = None) -> str:
    md = out.get("metadata") if isinstance(out.get("metadata"), dict) else {}
    family = str(out.get(REALIZATION_FALLBACK_FAMILY_FIELD) or md.get(REALIZATION_FALLBACK_FAMILY_FIELD) or "")
    assert family in FALLBACK_FAMILIES
    if expected is not None:
        assert family == expected
    return family


def _assert_all_emitted_families_known(out: dict[str, Any]) -> list[str]:
    md = out.get("metadata") if isinstance(out.get("metadata"), dict) else {}
    families = [
        str(value)
        for value in (
            out.get(REALIZATION_FALLBACK_FAMILY_FIELD),
            md.get(REALIZATION_FALLBACK_FAMILY_FIELD),
        )
        if isinstance(value, str) and value
    ]
    assert families
    assert all(family in FALLBACK_FAMILIES for family in families)
    return families


@pytest.fixture(autouse=True)
def _quiet_terminal_gates(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(api_mod, "apply_response_policy_enforcement", lambda gm, **_k: gm)


def test_api_narration_normal_gpt_path_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, Any]] = []

    def fake_gpt(_messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
        calls.append(dict(kwargs))
        return _gm("Rain beads on the gate chain.", metadata={"existing_marker": "normal"})

    monkeypatch.setattr(api_mod, "call_gpt", fake_gpt)
    monkeypatch.setattr(api_mod, "detect_retry_failures", lambda **_k: [])

    out = _build_gpt_narration_from_authoritative_state(**_base_kw())

    assert out["player_facing_text"]
    assert len(calls) == 1
    assert calls[0]["purpose"] == "primary_turn"
    assert calls[0]["retry_attempt"] == 0
    assert calls[0]["retry_reason"] is None
    assert calls[0]["strict_social"] is False
    assert _route_source(out) == "resolved_turn_ctir_bundle"
    md = out["metadata"]
    assert md["existing_marker"] == "normal"
    assert REALIZATION_FALLBACK_FAMILY_FIELD not in md


def test_api_narration_planner_convergence_emergency_path_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(api_mod, "build_messages", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("no prompt")))
    monkeypatch.setattr(api_mod, "call_gpt", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("no gpt")))
    monkeypatch.setattr(
        api_mod,
        "build_narration_plan_bundle",
        lambda **_k: {"plan_metadata": {"ctir_stamp": ""}, "narrative_plan": None, "renderer_inputs": {}},
    )
    kw = _base_kw()

    out = _build_gpt_narration_from_authoritative_state(**kw)

    assert out["player_facing_text"]
    assert _route_source(out)
    assert _assert_known_family(out) in FALLBACK_FAMILIES
    md = out["metadata"]
    assert md["human_adjacent_intent_family"] == "watch"
    assert md["narration_seam"]["path_kind"] == "resolved_turn_ctir_planner_convergence_seam"
    assert md["narration_seam"]["emergency_nonplan_output"] is True
    assert md["planner_convergence_report"]["failure_codes"]


def test_api_narration_gpt_budget_failure_path_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(api_mod, "MANUAL_PLAY_MAX_CALL_GPT", 0)
    monkeypatch.setattr(api_mod, "call_gpt", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("budget skips GPT")))
    monkeypatch.setattr(api_mod, "detect_retry_failures", lambda **_k: [])

    out = _build_gpt_narration_from_authoritative_state(**_base_kw())

    assert out["player_facing_text"]
    assert _route_source(out) == "manual_play_gpt_budget_exceeded"
    families = _assert_all_emitted_families_known(out)
    assert out[REALIZATION_FALLBACK_FAMILY_FIELD] == RETRY_TERMINAL_FALLBACK
    md = out["metadata"]
    assert md[REALIZATION_FALLBACK_FAMILY_FIELD] == GPT_BUDGET_OR_PROVIDER_FAILURE
    assert GPT_BUDGET_OR_PROVIDER_FAILURE in families
    assert md["human_adjacent_intent_family"] == "watch"
    assert md["upstream_api_error"]["failure_class"] == "manual_play_gpt_budget_exceeded"


def test_api_narration_targeted_retry_path_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[dict[str, Any]] = []

    def fake_gpt(messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
        calls.append(dict(kwargs))
        if len(messages) <= 2:
            return _gm("TRIGGER_VALIDATOR_VOICE", metadata={"existing_marker": "initial"})
        return _gm("The gate chain settles after the retry.", metadata={"existing_marker": "retry"})

    def fake_failures(*, gm_reply: dict[str, Any], **_kwargs: Any) -> list[dict[str, Any]]:
        if "TRIGGER_VALIDATOR_VOICE" in str(gm_reply.get("player_facing_text") or ""):
            return [{"failure_class": "validator_voice", "priority": 20, "reasons": ["snapshot_trigger"]}]
        return []

    monkeypatch.setattr(api_mod, "call_gpt", fake_gpt)
    monkeypatch.setattr(api_mod, "detect_retry_failures", fake_failures)
    monkeypatch.setattr(api_mod, "choose_retry_strategy", lambda failures: failures[0] if failures else None)
    monkeypatch.setattr(api_mod, "build_retry_prompt_for_failure", lambda *_a, **_k: "retry please")

    out = _build_gpt_narration_from_authoritative_state(**_base_kw())

    assert out["player_facing_text"] == "The gate chain settles after the retry."
    assert [c["retry_attempt"] for c in calls] == [0, 1]
    assert calls[1]["purpose"] == "retry_escalation"
    assert calls[1]["retry_reason"] == "validator_voice"
    assert _route_source(out) == "resolved_turn_ctir_bundle"
    md = out["metadata"]
    assert md["existing_marker"] == "retry"
    assert md["narration_seam"]["same_turn_retry_messages_reused"] is True


def test_api_narration_terminal_retry_fallback_path_snapshot(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(api_mod, "MAX_TARGETED_RETRY_ATTEMPTS", 0)
    monkeypatch.setattr(
        api_mod,
        "call_gpt",
        lambda *_a, **_k: _gm("TRIGGER_TERMINAL_RETRY", metadata={"existing_marker": "terminal"}),
    )
    monkeypatch.setattr(
        api_mod,
        "detect_retry_failures",
        lambda **_k: [{"failure_class": "validator_voice", "priority": 20, "reasons": ["snapshot_terminal"]}],
    )
    monkeypatch.setattr(api_mod, "choose_retry_strategy", lambda failures: failures[0] if failures else None)

    out = _build_gpt_narration_from_authoritative_state(**_base_kw())

    assert out["player_facing_text"]
    assert _route_source(out)
    _assert_known_family(out, RETRY_TERMINAL_FALLBACK)
    md = out["metadata"]
    assert md["existing_marker"] == "terminal"
    assert md["narration_seam"]["path_kind"] == "resolved_turn_ctir_force_terminal_fallback"
    assert md["narration_seam"]["emergency_nonplan_output"] is True
