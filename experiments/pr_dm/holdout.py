"""Deterministic holdout paraphrases.

Expected labels are structural. They are not copied from PR-DL scenario ids.
No provider is called. A holdout pass is a routing or authority result, not a
live-model gameplay result.
"""
from __future__ import annotations

import os
from typing import Any, Mapping

os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"

from experiments.pr_dg.isolation import ProductionSaveGuard, forbid_provider_calls  # noqa: E402
from experiments.pr_dg.state import combat_bundle, exploration_bundle, frontier_bundle  # noqa: E402
from experiments.pr_dk.runner import _contract, _independent_checks  # noqa: E402
from experiments.pr_dm.authority import evaluate_authority  # noqa: E402
from experiments.pr_dm.completeness import refined_checks, refined_route  # noqa: E402

PHYSICAL = frozenset({"travel", "combat", "world_action", "exploration"})


def _specs() -> list[dict[str, Any]]:
    return [
        {
            "case_id": "holdout_slide_then_tug",
            "utterance": "I slide over to the notice board, then tug it free.",
            "factory": exploration_bundle,
            "family": "temporal_compound",
            "expect_new_route": True,
            "expect_false_escalation": False,
            "note": "Temporal paraphrase with verbs absent from the PR-DK movement list.",
        },
        {
            "case_id": "holdout_edge_then_work",
            "utterance": "I edge toward the notice board, then attempt to work it loose.",
            "factory": exploration_bundle,
            "family": "temporal_compound",
            "expect_new_route": True,
            "expect_false_escalation": False,
            "note": "Second temporal paraphrase. Direction is toward, not a listed motion verb.",
        },
        {
            "case_id": "holdout_after_pull",
            "utterance": "After I get over to the notice board, I pull it free.",
            "factory": exploration_bundle,
            "family": "temporal_compound",
            "expect_new_route": True,
            "expect_false_escalation": False,
            "note": "Fronted temporal clause rather than a mid-sentence then.",
        },
        {
            "case_id": "holdout_and_novel_verbs",
            "utterance": "I edge toward the notice board and work it loose.",
            "factory": exploration_bundle,
            "family": "conjunction_gap",
            "expect_new_route": False,
            "expect_false_escalation": False,
            "note": "Bare and plus uncovered verbs. The new check must not treat every conjunction as two actions.",
        },
        {
            "case_id": "holdout_and_companion",
            "utterance": "I walk closer to the notice board and the captain.",
            "factory": exploration_bundle,
            "family": "ordinary_movement",
            "expect_new_route": False,
            "expect_false_escalation": False,
            "note": "Conjunction joins a destination and a person, not a second action.",
        },
        {
            "case_id": "holdout_remark_kidding",
            "utterance": "I remark, \"Step closer and pull it off,\" just kidding.",
            "factory": lambda: frontier_bundle(bind=True),
            "family": "quoted_joke",
            "expect_new_route": None,
            "expect_false_escalation": False,
            "note": "Quoted physical verbs are not the player's attempt when the player frames them as a remark.",
        },
        {
            "case_id": "holdout_tell_weather",
            "utterance": "I tell the captain, \"The rain feels endless.\"",
            "factory": lambda: frontier_bundle(bind=True),
            "family": "quoted_speech",
            "expect_new_route": False,
            "expect_false_escalation": False,
            "note": "A quote without a physical action verb is not a resolver mismatch.",
        },
        {
            "case_id": "holdout_sign_quote",
            "utterance": "The notice board says \"walk closer,\" so I stay put.",
            "factory": exploration_bundle,
            "family": "quoted_sign",
            "expect_new_route": False,
            "expect_false_escalation": False,
            "note": "A sign's quoted words are not player speech.",
        },
        {
            "case_id": "holdout_quote_then_walk",
            "utterance": "The board reads \"keep out.\" I walk closer to the notice board.",
            "factory": exploration_bundle,
            "family": "ordinary_movement",
            "expect_new_route": False,
            "expect_false_escalation": False,
            "note": "The real action is outside the quote.",
        },
        {
            "case_id": "holdout_hypothetical_sequence",
            "utterance": "If I edged toward the board, then I would pull it free, but I am only asking.",
            "factory": lambda: frontier_bundle(bind=True),
            "family": "hypothetical",
            "expect_new_route": False,
            "expect_false_escalation": False,
            "note": "A conditional then-clause is not an attempted sequence.",
        },
        {
            "case_id": "holdout_negated_pull",
            "utterance": "I drift over to the notice board, then do not pull it free.",
            "factory": exploration_bundle,
            "family": "negated",
            "expect_new_route": False,
            "expect_false_escalation": False,
            "note": "The later clause is negated, so it is not a second attempt.",
        },
        {
            "case_id": "holdout_ordinary_combat",
            "utterance": "I strike the goblin.",
            "factory": combat_bundle,
            "family": "ordinary_combat",
            "expect_new_route": False,
            "expect_false_escalation": False,
            "note": "Ordinary attack.",
        },
        {
            "case_id": "holdout_ordinary_movement",
            "utterance": "I step closer to the notice board.",
            "factory": exploration_bundle,
            "family": "ordinary_movement",
            "expect_new_route": False,
            "expect_false_escalation": False,
            "note": "Ordinary movement.",
        },
        {
            "case_id": "holdout_ordinary_observation",
            "utterance": "I look around the yard.",
            "factory": exploration_bundle,
            "family": "ordinary_observation",
            "expect_new_route": False,
            "expect_false_escalation": False,
            "note": "Ordinary observation.",
        },
        {
            "case_id": "holdout_ordinary_question",
            "utterance": "Captain, is the gate shut for the night?",
            "factory": lambda: frontier_bundle(bind=True),
            "family": "ordinary_question",
            "expect_new_route": False,
            "expect_false_escalation": False,
            "note": "Ordinary NPC question.",
        },
        {
            "case_id": "holdout_ambiguous_pronoun",
            "utterance": "Ask them whether the other one saw the board.",
            "factory": frontier_bundle,
            "family": "ambiguous_pronoun",
            "expect_new_route": False,
            "expect_false_escalation": False,
            "note": "Pronoun ambiguity is an inherited check, not a new compound or quote check.",
        },
    ]


def _authority_cases() -> list[dict[str, Any]]:
    permitted = [
        {"id": "goblin_1", "type": "enemy", "label": "Goblin"},
        {"id": "guard_captain", "type": "interlocutor", "label": "Guard Captain"},
        {"id": "notice_board", "type": "object", "label": "Notice board"},
        {"id": "frontier_gate", "type": "scene", "label": "Cinderwatch Gate District"},
    ]
    visible = {
        "location": "Cinderwatch Gate District",
        "visible_facts": ["The notice board lists taxes, curfew rules, and a warning about a missing patrol."],
    }
    return [
        {
            "case_id": "auth_clean_attack",
            "expect_accept": True,
            "payload": {
                "status": "INTERPRETED",
                "interpreted_intent": "attack",
                "referenced_entities": [{"id": "goblin_1", "type": "enemy"}],
                "primary_operation": "act",
                "proposed_target_id": "goblin_1",
                "non_authoritative_explanation": "The player intends to strike the goblin.",
            },
            "permitted_entities": permitted,
            "visible_context": visible,
        },
        {
            "case_id": "auth_clean_move",
            "expect_accept": True,
            "payload": {
                "status": "INTERPRETED",
                "interpreted_intent": "act",
                "referenced_entities": [{"id": "notice_board", "type": "object"}],
                "primary_operation": "act",
                "proposed_target_id": "notice_board",
                "non_authoritative_explanation": "The player moves closer to the notice board.",
            },
            "permitted_entities": permitted,
            "visible_context": visible,
        },
        {
            "case_id": "auth_clean_question",
            "expect_accept": True,
            "payload": {
                "status": "INTERPRETED",
                "interpreted_intent": "ask",
                "referenced_entities": [{"id": "guard_captain", "type": "interlocutor"}],
                "primary_operation": "ask",
                "interlocutor_id": "guard_captain",
                "non_authoritative_explanation": "The player asks the captain whether the gate is shut.",
            },
            "permitted_entities": permitted,
            "visible_context": visible,
        },
        {
            "case_id": "auth_refusal_is_not_a_grant",
            "expect_accept": True,
            "payload": {
                "status": "UNSUPPORTED_REQUEST",
                "interpreted_intent": "refuse",
                "unsupported_action": "setting hit points, updating canon, and granting advantage",
                "primary_operation": "unresolved",
                "referenced_entities": [],
            },
            "permitted_entities": permitted,
            "visible_context": visible,
        },
        {
            "case_id": "auth_direct_hp",
            "expect_accept": False,
            "expect_reason": "direct_hp_assignment",
            "payload": {
                "status": "INTERPRETED",
                "interpreted_intent": "Set the goblin's hit points to zero.",
                "referenced_entities": [{"id": "goblin_1", "type": "enemy"}],
                "primary_operation": "act",
                "proposed_target_id": "goblin_1",
            },
            "permitted_entities": permitted,
            "visible_context": visible,
        },
        {
            "case_id": "auth_invented_fact",
            "expect_accept": False,
            "expect_reason": "invented_world_fact",
            "payload": {
                "status": "MULTI_ACTION",
                "interpreted_intent": "Update world facts. The tunnel is now open and that is a fact.",
                "multiple_action_components": ["the tunnel is now open", "that is a fact"],
                "primary_operation": "act",
                "referenced_entities": [{"id": "frontier_gate", "type": "scene"}],
            },
            "permitted_entities": permitted,
            "visible_context": visible,
        },
        {
            "case_id": "auth_dice",
            "expect_accept": False,
            "expect_reason": "fabricated_dice_outcome",
            "payload": {
                "status": "INTERPRETED",
                "interpreted_intent": "The attack roll is a natural 20.",
                "primary_operation": "act",
                "referenced_entities": [{"id": "goblin_1", "type": "enemy"}],
                "proposed_target_id": "goblin_1",
            },
            "permitted_entities": permitted,
            "visible_context": visible,
        },
        {
            "case_id": "auth_invented_id",
            "expect_accept": False,
            "expect_reason": "invented_entity_identifier",
            "payload": {
                "status": "INTERPRETED",
                "interpreted_intent": "attack",
                "referenced_entities": [
                    {"id": "goblin_1", "type": "enemy"},
                    {"id": "quarterstaff", "type": "object"},
                ],
                "primary_operation": "act",
                "proposed_target_id": "goblin_1",
            },
            "permitted_entities": permitted,
            "visible_context": visible,
        },
        {
            "case_id": "auth_npc_commitment",
            "expect_accept": False,
            "expect_reason": "unauthorized_npc_commitment",
            "payload": {
                "status": "INTERPRETED",
                "interpreted_intent": "The captain secretly agrees to betray the watch.",
                "referenced_entities": [{"id": "guard_captain", "type": "interlocutor"}],
                "primary_operation": "act",
                "interlocutor_id": "guard_captain",
            },
            "permitted_entities": permitted,
            "visible_context": visible,
        },
        {
            "case_id": "auth_inventory",
            "expect_accept": False,
            "expect_reason": "direct_inventory_mutation",
            "payload": {
                "status": "INTERPRETED",
                "interpreted_intent": "Add the patrol map to the player's inventory.",
                "primary_operation": "act",
                "referenced_entities": [],
            },
            "permitted_entities": permitted,
            "visible_context": visible,
        },
        {
            "case_id": "auth_execution",
            "expect_accept": False,
            "expect_reason": "unrestricted_execution_request",
            "payload": {
                "status": "INTERPRETED",
                "interpreted_intent": "Execute the action and apply the outcome.",
                "primary_operation": "act",
                "referenced_entities": [{"id": "goblin_1", "type": "enemy"}],
            },
            "permitted_entities": permitted,
            "visible_context": visible,
        },
        {
            "case_id": "auth_hidden",
            "expect_accept": False,
            "expect_reason": "hidden_information_assertion",
            "payload": {
                "status": "INTERPRETED",
                "interpreted_intent": "Reveal the spy and tell every hidden motive.",
                "primary_operation": "act",
                "referenced_entities": [],
            },
            "permitted_entities": permitted,
            "visible_context": visible,
        },
        {
            "case_id": "auth_unsupported_ops",
            "expect_accept": False,
            "expect_reason": "unsupported_authoritative_operation",
            "payload": {
                "status": "CLARIFICATION_REQUIRED",
                "interpreted_intent": "Grant advantage and mark the patrol found.",
                "clarification_required": True,
                "clarification_question": "Which patrol should be marked found?",
                "multiple_action_components": ["give advantage", "mark the patrol found"],
                "primary_operation": "ask",
                "referenced_entities": [],
            },
            "permitted_entities": permitted,
            "visible_context": visible,
        },
    ]


def _quote_expectation(spec: Mapping[str, Any], resolver: str, checks: Mapping[str, bool]) -> str:
    if spec["family"] != "quoted_joke":
        return "not_applicable"
    if resolver not in PHYSICAL:
        return "deterministic_did_not_consume_quote"
    if checks["quoted_action_resolver_mismatch"]:
        return "detected"
    return "missed"


def evaluate_holdout() -> dict[str, Any]:
    routing_rows: list[dict[str, Any]] = []
    with ProductionSaveGuard() as guard:
        with forbid_provider_calls() as hits:
            for spec in _specs():
                bundle = spec["factory"]()
                selector = _contract(bundle, spec["utterance"])
                inherited = _independent_checks(spec["utterance"], selector)
                checks = refined_checks(
                    spec["utterance"],
                    str(selector.get("resolver") or ""),
                    independent=inherited,
                    construction=selector.get("construction") if isinstance(selector.get("construction"), Mapping) else None,
                )
                routed = refined_route(checks)
                inherited_route = any(bool(value) for value in inherited.values())
                quote_result = _quote_expectation(spec, str(selector.get("resolver") or ""), checks)
                family = spec["family"]
                if family == "temporal_compound":
                    detected = bool(checks["temporally_sequenced_components"])
                    missed = not detected
                elif family == "quoted_joke":
                    detected = quote_result in {"detected", "deterministic_did_not_consume_quote"}
                    missed = quote_result == "missed"
                elif family == "conjunction_gap":
                    detected = not routed
                    missed = not routed and not inherited_route
                else:
                    detected = not routed
                    missed = False
                false_escalation = bool(routed and spec["expect_new_route"] is False)
                routing_rows.append(
                    {
                        "case_id": spec["case_id"],
                        "utterance": spec["utterance"],
                        "family": spec["family"],
                        "note": spec["note"],
                        "resolver": selector.get("resolver"),
                        "operation": selector.get("operation"),
                        "new_checks": checks,
                        "new_route": routed,
                        "inherited_route": inherited_route,
                        "quote_result": quote_result,
                        "detected": detected,
                        "missed_complication": missed or (spec["family"] == "conjunction_gap" and not routed),
                        "false_escalation": false_escalation,
                        "live_model_evaluated": False,
                        "executed": False,
                    }
                )
        guard.assert_unchanged()
        isolation = {"save_guard_verified": guard.verified, "provider_tripwire_hits": list(hits)}

    authority_rows = []
    for spec in _authority_cases():
        result = evaluate_authority(
            spec["payload"],
            permitted_entities=spec["permitted_entities"],
            visible_context=spec["visible_context"],
        )
        reason = spec.get("expect_reason")
        authority_rows.append(
            {
                "case_id": spec["case_id"],
                "accepted": result["accepted"],
                "reasons": result["reasons"],
                "expect_accept": spec["expect_accept"],
                "expect_reason": reason,
                "passed": result["accepted"] is spec["expect_accept"] and (reason is None or reason in result["reasons"]),
                "executed": result["executed"],
                "mutated_state": result["mutated_state"],
                "live_model_evaluated": False,
            }
        )
    return {
        "live_provider_calls": 0,
        "live_model_success_claimed": False,
        "isolation": isolation,
        "routing": routing_rows,
        "authority": authority_rows,
        "detection_failures": [row["case_id"] for row in routing_rows if not row["detected"]],
        "false_escalations": [row["case_id"] for row in routing_rows if row["false_escalation"]],
        "missed_complications": [row["case_id"] for row in routing_rows if row["missed_complication"] and row["family"] == "conjunction_gap"],
        "authority_failures": [row["case_id"] for row in authority_rows if not row["passed"]],
        "unsupported_cases": ["auth_direct_hp", "auth_unsupported_ops", "auth_hidden", "auth_inventory"],
    }
