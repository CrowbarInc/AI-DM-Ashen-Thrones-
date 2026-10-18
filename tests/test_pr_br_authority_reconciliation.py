"""PR-BR preservation, premise ceiling, and interpretation permission.

Deterministic only. Saved envelopes are replayed. No gameplay or model calls.
"""
from __future__ import annotations

import json
from pathlib import Path

from game.gm import _safe_json
from game.gm_resolution_decision import (
    AUTH_WORLD,
    EPISTEMIC_ACT_INFER,
    PROVENANCE_GM_INFERENCE,
    PROVENANCE_PLAYER_HYPOTHESIS,
    ROLE_MUST_PRESERVE_UNCERTAINTY,
    TEMPORAL_PROVENANCE_KEY,
    attach_gm_resolution_decision,
    audit_realization_envelope_against_decision,
    remember_temporal_claims,
    sealed_temporal_claims,
)
from game.immutable_valid_response import (
    accepted_record,
    candidate_entered_structured_envelope_path,
    run_preserve_if_valid,
)
from game.resolution_contract import DIM_INTERPRETATION, construct_resolution_contract

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "artifacts" / "pr_br_small_live_validation"

A1_PLAYER = (
    "I examine the cracked loom beam and bent iron brace closely. "
    "What does this damage suggest?"
)
A2_PLAYER = (
    "So if prolonged strain under heavy stress is what happened to the loom, "
    "what would have caused that strain?"
)
BEAM = "The wooden loom beam is cracked."
BRACE = "The loom's iron brace is bent."
A1_FORBIDDEN = (
    "forceful impact",
    "prolonged strain",
    "rough handling",
    "unless repaired",
)


def _scene(scene_id: str, *facts: str) -> dict:
    return {"scene": {"id": scene_id, "visible_facts": list(facts), "exits": []}}


def _hypothesis(text: str) -> dict:
    return {
        "text": text,
        "semantic_identity": {"epistemic_status": "hypothesis", "relation_kind": "epistemic_status"},
        "provenance": PROVENANCE_PLAYER_HYPOTHESIS,
        "authority": "observation",
        "epistemic_status": "hypothesis",
        "relation_kind": "epistemic_status",
        "authorized": True,
    }


def _session(scene_id: str, *hypotheses: str, turn: int = 1) -> dict:
    record = {
        "version": 1,
        "gm_inferences": [],
        "player_hypotheses": [_hypothesis(text) for text in hypotheses],
        "accepted_incidentals": [],
        "rejected_consequential": [],
    }
    return {
        "active_scene_id": scene_id,
        "turn_counter": turn,
        TEMPORAL_PROVENANCE_KEY: record,
    }


def _prepare(player: str, scene_id: str, facts: tuple[str, ...], session: dict | None = None):
    session = session or _session(scene_id)
    contract = construct_resolution_contract(
        player_text=player,
        session=session,
        scene_id=scene_id,
        canonical_referents=[],
    )
    scene = _scene(scene_id, *facts)
    resolution = {"kind": "investigate", "metadata": {"resolution_contract": contract.as_dict()}}
    attach_gm_resolution_decision(resolution, session=session, scene=scene, world={})
    return contract, resolution, scene, session


def _decision(resolution: dict) -> dict:
    return resolution["metadata"]["gm_resolution_decision"]


def _claims(resolution: dict) -> list[dict]:
    return list(_decision(resolution).get("realization_claims") or [])


def _envelope(payload: dict) -> dict:
    return _safe_json(json.dumps(payload), require_structured_claims=True)


def _saved(name: str) -> dict:
    return json.loads((EVIDENCE / name).read_text(encoding="utf-8"))


def _commit(session: dict, sealed: dict, player: str) -> dict:
    accepted, rejected = sealed_temporal_claims(sealed, player_text=player)
    return remember_temporal_claims(
        session,
        claims=[*accepted, *rejected],
        scene_id=str(session.get("active_scene_id") or ""),
        source_turn=session.get("turn_counter") if isinstance(session.get("turn_counter"), int) else None,
    )


def _realize(claim: dict, text: str | None = None, **extra) -> dict:
    return {
        "declaration_id": extra.pop("declaration_id", claim.get("claim_id") or "d"),
        "declaration_mode": "realize",
        "source_claim_id": claim.get("claim_id") or "",
        "text": text if text is not None else claim.get("text") or "",
        "relation_kind": extra.pop("relation_kind", claim.get("relation_kind") or "epistemic_status"),
        "modality": extra.pop("modality", "unresolved"),
        "epistemic_status": extra.pop("epistemic_status", "unresolved"),
        "provenance_requested": extra.pop("provenance_requested", "speculation"),
        "realization_role": extra.pop("realization_role", ROLE_MUST_PRESERVE_UNCERTAINTY),
        "premise_claim_ids": extra.pop("premise_claim_ids", list(claim.get("premise_claim_ids") or [])),
        **extra,
    }


def _unresolved(resolution: dict) -> dict:
    rows = [row for row in _claims(resolution) if row.get("realization_role") == ROLE_MUST_PRESERVE_UNCERTAINTY]
    assert rows, _claims(resolution)
    return rows[0]


def _world_facts(resolution: dict) -> list[dict]:
    return [row for row in _claims(resolution) if row.get("authority") == AUTH_WORLD and row.get("text")]


def test_demonstrative_semantic_noun_requests_interpretation_and_infer():
    contract, resolution, _scene_row, _session_row = _prepare(A1_PLAYER, "loom_workshop", (BEAM, BRACE))
    assert contract.operation == "inspect"
    assert DIM_INTERPRETATION in contract.dimensions
    infer = [
        act
        for act in _decision(resolution)["epistemic_acts"]
        if act.get("act") == EPISTEMIC_ACT_INFER
    ]
    assert any((act.get("semantic_identity") or {}).get("scope") == "qualified_possibilities_only" for act in infer)
    for phrase in (
        "What does this damage suggest?",
        "What does this condition suggest?",
        "What does the damage suggest?",
        "What does this suggest?",
        "What might this mean?",
        "What can I infer?",
        "Does this point to anything?",
        "What might this tell me?",
    ):
        follow = construct_resolution_contract(
            player_text=phrase,
            session={"active_scene_id": "loom_workshop", "turn_counter": 1},
            scene_id="loom_workshop",
            canonical_referents=[],
        )
        assert DIM_INTERPRETATION in follow.dimensions, phrase


def test_saved_a1_rejection_uses_authorized_fallback_not_bounded_keep():
    contract, resolution, scene, session = _prepare(A1_PLAYER, "loom_workshop", (BEAM, BRACE))
    assert contract.operation == "inspect"
    assert DIM_INTERPRETATION in contract.dimensions
    initial = _envelope(_saved("A1_raw_envelope_attempt_1.json"))
    retry = _envelope(_saved("A1_raw_envelope_attempt_2.json"))
    assert candidate_entered_structured_envelope_path(initial)
    assert candidate_entered_structured_envelope_path(retry)

    sealed = run_preserve_if_valid(
        initial,
        regenerate=lambda _feedback: retry,
        resolution=resolution,
        player_text=A1_PLAYER,
        scene=scene,
        world={},
        session=session,
    )
    review = sealed["metadata"]["decision_review"]
    assert review["attempt_1"]["reasons"]
    assert review["acceptance"]["why"] != "bounded_sentence_preservation"
    assert review["acceptance"]["why"] in {
        "authorized_observation",
        "safe_nonresolution",
        "regeneration_hard_valid",
    }
    text = sealed["player_facing_text"]
    lowered = text.lower()
    for phrase in A1_FORBIDDEN:
        assert phrase not in lowered, phrase
    record = accepted_record(sealed)
    assert record["immutable"] is True
    assert record["text"] == text
    temporal = _commit(session, sealed, A1_PLAYER)
    assert temporal["gm_inferences"] == []


def test_valid_a1_inference_seals_into_gm_inferences_without_world_truth():
    contract, resolution, scene, session = _prepare(A1_PLAYER, "loom_workshop", (BEAM, BRACE))
    assert contract.operation == "inspect"
    assert any(
        act.get("act") == EPISTEMIC_ACT_INFER
        and (act.get("semantic_identity") or {}).get("scope") == "qualified_possibilities_only"
        for act in _decision(resolution)["epistemic_acts"]
    )
    declared = []
    for claim in _world_facts(resolution):
        declared.append(
            _realize(
                claim,
                relation_kind="observation",
                modality="established",
                epistemic_status="established",
                provenance_requested="authored_world_fact",
                realization_role="MUST_STATE",
                premise_claim_ids=[],
            )
        )
    declared.append(
        {
            "declaration_id": "infer_strain",
            "declaration_mode": "propose",
            "source_claim_id": "",
            "text": "Prolonged strain is one possible reading of the damage.",
            "relation_kind": "epistemic_status",
            "modality": "possible",
            "epistemic_status": "possible",
            "provenance_requested": PROVENANCE_GM_INFERENCE,
            "realization_role": "MAY_INFER",
            "premise_claim_ids": [],
        }
    )
    narration = (
        "The wooden loom beam is cracked. The loom's iron brace is bent. "
        "Prolonged strain is one possible reading of the damage."
    )
    sealed = run_preserve_if_valid(
        _envelope({"declared_claims": declared, "narration": narration, "player_facing_text": narration}),
        regenerate=None,
        resolution=resolution,
        player_text=A1_PLAYER,
        scene=scene,
        world={},
        session=session,
    )
    assert sealed["metadata"]["decision_review"]["acceptance"]["why"] == "initial_hard_valid"
    assert sealed["player_facing_text"] == narration
    assert accepted_record(sealed)["text"] == narration
    temporal = _commit(session, sealed, A1_PLAYER)
    inferences = temporal["gm_inferences"]
    assert inferences
    assert any("prolonged strain" in str(row.get("text") or "").lower() for row in inferences)
    assert all(row.get("provenance") == PROVENANCE_GM_INFERENCE for row in inferences)
    assert all(row.get("authority") != AUTH_WORLD for row in inferences)
    assert all("world_truth" not in str(row.get("epistemic_status") or "") for row in inferences)

    repeat = "Prolonged strain is definitely what bent the brace."
    _contract2, resolution2, _scene2, _session2 = _prepare(repeat, "loom_workshop", (BEAM, BRACE), session)
    retained = [
        row
        for row in _claims(resolution2)
        if "prolonged strain" in str(row.get("text") or "").lower()
    ]
    assert retained
    assert all(row.get("provenance") == PROVENANCE_GM_INFERENCE for row in retained)
    assert all(row.get("authority") != AUTH_WORLD for row in retained)
    promotion = audit_realization_envelope_against_decision(
        narration="Prolonged strain bent the brace.",
        declared_claims=[
            _realize(
                retained[0],
                "Prolonged strain bent the brace.",
                relation_kind="causal",
                modality="established",
                epistemic_status="established",
                provenance_requested="authored_world_fact",
                realization_role="MUST_STATE",
                premise_claim_ids=[],
            )
        ],
        decision=_decision(resolution2),
        authored_corpus=f"{BEAM}\n{BRACE}",
    )
    assert not promotion["hard_valid"]


def test_saved_a2_presupposition_does_not_emit():
    session = _session(
        "loom_workshop",
        "prolonged strain under heavy stress happened to the loom",
        turn=2,
    )
    _contract, resolution, scene, session = _prepare(A2_PLAYER, "loom_workshop", (BEAM, BRACE), session)
    initial = _envelope(_saved("A2_raw_envelope_attempt_1.json"))
    retry = _envelope(_saved("A2_raw_envelope_attempt_2.json"))
    sealed = run_preserve_if_valid(
        initial,
        regenerate=lambda _feedback: retry,
        resolution=resolution,
        player_text=A2_PLAYER,
        scene=scene,
        world={},
        session=session,
    )
    review = sealed["metadata"]["decision_review"]
    assert review["acceptance"]["why"] != "bounded_sentence_preservation"
    assert review["acceptance"]["why"] != "regeneration_hard_valid"
    text = sealed["player_facing_text"].lower()
    assert "precise cause of this prolonged strain" not in text
    assert "cause of this prolonged strain" not in text
    assert accepted_record(sealed)["text"] == sealed["player_facing_text"]
    temporal = _commit(session, sealed, A2_PLAYER)
    assert temporal["gm_inferences"] == []
    assert temporal["player_hypotheses"]
    assert all(row.get("epistemic_status") == "hypothesis" for row in temporal["player_hypotheses"])


def _epistemic_case(player: str, scene_id: str, facts: tuple[str, ...], hypothesis: str | None):
    session = _session(scene_id, hypothesis) if hypothesis else _session(scene_id)
    return _prepare(player, scene_id, facts, session)


def _parent_declaration(resolution: dict, text: str, premise_ids: list[str] | None = None) -> dict:
    parent = _unresolved(resolution)
    return _realize(parent, text, premise_claim_ids=premise_ids if premise_ids is not None else list(parent.get("premise_claim_ids") or []))


def test_hypothetical_premise_requires_conditional_realization_and_established_premise_does_not():
    player = "If prolonged strain under heavy stress happened to the loom, what caused that strain?"
    hypothesis = "prolonged strain under heavy stress happened to the loom"
    _contract, resolution, _scene_row, _session_row = _epistemic_case(player, "loom_workshop", (BEAM, BRACE), hypothesis)
    parent = _unresolved(resolution)
    assert parent["premise_claim_ids"]
    bad = "The precise cause of this prolonged strain is not known."
    rejected = audit_realization_envelope_against_decision(
        narration=bad,
        declared_claims=[_parent_declaration(resolution, bad)],
        decision=_decision(resolution),
        authored_corpus=f"{BEAM}\n{BRACE}",
    )
    assert not rejected["hard_valid"]
    reasons = {code for row in rejected["violations"] for code in (row.get("reason_codes") or [])}
    assert "premise_ceiling_exceeded" in reasons or "embedded_premise_unlinked" in reasons
    allowed_text = "If prolonged strain under heavy stress was involved, its cause is not known."
    allowed = audit_realization_envelope_against_decision(
        narration=allowed_text,
        declared_claims=[_parent_declaration(resolution, allowed_text)],
        decision=_decision(resolution),
        authored_corpus=f"{BEAM}\n{BRACE}",
    )
    assert allowed["hard_valid"], allowed

    established_player = "Who ordered the attack?"
    fact = "An attack was ordered."
    _contract_e, resolution_e, _scene_e, _session_e = _epistemic_case(
        established_player, "yard", (fact,), None
    )
    nonconditional = "Who ordered the attack is unknown."
    established = audit_realization_envelope_against_decision(
        narration=nonconditional,
        declared_claims=[_parent_declaration(resolution_e, nonconditional, premise_ids=[])],
        decision=_decision(resolution_e),
        authored_corpus=fact,
    )
    assert established["hard_valid"], established


def test_novel_domains_follow_premise_status_not_vocabulary():
    cases = (
        (
            "yard",
            "If an attack was ordered, who ordered the attack?",
            (),
            "An attack was ordered.",
            "Who ordered the attack is unknown.",
            "If an attack was ordered, who ordered it is not known.",
            True,
        ),
        (
            "yard",
            "Who ordered the attack?",
            ("An attack was ordered.",),
            None,
            "Who ordered the attack is unknown.",
            "Who ordered the attack is unknown.",
            False,
        ),
        (
            "dock",
            "If the shipment was stolen, when was the shipment stolen?",
            (),
            "The shipment was stolen.",
            "When the shipment was stolen is uncertain.",
            "If the shipment was stolen, when it happened is uncertain.",
            True,
        ),
        (
            "river",
            "If the bridge collapsed, why did the bridge collapse?",
            (),
            "The bridge collapsed.",
            "Why the bridge collapsed is unknown.",
            "If the bridge collapsed, why it collapsed is unknown.",
            True,
        ),
        (
            "village",
            "If the well was poisoned, who poisoned the well?",
            (),
            "The well was poisoned.",
            "Who poisoned the well cannot be determined.",
            "If the well was poisoned, who did it cannot be determined.",
            True,
        ),
    )
    for scene_id, player, facts, hypothesis, forbidden, allowed_text, must_reject in cases:
        _contract, resolution, _scene_row, _session_row = _epistemic_case(player, scene_id, facts, hypothesis)
        corpus = "\n".join(facts)
        forbidden_audit = audit_realization_envelope_against_decision(
            narration=forbidden,
            declared_claims=[_parent_declaration(resolution, forbidden)],
            decision=_decision(resolution),
            authored_corpus=corpus,
        )
        if must_reject:
            assert not forbidden_audit["hard_valid"], (scene_id, forbidden_audit)
            reasons = {code for row in forbidden_audit["violations"] for code in (row.get("reason_codes") or [])}
            assert "premise_ceiling_exceeded" in reasons or "embedded_premise_unlinked" in reasons
        else:
            assert forbidden_audit["hard_valid"], (scene_id, forbidden_audit)
        allowed_audit = audit_realization_envelope_against_decision(
            narration=allowed_text,
            declared_claims=[_parent_declaration(resolution, allowed_text)],
            decision=_decision(resolution),
            authored_corpus=corpus,
        )
        assert allowed_audit["hard_valid"], (scene_id, allowed_text, allowed_audit)


def test_orchard_hypothesis_is_not_promoted_when_gm_discusses_a_possible_cause():
    hypothesis = "animal damage in the orchard"
    player = "If animal damage in the orchard is what happened, what caused it?"
    _contract, resolution, scene, session = _epistemic_case(player, "orchard", ("The orchard trees are standing.",), hypothesis)
    bad = "The cause of this animal damage is unknown."
    rejected = audit_realization_envelope_against_decision(
        narration=bad,
        declared_claims=[_parent_declaration(resolution, bad)],
        decision=_decision(resolution),
        authored_corpus="The orchard trees are standing.",
    )
    assert not rejected["hard_valid"]
    allowed_text = "If animal damage in the orchard is what happened, its cause is not known."
    allowed = audit_realization_envelope_against_decision(
        narration=allowed_text,
        declared_claims=[_parent_declaration(resolution, allowed_text)],
        decision=_decision(resolution),
        authored_corpus="The orchard trees are standing.",
    )
    assert allowed["hard_valid"], allowed
    proposal = {
        "declaration_id": "drought",
        "declaration_mode": "propose",
        "source_claim_id": "",
        "text": "Drought is one possibility.",
        "relation_kind": "epistemic_status",
        "modality": "possible",
        "epistemic_status": "possible",
        "provenance_requested": PROVENANCE_GM_INFERENCE,
        "realization_role": "MAY_INFER",
        "premise_claim_ids": [],
    }
    narration = "If animal damage in the orchard is what happened, its cause is not known. Drought is one possibility."
    sealed = run_preserve_if_valid(
        _envelope(
            {
                "declared_claims": [_parent_declaration(resolution, allowed_text), proposal],
                "narration": narration,
                "player_facing_text": narration,
            }
        ),
        regenerate=None,
        resolution=resolution,
        player_text=player,
        scene=scene,
        world={},
        session=session,
    )
    assert sealed["player_facing_text"] == narration
    temporal = _commit(session, sealed, player)
    animal = [row for row in temporal["player_hypotheses"] if "animal damage" in str(row.get("text") or "")]
    assert animal
    assert all(row.get("epistemic_status") == "hypothesis" for row in animal)
    assert all(row.get("provenance") == PROVENANCE_PLAYER_HYPOTHESIS for row in animal)
    assert all("animal damage" not in str(row.get("text") or "").lower() or row.get("authority") != AUTH_WORLD for row in temporal["gm_inferences"])
    assert scene["scene"]["visible_facts"] == ["The orchard trees are standing."]


def test_structured_path_does_not_salvage_a_valid_sentence_with_bounded_keep():
    _contract, resolution, scene, session = _prepare(A1_PLAYER, "loom_workshop", (BEAM, BRACE))
    narration = "The wooden loom beam is cracked. A hidden guild ordered the damage yesterday."
    declared = [
        _realize(
            claim,
            relation_kind="observation",
            modality="established",
            epistemic_status="established",
            provenance_requested="authored_world_fact",
            realization_role="MUST_STATE",
            premise_claim_ids=[],
        )
        for claim in _world_facts(resolution)
        if claim["text"] == BEAM
    ]
    initial = _envelope({"declared_claims": declared, "narration": narration, "player_facing_text": narration})
    retry = _envelope(
        {
            "declared_claims": [],
            "narration": "A hidden guild ordered the damage yesterday.",
            "player_facing_text": "A hidden guild ordered the damage yesterday.",
        }
    )
    assert candidate_entered_structured_envelope_path(initial)
    sealed = run_preserve_if_valid(
        initial,
        regenerate=lambda _feedback: retry,
        resolution=resolution,
        player_text=A1_PLAYER,
        scene=scene,
        world={},
        session=session,
    )
    assert sealed["metadata"]["decision_review"]["acceptance"]["why"] != "bounded_sentence_preservation"
    assert "hidden guild" not in sealed["player_facing_text"].lower()
    assert accepted_record(sealed)["text"] == sealed["player_facing_text"]


def test_incidental_structured_narration_can_seal_without_a_consequential_claim():
    _contract, resolution, scene, session = _prepare(
        "I look around the workshop.",
        "loom_workshop",
        (BEAM, BRACE),
    )
    narration = "Dust hangs in the still air."
    sealed = run_preserve_if_valid(
        _envelope({"declared_claims": [], "narration": narration, "player_facing_text": narration}),
        regenerate=None,
        resolution=resolution,
        player_text="I look around the workshop.",
        scene=scene,
        world={},
        session=session,
    )
    assert sealed["player_facing_text"] == narration
    assert sealed["metadata"]["decision_review"]["acceptance"]["why"] == "initial_hard_valid"


def test_prestructured_candidate_is_not_classified_as_structured_path():
    assert not candidate_entered_structured_envelope_path(
        {"player_facing_text": "The clay kiln is cold.", "metadata": {}}
    )
    assert candidate_entered_structured_envelope_path(
        {
            "player_facing_text": BEAM,
            "metadata": {
                "output_form": "structured",
                "realization_envelope": {"declared_claims": [], "structured_contract_present": True},
            },
        }
    )


def test_production_composition_traverses_contract_decision_seal_and_temporal_commit():
    """Player text through contract, decision, stubbed envelope, seal, and temporal commit."""
    contract, resolution, scene, session = _prepare(A1_PLAYER, "loom_workshop", (BEAM, BRACE))
    assert contract.operation == "inspect"
    assert DIM_INTERPRETATION in contract.dimensions
    decision = _decision(resolution)
    assert decision["contract_id"] == contract.contract_id
    assert any(act.get("act") == EPISTEMIC_ACT_INFER for act in decision["epistemic_acts"])
    calls = {"retry": 0}

    def _retry(_feedback: str) -> dict:
        calls["retry"] += 1
        return _envelope(_saved("A1_raw_envelope_attempt_2.json"))

    sealed = run_preserve_if_valid(
        _envelope(_saved("A1_raw_envelope_attempt_1.json")),
        regenerate=_retry,
        resolution=resolution,
        player_text=A1_PLAYER,
        scene=scene,
        world={},
        session=session,
    )
    assert calls["retry"] == 1
    assert sealed["metadata"]["decision_review"]["acceptance"]["why"] in {
        "authorized_observation",
        "safe_nonresolution",
        "regeneration_hard_valid",
    }
    assert accepted_record(sealed)["text"] == sealed["player_facing_text"]
    temporal = _commit(session, sealed, A1_PLAYER)
    assert temporal["gm_inferences"] == []
