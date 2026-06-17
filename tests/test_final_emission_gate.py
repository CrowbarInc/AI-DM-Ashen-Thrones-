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
import game.final_emission_acceptance_quality as acceptance_quality_gate
import game.dialogue_social_plan as dialogue_social_plan
import game.final_emission_finalize as emission_finalize
import game.final_emission_fem_assembly as fem_assembly
import game.final_emission_fast_fallback_composition as fast_fallback_composition
import game.final_emission_gate_context as gate_context
import game.final_emission_generic_exit as generic_exit
import game.final_emission_non_strict_stack as non_strict_stack
import game.final_emission_repairs as emission_repairs
import game.final_emission_narrative_authority as narrative_authority
import game.final_emission_response_type as response_type
import game.final_emission_sealed_fallback as sealed_fallback
import game.final_emission_strict_social_stack as strict_social_stack
import game.final_emission_terminal_pipeline as terminal_pipeline
import game.final_emission_tone_escalation as tone_escalation
import game.final_emission_visibility_fallback as visibility_fallback
from game.final_emission_text import _normalize_text
from tests.helpers.gate_equivalence_monkeypatch import patch_get_speaker_selection_contract
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

    monkeypatch.setattr(acceptance_quality_gate, "validate_and_repair_acceptance_quality", _spy)
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

    monkeypatch.setattr(acceptance_quality_gate, "validate_and_repair_acceptance_quality", _spy)

    _orig_ic = terminal_pipeline.attach_interaction_continuity_validation

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

    monkeypatch.setattr(terminal_pipeline, "attach_interaction_continuity_validation", _ic_hook)

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
    real_response_type = response_type.enforce_response_type_contract
    real_ic_step = non_strict_stack.apply_interaction_continuity_emission_step

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
        mp.setattr(response_type, "enforce_response_type_contract", response_type_wrapper)
        mp.setattr(non_strict_stack, "apply_interaction_continuity_emission_step", continuity_validate_wrapper)
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
    orig_rd = strict_social_stack.emission_repairs._apply_response_delta_layer
    orig_enf = strict_social_stack.enforce_emitted_speaker_with_contract

    def rd(*args, **kwargs):
        order.append("response_delta")
        return orig_rd(*args, **kwargs)

    def enf(*args, **kwargs):
        order.append("speaker_contract")
        return orig_enf(*args, **kwargs)

    monkeypatch.setattr(strict_social_stack.emission_repairs, "_apply_response_delta_layer", rd)
    monkeypatch.setattr(strict_social_stack, "enforce_emitted_speaker_with_contract", enf)

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

    monkeypatch.setattr(strict_social_stack, "build_final_strict_social_response", fake_build)

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

    patch_get_speaker_selection_contract(monkeypatch, empty_contract)

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

    monkeypatch.setattr(strict_social_stack, "build_final_strict_social_response", fake_build)

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

    monkeypatch.setattr(strict_social_stack, "enforce_emitted_speaker_with_contract", boom)
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

    monkeypatch.setattr(strict_social_stack, "enforce_emitted_speaker_with_contract", boom)
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
    """Block F: production sync is only paired with strict-social speaker enforcement in the strict-social trunk."""
    from pathlib import Path as _Path

    repo_root = _Path(__file__).resolve().parents[1]
    gate_lines = (repo_root / "game" / "final_emission_gate.py").read_text(encoding="utf-8").splitlines()
    trunk_lines = (
        repo_root / "game" / "final_emission_strict_social_stack.py"
    ).read_text(encoding="utf-8").splitlines()
    sce_lines = (repo_root / "game" / "speaker_contract_enforcement.py").read_text(encoding="utf-8").splitlines()
    gate_calls = [i for i, _ln in enumerate(gate_lines, start=1) if "_sync_eff_social_to_resolution(" in _ln]
    gate_non_def = [ln for ln in gate_calls if not gate_lines[ln - 1].lstrip().startswith("def ")]
    assert len(gate_non_def) == 0
    trunk_calls = [i for i, _ln in enumerate(trunk_lines, start=1) if "_sync_eff_social_to_resolution(" in _ln]
    trunk_non_def = [ln for ln in trunk_calls if not trunk_lines[ln - 1].lstrip().startswith("def ")]
    assert len(trunk_non_def) == 1
    sync_ln = trunk_non_def[0]
    window = "\n".join(trunk_lines[sync_ln - 1 : sync_ln + 3])
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
    orig_enf = strict_social_stack.enforce_emitted_speaker_with_contract
    orig_ssa = strict_social_stack.apply_scene_state_anchor_layer

    def enf(*args, **kwargs):
        order.append("speaker_contract")
        return orig_enf(*args, **kwargs)

    def ssa(*args, **kwargs):
        order.append("scene_state_anchor")
        return orig_ssa(*args, **kwargs)

    monkeypatch.setattr(strict_social_stack, "enforce_emitted_speaker_with_contract", enf)
    monkeypatch.setattr(strict_social_stack, "apply_scene_state_anchor_layer", ssa)

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

    monkeypatch.setattr(strict_social_stack, "build_final_strict_social_response", fake_build)

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

    monkeypatch.setattr(strict_social_stack, "build_final_strict_social_response", fake_build)

    def fake_enforce(text, *, gm_output, resolution, eff_resolution, world, scene_id):
        fixed = 'Tavern Runner says, "Fine."'
        payload = {
            "contract_present": True,
            "final_reason_code": "local_rebind",
            "validation": {"ok": True},
            "repair": {"mode": "local_rebind"},
        }
        return fixed, payload

    monkeypatch.setattr(strict_social_stack, "enforce_emitted_speaker_with_contract", fake_enforce)

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
    orig_ac = non_strict_stack._apply_answer_completeness_layer
    orig_rd = non_strict_stack._apply_response_delta_layer
    orig_ssa = non_strict_stack.apply_scene_state_anchor_layer

    def ac(*args, **kwargs):
        order.append("answer_completeness")
        return orig_ac(*args, **kwargs)

    def rd(*args, **kwargs):
        order.append("response_delta")
        return orig_rd(*args, **kwargs)

    def ssa_layer(*args, **kwargs):
        order.append("scene_state_anchor")
        return orig_ssa(*args, **kwargs)

    monkeypatch.setattr(non_strict_stack, "_apply_answer_completeness_layer", ac)
    monkeypatch.setattr(non_strict_stack, "_apply_response_delta_layer", rd)
    monkeypatch.setattr(non_strict_stack, "apply_scene_state_anchor_layer", ssa_layer)

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
        meta = emission_repairs._default_response_delta_meta()
        meta["response_delta_repaired"] = True
        meta["response_delta_repair_mode"] = "boundary_echo_trim"
        return text + " |RD_OK|", meta, []

    monkeypatch.setattr(non_strict_stack, "_apply_answer_completeness_layer", fake_ac)
    monkeypatch.setattr(non_strict_stack, "_apply_response_delta_layer", fake_rd)

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
    patch_get_speaker_selection_contract(monkeypatch, speaker_contract)

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

    monkeypatch.setattr(strict_social_stack, "build_final_strict_social_response", fake_build)

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
    orig_na = non_strict_stack.apply_narrative_authority_layer
    orig_ar = non_strict_stack.apply_anti_railroading_layer
    orig_cs = non_strict_stack.apply_context_separation_layer
    orig_pur = non_strict_stack.apply_player_facing_narration_purity_layer
    orig_asp = non_strict_stack.apply_answer_shape_primacy_layer
    orig_ssa = non_strict_stack.apply_scene_state_anchor_layer

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

    monkeypatch.setattr(non_strict_stack, "apply_narrative_authority_layer", na)
    monkeypatch.setattr(non_strict_stack, "apply_anti_railroading_layer", ar)
    monkeypatch.setattr(non_strict_stack, "apply_context_separation_layer", cs)
    monkeypatch.setattr(non_strict_stack, "apply_player_facing_narration_purity_layer", pur)
    monkeypatch.setattr(non_strict_stack, "apply_answer_shape_primacy_layer", asp)
    monkeypatch.setattr(non_strict_stack, "apply_scene_state_anchor_layer", ssa)

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
    orig_cs = non_strict_stack.apply_context_separation_layer
    orig_pur = non_strict_stack.apply_player_facing_narration_purity_layer
    orig_asp = non_strict_stack.apply_answer_shape_primacy_layer
    orig_ssa = non_strict_stack.apply_scene_state_anchor_layer

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

    monkeypatch.setattr(non_strict_stack, "apply_context_separation_layer", cs)
    monkeypatch.setattr(non_strict_stack, "apply_player_facing_narration_purity_layer", pur)
    monkeypatch.setattr(non_strict_stack, "apply_answer_shape_primacy_layer", asp)
    monkeypatch.setattr(non_strict_stack, "apply_scene_state_anchor_layer", ssa)

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

    monkeypatch.setattr(gate_context, "maybe_attach_upstream_prepared_opening_fallback_payload", wrapped_maybe)
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
    monkeypatch.setattr(terminal_pipeline, "apply_visibility_enforcement", lambda out, **kwargs: out)
    order: list[str] = []
    orig_rd = non_strict_stack._apply_response_delta_layer
    orig_srs = non_strict_stack._apply_social_response_structure_layer
    orig_te = non_strict_stack.apply_tone_escalation_layer

    def rd(*args, **kwargs):
        order.append("response_delta")
        return orig_rd(*args, **kwargs)

    def srs(*args, **kwargs):
        order.append("social_response_structure")
        return orig_srs(*args, **kwargs)

    def te(*args, **kwargs):
        order.append("tone_escalation")
        return orig_te(*args, **kwargs)

    monkeypatch.setattr(non_strict_stack, "_apply_response_delta_layer", rd)
    monkeypatch.setattr(non_strict_stack, "_apply_social_response_structure_layer", srs)
    monkeypatch.setattr(non_strict_stack, "apply_tone_escalation_layer", te)

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
    monkeypatch.setattr(terminal_pipeline, "apply_visibility_enforcement", lambda out, **kwargs: out)
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

    monkeypatch.setattr(strict_social_stack, "build_final_strict_social_response", fake_build)

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


def test_bj41_finalize_emission_output_strips_appended_stock_and_packages_sidecar() -> None:
    selector = (
        "Rain drums steady on the slate roof above. "
        "For a breath, the scene stays still."
    )
    out = {
        "player_facing_text": selector,
        "_final_emission_meta": {"final_route": "accept_candidate"},
        "tags": [],
        "metadata": {},
        "debug_notes": "dbg",
    }
    pre = _normalize_text(selector)
    finalized = emission_finalize.finalize_emission_output(out, pre_gate_text=pre, fast_path=True)
    pft = (finalized.get("player_facing_text") or "").lower()
    assert "rain drums" in pft
    assert "scene stays still" not in pft
    assert "internal_state" in finalized
    fem = read_final_emission_meta_dict(finalized) or {}
    assert fem.get("finalize_route_illegal_strip_applied") is True
    lineage = fem.get("final_emission_mutation_lineage")
    assert "finalize_route_illegal_strip" in lineage
    assert "finalize_packaging" in lineage


def test_bj69_terminal_finalize_fast_path_gate_delegators_removed() -> None:
    """BJ-69: terminal pipeline, finalize, and fast-path gate delegators removed; exit stacks call owners."""
    assert not hasattr(feg, "_run_gate_terminal_enforcement_pipeline")
    assert not hasattr(feg, "_finalize_emission_output")
    assert not hasattr(feg, "_final_emission_fast_path_eligible")
    assert callable(getattr(terminal_pipeline, "run_gate_terminal_enforcement_pipeline", None))
    assert callable(getattr(emission_finalize, "finalize_emission_output", None))
    assert callable(getattr(emission_finalize, "final_emission_fast_path_eligible", None))


def test_bj69_exit_stacks_terminal_finalize_fast_path_call_owners_directly() -> None:
    """BJ-69: generic and strict-social exit stacks call terminal/finalize owners directly."""
    ge_accept_src = inspect.getsource(generic_exit.run_generic_accept_exit)
    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    for src in (ge_accept_src, ge_replace_src, ss_src):
        assert "terminal_pipeline.run_gate_terminal_enforcement_pipeline" in src
        assert "emission_finalize.finalize_emission_output" in src
        assert "emission_finalize.final_emission_fast_path_eligible" in src
        assert "feg._run_gate_terminal_enforcement_pipeline" not in src
        assert "feg._finalize_emission_output" not in src
        assert "feg._final_emission_fast_path_eligible" not in src


def test_bj71_non_strict_layer_stack_gate_delegator_removed() -> None:
    """BJ-71: non-strict layer stack gate delegator removed; apply_final_emission_gate calls owner directly."""
    assert not hasattr(feg, "_run_non_strict_layer_stack")
    assert callable(getattr(non_strict_stack, "run_non_strict_layer_stack", None))


def test_bj71_apply_final_emission_gate_calls_non_strict_stack_owner_directly() -> None:
    """BJ-71: gate orchestration calls non_strict_stack owner directly."""
    gate_src = inspect.getsource(feg.apply_final_emission_gate)
    assert "run_non_strict_layer_stack(" in gate_src
    assert "_run_non_strict_layer_stack" not in gate_src


def test_bj70_exit_stack_gate_delegators_removed() -> None:
    """BJ-70: exit/stack gate delegators removed; apply_final_emission_gate calls owners directly."""
    assert not hasattr(feg, "_run_strict_social_composition_trunk")
    assert not hasattr(feg, "_run_generic_accept_exit")
    assert not hasattr(feg, "_run_generic_replace_exit")
    assert callable(getattr(strict_social_stack, "run_strict_social_composition_trunk", None))
    assert callable(getattr(generic_exit, "run_generic_accept_exit", None))
    assert callable(getattr(generic_exit, "run_generic_replace_exit", None))


def test_bj70_apply_final_emission_gate_calls_exit_stack_owners_directly() -> None:
    """BJ-70: gate orchestration calls generic/strict-social exit owners directly."""
    gate_src = inspect.getsource(feg.apply_final_emission_gate)
    assert "run_strict_social_composition_trunk(" in gate_src
    assert "run_generic_accept_exit(" in gate_src
    assert "run_generic_replace_exit(" in gate_src
    assert "_run_strict_social_composition_trunk" not in gate_src
    assert "_run_generic_accept_exit" not in gate_src
    assert "_run_generic_replace_exit" not in gate_src


def test_bj63_fem_assembly_gate_delegators_collapsed() -> None:
    """Cycle BJ-63: FEM assembly gate delegators removed; exit stacks call owner directly."""
    import game.final_emission_fem_assembly as fa
    import game.final_emission_gate as feg

    for name in (
        "_build_gate_accept_fem_base",
        "_build_gate_replace_fem_base",
        "_merge_gate_layer_metas_into_fem",
    ):
        assert not hasattr(feg, name), name
    for name in (
        "build_gate_accept_fem_base",
        "build_gate_replace_fem_base",
        "merge_gate_layer_metas_into_fem",
    ):
        assert callable(getattr(fa, name, None)), name


def test_bj64_opening_rt_accept_path_promotion_gate_alias_removed() -> None:
    """BJ-64: opening RT accept-path promotion alias removed; non_strict_stack calls owner."""
    assert not hasattr(feg, "_scene_opening_rt_contract_accept_path_promotes_candidate")
    src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    assert "opening_fallback.scene_opening_rt_contract_accept_path_promotes_candidate" in src
    assert "_scene_opening_rt_contract_accept_path_promotes_candidate" not in src


def test_bj65_opening_upstream_prepare_observability_merge_gate_alias_removed() -> None:
    """BJ-65: opening upstream-prepare observability merge alias removed; stacks call response_type owner."""
    assert not hasattr(feg, "_merge_opening_upstream_prepare_attach_observability_into_response_type_debug")
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    marker = "response_type._merge_opening_upstream_prepare_attach_observability_into_response_type_debug"
    assert marker in nss_src
    assert ss_src.count(marker) == 2
    assert "feg._merge_opening_upstream_prepare_attach_observability_into_response_type_debug" not in nss_src
    assert "feg._merge_opening_upstream_prepare_attach_observability_into_response_type_debug" not in ss_src


def test_bj66_dead_opening_fallback_gate_imports_removed() -> None:
    """BJ-66: gate no longer re-exports unused opening-fallback normalization helpers."""
    gate_source = inspect.getsource(feg)
    assert "final_emission_opening_fallback" not in gate_source
    assert not hasattr(feg, "_gm_output_normalized_for_opening_context")
    assert not hasattr(feg, "_opening_curated_facts_schema_ok")


def test_bj67_stacks_response_type_enforcement_calls_owner_directly() -> None:
    """BJ-67: stacks call response_type owner directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    marker = "response_type.enforce_response_type_contract"
    assert marker in nss_src
    assert ss_src.count(marker) == 2
    assert "feg._enforce_response_type_contract" not in nss_src
    assert "feg._enforce_response_type_contract" not in ss_src


def test_bj68_response_type_enforcement_gate_delegator_removed() -> None:
    """BJ-68: gate no longer re-exports enforce_response_type_contract; harnesses call owner."""
    from tests.helpers import emission_smoke_assertions as smoke
    from tests.helpers import opening_fallback_gate_harness as ob_harness

    assert not hasattr(feg, "_enforce_response_type_contract")
    ob_src = inspect.getsource(ob_harness)
    smoke_fn_src = inspect.getsource(smoke.enforce_response_type_contract_layer)
    assert "response_type.enforce_response_type_contract" in ob_src
    assert "feg._enforce_response_type_contract" not in ob_src
    assert "final_emission_response_type" in smoke_fn_src
    assert "final_emission_gate" not in smoke_fn_src
    assert callable(getattr(response_type, "enforce_response_type_contract", None))


def test_bj86_fast_fallback_neutral_composition_layer_gate_delegator_removed() -> None:
    """BJ-86: FFNC layer gate delegator removed; stacks call owner directly."""
    assert not hasattr(feg, "_apply_fast_fallback_neutral_composition_layer")
    assert callable(getattr(fast_fallback_composition, "apply_fast_fallback_neutral_composition_layer", None))


def test_bj86_stacks_call_fast_fallback_composition_owner_directly() -> None:
    """BJ-86: strict and non-strict stacks call fast_fallback_composition owner directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "apply_fast_fallback_neutral_composition_layer(" in nss_src
    assert "apply_fast_fallback_neutral_composition_layer(" in ss_src
    assert "feg._apply_fast_fallback_neutral_composition_layer" not in nss_src
    assert "feg._apply_fast_fallback_neutral_composition_layer" not in ss_src


def test_bj87_answer_completeness_layer_gate_reexport_removed() -> None:
    """BJ-87: answer completeness layer no longer re-exported through gate."""
    import game.final_emission_repairs as emission_repairs

    assert not hasattr(feg, "_apply_answer_completeness_layer")
    assert callable(getattr(emission_repairs, "_apply_answer_completeness_layer", None))


def test_bj87_stacks_call_answer_completeness_repairs_owner_directly() -> None:
    """BJ-87: strict and non-strict stacks call final_emission_repairs answer completeness directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "_apply_answer_completeness_layer(" in nss_src
    assert "feg._apply_answer_completeness_layer" not in nss_src
    assert "emission_repairs._apply_answer_completeness_layer(" in ss_src
    assert "feg._apply_answer_completeness_layer" not in ss_src


def test_bj88_answer_exposition_plan_layer_gate_reexport_removed() -> None:
    """BJ-88: answer exposition plan layer no longer re-exported through gate."""
    import game.final_emission_repairs as emission_repairs

    assert not hasattr(feg, "_apply_answer_exposition_plan_layer")
    assert callable(getattr(emission_repairs, "_apply_answer_exposition_plan_layer", None))


def test_bj88_stacks_call_answer_exposition_plan_repairs_owner_directly() -> None:
    """BJ-88: stacks call final_emission_repairs answer exposition plan directly (3 strict-social sites)."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack)
    assert "_apply_answer_exposition_plan_layer(" in nss_src
    assert "feg._apply_answer_exposition_plan_layer" not in nss_src
    assert ss_src.count("emission_repairs._apply_answer_exposition_plan_layer(") == 3
    assert "feg._apply_answer_exposition_plan_layer" not in ss_src


def test_bj89_response_delta_layer_gate_reexport_removed() -> None:
    """BJ-89: response delta layer no longer re-exported through gate."""
    import game.final_emission_repairs as emission_repairs

    assert not hasattr(feg, "_apply_response_delta_layer")
    assert callable(getattr(emission_repairs, "_apply_response_delta_layer", None))


def test_bj89_stacks_call_response_delta_repairs_owner_directly() -> None:
    """BJ-89: strict and non-strict stacks call final_emission_repairs response delta directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "_apply_response_delta_layer(" in nss_src
    assert "feg._apply_response_delta_layer" not in nss_src
    assert "emission_repairs._apply_response_delta_layer(" in ss_src
    assert "feg._apply_response_delta_layer" not in ss_src


def test_bj90_social_response_structure_layer_gate_reexport_removed() -> None:
    """BJ-90: social response structure layer no longer re-exported through gate."""
    import game.final_emission_repairs as emission_repairs

    assert not hasattr(feg, "_apply_social_response_structure_layer")
    assert callable(getattr(emission_repairs, "_apply_social_response_structure_layer", None))


def test_bj90_stacks_call_social_response_structure_repairs_owner_directly() -> None:
    """BJ-90: strict and non-strict stacks call final_emission_repairs social response structure directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "_apply_social_response_structure_layer(" in nss_src
    assert "feg._apply_social_response_structure_layer" not in nss_src
    assert "emission_repairs._apply_social_response_structure_layer(" in ss_src
    assert "feg._apply_social_response_structure_layer" not in ss_src


def test_bj91_narrative_authenticity_layer_gate_reexport_removed() -> None:
    """BJ-91: narrative authenticity layer no longer re-exported through gate."""
    import game.final_emission_repairs as emission_repairs

    assert not hasattr(feg, "_apply_narrative_authenticity_layer")
    assert callable(getattr(emission_repairs, "_apply_narrative_authenticity_layer", None))


def test_bj91_stacks_call_narrative_authenticity_repairs_owner_directly() -> None:
    """BJ-91: strict and non-strict stacks call final_emission_repairs narrative authenticity directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "_apply_narrative_authenticity_layer(" in nss_src
    assert "feg._apply_narrative_authenticity_layer" not in nss_src
    assert "emission_repairs._apply_narrative_authenticity_layer(" in ss_src
    assert "feg._apply_narrative_authenticity_layer" not in ss_src


def test_bj92_fallback_behavior_layer_gate_reexport_removed() -> None:
    """BJ-92: fallback behavior layer no longer re-exported through gate."""
    import game.final_emission_repairs as emission_repairs

    assert not hasattr(feg, "_apply_fallback_behavior_layer")
    assert callable(getattr(emission_repairs, "_apply_fallback_behavior_layer", None))


def test_bj92_stacks_call_fallback_behavior_repairs_owner_directly() -> None:
    """BJ-92: non_strict_stack and terminal_pipeline call final_emission_repairs fallback behavior directly."""
    import game.final_emission_terminal_pipeline as terminal_pipeline

    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    tp_src = inspect.getsource(terminal_pipeline.run_gate_terminal_enforcement_pipeline)
    assert "_apply_fallback_behavior_layer(" in nss_src
    assert "feg._apply_fallback_behavior_layer" not in nss_src
    assert "_apply_fallback_behavior_layer(" in tp_src
    assert "feg._apply_fallback_behavior_layer" not in tp_src


def test_bj93_fallback_behavior_debug_merge_gate_reexports_removed() -> None:
    """BJ-93: fallback behavior debug/meta merge helpers no longer re-exported through gate."""
    import game.final_emission_repairs as emission_repairs

    assert not hasattr(feg, "_merge_fallback_behavior_into_emission_debug")
    assert not hasattr(feg, "_merge_fallback_behavior_meta")
    assert callable(getattr(emission_repairs, "merge_fallback_behavior_into_emission_debug", None))
    assert callable(getattr(emission_repairs, "_merge_fallback_behavior_meta", None))


def test_bj93_stacks_call_fallback_behavior_debug_merge_repairs_owner_directly() -> None:
    """BJ-93: non_strict_stack and terminal_pipeline call repairs fallback debug/meta merge directly."""
    import game.final_emission_terminal_pipeline as terminal_pipeline

    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    tp_src = inspect.getsource(terminal_pipeline.run_gate_terminal_enforcement_pipeline)
    assert "merge_fallback_behavior_into_emission_debug(" in nss_src
    assert "feg._merge_fallback_behavior_into_emission_debug" not in nss_src
    assert "merge_fallback_behavior_into_emission_debug(" in tp_src
    assert "feg._merge_fallback_behavior_into_emission_debug" not in tp_src
    assert "_merge_fallback_behavior_meta(" in tp_src
    assert "feg._merge_fallback_behavior_meta" not in tp_src


def test_bj94_conversational_memory_inspection_debug_merge_gate_reexport_removed() -> None:
    """BJ-94: conversational memory inspection debug merge no longer re-exported through gate."""
    import game.final_emission_repairs as emission_repairs

    assert not hasattr(feg, "_merge_conversational_memory_inspection_into_emission_debug")
    assert callable(
        getattr(emission_repairs, "merge_conversational_memory_inspection_into_emission_debug", None)
    )


def test_bj94_stacks_call_conversational_memory_inspection_debug_merge_repairs_owner_directly() -> None:
    """BJ-94: strict and non-strict stacks call repairs conversational memory debug merge directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "merge_conversational_memory_inspection_into_emission_debug(" in nss_src
    assert "feg._merge_conversational_memory_inspection_into_emission_debug" not in nss_src
    assert "emission_repairs.merge_conversational_memory_inspection_into_emission_debug(" in ss_src
    assert "feg._merge_conversational_memory_inspection_into_emission_debug" not in ss_src


def test_bj95_scene_state_anchor_emission_debug_merge_gate_reexport_removed() -> None:
    """BJ-95: scene state anchor emission_debug merge no longer re-exported through gate."""
    import game.final_emission_scene_state_anchor as scene_state_anchor

    assert not hasattr(feg, "_merge_scene_state_anchor_into_emission_debug")
    assert callable(getattr(scene_state_anchor, "_merge_scene_state_anchor_into_emission_debug", None))


def test_bj95_stacks_call_scene_state_anchor_emission_debug_merge_owner_directly() -> None:
    """BJ-95: strict and non-strict stacks call scene_state_anchor emission_debug merge directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "_merge_scene_state_anchor_into_emission_debug(" in nss_src
    assert "feg._merge_scene_state_anchor_into_emission_debug" not in nss_src
    assert "_merge_scene_state_anchor_into_emission_debug(" in ss_src
    assert "feg._merge_scene_state_anchor_into_emission_debug" not in ss_src


def test_bj96_tone_escalation_emission_debug_merge_gate_reexport_removed() -> None:
    """BJ-96: tone escalation emission_debug merge no longer re-exported through gate."""
    import game.final_emission_tone_escalation as tone_escalation

    assert not hasattr(feg, "_merge_tone_escalation_into_emission_debug")
    assert callable(getattr(tone_escalation, "merge_tone_escalation_into_emission_debug", None))


def test_bj96_stacks_call_tone_escalation_emission_debug_merge_owner_directly() -> None:
    """BJ-96: strict and non-strict stacks call tone_escalation emission_debug merge directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "_merge_tone_escalation_into_emission_debug(" in nss_src
    assert "feg._merge_tone_escalation_into_emission_debug" not in nss_src
    assert "_merge_tone_escalation_into_emission_debug(" in ss_src
    assert "feg._merge_tone_escalation_into_emission_debug" not in ss_src


def test_bj97_narrative_authority_emission_debug_merge_gate_reexport_removed() -> None:
    """BJ-97: narrative authority emission_debug merge no longer re-exported through gate."""
    import game.final_emission_narrative_authority as narrative_authority

    assert not hasattr(feg, "_merge_narrative_authority_into_emission_debug")
    assert callable(getattr(narrative_authority, "merge_narrative_authority_into_emission_debug", None))


def test_bj97_stacks_call_narrative_authority_emission_debug_merge_owner_directly() -> None:
    """BJ-97: strict and non-strict stacks call narrative_authority emission_debug merge directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "_merge_narrative_authority_into_emission_debug(" in nss_src
    assert "feg._merge_narrative_authority_into_emission_debug" not in nss_src
    assert "_merge_narrative_authority_into_emission_debug(" in ss_src
    assert "feg._merge_narrative_authority_into_emission_debug" not in ss_src


def test_bj98_anti_railroading_emission_debug_merge_gate_reexport_removed() -> None:
    """BJ-98: anti-railroading emission_debug merge no longer re-exported through gate."""
    import game.final_emission_anti_railroading as anti_railroading

    assert not hasattr(feg, "_merge_anti_railroading_into_emission_debug")
    assert callable(getattr(anti_railroading, "merge_anti_railroading_into_emission_debug", None))


def test_bj98_stacks_call_anti_railroading_emission_debug_merge_owner_directly() -> None:
    """BJ-98: strict and non-strict stacks call anti_railroading emission_debug merge directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "_merge_anti_railroading_into_emission_debug(" in nss_src
    assert "feg._merge_anti_railroading_into_emission_debug" not in nss_src
    assert "_merge_anti_railroading_into_emission_debug(" in ss_src
    assert "feg._merge_anti_railroading_into_emission_debug" not in ss_src


def test_bj99_context_separation_emission_debug_merge_gate_reexport_removed() -> None:
    """BJ-99: context separation emission_debug merge no longer re-exported through gate."""
    import game.final_emission_context_separation as context_separation

    assert not hasattr(feg, "_merge_context_separation_into_emission_debug")
    assert callable(getattr(context_separation, "merge_context_separation_into_emission_debug", None))


def test_bj99_stacks_call_context_separation_emission_debug_merge_owner_directly() -> None:
    """BJ-99: strict and non-strict stacks call context_separation emission_debug merge directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "_merge_context_separation_into_emission_debug(" in nss_src
    assert "feg._merge_context_separation_into_emission_debug" not in nss_src
    assert "_merge_context_separation_into_emission_debug(" in ss_src
    assert "feg._merge_context_separation_into_emission_debug" not in ss_src


def test_bj100_narration_purity_emission_debug_merge_gate_reexport_removed() -> None:
    """BJ-100: narration purity emission_debug merge no longer re-exported through gate."""
    import game.final_emission_player_facing_narration_purity as narration_purity

    assert not hasattr(feg, "_merge_player_facing_narration_purity_into_emission_debug")
    assert callable(
        getattr(narration_purity, "merge_player_facing_narration_purity_into_emission_debug", None)
    )


def test_bj100_stacks_call_narration_purity_emission_debug_merge_owner_directly() -> None:
    """BJ-100: strict and non-strict stacks call narration_purity emission_debug merge directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "_merge_player_facing_narration_purity_into_emission_debug(" in nss_src
    assert "feg._merge_player_facing_narration_purity_into_emission_debug" not in nss_src
    assert "_merge_player_facing_narration_purity_into_emission_debug(" in ss_src
    assert "feg._merge_player_facing_narration_purity_into_emission_debug" not in ss_src


def test_bj101_answer_shape_primacy_emission_debug_merge_gate_reexport_removed() -> None:
    """BJ-101: answer-shape primacy emission_debug merge no longer re-exported through gate."""
    import game.final_emission_answer_shape_primacy as answer_shape_primacy

    assert not hasattr(feg, "_merge_answer_shape_primacy_into_emission_debug")
    assert callable(getattr(answer_shape_primacy, "merge_answer_shape_primacy_into_emission_debug", None))


def test_bj101_stacks_call_answer_shape_primacy_emission_debug_merge_owner_directly() -> None:
    """BJ-101: strict and non-strict stacks call answer_shape_primacy emission_debug merge directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "_merge_answer_shape_primacy_into_emission_debug(" in nss_src
    assert "feg._merge_answer_shape_primacy_into_emission_debug" not in nss_src
    assert "_merge_answer_shape_primacy_into_emission_debug(" in ss_src
    assert "feg._merge_answer_shape_primacy_into_emission_debug" not in ss_src


def test_bj102_tone_escalation_pregate_flag_gate_reexport_removed() -> None:
    """BJ-102: non-hostile escalation pregate flag no longer re-exported through gate."""
    import game.final_emission_tone_escalation as tone_escalation

    assert not hasattr(feg, "_flag_non_hostile_escalation_from_writer_pregate")
    assert callable(getattr(tone_escalation, "flag_non_hostile_escalation_from_writer_pregate", None))


def test_bj102_strict_social_stack_calls_tone_escalation_pregate_flag_owner_directly() -> None:
    """BJ-102: strict_social_stack calls tone_escalation pregate flag owner directly."""
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "flag_non_hostile_escalation_from_writer_pregate(" in ss_src
    assert "feg._flag_non_hostile_escalation_from_writer_pregate" not in ss_src


def test_bj103_scene_emit_integrity_assessment_gate_reexport_removed() -> None:
    """BJ-103: scene emit integrity assessment no longer re-exported through gate."""
    import game.final_emission_scene_emit_integrity as scene_emit_integrity

    assert not hasattr(feg, "_compute_scene_emit_integrity_assessment")
    assert callable(getattr(scene_emit_integrity, "_compute_scene_emit_integrity_assessment", None))


def test_bj103_stacks_call_scene_emit_integrity_assessment_owner_directly() -> None:
    """BJ-103: strict and non-strict stacks call scene_emit_integrity assessment owner directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "_compute_scene_emit_integrity_assessment(" in nss_src
    assert "feg._compute_scene_emit_integrity_assessment" not in nss_src
    assert "_compute_scene_emit_integrity_assessment(" in ss_src
    assert "feg._compute_scene_emit_integrity_assessment" not in ss_src


def test_bj104_passive_scene_pressure_due_check_gate_reexport_removed() -> None:
    """BJ-104: passive scene pressure due-check no longer re-exported through gate."""
    import game.final_emission_passive_scene_pressure as passive_scene_pressure

    assert not hasattr(feg, "_passive_scene_pressure_due_for_fallback")
    assert callable(getattr(passive_scene_pressure, "_passive_scene_pressure_due_for_fallback", None))


def test_bj104_non_strict_stack_calls_passive_scene_pressure_due_check_owner_directly() -> None:
    """BJ-104: non_strict_stack calls passive_scene_pressure due-check owner directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    assert "_passive_scene_pressure_due_for_fallback(" in nss_src
    assert "feg._passive_scene_pressure_due_for_fallback" not in nss_src


def test_bj105_narrative_mode_output_assessment_gate_reexport_removed() -> None:
    """BJ-105: narrative mode output legality assessment no longer re-exported through gate."""
    import game.final_emission_narrative_mode_output as narrative_mode_output

    assert not hasattr(feg, "_narrative_mode_output_legality_assessment")
    assert callable(getattr(narrative_mode_output, "_narrative_mode_output_legality_assessment", None))


def test_bj105_non_strict_stack_calls_narrative_mode_output_assessment_owner_directly() -> None:
    """BJ-105: non_strict_stack calls narrative_mode_output assessment owner directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    assert "_narrative_mode_output_legality_assessment(" in nss_src
    assert "feg._narrative_mode_output_legality_assessment" not in nss_src


def test_bj106_response_type_decision_payload_gate_reexport_removed() -> None:
    """BJ-106: response_type decision payload no longer re-exported through gate."""
    import game.final_emission_meta as emission_meta

    assert not hasattr(feg, "_response_type_decision_payload")
    assert callable(getattr(emission_meta, "response_type_decision_payload", None))


def test_bj106_callers_use_response_type_decision_payload_owner_directly() -> None:
    """BJ-106: strict_social_stack and generic_exit call meta response_type_decision_payload directly."""
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    ge_accept_src = inspect.getsource(generic_exit.run_generic_accept_exit)
    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    assert "response_type_decision_payload(" in ss_src
    assert "feg._response_type_decision_payload" not in ss_src
    assert "response_type_decision_payload(" in ge_accept_src
    assert "feg._response_type_decision_payload" not in ge_accept_src
    assert "response_type_decision_payload(" in ge_replace_src
    assert "feg._response_type_decision_payload" not in ge_replace_src


def test_bj107_infer_accept_path_final_emitted_source_gate_reexport_removed() -> None:
    """BJ-107: accept-path final_emitted_source inference no longer re-exported through gate."""
    import game.final_emission_meta as emission_meta

    assert not hasattr(feg, "infer_accept_path_final_emitted_source")
    assert callable(getattr(emission_meta, "infer_accept_path_final_emitted_source", None))


def test_bj107_callers_use_infer_accept_path_final_emitted_source_owner_directly() -> None:
    """BJ-107: strict_social_stack and generic_exit call meta infer_accept_path_final_emitted_source directly."""
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    ge_accept_src = inspect.getsource(generic_exit.run_generic_accept_exit)
    assert "infer_accept_path_final_emitted_source(" in ss_src
    assert "feg.infer_accept_path_final_emitted_source" not in ss_src
    assert "infer_accept_path_final_emitted_source(" in ge_accept_src
    assert "feg.infer_accept_path_final_emitted_source" not in ge_accept_src


def test_bj108_opening_fallback_projection_gate_reexports_removed() -> None:
    """BJ-108: opening fallback projection helpers no longer re-exported through gate."""
    import game.final_emission_meta as emission_meta

    assert not hasattr(feg, "apply_opening_fallback_projection_fields")
    assert not hasattr(feg, "OPENING_FALLBACK_SELECTOR_DEBUG_FIELDS")
    assert callable(getattr(emission_meta, "apply_opening_fallback_projection_fields", None))
    assert hasattr(emission_meta, "OPENING_FALLBACK_SELECTOR_DEBUG_FIELDS")


def test_bj108_generic_exit_uses_opening_fallback_projection_owner_directly() -> None:
    """BJ-108: generic_exit calls meta opening fallback projection helpers directly."""
    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    assert "apply_opening_fallback_projection_fields(" in ge_replace_src
    assert "feg.apply_opening_fallback_projection_fields" not in ge_replace_src
    assert "OPENING_FALLBACK_SELECTOR_DEBUG_FIELDS" in ge_replace_src
    assert "feg.OPENING_FALLBACK_SELECTOR_DEBUG_FIELDS" not in ge_replace_src


def test_bj109_final_emission_meta_key_gate_reexport_removed() -> None:
    """BJ-109: FINAL_EMISSION_META_KEY no longer re-exported through gate."""
    import game.final_emission_meta as emission_meta

    assert not hasattr(feg, "FINAL_EMISSION_META_KEY")
    assert hasattr(emission_meta, "FINAL_EMISSION_META_KEY")
    assert emission_meta.FINAL_EMISSION_META_KEY == "_final_emission_meta"


def test_bj109_callers_use_final_emission_meta_key_owner_directly() -> None:
    """BJ-109: generic_exit and strict_social_stack use meta FINAL_EMISSION_META_KEY directly."""
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    ge_accept_src = inspect.getsource(generic_exit.run_generic_accept_exit)
    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    assert "FINAL_EMISSION_META_KEY" in ss_src
    assert "feg.FINAL_EMISSION_META_KEY" not in ss_src
    assert "FINAL_EMISSION_META_KEY" in ge_accept_src
    assert "feg.FINAL_EMISSION_META_KEY" not in ge_accept_src
    assert "FINAL_EMISSION_META_KEY" in ge_replace_src
    assert "feg.FINAL_EMISSION_META_KEY" not in ge_replace_src


def test_bj110_assert_final_emission_mutation_allowed_gate_reexport_removed() -> None:
    """BJ-110: boundary mutation assertion no longer re-exported through gate."""
    import game.final_emission_boundary_contract as boundary_contract

    assert not hasattr(feg, "assert_final_emission_mutation_allowed")
    assert callable(getattr(boundary_contract, "assert_final_emission_mutation_allowed", None))


def test_bj110_generic_exit_calls_assert_final_emission_mutation_allowed_owner_directly() -> None:
    """BJ-110: generic_exit calls boundary_contract mutation assertion owner directly."""
    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    assert "assert_final_emission_mutation_allowed(" in ge_replace_src
    assert "feg.assert_final_emission_mutation_allowed" not in ge_replace_src


def test_bj111_normalize_text_gate_reexport_removed() -> None:
    """BJ-111: _normalize_text no longer re-exported through gate."""
    import game.final_emission_text as emission_text

    assert not hasattr(feg, "_normalize_text")
    assert callable(getattr(emission_text, "_normalize_text", None))


def test_bj111_callers_use_normalize_text_owner_directly() -> None:
    """BJ-111: stack/exit callers use final_emission_text._normalize_text directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    ge_accept_src = inspect.getsource(generic_exit.run_generic_accept_exit)
    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    assert "_normalize_text(" in nss_src
    assert "feg._normalize_text(" not in nss_src
    assert "_normalize_text(" in ss_src
    assert "feg._normalize_text(" not in ss_src
    assert "_normalize_text(" in ge_accept_src
    assert "feg._normalize_text(" not in ge_accept_src
    assert "_normalize_text(" in ge_replace_src
    assert "feg._normalize_text(" not in ge_replace_src


def test_bj112_normalize_text_preserve_paragraphs_gate_reexport_removed() -> None:
    """BJ-112: _normalize_text_preserve_paragraphs no longer re-exported through gate."""
    import game.final_emission_text as emission_text

    assert not hasattr(feg, "_normalize_text_preserve_paragraphs")
    assert callable(getattr(emission_text, "_normalize_text_preserve_paragraphs", None))


def test_bj112_strict_social_stack_calls_normalize_text_preserve_paragraphs_owner_directly() -> None:
    """BJ-112: strict_social_stack calls final_emission_text._normalize_text_preserve_paragraphs directly."""
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "_normalize_text_preserve_paragraphs(" in ss_src
    assert "feg._normalize_text_preserve_paragraphs" not in ss_src


def test_bj113_diegetic_classified_fallback_meta_gate_reexport_removed() -> None:
    """BJ-113: diegetic_classified_fallback_meta no longer re-exported through gate."""
    import game.diegetic_fallback_narration as diegetic_fallback_narration

    assert not hasattr(feg, "diegetic_classified_fallback_meta")
    assert callable(getattr(diegetic_fallback_narration, "fallback_template_metadata", None))


def test_bj113_generic_exit_calls_diegetic_classified_fallback_meta_owner_directly() -> None:
    """BJ-113: generic_exit calls diegetic_fallback_narration fallback metadata owner directly."""
    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    assert "diegetic_classified_fallback_meta(" in ge_replace_src
    assert "feg.diegetic_classified_fallback_meta" not in ge_replace_src


def test_bj114_anti_reset_suppresses_intro_style_fallbacks_gate_reexport_removed() -> None:
    """BJ-114: anti_reset_suppresses_intro_style_fallbacks no longer re-exported through gate."""
    import game.anti_reset_emission_guard as anti_reset_emission_guard

    assert not hasattr(feg, "anti_reset_suppresses_intro_style_fallbacks")
    assert callable(getattr(anti_reset_emission_guard, "anti_reset_suppresses_intro_style_fallbacks", None))


def test_bj114_generic_exit_calls_anti_reset_suppresses_intro_style_fallbacks_owner_directly() -> None:
    """BJ-114: generic_exit calls anti_reset_emission_guard intro suppression owner directly."""
    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    assert "anti_reset_suppresses_intro_style_fallbacks(" in ge_replace_src
    assert "feg.anti_reset_suppresses_intro_style_fallbacks" not in ge_replace_src


def test_bj115_log_final_emission_logging_gate_reexports_removed() -> None:
    """BJ-115: final emission logging helpers no longer re-exported through gate."""
    import game.social_exchange_emission as social_exchange_emission

    assert not hasattr(feg, "log_final_emission_decision")
    assert not hasattr(feg, "log_final_emission_trace")
    assert callable(getattr(social_exchange_emission, "log_final_emission_decision", None))
    assert callable(getattr(social_exchange_emission, "log_final_emission_trace", None))


def test_bj115_stacks_call_log_final_emission_logging_owners_directly() -> None:
    """BJ-115: generic_exit and strict_social_stack call social_exchange_emission logging owners directly."""
    ge_accept_src = inspect.getsource(generic_exit.run_generic_accept_exit)
    ge_replace_src = inspect.getsource(generic_exit.run_generic_replace_exit)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "log_final_emission_decision(" in ge_accept_src
    assert "log_final_emission_trace(" in ge_accept_src
    assert "feg.log_final_emission_decision" not in ge_accept_src
    assert "feg.log_final_emission_trace" not in ge_accept_src
    assert "log_final_emission_decision(" in ge_replace_src
    assert "log_final_emission_trace(" in ge_replace_src
    assert "feg.log_final_emission_decision" not in ge_replace_src
    assert "feg.log_final_emission_trace" not in ge_replace_src
    assert "log_final_emission_decision(" in ss_src
    assert "log_final_emission_trace(" in ss_src
    assert "feg.log_final_emission_decision" not in ss_src
    assert "feg.log_final_emission_trace" not in ss_src


def test_bj116_strict_social_social_exchange_gate_reexports_removed() -> None:
    """BJ-116: strict-social social exchange helpers no longer re-exported through gate."""
    import game.social_exchange_emission as social_exchange_emission

    assert not hasattr(feg, "build_final_strict_social_response")
    assert not hasattr(feg, "minimal_social_emergency_fallback_line")
    assert not hasattr(feg, "strict_social_deterministic_fallback_family_token")
    assert callable(getattr(social_exchange_emission, "build_final_strict_social_response", None))
    assert callable(getattr(social_exchange_emission, "minimal_social_emergency_fallback_line", None))
    assert callable(getattr(social_exchange_emission, "strict_social_deterministic_fallback_family_token", None))


def test_bj116_strict_social_stack_calls_social_exchange_owners_directly() -> None:
    """BJ-116: strict_social_stack calls social_exchange_emission strict-social owners directly."""
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "build_final_strict_social_response(" in ss_src
    assert "minimal_social_emergency_fallback_line(" in ss_src
    assert "strict_social_deterministic_fallback_family_token(" in ss_src
    assert "feg.build_final_strict_social_response" not in ss_src
    assert "feg.minimal_social_emergency_fallback_line" not in ss_src
    assert "feg.strict_social_deterministic_fallback_family_token" not in ss_src


def test_bj117_telemetry_provenance_gate_reexports_removed() -> None:
    """BJ-117: telemetry/provenance helpers no longer re-exported through gate."""
    import game.fallback_provenance_debug as fallback_provenance_debug
    import game.stage_diff_telemetry as stage_diff_telemetry

    assert not hasattr(feg, "record_stage_snapshot")
    assert not hasattr(feg, "realign_fallback_provenance_selector_to_current_text")
    assert callable(getattr(stage_diff_telemetry, "record_stage_snapshot", None))
    assert callable(getattr(fallback_provenance_debug, "realign_fallback_provenance_selector_to_current_text", None))


def test_bj117_strict_social_stack_calls_telemetry_provenance_owners_directly() -> None:
    """BJ-117: strict_social_stack calls stage_diff and fallback_provenance owners directly."""
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "record_stage_snapshot(" in ss_src
    assert "realign_fallback_provenance_selector_to_current_text(" in ss_src
    assert "feg.record_stage_snapshot" not in ss_src
    assert "feg.realign_fallback_provenance_selector_to_current_text" not in ss_src


def test_bj118_should_replace_candidate_intro_fallback_gate_reexport_removed() -> None:
    """BJ-118: should_replace_candidate_intro_fallback no longer re-exported through gate."""
    import game.anti_reset_emission_guard as anti_reset_emission_guard

    assert not hasattr(feg, "should_replace_candidate_intro_fallback")
    assert callable(getattr(anti_reset_emission_guard, "should_replace_candidate_intro_fallback", None))


def test_bj119_stage_diff_telemetry_gate_reexports_removed() -> None:
    """BJ-119: stage_diff_telemetry helpers no longer re-exported through gate."""
    import game.stage_diff_telemetry as stage_diff_telemetry

    assert not hasattr(feg, "diff_turn_stage")
    assert not hasattr(feg, "record_stage_transition")
    assert not hasattr(feg, "snapshot_turn_stage")
    assert callable(getattr(stage_diff_telemetry, "diff_turn_stage", None))
    assert callable(getattr(stage_diff_telemetry, "record_stage_transition", None))
    assert callable(getattr(stage_diff_telemetry, "snapshot_turn_stage", None))


def test_bj120_harness_patches_canonical_owner_seams() -> None:
    """BJ-120: harness helpers patch owner/stack seams, not removed gate re-exports."""
    import tests.helpers.gate_equivalence_monkeypatch as gate_mp
    import tests.test_turn_packet_stage_diff_integration as tp_stage_diff

    mp_src = inspect.getsource(gate_mp.patch_build_final_strict_social_response)
    assert 'monkeypatch.setattr(strict_social_stack, "build_final_strict_social_response"' in mp_src
    assert 'monkeypatch.setattr(feg, "build_final_strict_social_response"' not in mp_src
    tp_src = inspect.getsource(tp_stage_diff.test_gate_exit_records_observability_before_cache_pop)
    assert 'monkeypatch.setattr(emission_finalize, "record_stage_snapshot"' in tp_src
    assert 'monkeypatch.setattr(feg, "record_stage_snapshot"' not in tp_src
    assert "import game.final_emission_gate as feg" not in inspect.getsource(tp_stage_diff)


def test_bj121_strict_social_build_patches_use_stack_seam_not_gate() -> None:
    """BJ-121: strict-social build monkeypatches target strict_social_stack, not gate re-exports."""
    import pathlib

    import tests.helpers.strict_social_harness as strict_social_harness

    harness_src = inspect.getsource(strict_social_harness.run_strict_social_motive_overclaim_gate_case)
    assert 'monkeypatch.setattr(strict_social_stack, "build_final_strict_social_response"' in harness_src
    assert 'monkeypatch.setattr(feg, "build_final_strict_social_response"' not in harness_src

    repo_root = pathlib.Path(__file__).resolve().parents[1]
    audited = [
        repo_root / "tests/test_fallback_behavior_gate.py",
        repo_root / "tests/test_scene_state_anchoring.py",
        repo_root / "tests/test_final_emission_boundary_convergence.py",
        repo_root / "tests/test_speaker_contract_enforcement.py",
        repo_root / "tests/test_social_exchange_emission.py",
        repo_root / "tests/test_prompt_context.py",
        repo_root / "tests/test_c4_narrative_mode_live_pipeline.py",
        repo_root / "tests/helpers/gate_equivalence_monkeypatch.py",
        repo_root / "tests/helpers/strict_social_harness.py",
    ]
    stale = 'monkeypatch.setattr(feg, "build_final_strict_social_response"'
    stale_module = 'monkeypatch.setattr(feg_module, "build_final_strict_social_response"'
    for path in audited:
        text = path.read_text(encoding="utf-8")
        assert stale not in text, f"{path.name} still patches gate build seam"
        assert stale_module not in text, f"{path.name} still patches gate build seam via feg_module"


def test_bj122_scene_state_anchoring_tests_use_ssa_owner_bindings_not_gate() -> None:
    """BJ-122: scene_state_anchoring tests patch/read SSA owner bindings, not removed gate re-exports."""
    import tests.test_scene_state_anchoring as scene_state_anchoring_tests

    module_src = inspect.getsource(scene_state_anchoring_tests)
    assert "import game.final_emission_gate as feg" not in module_src
    assert 'monkeypatch.setattr(feg, "_repair_location_opening"' not in module_src
    assert 'monkeypatch.setattr(feg, "validate_scene_state_anchoring"' not in module_src
    assert "feg._resolve_scene_state_anchor_contract" not in module_src
    assert "feg._merge_scene_state_anchor_meta" not in module_src

    repair_src = inspect.getsource(scene_state_anchoring_tests.test_scene_state_anchor_narrator_neutral_only_when_location_rebind_unavailable)
    validate_src = inspect.getsource(scene_state_anchoring_tests.test_validate_scene_state_anchoring_invoked_once_without_boundary_repair)
    resolve_src = inspect.getsource(scene_state_anchoring_tests.test_contract_resolution_from_gm_output_nested_paths)
    assert 'monkeypatch.setattr(scene_state_anchor_owner, "_repair_location_opening"' in repair_src
    assert 'monkeypatch.setattr(scene_state_anchor_owner, "validate_scene_state_anchoring"' in validate_src
    assert "scene_state_anchor_owner._resolve_scene_state_anchor_contract(" in resolve_src


def test_bj72_gate_context_initialization_delegator_removed() -> None:
    """BJ-72: gate context initialization delegator removed; apply_final_emission_gate calls owner directly."""
    assert not hasattr(feg, "_initialize_gate_execution_context")
    assert callable(getattr(gate_context, "initialize_gate_execution_context", None))


def test_bj72_apply_final_emission_gate_calls_gate_context_owner_directly() -> None:
    """BJ-72: gate orchestration calls gate_context owner directly."""
    gate_src = inspect.getsource(feg.apply_final_emission_gate)
    assert "initialize_gate_execution_context(" in gate_src
    assert "_initialize_gate_execution_context" not in gate_src


def test_bj51_gate_interaction_continuity_public_reexports_locked() -> None:
    """BJ-51/BJ-76: gate re-exports IC owner entrypoints; no gate-private IC delegators remain."""
    import game.interaction_continuity as ic

    assert feg.apply_interaction_continuity_emission_step is ic.apply_interaction_continuity_emission_step
    assert feg.attach_interaction_continuity_validation is ic.attach_interaction_continuity_validation


def test_bj52_fallback_provenance_gate_wrappers_removed() -> None:
    """BJ-52: upstream fallback provenance containment wrappers removed; owners call fallback_provenance_debug directly."""
    import game.fallback_provenance_debug as fpd
    import game.final_emission_finalize as fin
    import game.final_emission_gate_context as gc

    assert not hasattr(feg, "_upstream_fallback_canonical_provenance")
    assert not hasattr(feg, "_apply_upstream_fallback_pregate_containment")
    assert not hasattr(feg, "_finalize_upstream_fallback_overwrite_containment")
    assert callable(getattr(fpd, "upstream_fallback_canonical_provenance", None))
    assert callable(getattr(fpd, "apply_upstream_fallback_pregate_containment", None))
    assert callable(getattr(fpd, "finalize_upstream_fallback_overwrite_containment", None))
    assert callable(getattr(gc, "apply_upstream_fallback_pregate_containment", None))
    assert callable(getattr(fin, "finalize_upstream_fallback_overwrite_containment", None))


def test_bj53_referent_clarity_pre_finalize_gate_wrapper_removed() -> None:
    """BJ-53: referent pre-finalize wrapper removed; terminal pipeline owner calls repairs layer directly."""
    assert not hasattr(feg, "_apply_referent_clarity_pre_finalize")
    assert callable(getattr(terminal_pipeline, "_apply_referent_clarity_pre_finalize", None))


def test_bj54_narration_constraint_debug_merge_gate_wrapper_removed() -> None:
    """BJ-54: narration-constraint debug merge wrapper removed; terminal pipeline owner merges directly."""
    assert not hasattr(feg, "_merge_narration_constraint_debug_into_outputs")
    assert callable(getattr(terminal_pipeline, "_merge_narration_constraint_debug_into_outputs", None))


def test_bj55_gate_fem_text_fingerprint_helper_removed() -> None:
    """BJ-55: dead gate FEM fingerprint helper removed; terminal pipeline owns _patch_fem_text_fingerprint."""
    assert not hasattr(feg, "_patch_gate_fem_text_fingerprint")
    assert callable(getattr(terminal_pipeline, "_patch_fem_text_fingerprint", None))


def test_bj56_scene_opening_finalize_delegators_removed() -> None:
    """BJ-56: scene-opening finalize wrappers removed; finalize owner and non_strict_stack call directly."""
    assert not hasattr(feg, "_patch_scene_opening_candidate_emission_debug")
    assert not hasattr(feg, "_reassert_scene_opening_accepted_candidate")
    assert callable(getattr(emission_finalize, "patch_scene_opening_candidate_emission_debug", None))
    assert callable(getattr(emission_finalize, "reassert_scene_opening_accepted_candidate", None))


def test_bj57_strip_appended_route_illegal_contamination_sentences_gate_wrapper_removed() -> None:
    """BJ-57: route-illegal strip wrapper removed; finalize owner owns strip helper."""
    assert not hasattr(feg, "_strip_appended_route_illegal_contamination_sentences")
    assert callable(getattr(emission_finalize, "strip_appended_route_illegal_contamination_sentences", None))


def test_bj58_contract_resolver_gate_delegators_removed() -> None:
    """BJ-58: contract resolver wrappers removed; tone/authority owners resolve directly."""
    assert not hasattr(feg, "_resolve_tone_escalation_contract")
    assert not hasattr(feg, "_resolve_narrative_authority_contract")
    assert callable(getattr(tone_escalation, "resolve_tone_escalation_contract", None))
    assert callable(getattr(narrative_authority, "resolve_narrative_authority_contract", None))


def test_bj59_dialogue_social_plan_gate_delegators_removed() -> None:
    """BJ-59: dialogue-plan helpers removed from gate; strict-social stack calls dialogue_social_plan directly."""
    assert not hasattr(feg, "_enforce_dialogue_plan_invariant_on_strict_social")
    assert not hasattr(feg, "_strip_dialogue_from_text")
    assert not hasattr(feg, "_strict_social_line_matches_terminal_emission_pool")
    assert not hasattr(feg, "_is_bare_speech_attribution_shell_line")
    assert callable(getattr(dialogue_social_plan, "enforce_dialogue_plan_invariant_on_strict_social", None))
    assert callable(getattr(dialogue_social_plan, "strip_dialogue_from_text", None))
    assert callable(getattr(dialogue_social_plan, "strict_social_line_matches_terminal_emission_pool", None))
    assert callable(getattr(dialogue_social_plan, "is_bare_speech_attribution_shell_line", None))


def test_bj60_sealed_fallback_selector_gate_delegator_removed() -> None:
    """BJ-60: non-strict sealed selector wrapper removed; generic exit calls sealed_fallback owner."""
    assert not hasattr(feg, "_select_non_strict_replace_path_terminal_sealed_fallback_selection")
    assert callable(getattr(sealed_fallback, "select_non_strict_replace_path_terminal_sealed_fallback_selection", None))


def test_bj73_visibility_enforcement_gate_delegator_removed() -> None:
    """BJ-73: visibility enforcement gate delegator removed; terminal pipeline calls owner directly."""
    assert not hasattr(feg, "_apply_visibility_enforcement")
    assert callable(getattr(visibility_fallback, "apply_visibility_enforcement", None))


def test_bj73_terminal_pipeline_calls_visibility_owner_directly() -> None:
    """BJ-73: terminal pipeline calls visibility_fallback owner directly."""
    tp_src = inspect.getsource(terminal_pipeline.run_gate_terminal_enforcement_pipeline)
    assert "apply_visibility_enforcement(" in tp_src
    assert "feg._apply_visibility_enforcement" not in tp_src
    assert "_apply_visibility_enforcement" not in tp_src


def test_bj74_n4_floor_seam_gate_delegator_removed() -> None:
    """BJ-74: N4 floor seam gate delegator removed; terminal pipeline calls owner directly."""
    assert not hasattr(feg, "_apply_acceptance_quality_n4_floor_seam")
    assert callable(getattr(acceptance_quality_gate, "apply_acceptance_quality_n4_floor_seam", None))


def test_bj74_terminal_pipeline_calls_n4_floor_seam_owner_directly() -> None:
    """BJ-74: terminal pipeline calls acceptance_quality owner directly."""
    tp_src = inspect.getsource(terminal_pipeline.run_gate_terminal_enforcement_pipeline)
    assert "apply_acceptance_quality_n4_floor_seam(" in tp_src
    assert "feg._apply_acceptance_quality_n4_floor_seam" not in tp_src


def test_bj75_interaction_continuity_attach_gate_delegator_removed() -> None:
    """BJ-75: IC validation attach gate delegator removed; terminal pipeline calls owner directly."""
    import game.interaction_continuity as ic

    assert not hasattr(feg, "_attach_interaction_continuity_validation")
    assert callable(getattr(ic, "attach_interaction_continuity_validation", None))


def test_bj75_terminal_pipeline_calls_ic_attach_owner_directly() -> None:
    """BJ-75: terminal pipeline calls interaction_continuity attach owner directly."""
    tp_src = inspect.getsource(terminal_pipeline.run_gate_terminal_enforcement_pipeline)
    assert "attach_interaction_continuity_validation(" in tp_src
    assert "feg._attach_interaction_continuity_validation" not in tp_src


def test_bj76_interaction_continuity_emission_step_gate_delegator_removed() -> None:
    """BJ-76: IC emission-step gate delegator removed; stacks call interaction_continuity owner directly."""
    import game.interaction_continuity as ic

    assert not hasattr(feg, "_apply_interaction_continuity_emission_step")
    assert callable(getattr(ic, "apply_interaction_continuity_emission_step", None))


def test_bj76_terminal_pipeline_calls_ic_emission_step_owner_directly() -> None:
    """BJ-76: terminal pipeline calls interaction_continuity emission step owner directly."""
    tp_src = inspect.getsource(terminal_pipeline.run_gate_terminal_enforcement_pipeline)
    assert "apply_interaction_continuity_emission_step(" in tp_src
    assert "feg._apply_interaction_continuity_emission_step" not in tp_src


def test_bj76_non_strict_stack_calls_ic_emission_step_owner_directly() -> None:
    """BJ-76: non_strict_stack calls interaction_continuity emission step owner directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    assert "apply_interaction_continuity_emission_step(" in nss_src
    assert "feg._apply_interaction_continuity_emission_step" not in nss_src


def test_bj77_speaker_contract_gate_delegator_removed() -> None:
    """BJ-77: speaker-contract gate delegator removed; strict_social_stack calls owner directly."""
    import game.speaker_contract_enforcement as sce

    assert not hasattr(feg, "enforce_emitted_speaker_with_contract")
    assert callable(getattr(sce, "enforce_emitted_speaker_with_contract", None))


def test_bj77_strict_social_stack_calls_speaker_enforcement_owner_directly() -> None:
    """BJ-77: strict_social_stack calls speaker_contract_enforcement owner directly."""
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "enforce_emitted_speaker_with_contract(" in ss_src
    assert "feg.enforce_emitted_speaker_with_contract" not in ss_src


def test_bj78_sync_eff_social_gate_reexport_removed() -> None:
    """BJ-78: strict-social sync no longer resolves through gate re-export."""
    import game.speaker_contract_enforcement as sce

    assert not hasattr(feg, "_sync_eff_social_to_resolution")
    assert callable(getattr(sce, "_sync_eff_social_to_resolution", None))


def test_bj78_strict_social_stack_calls_sync_owner_directly() -> None:
    """BJ-78: strict_social_stack calls speaker_contract_enforcement sync owner directly."""
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "_sync_eff_social_to_resolution(" in ss_src
    assert "feg._sync_eff_social_to_resolution" not in ss_src


def test_bj79_tone_escalation_layer_gate_delegator_removed() -> None:
    """BJ-79: tone escalation layer gate delegator removed; stacks call owner directly."""
    assert not hasattr(feg, "_apply_tone_escalation_layer")
    assert callable(getattr(tone_escalation, "apply_tone_escalation_layer", None))


def test_bj79_stacks_call_tone_escalation_owner_directly() -> None:
    """BJ-79: strict and non-strict stacks call tone_escalation owner directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "apply_tone_escalation_layer(" in nss_src
    assert "apply_tone_escalation_layer(" in ss_src
    assert "feg._apply_tone_escalation_layer" not in nss_src
    assert "feg._apply_tone_escalation_layer" not in ss_src


def test_bj80_narrative_authority_layer_gate_delegator_removed() -> None:
    """BJ-80: narrative authority layer gate delegator removed; stacks call owner directly."""
    import game.final_emission_narrative_authority as narrative_authority

    assert not hasattr(feg, "_apply_narrative_authority_layer")
    assert callable(getattr(narrative_authority, "apply_narrative_authority_layer", None))


def test_bj80_stacks_call_narrative_authority_owner_directly() -> None:
    """BJ-80: strict and non-strict stacks call narrative_authority owner directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "apply_narrative_authority_layer(" in nss_src
    assert "apply_narrative_authority_layer(" in ss_src
    assert "feg._apply_narrative_authority_layer" not in nss_src
    assert "feg._apply_narrative_authority_layer" not in ss_src


def test_bj81_anti_railroading_layer_gate_delegator_removed() -> None:
    """BJ-81: anti-railroading layer gate delegator removed; stacks call owner directly."""
    import game.final_emission_anti_railroading as anti_railroading

    assert not hasattr(feg, "_apply_anti_railroading_layer")
    assert callable(getattr(anti_railroading, "apply_anti_railroading_layer", None))


def test_bj81_stacks_call_anti_railroading_owner_directly() -> None:
    """BJ-81: strict and non-strict stacks call anti_railroading owner directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "apply_anti_railroading_layer(" in nss_src
    assert "apply_anti_railroading_layer(" in ss_src
    assert "feg._apply_anti_railroading_layer" not in nss_src
    assert "feg._apply_anti_railroading_layer" not in ss_src


def test_bj82_context_separation_layer_gate_delegator_removed() -> None:
    """BJ-82: context separation layer gate delegator removed; stacks call owner directly."""
    import game.final_emission_context_separation as context_separation

    assert not hasattr(feg, "_apply_context_separation_layer")
    assert callable(getattr(context_separation, "apply_context_separation_layer", None))


def test_bj82_stacks_call_context_separation_owner_directly() -> None:
    """BJ-82: strict and non-strict stacks call context_separation owner directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "apply_context_separation_layer(" in nss_src
    assert "apply_context_separation_layer(" in ss_src
    assert "feg._apply_context_separation_layer" not in nss_src
    assert "feg._apply_context_separation_layer" not in ss_src


def test_bj83_player_facing_narration_purity_layer_gate_delegator_removed() -> None:
    """BJ-83: narration purity layer gate delegator removed; stacks call owner directly."""
    import game.final_emission_player_facing_narration_purity as narration_purity

    assert not hasattr(feg, "_apply_player_facing_narration_purity_layer")
    assert callable(getattr(narration_purity, "apply_player_facing_narration_purity_layer", None))


def test_bj83_stacks_call_narration_purity_owner_directly() -> None:
    """BJ-83: strict and non-strict stacks call narration_purity owner directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "apply_player_facing_narration_purity_layer(" in nss_src
    assert "apply_player_facing_narration_purity_layer(" in ss_src
    assert "feg._apply_player_facing_narration_purity_layer" not in nss_src
    assert "feg._apply_player_facing_narration_purity_layer" not in ss_src


def test_bj84_answer_shape_primacy_layer_gate_delegator_removed() -> None:
    """BJ-84: answer-shape primacy layer gate delegator removed; stacks call owner directly."""
    import game.final_emission_answer_shape_primacy as answer_shape_primacy

    assert not hasattr(feg, "_apply_answer_shape_primacy_layer")
    assert callable(getattr(answer_shape_primacy, "apply_answer_shape_primacy_layer", None))


def test_bj84_stacks_call_answer_shape_primacy_owner_directly() -> None:
    """BJ-84: strict and non-strict stacks call answer_shape_primacy owner directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "apply_answer_shape_primacy_layer(" in nss_src
    assert "apply_answer_shape_primacy_layer(" in ss_src
    assert "feg._apply_answer_shape_primacy_layer" not in nss_src
    assert "feg._apply_answer_shape_primacy_layer" not in ss_src


def test_bj85_scene_state_anchor_layer_gate_delegator_removed() -> None:
    """BJ-85: scene state anchor layer gate delegator removed; stacks call owner directly."""
    import game.final_emission_scene_state_anchor as scene_state_anchor

    assert not hasattr(feg, "_apply_scene_state_anchor_layer")
    assert callable(getattr(scene_state_anchor, "apply_scene_state_anchor_layer", None))


def test_bj85_stacks_call_scene_state_anchor_owner_directly() -> None:
    """BJ-85: strict and non-strict stacks call scene_state_anchor owner directly."""
    nss_src = inspect.getsource(non_strict_stack.run_non_strict_layer_stack)
    ss_src = inspect.getsource(strict_social_stack.run_strict_social_composition_trunk)
    assert "apply_scene_state_anchor_layer(" in nss_src
    assert "apply_scene_state_anchor_layer(" in ss_src
    assert "feg._apply_scene_state_anchor_layer" not in nss_src
    assert "feg._apply_scene_state_anchor_layer" not in ss_src


def test_bj47_merge_gate_layer_metas_into_fem_merge_order_locked(monkeypatch) -> None:
    """FEM layer-meta merges run in fixed post-AEP-second-pass order (Cycle AN2 / BJ-47)."""
    order: list[str] = []
    fem: dict[str, object] = {}
    layer_meta = {"marker": True}

    def _track(name: str, fn):
        def _wrapped(meta, dbg):
            order.append(name)
            fn(meta, dbg)

        return _wrapped

    monkeypatch.setattr(
        fem_assembly,
        "merge_response_type_meta",
        _track("response_type", fem_assembly.merge_response_type_meta),
    )
    monkeypatch.setattr(
        fem_assembly,
        "_merge_answer_completeness_meta",
        _track("ac", fem_assembly._merge_answer_completeness_meta),
    )
    monkeypatch.setattr(
        fem_assembly,
        "_merge_answer_exposition_plan_meta",
        _track("aep", fem_assembly._merge_answer_exposition_plan_meta),
    )
    monkeypatch.setattr(
        fem_assembly,
        "_merge_response_delta_meta",
        _track("rd", fem_assembly._merge_response_delta_meta),
    )
    monkeypatch.setattr(
        fem_assembly,
        "_merge_social_response_structure_meta",
        _track("srs", fem_assembly._merge_social_response_structure_meta),
    )
    monkeypatch.setattr(
        fem_assembly,
        "merge_narrative_authenticity_into_final_emission_meta",
        _track("nat", fem_assembly.merge_narrative_authenticity_into_final_emission_meta),
    )
    monkeypatch.setattr(
        fem_assembly,
        "merge_narrative_authority_meta",
        _track("na", fem_assembly.merge_narrative_authority_meta),
    )
    monkeypatch.setattr(
        fem_assembly,
        "merge_tone_escalation_meta",
        _track("te", fem_assembly.merge_tone_escalation_meta),
    )
    monkeypatch.setattr(
        fem_assembly,
        "merge_anti_railroading_meta",
        _track("ar", fem_assembly.merge_anti_railroading_meta),
    )
    monkeypatch.setattr(
        fem_assembly,
        "merge_context_separation_meta",
        _track("cs", fem_assembly.merge_context_separation_meta),
    )
    monkeypatch.setattr(
        fem_assembly,
        "merge_player_facing_narration_purity_meta",
        _track("purity", fem_assembly.merge_player_facing_narration_purity_meta),
    )
    monkeypatch.setattr(
        fem_assembly,
        "merge_answer_shape_primacy_meta",
        _track("asp", fem_assembly.merge_answer_shape_primacy_meta),
    )
    monkeypatch.setattr(
        fem_assembly,
        "_merge_scene_state_anchor_meta",
        _track("ssa", fem_assembly._merge_scene_state_anchor_meta),
    )
    monkeypatch.setattr(
        fem_assembly,
        "_merge_fallback_behavior_meta",
        _track("fb", fem_assembly._merge_fallback_behavior_meta),
    )
    monkeypatch.setattr(
        fem_assembly,
        "_merge_fast_fallback_neutral_composition_meta",
        _track("ffnc", fem_assembly._merge_fast_fallback_neutral_composition_meta),
    )

    fem_assembly.merge_gate_layer_metas_into_fem(
        fem,
        response_type_debug=layer_meta,
        ac_layer_meta=layer_meta,
        aep_layer_meta=layer_meta,
        rd_layer_meta=layer_meta,
        srs_layer_meta=layer_meta,
        nat_layer_meta=layer_meta,
        na_layer_meta=layer_meta,
        te_layer_meta=layer_meta,
        ar_layer_meta=layer_meta,
        cs_layer_meta=layer_meta,
        purity_layer_meta=layer_meta,
        asp_layer_meta=layer_meta,
        ssa_layer_meta=layer_meta,
        fb_layer_meta=layer_meta,
        ffnc_layer_meta=layer_meta,
    )
    assert order == [
        "response_type",
        "ac",
        "aep",
        "rd",
        "srs",
        "nat",
        "na",
        "te",
        "ar",
        "cs",
        "purity",
        "asp",
        "ssa",
        "fb",
        "ffnc",
    ]

    order.clear()
    fem_assembly.merge_gate_layer_metas_into_fem(
        fem,
        response_type_debug=layer_meta,
        ac_layer_meta=layer_meta,
        aep_layer_meta=layer_meta,
        rd_layer_meta=layer_meta,
        srs_layer_meta=layer_meta,
        nat_layer_meta=layer_meta,
        na_layer_meta=layer_meta,
        te_layer_meta=layer_meta,
        ar_layer_meta=layer_meta,
        cs_layer_meta=layer_meta,
        purity_layer_meta=layer_meta,
        asp_layer_meta=layer_meta,
        ssa_layer_meta=layer_meta,
        fb_layer_meta=layer_meta,
        ffnc_layer_meta=layer_meta,
        include_fast_fallback_neutral_composition=False,
    )
    assert order == [
        "response_type",
        "ac",
        "aep",
        "rd",
        "srs",
        "nat",
        "na",
        "te",
        "ar",
        "cs",
        "purity",
        "asp",
        "ssa",
        "fb",
    ]


def test_bj129_gate_module_thin_boundary_source_shape_locked() -> None:
    """BJ-129: gate owner rejects regrowth beyond orchestration wiring + documented live seams."""
    from tests.helpers.gate_thin_boundary_locks import (
        BJ128_LIVE_GATE_SEAM_SYMBOLS,
        BJ129_ALLOWED_GATE_IMPORT_MODULES,
        assert_gate_bj129_thin_boundary_shape,
        gate_import_modules,
        module_level_defs,
    )

    assert_gate_bj129_thin_boundary_shape(feg)

    gate_src = inspect.getsource(feg)
    assert gate_import_modules(gate_src) == BJ129_ALLOWED_GATE_IMPORT_MODULES
    assert module_level_defs(gate_src) == ("apply_final_emission_gate",)

    for name in BJ128_LIVE_GATE_SEAM_SYMBOLS:
        assert hasattr(feg, name), f"gate missing documented live seam: {name!r}"
