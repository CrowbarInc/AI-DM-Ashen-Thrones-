"""PR-BW narration-only provider envelope. Deterministic. No model calls."""
from __future__ import annotations

import json
from pathlib import Path

from game.gm import _safe_json
from game.gm_resolution_decision import (
    DECL_HYPOTHESIS_NOT_REQUIRED,
    DECL_REPLY_NOT_REQUIRED,
    DECL_REQUIRED_FOR_AUTHORIZED,
    OP_BOUNDED_INTERPRETATION,
    OP_CONSEQUENTIAL_REALIZATION,
    OP_INCIDENTAL_DIALOGUE,
    OP_PLAYER_HYPOTHESIS,
    PROVIDER_ENVELOPE_NARRATION_ONLY,
    PROVIDER_ENVELOPE_STRUCTURED,
    build_decision_facing_answer_recipe,
    select_provider_response_envelope,
    validate_declared_claims_against_decision,
)

LIVE = Path("artifacts/pr_bv_turn_operation_projection_micro_live/evidence")


def _load(probe: str, name: str) -> dict:
    return json.loads((LIVE / probe / name).read_text(encoding="utf-8"))


def _claim(
    claim_id: str,
    text: str,
    *,
    role: str = "MUST_STATE",
    provenance: str = "authored_world_fact",
    source: str = "scene.visible_facts.0",
) -> dict:
    return {
        "claim_id": claim_id,
        "text": text,
        "provenance": provenance,
        "authority": "world_truth" if provenance == "authored_world_fact" else "observation",
        "epistemic_status": "established",
        "modality": "",
        "realization_role": role,
        "relation_kind": "ordinary_predicate",
        "premise_claim_ids": [],
        "source_ref": source,
    }


def _decision(
    contract_id: str,
    claims: list[dict],
    *,
    acts: list[dict] | None = None,
    outcome: str = "established_or_retrieved",
    mutations: list[dict] | None = None,
) -> dict:
    return {
        "contract_id": contract_id,
        "outcome_classification": outcome,
        "realization_claims": claims,
        "epistemic_acts": list(acts or []),
        "permitted_state_mutations": list(mutations or []),
        "executable_obligations": {},
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


def _selected(decision: dict, contract: dict) -> dict:
    selected = select_provider_response_envelope(decision, contract)
    assert selected["projection_only"] is True
    assert selected["authority_owner"] == "gm_resolution_decision"
    return selected


def test_p1_p2_p3_and_consequential_selection_matrix() -> None:
    p1 = _selected(_load("P1", "gm_resolution_decision.json"), _load("P1", "resolution_contract.json"))
    p2 = _selected(_load("P2", "gm_resolution_decision.json"), _load("P2", "resolution_contract.json"))
    p3 = _selected(_load("P3", "gm_resolution_decision.json"), _load("P3", "resolution_contract.json"))

    assert p1["selected_envelope"] == PROVIDER_ENVELOPE_STRUCTURED
    assert p1["response_operation"] == OP_BOUNDED_INTERPRETATION
    assert p1["declaration_channel_exposed"] is True

    assert p2["selected_envelope"] == PROVIDER_ENVELOPE_NARRATION_ONLY
    assert p2["response_operation"] == OP_INCIDENTAL_DIALOGUE
    assert p2["declaration_expectation"] == DECL_REPLY_NOT_REQUIRED
    assert p2["declaration_channel_exposed"] is False

    assert p3["selected_envelope"] == PROVIDER_ENVELOPE_STRUCTURED
    assert p3["response_operation"] == OP_PLAYER_HYPOTHESIS
    assert p3["declaration_expectation"] == DECL_HYPOTHESIS_NOT_REQUIRED
    assert p3["declaration_channel_exposed"] is True

    consequential = _decision(
        "rc_gate",
        [_claim("rc_gate_barred", "The gate is barred.", source="resolution.state_changes.gate")],
        outcome="state_mutation",
        mutations=[{"type": "state_change", "key": "gate", "value": "barred"}],
    )
    selected = _selected(consequential, {"operation": "ask", "interlocutor_id": "warden", "raw_input": "Is it barred?"})
    assert selected["selected_envelope"] == PROVIDER_ENVELOPE_STRUCTURED
    assert selected["response_operation"] == OP_CONSEQUENTIAL_REALIZATION
    assert selected["declaration_expectation"] == DECL_REQUIRED_FOR_AUTHORIZED
    assert selected["declaration_channel_exposed"] is True


def test_generalization_controls_do_not_treat_all_npc_dialogue_as_narration_only() -> None:
    observation = _claim("rc_obs", "A mark is visible on the timber.")
    g1 = _selected(
        _decision("rc_g1", [observation], outcome="epistemically_qualified"),
        {"operation": "ask", "interlocutor_id": "miller", "raw_input": "How was your morning?"},
    )
    g2 = _selected(
        _decision("rc_g2", [observation], outcome="epistemically_qualified"),
        {"operation": "ask", "interlocutor_id": "clerk", "raw_input": "Do you know?"},
    )
    g3 = _selected(
        _decision("rc_g3", [observation], acts=[_infer_act("timber")]),
        {"operation": "inspect", "dimensions": ["interpretation"], "raw_input": "What does this suggest?"},
    )
    g4 = _selected(
        _decision("rc_g4", [observation]),
        {"operation": "perceive", "raw_input": "Maybe someone cut it deliberately. Does that fit?"},
    )
    g5 = _selected(
        _decision(
            "rc_g5",
            [_claim("rc_secret", "The steward hid the ledger.", source="resolution.state_changes.ledger")],
            outcome="state_mutation",
            mutations=[{"type": "fact", "key": "ledger", "value": "hidden"}],
        ),
        {"operation": "ask", "interlocutor_id": "steward", "raw_input": "Where is the ledger?"},
    )
    g6 = _selected(
        _decision(
            "rc_g6",
            [_claim("rc_door", "The vault door opens.", source="resolution.permitted_state_mutations.door")],
            outcome="state_mutation",
            mutations=[{"type": "state_change", "key": "door", "value": "open"}],
        ),
        {"operation": "act", "raw_input": "Open the vault."},
    )

    assert g1["selected_envelope"] == PROVIDER_ENVELOPE_NARRATION_ONLY
    assert g2["selected_envelope"] == PROVIDER_ENVELOPE_NARRATION_ONLY
    assert g3["selected_envelope"] == PROVIDER_ENVELOPE_STRUCTURED
    assert g4["selected_envelope"] == PROVIDER_ENVELOPE_STRUCTURED
    assert g5["selected_envelope"] == PROVIDER_ENVELOPE_STRUCTURED
    assert g6["selected_envelope"] == PROVIDER_ENVELOPE_STRUCTURED


def test_narration_only_parse_normalizes_empty_declarations_without_authorship() -> None:
    text = '{"narration": "The baker glances at the cooling rack. \\"Depends which one came out best.\\""}'
    parsed = _safe_json(text, require_structured_claims=True, provider_response_contract="narration_only")
    envelope = parsed["metadata"]["realization_envelope"]

    assert parsed["player_facing_text"] == 'The baker glances at the cooling rack. "Depends which one came out best."'
    assert envelope["declared_claims"] == []
    assert envelope["normalized_empty_declarations"] is True
    assert envelope["declaration_authorship"] is False


def test_narration_only_rejects_malformed_missing_wrong_and_smuggled_fields() -> None:
    cases = {
        "missing_narration": "{}",
        "wrong_type": '{"narration": 3}',
        "unexpected_declared_claims": '{"declared_claims": [], "narration": "No."}',
        "malformed": '{"narration": ',
    }
    for name, raw in cases.items():
        parsed = _safe_json(raw, require_structured_claims=True, provider_response_contract="narration_only")
        assert parsed["player_facing_text"] == "", name
        assert parsed["metadata"]["structured_contract_failure"] is True, name
        assert parsed["metadata"]["provider_response_contract"] == "narration_only", name


def test_full_envelope_response_and_authorized_declaration_are_unaffected() -> None:
    fact = "The beam is cracked."
    raw = json.dumps({"declared_claims": [{"declaration_mode": "realize", "text": fact}], "narration": fact})
    parsed = _safe_json(raw, require_structured_claims=True)
    assert parsed["player_facing_text"] == fact
    assert parsed["metadata"]["realization_envelope"]["declared_claims"]

    decision = _decision("rc_fact", [_claim("rc_fact_1", fact)])
    claim_id = build_decision_facing_answer_recipe(decision, {"operation": "inspect"})["required_content"][0]["claim_id"]
    declaration = {
        "declaration_mode": "realize",
        "source_claim_id": claim_id,
        "provenance_requested": "authored_world_fact",
        "text": fact,
    }
    verdict = validate_declared_claims_against_decision([declaration], decision=decision)
    assert verdict["hard_valid"] is True
