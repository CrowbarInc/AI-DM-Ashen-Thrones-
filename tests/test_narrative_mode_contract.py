import pytest

from game.narrative_mode_contract import (
    build_narrative_mode_contract,
    looks_like_narrative_mode_contract,
    validate_narrative_mode_contract,
)


def _ctir_stub(*, resolution: dict | None = None) -> dict:
    # Minimal CTIR-like shape; builder reads only a few dotted fields.
    return {
        "version": 1,
        "resolution": resolution or {},
    }


def test_selects_opening_when_opening_obligation_set() -> None:
    c = build_narrative_mode_contract(
        narration_obligations={"is_opening_scene": True},
        ctir=_ctir_stub(),
    )
    assert c["mode"] == "opening"
    ok, reasons = validate_narrative_mode_contract(c)
    assert ok, reasons


def test_selects_transition_when_scene_change_required() -> None:
    c = build_narrative_mode_contract(
        narration_obligations={"must_advance_scene": True},
        ctir=_ctir_stub(),
    )
    assert c["mode"] == "transition"
    ok, reasons = validate_narrative_mode_contract(c)
    assert ok, reasons


def test_selects_dialogue_when_social_reply_expected() -> None:
    c = build_narrative_mode_contract(
        narration_obligations={"active_npc_reply_expected": True, "active_npc_reply_kind": "answer"},
        ctir=_ctir_stub(),
    )
    assert c["mode"] == "dialogue"
    assert "no_dialogue_without_speaker_basis" in c["forbidden_moves"]


def test_selects_exposition_answer_when_answer_required() -> None:
    c = build_narrative_mode_contract(
        response_policy={"answer_completeness": {"answer_required": True, "answer_must_come_first": True}},
        ctir=_ctir_stub(),
    )
    assert c["mode"] == "exposition_answer"
    assert c["prompt_obligations"]["answer_first"] is True


def test_selects_action_outcome_when_outcome_present() -> None:
    c = build_narrative_mode_contract(
        ctir=_ctir_stub(resolution={"skill_check": {"kind": "perception"}, "requires_check": False}),
    )
    assert c["mode"] == "action_outcome"
    assert "no_resultless_outcome" in c["forbidden_moves"]


def test_selects_transition_over_dialogue_when_scene_change_prioritized() -> None:
    c = build_narrative_mode_contract(
        narration_obligations={"must_advance_scene": True, "active_npc_reply_expected": True},
        ctir=_ctir_stub(),
    )
    assert c["mode"] == "transition"


def test_selects_dialogue_over_answer_required_when_required_response_type_dialogue() -> None:
    c = build_narrative_mode_contract(
        response_policy={
            "response_type_contract": {"required_response_type": "dialogue"},
            "answer_completeness": {"answer_required": True},
        },
        ctir=_ctir_stub(),
    )
    assert c["mode"] == "dialogue"


def test_selects_opening_over_answer_required_and_dialogue_signals() -> None:
    """Opening is highest precedence: direct question + answer policy must not flip the mode."""
    c = build_narrative_mode_contract(
        narration_obligations={
            "is_opening_scene": True,
            "active_npc_reply_expected": True,
        },
        response_policy={
            "response_type_contract": {"required_response_type": "dialogue"},
            "answer_completeness": {"answer_required": True},
        },
        ctir=_ctir_stub(),
    )
    assert c["mode"] == "opening"


def test_selects_transition_over_active_npc_reply_signals() -> None:
    c = build_narrative_mode_contract(
        narration_obligations={
            "must_advance_scene": True,
            "active_npc_reply_expected": True,
            "suppress_non_social_emitters": True,
        },
        ctir=_ctir_stub(),
    )
    assert c["mode"] == "transition"


def test_selects_dialogue_when_required_response_type_only() -> None:
    c = build_narrative_mode_contract(
        response_policy={"response_type_contract": {"required_response_type": "dialogue"}},
        ctir=_ctir_stub(),
    )
    assert c["mode"] == "dialogue"


def test_pending_requires_check_without_skill_check_is_not_action_outcome() -> None:
    c = build_narrative_mode_contract(
        ctir=_ctir_stub(
            resolution={
                "kind": "interact",
                "requires_check": True,
                "check_request": {"kind": "skill", "skill": "thieves_tools"},
            }
        ),
    )
    assert c["mode"] == "continuation"


def test_requires_check_with_dc_only_skill_check_stub_is_not_action_outcome() -> None:
    """Echoed scene/config skill_check without a resolved roll must not select action_outcome."""
    c = build_narrative_mode_contract(
        ctir=_ctir_stub(
            resolution={
                "kind": "interact",
                "label": "pick_lock",
                "requires_check": True,
                "check_request": {"kind": "skill", "skill": "thieves_tools"},
                "skill_check": {"skill_id": "thieves_tools", "dc": 14},
            }
        ),
    )
    assert c["mode"] == "continuation"


def test_requires_check_with_resolved_skill_check_is_action_outcome() -> None:
    c = build_narrative_mode_contract(
        ctir=_ctir_stub(
            resolution={
                "kind": "interact",
                "requires_check": True,
                "skill_check": {
                    "skill": "thieves_tools",
                    "dc": 14,
                    "roll": 12,
                    "modifier": 4,
                    "total": 16,
                    "success": True,
                },
            }
        ),
    )
    assert c["mode"] == "action_outcome"


def test_kind_check_requires_check_without_roll_stays_continuation() -> None:
    """Matches structural CTIR used in narrative_plan regressions (prompt-for-roll, not outcome)."""
    c = build_narrative_mode_contract(
        ctir=_ctir_stub(resolution={"kind": "check", "requires_check": True}),
    )
    assert c["mode"] == "continuation"


def test_attack_with_dc_only_skill_check_still_action_outcome_when_check_not_required() -> None:
    """Combat / attack payloads may carry DC-only skill_check metadata; not the same as pending player roll."""
    c = build_narrative_mode_contract(
        ctir=_ctir_stub(
            resolution={
                "kind": "attack",
                "requires_check": False,
                "skill_check": {"dc": 12},
                "authoritative_outputs": {},
            }
        ),
    )
    assert c["mode"] == "action_outcome"


def test_selects_continuation_for_non_special_follow_up() -> None:
    c = build_narrative_mode_contract(ctir=_ctir_stub())
    assert c["mode"] == "continuation"
    assert "no_generic_fallback" in c["forbidden_moves"]


def test_looks_like_accepts_built_contract() -> None:
    c = build_narrative_mode_contract(ctir=_ctir_stub())
    assert looks_like_narrative_mode_contract(c) is True


def test_validator_rejects_unknown_mode() -> None:
    bad = build_narrative_mode_contract(ctir=_ctir_stub())
    bad["mode"] = "unknown"
    ok, reasons = validate_narrative_mode_contract(bad)
    assert ok is False
    assert any(r.startswith("narrative_mode_contract:unknown_mode:") for r in reasons)


def test_validator_rejects_missing_mode() -> None:
    bad = build_narrative_mode_contract(ctir=_ctir_stub())
    bad.pop("mode", None)
    ok, reasons = validate_narrative_mode_contract(bad)
    assert ok is False
    assert "narrative_mode_contract:missing_mode" in reasons


def test_validator_rejects_multi_mode_structures() -> None:
    bad = build_narrative_mode_contract(ctir=_ctir_stub())
    bad["modes"] = ["opening", "dialogue"]
    ok, reasons = validate_narrative_mode_contract(bad)
    assert ok is False
    assert "narrative_mode_contract:forbidden_multi_mode_field:modes" in reasons


def test_validator_rejects_prompt_obligations_non_prompt_safe_values() -> None:
    bad = build_narrative_mode_contract(ctir=_ctir_stub())
    bad["prompt_obligations"] = {"answer_first": {"nested": True}}  # not allowed
    ok, reasons = validate_narrative_mode_contract(bad)
    assert ok is False
    assert "narrative_mode_contract:prompt_obligations_bad_value:answer_first" in reasons


def test_validator_rejects_mode_family_mismatch() -> None:
    bad = build_narrative_mode_contract(ctir=_ctir_stub())
    bad["mode_family"] = "wrong_family"
    ok, reasons = validate_narrative_mode_contract(bad)
    assert ok is False
    assert "narrative_mode_contract:mode_family_mismatch" in reasons

