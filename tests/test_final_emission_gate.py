"""Practical primary direct-owner suite for ``apply_final_emission_gate`` orchestration.

This file owns direct layer-order, final gate-integration, and continuity-adjacent
gate-step semantics. Direct prompt-contract semantics belong in
``tests/test_prompt_context.py`` and direct response-policy accessor/materialization
semantics belong in ``tests/test_response_policy_contracts.py``. Downstream
emission, telemetry, metadata, pipeline, transcript, and continuity-adjacent
bridge/validation/repair suites should consume already-owned gate behavior here
rather than re-own orchestration order or gate-private attachment behavior there;
those files stay consumer, smoke, observability, packaged-snapshot, or regression
coverage once the orchestration contract is already owned here.
"""

# === PRACTICAL OWNER SUITE ===
# Owns gate orchestration order, continuity placement, repair-before-validation,
# route-decision / FEM projection through ``apply_final_emission_gate``, and Block AG
# selector snapshots. Semantic layer rules live in direct owner suites; N4 scoring
# lives in ``tests/test_acceptance_quality.py`` — gate keeps N4 order/replace only.

from __future__ import annotations

import copy
import inspect
import sys
from typing import Any, Mapping
from game.acceptance_quality import (
    build_acceptance_quality_contract,
    validate_and_repair_acceptance_quality,
)
from game.final_emission_meta import (
    SEALED_FALLBACK_OWNER_SEALED_GATE,
    SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
    infer_accept_path_final_emitted_source,
    read_final_emission_meta_dict,
)

import pytest

import game.final_emission_gate as feg
import game.final_emission_visibility_fallback as visibility_fallback
from game.contract_registry import emergency_fallback_source_ids
from game.defaults import default_scene, default_session, default_world
from game.final_emission_gate import apply_final_emission_gate, get_speaker_selection_contract
from game.narrative_mode_contract import build_narrative_mode_contract
from game.context_separation import build_context_separation_contract
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.social_exchange_emission import effective_strict_social_resolution_for_emission
from game.storage import get_scene_runtime
from game.realization_authority import FALLBACK_FAMILIES
from game.realization_provenance import (
    GATE_TERMINAL_REPAIR,
    LEGACY_DIEGETIC_FALLBACK,
    REALIZATION_FALLBACK_FAMILY_FIELD,
    STRICT_SOCIAL_DETERMINISTIC_FALLBACK,
    UPSTREAM_PREPARED_EMISSION,
)
from game.opening_deterministic_fallback import deterministic_opening_fallback_text_and_meta as _deterministic_opening_under_test
import game.opening_deterministic_fallback as opening_deterministic_fallback
from game.upstream_response_repairs import (
    UPSTREAM_PREPARED_OPENING_FALLBACK_KEY,
    maybe_attach_upstream_prepared_opening_fallback_payload,
)
from tests.helpers.emission_smoke_assertions import final_emission_meta_from_output, response_type_contract
from tests.helpers.opening_fallback_evidence import (
    assert_sealed_fallback_owner_bucket,
    opening_gm_output,
)
from tests.helpers.strict_social_harness import (
    run_strict_social_motive_overclaim_gate_case,
    runner_strict_bundle,
)
from tests.helpers.narrative_mode_validator_fixtures import minimal_ctir_continuation

pytestmark = pytest.mark.unit


def _minimal_n4_narrative_plan(*, acceptance_quality: dict[str, Any] | None = None) -> dict[str, Any]:
    """Minimal ``prompt_context.narrative_plan`` for N4 gate tests (CTIR-backed ``narrative_mode_contract``).

    Omit *acceptance_quality* to assert N4 defaults when the plan ships no ``acceptance_quality_contract``.
    """
    nmc = build_narrative_mode_contract(ctir=minimal_ctir_continuation())
    plan: dict[str, Any] = {"narrative_mode_contract": nmc}
    if acceptance_quality is not None:
        plan["acceptance_quality_contract"] = acceptance_quality
    return plan


_N4_TRAILER_LINE = "Nothing will ever be the same."
_N4_GROUNDED_LEAD = (
    "You still hold the sergeant's gaze while torchlight picks out wet cobbles on the east lane. "
)
_N4_REPAIRABLE_TWO_SENTENCE = f"{_N4_GROUNDED_LEAD}{_N4_TRAILER_LINE}"


def test_acceptance_quality_n4_off_when_narrative_plan_absent() -> None:
    out = apply_final_emission_gate(
        {"player_facing_text": "Wind rises.", "tags": []},
        resolution={"kind": "observe", "prompt": "I wait."},
        session=None,
        scene_id="s1",
        world={},
    )
    fem = read_final_emission_meta_dict(out) or {}
    assert fem.get("acceptance_quality_checked") is False


def test_acceptance_quality_n4_replace_path_reruns_seam_on_fallback_and_fem_terminal(monkeypatch) -> None:
    plan = _minimal_n4_narrative_plan(acceptance_quality={"enabled": True})
    calls: list[str] = []

    def _spy(text: str, contract: dict) -> dict:
        calls.append(str(text or ""))
        return validate_and_repair_acceptance_quality(text, contract)

    monkeypatch.setattr(feg, "validate_and_repair_acceptance_quality", _spy)
    out = apply_final_emission_gate(
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

    assert len(calls) == 2
    assert calls[0].lower().strip() == _N4_TRAILER_LINE.lower().strip()
    assert calls[0] != calls[1]
    fem = read_final_emission_meta_dict(out) or {}
    assert fem.get("acceptance_quality_gate_replaced_candidate") is True
    assert fem.get("final_route") == "replaced"
    assert fem.get("acceptance_quality_rejected_reason_codes")
    assert isinstance(fem.get("acceptance_quality_rejected_reason_codes"), list)
    assert fem.get("candidate_validation_passed") is False
    assert fem.get("final_emitted_source") == "acceptance_quality_global_scene_fallback"
    assert fem.get(REALIZATION_FALLBACK_FAMILY_FIELD) == GATE_TERMINAL_REPAIR
    aq_contract = build_acceptance_quality_contract(overrides=plan["acceptance_quality_contract"])
    ref = validate_and_repair_acceptance_quality(str(out.get("player_facing_text") or ""), aq_contract)
    assert fem.get("acceptance_quality_passed") == bool(ref["validation"]["passed"])
    tags = list(out.get("tags") or [])
    assert "final_emission_gate:acceptance_quality" in tags
    assert "nothing will ever be the same" not in (out.get("player_facing_text") or "").lower()


def test_acceptance_quality_n4_runs_before_interaction_continuity_attachment(monkeypatch) -> None:
    plan = _minimal_n4_narrative_plan(acceptance_quality={"enabled": True})
    order: list[str] = []

    def _spy(text: str, contract: dict) -> dict:
        order.append("n4")
        return validate_and_repair_acceptance_quality(text, contract)

    monkeypatch.setattr(feg, "validate_and_repair_acceptance_quality", _spy)

    _orig_ic = feg._attach_interaction_continuity_validation

    def _ic_hook(
        out: dict,
        *,
        resolution_for_contracts=None,
        eff_resolution=None,
        session=None,
        preserve_existing_validation: bool = False,
    ) -> None:
        order.append("ic")
        return _orig_ic(
            out,
            resolution_for_contracts=resolution_for_contracts,
            eff_resolution=eff_resolution,
            session=session,
            preserve_existing_validation=preserve_existing_validation,
        )

    monkeypatch.setattr(feg, "_attach_interaction_continuity_validation", _ic_hook)

    apply_final_emission_gate(
        {
            "player_facing_text": _N4_REPAIRABLE_TWO_SENTENCE,
            "tags": [],
            "prompt_context": {"narrative_plan": plan},
        },
        resolution={"kind": "narrate", "prompt": "I hold position."},
        session=None,
        scene_id="lane_scene",
        world={},
    )
    assert order.index("n4") < order.index("ic")


def _strong_interaction_continuity_contract(*, anchor: str = "npc_melka") -> dict:
    return {
        "enabled": True,
        "continuity_strength": "strong",
        "anchored_interlocutor_id": anchor,
        "preserve_conversational_thread": True,
        "speaker_selection_contract": None,
    }


def test_apply_final_emission_gate_runs_response_type_then_continuity_then_fallback():
    """C2: continuity at the gate is validate-only; ``repair_interaction_continuity`` is not invoked."""
    calls: list[str] = []
    real_response_type = feg._enforce_response_type_contract
    real_ic_step = feg._apply_interaction_continuity_emission_step

    def response_type_wrapper(*args, **kwargs):
        calls.append("response_type")
        return real_response_type(*args, **kwargs)

    def continuity_validate_wrapper(*args, **kwargs):
        calls.append("interaction_continuity_validate")
        return real_ic_step(*args, **kwargs)

    long_narration = (
        "The regional economy depends on tolls, wayposts, and seasonal trade convoys moving "
        "between jurisdictions, a fact recorded in dry ledgers that never mention your question."
    )
    gm = {
        "player_facing_text": long_narration,
        "tags": [],
        "metadata": {},
        "response_policy": {"interaction_continuity": _strong_interaction_continuity_contract()},
    }
    resolution = {"metadata": {"emission_debug": {}, "player_input": "What?"}}

    with (
        pytest.MonkeyPatch.context() as mp,
    ):
        mp.setattr(feg, "_enforce_response_type_contract", response_type_wrapper)
        mp.setattr(feg, "_apply_interaction_continuity_emission_step", continuity_validate_wrapper)
        apply_final_emission_gate(
            gm,
            resolution=resolution,
            session=None,
            scene_id="test_scene",
            scene={},
            world={},
        )

    assert calls.index("response_type") < calls.index("interaction_continuity_validate")


def test_apply_final_emission_gate_runs_response_delta_before_speaker_enforcement(monkeypatch):
    session, world, sid, resolution = runner_strict_bundle()
    eff, route, _ = effective_strict_social_resolution_for_emission(resolution, session, world, sid)
    assert route is True
    assert isinstance(eff, dict)

    order: list[str] = []
    orig_rd = feg._apply_response_delta_layer
    orig_enf = feg.enforce_emitted_speaker_with_contract

    def rd(*args, **kwargs):
        order.append("response_delta")
        return orig_rd(*args, **kwargs)

    def enf(*args, **kwargs):
        order.append("speaker_contract")
        return orig_enf(*args, **kwargs)

    monkeypatch.setattr(feg, "_apply_response_delta_layer", rd)
    monkeypatch.setattr(feg, "enforce_emitted_speaker_with_contract", enf)

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
        return 'Tavern Runner says, "No names, only rumors."', dict(stub_details)

    monkeypatch.setattr(feg, "build_final_strict_social_response", fake_build)

    out = apply_final_emission_gate(
        {"player_facing_text": 'Tavern Runner says, "No names, only rumors."', "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    assert order.index("response_delta") < order.index("speaker_contract")
    em = (out.get("metadata") or {}).get("emission_debug") or {}
    assert "speaker_contract_enforcement" in em
    reason = (read_final_emission_meta_dict(out) or {}).get("speaker_contract_enforcement_reason")
    assert reason == em["speaker_contract_enforcement"]["final_reason_code"]


def test_apply_final_emission_gate_strict_social_contract_missing_skips_tightening(monkeypatch):
    """Legacy / missing contract: enforcement must not invent a stricter policy."""
    session, world, sid, resolution = runner_strict_bundle()
    empty_contract = get_speaker_selection_contract(None, None, None)
    assert empty_contract["debug"].get("contract_missing") is True

    monkeypatch.setattr(feg, "get_speaker_selection_contract", lambda *a, **kw: empty_contract)

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
        # Would be forbidden repair if a real contract were present.
        return 'Ragged stranger says, "Pay me."', dict(stub_details)

    monkeypatch.setattr(feg, "build_final_strict_social_response", fake_build)

    out = apply_final_emission_gate(
        {"player_facing_text": 'Ragged stranger says, "Pay me."', "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    text = out.get("player_facing_text") or ""
    assert "Ragged stranger" in text
    assert (read_final_emission_meta_dict(out) or {}).get("speaker_contract_enforcement_reason") == "speaker_contract_match"
    payload = ((out.get("metadata") or {}).get("emission_debug") or {}).get("speaker_contract_enforcement") or {}
    assert payload.get("validation", {}).get("details", {}).get("skipped") == "no_contract"
    assert "repair" not in payload

























# Ownership note:
# This cluster owns speaker-repair invocation boundaries and historical ordering
# locks. Investigate prose/speaker semantics outside the gate first; add cases
# here only for dispatch, mutation taxonomy, or layer order.


def test_block_f_apply_final_emission_gate_non_strict_never_invokes_enforce_emitted_speaker_with_contract(monkeypatch):
    """Block F: speaker contract repair is strict-social-trunk only; non-strict gate must not call enforcement."""

    def boom(*_a, **_k):
        raise AssertionError("enforce_emitted_speaker_with_contract must not run on non-strict-social gate path")

    monkeypatch.setattr(feg, "enforce_emitted_speaker_with_contract", boom)
    apply_final_emission_gate(
        {"player_facing_text": "Rain drums on the slate roof.", "tags": []},
        resolution={"kind": "observe", "prompt": "I listen to the rain."},
        session={},
        scene_id="scene_investigate",
        world={},
    )


def test_block_f_apply_final_emission_gate_suppressed_non_social_turn_never_invokes_enforce_emitted_speaker_with_contract(
    monkeypatch,
):
    """Block F: strict-social suppressed narration uses the non-strict trunk — no speaker repair."""
    world = default_world()
    session = default_session()
    session["interaction_context"] = {
        "active_interaction_target_id": "tavern_runner",
        "active_interaction_kind": "social",
        "interaction_mode": "social",
        "engagement_level": "engaged",
        "conversation_privacy": None,
        "player_position_context": None,
    }

    def boom(*_a, **_k):
        raise AssertionError(
            "enforce_emitted_speaker_with_contract must not run when strict_social_turn is suppressed"
        )

    monkeypatch.setattr(feg, "enforce_emitted_speaker_with_contract", boom)
    apply_final_emission_gate(
        {
            "player_facing_text": "from here, no certain answer presents itself",
            "tags": [],
            "scene_update": None,
            "activate_scene_id": None,
            "new_scene_draft": None,
            "world_updates": None,
            "suggested_action": None,
            "debug_notes": "",
        },
        resolution={"kind": "observe", "prompt": "wait"},
        session=session,
        scene_id="frontier_gate",
        world=world,
    )


def test_block_f_sync_eff_social_to_resolution_single_call_site_in_final_emission_gate():
    """Block F: production sync is only paired with strict-social speaker enforcement in apply_final_emission_gate."""
    from pathlib import Path as _Path

    repo_root = _Path(__file__).resolve().parents[1]
    gate_lines = (repo_root / "game" / "final_emission_gate.py").read_text(encoding="utf-8").splitlines()
    sce_lines = (repo_root / "game" / "speaker_contract_enforcement.py").read_text(encoding="utf-8").splitlines()
    call_lines = [i for i, _ln in enumerate(gate_lines, start=1) if "_sync_eff_social_to_resolution(" in _ln]
    non_def = [ln for ln in call_lines if not gate_lines[ln - 1].lstrip().startswith("def ")]
    assert len(non_def) == 1
    sync_ln = non_def[0]
    window = "\n".join(gate_lines[sync_ln - 1 : sync_ln + 3])
    assert "eff_resolution" in window and "resolution" in window
    def_lines = [i for i, _ln in enumerate(sce_lines, start=1) if _ln.startswith("def _sync_eff_social_to_resolution")]
    assert len(def_lines) == 1




def test_apply_final_emission_gate_non_strict_path_does_not_attach_speaker_enforcement():
    out = apply_final_emission_gate(
        {"player_facing_text": "Rain drums on the slate roof.", "tags": []},
        resolution={"kind": "observe", "prompt": "I listen to the rain."},
        session={},
        scene_id="scene_investigate",
        world={},
    )
    em = (out.get("metadata") or {}).get("emission_debug") or {}
    assert "speaker_contract_enforcement" not in em


def test_apply_final_emission_gate_runs_scene_state_anchor_after_speaker_enforcement(monkeypatch):
    """Objective #8 layer is ordered after speaker contract enforcement on strict-social turns."""
    session, world, sid, resolution = runner_strict_bundle()
    order: list[str] = []
    orig_enf = feg.enforce_emitted_speaker_with_contract
    orig_ssa = feg._apply_scene_state_anchor_layer

    def enf(*args, **kwargs):
        order.append("speaker_contract")
        return orig_enf(*args, **kwargs)

    def ssa(*args, **kwargs):
        order.append("scene_state_anchor")
        return orig_ssa(*args, **kwargs)

    monkeypatch.setattr(feg, "enforce_emitted_speaker_with_contract", enf)
    monkeypatch.setattr(feg, "_apply_scene_state_anchor_layer", ssa)

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
        return 'Tavern Runner says, "No names, only rumors."', dict(stub_details)

    monkeypatch.setattr(feg, "build_final_strict_social_response", fake_build)

    apply_final_emission_gate(
        {"player_facing_text": 'Tavern Runner says, "No names, only rumors."', "tags": []},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    assert order.index("speaker_contract") < order.index("scene_state_anchor")


# Ownership note:
# This cluster owns scene-state-anchor integration and metadata projection at
# final emission. Semantic anchor validation should live with scene-state-anchor
# owners; do not grow this into a broader legality matrix.


def test_apply_final_emission_gate_scene_state_anchor_location_repair_non_strict():
    """C2: floating narration that fails anchoring is not tethered at the boundary (validate-only)."""
    contract = {
        "enabled": True,
        "required_any_of": ["location", "actor", "player_action"],
        "minimum_anchor_hits": 1,
        "scene_id": "frontier_gate",
        "scene_location_label": "Frontier Checkpoint",
        "location_tokens": ["checkpoint", "frontier gate"],
        "actor_tokens": [],
        "player_action_tokens": [],
        "preferred_repair_order": ["actor", "player_action", "location"],
        "debug_reason": "test",
        "debug_sources": {},
    }
    raw = "The air tastes of iron and distant smoke."
    out = apply_final_emission_gate(
        {
            "player_facing_text": raw,
            "tags": [],
            "scene_state_anchor_contract": contract,
        },
        resolution={"kind": "observe", "prompt": "I look around."},
        session=None,
        scene_id="frontier_gate",
        world={},
    )
    text = out.get("player_facing_text") or ""
    assert text.strip() == raw.strip()
    meta = read_final_emission_meta_dict(out) or {}
    em = (out.get("metadata") or {}).get("emission_debug") or {}
    assert meta.get("scene_state_anchor_checked") is True
    assert meta.get("scene_state_anchor_failed") is True
    assert meta.get("scene_state_anchor_repaired") is False
    assert em.get("scene_state_anchor_boundary_semantic_repair_disabled") is True


def _ssa_contract(**overrides):
    base = {
        "enabled": True,
        "required_any_of": ["location", "actor", "player_action"],
        "minimum_anchor_hits": 1,
        "scene_id": "frontier_gate",
        "scene_location_label": None,
        "location_tokens": [],
        "actor_tokens": [],
        "player_action_tokens": [],
        "preferred_repair_order": ["actor", "player_action", "location"],
        "debug_reason": "test",
        "debug_sources": {},
    }
    base.update(overrides)
    return base


def test_strict_social_preserves_speaker_repair_then_applies_anchor_repair(monkeypatch):
    """Speaker enforcement still runs; SSA is validate-only and may record anchor failure without rewriting."""
    session, world, sid, resolution = runner_strict_bundle()

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
        return 'A stranger says, "Fine."', dict(stub_details)

    monkeypatch.setattr(feg, "build_final_strict_social_response", fake_build)

    def fake_enforce(text, *, gm_output, resolution, eff_resolution, world, scene_id):
        fixed = 'Tavern Runner says, "Fine."'
        payload = {
            "contract_present": True,
            "final_reason_code": "local_rebind",
            "validation": {"ok": True},
            "repair": {"mode": "local_rebind"},
        }
        return fixed, payload

    monkeypatch.setattr(feg, "enforce_emitted_speaker_with_contract", fake_enforce)

    contract = _ssa_contract(
        scene_id=sid,
        location_tokens=["investigate", "scene investigate"],
        actor_tokens=[],
        player_action_tokens=[],
    )
    out = apply_final_emission_gate(
        {
            "player_facing_text": 'A stranger says, "Fine."',
            "tags": [],
            "scene_state_anchor_contract": contract,
        },
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    text = (out.get("player_facing_text") or "").lower()
    assert "tavern runner" in text
    meta = read_final_emission_meta_dict(out) or {}
    em = (out.get("metadata") or {}).get("emission_debug") or {}
    assert meta.get("scene_state_anchor_checked") is True
    assert meta.get("scene_state_anchor_repaired") is False
    assert em.get("scene_state_anchor_boundary_semantic_repair_disabled") is True


def test_non_strict_runs_answer_completeness_and_response_delta_before_scene_state_anchor(monkeypatch):
    order: list[str] = []
    orig_ac = feg._apply_answer_completeness_layer
    orig_rd = feg._apply_response_delta_layer
    orig_ssa = feg._apply_scene_state_anchor_layer

    def ac(*args, **kwargs):
        order.append("answer_completeness")
        return orig_ac(*args, **kwargs)

    def rd(*args, **kwargs):
        order.append("response_delta")
        return orig_rd(*args, **kwargs)

    def ssa_layer(*args, **kwargs):
        order.append("scene_state_anchor")
        return orig_ssa(*args, **kwargs)

    monkeypatch.setattr(feg, "_apply_answer_completeness_layer", ac)
    monkeypatch.setattr(feg, "_apply_response_delta_layer", rd)
    monkeypatch.setattr(feg, "_apply_scene_state_anchor_layer", ssa_layer)

    apply_final_emission_gate(
        {
            "player_facing_text": "Rain drums on the slate roof.",
            "tags": [],
            "scene_state_anchor_contract": _ssa_contract(
                scene_location_label="Frontier Checkpoint",
                location_tokens=["checkpoint"],
            ),
        },
        resolution={"kind": "observe", "prompt": "I listen."},
        session={},
        scene_id="frontier_gate",
        world={},
    )
    ix_ac = order.index("answer_completeness")
    ix_rd = order.index("response_delta")
    ix_ssa = order.index("scene_state_anchor")
    assert ix_ac < ix_ssa and ix_rd < ix_ssa


def test_non_strict_scene_state_anchor_does_not_strip_prior_objective_repairs(monkeypatch):
    """Earlier layers may decorate text; SSA validate-only must not strip those markers."""

    def fake_ac(text, **kwargs):
        meta = {
            "answer_completeness_checked": False,
            "answer_completeness_failed": False,
            "answer_completeness_failure_reasons": [],
            "answer_completeness_repaired": True,
            "answer_completeness_repair_mode": "inject_resolution_gate_phrase",
            "answer_completeness_expected_voice": None,
            "answer_completeness_skip_reason": None,
        }
        return text + " |AC_OK|", meta, []

    def fake_rd(text, **kwargs):
        meta = feg._default_response_delta_meta()
        meta["response_delta_repaired"] = True
        meta["response_delta_repair_mode"] = "boundary_echo_trim"
        return text + " |RD_OK|", meta, []

    monkeypatch.setattr(feg, "_apply_answer_completeness_layer", fake_ac)
    monkeypatch.setattr(feg, "_apply_response_delta_layer", fake_rd)

    out = apply_final_emission_gate(
        {
            "player_facing_text": "The wind shifts.",
            "tags": [],
            "scene_state_anchor_contract": _ssa_contract(
                scene_location_label="Frontier Checkpoint",
                location_tokens=["checkpoint"],
            ),
        },
        resolution={"kind": "observe", "prompt": "I listen."},
        session={},
        scene_id="frontier_gate",
        world={},
    )
    text = out.get("player_facing_text") or ""
    assert "|AC_OK|" in text
    assert "|RD_OK|" in text
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("answer_completeness_repaired") is True
    assert meta.get("response_delta_repaired") is True
    assert meta.get("scene_state_anchor_repaired") is False
    assert meta.get("scene_state_anchor_failed") is True
















def test_final_emission_meta_and_emission_debug_merge_scene_state_anchor(monkeypatch):
    upstream = {"enabled": True, "scene_id": "frontier_gate", "counts": {"location": 2, "actor": 1, "player_action": 0}}
    gm_out = {
        "player_facing_text": "The wind shifts.",
        "tags": [],
        "scene_state_anchor_contract": _ssa_contract(location_tokens=["checkpoint"]),
        "metadata": {
            "emission_debug": {
                "scene_state_anchor": dict(upstream),
                "prior_debug_counts": {"x": 1},
            }
        },
    }
    out = apply_final_emission_gate(
        gm_out,
        resolution={"kind": "observe", "prompt": "I look."},
        session={},
        scene_id="frontier_gate",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("scene_state_anchor_checked") is True
    assert meta.get("scene_state_anchor_upstream_debug") == upstream
    em = (out.get("metadata") or {}).get("emission_debug") or {}
    merged = em.get("scene_state_anchor") or {}
    assert merged.get("counts") == {"location": 2, "actor": 1, "player_action": 0}
    assert meta.get("scene_state_anchor_failed") is True
    assert em.get("scene_state_anchor_boundary_semantic_repair_disabled") is True
    assert em.get("prior_debug_counts") == {"x": 1}
    flat_ok = any(k.startswith("scene_state_anchor_") for k in em.keys())
    assert flat_ok




























def test_apply_final_emission_gate_tolerates_missing_gm_output_for_narration_constraint_debug():
    assert apply_final_emission_gate(
        None,
        resolution=None,
        session=None,
        scene_id="scene_investigate",
        world=None,
    ) is None


def test_apply_final_emission_gate_surfaces_narration_constraint_debug_in_metadata(monkeypatch):
    session, world, sid, resolution = runner_strict_bundle()
    speaker_contract = {
        "primary_speaker_id": "runner",
        "primary_speaker_name": "Tavern Runner",
        "primary_speaker_source": "continuity",
        "allowed_speaker_ids": ["runner"],
        "continuity_locked": True,
        "speaker_switch_allowed": False,
        "debug": {"grounding_reason_code": "grounded_in_scene_npc"},
    }
    monkeypatch.setattr(feg, "get_speaker_selection_contract", lambda *a, **kw: dict(speaker_contract))

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
        return 'Tavern Runner says, "East lanes."', dict(stub_details)

    monkeypatch.setattr(feg, "build_final_strict_social_response", fake_build)

    out = apply_final_emission_gate(
        {
            "player_facing_text": 'Tavern Runner says, "East lanes."',
            "tags": [],
            "response_policy": {"response_type_contract": response_type_contract("dialogue")},
        },
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )

    payload = ((out.get("metadata") or {}).get("emission_debug") or {}).get("narration_constraint_debug") or {}
    assert payload["response_type"]["required"] == "dialogue"
    assert payload["response_type"]["candidate_ok"] is True
    assert payload["visibility"]["contract_present"] is True
    assert isinstance(payload["visibility"]["visible_entity_count"], int)
    assert payload["speaker_selection"] == {
        "speaker_id": "runner",
        "speaker_name": "Tavern Runner",
        "selection_source": "continuity",
        "reason_code": "speaker_contract_match",
        "binding_confident": True,
    }

    res_payload = ((resolution.get("metadata") or {}).get("emission_debug") or {}).get("narration_constraint_debug") or {}
    assert res_payload == payload











def test_non_strict_gate_runs_anti_railroading_after_na_before_scene_state_anchor(monkeypatch):
    order: list[str] = []
    orig_na = feg._apply_narrative_authority_layer
    orig_ar = feg._apply_anti_railroading_layer
    orig_cs = feg._apply_context_separation_layer
    orig_pur = feg._apply_player_facing_narration_purity_layer
    orig_asp = feg._apply_answer_shape_primacy_layer
    orig_ssa = feg._apply_scene_state_anchor_layer

    def na(*args, **kwargs):
        order.append("narrative_authority")
        return orig_na(*args, **kwargs)

    def ar(*args, **kwargs):
        order.append("anti_railroading")
        return orig_ar(*args, **kwargs)

    def cs(*args, **kwargs):
        order.append("context_separation")
        return orig_cs(*args, **kwargs)

    def pur(*args, **kwargs):
        order.append("player_facing_narration_purity")
        return orig_pur(*args, **kwargs)

    def asp(*args, **kwargs):
        order.append("answer_shape_primacy")
        return orig_asp(*args, **kwargs)

    def ssa(*args, **kwargs):
        order.append("scene_state_anchor")
        return orig_ssa(*args, **kwargs)

    monkeypatch.setattr(feg, "_apply_narrative_authority_layer", na)
    monkeypatch.setattr(feg, "_apply_anti_railroading_layer", ar)
    monkeypatch.setattr(feg, "_apply_context_separation_layer", cs)
    monkeypatch.setattr(feg, "_apply_player_facing_narration_purity_layer", pur)
    monkeypatch.setattr(feg, "_apply_answer_shape_primacy_layer", asp)
    monkeypatch.setattr(feg, "_apply_scene_state_anchor_layer", ssa)

    cs_contract = build_context_separation_contract(
        player_text="I watch.",
        resolution={"kind": "observe"},
    )
    apply_final_emission_gate(
        {
            "player_facing_text": "Fog rolls in.",
            "tags": [],
            "context_separation_contract": cs_contract,
            "scene_state_anchor_contract": _ssa_contract(location_tokens=["granite"]),
        },
        resolution={"kind": "observe", "prompt": "I watch."},
        session={},
        scene_id="frontier_gate",
        world={},
    )
    assert order.index("narrative_authority") < order.index("anti_railroading")
    assert order.index("anti_railroading") < order.index("context_separation")
    assert order.index("context_separation") < order.index("player_facing_narration_purity")
    assert order.index("player_facing_narration_purity") < order.index("answer_shape_primacy")
    assert order.index("answer_shape_primacy") < order.index("scene_state_anchor")


def test_apply_final_emission_gate_runs_context_separation_before_scene_state_anchor(monkeypatch):
    order: list[str] = []
    orig_cs = feg._apply_context_separation_layer
    orig_pur = feg._apply_player_facing_narration_purity_layer
    orig_asp = feg._apply_answer_shape_primacy_layer
    orig_ssa = feg._apply_scene_state_anchor_layer

    def cs(*args, **kwargs):
        order.append("context_separation")
        return orig_cs(*args, **kwargs)

    def pur(*args, **kwargs):
        order.append("player_facing_narration_purity")
        return orig_pur(*args, **kwargs)

    def asp(*args, **kwargs):
        order.append("answer_shape_primacy")
        return orig_asp(*args, **kwargs)

    def ssa(*args, **kwargs):
        order.append("scene_state_anchor")
        return orig_ssa(*args, **kwargs)

    monkeypatch.setattr(feg, "_apply_context_separation_layer", cs)
    monkeypatch.setattr(feg, "_apply_player_facing_narration_purity_layer", pur)
    monkeypatch.setattr(feg, "_apply_answer_shape_primacy_layer", asp)
    monkeypatch.setattr(feg, "_apply_scene_state_anchor_layer", ssa)

    cs_contract = build_context_separation_contract(
        player_text="I look around.",
        resolution={"kind": "observe"},
    )
    apply_final_emission_gate(
        {
            "player_facing_text": "Fog rolls in low over the gate.",
            "tags": [],
            "context_separation_contract": cs_contract,
            "scene_state_anchor_contract": _ssa_contract(location_tokens=["granite"]),
        },
        resolution={"kind": "observe", "prompt": "I look around."},
        session={},
        scene_id="frontier_gate",
        world={},
    )
    assert order.index("context_separation") < order.index("player_facing_narration_purity")
    assert order.index("player_facing_narration_purity") < order.index("answer_shape_primacy")
    assert order.index("answer_shape_primacy") < order.index("scene_state_anchor")


# Opening adapter/ownership: tests/test_final_emission_opening_fallback.py
# Gate suite keeps Block L attach-order pin and Block AG opening selector snapshots only.


def _assert_known_realization_family(value: str) -> None:
    assert value in FALLBACK_FAMILIES


def test_block_l_apply_final_emission_gate_scene_opening_maybe_attach_runs_before_deterministic_opening_composer(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Block L: full gate orchestration always invokes ``maybe_attach_upstream_prepared_opening_fallback_payload`` before any upstream opening composer call."""
    gm_output = opening_gm_output()
    gm_output["player_facing_text"] = "Nearby crates appear disturbed."
    gm_output["tags"] = []
    gm_output.pop(UPSTREAM_PREPARED_OPENING_FALLBACK_KEY, None)

    seq: list[str] = []
    real_maybe = maybe_attach_upstream_prepared_opening_fallback_payload
    real_det = _deterministic_opening_under_test

    def wrapped_maybe(out: dict[str, Any], *, resolution: dict[str, Any] | None) -> None:
        seq.append("maybe_attach")
        return real_maybe(out, resolution=resolution)

    def wrapped_det(out: Mapping[str, Any] | None) -> tuple[str, dict[str, Any]]:
        seq.append("deterministic_opening_fallback")
        return real_det(out)

    monkeypatch.setattr(feg, "maybe_attach_upstream_prepared_opening_fallback_payload", wrapped_maybe)
    monkeypatch.setattr(opening_deterministic_fallback, "deterministic_opening_fallback_text_and_meta", wrapped_det)

    apply_final_emission_gate(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )

    assert seq[0] == "maybe_attach"
    if "deterministic_opening_fallback" in seq:
        assert seq.index("maybe_attach") < seq.index("deterministic_opening_fallback")


def test_final_gate_terminal_repair_branch_records_gate_terminal_family() -> None:
    out = apply_final_emission_gate(
        {"player_facing_text": "", "tags": []},
        resolution={"kind": "observe", "prompt": "I wait."},
        session={},
        scene_id="yard",
        world={},
    )

    fem = read_final_emission_meta_dict(out) or {}
    assert out["player_facing_text"] == "For a breath, the scene holds while voices shift around you."
    assert "final_emission_gate_replaced" in out["tags"]
    assert fem["final_route"] == "replaced"
    assert fem["candidate_validation_passed"] is False
    assert fem["final_emitted_source"] == "global_scene_fallback"
    family = fem[REALIZATION_FALLBACK_FAMILY_FIELD]
    _assert_known_realization_family(family)
    assert family == GATE_TERMINAL_REPAIR
    assert family != UPSTREAM_PREPARED_EMISSION


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

    monkeypatch.setattr(feg, "build_final_strict_social_response", fake_build)
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
    orig_vis = feg._apply_visibility_enforcement
    orig_n4 = feg._apply_acceptance_quality_n4_floor_seam

    def wrap_vis(*args: Any, **kwargs: Any):
        order.append("visibility")
        return orig_vis(*args, **kwargs)

    def wrap_n4(*args: Any, **kwargs: Any):
        order.append("n4")
        return orig_n4(*args, **kwargs)

    monkeypatch.setattr(feg, "_apply_visibility_enforcement", wrap_vis)
    monkeypatch.setattr(feg, "_apply_acceptance_quality_n4_floor_seam", wrap_n4)

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
    orig_vis = feg._apply_visibility_enforcement
    orig_n4 = feg._apply_acceptance_quality_n4_floor_seam

    def wrap_vis(*args: Any, **kwargs: Any):
        order.append("visibility")
        return orig_vis(*args, **kwargs)

    def wrap_n4(*args: Any, **kwargs: Any):
        order.append("n4")
        return orig_n4(*args, **kwargs)

    monkeypatch.setattr(feg, "_apply_visibility_enforcement", wrap_vis)
    monkeypatch.setattr(feg, "_apply_acceptance_quality_n4_floor_seam", wrap_n4)

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

    assert gate_source.count("infer_accept_path_final_emitted_source(") == 2
    assert (
        'str(details.get("final_emitted_source") or "unknown_post_gate_writer")'
        in gate_source
    )
    assert 'infer_accept_path_final_emitted_source(\n            "generated_candidate"' in gate_source


def test_block_m4_replacement_final_source_ownership_is_locked() -> None:
    """Characterization: replacement paths use selected fallback source, with late patch-only exceptions."""

    source = inspect.getsource(feg.apply_final_emission_gate)

    _assert_source_markers_in_order(
        source,
        [
            'details = {**details, "final_emitted_source": "minimal_social_emergency_fallback"}',
            '"final_emitted_source": "minimal_social_emergency_fallback"',
            'infer_accept_path_final_emitted_source(',
            'str(details.get("final_emitted_source") or "unknown_post_gate_writer")',
            'gate_tag="interaction_continuity"',
            'gate_tag="narrative_mode_output"',
        ],
    )
    _assert_source_markers_in_order(
        source,
        [
            'sealed_selection = _select_non_strict_replace_path_terminal_sealed_fallback_selection',
            'final_emitted_source = sealed_selection.final_emitted_source',
            '"final_emitted_source": final_emitted_source',
            '_stamp_sealed_fallback_realization_family(',
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


# --- Social response structure downstream integration (orchestration + metadata) -----------------
# Direct prompt-contract semantics live in tests/test_prompt_context.py; these checks verify
# gate ordering, metadata merge paths, and repair behavior after the prompt bundle is shipped.
#
# Ownership note:
# This cluster owns route/speaker/social downstream orchestration and metadata.
# Social-response semantics belong to social emission/structure owners; add cases
# here only for gate ordering, skip reasons, strict-social routing, or FEM fields.


def _secondary_social_response_structure_contract(
    required_response_type: str,
    **overrides,
):
    # Downstream gate tests consume the shipped shape without re-importing the prompt owner helper.
    contract = {
        "enabled": required_response_type == "dialogue",
        "applies_to_response_type": "dialogue",
        "require_spoken_dialogue_shape": required_response_type == "dialogue",
        "discourage_expository_monologue": required_response_type == "dialogue",
        "require_natural_cadence": required_response_type == "dialogue",
        "allow_brief_action_beats": True,
        "allow_brief_refusal_or_uncertainty": True,
        "max_contiguous_expository_lines": 2 if required_response_type == "dialogue" else None,
        "max_dialogue_paragraphs_before_break": 2 if required_response_type == "dialogue" else None,
        "prefer_single_speaker_turn": required_response_type == "dialogue",
        "forbid_bulleted_or_list_like_dialogue": required_response_type == "dialogue",
        "required_response_type": required_response_type,
        "debug_reason": (
            "response_type_contract_requires_dialogue"
            if required_response_type == "dialogue"
            else f"response_type_not_dialogue:{required_response_type}"
        ),
        "debug_inputs": {},
    }
    contract.update(overrides)
    return contract


def _dialogue_response_policy_with_social_structure(**srs_overrides):
    rtc = response_type_contract("dialogue")
    srs = _secondary_social_response_structure_contract("dialogue")
    srs.update(srs_overrides)
    return {"response_type_contract": rtc, "social_response_structure": srs}


def test_social_response_structure_layer_runs_after_response_delta_and_before_tone_escalation(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    order: list[str] = []
    orig_rd = feg._apply_response_delta_layer
    orig_srs = feg._apply_social_response_structure_layer
    orig_te = feg._apply_tone_escalation_layer

    def rd(*args, **kwargs):
        order.append("response_delta")
        return orig_rd(*args, **kwargs)

    def srs(*args, **kwargs):
        order.append("social_response_structure")
        return orig_srs(*args, **kwargs)

    def te(*args, **kwargs):
        order.append("tone_escalation")
        return orig_te(*args, **kwargs)

    monkeypatch.setattr(feg, "_apply_response_delta_layer", rd)
    monkeypatch.setattr(feg, "_apply_social_response_structure_layer", srs)
    monkeypatch.setattr(feg, "_apply_tone_escalation_layer", te)

    pol = _dialogue_response_policy_with_social_structure()
    apply_final_emission_gate(
        {
            "player_facing_text": 'Sergeant says "East gate is two hundred feet south."',
            "tags": [],
            "response_policy": pol,
        },
        resolution={"kind": "question", "prompt": "Where is the east gate?"},
        session=None,
        scene_id="gate_yard",
        world={},
    )
    assert order.index("response_delta") < order.index("social_response_structure") < order.index(
        "tone_escalation"
    )


def test_response_type_failure_skips_social_response_structure_layer(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    pol = _dialogue_response_policy_with_social_structure()
    raw = "The lane stays quiet under the lamps without a direct reply."
    out = apply_final_emission_gate(
        {"player_facing_text": raw, "tags": [], "response_policy": pol},
        resolution={"kind": "observe", "prompt": "What do I hear?"},
        session=None,
        scene_id="lane",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("social_response_structure_skip_reason") == "response_type_contract_failed"
    assert meta.get("social_response_structure_checked") is False
    assert meta.get("final_route") == "replaced"


# Ownership note:
# This cluster owns narrative-mode output orchestration and final replacement
# projection. Narrative-mode semantics belong to their direct contract validators;
# add cases here only for gate skip reasons, branch routing, or final FEM shape.


def _narrative_mode_plan_payload(contract: dict) -> dict:
    return {"prompt_context": {"narrative_plan": {"narrative_mode_contract": contract}}}


def test_strict_social_narrative_mode_output_enforcement_terminal_fallback(monkeypatch):
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

    monkeypatch.setattr(feg, "build_final_strict_social_response", fake_build)

    out = apply_final_emission_gate(
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
    tl = [str(t) for t in (out.get("tags") or []) if isinstance(t, str)]
    assert any("final_emission_gate:narrative_mode_output" in t for t in tl)
    fem = read_final_emission_meta_dict(out) or {}
    assert fem.get("final_route") == "replaced"
    assert fem.get("final_emitted_source") == "minimal_social_emergency_fallback"
    assert fem.get("final_emitted_source") in emergency_fallback_source_ids()
    family = fem[REALIZATION_FALLBACK_FAMILY_FIELD]
    _assert_known_realization_family(family)
    assert family == STRICT_SOCIAL_DETERMINISTIC_FALLBACK
    assert family != GATE_TERMINAL_REPAIR
