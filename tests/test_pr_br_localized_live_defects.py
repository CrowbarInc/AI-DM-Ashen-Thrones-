"""PR-BR localized live-validation repairs. Deterministic; no model calls."""
from __future__ import annotations

from game.discourse_state import commit_active_epistemic_claim
from game.api_turn_support import _finalize_player_facing_for_turn
from game.gm_resolution_decision import (
    AUTH_OBSERVATION,
    EPISTEMIC_ACT_INFER,
    PROVENANCE_GM_INFERENCE,
    PROVENANCE_PLAYER_HYPOTHESIS,
    REL_EPISTEMIC_STATUS,
    STATUS_HYPOTHESIS,
    STATUS_INFERRED,
    audit_narration_against_decision,
    build_gm_resolution_decision,
    preservation_structure_valid,
    prompt_projection_for_temporal_provenance,
    remember_temporal_claims,
    sealed_temporal_claims,
)
from game.immutable_valid_response import run_preserve_if_valid
from game.resolution_contract import construct_resolution_contract
from tests.test_pr_br_claim_control_slice1 import _decision, _fact
from tests.test_pr_br_claim_control_slice2 import _relation_fact


def _scene_fact(text: str, subject: str, aliases: list[str], value: str, value_aliases: list[str]) -> dict:
    return {
        "text": text,
        "semantic_identity": {
            "kind": "world_fact",
            "subject": subject,
            "subject_aliases": aliases,
            "relation": "observation",
            "value": value,
            "value_aliases": value_aliases,
            "polarity": "positive",
        },
    }


def test_a1_explicit_inspection_subject_binds_referential_inference_question():
    text = (
        "I examine the snapped counterweight chain and the roof-hatch mechanism. "
        "What does the damage suggest?"
    )
    contract = construct_resolution_contract(
        player_text=text,
        session={"active_scene_id": "service_room", "turn_counter": 1},
        scene_id="service_room",
        canonical_referents=[],
    )
    assert contract.operation == "inspect"
    assert contract.expected_resolution == "answer"
    assert contract.dimensions == ("interpretation",)
    assert contract.ambiguous is False
    assert contract.construction["validation_status"] == "validated"
    assert contract.conversational_subject == "snapped counterweight chain and the roof-hatch mechanism"


def test_inference_request_generalizes_without_domain_target_vocabulary():
    examples = [
        ("I inspect the cracked wheel. What does the damage suggest?", "cracked wheel"),
        ("I examine the spoiled medicine. What might its condition mean?", "spoiled medicine"),
        ("I study the torn net. Does this point to anything?", "torn net"),
        ("I look over the faded banner. What might this tell me?", "faded banner"),
    ]
    for text, subject in examples:
        contract = construct_resolution_contract(
            player_text=text,
            session={"active_scene_id": "workshop", "turn_counter": 1},
            scene_id="workshop",
            canonical_referents=[],
        )
        assert contract.operation == "inspect", text
        assert contract.expected_resolution == "answer", text
        assert "interpretation" in contract.dimensions, text
        assert contract.conversational_subject == subject, text
        assert contract.construction["validation_status"] == "validated", text


def test_inference_request_adds_infer_act_without_establishing_an_explanation():
    player = "I inspect the cracked wheel. What does the damage suggest?"
    contract = construct_resolution_contract(
        player_text=player,
        session={"active_scene_id": "mill", "turn_counter": 1},
        scene_id="mill",
        canonical_referents=[],
    )
    resolution = {"kind": "investigate", "metadata": {"resolution_contract": contract.as_dict()}}
    scene = {
        "scene": {
            "id": "mill",
            "visible_facts": [
                _scene_fact(
                    "One spoke of the wheel is cracked.",
                    "mill_wheel",
                    ["wheel", "cracked wheel"],
                    "cracked spoke",
                    ["cracked", "cracked spoke"],
                )
            ],
        }
    }
    decision = build_gm_resolution_decision(resolution=resolution, scene=scene).as_dict()
    infer = [act for act in decision["epistemic_acts"] if act["act"] == EPISTEMIC_ACT_INFER]
    assert infer
    assert infer[-1]["semantic_identity"]["scope"] == "qualified_possibilities_only"
    assert audit_narration_against_decision(
        "Heavy strain is one possibility.", decision=decision
    )["hard_valid"]
    assert not audit_narration_against_decision(
        "A saboteur broke the wheel.", decision=decision
    )["hard_valid"]


def test_negative_epistemic_status_and_limits_are_valid_but_positive_evidence_is_not():
    decision = _decision(
        _fact("The lock is damaged.", "lock", "damaged"),
        unresolved=("cause", "actor", "time"),
    )
    allowed = [
        "The cause remains unknown.",
        "Nothing established here identifies who did it.",
        "We do not know when it happened.",
        "That is only a possibility.",
        "The damage does not identify who caused it.",
        "Nothing established here tells you when it happened.",
        "The observation supports several possibilities but no confirmed cause.",
    ]
    for text in allowed:
        audit = audit_narration_against_decision(text, decision=decision)
        assert audit["hard_valid"], (text, audit)
        reasons = {reason for row in audit["claim_results"] for reason in row["reason_codes"]}
        assert "unauthorized_certainty_upgrade" not in reasons
        assert "unauthorized_evidential_relation" not in reasons
    assert not audit_narration_against_decision(
        "The broken lock proves nobody touched it.", decision=decision
    )["hard_valid"]


def test_direct_epistemic_question_binds_active_claim_and_requests_answer():
    session = {
        "active_scene_id": "mill",
        "turn_counter": 2,
        "discourse_focus": {
            "version": 1,
            "scene_id": "mill",
            "active_claim": {
                "id": "claim_strain",
                "label": "Heavy strain is one possibility.",
                "kind": "claim",
                "scene_id": "mill",
                "turn_index": 1,
                "source": "gm_inference",
                "epistemic_status": "inferred",
            },
        },
    }
    for text in (
        "Do we know the cause, or are we guessing?",
        "Is that established, or just one possibility?",
        "Can we actually tell who did this?",
    ):
        contract = construct_resolution_contract(
            player_text=text,
            session=session,
            scene_id="mill",
            canonical_referents=[],
        )
        assert contract.expected_resolution == "answer", text
        assert contract.dimension == "confidence", text
        assert contract.discourse_ref and contract.discourse_ref.type == "claim", text


def test_unsupported_hedged_leads_remain_rejected_and_authorized_lead_survives():
    decision = _decision(_fact("A brass lamp stands on the desk.", "brass lamp", "present"))
    for text in (
        "Maybe the brass lamp contains a hidden message.",
        "You could inspect the brass lamp for evidence.",
    ):
        audit = audit_narration_against_decision(text, decision=decision)
        assert not audit["hard_valid"], (text, audit)
        assert any(
            "unsupported_narrator_lead" in row["reason_codes"]
            for row in audit["violations"]
        )
    lead = _fact(
        "The maintenance journal contains notes relevant to the mechanism.",
        "maintenance journal",
        "relevant maintenance notes",
    )
    lead["semantic_identity"]["relation"] = "lead"
    lead["semantic_identity"]["value_aliases"].append("worth checking")
    authorized = _decision(lead)
    assert audit_narration_against_decision(
        "The maintenance journal may be worth checking.", decision=authorized
    )["hard_valid"]


def test_dialogue_preservation_keeps_structural_units_and_reaudits_exact_candidate():
    decision = _decision(_fact("Tavia sorts the blank tags.", "Tavia", "sorts blank tags"))
    resolution = {
        "kind": "question",
        "metadata": {
            "resolution_contract": {
                "contract_id": "quoted-preservation",
                "operation": "ask",
                "raw_input": "What are you tying the tags with?",
                "interlocutor_id": "tavia",
                "expected_resolution": "answer",
            },
            "gm_resolution_decision": decision,
        },
    }
    source = (
        '"I tie the tags with hemp cord," Tavia says. '
        '"It is sturdy and easy to handle." She flexes her fingers. '
        '"They do get sore after a long stretch of sorting, but I have gotten used to it over time. '
        'The knot is quick to tie."'
    )
    sealed = run_preserve_if_valid(
        {"player_facing_text": source, "metadata": {}},
        regenerate=None,
        resolution=resolution,
        player_text="What are you tying the tags with?",
    )
    text = sealed["player_facing_text"]
    assert "gotten used" not in text
    assert preservation_structure_valid(text)
    final_audit = sealed["metadata"]["accepted_response"]["hard_validation"][
        "gm_resolution_decision_audit"
    ]
    assert final_audit["hard_valid"]
    assert all(row["text"] in text for row in final_audit["claim_results"])


def test_malformed_quote_candidate_is_rejected_instead_of_sealed():
    decision = _decision()
    resolution = {
        "metadata": {
            "resolution_contract": {
                "contract_id": "bad-quote",
                "operation": "ask",
                "raw_input": "What are you using?",
                "expected_resolution": "answer",
            },
            "gm_resolution_decision": decision,
        }
    }
    sealed = run_preserve_if_valid(
        {"player_facing_text": '"I use hemp cord, Tavia says.', "metadata": {}},
        regenerate=None,
        resolution=resolution,
        player_text="What are you using?",
    )
    assert sealed["player_facing_text"] != '"I use hemp cord, Tavia says.'
    assert preservation_structure_valid(sealed["player_facing_text"])


def test_temporal_provenance_persists_status_without_repetition_promotion():
    session = {"active_scene_id": "mill", "turn_counter": 1}
    claims = [
        {
            "text": "Heavy strain is one possibility.",
            "semantic_identity": {"subject": "heavy strain", "relation": "possibility"},
            "provenance": PROVENANCE_GM_INFERENCE,
            "authority": AUTH_OBSERVATION,
            "epistemic_status": STATUS_INFERRED,
            "relation_kind": REL_EPISTEMIC_STATUS,
            "authorized": True,
        },
        {
            "text": "If strain caused it, who operated the machine?",
            "semantic_identity": {"subject": "heavy strain", "relation": "hypothesis"},
            "provenance": PROVENANCE_PLAYER_HYPOTHESIS,
            "authority": AUTH_OBSERVATION,
            "epistemic_status": STATUS_HYPOTHESIS,
            "relation_kind": REL_EPISTEMIC_STATUS,
            "authorized": True,
        },
        {
            "text": "Hemp cord binds the tags.",
            "semantic_identity": {"subject": "hemp cord", "relation": "incidental"},
            "provenance": "bounded_incidental",
            "authority": "bounded_incidental",
            "epistemic_status": "established",
            "relation_kind": "ordinary_predicate",
            "authorized": True,
        },
        {
            "text": "A saboteur snapped the chain.",
            "semantic_identity": {"subject": "chain", "relation": "actor"},
            "provenance": "generated_proposal",
            "authority": "unauthorized",
            "epistemic_status": "unresolved",
            "relation_kind": "actor_attribution",
            "authorized": False,
            "reason_codes": ["unauthorized_actor_attribution"],
        },
    ]
    record = remember_temporal_claims(session, claims=claims, scene_id="mill", source_turn=1)
    assert len(record["gm_inferences"]) == 1
    assert len(record["player_hypotheses"]) == 1
    assert len(record["accepted_incidentals"]) == 1
    assert len(record["rejected_consequential"]) == 1
    remember_temporal_claims(session, claims=claims[:2], scene_id="mill", source_turn=2)
    assert all(row["authority"] != "world_truth" for row in record["gm_inferences"])
    assert all(row["authority"] != "world_truth" for row in record["player_hypotheses"])
    projection = prompt_projection_for_temporal_provenance(session, scene_id="mill")
    assert projection["buckets"]["gm_inferences"]
    assert projection["buckets"]["player_hypotheses"]


def test_sealed_claim_extraction_excludes_rejected_acceptance_and_sets_active_claim():
    decision = _decision()
    decision["epistemic_acts"].append(
        {
            "act": EPISTEMIC_ACT_INFER,
            "authority": AUTH_OBSERVATION,
            "semantic_identity": {"scope": "qualified_possibilities_only"},
        }
    )
    resolution = {
        "metadata": {
            "resolution_contract": {
                "contract_id": "inference-seal",
                "operation": "inspect",
                "raw_input": "What does this suggest?",
                "expected_resolution": "answer",
            },
            "gm_resolution_decision": decision,
        }
    }
    sealed = run_preserve_if_valid(
        {"player_facing_text": "Heavy strain is one possibility.", "metadata": {}},
        regenerate=None,
        resolution=resolution,
        player_text="What does this suggest?",
    )
    accepted, rejected = sealed_temporal_claims(sealed, player_text="What does this suggest?")
    assert any(row["provenance"] == PROVENANCE_GM_INFERENCE for row in accepted)
    assert not rejected
    session = {"active_scene_id": "mill", "turn_counter": 1}
    remember_temporal_claims(session, claims=accepted, scene_id="mill", source_turn=1)
    assert commit_active_epistemic_claim(
        session, claims=accepted, scene_id="mill", turn_index=1
    )
    active = session["discourse_focus"]["active_claim"]
    assert active["source"] == PROVENANCE_GM_INFERENCE
    assert active["epistemic_status"] == STATUS_INFERRED


def test_production_final_emission_commits_exact_sealed_inference():
    decision = _decision()
    decision["epistemic_acts"].append(
        {
            "act": EPISTEMIC_ACT_INFER,
            "authority": AUTH_OBSERVATION,
            "semantic_identity": {"scope": "qualified_possibilities_only"},
        }
    )
    resolution = {
        "kind": "investigate",
        "metadata": {
            "resolution_contract": {
                "contract_id": "production-provenance",
                "turn_index": 1,
                "operation": "inspect",
                "raw_input": "What does this suggest?",
                "expected_resolution": "answer",
                "construction": {},
            },
            "gm_resolution_decision": decision,
        },
    }
    sealed = run_preserve_if_valid(
        {"player_facing_text": "Heavy strain is one possibility.", "metadata": {}},
        regenerate=None,
        resolution=resolution,
        player_text="What does this suggest?",
    )
    session = {"active_scene_id": "mill", "turn_counter": 1}
    emitted, _ = _finalize_player_facing_for_turn(
        sealed,
        resolution=resolution,
        session=session,
        world={},
        scene={"scene": {"id": "mill", "visible_facts": []}},
    )
    assert emitted["player_facing_text"] == "Heavy strain is one possibility."
    assert session["narration_temporal_provenance"]["gm_inferences"][0]["text"] == emitted["player_facing_text"]
    assert session["discourse_focus"]["active_claim"]["epistemic_status"] == STATUS_INFERRED
    evidence = emitted["metadata"]["emission_debug"]["temporal_provenance_commit"]
    assert evidence["sealed_text"] == emitted["player_facing_text"]


def test_later_explicit_establish_is_valid_without_promoting_nearby_claims():
    established = _decision(
        _relation_fact(
            "A mason cut the bridge cable.",
            "bridge cable",
            "mason cut",
            "actor_attribution",
            ["mason cut the bridge cable"],
        ),
    )
    assert audit_narration_against_decision(
        "A mason cut the bridge cable.", decision=established
    )["hard_valid"]
    assert not audit_narration_against_decision(
        "A mason cut the bridge railing.", decision=established
    )["hard_valid"]
