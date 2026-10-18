"""Stubbed model interpretation. No paid inference."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from game.api import app
from game.discourse_state import DISCOURSE_FOCUS_KEY, commit_discourse_focus
from game.interpretation_proposal import SOURCE_MODEL, proposal_from_mapping, validate_interpretation_proposal
from game.resolution_contract import construct_resolution_contract
from game.scene_referent_catalog import build_canonical_referent_catalog
from game.semantic_interpreter import interpretation_messages, parse_interpretation_output
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _seed_shared_world

NOTICE = {"type": "object", "id": "notice_board", "label": "notice board", "aliases": ["notice", "posted notice"], "source": "scene"}
GUARD = {"type": "interlocutor", "id": "guard_captain", "label": "Guard Captain", "aliases": ["guard", "sentry"], "source": "scene"}
LEDGER = {"type": "object", "id": "ledger", "label": "ledger", "source": "scene"}


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
    return {"active_scene_id": "yard", DISCOURSE_FOCUS_KEY: focus}


def _contract(text, session=None, referents=None, interpreter=None):
    return construct_resolution_contract(
        player_text=text,
        session=session if session is not None else _focus(),
        scene_id="yard",
        canonical_referents=referents if referents is not None else [NOTICE, GUARD],
        model_interpreter=interpreter,
    )


def _proposal(**fields):
    payload = {
        "primary_operation": "ask",
        "supporting_operations": [],
        "raw_target_text": None,
        "proposed_target_id": None,
        "interlocutor_id": None,
        "conversational_subject": None,
        "dimension": None,
        "dimensions": [],
        "expected_resolution": "answer",
        "referenced_claim_id": None,
        "referenced_action_id": None,
        "referenced_inspected_id": None,
        "clarification_required": False,
        "ambiguous": False,
        "confidence": "0.4",
    }
    payload.update(fields)
    return {"status": "proposed", "proposal": payload, "api_calls": 0}


def _raising(_context):
    raise AssertionError("interpreter must not run when the fast path validates")


def test_fast_path_successes_do_not_invoke_the_interpreter():
    inspected = _focus(active_inspected={"id": "notice_board", "label": "notice board", "kind": "object"})
    claim = _focus(active_claim={"id": "claim-2", "label": "The toll changed last night.", "kind": "claim"})
    lead = _focus(active_actionable_lead={"id": "lead-7", "label": "shelter at the east lane", "kind": "lead", "scene_id": "yard"})
    action = _focus(last_attempted_action={"id": "act-1", "label": "I examined the board.", "kind": "act"})
    samples = (
        ("I examine the notice board.", _focus()),
        ("I inspect it.", inspected),
        ("Who told you that?", claim),
        ("Does it look worn?", inspected),
        ("I follow that lead.", lead),
        ("I take that step.", action),
    )
    for text, session in samples:
        contract = _contract(text, session, interpreter=_raising)
        assert contract.construction["fast_path_used"] is True, text
        assert contract.construction["model_interpreter_invoked"] is False, text
        assert contract.construction["compatibility_bridge"] is None, text


def test_fast_path_abstention_invokes_the_interpreter_once():
    calls = []

    def interpret(context):
        calls.append(context)
        return _proposal(
            interlocutor_id="guard_captain",
            conversational_subject="what a traveler must do to pass tonight",
            supporting_operations=["inspect"],
        )

    text = "I look for someone on duty and ask what a traveler has to do to pass the gate tonight."
    contract = _contract(text, interpreter=interpret)
    assert len(calls) == 1
    assert contract.construction["fast_path_abstained"] is True
    assert contract.construction["model_interpreter_invoked"] is True
    assert calls[0]["raw_input"] == text
    assert any(row["id"] == "notice_board" for row in calls[0]["candidates"])


def test_valid_model_proposal_becomes_the_authoritative_contract():
    text = "I look for someone on duty and ask what a traveler has to do to pass the gate tonight."
    contract = _contract(
        text,
        interpreter=lambda _ctx: _proposal(
            primary_operation="ask",
            supporting_operations=["inspect"],
            interlocutor_id="guard_captain",
            conversational_subject="requirements for passing the gate tonight",
        ),
    )
    assert contract.construction["validation_status"] == "validated"
    assert contract.operation == "ask"
    assert contract.operation != "inspect"
    assert contract.interlocutor_id == "guard_captain"
    assert "tonight" in (contract.conversational_subject or "")
    assert contract.construction["proposal_source"] == SOURCE_MODEL
    assert contract.construction["proposed_supporting_operations"] == ["inspect"]
    assert contract.construction["discourse_commit_allowed"] is True
    assert contract.construction["compatibility_bridge"] is None
    identity = ""
    if contract.target_ref:
        identity += contract.target_ref.id_or_text
    assert "duty" not in identity


def test_nonexistent_targets_are_rejected():
    text = "I look for someone on duty and ask what a traveler has to do to pass the gate tonight."
    cases = (
        {"primary_operation": "inspect", "proposed_target_id": "captain_of_the_watch", "raw_target_text": "the captain"},
        {"primary_operation": "ask", "interlocutor_id": "captain_who_is_not_here"},
        {"primary_operation": "ask", "referenced_claim_id": "claim-missing"},
        {"primary_operation": "act", "referenced_action_id": "action-never"},
        {"primary_operation": "invent_fact", "proposed_target_id": "notice_board"},
    )
    for fields in cases:
        contract = _contract(text, interpreter=lambda _ctx, fields=fields: _proposal(**fields))
        assert contract.construction["validation_status"] == "abstained", fields
        assert contract.construction["model_proposal_rejected"] is True, fields
        assert contract.construction["discourse_commit_allowed"] is False, fields
        assert contract.target_ref is None


def test_ambiguous_model_proposal_clarifies():
    contract = _contract(
        "I look for someone on duty and ask what a traveler has to do to pass the gate tonight.",
        interpreter=lambda _ctx: _proposal(primary_operation="ask", ambiguous=True, clarification_required=True),
    )
    assert contract.operation == "unresolved"
    assert contract.construction["clarification_after_model"] is True
    assert contract.request_kind == "clarification"


def test_malformed_structured_output_fails_closed():
    with pytest.raises(ValueError):
        parse_interpretation_output("The player means the notice board.", raw_input="look at it")
    contract = _contract(
        "I look for someone on duty and ask what a traveler has to do to pass the gate tonight.",
        interpreter=lambda _ctx: {"status": "failed", "reason": "malformed_structured_output", "api_calls": 1},
    )
    assert contract.operation == "unresolved"
    assert contract.target_ref is None
    assert contract.construction["compatibility_bridge"] is None
    assert "duty" not in json.dumps(contract.as_dict()).lower() or contract.target_ref is None


def test_rejected_proposal_does_not_mutate_discourse_and_accepted_one_does():
    session = _focus()
    rejected = _contract(
        "I look for someone on duty and ask what a traveler has to do to pass the gate tonight.",
        session,
        interpreter=lambda _ctx: _proposal(proposed_target_id="phantom_bell", primary_operation="inspect"),
    )
    commit_discourse_focus(session, contract=rejected.as_dict(), scene_id="yard")
    assert session[DISCOURSE_FOCUS_KEY]["active_inspected"] is None
    assert session[DISCOURSE_FOCUS_KEY]["active_interlocutor"] is None

    accepted = _contract(
        "I look for the guard and ask about the curfew.",
        session,
        interpreter=lambda _ctx: _proposal(
            primary_operation="ask",
            supporting_operations=["inspect"],
            interlocutor_id="guard_captain",
            conversational_subject="the curfew",
        ),
    )
    commit_discourse_focus(session, contract=accepted.as_dict(), scene_id="yard")
    interlocutor = session[DISCOURSE_FOCUS_KEY]["active_interlocutor"]
    assert interlocutor["id"] == "guard_captain"
    assert session[DISCOURSE_FOCUS_KEY]["active_inspected"] is None


def test_pronoun_proposal_binds_only_an_existing_referent():
    session = _focus(active_inspected={"id": "notice_board", "label": "notice board", "kind": "object"})
    contract = _contract(
        "I examine it up close and try to work out what people use it for.",
        session,
        interpreter=lambda _ctx: _proposal(
            primary_operation="inspect",
            proposed_target_id="notice_board",
            dimension="use",
            conversational_subject="what people use it for",
        ),
    )
    assert contract.operation == "inspect"
    assert contract.discourse_ref is not None
    assert contract.discourse_ref.id == "notice_board"
    assert "up close" not in (contract.target_ref.id_or_text if contract.target_ref else "")


def test_model_cannot_select_an_entity_absent_from_the_catalog():
    scene = {
        "scene": {
            "id": "frontier_gate",
            "location": "Cinderwatch Gate District",
            "hidden_facts": ["An agent of a noble house is watching new arrivals from the square's edge."],
            "interactables": [{"id": "notice_board", "label": "Notice board", "aliases": ["notice"]}],
            "addressables": [{"id": "guard_captain", "name": "Guard Captain", "addressable": True, "aliases": []}],
        }
    }
    catalog = build_canonical_referent_catalog(scene=scene, world={"npcs": []}, scene_id="frontier_gate")
    hidden = "agent of a noble house"
    assert all(hidden not in json.dumps(row).lower() for row in catalog)
    messages = interpretation_messages(
        {
            "raw_input": "I ask the noble agent what he is watching.",
            "candidates": catalog,
            "discourse_focus": {},
            "visible_turns": [{"player": "I look around.", "gm": "Rain hits the gate."}],
        }
    )
    assert hidden not in messages[1]["content"].lower()
    contract = construct_resolution_contract(
        player_text="I look for the noble agent and ask what he is watching.",
        session=_focus(),
        scene_id="frontier_gate",
        canonical_referents=catalog,
        model_interpreter=lambda _ctx: _proposal(
            primary_operation="ask",
            interlocutor_id="noble_agent",
            conversational_subject="what he is watching",
        ),
    )
    assert contract.construction["model_proposal_rejected"] is True
    assert contract.interlocutor_id != "noble_agent"


def test_persona_sessions_do_not_share_referents():
    latch = {"type": "object", "id": "iron_latch", "label": "iron latch", "source": "scene"}
    first = _focus(active_inspected={"id": "iron_latch", "label": "iron latch", "kind": "object", "scene_id": "yard"})
    second = _focus()
    contract = construct_resolution_contract(
        player_text="I examine that thing more closely and try to place it.",
        session=second,
        scene_id="yard",
        canonical_referents=[NOTICE],
        model_interpreter=lambda _ctx: _proposal(primary_operation="inspect", proposed_target_id="iron_latch"),
    )
    assert contract.target_ref is None
    assert first[DISCOURSE_FOCUS_KEY]["active_inspected"]["id"] == "iron_latch"
    assert second[DISCOURSE_FOCUS_KEY]["active_inspected"] is None
    assert latch["id"] not in json.dumps(contract.construction.get("canonical_candidates"))


def test_recorded_compound_and_pronoun_shapes_round_trip_through_the_validator():
    fixture = json.loads(
        Path("tests/fixtures/pr_br_interpretation/continuation8_shapes.json").read_text(encoding="utf-8")
    )
    compound = next(case for case in fixture["cases"] if "on duty" in case.get("raw_player_text", ""))
    contract = construct_resolution_contract(
        player_text=compound["raw_player_text"],
        session=_focus(),
        scene_id="yard",
        canonical_referents=compound.get("canonical_referents") or [NOTICE, GUARD],
        model_interpreter=lambda _ctx: _proposal(
            primary_operation="ask",
            supporting_operations=["inspect"],
            interlocutor_id="guard_captain",
            conversational_subject="requirements for passing the gate tonight",
        ),
    )
    assert contract.operation == "ask"
    result = validate_interpretation_proposal(
        proposal_from_mapping(contract.construction["interpretation_proposal"]),
        canonical_referents=[NOTICE, GUARD],
    )
    assert result.status == "validated"


def test_raw_chat_path_uses_the_stubbed_interpreter(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    from game import storage

    scene = storage.load_scene("scene_investigate")
    scene["scene"]["interactables"] = [
        {"id": "notice_board", "label": "Notice board", "aliases": ["notice", "posted notice"]},
    ]
    scene["scene"]["addressables"] = [
        {"id": "guard_captain", "name": "Guard Captain", "addressable": True, "address_roles": ["guard", "sentry"]},
    ]
    storage._save_json(storage.scene_path("scene_investigate"), scene)
    calls = []

    def interpret(context):
        calls.append(context["raw_input"])
        if "on duty" in context["raw_input"]:
            return _proposal(
                primary_operation="ask",
                supporting_operations=["inspect"],
                interlocutor_id="guard_captain",
                conversational_subject="what a traveler needs in order to pass tonight",
            )
        return {"status": "failed", "reason": "malformed_structured_output", "api_calls": 0}

    def fake_gpt(_messages, **_kwargs):
        return _gm_response('Guard Captain says, "You need the night pass and your name on the roster."')

    monkeypatch.setattr("game.semantic_interpreter.interpret_for_contract", interpret)
    monkeypatch.setattr("game.api.call_gpt", fake_gpt)
    client = TestClient(app)
    compound = client.post(
        "/api/chat",
        json={"text": "I look for someone on duty and ask what I need to get through tonight."},
    ).json()
    explicit = client.post("/api/chat", json={"text": "I examine the notice board."}).json()

    first = compound["resolution"]["metadata"]["resolution_contract"]
    second = explicit["resolution"]["metadata"]["resolution_contract"]
    assert first["operation"] == "ask"
    assert first["interlocutor_id"] == "guard_captain"
    assert first["construction"]["fast_path_abstained"] is True
    assert first["construction"]["model_interpreter_invoked"] is True
    assert first["construction"]["proposal_source"] == "model_assisted"
    assert first["construction"]["compatibility_bridge"] is None
    assert "duty" not in json.dumps(first.get("target_ref"))
    assert second["construction"]["fast_path_used"] is True
    assert second["construction"]["model_interpreter_invoked"] is False
    assert calls == ["I look for someone on duty and ask what I need to get through tonight."]
    focus = compound["session"]["discourse_focus"]["active_interlocutor"]
    assert focus["id"] == "guard_captain"
    assert compound["session"]["discourse_focus"]["active_claim"] is None
    visible = compound["gm_output"]["player_facing_text"].lower()
    assert "no such thing" not in visible
    assert "night pass" in visible or "roster" in visible


def test_raw_chat_preserves_a_useful_notice_use_answer(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)
    from game import storage

    scene = storage.load_scene("scene_investigate")
    scene["scene"]["interactables"] = [
        {"id": "notice_board", "label": "Notice board", "aliases": ["notice", "posted notice", "posted sheet"]},
    ]
    storage._save_json(storage.scene_path("scene_investigate"), scene)

    def interpret(context):
        if "use" in context["raw_input"]:
            return _proposal(
                primary_operation="inspect",
                proposed_target_id="notice_board",
                dimension="use",
                conversational_subject="what the notice board is for",
            )
        return {"status": "failed", "reason": "unexpected", "api_calls": 0}

    def fake_gpt(_messages, **_kwargs):
        return _gm_response(
            "The notice board serves as a clearinghouse for taxes, curfew rules, and public warnings."
        )

    monkeypatch.setattr("game.semantic_interpreter.interpret_for_contract", interpret)
    monkeypatch.setattr("game.api.call_gpt", fake_gpt)
    client = TestClient(app)
    payload = client.post(
        "/api/chat",
        json={"text": "I go up to the posted notice and try to work out what people actually use it for."},
    ).json()
    contract = payload["resolution"]["metadata"]["resolution_contract"]
    visible = payload["gm_output"]["player_facing_text"].lower()
    assert contract["operation"] == "inspect"
    assert "notice" in str((contract.get("target_ref") or {}).get("id_or_text") or "").lower()
    assert "no reliable use" not in visible
    assert "clearinghouse" in visible or "serves as" in visible


def test_raw_chat_does_not_emit_a_literal_physical_step(tmp_path, monkeypatch):
    _seed_shared_world(tmp_path, monkeypatch)

    def fake_gpt(_messages, **_kwargs):
        return _gm_response("You place your foot on the worn step. The mud holds.")

    monkeypatch.setattr("game.api.call_gpt", fake_gpt)
    monkeypatch.setattr(
        "game.semantic_interpreter.interpret_for_contract",
        lambda _ctx: _proposal(primary_operation="act"),
    )
    client = TestClient(app)
    payload = client.post("/api/chat", json={"text": "Fine, I take the step he suggested."}).json()
    visible = payload["gm_output"]["player_facing_text"].lower()
    contract = payload["resolution"]["metadata"]["resolution_contract"]
    assert contract["construction"]["fast_path_abstained"] is True
    assert "foot" not in visible
    assert "worn step" not in visible
