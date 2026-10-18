"""PR-DJ selective interpretation contract tests."""
from __future__ import annotations

import pytest

from experiments.pr_dg.scenarios import AMBIGUOUS, DUMP, S1
from experiments.pr_dj.adapter import (
    STATUS_CLARIFICATION_REQUIRED,
    STATUS_INTERPRETED,
    validate_hand_authored_interpretation,
)
from experiments.pr_dj.runner import run_adapter_controls, run_routing_preflight

pytestmark = pytest.mark.unit


REFERENTS = [
    {"type": "interlocutor", "id": "guard_captain", "label": "Guard Captain", "source": "scene"},
    {"type": "enemy", "id": "goblin_1", "label": "goblin", "source": "scene"},
]


def test_adapter_accepts_non_authoritative_social_intent() -> None:
    result = validate_hand_authored_interpretation(
        {
            "status": STATUS_INTERPRETED,
            "interpreted_intent": "Ask the guard captain about a preference.",
            "referenced_entities": [{"type": "interlocutor", "id": "guard_captain"}],
            "primary_operation": "ask",
            "interlocutor_id": "guard_captain",
            "non_authoritative_explanation": "No outcome is asserted.",
        },
        raw_input=S1,
        canonical_referents=REFERENTS,
    )
    assert result.accepted is True
    assert result.executed is False
    assert result.mutated_state is False


def test_adapter_surfaces_clarification_without_guessing() -> None:
    result = validate_hand_authored_interpretation(
        {
            "status": STATUS_CLARIFICATION_REQUIRED,
            "clarification_required": True,
            "clarification_question": "Who do you mean by him?",
            "unresolved_references": ["him"],
            "primary_operation": "unresolved",
            "ambiguous": True,
        },
        raw_input=AMBIGUOUS,
        canonical_referents=REFERENTS,
    )
    assert result.accepted is True
    assert result.clarification == "Who do you mean by him?"
    assert result.unresolved_references == ("him",)


@pytest.mark.parametrize(
    "payload",
    [
        {"status": STATUS_INTERPRETED, "hit_points": {"goblin_1": 0}, "primary_operation": "act"},
        {"status": STATUS_INTERPRETED, "dice_result": 20, "primary_operation": "act"},
        {"status": STATUS_INTERPRETED, "world_flags": {"secret_open": True}, "primary_operation": "act"},
        {"status": STATUS_INTERPRETED, "resolver": "combat", "primary_operation": "act"},
        {"status": STATUS_INTERPRETED, "execute_action": True, "primary_operation": "act"},
    ],
)
def test_adapter_rejects_authoritative_fields(payload) -> None:
    result = validate_hand_authored_interpretation(payload, raw_input=DUMP, canonical_referents=REFERENTS)
    assert result.accepted is False
    assert result.executed is False
    assert result.mutated_state is False


def test_adapter_control_matrix_passes() -> None:
    payload = run_adapter_controls()
    assert payload["passed"] is True


def test_routing_preflight_is_deterministic_and_selective() -> None:
    payload = run_routing_preflight()
    assert payload["live_provider_calls"] == 0
    assert payload["precision_recall"]["precision"] == 1.0
    assert payload["precision_recall"]["recall"] == 0.4
    assert all(row["pre_mutation_signal"] for row in payload["rows"])
    assert all(row["state_changed"] is False for row in payload["rows"])
    classes = {row["scenario_id"]: row["classification"] for row in payload["rows"]}
    assert classes["compound"] == "MISSED_TRIGGER"
    assert classes["ambiguous"] == "MISSED_TRIGGER"
    assert classes["C1"] == "MISSED_TRIGGER"
    assert classes["declared_canon"] == "CORRECT_TRIGGER"
    assert classes["mechanical_dump"] == "CORRECT_TRIGGER"
    assert classes["control_movement"] == "NO_TRIGGER_NEEDED"
