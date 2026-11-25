"""Harness validation for the controlled model evaluation. No live provider."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))

from controlled_model_evaluation.cases import CASES, sequences
from controlled_model_evaluation.harness import discover_identity, negative_safety_checks, validate
from controlled_model_evaluation.pricing import (
    MAX_INPUT_TOKENS_PER_CALL,
    MAX_OUTPUT_TOKENS_PER_CALL,
    MAX_TOTAL_PROVIDER_CALLS,
    MEASURED_INTERPRETATION_INPUT_TOKENS,
    MEASURED_NARRATION_INPUT_TOKENS,
    approved_cost_ceiling,
)
from controlled_model_evaluation.scoring import FAIL, PARTIAL, PASS


def test_case_distribution_is_twenty_across_five_sequences():
    assert len(CASES) == 20
    grouped = sequences()
    assert set(grouped) == {"A", "B", "C", "D", "E"}
    assert all(len(turns) == 4 for turns in grouped.values())
    assert len({case.utterance for case in CASES}) == 20


def test_cost_ceiling_uses_uncached_published_rates():
    assert MEASURED_NARRATION_INPUT_TOKENS <= MAX_INPUT_TOKENS_PER_CALL
    assert MEASURED_INTERPRETATION_INPUT_TOKENS <= MAX_INPUT_TOKENS_PER_CALL
    assert MAX_OUTPUT_TOKENS_PER_CALL == 600
    assert MAX_TOTAL_PROVIDER_CALLS == 40
    assert approved_cost_ceiling() == __import__("decimal").Decimal("0.53")


def test_fixture_scores_distinguish_model_and_orchestration():
    report = validate(Path(__file__).resolve().parents[1] / "development" / "tmp" / "controlled_model_eval_unit")
    by_name = {row["fixture"]: row for row in report["fixture_results"]}
    assert by_name["successful_notice"]["scores"]["admission"] == PASS
    assert by_name["successful_notice"]["execution_success"] is True
    assert by_name["rejected_teleport"]["withholding_required_held"] is True
    assert by_name["rejected_teleport"]["execution_success"] is False
    assert by_name["ambiguous_clarification"]["scores"]["reference"] == PARTIAL
    assert by_name["negation_executed"]["attribution"]["primary"] == "MODEL_INTERPRETATION"
    assert by_name["orchestration_withholds_valid_reading"]["attribution"]["primary"] == "ACTION_ADMISSION"
    assert by_name["orchestration_withholds_valid_reading"]["scores"]["admission"] == PARTIAL
    assert by_name["orchestration_withholds_valid_reading"]["execution_success"] is False
    assert by_name["deterministic_miss_without_model"]["attribution"]["primary"] == "ACTION_CLASSIFICATION"
    assert by_name["provider_timeout"]["attribution"]["primary"] == "PROVIDER_TIMEOUT"
    assert by_name["provider_timeout"]["scores"]["operational"] == FAIL
    assert by_name["provider_transport"]["attribution"]["primary"] == "PROVIDER_TRANSPORT"
    assert by_name["false_arrival"]["scores"]["consequence"] == FAIL
    assert by_name["recall_without_commit"]["scores"]["consequence"] == PASS
    assert report["provider_calls_during_validation"] == 0
    assert report["negative_failures"] == []
    assert report["redaction_sample_clean"] is True
    assert report["identity"]["model"] == "gpt-4.1-mini"


def test_negative_gate_refuses_each_required_condition(tmp_path):
    rows = negative_safety_checks(tmp_path, discover_identity())
    assert rows
    assert all(row["refused"] for row in rows)
    reasons = {row["name"]: row["reason"] for row in rows}
    assert reasons["no_authorization"] == "no authorization exists"
    assert reasons["pricing_unverified"] == "pricing unverified"
    assert reasons["budget_exceeded"] == "call ceiling would be exceeded"
    assert reasons["retry_exceeds_calls"] == "retry would exceed call ceiling"
    assert reasons["input_token_limit"] == "request would exceed input-token limit"


def test_isolated_sessions_make_no_provider_call(tmp_path):
    report = validate(tmp_path / "validation", include_isolation=True)
    isolation = report["isolation"]
    assert isolation["openai_constructed"] == 0
    assert isolation["external_hosts"] == []
    assert isolation["isolated"] is True
    assert isolation["turns"]["left"]["provider_records"] == 0
    assert isolation["turns"]["right"]["provider_records"] == 0
    assert isolation["turns"]["left"]["status"] == 200
    assert isolation["turns"]["right"]["status"] == 200
    assert report["provider_calls_during_validation"] == 0
