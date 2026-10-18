"""PR-BR decision-owned realization claims.

Deterministic only. No gameplay/model calls.
"""
from __future__ import annotations

import json
from pathlib import Path

from game.gm_resolution_decision import (
    DECISION_METADATA_KEY,
    TEMPORAL_PROVENANCE_KEY,
    audit_narration_against_decision,
    attach_gm_resolution_decision,
    build_gm_resolution_decision,
    remember_temporal_claims,
)


ROOT = Path(__file__).resolve().parents[1]
TRACE = ROOT / "artifacts" / "pr_br_final_live_validation" / "20261004T035044Z"


def _scene(*facts: object) -> dict:
    return {
        "scene": {
            "id": "novel_claim_lab",
            "summary": "A neutral test scene.",
            "visible_facts": list(facts),
            "exits": [],
        }
    }


def _resolution(raw: str = "I inspect it.", operation: str = "inspect", dimensions: list[str] | None = None) -> dict:
    return {
        "kind": operation,
        "metadata": {
            "resolution_contract": {
                "contract_id": "decision_owned_claims",
                "operation": operation,
                "dimensions": dimensions or ["appearance"],
                "raw_input": raw,
                "conversational_subject": raw,
            }
        },
    }


def _decision(scene: dict, *, session: dict | None = None, resolution: dict | None = None) -> dict:
    res = resolution or _resolution()
    attach_gm_resolution_decision(res, session=session or {}, scene=scene, world={})
    return res["metadata"][DECISION_METADATA_KEY]


def _audit(text: str, decision: dict, scene: dict) -> dict:
    facts = scene["scene"].get("visible_facts") or []
    return audit_narration_against_decision(text, decision=decision, authored_corpus="\n".join(str(f) for f in facts))


def _reasons(audit: dict) -> set[str]:
    return {reason for row in audit["violations"] for reason in row["reason_codes"]}


def test_decision_contains_realization_claims_for_authored_and_unresolved_slots():
    scene = _scene(
        {
            "text": "The lantern frame is bent.",
            "semantic_identity": {
                "kind": "world_fact",
                "subject": "lantern_frame",
                "subject_aliases": ["lantern frame"],
                "relation": "condition",
                "value": "bent",
                "value_aliases": ["bent"],
                "authority": "world_truth",
            },
        }
    )
    decision = build_gm_resolution_decision(
        resolution=_resolution("What caused the lantern frame to bend?", dimensions=["appearance", "interpretation"]),
        session={},
        scene=scene,
        world={},
    )
    assert decision is not None
    data = decision.as_dict()
    roles = {claim["realization_role"] for claim in data["realization_claims"]}
    assert "MUST_STATE" in roles
    assert "MUST_PRESERVE_UNCERTAINTY" in roles
    assert any(claim["semantic_identity"].get("unresolved_qualifiers") == ["cause"] for claim in data["realization_claims"])


def test_saved_turn1_uncertain_causes_and_negative_evidence_require_claim_ownership():
    text = json.loads((TRACE / "turn_1" / "gm_output.json").read_text())["player_facing_text"]
    scene = _scene(
        {
            "text": "The long iron handle of the bathhouse pump is noticeably bowed.",
            "semantic_identity": {
                "kind": "world_fact",
                "subject": "pump_handle",
                "subject_aliases": ["long iron handle", "handle"],
                "relation": "condition",
                "value": "bowed",
                "value_aliases": ["bowed"],
                "authority": "world_truth",
            },
        },
        {
            "text": "The pivot pin has been sheared through.",
            "semantic_identity": {
                "kind": "world_fact",
                "subject": "pivot_pin",
                "subject_aliases": ["pivot pin", "pin"],
                "relation": "condition",
                "value": "sheared",
                "value_aliases": ["sheared"],
                "authority": "world_truth",
            },
        },
    )
    decision = _decision(scene, resolution=_resolution("What does this damage suggest?", dimensions=["appearance"]))
    audit = _audit(text, decision, scene)
    assert audit["hard_valid"] is False
    assert "unauthorized_negative_evidence" in _reasons(audit)


def test_saved_turn2_player_hypothesis_enters_next_decision_as_ceiling():
    temporal = json.loads((TRACE / "turn_2" / "temporal_provenance_after.json").read_text())
    session = {"active_scene_id": "bathhouse_pump_alcove", TEMPORAL_PROVENANCE_KEY: temporal["full_temporal_provenance"]}
    decision = _decision(_scene("The pump handle is bowed."), session=session)
    claims = decision["realization_claims"]
    assert any(claim["provenance"] == "player_hypothesis" for claim in claims)
    assert not any(claim["provenance"] == "player_hypothesis" and claim["authority"] == "world_truth" for claim in claims)


def test_saved_turn3_cause_and_specific_leads_do_not_inherit_authored_observation():
    text = json.loads((TRACE / "turn_3" / "gm_output.json").read_text())["player_facing_text"]
    scene = _scene(
        {
            "text": "The handle is bowed.",
            "semantic_identity": {
                "kind": "world_fact",
                "subject": "handle",
                "subject_aliases": ["handle"],
                "relation": "condition",
                "value": "bowed",
                "value_aliases": ["bowed"],
                "authority": "world_truth",
            },
        },
        {
            "text": "The pin is sheared.",
            "semantic_identity": {
                "kind": "world_fact",
                "subject": "pin",
                "subject_aliases": ["pin"],
                "relation": "condition",
                "value": "sheared",
                "value_aliases": ["sheared"],
                "authority": "world_truth",
            },
        },
    )
    temporal = json.loads((TRACE / "turn_2" / "temporal_provenance_after.json").read_text())
    session = {"active_scene_id": "bathhouse_pump_alcove", TEMPORAL_PROVENANCE_KEY: temporal["full_temporal_provenance"]}
    decision = _decision(scene, session=session, resolution=_resolution("Do we know the cause?", dimensions=["confidence"]))
    audit = _audit(text, decision, scene)
    assert audit["hard_valid"] is False
    reasons = _reasons(audit)
    assert "unauthorized_causal_relation" in reasons or "unauthorized_cause_attribution" in reasons
    assert "unsupported_narrator_lead" in reasons
    causal_rows = [row for row in audit["claim_results"] if row["relation_kind"] == "causal"]
    assert causal_rows
    assert not any(row["authority"] == "world_truth" for row in causal_rows)


def test_saved_turn4_npc_mundane_claim_persists_as_claim_only_not_world_truth():
    text = json.loads((TRACE / "turn_4" / "gm_output.json").read_text())["player_facing_text"]
    decision = _decision(_scene("Nessa is folding towels beside the bench."))
    audit = _audit(text, decision, _scene("Nessa is folding towels beside the bench."))
    assert audit["hard_valid"] is True
    assert any(row["authority"] == "claim_only" for row in audit["claim_results"])
    assert not any("lavender" in row["text"].lower() and row["authority"] == "world_truth" for row in audit["claim_results"])


def test_novel_observation_does_not_authorize_cause_actor_time_absence_or_lead():
    cases = [
        ("The lantern frame is bent.", "A hard impact probably bent the lantern frame.", "unauthorized_causal_relation"),
        ("The orchard gate is open.", "A farmhand must have left the orchard gate open.", "unauthorized_actor_attribution"),
        ("The fountain basin is cracked.", "The basin cracked during the night.", "unauthorized_time_attribution"),
        ("The desk drawer is open.", "Nothing else in the room appears disturbed.", "unauthorized_negative_evidence"),
        ("The wagon wheel is broken.", "The stable hands may know who used the wagon last.", "unsupported_narrator_lead"),
    ]
    for fact, narration, reason in cases:
        scene = _scene(fact)
        audit = _audit(narration, _decision(scene), scene)
        assert audit["hard_valid"] is False, narration
        assert reason in _reasons(audit)


def test_authorized_possible_inference_may_not_strengthen_to_certain_cause():
    scene = _scene("The cart axle is cracked.")
    decision = _decision(scene)
    decision["proposed_facts"].append(
        {
            "text": "Excessive load is a possible cause.",
            "provenance": "gm_inference",
            "authority": "inference",
            "authorized": True,
            "persistence": "do_not_persist",
            "source_ref": "test.candidate_inference",
            "reason_codes": ["explicit_candidate_inference"],
            "semantic_identity": {
                "kind": "world_fact",
                "subject": "excessive_load",
                "subject_aliases": ["excessive load"],
                "relation": "possible_cause",
                "value": "cart axle cracked",
                "value_aliases": ["cracked"],
                "modality": "possible",
            },
        }
    )
    possible = _audit("Excessive load is one possibility.", decision, scene)
    assert possible["hard_valid"] is True, possible
    certain = _audit("Excessive load caused it.", decision, scene)
    assert certain["hard_valid"] is False
    assert "modality_strengthening" in _reasons(certain) or "unauthorized_causal_relation" in _reasons(certain)


def test_player_hypothesis_repetition_does_not_promote_but_explicit_promotion_can():
    scene = _scene(
        {
            "text": "The roof rafters are wet.",
            "semantic_identity": {
                "kind": "world_fact",
                "subject": "roof_rafters",
                "subject_aliases": ["roof", "rafters"],
                "relation": "condition",
                "value": "wet",
                "value_aliases": ["wet"],
                "authority": "world_truth",
            },
        }
    )
    session: dict = {"active_scene_id": "novel_claim_lab"}
    remember_temporal_claims(
        session,
        claims=[
            {
                "text": "Rain damaged the roof.",
                "provenance": "player_hypothesis",
                "authority": "observation",
                "authorized": True,
                "epistemic_status": "hypothesis",
                "semantic_identity": {
                    "subject": "rain",
                    "subject_aliases": ["rain"],
                    "relation": "possible_cause",
                    "value": "roof damage",
                    "value_aliases": ["roof"],
                    "modality": "hypothetical",
                },
            }
        ],
    )
    decision = _decision(scene, session=session)
    assert _audit("The rain damaged the roof.", decision, scene)["hard_valid"] is False

    promoted_scene = _scene(
        *scene["scene"]["visible_facts"],
        {
            "text": "Rain damaged the roof.",
            "semantic_identity": {
                "kind": "world_fact",
                "subject": "rain",
                "subject_aliases": ["rain"],
                "relation": "cause",
                "value": "roof damage",
                "value_aliases": ["roof"],
                "authority": "world_truth",
                "causal_authorized": "true",
            },
        },
    )
    promoted = _decision(promoted_scene, session=session)
    assert _audit("The rain damaged the roof.", promoted, promoted_scene)["hard_valid"] is True
