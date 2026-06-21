"""Anti-Railroading contract, validator, and gate-layer ownership coverage.

Unit tests cover ``game.anti_railroading`` directly. Gate-integration tests cover
pass/fail/repair/replace semantics through the downstream emission facade without
owning gate ordering.
"""
from __future__ import annotations

import game.final_emission_visibility_fallback as visibility_fallback
import pytest

from game.anti_railroading import (
    ALLOWED_LEAD_ROLES,
    FORBIDDEN_LEAD_ROLES,
    anti_railroading_repair_hints,
    build_anti_railroading_contract,
    validate_anti_railroading,
)
from game.final_emission_anti_railroading import (
    apply_anti_railroading_layer,
    repair_anti_railroading_narrow,
    resolve_anti_railroading_contract,
)
from tests.helpers.replay_fem_read_smoke import final_emission_meta_from_output
from tests.helpers.gate_orchestration_smoke import apply_final_emission_gate_consumer

pytestmark = pytest.mark.unit


def _apply_gate(*args, **kwargs):
    out, _ = apply_final_emission_gate_consumer(*args, **kwargs)
    return out


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


# --- Gate-layer integration (Anti-Railroading ownership) ---


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
        out = _apply_gate(
            {"player_facing_text": raw, "tags": [], "anti_railroading_contract": _ar_contract()},
            resolution={"kind": "observe", "prompt": "I look around."},
            session={},
            scene_id="dock",
            world={},
        )
        assert out.get("player_facing_text") == raw
        meta = final_emission_meta_from_output(out) or {}
        assert meta.get("anti_railroading_repaired") is False
        em = (out.get("metadata") or {}).get("emission_debug") or {}
        assert em.get("anti_railroading", {}).get("validation", {}).get("passed") is True


def test_anti_railroading_gate_repairs_forced_pathing():
    out = _apply_gate(
        {"player_facing_text": "You head straight to the archive.", "tags": []},
        resolution={"kind": "observe", "prompt": "I look."},
        session={},
        scene_id="s",
        world={},
    )
    meta = final_emission_meta_from_output(out) or {}
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
        out = _apply_gate(
            {"player_facing_text": raw, "tags": []},
            resolution={"kind": "observe", "prompt": "I listen."},
            session={},
            scene_id="s",
            world={},
        )
        meta = final_emission_meta_from_output(out) or {}
        assert meta.get("anti_railroading_failed") is True, raw
        assert meta.get("anti_railroading_repaired") is False, raw
        assert meta.get("final_route") == "replaced", raw


def test_anti_railroading_resolved_transition_allows_arrival_language():
    res = {"kind": "travel", "resolved_transition": True, "prompt": "I enter the ward."}
    c = _ar_contract(resolution=res)
    raw = "You step through the arch into the lower ward, noise washing over you."
    out = _apply_gate(
        {"player_facing_text": raw, "tags": [], "anti_railroading_contract": c},
        resolution=res,
        session={},
        scene_id="ward",
        world={},
    )
    assert out.get("player_facing_text") == raw
    assert (final_emission_meta_from_output(out) or {}).get("anti_railroading_repaired") is False


def test_anti_railroading_commitment_echo_allowed_when_player_committed():
    pt = "I'll head to the archives and check the register."
    c = _ar_contract(player_text=pt)
    raw = "You head toward the archives, letting the crowd carry you a block at a time."
    out = _apply_gate(
        {"player_facing_text": raw, "tags": [], "anti_railroading_contract": c},
        resolution={"kind": "observe", "prompt": pt},
        session={"scene_runtime": {"test_scene": {"last_player_action_text": pt}}},
        scene_id="test_scene",
        world={},
    )
    assert out.get("player_facing_text") == raw


def test_anti_railroading_quoted_dialogue_not_spuriously_flagged():
    raw = 'The clerk mutters, "You head straight to the archive." Then the door clicks.'
    out = _apply_gate(
        {"player_facing_text": raw, "tags": []},
        resolution={"kind": "observe", "prompt": "I listen."},
        session={},
        scene_id="s",
        world={},
    )
    assert '"' in (out.get("player_facing_text") or "")
    meta = final_emission_meta_from_output(out) or {}
    assert meta.get("anti_railroading_repaired") is False


def test_anti_railroading_prompt_context_contract_resolution():
    c = _ar_contract()
    out = _apply_gate(
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
    fem = final_emission_meta_from_output(out) or {}
    assert fem.get("anti_railroading_failed") is True
    assert fem.get("anti_railroading_repaired") is False
    assert fem.get("anti_railroading_contract_resolution_source") == "shipped"
    assert fem.get("final_route") == "replaced"


def test_anti_railroading_surfaced_lead_mandatory_repair(monkeypatch):
    """Surfaced-lead mandatory framing fails AR validation and triggers non-social replace."""
    monkeypatch.setattr(visibility_fallback, "apply_visibility_enforcement", lambda out, **kwargs: out)
    c = _ar_contract(prompt_leads=[{"id": "h1", "title": "Harbor warehouse"}])
    raw = "The Harbor warehouse lead isn't optional; you're going there now."
    out = _apply_gate(
        {"player_facing_text": raw, "tags": [], "anti_railroading_contract": c},
        resolution={"kind": "observe", "prompt": "I look."},
        session={},
        scene_id="s",
        world={},
    )
    fem = final_emission_meta_from_output(out) or {}
    assert fem.get("anti_railroading_failed") is True
    assert fem.get("final_route") == "replaced"


def test_bj33_repair_anti_railroading_narrow_softens_forced_direction() -> None:
    c = _ar_contract()
    validation = validate_anti_railroading("You head straight to the archive.", c)
    repaired, mode = repair_anti_railroading_narrow(
        "You head straight to the archive.",
        validation,
        contract=c,
        player_text="Where next?",
        resolution={"kind": "observe", "prompt": "Where next?"},
    )
    assert repaired is not None
    assert mode
    assert "head straight" not in str(repaired).lower()


def test_bj33_resolve_anti_railroading_contract_from_direct_field() -> None:
    c = _ar_contract()
    gm = {"anti_railroading_contract": c}
    assert resolve_anti_railroading_contract(gm) is c


def test_bj33_apply_anti_railroading_layer_boundary_no_rewrite_on_failure() -> None:
    c = _ar_contract()
    text, meta, extra = apply_anti_railroading_layer(
        "You decide to follow the priest.",
        gm_output={"anti_railroading_contract": c},
        resolution={"kind": "observe", "prompt": "I look around."},
        session={},
        scene_id="s",
        response_type_debug={
            "response_type_required": None,
            "response_type_contract_source": None,
            "response_type_candidate_ok": True,
            "response_type_repair_used": False,
            "response_type_repair_kind": None,
            "response_type_rejection_reasons": [],
        },
        strict_social_details=None,
    )
    assert text == "You decide to follow the priest."
    assert meta.get("anti_railroading_failed") is True
    assert meta.get("anti_railroading_repaired") is False
    assert "anti_railroading_unsatisfied_at_boundary_no_rewrite" in extra
