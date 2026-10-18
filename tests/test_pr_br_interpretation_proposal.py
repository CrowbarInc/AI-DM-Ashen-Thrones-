"""Canonical-or-abstain interpretation. Mechanisms, not phrase blacklists."""
from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path

from game.discourse_state import DISCOURSE_FOCUS_KEY, commit_discourse_focus
from game.interpretation_proposal import (
    STATUS_ABSTAINED,
    STATUS_VALIDATED,
    InterpretationProposal,
    proposal_from_mapping,
    validate_interpretation_proposal,
)
from game.resolution_contract import construct_resolution_contract

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "pr_br_interpretation" / "continuation8_shapes.json"
NOTICE = {"type": "object", "id": "notice_board", "label": "notice board", "source": "scene"}
LEDGER = {"type": "object", "id": "ledger", "label": "ledger", "source": "scene"}
LATCH = {"type": "object", "id": "iron_latch", "label": "iron latch", "source": "scene"}


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


def _contract(text: str, session: dict | None = None, referents=None):
    return construct_resolution_contract(
        player_text=text,
        session=session or _focus(),
        scene_id="yard",
        canonical_referents=referents,
    )


def _identity(contract) -> str:
    target = contract.target_ref.id_or_text if contract.target_ref else ""
    discourse_id = contract.discourse_ref.id if contract.discourse_ref else ""
    discourse = contract.discourse_ref.label if contract.discourse_ref else ""
    return f"{target} {discourse_id} {discourse}".lower()


def _assert_not_identity(contract, fragment: str) -> None:
    assert fragment.lower() not in _identity(contract)


def test_proposal_construction_does_not_mutate_session():
    session = _focus(active_inspected={"id": "notice_board", "label": "notice board", "kind": "object"})
    before = copy.deepcopy(session)
    proposal = InterpretationProposal(
        raw_input="I examine the missing bell.",
        source="model_assisted",
        primary_operation="inspect",
        raw_target_text="missing bell",
        proposed_target_id="missing_bell",
        confidence="1.0",
    )
    validate_interpretation_proposal(proposal, discourse_focus=session[DISCOURSE_FOCUS_KEY], canonical_referents=[NOTICE])
    assert session == before
    assert proposal.proposed_target_id == "missing_bell"


def test_fixture_a_on_duty_does_not_become_an_object():
    text = "I look for someone on duty and ask what a traveler has to do to pass the gate tonight."
    contract = _contract(text, referents=[NOTICE])
    assert contract.construction["validation_status"] == STATUS_ABSTAINED
    assert contract.operation == "unresolved"
    assert contract.construction["discourse_commit_allowed"] is False
    _assert_not_identity(contract, "duty")
    assert contract.target_ref is None


def test_fixture_b_compound_look_and_ask_does_not_select_inspect_by_order():
    text = "I look for someone on duty and ask what a traveler has to do to pass the gate tonight."
    contract = _contract(text, referents=[NOTICE])
    assert contract.operation != "inspect"
    assert contract.construction["operation_conflict"] is True
    assert contract.construction["abstention_reason"] in {"unresolved_compound_intent", "conflicting_operations"}


def test_structural_compound_variants_abstain():
    samples = (
        "I examine the latch and ask how it opens.",
        "I search the yard and inquire who keeps the key.",
        "I check the rope and ask whether it will hold.",
    )
    for text in samples:
        contract = _contract(text, referents=[LATCH, NOTICE])
        assert contract.operation != "inspect", text
        assert contract.construction["validation_status"] == STATUS_ABSTAINED, text
        assert contract.target_ref is None


def test_fixture_c_clause_sized_pronoun_rebinds_or_abstains():
    session = _focus(active_inspected={"id": "notice_board", "label": "notice board", "kind": "object"})
    text = "I examine it up close and try to work out what people use it for."
    contract = _contract(text, session, referents=[NOTICE])
    assert contract.construction["validation_status"] == STATUS_VALIDATED
    assert "notice" in _identity(contract)
    _assert_not_identity(contract, "up close")
    _assert_not_identity(contract, "work out")

    bare = _contract(text, _focus(), referents=[NOTICE])
    assert bare.construction["validation_status"] == STATUS_ABSTAINED
    assert bare.target_ref is None
    _assert_not_identity(bare, "up close")


def test_clause_length_and_pronoun_variants_do_not_become_ids():
    session = _focus(active_inspected={"id": "iron_latch", "label": "iron latch", "kind": "object"})
    samples = (
        "I inspect them carefully and try to see who made them.",
        "I examine this from the left and try to work out how the hinge was set.",
        "I study it beside the post and try to work out what people use it for at night.",
    )
    for text in samples:
        bound = _contract(text, session, referents=[LATCH])
        assert "latch" in _identity(bound), text
        assert "carefully and" not in _identity(bound)
        assert "from the left" not in _identity(bound)
        unbound = _contract(text, _focus(), referents=[LATCH])
        assert unbound.target_ref is None, text
        assert unbound.construction["discourse_commit_allowed"] is False


def test_fixture_d_bare_pronoun_binds_unique_inspected_object():
    session = _focus(active_inspected={"id": "notice_board", "label": "notice board", "kind": "object"})
    contract = _contract("I inspect it.", session, referents=[NOTICE])
    assert contract.construction["validation_status"] == STATUS_VALIDATED
    assert contract.discourse_ref is not None
    assert contract.discourse_ref.id == "notice_board"
    assert "notice" in _identity(contract)


def test_fixture_e_unknown_pronoun_does_not_create_object_it():
    contract = _contract("I inspect it.", _focus(), referents=[])
    assert contract.construction["validation_status"] == STATUS_ABSTAINED
    assert contract.construction["discourse_commit_allowed"] is False
    _assert_not_identity(contract, "object:it")
    target = contract.target_ref.id_or_text if contract.target_ref else ""
    assert (target or "").lower() != "it"


def test_fixture_f_ambiguous_pronoun_does_not_pick_a_referent():
    session = _focus(
        active_inspected={"id": "notice_board", "label": "notice board", "kind": "object"},
        active_actionable_lead={"id": "lead-7", "label": "east lane", "kind": "lead"},
    )
    contract = _contract("What about that?", session, referents=[NOTICE])
    assert contract.ambiguous is True
    assert contract.target_ref is None
    assert contract.discourse_ref is None
    assert contract.construction["validation_status"] == STATUS_ABSTAINED
    assert contract.construction["abstention_reason"] == "ambiguous_referent"


def test_fixture_g_explicit_known_entity_still_fast_paths():
    contract = _contract("I examine the notice board.", _focus(), referents=[NOTICE, LEDGER])
    assert contract.construction["validation_status"] == STATUS_VALIDATED
    assert contract.construction["canonical_target_found"] is True
    assert contract.operation in {"inspect", "perceive"}
    assert "notice" in _identity(contract)
    assert contract.construction["discourse_commit_allowed"] is True


def test_fixture_h_unknown_noun_does_not_create_a_pseudo_entity():
    contract = _contract("I examine the brass widget.", _focus(), referents=[NOTICE])
    assert contract.construction["validation_status"] == STATUS_ABSTAINED
    assert contract.construction["abstention_reason"] == "target_not_canonical"
    assert contract.target_ref is None
    _assert_not_identity(contract, "widget")
    assert contract.construction["discourse_commit_allowed"] is False


def test_unknown_noun_variants_abstain_against_a_supplied_index():
    for text in ("I inspect the cedar chest.", "I examine a cracked bell.", "I study the west shutter."):
        contract = _contract(text, _focus(), referents=[NOTICE, LATCH])
        assert contract.target_ref is None, text
        assert contract.construction["abstention_reason"] == "target_not_canonical"


def test_fixture_i_malformed_target_cannot_poison_a_later_pronoun():
    session = _focus()
    poisoned = _contract(
        "I look for someone on duty and ask what a traveler has to do to pass the gate tonight.",
        session,
        referents=[NOTICE],
    )
    commit_discourse_focus(session, contract=poisoned.as_dict(), scene_id="yard")
    inspected = session[DISCOURSE_FOCUS_KEY]["active_inspected"]
    assert inspected is None
    follow = _contract("I inspect it.", session, referents=[NOTICE])
    _assert_not_identity(follow, "duty")
    assert follow.discourse_ref is None or follow.discourse_ref.id != "duty"


def test_fixture_j_validated_inspection_still_commits():
    session = _focus()
    contract = _contract("I examine the notice board.", session, referents=[NOTICE])
    assert contract.construction["discourse_commit_allowed"] is True
    commit_discourse_focus(session, contract=contract.as_dict(), scene_id="yard")
    inspected = session[DISCOURSE_FOCUS_KEY]["active_inspected"]
    assert isinstance(inspected, dict)
    assert "notice" in str(inspected.get("label") or "").lower()


def test_fixture_k_active_claim_follow_up_still_binds():
    session = _focus(active_claim={"id": "claim-2", "label": "The toll changed last night.", "kind": "claim", "turn_index": 2})
    contract = _contract("Who told you that?", session, referents=[NOTICE])
    assert contract.dimension == "source"
    assert contract.discourse_ref is not None
    assert contract.discourse_ref.id == "claim-2"
    assert contract.operation != "unresolved"


def test_fixture_l_previous_action_still_binds():
    session = _focus(
        active_actionable_lead={"id": "lead-7", "label": "shelter at the east lane", "kind": "lead", "scene_id": "yard", "turn_index": 3}
    )
    contract = _contract("I follow that lead.", session, referents=[NOTICE])
    assert contract.operation == "follow"
    assert contract.discourse_ref is not None
    assert contract.discourse_ref.id == "lead-7"


def test_fixture_m_operation_conflict_abstains_without_lexical_order():
    first_ask = _contract("I ask the sentry and then examine the seal.", _focus(), referents=[NOTICE])
    first_look = _contract("I examine the seal and then ask the sentry.", _focus(), referents=[NOTICE])
    for contract in (first_ask, first_look):
        assert contract.operation == "unresolved"
        assert contract.construction["operation_conflict"] is True
        assert contract.target_ref is None


def test_fixture_n_raw_span_is_rejected_by_the_validator():
    proposal = proposal_from_mapping(
        {
            "raw_input": "I examine it up close and try to work out what people use it for.",
            "source": "model_assisted",
            "primary_operation": "inspect",
            "raw_target_text": "it up close and try to work out what people use it for",
            "confidence": "1.0",
            "target_capture": "model",
        }
    )
    result = validate_interpretation_proposal(proposal, discourse_focus={}, canonical_referents=[NOTICE])
    assert result.status == STATUS_ABSTAINED
    assert result.reason == "malformed_target_span"
    assert result.canonical_target_id is None
    assert result.discourse_commit_allowed is False


def test_invalid_model_proposals_are_rejected():
    catalog = [NOTICE, {"type": "interlocutor", "id": "serjeant", "label": "serjeant", "source": "scene"}]
    focus = {
        "active_claim": {"id": "claim-2", "label": "The toll changed.", "kind": "claim"},
        "last_attempted_action": {"id": "act-1", "label": "I examined the board.", "kind": "act"},
    }
    cases = (
        {"primary_operation": "inspect", "proposed_target_id": "captain_of_the_watch", "raw_target_text": "the captain"},
        {"primary_operation": "invent_fact", "proposed_target_id": "notice_board"},
        {"primary_operation": "ask", "referenced_claim_id": "claim-does-not-exist"},
        {"primary_operation": "act", "referenced_action_id": "action-never-happened"},
        {"primary_operation": "ask", "interlocutor_id": "captain_who_is_not_here"},
        {
            "primary_operation": "inspect",
            "raw_target_text": "board",
            "ambiguous": True,
            "confidence": "1.0",
        },
    )
    reasons = set()
    for payload in cases:
        payload = {"source": "model_assisted", "raw_input": "model proposal", "confidence": "1.0", **payload}
        result = validate_interpretation_proposal(
            proposal_from_mapping(payload),
            discourse_focus=focus,
            canonical_referents=catalog,
        )
        assert result.status == STATUS_ABSTAINED
        assert result.discourse_commit_allowed is False
        assert result.canonical_target_id != "captain_of_the_watch"
        reasons.add(result.reason)
    assert "target_not_canonical" in reasons
    assert "unsupported_operation" in reasons
    assert "nonexistent_referent" in reasons
    assert "ambiguous_referent" in reasons
    assert "unknown_interlocutor" in reasons


def test_model_confidence_does_not_authorize_duty():
    proposal = proposal_from_mapping(
        {
            "raw_input": "someone on duty",
            "source": "model_assisted",
            "primary_operation": "inspect",
            "raw_target_text": "duty",
            "proposed_target_id": "duty",
            "confidence": "1.0",
        }
    )
    result = validate_interpretation_proposal(proposal, canonical_referents=[NOTICE])
    assert result.status == STATUS_ABSTAINED
    assert result.canonical_target_id is None
    assert result.reason == "target_not_canonical"


def test_valid_model_proposal_uses_the_same_validator():
    proposal = proposal_from_mapping(
        {
            "raw_input": "I examine the notice board.",
            "source": "model_assisted",
            "primary_operation": "inspect",
            "proposed_target_id": "notice_board",
            "raw_target_text": "notice board",
            "confidence": "0.2",
        }
    )
    result = validate_interpretation_proposal(proposal, canonical_referents=[NOTICE, LEDGER])
    assert result.status == STATUS_VALIDATED
    assert result.canonical_target_id == "notice_board"
    assert result.discourse_commit_allowed is True


def test_two_matching_referents_stay_ambiguous_even_when_marked_certain():
    proposal = proposal_from_mapping(
        {
            "raw_input": "I examine the board.",
            "source": "model_assisted",
            "primary_operation": "inspect",
            "raw_target_text": "board",
            "ambiguous": False,
            "confidence": "1.0",
        }
    )
    catalog = [
        {"type": "object", "id": "notice_board", "label": "notice board", "source": "scene"},
        {"type": "object", "id": "duty_board", "label": "duty board", "source": "scene"},
    ]
    result = validate_interpretation_proposal(proposal, canonical_referents=catalog)
    assert result.status == STATUS_ABSTAINED
    assert result.reason == "ambiguous_referent"
    assert result.canonical_target_id is None


def test_recorded_fixtures_replay_without_inference():
    payload = json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))
    assert payload["schema"] == "pr_br_interpretation_fixture_v1"
    for case in payload["cases"]:
        expect = case["expect"]
        if case.get("mode") == "proposal":
            result = validate_interpretation_proposal(
                proposal_from_mapping(case["proposal"]),
                discourse_focus=case.get("discourse_context") or {},
                canonical_referents=case.get("canonical_referents"),
            )
            assert result.status == expect["validation_status"], case["id"]
            if "reason" in expect:
                assert result.reason == expect["reason"], case["id"]
            if expect.get("discourse_commit_allowed") is False:
                assert result.discourse_commit_allowed is False
            continue
        session = _focus(**(case.get("discourse_context") or {}))
        contract = _contract(case["raw_player_text"], session, referents=case.get("canonical_referents"))
        assert contract.construction["validation_status"] == expect["validation_status"], case["id"]
        if "operation" in expect:
            assert contract.operation == expect["operation"], case["id"]
        if "operation_any" in expect:
            assert contract.operation in expect["operation_any"], case["id"]
        if "forbidden_identity" in expect:
            _assert_not_identity(contract, expect["forbidden_identity"])
        if "canonical_contains" in expect:
            assert expect["canonical_contains"] in _identity(contract), case["id"]
        if "abstention_reason_any" in expect:
            assert contract.construction["abstention_reason"] in expect["abstention_reason_any"], case["id"]


def test_persona_sessions_do_not_inherit_discourse():
    import game.storage as storage
    from tools.run_pr_br_level2_probes import _isolate_storage

    names = (
        "BASE_DIR",
        "DATA_DIR",
        "WORLD_PATH",
        "SCENES_DIR",
        "CHARACTER_PATH",
        "CAMPAIGN_PATH",
        "SESSION_PATH",
        "COMBAT_PATH",
        "CONDITIONS_PATH",
        "SESSION_LOG_PATH",
    )
    snapshot = {name: getattr(storage, name) for name in names}
    tmp = Path(tempfile.mkdtemp(prefix="prbr-session-isolation-"))
    try:
        _isolate_storage(tmp)
        first = storage.load_session()
        first[DISCOURSE_FOCUS_KEY] = {
            "version": 1,
            "scene_id": "frontier_gate",
            "active_inspected": {"id": "persona-a", "label": "persona-a-only-latch", "kind": "object"},
            "active_claim": None,
            "active_actionable_lead": None,
            "active_interlocutor": None,
            "last_attempted_action": None,
        }
        storage.save_session(first)
        assert "persona-a-only-latch" in storage.SESSION_PATH.read_text(encoding="utf-8")
        _isolate_storage(tmp)
        second = storage.load_session()
        assert "persona-a-only-latch" not in json.dumps(second)
        inspected = (second.get(DISCOURSE_FOCUS_KEY) or {}).get("active_inspected")
        assert inspected is None
    finally:
        for name, value in snapshot.items():
            setattr(storage, name, value)
