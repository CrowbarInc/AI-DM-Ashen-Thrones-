"""PR-BU claim-composition regressions. Deterministic. No model or gameplay calls.

A permitted epistemic operation authorizes that operation, not the sentence.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from game.gm_resolution_decision import (
    PROVENANCE_AUTHORITATIVE,
    PROVENANCE_GM_INFERENCE,
    AUTH_INFERENCE,
    AUTH_WORLD,
    audit_narrated_claims,
    audit_realization_envelope_against_decision,
    classify_narrated_fact,
    validate_declared_claims_against_decision,
    _decision_ground,
    _has_ungrounded_definite,
)

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "artifacts" / "pr_bt_selective_epistemic_restoration_final_micro_live" / "evidence"
MATRIX = ROOT / "PR-BU_validator_semantic_matrix.json"
CORPUS = (
    "The bell's wooden yoke is split.\n"
    "The bell's leather hanger is torn.\n"
    "A bronze bell hangs from a timber frame.\n"
    "Chapel belfry"
)
P1_SENTENCE = (
    "This damage might suggest the bell has been subjected to significant stress or prolonged neglect, "
    "perhaps due to heavy use or an external force acting upon it."
)
P1_DECLARATION = (
    "The split wooden yoke and torn leather hanger might indicate the bell has been under significant stress "
    "or neglect, possibly from heavy use or an external force."
)
P3_SENTENCE = (
    "These visible damages could be consistent with being deliberately cut, but without additional evidence, "
    "that motive remains uncertain."
)
USEFUL = (
    "The split wooden yoke and the torn leather hanger could be consistent with significant stress or force."
)
C04_TEXT = "The split wooden yoke might point to neglect."
CONTROL_A = "The split yoke might suggest the wood gave under a load."
POSITIVE_COMPLEMENT = "The split wooden yoke might point to significant stress."


def _load(name: str) -> dict:
    return json.loads((EVIDENCE / name).read_text(encoding="utf-8"))


def _proposal(text: str) -> dict:
    return {
        "declaration_id": "inf_1",
        "declaration_mode": "propose",
        "source_claim_id": None,
        "premise_claim_ids": ["rc_db5ec0aa65c3", "rc_b31ecb1fd1c7"],
        "semantic_identity": {},
        "provenance_requested": "gm_inference",
        "epistemic_status": "inferred",
        "modality": "possible",
        "realization_role": "MAY_STATE",
        "relation_kind": "epistemic_status",
        "text": text,
    }


def _classify(sentence: str, decision: dict) -> str:
    fact = classify_narrated_fact(
        sentence,
        decision=decision,
        authored_corpus=CORPUS,
        response_text=sentence,
    )
    if fact is None:
        return "accept_by_omission"
    return "accept" if fact.authorized else "reject"


def _reasons(sentence: str, decision: dict) -> list[str]:
    claims = audit_narrated_claims(
        sentence,
        decision=decision,
        authored_corpus=CORPUS,
        response_text=sentence,
    )
    reasons: list[str] = []
    for claim in claims:
        reasons.extend(claim.reason_codes)
    return reasons


def _passed(expected: str, actual: str) -> bool:
    if expected == "accept":
        return actual in {"accept", "accept_by_omission"}
    return actual == expected


@pytest.fixture(scope="module")
def decisions() -> dict:
    p1 = _load("P1/gm_resolution_decision.json")
    p3 = _load("P3/gm_resolution_decision.json")
    declared = validate_declared_claims_against_decision([_proposal(P1_DECLARATION)], decision=p1)
    slotted = dict(p1)
    slotted["unresolved_qualifiers"] = ["cause", "actor", "time", "history"]
    return {
        "p1": p1,
        "p3": p3,
        "p1_declaration": declared,
        "slotted": slotted,
    }


@pytest.fixture(scope="module")
def matrix_cases() -> list[dict]:
    payload = json.loads(MATRIX.read_text(encoding="utf-8"))
    assert payload["case_count"] == 41
    assert len(payload["cases"]) == 41
    return payload["cases"]


def _decision_for(case: dict, decisions: dict) -> dict:
    setup = case["authority_setup"]
    if setup == "p3_perceive":
        return decisions["p3"]
    if setup == "p1_interpret_with_unresolved_qualifiers":
        return decisions["slotted"]
    return decisions["p1"]


def _matrix_ids() -> list[str]:
    payload = json.loads(MATRIX.read_text(encoding="utf-8"))
    return [row["case_id"] for row in payload["cases"]]


@pytest.mark.parametrize("case_id", _matrix_ids())
def test_promoted_matrix_keeps_discovery_classification(case_id, matrix_cases, decisions):
    rows = {row["case_id"]: row for row in matrix_cases}
    case = rows[case_id]
    actual = _classify(case["text"], _decision_for(case, decisions))
    assert _passed(case["expected_classification"], actual), (case_id, actual, case["text"])


def test_matrix_has_forty_one_cases(matrix_cases):
    assert len(matrix_cases) == 41
    assert {row["case_id"] for row in matrix_cases} >= {"A01", "C01", "C01b", "D02", "H01", "G01", "G02"}


def test_p1_hedge_does_not_authorize_cause(decisions):
    claims = audit_narrated_claims(
        P1_SENTENCE,
        decision=decisions["p1"],
        authored_corpus=CORPUS,
        response_text=P1_SENTENCE,
    )
    codes = [code for claim in claims for code in claim.reason_codes]
    assert "authorized_qualified_inference" in codes
    assert "unauthorized_causal_relation" in codes
    assert _classify(P1_SENTENCE, decisions["p1"]) == "reject"
    fact = classify_narrated_fact(
        P1_SENTENCE,
        decision=decisions["p1"],
        authored_corpus=CORPUS,
        response_text=P1_SENTENCE,
    )
    assert fact is not None and fact.authorized is False
    assert "unauthorized_causal_relation" in fact.reason_codes


def test_p1_declaration_hedge_does_not_authorize_possibly_from(decisions):
    declared = decisions["p1_declaration"]
    assert declared["hard_valid"] is False
    reasons = [code for row in declared["violations"] for code in row.get("reason_codes") or []]
    assert "unauthorized_causal_relation" in reasons
    assert declared["accepted_claims"] == []


def test_p1_envelope_rejects_before_the_declaration_can_ground_narration(decisions):
    envelope = audit_realization_envelope_against_decision(
        narration=(
            "The bell's wooden yoke is visibly split, and its leather hanger is torn. " + P1_SENTENCE
        ),
        declared_claims=[_proposal(P1_DECLARATION)],
        decision=decisions["p1"],
        authored_corpus=CORPUS,
    )
    assert envelope["hard_valid"] is False
    assert envelope["narration_validation"] is None
    reasons = [code for row in envelope["violations"] for code in row.get("reason_codes") or []]
    assert "unauthorized_causal_relation" in reasons


def test_speculative_inference_does_not_ground_a_definite_span(decisions):
    polluted = dict(decisions["p1"])
    polluted["proposed_facts"] = list(decisions["p1"].get("proposed_facts") or []) + [
        {
            "text": P1_DECLARATION,
            "provenance": PROVENANCE_GM_INFERENCE,
            "authority": AUTH_INFERENCE,
            "authorized": True,
        }
    ]
    ground = _decision_ground(CORPUS, polluted)
    assert "might" not in ground.split()
    assert _has_ungrounded_definite(P1_SENTENCE, ground) is True
    assert _classify(P1_SENTENCE, polluted) == "reject"

    authoritative = dict(decisions["p1"])
    authoritative["proposed_facts"] = list(decisions["p1"].get("proposed_facts") or []) + [
        {
            "text": "This damage is the split in the wooden yoke.",
            "provenance": PROVENANCE_AUTHORITATIVE,
            "authority": AUTH_WORLD,
            "authorized": True,
        }
    ]
    authored_ground = _decision_ground(CORPUS, authoritative)
    assert "damage" in authored_ground


def test_useful_qualified_inference_stays_accepted_in_narration_and_declaration(decisions):
    assert _classify(USEFUL, decisions["p1"]) == "accept"
    codes = _reasons(USEFUL, decisions["p1"])
    assert "authorized_qualified_inference" in codes
    assert "unauthorized_causal_relation" not in codes
    assert "unauthorized_evidential_relation" not in codes
    declared = validate_declared_claims_against_decision([_proposal(USEFUL)], decision=decisions["p1"])
    assert declared["hard_valid"] is True


def test_control_a_suggest_is_not_an_evidential_establishment(decisions):
    text = "The split yoke might suggest the wood gave under a load."
    assert _classify(text, decisions["p1"]) == "accept"
    assert "unauthorized_evidential_relation" not in _reasons(text, decisions["p1"])


def test_p3_uncertain_and_unclear_accept_the_same_conditional_without_a_new_slot(decisions):
    stem = (
        "The split wooden yoke and the torn leather hanger could be consistent with deliberate cutting, but "
    )
    for coda in (
        "the explanation remains uncertain.",
        "the explanation remains unclear.",
        "the explanation is uncertain.",
        "the explanation is unclear.",
        "deliberate cutting cannot be determined.",
        "deliberate cutting cannot be established.",
    ):
        text = stem + coda
        assert _classify(text, decisions["p3"]) in {"accept", "accept_by_omission"}, text
        assert "unsupported_narrator_lead" not in _reasons(text, decisions["p3"])


def test_p3_unresolved_status_does_not_authorize_motive(decisions):
    for sentence in (
        P3_SENTENCE,
        P3_SENTENCE.replace("remains uncertain", "remains unclear"),
        "That motive remains unclear, but the split wooden yoke could be consistent with deliberate cutting.",
        "The split wooden yoke could be consistent with deliberate cutting, but that motive remains uncertain.",
    ):
        assert _classify(sentence, decisions["p3"]) == "reject", sentence
        assert "unsupported_narrator_lead" in _reasons(sentence, decisions["p3"])


def test_cause_order_does_not_change_the_reject(decisions):
    forward = "The split wooden yoke might suggest significant stress, perhaps due to prolonged neglect."
    reverse = "Perhaps due to prolonged neglect, the split wooden yoke might suggest significant stress."
    for text in (forward, reverse):
        assert _classify(text, decisions["p1"]) == "reject"
        codes = _reasons(text, decisions["p1"])
        assert "authorized_qualified_inference" in codes
        assert "unauthorized_causal_relation" in codes


def test_declaration_and_narration_agree_on_hedged_cause(decisions):
    text = "The split wooden yoke might suggest significant stress, perhaps due to prolonged neglect."
    assert _classify(text, decisions["p1"]) == "reject"
    assert "unauthorized_causal_relation" in _reasons(text, decisions["p1"])
    declared = validate_declared_claims_against_decision([_proposal(text)], decision=decisions["p1"])
    assert declared["hard_valid"] is False
    reasons = [code for row in declared["violations"] for code in row.get("reason_codes") or []]
    assert "unauthorized_causal_relation" in reasons


def test_negation_blocks_certainty_and_positive_clarity_does_not(decisions):
    assert _classify("It is not clearly neglect.", decisions["p1"]) in {"accept", "accept_by_omission"}
    assert "unauthorized_certainty_upgrade" not in _reasons("It is not clearly neglect.", decisions["p1"])
    assert _classify("Deliberate cutting cannot be established.", decisions["p3"]) in {"accept", "accept_by_omission"}
    assert "unauthorized_certainty_upgrade" not in _reasons("Deliberate cutting cannot be established.", decisions["p3"])
    clearly = "It clearly could be neglect."
    assert _classify(clearly, decisions["p1"]) == "reject"
    assert "unauthorized_certainty_upgrade" in _reasons(clearly, decisions["p1"])
    cause = "The cause is clear."
    assert _classify(cause, decisions["p1"]) == "reject"
    assert "unauthorized_certainty_upgrade" in _reasons(cause, decisions["p1"])
    assert _classify("The cause is not clear.", decisions["p1"]) in {"accept", "accept_by_omission"}


def test_someone_cracked_is_an_actor_attribution(decisions):
    text = "Someone cracked the wooden yoke."
    assert _classify(text, decisions["p1"]) == "reject"
    assert "unauthorized_actor_attribution" in _reasons(text, decisions["p1"])


def _copy_decision(decision: dict) -> dict:
    return json.loads(json.dumps(decision))


def _complement_identity(sentence: str, decision: dict) -> dict:
    claims = audit_narrated_claims(
        sentence,
        decision=decision,
        authored_corpus=CORPUS,
        response_text=sentence,
    )
    for claim in claims:
        if "unauthorized_inference_complement" in claim.reason_codes:
            return dict(claim.semantic_identity)
    return {}


def test_c04_hedge_does_not_authorize_neglect_complement(decisions):
    assert _classify(C04_TEXT, decisions["p1"]) == "reject"
    codes = _reasons(C04_TEXT, decisions["p1"])
    assert "authorized_qualified_inference" in codes
    assert "unauthorized_inference_complement" in codes
    assert _complement_identity(C04_TEXT, decisions["p1"]).get("unsupported_complement") == "neglect"


def test_valid_hedge_with_authorized_complement_stays_accepted(decisions):
    assert _classify(POSITIVE_COMPLEMENT, decisions["p1"]) == "accept"
    codes = _reasons(POSITIVE_COMPLEMENT, decisions["p1"])
    assert "authorized_qualified_inference" in codes
    assert "unauthorized_inference_complement" not in codes
    assert _classify(CONTROL_A, decisions["p1"]) == "accept"
    assert _classify(USEFUL, decisions["p1"]) == "accept"
    declared = validate_declared_claims_against_decision(
        [_proposal(POSITIVE_COMPLEMENT)],
        decision=decisions["p1"],
    )
    assert declared["hard_valid"] is True


def test_same_neglect_complement_is_accepted_when_the_decision_permits_it(decisions):
    permitted = _copy_decision(decisions["p1"])
    permitted["realization_claims"] = list(permitted.get("realization_claims") or []) + [
        {
            "claim_id": "rc_permit_neglect",
            "text": "Neglect is one qualified possibility for this damage.",
            "semantic_identity": {"value": "neglect", "epistemic_status": "inferred"},
            "provenance": "gm_inference",
            "authority": "inference",
            "epistemic_status": "inferred",
            "modality": "possible",
            "realization_role": "MAY_INFER",
            "relation_kind": "epistemic_status",
        }
    ]
    assert _classify(C04_TEXT, permitted) == "accept"
    fact = classify_narrated_fact(
        C04_TEXT,
        decision=permitted,
        authored_corpus=CORPUS,
        response_text=C04_TEXT,
    )
    assert fact is not None and fact.authorized is True
    assert fact.authority != AUTH_WORLD
    assert "unauthorized_inference_complement" not in _reasons(C04_TEXT, permitted)


def test_player_hypothesis_lets_the_gm_discuss_neglect_without_promoting_it(decisions):
    hypothesized = _copy_decision(decisions["p1"])
    hypothesized["proposed_facts"] = list(hypothesized.get("proposed_facts") or []) + [
        {
            "text": "Maybe this was neglect?",
            "provenance": "player_hypothesis",
            "authority": "observation",
            "authorized": True,
            "epistemic_status": "hypothesis",
            "semantic_identity": {"epistemic_status": "hypothesis", "value": "neglect"},
        }
    ]
    assert _classify(C04_TEXT, hypothesized) == "accept"
    fact = classify_narrated_fact(
        C04_TEXT,
        decision=hypothesized,
        authored_corpus=CORPUS,
        response_text=C04_TEXT,
    )
    assert fact is not None and fact.authorized is True
    assert fact.authority != AUTH_WORLD
    assert fact.provenance != "authored_world_fact"
    assert "unauthorized_inference_complement" not in _reasons(C04_TEXT, hypothesized)


def test_authoritative_neglect_is_not_rejected_as_ordinary_narration(decisions):
    authoritative = _copy_decision(decisions["p1"])
    authoritative["proposed_facts"] = list(authoritative.get("proposed_facts") or []) + [
        {
            "text": "The wooden yoke shows long neglect.",
            "provenance": "authored_world_fact",
            "authority": "world_truth",
            "authorized": True,
            "semantic_identity": {},
        }
    ]
    ordinary = "Long neglect marks the wooden yoke."
    assert _classify(ordinary, authoritative) in {"accept", "accept_by_omission"}
    assert "unauthorized_inference_complement" not in _reasons(ordinary, authoritative)
    assert _classify(C04_TEXT, authoritative) == "accept"


def test_declaration_checks_the_inference_complement(decisions):
    rejected = validate_declared_claims_against_decision([_proposal(C04_TEXT)], decision=decisions["p1"])
    assert rejected["hard_valid"] is False
    reasons = [code for row in rejected["violations"] for code in row.get("reason_codes") or []]
    assert "unauthorized_inference_complement" in reasons
    accepted = validate_declared_claims_against_decision(
        [_proposal(POSITIVE_COMPLEMENT)],
        decision=decisions["p1"],
    )
    assert accepted["hard_valid"] is True


def test_authorized_complement_does_not_immunize_an_unauthorized_neighbor(decisions):
    forward = "The split wooden yoke might point to significant stress or neglect."
    reverse = "Neglect is what the split wooden yoke might point to, along with significant stress."
    for text in (forward, reverse):
        assert _classify(text, decisions["p1"]) == "reject", text
        codes = _reasons(text, decisions["p1"])
        assert "authorized_qualified_inference" in codes
        assert "unauthorized_inference_complement" in codes


def test_speculative_neglect_declaration_does_not_authorize_the_complement(decisions):
    polluted = _copy_decision(decisions["p1"])
    polluted["proposed_facts"] = list(polluted.get("proposed_facts") or []) + [
        {
            "text": C04_TEXT,
            "provenance": PROVENANCE_GM_INFERENCE,
            "authority": AUTH_INFERENCE,
            "authorized": True,
            "semantic_identity": {"value": "neglect", "epistemic_status": "inferred"},
        }
    ]
    assert _classify(C04_TEXT, polluted) == "reject"
    assert "unauthorized_inference_complement" in _reasons(C04_TEXT, polluted)
    envelope = audit_realization_envelope_against_decision(
        narration=C04_TEXT,
        declared_claims=[_proposal(C04_TEXT)],
        decision=decisions["p1"],
        authored_corpus=CORPUS,
    )
    assert envelope["hard_valid"] is False
    assert envelope["narration_validation"] is None
