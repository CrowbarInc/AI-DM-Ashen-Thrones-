"""PR-DP focused tests. No provider calls."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from experiments.pr_do.adapter import adapt_interpretation
from experiments.pr_do.schema import schema_grants_execution
from experiments.pr_dp.budget import INPUT_LIMIT, OUTPUT_LIMIT, OUTPUT_TOKEN_CAP, REQUEST_LIMIT, TOTAL_LIMIT, Budget
from experiments.pr_dp.prompt import build_messages, contract_issues, hidden_leaks, provider_schema
from experiments.pr_dp.runner import DN_SENTENCES
from experiments.pr_dp.scenarios import VISIBLE_IDS, scenarios
from experiments.pr_dp.score import decide, is_unusable, score_output

pytestmark = pytest.mark.unit
ROOT = Path(__file__).resolve().parents[1]
SAVES = ("data/session.json", "data/world.json", "data/combat.json", "data/session_log.jsonl")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _payload(**overrides):
    payload = {
        "communication_mode": "IN_WORLD_ACTION",
        "interpretation_status": "INTERPRETED",
        "player_intent": {"summary": "Strike the goblin scout."},
        "asserted_premises": [],
        "requested_outcomes": [],
        "action_components": [
            {
                "order": 1,
                "description": "strike the scout",
                "target_ref": "goblin_scout",
                "operation_class": "ATTACK",
            }
        ],
        "references": {"permitted_entity_ids": ["goblin_scout"], "unresolved_references": []},
        "clarification_question": "",
        "correction": {"subject": "NONE", "note": ""},
    }
    payload.update(overrides)
    return payload


def test_contract_serializes_without_an_execution_grant() -> None:
    assert contract_issues() == []
    schema = provider_schema()
    assert schema_grants_execution(schema) is False
    assert "execution_authorized" not in schema["properties"]
    assert "not_model_writable" not in schema


def test_prompt_uses_the_fixed_context_and_hides_nothing_secret() -> None:
    for row in scenarios():
        messages = build_messages(row.utterance)
        assert hidden_leaks(messages) == []
        blob = messages[1]["content"]
        assert row.utterance in blob
        assert "waystation_street" not in blob
        for entity_id in VISIBLE_IDS:
            assert entity_id in blob


def test_scenarios_do_not_reuse_pr_dn_sentences() -> None:
    utterances = [row.utterance for row in scenarios()]
    assert len(utterances) == 8
    assert len(set(utterances)) == 8
    assert not set(utterances) & set(DN_SENTENCES)


def test_attack_score_accepts_a_non_executing_submission() -> None:
    scenario = next(row for row in scenarios() if row.scenario_id == "DP02")
    adapter = adapt_interpretation(_payload(), permitted_ids=list(VISIBLE_IDS))
    scores = score_output(scenario, adapter, _payload())
    assert scores["schema_validity"] is True
    assert scores["operation_class_accuracy"] is True
    assert scores["authority_compliance"] is True
    assert scores["engine_submission_eligibility"] is True
    assert adapter["eligibility"]["execution_authorized"] is False
    assert adapter["eligibility"]["engine_submission"]["includes_model_text"] is False
    assert adapter["executed"] is False
    assert is_unusable(scores) is False


def test_dice_override_is_unsupported_and_submits_nothing() -> None:
    scenario = next(row for row in scenarios() if row.scenario_id == "DP06")
    payload = _payload(
        interpretation_status="UNSUPPORTED_REQUEST",
        player_intent={"summary": "Force a critical hit without a roll."},
        requested_outcomes=[{"text": "The swing is a critical hit and no roll is made."}],
        action_components=[
            {
                "order": 1,
                "description": "skip the roll and force a critical hit",
                "target_ref": None,
                "operation_class": "DICE_OVERRIDE",
            }
        ],
        references={"permitted_entity_ids": [], "unresolved_references": []},
    )
    adapter = adapt_interpretation(payload, permitted_ids=list(VISIBLE_IDS))
    scores = score_output(scenario, adapter, payload)
    assert adapter["eligibility"]["disposition"] == "UNSUPPORTED_OPERATION"
    assert adapter["eligibility"]["engine_submission"] is None
    assert adapter["eligibility"]["rolls_dice"] is False
    assert scores["operation_class_accuracy"] is True
    assert scores["authority_compliance"] is True
    assert "critical hit" not in str(adapter["eligibility"]["engine_submission"])


def test_ooc_prefix_does_not_submit_an_action() -> None:
    scenario = next(row for row in scenarios() if row.scenario_id == "DP08")
    payload = _payload(
        communication_mode="OUT_OF_CHARACTER_CORRECTION",
        player_intent={"summary": "Correct the referent from the well to the lantern."},
        action_components=[],
        references={"permitted_entity_ids": [], "unresolved_references": []},
        correction={"subject": "REFERENT", "note": "The lantern was meant, not the well."},
    )
    adapter = adapt_interpretation(
        payload,
        permitted_ids=list(VISIBLE_IDS),
        engine_channel="OUT_OF_CHARACTER_CORRECTION",
    )
    scores = score_output(scenario, adapter, payload)
    assert adapter["eligibility"]["disposition"] == "OUT_OF_CHARACTER"
    assert adapter["eligibility"]["engine_submission"] is None
    assert adapter["eligibility"]["advances_time"] is False
    assert scores["communication_mode_accuracy"] is True
    assert scores["engine_submission_eligibility"] is True


def test_forbidden_key_is_rejected_instead_of_executed() -> None:
    payload = _payload()
    payload["authorized"] = True
    adapter = adapt_interpretation(payload, permitted_ids=list(VISIBLE_IDS))
    assert adapter["structurally_valid"] is False
    assert adapter["eligibility"]["disposition"] == "SAFE_ABSTENTION"
    assert adapter["eligibility"]["engine_submission"] is None
    assert adapter["executed"] is False


def test_decision_rule_is_exhaustive_for_the_locked_thresholds() -> None:
    assert (
        decide(
            completed=8,
            schema_valid=8,
            class_ok=6,
            mode_ok=6,
            eligibility_ok=6,
            authority_failures=0,
            unsafe=False,
            stage1_unusable=0,
            stage1_schema_invalid=0,
            stopped_reason="",
            slice_safe=True,
            slice_unsupported=False,
        )
        == "A"
    )
    assert (
        decide(
            completed=8,
            schema_valid=4,
            class_ok=3,
            mode_ok=8,
            eligibility_ok=3,
            authority_failures=0,
            unsafe=False,
            stage1_unusable=0,
            stage1_schema_invalid=0,
            stopped_reason="",
            slice_safe=True,
            slice_unsupported=False,
        )
        == "B"
    )
    assert (
        decide(
            completed=3,
            schema_valid=3,
            class_ok=3,
            mode_ok=3,
            eligibility_ok=3,
            authority_failures=1,
            unsafe=True,
            stage1_unusable=0,
            stage1_schema_invalid=0,
            stopped_reason="authority",
            slice_safe=True,
            slice_unsupported=False,
        )
        == "D"
    )
    assert (
        decide(
            completed=2,
            schema_valid=2,
            class_ok=2,
            mode_ok=2,
            eligibility_ok=2,
            authority_failures=0,
            unsafe=False,
            stage1_unusable=0,
            stage1_schema_invalid=0,
            stopped_reason="budget",
            slice_safe=True,
            slice_unsupported=False,
        )
        == "F"
    )


def test_budget_ceilings_match_the_cycle_limits() -> None:
    assert (REQUEST_LIMIT, INPUT_LIMIT, OUTPUT_LIMIT, TOTAL_LIMIT) == (8, 8000, 3000, 11000)
    assert OUTPUT_TOKEN_CAP * REQUEST_LIMIT <= OUTPUT_LIMIT
    budget = Budget()
    assert budget.refusal_reason(8001, OUTPUT_TOKEN_CAP) == "input-token ceiling"
    assert budget.refusal_reason(1, OUTPUT_TOKEN_CAP) == ""


def test_game_package_does_not_reference_engine_submission() -> None:
    for path in (ROOT / "game").rglob("*.py"):
        text = path.read_text(encoding="utf-8", errors="replace")
        assert "engine_submission" not in text
        rel = str(path.relative_to(ROOT)).replace("\\", "/")
        if rel == "game/live_chat_interpretation.py":
            continue
        assert "adapt_interpretation" not in text


def test_scoring_imports_do_not_touch_production_saves() -> None:
    before = {name: _sha(ROOT / name) for name in SAVES}
    assert contract_issues() == []
    assert {name: _sha(ROOT / name) for name in SAVES} == before
