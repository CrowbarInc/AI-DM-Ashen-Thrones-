"""Content dimension, clarification precedence, and additive coverage. No paid inference.

Continuation 14's six recorded turns are replayed from their player lines and
the candidates generation and emission actually produced.
"""
from __future__ import annotations

import json

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
    detect_semantic_degradation,
    enforce_emitted_contract_monotonicity,
    necessary_clarification,
    prefer_stronger_resolution,
    remember_satisfied_candidate,
    resolution_coverage,
    resolution_rank,
    semantic_line_view,
)
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _seed_shared_world


NOTICE = {
    "type": "object",
    "id": "notice_board",
    "label": "Notice board",
    "aliases": ["notice", "board", "posted notice", "notice board"],
    "source": "scene",
}
GUARD = {"type": "interlocutor", "id": "gate_guard", "label": "Gate Guard", "aliases": ["guard", "him"], "source": "scene"}

TURN1 = "I ask the gate guard what's required before they'll let me through tonight."
TURN1_ANSWER = (
    '"Captain Thoran commands the gate watch tonight," the gate guard replies crisply. '
    '"You\'ll need to have your papers in order, and follow the curfew rules posted on the notice board. '
    'Any special permissions will have to come from him."'
)
TURN1_IDENTITY = 'Gate Guard says, "Word is, captain Thoran commands the gate watch tonight."'
TURN2 = "When did that start?"
TURN2_CLARIFICATION = (
    '"Could you clarify what you mean by \'that\' exactly? Are you asking about the new curfew, '
    'the missing patrol, or something else posted on the notice board?" the gate guard asks.'
)
TURN2_INABILITY = 'Gate Guard says, "I cannot say how recently that was."'
TURN3 = "How sure is he about that?"
TURN3_ANSWER = (
    '"I can\'t say for certain," the gate guard admits with a guarded glance. '
    '"Captain Thoran\'s been in command since at least the last roster update, but beyond that, '
    'the exact timing isn\'t clear to me."'
)
TURN4 = "What's that notice board used for?"
TURN4_ANSWER = (
    '"The notice board has a few important postings," the gate guard says, nodding toward it. '
    '"It lists the current taxes and curfew rules everyone must follow. '
    'There\'s also a warning about a patrol that\'s gone missing recently. '
    'It\'s where travelers and locals alike find crucial updates before entering the city."'
)
TURN5 = "I ask him what travelers have been saying as they come through."
TURN5_ANSWER = (
    '"I\'ve not heard many tales from the travelers themselves," the gate guard admits. '
    '"Most arrive worn and wary, speaking little beyond urgent concerns about the tightened census '
    'at the eastern caravan choke point."'
)
TURN5_IDENTITY = 'Gate Guard says, "Word is, captain Thoran commands the gate watch tonight."'
TURN6 = "I'll do whatever he just told me to do."
TURN6_REFUSAL = 'Gate Guard says, "I will not carry out that request; you will need another route."'
CLEAR_INABILITY = 'Gate Guard says, "I cannot say when the curfew began."'


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
    return {"active_scene_id": "frontier_gate", "turn_counter": 4, DISCOURSE_FOCUS_KEY: focus}


def _split_focus():
    return _focus(
        active_claim={"id": "curfew_claim", "label": "A new curfew is in force.", "kind": "claim"},
        active_inspected={"id": "notice_board", "label": "Notice about the missing patrol", "kind": "object"},
    )


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
        "metadata": {"resolution_contract": contract.as_dict()},
    }


def _eval(contract, text):
    payload = contract.as_dict() if hasattr(contract, "as_dict") else dict(contract)
    return evaluate_playability(
        {
            "player_text": payload.get("raw_input"),
            "gm_text": text,
            "gm_output": {"player_facing_text": text, "metadata": {"emission_debug": {"resolution_contract": payload}}},
        }
    )


def test_content_is_distinct_from_source_confidence_time_and_use():
    assert _contract("Who told you that?").dimension == "source"
    assert _contract("What did they tell you?").dimension == "content"
    assert _contract("What are travelers saying?").dimension == "content"
    assert _contract("Do the travelers sound certain?").dimension == "confidence"
    assert _contract("What did they say?").dimension == "content"
    assert _contract("When did they say it?").dimension == "time"
    assert _contract("What does the notice say?").dimension == "content"
    board = _focus(active_inspected={"id": "notice_board", "label": "Notice board", "kind": "object"})
    purpose = _contract("What is the notice board used for?", board)
    assert purpose.dimension == "use"
    assert purpose.operation == "ask"


def test_content_fast_path_variants_and_abstention():
    samples = (
        "What did he say?",
        "What are travelers saying?",
        "What does the letter say?",
        "What was written there?",
        "What did she report?",
        "What have people been telling the guards?",
        "I ask him what travelers have been saying as they come through.",
    )
    for text in samples:
        contract = _contract(text)
        assert contract.dimension == "content", text
        assert contract.dimension != "source", text
    unbound = _contract("What was written there?", _focus(active_interlocutor=None, active_inspected=None))
    assert unbound.dimension == "content"
    assert unbound.construction["fast_path_abstained"] is True
    assert "content_referent" in unbound.construction["failed_fields"]
    bound = _contract("What did he say?")
    assert bound.dimension == "content"
    assert bound.construction["fast_path_abstained"] is False


def test_structured_interpreter_content_is_accepted_and_unknown_is_rejected():
    proposal = proposal_from_mapping(
        {
            "source": SOURCE_MODEL,
            "raw_input": "What are the travelers saying?",
            "primary_operation": "ask",
            "dimension": "substance",
            "interlocutor_id": "gate_guard",
        }
    )
    assert proposal.dimension == "content"
    accepted = validate_interpretation_proposal(
        proposal,
        discourse_focus=_focus()[DISCOURSE_FOCUS_KEY],
        canonical_referents=[GUARD],
    )
    assert accepted.status == "validated"
    unknown = proposal_from_mapping(
        {"source": SOURCE_MODEL, "raw_input": "mood?", "primary_operation": "ask", "dimension": "mood"}
    )
    rejected = validate_interpretation_proposal(unknown, canonical_referents=[GUARD])
    assert rejected.reason == "unknown_dimension"
    omitted = InterpretationProposal(
        raw_input="What are travelers saying?",
        source=SOURCE_FAST_PATH,
        primary_operation="ask",
        interlocutor_id="gate_guard",
    )
    abstained = validate_interpretation_proposal(
        omitted,
        discourse_focus=_focus()[DISCOURSE_FOCUS_KEY],
        canonical_referents=[GUARD],
    )
    assert abstained.status == "abstained"
    assert "requested_dimension" in abstained.failed_fields


def test_content_coverage_rejects_a_related_identity_and_allows_a_superset():
    contract = _contract(TURN5)
    assert contract.dimension == "content"
    resolution = _resolution(contract)
    assert "content" in resolution_coverage(TURN5_ANSWER, resolution)["covered_dimensions"]
    assert resolution_coverage(TURN5_IDENTITY, resolution)["covered_dimensions"] == []
    assert assess_contract_satisfaction(TURN5_ANSWER, contract.as_dict())["status"] == "satisfied"
    assert assess_contract_satisfaction(TURN5_IDENTITY, contract.as_dict())["status"] == "unsatisfied"
    superset = "Travelers say the north road is flooded. Most arrived this morning."
    assert "content" in resolution_coverage(superset, resolution)["covered_dimensions"]
    assert assess_contract_satisfaction(superset, contract.as_dict())["status"] == "satisfied"
    assert candidate_may_replace("Travelers say the north road is flooded.", superset, resolution)[0] is True
    assert candidate_may_replace(TURN5_ANSWER, TURN5_IDENTITY, resolution)[0] is False


def test_ambiguity_makes_clarification_outrank_inability_and_a_clear_referent_does_not():
    ambiguous = _contract(TURN2, _split_focus())
    assert ambiguous.dimension == "time"
    assert ambiguous.ambiguous is True
    resolution = _resolution(ambiguous)
    assert necessary_clarification(TURN2_CLARIFICATION, ambiguous.as_dict()) is True
    clarification = semantic_line_view(TURN2_CLARIFICATION, resolution)
    inability = semantic_line_view(TURN2_INABILITY, resolution)
    assert clarification["resolution_kind"] == "clarification"
    assert clarification["necessary_clarification"] is True
    assert inability["resolution_kind"] == "inability"
    assert resolution_rank(clarification) > resolution_rank(inability)
    kept, info = prefer_stronger_resolution(TURN2_CLARIFICATION, TURN2_INABILITY, resolution)
    assert "clarify" in kept.lower() or "asking" in kept.lower()
    assert info["downgrade_rejected"] is True
    gm = {"player_facing_text": TURN2_CLARIFICATION, "metadata": {}}
    remember_satisfied_candidate(gm, TURN2_CLARIFICATION, resolution)
    gm["player_facing_text"] = TURN2_INABILITY
    enforce_emitted_contract_monotonicity(gm, resolution)
    assert "clarify" in gm["player_facing_text"].lower() or "asking" in gm["player_facing_text"].lower()
    assert gm["metadata"]["emission_debug"]["final_selected_candidate"]
    assert gm["metadata"]["emission_debug"]["semantic_degradation"] is False

    clear = _contract("When did the curfew begin?", _split_focus())
    assert clear.ambiguous is False
    assert clear.dimension == "time"
    assert "curfew" in str(clear.target_ref.id_or_text or "").lower()
    clear_resolution = _resolution(clear)
    clear_view = semantic_line_view(CLEAR_INABILITY, clear_resolution)
    unnecessary = semantic_line_view(TURN2_CLARIFICATION, clear_resolution)
    assert clear_view["resolution_kind"] == "inability"
    assert unnecessary.get("necessary_clarification") is not True
    assert resolution_rank(unnecessary) <= resolution_rank(clear_view)
    direct = _contract("When did the patrol disappear?", _split_focus())
    assert direct.ambiguous is False
    assert "patrol" in str(direct.target_ref.id_or_text or "").lower()


def test_dimension_coverage_is_additive():
    board = _focus(active_inspected={"id": "notice_board", "label": "Notice board", "kind": "object"})
    use = _contract("What is this board used for?", board)
    use_line = "People use it for official notices; one was posted yesterday."
    assert "use" in resolution_coverage(use_line, _resolution(use))["covered_dimensions"]
    assert assess_contract_satisfaction(use_line, use.as_dict())["status"] == "satisfied"
    assert "dimension_substituted" not in assess_contract_satisfaction(use_line, use.as_dict())["reasons"]
    content = _contract("What are travelers saying?")
    content_line = "Travelers say the bridge is washed out; they heard it from a ferryman."
    assert "content" in resolution_coverage(content_line, _resolution(content))["covered_dimensions"]
    assert assess_contract_satisfaction(content_line, content.as_dict())["status"] == "satisfied"
    confidence = _contract("How sure is he about that?")
    confidence_line = "He sounds certain; he heard it this morning."
    assert "confidence" in resolution_coverage(confidence_line, _resolution(confidence))["covered_dimensions"]
    assert assess_contract_satisfaction(confidence_line, confidence.as_dict())["status"] == "satisfied"


def test_recorded_continuation14_turns():
    procedure = _contract(TURN1)
    assert procedure.dimension == "next_step"
    procedure_resolution = _resolution(procedure)
    assert assess_contract_satisfaction(TURN1_ANSWER, procedure.as_dict())["status"] == "satisfied"
    kept, info = prefer_stronger_resolution(TURN1_ANSWER, TURN1_IDENTITY, procedure_resolution)
    assert "papers" in kept.lower() or "need" in kept.lower()
    assert info["downgrade_rejected"] is True

    ambiguous = _contract(TURN2, _split_focus())
    assert "asking" in prefer_stronger_resolution(TURN2_CLARIFICATION, TURN2_INABILITY, _resolution(ambiguous))[0].lower() or "clarify" in prefer_stronger_resolution(TURN2_CLARIFICATION, TURN2_INABILITY, _resolution(ambiguous))[0].lower()

    confidence = _contract(TURN3)
    assert confidence.dimension == "confidence"
    confidence_resolution = _resolution(confidence)
    assert assess_contract_satisfaction(TURN3_ANSWER, confidence.as_dict())["status"] in {"satisfied", "legitimate_nonresolution"}
    kept_confidence, _info = prefer_stronger_resolution(TURN3_ANSWER, TURN5_IDENTITY, confidence_resolution)
    assert "certain" in kept_confidence.lower()

    use = _contract(TURN4)
    assert use.dimension == "use"
    assert use.operation == "ask"
    assert "notice" in str(use.target_ref.id_or_text or "").lower()
    use_resolution = _resolution(use)
    assert "use" in resolution_coverage(TURN4_ANSWER, use_resolution)["covered_dimensions"]
    assert assess_contract_satisfaction(TURN4_ANSWER, use.as_dict())["status"] == "satisfied"
    assert "dimension_substituted" not in assess_contract_satisfaction(TURN4_ANSWER, use.as_dict())["reasons"]

    content = _contract(TURN5)
    assert content.dimension == "content"
    content_resolution = _resolution(content)
    kept_content, content_info = prefer_stronger_resolution(TURN5_ANSWER, TURN5_IDENTITY, content_resolution)
    assert "census" in kept_content.lower() or "travelers" in kept_content.lower()
    assert content_info["downgrade_rejected"] is True
    gm = {"player_facing_text": TURN5_ANSWER, "metadata": {}}
    remember_satisfied_candidate(gm, TURN5_ANSWER, content_resolution)
    gm["player_facing_text"] = TURN5_IDENTITY
    enforce_emitted_contract_monotonicity(gm, content_resolution)
    assert "census" in gm["player_facing_text"].lower() or "concerns" in gm["player_facing_text"].lower()
    assert gm["metadata"]["emission_debug"]["best_safe_candidate"]

    action = _contract(TURN6)
    assert action.operation == "act"
    assert action.dimension is None
    action_resolution = _resolution(action)
    gm = {"player_facing_text": TURN1_ANSWER, "metadata": {}}
    remember_satisfied_candidate(gm, TURN1_ANSWER, procedure_resolution)
    gm["player_facing_text"] = TURN6_REFUSAL
    enforce_emitted_contract_monotonicity(gm, action_resolution)
    assert "another route" in gm["player_facing_text"].lower()
    assert "papers" not in gm["player_facing_text"].lower()


def test_semantic_degradation_detects_equal_rank_coverage_loss():
    contract = _contract(TURN5)
    payload = contract.as_dict()
    payload["dimension"] = None
    payload["dimensions"] = []
    resolution = {
        "kind": "question",
        "prompt": TURN5,
        "metadata": {"resolution_contract": payload},
    }
    before = semantic_line_view(TURN5_ANSWER, resolution)
    after = semantic_line_view(TURN5_IDENTITY, resolution)
    assert resolution_rank(before) == resolution_rank(after)
    report = detect_semantic_degradation(TURN5_ANSWER, TURN5_IDENTITY, resolution)
    assert report["degraded"] is True
    assert "requested_dimension_loss" in report["reasons"]
    ambiguous = _resolution(_contract(TURN2, _split_focus()))
    replaced = detect_semantic_degradation(TURN2_CLARIFICATION, TURN2_INABILITY, ambiguous)
    assert replaced["degraded"] is True
    assert "clarification_replaced_by_inability" in replaced["reasons"] or "lower_rank" in replaced["reasons"]
    assert candidate_may_replace(TURN5_ANSWER, TURN5_IDENTITY, resolution)[0] is False


def test_evaluator_content_mismatch_and_multidimension_and_clarification():
    content = _contract(TURN5).as_dict()
    assert _eval(content, TURN5_IDENTITY)["semantic_result"] == "FAIL"
    assert _eval(content, TURN5_ANSWER)["semantic_result"] == "PASS"
    use = _contract(TURN4).as_dict()
    assert _eval(use, TURN4_ANSWER)["semantic_result"] == "PASS"
    ambiguous = _contract(TURN2, _split_focus()).as_dict()
    assert _eval(ambiguous, TURN2_CLARIFICATION)["semantic_result"] == "PASS"


def test_raw_chat_preserves_content_clarification_use_and_blocks_equal_rank_loss(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)

    def fake_gpt(messages, **_kwargs):
        user = ""
        for message in reversed(messages):
            if isinstance(message, dict) and message.get("role") == "user":
                user = str(message.get("content") or "")
                break
        try:
            payload = json.loads(user)
            current = str(payload.get("player_input") or payload.get("raw_player_input") or payload.get("raw_input") or "")
        except (TypeError, ValueError, json.JSONDecodeError):
            current = user
        low = current.lower()
        if "when did that start" in low:
            return _gm_response(TURN2_CLARIFICATION)
        if "notice board used for" in low:
            return _gm_response(TURN4_ANSWER)
        if "travelers have been saying" in low or "what are travelers saying" in low:
            return _gm_response(TURN5_ANSWER)
        return _gm_response(TURN5_ANSWER)

    monkeypatch.setattr("game.api.call_gpt", fake_gpt)
    client = TestClient(app)
    content = client.post("/api/chat", json={"text": "I ask the gate guard what travelers have been saying tonight."}).json()
    content_contract = content["resolution"]["metadata"]["resolution_contract"]
    content_visible = content["gm_output"]["player_facing_text"]
    assert content_contract["dimension"] == "content"
    assert "census" in content_visible.lower() or "concerns" in content_visible.lower()
    emission = content["gm_output"]["metadata"]["emission_debug"]
    assert emission.get("semantic_degradation") is False
    resolution = content["resolution"]
    historical = detect_semantic_degradation(TURN5_ANSWER, TURN5_IDENTITY, resolution)
    assert historical["degraded"] is True

    follow = client.post("/api/chat", json={"text": "When did that start?"}).json()
    follow_visible = follow["gm_output"]["player_facing_text"].lower()
    assert "clarify" in follow_visible or "asking" in follow_visible
    assert "cannot say how recently" not in follow_visible

    board = client.post("/api/chat", json={"text": "What's that notice board used for?"}).json()
    board_contract = board["resolution"]["metadata"]["resolution_contract"]
    board_visible = board["gm_output"]["player_facing_text"]
    assert board_contract["dimension"] == "use"
    assert "use" in resolution_coverage(board_visible, board["resolution"])["covered_dimensions"]
    assert _eval(board_contract, board_visible)["semantic_result"] == "PASS"
