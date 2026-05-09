"""API narration path-selection snapshots for the manual-play GPT builder."""
from __future__ import annotations

import copy
import sys
from typing import Any

import pytest

import game.api as api_mod
import game.api_turn_support as api_turn_support_module
from game.api import _build_gpt_narration_from_authoritative_state
from game.api_turn_support import _finalize_player_facing_for_turn
from game.final_emission_gate import apply_final_emission_gate as real_apply_final_emission_gate
from game.gm import apply_response_policy_enforcement as real_apply_response_policy_enforcement
from game.defaults import default_campaign, default_character, default_session, default_world
from game.final_emission_meta import read_final_emission_meta_dict
from game.realization_authority import FALLBACK_FAMILIES
from game.realization_provenance import (
    GPT_BUDGET_OR_PROVIDER_FAILURE,
    REALIZATION_FALLBACK_FAMILY_FIELD,
    RETRY_TERMINAL_FALLBACK,
)
from game.storage import get_scene_runtime
from game.upstream_response_repairs import (
    OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED,
    UPSTREAM_PREPARED_OPENING_FALLBACK_KEY,
)
from tests.test_final_emission_gate import EXPECTED_FRONTIER_GATE_OPENING_FALLBACK, _opening_gm_output

pytestmark = pytest.mark.unit

# Block AL / AM snapshot registry — keep aligned with Block AN contract guard (`test_block_an_*`).
_BLOCK_AL_ORCHESTRATION_HANDOFF_TEST_NAMES: tuple[str, ...] = (
    "test_block_al_handoff_normal_gpt_then_policy_then_gate",
    "test_block_al_handoff_gpt_budget_exceeded_skips_provider_call_order",
    "test_block_al_handoff_targeted_retry_second_gpt_before_policy_then_gate",
    "test_block_al_handoff_terminal_retry_force_fallback_before_policy_then_gate",
    "test_block_al_handoff_planner_convergence_emergency_skips_gpt_and_retry_stack",
)
_BLOCK_AM_POLICY_HANDOFF_TEST_NAMES: tuple[str, ...] = (
    "test_block_am_policy_handoff_adapter_callable",
    "test_block_am_policy_handoff_skips_enforcement_when_fast_fallback",
    "test_block_am_policy_handoff_runs_enforcement_when_not_fast_fallback",
    "test_block_am_policy_handoff_invokes_repair_after_policy_with_expected_reason",
    "test_block_am_policy_handoff_does_not_invoke_gpt_retry_or_final_gate",
)


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


def test_finalize_player_facing_scene_opening_carries_upstream_opening_fallback_payload() -> None:
    gm = _opening_gm_output()
    gm["player_facing_text"] = "Nearby crates appear disturbed."
    gm["tags"] = []
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    session.setdefault("scene_runtime", {})
    world = default_world()
    pub = gm["prompt_context"]["scene"]["public"]
    scene = {"scene": dict(pub)}
    resolution = {"kind": "scene_opening", "prompt": "Start the campaign."}

    out, _narr_meta = _finalize_player_facing_for_turn(
        gm,
        resolution=resolution,
        session=session,
        world=world,
        scene=scene,
    )

    assert isinstance(out, dict)
    pay = out.get(UPSTREAM_PREPARED_OPENING_FALLBACK_KEY)
    assert isinstance(pay, dict)
    assert pay["prepared_opening_fallback_text"] == EXPECTED_FRONTIER_GATE_OPENING_FALLBACK
    assert out["player_facing_text"] == EXPECTED_FRONTIER_GATE_OPENING_FALLBACK
    fem = read_final_emission_meta_dict(out) or {}
    assert fem.get("opening_fallback_authorship_source") == OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED


# --- Block AJ: narration hub finalize route classification (metadata only; no text production) ---


def test_block_aj_classify_narration_hub_route_finalize_labels() -> None:
    observe = {"kind": "observe", "prompt": "I watch."}
    assert (
        api_mod._classify_narration_hub_route(
            resolution=observe,
            planner_convergence_emergency_exit=False,
            gpt_budget_exceeded=False,
            fast_fallback_mode=False,
            used_force_terminal_fallback=False,
        )
        == "resolved_turn_ctir_bundle"
    )
    assert (
        api_mod._classify_narration_hub_route(
            resolution=observe,
            planner_convergence_emergency_exit=False,
            gpt_budget_exceeded=False,
            fast_fallback_mode=True,
            used_force_terminal_fallback=False,
        )
        == "resolved_turn_ctir_upstream_fast_fallback"
    )
    assert (
        api_mod._classify_narration_hub_route(
            resolution=observe,
            planner_convergence_emergency_exit=False,
            gpt_budget_exceeded=False,
            fast_fallback_mode=False,
            used_force_terminal_fallback=True,
        )
        == "resolved_turn_ctir_force_terminal_fallback"
    )
    assert (
        api_mod._classify_narration_hub_route(
            resolution=observe,
            planner_convergence_emergency_exit=True,
            gpt_budget_exceeded=False,
            fast_fallback_mode=False,
            used_force_terminal_fallback=False,
        )
        == "planner_convergence_emergency"
    )
    assert (
        api_mod._classify_narration_hub_route(
            resolution=observe,
            planner_convergence_emergency_exit=False,
            gpt_budget_exceeded=True,
            fast_fallback_mode=False,
            used_force_terminal_fallback=False,
        )
        == "gpt_budget_exceeded"
    )
    assert (
        api_mod._classify_narration_hub_route(
            resolution=None,
            planner_convergence_emergency_exit=False,
            gpt_budget_exceeded=False,
            fast_fallback_mode=False,
            used_force_terminal_fallback=False,
        )
        == "non_resolution_model_narration"
    )


def test_block_aj_build_narration_hub_route_meta_matches_snapshot_paths() -> None:
    observe = {"kind": "observe", "prompt": "I watch."}
    meta = api_mod._build_narration_hub_route_meta(
        resolution=observe,
        planner_convergence_emergency_exit=False,
        gpt_budget_exceeded=False,
        fast_fallback_mode=False,
        used_force_terminal_fallback=False,
        bundle_seam_requirement={"ok": True},
        gpt_calls_used=0,
    )
    assert meta["path_kind"] == "resolved_turn_ctir_bundle"
    assert meta["ctir_backed"] is True
    assert meta["plan_driven"] is True
    assert meta["emergency_nonplan_output"] is False

    meta_budget = api_mod._build_narration_hub_route_meta(
        resolution=observe,
        planner_convergence_emergency_exit=False,
        gpt_budget_exceeded=True,
        fast_fallback_mode=False,
        used_force_terminal_fallback=False,
        bundle_seam_requirement={"ok": True},
        gpt_calls_used=2,
    )
    assert meta_budget["path_kind"] == "manual_play_gpt_budget_exceeded"
    assert meta_budget["same_turn_retry_messages_reused"] is True


def test_block_aj_build_narration_hub_route_meta_does_not_mutate_bundle_seam() -> None:
    seam: dict[str, Any] = {"ok": False, "error": "unit_test_error", "skipped": "unit_skip"}
    seam_snapshot = copy.deepcopy(seam)
    api_mod._build_narration_hub_route_meta(
        resolution={"kind": "observe", "prompt": "x"},
        planner_convergence_emergency_exit=False,
        gpt_budget_exceeded=False,
        fast_fallback_mode=False,
        used_force_terminal_fallback=False,
        bundle_seam_requirement=seam,
        gpt_calls_used=0,
    )
    assert seam == seam_snapshot


def test_block_aj_narration_hub_finalize_annotation_parts_planner_skips_path_kind() -> None:
    route, pk, kw, attach_only = api_mod._narration_hub_finalize_annotation_parts(
        resolution={"kind": "observe"},
        planner_convergence_emergency_exit=True,
        gpt_budget_exceeded=False,
        fast_fallback_mode=False,
        used_force_terminal_fallback=False,
        bundle_seam_requirement={"ok": True},
        gpt_calls_used=0,
    )
    assert route == "planner_convergence_emergency"
    assert pk is None and kw is None
    assert attach_only is True


# --- Block AK: narration hub route helper contract guards ---


def test_block_ak_route_helpers_importable_and_callable() -> None:
    for name in (
        "_narration_hub_finalize_annotation_parts",
        "_classify_narration_hub_route",
        "_build_narration_hub_route_meta",
    ):
        assert callable(getattr(api_mod, name, None)), name
    r, pk, kw, att = api_mod._narration_hub_finalize_annotation_parts(
        resolution={"kind": "observe"},
        planner_convergence_emergency_exit=False,
        gpt_budget_exceeded=False,
        fast_fallback_mode=False,
        used_force_terminal_fallback=False,
        bundle_seam_requirement={"ok": True},
        gpt_calls_used=0,
    )
    assert r == "resolved_turn_ctir_bundle" and pk == "resolved_turn_ctir_bundle" and isinstance(kw, dict) and att is False


def test_block_ak_route_helpers_do_not_invoke_gpt_stack(monkeypatch: pytest.MonkeyPatch) -> None:
    def _forbidden_gpt(*_a: Any, **_k: Any) -> Any:
        raise AssertionError("route metadata helpers must not call call_gpt")

    monkeypatch.setattr(api_mod, "call_gpt", _forbidden_gpt)
    api_mod._classify_narration_hub_route(
        resolution={"kind": "observe"},
        planner_convergence_emergency_exit=False,
        gpt_budget_exceeded=False,
        fast_fallback_mode=False,
        used_force_terminal_fallback=False,
    )
    api_mod._build_narration_hub_route_meta(
        resolution={"kind": "observe"},
        planner_convergence_emergency_exit=False,
        gpt_budget_exceeded=False,
        fast_fallback_mode=False,
        used_force_terminal_fallback=False,
        bundle_seam_requirement={"ok": True},
        gpt_calls_used=0,
    )
    api_mod._narration_hub_finalize_annotation_parts(
        resolution={"kind": "observe"},
        planner_convergence_emergency_exit=False,
        gpt_budget_exceeded=False,
        fast_fallback_mode=False,
        used_force_terminal_fallback=False,
        bundle_seam_requirement={"ok": True},
        gpt_calls_used=0,
    )


def test_block_ak_route_helpers_do_not_mutate_resolution_or_seam_payloads() -> None:
    """Route helpers only read Mapping inputs; they must not alter caller-owned dicts."""
    resolution: dict[str, Any] = {
        "kind": "observe",
        "prompt": "I watch.",
        "metadata": {"nested": [1, 2]},
    }
    seam: dict[str, Any] = {"ok": True, "extra": {"x": 1}}
    res_snap = copy.deepcopy(resolution)
    seam_snap = copy.deepcopy(seam)
    api_mod._classify_narration_hub_route(
        resolution=resolution,
        planner_convergence_emergency_exit=False,
        gpt_budget_exceeded=False,
        fast_fallback_mode=False,
        used_force_terminal_fallback=False,
    )
    api_mod._build_narration_hub_route_meta(
        resolution=resolution,
        planner_convergence_emergency_exit=False,
        gpt_budget_exceeded=False,
        fast_fallback_mode=False,
        used_force_terminal_fallback=False,
        bundle_seam_requirement=seam,
        gpt_calls_used=0,
    )
    api_mod._narration_hub_finalize_annotation_parts(
        resolution=resolution,
        planner_convergence_emergency_exit=False,
        gpt_budget_exceeded=False,
        fast_fallback_mode=False,
        used_force_terminal_fallback=False,
        bundle_seam_requirement=seam,
        gpt_calls_used=1,
    )
    assert resolution == res_snap
    assert seam == seam_snap


def test_block_ak_planner_branch_skips_route_meta_and_skips_path_kind_in_parts() -> None:
    """Planner convergence finalize path does not produce annotate_narration_path_kind kwargs here."""
    observe = {"kind": "observe", "prompt": "I wait."}
    assert api_mod._build_narration_hub_route_meta(
        resolution=observe,
        planner_convergence_emergency_exit=True,
        gpt_budget_exceeded=False,
        fast_fallback_mode=False,
        used_force_terminal_fallback=False,
        bundle_seam_requirement={"ok": True},
        gpt_calls_used=0,
    ) == {}
    _r, pk, kw, attach = api_mod._narration_hub_finalize_annotation_parts(
        resolution=observe,
        planner_convergence_emergency_exit=True,
        gpt_budget_exceeded=False,
        fast_fallback_mode=False,
        used_force_terminal_fallback=False,
        bundle_seam_requirement={"ok": True},
        gpt_calls_used=0,
    )
    assert pk is None and kw is None and attach is True


def test_block_ak_route_meta_snapshot_normal_bundle_matches_contract() -> None:
    observe = {"kind": "observe", "prompt": "I watch."}
    meta = api_mod._build_narration_hub_route_meta(
        resolution=observe,
        planner_convergence_emergency_exit=False,
        gpt_budget_exceeded=False,
        fast_fallback_mode=False,
        used_force_terminal_fallback=False,
        bundle_seam_requirement={"ok": True},
        gpt_calls_used=0,
    )
    assert meta == {
        "path_kind": "resolved_turn_ctir_bundle",
        "ctir_backed": True,
        "bundle_required": True,
        "plan_driven": True,
        "emergency_nonplan_output": False,
        "same_turn_retry_messages_reused": False,
        "extra": None,
    }


def test_block_ak_route_meta_snapshot_gpt_budget_matches_contract() -> None:
    observe = {"kind": "observe", "prompt": "I watch."}
    meta = api_mod._build_narration_hub_route_meta(
        resolution=observe,
        planner_convergence_emergency_exit=False,
        gpt_budget_exceeded=True,
        fast_fallback_mode=False,
        used_force_terminal_fallback=False,
        bundle_seam_requirement={"ok": True},
        gpt_calls_used=2,
    )
    assert meta == {
        "path_kind": "manual_play_gpt_budget_exceeded",
        "ctir_backed": False,
        "bundle_required": False,
        "plan_driven": False,
        "emergency_nonplan_output": True,
        "same_turn_retry_messages_reused": True,
    }


# --- Block AL: API narration hub orchestration handoff (GPT → retry → policy → finalize emission gate) ---


def _spy_handoff_stack(*, monkeypatch: pytest.MonkeyPatch, events: list[str]) -> None:
    """Wrap response policy + final emission gate so hub ordering can be snapshotted."""

    def spy_policy(*args: Any, **kwargs: Any) -> dict[str, Any]:
        events.append("response_policy_enforcement")
        return real_apply_response_policy_enforcement(*args, **kwargs)

    def spy_gate(*args: Any, **kwargs: Any) -> dict[str, Any]:
        events.append("final_emission_gate")
        return real_apply_final_emission_gate(*args, **kwargs)

    monkeypatch.setattr(api_mod, "apply_response_policy_enforcement", spy_policy)
    monkeypatch.setattr(api_turn_support_module, "apply_final_emission_gate", spy_gate)


def _finalize_kw_slice(kw: dict[str, Any]) -> dict[str, Any]:
    return {
        "resolution": kw["resolution"],
        "session": kw["session"],
        "world": kw["world"],
        "scene": kw["scene"],
    }


def test_block_al_handoff_normal_gpt_then_policy_then_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []

    def spy_gpt(_messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
        events.append("call_gpt")
        return _gm("Rain beads on the gate chain.", metadata={"existing_marker": "normal"})

    monkeypatch.setattr(api_mod, "call_gpt", spy_gpt)
    monkeypatch.setattr(api_mod, "detect_retry_failures", lambda **_k: [])
    _spy_handoff_stack(monkeypatch=monkeypatch, events=events)

    kw = _base_kw()
    built = _build_gpt_narration_from_authoritative_state(**kw)
    route_hub = _route_source(built)
    seam_hub = (
        (built.get("metadata") or {}).get("narration_seam")
        if isinstance(built.get("metadata"), dict)
        else None
    )
    pk_hub = seam_hub.get("path_kind") if isinstance(seam_hub, dict) else None

    gm_out, _narr = _finalize_player_facing_for_turn(built, **_finalize_kw_slice(kw))

    assert events.index("call_gpt") < events.index("response_policy_enforcement")
    assert events.index("response_policy_enforcement") < events.index("final_emission_gate")
    assert events.count("call_gpt") == 1
    assert route_hub == "resolved_turn_ctir_bundle"
    md = gm_out.get("metadata") if isinstance(gm_out.get("metadata"), dict) else {}
    seam_fin = md.get("narration_seam") if isinstance(md.get("narration_seam"), dict) else {}
    if pk_hub:
        assert seam_fin.get("path_kind") == pk_hub
    fem = read_final_emission_meta_dict(gm_out) or {}
    assert fem.get("final_emitted_source") or md.get("final_emitted_source") or route_hub


def test_block_al_handoff_gpt_budget_exceeded_skips_provider_call_order(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []

    def forbidden_gpt(*_a: Any, **_k: Any) -> dict[str, Any]:
        raise AssertionError("manual_play_gpt_budget_exceeded must not invoke call_gpt")

    monkeypatch.setattr(api_mod, "MANUAL_PLAY_MAX_CALL_GPT", 0)
    monkeypatch.setattr(api_mod, "call_gpt", forbidden_gpt)
    monkeypatch.setattr(api_mod, "detect_retry_failures", lambda **_k: [])
    _spy_handoff_stack(monkeypatch=monkeypatch, events=events)

    kw = _base_kw()
    built = _build_gpt_narration_from_authoritative_state(**kw)
    route_hub = _route_source(built)
    assert route_hub == "manual_play_gpt_budget_exceeded"
    # Synthetic budget GM carries upstream_api_error → fast fallback repairs before policy;
    # hub skips apply_response_policy_enforcement when fast_fallback_mode is set (api.py).
    assert "response_policy_enforcement" not in events

    gm_out, _narr = _finalize_player_facing_for_turn(built, **_finalize_kw_slice(kw))

    assert "call_gpt" not in events
    assert events == ["final_emission_gate"]
    families = _assert_all_emitted_families_known(built)
    assert GPT_BUDGET_OR_PROVIDER_FAILURE in families
    fem = read_final_emission_meta_dict(gm_out) or {}
    assert fem.get("final_emitted_source") or route_hub


def test_block_al_handoff_targeted_retry_second_gpt_before_policy_then_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []

    def spy_gpt(messages: list[dict[str, str]], **kwargs: Any) -> dict[str, Any]:
        events.append("call_gpt")
        if len(messages) <= 2:
            return _gm("TRIGGER_VALIDATOR_VOICE", metadata={"existing_marker": "initial"})
        return _gm("The gate chain settles after the retry.", metadata={"existing_marker": "retry"})

    def fake_failures(*, gm_reply: dict[str, Any], **_kwargs: Any) -> list[dict[str, Any]]:
        if "TRIGGER_VALIDATOR_VOICE" in str(gm_reply.get("player_facing_text") or ""):
            return [{"failure_class": "validator_voice", "priority": 20, "reasons": ["snapshot_trigger"]}]
        return []

    monkeypatch.setattr(api_mod, "call_gpt", spy_gpt)
    monkeypatch.setattr(api_mod, "detect_retry_failures", fake_failures)
    monkeypatch.setattr(api_mod, "choose_retry_strategy", lambda failures: failures[0] if failures else None)
    monkeypatch.setattr(api_mod, "build_retry_prompt_for_failure", lambda *_a, **_k: "retry please")
    _spy_handoff_stack(monkeypatch=monkeypatch, events=events)

    kw = _base_kw()
    built = _build_gpt_narration_from_authoritative_state(**kw)
    assert built["player_facing_text"] == "The gate chain settles after the retry."
    route_hub = _route_source(built)
    assert route_hub == "resolved_turn_ctir_bundle"

    gm_out, _narr = _finalize_player_facing_for_turn(built, **_finalize_kw_slice(kw))

    assert events.count("call_gpt") == 2
    assert events.index("call_gpt") < events.index("response_policy_enforcement")
    last_gpt = max(i for i, e in enumerate(events) if e == "call_gpt")
    assert last_gpt < events.index("response_policy_enforcement")
    assert events.index("response_policy_enforcement") < events.index("final_emission_gate")
    md = gm_out.get("metadata") if isinstance(gm_out.get("metadata"), dict) else {}
    assert md["existing_marker"] == "retry"
    fem = read_final_emission_meta_dict(gm_out) or {}
    assert fem.get("final_emitted_source") or route_hub


def test_block_al_handoff_terminal_retry_force_fallback_before_policy_then_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []

    def spy_gpt(*_a: Any, **_k: Any) -> dict[str, Any]:
        events.append("call_gpt")
        return _gm("TRIGGER_TERMINAL_RETRY", metadata={"existing_marker": "terminal"})

    real_force = api_mod.force_terminal_retry_fallback

    def spy_force(**kwargs: Any) -> dict[str, Any]:
        events.append("force_terminal_retry_fallback")
        return real_force(**kwargs)

    monkeypatch.setattr(api_mod, "MAX_TARGETED_RETRY_ATTEMPTS", 0)
    monkeypatch.setattr(api_mod, "call_gpt", spy_gpt)
    monkeypatch.setattr(
        api_mod,
        "detect_retry_failures",
        lambda **_k: [{"failure_class": "validator_voice", "priority": 20, "reasons": ["snapshot_terminal"]}],
    )
    monkeypatch.setattr(api_mod, "choose_retry_strategy", lambda failures: failures[0] if failures else None)
    monkeypatch.setattr(api_mod, "force_terminal_retry_fallback", spy_force)
    _spy_handoff_stack(monkeypatch=monkeypatch, events=events)

    kw = _base_kw()
    built = _build_gpt_narration_from_authoritative_state(**kw)
    _assert_known_family(built, RETRY_TERMINAL_FALLBACK)
    route_hub = _route_source(built)

    gm_out, _narr = _finalize_player_facing_for_turn(built, **_finalize_kw_slice(kw))

    assert events.index("call_gpt") < events.index("force_terminal_retry_fallback")
    assert events.index("force_terminal_retry_fallback") < events.index("response_policy_enforcement")
    assert events.index("response_policy_enforcement") < events.index("final_emission_gate")
    md = gm_out.get("metadata") if isinstance(gm_out.get("metadata"), dict) else {}
    assert md["existing_marker"] == "terminal"
    fem = read_final_emission_meta_dict(gm_out) or {}
    assert fem.get("final_emitted_source") or route_hub


def test_block_al_handoff_planner_convergence_emergency_skips_gpt_and_retry_stack(monkeypatch: pytest.MonkeyPatch) -> None:
    events: list[str] = []

    monkeypatch.setattr(api_mod, "build_messages", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("no prompt")))
    monkeypatch.setattr(api_mod, "call_gpt", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("no gpt")))
    monkeypatch.setattr(
        api_mod,
        "build_narration_plan_bundle",
        lambda **_k: {"plan_metadata": {"ctir_stamp": ""}, "narrative_plan": None, "renderer_inputs": {}},
    )
    _spy_handoff_stack(monkeypatch=monkeypatch, events=events)

    kw = _base_kw()
    built = _build_gpt_narration_from_authoritative_state(**kw)

    assert built["player_facing_text"]
    assert _route_source(built)
    md = built["metadata"]
    assert md["narration_seam"]["path_kind"] == "resolved_turn_ctir_planner_convergence_seam"
    assert md["narration_seam"]["emergency_nonplan_output"] is True

    gm_out, _narr = _finalize_player_facing_for_turn(built, **_finalize_kw_slice(kw))

    assert "call_gpt" not in events
    assert events == ["response_policy_enforcement", "final_emission_gate"]
    assert events.index("response_policy_enforcement") < events.index("final_emission_gate")

    md_out = gm_out.get("metadata") if isinstance(gm_out.get("metadata"), dict) else {}
    assert md_out["narration_seam"]["path_kind"] == md["narration_seam"]["path_kind"]
    fem = read_final_emission_meta_dict(gm_out) or {}
    assert fem.get("final_emitted_source") or _route_source(built)


# --- Block AM: narration hub policy handoff adapter (no GPT / retry / final gate) ---


def test_block_am_policy_handoff_adapter_callable() -> None:
    assert callable(api_mod._apply_narration_hub_policy_handoff)


def test_block_am_policy_handoff_skips_enforcement_when_fast_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[str] = []

    def spy(*args: Any, **_k: Any) -> Any:
        seen.append("policy")
        return args[0] if args else {}

    monkeypatch.setattr(api_mod, "apply_response_policy_enforcement", spy)
    out = api_mod._apply_narration_hub_policy_handoff(
        {"player_facing_text": "x"},
        fast_fallback_mode=True,
        response_policy={},
        player_text="t",
        scene_envelope={},
        session={},
        world={},
        resolution={},
        discovered_clues=[],
        repair_terminal_player_facing_if_needed=lambda g, **kw: g,
    )
    assert seen == []
    assert out == {"player_facing_text": "x"}


def test_block_am_policy_handoff_runs_enforcement_when_not_fast_fallback(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[str] = []

    def spy(*args: Any, **_k: Any) -> Any:
        seen.append("policy")
        return args[0] if args else {}

    monkeypatch.setattr(api_mod, "apply_response_policy_enforcement", spy)
    out = api_mod._apply_narration_hub_policy_handoff(
        {"player_facing_text": "x"},
        fast_fallback_mode=False,
        response_policy={},
        player_text="t",
        scene_envelope={},
        session={},
        world={},
        resolution={},
        discovered_clues=[],
        repair_terminal_player_facing_if_needed=lambda g, **kw: g,
    )
    assert seen == ["policy"]
    assert out == {"player_facing_text": "x"}


def test_block_am_policy_handoff_invokes_repair_after_policy_with_expected_reason() -> None:
    reasons: list[str] = []

    def repair(g: dict[str, Any], **kw: Any) -> dict[str, Any]:
        reasons.append(str(kw.get("reason") or ""))
        return g

    out = api_mod._apply_narration_hub_policy_handoff(
        {"player_facing_text": "x"},
        fast_fallback_mode=False,
        response_policy={},
        player_text="t",
        scene_envelope={},
        session={},
        world={},
        resolution={},
        discovered_clues=[],
        repair_terminal_player_facing_if_needed=repair,
    )
    assert reasons == ["api_post_response_policy_enforcement"]
    assert out["player_facing_text"] == "x"


def test_block_am_policy_handoff_does_not_invoke_gpt_retry_or_final_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(api_mod, "call_gpt", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("call_gpt")))
    monkeypatch.setattr(
        api_mod, "detect_retry_failures", lambda **_k: (_ for _ in ()).throw(AssertionError("detect_retry"))
    )
    monkeypatch.setattr(
        api_mod,
        "force_terminal_retry_fallback",
        lambda **_k: (_ for _ in ()).throw(AssertionError("force_terminal")),
    )
    monkeypatch.setattr(
        api_turn_support_module,
        "apply_final_emission_gate",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("apply_final_emission_gate")),
    )
    monkeypatch.setattr(api_mod, "apply_response_policy_enforcement", lambda gm, **kw: gm)

    api_mod._apply_narration_hub_policy_handoff(
        {"player_facing_text": "ok"},
        fast_fallback_mode=False,
        response_policy={},
        player_text="t",
        scene_envelope={"scene": {}},
        session={},
        world={},
        resolution={},
        discovered_clues=[],
        repair_terminal_player_facing_if_needed=lambda g, **kw: g,
    )


def test_block_am_policy_handoff_tests_remain_registered() -> None:
    mod = sys.modules[__name__]
    for name in _BLOCK_AM_POLICY_HANDOFF_TEST_NAMES:
        assert callable(getattr(mod, name, None)), name


# --- Block AN: API narration hub extraction boundary / contract guard (stop point) ---


def test_block_an_policy_handoff_adapter_remains_callable() -> None:
    assert callable(api_mod._apply_narration_hub_policy_handoff)


def test_block_an_route_helpers_remain_metadata_only_surface(monkeypatch: pytest.MonkeyPatch) -> None:
    """Route helpers must stay classification / annotation-kwargs only (no GPT / emission)."""

    def _forbidden_gpt(*_a: Any, **_k: Any) -> Any:
        raise AssertionError("route metadata helpers must not call call_gpt")

    monkeypatch.setattr(api_mod, "call_gpt", _forbidden_gpt)
    api_mod._classify_narration_hub_route(
        resolution={"kind": "observe"},
        planner_convergence_emergency_exit=False,
        gpt_budget_exceeded=False,
        fast_fallback_mode=False,
        used_force_terminal_fallback=False,
    )
    api_mod._build_narration_hub_route_meta(
        resolution={"kind": "observe"},
        planner_convergence_emergency_exit=False,
        gpt_budget_exceeded=False,
        fast_fallback_mode=False,
        used_force_terminal_fallback=False,
        bundle_seam_requirement={"ok": True},
        gpt_calls_used=0,
    )
    api_mod._narration_hub_finalize_annotation_parts(
        resolution={"kind": "observe"},
        planner_convergence_emergency_exit=False,
        gpt_budget_exceeded=False,
        fast_fallback_mode=False,
        used_force_terminal_fallback=False,
        bundle_seam_requirement={"ok": True},
        gpt_calls_used=0,
    )


def test_block_an_policy_handoff_adapter_does_not_invoke_gpt_retry_or_final_emission(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(api_mod, "call_gpt", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("call_gpt")))
    monkeypatch.setattr(
        api_mod, "detect_retry_failures", lambda **_k: (_ for _ in ()).throw(AssertionError("detect_retry"))
    )
    monkeypatch.setattr(
        api_mod,
        "force_terminal_retry_fallback",
        lambda **_k: (_ for _ in ()).throw(AssertionError("force_terminal")),
    )
    monkeypatch.setattr(
        api_turn_support_module,
        "apply_final_emission_gate",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("apply_final_emission_gate")),
    )
    monkeypatch.setattr(api_mod, "apply_response_policy_enforcement", lambda gm, **kw: gm)

    api_mod._apply_narration_hub_policy_handoff(
        {"player_facing_text": "ok"},
        fast_fallback_mode=False,
        response_policy={},
        player_text="t",
        scene_envelope={"scene": {}},
        session={},
        world={},
        resolution={},
        discovered_clues=[],
        repair_terminal_player_facing_if_needed=lambda g, **kw: g,
    )


def test_block_an_orchestration_snapshot_tests_remain_registered() -> None:
    mod = sys.modules[__name__]
    for name in _BLOCK_AL_ORCHESTRATION_HANDOFF_TEST_NAMES:
        assert callable(getattr(mod, name, None)), name


def test_block_an_adapter_contract_tests_remain_registered() -> None:
    mod = sys.modules[__name__]
    for name in _BLOCK_AM_POLICY_HANDOFF_TEST_NAMES:
        assert callable(getattr(mod, name, None)), name


def test_block_an_api_narration_hub_contract_guard_registry_nonempty() -> None:
    assert _BLOCK_AL_ORCHESTRATION_HANDOFF_TEST_NAMES
    assert _BLOCK_AM_POLICY_HANDOFF_TEST_NAMES


def test_block_an_contract_guard_tests_remain_registered() -> None:
    mod = sys.modules[__name__]
    for name in (
        "test_block_an_policy_handoff_adapter_remains_callable",
        "test_block_an_route_helpers_remain_metadata_only_surface",
        "test_block_an_policy_handoff_adapter_does_not_invoke_gpt_retry_or_final_emission",
        "test_block_an_orchestration_snapshot_tests_remain_registered",
        "test_block_an_adapter_contract_tests_remain_registered",
        "test_block_an_api_narration_hub_contract_guard_registry_nonempty",
    ):
        assert callable(getattr(mod, name, None)), name


def test_block_ak_api_path_selection_snapshot_tests_remain_registered() -> None:
    mod = sys.modules[__name__]
    for name in (
        "test_api_narration_normal_gpt_path_snapshot",
        "test_api_narration_planner_convergence_emergency_path_snapshot",
        "test_api_narration_gpt_budget_failure_path_snapshot",
        "test_api_narration_targeted_retry_path_snapshot",
        "test_api_narration_terminal_retry_fallback_path_snapshot",
        "test_block_aj_classify_narration_hub_route_finalize_labels",
    ):
        assert callable(getattr(mod, name, None)), name


def test_block_al_handoff_snapshot_tests_remain_registered() -> None:
    mod = sys.modules[__name__]
    for name in _BLOCK_AL_ORCHESTRATION_HANDOFF_TEST_NAMES:
        assert callable(getattr(mod, name, None)), name
