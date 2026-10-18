"""PR-DL focused tests. No provider calls."""
from __future__ import annotations

import json

import pytest

from experiments.pr_dj.adapter import FORBIDDEN_KEYS
from experiments.pr_dl.budget import INPUT_LIMIT, OUTPUT_TOKEN_CAP, REQUEST_LIMIT, Budget
from experiments.pr_dl.evidence import evidence_corrections
from experiments.pr_dl.policies import invocation_classes, summarize_policy, usage_for
from experiments.pr_dl.prompt import hidden_leaks, interpretation_schema, schema_is_non_authoritative
from experiments.pr_dl.scoring import deterministic_gameplay, score_live

pytestmark = pytest.mark.unit

ROOT_HINT = __import__("pathlib").Path(__file__).resolve().parents[1]


def test_schema_has_no_authoritative_fields() -> None:
    schema = interpretation_schema()
    assert schema_is_non_authoritative(schema)
    assert not (set(schema["properties"]) & FORBIDDEN_KEYS)
    assert "advance_time" not in json.dumps(schema)


def test_budget_blocks_the_request_past_the_ceiling() -> None:
    budget = Budget(requests=REQUEST_LIMIT, input_tokens=0, output_tokens=0)
    assert budget.can_send(10, OUTPUT_TOKEN_CAP) is False
    near = Budget(requests=20, input_tokens=INPUT_LIMIT - 50, output_tokens=0)
    assert near.can_send(51, OUTPUT_TOKEN_CAP) is False
    assert near.can_send(50, OUTPUT_TOKEN_CAP) is True


def test_candidate_c_correction_uses_candidate_rows_only() -> None:
    payload = evidence_corrections(ROOT_HINT, [])
    candidate_c = payload["candidate_totals"]["C"]
    assert candidate_c["requests"] == 16
    assert candidate_c["input_tokens"] == 14569
    assert candidate_c["output_tokens"] == 1498
    assert candidate_c["total_tokens"] == 16067
    assert payload["published_matches_combined_not_candidate_c"] is True
    assert payload["manual_trace"]["provider_calls_observed"] is False
    assert payload["shared_pipeline_suite"]["status"] == "incomplete"
    assert payload["shared_pipeline_suite"]["passed"] is False


def test_ambiguous_clarification_is_not_scored_as_failure() -> None:
    scores = score_live(
        "ambiguous",
        {
            "status": "CLARIFICATION_REQUIRED",
            "interpreted_intent": "Ask whether to trust someone.",
            "clarification_required": True,
            "clarification_question": "Who is him, and who is the other one?",
            "unresolved_references": ["him", "the other one"],
            "ambiguous": True,
            "primary_operation": "unresolved",
            "referenced_entities": [],
            "multiple_action_components": [],
            "unsupported_action": "",
        },
        {"accepted": True, "errors": []},
    )
    assert scores["gameplay_usefulness"] == "PASS"
    assert scores["clarification_usefulness"] == "PASS"
    assert scores["schema_validity"] == "PASS"


def test_rejected_output_is_not_authority_compliance() -> None:
    scores = score_live(
        "S1",
        {"status": "INTERPRETED", "interpreted_intent": "Ask."},
        {"accepted": False, "errors": ["clarification status requires clarification_question"]},
    )
    assert scores["schema_validity"] == "FAIL"
    assert scores["authority_compliance"] == "NOT OBSERVABLE"
    assert scores["gameplay_usefulness"] == "FAIL"


def test_policy_replay_uses_one_stored_output() -> None:
    rows = [
        {
            "scenario_id": "compound",
            "B_requested": True,
            "deterministic_gameplay": "FAIL",
            "live_accepted": True,
            "live_gameplay": "PASS",
            "live_authority": "PASS",
            "live_clarification_useful": "NOT OBSERVABLE",
            "live_asserted_outcome": "PASS",
            "usage": {"input_tokens": 10, "output_tokens": 4, "total_tokens": 14},
        },
        {
            "scenario_id": "S1",
            "B_requested": False,
            "deterministic_gameplay": "PASS",
            "live_accepted": True,
            "live_gameplay": "FAIL",
            "live_authority": "PASS",
            "live_clarification_useful": "NOT OBSERVABLE",
            "live_asserted_outcome": "PASS",
            "usage": {"input_tokens": 8, "output_tokens": 3, "total_tokens": 11},
        },
    ]
    policy_a = summarize_policy(rows, "A")
    policy_b = summarize_policy(rows, "B")
    policy_c = summarize_policy(rows, "C")
    classes = invocation_classes(rows)
    assert policy_a["correctly_handled"] == ["S1"]
    assert policy_b["correctly_handled"] == ["compound", "S1"]
    assert policy_c["incorrect_interpretations"] == ["S1"]
    assert policy_c["correctly_handled"] == ["compound"]
    assert classes["beneficial_invocations"] == ["compound"]
    assert classes["harmful_invocations"] == ["S1"]
    assert classes["false_negatives"] == []
    assert classes["false_positives"] == []
    selective = usage_for(rows, selector=lambda row: row["B_requested"])
    universal = usage_for(rows, selector=lambda row: True)
    assert selective["provider_requests"] == 1
    assert selective["actual_total_tokens"] == 14
    assert universal["provider_requests"] == 2
    assert universal["actual_total_tokens"] == 25


def test_quote_travel_is_not_a_sufficient_deterministic_interpretation() -> None:
    assert deterministic_gameplay("var_quote_control", {"resolver": "travel", "operation": "act"}) == "FAIL"
    assert deterministic_gameplay("S1", {"resolver": "social", "operation": "ask"}) == "PASS"


def test_prompt_omits_hidden_strings() -> None:
    from experiments.pr_dg.state import frontier_bundle
    from experiments.pr_dl.prompt import build_messages

    bundle = frontier_bundle(bind=True)
    messages, _public = build_messages(bundle, "Guard Captain, do you prefer the rain?")
    assert hidden_leaks(messages, bundle.hidden_strings) == []
    blob = json.dumps(messages)
    assert "hidden_facts" not in blob
    assert "hit_points" not in blob
    assert "world_flags" not in blob
