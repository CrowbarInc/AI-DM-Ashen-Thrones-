"""Selector snapshot and final-emitted source-shape regression locks for final emission gate.

This file owns Block AG sealed-branch selector snapshots, sealed-branch order pins,
Block M4 accept/replace source precedence characterization, and plain-candidate
source projection locks. Coverage is mostly distinct-marker / ``inspect`` source-shape
regression rather than full behavioral orchestration.

Behavioral gate orchestration (layer order, continuity placement, diagnostics) remains in
``tests/test_final_emission_gate.py``. Historical BJ thin-boundary/delegator locks live in
``tests/test_final_emission_gate_delegator_regression.py``.
"""

from __future__ import annotations

import inspect
import sys
from typing import Any

import pytest

import game.final_emission_fem_assembly as fem_assembly
import game.final_emission_gate as feg
import game.final_emission_generic_exit as generic_exit
import game.final_emission_sealed_fallback as sealed_fallback
import game.final_emission_strict_social_stack as strict_social_stack
import game.final_emission_terminal_pipeline as terminal_pipeline
from game.defaults import default_scene, default_session, default_world
from game.final_emission_gate import apply_final_emission_gate
from game.final_emission_meta import (
    SEALED_FALLBACK_OWNER_SEALED_GATE,
    SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
    infer_accept_path_final_emitted_source,
    read_final_emission_meta_dict,
)
from game.interaction_context import rebuild_active_scene_entities
from game.narrative_mode_contract import build_narrative_mode_contract
from game.realization_provenance import (
    GATE_TERMINAL_REPAIR,
    REALIZATION_FALLBACK_FAMILY_FIELD,
    STRICT_SOCIAL_DETERMINISTIC_FALLBACK,
    UPSTREAM_PREPARED_EMISSION,
)
from tests.helpers.narrative_mode_validator_fixtures import minimal_ctir_continuation
from tests.helpers.opening_fallback_evidence import (
    assert_sealed_fallback_owner_bucket,
    opening_gm_output,
)
from tests.helpers.strict_social_harness import runner_strict_bundle

pytestmark = pytest.mark.unit


def _minimal_n4_narrative_plan(*, acceptance_quality: dict[str, Any] | None = None) -> dict[str, Any]:
    """Minimal ``prompt_context.narrative_plan`` for selector N4 snapshot tests."""
    nmc = build_narrative_mode_contract(ctir=minimal_ctir_continuation())
    plan: dict[str, Any] = {"narrative_mode_contract": nmc}
    if acceptance_quality is not None:
        plan["acceptance_quality_contract"] = acceptance_quality
    return plan


_N4_TRAILER_LINE = "Nothing will ever be the same."


def _narrative_mode_plan_payload(contract: dict) -> dict:
    return {"prompt_context": {"narrative_plan": {"narrative_mode_contract": contract}}}


def _visibility_offscene_npc_gate_bundle() -> tuple[dict, dict, dict, str]:
    """Session/scene/world/sid where referencing Lord Aldric is visibility-illegal (offscene NPC)."""
    session = default_session()
    world = default_world()
    world["npcs"].append({"id": "lord_aldric", "name": "Lord Aldric", "location": "castle_keep"})
    scene = default_scene("frontier_gate")
    scene["scene"]["visible_facts"] = ["A brazier throws orange sparks over the checkpoint."]
    scene["scene"]["discoverable_clues"] = ["The missing patrol was last seen near the old stone bridge."]
    scene["scene"]["hidden_facts"] = ["The checkpoint taxes are funding an Ash Cowl payoff."]
    sid = "frontier_gate"
    session["active_scene_id"] = sid
    session["scene_state"]["active_scene_id"] = sid
    rebuild_active_scene_entities(session, world, sid, scene_envelope=scene)
    scene["scene_state"] = dict(session["scene_state"])
    return session, world, scene, sid


# --- Block AG: sealed branch selector / order snapshots (branch routing locks) ---
def test_selector_snapshot_visibility_vs_generic_terminal_distinct_markers() -> None:
    """Visibility illegality uses visibility-specific tags and debug; generic terminal replace does not."""
    session, world, scene, sid = _visibility_offscene_npc_gate_bundle()
    vis = apply_final_emission_gate(
        {"player_facing_text": "Lord Aldric watches the checkpoint from the square.", "tags": []},
        resolution={"kind": "observe", "prompt": "I look."},
        session=session,
        scene_id=sid,
        world=world,
        scene=scene,
    )
    gen = apply_final_emission_gate(
        {"player_facing_text": "", "tags": []},
        resolution={"kind": "observe", "prompt": "I wait."},
        session={},
        scene_id="yard",
        world={},
    )
    vis_tl = [str(t) for t in (vis.get("tags") or []) if isinstance(t, str)]
    gen_tl = [str(t) for t in (gen.get("tags") or []) if isinstance(t, str)]
    assert "visibility_enforcement_replaced" in vis_tl
    assert "visibility_enforcement_replaced" not in gen_tl
    assert "final_emission_gate:narrative_safe_fallback" in gen_tl

    vis_fem = read_final_emission_meta_dict(vis) or {}
    gen_fem = read_final_emission_meta_dict(gen) or {}
    assert vis_fem["final_emitted_source"] == "global_scene_fallback"
    assert gen_fem["final_emitted_source"] == "global_scene_fallback"
    assert vis_fem["visibility_replacement_applied"] is True
    assert gen_fem.get("visibility_replacement_applied") is not True


def test_selector_snapshot_n4_replace_vs_generic_terminal_distinct_markers() -> None:
    """N4 floor failure tags acceptance_quality; generic terminal uses narrative_safe_fallback pool tag."""
    plan = _minimal_n4_narrative_plan(acceptance_quality={"enabled": True})
    n4_out = apply_final_emission_gate(
        {
            "player_facing_text": _N4_TRAILER_LINE,
            "tags": [],
            "prompt_context": {"narrative_plan": plan},
        },
        resolution={"kind": "narrate", "prompt": "I wait."},
        session=None,
        scene_id="lane_scene",
        world={},
    )
    gen_out = apply_final_emission_gate(
        {"player_facing_text": "", "tags": []},
        resolution={"kind": "observe", "prompt": "I wait."},
        session={},
        scene_id="yard",
        world={},
    )
    n4_tl = [str(t) for t in (n4_out.get("tags") or []) if isinstance(t, str)]
    gen_tl = [str(t) for t in (gen_out.get("tags") or []) if isinstance(t, str)]
    assert "final_emission_gate:acceptance_quality" in n4_tl
    assert "final_emission_gate:acceptance_quality" not in gen_tl
    assert "final_emission_gate:narrative_safe_fallback" in gen_tl

    n4_fem = read_final_emission_meta_dict(n4_out) or {}
    gen_fem = read_final_emission_meta_dict(gen_out) or {}
    assert n4_fem["final_emitted_source"] == "acceptance_quality_global_scene_fallback"
    assert gen_fem["final_emitted_source"] == "global_scene_fallback"
    assert n4_fem[REALIZATION_FALLBACK_FAMILY_FIELD] == GATE_TERMINAL_REPAIR
    assert gen_fem[REALIZATION_FALLBACK_FAMILY_FIELD] == GATE_TERMINAL_REPAIR
    assert_sealed_fallback_owner_bucket(n4_fem, SEALED_FALLBACK_OWNER_SEALED_GATE)
    assert_sealed_fallback_owner_bucket(gen_fem, SEALED_FALLBACK_OWNER_SEALED_GATE)
    assert n4_fem.get("acceptance_quality_gate_replaced_candidate") is True
    assert gen_fem.get("acceptance_quality_gate_replaced_candidate") is not True


def test_selector_snapshot_opening_rt_repair_vs_generic_terminal_families() -> None:
    """Opening contract repair stamps legacy diegetic family; generic terminal stamps gate_terminal_repair."""
    gm_open = opening_gm_output()
    gm_open["player_facing_text"] = "Nearby crates appear disturbed."
    gm_open["tags"] = []
    open_out = apply_final_emission_gate(
        gm_open,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )
    gen_out = apply_final_emission_gate(
        {"player_facing_text": "", "tags": []},
        resolution={"kind": "observe", "prompt": "I wait."},
        session={},
        scene_id="yard",
        world={},
    )
    o_fem = read_final_emission_meta_dict(open_out) or {}
    g_fem = read_final_emission_meta_dict(gen_out) or {}
    assert o_fem["final_emitted_source"] == "opening_deterministic_fallback"
    assert o_fem["final_route"] == "accept_candidate"
    assert o_fem[REALIZATION_FALLBACK_FAMILY_FIELD] == UPSTREAM_PREPARED_EMISSION

    assert g_fem["final_emitted_source"] == "global_scene_fallback"
    assert g_fem["final_route"] == "replaced"
    assert g_fem[REALIZATION_FALLBACK_FAMILY_FIELD] == GATE_TERMINAL_REPAIR


def test_selector_snapshot_strict_social_emergency_vs_gate_terminal_family(monkeypatch) -> None:
    """Strict-social sealed minimal emergency uses strict-social deterministic family; generic terminal uses gate_terminal."""
    gen_out = apply_final_emission_gate(
        {"player_facing_text": "", "tags": []},
        resolution={"kind": "observe", "prompt": "I wait."},
        session={},
        scene_id="yard",
        world={},
    )
    gen_fem = read_final_emission_meta_dict(gen_out) or {}
    assert gen_fem[REALIZATION_FALLBACK_FAMILY_FIELD] == GATE_TERMINAL_REPAIR

    session, world, sid, resolution = runner_strict_bundle()
    nmc = build_narrative_mode_contract(ctir=minimal_ctir_continuation())
    stub_details = {
        "used_internal_fallback": False,
        "final_emitted_source": "test_stub",
        "rejection_reasons": [],
        "deterministic_attempted": False,
        "deterministic_passed": False,
        "fallback_pool": "none",
        "fallback_kind": "none",
        "route_illegal_intercepted": False,
    }

    def fake_build(candidate_text, *, resolution, tags, session, scene_id, world):
        bad = "You wake to a new day. The market unfolds around you as if nothing before it mattered."
        return bad, dict(stub_details)

    monkeypatch.setattr(strict_social_stack, "build_final_strict_social_response", fake_build)
    ss_out = apply_final_emission_gate(
        {
            "player_facing_text": "stub",
            "tags": [],
            **_narrative_mode_plan_payload(nmc),
        },
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    ss_fem = read_final_emission_meta_dict(ss_out) or {}
    assert ss_fem["final_emitted_source"] == "minimal_social_emergency_fallback"
    assert ss_fem[REALIZATION_FALLBACK_FAMILY_FIELD] == STRICT_SOCIAL_DETERMINISTIC_FALLBACK
    assert_sealed_fallback_owner_bucket(ss_fem, SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED)
    tl = [str(t) for t in (ss_out.get("tags") or []) if isinstance(t, str)]
    assert any("final_emission_gate:narrative_mode_output" in t for t in tl)


def test_selector_snapshot_valid_candidate_bypasses_sealed_branches() -> None:
    """Clean observe narration accepts without sealed-replace tags."""
    out = apply_final_emission_gate(
        {"player_facing_text": "Rain ticks against the gatehouse stones.", "tags": []},
        resolution={"kind": "observe", "prompt": "I listen."},
        session={},
        scene_id="yard",
        world={},
    )
    fem = read_final_emission_meta_dict(out) or {}
    tl = [str(t) for t in (out.get("tags") or []) if isinstance(t, str)]
    assert fem["final_route"] == "accept_candidate"
    assert fem["final_emitted_source"] == "generated_candidate"
    assert fem.get(REALIZATION_FALLBACK_FAMILY_FIELD) is None
    assert_sealed_fallback_owner_bucket(fem, None)
    assert "visibility_enforcement_replaced" not in tl
    assert "final_emission_gate:acceptance_quality" not in tl
    assert "final_emission_gate_replaced" not in tl


def test_sealed_branch_order_accept_path_visibility_before_n4(monkeypatch) -> None:
    order: list[str] = []
    orig_vis = terminal_pipeline.apply_visibility_enforcement
    orig_n4 = terminal_pipeline.apply_acceptance_quality_n4_floor_seam

    def wrap_vis(*args: Any, **kwargs: Any):
        order.append("visibility")
        return orig_vis(*args, **kwargs)

    def wrap_n4(*args: Any, **kwargs: Any):
        order.append("n4")
        return orig_n4(*args, **kwargs)

    monkeypatch.setattr(terminal_pipeline, "apply_visibility_enforcement", wrap_vis)
    monkeypatch.setattr(terminal_pipeline, "apply_acceptance_quality_n4_floor_seam", wrap_n4)

    plan = _minimal_n4_narrative_plan(acceptance_quality={"enabled": True})
    apply_final_emission_gate(
        {
            "player_facing_text": "Torchlight holds on wet cobbles near the east lane.",
            "tags": [],
            "prompt_context": {"narrative_plan": plan},
        },
        resolution={"kind": "narrate", "prompt": "I wait."},
        session=None,
        scene_id="lane_scene",
        world={},
    )
    assert order == ["visibility", "n4"]


def test_sealed_branch_order_replace_path_visibility_before_n4(monkeypatch) -> None:
    order: list[str] = []
    orig_vis = terminal_pipeline.apply_visibility_enforcement
    orig_n4 = terminal_pipeline.apply_acceptance_quality_n4_floor_seam

    def wrap_vis(*args: Any, **kwargs: Any):
        order.append("visibility")
        return orig_vis(*args, **kwargs)

    def wrap_n4(*args: Any, **kwargs: Any):
        order.append("n4")
        return orig_n4(*args, **kwargs)

    monkeypatch.setattr(terminal_pipeline, "apply_visibility_enforcement", wrap_vis)
    monkeypatch.setattr(terminal_pipeline, "apply_acceptance_quality_n4_floor_seam", wrap_n4)

    apply_final_emission_gate(
        {"player_facing_text": "", "tags": []},
        resolution={"kind": "observe", "prompt": "I wait."},
        session={},
        scene_id="yard",
        world={},
    )
    assert order == ["visibility", "n4"]


def _assert_source_markers_in_order(source: str, markers: list[str]) -> None:
    cursor = -1
    for marker in markers:
        next_index = source.find(marker, cursor + 1)
        assert next_index > cursor, marker
        cursor = next_index


def test_block_m4_final_emitted_source_accept_precedence_ladders_are_locked() -> None:
    """Characterization: accept-path final source attribution is a last-repair-wins ladder."""

    projector_source = inspect.getsource(infer_accept_path_final_emitted_source)
    gate_source = inspect.getsource(feg.apply_final_emission_gate)
    strict_social_source = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)

    precedence_markers = [
        'rtd.get("response_type_repair_used")',
        'source = "retry_output"',
        'ac.get("answer_completeness_repaired")',
        'rd.get("response_delta_repaired")',
        'srs.get("social_response_structure_repair_applied")',
        'nat.get("narrative_authenticity_repaired")',
        'na.get("narrative_authority_repaired")',
        'te.get("tone_escalation_repaired")',
        'ar.get("anti_railroading_repaired")',
        'cs.get("context_separation_repaired")',
        'fb.get("fallback_behavior_repaired")',
        'purity.get("player_facing_narration_purity_repaired")',
        'asp.get("answer_shape_primacy_repaired")',
        'ffnc.get("fast_fallback_neutral_composition_repaired")',
    ]
    _assert_source_markers_in_order(projector_source, precedence_markers)

    assert gate_source.count("infer_accept_path_final_emitted_source(") == 0
    assert strict_social_source.count("infer_accept_path_final_emitted_source(") == 1
    generic_accept_source = inspect.getsource(generic_exit.run_generic_accept_exit)
    assert generic_accept_source.count("infer_accept_path_final_emitted_source(") == 1
    assert (
        'str(details.get("final_emitted_source") or "unknown_post_gate_writer")'
        in strict_social_source
    )
    assert 'infer_accept_path_final_emitted_source(\n        "generated_candidate"' in generic_accept_source
    assert "fem_assembly.build_gate_accept_fem_base" in generic_accept_source
    assert "fem_assembly.merge_gate_layer_metas_into_fem" in generic_accept_source


def test_block_m4_replacement_final_source_ownership_is_locked() -> None:
    """Characterization: replacement paths use selected fallback source, with late patch-only exceptions."""

    gate_source = inspect.getsource(feg.apply_final_emission_gate)
    strict_social_source = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    generic_replace_source = inspect.getsource(generic_exit.run_generic_replace_exit)

    _assert_source_markers_in_order(
        strict_social_source,
        [
            'details = {**details, "final_emitted_source": "minimal_social_emergency_fallback"}',
            '"final_emitted_source": "minimal_social_emergency_fallback"',
            'infer_accept_path_final_emitted_source(',
            'str(details.get("final_emitted_source") or "unknown_post_gate_writer")',
            'fem_assembly.build_gate_accept_fem_base(',
            'fem_assembly.merge_gate_layer_metas_into_fem(',
            'gate_tag="interaction_continuity"',
            'gate_tag="narrative_mode_output"',
        ],
    )
    assert "fem_assembly.build_gate_replace_fem_base" in strict_social_source
    assert strict_social_source.count("fem_assembly.merge_gate_layer_metas_into_fem") == 2
    _assert_source_markers_in_order(
        generic_replace_source,
        [
            'sealed_selection = sealed_fallback.select_non_strict_replace_path_terminal_sealed_fallback_selection',
            'final_emitted_source = sealed_selection.final_emitted_source',
            '"final_emitted_source": final_emitted_source',
            'fem_assembly.build_gate_replace_fem_base(',
            'sealed_fallback.stamp_non_strict_sealed_replacement_realization_family(',
            'sealed_fallback.stamp_sealed_fallback_realization_family(',
        ],
    )


def test_block_ai_block_ag_selector_order_snapshots_remain_entrypoints() -> None:
    """Regression anchor: Block AG / BG-2 gate-orchestration snapshots must stay importable.

    Pure visibility/sealed helper importability, tuple round-trips, and defensive-copy
    locks live in tests/test_final_emission_visibility_fallback.py,
    tests/test_final_emission_sealed_fallback.py, and opening RT/upstream-prepared pins in
    tests/test_final_emission_opening_fallback.py (see owner entrypoint anchors).
    """
    mod = sys.modules[__name__]
    for name in (
        "test_sealed_branch_order_accept_path_visibility_before_n4",
        "test_sealed_branch_order_replace_path_visibility_before_n4",
        "test_selector_snapshot_visibility_vs_generic_terminal_distinct_markers",
        "test_selector_snapshot_n4_replace_vs_generic_terminal_distinct_markers",
        "test_selector_snapshot_opening_rt_repair_vs_generic_terminal_families",
        "test_selector_snapshot_valid_candidate_bypasses_sealed_branches",
    ):
        assert callable(getattr(mod, name, None)), name


# Ownership note:
# This cluster extends opening fallback historical regression locks. Investigate
# upstream/opening fallback ownership first; add cases here only for final-gate
# accept/replace routing, curated-fact source precedence, or fail-closed FEM.


def test_final_gate_plain_valid_candidate_has_source_without_fallback_family() -> None:
    candidate = "Rain ticks against the gatehouse stones."
    out = apply_final_emission_gate(
        {"player_facing_text": candidate, "tags": []},
        resolution={"kind": "observe", "prompt": "I listen."},
        session={},
        scene_id="yard",
        world={},
    )

    fem = read_final_emission_meta_dict(out) or {}
    assert out["player_facing_text"] == candidate
    assert fem["final_route"] == "accept_candidate"
    assert fem["candidate_validation_passed"] is True
    assert fem["final_emitted_source"] == "generated_candidate"
    assert fem.get(REALIZATION_FALLBACK_FAMILY_FIELD) is None
    assert fem.get("fallback_family_used") is None
