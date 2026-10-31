"""Write the PR-BV matrix from the same helpers the tests use. No model calls."""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
spec = importlib.util.spec_from_file_location(
    "pr_bv_tests",
    ROOT / "tests" / "test_pr_bv_turn_local_operation_projection.py",
)
assert spec and spec.loader
tests = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tests)

from game.gm_resolution_decision import project_turn_local_operation

PROVIDER = {
    "P1": {"before": 97812, "after": 98442},
    "P2": {"before": 110405, "after": 111060},
    "P3": {"before": 99752, "after": 100389},
}


def _row(fixture_id: str, decision_shape: str, decision: dict, contract: dict, expected: dict, notes: str) -> dict:
    recipe = tests._recipe(decision, contract)
    turn = tests._operation(recipe)
    projected = project_turn_local_operation(decision, contract)
    assert projected is not None
    provider = PROVIDER.get(fixture_id)
    before = provider["before"] if provider else None
    after = provider["after"] if provider else None
    actual = {
        "response_operation": turn["response_operation"],
        "declaration_expectation": turn["declaration_expectation"],
        "semantic_ceiling": turn["semantic_ceiling"],
    }
    return {
        "fixture_id": fixture_id,
        "decision_shape": decision_shape,
        "response_operation": actual["response_operation"],
        "declaration_expectation": actual["declaration_expectation"],
        "semantic_ceiling": actual["semantic_ceiling"],
        "projection_only": turn["projection_only"],
        "authority_owner": turn["authority_owner"],
        "source_authority_fields": projected["source_authority_fields"],
        "expected_operation": expected["response_operation"],
        "expected_declaration_expectation": expected["declaration_expectation"],
        "expected_ceiling": expected["semantic_ceiling"],
        "matches_expected": actual == expected and turn["projection_only"] is True and turn["authority_owner"] == "gm_resolution_decision",
        "provider_chars_before": before,
        "provider_chars_after": after,
        "net_char_change": None if before is None else after - before,
        "instruction": turn["instruction"],
        "notes": notes,
    }


def main() -> None:
    observation = tests._claim("rc_obs", "A mark is visible on the timber.")
    p1_decision = tests._load("P1", "gm_resolution_decision.json")
    p1_contract = tests._load("P1", "resolution_contract.json")
    p2_decision = tests._load("P2", "gm_resolution_decision.json")
    p2_contract = tests._load("P2", "resolution_contract.json")
    p3_decision = tests._load("P3", "gm_resolution_decision.json")
    p3_contract = tests._load("P3", "resolution_contract.json")
    g4_decision = tests._decision(
        "rc_gate",
        [tests._claim("rc_gate_barred", "The gate is barred.", source="resolution.state_changes.gate")],
        outcome="state_mutation",
        mutations=[{"type": "state_change", "key": "gate", "value": "barred"}],
    )
    g4_contract = {"operation": "act", "interlocutor_id": "warden", "raw_input": "Bar the gate.", "dimensions": []}
    g1_decision = tests._decision("rc_g1", [observation], outcome="epistemically_qualified")
    g1_contract = {"operation": "ask", "interlocutor_id": "miller", "raw_input": "What did you eat this morning?", "dimensions": []}
    g2_decision = tests._decision("rc_g2", [observation], acts=[tests._infer_act("timber")])
    g2_contract = {
        "operation": "inspect",
        "dimensions": ["interpretation"],
        "dimension": "interpretation",
        "raw_input": "What might these marks indicate?",
    }
    g3_decision = tests._decision("rc_g3", [observation])
    g3_contract = {"operation": "perceive", "dimensions": [], "raw_input": "Perhaps the latch failed. Does that match this?"}
    g5_decision = tests._decision("rc_g5", [observation])
    g5_contract = {"operation": "perceive", "dimensions": ["appearance"], "raw_input": "What is directly in front of me?"}
    rows = [
        _row(
            "P1",
            "qualified_possibilities_infer",
            p1_decision,
            p1_contract,
            {
                "response_operation": "bounded_interpretation",
                "declaration_expectation": "optional_bounded_inference",
                "semantic_ceiling": "interpret_observations_not_unauthorized_cause",
            },
            "Live repaired-chain decision. Interpretation is not an explanation. Request-classification truncation is unchanged.",
        ),
        _row(
            "P2",
            "interlocutor_without_inference_or_mutation",
            p2_decision,
            p2_contract,
            {
                "response_operation": "incidental_dialogue",
                "declaration_expectation": "reply_not_required",
                "semantic_ceiling": "transient_dialogue_not_durable_fact",
            },
            "Turn-local. Listed claims may still be restated. The reply itself is not a declaration.",
        ),
        _row(
            "P3",
            "player_hypothesis_in_contract_text",
            p3_decision,
            p3_contract,
            {
                "response_operation": "player_hypothesis_discussion",
                "declaration_expectation": "hypothesis_discussion_not_required",
                "semantic_ceiling": "conditional_hypothesis_not_established",
            },
            "Detected by the existing player_hypothesis_claims classifier on resolution_contract.raw_input. No new claim is added.",
        ),
        _row(
            "G4_consequential_control",
            "authorized_state_mutation_with_interlocutor",
            g4_decision,
            g4_contract,
            {
                "response_operation": "consequential_realization",
                "declaration_expectation": "required_for_authorized_realization",
                "semantic_ceiling": "authorized_consequential_state_only",
            },
            "Interlocutor is present and still loses to explicit mutation authority. Not a global anti-declaration rule. Provider size not reconstructed.",
        ),
        _row(
            "G1_ordinary_npc",
            "interlocutor_without_inference_or_mutation",
            g1_decision,
            g1_contract,
            {
                "response_operation": "incidental_dialogue",
                "declaration_expectation": "reply_not_required",
                "semantic_ceiling": "transient_dialogue_not_durable_fact",
            },
            "Same turn_operation as P2. Nouns differ. Provider size not reconstructed.",
        ),
        _row(
            "G2_observational_interpretation",
            "qualified_possibilities_infer",
            g2_decision,
            g2_contract,
            {
                "response_operation": "bounded_interpretation",
                "declaration_expectation": "optional_bounded_inference",
                "semantic_ceiling": "interpret_observations_not_unauthorized_cause",
            },
            "Same turn_operation as P1. Provider size not reconstructed.",
        ),
        _row(
            "G3_player_hypothesis",
            "player_hypothesis_in_contract_text",
            g3_decision,
            g3_contract,
            {
                "response_operation": "player_hypothesis_discussion",
                "declaration_expectation": "hypothesis_discussion_not_required",
                "semantic_ceiling": "conditional_hypothesis_not_established",
            },
            "Same turn_operation as P3. Provider size not reconstructed.",
        ),
        _row(
            "G5_direct_observation",
            "perceive_or_inspect_without_interpretation",
            g5_decision,
            g5_contract,
            {
                "response_operation": "direct_observation",
                "declaration_expectation": "observations_only",
                "semantic_ceiling": "direct_observations_only",
            },
            "No infer act, no hypothesis, no interlocutor, no mutation. Provider size not reconstructed.",
        ),
    ]
    payload = {"fixtures": rows}
    target = ROOT / "PR-BV_operation_projection_matrix.json"
    target.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    assert all(row["matches_expected"] for row in rows)

    def excerpt(title: str, decision: dict, contract: dict) -> str:
        recipe = tests._recipe(decision, contract)
        shown = {
            "projection_only": recipe["projection_only"],
            "authority_owner": recipe["authority_owner"],
            "turn_operation": recipe["turn_operation"],
            "answer_strategy": recipe["answer_strategy"],
            "declaration_guidance": {
                "consequential_authorized_claim": recipe["declaration_guidance"]["consequential_authorized_claim"],
                "bounded_inference": recipe["declaration_guidance"]["bounded_inference"],
                "epistemic_premise": recipe["declaration_guidance"]["epistemic_premise"],
                "ordinary_incidental_expression": recipe["declaration_guidance"]["ordinary_incidental_expression"],
            },
            "incidental_improvisation_guidance": recipe["incidental_improvisation_guidance"],
        }
        body = json.dumps(shown, indent=2, ensure_ascii=False)
        return f"## {title}\n\nModel-facing path: user message `decision_facing_answer_recipe`. `turn_operation` is serialized immediately after `authority_owner`.\n\n```json\n{body}\n```\n"

    sections = [
        excerpt("1. P1 — bounded interpretation", p1_decision, p1_contract),
        excerpt("2. P2 — incidental dialogue", p2_decision, p2_contract),
        excerpt("3. P3 — player-hypothesis discussion", p3_decision, p3_contract),
        excerpt("4. Consequential realization control", g4_decision, g4_contract),
        excerpt("5. Ordinary NPC generalization control", g1_decision, g1_contract),
        excerpt("6. Bounded-interpretation generalization control", g2_decision, g2_contract),
    ]
    snapshot = (
        "# PR-BV — Operation projection snapshots\n\n"
        "MODE: DETERMINISTIC. MODEL/API CALLS: ZERO.\n\n"
        "These excerpts are the model-facing recipe fields that select the turn's response. "
        "Claim lists are omitted here; they are unchanged and still travel in `required_content`.\n\n"
        + "\n".join(sections)
    )
    (ROOT / "PR-BV_operation_projection_snapshots.md").write_text(snapshot, encoding="utf-8")
    print(f"wrote {len(rows)} matrix rows")


if __name__ == "__main__":
    main()
