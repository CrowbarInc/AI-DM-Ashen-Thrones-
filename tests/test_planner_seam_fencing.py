"""Planner seam fencing — CTIR vs phrase-heuristic RTC lanes (trace + containment)."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from game.ctir import build_ctir
from game.narration_plan_bundle import build_narration_plan_bundle
from game.narrative_plan_upstream import compute_narrative_plan_for_bundle_from_head
from game.planner_seam_fencing import (
    GUARD_CTIR_BACKED_BUNDLE_REQUIRED,
    GUARD_FALLBACK_VISIBLE_FAILURE,
    GUARD_LEGACY_NO_CTIR_ONLY,
    GUARD_NON_CTIR_SEMANTIC_PATH,
    GUARD_PHRASE_HEURISTICS_LEGACY_LANE,
    GUARD_PLAYER_TEXT_RTC_FALLBACK,
    resolve_response_type_contract_for_planner_seam,
    response_type_seam_already_traced,
)
from game.planner_input_manifest import PHRASE_PATCH_AUDIT
from game.response_policy_contracts import coerce_valid_response_type_contract
from game.response_type_gating import derive_response_type_contract

pytestmark = pytest.mark.unit


def test_resolve_ctir_with_peek_skips_phrase_fallback_and_does_not_use_derive_player_channel() -> None:
    """metadata.response_type_contract wins; phrase regex lane must not decide semantics."""
    md_rtc = {
        "required_response_type": "dialogue",
        "source_route": "social",
        "allow_escalation": True,
        "escalation_block_reason": None,
        "strict_target_id": "npc_a",
        "strict_answer_expected": False,
        "strict_dialogue_expected": True,
        "action_must_preserve_agency": False,
        "debug_reasons": [],
    }
    assert coerce_valid_response_type_contract(md_rtc) is not None
    head_resolution = {"kind": "question", "metadata": {"response_type_contract": md_rtc}}
    with patch("game.planner_seam_fencing.derive_response_type_contract") as mock_derive:
        got, trace = resolve_response_type_contract_for_planner_seam(
            ctir_attached=True,
            resolution_sem=head_resolution,
            response_policy={},
            interaction_context={},
            user_text="WHO ARE YOU???",
        )
    mock_derive.assert_not_called()
    assert trace[GUARD_PLAYER_TEXT_RTC_FALLBACK] is False
    assert trace["source"] == "resolution_metadata_peek"
    assert got["required_response_type"] == "dialogue"


def test_resolve_ctir_without_metadata_uses_suppressed_derive_not_player_phrase_regex() -> None:
    """When peek is absent, CTIR path uses suppress_phrase_heuristics (no regex question lane)."""
    resolution = {"kind": "neutral_narration"}

    def _capture_derive(**kwargs):
        assert kwargs.get("suppress_phrase_heuristics") is True
        return derive_response_type_contract(**kwargs)

    with patch("game.planner_seam_fencing.derive_response_type_contract", side_effect=_capture_derive):
        _got, trace = resolve_response_type_contract_for_planner_seam(
            ctir_attached=True,
            resolution_sem=resolution,
            response_policy={},
            interaction_context={},
            user_text="who what where why?",  # would flip question bits if phrases ran
        )
    assert trace["phrase_heuristics_suppressed"] is True
    assert trace[GUARD_PLAYER_TEXT_RTC_FALLBACK] is False


def test_resolve_non_ctir_enables_legacy_phrase_lane() -> None:
    resolution = {"kind": "neutral_narration"}

    def _capture_derive(**kwargs):
        assert kwargs.get("suppress_phrase_heuristics") is False
        return derive_response_type_contract(**kwargs)

    with patch("game.planner_seam_fencing.derive_response_type_contract", side_effect=_capture_derive):
        _, trace = resolve_response_type_contract_for_planner_seam(
            ctir_attached=False,
            resolution_sem=resolution,
            response_policy={},
            interaction_context={},
            user_text="hello?",
        )
    assert trace[GUARD_PLAYER_TEXT_RTC_FALLBACK] is True
    assert trace[GUARD_PHRASE_HEURISTICS_LEGACY_LANE] is True


def test_compute_bundle_records_rtc_trace_and_skips_redundant_derive_on_second_pass() -> None:
    """compute_narrative_plan_for_bundle_from_head mutates response_policy; traced seam prevents re-derive."""
    ctir = build_ctir(
        turn_id=1,
        scene_id="s1",
        player_input="x",
        builder_source="tests.fencing",
        narrative_anchors={
            "scene_framing": [],
            "actors_speakers": [],
            "outcomes": [],
            "uncertainty": [],
            "next_leads_affordances": [],
        },
        resolution={"kind": "neutral_narration"},
        interaction={"active_target_id": "npc_a", "interaction_mode": "social"},
    )
    head = {
        "ctir_obj": ctir,
        "resolution_sem": {"kind": "neutral_narration"},
        "interaction_sem": {},
        "response_policy": {"narrative_authority": "standard"},
        "visibility_contract": {"visible_entity_ids": [], "visible_entity_names": []},
        "public_scene": {"id": "s1"},
        "scene_state_anchor_contract": {},
        "active_pending_leads": [],
        "session_view": {},
        "recent_log_compact": [],
        "narration_obligations": {},
    }
    compute_narrative_plan_for_bundle_from_head(head, user_text="test")
    rp = head["response_policy"]
    assert response_type_seam_already_traced(rp)
    with patch("game.planner_seam_fencing.derive_response_type_contract") as mock_derive:
        assert coerce_valid_response_type_contract(rp.get("response_type_contract"))
        _, trace = resolve_response_type_contract_for_planner_seam(
            ctir_attached=True,
            resolution_sem=head["resolution_sem"],
            response_policy=rp,
            interaction_context={},
            user_text="OVERRIDE TEXT",
        )
    mock_derive.assert_not_called()
    assert trace["source"] == "response_policy_prevalidated"


def test_scene_opening_fallback_marker_scan_is_non_authoritative() -> None:
    """Fallback markers only trigger structural validation paths — not alternate opener authority."""
    from game.narrative_planning import _scan_scene_opening_for_proseish_keys

    hit = _scan_scene_opening_for_proseish_keys("template opener leak", prefix="derivation_codes", depth=0)
    assert hit is not None
    assert "fallback_marker" in hit


def test_bundle_no_ctir_labels_legacy_path() -> None:
    bundle = build_narration_plan_bundle(session={}, narration_context_kwargs={})
    pm = bundle["plan_metadata"]
    assert pm.get(GUARD_LEGACY_NO_CTIR_ONLY) is True
    assert pm.get(GUARD_NON_CTIR_SEMANTIC_PATH) is True
    assert pm.get(GUARD_CTIR_BACKED_BUNDLE_REQUIRED) is False


def test_phrase_patch_audit_has_containment_or_todo() -> None:
    """Each phrase_patch / narrow_scenario_patch row documents containment or deferral."""
    for row in PHRASE_PATCH_AUDIT:
        if row.get("kind") not in ("phrase_patch", "narrow_scenario_patch"):
            continue
        note = row.get("containment") or row.get("containment_deferred")
        assert isinstance(note, str) and note.strip(), row.get("artifact")
