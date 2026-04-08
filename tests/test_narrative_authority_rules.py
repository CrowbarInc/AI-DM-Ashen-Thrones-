"""Direct unit tests for ``game.narrative_authority`` (Block 1) and focused gate helpers.

Aligned to Block 3: shipped full contracts only for validation; ``prompt_debug`` mirrors are
diagnostics-only (covered in ``test_final_emission_gate.py``).
"""
from __future__ import annotations

import pytest

import game.final_emission_gate as feg
from game.narrative_authority import (
    build_narrative_authority_contract,
    validate_narrative_authority,
)
from game.social_exchange_emission import merged_player_prompt_for_gate

pytestmark = pytest.mark.unit


def _na_contract(
    *,
    resolution: dict | None,
    session_view: dict | None = None,
) -> dict:
    return build_narrative_authority_contract(
        resolution=resolution,
        narration_visibility={},
        scene_state_anchor_contract=None,
        speaker_selection_contract=None,
        session_view=session_view,
    )


def _rt_debug(*, candidate_ok: bool | None = True) -> dict:
    return {
        "response_type_required": None,
        "response_type_contract_source": None,
        "response_type_candidate_ok": candidate_ok,
        "response_type_repair_used": False,
        "response_type_repair_kind": None,
        "response_type_rejection_reasons": [],
        "non_hostile_escalation_blocked": False,
    }


# ---------------------------------------------------------------------------
# validate_narrative_authority (Block 1)
# ---------------------------------------------------------------------------


def test_validate_narrative_authority_visible_observation_passes():
    res = {"kind": "question", "prompt": "What did you see?"}
    c = _na_contract(resolution=res)
    out = validate_narrative_authority(
        "He glances toward the alley.",
        c,
        resolution=res,
        player_text="What did you see?",
    )
    assert out["checked"] is True
    assert out["passed"] is True
    assert out["failure_reasons"] == []
    assert out["assertion_flags"]["invented_intent"] is False
    assert out["matched_deferral_mode"] is None


def test_validate_narrative_authority_invented_intent_fails():
    res = {"kind": "question", "prompt": "Who attacked them?"}
    c = _na_contract(resolution=res)
    out = validate_narrative_authority(
        "He plans to stall you until help arrives.",
        c,
        resolution=res,
        player_text=merged_player_prompt_for_gate(res, {}, "s"),
    )
    assert out["passed"] is False
    assert "unknown_intent" in out["failure_reasons"]
    assert out["assertion_flags"]["invented_intent"] is True


def test_validate_narrative_authority_invented_hidden_fact_fails():
    res = {"kind": "observe", "prompt": "I read the ledger."}
    c = _na_contract(resolution=res)
    out = validate_narrative_authority(
        "The ledger was planted.",
        c,
        resolution=res,
        player_text="I read the ledger.",
    )
    assert out["passed"] is False
    assert "unknown_hidden_fact" in out["failure_reasons"]
    assert out["assertion_flags"]["invented_hidden_fact"] is True


def test_validate_narrative_authority_unresolved_outcome_fails():
    res = {"kind": "interact", "prompt": "I pick the lock."}
    c = _na_contract(resolution=res)
    out = validate_narrative_authority(
        "The lock clicks open.",
        c,
        resolution=res,
        player_text="I pick the lock.",
    )
    assert out["passed"] is False
    assert "unresolved_action" in out["failure_reasons"]
    assert out["assertion_flags"]["invented_outcome"] is True
    assert out["assertion_flags"]["overcertain_unresolved_action"] is True


def test_validate_narrative_authority_resolved_outcome_passes():
    res = {
        "kind": "interact",
        "prompt": "I pick the lock.",
        "skill_check": {"success": True},
    }
    c = _na_contract(resolution=res)
    out = validate_narrative_authority(
        "The lock clicks open.",
        c,
        resolution=res,
        player_text="I pick the lock.",
    )
    assert out["passed"] is True
    assert out["failure_reasons"] == []


def test_validate_narrative_authority_ask_for_roll_deferral_detected():
    res = {"kind": "interact", "prompt": "I pick the lock."}
    c = _na_contract(resolution=res)
    out = validate_narrative_authority(
        "Before you assume it opens, give me a Disable Device check.",
        c,
        resolution=res,
        player_text="I pick the lock.",
    )
    assert out["passed"] is True
    assert out["matched_deferral_mode"] == "ask_for_roll"


def test_validate_narrative_authority_bounded_uncertainty_passes():
    res = {"kind": "interact", "prompt": "I try the door."}
    c = _na_contract(resolution=res)
    out = validate_narrative_authority(
        "The latch might still be engaged; you cannot tell yet without testing it.",
        c,
        resolution=res,
        player_text="I try the door.",
    )
    assert out["passed"] is True
    assert out["matched_deferral_mode"] == "bounded_uncertainty"


def test_validate_narrative_authority_branch_framing_passes():
    res = {"kind": "interact", "prompt": "I try the door."}
    c = _na_contract(resolution=res)
    out = validate_narrative_authority(
        "If you succeed, the bar lifts and the door can swing inward.",
        c,
        resolution=res,
        player_text="I try the door.",
    )
    assert out["passed"] is True
    assert out["matched_deferral_mode"] == "branch_outcome"


def test_validate_narrative_authority_already_valid_examples():
    res = {"kind": "question", "prompt": "What is he thinking?"}
    c = _na_contract(resolution=res)
    samples = [
        "He glances toward the alley.",
        "If you want to judge whether he is lying, give me a Sense Motive check.",
        (
            "Something about the ledger is off, but you cannot tell yet "
            "whether it was planted."
        ),
    ]
    for s in samples:
        out = validate_narrative_authority(s, c, resolution=res, player_text=res["prompt"])
        assert out["passed"] is True, s


# ---------------------------------------------------------------------------
# Gate layer: repair ladder & ordering (uses real ``_apply_narrative_authority_layer``)
# ---------------------------------------------------------------------------


def test_apply_na_layer_repairs_unresolved_outcome_with_uncertainty_replace():
    """Non-mechanical resolution: replace settled-outcome sentence (narrow repair)."""
    res = {"kind": "observe", "prompt": "I look at the lock."}
    na = _na_contract(resolution=res)
    gm = {"player_facing_text": "x", "response_policy": {"narrative_authority": na}}
    text, meta, extra = feg._apply_narrative_authority_layer(
        "The lock clicks open.",
        gm_output=gm,
        resolution=res,
        strict_social_details=None,
        response_type_debug=_rt_debug(),
        answer_completeness_meta={},
        session={},
        scene_id="s",
    )
    assert meta["narrative_authority_checked"] is True
    assert meta["narrative_authority_failed"] is False
    assert meta["narrative_authority_repaired"] is True
    assert meta["narrative_authority_repair_mode"] == "invented_outcome_uncertainty_replace"
    assert "lock clicks open" not in text.lower()
    assert "not settled yet" in text.lower()
    assert validate_narrative_authority(text, na, resolution=res, player_text="I look at the lock.")["passed"]
    assert extra == []


def test_apply_na_layer_lockpick_roll_append_may_fail_revalidation():
    """Mechanical-interact path appends roll text but leaves the outcome sentence; revalidation can fail."""
    res = {"kind": "interact", "prompt": "I pick the lock."}
    na = _na_contract(resolution=res)
    gm = {"player_facing_text": "x", "response_policy": {"narrative_authority": na}}
    text, meta, extra = feg._apply_narrative_authority_layer(
        "The lock clicks open.",
        gm_output=gm,
        resolution=res,
        strict_social_details=None,
        response_type_debug=_rt_debug(),
        answer_completeness_meta={},
        session={},
        scene_id="s",
    )
    assert meta["narrative_authority_checked"] is True
    assert meta["narrative_authority_failed"] is True
    assert meta["narrative_authority_repaired"] is False
    assert meta["narrative_authority_assertion_flags"]["invented_outcome"] is True
    assert text == "The lock clicks open."
    assert "narrative_authority_unsatisfied_after_repair" in extra


def test_apply_na_layer_repairs_invented_hidden_fact():
    res = {"kind": "observe", "prompt": "I examine the papers."}
    na = _na_contract(resolution=res)
    gm = {"player_facing_text": "x", "response_policy": {"narrative_authority": na}}
    text, meta, extra = feg._apply_narrative_authority_layer(
        "The ledger was planted.",
        gm_output=gm,
        resolution=res,
        strict_social_details=None,
        response_type_debug=_rt_debug(),
        answer_completeness_meta={},
        session={},
        scene_id="s",
    )
    assert meta["narrative_authority_repair_mode"] == "invented_hidden_fact_downgrade"
    assert meta["narrative_authority_repaired"] is True
    assert "planted" not in text.lower()
    assert "pin the hidden cause" in text.lower() or "can't pin" in text.lower()
    assert extra == []


def test_apply_na_layer_repairs_invented_intent_with_observable_cues():
    res = {"kind": "question", "prompt": "What is he thinking?"}
    na = _na_contract(resolution=res)
    gm = {"player_facing_text": "x", "response_policy": {"narrative_authority": na}}
    text, meta, extra = feg._apply_narrative_authority_layer(
        "He plans to stall you until help arrives.",
        gm_output=gm,
        resolution=res,
        strict_social_details=None,
        response_type_debug=_rt_debug(),
        answer_completeness_meta={},
        session={},
        scene_id="s",
    )
    assert meta["narrative_authority_repair_mode"] == "invented_intent_observable_cues"
    assert meta["narrative_authority_repaired"] is True
    assert "plans to stall" not in text.lower()
    assert "posture" in text.lower() or "wording" in text.lower()
    assert extra == []


def test_strict_vs_non_strict_post_repair_failure_extra_reason():
    monkeypatch = pytest.MonkeyPatch()
    try:
        calls: list[int] = []

        def fake_validate(_text, _contract, **kwargs):
            calls.append(1)
            if len(calls) == 1:
                return {
                    "checked": True,
                    "passed": False,
                    "failure_reasons": ["unresolved_action"],
                    "matched_deferral_mode": None,
                    "assertion_flags": {
                        "invented_outcome": True,
                        "invented_hidden_fact": False,
                        "invented_intent": False,
                        "overcertain_unresolved_action": True,
                    },
                }
            return {
                "checked": True,
                "passed": False,
                "failure_reasons": ["unresolved_action"],
                "matched_deferral_mode": None,
                "assertion_flags": {
                    "invented_outcome": True,
                    "invented_hidden_fact": False,
                    "invented_intent": False,
                    "overcertain_unresolved_action": True,
                },
            }

        def fake_repair(*_a, **_k):
            return "Still unacceptable.", "forced_repair"

        monkeypatch.setattr(feg, "validate_narrative_authority", fake_validate)
        monkeypatch.setattr(feg, "_repair_narrative_authority_narrow", fake_repair)

        res = {"kind": "observe", "prompt": "I try the door."}
        na = _na_contract(resolution=res)
        gm = {"player_facing_text": "x", "response_policy": {"narrative_authority": na}}
        original = "The lock snaps open."

        t_strict, m_strict, e_strict = feg._apply_narrative_authority_layer(
            original,
            gm_output=gm,
            resolution=res,
            strict_social_details={"final_emitted_source": "test_strict"},
            response_type_debug=_rt_debug(),
            answer_completeness_meta={},
            session={},
            scene_id="s",
        )
        assert t_strict == original
        assert m_strict["narrative_authority_failed"] is True
        assert "narrative_authority_unsatisfied_after_repair" not in e_strict

        t_loose, m_loose, e_loose = feg._apply_narrative_authority_layer(
            original,
            gm_output=gm,
            resolution=res,
            strict_social_details=None,
            response_type_debug=_rt_debug(),
            answer_completeness_meta={},
            session={},
            scene_id="s",
        )
        assert t_loose == original
        assert m_loose["narrative_authority_failed"] is True
        assert "narrative_authority_unsatisfied_after_repair" in e_loose
    finally:
        monkeypatch.undo()


def test_merge_na_emission_debug_mirror_aligned_and_mismatch():
    res = {"kind": "observe", "prompt": "I look."}
    full = _na_contract(resolution=res)
    slim_aligned = {
        "enabled": full["enabled"],
        "authoritative_outcome_available": full["authoritative_outcome_available"],
        "forbid_unresolved_outcome_assertions": full["forbid_unresolved_outcome_assertions"],
        "forbid_hidden_fact_assertions": full["forbid_hidden_fact_assertions"],
        "forbid_npc_intent_assertions_without_basis": full["forbid_npc_intent_assertions_without_basis"],
    }
    slim_mismatch = {**slim_aligned, "authoritative_outcome_available": not full["authoritative_outcome_available"]}

    gate_meta = {
        "narrative_authority_checked": True,
        "narrative_authority_failed": False,
    }

    out_aligned = {
        "player_facing_text": "ok",
        "response_policy": {"narrative_authority": full},
        "prompt_debug": {"narrative_authority": slim_aligned},
        "metadata": {},
    }
    feg._merge_narrative_authority_into_emission_debug(
        out_aligned, res, res, gate_meta=gate_meta, gm_output=out_aligned
    )
    em = (out_aligned["metadata"].get("emission_debug") or {}).get("narrative_authority") or {}
    assert em.get("prompt_debug_mirror_present") is True
    assert em.get("prompt_debug_mirror_mismatch_vs_shipped") is False

    out_mis = {
        "player_facing_text": "ok",
        "response_policy": {"narrative_authority": full},
        "prompt_debug": {"narrative_authority": slim_mismatch},
        "metadata": {},
    }
    feg._merge_narrative_authority_into_emission_debug(
        out_mis, res, res, gate_meta=gate_meta, gm_output=out_mis
    )
    em2 = (out_mis["metadata"].get("emission_debug") or {}).get("narrative_authority") or {}
    assert em2.get("prompt_debug_mirror_mismatch_vs_shipped") is True


def test_merge_na_emission_debug_mirror_only_slim_skips_validation_but_merges_presence():
    """Slim ``prompt_debug`` is not a shipped contract; merge can still record mirror presence."""
    res = {"kind": "observe", "prompt": "I look."}
    slim = {"enabled": True, "authoritative_outcome_available": False}
    assert feg._is_shipped_full_narrative_authority_contract(slim) is False

    gm = {
        "player_facing_text": "Hello.",
        "prompt_debug": {"narrative_authority": slim},
        "response_policy": {},
        "metadata": {},
    }
    text, meta, _ = feg._apply_narrative_authority_layer(
        "Hello.",
        gm_output=gm,
        resolution=res,
        strict_social_details=None,
        response_type_debug=_rt_debug(),
        answer_completeness_meta={},
        session={},
        scene_id="s",
    )
    assert meta["narrative_authority_skip_reason"] == "no_full_contract"

    feg._merge_narrative_authority_into_emission_debug(
        gm, res, res, gate_meta=meta, gm_output=gm
    )
    em = (gm["metadata"].get("emission_debug") or {}).get("narrative_authority") or {}
    assert em.get("prompt_debug_mirror_present") is True


# ---------------------------------------------------------------------------
# Cross-objective ordering: NA after answer/delta; preserves prior clauses
# ---------------------------------------------------------------------------


def test_na_repair_preserves_answer_first_clause():
    res = {"kind": "question", "prompt": "Where did they go?"}
    na = _na_contract(resolution=res)
    gm = {"player_facing_text": "x", "response_policy": {"narrative_authority": na}}
    raw = 'They fled east toward the old mill. The ledger was planted.'
    text, meta, _ = feg._apply_narrative_authority_layer(
        raw,
        gm_output=gm,
        resolution=res,
        strict_social_details=None,
        response_type_debug=_rt_debug(),
        answer_completeness_meta={},
        session={},
        scene_id="s",
    )
    assert meta["narrative_authority_repaired"] is True
    assert "east toward the old mill" in text.lower()
    assert "planted" not in text.lower()


def test_na_after_response_delta_preserves_net_new_clause():
    from game.final_emission_gate import _apply_response_delta_layer

    rd = {
        "enabled": True,
        "delta_required": True,
        "previous_answer_snippet": (
            "The watch keeps a lane open on the east road past the old mill checkpoint."
        ),
        "allowed_delta_kinds": ["new_information", "refinement"],
        "delta_must_come_early": False,
        "allow_short_bridge_before_delta": False,
        "expected_delta_shape": "direct_delta",
        "trace": {"trigger_source": "test"},
    }
    res = {"kind": "question", "prompt": "What else?"}
    na = _na_contract(resolution=res)
    pol = {"response_delta": rd, "narrative_authority": na}
    gm = {"player_facing_text": "x", "tags": [], "response_policy": pol}
    raw = (
        "Also, a bonded clerk mentioned a sealed side entrance the patrol never lists. "
        "The ledger was planted."
    )
    text_rd, _, _ = _apply_response_delta_layer(
        raw,
        gm_output=gm,
        strict_social_details=None,
        response_type_debug=_rt_debug(),
        answer_completeness_meta={"answer_completeness_failed": False},
        strict_social_path=False,
    )
    text_na, meta, _ = feg._apply_narrative_authority_layer(
        text_rd,
        gm_output=gm,
        resolution=res,
        strict_social_details=None,
        response_type_debug=_rt_debug(),
        answer_completeness_meta={"answer_completeness_failed": False},
        session={},
        scene_id="s",
    )
    assert meta["narrative_authority_repaired"] is True
    assert "side entrance" in text_na.lower()
    assert "planted" not in text_na.lower()


def test_na_repair_then_scene_anchor_still_matches_location():
    res = {"kind": "observe", "prompt": "I scan the pier."}
    na = _na_contract(resolution=res)
    sac = {
        "enabled": True,
        "required_any_of": ["location", "actor", "player_action"],
        "location_tokens": ["pier", "salt"],
        "actor_tokens": [],
        "player_action_tokens": [],
        "scene_location_label": "Salt Pier",
    }
    gm = {
        "player_facing_text": "x",
        "response_policy": {"narrative_authority": na},
        "scene_state_anchor_contract": sac,
    }
    raw = "At the salt pier, gulls wheel overhead. The ledger was planted."
    text, _, _ = feg._apply_narrative_authority_layer(
        raw,
        gm_output=gm,
        resolution=res,
        strict_social_details=None,
        response_type_debug=_rt_debug(),
        answer_completeness_meta={},
        session={},
        scene_id="pier",
    )
    text2, ssa_meta = feg._apply_scene_state_anchor_layer(
        feg._normalize_text(text),
        gm_output=gm,
        strict_social_details=None,
        response_type_debug=_rt_debug(),
    )
    assert ssa_meta.get("scene_state_anchor_passed") is True
    assert "location" in (ssa_meta.get("scene_state_anchor_matched_kinds") or [])
    assert "salt pier" in text2.lower()
