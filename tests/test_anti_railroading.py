"""Unit tests for ``game.anti_railroading`` (anti-railroading contract + validator)."""
from __future__ import annotations

import pytest

from game.anti_railroading import (
    ALLOWED_LEAD_ROLES,
    FORBIDDEN_LEAD_ROLES,
    anti_railroading_repair_hints,
    build_anti_railroading_contract,
    validate_anti_railroading,
)

pytestmark = pytest.mark.unit


def _contract(**kwargs):
    return build_anti_railroading_contract(
        resolution=kwargs.get("resolution"),
        narration_obligations=kwargs.get("narration_obligations"),
        session_view=kwargs.get("session_view"),
        scene_state_anchor_contract=kwargs.get("scene_state_anchor_contract"),
        speaker_selection_contract=kwargs.get("speaker_selection_contract"),
        narrative_authority_contract=kwargs.get("narrative_authority_contract"),
        prompt_leads=kwargs.get("prompt_leads"),
        active_pending_leads=kwargs.get("active_pending_leads"),
        follow_surface=kwargs.get("follow_surface"),
        player_text=kwargs.get("player_text"),
    )


def test_build_contract_minimum_surface_and_vocab():
    c = _contract(
        prompt_leads=[{"id": "L1", "title": "Harbor rumor"}],
        session_view={"active_pending_leads": [{"id": "L2", "label": "Seal breach"}]},
    )
    assert c["enabled"] is True
    assert c["surfaced_lead_ids"] == ["L1", "L2"]
    assert "Harbor rumor" in c["surfaced_lead_labels"]
    assert c["allowed_lead_roles"] == list(ALLOWED_LEAD_ROLES)
    assert c["forbidden_lead_roles"] == list(FORBIDDEN_LEAD_ROLES)
    assert "debug_reason" in c and "debug_inputs" in c and "debug_flags" in c


# --- PASS cases ---


def test_pass_lead_as_one_option_among_several():
    c = _contract()
    text = (
        "One option is the lighthouse signal; another is the magistrate's hall; "
        "a third is to wait on the quay and watch who boards next."
    )
    out = validate_anti_railroading(text, c)
    assert out["checked"] is True
    assert out["passed"] is True
    assert out["failure_reasons"] == []


def test_pass_rumor_as_pressure_not_destiny():
    c = _contract()
    text = (
        "Dockhands whisper about a sealed hold—the rumor tightens the clock, "
        "but it does not prove any single course."
    )
    out = validate_anti_railroading(text, c)
    assert out["passed"] is True


def test_pass_resolved_scene_transition_direction():
    res = {"kind": "travel", "resolved_transition": True}
    c = _contract(resolution=res)
    text = "You step through the arch into the lower ward, noise and lantern-smoke washing over you."
    out = validate_anti_railroading(text, c, resolution=res)
    assert out["passed"] is True


def test_pass_hard_constraints_without_player_action_decision():
    c = _contract(scene_state_anchor_contract={"enabled": True})
    text = "The bridge is out; the river roars below. The gate is locked from the outside."
    out = validate_anti_railroading(text, c)
    assert out["passed"] is True


def test_pass_exclusivity_when_authoritative_resolution():
    res = {"kind": "investigate", "success": True}
    c = _contract(resolution=res)
    text = (
        "The only way forward is through the collapsed tunnel; "
        "that much is settled by what you found."
    )
    out = validate_anti_railroading(text, c, resolution=res)
    assert out["passed"] is True


def test_pass_explicit_player_commitment_allows_direction_echo():
    pt = "I'll head to the archives and see whether the register survived the fire."
    c = _contract(player_text=pt)
    text = "You head toward the archives, letting the crowd's current carry you a block at a time."
    out = validate_anti_railroading(text, c, player_text=pt)
    assert out["passed"] is True


# --- FAIL cases ---


def test_fail_you_decide_to_follow():
    c = _contract()
    out = validate_anti_railroading("You decide to follow the priest.", c)
    assert out["passed"] is False
    assert "player_decision_override" in out["failure_reasons"]
    assert out["assertion_flags"]["player_decision_override"] is True


def test_fail_only_real_lead_is_lighthouse():
    c = _contract()
    out = validate_anti_railroading("The only real lead is the lighthouse.", c)
    assert out["passed"] is False
    assert out["assertion_flags"]["lead_plot_gravity"] is True


def test_fail_it_becomes_clear_you_must():
    c = _contract()
    out = validate_anti_railroading("It becomes clear you must confront the captain.", c)
    assert out["passed"] is False
    assert "exclusive_path_claim" in out["failure_reasons"]


def test_fail_story_pulls_toward_destination():
    c = _contract()
    out = validate_anti_railroading("The story now pulls you toward Greywake.", c)
    assert out["passed"] is False
    assert out["assertion_flags"]["lead_plot_gravity"] is True


def test_fail_no_choice_but_trail():
    c = _contract()
    out = validate_anti_railroading("There is no choice but to take the sahuagin trail.", c)
    assert out["passed"] is False
    assert out["assertion_flags"]["exclusive_path_claim"] is True


def test_fail_main_plot_framing():
    c = _contract()
    out = validate_anti_railroading("This is the main plot, so treat it as central.", c)
    assert out["passed"] is False
    assert out["assertion_flags"]["lead_plot_gravity"] is True


def test_fail_obvious_answer_you_go_archives():
    c = _contract()
    out = validate_anti_railroading("The answer is obvious: you go to the archives.", c)
    assert out["passed"] is False
    assert out["assertion_flags"]["forced_conclusion"] is True


def test_fail_surfaced_lead_becomes_required_destination():
    c = _contract(
        prompt_leads=[{"id": "h1", "title": "Harbor warehouse"}],
    )
    text = "The Harbor warehouse lead isn't optional; you're going there now."
    out = validate_anti_railroading(text, c)
    assert out["passed"] is False
    assert out["assertion_flags"]["forced_direction"] is True
    assert out["assertion_flags"]["exclusive_path_claim"] is True


# --- Regression: lead pressure vs forced pathing / implied hostility ---


def test_regression_lead_pressure_allows_urgency_without_forced_path():
    c = _contract()
    text = (
        "The harbor rumor puts real time pressure on the decision, "
        "but several angles—including silence—remain legitimate."
    )
    out = validate_anti_railroading(text, c)
    assert out["passed"] is True


def test_regression_lead_urgency_does_not_authorize_forced_pathing():
    c = _contract()
    text = "The harbor lead is urgent; you have to go there now."
    out = validate_anti_railroading(text, c)
    assert out["passed"] is False
    assert out["assertion_flags"]["forced_direction"] is True


def test_repair_hints_nonempty_on_failure():
    c = _contract()
    val = validate_anti_railroading("You choose to abandon the docks.", c)
    hints = anti_railroading_repair_hints(val)
    assert hints
    assert any("decide" in h.lower() or "player" in h.lower() for h in hints)


def test_repair_hints_empty_when_passed():
    c = _contract()
    val = validate_anti_railroading("You could stay, push, or watch.", c)
    assert anti_railroading_repair_hints(val) == []


def test_fail_you_head_straight_to_destination():
    c = _contract()
    out = validate_anti_railroading("You head straight to the archive.", c)
    assert out["passed"] is False
    assert out["assertion_flags"]["forced_direction"] is True


def test_fail_story_wants_you_to_go():
    c = _contract()
    out = validate_anti_railroading("This is where the story wants you to go.", c)
    assert out["passed"] is False
    assert out["assertion_flags"]["lead_plot_gravity"] is True


def test_fail_everything_points_so_you_go_there():
    c = _contract()
    out = validate_anti_railroading("Everything points to Greywake, so you go there.", c)
    assert out["passed"] is False
    assert out["assertion_flags"]["forced_direction"] is True


def test_fail_obvious_you_must_follow():
    c = _contract()
    out = validate_anti_railroading("It's obvious now that you must follow the priest.", c)
    assert out["passed"] is False
    assert out["assertion_flags"]["forced_conclusion"] is True
