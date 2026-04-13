"""Unit tests for ``game.playability_eval`` (deterministic, no model calls)."""

from __future__ import annotations

import pytest

from game.playability_eval import SCHEMA_VERSION, evaluate_playability

pytestmark = pytest.mark.unit


def _assert_stable_schema(out: dict) -> None:
    assert out["version"] == SCHEMA_VERSION
    overall = out["overall"]
    assert set(overall) == {"score", "rating", "passed"}
    assert isinstance(overall["score"], int)
    assert overall["rating"] in {"strong", "acceptable", "weak"}
    assert isinstance(overall["passed"], bool)
    assert set(out["axes"]) == {
        "direct_answer",
        "player_intent",
        "logical_escalation",
        "immersion",
    }
    for ax in out["axes"].values():
        assert set(ax) == {"score", "passed", "reasons", "signals"}
        assert isinstance(ax["score"], int)
        assert 0 <= ax["score"] <= 25
        assert isinstance(ax["passed"], bool)
        assert isinstance(ax["reasons"], list)
        assert isinstance(ax["signals"], dict)
    summ = out["summary"]
    assert set(summ) == {"strengths", "failures", "warnings"}
    for k in summ:
        assert isinstance(summ[k], list)
    gv = out.get("gameplay_validation")
    assert isinstance(gv, dict)
    for key in (
        "run_valid",
        "excluded_from_scoring",
        "invalidation_reason",
        "dead_turn_count",
        "infra_failure_count",
        "dead_turn",
    ):
        assert key in gv
    assert isinstance(gv.get("dead_turn"), dict)


def test_direct_answer_high_for_clear_question_and_answer():
    out = evaluate_playability(
        {
            "player_prompt": "Who commands the watch here?",
            "gm_text": (
                "Captain Halvar commands the watch; sergeants rotate shifts and the gate stays tight after curfew."
            ),
        }
    )
    _assert_stable_schema(out)
    ax = out["axes"]["direct_answer"]
    assert ax["score"] >= 20
    assert ax["passed"] is True


def test_bounded_partial_with_next_lead_passes():
    out = evaluate_playability(
        {
            "player_prompt": "Who stole the relic from the chapel?",
            "gm_text": (
                "It is unclear who took it, but the east lane crew trades solid rumors; head there and ask quietly."
            ),
        }
    )
    _assert_stable_schema(out)
    ax = out["axes"]["direct_answer"]
    assert ax["passed"] is True
    assert ax["signals"].get("bounded_partial") is True
    assert ax["signals"].get("next_lead") is True


def test_procedural_dodge_scores_poorly():
    out = evaluate_playability(
        {
            "player_prompt": "What happened at the gate last night?",
            "gm_text": (
                "Per the rules, I need you to be more specific about what you mean without more information."
            ),
        }
    )
    _assert_stable_schema(out)
    assert out["axes"]["direct_answer"]["score"] <= 12
    assert out["axes"]["direct_answer"]["passed"] is False


def test_narrow_follow_up_gets_specific_credit():
    out = evaluate_playability(
        {
            "prior_player_prompt": "Tell me about the thief.",
            "prior_gm_text": "A shadow slips through the market; details are thin.",
            "player_prompt": "Who exactly was seen near the dye vats?",
            "gm_text": "Witnesses name Mira Keth lingering by the dye vats until the bells rang.",
        }
    )
    _assert_stable_schema(out)
    intent = out["axes"]["player_intent"]
    assert intent["signals"].get("narrowing") is True
    assert intent["score"] >= 20
    assert intent["passed"] is True


def test_repeated_stale_gm_hurts_logical_escalation():
    prior = "The guards watch the gate quietly; a notice is posted."
    out = evaluate_playability(
        {
            "prior_player_prompt": "What do I see at the gate?",
            "prior_gm_text": prior,
            "player_prompt": "I press again: what is actually posted on the notice?",
            "gm_text": prior,
        }
    )
    _assert_stable_schema(out)
    esc = out["axes"]["logical_escalation"]
    assert esc["signals"].get("gm_repeat_jaccard", 0) >= 0.9
    assert esc["score"] <= 12
    assert esc["passed"] is False


def test_system_validator_leakage_hurts_immersion():
    out = evaluate_playability(
        {
            "player_prompt": "I glance at the notice.",
            "gm_text": "The validator flagged established state drift; the router wants a cleaner scene anchor.",
        }
    )
    _assert_stable_schema(out)
    imm = out["axes"]["immersion"]
    assert imm["score"] <= 10
    assert imm["passed"] is False
    assert imm["signals"].get("leak_hits", 0) >= 1


def test_malformed_minimal_payload_returns_valid_schema():
    for payload in [None, {}, [], "not-a-dict", {"gm_output": object()}]:
        out = evaluate_playability(payload)  # type: ignore[arg-type]
        _assert_stable_schema(out)


def test_dead_turn_excludes_from_scoring_but_preserves_axis_diagnostics():
    """DTD1 ``validation_playable: false`` must zero overall pass/score; axes remain for inspection."""
    fem = {
        "dead_turn": {
            "is_dead_turn": True,
            "dead_turn_reason_codes": ["upstream_api_error"],
            "dead_turn_class": "upstream_api_failure",
            "validation_playable": False,
            "manual_test_valid": False,
        }
    }
    out = evaluate_playability(
        {
            "player_prompt": "Who commands the watch here?",
            "gm_text": "Captain Halvar commands the watch; sergeants rotate shifts.",
            "gm_output": {"player_facing_text": "x", "_final_emission_meta": fem},
        }
    )
    _assert_stable_schema(out)
    assert out["overall"]["score"] == 0
    assert out["overall"]["passed"] is False
    assert out["gameplay_validation"]["excluded_from_scoring"] is True
    assert out["gameplay_validation"]["dead_turn_count"] == 1
    assert out["gameplay_validation"]["raw_overall"]["score"] > 0
    assert out["axes"]["direct_answer"]["score"] >= 15


def test_synthetic_terminal_fallback_without_upstream_not_dead_stays_scoreable():
    """DTD1 marks non-dead; evaluator must not infer dead from tags/routes here."""
    fem = {
        "dead_turn": {
            "is_dead_turn": False,
            "dead_turn_class": "none",
            "validation_playable": True,
            "dead_turn_reason_codes": [],
            "manual_test_valid": True,
        }
    }
    out = evaluate_playability(
        {
            "player_prompt": "What happened?",
            "gm_text": "A forced terminal fallback line without upstream metadata.",
            "gm_output": {
                "player_facing_text": "Fallback prose.",
                "tags": ["forced_retry_fallback", "retry_escape_hatch"],
                "_final_emission_meta": fem,
            },
        }
    )
    _assert_stable_schema(out)
    assert out["gameplay_validation"]["run_valid"] is True
    assert out["overall"]["passed"] is True
