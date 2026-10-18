"""PR-BS decision-facing answer recipe. Deterministic. No model or gameplay calls."""
from __future__ import annotations

import inspect
import json
from pathlib import Path

from game.gm import SYSTEM_PROMPT
from game.gm_resolution_decision import (
    PROVENANCE_PLAYER_HYPOTHESIS,
    ROLE_MAY_INFER,
    ROLE_MUST_PRESERVE_UNCERTAINTY,
    audit_realization_envelope_against_decision,
    build_decision_facing_answer_recipe,
    narration_authority_fields,
)
from game.prompt_context import _provider_mechanical_resolution
from game.resolution_contract import generation_projection

ROOT = Path("artifacts/pr_br_closeout_live_revalidation")
BEFORE = Path("artifacts/pr_bs_decision_facing_answer_recipe/payload_before.json")

USEFUL_A1 = (
    "The split wooden yoke and the torn leather hanger could be consistent with significant stress or force."
)
UNGROUNDED_A1 = "The visible support failures could be consistent with significant stress or force."


def _saved(name: str) -> dict:
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def _resolution(saved: dict) -> dict:
    return {
        "kind": saved["contract"].get("operation"),
        "metadata": {
            "resolution_contract": saved["contract"],
            "gm_resolution_decision": saved["decision"],
            "emission_debug": {"trace_only": True},
        },
    }


def _audit(saved: dict, narration: str, declared: list | None):
    corpus = "\n".join(saved["scene"].get("visible_facts") or [])
    return audit_realization_envelope_against_decision(
        narration=narration,
        declared_claims=declared,
        decision=saved["decision"],
        authored_corpus=corpus,
    )


def _reasons(audit: dict) -> list[str]:
    reasons: list[str] = []
    for row in audit.get("violations") or []:
        reasons.extend(str(item) for item in (row.get("reason_codes") or []))
    return reasons


def _chars(value) -> int:
    return len(json.dumps(value, ensure_ascii=False, default=str))


def _authority_slice(saved: dict) -> dict:
    resolution = _resolution(saved)
    fields = narration_authority_fields(resolution)
    mechanical = _provider_mechanical_resolution(resolution)
    instructions = [
        "ANSWER RECIPE: Follow decision_facing_answer_recipe for this turn. "
        "It projects gm_resolution_decision and does not add authority. "
        "The decision wins if they disagree."
    ]
    user = {
        "instructions": instructions,
        "resolution_contract": fields.get("resolution_contract"),
        "gm_resolution_decision": fields.get("gm_resolution_decision"),
        "decision_facing_answer_recipe": fields.get("decision_facing_answer_recipe"),
        "mechanical_resolution": {
            "metadata": mechanical.get("metadata"),
        },
    }
    recipe = fields.get("decision_facing_answer_recipe") or {}
    decision = fields.get("gm_resolution_decision") or {}
    contract = fields.get("resolution_contract") or {}
    return {
        "system_prompt_chars": len(SYSTEM_PROMPT),
        "instructions_chars": _chars(instructions),
        "response_policy_chars": 0,
        "turn_packet_chars": 0,
        "decision_contract_claim_projection_chars": _chars(
            {"resolution_contract": contract, "gm_resolution_decision": decision}
        ),
        "answer_recipe_chars": _chars(recipe),
        "mechanical_resolution_chars": _chars({"metadata": mechanical.get("metadata")}),
        "user_authority_slice_chars": _chars(user),
        "total_provider_facing_chars": len(SYSTEM_PROMPT) + _chars(user),
        "recipe_key_count": 1 if recipe else 0,
    }


def test_missing_authority_invents_no_permission():
    assert build_decision_facing_answer_recipe(None) is None
    assert build_decision_facing_answer_recipe({}) is None
    assert build_decision_facing_answer_recipe({"outcome_classification": "established_or_retrieved"}) is None
    bare = build_decision_facing_answer_recipe(
        {"contract_id": "rc_bare", "realization_claims": [], "epistemic_acts": []},
        {},
    )
    assert bare is not None
    assert bare["projection_only"] is True
    assert bare["authority_owner"] == "gm_resolution_decision"
    assert bare["permitted_inference"]["allowed"] is False
    assert bare["inference_modality"] == "none"
    assert bare["required_content"] == []
    assert "qualified_possibilities_only" not in json.dumps(bare["permitted_inference"])


def test_recipe_cannot_authorize_new_consequential_content():
    signature = inspect.signature(audit_realization_envelope_against_decision)
    assert "decision_facing_answer_recipe" not in signature.parameters
    saved = _saved("A1_decision_1.json")
    recipe = build_decision_facing_answer_recipe(saved["decision"], saved["contract"])
    assert recipe["projection_only"] is True
    claim_texts = {row.get("text") for row in saved["decision"]["realization_claims"]}
    for row in recipe["required_content"] + recipe["permitted_content"]:
        assert row["text"] in claim_texts
    invented = dict(recipe)
    invented["answer_strategy"] = "Establish that neglect caused the damage."
    audit = _audit(saved, "Neglect caused the split yoke.", [])
    assert audit["hard_valid"] is False
    assert invented["answer_strategy"] not in json.dumps(audit)


def test_a1_recipe_makes_qualified_inference_operational():
    saved = _saved("A1_decision_1.json")
    recipe = build_decision_facing_answer_recipe(saved["decision"], saved["contract"])
    assert recipe is not None
    blob = json.dumps(recipe)
    assert "interpretation" in recipe["requested_answer"]
    assert "What does this damage suggest?" in recipe["requested_answer"]
    assert recipe["permitted_inference"]["allowed"] is True
    assert recipe["permitted_inference"]["qualified_observations"][0]["scope"] == "qualified_possibilities_only"
    assert recipe["permitted_inference"]["qualified_observations"][0]["epistemic_status"] == "inferred"
    assert recipe["inference_modality"] == "possible"
    assert "could, may, or might" in recipe["answer_strategy"]
    for token in ("exact_cause", "actor", "time", "history", "neglect", "harsh_conditions", "gameplay_lead"):
        assert token in recipe["forbidden_upgrades"]
    for slot in ("cause", "actor", "time", "history"):
        assert slot in recipe["unresolved_content"]
    assert "The bell's wooden yoke is split." in blob
    assert "The bell's leather hanger is torn." in blob
    assert "propose only" in recipe["declaration_guidance"]["bounded_inference"]
    assert "authored_world_fact" in recipe["declaration_guidance"]["bounded_inference"]


def test_a1_useful_bounded_inference_passes_and_overreach_stays_rejected():
    saved = _saved("A1_decision_1.json")
    useful = _audit(saved, USEFUL_A1, [])
    assert useful["hard_valid"] is True, _reasons(useful)
    proposed = _audit(
        saved,
        USEFUL_A1,
        [
            {
                "declaration_id": "inf1",
                "declaration_mode": "propose",
                "provenance_requested": "gm_inference",
                "epistemic_status": "inferred",
                "modality": "possible",
                "realization_role": "MAY_INFER",
                "relation_kind": "epistemic_status",
                "text": USEFUL_A1,
            }
        ],
    )
    assert proposed["hard_valid"] is True, _reasons(proposed)
    ungrounded = _audit(saved, UNGROUNDED_A1, [])
    assert ungrounded["hard_valid"] is False
    assert "unsupported_narrator_lead" in _reasons(ungrounded)
    original = json.loads((ROOT / "A1_raw_envelope_attempt_1.json").read_text(encoding="utf-8"))
    envelope = json.loads(original["raw_output"])
    rejected = _audit(saved, envelope["narration"], envelope["declared_claims"])
    assert rejected["hard_valid"] is False
    reasons = _reasons(rejected)
    assert "unauthorized_evidential_relation" in reasons or "unauthorized_declared_claim" in reasons
    assert "unsupported_narrator_lead" in reasons
    cases = {
        "cause": "A sudden pull caused the split yoke.",
        "neglect": "The damage might point to neglect.",
        "harsh_conditions": "This degradation might point to neglect or recent harsh conditions in the chapel belfry.",
        "actor": "Someone cracked the wooden yoke.",
        "history": "The hanger was torn last night.",
        "gameplay_lead": "You might ask the sexton who saw what happened.",
    }
    for label, text in cases.items():
        audit = _audit(saved, text, [])
        assert audit["hard_valid"] is False, label


def test_b1_recipe_exposes_mundane_dialogue_without_new_authority():
    saved = _saved("B1_decision_4.json")
    recipe = build_decision_facing_answer_recipe(saved["decision"], saved["contract"])
    assert recipe["permitted_inference"]["allowed"] is False
    assert recipe["inference_modality"] == "none"
    assert "baker" in recipe["requested_answer"].lower()
    assert "ordinary dialogue" in recipe["answer_strategy"]
    assert "authored world truth" in recipe["incidental_improvisation_guidance"]
    assert "durable_preference_without_authorized_claim" in recipe["forbidden_upgrades"]
    assert "generated_dialogue_as_authored_world_fact" in recipe["forbidden_upgrades"]
    guidance = recipe["declaration_guidance"]["ordinary_incidental_expression"]
    assert "not authored world truth" in guidance
    assert "refusal" in guidance


def test_b1_dialogue_passes_and_durable_preference_declaration_fails():
    saved = _saved("B1_decision_4.json")
    dialogue = (
        '"I\'m not comfortable saying which loaf I keep for myself," '
        "the baker replies cautiously, their gaze flickering briefly away."
    )
    assert _audit(saved, dialogue, [])["hard_valid"] is True
    mannerism = (
        'The baker shrugs and brushes flour from one sleeve. "I would rather not say which loaf I keep."'
    )
    assert _audit(saved, mannerism, [])["hard_valid"] is True
    authored_speech = _audit(
        saved,
        dialogue,
        [
            {
                "declaration_id": "refusal",
                "declaration_mode": "realize",
                "provenance_requested": "authored_world_fact",
                "epistemic_status": "established",
                "modality": "established",
                "realization_role": "MUST_STATE",
                "relation_kind": "ordinary_predicate",
                "text": "The baker refuses to reveal which loaf they usually keep for themselves.",
            }
        ],
    )
    assert authored_speech["hard_valid"] is False
    assert "unauthorized_declared_claim" in _reasons(authored_speech)
    preference = _audit(
        saved,
        "The baker always keeps the rye loaf for herself.",
        [
            {
                "declaration_id": "pref",
                "declaration_mode": "realize",
                "provenance_requested": "authored_world_fact",
                "epistemic_status": "established",
                "modality": "established",
                "relation_kind": "ordinary_predicate",
                "text": "The baker always keeps the rye loaf for herself.",
            }
        ],
    )
    assert preference["hard_valid"] is False
    assert "unauthorized_declared_claim" in _reasons(preference)


def test_hypothesis_ceiling_is_projected_not_raised():
    decision = {
        "contract_id": "rc_hyp",
        "realization_claims": [
            {
                "claim_id": "rc_obs",
                "text": "The bell's wooden yoke is split.",
                "provenance": "authored_world_fact",
                "epistemic_status": "established",
                "modality": "",
                "realization_role": "MUST_STATE",
                "relation_kind": "ordinary_predicate",
                "premise_claim_ids": [],
            },
            {
                "claim_id": "rc_hyp",
                "text": "The yoke was cut on purpose.",
                "provenance": PROVENANCE_PLAYER_HYPOTHESIS,
                "epistemic_status": "hypothesis",
                "modality": "hypothetical",
                "realization_role": ROLE_MAY_INFER,
                "relation_kind": "epistemic_status",
                "premise_claim_ids": ["rc_obs"],
            },
        ],
        "epistemic_acts": [
            {
                "act": "leave_unresolved",
                "authority": "observation",
                "semantic_identity": {
                    "epistemic_status": "unresolved",
                    "premise_claim_ids": ["rc_hyp"],
                },
            }
        ],
        "unresolved_qualifiers": ["cause"],
        "realization_claims_note": "",
    }
    # The leave_unresolved act is not itself a realization claim here.
    # Attach the preserve-uncertainty claim the decision builder would emit.
    decision["realization_claims"].append(
        {
            "claim_id": "rc_open",
            "text": "Unresolved consequential slot",
            "provenance": "speculation",
            "epistemic_status": "unresolved",
            "modality": "unresolved",
            "realization_role": ROLE_MUST_PRESERVE_UNCERTAINTY,
            "relation_kind": "epistemic_status",
            "premise_claim_ids": ["rc_hyp"],
        }
    )
    recipe = build_decision_facing_answer_recipe(decision, {"operation": "inspect", "dimensions": ["cause"]})
    assert recipe["permitted_inference"]["qualified_observations"] == []
    assert recipe["inference_modality"] == "hypothetical"
    assert "existing status" in recipe["answer_strategy"]
    projected_infer = recipe["permitted_inference"]["may_infer_claims"]
    assert projected_infer[0]["claim_id"] == "rc_hyp"
    assert projected_infer[0]["epistemic_status"] == "hypothesis"
    assert projected_infer[0]["premise_claim_ids"] == ["rc_obs"]
    assert projected_infer[0]["modality"] == "hypothetical"
    preserved = recipe["declaration_guidance"]["epistemic_claims"]
    assert any(row["claim_id"] == "rc_open" and row["premise_claim_ids"] == ["rc_hyp"] for row in preserved)
    assert "world truth" in recipe["declaration_guidance"]["epistemic_premise"]
    assert "cause" in recipe["unresolved_content"]
    assert recipe["inference_modality"] != "established"


def test_provider_projection_keeps_canonical_authority_and_one_recipe():
    saved = _saved("A1_decision_1.json")
    resolution = _resolution(saved)
    fields = narration_authority_fields(resolution)
    shipped = _provider_mechanical_resolution(resolution)
    assert fields["decision_facing_answer_recipe"]["schema"] == "decision_facing_answer_recipe_v1"
    assert "decision_facing_answer_recipe" not in json.dumps(shipped)
    assert resolution["metadata"]["gm_resolution_decision"]["narration_constraints"]
    assert resolution["metadata"]["gm_resolution_decision"]["epistemic_acts"]
    assert resolution["metadata"]["resolution_contract"]["raw_input"]
    assert resolution["metadata"]["emission_debug"]["trace_only"] is True
    assert shipped["metadata"].get("gm_resolution_decision") is None
    assert shipped["metadata"].get("resolution_contract") is None
    assert shipped["metadata"]["emission_debug"]["trace_only"] is True
    projected = fields["gm_resolution_decision"]
    assert "narration_constraints" not in projected
    assert "epistemic_acts" not in projected
    assert "proposed_facts" not in projected
    assert projected["realization_claims"][0]["text"] == "The bell's wooden yoke is split."
    assert projected["realization_claims"][0]["claim_id"]
    compact_contract = generation_projection(saved["contract"])
    assert fields["resolution_contract"]["constraint"] == compact_contract["constraint"]


def test_authority_slice_does_not_grow():
    before = json.loads(BEFORE.read_text(encoding="utf-8"))
    before_by_label = {row["label"]: row for row in before["cases"]}
    for label, filename in (("A1", "A1_decision_1.json"), ("B1", "B1_decision_4.json")):
        after = _authority_slice(_saved(filename))
        prior = before_by_label[label]
        assert after["recipe_key_count"] == 1
        assert after["answer_recipe_chars"] > 0
        assert after["total_provider_facing_chars"] < prior["total_provider_facing_chars"]
        assert after["mechanical_resolution_chars"] < prior["mechanical_resolution_chars"]
