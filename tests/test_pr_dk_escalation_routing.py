"""PR-DK deterministic escalation routing investigation tests."""
from __future__ import annotations

import pytest

from experiments.pr_dk.runner import run_comparison

pytestmark = pytest.mark.unit


def test_pr_dk_independent_checks_catch_pr_dj_misses_without_provider_calls() -> None:
    payload = run_comparison()
    rows = {row["scenario_id"]: row for row in payload["rows"]}

    assert payload["live_provider_calls"] == 0
    assert all(row["pre_mutation_signal"] for row in payload["rows"])
    assert all(row["state_changed"] is False for row in payload["rows"])

    assert rows["C1"]["A_classification"] == "MISSED_TRIGGER"
    assert rows["compound"]["A_classification"] == "MISSED_TRIGGER"
    assert rows["ambiguous"]["A_classification"] == "MISSED_TRIGGER"

    assert rows["C1"]["B_classification"] == "CORRECT_TRIGGER"
    assert rows["compound"]["B_classification"] == "CORRECT_TRIGGER"
    assert rows["ambiguous"]["B_classification"] == "CORRECT_TRIGGER"

    assert rows["C1"]["independent_checks"]["consequential_social_interpretation"] is True
    assert rows["compound"]["independent_checks"]["multiple_independent_action_clauses"] is True
    assert rows["ambiguous"]["independent_checks"]["unresolved_personal_pronoun"] is True


def test_pr_dk_comparison_keeps_universal_policy_hypothetical() -> None:
    payload = run_comparison()
    metrics = payload["metrics"]
    core = {
        row["scenario_id"]: row
        for row in payload["rows"]
        if row["scenario_id"]
        in {
            "S1",
            "C1",
            "compound",
            "ambiguous",
            "declared_canon",
            "mechanical_dump",
            "control_movement",
            "control_combat",
            "control_observation",
            "control_authored_fact",
            "control_followup",
        }
    }
    core_tp = sum(1 for row in core.values() if row["A_requested"] and row["assistance_justified"])
    core_fn = sum(1 for row in core.values() if not row["A_requested"] and row["assistance_justified"])

    assert core_tp / (core_tp + core_fn) == pytest.approx(0.4)
    assert metrics["B"]["recall"] > metrics["A"]["recall"]
    assert metrics["C"]["recall"] == pytest.approx(1.0)
    assert metrics["C"]["false_positive"] > 0
