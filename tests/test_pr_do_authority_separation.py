"""PR-DO authority separation tests. No provider calls."""

from __future__ import annotations

import ast
import hashlib
import inspect
from pathlib import Path

import pytest

from experiments.pr_do import LIVE_PROVIDER_CALLS, refuse_live_provider_call
from experiments.pr_do.adapter import adapt_interpretation
from experiments.pr_do.eligibility import evaluate_eligibility
from experiments.pr_do.fixtures import (
    COMBAT,
    GATE,
    adversarial_cases,
    canon_smuggle_payload,
    contract_cases,
    forbidden_payload,
)
from experiments.pr_do.replay import evaluate_case, replay_translations
from experiments.pr_do.routing import STORED_ROUTING, engine_channel_from_utterance, routing_assessment
from experiments.pr_do.schema import schema_document, schema_grants_execution
from experiments.pr_do.translate import STORED_RESULTS

pytestmark = pytest.mark.unit
ROOT = Path(__file__).resolve().parents[1]
SAVES = ("data/session.json", "data/world.json", "data/combat.json", "data/session_log.jsonl")


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _case(case_id: str) -> dict:
    return next(row for row in adversarial_cases() if row["case_id"] == case_id)


def test_schema_exposes_no_execution_grant() -> None:
    schema = schema_document()
    assert schema_grants_execution(schema) is False
    assert "execution_eligibility" in schema["not_model_writable"]


def test_eligibility_source_does_not_read_model_text() -> None:
    source = inspect.getsource(evaluate_eligibility)
    names = {node.id for node in ast.walk(ast.parse(source)) if isinstance(node, ast.Name)}
    assert "summary" not in names
    assert "re" not in names
    assert "search" not in names


def test_live_provider_path_is_closed_and_saves_stay_put() -> None:
    before = {name: _sha(ROOT / name) for name in SAVES}
    stored_before = _sha(STORED_RESULTS)
    assert LIVE_PROVIDER_CALLS == 0
    with pytest.raises(RuntimeError, match="forbids live provider calls"):
        refuse_live_provider_call()
    assert {name: _sha(ROOT / name) for name in SAVES} == before
    assert _sha(STORED_RESULTS) == stored_before


def test_failure_replay_keeps_claims_and_wishes_non_authoritative() -> None:
    by_id = {row["case_id"]: evaluate_case(row) for row in contract_cases()}
    favor = by_id["DN05"]
    assert favor["disposition"] == "UNSUPPORTED_OPERATION"
    assert favor["canon_statuses"] == ["PLAYER_CLAIM"]
    assert favor["adjudication_statuses"] == ["UNADJUDICATED"]
    assert favor["engine_submission"] is None
    assert favor["executed"] is False

    hp = by_id["DN07"]
    assert hp["operation_classes"] == ["HP_ASSIGNMENT", "DICE_OVERRIDE"]
    assert hp["disposition"] == "UNSUPPORTED_OPERATION"
    assert hp["rolls_dice"] is False

    inventory = by_id["DN08"]
    assert inventory["disposition"] == "UNSUPPORTED_OPERATION"
    assert "INVENTORY_GRANT" in inventory["operation_classes"]
    assert inventory["mutated_state"] is False

    assert by_id["DN09"]["disposition"] == "UNSUPPORTED_OPERATION"
    assert by_id["DN09"]["history_rewritten"] is False
    assert by_id["DN10"]["disposition"] == "UNSUPPORTED_OPERATION"
    assert by_id["DN10"]["reveals_hidden_information"] is False
    assert by_id["DN10"]["forbidden_keys_in_result"] == []


def test_ooc_corrections_do_not_become_actions() -> None:
    by_id = {row["case_id"]: evaluate_case(row) for row in contract_cases()}
    referent = by_id["DN04"]
    assert referent["disposition"] == "OUT_OF_CHARACTER"
    assert referent["consumes_action"] is False
    assert referent["advances_time"] is False
    assert referent["creates_npc_response"] is False
    assert referent["history_rewritten"] is False
    assert referent["engine_submission"] is None

    intention = by_id["DN12"]
    assert intention["disposition"] == "OUT_OF_CHARACTER"
    assert intention["history_disposition"] == "ADJUDICATION_REQUIRED"
    assert intention["history_rewritten"] is False
    assert intention["engine_submission"] is None

    forced = _case("ooc_correction")
    forced_result = evaluate_case(forced)
    assert forced["payload"]["communication_mode"] == "IN_WORLD_ACTION"
    assert forced_result["disposition"] == "OUT_OF_CHARACTER"
    assert forced_result["engine_submission"] is None


def test_compound_recognition_is_not_execution() -> None:
    by_id = {row["case_id"]: evaluate_case(row) for row in contract_cases()}
    first = by_id["DN01"]
    second = by_id["DN02"]
    assert first["component_orders"] == [1, 2]
    assert second["component_orders"] == [1, 2, 3]
    assert first["disposition"] == "ELIGIBLE_FOR_VALIDATION"
    assert second["disposition"] == "ELIGIBLE_FOR_VALIDATION"
    assert first["compound_transaction"] is False
    assert second["engine_submission"]["compound_transaction"] is False
    assert first["execution_authorized"] is False
    assert second["executed"] is False
    assert "The guard comes over." not in str(second["engine_submission"])
    assert second["unexpected_submission_tokens"] == []

    mixed = evaluate_case(_case("mixed_compound_with_grant"))
    assert mixed["component_orders"] == [1, 2]
    assert mixed["disposition"] == "UNSUPPORTED_OPERATION"
    assert mixed["engine_submission"] is None


def test_descriptive_text_cannot_become_execution_authority() -> None:
    descriptive = evaluate_case(_case("descriptive_override_on_attack"))
    submission = descriptive["engine_submission"]
    assert descriptive["disposition"] == "ELIGIBLE_FOR_VALIDATION"
    assert submission["operation_classes"] == ["ATTACK"]
    assert submission["includes_model_text"] is False
    assert descriptive["model_text_in_submission"] == []
    assert descriptive["unexpected_submission_tokens"] == []
    blob = str(submission)
    assert "HP" not in blob
    assert "natural 20" not in blob
    assert "Execute" not in blob

    beside = evaluate_case(_case("outcome_text_beside_attack"))
    assert beside["canon_statuses"] == ["PLAYER_CLAIM"]
    assert beside["adjudication_statuses"] == ["UNADJUDICATED"]
    assert "Goblin hit points are now 1." not in str(beside["engine_submission"])
    assert "owes me a favor" not in str(beside["engine_submission"])
    assert beside["authoritative_effects"] == []


def test_adversarial_controls_cover_the_required_boundaries() -> None:
    results = {row["case_id"]: evaluate_case(row) for row in adversarial_cases()}
    unsupported = [
        "invented_npc_obligation",
        "requested_npc_cooperation",
        "direct_hp",
        "fabricated_critical",
        "inventory_grant",
        "retroactive_world_change",
        "hidden_information",
        "unsupported_mechanic",
    ]
    for case_id in unsupported:
        assert results[case_id]["disposition"] == "UNSUPPORTED_OPERATION"
        assert results[case_id]["engine_submission"] is None
        assert results[case_id]["executed"] is False
    assert results["ordinary_attack"]["disposition"] == "ELIGIBLE_FOR_VALIDATION"
    assert results["ordinary_attack"]["execution_authorized"] is False
    assert results["ordinary_social_question"]["engine_submission"]["operation_classes"] == ["ASK"]
    assert results["compound_actions"]["component_orders"] == [1, 2]
    assert results["compound_actions"]["engine_submission"]["operation_classes"] == ["MOVE", "INSPECT"]
    assert results["ambiguous_references"]["disposition"] == "NEEDS_CLARIFICATION"
    assert results["rules_question"]["disposition"] == "OUT_OF_CHARACTER"
    assert results["rules_question"]["rolls_dice"] is False
    assert results["committed_action_correction"]["history_disposition"] == "ADJUDICATION_REQUIRED"
    assert results["committed_action_correction"]["history_rewritten"] is False
    assert results["hidden_information"]["reveals_hidden_information"] is False


def test_model_cannot_write_execution_or_canon() -> None:
    rejected = adapt_interpretation(forbidden_payload(), permitted_ids=list(COMBAT))
    assert rejected["structurally_valid"] is False
    assert rejected["eligibility"]["disposition"] == "SAFE_ABSTENTION"
    assert rejected["eligibility"]["execution_authorized"] is False
    smuggled = adapt_interpretation(canon_smuggle_payload(), permitted_ids=list(GATE))
    assert smuggled["structurally_valid"] is False
    assert smuggled["record"] is None
    assert smuggled["executed"] is False


def test_stored_outputs_are_not_pretended_to_match_the_new_schema() -> None:
    rows = replay_translations()
    assert [row["scenario_id"] for row in rows] == [f"DN{index:02d}" for index in range(1, 13)]
    for row in rows:
        assert row["validation_outcome"] == "NOT_REPRESENTABLE"
        assert row["submitted"] is False
        assert row["assumptions"] == []
        assert row["executed"] is False
        translated = row["translated_representation"]
        assert translated["asserted_premises"] == "NOT_REPRESENTABLE"
        assert translated["requested_outcomes"] == "NOT_REPRESENTABLE"
        assert translated["communication_mode"] == "NOT_REPRESENTABLE"


def test_routing_separation_records_remaining_misses() -> None:
    utterances = {row["case_id"]: row["utterance"] for row in contract_cases()}
    utterances["DN11"] = "I ask the captain whether the rain and mud are slowing patrols."
    assessed = {row["scenario_id"]: row for row in routing_assessment(utterances)}
    assert assessed["DN04"]["separable_before_gameplay_routing"] is True
    assert assessed["DN04"]["refined_routed"] is False
    assert assessed["DN12"]["explicit_ooc_prefix"] is False
    assert assessed["DN12"]["refined_routed"] is False
    assert engine_channel_from_utterance(utterances["DN12"]) is None
    assert sum(1 for row in STORED_ROUTING if row["refined_routed"]) == 3


def test_unmarked_correction_is_not_silently_reclassified() -> None:
    payload = next(row["payload"] for row in contract_cases() if row["case_id"] == "DN12")
    mislabeled = {
        **payload,
        "communication_mode": "IN_WORLD_ACTION",
        "interpretation_status": "INTERPRETED",
        "clarification_question": "",
        "correction": {"subject": "NONE", "note": ""},
        "action_components": [
            {
                "order": 1,
                "operation_class": "ASK",
                "description": "ask about patrols",
                "target_ref": "guard_captain",
            }
        ],
        "requested_outcomes": [],
    }
    result = adapt_interpretation(mislabeled, permitted_ids=list(GATE), engine_channel=None)
    assert result["eligibility"]["disposition"] == "ELIGIBLE_FOR_VALIDATION"
    assert result["eligibility"]["execution_authorized"] is False
    assert result["executed"] is False
