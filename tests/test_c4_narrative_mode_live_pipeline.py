"""Objective C4 — live planner→prompt→gate smoke (compact fixtures, telemetry-first).

End-to-end here means: ``apply_final_emission_gate`` with ``gm_output.prompt_context.narrative_plan``
carrying the **planner-shipped** ``narrative_mode_contract`` (same seam the gate reads), plus optional
``build_narration_context`` coverage when the session bundle is mutated.

**Smoke only; detailed NMO legality** (failure subcodes, per-mode matrices) is owned by
``tests/test_narrative_mode_output_validator.py`` and ``tests/test_final_emission_gate.py``.
**Prompt struct / NMC seam strings** are owned by ``tests/test_prompt_context.py`` and
``tests/test_prompt_context_narrative_modes.py`` — this module only checks that the wire-up produces
markers and non-empty instructions, not every shipped instruction token.

No new architecture: these tests prove the C4 pipeline runs without crashes and surfaces coarse
FEM / prompt-debug markers; they do not re-own gate validator internals.
"""

from __future__ import annotations

import copy
import json
from unittest.mock import MagicMock

import pytest

import game.narrative_planning as narrative_planning
from game import ctir
from game.ctir_runtime import SESSION_CTIR_STAMP_KEY, attach_ctir, detach_ctir
from game.defaults import default_session, default_world
from game.final_emission_gate import apply_final_emission_gate
import game.final_emission_gate as feg_module
from game.final_emission_meta import read_final_emission_meta_dict
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.narration_plan_bundle import attach_narration_plan_bundle, get_attached_narration_plan_bundle
from game.narrative_mode_contract import build_narrative_mode_contract
from game.prompt_context import build_narration_context
from tests.helpers.ctir_narration_bundle import ensure_narration_plan_bundle_for_manual_ctir_tests
from tests.test_narrative_mode_output_validator import _minimal_ctir_continuation

pytestmark = pytest.mark.unit


def _gm_with_shipped_plan(
    *,
    text: str,
    contract: dict | None,
    narrative_mode_field: str | None = None,
    extra_plan_keys: dict | None = None,
    include_plan_narrative_mode_alias: bool = False,
) -> dict:
    """Build gm_output ``prompt_context.narrative_plan`` the way production does for the gate seam."""
    plan: dict = {"version": 1}
    if contract is not None:
        plan["narrative_mode_contract"] = contract
        if include_plan_narrative_mode_alias or narrative_mode_field:
            plan["narrative_mode"] = narrative_mode_field or str(contract.get("mode") or "")
    elif narrative_mode_field:
        plan["narrative_mode"] = narrative_mode_field
    if extra_plan_keys:
        plan.update(extra_plan_keys)
    if not isinstance(plan.get("acceptance_quality_contract"), dict):
        plan["acceptance_quality_contract"] = {"enabled": False}
    return {"player_facing_text": text, "tags": [], "prompt_context": {"narrative_plan": plan}}


def _fem(out: dict) -> dict:
    return read_final_emission_meta_dict(out) or {}


def _strict_runner_session_world_scene():
    session = default_session()
    world = default_world()
    sid = "scene_investigate"
    world["npcs"] = [
        {
            "id": "runner",
            "name": "Tavern Runner",
            "location": "scene_investigate",
            "topics": [{"id": "lanes", "text": "East lanes.", "clue_id": "east_lanes"}],
        }
    ]
    session["active_scene_id"] = sid
    session["visited_scene_ids"] = [sid]
    set_social_target(session, "runner")
    rebuild_active_scene_entities(session, world, sid)
    ic = dict(session.get("interaction_context") or {})
    ic["engagement_level"] = "engaged"
    session["interaction_context"] = ic
    resolution = {
        "kind": "question",
        "prompt": "Who attacked them?",
        "social": {
            "social_intent_class": "social_exchange",
            "npc_id": "runner",
            "npc_name": "Tavern Runner",
        },
    }
    return session, world, sid, resolution


def _minimal_narration_kwargs(session: dict, **overrides: object) -> dict:
    base = {
        "campaign": {"title": "", "premise": "", "character_role": "", "gm_guidance": [], "world_pressures": []},
        "world": {},
        "session": session,
        "character": {"name": "Hero", "hp": {}, "ac": {}},
        "scene": {"scene": {"id": "s1", "visible_facts": [], "exits": [], "enemies": []}},
        "combat": {"in_combat": False},
        "recent_log": [],
        "user_text": "Continue.",
        "resolution": {"kind": "observe", "label": "look"},
        "scene_runtime": {},
        "public_scene": {"id": "s1", "visible_facts": [], "exits": [], "enemies": []},
        "discoverable_clues": [],
        "gm_only_hidden_facts": [],
        "gm_only_discoverable_locked": [],
        "discovered_clue_records": [],
        "undiscovered_clue_records": [],
        "pending_leads": [],
        "intent": {"labels": ["general"]},
        "world_state_view": {"flags": {}, "counters": {}, "clocks_summary": []},
        "mode_instruction": "Standard.",
        "recent_log_for_prompt": [],
    }
    base.update(overrides)
    return base


def _attach_ctir_session(session: dict, c: dict) -> None:
    attach_ctir(session, c)
    if not str(session.get(SESSION_CTIR_STAMP_KEY) or "").strip():
        session[SESSION_CTIR_STAMP_KEY] = "non_production_test_ctir_bundle_stamp_v1"


def test_c4_smoke_shipped_continuation_contract_accept_candidate() -> None:
    """Smoke: gate accepts a clean continuation line when contract ships on the plan."""
    nmc = build_narrative_mode_contract(ctir=_minimal_ctir_continuation())
    text = (
        "You keep your weight forward; the east lane stays open ahead of you "
        "while torchlight holds the stones."
    )
    out = apply_final_emission_gate(
        _gm_with_shipped_plan(text=text, contract=nmc),
        resolution={"kind": "observe", "prompt": "I wait."},
        session={},
        scene_id="lane_scene",
        world={},
    )
    fem = _fem(out)
    assert fem.get("narrative_mode_output_checked") is True
    assert fem.get("narrative_mode_output_passed") is True
    assert fem.get("final_route") == "accept_candidate"
    assert str(out.get("player_facing_text") or "").strip()


def test_c4_smoke_bad_continuation_candidate_replaced_without_crash() -> None:
    """Smoke: obvious continuation violation is replaced; exact subcodes owned by gate/validator suites."""
    nmc = build_narrative_mode_contract(ctir=_minimal_ctir_continuation())
    bad = "You wake to a new day. The market unfolds around you as if nothing before it mattered."
    out = apply_final_emission_gate(
        _gm_with_shipped_plan(text=bad, contract=nmc),
        resolution={"kind": "observe", "prompt": "wait"},
        session={},
        scene_id="s",
        world={},
    )
    fem = _fem(out)
    assert fem.get("narrative_mode_output_checked") is True
    assert fem.get("narrative_mode_output_passed") is False
    assert fem.get("final_route") == "replaced"
    assert (out.get("player_facing_text") or "") != bad


def test_c4_smoke_bundle_prompt_gate_absent_contract_cross_cut() -> None:
    """Smoke: plan bundle without NMC still yields prompt seam signal + gate skip (exact strings: prompt_context tests)."""
    session = dict(_minimal_narration_kwargs({"active_scene_id": "s1", "turn_counter": 5, "visited_scene_ids": ["s1"]})["session"])
    c = ctir.build_ctir(
        turn_id=5,
        scene_id="s1",
        player_input="I nod.",
        builder_source="tests.c4.skip_absent",
        resolution={"kind": "observe", "label": "nod"},
        intent={"labels": ["general"]},
        interaction={"interaction_mode": "none"},
        world={},
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    _attach_ctir_session(session, c)
    try:
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, _minimal_narration_kwargs(session))
        bundle = dict(get_attached_narration_plan_bundle(session) or {})
        plan = dict(bundle.get("narrative_plan") or {})
        plan.pop("narrative_mode_contract", None)
        plan["narrative_mode"] = "continuation"
        bundle["narrative_plan"] = plan
        attach_narration_plan_bundle(session, bundle)
        ctx = build_narration_context(
            **_minimal_narration_kwargs(session, user_text="I nod.", include_non_public_prompt_keys=True),
        )
    finally:
        detach_ctir(session)
    nm_dbg = (ctx.get("prompt_debug") or {}).get("narrative_mode_instructions") or {}
    seam_blob = " ".join(nm_dbg.get("seam_codes") or [])
    assert "nmc_missing_contract" in seam_blob
    assert ctx.get("instructions")

    out = apply_final_emission_gate(
        _gm_with_shipped_plan(text="The lane holds.", contract=None, narrative_mode_field="continuation"),
        resolution={"kind": "observe"},
        session={},
        scene_id="s1",
        world={},
    )
    fem = _fem(out)
    assert fem.get("narrative_mode_output_skip_reason") == "narrative_mode_contract_absent"
    assert fem.get("narrative_mode_output_checked") is False


def test_c4_smoke_bundle_prompt_gate_invalid_contract_cross_cut() -> None:
    """Smoke: invalid NMC shape surfaces a seam code + gate invalid skip prefix."""
    invalid = {
        "version": 1,
        "enabled": True,
        "mode": "continuation",
        "mode_family": "continuation",
        "source_signals": [],
        "prompt_obligations": {},
        "forbidden_moves": [],
        "debug": {"derivation_codes": []},
    }
    session = dict(_minimal_narration_kwargs({"active_scene_id": "s1", "turn_counter": 5, "visited_scene_ids": ["s1"]})["session"])
    c = ctir.build_ctir(
        turn_id=5,
        scene_id="s1",
        player_input="ping",
        builder_source="tests.c4.skip_invalid",
        resolution={"kind": "observe"},
        intent={"labels": ["general"]},
        interaction={"interaction_mode": "none"},
        world={},
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    _attach_ctir_session(session, c)
    try:
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, _minimal_narration_kwargs(session))
        bundle = dict(get_attached_narration_plan_bundle(session) or {})
        plan = dict(bundle.get("narrative_plan") or {})
        plan["narrative_mode_contract"] = invalid
        plan["narrative_mode"] = "continuation"
        bundle["narrative_plan"] = plan
        attach_narration_plan_bundle(session, bundle)
        ctx = build_narration_context(
            **_minimal_narration_kwargs(session, user_text="ping", include_non_public_prompt_keys=True),
        )
    finally:
        detach_ctir(session)
    seam = " ".join((ctx.get("prompt_debug") or {}).get("narrative_mode_instructions", {}).get("seam_codes") or [])
    assert "nmc_contract_invalid" in seam

    out = apply_final_emission_gate(
        _gm_with_shipped_plan(text="The lane holds.", contract=invalid),
        resolution={"kind": "observe"},
        session={},
        scene_id="s1",
        world={},
    )
    fem = _fem(out)
    assert fem.get("narrative_mode_output_checked") is False
    assert str(fem.get("narrative_mode_output_skip_reason") or "").startswith("narrative_mode_contract_invalid:")


def test_c4_smoke_bundle_prompt_gate_disabled_contract_cross_cut() -> None:
    """Smoke: disabled NMC still flows through prompt + gate skip reason."""
    nmc = build_narrative_mode_contract(enabled=False, ctir=_minimal_ctir_continuation())
    session = dict(_minimal_narration_kwargs({"active_scene_id": "s1", "turn_counter": 5, "visited_scene_ids": ["s1"]})["session"])
    c = ctir.build_ctir(
        turn_id=5,
        scene_id="s1",
        player_input="ping",
        builder_source="tests.c4.skip_disabled",
        resolution={"kind": "observe"},
        intent={"labels": ["general"]},
        interaction={"interaction_mode": "none"},
        world={},
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    _attach_ctir_session(session, c)
    try:
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, _minimal_narration_kwargs(session))
        bundle = dict(get_attached_narration_plan_bundle(session) or {})
        plan = dict(bundle.get("narrative_plan") or {})
        plan["narrative_mode_contract"] = copy.deepcopy(nmc)
        plan["narrative_mode"] = "continuation"
        bundle["narrative_plan"] = plan
        attach_narration_plan_bundle(session, bundle)
        ctx = build_narration_context(
            **_minimal_narration_kwargs(session, user_text="ping", include_non_public_prompt_keys=True),
        )
    finally:
        detach_ctir(session)
    instr_blob = "\n".join(ctx.get("instructions") or [])
    assert "disabled" in instr_blob.lower()

    out = apply_final_emission_gate(
        _gm_with_shipped_plan(text="You wake to a new day.", contract=nmc),
        resolution={"kind": "observe"},
        session={},
        scene_id="s1",
        world={},
    )
    fem = _fem(out)
    assert fem.get("narrative_mode_output_skip_reason") == "narrative_mode_contract_disabled"
    assert fem.get("narrative_mode_output_checked") is False


def test_c4_strict_social_nmo_terminal_fallback_metadata_and_reassessment(monkeypatch) -> None:
    """Smoke: strict-social path invokes stub builder once; FEM shows emergency fallback source."""
    session, world, sid, resolution = _strict_runner_session_world_scene()
    nmc = build_narrative_mode_contract(ctir=_minimal_ctir_continuation())
    calls: list[int] = []

    def fake_build(candidate_text, *, resolution, tags, session, scene_id, world):
        calls.append(1)
        bad = "You wake to a new day. The market unfolds around you as if nothing before it mattered."
        return bad, {
            "used_internal_fallback": False,
            "final_emitted_source": "test_stub",
            "rejection_reasons": [],
            "deterministic_attempted": False,
            "deterministic_passed": False,
            "fallback_pool": "none",
            "fallback_kind": "none",
            "route_illegal_intercepted": False,
        }

    monkeypatch.setattr(feg_module, "build_final_strict_social_response", fake_build)
    out = apply_final_emission_gate(
        _gm_with_shipped_plan(text="stub", contract=nmc),
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    assert calls == [1]
    tags = [str(t) for t in (out.get("tags") or []) if isinstance(t, str)]
    assert "final_emission_gate:narrative_mode_output" in tags
    fem = _fem(out)
    assert fem.get("final_route") == "replaced"
    assert fem.get("final_emitted_source") == "minimal_social_emergency_fallback"
    assert fem.get("narrative_mode_output_checked") is True
    assert fem.get("narrative_mode_output_passed") is True
    assert fem.get("narrative_mode_output_failure_reasons") == []


def test_c4_gate_does_not_import_mode_contract_builder() -> None:
    assert getattr(feg_module, "build_narrative_mode_contract", None) is None


def test_c4_gate_does_not_invoke_planner_build_during_emit(monkeypatch) -> None:
    boom = MagicMock(side_effect=AssertionError("build_narrative_plan must not run inside the gate"))

    monkeypatch.setattr(narrative_planning, "build_narrative_plan", boom)
    nmc = build_narrative_mode_contract(ctir=_minimal_ctir_continuation())
    apply_final_emission_gate(
        _gm_with_shipped_plan(
            text=(
                "You keep your weight forward; the east lane stays open ahead of you "
                "while torchlight holds the stones."
            ),
            contract=nmc,
        ),
        resolution={"kind": "observe"},
        session={},
        scene_id="lane_scene",
        world={},
    )


def test_c4_prompt_debug_shipped_contract_valid_smoke() -> None:
    """Smoke: shipped valid NMC in bundle yields contract_valid in prompt_debug (alias details: test_prompt_context)."""
    session = dict(_minimal_narration_kwargs({"active_scene_id": "s1", "turn_counter": 5, "visited_scene_ids": ["s1"]})["session"])
    c = ctir.build_ctir(
        turn_id=5,
        scene_id="s1",
        player_input="I nod.",
        builder_source="tests.c4.alias",
        resolution={"kind": "observe"},
        intent={"labels": ["general"]},
        interaction={"interaction_mode": "none"},
        world={},
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    _attach_ctir_session(session, c)
    try:
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, _minimal_narration_kwargs(session))
        ctx = build_narration_context(
            **_minimal_narration_kwargs(session, user_text="I nod.", include_non_public_prompt_keys=True),
        )
    finally:
        detach_ctir(session)
    anchor = (ctx.get("prompt_debug") or {}).get("narrative_plan") or {}
    assert anchor.get("narrative_mode_contract_valid") is True


def test_c4_gate_payload_may_include_plan_narrative_mode_alias_when_enabled() -> None:
    nmc = build_narrative_mode_contract(ctir=_minimal_ctir_continuation())
    gm = _gm_with_shipped_plan(
        text=(
            "You keep your weight forward; the east lane stays open ahead of you "
            "while torchlight holds the stones."
        ),
        contract=nmc,
        include_plan_narrative_mode_alias=True,
    )
    assert gm["prompt_context"]["narrative_plan"].get("narrative_mode") == "continuation"


def test_c4_gate_does_not_mutate_shipped_plan_contract() -> None:
    nmc = build_narrative_mode_contract(ctir=_minimal_ctir_continuation())
    gm = _gm_with_shipped_plan(
        text=(
            "You keep your weight forward; the east lane stays open ahead of you "
            "while torchlight holds the stones."
        ),
        contract=nmc,
    )
    snap = json.dumps(gm["prompt_context"]["narrative_plan"], sort_keys=True)
    apply_final_emission_gate(
        gm,
        resolution={"kind": "observe"},
        session={},
        scene_id="s",
        world={},
    )
    assert json.dumps(gm["prompt_context"]["narrative_plan"], sort_keys=True) == snap


def test_c4_continuation_stable_single_gate_pass_smoke() -> None:
    """Smoke: one clean pass still accepts (multi-turn repetition owned by integration if needed)."""
    nmc = build_narrative_mode_contract(ctir=_minimal_ctir_continuation())
    text = (
        "You keep your weight forward; the east lane stays open ahead of you "
        "while torchlight holds the stones."
    )
    out = apply_final_emission_gate(
        _gm_with_shipped_plan(text=text, contract=nmc),
        resolution={"kind": "observe", "prompt": "I wait."},
        session={},
        scene_id="lane_scene",
        world={},
    )
    fem = _fem(out)
    assert fem.get("narrative_mode_output_mode") == "continuation"
    assert fem.get("narrative_mode_output_passed") is True
    assert fem.get("final_route") == "accept_candidate"
    tags = [str(t) for t in (out.get("tags") or []) if isinstance(t, str)]
    assert "final_emission_gate:narrative_mode_output" not in tags


def test_c4_no_second_planner_call_on_gate_emit(monkeypatch) -> None:
    called: list[str] = []
    _orig = narrative_planning.build_narrative_plan

    def traced(*args, **kwargs):
        called.append("build_narrative_plan")
        return _orig(*args, **kwargs)

    monkeypatch.setattr(narrative_planning, "build_narrative_plan", traced)
    nmc = build_narrative_mode_contract(ctir=_minimal_ctir_continuation())
    apply_final_emission_gate(
        _gm_with_shipped_plan(
            text=(
                "You keep your weight forward; the east lane stays open ahead of you "
                "while torchlight holds the stones."
            ),
            contract=nmc,
        ),
        resolution={"kind": "observe"},
        session={},
        scene_id="lane_scene",
        world={},
    )
    assert called == []


def test_c4_malformed_plan_contract_surfaces_narrative_mode_instruction_lines() -> None:
    """Smoke: invalid NMC in bundle yields some NMC-related instruction lines (not silent)."""
    invalid = {
        "version": 1,
        "enabled": True,
        "mode": "continuation",
        "mode_family": "continuation",
        "source_signals": [],
        "prompt_obligations": {},
        "forbidden_moves": [],
        "debug": {"derivation_codes": []},
    }
    session = dict(_minimal_narration_kwargs({"active_scene_id": "s1", "turn_counter": 5, "visited_scene_ids": ["s1"]})["session"])
    c = ctir.build_ctir(
        turn_id=5,
        scene_id="s1",
        player_input="ping",
        builder_source="tests.c4.floor",
        resolution={"kind": "observe"},
        intent={"labels": ["general"]},
        interaction={"interaction_mode": "none"},
        world={},
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
    )
    _attach_ctir_session(session, c)
    try:
        ensure_narration_plan_bundle_for_manual_ctir_tests(session, _minimal_narration_kwargs(session))
        bundle = dict(get_attached_narration_plan_bundle(session) or {})
        plan = dict(bundle.get("narrative_plan") or {})
        plan["narrative_mode_contract"] = invalid
        plan["narrative_mode"] = "continuation"
        bundle["narrative_plan"] = plan
        attach_narration_plan_bundle(session, bundle)
        ctx = build_narration_context(
            **_minimal_narration_kwargs(session, user_text="ping", include_non_public_prompt_keys=True),
        )
    finally:
        detach_ctir(session)
    nm_lines = [ln for ln in (ctx.get("instructions") or []) if "NARRATIVE MODE" in ln or ln.startswith("struct:nmc")]
    assert nm_lines, "expected explicit seam/floor instructions, not silent omission"
