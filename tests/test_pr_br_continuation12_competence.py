"""Fast-path completeness, discourse typing, and contract-honoring checks.

No paid inference. Routing cases use a raising or stub interpreter.
"""
from __future__ import annotations

from game.discourse_state import DISCOURSE_FOCUS_KEY, commit_discourse_focus, note_emitted_npc_claim
from game.playability_eval import evaluate_playability
from game.resolution_contract import (
    assess_contract_satisfaction,
    construct_resolution_contract,
    prefer_stronger_resolution,
)


NOTICE = {"type": "object", "id": "notice_board", "label": "Notice board", "aliases": ["notice", "posted notice"], "source": "scene"}
GUARD = {"type": "interlocutor", "id": "gate_guard", "label": "Gate Guard", "aliases": ["guard"], "source": "scene"}


def _focus(**slots):
    focus = {
        "version": 1,
        "scene_id": "yard",
        "active_interlocutor": None,
        "active_claim": None,
        "active_actionable_lead": None,
        "active_inspected": None,
        "last_attempted_action": None,
    }
    focus.update(slots)
    return {"active_scene_id": "yard", "turn_counter": 3, DISCOURSE_FOCUS_KEY: focus}


def _contract(text, session=None, interpreter=None):
    return construct_resolution_contract(
        player_text=text,
        session=session if session is not None else _focus(),
        scene_id="yard",
        canonical_referents=[NOTICE, GUARD],
        model_interpreter=interpreter,
    )


def _raising(_context):
    raise AssertionError("interpreter must not run")


def _stub(**fields):
    payload = {
        "primary_operation": "ask",
        "supporting_operations": [],
        "proposed_target_id": None,
        "interlocutor_id": None,
        "conversational_subject": None,
        "dimension": None,
        "referenced_claim_id": None,
        "referenced_action_id": None,
        "clarification_required": False,
        "ambiguous": False,
    }
    payload.update(fields)
    return {"status": "proposed", "proposal": payload, "api_calls": 0}


def test_obvious_canonical_inquiry_stays_on_the_fast_path():
    contract = _contract("I examine the notice board.", interpreter=_raising)
    assert contract.construction["fast_path_used"] is True
    assert contract.construction["semantic_completeness"] == "sufficient"
    assert contract.construction["model_interpreter_invoked"] is False
    assert contract.operation == "inspect"
    assert contract.discourse_ref.id == "notice_board"


def test_elliptical_source_with_a_claim_binds_without_the_interpreter():
    session = _focus(active_claim={"id": "claim-2", "label": "The toll changed last night.", "kind": "claim", "turn_index": 2})
    for text in ("Who from?", "How recently?", "Where?"):
        contract = _contract(text, session, interpreter=_raising)
        assert contract.construction["fast_path_used"] is True, text
        assert contract.discourse_ref.id == "claim-2", text
        assert contract.construction["model_interpreter_invoked"] is False, text


def test_elliptical_source_without_a_claim_abstains_and_calls_the_interpreter():
    calls = []

    def interpret(context):
        calls.append(context["raw_input"])
        return _stub(interlocutor_id="gate_guard", conversational_subject="the source of that", dimension="source")

    for text in ("Who from?", "How recently?", "And if I do?"):
        calls.clear()
        contract = _contract(text, interpreter=interpret)
        assert contract.construction["fast_path_used"] is False, text
        assert contract.construction["fast_path_abstained"] is True, text
        assert contract.construction["semantic_completeness"] == "insufficient" or contract.construction["abstention_reason"], text
        assert contract.construction["model_interpreter_invoked"] is True, text
        assert calls == [text]


def test_referential_action_with_a_unique_previous_step_stays_on_the_fast_path():
    session = _focus(
        last_attempted_action={"id": "act-1", "label": "Ask the watchers about the patrol.", "kind": "act", "turn_index": 2}
    )
    for text in ("Fine, I take the step he suggested.", "I do what she suggested.", "Alright, I'll take that step."):
        contract = _contract(text, session, interpreter=_raising)
        assert contract.construction["fast_path_used"] is True, text
        assert contract.operation == "act", text
        assert contract.discourse_ref.type == "action", text


def test_referential_action_without_a_step_abstains():
    calls = []

    def interpret(context):
        calls.append(context["raw_input"])
        return _stub(primary_operation="act", referenced_action_id="act-9")

    contract = _contract("Fine, I take the step he suggested.", interpreter=interpret)
    assert contract.construction["fast_path_abstained"] is True
    assert contract.construction["model_interpreter_invoked"] is True
    assert calls == ["Fine, I take the step he suggested."]
    assert contract.operation == "unresolved"


def test_multi_reference_succeeds_only_when_both_bind():
    both = _focus(
        active_interlocutor={"id": "gate_guard", "label": "Gate Guard", "kind": "interlocutor"},
        active_inspected={"id": "notice_board", "label": "Notice board", "kind": "object"},
    )
    bound = _contract("I ask him about it.", both, interpreter=_raising)
    assert bound.construction["fast_path_used"] is True
    assert bound.interlocutor_id == "gate_guard"
    assert bound.discourse_ref.id == "notice_board"

    turned = _contract("I turn to him and ask about it.", both, interpreter=_raising)
    assert turned.construction["fast_path_used"] is True
    assert turned.interlocutor_id == "gate_guard"
    assert turned.discourse_ref.id == "notice_board"

    only_object = _focus(active_inspected={"id": "notice_board", "label": "Notice board", "kind": "object"})
    partial = _contract("I ask him about it.", only_object, interpreter=lambda _ctx: _stub())
    assert partial.construction["fast_path_abstained"] is True
    assert partial.construction["model_interpreter_invoked"] is True
    assert partial.construction["semantic_completeness"] != "sufficient" or partial.interlocutor_id != "gate_guard"


def test_interlocutor_identity_is_not_stored_as_a_claim():
    session = _focus()
    contract = {
        "contract_id": "rc_identity",
        "turn_index": 1,
        "operation": "ask",
        "dimension": "time",
        "dimensions": ["time"],
        "interlocutor_id": "gate_guard",
        "conversational_subject": "requirements to get through the gate tonight",
        "ambiguous": False,
        "raw_input": "I ask what I need to get through tonight.",
        "referent_provenance": "explicit_player",
        "discourse_ref": {"type": "interlocutor", "id": "gate_guard", "label": "Gate Guard"},
        "target_ref": {"type": "interlocutor", "id_or_text": "Gate Guard"},
        "construction": {"validation_status": "validated", "discourse_commit_allowed": True},
    }
    commit_discourse_focus(session, contract=contract, scene_id="yard")
    assert session[DISCOURSE_FOCUS_KEY]["active_interlocutor"]["id"] == "gate_guard"
    assert session[DISCOURSE_FOCUS_KEY]["active_claim"] is None


def test_a_real_assertion_still_becomes_the_active_claim():
    session = _focus()
    asserted = {
        "contract_id": "rc_claim",
        "turn_index": 2,
        "operation": "ask",
        "dimension": "source",
        "ambiguous": False,
        "raw_input": "Who told you that?",
        "discourse_ref": {"type": "claim", "id": "claim-2", "label": "The toll changed last night."},
        "target_ref": {"type": "claim", "id_or_text": "The toll changed last night."},
        "construction": {"validation_status": "validated", "discourse_commit_allowed": True},
    }
    commit_discourse_focus(session, contract=asserted, scene_id="yard")
    claim = session[DISCOURSE_FOCUS_KEY]["active_claim"]
    assert claim["id"] == "claim-2"
    assert "toll" in claim["label"].lower()

    emitted = _focus()
    assert note_emitted_npc_claim(
        emitted,
        emitted_text='Gate Guard says, "Travelers say carts have vanished along the east lane."',
        scene_id="yard",
    ) is True
    assert "vanished" in emitted[DISCOURSE_FOCUS_KEY]["active_claim"]["label"].lower()


def test_validated_guard_answer_is_not_replaced_by_an_absence_denial():
    contract = _contract(
        "I look for someone working the gate and ask what I need to get through tonight.",
        interpreter=lambda _ctx: _stub(
            interlocutor_id="gate_guard",
            proposed_target_id="gate_guard",
            conversational_subject="requirements to get through the gate tonight",
        ),
    )
    assert contract.operation == "ask"
    assert contract.interlocutor_id == "gate_guard"
    payload = contract.as_dict()
    answer = 'Gate Guard says, "You need a night pass and your name on the roster to get through tonight."'
    denial = "You find no such thing among what is actually present. The notice board lists taxes."
    assert assess_contract_satisfaction(denial, payload)["status"] == "unsatisfied"
    assert "canonical_premise_contradicted" in assess_contract_satisfaction(denial, payload)["reasons"]
    kept, info = prefer_stronger_resolution(
        answer,
        denial,
        {"metadata": {"resolution_contract": payload}},
        invalidated=True,
    )
    assert "night pass" in kept
    assert info["downgrade_rejected"] is True


def test_notice_board_use_answer_outranks_the_generic_wear_line():
    contract = _contract(
        "I go up to the posted notice and try to work out what people actually use it for.",
        interpreter=lambda _ctx: _stub(
            primary_operation="inspect",
            proposed_target_id="notice_board",
            dimension="use",
            conversational_subject="what the notice board is for",
        ),
    )
    payload = contract.as_dict()
    useful = "The notice board serves as a clearinghouse for taxes, curfew rules, and public warnings."
    canned = "The visible wear and marks establish no reliable use of the Notice board."
    assert assess_contract_satisfaction(useful, payload)["status"] == "satisfied"
    assert assess_contract_satisfaction(canned, payload)["status"] == "unsatisfied"
    assert "generic_use_nonanswer" in assess_contract_satisfaction(canned, payload)["reasons"]
    kept, info = prefer_stronger_resolution(useful, canned, {"metadata": {"resolution_contract": payload}})
    assert "clearinghouse" in kept
    assert info["downgrade_rejected"] is True


def test_evaluator_rejects_a_literal_step_and_a_denied_guard_and_a_generic_use_line():
    step = evaluate_playability(
        {
            "player_prompt": "Fine, I take the step he suggested.",
            "gm_text": "You place your foot on the worn step. The mud holds.",
        }
    )
    assert step["semantic_result"] == "FAIL"
    guard_contract = _contract("I examine the notice board.").as_dict()
    guard_contract["operation"] = "ask"
    guard_contract["interlocutor_id"] = "gate_guard"
    guard_contract["discourse_ref"] = {"type": "interlocutor", "id": "gate_guard", "label": "Gate Guard"}
    denied = evaluate_playability(
        {
            "player_prompt": "What do I need to get through tonight?",
            "gm_text": "You find no such thing among what is actually present.",
            "resolution_contract": guard_contract,
        }
    )
    assert denied["semantic_result"] == "FAIL"
    use_contract = _contract("I examine the notice board.").as_dict()
    use_contract["operation"] = "inspect"
    use_contract["dimension"] = "use"
    use_contract["dimensions"] = ["use"]
    generic = evaluate_playability(
        {
            "player_prompt": "What do people use the notice board for?",
            "gm_text": "The visible wear and marks establish no reliable use of the Notice board.",
            "resolution_contract": use_contract,
        }
    )
    assert generic["semantic_result"] == "FAIL"
