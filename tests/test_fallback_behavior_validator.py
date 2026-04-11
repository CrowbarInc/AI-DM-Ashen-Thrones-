from __future__ import annotations

import pytest

from game.final_emission_validators import validate_fallback_behavior


pytestmark = pytest.mark.unit


def _fallback_contract(**overrides: object) -> dict:
    contract = {
        "enabled": True,
        "uncertainty_active": True,
        "uncertainty_sources": ["unknown_identity"],
        "uncertainty_mode": "scene_ambiguity",
        "allowed_behaviors": {
            "ask_clarifying_question": True,
            "hedge_appropriately": True,
            "provide_partial_information": True,
        },
        "disallowed_behaviors": {
            "invented_certainty": True,
            "fabricated_authority": True,
            "meta_system_explanations": True,
        },
        "diegetic_only": True,
        "max_clarifying_questions": 1,
        "prefer_partial_over_question": True,
        "require_partial_to_state_known_edge": True,
        "require_partial_to_state_unknown_edge": True,
        "require_partial_to_offer_next_lead": True,
        "allowed_hedge_forms": [
            "I can't swear to it, but",
            "From what I saw,",
            "As far as rumor goes,",
            "Looks like",
            "Hard to tell, but",
        ],
        "forbidden_hedge_forms": [
            "I lack enough information to answer confidently.",
            "The system cannot confirm that.",
            "Canon proves it.",
            "As an AI, I don't know.",
            "There is insufficient context available.",
        ],
        "allowed_authority_bases": [
            "direct_observation",
            "established_report",
            "rumor_marked_as_rumor",
            "visible_evidence",
        ],
        "forbidden_authority_bases": [
            "unsupported_named_culprit",
            "unsupported_exact_location",
            "unsupported_motive_as_fact",
            "unsupported_procedural_certainty",
            "system_or_canon_claims",
        ],
        "debug": {},
    }
    contract.update(overrides)
    return contract


def test_validate_fallback_behavior_skips_cleanly_without_contract() -> None:
    out = validate_fallback_behavior("No names yet. Check the ward clerk.", None)

    assert out["checked"] is False
    assert out["contract_present"] is False
    assert out["skip_reason"] == "no_contract"
    assert out["passed"] is True


def test_validate_fallback_behavior_skips_cleanly_when_uncertainty_inactive() -> None:
    out = validate_fallback_behavior(
        "Captain Verrick did it.",
        _fallback_contract(uncertainty_active=False),
    )

    assert out["checked"] is False
    assert out["uncertainty_active"] is False
    assert out["skip_reason"] == "uncertainty_inactive"
    assert out["passed"] is True


def test_validate_fallback_behavior_fails_on_invented_certainty() -> None:
    out = validate_fallback_behavior(
        "The culprit was Captain Verrick. Check the ward clerk at the east gate office.",
        _fallback_contract(),
    )

    assert out["passed"] is False
    assert out["invented_certainty_detected"] is True
    assert "invented_certainty" in out["failure_reasons"]


def test_validate_fallback_behavior_fails_on_fabricated_authority() -> None:
    out = validate_fallback_behavior(
        "The records show it was Captain Verrick. Check the ward clerk at the east gate office.",
        _fallback_contract(),
    )

    assert out["passed"] is False
    assert out["fabricated_authority_detected"] is True
    assert "fabricated_authority" in out["failure_reasons"]


def test_validate_fallback_behavior_fails_on_meta_fallback_voice() -> None:
    out = validate_fallback_behavior(
        "I don't have enough information to answer confidently. Check the ward clerk at the east gate office.",
        _fallback_contract(),
    )

    assert out["passed"] is False
    assert out["meta_fallback_voice_detected"] is True
    assert "meta_fallback_voice" in out["failure_reasons"]


@pytest.mark.parametrize(
    "text",
    [
        "The reason is still unclear.",
        "That is not settled until the move plays out.",
        "Anyone willing to talk? GM: That is not settled until the move plays out.",
        "The answer remains unresolved.",
        "That depends on how the move plays out.",
    ],
)
def test_validate_fallback_behavior_catches_meta_adjudicative_uncertainty_leaks(text: str) -> None:
    out = validate_fallback_behavior(text, _fallback_contract())

    assert out["passed"] is False
    assert out["meta_fallback_voice_detected"] is True
    assert "meta_fallback_voice" in out["failure_reasons"]


def test_validate_fallback_behavior_accepts_bounded_partial_shape() -> None:
    out = validate_fallback_behavior(
        "No name comes clear from what shows. Check the ward clerk at the east gate office.",
        _fallback_contract(),
    )

    assert out["checked"] is True
    assert out["passed"] is True
    assert out["partial_information_detected"] is True
    assert out["known_edge_present"] is True
    assert out["unknown_edge_present"] is True
    assert out["next_lead_present"] is True


def test_validate_fallback_behavior_accepts_single_clarifying_question_when_partial_not_allowed() -> None:
    out = validate_fallback_behavior(
        "Which one do you mean?",
        _fallback_contract(
            allowed_behaviors={
                "ask_clarifying_question": True,
                "hedge_appropriately": False,
                "provide_partial_information": False,
            },
            prefer_partial_over_question=False,
        ),
    )

    assert out["passed"] is True
    assert out["clarifying_question_detected"] is True
    assert out["question_count"] == 1


def test_validate_fallback_behavior_fails_when_question_count_exceeds_contract_cap() -> None:
    out = validate_fallback_behavior(
        "Which one do you mean? Which place are you asking about?",
        _fallback_contract(
            allowed_behaviors={
                "ask_clarifying_question": True,
                "hedge_appropriately": False,
                "provide_partial_information": False,
            },
            prefer_partial_over_question=False,
        ),
    )

    assert out["passed"] is False
    assert out["question_count"] == 2
    assert "too_many_clarifying_questions" in out["failure_reasons"]


def test_validate_fallback_behavior_rejects_bare_question_when_partial_is_preferred() -> None:
    out = validate_fallback_behavior(
        "Which one do you mean?",
        _fallback_contract(),
    )

    assert out["passed"] is False
    assert out["clarifying_question_detected"] is True
    assert "question_used_when_partial_preferred" in out["failure_reasons"]
