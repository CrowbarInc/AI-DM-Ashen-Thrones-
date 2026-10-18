"""PR-BR structured one-call realization envelope.

Deterministic only. No gameplay/model calls.
"""
from __future__ import annotations

import json

from game.gm import _safe_json
from game.gm_resolution_decision import (
    AUTH_INFERENCE,
    AUTH_WORLD,
    DECISION_METADATA_KEY,
    PROVENANCE_AUTHORITATIVE,
    PROVENANCE_GM_INFERENCE,
    PROVENANCE_PLAYER_HYPOTHESIS,
    REL_CAUSAL,
    REL_GAMEPLAY_LEAD,
    REL_OBSERVATION,
    ROLE_MAY_INFER,
    ROLE_MUST_STATE,
    STATUS_ESTABLISHED,
    STATUS_HYPOTHESIS,
    STATUS_POSSIBLE,
    audit_realization_envelope_against_decision,
    attach_gm_resolution_decision,
    remember_temporal_claims,
    sealed_temporal_claims,
)
from game.immutable_valid_response import accepted_record, run_preserve_if_valid


def _scene(*facts: object) -> dict:
    return {"scene": {"id": "structured_lab", "visible_facts": list(facts), "exits": []}}


def _resolution(raw: str = "Inspect the beam.", *, dimensions: list[str] | None = None) -> dict:
    return {
        "kind": "inspect",
        "metadata": {
            "resolution_contract": {
                "contract_id": "structured_claim_boundary",
                "operation": "inspect",
                "raw_input": raw,
                "conversational_subject": raw,
                "dimensions": dimensions or ["appearance"],
            }
        },
    }


def _decision(scene: dict, *, dimensions: list[str] | None = None, session: dict | None = None) -> dict:
    res = _resolution(dimensions=dimensions)
    attach_gm_resolution_decision(res, session=session or {}, scene=scene, world={})
    return res["metadata"][DECISION_METADATA_KEY]


def _decl(text: str, *, source_claim_id: str = "", mode: str = "realize", relation: str = REL_OBSERVATION, **extra) -> dict:
    return {
        "declaration_id": extra.pop("declaration_id", text[:8].replace(" ", "_") or "d"),
        "declaration_mode": mode,
        "source_claim_id": source_claim_id,
        "semantic_identity": extra.pop("semantic_identity", {}),
        "provenance_requested": extra.pop("provenance_requested", PROVENANCE_AUTHORITATIVE),
        "epistemic_status": extra.pop("epistemic_status", STATUS_ESTABLISHED),
        "modality": extra.pop("modality", STATUS_ESTABLISHED),
        "realization_role": extra.pop("realization_role", ROLE_MUST_STATE),
        "relation_kind": relation,
        "text": text,
        **extra,
    }


def _audit(decision: dict, declared: list[dict], narration: str) -> dict:
    return audit_realization_envelope_against_decision(
        narration=narration,
        declared_claims=declared,
        decision=decision,
        authored_corpus="\n".join(row["text"] if isinstance(row, dict) else str(row) for row in _scene()["scene"].get("visible_facts", [])),
    )


def test_case_1_authored_only_passes_with_declared_claim() -> None:
    scene = _scene("The beam is cracked.")
    decision = _decision(scene)
    claim = decision["realization_claims"][0]
    out = audit_realization_envelope_against_decision(
        narration="The beam is cracked.",
        declared_claims=[_decl("The beam is cracked.", source_claim_id=claim["claim_id"])],
        decision=decision,
        authored_corpus="The beam is cracked.",
    )
    assert out["hard_valid"] is True
    assert out["declaration_validation"]["accepted_claims"][0]["authority"] == AUTH_WORLD


def test_case_2_authorized_observation_plus_unauthorized_cause_fails_before_sentence_authority() -> None:
    decision = _decision(_scene("The beam is cracked."))
    claim = decision["realization_claims"][0]
    declared = [
        _decl("The beam is cracked.", source_claim_id=claim["claim_id"]),
        _decl(
            "The storm caused the crack.",
            mode="propose",
            relation=REL_CAUSAL,
            semantic_identity={"subject": "storm", "relation": "cause", "value": "beam crack"},
        ),
    ]
    out = audit_realization_envelope_against_decision(
        narration="The beam is cracked from last night's storm.",
        declared_claims=declared,
        decision=decision,
        authored_corpus="The beam is cracked.",
    )
    assert out["hard_valid"] is False
    assert out["narration_validation"] is None
    assert out["declaration_validation"]["rejected_claims"][0]["reason_codes"] == ["proposal_inference_not_permitted"]


def test_case_3_hidden_undeclared_cause_fails_residual_backstop() -> None:
    decision = _decision(_scene("The beam is cracked."))
    claim = decision["realization_claims"][0]
    out = audit_realization_envelope_against_decision(
        narration="The storm cracked the beam.",
        declared_claims=[_decl("The beam is cracked.", source_claim_id=claim["claim_id"])],
        decision=decision,
        authored_corpus="The beam is cracked.",
    )
    assert out["hard_valid"] is False
    assert any("undeclared_consequential_claim" in row["reason_codes"] for row in out["violations"])


def test_case_4_authorized_inference_passes_and_persists_as_gm_inference() -> None:
    decision = _decision(_scene("The cart axle is cracked."), dimensions=["appearance", "interpretation"])
    declared = [
        _decl(
            "Excessive strain is a possible cause.",
            mode="propose",
            relation=REL_CAUSAL,
            provenance_requested=PROVENANCE_GM_INFERENCE,
            epistemic_status=STATUS_POSSIBLE,
            modality=STATUS_POSSIBLE,
            realization_role=ROLE_MAY_INFER,
            semantic_identity={"subject": "excessive strain", "relation": "possible_cause", "value": "cracked axle"},
        )
    ]
    out = audit_realization_envelope_against_decision(
        narration="Excessive strain is one possibility.",
        declared_claims=declared,
        decision=decision,
        authored_corpus="The cart axle is cracked.",
    )
    assert out["hard_valid"] is True
    accepted = out["declaration_validation"]["accepted_claims"][0]
    assert accepted["provenance"] == PROVENANCE_GM_INFERENCE
    assert accepted["authority"] == AUTH_INFERENCE


def test_case_5_modality_strengthening_fails() -> None:
    decision = _decision(_scene("The axle is cracked."), dimensions=["appearance", "interpretation"])
    declared = [
        _decl(
            "Excessive strain caused it.",
            mode="propose",
            relation=REL_CAUSAL,
            semantic_identity={"subject": "excessive strain", "relation": "cause", "value": "cracked axle"},
        )
    ]
    out = audit_realization_envelope_against_decision(
        narration="Excessive strain caused it.",
        declared_claims=declared,
        decision=decision,
        authored_corpus="The axle is cracked.",
    )
    assert out["hard_valid"] is False
    assert set(out["violations"][0]["reason_codes"]) & {"proposal_modality_strengthening", "proposal_requested_world_truth"}


def test_cases_6_and_7_player_hypothesis_needs_explicit_promotion() -> None:
    session: dict = {"active_scene_id": "structured_lab"}
    remember_temporal_claims(
        session,
        claims=[
            {
                "text": "Sabotage caused the damage.",
                "provenance": PROVENANCE_PLAYER_HYPOTHESIS,
                "authority": "observation",
                "authorized": True,
                "epistemic_status": STATUS_HYPOTHESIS,
                "semantic_identity": {"subject": "sabotage", "relation": "possible_cause", "value": "damage"},
            }
        ],
    )
    decision = _decision(_scene("The hinge is broken."), session=session)
    hyp = next(row for row in decision["realization_claims"] if row["provenance"] == PROVENANCE_PLAYER_HYPOTHESIS)
    rejected = audit_realization_envelope_against_decision(
        narration="Sabotage caused the damage.",
        declared_claims=[_decl("Sabotage caused the damage.", source_claim_id=hyp["claim_id"], relation=REL_CAUSAL)],
        decision=decision,
        authored_corpus="The hinge is broken.",
    )
    assert rejected["hard_valid"] is False
    assert "modality_strengthening" in rejected["violations"][0]["reason_codes"]

    promoted_scene = _scene(
        {
            "text": "Sabotage caused the damage.",
            "semantic_identity": {
                "subject": "sabotage",
                "subject_aliases": ["sabotage"],
                "relation": "cause",
                "value": "damage",
                "value_aliases": ["damage"],
            },
        }
    )
    promoted_decision = _decision(promoted_scene, session=session)
    promoted = audit_realization_envelope_against_decision(
        narration="Sabotage caused the damage.",
        declared_claims=[_decl("Sabotage caused the damage.", source_claim_id=promoted_decision["realization_claims"][0]["claim_id"], relation=REL_CAUSAL)],
        decision=promoted_decision,
        authored_corpus="Sabotage caused the damage.",
    )
    assert promoted["hard_valid"] is True


def test_cases_8_and_9_negative_evidence_and_specific_lead_require_ownership() -> None:
    decision = _decision(_scene("The dock gate is bent."), dimensions=["appearance", "interpretation"])
    for text, relation in (
        ("There are no footprints.", "evidential"),
        ("Dockworkers may know the culprit.", REL_GAMEPLAY_LEAD),
    ):
        out = audit_realization_envelope_against_decision(
            narration=text,
            declared_claims=[_decl(text, mode="propose", relation=relation, modality=STATUS_POSSIBLE, epistemic_status=STATUS_POSSIBLE)],
            decision=decision,
            authored_corpus="The dock gate is bent.",
        )
        assert out["hard_valid"] is False
        assert out["narration_validation"] is None


def test_cases_10_and_11_incidental_freedom_and_undeclared_consequential_npc_claim() -> None:
    decision = _decision(_scene("Nessa folds towels beside the bench."))
    mundane = audit_realization_envelope_against_decision(
        narration="Nessa folds the towel lengthwise and says she prefers lavender soap.",
        declared_claims=[],
        decision=decision,
        authored_corpus="Nessa folds towels beside the bench.",
    )
    assert mundane["hard_valid"] is True

    accusation = audit_realization_envelope_against_decision(
        narration="Nessa folds the towel lengthwise and says the steward poisoned the well.",
        declared_claims=[],
        decision=decision,
        authored_corpus="Nessa folds towels beside the bench.",
    )
    assert accusation["hard_valid"] is False


def test_case_12_malformed_envelope_rejected_without_json_leakage() -> None:
    gm = _safe_json('{"declared_claims": [{"text": 12}], "narration": ""}')
    assert gm["player_facing_text"] == ""
    assert gm["metadata"]["structured_output_rejected"] is True


def test_case_13_retry_uses_structured_envelope_again_and_second_attempt_seals() -> None:
    scene = _scene("The beam is cracked.")
    resolution = _resolution()
    attach_gm_resolution_decision(resolution, session={}, scene=scene, world={})
    first = _safe_json(
        json.dumps(
            {
                "declared_claims": [
                    _decl("The storm caused the crack.", mode="propose", relation=REL_CAUSAL),
                ],
                "narration": "The storm caused the crack.",
            }
        )
    )
    claim_id = resolution["metadata"][DECISION_METADATA_KEY]["realization_claims"][0]["claim_id"]

    def _regen(_feedback: str) -> dict:
        assert "declared_claims plus narration" in _feedback
        return _safe_json(
            json.dumps(
                {
                    "declared_claims": [_decl("The beam is cracked.", source_claim_id=claim_id)],
                    "narration": "The beam is cracked.",
                }
            )
        )

    sealed = run_preserve_if_valid(
        first,
        regenerate=_regen,
        resolution=resolution,
        player_text="Inspect the beam.",
        scene=scene,
        world={},
        session={},
    )
    record = accepted_record(sealed)
    assert record and record["immutable"] is True
    assert record["attempt"] == 2
    assert sealed["player_facing_text"] == "The beam is cracked."


def test_case_14_temporal_commit_uses_only_accepted_realized_claims() -> None:
    scene = _scene("The cart axle is cracked.")
    resolution = _resolution("What caused it?", dimensions=["appearance", "interpretation"])
    attach_gm_resolution_decision(resolution, session={}, scene=scene, world={})
    gm = _safe_json(
        json.dumps(
            {
                "declared_claims": [
                    _decl(
                        "Excessive strain is a possible cause.",
                        mode="propose",
                        relation=REL_CAUSAL,
                        provenance_requested=PROVENANCE_GM_INFERENCE,
                        epistemic_status=STATUS_POSSIBLE,
                        modality=STATUS_POSSIBLE,
                        realization_role=ROLE_MAY_INFER,
                        semantic_identity={"subject": "excessive strain", "relation": "possible_cause", "value": "cracked axle"},
                    ),
                    _decl("There are no footprints.", mode="propose", relation="evidential", modality=STATUS_POSSIBLE, epistemic_status=STATUS_POSSIBLE),
                ],
                "narration": "Excessive strain is one possibility.",
            }
        )
    )
    # First candidate has a rejected declaration, so no accepted temporal claim is sealed.
    rejected = run_preserve_if_valid(gm, regenerate=None, resolution=resolution, player_text="What caused it?", scene=scene, world={}, session={})
    accepted, rejected_claims = sealed_temporal_claims(rejected)
    assert not any(row.get("text") == "There are no footprints." for row in accepted)
    assert not any(row.get("authority") == AUTH_WORLD for row in accepted)
    assert rejected_claims or accepted == []
