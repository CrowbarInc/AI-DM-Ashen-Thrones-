"""PR-BV turn-local realization operation projection. Deterministic. No model calls."""
from __future__ import annotations

import inspect
import json
from pathlib import Path

from game.gm_resolution_decision import (
    DECL_HYPOTHESIS_NOT_REQUIRED,
    DECL_OBSERVATIONS_ONLY,
    DECL_OPTIONAL_BOUNDED_INFERENCE,
    DECL_PROHIBITED,
    DECL_REPLY_NOT_REQUIRED,
    DECL_REQUIRED_FOR_AUTHORIZED,
    OP_BOUNDED_INTERPRETATION,
    OP_CONSEQUENTIAL_REALIZATION,
    OP_DIRECT_OBSERVATION,
    OP_INCIDENTAL_DIALOGUE,
    OP_PLAYER_HYPOTHESIS,
    OP_REFUSAL_OR_LIMIT,
    CEIL_AUTHORIZED_STATE,
    CEIL_CONDITIONAL_HYPOTHESIS,
    CEIL_DIRECT_OBSERVATION,
    CEIL_INTERPRET_NOT_EXPLAIN,
    CEIL_STATE_LIMIT,
    CEIL_TRANSIENT_DIALOGUE,
    audit_narration_against_decision,
    audit_realization_envelope_against_decision,
    build_decision_facing_answer_recipe,
    narration_authority_fields,
    project_turn_local_operation,
)

LIVE = Path("artifacts/pr_bu_pr_bt_final_repaired_chain_micro_live/evidence")
_OPERATION_KEYS = (
    "projection_only",
    "authority_owner",
    "response_operation",
    "declaration_expectation",
    "semantic_ceiling",
    "instruction",
)
_P1_FORBIDDEN = (
    "years of use",
    "recent forceful",
    "neglect",
    "maintenance history",
    "weather",
    "exact mechanism",
    "most likely cause",
)


def _load(probe: str, name: str) -> dict:
    return json.loads((LIVE / probe / name).read_text(encoding="utf-8"))


def _recipe(decision: dict, contract: dict) -> dict:
    recipe = build_decision_facing_answer_recipe(decision, contract)
    assert recipe is not None
    return recipe


def _claim(
    claim_id: str,
    text: str,
    *,
    role: str = "MUST_STATE",
    provenance: str = "authored_world_fact",
    status: str = "established",
    source: str = "scene.visible_facts.0",
    relation: str = "ordinary_predicate",
    modality: str = "",
    premises: list[str] | None = None,
) -> dict:
    return {
        "claim_id": claim_id,
        "text": text,
        "provenance": provenance,
        "authority": "world_truth" if provenance == "authored_world_fact" else "observation",
        "epistemic_status": status,
        "modality": modality,
        "realization_role": role,
        "relation_kind": relation,
        "premise_claim_ids": list(premises or []),
        "source_ref": source,
    }


def _decision(
    contract_id: str,
    claims: list[dict],
    *,
    acts: list[dict] | None = None,
    outcome: str = "established_or_retrieved",
    mutations: list[dict] | None = None,
    obligations: dict | None = None,
) -> dict:
    return {
        "contract_id": contract_id,
        "outcome_classification": outcome,
        "realization_claims": claims,
        "epistemic_acts": list(acts or []),
        "permitted_state_mutations": list(mutations or []),
        "executable_obligations": dict(obligations or {}),
        "unresolved_qualifiers": [],
        "proposed_facts": [],
    }


def _infer_act(subject: str) -> dict:
    return {
        "act": "infer",
        "authority": "observation",
        "semantic_identity": {
            "relation_kind": "epistemic_status",
            "epistemic_status": "inferred",
            "subject": subject,
            "scope": "qualified_possibilities_only",
        },
    }


def _operation(recipe: dict) -> dict:
    turn = recipe["turn_operation"]
    assert set(turn) == set(_OPERATION_KEYS)
    assert "source_authority_fields" not in turn
    return turn


def _same_operation(left: dict, right: dict) -> None:
    assert _operation(left) == _operation(right)


def test_p1_projects_bounded_interpretation_without_authorizing_a_cause() -> None:
    decision = _load("P1", "gm_resolution_decision.json")
    contract = _load("P1", "resolution_contract.json")
    recipe = _recipe(decision, contract)
    projected = project_turn_local_operation(decision, contract)
    turn = _operation(recipe)
    assert turn["projection_only"] is True
    assert turn["authority_owner"] == "gm_resolution_decision"
    assert recipe["projection_only"] is True
    assert recipe["authority_owner"] == "gm_resolution_decision"
    assert turn["response_operation"] == OP_BOUNDED_INTERPRETATION
    assert turn["declaration_expectation"] == DECL_OPTIONAL_BOUNDED_INFERENCE
    assert turn["semantic_ceiling"] == CEIL_INTERPRET_NOT_EXPLAIN
    instruction = turn["instruction"]
    assert "Interpret what the listed observations may indicate" in instruction
    assert "Do not explain an unauthorized cause" in instruction
    assert "Do not declare a new world fact merely to answer" in instruction
    assert "gm_inference" in instruction
    assert "could, may, or might" in recipe["answer_strategy"]
    assert "Do not explain an unauthorized cause" in recipe["answer_strategy"]
    lowered = f"{instruction}\n{recipe['answer_strategy']}".lower()
    for phrase in _P1_FORBIDDEN:
        assert phrase not in lowered
    assert projected is not None
    assert projected["source_authority_fields"] == [
        "gm_resolution_decision.epistemic_acts",
        "gm_resolution_decision.epistemic_acts.semantic_identity.scope",
    ]
    claim_texts = {row["text"] for row in decision["realization_claims"]}
    for row in recipe["required_content"]:
        assert row["text"] in claim_texts


def test_p2_projects_incidental_dialogue_and_does_not_require_a_reply_declaration() -> None:
    decision = _load("P2", "gm_resolution_decision.json")
    contract = _load("P2", "resolution_contract.json")
    recipe = _recipe(decision, contract)
    turn = _operation(recipe)
    assert turn["projection_only"] is True
    assert turn["authority_owner"] == "gm_resolution_decision"
    assert turn["response_operation"] == OP_INCIDENTAL_DIALOGUE
    assert turn["declaration_expectation"] == DECL_REPLY_NOT_REQUIRED
    assert turn["semantic_ceiling"] == CEIL_TRANSIENT_DIALOGUE
    instruction = turn["instruction"]
    assert "On this turn" in instruction
    assert "The reply itself belongs in narration" in instruction
    assert "Do not declare that reply as a world fact" in instruction
    assert "durable preference or history" in instruction
    assert "ordinary dialogue" in recipe["answer_strategy"]
    assert "refusal" in recipe["incidental_improvisation_guidance"]
    guidance = recipe["declaration_guidance"]["consequential_authorized_claim"]
    assert "turn-local reply is narration" in guidance
    assert "not a new authored world fact" in guidance
    blob = json.dumps(recipe)
    assert "realize with source_claim_id and the claim provenance" not in blob
    assert "declare the reply as an authored world fact" not in blob.lower()
    assert "npc dialogue never" not in blob.lower()


def test_p3_projects_conditional_hypothesis_discussion_without_promotion() -> None:
    decision = _load("P3", "gm_resolution_decision.json")
    contract = _load("P3", "resolution_contract.json")
    recipe = _recipe(decision, contract)
    projected = project_turn_local_operation(decision, contract)
    turn = _operation(recipe)
    assert turn["projection_only"] is True
    assert turn["authority_owner"] == "gm_resolution_decision"
    assert turn["response_operation"] == OP_PLAYER_HYPOTHESIS
    assert turn["declaration_expectation"] == DECL_HYPOTHESIS_NOT_REQUIRED
    assert turn["semantic_ceiling"] == CEIL_CONDITIONAL_HYPOTHESIS
    instruction = turn["instruction"]
    assert "conditionally" in instruction
    assert "Do not establish the hypothesis" in instruction
    assert "No declaration is needed merely to discuss it" in instruction
    assert "Realize only claims already listed" in instruction
    assert recipe["permitted_inference"]["allowed"] is False
    assert "Do not establish it" in recipe["answer_strategy"]
    premise = recipe["declaration_guidance"]["epistemic_premise"]
    assert "discussed conditionally" in premise
    assert "not world truth" in premise
    assert "No player hypothesis, NPC claim, or unresolved premise is authorized" not in premise
    assert projected is not None
    assert projected["source_authority_fields"] == ["resolution_contract.raw_input"]
    blob = json.dumps(recipe).lower()
    assert "establish the hypothesis as world truth" not in blob
    assert "most likely cause" not in blob


def test_consequential_control_still_expects_a_declaration_even_with_an_interlocutor() -> None:
    decision = _decision(
        "rc_gate",
        [
            _claim(
                "rc_gate_barred",
                "The gate is barred.",
                source="resolution.state_changes.gate",
            )
        ],
        outcome="state_mutation",
        mutations=[{"type": "state_change", "key": "gate", "value": "barred"}],
    )
    contract = {
        "operation": "act",
        "interlocutor_id": "warden",
        "raw_input": "Bar the gate.",
        "dimensions": [],
    }
    recipe = _recipe(decision, contract)
    turn = _operation(recipe)
    assert turn["response_operation"] == OP_CONSEQUENTIAL_REALIZATION
    assert turn["declaration_expectation"] == DECL_REQUIRED_FOR_AUTHORIZED
    assert turn["semantic_ceiling"] == CEIL_AUTHORIZED_STATE
    assert "Declare those authorized claims" in turn["instruction"]
    assert turn["declaration_expectation"] != DECL_REPLY_NOT_REQUIRED
    assert "source_claim_id" in recipe["answer_strategy"]
    assert "realize the authorized consequential claims" in recipe["declaration_guidance"]["consequential_authorized_claim"]
    without_speaker = _recipe(
        decision,
        {"operation": "act", "raw_input": "Bar the gate.", "dimensions": []},
    )
    _same_operation(recipe, without_speaker)


def test_generalization_controls_follow_decision_shape_not_scenario_nouns() -> None:
    observation = _claim("rc_obs", "A mark is visible on the timber.")
    p1 = _recipe(_load("P1", "gm_resolution_decision.json"), _load("P1", "resolution_contract.json"))
    p2 = _recipe(_load("P2", "gm_resolution_decision.json"), _load("P2", "resolution_contract.json"))
    p3 = _recipe(_load("P3", "gm_resolution_decision.json"), _load("P3", "resolution_contract.json"))

    g1 = _recipe(
        _decision("rc_g1", [observation], outcome="epistemically_qualified"),
        {"operation": "ask", "interlocutor_id": "miller", "raw_input": "What did you eat this morning?", "dimensions": []},
    )
    g1_other = _recipe(
        _decision(
            "rc_g1b",
            [_claim("rc_other", "A clerk stands at the counter.", source="scene.visible_facts.1")],
            outcome="epistemically_qualified",
        ),
        {"operation": "ask", "interlocutor_id": "clerk", "raw_input": "How was the morning?", "dimensions": []},
    )
    _same_operation(g1, g1_other)
    _same_operation(g1, p2)
    assert _operation(g1)["response_operation"] == OP_INCIDENTAL_DIALOGUE
    assert _operation(g1)["declaration_expectation"] == DECL_REPLY_NOT_REQUIRED

    g2 = _recipe(
        _decision("rc_g2", [observation], acts=[_infer_act("timber")]),
        {
            "operation": "inspect",
            "dimensions": ["interpretation"],
            "dimension": "interpretation",
            "raw_input": "What might these marks indicate?",
        },
    )
    g2_reordered = _recipe(
        _decision(
            "rc_g2b",
            [
                _claim("rc_b", "The hinge sits loose.", source="scene.visible_facts.1"),
                _claim("rc_a", "The latch is scratched.", source="scene.visible_facts.0"),
            ],
            acts=[_infer_act("latch")],
        ),
        {
            "operation": "inspect",
            "dimensions": ["interpretation"],
            "raw_input": "What might these marks indicate?",
        },
    )
    _same_operation(g2, g2_reordered)
    _same_operation(g2, p1)
    assert _operation(g2)["semantic_ceiling"] == CEIL_INTERPRET_NOT_EXPLAIN

    g3 = _recipe(
        _decision("rc_g3", [observation]),
        {"operation": "perceive", "dimensions": [], "raw_input": "Perhaps the latch failed. Does that match this?"},
    )
    g3_claim = _recipe(
        _decision(
            "rc_g3b",
            [
                observation,
                _claim(
                    "rc_hyp",
                    "The latch failed.",
                    role="MAY_INFER",
                    provenance="player_hypothesis",
                    status="hypothesis",
                    modality="hypothetical",
                    relation="epistemic_status",
                    premises=["rc_obs"],
                ),
            ],
        ),
        {"operation": "perceive", "dimensions": [], "raw_input": "Does the supplied possibility fit?"},
    )
    _same_operation(g3, p3)
    _same_operation(g3, g3_claim)
    assert _operation(g3)["response_operation"] == OP_PLAYER_HYPOTHESIS
    assert g3_claim["permitted_inference"]["may_infer_claims"][0]["epistemic_status"] == "hypothesis"
    assert "existing status" in g3_claim["answer_strategy"]
    assert "world truth" in g3_claim["declaration_guidance"]["epistemic_premise"]

    g5 = _recipe(
        _decision("rc_g5", [observation]),
        {"operation": "perceive", "dimensions": ["appearance"], "raw_input": "What is directly in front of me?"},
    )
    g5_other = _recipe(
        _decision("rc_g5b", [_claim("rc_seen", "The table holds a closed book.")]),
        {"operation": "inspect", "dimensions": [], "raw_input": "What can I see here?"},
    )
    _same_operation(g5, g5_other)
    assert _operation(g5)["response_operation"] == OP_DIRECT_OBSERVATION
    assert _operation(g5)["declaration_expectation"] == DECL_OBSERVATIONS_ONLY
    assert _operation(g5)["semantic_ceiling"] == CEIL_DIRECT_OBSERVATION
    assert "Do not add an inference" in _operation(g5)["instruction"]


def test_refusal_outcome_prohibits_a_declaration() -> None:
    recipe = _recipe(
        _decision("rc_limit", [], outcome="consequentially_unresolved"),
        {"operation": "act", "raw_input": "I force the door open.", "dimensions": []},
    )
    turn = _operation(recipe)
    assert turn["response_operation"] == OP_REFUSAL_OR_LIMIT
    assert turn["declaration_expectation"] == DECL_PROHIBITED
    assert turn["semantic_ceiling"] == CEIL_STATE_LIMIT
    assert "not authorized" in turn["instruction"]


def test_projection_does_not_exceed_or_suppress_authorized_realization() -> None:
    p1 = _recipe(_load("P1", "gm_resolution_decision.json"), _load("P1", "resolution_contract.json"))
    assert p1["permitted_inference"]["allowed"] is True
    assert p1["permitted_inference"]["qualified_observations"][0]["scope"] == "qualified_possibilities_only"
    assert "propose only" in p1["declaration_guidance"]["bounded_inference"]

    consequential = _recipe(
        _decision(
            "rc_move",
            [_claim("rc_loc", "Location changes to the yard.", source="resolution.permitted_state_mutations.location")],
            outcome="state_mutation",
            mutations=[{"type": "location", "target_scene_id": "yard"}],
        ),
        {"operation": "act", "raw_input": "I go into the yard.", "dimensions": []},
    )
    assert _operation(consequential)["declaration_expectation"] == DECL_REQUIRED_FOR_AUTHORIZED
    assert "Do not declare" not in _operation(consequential)["instruction"]
    assert "Declare those authorized claims" in _operation(consequential)["instruction"]


def test_model_facing_recipe_has_no_internal_operation_contradiction() -> None:
    cases = {
        "P1": _recipe(_load("P1", "gm_resolution_decision.json"), _load("P1", "resolution_contract.json")),
        "P2": _recipe(_load("P2", "gm_resolution_decision.json"), _load("P2", "resolution_contract.json")),
        "P3": _recipe(_load("P3", "gm_resolution_decision.json"), _load("P3", "resolution_contract.json")),
    }
    for recipe in cases.values():
        blob = json.dumps(recipe).lower()
        assert "provide the most likely cause" not in blob
        assert "declare this as established world fact" not in blob
    p1 = json.dumps(cases["P1"])
    assert "Do not explain an unauthorized cause" in p1
    assert "years of use" not in p1.lower()
    p2 = json.dumps(cases["P2"])
    assert "Do not declare that reply as a world fact" in p2
    assert "realize with source_claim_id and the claim provenance" not in p2
    p3 = json.dumps(cases["P3"])
    assert "Do not establish the hypothesis" in p3
    assert "discussed conditionally" in p3


def test_validator_does_not_consume_the_projection() -> None:
    for fn in (audit_realization_envelope_against_decision, audit_narration_against_decision):
        source = inspect.getsource(fn)
        assert "turn_operation" not in source
        assert "project_turn_local_operation" not in source
        assert "decision_facing_answer_recipe" not in source
    signature = inspect.signature(audit_realization_envelope_against_decision)
    assert "decision_facing_answer_recipe" not in signature.parameters
    assert "turn_operation" not in signature.parameters


def test_provider_authority_fields_include_the_projection() -> None:
    saved_decision = _load("P1", "gm_resolution_decision.json")
    saved_contract = _load("P1", "resolution_contract.json")
    resolution = {
        "kind": saved_contract.get("operation"),
        "metadata": {
            "resolution_contract": saved_contract,
            "gm_resolution_decision": saved_decision,
        },
    }
    fields = narration_authority_fields(resolution)
    recipe = fields["decision_facing_answer_recipe"]
    assert recipe["turn_operation"]["response_operation"] == OP_BOUNDED_INTERPRETATION
    assert recipe["turn_operation"]["projection_only"] is True
