"""Owner tests for ``fallback_behavior`` validator predicate semantics.

Failures here should point first to
``game.final_emission_validators.validate_fallback_behavior``.

Downstream gate/retry tests should not duplicate detailed predicate ownership;
they should only observe invocation, propagation, or end-to-end behavior.
"""

from __future__ import annotations

import pytest

from game.final_emission_validators import validate_fallback_behavior
from tests.helpers.fallback_behavior_fixtures import fallback_contract
from tests.helpers.opening_fallback_evidence import (
    assert_fallback_validator_failure,
    assert_fallback_validator_pass,
)


pytestmark = pytest.mark.unit


def test_validate_fallback_behavior_skips_cleanly_without_contract() -> None:
    out = validate_fallback_behavior("No names yet. Check the ward clerk.", None)

    assert_fallback_validator_pass(
        out,
        checked=False,
        contract_present=False,
        skip_reason="no_contract",
    )


def test_validate_fallback_behavior_skips_cleanly_when_uncertainty_inactive() -> None:
    out = validate_fallback_behavior(
        "Captain Verrick did it.",
        fallback_contract(uncertainty_active=False),
    )

    assert_fallback_validator_pass(
        out,
        checked=False,
        uncertainty_active=False,
        skip_reason="uncertainty_inactive",
    )


def test_validate_fallback_behavior_fails_on_invented_certainty() -> None:
    out = validate_fallback_behavior(
        "The culprit was Captain Verrick. Check the ward clerk at the east gate office.",
        fallback_contract(),
    )

    assert_fallback_validator_failure(
        out,
        failure_reason="invented_certainty",
        invented_certainty_detected=True,
    )


def test_validate_fallback_behavior_fails_on_fabricated_authority() -> None:
    out = validate_fallback_behavior(
        "The records show it was Captain Verrick. Check the ward clerk at the east gate office.",
        fallback_contract(),
    )

    assert_fallback_validator_failure(
        out,
        failure_reason="fabricated_authority",
        fabricated_authority_detected=True,
    )


def test_validate_fallback_behavior_fails_on_meta_fallback_voice() -> None:
    out = validate_fallback_behavior(
        "I don't have enough information to answer confidently. Check the ward clerk at the east gate office.",
        fallback_contract(),
    )

    assert_fallback_validator_failure(
        out,
        failure_reason="meta_fallback_voice",
        meta_fallback_voice_detected=True,
    )


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
    out = validate_fallback_behavior(text, fallback_contract())

    assert_fallback_validator_failure(
        out,
        failure_reason="meta_fallback_voice",
        meta_fallback_voice_detected=True,
    )


def test_validate_fallback_behavior_accepts_bounded_partial_shape() -> None:
    out = validate_fallback_behavior(
        "No name comes clear from what shows. Check the ward clerk at the east gate office.",
        fallback_contract(),
    )

    assert_fallback_validator_pass(
        out,
        checked=True,
        partial_information_detected=True,
        known_edge_present=True,
        unknown_edge_present=True,
        next_lead_present=True,
    )


def test_validate_fallback_behavior_rejects_bare_thin_identity_line_without_known_and_lead() -> None:
    out = validate_fallback_behavior(
        "No name comes clear from what shows.",
        fallback_contract(),
    )

    assert_fallback_validator_failure(
        out,
        failure_reason="bounded_partial_insufficient_substance",
    )


def test_validate_fallback_behavior_accepts_single_clarifying_question_when_partial_not_allowed() -> None:
    out = validate_fallback_behavior(
        "Which one do you mean?",
        fallback_contract(
            allowed_behaviors={
                "ask_clarifying_question": True,
                "hedge_appropriately": False,
                "provide_partial_information": False,
            },
            prefer_partial_over_question=False,
        ),
    )

    assert_fallback_validator_pass(
        out,
        clarifying_question_detected=True,
        question_count=1,
    )


def test_validate_fallback_behavior_fails_when_question_count_exceeds_contract_cap() -> None:
    out = validate_fallback_behavior(
        "Which one do you mean? Which place are you asking about?",
        fallback_contract(
            allowed_behaviors={
                "ask_clarifying_question": True,
                "hedge_appropriately": False,
                "provide_partial_information": False,
            },
            prefer_partial_over_question=False,
        ),
    )

    assert_fallback_validator_failure(
        out,
        failure_reason="too_many_clarifying_questions",
        question_count=2,
    )


def test_validate_fallback_behavior_rejects_bare_question_when_partial_is_preferred() -> None:
    out = validate_fallback_behavior(
        "Which one do you mean?",
        fallback_contract(),
    )

    assert_fallback_validator_failure(
        out,
        failure_reason="question_used_when_partial_preferred",
        clarifying_question_detected=True,
    )
