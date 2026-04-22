"""C4 — deterministic ``validate_narrative_mode_output`` (per-mode positive/negative)."""

from __future__ import annotations

import pytest

from game.final_emission_meta import (
    NARRATIVE_MODE_OUTPUT_FEM_KEYS,
    default_narrative_mode_output_layer_meta,
    merge_narrative_mode_output_into_final_emission_meta,
)
from game.narrative_mode_contract import (
    build_narrative_mode_emission_trace,
    build_narrative_mode_contract,
    validate_narrative_mode_output,
)

pytestmark = pytest.mark.unit


def _contract(**kwargs: object) -> dict:
    return build_narrative_mode_contract(**kwargs)


def test_skips_when_contract_disabled_or_invalid() -> None:
    c = _contract(enabled=False)
    r = validate_narrative_mode_output("any", c)
    assert r["checked"] is False
    assert r["passed"] is True
    bad = dict(c)
    bad["mode"] = "bogus"
    r2 = validate_narrative_mode_output("any", bad)
    assert r2["checked"] is False


def test_opening_passes_fresh_scene_without_mid_thread() -> None:
    c = _contract(
        narration_obligations={"is_opening_scene": True},
    )
    text = "The square gathers torchlight against the mist. You stand at the eastern curb with the crowd."
    r = validate_narrative_mode_output(text, c)
    assert r["checked"] and r["passed"]
    assert r["mode"] == "opening"
    assert r["failure_reasons"] == []


def test_opening_fails_mid_thread_shape() -> None:
    c = _contract(narration_obligations={"is_opening_scene": True})
    text = "As we discussed earlier, the sergeant still waits by the east gate with folded arms."
    r = validate_narrative_mode_output(text, c)
    assert r["checked"] and not r["passed"]
    assert "nmo:opening:mid_thread_continuation_shape" in r["failure_reasons"]


def test_opening_fails_answer_buried_under_tableau_when_answer_pressure() -> None:
    c = _contract(narration_obligations={"is_opening_scene": True})
    text = "The mist beads on stone. The east gate lies two hundred feet south along the market road."
    rp = {"answer_completeness": {"answer_required": True}}
    r = validate_narrative_mode_output(text, c, response_policy=rp)
    assert r["checked"] and not r["passed"]
    assert "nmo:opening:answer_buried_under_tableau" in r["failure_reasons"]
    assert r["repairable"] is True


def test_continuation_passes_thread_forward() -> None:
    c = _contract(ctir=_minimal_ctir_continuation())
    text = "You still hold the sergeant's gaze; he nods once toward the east lane without breaking stride."
    r = validate_narrative_mode_output(text, c)
    assert r["checked"] and r["passed"]


def test_continuation_fails_fresh_opening_reset() -> None:
    c = _contract(ctir=_minimal_ctir_continuation())
    text = "You wake to a new day. The market unfolds around you as if nothing before it mattered."
    r = validate_narrative_mode_output(text, c)
    assert r["checked"] and not r["passed"]
    assert "nmo:continuation:fresh_opening_reset_shape" in r["failure_reasons"]


def test_continuation_fails_scenic_regrounding_without_transition() -> None:
    c = _contract(ctir=_minimal_ctir_continuation())
    text = "The square holds silence while mist gathers at the eastern gate and torchlight presses the cobbles."
    r = validate_narrative_mode_output(text, c)
    assert r["checked"] and not r["passed"]
    assert "nmo:continuation:scenic_regrounding_without_transition" in r["failure_reasons"]


def test_action_outcome_passes_early_result() -> None:
    c = _contract(
        ctir=_minimal_ctir_action_outcome(),
    )
    text = "You find nothing new in the crate. The alley stays quiet except for distant footsteps."
    r = validate_narrative_mode_output(text, c, resolution=_minimal_ctir_action_outcome())
    assert r["checked"] and r["passed"]


def test_action_outcome_fails_result_not_frontloaded() -> None:
    c = _contract(ctir=_minimal_ctir_action_outcome())
    text = (
        "The mist holds the alley in a grey hush. "
        "A rusted chain sags from the staple while drafts slide along the stones without settling."
    )
    r = validate_narrative_mode_output(text, c, resolution=_minimal_ctir_action_outcome())
    assert r["checked"] and not r["passed"]
    assert "nmo:action_outcome:result_not_frontloaded" in r["failure_reasons"]


def test_action_outcome_fails_atmosphere_before_result() -> None:
    c = _contract(ctir=_minimal_ctir_action_outcome())
    text = "The mist beads along the stones. You find nothing new in the crate after a long breath."
    r = validate_narrative_mode_output(text, c, resolution=_minimal_ctir_action_outcome())
    assert r["checked"] and not r["passed"]
    assert "nmo:action_outcome:atmosphere_before_result" in r["failure_reasons"]
    assert r["repairable"] is True


def test_action_outcome_fails_unresolved_mixed_with_landed_result_when_pending() -> None:
    c = _contract(ctir=_minimal_ctir_action_outcome())
    res = _resolution_pending_check()
    text = "You succeed immediately, yet the outcome remains unresolved until the roll settles."
    r = validate_narrative_mode_output(text, c, resolution=res)
    assert r["checked"] and not r["passed"]
    assert "nmo:action_outcome:unresolved_check_treated_as_result" in r["failure_reasons"]


def test_dialogue_passes_spoken_reply() -> None:
    c = _contract(
        response_policy={
            "response_type_contract": {"required_response_type": "dialogue"},
        },
    )
    text = 'He shrugs once. "East gate lies two hundred feet south—watch keeps that lane."'
    r = validate_narrative_mode_output(text, c)
    assert r["checked"] and r["passed"]


def test_dialogue_fails_scenic_recap_dominates() -> None:
    c = _contract(
        response_policy={
            "response_type_contract": {"required_response_type": "dialogue"},
        },
    )
    text = (
        "The checkpoint rumor describes supply movements, watch rotations, curfew lanes, patrol timings, "
        "merchant grudges, barracks gossip, seal stamps, toll ledgers, river tariffs, forge quotas, "
        "guild pledges, warehouse seals, night-watch swaps, lantern laws, bridge levies, wharf fees, "
        "smithy quotas, pier tariffs, wagon levies, granary seals, dock manifests, yard postings, "
        "clerk rotations, watchhouse maps, lantern routes, postern keys, seal wax orders, barracks chalkboards, "
        "and which officers avoid the yard; nothing in it names a single responsible sergeant for the east "
        "gate roster tonight or which lane stays open after curfew when the river patrol shifts."
    )
    r = validate_narrative_mode_output(text, c)
    assert r["checked"] and not r["passed"]
    assert "nmo:dialogue:scenic_recap_dominates" in r["failure_reasons"]


def test_dialogue_fails_missing_reply_continuity_moderate_length() -> None:
    c = _contract(
        response_policy={
            "response_type_contract": {"required_response_type": "dialogue"},
        },
    )
    text = (
        "The sergeant studies your face, then the lane, then the distant gate without committing "
        "to a direction or naming anyone who holds the watch roster."
    )
    r = validate_narrative_mode_output(text, c)
    assert r["checked"] and not r["passed"]
    assert "nmo:dialogue:missing_reply_continuity" in r["failure_reasons"]


def test_transition_passes_motion() -> None:
    c = _contract(
        narration_obligations={"must_advance_scene": True},
    )
    text = "You step through the east gate into the yard where torchlight pools along the wall."
    r = validate_narrative_mode_output(text, c)
    assert r["checked"] and r["passed"]


def test_transition_fails_no_scene_change_motion() -> None:
    c = _contract(narration_obligations={"must_advance_scene": True})
    text = "He meets your eyes and says nothing while the same crowd murmurs at your back."
    r = validate_narrative_mode_output(text, c)
    assert r["checked"] and not r["passed"]
    assert "nmo:transition:no_scene_change_motion" in r["failure_reasons"]


def test_exposition_answer_passes_direct_lead() -> None:
    c = _contract(
        response_policy={"answer_completeness": {"answer_required": True}},
    )
    text = "The east gate lies two hundred feet south along the market road past the checkpoint."
    r = validate_narrative_mode_output(text, c)
    assert r["checked"] and r["passed"]


def test_exposition_answer_fails_answer_buried() -> None:
    c = _contract(
        response_policy={"answer_completeness": {"answer_required": True}},
    )
    text = (
        "For a breath the scene holds while voices shift around you. "
        "The east gate lies two hundred feet south along the market road."
    )
    r = validate_narrative_mode_output(text, c)
    assert r["checked"] and not r["passed"]
    assert "nmo:exposition_answer:answer_buried" in r["failure_reasons"]
    assert r["repairable"] is True


def test_exposition_answer_fails_fabricated_action_resolution() -> None:
    c = _contract(
        response_policy={"answer_completeness": {"answer_required": True}},
    )
    text = "Your blow lands cleanly for 12 damage. The east gate is two hundred feet south."
    r = validate_narrative_mode_output(text, c)
    assert r["checked"] and not r["passed"]
    assert "nmo:exposition_answer:fabricated_action_resolution" in r["failure_reasons"]


def test_generic_meta_fallback_fails_all_modes() -> None:
    c = _contract(ctir=_minimal_ctir_continuation())
    text = "I don't have enough information to describe the lane beyond insufficient context here."
    r = validate_narrative_mode_output(text, c)
    assert r["checked"] and not r["passed"]
    assert "nmo:generic_meta_fallback_voice" in r["failure_reasons"]


def test_build_narrative_mode_emission_trace_and_fem_merge() -> None:
    c = _contract(narration_obligations={"is_opening_scene": True})
    v = validate_narrative_mode_output("As before, the gate waits.", c)
    trace = build_narrative_mode_emission_trace(v, narrative_mode_contract=c)
    assert trace["narrative_mode_output_checked"] is True
    assert trace["narrative_mode_output_passed"] is False
    fem: dict = {}
    merge_narrative_mode_output_into_final_emission_meta(fem, trace)
    for k in NARRATIVE_MODE_OUTPUT_FEM_KEYS:
        if k in trace:
            assert k in fem
    d = default_narrative_mode_output_layer_meta()
    assert set(d.keys()) == NARRATIVE_MODE_OUTPUT_FEM_KEYS


def _minimal_ctir_continuation() -> dict:
    return {"resolution": {"kind": "narrate", "requires_check": False}}


def _minimal_ctir_action_outcome() -> dict:
    return {
        "resolution": {
            "kind": "skill_check",
            "requires_check": False,
            "skill_check": {"success": True, "roll": 14, "total": 18},
            "outcome_type": "search",
        }
    }


def _resolution_pending_check() -> dict:
    return {"resolution": {"requires_check": True, "skill_check": {"dc": 12, "skill_id": "perception"}}}
