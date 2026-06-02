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
    OPENING_FALLBACK_OWNER_SEALED_GATE,
    OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
    SEALED_FALLBACK_OWNER_SEALED_GATE,
    SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED,
    infer_accept_path_final_emitted_source,
    opening_fallback_owner_bucket_from_meta,
    read_final_emission_meta_dict,
)

import pytest

import game.final_emission_gate as feg
import game.final_emission_visibility_fallback as visibility_fallback
import game.scene_state_anchoring as ssa
from game.contract_registry import emergency_fallback_source_ids
from game.defaults import default_scene, default_session, default_world
from game.final_emission_gate import apply_final_emission_gate, get_speaker_selection_contract
from game.narrative_mode_contract import build_narrative_mode_contract
from game.anti_railroading import build_anti_railroading_contract
from game.context_separation import build_context_separation_contract
from game.narrative_authority import build_narrative_authority_contract
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.player_facing_narration_purity import build_player_facing_narration_purity_contract
from game.social_exchange_emission import effective_strict_social_resolution_for_emission
from game.storage import get_scene_runtime
from game.final_emission_text import _normalize_text
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
    OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED,
    UPSTREAM_PREPARED_EMISSION_KEY,
    UPSTREAM_PREPARED_OPENING_FALLBACK_KEY,
    build_upstream_prepared_opening_fallback_payload,
    maybe_attach_upstream_prepared_opening_fallback_payload,
)
from tests.helpers.opening_fallback_evidence import OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL
from tests.helpers.final_emission_gate_fixtures import (
    EXPECTED_FRONTIER_GATE_OPENING_FALLBACK,
    assert_fallback_owner_bucket,
    assert_final_emission_meta_contains,
    assert_opening_fallback_source,
    assert_sealed_fallback_owner_bucket,
    final_emission_meta_from_output,
    opening_gm_output,
    opening_validation_context,
    response_type_contract,
    runner_strict_bundle,
    run_strict_social_motive_overclaim_gate_case,
)
from tests.helpers.objective7_referent_fixtures import (
    minimal_full_referent_artifact,
    referent_compact_mirror,
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


_IC_BRIDGE_LIVE_MALFORMED = 'South road." Tavern Runner nods once. "Old Millstone.'


# Ownership note:
# This cluster owns route/speaker/social-continuity attachment at final-gate time.
# Investigate speaker/continuity semantics in their direct modules first; add
# cases here only for gate order, bridge routing, or metadata projection.


def _strong_interaction_continuity_contract(*, anchor: str = "npc_melka") -> dict:
    return {
        "enabled": True,
        "continuity_strength": "strong",
        "anchored_interlocutor_id": anchor,
        "preserve_conversational_thread": True,
        "speaker_selection_contract": None,
    }


def _ssc_locked_tavern_runner() -> dict:
    return {
        "continuity_locked": True,
        "primary_speaker_id": "tavern_runner",
        "primary_speaker_name": "Tavern Runner",
        "allowed_speaker_ids": ["tavern_runner"],
        "speaker_switch_allowed": False,
    }


def _strong_runner_interaction_continuity() -> dict:
    return {
        "enabled": True,
        "continuity_strength": "strong",
        "anchored_interlocutor_id": "tavern_runner",
        "preserve_conversational_thread": True,
        "speaker_selection_contract": _ssc_locked_tavern_runner(),
    }


def _speaker_binding_mismatch_malformed_enforcement() -> dict:
    return {
        "validation": {
            "ok": False,
            "reason_code": "speaker_binding_mismatch",
            "canonical_speaker_name": "Tavern Runner",
            "details": {
                "signature": {
                    "speaker_label": 'South road." Tavern Runner',
                    "speaker_name": 'South road." Tavern Runner',
                    "is_explicitly_attributed": True,
                }
            },
        },
        "post_validation": {
            "ok": False,
            "reason_code": "speaker_binding_mismatch",
            "canonical_speaker_name": "Tavern Runner",
            "details": {
                "signature": {
                    "speaker_label": 'South road." Tavern Runner',
                    "speaker_name": 'South road." Tavern Runner',
                    "is_explicitly_attributed": True,
                }
            },
        },
    }


def _assert_interaction_continuity_validation_shape(v: dict) -> None:
    assert set(v.keys()) == {
        "ok",
        "enabled",
        "continuity_strength",
        "violations",
        "warnings",
        "facts",
        "debug",
    }
    assert isinstance(v["violations"], list)
    assert isinstance(v["warnings"], list)
    assert isinstance(v["facts"], dict)
    assert isinstance(v["debug"], dict)
    for k in (
        "anchored_interlocutor_id",
        "anchor_required",
        "speaker_switch_detected",
        "explicit_switch_cue_present",
        "thread_drop_detected",
        "narrator_bridge_present",
        "multi_speaker_pattern_present",
        "dialogue_presence",
    ):
        assert k in v["facts"]
    assert "speaker_labels_detected" in v["debug"]
    assert "cue_labels" in v["debug"]
    assert "reason_path" in v["debug"]


def _interaction_continuity_gate_payload(text: str, *, ic: dict | None = None) -> tuple[dict, dict]:
    return (
        {
            "player_facing_text": text,
            "metadata": {"emission_debug": {"speaker_contract_enforcement": _speaker_binding_mismatch_malformed_enforcement()}},
            "response_policy": {"interaction_continuity": ic or _strong_runner_interaction_continuity()},
        },
        {"metadata": {"emission_debug": {}}},
    )


def test_attach_interaction_continuity_validation_populates_debug_and_final_meta():
    out = {
        "player_facing_text": "The scene holds.",
        "_final_emission_meta": {},
        "metadata": {},
        "response_policy": {"interaction_continuity": _strong_interaction_continuity_contract()},
    }
    resolution = {"metadata": {"emission_debug": {}}}

    feg._attach_interaction_continuity_validation(
        out,
        resolution_for_contracts=resolution,
        eff_resolution=None,
        session=None,
    )

    assert out["player_facing_text"] == "The scene holds."
    icv = out["metadata"]["emission_debug"]["interaction_continuity_validation"]
    _assert_interaction_continuity_validation_shape(icv)
    assert read_final_emission_meta_dict(out)["interaction_continuity_validation"] is icv
    assert resolution["metadata"]["emission_debug"]["interaction_continuity_validation"] is icv


def test_referent_clarity_pre_finalize_merges_fem_and_tracks_input_source():
    art = minimal_full_referent_artifact(referential_ambiguity_class="none", ambiguity_risk=5)
    out = {
        "player_facing_text": "They halt.",
        "prompt_context": {"referent_tracking": art},
        "_gate_turn_packet_cache": {
            "referent_tracking_compact": referent_compact_mirror(
                referential_ambiguity_class="ambiguous_singular",
                ambiguity_risk=40,
            )
        },
        "_final_emission_meta": {"final_route": "accept_candidate", "tone_escalation": {"lane": "stub"}},
    }
    feg._apply_referent_clarity_pre_finalize(out, pre_gate_text="They halt.")
    fem = read_final_emission_meta_dict(out)
    assert fem["referent_validation_input_source"] == "full_artifact"
    assert fem["referent_validation_ran"] is True
    assert fem["referent_repair_applied"] is False
    assert fem.get("referent_boundary_semantic_repair_disabled") is True
    assert out["player_facing_text"] == "They halt."
    assert fem.get("tone_escalation") == {"lane": "stub"}
    gtxt = _normalize_text(out["player_facing_text"])
    preview = (gtxt[:120] + "…") if len(gtxt) > 120 else gtxt
    assert fem.get("final_text_preview") == preview
    assert fem.get("post_gate_mutation_detected") is False


def test_referent_clarity_pre_finalize_four_gate_exit_paths_all_use_same_hook():
    """Documentation-by-test: referent pre-finalize is invoked from each finalize branch."""
    import inspect

    src = inspect.getsource(feg.apply_final_emission_gate)
    assert src.count("_apply_referent_clarity_pre_finalize") == 4


def test_apply_interaction_continuity_step_records_bridge_metadata_when_bridge_fires():
    out, resolution = _interaction_continuity_gate_payload(_IC_BRIDGE_LIVE_MALFORMED)

    feg._apply_interaction_continuity_emission_step(
        out,
        text=_IC_BRIDGE_LIVE_MALFORMED,
        resolution_for_contracts=resolution,
        eff_resolution=None,
        session=None,
        validate_only=False,
        strict_social_path=False,
    )

    bridge = (out["metadata"].get("emission_debug") or {}).get("interaction_continuity_speaker_binding_bridge")
    assert isinstance(bridge, dict)
    assert bridge.get("applied") is True
    assert bridge.get("synthetic_violation") == "malformed_speaker_attribution_under_continuity"
    assert bridge.get("malformed_attribution_detected") is True


def test_apply_interaction_continuity_step_repairs_malformed_bridge_case_before_enforcement():
    out, resolution = _interaction_continuity_gate_payload(_IC_BRIDGE_LIVE_MALFORMED)

    feg._apply_interaction_continuity_emission_step(
        out,
        text=_IC_BRIDGE_LIVE_MALFORMED,
        resolution_for_contracts=resolution,
        eff_resolution=None,
        session=None,
        validate_only=False,
        strict_social_path=False,
    )

    em = out["metadata"]["emission_debug"]
    icv = em.get("interaction_continuity_validation") or {}
    rep = em.get("interaction_continuity_repair") or {}
    assert icv.get("ok") is True
    assert rep.get("applied") is True
    assert rep.get("repair_type") == "repair_malformed_speaker_attribution"
    assert "malformed_speaker_attribution_under_continuity" in (rep.get("violations") or [])
    assert em.get("interaction_continuity_enforced") is not True
    assert em.get("interaction_continuity_speaker_binding_bridge", {}).get("applied") is True


def test_apply_interaction_continuity_step_enforces_when_bridge_failure_is_unrepairable():
    unrecoverable = 'South road." Stranger waits. "Old Millstone.'
    out, resolution = _interaction_continuity_gate_payload(unrecoverable)

    feg._apply_interaction_continuity_emission_step(
        out,
        text=unrecoverable,
        resolution_for_contracts=resolution,
        eff_resolution=None,
        session=None,
        validate_only=False,
        strict_social_path=False,
    )

    em = out["metadata"]["emission_debug"]
    assert em.get("interaction_continuity_enforced") is True
    assert em.get("interaction_continuity_repair", {}).get("applied") is not True
    assert em.get("interaction_continuity_speaker_binding_bridge", {}).get("applied") is True


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


def test_block_d_validate_only_attach_never_calls_repair_interaction_continuity(monkeypatch):
    def boom(*_a, **_k):
        raise AssertionError("repair_interaction_continuity must not run on validate_only attach paths")

    monkeypatch.setattr(feg, "repair_interaction_continuity", boom)
    out = {
        "player_facing_text": "The scene holds.",
        "_final_emission_meta": {},
        "metadata": {},
        "response_policy": {"interaction_continuity": _strong_interaction_continuity_contract()},
    }
    resolution = {"metadata": {"emission_debug": {}}}
    feg._attach_interaction_continuity_validation(
        out,
        resolution_for_contracts=resolution,
        eff_resolution=None,
        session=None,
    )
    assert out["player_facing_text"] == "The scene holds."


def test_apply_final_emission_gate_validate_only_ic_never_calls_repair_interaction_continuity(monkeypatch):
    """Orchestration path attaches IC validation with validate_only=True; repair helper stays cold."""

    def boom(*_a, **_k):
        raise AssertionError("repair_interaction_continuity must not run on live gate validate-only IC paths")

    monkeypatch.setattr(feg, "repair_interaction_continuity", boom)
    gm = {
        "player_facing_text": "Short.",
        "tags": [],
        "metadata": {},
        "response_policy": {"interaction_continuity": _strong_interaction_continuity_contract()},
    }
    apply_final_emission_gate(
        gm,
        resolution={"kind": "observe", "prompt": "Hi."},
        session=None,
        scene_id="s1",
        scene={},
        world={},
    )


def test_block_d_strict_social_continuity_hard_fallback_applies_sealed_line(monkeypatch):
    """When repair cannot fix strong continuity failure under strict-social, sealed fallback is applied."""
    ic = _strong_runner_interaction_continuity()
    out = {
        "player_facing_text": "You can't go there.",
        "metadata": {},
        "response_policy": {"interaction_continuity": ic},
    }
    resolution = {
        "social": {"npc_id": "tavern_runner", "npc_name": "Tavern Runner"},
        "metadata": {"emission_debug": {}},
    }

    monkeypatch.setattr(
        feg,
        "repair_interaction_continuity",
        lambda *_a, **_k: {"applied": False, "repaired_text": "unused"},
    )
    txt, extra, strict_fb = feg._apply_interaction_continuity_emission_step(
        out,
        text="You can't go there.",
        resolution_for_contracts=resolution,
        eff_resolution=resolution,
        session={"turn_counter": "1"},
        validate_only=False,
        strict_social_path=True,
        strict_fallback_resolution=resolution,
    )
    assert strict_fb is True
    assert extra == []
    assert '"' in txt
    em = out["metadata"]["emission_debug"]
    assert em.get("interaction_continuity_enforced") is True


def test_block_b_speaker_local_rebind_is_metadata_visible_and_sync_traceable():
    session, world, sid, resolution = runner_strict_bundle()
    eff_resolution = copy.deepcopy(resolution)
    eff_resolution["social"]["npc_id"] = "runner"
    eff_resolution["social"]["npc_name"] = "Tavern Runner"
    gm = {"metadata": {}}

    contract = {
        "primary_speaker_id": "runner",
        "primary_speaker_name": "Tavern Runner",
        "allowed_speaker_ids": ["runner"],
        "continuity_locked": True,
        "speaker_switch_allowed": False,
        "generic_fallback_forbidden": False,
        "offscene_speakers_forbidden": True,
        "debug": {"contract_missing": False},
    }

    def fake_contract(*args, **kwargs):
        return dict(contract)

    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(feg, "get_speaker_selection_contract", fake_contract)
        repaired, payload = feg.enforce_emitted_speaker_with_contract(
            'Ragged stranger says, "East lanes."',
            gm_output=gm,
            resolution=resolution,
            eff_resolution=eff_resolution,
            world=world,
            scene_id=sid,
        )

    assert repaired == 'Tavern Runner says, "East lanes."'
    assert payload["final_reason_code"] == "continuity_locked_speaker_repair"
    assert payload["repair"]["local_rebind_applied"] is True

    feg._sync_eff_social_to_resolution(eff_resolution, resolution)
    assert resolution["social"]["npc_id"] == "runner"
    assert resolution["social"]["npc_name"] == "Tavern Runner"

    em = (gm.get("metadata") or {}).get("emission_debug") or {}
    assert em["speaker_contract_enforcement"] is payload
    assert em["speaker_contract_enforcement"]["repair"]["local_rebind_applied"] is True


def test_block_b_strict_social_pronoun_substitution_records_explicit_metadata(monkeypatch):
    out = {
        "player_facing_text": 'She says, "East gate is watched."',
        "tags": [],
        "_final_emission_meta": {"response_type_required": "dialogue"},
    }
    eff_resolution = {
        "kind": "question",
        "social": {"npc_id": "runner", "npc_name": "Tavern Runner"},
    }

    calls = {"ref": 0}

    def fake_ref(text, **kwargs):
        calls["ref"] += 1
        if calls["ref"] == 1:
            return {
                "ok": False,
                "violations": [
                    {
                        "kind": "ambiguous_entity_reference",
                        "token": "She",
                        "candidate_entity_ids": ["runner"],
                        "sentence_text": text,
                    }
                ],
                "checked_entities": ["runner"],
            }
        return {"ok": True, "violations": [], "checked_entities": ["runner"]}

    monkeypatch.setattr(feg, "validate_player_facing_referential_clarity", fake_ref)
    monkeypatch.setattr(feg, "validate_player_facing_first_mentions", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(feg, "validate_player_facing_visibility", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(feg, "_active_interlocutor_visible_person_like", lambda *a, **k: True)

    result = feg._apply_referential_clarity_enforcement(
        out,
        session={},
        scene={},
        world={},
        scene_id="scene_investigate",
        eff_resolution=eff_resolution,
        active_interlocutor="runner",
        strict_social_active=True,
        strict_social_suppressed_non_social_turn=False,
    )

    meta = result["_final_emission_meta"]
    assert result["player_facing_text"].startswith("The Tavern Runner says")
    assert meta["referential_clarity_local_substitution_attempted"] is True
    assert meta["referential_clarity_local_substitution_applied"] is True
    assert meta["referential_clarity_local_substitution_token"] == "She"
    assert meta["referential_clarity_local_substitution_replacement"] == "The Tavern Runner"
    assert "referential_clarity_local_substitution" in result["tags"]


# === BLOCK E — Strict-social referential substitution (gate routing/fencing only) ===
# Semantic legality: game/narration_visibility.py and tests/test_final_emission_visibility.py.


_BLOCK_E_REFCLARITY_FAIL_VIOLATION = {
    "kind": "ambiguous_entity_reference",
    "token": "She",
    "candidate_entity_ids": ["runner"],
    "sentence_text": 'She says, "East gate is watched."',
}


def _block_e_failing_referential_validation(text: str, **_kwargs):
    return {
        "ok": False,
        "violations": [dict(_BLOCK_E_REFCLARITY_FAIL_VIOLATION, sentence_text=text)],
        "checked_entities": ["runner"],
    }


def _block_e_benign_fallback_selection(*_args, **_kwargs) -> visibility_fallback.VisibilitySelectedFallback:
    return visibility_fallback.VisibilitySelectedFallback(
        text="Block E sealed fallback line.",
        fallback_pool="block_e_test_pool",
        fallback_kind="block_e_test_kind",
        final_emitted_source="block_e_test_source",
        fallback_strategy="standard_safe_fallback",
        fallback_candidate_source="block_e_test_candidate_source",
        composition_meta=feg._first_mention_composition_meta(),
    )


def _block_e_seed_strict_social_dialogue_out() -> dict:
    return {
        "player_facing_text": 'She says, "East gate is watched."',
        "tags": [],
        "_final_emission_meta": {"response_type_required": "dialogue"},
    }


def _block_e_eff_resolution() -> dict:
    return {
        "kind": "question",
        "social": {"npc_id": "runner", "npc_name": "Tavern Runner"},
    }


def test_block_e_strict_social_referential_substitution_skipped_on_non_strict_path(monkeypatch):
    """Block E: non-strict callers must not reach the substitution helper, even when validation fails."""
    out = _block_e_seed_strict_social_dialogue_out()
    monkeypatch.setattr(
        feg, "validate_player_facing_referential_clarity", _block_e_failing_referential_validation
    )
    monkeypatch.setattr(feg, "_standard_visibility_safe_fallback", _block_e_benign_fallback_selection)

    def boom(*_a, **_k):
        raise AssertionError(
            "_try_strict_social_local_pronoun_substitution_repair must not run on non-strict-social paths"
        )

    monkeypatch.setattr(feg, "_try_strict_social_local_pronoun_substitution_repair", boom)

    result = feg._apply_referential_clarity_enforcement(
        out,
        session={},
        scene={},
        world={},
        scene_id="scene_investigate",
        eff_resolution=_block_e_eff_resolution(),
        active_interlocutor="runner",
        strict_social_active=False,
        strict_social_suppressed_non_social_turn=False,
    )
    meta = result["_final_emission_meta"]
    assert meta["referential_clarity_local_substitution_attempted"] is False
    assert meta["referential_clarity_local_substitution_applied"] is False
    assert meta["referential_clarity_local_substitution_token"] is None
    assert meta["referential_clarity_local_substitution_replacement"] is None
    assert meta["referential_clarity_fallback_avoided"] is False
    assert meta["referential_clarity_replacement_applied"] is True
    assert "referential_clarity_local_substitution" not in (result.get("tags") or [])
    assert "referential_clarity_enforcement_replaced" in (result.get("tags") or [])


def test_block_e_strict_social_referential_substitution_skipped_on_non_dialogue_response_type(monkeypatch):
    """Block E: even strict-social, a non-dialogue response_type_required must not reach the helper."""
    out = _block_e_seed_strict_social_dialogue_out()
    out["_final_emission_meta"]["response_type_required"] = "action_outcome"
    monkeypatch.setattr(
        feg, "validate_player_facing_referential_clarity", _block_e_failing_referential_validation
    )
    monkeypatch.setattr(feg, "_standard_visibility_safe_fallback", _block_e_benign_fallback_selection)

    def boom(*_a, **_k):
        raise AssertionError(
            "_try_strict_social_local_pronoun_substitution_repair must not run when response_type != dialogue"
        )

    monkeypatch.setattr(feg, "_try_strict_social_local_pronoun_substitution_repair", boom)

    result = feg._apply_referential_clarity_enforcement(
        out,
        session={},
        scene={},
        world={},
        scene_id="scene_investigate",
        eff_resolution=_block_e_eff_resolution(),
        active_interlocutor="runner",
        strict_social_active=True,
        strict_social_suppressed_non_social_turn=False,
    )
    meta = result["_final_emission_meta"]
    assert meta["referential_clarity_local_substitution_attempted"] is False
    assert meta["referential_clarity_local_substitution_applied"] is False
    assert meta["referential_clarity_replacement_applied"] is True


def test_block_e_strict_social_referential_substitution_skipped_when_suppressed_non_social_turn(monkeypatch):
    """Block E: strict-social-suppressed-non-social-turn blocks substitution; sealed fallback runs instead."""
    out = _block_e_seed_strict_social_dialogue_out()
    monkeypatch.setattr(
        feg, "validate_player_facing_referential_clarity", _block_e_failing_referential_validation
    )
    monkeypatch.setattr(feg, "_standard_visibility_safe_fallback", _block_e_benign_fallback_selection)

    def boom(*_a, **_k):
        raise AssertionError(
            "_try_strict_social_local_pronoun_substitution_repair must not run when "
            "strict_social_suppressed_non_social_turn=True"
        )

    monkeypatch.setattr(feg, "_try_strict_social_local_pronoun_substitution_repair", boom)

    result = feg._apply_referential_clarity_enforcement(
        out,
        session={},
        scene={},
        world={},
        scene_id="scene_investigate",
        eff_resolution=_block_e_eff_resolution(),
        active_interlocutor="runner",
        strict_social_active=True,
        strict_social_suppressed_non_social_turn=True,
    )
    meta = result["_final_emission_meta"]
    assert meta["referential_clarity_local_substitution_attempted"] is False
    assert meta["referential_clarity_local_substitution_applied"] is False
    assert meta["referential_clarity_replacement_applied"] is True


def test_block_e_strict_social_referential_substitution_post_validation_rejection_records_failure_reason(monkeypatch):
    """Block E: helper attempts substitution but post-validation fails; metadata records attempted-but-not-applied."""
    out = _block_e_seed_strict_social_dialogue_out()

    calls = {"ref": 0}

    def fake_ref(text, **_kwargs):
        calls["ref"] += 1
        return {
            "ok": False,
            "violations": [dict(_BLOCK_E_REFCLARITY_FAIL_VIOLATION, sentence_text=text)],
            "checked_entities": ["runner"],
        }

    monkeypatch.setattr(feg, "validate_player_facing_referential_clarity", fake_ref)
    monkeypatch.setattr(feg, "validate_player_facing_first_mentions", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(feg, "validate_player_facing_visibility", lambda *a, **k: {"ok": True})
    monkeypatch.setattr(feg, "_active_interlocutor_visible_person_like", lambda *a, **k: True)
    monkeypatch.setattr(feg, "_standard_visibility_safe_fallback", _block_e_benign_fallback_selection)

    result = feg._apply_referential_clarity_enforcement(
        out,
        session={},
        scene={},
        world={},
        scene_id="scene_investigate",
        eff_resolution=_block_e_eff_resolution(),
        active_interlocutor="runner",
        strict_social_active=True,
        strict_social_suppressed_non_social_turn=False,
    )
    meta = result["_final_emission_meta"]
    assert meta["referential_clarity_local_substitution_attempted"] is True
    assert meta["referential_clarity_local_substitution_applied"] is False
    assert meta["referential_clarity_fallback_after_failed_local_repair"] is True
    assert meta["referential_clarity_replacement_applied"] is True
    assert calls["ref"] >= 2


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


def test_block_f_canonical_rewrite_and_narrator_neutral_repair_metadata_visible(monkeypatch):
    """Block F: canonical rewrite and narrator-neutral branches record repair flags on enforcement payload."""
    from copy import deepcopy

    from game.social import SPEAKER_CONTRACT_FORBIDDEN_FALLBACK_LABELS

    def _contract_canonical(**overrides):
        c = {
            "primary_speaker_id": "runner",
            "primary_speaker_name": "Tavern Runner",
            "allowed_speaker_ids": ["runner"],
            "continuity_locked": True,
            "speaker_switch_allowed": True,
            "interruption_allowed": True,
            "interruption_requires_scene_event": False,
            "generic_fallback_forbidden": True,
            "forbidden_fallback_labels": list(SPEAKER_CONTRACT_FORBIDDEN_FALLBACK_LABELS),
            "offscene_speakers_forbidden": True,
            "debug": {"contract_missing": False},
        }
        c.update(overrides)
        return c

    session, world, sid, resolution = runner_strict_bundle()

    c_cr = _contract_canonical()
    eff_cr = {
        "kind": "question",
        "social": {"npc_id": "runner", "npc_name": "Tavern Runner", "social_intent_class": "social_exchange"},
        "metadata": {"emission_debug": {"speaker_selection_contract": c_cr}},
    }
    gm_cr = {"metadata": deepcopy(eff_cr["metadata"]), "trace": {}}
    monkeypatch.setattr(feg, "get_speaker_selection_contract", lambda *a, **kw: dict(c_cr))
    out_cr, payload_cr = feg.enforce_emitted_speaker_with_contract(
        "Merchant mutters under his breath without giving a straight answer.",
        gm_output=gm_cr,
        resolution=eff_cr,
        eff_resolution=eff_cr,
        world={},
        scene_id=sid,
    )
    assert "Merchant" not in out_cr
    assert payload_cr["final_reason_code"] == "canonical_speaker_rewrite"
    assert (payload_cr.get("repair") or {}).get("canonical_rewrite_applied") is True

    c_nn = _contract_canonical(
        allowed_speaker_ids=[],
        primary_speaker_id=None,
        primary_speaker_name=None,
        generic_fallback_forbidden=True,
    )
    eff_nn = {
        "kind": "question",
        "social": {"npc_id": "runner", "npc_name": "Tavern Runner", "social_intent_class": "social_exchange"},
        "metadata": {"emission_debug": {"speaker_selection_contract": c_nn}},
    }
    gm_nn = {"metadata": deepcopy(eff_nn["metadata"]), "trace": {}}
    monkeypatch.setattr(feg, "get_speaker_selection_contract", lambda *a, **kw: dict(c_nn))
    out_nn, payload_nn = feg.enforce_emitted_speaker_with_contract(
        'Someone says, "Hello."',
        gm_output=gm_nn,
        resolution=eff_nn,
        eff_resolution=eff_nn,
        world={},
        scene_id=sid,
    )
    assert eff_nn["social"].get("reply_speaker_grounding_neutral_bridge") is True
    assert (payload_nn.get("repair") or {}).get("narrator_neutral_applied") is True
    assert payload_nn["final_reason_code"] == "narrator_neutral_no_allowed_speaker"
    assert len(out_nn or "") > 0


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


def test_scene_state_anchor_pass_path_flags_and_matched_kinds():
    """Use location-only anchors so visibility enforcement does not replace the line (no unseen NPC names)."""
    contract = _ssa_contract(
        location_tokens=["granite", "slate"],
    )
    raw = "Granite steps wear smooth under the slate roof."
    out = apply_final_emission_gate(
        {
            "player_facing_text": raw,
            "tags": [],
            "scene_state_anchor_contract": contract,
        },
        resolution={"kind": "observe", "prompt": "I listen for routes."},
        session=None,
        scene_id="frontier_gate",
        world={},
    )
    assert out.get("player_facing_text") == raw
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("scene_state_anchor_checked") is True
    assert meta.get("scene_state_anchor_passed") is True
    assert meta.get("scene_state_anchor_failed") is False
    assert meta.get("scene_state_anchor_repaired") is False
    assert meta.get("scene_state_anchor_skip_reason") is None
    assert "location" in (meta.get("scene_state_anchor_matched_kinds") or [])


def test_scene_state_anchor_actor_rebind_repair_metadata():
    contract = _ssa_contract(actor_tokens=["mara the smith"])
    text, meta = feg._apply_scene_state_anchor_layer(
        "The hammer rings once.",
        gm_output={"scene_state_anchor_contract": contract},
        strict_social_details=None,
    )
    assert text == "The hammer rings once."
    assert meta.get("scene_state_anchor_failed") is True
    assert meta.get("scene_state_anchor_repaired") is False
    assert meta.get("scene_state_anchor_boundary_semantic_repair_disabled") is True


def test_scene_state_anchor_action_rebind_repair_metadata():
    contract = _ssa_contract(
        actor_tokens=[],
        player_action_tokens=["north gate", "question"],
    )
    text, meta = feg._apply_scene_state_anchor_layer(
        "The guards exchange a look.",
        gm_output={"scene_state_anchor_contract": contract},
        strict_social_details=None,
    )
    assert text == "The guards exchange a look."
    assert meta.get("scene_state_anchor_failed") is True
    assert meta.get("scene_state_anchor_repaired") is False


def test_scene_state_anchor_location_rebind_repair_metadata():
    contract = _ssa_contract(
        scene_location_label="Stone Quay",
        location_tokens=["quay", "stone"],
    )
    text, meta = feg._apply_scene_state_anchor_layer(
        "Gulls wheel overhead.",
        gm_output={"scene_state_anchor_contract": contract},
        strict_social_details=None,
    )
    assert text == "Gulls wheel overhead."
    assert meta.get("scene_state_anchor_failed") is True
    assert meta.get("scene_state_anchor_repaired") is False


def test_scene_state_anchor_narrator_neutral_only_when_location_rebind_unavailable(monkeypatch):
    """C2: with anchor validation failing, boundary repair helpers are not invoked."""

    def no_location_opening(*args, **kwargs):
        return None, None

    monkeypatch.setattr(feg, "_repair_location_opening", no_location_opening)
    contract = _ssa_contract(
        scene_location_label="Ash Harbor",
        location_tokens=["harbor"],
    )
    text, meta = feg._apply_scene_state_anchor_layer(
        "Salt stings the air.",
        gm_output={"scene_state_anchor_contract": contract},
        strict_social_details=None,
    )
    assert text == "Salt stings the air."
    assert meta.get("scene_state_anchor_failed") is True
    assert meta.get("scene_state_anchor_repaired") is False


def test_scene_state_anchor_unrecoverable_preserves_text_and_records_failure():
    contract = _ssa_contract(
        enabled=True,
        location_tokens=[],
        actor_tokens=[],
        player_action_tokens=[],
        scene_location_label=None,
    )
    raw = "Untethered prose with no hooks."
    text, meta = feg._apply_scene_state_anchor_layer(
        raw,
        gm_output={"scene_state_anchor_contract": contract},
        strict_social_details=None,
    )
    assert text == raw
    assert meta.get("scene_state_anchor_failed") is True
    assert meta.get("scene_state_anchor_repaired") is False
    assert meta.get("scene_state_anchor_repair_mode") is None
    assert meta.get("scene_state_anchor_passed") is False
    assert "no_anchor_match" in (meta.get("scene_state_anchor_failure_reasons") or [])


def test_scene_state_anchor_fast_fallback_neutral_prefers_location_rebind_over_actor_prefix():
    contract = _ssa_contract(
        scene_location_label="Frontier Gate",
        location_tokens=["frontier gate", "gate"],
        actor_tokens=["emergent lord aldric"],
    )
    text, meta = feg._apply_scene_state_anchor_layer(
        "Several patrons exchange furtive glances.",
        gm_output={
            "scene_state_anchor_contract": contract,
            "tags": ["forced_retry_fallback", "upstream_api_fast_fallback"],
        },
        strict_social_details=None,
    )
    assert text == "Several patrons exchange furtive glances."
    assert meta.get("scene_state_anchor_failed") is True
    assert meta.get("scene_state_anchor_repaired") is False


def test_apply_final_emission_gate_repairs_malformed_opening_fast_fallback_composition():
    session = default_session()
    world = default_world()
    sid = "frontier_gate"
    session["active_scene_id"] = sid
    session["scene_state"]["active_scene_id"] = sid
    session["turn_counter"] = 0
    session["visited_scene_ids"] = [sid]
    scene = default_scene(sid)
    scene["scene"]["location"] = "Frontier Gate"
    scene["scene"]["summary"] = "A rain-soaked checkpoint holds a nervous crowd at the gate."
    scene["scene"]["visible_facts"] = [
        "Several patrons exchange furtive glances.",
        "A notice board lists a missing patrol.",
        "Rain darkens the flagstones around the checkpoint.",
    ]
    rebuild_active_scene_entities(session, world, sid, scene_envelope=scene)
    scene["scene_state"] = dict(session["scene_state"])

    out = apply_final_emission_gate(
        {
            "player_facing_text": (
                "Emergent Lord Aldric Several patrons exchange furtive glances. "
                "The rain holds; beside it, a notice board lists a missing patrol."
            ),
            "tags": ["forced_retry_fallback", "upstream_api_fast_fallback"],
            "scene_state_anchor_contract": _ssa_contract(
                scene_id=sid,
                scene_location_label="Frontier Gate",
                location_tokens=["frontier gate", "gate", "checkpoint"],
                actor_tokens=["emergent lord aldric"],
            ),
        },
        resolution={"kind": "observe", "prompt": "Begin."},
        session=session,
        scene_id=sid,
        scene=scene,
        world=world,
    )

    text = str(out.get("player_facing_text") or "")
    low = text.lower()
    meta = read_final_emission_meta_dict(out) or {}
    assert "emergent lord aldric several" in low
    assert "holds; beside it" in low
    assert meta.get("fast_fallback_neutral_composition_malformed_detected") is True
    assert meta.get("fast_fallback_neutral_composition_repaired") is False
    assert meta.get("scene_state_anchor_passed") is True


def test_ssa_layer_skip_reasons_direct():
    assert feg._skip_scene_state_anchor_layer(
        "x",
        None,
        strict_social_details=None,
    ) == "missing_contract"

    assert feg._skip_scene_state_anchor_layer(
        "x",
        _ssa_contract(enabled=False),
        strict_social_details=None,
    ) == "contract_disabled"

    assert feg._skip_scene_state_anchor_layer(
        "",
        _ssa_contract(),
        strict_social_details=None,
    ) == "empty_text"

    assert feg._skip_scene_state_anchor_layer(
        None,
        _ssa_contract(),
        strict_social_details=None,
    ) == "non_string_text"

    assert feg._skip_scene_state_anchor_layer(
        "x",
        _ssa_contract(),
        strict_social_details={"used_internal_fallback": True},
    ) == "strict_social_authoritative_internal_fallback"

    assert feg._skip_scene_state_anchor_layer(
        "x",
        _ssa_contract(),
        strict_social_details={"final_emitted_source": "neutral_reply_speaker_grounding_bridge"},
    ) == "strict_social_structured_or_bridge_source"

    assert feg._skip_scene_state_anchor_layer(
        "x",
        _ssa_contract(),
        strict_social_details=None,
        response_type_debug={"response_type_candidate_ok": False},
    ) == "response_type_contract_failed"


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


def test_validate_scene_state_anchoring_invoked_once_without_boundary_repair(monkeypatch):
    calls: list[str] = []

    def tracking_validate(t, c):
        calls.append(str(t))
        return {
            "checked": True,
            "passed": False,
            "matched_anchor_kinds": [],
            "failure_reasons": ["no_anchor_match"],
        }

    monkeypatch.setattr(feg, "validate_scene_state_anchoring", tracking_validate)
    contract = _ssa_contract(location_tokens=["beacon"])
    out = apply_final_emission_gate(
        {
            "player_facing_text": "Fog rolls in.",
            "tags": [],
            "scene_state_anchor_contract": contract,
        },
        resolution={"kind": "observe", "prompt": "I watch."},
        session={},
        scene_id="beacon_yard",
        world={},
    )
    assert calls == ["Fog rolls in."]
    fem = read_final_emission_meta_dict(out) or {}
    assert fem.get("scene_state_anchor_failed") is True
    assert fem.get("scene_state_anchor_repaired") is False


def test_gate_never_invokes_build_scene_state_anchor_contract(monkeypatch):
    def boom(*_a, **_kw):
        raise AssertionError("build_scene_state_anchor_contract must not be called from final emission gate")

    monkeypatch.setattr(ssa, "build_scene_state_anchor_contract", boom)
    out = apply_final_emission_gate(
        {
            "player_facing_text": "Stable air, cold iron.",
            "tags": [],
            "scene_state_anchor_contract": _ssa_contract(location_tokens=["stable"]),
        },
        resolution={"kind": "observe", "prompt": "I look."},
        session={},
        scene_id="frontier_gate",
        world={},
    )
    assert "stable" in (out.get("player_facing_text") or "").lower()


_contract_rope = _ssa_contract(location_tokens=["rope_bridge"])


@pytest.mark.parametrize(
    "attach_key,attach_payload",
    [
        ("scene_state_anchor_contract", _contract_rope),
        ("narration_payload", {"scene_state_anchor_contract": _contract_rope}),
        ("prompt_payload", {"scene_state_anchor_contract": _contract_rope}),
        ("_narration_payload", {"scene_state_anchor_contract": _contract_rope}),
        ("metadata", {"scene_state_anchor_contract": _contract_rope}),
        ("trace", {"scene_state_anchor_contract": _contract_rope}),
    ],
)
def test_contract_resolution_from_gm_output_nested_paths(attach_key, attach_payload):
    gm = {"player_facing_text": "Wind rises.", "tags": []}
    if attach_key == "scene_state_anchor_contract":
        gm["scene_state_anchor_contract"] = attach_payload
    else:
        gm[attach_key] = attach_payload
    out = apply_final_emission_gate(
        gm,
        resolution={"kind": "observe", "prompt": "I steady myself."},
        session={},
        scene_id="rope_bridge",
        world={},
    )
    assert feg._resolve_scene_state_anchor_contract(out) is not None
    fem = read_final_emission_meta_dict(out) or {}
    assert fem.get("scene_state_anchor_checked") is True
    assert fem.get("scene_state_anchor_failed") is True
    assert (out.get("player_facing_text") or "").strip() == "Wind rises."


def test_strict_social_npc_line_with_actor_token_passes_without_anchor_rewrite(monkeypatch):
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
        return 'Tavern Runner says, "East lanes."', dict(stub_details)

    monkeypatch.setattr(feg, "build_final_strict_social_response", fake_build)

    contract = _ssa_contract(actor_tokens=["tavern runner"])
    out = apply_final_emission_gate(
        {
            "player_facing_text": 'Tavern Runner says, "East lanes."',
            "tags": [],
            "scene_state_anchor_contract": contract,
        },
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("scene_state_anchor_repaired") is False
    assert meta.get("scene_state_anchor_passed") is True


def test_floating_narration_silence_line_records_anchor_failure_without_boundary_repair():
    raw = "The silence stretches for a moment."
    out = apply_final_emission_gate(
        {
            "player_facing_text": raw,
            "tags": [],
            "scene_state_anchor_contract": _ssa_contract(
                scene_location_label="Frontier Checkpoint",
                location_tokens=["checkpoint"],
            ),
        },
        resolution={"kind": "observe", "prompt": "I wait."},
        session={},
        scene_id="frontier_gate",
        world={},
    )
    assert out.get("player_facing_text") == raw
    fem = read_final_emission_meta_dict(out) or {}
    assert fem.get("scene_state_anchor_failed") is True
    assert fem.get("scene_state_anchor_repaired") is False


def test_contract_actor_only_player_action_only_location_only():
    for tokens, _kind in (
        ({"actor_tokens": ["yrsa"]}, "actor"),
        ({"player_action_tokens": ["barter check", "question"]}, "player_action"),
        ({"location_tokens": ["granary"], "scene_location_label": "Old Granary"}, "location"),
    ):
        c = _ssa_contract(**tokens)
        out = apply_final_emission_gate(
            {
                "player_facing_text": "Dust motes drift.",
                "tags": [],
                "scene_state_anchor_contract": c,
            },
            resolution={"kind": "question", "prompt": "I look."},
            session={},
            scene_id="granary_scene",
            world={},
        )
        meta = read_final_emission_meta_dict(out) or {}
        assert meta.get("scene_state_anchor_failed") is True
        assert meta.get("scene_state_anchor_passed") is False


def test_scene_transition_prefers_location_when_no_actor_tokens():
    out = apply_final_emission_gate(
        {
            "player_facing_text": "The road bends without a name.",
            "tags": [],
            "scene_state_anchor_contract": _ssa_contract(
                actor_tokens=[],
                player_action_tokens=[],
                location_tokens=["crossroads"],
                scene_location_label="The Crossroads",
            ),
        },
        resolution={"kind": "observe", "prompt": "I follow the road."},
        session={},
        scene_id="crossroads",
        world={},
    )
    m = read_final_emission_meta_dict(out) or {}
    assert m.get("scene_state_anchor_failed") is True
    assert m.get("scene_state_anchor_repaired") is False


def test_scene_location_label_used_when_location_tokens_sparse():
    """``scene_location_label`` drives the repair phrase; sparse ``location_tokens`` still validate the tether."""
    contract = _ssa_contract(
        location_tokens=["salt"],
        scene_location_label="Salt Docks",
    )
    text, meta = feg._apply_scene_state_anchor_layer(
        "Ropes creak.",
        gm_output={"scene_state_anchor_contract": contract},
        strict_social_details=None,
    )
    assert text == "Ropes creak."
    assert meta.get("scene_state_anchor_failed") is True


def test_repaired_output_excludes_hidden_bucket_strings():
    gm_out = {
        "player_facing_text": "Stillness.",
        "tags": [],
        "scene_state_anchor_contract": _ssa_contract(location_tokens=["watchtower"]),
        "gm_only_hidden_facts": ["SECRET_CULT_LEADER_NAME_XYZ"],
        "metadata": {"emission_debug": {"scene_state_anchor": {"counts": {"location": 1, "actor": 0, "player_action": 0}}}},
    }
    out = apply_final_emission_gate(
        gm_out,
        resolution={"kind": "observe", "prompt": "I listen."},
        session={},
        scene_id="watchtower",
        world={},
    )
    assert "SECRET_CULT" not in (out.get("player_facing_text") or "")


def test_short_npc_line_grounded_by_actor_token_passes_without_rewrite():
    out = apply_final_emission_gate(
        {
            "player_facing_text": 'Kara says, "No."',
            "tags": [],
            "scene_state_anchor_contract": _ssa_contract(actor_tokens=["kara"]),
        },
        resolution={"kind": "question", "prompt": "Did they leave?"},
        session=None,
        scene_id="lane_scene",
        world={},
    )
    assert "Kara" in (out.get("player_facing_text") or "")
    m = read_final_emission_meta_dict(out) or {}
    assert m.get("scene_state_anchor_repaired") is False
    assert m.get("scene_state_anchor_passed") is True


def test_observational_follow_up_grounded_by_player_action_token():
    out = apply_final_emission_gate(
        {
            "player_facing_text": "You study the latch; rust flakes away.",
            "tags": [],
            "scene_state_anchor_contract": _ssa_contract(
                actor_tokens=[],
                player_action_tokens=["study", "latch", "investigate"],
            ),
        },
        resolution={"kind": "investigate", "prompt": "I study the latch."},
        session=None,
        scene_id="storeroom",
        world={},
    )
    m = read_final_emission_meta_dict(out) or {}
    assert m.get("scene_state_anchor_passed") is True
    assert "player_action" in (m.get("scene_state_anchor_matched_kinds") or [])


def test_strict_and_non_strict_repair_sync_metadata():
    contract = _ssa_contract(location_tokens=["pier"])
    non_strict = apply_final_emission_gate(
        {
            "player_facing_text": "Fog.",
            "tags": [],
            "scene_state_anchor_contract": contract,
        },
        resolution={"kind": "observe", "prompt": "I smell salt."},
        session={},
        scene_id="pier",
        world={},
    )
    ns = read_final_emission_meta_dict(non_strict) or {}
    em_ns = (non_strict.get("metadata") or {}).get("emission_debug") or {}
    assert ns.get("scene_state_anchor_failed") is True
    assert ns.get("scene_state_anchor_repaired") is False
    assert em_ns.get("scene_state_anchor_failed") is True

    text, layer_meta = feg._apply_scene_state_anchor_layer(
        "Fog.",
        gm_output={"scene_state_anchor_contract": contract},
        strict_social_details=None,
    )
    merged = {}
    feg._merge_scene_state_anchor_meta(merged, layer_meta)
    assert merged.get("scene_state_anchor_failed") is True
    assert merged.get("scene_state_anchor_repaired") is False
    assert text == "Fog."


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


# --- Narrative authority (Objective #9 Block 3 contract resolution + strict-social slice) ---------

# Ownership note:
# This cluster owns final-gate orchestration for narrative-authority enforcement.
# Semantic authority rules should live with their validator/repair owners; add
# cases here only for contract resolution, layer order, strict-social routing, or FEM.


def _na_contract_for_resolution(resolution: dict) -> dict:
    return build_narrative_authority_contract(
        resolution=resolution,
        narration_visibility={},
        scene_state_anchor_contract=None,
        speaker_selection_contract=None,
        session_view=None,
    )


def _response_type_debug(*, candidate_ok: bool | None = True) -> dict:
    return {
        "response_type_required": None,
        "response_type_contract_source": None,
        "response_type_candidate_ok": candidate_ok,
        "response_type_repair_used": False,
        "response_type_repair_kind": None,
        "response_type_upstream_prepared_absent": False,
        "response_type_rejection_reasons": [],
        "non_hostile_escalation_blocked": False,
    }


def test_resolve_narrative_authority_full_contract_from_response_policy():
    res = {"kind": "observe", "prompt": "I listen."}
    na = _na_contract_for_resolution(res)
    gm = {"response_policy": {"narrative_authority": na}}
    full = feg._resolve_narrative_authority_contract(gm)
    assert full is na
    assert feg._is_shipped_full_narrative_authority_contract(full) is True


def test_resolve_narrative_authority_slim_prompt_debug_is_not_full_contract():
    slim = {"enabled": True, "authoritative_outcome_available": False}
    gm = {"prompt_debug": {"narrative_authority": slim}}
    assert feg._is_shipped_full_narrative_authority_contract(slim) is False
    assert feg._resolve_narrative_authority_contract(gm) is None


def test_resolve_narrative_authority_full_contract_from_narration_payload():
    res = {"kind": "observe", "prompt": "I listen."}
    na = _na_contract_for_resolution(res)
    gm = {"narration_payload": {"narrative_authority": na}}
    assert feg._resolve_narrative_authority_contract(gm) is na


def test_resolve_narrative_authority_full_contract_from_prompt_payload():
    res = {"kind": "observe", "prompt": "I listen."}
    na = _na_contract_for_resolution(res)
    gm = {"prompt_payload": {"narrative_authority": na}}
    assert feg._resolve_narrative_authority_contract(gm) is na


def test_resolve_narrative_authority_full_contract_from_trace_response_policy():
    res = {"kind": "observe", "prompt": "I listen."}
    na = _na_contract_for_resolution(res)
    gm = {"trace": {"response_policy": {"narrative_authority": na}}}
    assert feg._resolve_narrative_authority_contract(gm) is na


def test_resolve_narrative_authority_full_contract_from_narration_payload_mirror_key():
    res = {"kind": "observe", "prompt": "I listen."}
    na = _na_contract_for_resolution(res)
    gm = {"_narration_payload": {"response_policy": {"narrative_authority": na}}}
    assert feg._resolve_narrative_authority_contract(gm) is na


def test_skip_narrative_authority_when_forbid_unjustified_is_false():
    res = {"kind": "observe", "prompt": "I listen."}
    na = _na_contract_for_resolution(res)
    gm = {
        "response_policy": {
            "forbid_unjustified_narrative_authority": False,
            "narrative_authority": na,
        }
    }
    text, meta, _ = feg._apply_narrative_authority_layer(
        "The lock clicks open.",
        gm_output=gm,
        resolution=res,
        strict_social_details=None,
        response_type_debug=_response_type_debug(),
        answer_completeness_meta={},
        session={},
        scene_id="s",
    )
    assert meta["narrative_authority_skip_reason"] == "narrative_authority_policy_disabled"
    assert meta["narrative_authority_checked"] is False
    assert text == "The lock clicks open."


def test_skip_narrative_authority_when_contract_enabled_false():
    res = {"kind": "observe", "prompt": "I listen."}
    base = _na_contract_for_resolution(res)
    na = {**base, "enabled": False}
    gm = {"response_policy": {"narrative_authority": na}}
    text, meta, _ = feg._apply_narrative_authority_layer(
        "The lock clicks open.",
        gm_output=gm,
        resolution=res,
        strict_social_details=None,
        response_type_debug=_response_type_debug(),
        answer_completeness_meta={},
        session={},
        scene_id="s",
    )
    assert meta["narrative_authority_skip_reason"] == "contract_disabled"
    assert meta["narrative_authority_checked"] is False


def test_skip_narrative_authority_when_response_type_candidate_not_ok():
    res = {"kind": "observe", "prompt": "I listen."}
    na = _na_contract_for_resolution(res)
    gm = {"response_policy": {"narrative_authority": na}}
    text, meta, _ = feg._apply_narrative_authority_layer(
        "The lock clicks open.",
        gm_output=gm,
        resolution=res,
        strict_social_details=None,
        response_type_debug=_response_type_debug(candidate_ok=False),
        answer_completeness_meta={},
        session={},
        scene_id="s",
    )
    assert meta["narrative_authority_skip_reason"] == "response_type_contract_failed"
    assert meta["narrative_authority_checked"] is False


def test_skip_narrative_authority_only_slim_prompt_debug_no_validation():
    res = {"kind": "observe", "prompt": "I look."}
    slim = {"enabled": True, "authoritative_outcome_available": False}
    gm = {"prompt_debug": {"narrative_authority": slim}, "response_policy": {}}
    text, meta, _ = feg._apply_narrative_authority_layer(
        "The lock clicks open.",
        gm_output=gm,
        resolution=res,
        strict_social_details=None,
        response_type_debug=_response_type_debug(),
        answer_completeness_meta={},
        session={},
        scene_id="s",
    )
    assert meta["narrative_authority_skip_reason"] == "no_full_contract"
    assert meta["narrative_authority_checked"] is False
    assert text == "The lock clicks open."


def test_apply_na_with_full_contract_validates_normally():
    res = {"kind": "observe", "prompt": "I look at the moss."}
    na = _na_contract_for_resolution(res)
    gm = {"response_policy": {"narrative_authority": na}}
    text, meta, _ = feg._apply_narrative_authority_layer(
        "Rain brightens the moss; nothing is decided yet.",
        gm_output=gm,
        resolution=res,
        strict_social_details=None,
        response_type_debug=_response_type_debug(),
        answer_completeness_meta={},
        session={},
        scene_id="s",
    )
    assert meta["narrative_authority_skip_reason"] is None
    assert meta["narrative_authority_checked"] is True
    assert meta["narrative_authority_failed"] is False
    assert text == "Rain brightens the moss; nothing is decided yet."


def test_strict_social_gate_repairs_motive_overclaim_and_keeps_speaker(monkeypatch):
    """Strict-social: NA is validate-only; motive overclaim remains visible in meta, not silently rewritten."""
    run_strict_social_motive_overclaim_gate_case(monkeypatch)


def test_final_emission_gate_marks_non_hostile_escalation_blocked_on_tone_writer_overshoot() -> None:
    """When pre-repair text violates shipped tone policy, legacy meta records the overshoot."""
    ctr = {
        "enabled": True,
        "scene_id": "hall",
        "base_tone": "neutral",
        "max_allowed_tone": "guarded",
        "allow_guarded_refusal": True,
        "allow_verbal_pressure": False,
        "allow_explicit_threat": False,
        "allow_physical_hostility": False,
        "allow_combat_initiation": False,
        "justification_flags": {},
        "justification_reasons": [],
        "debug_inputs": {"scene_id": "hall"},
        "debug_flags": {},
    }
    out = apply_final_emission_gate(
        {
            "player_facing_text": "Out of nowhere, chaos erupts through the hall.",
            "tags": [],
            "response_policy": {"tone_escalation": ctr},
        },
        resolution={"kind": "observe", "prompt": "I listen."},
        session={},
        scene_id="hall",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("non_hostile_escalation_blocked") is True
    assert meta.get("tone_escalation_violation_before_repair") is True


# --- Anti-railroading (Objective Block 3) -------------------------------------------------------

# Ownership note:
# This cluster owns anti-railroading and context-separation gate integration.
# Investigate policy semantics in their direct modules first; add cases here only
# for final-gate repair timing, replacement routing, or metadata attachment.


def _ar_contract(**kwargs):
    return build_anti_railroading_contract(
        resolution=kwargs.get("resolution"),
        prompt_leads=kwargs.get("prompt_leads"),
        player_text=kwargs.get("player_text"),
    )


def test_anti_railroading_gate_passes_clean_leads_and_constraints():
    for raw in (
        "Two leads stand out: the lighthouse keeper and the customs office.",
        "The bridge is out. The alley and the roofline are still open.",
        "If you want an immediate answer, confronting the priest publicly is one option.",
    ):
        out = apply_final_emission_gate(
            {"player_facing_text": raw, "tags": [], "anti_railroading_contract": _ar_contract()},
            resolution={"kind": "observe", "prompt": "I look around."},
            session={},
            scene_id="dock",
            world={},
        )
        assert out.get("player_facing_text") == raw
        meta = read_final_emission_meta_dict(out) or {}
        assert meta.get("anti_railroading_repaired") is False
        em = (out.get("metadata") or {}).get("emission_debug") or {}
        assert em.get("anti_railroading", {}).get("validation", {}).get("passed") is True


def test_anti_railroading_gate_repairs_forced_pathing():
    out = apply_final_emission_gate(
        {"player_facing_text": "You head straight to the archive.", "tags": []},
        resolution={"kind": "observe", "prompt": "I look."},
        session={},
        scene_id="s",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    em = (out.get("metadata") or {}).get("emission_debug") or {}
    assert meta.get("final_route") == "replaced"
    assert meta.get("anti_railroading_failed") is True
    assert meta.get("anti_railroading_repaired") is False
    assert em.get("anti_railroading_boundary_semantic_repair_disabled") is True
    assert "anti_railroading_unsatisfied_at_boundary_no_rewrite" in (meta.get("rejection_reasons_sample") or [])


def test_anti_railroading_gate_repairs_exclusive_and_meta_hooks():
    for raw in (
        "The only real lead is the archive.",
        "This is where the story wants you to go.",
        "It's obvious now that you must follow the priest.",
        "Everything points to Greywake, so you go there.",
    ):
        out = apply_final_emission_gate(
            {"player_facing_text": raw, "tags": []},
            resolution={"kind": "observe", "prompt": "I listen."},
            session={},
            scene_id="s",
            world={},
        )
        meta = read_final_emission_meta_dict(out) or {}
        assert meta.get("anti_railroading_failed") is True, raw
        assert meta.get("anti_railroading_repaired") is False, raw
        assert meta.get("final_route") == "replaced", raw


def test_anti_railroading_resolved_transition_allows_arrival_language():
    res = {"kind": "travel", "resolved_transition": True, "prompt": "I enter the ward."}
    c = _ar_contract(resolution=res)
    raw = "You step through the arch into the lower ward, noise washing over you."
    out = apply_final_emission_gate(
        {"player_facing_text": raw, "tags": [], "anti_railroading_contract": c},
        resolution=res,
        session={},
        scene_id="ward",
        world={},
    )
    assert out.get("player_facing_text") == raw
    assert (read_final_emission_meta_dict(out) or {}).get("anti_railroading_repaired") is False


def test_anti_railroading_commitment_echo_allowed_when_player_committed():
    pt = "I'll head to the archives and check the register."
    c = _ar_contract(player_text=pt)
    raw = "You head toward the archives, letting the crowd carry you a block at a time."
    out = apply_final_emission_gate(
        {"player_facing_text": raw, "tags": [], "anti_railroading_contract": c},
        resolution={"kind": "observe", "prompt": pt},
        session={"scene_runtime": {"test_scene": {"last_player_action_text": pt}}},
        scene_id="test_scene",
        world={},
    )
    assert out.get("player_facing_text") == raw


def test_anti_railroading_quoted_dialogue_not_spuriously_flagged():
    raw = 'The clerk mutters, "You head straight to the archive." Then the door clicks.'
    out = apply_final_emission_gate(
        {"player_facing_text": raw, "tags": []},
        resolution={"kind": "observe", "prompt": "I listen."},
        session={},
        scene_id="s",
        world={},
    )
    assert '"' in (out.get("player_facing_text") or "")
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("anti_railroading_repaired") is False


def test_anti_railroading_prompt_context_contract_resolution():
    c = _ar_contract()
    out = apply_final_emission_gate(
        {
            "player_facing_text": "You head straight to the pier.",
            "tags": [],
            "prompt_context": {"anti_railroading_contract": c},
        },
        resolution={"kind": "observe", "prompt": "I walk."},
        session={},
        scene_id="pier",
        world={},
    )
    fem = read_final_emission_meta_dict(out) or {}
    assert fem.get("anti_railroading_failed") is True
    assert fem.get("anti_railroading_repaired") is False
    assert fem.get("anti_railroading_contract_resolution_source") == "shipped"
    assert fem.get("final_route") == "replaced"


def test_anti_railroading_coexists_with_narrative_authority_and_tone():
    na = build_narrative_authority_contract(
        resolution={"kind": "observe", "prompt": "I look."},
        narration_visibility={},
        scene_state_anchor_contract=None,
        speaker_selection_contract=None,
        session_view=None,
    )
    ctr = {
        "enabled": True,
        "scene_id": "hall",
        "base_tone": "neutral",
        "max_allowed_tone": "tense",
        "allow_guarded_refusal": True,
        "allow_verbal_pressure": True,
        "allow_explicit_threat": False,
        "allow_physical_hostility": False,
        "allow_combat_initiation": False,
        "justification_flags": {},
        "justification_reasons": [],
        "debug_inputs": {"scene_id": "hall"},
        "debug_flags": {},
    }
    out = apply_final_emission_gate(
        {
            "player_facing_text": "The only real lead is the cellar door.",
            "tags": [],
            "response_policy": {"narrative_authority": na, "tone_escalation": ctr},
        },
        resolution={"kind": "observe", "prompt": "I listen."},
        session={},
        scene_id="hall",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("narrative_authority_checked") is True
    assert meta.get("tone_escalation_checked") is True
    assert meta.get("anti_railroading_failed") is True
    assert meta.get("anti_railroading_repaired") is False
    assert meta.get("final_route") == "replaced"
    em = (out.get("metadata") or {}).get("emission_debug") or {}
    assert "narrative_authority_checked" in em
    assert "tone_escalation_checked" in em
    assert em.get("anti_railroading", {}).get("validation", {}).get("checked") is True


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


def test_anti_railroading_surfaced_lead_mandatory_repair(monkeypatch):
    """Surfaced-lead mandatory framing fails AR validation and triggers non-social replace."""
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    c = _ar_contract(prompt_leads=[{"id": "h1", "title": "Harbor warehouse"}])
    raw = "The Harbor warehouse lead isn't optional; you're going there now."
    out = apply_final_emission_gate(
        {"player_facing_text": raw, "tags": [], "anti_railroading_contract": c},
        resolution={"kind": "observe", "prompt": "I look."},
        session={},
        scene_id="s",
        world={},
    )
    fem = read_final_emission_meta_dict(out) or {}
    assert fem.get("anti_railroading_failed") is True
    assert fem.get("final_route") == "replaced"


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


def test_gate_context_separation_pass_brief_pressure_after_direct_answer(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    pt = "What does the loaf cost today?"
    cs = build_context_separation_contract(player_text=pt, resolution={"kind": "barter"})
    text = (
        'She names a price flatly. "Two coppers," she says. '
        "The ward's tense tonight—patrols everywhere—but bread is still bread."
    )
    out = apply_final_emission_gate(
        {"player_facing_text": text, "tags": [], "context_separation_contract": cs},
        resolution={"kind": "barter", "prompt": pt},
        session=None,
        scene_id="market_stall",
        world={},
    )
    em = (out.get("metadata") or {}).get("emission_debug") or {}
    assert em.get("context_separation", {}).get("validation", {}).get("passed") is True
    assert (read_final_emission_meta_dict(out) or {}).get("final_route") == "accept_candidate"


def test_gate_context_separation_pass_crisis_scene_pressure_focus(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    pt = "Where is the exit?"
    cs = build_context_separation_contract(
        player_text=pt,
        scene_summary="A raid tears through the lower ward; panic and smoke choke the alleys.",
        resolution={"kind": "travel"},
    )
    text = (
        "A guardsman points past a splintered door. "
        "The crackdown is still rolling house to house; you move or you are moved."
    )
    out = apply_final_emission_gate(
        {"player_facing_text": text, "tags": [], "context_separation_contract": cs},
        resolution={"kind": "travel", "prompt": pt},
        session=None,
        scene_id="ward_raid",
        world={},
    )
    em = (out.get("metadata") or {}).get("emission_debug") or {}
    assert em.get("context_separation", {}).get("validation", {}).get("passed") is True


def test_gate_context_separation_pass_player_asks_danger(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    pt = "Is it safe to linger here with the patrols?"
    cs = build_context_separation_contract(player_text=pt, resolution={"kind": "social_probe"})
    text = (
        "He doesn't laugh. 'Safe is a small word for a big war,' he says. "
        "Unrest has the factions eyeing each other; tonight, nowhere feels clean."
    )
    out = apply_final_emission_gate(
        {"player_facing_text": text, "tags": [], "context_separation_contract": cs},
        resolution={"kind": "social_probe", "prompt": pt},
        session=None,
        scene_id="street",
        world={},
    )
    em = (out.get("metadata") or {}).get("emission_debug") or {}
    assert em.get("context_separation", {}).get("validation", {}).get("passed") is True


def test_gate_context_separation_repair_drops_pressure_lead_in(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    pt = "What does the loaf cost today?"
    cs = build_context_separation_contract(player_text=pt, resolution={"kind": "barter"})
    text = (
        "The war along the border has everyone on edge, and coin means nothing next to survival. "
        'She still says, "Two coppers," flat as slate.'
    )
    out = apply_final_emission_gate(
        {"player_facing_text": text, "tags": [], "context_separation_contract": cs},
        resolution={"kind": "barter", "prompt": pt},
        session=None,
        scene_id="market_stall",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("context_separation_failed") is True
    assert meta.get("context_separation_repaired") is False
    assert meta.get("final_route") == "replaced"
    assert "context_separation_unsatisfied_at_boundary_no_lead_drop" in (meta.get("rejection_reasons_sample") or [])


def test_gate_context_separation_fail_pressure_monologue_replaces_non_social(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    pt = "What does the loaf cost today?"
    cs = build_context_separation_contract(player_text=pt, resolution={"kind": "barter"})
    text = (
        "The war along the border has everyone on edge, and coin means nothing next to survival. "
        "Factions trade rumors faster than grain, and the capital's politics swallow small questions whole."
    )
    out = apply_final_emission_gate(
        {"player_facing_text": text, "tags": [], "context_separation_contract": cs},
        resolution={"kind": "barter", "prompt": pt},
        session=None,
        scene_id="market_stall",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("context_separation_failed") is True
    assert meta.get("final_route") == "replaced"


def test_gate_context_separation_tone_escalation_with_city_pressure_fails(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    pt = "Good morning. A loaf, please."
    cs = build_context_separation_contract(
        player_text=pt,
        resolution={"kind": "barter"},
        tone_escalation_contract={"allow_verbal_pressure": False, "allow_explicit_threat": False},
    )
    text = (
        "The city is on edge tonight, so back off and drop it—this is not the time for questions."
    )
    out = apply_final_emission_gate(
        {"player_facing_text": text, "tags": [], "context_separation_contract": cs},
        resolution={"kind": "barter", "prompt": pt},
        session=None,
        scene_id="market_stall",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("context_separation_failed") is True
    assert "ambient_pressure_forced_tone_shift" in (meta.get("context_separation_failure_reasons") or [])


def test_gate_context_separation_substitution_fail_then_replace(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    pt = "What is the price today?"
    cs = build_context_separation_contract(player_text=pt, resolution={"kind": "barter"})
    text = (
        "It is impossible to say with the unrest what the price is; "
        "any answer is swallowed by the instability of the war."
    )
    out = apply_final_emission_gate(
        {"player_facing_text": text, "tags": [], "context_separation_contract": cs},
        resolution={"kind": "barter", "prompt": pt},
        session=None,
        scene_id="market_stall",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("context_separation_failed") is True
    assert meta.get("final_route") == "replaced"


def test_gate_context_separation_pressure_overweight_replaces(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    pt = "What is your name?"
    cs = build_context_separation_contract(player_text=pt, resolution={"kind": "social_probe"})
    text = (
        "The border war reshapes every oath. "
        "Unrest makes factions bold and the crown brittle. "
        "Invasion rumors outrun truth, and politics turns markets into maps. "
        "Empire scouts watch the passes, and the realm tears at its seams."
    )
    out = apply_final_emission_gate(
        {"player_facing_text": text, "tags": [], "context_separation_contract": cs},
        resolution={"kind": "social_probe", "prompt": pt},
        session=None,
        scene_id="scene",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("context_separation_failed") is True
    assert "pressure_overweighting" in (meta.get("context_separation_failure_reasons") or [])


# --- Player-facing narration purity + answer-shape primacy (Block 3) ------------------------------

# Ownership note:
# This cluster owns final-gate packaging for purity, answer-shape primacy, and
# response-type enforcement. Semantic repair breadth belongs in validators/repairs;
# add cases here only for gate sequencing, final text packaging, or FEM projection.


def _purity_contract(**kwargs):
    return build_player_facing_narration_purity_contract(**kwargs)


# Opening adapter/tuple/helper semantics: tests/test_final_emission_opening_fallback.py
# Owner-bucket read mapping: tests/test_opening_fallback_owner_bucket.py


def test_enforce_response_type_contract_marks_upstream_absent_for_answer_without_prepared_text():
    text, dbg = feg._enforce_response_type_contract(
        "Only mist between the torches.",
        gm_output={
            "response_policy": {"response_type_contract": response_type_contract("answer")},
            "upstream_prepared_emission": {},
        },
        resolution={"kind": "observe", "prompt": "What do I see?"},
        session={},
        scene_id="yard",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )
    assert dbg.get("response_type_upstream_prepared_absent") is True
    assert dbg.get("response_type_candidate_ok") is False
    assert text == "Only mist between the torches."


def _assert_known_realization_family(value: str) -> None:
    assert value in FALLBACK_FAMILIES


def test_opening_validator_rejects_investigation_continuation_language():
    failures = feg.validate_opening_output("Nearby crates appear disturbed.", opening_validation_context())

    assert "continuation_or_investigation_language" in failures
    assert "invalid_sentence_structure" in failures


def test_opening_validator_rejects_fragment_sentence():
    failures = feg.validate_opening_output("At the Cinderwatch Gate District, rain and refugees.", opening_validation_context())

    assert "invalid_sentence_structure" in failures


def test_opening_validator_rejects_opening_without_actionable_hook():
    failures = feg.validate_opening_output(
        "Cinderwatch Gate District. Rain spatters soot-dark stone while refugees and wagons clog the muddy approach.",
        opening_validation_context(),
    )

    assert "missing_hook" in failures


def test_full_gate_malformed_opening_payload_without_upstream_repair_is_sealed_gate(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Block C9: full-gate path cannot turn malformed opening payloads into unknown/compat ownership."""
    gm_output = opening_gm_output()
    gm_output[UPSTREAM_PREPARED_OPENING_FALLBACK_KEY] = {
        "prepared_opening_fallback_text": EXPECTED_FRONTIER_GATE_OPENING_FALLBACK,
    }
    gm_output["player_facing_text"] = "Nearby crates appear disturbed."
    gm_output["tags"] = []

    def _skip_upstream_repair(out: dict[str, Any] | None, *, resolution: dict[str, Any] | None) -> None:
        return None

    monkeypatch.setattr(feg, "maybe_attach_upstream_prepared_opening_fallback_payload", _skip_upstream_repair)
    out = apply_final_emission_gate(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )

    fem = final_emission_meta_from_output(out)
    assert_final_emission_meta_contains(
        fem,
        response_type_repair_kind="opening_deterministic_fallback_failed_closed",
        opening_fallback_authorship_source=None,
    )
    assert fem.get("opening_fallback_authorship_source") != OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL
    assert_fallback_owner_bucket(OPENING_FALLBACK_OWNER_SEALED_GATE, meta=fem)


def _rich_scene_opening_candidate() -> str:
    return (
        "Rain spatters soot-dark stone across Cinderwatch's eastern gate while frayed banners snap "
        "above the muddy approach. You stand in the churned mud before the gate as refugees press "
        "shoulder to shoulder around the wagon line and guards hold the choke under shouted orders. "
        "A tavern runner weaves through the crush, calling offers of hot stew and paid rumor as the "
        "notice board waits beside the arch. The queue inches forward in fits, wagon wheels grinding "
        "through black ruts while wet canvas slaps against overloaded carts and the smell of damp wool, "
        "smoke, and sour road dust clings to everyone close enough to breathe on you. Somewhere ahead, "
        "a guard captain's voice cuts through the mutter of the crowd, sharp enough to make shoulders "
        "hunch and conversations die for a heartbeat before the pressure of bodies closes in again. "
        "You can read the notice board, press the guards, approach the tavern runner, or watch the "
        "silent figure in the crush."
    )


def test_scene_opening_accepted_candidate_promotes_over_short_stale_player_text(monkeypatch):
    short = "You stand at Cinderwatch's eastern gate in the rain. Guards hold the choke."
    rich = _rich_scene_opening_candidate()
    orig_enforce = feg._enforce_response_type_contract

    def _select_rich_candidate(candidate_text, **kwargs):
        assert candidate_text == short
        return orig_enforce(rich, **kwargs)

    def _late_stale_rewrite(out, *, text, **kwargs):
        return short, [], False

    monkeypatch.setattr(feg, "_enforce_response_type_contract", _select_rich_candidate)
    monkeypatch.setattr(feg, "_apply_interaction_continuity_emission_step", _late_stale_rewrite)

    gm_output = opening_gm_output()
    gm_output["player_facing_text"] = short
    gm_output["tags"] = []
    out = apply_final_emission_gate(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )
    emitted = str(out.get("player_facing_text") or "")
    emission_debug = ((out.get("metadata") or {}).get("emission_debug") or {})
    fem = read_final_emission_meta_dict(out) or {}

    assert emitted == rich
    assert emitted != short
    assert emission_debug.get("scene_opening_candidate_len") == len(rich)
    assert emission_debug.get("scene_opening_emitted_len") == len(rich)
    assert emission_debug.get("scene_opening_candidate_emitted_match") is True
    assert emission_debug.get("scene_opening_accepted_candidate_promoted") is True
    assert emission_debug.get("response_type_candidate_preview") == emission_debug.get("response_type_emitted_preview")
    assert fem.get("response_type_candidate_preview") == fem.get("response_type_emitted_preview")


# Full-gate/FEM integration pins: these keep final output and emitted metadata
# propagation observable after adapter selection; they do not define adapter
# selection policy.
def test_canonical_final_gate_opening_fallback_fem_is_upstream_prepared_not_compatibility_local() -> None:
    gm_output = opening_gm_output()
    gm_output["player_facing_text"] = "Nearby crates appear disturbed."
    gm_output["tags"] = []

    out = apply_final_emission_gate(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )

    fem = final_emission_meta_from_output(out)
    assert out["player_facing_text"] == EXPECTED_FRONTIER_GATE_OPENING_FALLBACK
    assert_final_emission_meta_contains(
        fem,
        final_emitted_source="opening_deterministic_fallback",
        fallback_family_used="scene_opening",
        response_type_repair_kind="opening_deterministic_fallback",
        opening_fallback_context_source="opening_curated_facts",
        opening_fallback_authorship_source=OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED,
    )
    family = fem[REALIZATION_FALLBACK_FAMILY_FIELD]
    assert family in FALLBACK_FAMILIES
    assert family == UPSTREAM_PREPARED_EMISSION
    assert family != LEGACY_DIEGETIC_FALLBACK
    assert fem.get("opening_fallback_authorship_source") != OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL
    assert_opening_fallback_source(
        fem,
        final_emitted_source="opening_deterministic_fallback",
        authorship_source=OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED,
        owner_bucket=OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
    )


def test_canonical_final_gate_auto_attaches_upstream_opening_fallback_before_emission(monkeypatch) -> None:
    gm_output = opening_gm_output()
    assert UPSTREAM_PREPARED_OPENING_FALLBACK_KEY not in gm_output
    gm_output["player_facing_text"] = "Nearby crates appear disturbed."
    gm_output["tags"] = []

    def _should_not_run_gate_local_deterministic_opening(*_a: Any, **_k: Any) -> tuple[str, dict]:
        raise AssertionError("gate-local deterministic opening must not run when upstream payload is present")

    monkeypatch.setattr(opening_deterministic_fallback, "deterministic_opening_fallback_text_and_meta", _should_not_run_gate_local_deterministic_opening)
    out = apply_final_emission_gate(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )

    pay = out.get(UPSTREAM_PREPARED_OPENING_FALLBACK_KEY)
    assert isinstance(pay, dict)
    assert pay["prepared_opening_fallback_text"] == EXPECTED_FRONTIER_GATE_OPENING_FALLBACK
    assert out["player_facing_text"] == EXPECTED_FRONTIER_GATE_OPENING_FALLBACK
    fem = final_emission_meta_from_output(out)
    assert_final_emission_meta_contains(
        fem,
        final_emitted_source="opening_deterministic_fallback",
        fallback_family_used="scene_opening",
    )
    assert fem[REALIZATION_FALLBACK_FAMILY_FIELD] == UPSTREAM_PREPARED_EMISSION
    assert_opening_fallback_source(
        fem,
        final_emitted_source="opening_deterministic_fallback",
        authorship_source=OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED,
        owner_bucket=OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED,
        forbid_compat_local_authorship=True,
    )


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


def test_block_n_opening_attach_build_failure_fails_closed_preserves_block_m_telemetry(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Block N: attach build failure on full gate entry fails closed; Block M telemetry preserved; no compat compose."""
    import game.upstream_response_repairs as urr

    gm_output = opening_gm_output()
    gm_output.pop(UPSTREAM_PREPARED_OPENING_FALLBACK_KEY, None)
    gm_output["player_facing_text"] = "Nearby crates appear disturbed."
    gm_output["tags"] = []

    def boom(_mapping: object) -> dict[str, object]:
        raise RuntimeError("simulated upstream attach build failure")

    monkeypatch.setattr(urr, "build_upstream_prepared_opening_fallback_payload", boom)

    calls: list[str] = []
    real_det = _deterministic_opening_under_test

    def wrapped_det(out: Mapping[str, Any] | None) -> tuple[str, dict[str, Any]]:
        calls.append("deterministic")
        return real_det(out)

    monkeypatch.setattr(opening_deterministic_fallback, "deterministic_opening_fallback_text_and_meta", wrapped_det)

    out = apply_final_emission_gate(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )
    fem = read_final_emission_meta_dict(out) or {}
    assert fem.get("opening_upstream_prepare_attach_build_failed") is True
    assert fem.get("opening_upstream_prepare_attach_failure_exc_type") == "RuntimeError"
    assert fem.get("opening_upstream_prepare_attach_no_usable_payload_after_attempt") is True
    # Response-type path emits the sealed marker; downstream visibility/N4 may replace with global stock (cf. Block H full gate).
    assert out["player_facing_text"] == "For a breath, the scene holds while voices shift around you."
    assert fem.get("opening_fallback_failed_closed") is True
    assert fem.get("opening_fallback_compatibility_local_disabled") is True
    assert fem.get("blocked_repair_kind") == "opening_upstream_prepare_attach_failed"
    assert fem.get("opening_fallback_authorship_source") is None
    assert fem.get("response_type_repair_kind") == "opening_deterministic_fallback_failed_closed"
    assert opening_fallback_owner_bucket_from_meta(fem) == OPENING_FALLBACK_OWNER_SEALED_GATE
    assert not calls


def test_block_m_successful_upstream_attach_has_no_attach_failure_telemetry() -> None:
    gm_output = opening_gm_output()
    gm_output["player_facing_text"] = "Nearby crates appear disturbed."
    gm_output["tags"] = []
    out = apply_final_emission_gate(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )
    fem = read_final_emission_meta_dict(out) or {}
    assert fem.get("opening_upstream_prepare_attach_build_failed") is False
    assert fem.get("opening_upstream_prepare_attach_no_usable_payload_after_attempt") is False
    assert fem.get("opening_upstream_prepare_attach_failure_exc_type") in (None, "")
    assert out["player_facing_text"] == EXPECTED_FRONTIER_GATE_OPENING_FALLBACK
    assert fem.get("opening_fallback_authorship_source") == OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED
    assert opening_fallback_owner_bucket_from_meta(fem) == OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED


def test_fail_closed_sealed_gate_empty_curated_facts_skips_upstream_opening_payload() -> None:
    gm_output = opening_gm_output()
    gm_output["opening_curated_facts"] = []
    gm_output["opening_selector_selected_facts"] = []
    md = gm_output.setdefault("metadata", {})
    em = md.setdefault("emission_debug", {})
    em["opening_curated_facts_present"] = False
    em["opening_curated_facts_count"] = 0
    em["opening_selector_selected_facts"] = []
    em["opening_curated_facts"] = []
    gm_output["player_facing_text"] = "Nearby crates appear disturbed."
    gm_output["tags"] = []

    out = apply_final_emission_gate(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )

    assert UPSTREAM_PREPARED_OPENING_FALLBACK_KEY not in out
    assert out["player_facing_text"] == "For a breath, the scene holds while voices shift around you."
    fem = read_final_emission_meta_dict(out) or {}
    assert fem["final_route"] == "replaced"
    assert fem["final_emitted_source"] == "acceptance_quality_global_scene_fallback"
    assert fem[REALIZATION_FALLBACK_FAMILY_FIELD] == GATE_TERMINAL_REPAIR
    assert fem["response_type_repair_kind"] == "opening_deterministic_fallback_failed_closed"
    assert fem.get("opening_fallback_authorship_source") is None
    assert fem.get("opening_fallback_authorship_source") != OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL
    assert fem.get("opening_fallback_compatibility_local_disabled") is True
    assert fem.get("opening_fallback_missing_upstream_prepared_payload") is True
    assert opening_fallback_owner_bucket_from_meta(fem) == OPENING_FALLBACK_OWNER_SEALED_GATE


def test_canonical_final_gate_prefers_upstream_prepared_payload_when_present(monkeypatch) -> None:
    gm_output = opening_gm_output()
    gm_output["player_facing_text"] = "Nearby crates appear disturbed."
    gm_output["tags"] = []
    gm_output[UPSTREAM_PREPARED_OPENING_FALLBACK_KEY] = build_upstream_prepared_opening_fallback_payload(gm_output)

    def _should_not_run_local_deterministic_opening(*_a: Any, **_k: Any) -> tuple[str, dict]:
        raise AssertionError("gate-local deterministic opening must not run when upstream payload is present")

    monkeypatch.setattr(opening_deterministic_fallback, "deterministic_opening_fallback_text_and_meta", _should_not_run_local_deterministic_opening)
    out = apply_final_emission_gate(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )

    fem = read_final_emission_meta_dict(out) or {}
    assert out["player_facing_text"] == EXPECTED_FRONTIER_GATE_OPENING_FALLBACK
    assert fem["final_emitted_source"] == "opening_deterministic_fallback"
    assert fem["fallback_family_used"] == "scene_opening"
    assert fem[REALIZATION_FALLBACK_FAMILY_FIELD] == UPSTREAM_PREPARED_EMISSION
    assert fem["response_type_repair_kind"] == "opening_deterministic_fallback"
    assert fem["opening_fallback_context_source"] == "opening_curated_facts"
    assert fem.get("opening_fallback_authorship_source") == OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED
    assert fem.get("opening_fallback_authorship_source") != OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL
    assert opening_fallback_owner_bucket_from_meta(fem) == OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED


def test_final_gate_valid_opening_candidate_has_no_fallback_provenance() -> None:
    candidate = (
        "You stand in the churned mud before Cinderwatch's eastern gate as rain spatters soot-dark stone. "
        "Refugees press shoulder to shoulder around the wagon line while guards hold the choke. "
        "You can read the notice board or approach the guards."
    )
    gm_output = opening_gm_output()
    gm_output["player_facing_text"] = candidate
    gm_output["tags"] = []

    out = apply_final_emission_gate(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )

    fem = read_final_emission_meta_dict(out) or {}
    assert out["player_facing_text"] == candidate
    assert fem["final_emitted_source"] == "generated_candidate"
    assert fem.get("fallback_family_used") is None
    assert fem.get(REALIZATION_FALLBACK_FAMILY_FIELD) is None
    assert isinstance(out.get(UPSTREAM_PREPARED_OPENING_FALLBACK_KEY), dict)
    assert fem.get("opening_fallback_authorship_source") is None


def test_final_gate_upstream_prepared_emission_branch_records_upstream_family() -> None:
    out = apply_final_emission_gate(
        {
            "player_facing_text": "Mist gathers without answering.",
            "tags": [],
            "response_policy": {"response_type_contract": response_type_contract("answer")},
            UPSTREAM_PREPARED_EMISSION_KEY: {
                "prepared_answer_fallback_text": "Yes. The east gate is open until dusk.",
                "upstream_prepared_emission_attribution": "unit_upstream_answer",
            },
        },
        resolution={"kind": "question", "prompt": "Is the east gate open?"},
        session={},
        scene_id="yard",
        world={},
    )

    fem = read_final_emission_meta_dict(out) or {}
    assert out["player_facing_text"] == "Yes. The east gate is open until dusk."
    assert fem["final_route"] == "accept_candidate"
    assert fem["final_emitted_source"] == "answer_upstream_prepared_repair"
    assert fem["response_type_repair_kind"] == "answer_upstream_prepared_repair"
    assert fem["upstream_prepared_emission_used"] is True
    assert fem["upstream_prepared_emission_valid"] is True
    assert fem["upstream_prepared_emission_source"] == "unit_upstream_answer"
    lineage = fem.get("final_emission_mutation_lineage")
    assert "response_type_repair" in lineage
    assert "prepared_emission_selection" in lineage
    assert "finalize_packaging" in lineage
    family = fem[REALIZATION_FALLBACK_FAMILY_FIELD]
    _assert_known_realization_family(family)
    assert family == UPSTREAM_PREPARED_EMISSION
    assert family != GATE_TERMINAL_REPAIR


@pytest.mark.parametrize(
    ("required", "prepared_field", "invalid_prepared", "repair_kind"),
    [
        ("answer", "prepared_answer_fallback_text", "Mist gathers without answering.", "answer_upstream_prepared_repair"),
        (
            "action_outcome",
            "prepared_action_fallback_text",
            "You consider the lock.",
            "action_outcome_upstream_prepared_repair",
        ),
    ],
)
def test_enforce_response_type_contract_rejects_malformed_prepared_answer_action_without_synthesis(
    required: str,
    prepared_field: str,
    invalid_prepared: str,
    repair_kind: str,
) -> None:
    candidate = "Only mist between the torches."

    text, dbg = feg._enforce_response_type_contract(
        candidate,
        gm_output={
            "response_policy": {"response_type_contract": response_type_contract(required)},
            UPSTREAM_PREPARED_EMISSION_KEY: {
                prepared_field: invalid_prepared,
                "upstream_prepared_emission_attribution": f"unit_invalid_{required}",
            },
        },
        resolution={"kind": "investigate", "prompt": "Can I force the lock?"},
        session={},
        scene_id="yard",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )

    assert text == candidate
    assert text != invalid_prepared
    assert dbg.get("response_type_candidate_ok") is False
    assert dbg.get("response_type_repair_kind") == repair_kind
    assert dbg.get("upstream_prepared_emission_used") is False
    assert dbg.get("upstream_prepared_emission_valid") is False
    assert dbg.get("upstream_prepared_emission_source") == f"unit_invalid_{required}"
    assert dbg.get("upstream_prepared_emission_reject_reason")


@pytest.mark.parametrize(
    ("required", "prompt"),
    [
        ("answer", "What do I see?"),
        ("action_outcome", "I force the lock."),
    ],
)
def test_enforce_response_type_contract_absent_prepared_answer_action_keeps_candidate_without_synthesis(
    required: str,
    prompt: str,
) -> None:
    candidate = "Only mist between the torches."

    text, dbg = feg._enforce_response_type_contract(
        candidate,
        gm_output={
            "response_policy": {"response_type_contract": response_type_contract(required)},
            UPSTREAM_PREPARED_EMISSION_KEY: {},
        },
        resolution={"kind": "investigate", "prompt": prompt},
        session={},
        scene_id="yard",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )

    assert text == candidate
    assert dbg.get("response_type_upstream_prepared_absent") is True
    assert dbg.get("response_type_candidate_ok") is False
    assert dbg.get("response_type_repair_used") is False
    assert dbg.get("response_type_repair_kind") is None
    assert dbg.get("upstream_prepared_emission_source") == "absent"


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


# Visibility/sealed gate integration: routing and FEM projection only (legality in
# tests/test_final_emission_visibility.py; helper shaping in test_final_emission_sealed_fallback.py).
def test_visibility_safe_fallback_final_emitted_source_snapshot() -> None:
    """Visibility replace uses sealed tuples for text; FEM source pins global_scene_fallback today."""
    session, world, scene, sid = _visibility_offscene_npc_gate_bundle()
    out = apply_final_emission_gate(
        {"player_facing_text": "Lord Aldric watches the checkpoint from the square.", "tags": []},
        resolution={"kind": "observe", "prompt": "I look."},
        session=session,
        scene_id=sid,
        world=world,
        scene=scene,
    )
    tl = [str(t) for t in (out.get("tags") or []) if isinstance(t, str)]
    assert "visibility_enforcement_replaced" in tl
    fem = final_emission_meta_from_output(out)
    assert_final_emission_meta_contains(
        fem,
        final_route="replaced",
        final_emitted_source="global_scene_fallback",
    )
    assert fem.get(REALIZATION_FALLBACK_FAMILY_FIELD) == GATE_TERMINAL_REPAIR
    assert_sealed_fallback_owner_bucket(fem, SEALED_FALLBACK_OWNER_SEALED_GATE)


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
    assert n4_fem["sealed_fallback_owner_bucket"] == SEALED_FALLBACK_OWNER_SEALED_GATE
    assert gen_fem["sealed_fallback_owner_bucket"] == SEALED_FALLBACK_OWNER_SEALED_GATE
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
    assert ss_fem["sealed_fallback_owner_bucket"] == SEALED_FALLBACK_OWNER_STRICT_SOCIAL_SEALED
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
    assert fem.get("sealed_fallback_owner_bucket") is None
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
    """Regression anchor: Block AG tests must stay importable so selector/order contracts do not drift unnoticed."""
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


def test_canonical_missing_curated_facts_upstream_prepared_payload_still_wins(monkeypatch) -> None:
    gm_output = opening_gm_output()
    gm_output[UPSTREAM_PREPARED_OPENING_FALLBACK_KEY] = build_upstream_prepared_opening_fallback_payload(gm_output)
    gm_output.pop("opening_curated_facts", None)
    gm_output["player_facing_text"] = "Nearby crates appear disturbed."
    gm_output["tags"] = []

    def _boom(*_a: Any, **_k: Any) -> tuple[str, dict]:
        raise AssertionError("compatibility-local deterministic opening must not run when upstream snapshot is attached")

    monkeypatch.setattr(opening_deterministic_fallback, "deterministic_opening_fallback_text_and_meta", _boom)
    out = apply_final_emission_gate(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )
    assert out["player_facing_text"] == EXPECTED_FRONTIER_GATE_OPENING_FALLBACK
    fem = read_final_emission_meta_dict(out) or {}
    assert fem.get("opening_fallback_authorship_source") == OPENING_FALLBACK_AUTHORSHIP_UPSTREAM_PREPARED
    assert fem.get("opening_fallback_authorship_source") != OPENING_FALLBACK_AUTHORSHIP_COMPATIBILITY_LOCAL
    assert fem.get("opening_fallback_missing_curated_facts") is True
    assert fem.get("response_type_repair_kind") == "opening_deterministic_fallback"
    assert opening_fallback_owner_bucket_from_meta(fem) == OPENING_FALLBACK_OWNER_UPSTREAM_PREPARED


def test_fail_closed_sealed_gate_missing_curated_facts_records_fem() -> None:
    gm_output = opening_gm_output()
    gm_output.pop("opening_curated_facts", None)
    gm_output["player_facing_text"] = "Nearby crates appear disturbed."
    gm_output["tags"] = []

    out = apply_final_emission_gate(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )

    fem = read_final_emission_meta_dict(out) or {}
    assert fem.get("opening_fallback_missing_curated_facts") is True
    assert fem.get("blocked_repair_kind") == "opening_missing_curated_facts"
    assert fem.get("response_type_repair_kind") == "opening_deterministic_fallback_failed_closed"
    assert opening_fallback_owner_bucket_from_meta(fem) == OPENING_FALLBACK_OWNER_SEALED_GATE


# Ownership note:
# This cluster owns downstream gate integration for purity and answer-shape
# repairs. Semantic text-repair behavior belongs in validator/repair owners; add
# cases here only for final-gate pass/repair/replace routing or final packaging.


def test_resolve_player_facing_narration_purity_contract_from_response_policy():
    c = _purity_contract()
    gm = {"response_policy": {"player_facing_narration_purity": c}}
    got, src = feg._resolve_player_facing_narration_purity_contract(gm)
    assert got is c
    assert src == "response_policy"


def test_gate_purity_and_asp_pass_clean_observation(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    out = apply_final_emission_gate(
        {
            "player_facing_text": "Rain hammers the slate roof; torchlight shivers in the gutter below.",
            "tags": [],
            "player_facing_narration_purity_contract": _purity_contract(),
            "response_policy": {"response_type_contract": response_type_contract("neutral_narration")},
        },
        resolution={"kind": "observe", "prompt": "I look around the street."},
        session={},
        scene_id="market_lane",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("player_facing_narration_purity_failed") is False
    assert meta.get("answer_shape_primacy_failed") is False
    assert "Rain" in (out.get("player_facing_text") or "")


def test_gate_purity_and_asp_pass_scene_transition_arrival(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    out = apply_final_emission_gate(
        {
            "player_facing_text": (
                "You emerge into the lower ward—smoke, shouted names, the harbor's brine on the wind."
            ),
            "tags": [],
            "player_facing_narration_purity_contract": _purity_contract(),
            "response_policy": {"response_type_contract": response_type_contract("neutral_narration")},
        },
        resolution={
            "kind": "travel",
            "prompt": "I take the postern into the ward.",
            "resolved_transition": True,
        },
        session={},
        scene_id="lower_ward",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("answer_shape_primacy_failed") is False
    assert "emerge" in (out.get("player_facing_text") or "").lower()


def test_gate_purity_pass_npc_quoted_command_in_observe(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    text = (
        'The sergeant does not raise her voice. "Move toward the gate, now," she says, '
        "and the line stiffens as if pulled by a single wire."
    )
    out = apply_final_emission_gate(
        {
            "player_facing_text": text,
            "tags": [],
            "player_facing_narration_purity_contract": _purity_contract(),
            "response_policy": {"response_type_contract": response_type_contract("neutral_narration")},
        },
        resolution={"kind": "observe", "prompt": "I watch the line."},
        session={},
        scene_id="gate_yard",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("player_facing_narration_purity_failed") is False
    assert "gate" in (out.get("player_facing_text") or "").lower()


def test_gate_purity_and_asp_pass_action_outcome_then_brief_consequence(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    text = (
        "You thumb the latch; it gives with a dry snap. "
        "Patrol whistles tighten two streets over, a thin urgent sound against the rain."
    )
    out = apply_final_emission_gate(
        {
            "player_facing_text": text,
            "tags": [],
            "player_facing_narration_purity_contract": _purity_contract(),
            "response_policy": {"response_type_contract": response_type_contract("action_outcome")},
        },
        resolution={"kind": "interact", "prompt": "I try the latch on the side door."},
        session={},
        scene_id="alley_door",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("answer_shape_primacy_failed") is False
    assert "latch" in (out.get("player_facing_text") or "").lower()


def test_gate_purity_repairs_scaffold_header_leak(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    raw = "Consequence / Opportunity:\nThe patrol's torchlight sweeps the far arch."
    out = apply_final_emission_gate(
        {
            "player_facing_text": raw,
            "tags": [],
            "player_facing_narration_purity_contract": _purity_contract(),
            "response_policy": {"response_type_contract": response_type_contract("neutral_narration")},
        },
        resolution={"kind": "observe", "prompt": "I glance up the street."},
        session={},
        scene_id="arch_lane",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("player_facing_narration_purity_failed") is True
    assert meta.get("player_facing_narration_purity_repaired") is False
    assert meta.get("final_route") == "replaced"


def test_gate_purity_repairs_coaching_language(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    raw = "You weigh what you just tried near the checkpoint; rain drums on the slate roof."
    out = apply_final_emission_gate(
        {
            "player_facing_text": raw,
            "tags": [],
            "player_facing_narration_purity_contract": _purity_contract(),
            "response_policy": {"response_type_contract": response_type_contract("neutral_narration")},
        },
        resolution={"kind": "observe", "prompt": "I listen at the checkpoint."},
        session={},
        scene_id="frontier_gate",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("player_facing_narration_purity_failed") is True
    assert meta.get("final_route") == "replaced"


def test_gate_purity_repairs_ui_label_leak(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    raw = "Take the exit labeled North and you smell cold river air beyond the arch."
    out = apply_final_emission_gate(
        {
            "player_facing_text": raw,
            "tags": [],
            "player_facing_narration_purity_contract": _purity_contract(),
            "response_policy": {"response_type_contract": response_type_contract("neutral_narration")},
        },
        resolution={"kind": "observe", "prompt": "I scan for a way out."},
        session={},
        scene_id="river_arch",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("player_facing_narration_purity_failed") is True
    assert meta.get("final_route") == "replaced"


def test_gate_asp_repairs_observe_when_pressure_leads_concrete_observation(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    raw = (
        "The ward's tension mounts; confrontation feels inevitable. "
        "You hear boots on wet cobbles to your left, uneven and hurried."
    )
    out = apply_final_emission_gate(
        {
            "player_facing_text": raw,
            "tags": [],
            "player_facing_narration_purity_contract": _purity_contract(),
            "response_policy": {"response_type_contract": response_type_contract("neutral_narration")},
        },
        resolution={"kind": "observe", "prompt": "I listen for movement."},
        session={},
        scene_id="lower_ward",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("answer_shape_primacy_failed") is True
    assert meta.get("final_route") == "replaced"


def test_gate_purity_strips_transition_scaffold_on_travel(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    raw = "The next beat is yours. You emerge onto the quay, ropes creaking, gulls wheeling overhead."
    out = apply_final_emission_gate(
        {
            "player_facing_text": raw,
            "tags": [],
            "player_facing_narration_purity_contract": _purity_contract(),
            "response_policy": {"response_type_contract": response_type_contract("neutral_narration")},
        },
        resolution={"kind": "travel", "prompt": "I head down to the quay.", "resolved_transition": True},
        session={},
        scene_id="stone_quay",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("player_facing_narration_purity_failed") is True
    assert meta.get("final_route") == "replaced"


def test_gate_asp_triggers_replace_when_no_observation_payload(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    raw = (
        "Unrest makes factions bold and the crown brittle. "
        "Invasion rumors outrun truth, and politics turns markets into maps."
    )
    out = apply_final_emission_gate(
        {
            "player_facing_text": raw,
            "tags": [],
            "player_facing_narration_purity_contract": _purity_contract(),
            "response_policy": {"response_type_contract": response_type_contract("neutral_narration")},
        },
        resolution={"kind": "observe", "prompt": "What do I see on the street?"},
        session={},
        scene_id="market_square",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("answer_shape_primacy_failed") is True
    assert meta.get("final_route") == "replaced"


# --- Social response structure downstream integration (orchestration + metadata) -----------------
# Direct prompt-contract semantics live in tests/test_prompt_context.py; these checks verify
# gate ordering, metadata merge paths, and repair behavior after the prompt bundle is shipped.
#
# Ownership note:
# This cluster owns route/speaker/social downstream orchestration and metadata.
# Social-response semantics belong to social emission/structure owners; add cases
# here only for gate ordering, skip reasons, strict-social routing, or FEM fields.


def _monoblob_dialogue_quote() -> str:
    core = " ".join(f"w{i}" for i in range(110))
    return f'Tavern Runner says "{core}."'


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


def test_non_strict_social_failed_repair_adds_unsatisfied_after_repair_reason(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    bad = _monoblob_dialogue_quote()
    pol = _dialogue_response_policy_with_social_structure()
    out = apply_final_emission_gate(
        {"player_facing_text": bad, "tags": [], "response_policy": pol},
        resolution={"kind": "observe", "prompt": "What does the runner say?"},
        session=None,
        scene_id="checkpoint",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("social_response_structure_passed") is False
    assert meta.get("social_response_structure_boundary_semantic_repair_disabled") is True
    assert meta.get("social_response_structure_repair_applied") is False
    assert _normalize_text(bad) == _normalize_text(str(out.get("player_facing_text") or ""))


def test_strict_social_failed_repair_does_not_add_unsatisfied_after_repair_reason(monkeypatch):
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
    bad = _monoblob_dialogue_quote()

    def fake_build(candidate_text, *, resolution, tags, session, scene_id, world):
        return bad, dict(stub_details)

    monkeypatch.setattr(feg, "build_final_strict_social_response", fake_build)
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    pol = _dialogue_response_policy_with_social_structure()
    out = apply_final_emission_gate(
        {"player_facing_text": bad, "tags": [], "response_policy": pol},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    meta = read_final_emission_meta_dict(out) or {}
    txt = out.get("player_facing_text") or ""
    assert "w0" in txt and "w50" in txt
    assert meta.get("social_response_structure_passed") is False
    assert meta.get("social_response_structure_repair_passed") is False
    ins = meta.get("social_response_structure_inspect")
    assert isinstance(ins, dict) and ins.get("failed") is True
    assert "final_emission_gate_replaced" not in (out.get("tags") or [])
    assert "social_response_structure_unsatisfied_after_repair" not in (meta.get("rejection_reasons_sample") or [])


def test_bare_speech_attribution_shell_line_heuristic() -> None:
    assert feg._is_bare_speech_attribution_shell_line("Tavern Runner says") is True
    assert feg._is_bare_speech_attribution_shell_line("  Runner replies  ") is True
    assert feg._is_bare_speech_attribution_shell_line("") is True
    assert feg._is_bare_speech_attribution_shell_line('Runner mutters, "East."') is False
    assert feg._is_bare_speech_attribution_shell_line("Rain falls hard on the square.") is False


def test_subtractive_dialogue_strip_on_long_monoblob_yields_shell_not_playable_narration() -> None:
    stripped = feg._strip_dialogue_from_text(_monoblob_dialogue_quote())
    assert '"' not in stripped
    assert feg._is_bare_speech_attribution_shell_line(stripped)


def test_strict_social_long_quoted_line_retains_speaker_and_dialogue_payload(monkeypatch) -> None:
    """Invalid dialogue plan must not truncate strict-social output to a bare '… says' tail."""
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
    bad = _monoblob_dialogue_quote()

    def fake_build(candidate_text, *, resolution, tags, session, scene_id, world):
        return bad, dict(stub_details)

    monkeypatch.setattr(feg, "build_final_strict_social_response", fake_build)
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    pol = _dialogue_response_policy_with_social_structure()
    out = apply_final_emission_gate(
        {"player_facing_text": bad, "tags": [], "response_policy": pol},
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    txt = str(out.get("player_facing_text") or "")
    low = txt.lower()
    assert "tavern runner" in low
    assert '"' in txt
    assert "w0" in low and "w109" in low
    banned = (
        "that is all i can give you",
        "from here, no",
        "no certain answer",
        "truth is still buried",
        "nothing in the scene",
        "scene holds",
        "hard to say",
        "i can only point you",
        "best lead",
    )
    for phrase in banned:
        assert phrase not in low, phrase


def test_social_response_structure_boundary_skips_list_to_prose_repair(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    pol = _dialogue_response_policy_with_social_structure()
    bullet = '- "East gate is two hundred feet south," he says.\n- "Patrols chart that lane nightly."'
    out = apply_final_emission_gate(
        {"player_facing_text": bullet, "tags": [], "response_policy": pol},
        resolution={"kind": "question", "prompt": "Where is the east gate?"},
        session=None,
        scene_id="gate_yard",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("social_response_structure_repair_applied") is False
    assert meta.get("social_response_structure_boundary_semantic_repair_disabled") is True
    assert meta.get("social_response_structure_passed") is False
    out_txt = out.get("player_facing_text") or ""
    assert "east gate" in out_txt.lower() and "patrols" in out_txt.lower()
    assert any(ln.lstrip().startswith("-") for ln in out_txt.splitlines() if ln.strip())


def test_social_response_structure_metadata_merged_on_layer_execution(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    pol = _dialogue_response_policy_with_social_structure()
    out = apply_final_emission_gate(
        {
            "player_facing_text": 'Watchman says "East road bends past the mill."',
            "tags": [],
            "response_policy": pol,
        },
        resolution={"kind": "question", "prompt": "Which way?"},
        session=None,
        scene_id="lane",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    for key in (
        "social_response_structure_checked",
        "social_response_structure_applicable",
        "social_response_structure_passed",
        "social_response_structure_failure_reasons",
        "social_response_structure_repair_applied",
        "social_response_structure_repair_changed_text",
        "social_response_structure_repair_passed",
        "social_response_structure_repair_mode",
        "social_response_structure_skip_reason",
        "social_response_structure_inspect",
    ):
        assert key in meta
    assert meta.get("social_response_structure_checked") is True
    assert meta.get("social_response_structure_applicable") is True
    assert meta.get("social_response_structure_passed") is True
    assert meta.get("social_response_structure_repair_applied") is False


def test_social_response_structure_skip_path_records_skip_reason_on_answer_completeness_failed():
    rtc = response_type_contract("dialogue")
    srs = _secondary_social_response_structure_contract("dialogue")
    gm = {"response_policy": {"response_type_contract": rtc, "social_response_structure": srs}}
    raw = '- "East gate is south," he says.\n- "Patrols watch it nightly."'
    text, meta, extra = feg._apply_social_response_structure_layer(
        raw,
        gm_output=gm,
        strict_social_details=None,
        response_type_debug={"response_type_candidate_ok": True},
        answer_completeness_meta={"answer_completeness_failed": True},
        strict_social_path=False,
    )
    assert text == raw
    assert extra == []
    assert meta.get("social_response_structure_skip_reason") == "answer_completeness_failed"
    assert meta.get("social_response_structure_checked") is False


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


def test_action_outcome_turn_social_response_structure_not_applicable(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    rtc = response_type_contract("action_outcome")
    srs = _secondary_social_response_structure_contract("action_outcome")
    raw = "You lift the bar; it groans, and the side door eases open a finger's width."
    out = apply_final_emission_gate(
        {"player_facing_text": raw, "tags": [], "response_policy": {"response_type_contract": rtc, "social_response_structure": srs}},
        resolution={"kind": "interact", "prompt": "I try the side door."},
        session=None,
        scene_id="alley",
        world={},
    )
    meta = read_final_emission_meta_dict(out) or {}
    assert meta.get("social_response_structure_applicable") is False
    assert meta.get("social_response_structure_failure_reasons") == []


def test_social_response_structure_coexists_with_tone_escalation_layer(monkeypatch):
    monkeypatch.setattr(feg, "_apply_visibility_enforcement", lambda out, **kwargs: out)
    order: list[str] = []
    orig_srs = feg._apply_social_response_structure_layer
    orig_te = feg._apply_tone_escalation_layer

    def srs(*args, **kwargs):
        order.append("social_response_structure")
        return orig_srs(*args, **kwargs)

    def te(*args, **kwargs):
        order.append("tone_escalation")
        return orig_te(*args, **kwargs)

    monkeypatch.setattr(feg, "_apply_social_response_structure_layer", srs)
    monkeypatch.setattr(feg, "_apply_tone_escalation_layer", te)
    pol = _dialogue_response_policy_with_social_structure()
    out = apply_final_emission_gate(
        {
            "player_facing_text": 'Clerk says "East ledger is closed until dawn."',
            "tags": [],
            "response_policy": pol,
        },
        resolution={"kind": "question", "prompt": "When does the east ledger open?"},
        session=None,
        scene_id="hall",
        world={},
    )
    assert order.index("social_response_structure") < order.index("tone_escalation")
    meta = read_final_emission_meta_dict(out) or {}
    assert "tone_escalation_checked" in meta
    assert meta.get("candidate_validation_passed") is True


# --- Appended global-visibility stock: last-mile owner is _finalize_emission_output (not sanitizer-only). ---

# Ownership note:
# This cluster owns packaging/final-output historical regression locks. If replay,
# classifier, or dashboard projections fail, investigate downstream projection
# first; add cases here only for final text containment or last-mile packaging.


def test_strip_appended_global_visibility_stock_multi_sentence_trailing():
    raw = (
        "The clerk taps the ledger. "
        "For a breath, the scene holds while voices shift around you."
    )
    stripped = feg._strip_appended_route_illegal_contamination_sentences(raw)
    assert stripped == "The clerk taps the ledger."


def test_strip_appended_global_visibility_stock_alt_sentence_variant():
    raw = "Fog hugs the river tents. For a breath, the scene stays still."
    assert feg._strip_appended_route_illegal_contamination_sentences(raw) == "Fog hugs the river tents."


def test_strip_placeholder_stock_single_sentence_output_unchanged():
    solo = "For a breath, the scene stays still."
    assert feg._strip_appended_route_illegal_contamination_sentences(solo) == solo


def test_strip_preserves_dialogue_sentence_containing_for_a_breath_stock_phrase():
    text = 'The runner shrugs. "For a breath, the scene stays still," she adds with a smirk.'
    assert feg._strip_appended_route_illegal_contamination_sentences(text) == text


def test_strip_preserves_interruption_setup_strips_only_trailing_stock_sentence():
    intr = (
        "The clerk starts to answer, but a shout from the square cuts across the room. "
        "For a breath, the scene holds while voices shift around you."
    )
    out = feg._strip_appended_route_illegal_contamination_sentences(intr)
    assert "shout from the square" in out.lower()
    assert "voices shift around you" not in out.lower()


def test_strip_preserves_paragraph_break_when_stripping_within_second_block():
    raw = "First block line.\n\nSecond block body. For a breath, the scene stays still."
    got = feg._strip_appended_route_illegal_contamination_sentences(raw)
    assert "\n\n" in got
    assert "First block line." in got
    assert "Second block body." in got
    assert "scene stays still" not in got.lower()


def test_strip_does_not_remove_unrelated_multi_sentence_atmosphere():
    raw = (
        "Mist threads between the tents. "
        "Somewhere a dog barks once, and the sound thins in damp air."
    )
    assert feg._strip_appended_route_illegal_contamination_sentences(raw) == raw


def test_finalize_emission_output_post_containment_reseals_appended_stock(monkeypatch):
    """Block I containment can revert to selector text after exit fingerprinting; stock strip must still win."""
    selector = (
        "Rain drums steady on the slate roof above. "
        "For a breath, the scene stays still."
    )
    out = {
        "player_facing_text": selector,
        "_final_emission_meta": {"final_route": "accept_candidate"},
        "tags": [],
        "metadata": {},
    }

    def _simulate_containment_revert(o: dict, **kwargs):
        o["player_facing_text"] = selector
        return False

    monkeypatch.setattr(feg, "_finalize_upstream_fallback_overwrite_containment", _simulate_containment_revert)
    pre = feg._normalize_text(selector)
    finalized = feg._finalize_emission_output(out, pre_gate_text=pre, fast_path=True)
    pft = (finalized.get("player_facing_text") or "").lower()
    assert "rain drums" in pft
    assert "scene stays still" not in pft
    fem = read_final_emission_meta_dict(finalized) or {}
    lineage = fem.get("final_emission_mutation_lineage")
    assert "finalize_route_illegal_strip" in lineage
    assert "finalize_packaging" in lineage
    assert "post_gate_mutation_detected" in lineage


# Ownership note:
# This cluster owns narrative-mode output orchestration and final replacement
# projection. Narrative-mode semantics belong to their direct contract validators;
# add cases here only for gate skip reasons, branch routing, or final FEM shape.


def _narrative_mode_plan_payload(contract: dict) -> dict:
    return {"prompt_context": {"narrative_plan": {"narrative_mode_contract": contract}}}


def test_narrative_mode_output_layer_runs_when_plan_contract_shipped() -> None:
    nmc = build_narrative_mode_contract(ctir=minimal_ctir_continuation())
    text = (
        "You still hold the sergeant's gaze; he nods once toward the east lane without breaking stride."
    )
    out = apply_final_emission_gate(
        {"player_facing_text": text, "tags": [], **_narrative_mode_plan_payload(nmc)},
        resolution={"kind": "observe", "prompt": "I wait."},
        session={},
        scene_id="lane_scene",
        world={},
    )
    fem = read_final_emission_meta_dict(out) or {}
    assert fem.get("narrative_mode_output_checked") is True
    assert fem.get("narrative_mode_output_passed") is True
    assert fem.get("narrative_mode_output_mode") == nmc["mode"] == "continuation"
    assert fem.get("narrative_mode_contract_mode") == "continuation"
    assert fem.get("narrative_mode_output_skip_reason") is None


def test_narrative_mode_output_opening_validation_runs_for_scene_opening_response_type() -> None:
    nmc = build_narrative_mode_contract(narration_obligations={"is_opening_scene": True})
    gm_output = opening_gm_output()
    gm_output["prompt_context"]["narrative_plan"]["narrative_mode_contract"] = nmc
    gm_output["player_facing_text"] = (
        "Cinderwatch Gate District gathers rain, refugees, wagons, guards, and torchlight "
        "around the eastern gate. You can read the notice board or approach the guards."
    )
    gm_output["tags"] = []

    out = apply_final_emission_gate(
        gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
    )
    fem = read_final_emission_meta_dict(out) or {}

    assert fem.get("response_type_required") == "scene_opening"
    assert fem.get("narrative_mode_output_checked") is True
    assert fem.get("narrative_mode_output_mode") == "opening"
    assert fem.get("narrative_mode_contract_mode") == "opening"


def test_narrative_mode_output_failure_reasons_in_fem_and_replace_route() -> None:
    nmc = build_narrative_mode_contract(ctir=minimal_ctir_continuation())
    bad = "You wake to a new day. The market unfolds around you as if nothing before it mattered."
    out = apply_final_emission_gate(
        {"player_facing_text": bad, "tags": [], **_narrative_mode_plan_payload(nmc)},
        resolution={"kind": "observe", "prompt": "I wait."},
        session={},
        scene_id="lane_scene",
        world={},
    )
    fem = read_final_emission_meta_dict(out) or {}
    assert fem.get("narrative_mode_output_checked") is True
    assert fem.get("narrative_mode_output_passed") is False
    assert "nmo:continuation:fresh_opening_reset_shape" in (fem.get("narrative_mode_output_failure_reasons") or [])
    assert fem.get("final_route") == "replaced"


def test_narrative_mode_output_skip_absent_contract() -> None:
    out = apply_final_emission_gate(
        {"player_facing_text": "The lane holds.", "tags": []},
        resolution={"kind": "observe", "prompt": "I look."},
        session={},
        scene_id="s",
        world={},
    )
    fem = read_final_emission_meta_dict(out) or {}
    assert fem.get("narrative_mode_output_checked") is False
    assert fem.get("narrative_mode_output_skip_reason") == "narrative_mode_contract_absent"


def test_narrative_mode_output_skip_disabled_contract() -> None:
    nmc = build_narrative_mode_contract(enabled=False)
    out = apply_final_emission_gate(
        {"player_facing_text": "You wake to a new day.", "tags": [], **_narrative_mode_plan_payload(nmc)},
        resolution={"kind": "observe", "prompt": "I wait."},
        session={},
        scene_id="s",
        world={},
    )
    fem = read_final_emission_meta_dict(out) or {}
    assert fem.get("narrative_mode_output_checked") is False
    assert fem.get("narrative_mode_output_skip_reason") == "narrative_mode_contract_disabled"


def test_narrative_mode_output_skip_invalid_contract_shape() -> None:
    bad = {
        "version": 1,
        "enabled": True,
        "mode": "continuation",
        "mode_family": "continuation",
        "source_signals": [],
        "prompt_obligations": {},
        "forbidden_moves": [],
        "debug": {"derivation_codes": []},
    }
    out = apply_final_emission_gate(
        {"player_facing_text": "The lane holds.", "tags": [], **_narrative_mode_plan_payload(bad)},
        resolution={"kind": "observe", "prompt": "I wait."},
        session={},
        scene_id="s",
        world={},
    )
    fem = read_final_emission_meta_dict(out) or {}
    assert fem.get("narrative_mode_output_checked") is False
    assert str(fem.get("narrative_mode_output_skip_reason") or "").startswith("narrative_mode_contract_invalid:")


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
