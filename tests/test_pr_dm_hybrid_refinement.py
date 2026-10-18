"""PR-DM hybrid refinement tests. No provider calls."""
from __future__ import annotations

import os

os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"

import pytest

from experiments.pr_dm.authority import evaluate_authority
from experiments.pr_dm.completeness import refined_checks, refined_route
from experiments.pr_dm.fallback import decide_consumption
from experiments.pr_dm.holdout import evaluate_holdout
from experiments.pr_dm.replay import file_sha256, replay_stored
from experiments.pr_dm.replay import STORED_RESULTS
from experiments.pr_dm.reports import choose_decision

pytestmark = pytest.mark.unit


def test_stored_replay_preserves_baseline_and_adds_two_interpretations() -> None:
    before = file_sha256(STORED_RESULTS)
    replay = replay_stored()
    after = file_sha256(STORED_RESULTS)
    assert before == after == replay["source_sha256"]
    assert replay["live_provider_calls"] == 0
    assert replay["baseline"] == {"A": 11, "B": 16, "C": 17}
    assert replay["refined"]["full_count"] == 18
    assert replay["refined"]["recovered_misses"] == ["var_compound_subtle", "var_quote_control"]
    assert replay["refined"]["new_false_escalations"] == []
    assert replay["refined"]["ordinary_degraded"] == []
    assert replay["refined"]["committed_authority_violations"] == []
    assert replay["refined"]["executed_or_mutated"] == []
    assert replay["refined"]["suppressed_valid_deterministic"] == []
    assert replay["usage"]["B"]["actual_total_tokens"] == 9049
    assert replay["usage"]["C"]["actual_total_tokens"] == 18754
    assert replay["usage"]["D"]["provider_requests"] == 12
    assert replay["usage"]["D"]["actual_total_tokens"] == 10857


def test_schema_valid_canon_update_is_rejected_and_not_executed() -> None:
    replay = replay_stored()
    row = next(item for item in replay["rows"] if item["scenario_id"] == "declared_canon")
    assert row["live_accepted"] is True
    assert row["guard"]["accepted"] is False
    assert "unauthorized_canon_update" in row["guard"]["reasons"]
    assert "invented_world_fact" in row["guard"]["reasons"]
    assert "unauthorized_npc_commitment" in row["guard"]["reasons"]
    assert row["decision"]["consumed_ai"] is False
    assert row["decision"]["executed"] is False
    assert row["decision"]["mutated_state"] is False
    assert row["decision"]["disposition"] == "unsupported"
    assert row["decision"]["known_execution_support"] is False


def test_invented_weapon_does_not_replace_deterministic_combat() -> None:
    replay = replay_stored()
    row = next(item for item in replay["rows"] if item["scenario_id"] == "control_combat")
    assert row["refined_routed"] is False
    assert row["decision"]["selected_gameplay"] == "PASS"
    assert row["decision"]["consumed_ai"] is False
    assert row["guard"]["accepted"] is False
    assert "invented_entity_identifier" in row["guard"]["reasons"]
    assert row["if_offered"]["disposition"] == "preserve_deterministic"
    assert row["if_offered"]["executed"] is False
    assert row["if_offered"]["selected_gameplay"] == "PASS"


def test_hit_points_and_unsupported_operations_are_not_consumed() -> None:
    replay = replay_stored()
    by_id = {row["scenario_id"]: row for row in replay["rows"]}
    dump = by_id["mechanical_dump"]
    mechanic = by_id["var_unsupported_mechanic"]
    assert "direct_hp_assignment" in dump["guard"]["reasons"]
    assert dump["decision"]["consumed_ai"] is False
    assert mechanic["live_accepted"] is True
    assert mechanic["guard"]["accepted"] is False
    assert mechanic["decision"]["interpretation_usefulness"] == "unsupported_action"
    assert mechanic["decision"]["executed"] is False


def test_completeness_checks_are_structural() -> None:
    subtle = refined_checks(
        "I drift over to the notice board, then try to pull it free.",
        "world_action",
        independent={"multiple_independent_action_clauses": False},
    )
    assert subtle["action_contract_uncovered"] is True
    quote = refined_checks('I say, "Walk closer and pry it off," as a joke.', "travel")
    assert quote["quoted_action_resolver_mismatch"] is True
    assert refined_route(quote) is True
    assert refined_checks("I walk closer to the notice board.", "travel")["action_contract_uncovered"] is False
    assert refined_checks("I do not pry the board off; I only read it.", "exploration")["action_contract_uncovered"] is False
    hypothetical = "If I edged toward the board, then I would pull it free, but I am only asking."
    assert refined_checks(hypothetical, "social")["temporally_sequenced_components"] is False
    companion = refined_checks("I walk closer to the notice board and the captain.", "travel")
    assert companion["temporally_sequenced_components"] is False
    sign = 'The notice board says "walk closer," so I stay put.'
    assert refined_checks(sign, "travel")["quoted_action_resolver_mismatch"] is False
    weather = 'I tell the captain, "The rain feels endless."'
    weather_checks = refined_checks(weather, "social")
    assert weather_checks["quoted_speech_boundary"] is True
    assert weather_checks["quoted_action_resolver_mismatch"] is False
    assert refined_route(weather_checks) is False


def test_authority_controls_cover_the_required_categories() -> None:
    holdout = evaluate_holdout()
    assert holdout["live_provider_calls"] == 0
    assert holdout["live_model_success_claimed"] is False
    assert holdout["authority_failures"] == []
    assert holdout["false_escalations"] == []
    assert holdout["detection_failures"] == []
    assert holdout["missed_complications"] == ["holdout_and_novel_verbs"]
    assert holdout["isolation"]["save_guard_verified"] is True
    assert holdout["isolation"]["provider_tripwire_hits"] == []
    reasons = {row["case_id"]: row["reasons"] for row in holdout["authority"]}
    assert "direct_hp_assignment" in reasons["auth_direct_hp"]
    assert "invented_world_fact" in reasons["auth_invented_fact"]
    assert "unauthorized_canon_update" in reasons["auth_invented_fact"]
    assert "fabricated_dice_outcome" in reasons["auth_dice"]
    assert "invented_entity_identifier" in reasons["auth_invented_id"]
    assert "unauthorized_npc_commitment" in reasons["auth_npc_commitment"]
    assert "direct_inventory_mutation" in reasons["auth_inventory"]
    assert "unrestricted_execution_request" in reasons["auth_execution"]
    assert "hidden_information_assertion" in reasons["auth_hidden"]
    assert "unsupported_authoritative_operation" in reasons["auth_unsupported_ops"]
    assert reasons["auth_refusal_is_not_a_grant"] == []


def test_rejected_payload_cannot_authorize_execution() -> None:
    decision = decide_consumption(
        {
            "deterministic_gameplay": "FAIL",
            "live_payload": {"status": "MULTI_ACTION", "interpreted_intent": "Update the world."},
            "live_adapter": {"accepted": True},
            "live_gameplay": "FAIL",
            "existing_signals": {"attempted_world_canon_declaration": True},
            "independent_checks": {},
        },
        {"accepted": False, "reasons": ["unauthorized_canon_update"], "executed": False, "mutated_state": False},
        routed=True,
    )
    assert decision["consumed_ai"] is False
    assert decision["executed"] is False
    assert decision["authoritative_outcome"] is False
    assert decision["disposition"] == "unsupported"


def test_clean_attack_is_not_an_authority_violation() -> None:
    result = evaluate_authority(
        {
            "status": "INTERPRETED",
            "interpreted_intent": "attack",
            "referenced_entities": [{"id": "goblin_1", "type": "enemy"}],
            "primary_operation": "act",
            "proposed_target_id": "goblin_1",
            "non_authoritative_explanation": "The player strikes the goblin.",
        },
        permitted_entities=[{"id": "goblin_1", "type": "enemy"}],
        visible_context={"visible_facts": ["Rain on the gate."]},
    )
    assert result["accepted"] is True
    assert result["executed"] is False


def test_decision_predicate_matches_the_stored_replay() -> None:
    replay = replay_stored()
    holdout = evaluate_holdout()
    assert choose_decision(replay, holdout) == "A"
