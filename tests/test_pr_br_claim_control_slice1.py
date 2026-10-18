"""PR-BR proposition-level claim control slice 1.

Deterministic only. No gameplay/model calls.
"""
from __future__ import annotations

from game.gm_resolution_decision import (
    AUTH_WORLD,
    EPISTEMIC_ACT_ESTABLISH,
    EPISTEMIC_ACT_LEAVE_UNRESOLVED,
    PERSIST_WORLD,
    PROVENANCE_AUTHORITATIVE,
    PROVENANCE_GM_INFERENCE,
    PROVENANCE_PLAYER_HYPOTHESIS,
    REL_CAUSAL,
    REL_EVIDENTIAL,
    REL_OBSERVATION,
    STATUS_HYPOTHESIS,
    STATUS_INFERRED,
    audit_narration_against_decision,
    remember_temporal_claims,
)
from game.immutable_valid_response import PROVENANCE_SAFE, run_preserve_if_valid


def _fact(text: str, subject: str, value: str, *, relation_kind: str = REL_OBSERVATION) -> dict:
    return {
        "text": text,
        "provenance": PROVENANCE_AUTHORITATIVE,
        "consequence": "consequential",
        "authorized": True,
        "reason_codes": ["test_authorized"],
        "authority": AUTH_WORLD,
        "persistence": PERSIST_WORLD,
        "source_ref": f"test.{subject}.{value}",
        "outcome_classification": "established_or_retrieved",
        "semantic_identity": {
            "kind": "state_fact",
            "subject": subject,
            "subject_aliases": [subject.replace("_", " ")],
            "relation": "status",
            "value": value,
            "value_aliases": [value.replace("_", " ")],
            "relation_kind": relation_kind,
            "authority": AUTH_WORLD,
        },
    }


def _decision(*facts: dict, unresolved=()) -> dict:
    return {
        "contract_id": "claim-control-test",
        "resolution_method": "deterministic",
        "outcome_classification": "established_or_retrieved",
        "proposed_facts": list(facts),
        "permitted_state_mutations": [],
        "persistence_policy": "world_truth",
        "narration_constraints": [],
        "unresolved_consequential_questions": [],
        "unresolved_qualifiers": list(unresolved),
        "answer_relations": [],
        "epistemic_acts": [
            {"act": EPISTEMIC_ACT_ESTABLISH, "semantic_identity": fact["semantic_identity"]}
            for fact in facts
        ]
        + ([{"act": EPISTEMIC_ACT_LEAVE_UNRESOLVED, "semantic_identity": {"unresolved_qualifiers": list(unresolved)}}] if unresolved else []),
    }


def _audit(text: str, decision: dict) -> dict:
    return audit_narration_against_decision(text, decision=decision, authored_corpus="")


def _reasons(audit: dict) -> set[str]:
    return {reason for row in audit["violations"] for reason in row["reason_codes"]}


def _claim_reasons(audit: dict) -> set[str]:
    return {reason for row in audit["claim_results"] for reason in row["reason_codes"]}


def test_authorized_observation_does_not_authorize_evidential_residuals_for_novel_domains():
    cases = [
        (
            _decision(_fact("The bridge cable is severed.", "bridge cable", "severed")),
            "The severed bridge cable shows saboteurs cut it overnight.",
        ),
        (
            _decision(_fact("The sheep is ill.", "sheep", "ill")),
            "The ill sheep shows the well water poisoned it.",
        ),
        (
            _decision(_fact("The shelf is empty.", "shelf", "empty")),
            "The empty shelf proves thieves removed the cargo.",
        ),
        (
            _decision(_fact("The ledger is burned.", "ledger", "burned")),
            "The burned ledger makes it clear the owner destroyed it to hide fraud.",
        ),
    ]
    for decision, text in cases:
        audit = _audit(text, decision)
        assert audit["hard_valid"] is False, text
        assert any(row["authorized"] is True and row["relation_kind"] == REL_OBSERVATION for row in audit["claim_results"])
        assert "unauthorized_evidential_relation" in _claim_reasons(audit)
        assert "unauthorized_certainty_upgrade" in _claim_reasons(audit) or "shows" in text


def test_positive_authorized_evidential_relation_is_allowed():
    observation = _fact("The bridge cable is severed.", "bridge cable", "severed")
    relation = _fact(
        "The severed bridge cable shows saboteurs cut it overnight.",
        "bridge cable",
        "saboteurs cut overnight",
        relation_kind=REL_EVIDENTIAL,
    )
    relation["semantic_identity"]["relation"] = "evidence"
    relation["semantic_identity"]["evidential_authorized"] = True
    relation["semantic_identity"]["value_aliases"].append("saboteurs cut it overnight")
    decision = _decision(observation, relation)
    audit = _audit("The severed bridge cable shows saboteurs cut it overnight.", decision)
    assert audit["hard_valid"] is True
    assert any(row["relation_kind"] == REL_EVIDENTIAL and row["authorized"] for row in audit["claim_results"])


def test_actual_a2_a4_regressions_do_not_hide_inside_authorized_observation_sentences():
    decision = _decision(
        _fact("The water jar is split.", "water jar", "split"),
        _fact("The clay is dried flakes.", "clay", "dried flakes"),
        _fact("The coil-pots are intact.", "coil pots", "intact"),
    )
    a2_1 = "The split jar and dried clay flakes indicate it was left unfired."
    a2_2 = "Unfired clay failed to hold moisture, pointing to process disruption."
    a4_2 = "The intact coil-pots nearby show no signs of firing."
    a4_3 = "That makes it clear it was never fired in a kiln."
    for text in (a2_1, a2_2, a4_2, a4_3):
        audit = _audit(text, decision)
        assert audit["hard_valid"] is False, text
        assert _claim_reasons(audit) & {
            "unauthorized_evidential_relation",
            "unauthorized_causal_relation",
            "unauthorized_certainty_upgrade",
            "unauthorized_consequential_residual",
        }


def test_leave_unresolved_hedge_is_valid_epistemic_speech():
    decision = _decision(_fact("The water jar is split.", "water jar", "split"), unresolved=("actor", "cause", "time"))
    audit = _audit("The cause is still unclear, and nothing here establishes who did it.", decision)
    assert audit["hard_valid"] is True
    assert any(row["relation_kind"] == "epistemic_status" and row["authorized"] for row in audit["claim_results"])


def test_preservation_does_not_keep_certainty_after_deleting_uncertainty():
    resolution = {
        "kind": "investigate",
        "metadata": {
            "resolution_contract": {"operation": "inspect", "contract_id": "rc-claim-control"},
            "gm_resolution_decision": _decision(
                _fact("The water jar is split.", "water jar", "split"),
                unresolved=("actor", "cause", "time"),
            ),
        },
    }
    mixed = "The split jar proves it was never fired. The cause remains unclear."
    sealed = run_preserve_if_valid(
        {"player_facing_text": mixed, "metadata": {}},
        regenerate=None,
        resolution=resolution,
        player_text="Why did the jar fail?",
    )
    assert "proves" not in sealed["player_facing_text"].lower()
    assert "never fired" not in sealed["player_facing_text"].lower()
    assert "unclear" in sealed["player_facing_text"].lower()


def test_temporal_provenance_records_non_world_truth_without_promotion():
    session = {"active_scene_id": "bridge", "turn_counter": 2}
    claims = [
        {
            "text": "Sabotage is one possibility.",
            "semantic_identity": {"subject": "sabotage", "relation": "possibility"},
            "provenance": PROVENANCE_GM_INFERENCE,
            "authority": "observation",
            "epistemic_status": STATUS_INFERRED,
            "relation_kind": "epistemic_status",
            "authorized": True,
        },
        {
            "text": "If saboteurs cut it last night, who had access?",
            "semantic_identity": {"subject": "sabotage", "relation": "hypothesis"},
            "provenance": PROVENANCE_PLAYER_HYPOTHESIS,
            "authority": "observation",
            "epistemic_status": STATUS_HYPOTHESIS,
            "relation_kind": "epistemic_status",
            "authorized": True,
        },
        {
            "text": "The severed cable proves saboteurs cut it overnight.",
            "semantic_identity": {"subject": "sabotage"},
            "provenance": "generated_proposal",
            "authority": "unauthorized",
            "epistemic_status": "unresolved",
            "relation_kind": REL_EVIDENTIAL,
            "authorized": False,
            "reason_codes": ["unauthorized_evidential_relation"],
        },
    ]
    record = remember_temporal_claims(session, claims=claims, scene_id="bridge", source_turn=2)
    assert record["gm_inferences"][0]["authority"] != AUTH_WORLD
    assert record["player_hypotheses"][0]["epistemic_status"] == STATUS_HYPOTHESIS
    assert record["rejected_consequential"][0]["reason_codes"] == ["unauthorized_evidential_relation"]
