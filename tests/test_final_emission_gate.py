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
# This suite owns:
# - gate orchestration order
# - continuity step placement
# - repair-before-validation guarantees
#
# All other suites must consume outputs only.

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from game.acceptance_quality import (
    ACCEPTANCE_QUALITY_VERSION,
    build_acceptance_quality_contract,
    validate_and_repair_acceptance_quality,
)
from game.final_emission_meta import read_emission_debug_lane, read_final_emission_meta_dict

import json

import pytest

import game.final_emission_gate as feg
import game.scene_state_anchoring as ssa
from game.contract_registry import emergency_fallback_source_ids
from game.defaults import default_scene, default_session, default_world
from game.final_emission_gate import apply_final_emission_gate, get_speaker_selection_contract
from game.diegetic_fallback_narration import fallback_template_metadata
from game.narrative_mode_contract import build_narrative_mode_contract
from game.anti_railroading import build_anti_railroading_contract
from game.context_separation import build_context_separation_contract
from game.narrative_authority import build_narrative_authority_contract
from game.interaction_context import rebuild_active_scene_entities, set_social_target
from game.player_facing_narration_purity import build_player_facing_narration_purity_contract
from game.social_exchange_emission import effective_strict_social_resolution_for_emission
from game.storage import get_scene_runtime
from game.final_emission_text import _normalize_text
from tests.helpers.objective7_referent_fixtures import (
    minimal_full_referent_artifact,
    referent_compact_mirror,
)
from tests.test_narrative_mode_output_validator import _minimal_ctir_continuation

pytestmark = pytest.mark.unit


def _minimal_n4_narrative_plan(*, acceptance_quality: dict[str, Any] | None = None) -> dict[str, Any]:
    """Minimal ``prompt_context.narrative_plan`` for N4 gate tests (CTIR-backed ``narrative_mode_contract``).

    Omit *acceptance_quality* to assert N4 defaults when the plan ships no ``acceptance_quality_contract``.
    """
    nmc = build_narrative_mode_contract(ctir=_minimal_ctir_continuation())
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


def test_acceptance_quality_n4_subtractive_repair_when_plan_enabled() -> None:
    plan = _minimal_n4_narrative_plan(acceptance_quality={"enabled": True})
    out = apply_final_emission_gate(
        {"player_facing_text": _N4_REPAIRABLE_TWO_SENTENCE, "tags": [], "prompt_context": {"narrative_plan": plan}},
        resolution={"kind": "narrate", "prompt": "I hold position."},
        session=None,
        scene_id="lane_scene",
        world={},
    )
    fem = read_final_emission_meta_dict(out) or {}
    assert fem.get("acceptance_quality_checked") is True
    assert fem.get("acceptance_quality_passed") is True
    assert fem.get("acceptance_quality_repair_applied") is True
    assert "nothing will ever be the same" not in (out.get("player_facing_text") or "").lower()
    assert "sergeant" in (out.get("player_facing_text") or "").lower()


def test_acceptance_quality_n4_replace_when_floor_still_fails() -> None:
    plan = _minimal_n4_narrative_plan(acceptance_quality={"enabled": True})
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
    fem = read_final_emission_meta_dict(out) or {}
    assert fem.get("acceptance_quality_gate_replaced_candidate") is True
    assert fem.get("final_route") == "replaced"
    assert "nothing will ever be the same" not in (out.get("player_facing_text") or "").lower()


def test_acceptance_quality_n4_legacy_trailer_phrase_passthrough_without_plan() -> None:
    raw = _N4_TRAILER_LINE
    out = apply_final_emission_gate(
        {"player_facing_text": raw, "tags": []},
        resolution={"kind": "narrate", "prompt": "I wait."},
        session=None,
        scene_id="lane_scene",
        world={},
    )
    assert _normalize_text(out.get("player_facing_text") or "") == _normalize_text(raw)
    fem = read_final_emission_meta_dict(out) or {}
    assert fem.get("acceptance_quality_checked") is False
    assert fem.get("acceptance_quality_gate_replaced_candidate") is not True


def test_acceptance_quality_n4_respects_explicit_disable_with_plan() -> None:
    raw = _N4_TRAILER_LINE
    plan = _minimal_n4_narrative_plan(acceptance_quality={"enabled": False})
    out = apply_final_emission_gate(
        {"player_facing_text": raw, "tags": [], "prompt_context": {"narrative_plan": plan}},
        resolution={"kind": "narrate", "prompt": "I wait."},
        session=None,
        scene_id="lane_scene",
        world={},
    )
    assert _normalize_text(out.get("player_facing_text") or "") == _normalize_text(raw)
    fem = read_final_emission_meta_dict(out) or {}
    assert fem.get("acceptance_quality_checked") is False
    assert fem.get("acceptance_quality_passed") is True
    assert fem.get("acceptance_quality_gate_replaced_candidate") is not True


def test_acceptance_quality_n4_defaults_on_when_plan_has_no_shipped_aq_contract() -> None:
    plan = _minimal_n4_narrative_plan()
    out = apply_final_emission_gate(
        {"player_facing_text": _N4_REPAIRABLE_TWO_SENTENCE, "tags": [], "prompt_context": {"narrative_plan": plan}},
        resolution={"kind": "narrate", "prompt": "I hold position."},
        session=None,
        scene_id="lane_scene",
        world={},
    )
    fem = read_final_emission_meta_dict(out) or {}
    assert fem.get("acceptance_quality_checked") is True
    assert fem.get("acceptance_quality_passed") is True


def test_acceptance_quality_gate_invokes_canonical_seam_and_emits_its_text(monkeypatch) -> None:
    plan = _minimal_n4_narrative_plan(acceptance_quality={"enabled": True})
    trace = {
        "acceptance_quality_version": ACCEPTANCE_QUALITY_VERSION,
        "acceptance_quality_checked": True,
        "acceptance_quality_passed": True,
        "acceptance_quality_reason_codes": [],
        "acceptance_quality_repair_applied": False,
        "acceptance_quality_evidence": {},
    }
    bundle = {
        "text": "SEAM_CANONICAL_LINE_ONLY",
        "validation": {"passed": True, "failure_reasons": [], "reason_codes": [], "evidence": {}},
        "repair": {"repair_applied": False, "repair_modes": []},
        "acceptance_quality_emission_trace": trace,
    }
    mock = MagicMock(return_value=bundle)
    monkeypatch.setattr(feg, "validate_and_repair_acceptance_quality", mock)
    monkeypatch.setattr(feg, "_attach_interaction_continuity_validation", lambda *a, **k: None)
    out = apply_final_emission_gate(
        {
            "player_facing_text": "Any candidate would be ignored while mock is active.",
            "tags": [],
            "prompt_context": {"narrative_plan": plan},
        },
        resolution={"kind": "narrate", "prompt": "I wait."},
        session=None,
        scene_id="lane_scene",
        world={},
    )
    mock.assert_called()
    assert out.get("player_facing_text") == "SEAM_CANONICAL_LINE_ONLY"
    fem = read_final_emission_meta_dict(out) or {}
    assert fem.get("acceptance_quality_passed") is True
    assert fem.get("acceptance_quality_trace") == trace


def test_acceptance_quality_seam_disabled_contract_without_plan(monkeypatch) -> None:
    seen: list[bool] = []

    def _spy(text: str, contract: dict) -> dict:
        seen.append(bool(contract.get("enabled")))
        return validate_and_repair_acceptance_quality(text, contract)

    monkeypatch.setattr(feg, "validate_and_repair_acceptance_quality", _spy)
    apply_final_emission_gate(
        {"player_facing_text": "Wind rises.", "tags": []},
        resolution={"kind": "observe", "prompt": "I wait."},
        session=None,
        scene_id="s1",
        world={},
    )
    assert seen and all(enabled is False for enabled in seen)


def test_acceptance_quality_seam_enabled_with_plan_bundle(monkeypatch) -> None:
    plan = _minimal_n4_narrative_plan(acceptance_quality={"enabled": True})
    seen: list[bool] = []

    def _spy(text: str, contract: dict) -> dict:
        seen.append(bool(contract.get("enabled")))
        return validate_and_repair_acceptance_quality(text, contract)

    monkeypatch.setattr(feg, "validate_and_repair_acceptance_quality", _spy)
    apply_final_emission_gate(
        {"player_facing_text": _N4_REPAIRABLE_TWO_SENTENCE, "tags": [], "prompt_context": {"narrative_plan": plan}},
        resolution={"kind": "narrate", "prompt": "I hold position."},
        session=None,
        scene_id="lane_scene",
        world={},
    )
    assert any(enabled is True for enabled in seen)


def test_acceptance_quality_n4_repair_path_fem_nested_and_flattened_align() -> None:
    plan = _minimal_n4_narrative_plan(acceptance_quality={"enabled": True})
    out = apply_final_emission_gate(
        {"player_facing_text": _N4_REPAIRABLE_TWO_SENTENCE, "tags": [], "prompt_context": {"narrative_plan": plan}},
        resolution={"kind": "narrate", "prompt": "I hold position."},
        session=None,
        scene_id="lane_scene",
        world={},
    )
    fem = read_final_emission_meta_dict(out) or {}
    tr = fem.get("acceptance_quality_trace")
    assert isinstance(tr, dict)
    for k in (
        "acceptance_quality_version",
        "acceptance_quality_checked",
        "acceptance_quality_passed",
        "acceptance_quality_reason_codes",
        "acceptance_quality_repair_applied",
        "acceptance_quality_evidence",
    ):
        assert k in tr
        assert fem.get(k) == tr.get(k)
    assert isinstance(fem.get("acceptance_quality_reason_codes"), list)
    assert isinstance(fem.get("acceptance_quality_failure_reasons"), list)
    assert isinstance(fem.get("acceptance_quality_repair_modes"), list)
    assert isinstance(fem.get("acceptance_quality_evidence"), dict)
    assert fem.get("acceptance_quality_version") == ACCEPTANCE_QUALITY_VERSION
    assert fem.get("acceptance_quality_failure_reasons") == []
    assert fem.get("acceptance_quality_passed") is True
    assert fem.get("acceptance_quality_repair_applied") is True


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
    assert fem.get("acceptance_quality_rejected_reason_codes")
    assert isinstance(fem.get("acceptance_quality_rejected_reason_codes"), list)
    assert fem.get("candidate_validation_passed") is False
    assert fem.get("final_emitted_source") == "acceptance_quality_global_scene_fallback"
    aq_contract = build_acceptance_quality_contract(overrides=plan["acceptance_quality_contract"])
    ref = validate_and_repair_acceptance_quality(str(out.get("player_facing_text") or ""), aq_contract)
    assert fem.get("acceptance_quality_passed") == bool(ref["validation"]["passed"])
    tags = list(out.get("tags") or [])
    assert "final_emission_gate:acceptance_quality" in tags
    assert "nothing will ever be the same" not in (out.get("player_facing_text") or "").lower()


def test_acceptance_quality_unknown_trailer_version_passes_through_on_shipped_plan() -> None:
    plan = _minimal_n4_narrative_plan(
        acceptance_quality={"enabled": True, "trailer_phrase_patterns_version": 999},
    )
    out = apply_final_emission_gate(
        {"player_facing_text": _N4_REPAIRABLE_TWO_SENTENCE, "tags": [], "prompt_context": {"narrative_plan": plan}},
        resolution={"kind": "narrate", "prompt": "I hold position."},
        session=None,
        scene_id="lane_scene",
        world={},
    )
    fem = read_final_emission_meta_dict(out) or {}
    ev = fem.get("acceptance_quality_evidence") or {}
    assert ev.get("trailer_phrase_patterns_version_unresolved") == 999
    assert ev.get("trailer_phrase_patterns_version") != 1
    assert "nothing will ever be the same" in (out.get("player_facing_text") or "").lower()


def test_acceptance_quality_n4_does_not_invent_grounding_when_floor_fails() -> None:
    plan = _minimal_n4_narrative_plan(acceptance_quality={"enabled": True})
    out = apply_final_emission_gate(
        {
            "player_facing_text": "Yes.",
            "tags": [],
            "prompt_context": {"narrative_plan": plan},
        },
        resolution={"kind": "narrate", "prompt": "I wait."},
        session=None,
        scene_id="lane_scene",
        world={},
    )
    text = _normalize_text(out.get("player_facing_text") or "")
    assert "yes." != text.lower()
    assert "sergeant" not in text.lower()
    assert "torchlight" not in text.lower()
    fem = read_final_emission_meta_dict(out) or {}
    assert fem.get("acceptance_quality_gate_replaced_candidate") is True


def test_acceptance_quality_n4_strict_social_and_non_strict_attach_consistent_fem_shape(monkeypatch) -> None:
    plan = _minimal_n4_narrative_plan(acceptance_quality={"enabled": True})

    non_strict = apply_final_emission_gate(
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
    fem_ns = read_final_emission_meta_dict(non_strict) or {}

    session, world, sid, resolution = _runner_strict_bundle()
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
        return _N4_REPAIRABLE_TWO_SENTENCE, dict(stub_details)

    monkeypatch.setattr(feg, "build_final_strict_social_response", fake_build)
    strict_out = apply_final_emission_gate(
        {
            "player_facing_text": 'Tavern Runner says, "East lanes."',
            "tags": [],
            "prompt_context": {"narrative_plan": plan},
        },
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    fem_s = read_final_emission_meta_dict(strict_out) or {}

    for fem in (fem_ns, fem_s):
        assert fem.get("acceptance_quality_checked") is True
        assert isinstance(fem.get("acceptance_quality_trace"), dict)
        assert isinstance(fem.get("acceptance_quality_reason_codes"), list)
        assert isinstance(fem.get("acceptance_quality_evidence"), dict)


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


def _runner_strict_bundle():
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
    rt = get_scene_runtime(session, sid)
    rt["last_player_action_text"] = "Who attacked them?"
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


_IC_BRIDGE_LIVE_MALFORMED = 'South road." Tavern Runner nods once. "Old Millstone.'


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
    session, world, sid, resolution = _runner_strict_bundle()
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
    session, world, sid, resolution = _runner_strict_bundle()
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
    session, world, sid, resolution = _runner_strict_bundle()
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
    session, world, sid, resolution = _runner_strict_bundle()

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
    session, world, sid, resolution = _runner_strict_bundle()
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


def _iter_narration_constraint_strings(value):
    if isinstance(value, str):
        yield value
        return
    if isinstance(value, dict):
        for child in value.values():
            yield from _iter_narration_constraint_strings(child)
        return
    if isinstance(value, list):
        for child in value:
            yield from _iter_narration_constraint_strings(child)


def _assert_narration_constraint_payload_is_compact(payload: dict) -> None:
    assert set(payload) == {"response_type", "visibility", "speaker_selection"}
    assert set(payload["response_type"]) == {
        "required",
        "contract_source",
        "candidate_ok",
        "repair_used",
        "repair_kind",
        "upstream_prepared_absent",
    }
    assert set(payload["visibility"]) == {
        "contract_present",
        "decision_mode",
        "visible_entity_count",
        "withheld_fact_count",
        "reason_codes",
    }
    assert set(payload["speaker_selection"]) == {
        "speaker_id",
        "speaker_name",
        "selection_source",
        "reason_code",
        "binding_confident",
    }
    assert isinstance(payload["visibility"]["reason_codes"], list)
    assert len(payload["visibility"]["reason_codes"]) <= 5
    assert payload["visibility"]["visible_entity_count"] is None or isinstance(
        payload["visibility"]["visible_entity_count"], int
    )
    assert payload["visibility"]["withheld_fact_count"] is None or isinstance(
        payload["visibility"]["withheld_fact_count"], int
    )
    for text in _iter_narration_constraint_strings(payload):
        assert len(text) <= 120


def _assert_payload_omits_sentinels(payload: dict, *sentinels: str) -> None:
    blob = json.dumps(payload, sort_keys=True)
    for sentinel in sentinels:
        assert sentinel not in blob


def test_narration_constraint_debug_default_shape_is_stable():
    assert feg._default_narration_constraint_debug() == {
        "response_type": {
            "required": None,
            "contract_source": None,
            "candidate_ok": None,
            "repair_used": False,
            "repair_kind": None,
            "upstream_prepared_absent": None,
        },
        "visibility": {
            "contract_present": False,
            "decision_mode": None,
            "visible_entity_count": None,
            "withheld_fact_count": None,
            "reason_codes": [],
        },
        "speaker_selection": {
            "speaker_id": None,
            "speaker_name": None,
            "selection_source": None,
            "reason_code": None,
            "binding_confident": None,
        },
    }


def test_narration_constraint_debug_builder_and_merge_are_null_safe():
    payload = feg._build_narration_constraint_debug(
        response_type_debug={
            "response_type_required": "dialogue",
            "response_type_contract_source": "resolution.metadata",
            "response_type_candidate_ok": True,
            "response_type_repair_used": False,
            "response_type_repair_kind": None,
        },
        narration_visibility={
            "visible_entity_ids": ["runner", "guard"],
            "hidden_fact_strings": ["hidden one", "hidden two"],
        },
        visibility_meta={
            "visibility_validation_passed": False,
            "visibility_replacement_applied": True,
            "visibility_violation_kinds": [
                "hidden_fact_reference",
                "unseen_entity_reference",
                "hidden_fact_reference",
                "offscene_reference",
                "continuity_bleed",
                "should_not_fit",
            ],
        },
        speaker_selection_contract={
            "primary_speaker_id": "runner",
            "primary_speaker_name": "Tavern Runner",
            "primary_speaker_source": "continuity",
            "continuity_locked": True,
            "speaker_switch_allowed": False,
            "debug": {"grounding_reason_code": "grounded_in_scene_npc"},
        },
        speaker_contract_enforcement={
            "final_reason_code": "speaker_contract_match",
            "validation": {
                "reason_code": "speaker_contract_match",
                "details": {"signature": {"confidence": "high"}},
            },
        },
    )

    assert payload == {
        "response_type": {
            "required": "dialogue",
            "contract_source": "resolution.metadata",
            "candidate_ok": True,
            "repair_used": False,
            "repair_kind": None,
            "upstream_prepared_absent": None,
        },
        "visibility": {
            "contract_present": True,
            "decision_mode": "replaced",
            "visible_entity_count": 2,
            "withheld_fact_count": 2,
            "reason_codes": [
                "hidden_fact_reference",
                "unseen_entity_reference",
                "offscene_reference",
                "continuity_bleed",
                "should_not_fit",
            ],
        },
        "speaker_selection": {
            "speaker_id": "runner",
            "speaker_name": "Tavern Runner",
            "selection_source": "continuity",
            "reason_code": "speaker_contract_match",
            "binding_confident": True,
        },
    }

    metadata = {
        "other_key": 7,
        "emission_debug": {
            "speaker_contract_enforcement": {"final_reason_code": "speaker_contract_match"},
            "narration_constraint_debug": {
                "speaker_selection": {
                    "speaker_id": "runner",
                    "selection_source": "existing_source",
                }
            },
        },
    }
    feg._merge_narration_constraint_debug_meta(
        metadata,
        {
            "response_type": {"required": "dialogue"},
            "speaker_selection": {"speaker_name": "Tavern Runner"},
        },
    )

    merged = metadata["emission_debug"]["narration_constraint_debug"]
    assert metadata["other_key"] == 7
    assert metadata["emission_debug"]["speaker_contract_enforcement"]["final_reason_code"] == "speaker_contract_match"
    assert merged["response_type"]["required"] == "dialogue"
    assert merged["response_type"]["repair_used"] is False
    assert merged["speaker_selection"]["speaker_id"] == "runner"
    assert merged["speaker_selection"]["selection_source"] == "existing_source"
    assert merged["speaker_selection"]["speaker_name"] == "Tavern Runner"
    assert merged["visibility"]["reason_codes"] == []


def test_narration_constraint_debug_excludes_sensitive_and_verbose_inputs():
    hidden_fact = "The cult leader's name is Marrow Vale."
    unpublished_clue = "The ledger under the chapel floor names Iven as the courier."
    raw_prompt = "Player prompt fragment: tell me the secret name from the hidden ledger right now."
    candidate_generation = (
        'Candidate generation: Tavern Runner says, "The ledger under the chapel floor names Iven as the courier."'
    )
    contract_dump = (
        'Contract dump: {"allowed_speaker_ids":["runner","guard"],"debug":{"authoritative_source":"prompt"}}'
    )
    roster_dump = "Scene roster: Tavern Runner, Gate Guard, Harbor Priest, Smuggler Lookout, Dock Clerk."
    long_narration = " ".join(["Rain hammers the slate roof while the harbor bells answer the wind."] * 8)

    payload = feg._build_narration_constraint_debug(
        response_type_debug={
            "response_type_required": "dialogue",
            "response_type_contract_source": raw_prompt,
            "response_type_candidate_ok": True,
            "response_type_repair_used": True,
            "response_type_repair_kind": candidate_generation,
        },
        narration_visibility={
            "visible_entity_ids": ["runner", "guard", "priest"],
            "hidden_fact_strings": [hidden_fact, unpublished_clue],
        },
        visibility_meta={
            "visibility_validation_passed": False,
            "visibility_violation_kinds": [
                hidden_fact,
                unpublished_clue,
                raw_prompt,
                candidate_generation,
                contract_dump,
                roster_dump,
                long_narration,
            ],
        },
        speaker_selection_contract={
            "primary_speaker_id": "runner",
            "primary_speaker_name": roster_dump,
            "primary_speaker_source": raw_prompt,
            "debug": {
                "grounding_reason_code": contract_dump,
                "authoritative_source": roster_dump,
            },
        },
        speaker_contract_enforcement={
            "final_reason_code": candidate_generation,
            "validation": {
                "reason_code": unpublished_clue,
                "canonical_speaker_name": long_narration,
                "details": {"signature": {"confidence": "high"}},
            },
        },
        speaker_binding_bridge={
            "speaker_reason_code": contract_dump,
            "malformed_attribution_detected": False,
        },
    )

    assert payload["response_type"]["required"] == "dialogue"
    assert payload["visibility"]["contract_present"] is True
    assert payload["visibility"]["visible_entity_count"] == 3
    assert payload["visibility"]["withheld_fact_count"] == 2
    _assert_narration_constraint_payload_is_compact(payload)
    _assert_payload_omits_sentinels(
        payload,
        hidden_fact,
        unpublished_clue,
        raw_prompt,
        candidate_generation,
        contract_dump,
        roster_dump,
        long_narration,
    )


def test_narration_constraint_debug_speaker_fallback_reason_codes_are_stable():
    explicit = feg._build_narration_constraint_debug(
        speaker_selection_contract={
            "primary_speaker_id": "runner",
            "primary_speaker_name": "Tavern Runner",
            "primary_speaker_source": "explicit_target",
        }
    )
    assert explicit["speaker_selection"]["reason_code"] == "speaker_from_explicit_target"

    continuity = feg._build_narration_constraint_debug(
        speaker_selection_contract={
            "primary_speaker_id": "runner",
            "primary_speaker_name": "Tavern Runner",
            "primary_speaker_source": "continuity",
        }
    )
    assert continuity["speaker_selection"]["reason_code"] == "speaker_from_continuity"

    unresolved = feg._build_narration_constraint_debug()
    assert unresolved["speaker_selection"]["reason_code"] == "speaker_unresolved"


def test_narration_constraint_debug_prefers_grounded_speaker_reason_code_over_fallbacks():
    payload = feg._build_narration_constraint_debug(
        speaker_selection_contract={
            "primary_speaker_id": "runner",
            "primary_speaker_name": "Tavern Runner",
            "primary_speaker_source": "continuity",
            "debug": {"grounding_reason_code": "speaker_from_continuity"},
        },
        speaker_contract_enforcement={
            "final_reason_code": "local_rebind",
            "validation": {"details": {"signature": {"confidence": "high"}}},
        },
        speaker_binding_bridge={"speaker_reason_code": "speaker_from_explicit_target"},
    )
    assert payload["speaker_selection"]["reason_code"] == "local_rebind"


def test_narration_constraint_debug_missing_speaker_inputs_do_not_emit_noisy_values():
    noisy = "Malformed prompt fragment that should never surface in narration_constraint_debug output."
    payload = feg._build_narration_constraint_debug(
        speaker_selection_contract={
            "primary_speaker_source": noisy,
            "debug": {
                "grounding_reason_code": noisy,
                "authoritative_source": noisy,
            },
        },
        speaker_contract_enforcement={
            "validation": {"reason_code": noisy},
        },
        speaker_binding_bridge={"speaker_reason_code": noisy},
    )

    assert payload["speaker_selection"]["speaker_id"] is None
    assert payload["speaker_selection"]["speaker_name"] is None
    assert payload["speaker_selection"]["reason_code"] == "speaker_unresolved"
    _assert_payload_omits_sentinels(payload, noisy)


def test_merge_narration_constraint_debug_into_outputs_is_null_safe_and_preserves_metadata(monkeypatch):
    out = {
        "player_facing_text": "Rain drums on the slate roof.",
        "_final_emission_meta": {"visibility_validation_passed": True},
        "metadata": {
            "top_level_keep": {"ok": True},
            "emission_debug": {
                "existing_out_debug": {"count": 1},
            },
        },
    }
    resolution = {
        "kind": "observe",
        "prompt": "I listen.",
        "metadata": {
            "resolution_keep": {"source": "original"},
            "emission_debug": {"existing_resolution_debug": {"count": 2}},
        },
    }
    eff_resolution = {
        "kind": "observe",
        "metadata": {
            "effective_keep": {"source": "effective"},
            "emission_debug": {"existing_effective_debug": {"count": 3}},
        },
    }

    monkeypatch.setattr(feg, "get_speaker_selection_contract", lambda *a, **kw: None)

    feg._merge_narration_constraint_debug_into_outputs(
        out,
        resolution,
        eff_resolution,
        session=None,
        scene=None,
        world=None,
        response_type_debug={"response_type_required": "neutral_narration"},
        speaker_contract_enforcement=None,
    )

    out_payload = ((out.get("metadata") or {}).get("emission_debug") or {}).get("narration_constraint_debug")
    res_payload = ((resolution.get("metadata") or {}).get("emission_debug") or {}).get("narration_constraint_debug")
    eff_payload = ((eff_resolution.get("metadata") or {}).get("emission_debug") or {}).get("narration_constraint_debug")

    assert out["metadata"]["top_level_keep"] == {"ok": True}
    assert out["metadata"]["emission_debug"]["existing_out_debug"] == {"count": 1}
    assert resolution["metadata"]["resolution_keep"] == {"source": "original"}
    assert resolution["metadata"]["emission_debug"]["existing_resolution_debug"] == {"count": 2}
    assert eff_resolution["metadata"]["effective_keep"] == {"source": "effective"}
    assert eff_resolution["metadata"]["emission_debug"]["existing_effective_debug"] == {"count": 3}
    assert out_payload == res_payload == eff_payload
    assert out_payload["response_type"]["required"] == "neutral_narration"
    assert out_payload["speaker_selection"]["reason_code"] == "speaker_unresolved"
    _assert_narration_constraint_payload_is_compact(out_payload)


def test_apply_final_emission_gate_tolerates_missing_gm_output_for_narration_constraint_debug():
    assert apply_final_emission_gate(
        None,
        resolution=None,
        session=None,
        scene_id="scene_investigate",
        world=None,
    ) is None


def test_apply_final_emission_gate_surfaces_narration_constraint_debug_in_metadata(monkeypatch):
    session, world, sid, resolution = _runner_strict_bundle()
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
            "response_policy": {"response_type_contract": _response_type_contract("dialogue")},
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


def test_apply_final_emission_gate_narration_constraint_debug_stays_compact_after_gate_pass(monkeypatch):
    session, world, sid, resolution = _runner_strict_bundle()
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

    secret_fact = "The sealed ledger under the chapel floor names Iven as the courier."
    prompt_fragment = "Player prompt fragment: reveal the sealed ledger courier by name."
    candidate_generation = (
        'Candidate generation: Tavern Runner says, "The sealed ledger under the chapel floor names Iven as the courier."'
    )

    out = apply_final_emission_gate(
        {
            "player_facing_text": 'Tavern Runner says, "East lanes."',
            "tags": [],
            "gm_only_hidden_facts": [secret_fact],
            "metadata": {
                "top_level_keep": {"ok": True},
                "emission_debug": {
                    "existing_debug": {"count": 1},
                    "raw_prompt_fragment": prompt_fragment,
                    "candidate_generations": [candidate_generation],
                },
            },
            "response_policy": {"response_type_contract": _response_type_contract("dialogue")},
        },
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )

    payload = ((out.get("metadata") or {}).get("emission_debug") or {}).get("narration_constraint_debug") or {}
    assert payload["response_type"]["required"] == "dialogue"
    assert "response_type" in payload
    assert "visibility" in payload
    assert "speaker_selection" in payload
    assert (out.get("metadata") or {}).get("top_level_keep") == {"ok": True}
    assert ((out.get("metadata") or {}).get("emission_debug") or {}).get("existing_debug") == {"count": 1}
    _assert_narration_constraint_payload_is_compact(payload)
    _assert_payload_omits_sentinels(payload, secret_fact, prompt_fragment, candidate_generation)

# --- Narrative authority (Objective #9 Block 3 contract resolution + strict-social slice) ---------


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
    session, world, sid, resolution = _runner_strict_bundle()
    eff, route, _ = effective_strict_social_resolution_for_emission(resolution, session, world, sid)
    assert route is True

    na = _na_contract_for_resolution(eff if isinstance(eff, dict) else resolution)
    # Newline so intent lives in its own sentence (quoted periods are masked and can
    # prevent splitting; one merged sentence would replace the whole NPC line on repair).
    bad = (
        'Tavern Runner says, "No names yet—only rumors."\n\n'
        "He plans to stall you until the watch arrives."
    )

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

    def fake_build(_candidate_text, *, resolution, tags, session, scene_id, world):
        return bad, dict(stub_details)

    monkeypatch.setattr(feg, "build_final_strict_social_response", fake_build)

    out = apply_final_emission_gate(
        {
            "player_facing_text": bad,
            "tags": [],
            "response_policy": {"narrative_authority": na},
        },
        resolution=resolution,
        session=session,
        scene_id=sid,
        world=world,
    )
    text = out.get("player_facing_text") or ""
    meta = read_final_emission_meta_dict(out) or {}
    em = (out.get("metadata") or {}).get("emission_debug") or {}
    assert meta.get("narrative_authority_repaired") is False
    assert meta.get("narrative_authority_failed") is True
    assert em.get("narrative_authority_boundary_semantic_repair_disabled") is True
    assert "plans to stall" in text.lower()
    assert "Tavern Runner" in text
    assert meta.get("speaker_contract_enforcement_reason") == "speaker_contract_match"


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


def _purity_contract(**kwargs):
    return build_player_facing_narration_purity_contract(**kwargs)


def _response_type_contract(required: str) -> dict:
    return {
        "required_response_type": required,
        "action_must_preserve_agency": required == "action_outcome",
    }


def test_enforce_response_type_contract_marks_upstream_absent_for_answer_without_prepared_text():
    text, dbg = feg._enforce_response_type_contract(
        "Only mist between the torches.",
        gm_output={
            "response_policy": {"response_type_contract": _response_type_contract("answer")},
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


def _opening_validation_context() -> dict:
    facts = [
        "Rain spatters soot-dark stone; frayed banners hang above Cinderwatch's eastern gate.",
        "Refugees, wagons, and foot traffic clog the muddy approach; guards hold the choke while the crowd presses in.",
        "A notice board lists new taxes, curfews, and a posted warning about a missing patrol.",
    ]
    return {
        "location_anchors": ["Cinderwatch Gate District"],
        "visible_facts": facts,
        "actionable_labels": ["Read the notice board", "Approach the guards"],
    }


def _opening_gm_output() -> dict:
    facts = _opening_validation_context()["visible_facts"]
    return {
        "response_policy": {"response_type_contract": _response_type_contract("scene_opening")},
        "opening_curated_facts": list(facts),
        "metadata": {
            "emission_debug": {
                "opening_curated_facts_present": True,
                "opening_curated_facts_count": len(facts),
                "opening_curated_facts_source": "realization",
            }
        },
        "prompt_context": {
            "opening_inputs_are_curated": True,
            "opening_curated_facts": list(facts),
            "narration_obligations": {"is_opening_scene": True},
            "narrative_plan": {
                "scene_opening": {"location_anchors": ["Cinderwatch Gate District"]},
                "scene_anchors": {"location_anchors": ["Cinderwatch Gate District"]},
                "active_pressures": {},
            },
            "opening_scene_realization": {"contract": {"narration_basis_visible_facts": facts}},
            "narration_visibility": {"visible_facts": facts},
            "scene": {
                "public": {
                    "id": "frontier_gate",
                    "location": "Cinderwatch Gate District",
                    "visible_facts": facts,
                    "actions": [{"label": "Read the notice board"}, {"label": "Approach the guards"}],
                }
            },
        },
    }


def test_opening_validator_rejects_investigation_continuation_language():
    failures = feg.validate_opening_output("Nearby crates appear disturbed.", _opening_validation_context())

    assert "continuation_or_investigation_language" in failures
    assert "invalid_sentence_structure" in failures


def test_opening_validator_rejects_fragment_sentence():
    failures = feg.validate_opening_output("At the Cinderwatch Gate District, rain and refugees.", _opening_validation_context())

    assert "invalid_sentence_structure" in failures


def test_opening_validator_rejects_opening_without_actionable_hook():
    failures = feg.validate_opening_output(
        "Cinderwatch Gate District. Rain spatters soot-dark stone while refugees and wagons clog the muddy approach.",
        _opening_validation_context(),
    )

    assert "missing_hook" in failures


def test_opening_failure_recovers_via_deterministic_fallback_not_action_outcome():
    text, dbg = feg._enforce_response_type_contract(
        "Nearby crates appear disturbed.",
        gm_output=_opening_gm_output(),
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )

    assert "Cinderwatch's eastern gate" in text
    assert "You can" in text
    assert "appears disturbed" not in text
    assert dbg.get("opening_validation_failed") is True
    assert "continuation_or_investigation_language" in dbg.get("opening_failure_reasons")
    assert dbg.get("opening_recovered_via_fallback") is True
    assert dbg.get("response_type_repair_kind") == "opening_deterministic_fallback"
    assert dbg.get("fallback_family_used") == "scene_opening"
    assert dbg.get("fallback_temporal_frame") == "first_impression"


def test_valid_scene_opening_skips_deterministic_fallback():
    candidate = (
        "You stand in the churned mud before Cinderwatch's eastern gate as rain spatters soot-dark stone "
        "and frayed banners snap above you. Refugees press shoulder to shoulder around the wagon line "
        "while guards hold the choke under shouted orders."
    )
    text, dbg = feg._enforce_response_type_contract(
        candidate,
        gm_output=_opening_gm_output(),
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )

    assert text == candidate
    assert dbg.get("opening_fallback_skipped") is True
    assert dbg.get("response_type_repair_used") is False
    assert dbg.get("response_type_repair_kind") is None
    assert dbg.get("opening_repair_source") in {
        "preserved_candidate",
        "preserved_candidate_validity_check",
    }


def test_empty_scene_opening_uses_deterministic_fallback():
    text, dbg = feg._enforce_response_type_contract(
        "",
        gm_output=_opening_gm_output(),
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )

    assert text
    assert "Cinderwatch's eastern gate" in text
    assert dbg.get("opening_fallback_skipped") is False
    assert dbg.get("response_type_repair_used") is True
    assert dbg.get("response_type_repair_kind") == "opening_deterministic_fallback"


def test_scene_opening_candidate_not_rejected_for_lacking_action_result_language():
    text, dbg = feg._enforce_response_type_contract(
        (
            "Cinderwatch Gate District gathers rain, refugees, wagons, guards, and torchlight "
            "around the eastern gate. You can read the notice board or approach the guards."
        ),
        gm_output=_opening_gm_output(),
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )

    assert "Cinderwatch Gate District" in text
    assert dbg.get("response_type_required") == "scene_opening"
    assert dbg.get("response_type_candidate_ok") is True
    assert "action_outcome_missing_result" not in dbg.get("response_type_rejection_reasons")
    assert dbg.get("response_type_repair_used") is False


def test_scene_opening_fallback_with_opening_seed_facts_emits_seed_facts():
    curated = [
        "Ash Quay crouches under black rain and lantern smoke.",
        "Dock guards hold a shouting crowd behind a rope line.",
        "A brass notice board points newcomers toward the harbor clerk.",
    ]
    gm_output = {
        "response_policy": {"response_type_contract": _response_type_contract("scene_opening")},
        "opening_curated_facts": list(curated),
        "prompt_context": {
            "opening_inputs_are_curated": True,
            "narration_obligations": {"is_opening_scene": True},
            "narrative_plan": {
                "scene_opening": {"location_anchors": ["Ash Quay"]},
                "scene_anchors": {"location_anchors": ["Ash Quay"]},
            },
            "scene": {
                "public": {
                    "id": "ash_quay",
                    "location": "Ash Quay",
                    "opening_seed_facts": [
                        "This opening_seed_facts line must not be the fallback source.",
                    ],
                }
            },
        },
    }

    text, dbg = feg._enforce_response_type_contract(
        "Nearby crates appear disturbed.",
        gm_output=gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="ash_quay",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )

    assert "Ash Quay crouches under black rain" in text
    assert "Dock guards hold a shouting crowd" in text
    assert "brass notice board" in text
    assert "opening_seed_facts line" not in text
    assert dbg.get("opening_fallback_context_source") == "opening_curated_facts"
    assert dbg.get("opening_fallback_basis_count") == 3
    assert dbg.get("opening_fallback_failed_closed") is False


def test_scene_opening_fallback_prefers_opening_curated_facts():
    curated = [
        "Glass rain hangs over the Argent Court hall's silent balconies.",
        "Court guards keep a velvet rope across the marble stair.",
        "A silver notice board names the first petitioners for the morning.",
    ]
    gm_output = _opening_gm_output()
    gm_output["opening_curated_facts"] = curated
    gm_output["metadata"]["emission_debug"]["opening_curated_facts_count"] = len(curated)
    gm_output["metadata"]["emission_debug"]["opening_curated_facts_source"] = "realization"
    gm_output["prompt_context"]["narration_visibility"]["visible_facts"] = [
        "This narration_visibility fact should not be used while curated facts exist."
    ]

    text, dbg = feg._enforce_response_type_contract(
        "Nearby crates appear disturbed.",
        gm_output=gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="argent_court",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )

    assert "Argent Court hall's silent balconies" in text
    assert "velvet rope" in text
    assert "should not be used" not in text
    assert dbg.get("opening_fallback_context_source") == "opening_curated_facts"
    assert dbg.get("opening_curated_facts_present") is True
    assert dbg.get("opening_curated_facts_count") == 3
    assert dbg.get("opening_curated_facts_source") == "realization"
    assert dbg.get("opening_fallback_failed_closed") is False


def test_removing_opening_curated_facts_raises_instead_of_falling_back():
    gm_output = _opening_gm_output()
    gm_output.pop("opening_curated_facts", None)

    with pytest.raises(AssertionError, match="scene_opening missing curated facts"):
        feg._enforce_response_type_contract(
            "Nearby crates appear disturbed.",
            gm_output=gm_output,
            resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
            session={},
            scene_id="empty_opening",
            world={},
            strict_social_turn=False,
            strict_social_suppressed_non_social_turn=False,
            active_interlocutor="",
        )


def test_opening_failure_fallback_classification_excludes_observe_family():
    text, dbg = feg._enforce_response_type_contract(
        "A bad response type.",
        gm_output=_opening_gm_output(),
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )

    repair_kind = str(dbg.get("response_type_repair_kind") or "")
    meta = fallback_template_metadata(repair_kind)
    observe_meta = fallback_template_metadata("observe_perception_fallback")
    assert text
    assert meta == {"fallback_family": "scene_opening", "temporal_frame": "first_impression"}
    assert meta.get("fallback_family") != observe_meta.get("fallback_family")
    assert meta.get("temporal_frame") not in {"reinspection", "continuation"}
    assert dbg.get("fallback_family_used") == "scene_opening"
    assert dbg.get("fallback_temporal_frame") == "first_impression"


def test_opening_visibility_safe_fallback_routes_to_opening_family_not_observe():
    fallback = feg._standard_visibility_safe_fallback(
        gm_output=_opening_gm_output(),
        session={},
        scene={"scene": _opening_gm_output()["prompt_context"]["scene"]["public"]},
        world={},
        scene_id="frontier_gate",
        eff_resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        active_interlocutor="",
        strict_social_active=False,
        strict_social_suppressed_non_social_turn=False,
    )

    text, _pool, fallback_kind, _source, _strategy, _candidate_source, composition_meta = fallback
    low = text.lower()
    assert fallback_kind == "opening_deterministic_fallback"
    assert composition_meta.get("fallback_family_used") == "scene_opening"
    assert composition_meta.get("fallback_temporal_frame") == "first_impression"
    assert "look again" not in low
    assert "still" not in low


def test_opening_fallback_ignores_contaminated_public_scene_visible_facts():
    gm_output = _opening_gm_output()
    gm_output["prompt_context"]["scene"]["public"]["visible_facts"] = [
        "Rain spatters soot-dark stone; frayed banners hang above Cinderwatch's eastern gate.",
        "GM hint: the captain plans to arrest the player after sundown.",
        "Backstage: the hidden cult controls the west-road patrol.",
    ]

    text, dbg = feg._enforce_response_type_contract(
        "Nearby crates appear disturbed.",
        gm_output=gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )

    low = text.lower()
    assert dbg.get("opening_recovered_via_fallback") is True
    assert "gm hint" not in low
    assert "captain plans" not in low
    assert "backstage" not in low
    assert "hidden cult" not in low


def test_opening_fallback_never_uses_polluted_narration_visibility_facts():
    gm_output = _opening_gm_output()
    gm_output["opening_curated_facts"] = [
        "Blue rain beads on the Gate Ward's iron lamps.",
        "Ward guards keep travelers moving past the toll arch.",
        "A brass notice board names the morning crossings.",
    ]
    gm_output["prompt_context"]["narration_visibility"]["visible_facts"] = [
        "A dead drop waits beneath the third bench.",
        "Muddy footprints lead toward the shuttered apothecary.",
    ]

    text, dbg = feg._enforce_response_type_contract(
        "Nearby crates appear disturbed.",
        gm_output=gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )

    low = text.lower()
    assert "dead drop" not in low
    assert "footprints" not in low
    assert "gate ward's iron lamps" in text.lower()
    assert dbg.get("opening_fallback_context_source") == "opening_curated_facts"


def test_failed_scene_opening_never_emits_generic_the_scene_fallback():
    gm_output = _opening_gm_output()
    plan = gm_output["prompt_context"]["narrative_plan"]
    plan["scene_opening"]["location_anchors"] = []
    plan["scene_anchors"]["location_anchors"] = []
    gm_output["prompt_context"]["scene"]["public"].pop("location", None)

    text, dbg = feg._enforce_response_type_contract(
        "Nearby crates appear disturbed.",
        gm_output=gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )

    assert dbg.get("response_type_repair_kind") == "opening_deterministic_fallback"
    assert "the scene" not in text.lower()
    assert "before you is immediately before you" not in text.lower()
    assert "the scene is immediately before you" not in text.lower()
    assert text


def test_scene_opening_fallback_fail_closes_without_curated_context():
    with pytest.raises(AssertionError, match="scene_opening missing curated facts"):
        feg._enforce_response_type_contract(
            "Nearby crates appear disturbed.",
            gm_output={"response_policy": {"response_type_contract": _response_type_contract("scene_opening")}},
            resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
            session={},
            scene_id="empty_opening",
            world={},
            strict_social_turn=False,
            strict_social_suppressed_non_social_turn=False,
            active_interlocutor="",
        )


def test_scene_opening_fallback_fail_closes_with_empty_curated_facts():
    text, dbg = feg._enforce_response_type_contract(
        "Nearby crates appear disturbed.",
        gm_output={
            "response_policy": {"response_type_contract": _response_type_contract("scene_opening")},
            "opening_curated_facts": [],
        },
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="empty_opening",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )

    assert text == "[opening_fallback_failed_closed: empty_curated_facts]"
    assert dbg.get("opening_fallback_context_missing") is True
    assert dbg.get("opening_fallback_failed_closed") is True
    assert dbg.get("response_type_repair_kind") == "opening_deterministic_fallback_failed_closed"


def test_frontier_gate_opening_fallback_uses_top_level_curated_facts():
    public_scene = default_scene("frontier_gate")["scene"]
    curated = [
        "Cold rain needles Cinderwatch's eastern gate while torchlight smears across the stone.",
        "Refugees, wagons, and travelers crowd the muddy checkpoint.",
        "A notice board announces new taxes and curfews beside the guard post.",
    ]
    gm_output = {
        "response_policy": {"response_type_contract": _response_type_contract("scene_opening")},
        "opening_curated_facts": curated,
        "prompt_context": {
            "opening_inputs_are_curated": True,
            "narration_obligations": {"is_opening_scene": True},
            "narrative_plan": {
                "scene_opening": {"location_anchors": ["Cinderwatch Gate"]},
                "scene_anchors": {"location_anchors": ["Cinderwatch Gate"]},
            },
            "scene": {"public": public_scene},
        },
    }

    text, dbg = feg._enforce_response_type_contract(
        "Nearby crates appear disturbed.",
        gm_output=gm_output,
        resolution={"kind": "scene_opening", "prompt": "Start the campaign."},
        session={},
        scene_id="frontier_gate",
        world={},
        strict_social_turn=False,
        strict_social_suppressed_non_social_turn=False,
        active_interlocutor="",
    )

    assert "Cold rain needles Cinderwatch's eastern gate" in text
    assert any(
        phrase in text
        for phrase in (
            "refugees, wagons, and travelers",
            "notice board announces new taxes and curfews",
            "tavern runner is hawking hot stew",
            "ragged stranger hangs back",
        )
    )
    assert dbg.get("opening_fallback_context_source") == "opening_curated_facts"
    assert dbg.get("opening_fallback_failed_closed") is False
    assert "immediately before you" not in text.lower()


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
            "response_policy": {"response_type_contract": _response_type_contract("neutral_narration")},
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
            "response_policy": {"response_type_contract": _response_type_contract("neutral_narration")},
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
            "response_policy": {"response_type_contract": _response_type_contract("neutral_narration")},
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
            "response_policy": {"response_type_contract": _response_type_contract("action_outcome")},
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
            "response_policy": {"response_type_contract": _response_type_contract("neutral_narration")},
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
            "response_policy": {"response_type_contract": _response_type_contract("neutral_narration")},
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
            "response_policy": {"response_type_contract": _response_type_contract("neutral_narration")},
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
            "response_policy": {"response_type_contract": _response_type_contract("neutral_narration")},
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
            "response_policy": {"response_type_contract": _response_type_contract("neutral_narration")},
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
            "response_policy": {"response_type_contract": _response_type_contract("neutral_narration")},
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
    rtc = _response_type_contract("dialogue")
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
    session, world, sid, resolution = _runner_strict_bundle()
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
    session, world, sid, resolution = _runner_strict_bundle()
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
    rtc = _response_type_contract("dialogue")
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
    rtc = _response_type_contract("action_outcome")
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


def _narrative_mode_plan_payload(contract: dict) -> dict:
    return {"prompt_context": {"narrative_plan": {"narrative_mode_contract": contract}}}


def test_narrative_mode_output_layer_runs_when_plan_contract_shipped() -> None:
    nmc = build_narrative_mode_contract(ctir=_minimal_ctir_continuation())
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
    gm_output = _opening_gm_output()
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
    nmc = build_narrative_mode_contract(ctir=_minimal_ctir_continuation())
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
    session, world, sid, resolution = _runner_strict_bundle()
    nmc = build_narrative_mode_contract(ctir=_minimal_ctir_continuation())
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
