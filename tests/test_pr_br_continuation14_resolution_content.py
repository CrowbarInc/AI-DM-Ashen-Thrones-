"""Resolution-content preservation. No paid inference.

Continuation 13's six recorded turns are replayed from their player lines and
the candidates that generation and emission actually produced.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from game.api import app
from game.discourse_state import DISCOURSE_FOCUS_KEY
from game.interpretation_proposal import (
    SOURCE_FAST_PATH,
    SOURCE_MODEL,
    InterpretationProposal,
    proposal_from_mapping,
    validate_interpretation_proposal,
)
from game.playability_eval import evaluate_playability
from game.resolution_contract import (
    assess_contract_satisfaction,
    candidate_may_replace,
    construct_resolution_contract,
    enforce_emitted_contract_monotonicity,
    prefer_stronger_resolution,
    remember_satisfied_candidate,
)
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _seed_shared_world


NOTICE = {"type": "object", "id": "notice_board", "label": "Notice board", "aliases": ["notice", "board", "posted notice"], "source": "scene"}
GUARD = {"type": "interlocutor", "id": "gate_guard", "label": "Gate Guard", "aliases": ["guard"], "source": "scene"}

TURN1 = "I walk up to the gate guard and ask him what I have to do before I can pass through tonight."
TURN1_ANSWER = '"You\'ll need to report to him for clearance before passing through," the gate guard says.'
TURN1_IDENTITY = 'Gate Guard mutters, "Word is, captain Thoran commands the gate watch tonight."'
TURN2 = "And how long has that been the case?"
TURN2_ANSWER = '"I can\'t say exactly how long," the gate guard replies. "Captain Thoran only took command tonight, as far as I know."'
TURN2_INABILITY = 'Gate Guard says, "I cannot say how recently that was."'
TURN3 = "I read the notice board from top to bottom."
TURN3_ANSWER = (
    "The notice board bears a series of official postings. At the top, new taxes impose added levies. "
    "Below are curfew rules. A warning about a missing patrol is pinned there."
)
TURN4 = "What do people come to that board for?"
TURN4_ANSWER = (
    "People come to the notice board to see official postings: taxes, curfew, and patrol warnings, "
    "so they stay informed about changes in law, enforcement, and safety."
)
TURN4_CLUE = "The missing patrol was last seen taking the northwest mud track past the crates."
TURN5 = "Then I'll do the thing he said."
TURN5_CLARIFICATION = "The requested action cannot be completed here; another route is needed."
TURN6 = "I ask him whether he's sure about that."
TURN6_ANSWER = 'The gate guard mutters, "If you want to pass tonight, it\'s best to take that as certain."'
TURN6_IDENTITY = "Captain Thoran commands the gate watch tonight."


def _focus(**slots):
    focus = {
        "version": 1,
        "scene_id": "frontier_gate",
        "active_interlocutor": {"id": "gate_guard", "label": "Gate Guard", "kind": "interlocutor"},
        "active_claim": None,
        "active_actionable_lead": None,
        "active_inspected": None,
        "last_attempted_action": None,
    }
    focus.update(slots)
    return {"active_scene_id": "frontier_gate", "turn_counter": 3, DISCOURSE_FOCUS_KEY: focus}


def _contract(text, session=None, **kwargs):
    return construct_resolution_contract(
        player_text=text,
        session=session if session is not None else _focus(),
        scene_id="frontier_gate",
        canonical_referents=[NOTICE, GUARD],
        resolution={"social": {"npc_id": "gate_guard", "npc_name": "Gate Guard"}},
        **kwargs,
    )


def _resolution(contract):
    return {
        "kind": "question",
        "prompt": contract.raw_input,
        "social": {"npc_id": "gate_guard", "npc_name": "Gate Guard", "npc_reply_expected": True},
        "metadata": {
            "resolution_contract": contract.as_dict(),
            "emission_debug": {
                "speaker_selection_contract": {
                    "primary_speaker_id": "gate_guard",
                    "primary_speaker_name": "Gate Guard",
                    "allowed_speaker_ids": ["gate_guard"],
                    "continuity_locked": True,
                    "speaker_switch_allowed": False,
                    "generic_fallback_forbidden": True,
                }
            },
        },
    }


def _claim_focus():
    return _focus(
        active_claim={
            "id": "emitted_5d3beeb7c6",
            "label": "Word is, captain Thoran commands the gate watch tonight.",
            "kind": "claim",
        }
    )


def test_recorded_turn_1_keeps_the_procedure():
    contract = _contract(TURN1)
    assert contract.operation == "ask"
    assert contract.dimension == "next_step"
    assert contract.interlocutor_id == "gate_guard"
    resolution = _resolution(contract)
    assert assess_contract_satisfaction(TURN1_ANSWER, contract.as_dict())["status"] == "satisfied"
    assert assess_contract_satisfaction(TURN1_IDENTITY, contract.as_dict())["status"] == "unsatisfied"
    kept, info = prefer_stronger_resolution(TURN1_ANSWER, TURN1_IDENTITY, resolution)
    assert "clearance" in kept.lower()
    assert info["downgrade_rejected"] is True
    superset = TURN1_ANSWER + " He commands the gate watch tonight."
    richer, richer_info = prefer_stronger_resolution(TURN1_ANSWER, superset, resolution)
    assert "clearance" in richer.lower() and "commands" in richer.lower()
    assert richer_info["downgrade_rejected"] is False
    gm = {"player_facing_text": TURN1_ANSWER, "metadata": {}}
    remember_satisfied_candidate(gm, TURN1_ANSWER, resolution)
    gm["player_facing_text"] = TURN1_IDENTITY
    enforce_emitted_contract_monotonicity(gm, resolution)
    assert "clearance" in gm["player_facing_text"].lower()
    assert gm["metadata"]["emission_debug"]["final_selected_candidate"]


def test_recorded_turn_2_emits_the_stronger_temporal_answer():
    contract = _contract(TURN2, _claim_focus())
    assert contract.dimension == "time"
    resolution = _resolution(contract)
    assert assess_contract_satisfaction(TURN2_ANSWER, contract.as_dict())["status"] == "satisfied"
    assert assess_contract_satisfaction(TURN2_INABILITY, contract.as_dict())["status"] == "legitimate_nonresolution"
    gm = {"player_facing_text": TURN2_ANSWER, "metadata": {}}
    remember_satisfied_candidate(gm, TURN2_ANSWER, resolution)
    gm["player_facing_text"] = TURN2_INABILITY
    enforce_emitted_contract_monotonicity(gm, resolution)
    visible = gm["player_facing_text"].lower()
    assert "tonight" in visible
    assert "cannot say how recently" not in visible
    assert gm["metadata"]["emission_debug"]["best_safe_candidate"].lower().startswith('"i can\'t say') or "tonight" in gm["metadata"]["emission_debug"]["best_safe_candidate"].lower()


def test_recorded_turn_3_inspection_is_not_regressed():
    contract = _contract(TURN3, normalized_action={"type": "investigate", "target_id": "notice_board"})
    assert contract.operation == "inspect"
    assert "notice" in str(contract.target_ref.id_or_text or "").lower()
    resolution = _resolution(contract)
    assert assess_contract_satisfaction(TURN3_ANSWER, contract.as_dict())["status"] == "satisfied"
    kept, _info = prefer_stronger_resolution(TURN3_ANSWER, TURN4_CLUE, resolution)
    assert "curfew" in kept.lower() or "tax" in kept.lower()
    gm = {"player_facing_text": TURN3_ANSWER, "metadata": {}}
    remember_satisfied_candidate(gm, TURN3_ANSWER, resolution)
    gm["player_facing_text"] = TURN4_CLUE
    enforce_emitted_contract_monotonicity(gm, resolution)
    assert "curfew" in gm["player_facing_text"].lower() or "tax" in gm["player_facing_text"].lower()


def test_recorded_turn_4_keeps_use_rather_than_the_clue():
    contract = _contract(TURN4, _focus(active_inspected={"id": "notice_board", "label": "Notice board", "kind": "object"}))
    assert contract.dimension == "use"
    assert contract.operation == "ask"
    assert "notice" in str(contract.target_ref.id_or_text or "").lower()
    resolution = _resolution(contract)
    assert assess_contract_satisfaction(TURN4_ANSWER, contract.as_dict())["status"] == "satisfied"
    assert assess_contract_satisfaction(TURN4_CLUE, contract.as_dict())["status"] == "unsatisfied"
    kept, info = prefer_stronger_resolution(TURN4_ANSWER, TURN4_CLUE, resolution)
    assert "official" in kept.lower() or "informed" in kept.lower()
    assert "mud track" not in kept.lower()
    assert info["downgrade_reason"] == "lower_satisfaction_rank"
    both = TURN4_ANSWER + " " + TURN4_CLUE
    richer, _info = prefer_stronger_resolution(TURN4_ANSWER, both, resolution)
    assert "informed" in richer.lower() or "official" in richer.lower()
    assert "mud track" in richer.lower()


def test_recorded_turn_5_does_not_revive_a_stale_answer():
    procedure = _contract(TURN1)
    procedure_resolution = _resolution(procedure)
    gm = {"player_facing_text": TURN1_ANSWER, "metadata": {}}
    remember_satisfied_candidate(gm, TURN1_ANSWER, procedure_resolution)
    action = _contract(TURN5)
    assert action.operation == "act"
    assert action.dimension is None
    action_resolution = _resolution(action)
    gm["player_facing_text"] = TURN5_CLARIFICATION
    enforce_emitted_contract_monotonicity(gm, action_resolution)
    assert "clearance" not in gm["player_facing_text"].lower()
    assert "another route" in gm["player_facing_text"].lower()


def test_recorded_turn_6_confidence_beats_the_underlying_claim():
    contract = _contract(TURN6, _claim_focus())
    assert contract.dimension == "confidence"
    assert contract.interlocutor_id == "gate_guard"
    resolution = _resolution(contract)
    assert assess_contract_satisfaction(TURN6_ANSWER, contract.as_dict())["status"] == "satisfied"
    assert assess_contract_satisfaction(TURN6_IDENTITY, contract.as_dict())["status"] == "unsatisfied"
    kept, _info = prefer_stronger_resolution(TURN6_ANSWER, TURN6_IDENTITY, resolution)
    assert "certain" in kept.lower()
    gm = {"player_facing_text": TURN6_ANSWER, "metadata": {}}
    remember_satisfied_candidate(gm, TURN6_ANSWER, resolution)
    gm["player_facing_text"] = TURN6_IDENTITY
    enforce_emitted_contract_monotonicity(gm, resolution)
    assert "certain" in gm["player_facing_text"].lower()


def test_structural_dimension_variants_and_dimensionless_requests():
    procedure = (
        "What do I have to do to enter?",
        "What's required before they'll let me through?",
    )
    for text in procedure:
        contract = _contract(text)
        assert contract.dimension == "next_step", text
    use = ("What's this used for?", "Why do people use this thing?")
    board = _focus(active_inspected={"id": "notice_board", "label": "Notice board", "kind": "object"})
    for text in use:
        contract = _contract(text, board)
        assert contract.dimension == "use", text
        assert contract.operation == "ask", text
    confidence = ("Are you certain?", "How sure is she?")
    for text in confidence:
        contract = _contract(text, _claim_focus())
        assert contract.dimension == "confidence", text
    timing = ("When did that start?", "How long ago?")
    for text in timing:
        contract = _contract(text, _claim_focus())
        assert contract.dimension == "time", text
    greeting = _contract("I greet the gate guard.")
    rumor = _contract("Any news from the road?")
    assert greeting.dimension is None
    assert rumor.dimension is None
    assert greeting.construction["fast_path_abstained"] is False
    assert rumor.construction["fast_path_abstained"] is False


def test_equal_rank_wrong_dimension_does_not_replace():
    time_contract = _contract("How long ago?", _claim_focus())
    resolution = _resolution(time_contract)
    assert candidate_may_replace("That was earlier tonight.", "She heard it from the runner.", resolution)[0] is False
    use_contract = _contract(TURN4, _focus(active_inspected={"id": "notice_board", "label": "Notice board", "kind": "object"}))
    assert candidate_may_replace(TURN4_ANSWER, TURN4_CLUE, _resolution(use_contract))[0] is False
    confidence = _contract(TURN6, _claim_focus())
    assert candidate_may_replace(TURN6_ANSWER, TURN6_IDENTITY, _resolution(confidence))[0] is False
    procedure = _contract(TURN1)
    assert candidate_may_replace(TURN1_ANSWER, TURN1_IDENTITY, _resolution(procedure))[0] is False


def test_same_dimension_improvement_and_superset_still_replace():
    contract = _contract("How long ago?", _claim_focus())
    resolution = _resolution(contract)
    assert candidate_may_replace("Recently.", "Earlier tonight.", resolution) == (True, "resolution_content_preserved")
    assert candidate_may_replace("Earlier tonight.", "Recently.", resolution)[0] is False
    procedure = _resolution(_contract(TURN1))
    richer = "Report to Captain Thoran for clearance; he commands the gate watch tonight."
    assert candidate_may_replace("Report to Captain Thoran for clearance.", richer, procedure)[0] is True


def test_authority_invalid_coverage_cannot_replace_a_safe_answer():
    contract = _contract(TURN1)
    resolution = _resolution(contract)
    resolution["metadata"]["authority_invalid_candidates"] = ["sealed black writ"]
    unsafe = "You must present the sealed black writ before they let you through."
    kept, info = prefer_stronger_resolution("You need to report to Captain Thoran.", unsafe, resolution)
    assert "report" in kept.lower()
    assert info["downgrade_reason"] == "authority_violation"
    gm = {"player_facing_text": "You need to report to Captain Thoran.", "metadata": {}}
    remember_satisfied_candidate(gm, "You need to report to Captain Thoran.", resolution)
    remember_satisfied_candidate(gm, unsafe, resolution)
    assert "writ" not in gm["metadata"]["emission_debug"]["best_safe_candidate"].lower()
    assert gm["metadata"]["emission_debug"]["best_safe_invalidation"]["reason"] == "authority_violation"


def test_fast_path_abstains_when_an_obvious_dimension_was_omitted():
    proposal = InterpretationProposal(
        raw_input="Are you sure about that?",
        source=SOURCE_FAST_PATH,
        primary_operation="ask",
        interlocutor_id="gate_guard",
    )
    result = validate_interpretation_proposal(
        proposal,
        discourse_focus=_claim_focus()[DISCOURSE_FOCUS_KEY],
        canonical_referents=[GUARD],
    )
    assert result.status == "abstained"
    assert "requested_dimension" in result.failed_fields
    built = _contract("Are you certain?", _claim_focus())
    assert built.dimension == "confidence"
    assert built.construction["fast_path_abstained"] is False
    unknown = proposal_from_mapping(
        {"source": SOURCE_MODEL, "raw_input": "mood?", "primary_operation": "ask", "dimension": "mood"}
    )
    rejected = validate_interpretation_proposal(unknown, canonical_referents=[GUARD])
    assert rejected.status == "abstained"
    assert rejected.reason == "unknown_dimension"
    purpose = proposal_from_mapping(
        {
            "source": SOURCE_MODEL,
            "raw_input": "What is that board for?",
            "primary_operation": "ask",
            "dimension": "purpose",
            "proposed_target_id": "notice_board",
        }
    )
    assert purpose.dimension == "use"


def test_evaluator_rejects_wrong_proposition_and_accepts_a_superset():
    procedure = _contract(TURN1).as_dict()
    identity = evaluate_playability(
        {
            "player_text": TURN1,
            "gm_text": TURN1_IDENTITY,
            "gm_output": {"player_facing_text": TURN1_IDENTITY, "metadata": {"emission_debug": {"resolution_contract": procedure}}},
        }
    )
    assert identity["semantic_result"] == "FAIL"
    use = _contract(TURN4, _focus(active_inspected={"id": "notice_board", "label": "Notice board", "kind": "object"})).as_dict()
    clue = evaluate_playability(
        {
            "player_text": TURN4,
            "gm_text": TURN4_CLUE,
            "gm_output": {"player_facing_text": TURN4_CLUE, "metadata": {"emission_debug": {"resolution_contract": use}}},
        }
    )
    assert clue["semantic_result"] == "FAIL"
    confidence = _contract(TURN6, _claim_focus()).as_dict()
    claim = evaluate_playability(
        {
            "player_text": TURN6,
            "gm_text": TURN6_IDENTITY,
            "gm_output": {"player_facing_text": TURN6_IDENTITY, "metadata": {"emission_debug": {"resolution_contract": confidence}}},
        }
    )
    assert claim["semantic_result"] == "FAIL"
    timing = _contract(TURN2, _claim_focus()).as_dict()
    source = evaluate_playability(
        {
            "player_text": TURN2,
            "gm_text": "She heard that from the night runner.",
            "gm_output": {
                "player_facing_text": "She heard that from the night runner.",
                "metadata": {"emission_debug": {"resolution_contract": timing}},
            },
        }
    )
    assert source["semantic_result"] == "FAIL"
    superset = TURN4_ANSWER + " " + TURN4_CLUE
    accepted = evaluate_playability(
        {
            "player_text": TURN4,
            "gm_text": superset,
            "gm_output": {"player_facing_text": superset, "metadata": {"emission_debug": {"resolution_contract": use}}},
        }
    )
    assert accepted["semantic_result"] == "PASS"


def test_raw_chat_keeps_a_procedural_answer(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)

    def fake_gpt(messages, **_kwargs):
        blob = " ".join(str(item.get("content") or "") for item in messages if isinstance(item, dict)).lower()
        if "clearance" in blob or "have to do" in blob or "required" in blob:
            return _gm_response(TURN1_ANSWER)
        return _gm_response(TURN1_ANSWER)

    monkeypatch.setattr("game.api.call_gpt", fake_gpt)
    client = TestClient(app)
    payload = client.post("/api/chat", json={"text": TURN1}).json()
    visible = payload["gm_output"]["player_facing_text"].lower()
    contract = payload["resolution"]["metadata"]["resolution_contract"]
    assert contract["operation"] == "ask"
    assert contract["dimension"] == "next_step"
    assert "clearance" in visible or "report" in visible
