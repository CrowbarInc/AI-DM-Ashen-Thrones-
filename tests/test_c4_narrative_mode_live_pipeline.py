"""Objective C4 — live planner→prompt→gate→FEM regressions (compact fixtures, telemetry-first).

End-to-end here means: ``apply_final_emission_gate`` with ``gm_output.prompt_context.narrative_plan``
carrying the **planner-shipped** ``narrative_mode_contract`` (same seam the gate reads), plus optional
``build_narration_context`` coverage for prompt seam markers when the session bundle is mutated.

No new architecture: assertions lock down NMO execution, FEM, routing, and inspectable skip/fallback
behavior already implemented in Blocks A–C.
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
from tests.test_narrative_mode_output_validator import (
    _minimal_ctir_action_outcome,
    _minimal_ctir_continuation,
    _resolution_pending_check,
)

pytestmark = pytest.mark.unit


def _gm_with_shipped_plan(
    *,
    text: str,
    contract: dict | None,
    narrative_mode_field: str | None = None,
    extra_plan_keys: dict | None = None,
    include_plan_narrative_mode_alias: bool = False,
) -> dict:
    """Build gm_output ``prompt_context.narrative_plan`` the way production does for the gate seam.

    By default **omit** ``narrative_plan.narrative_mode`` (matches ``_narrative_mode_plan_payload`` in
    ``test_final_emission_gate``). Opt-in alias when testing planner/prompt alignment.
    """
    plan: dict = {"version": 1}
    if contract is not None:
        plan["narrative_mode_contract"] = contract
        if include_plan_narrative_mode_alias or narrative_mode_field:
            plan["narrative_mode"] = narrative_mode_field or str(contract.get("mode") or "")
    elif narrative_mode_field:
        plan["narrative_mode"] = narrative_mode_field
    if extra_plan_keys:
        plan.update(extra_plan_keys)
    return {"player_facing_text": text, "tags": [], "prompt_context": {"narrative_plan": plan}}


def _fem(out: dict) -> dict:
    return read_final_emission_meta_dict(out) or {}


def _legality_nmo_codes(out: dict, fem: dict) -> list[str]:
    sample = [str(x) for x in (fem.get("rejection_reasons_sample") or []) if str(x).strip()]
    return [x for x in sample if x.startswith("nmo:")]


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


# --- 1) Named failure modes (shipped contract + violating prose) ---


@pytest.mark.parametrize(
    "mode_label,contract_kwargs,bad_text,expected_subcodes",
    [
        (
            "continuation_vs_opening_reset",
            {"ctir": _minimal_ctir_continuation()},
            "You wake to a new day. The market unfolds around you as if nothing before it mattered.",
            ("nmo:continuation:fresh_opening_reset_shape",),
        ),
        (
            "action_outcome_buried",
            {"ctir": _minimal_ctir_action_outcome()},
            (
                "The mist holds the alley in a grey hush. "
                "A rusted chain sags from the staple while drafts slide along the stones without settling."
            ),
            ("nmo:action_outcome:result_not_frontloaded",),
        ),
        (
            "dialogue_scenic_recap",
            {
                "response_policy": {"response_type_contract": {"required_response_type": "dialogue"}},
            },
            (
                "The checkpoint rumor describes supply movements, watch rotations, curfew lanes, patrol timings, "
                "merchant grudges, barracks gossip, seal stamps, toll ledgers, river tariffs, forge quotas, "
                "guild pledges, warehouse seals, night-watch swaps, lantern laws, bridge levies, wharf fees, "
                "smithy quotas, pier tariffs, wagon levies, granary seals, dock manifests, yard postings, "
                "clerk rotations, watchhouse maps, lantern routes, postern keys, seal wax orders, barracks chalkboards, "
                "and which officers avoid the yard; nothing in it names a single responsible sergeant for the east "
                "gate roster tonight or which lane stays open after curfew when the river patrol shifts."
            ),
            ("nmo:dialogue:scenic_recap_dominates",),
        ),
        (
            "dialogue_weak_reply",
            {
                "response_policy": {"response_type_contract": {"required_response_type": "dialogue"}},
            },
            (
                "The sergeant studies your face, then the lane, then the distant gate without committing "
                "to a direction or naming anyone who holds the watch roster."
            ),
            ("nmo:dialogue:missing_reply_continuity",),
        ),
        (
            "exposition_answer_buried",
            {"response_policy": {"answer_completeness": {"answer_required": True}}},
            (
                "For a breath the scene holds while voices shift around you. "
                "The east gate lies two hundred feet south along the market road."
            ),
            ("nmo:exposition_answer:answer_buried",),
        ),
        (
            "transition_static_hold",
            {"narration_obligations": {"must_advance_scene": True}},
            "He meets your eyes and says nothing while the same crowd murmurs at your back.",
            ("nmo:transition:no_scene_change_motion",),
        ),
    ],
)
def test_c4_e2e_nmo_failure_named_modes(
    mode_label: str,
    contract_kwargs: dict,
    bad_text: str,
    expected_subcodes: tuple[str, ...],
) -> None:
    nmc = build_narrative_mode_contract(**contract_kwargs)
    res = (
        (contract_kwargs.get("ctir") or {}).get("resolution")
        if isinstance(contract_kwargs.get("ctir"), dict)
        else {"kind": "observe", "prompt": "wait"}
    )
    gm = _gm_with_shipped_plan(text=bad_text, contract=nmc)
    out = apply_final_emission_gate(
        gm,
        resolution=res if isinstance(res, dict) else {"kind": "observe"},
        session={},
        scene_id="lane_scene",
        world={},
    )
    fem = _fem(out)
    assert fem.get("narrative_mode_output_checked") is True, mode_label
    assert fem.get("narrative_mode_output_passed") is False, mode_label
    merged = list(fem.get("narrative_mode_output_failure_reasons") or []) + _legality_nmo_codes(out, fem)
    for code in expected_subcodes:
        assert any(code in str(x) for x in merged), (mode_label, code, merged)
    assert fem.get("final_route") == "replaced", mode_label
    assert fem.get("narrative_mode_output_skip_reason") is None


def test_c4_e2e_continuation_scenic_regrounding_failure() -> None:
    nmc = build_narrative_mode_contract(ctir=_minimal_ctir_continuation())
    bad = (
        "The square holds silence while mist gathers at the eastern gate and torchlight presses the cobbles."
    )
    out = apply_final_emission_gate(
        _gm_with_shipped_plan(text=bad, contract=nmc),
        resolution={"kind": "observe", "prompt": "I wait."},
        session={},
        scene_id="s",
        world={},
    )
    fem = _fem(out)
    assert "nmo:continuation:scenic_regrounding_without_transition" in (
        fem.get("narrative_mode_output_failure_reasons") or []
    )
    assert fem.get("final_route") == "replaced"


def test_c4_e2e_action_outcome_delayed_unresolved_mixed() -> None:
    nmc = build_narrative_mode_contract(ctir=_minimal_ctir_action_outcome())
    text = "You succeed immediately, yet the outcome remains unresolved until the roll settles."
    out = apply_final_emission_gate(
        _gm_with_shipped_plan(text=text, contract=nmc),
        resolution=_resolution_pending_check(),
        session={},
        scene_id="s",
        world={},
    )
    fem = _fem(out)
    assert "nmo:action_outcome:unresolved_check_treated_as_result" in (
        fem.get("narrative_mode_output_failure_reasons") or []
    )


# --- 2) Happy-path canonical modes (clean FEM, no skip, accept) ---


@pytest.mark.parametrize(
    "label,contract_kwargs,good_text,resolution",
    [
        (
            "opening",
            {"narration_obligations": {"is_opening_scene": True}},
            "The square gathers torchlight against the mist. You stand at the eastern curb with the crowd.",
            {"kind": "observe", "prompt": "look"},
        ),
        (
            "continuation",
            {"ctir": _minimal_ctir_continuation()},
            (
                "You keep your weight forward; the east lane stays open ahead of you "
                "while torchlight holds the stones."
            ),
            {"kind": "observe", "prompt": "I wait."},
        ),
        (
            "action_outcome",
            {"ctir": _minimal_ctir_action_outcome()},
            "You find nothing new in the crate. The alley stays quiet except for distant footsteps.",
            {"kind": "observe"},
        ),
        (
            "transition",
            {"narration_obligations": {"must_advance_scene": True}},
            "You step through the east gate into the yard where torchlight pools along the wall.",
            {"kind": "travel", "label": "enter"},
        ),
        (
            "exposition_answer",
            {"response_policy": {"answer_completeness": {"answer_required": True}}},
            "The east gate lies two hundred feet south along the market road past the checkpoint.",
            {"kind": "observe"},
        ),
    ],
)
def test_c4_e2e_happy_canonical_modes(
    label: str,
    contract_kwargs: dict,
    good_text: str,
    resolution: dict,
) -> None:
    nmc = build_narrative_mode_contract(**contract_kwargs)
    assert nmc.get("mode") == label
    out = apply_final_emission_gate(
        _gm_with_shipped_plan(text=good_text, contract=nmc),
        resolution=resolution,
        session={},
        scene_id="lane_scene",
        world={},
    )
    fem = _fem(out)
    assert fem.get("narrative_mode_output_checked") is True, label
    assert fem.get("narrative_mode_output_passed") is True, label
    assert fem.get("narrative_mode_output_skip_reason") is None, label
    assert fem.get("final_route") == "accept_candidate", label
    assert fem.get("narrative_mode_output_mode") == label
    assert fem.get("narrative_mode_contract_mode") == label
    assert "final_emission_gate_replaced" not in (out.get("tags") or [])


def test_c4_e2e_happy_dialogue_grounded_passes_gate_layers() -> None:
    """Dialogue contract + explicit NPC naming so referential clarity and NMO both accept."""
    nmc = build_narrative_mode_contract(
        response_policy={
            "response_type_contract": {"required_response_type": "dialogue"},
            "social_response_structure": {"enabled": True},
        },
        narration_obligations={"active_npc_reply_expected": True},
    )
    assert nmc.get("mode") == "dialogue"
    text = (
        'Gatekeeper Mira shrugs once. "East gate lies two hundred feet south—watch keeps that lane."'
    )
    out = apply_final_emission_gate(
        _gm_with_shipped_plan(text=text, contract=nmc),
        resolution={"kind": "observe", "prompt": "Which way?"},
        session={},
        scene_id="lane_scene",
        world={},
    )
    fem = _fem(out)
    assert fem.get("narrative_mode_output_checked") is True
    assert fem.get("narrative_mode_output_passed") is True
    assert fem.get("narrative_mode_output_skip_reason") is None
    assert fem.get("final_route") == "accept_candidate"
    assert fem.get("narrative_mode_output_mode") == "dialogue"


# --- 3) Skip-path telemetry + prompt seam (bundle mutation) ---


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


def test_c4_skip_absent_contract_plan_present_prompt_seam_and_gate() -> None:
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
    assert "nmc_missing_contract" in " ".join(nm_dbg.get("seam_codes") or [])
    instr = "\n".join(ctx.get("instructions") or [])
    assert "struct:nmc_seam:narrative_mode_contract_missing" in instr
    assert "struct:nmc_floor:use_continuation_lane_pending_gate_skip_on_c4" in instr

    out = apply_final_emission_gate(
        _gm_with_shipped_plan(text="The lane holds.", contract=None, narrative_mode_field="continuation"),
        resolution={"kind": "observe"},
        session={},
        scene_id="s1",
        world={},
    )
    fem = _fem(out)
    assert fem.get("narrative_mode_output_checked") is False
    assert fem.get("narrative_mode_output_skip_reason") == "narrative_mode_contract_absent"
    assert fem.get("narrative_mode_output_passed") is True


def test_c4_skip_invalid_contract_shape_prompt_seam_and_gate() -> None:
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
    instr = "\n".join(ctx.get("instructions") or [])
    assert "struct:nmc_seam:narrative_mode_contract_invalid" in instr

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


def test_c4_skip_disabled_contract_prompt_marker_and_gate() -> None:
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
    instr = "\n".join(ctx.get("instructions") or [])
    assert "struct:nmc_contract:disabled|c4_gate_skips_nmo|shipped_continuation_lane" in instr

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


# --- 4) Strict-social terminal fallback (deterministic, no second builder) ---


def test_c4_strict_social_nmo_terminal_fallback_metadata_and_reassessment(monkeypatch) -> None:
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


# --- 5) Pre-replace NMO telemetry preserved on generic replace path ---


def test_c4_pre_replace_nmo_failure_visible_after_non_strict_replace() -> None:
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
    assert fem.get("narrative_mode_output_passed") is False
    assert "nmo:continuation:fresh_opening_reset_shape" in (fem.get("narrative_mode_output_failure_reasons") or [])
    assert (out.get("player_facing_text") or "") != bad


# --- 6) Ownership boundaries ---


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


def test_c4_prompt_debug_reflects_shipped_contract_mode_alias_match() -> None:
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
    plan = ctx.get("narrative_plan") or {}
    nmc = plan.get("narrative_mode_contract") or {}
    anchor = (ctx.get("prompt_debug") or {}).get("narrative_plan") or {}
    assert anchor.get("narrative_mode_contract_valid") is True
    assert anchor.get("narrative_plan_mode_alias_matches_contract_mode") is True
    assert str(anchor.get("narrative_mode") or "").strip() == str(nmc.get("mode") or "").strip()


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


# --- 7) Long-session consistency smoke ---


@pytest.mark.parametrize("turn", range(1, 6))
def test_c4_continuation_stable_across_repeated_gate_passes(turn: int) -> None:
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
    assert fem.get("narrative_mode_output_skip_reason") is None
    assert fem.get("final_route") == "accept_candidate"
    tags = [str(t) for t in (out.get("tags") or []) if isinstance(t, str)]
    assert not any("narrative_mode_output_skip" in t for t in tags)
    assert "final_emission_gate:narrative_mode_output" not in tags


# --- 8) Negative policy (no second planner / no silent generic escape in prompt seam) ---


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


def test_c4_malformed_plan_contract_surfaces_floor_not_empty_instructions() -> None:
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
    blob = "\n".join(ctx.get("instructions") or [])
    assert "generic narration" not in blob.lower()
