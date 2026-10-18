"""Production host-constrained candidate selection. No live provider calls."""
import copy
import inspect
import json

import pytest

from game import conversational_referents as refs
from game import host_constrained_candidates as candidates
from game import unified_semantic_planning as planning
from game.conversational_continuity import record_delivered_exchange
from game.immutable_valid_response import accepted_record, seal_host_speech
from tests.test_pr_eg_r6_r2_r1_referents import deliver
from tests.test_pr_eg_r6_r2_r2_operations import named, named_seed, role
from tests.test_pr_eg_r6_unified_semantic_planning import _multi_scene


pytestmark = pytest.mark.filterwarnings("ignore")


@pytest.fixture(autouse=True)
def gates(monkeypatch):
    monkeypatch.setenv(planning.FLAG, "1")
    monkeypatch.setenv(candidates.FLAG, "1")


def _record(ident="conv:1", status="direct", conversation="conv", corrected="", clarification="", speech=""):
    proposition = named()
    return {
        "referent_id": ident,
        "conversation_id": conversation,
        "request_proposition": proposition,
        "requested_relationship": "communicate_of(road)",
        "requested_subject": "road",
        "addressee_id": "mara",
        "answer_status": status,
        "focus_status": "active",
        "correction_status": corrected,
        "outstanding_clarification": clarification,
        "delivered_speech": speech,
        "witness_text": "Mara tell Oren road",
    }


def _context(utterance, records, sources=None, **extra):
    active = next((row["referent_id"] for row in records if row.get("focus_status") == "active"), "")
    return {
        "utterance": utterance,
        "participants": [{"id": "mara", "name": "Mara"}, {"id": "oren", "name": "Oren"}, {"id": "cala", "name": "Cala"}, {"id": "brin", "name": "Brin"}],
        "candidates": list(sources or []),
        "referents": {"conversation_id": records[0]["conversation_id"] if records else "conv", "active_id": active, "recent": []},
        "referent_records": records,
        "recent_dialogue": extra.get("recent") or [],
    }


def _rows(context, nonce="turn1"):
    return candidates.generate_candidates(context, nonce=nonce)


def _choice(rows, kind, **fills):
    row = next(item for item in rows if item["kind"] == kind)
    return candidates.blank_choice(candidate_id=row["id"], **fills)


def _compile(context, kind, nonce="turn1", **fills):
    rows = _rows(context, nonce)
    plan, reason, meta = candidates.compile_selection(_choice(rows, kind, **fills), context, rows)
    return plan, reason, meta, rows


def _people(topics, extra=None):
    return [
        {"id": "mara", "name": "Mara", "topics": topics},
        {"id": "oren", "name": "Oren", "topics": []},
        *(extra or []),
    ]


def _ask(session, text, choice, topics, extra=None):
    scene, world = _multi_scene(_people(topics, extra))
    world["clues"] = [{"id": "hidden-clue", "text": "gray-lantern"}]
    before_world = copy.deepcopy(world)
    before_session = copy.deepcopy(session)
    with candidates.candidate_selector(choice if callable(choice) else (lambda _context, _rows: choice)):
        locked = planning.authorize_information_turn(player_text=text, scene=scene, world=world, session=session)["plan"]
    return locked, world, before_world, before_session


def _select(kind, **fills):
    def choose(_context, rows):
        return _choice(rows, kind, **fills)
    return choose


def test_t01_candidate_generation_covers_structural_operations():
    rows = _rows(_context("unused", [_record()]))
    kinds = {row["kind"] for row in rows}
    assert {"new", "clarify", "none", "role:speaker", "role:recipient", "role:topic", "reverse", "reassign", "predicate", "requested", "temporal", "spatial", "negation"} <= kinds
    assert {"follow:who_supplied", "follow:why", "follow:support", "follow:other_time", "follow:what_was_said", "follow:other:topic"} <= kinds


def test_t02_candidate_identity_is_host_owned_and_unique():
    rows = _rows(_context("x", [_record()]), nonce="abc123")
    assert len({row["id"] for row in rows}) == len(rows)
    assert all(row["id"].startswith("abc123:") for row in rows)


def test_t03_candidate_turn_ownership_rejects_another_turns_id():
    context = _context("No, what did Oren tell Mara?", [_record()])
    first = _rows(context, "aaaa")
    second = _rows(context, "bbbb")
    stolen = _choice(first, "reverse", evidence="Oren tell Mara")
    plan, reason, _meta = candidates.compile_selection(stolen, context, second)
    assert plan is None and reason == "unknown_candidate"


def test_t04_candidate_referent_ownership_skips_other_conversations():
    local = _record("conv:1")
    foreign = _record("other:9", conversation="other")
    rows = _rows(_context("hello", [local, foreign]))
    assert any(row["referent"] == "conv:1" for row in rows)
    assert all(row["referent"] != "other:9" for row in rows)


def test_t05_candidate_structural_validity():
    record = _record()
    record["request_proposition"]["roles"] = [role("topic", "road")]
    rows = _rows(_context("hello", [record]))
    assert not any(row["kind"] == "reverse" for row in rows)
    assert all(row["id"] and row["summary"] and isinstance(row["fills"], list) for row in rows)


def test_t06_candidate_selection_compiles_a_new_question():
    context = _context("Mara, who keeps the cistern?", [])
    plan, reason, meta, _rows_out = _compile(
        context, "new", addressee_id="mara", evidence="keeps", predicate="keep", predicate_evidence="keeps",
        requested_role="keeper", new_roles=[{"role": "item", "value": "cistern", "evidence": "cistern"}],
    )
    assert reason == "" and meta["validation"] == "accepted"
    assert plan["conversational_act"] == "information_question"
    assert plan["request_proposition"]["requested_role"] == "keeper"
    assert plan["request_proposition"]["roles"][0]["value"] == "cistern"


def test_t07_candidate_ranking_does_not_replace_the_selected_id():
    context = _context("Mara, who keeps the cistern?", [])
    rows = _rows(context)
    valid = _choice(rows, "new", predicate="keep", predicate_evidence="keeps", requested_role="keeper",
                    new_roles=[{"role": "item", "value": "cistern", "evidence": "cistern"}], evidence="keeps")
    valid["ranked_ids"] = [next(row["id"] for row in rows if row["kind"] == "none"), valid["candidate_id"]]
    plan, reason, meta = candidates.compile_selection(valid, context, rows)
    assert reason == "" and plan["conversational_act"] == "information_question"
    assert meta["selected_candidate"] == valid["candidate_id"]


def test_t08_invalid_candidate_id_is_rejected():
    context = _context("Mara, who keeps the cistern?", [_record()])
    plan, reason, _meta = candidates.compile_selection(candidates.blank_choice(candidate_id="missing"), context, _rows(context))
    assert plan is None and reason == "unknown_candidate"


def test_t09_forged_candidate_id_is_rejected_without_repair():
    context = _context("No, what did Oren tell Mara?", [_record()])
    rows = _rows(context)
    forged = rows[0]["id"] + "-forged"
    plan, reason, _meta = candidates.compile_selection(candidates.blank_choice(candidate_id=forged, ranked_ids=[rows[0]["id"]]), context, rows)
    assert plan is None and reason == "unknown_candidate"


def test_t10_cross_turn_candidate_id_is_rejected():
    test_t03_candidate_turn_ownership_rejects_another_turns_id()


def test_t11_cross_conversation_referent_is_not_selectable():
    test_t04_candidate_referent_ownership_skips_other_conversations()


def test_t12_missing_candidate_fails_closed_inside_authorization():
    session, _record_out = named_seed()
    locked, world, before_world, before_session = _ask(session, "No, what did Oren tell Mara?", candidates.blank_choice(candidate_id="forged"), [])
    assert locked["response_kind"] == "unknown"
    assert locked["reason"] == "unknown_candidate"
    assert world == before_world and session == before_session


def test_t13_ambiguous_candidate_selection_asks_instead_of_guessing():
    first, second = _record("conv:1"), _record("conv:2")
    second["request_proposition"] = named(roles=[role("speaker", "Cala", "cala"), role("recipient", "Brin"), role("topic", "cistern")])
    context = _context("No, switch them", [first, second])
    plan, reason, meta, _rows_out = _compile(context, "reverse", evidence="switch")
    assert reason == "" and meta["validation"] == "clarification"
    assert plan["clarification_needed"] is True


def test_t14_new_question_is_not_forced_into_a_referent_transformation():
    context = _context("Mara, who keeps the cistern?", [_record()])
    plan, reason, _meta, _rows_out = _compile(
        context, "new", predicate="keep", predicate_evidence="keeps", requested_role="keeper",
        new_roles=[{"role": "item", "value": "cistern", "evidence": "cistern"}], evidence="keeps", addressee_id="mara",
    )
    assert reason == ""
    assert plan["referent_operation"]["target_referent_id"] == ""
    assert plan["request_proposition"]["roles"][0]["name"] == "item"


def test_t15_correction_classification():
    context = _context("No, the cistern", [_record()])
    plan, _reason, _meta, _rows_out = _compile(context, "role:topic", value="cistern", value_evidence="cistern", evidence="cistern")
    assert plan["conversational_act"] == "correction"
    assert plan["referent_operation"]["operation"] == "replace_role_value"


def test_t16_follow_up_classification():
    context = _context("Who told you?", [_record()])
    plan, _reason, _meta, _rows_out = _compile(context, "follow:who_supplied", evidence="told you")
    assert plan["conversational_act"] == "follow_up"
    assert plan["referent_operation"]["follow_up_relationship"] == "source_attribution"
    assert plan["request_proposition"]["requested_role"] == "informant"


def test_t17_clarification_response_targets_outstanding_clarification():
    record = _record(status="clarification", clarification="proposition")
    context = _context("I mean Oren", [record])
    plan, reason, _meta, _rows_out = _compile(context, "resolve", value="Oren", value_evidence="Oren", requested_role="speaker", evidence="Oren")
    assert reason == ""
    assert plan["conversational_act"] == "clarification_response"
    assert plan["request_proposition"]["roles"][0]["value"] == "Oren"


def test_t18_subject_replacement_preserves_the_object():
    record = _record()
    record["request_proposition"] = {
        "predicate": "keeper", "predicate_evidence": "keeps", "subject": "miller", "subject_evidence": "miller",
        "object": "night drum", "object_evidence": "night drum", "missing_argument": "", "temporal": "", "spatial": "",
        "epistemic": "npc_knowledge", "prior_reference": "", "negated": False,
    }
    context = _context("I meant the porter", [record])
    plan, reason, _meta, _rows_out = _compile(context, "subject", value="porter", value_evidence="porter", evidence="porter")
    assert reason == ""
    assert plan["request_proposition"]["subject"] == "porter"
    assert plan["request_proposition"]["object"] == "night drum"


def test_t19_object_replacement_preserves_the_subject():
    record = _record()
    record["request_proposition"] = {
        "predicate": "keeper", "predicate_evidence": "keeps", "subject": "miller", "subject_evidence": "miller",
        "object": "night drum", "object_evidence": "night drum", "missing_argument": "", "temporal": "", "spatial": "",
        "epistemic": "npc_knowledge", "prior_reference": "", "negated": False,
    }
    context = _context("I meant the night ledger", [record])
    plan, reason, _meta, _rows_out = _compile(context, "object", value="night ledger", value_evidence="night ledger", evidence="night ledger")
    assert reason == ""
    assert plan["request_proposition"]["object"] == "night ledger"
    assert plan["request_proposition"]["subject"] == "miller"


def test_t20_relationship_replacement_preserves_roles():
    context = _context("Rather, who owns it?", [_record()])
    plan, reason, _meta, _rows_out = _compile(context, "predicate", predicate="own", predicate_evidence="owns", evidence="owns")
    assert reason == ""
    assert plan["request_proposition"]["predicate"] == "own"
    assert [role["value"] for role in plan["request_proposition"]["roles"]] == ["Mara", "Oren", "road"]


def test_t21_requested_role_replacement_preserves_known_roles():
    context = _context("I was asking who heard it", [_record()])
    plan, reason, _meta, _rows_out = _compile(context, "requested", requested_role="hearer", evidence="heard")
    assert reason == ""
    assert plan["request_proposition"]["requested_role"] == "hearer"
    assert plan["referent_operation"]["changed_fields"] == ["requested_role"]
    assert [role["name"] for role in plan["request_proposition"]["roles"]] == ["speaker", "recipient", "topic"]


def test_t22_temporal_replacement():
    context = _context("I meant tomorrow", [_record()])
    plan, reason, _meta, _rows_out = _compile(context, "temporal", temporal="tomorrow", evidence="tomorrow")
    assert reason == ""
    assert plan["request_proposition"]["temporal"] == "tomorrow"
    assert plan["request_proposition"]["spatial"] == ""


def test_t23_spatial_replacement():
    context = _context("I meant at the quay", [_record()])
    plan, reason, _meta, _rows_out = _compile(context, "spatial", spatial="quay", evidence="quay")
    assert reason == ""
    assert plan["request_proposition"]["spatial"] == "quay"


def test_t24_role_reversal():
    context = _context("No, what did Oren tell Mara?", [_record()])
    plan, reason, _meta, _rows_out = _compile(context, "reverse", evidence="Oren tell Mara")
    assert reason == ""
    values = {role["name"]: role["value"] for role in plan["request_proposition"]["roles"]}
    assert values == {"speaker": "Oren", "recipient": "Mara", "topic": "road"}
    assert plan["request_proposition"]["requested_role"] == "message_content"


def test_t25_multi_role_preservation_on_reversal():
    plan, _reason, _meta, _rows_out = _compile(_context("No, what did Oren tell Mara?", [_record()]), "reverse", evidence="Oren tell Mara")
    assert plan["referent_operation"]["changed_roles"] == ["speaker", "recipient"]
    assert plan["request_proposition"]["roles"][2]["name"] == "topic"


def test_t26_unchanged_role_preservation_on_single_replacement():
    plan, _reason, _meta, _rows_out = _compile(
        _context("I meant the cistern", [_record()]), "role:topic", value="cistern", value_evidence="cistern", evidence="cistern",
    )
    values = {role["name"]: role["value"] for role in plan["request_proposition"]["roles"]}
    assert values["speaker"] == "Mara" and values["recipient"] == "Oren" and values["topic"] == "cistern"


def test_t27_correction_lineage_is_recorded_on_the_operation():
    plan, _reason, _meta, _rows_out = _compile(
        _context("I meant the cistern", [_record()]), "role:topic", value="cistern", value_evidence="cistern", evidence="cistern",
    )
    assert plan["referent_operation"]["target_referent_id"] == "conv:1"
    assert plan["request_proposition"]["prior_reference"] == "communicate_of(road)"


def test_t28_follow_up_source_attribution():
    plan, _reason, _meta, _rows_out = _compile(_context("Who told you?", [_record()]), "follow:who_supplied", evidence="told")
    assert plan["referent_operation"]["follow_up_relationship"] == "source_attribution"
    assert plan["request_proposition"]["requested_role"] == "informant"


def test_t29_follow_up_explanation():
    plan, _reason, _meta, _rows_out = _compile(_context("Why?", [_record()]), "follow:why", evidence="Why")
    assert plan["referent_operation"]["follow_up_relationship"] == "explanation"
    assert plan["request_proposition"]["requested_role"] == "reason"


def test_t30_follow_up_evidence():
    plan, _reason, _meta, _rows_out = _compile(_context("What supports that?", [_record()]), "follow:support", evidence="supports")
    assert plan["referent_operation"]["follow_up_relationship"] == "evidence"


def test_t31_follow_up_temporal_variation():
    plan, reason, _meta, _rows_out = _compile(_context("What about tomorrow?", [_record()]), "follow:other_time", temporal="tomorrow", evidence="tomorrow")
    assert reason == ""
    assert plan["referent_operation"]["follow_up_relationship"] == "temporal_modification"
    assert plan["request_proposition"]["temporal"] == "tomorrow"
    assert plan["request_proposition"]["roles"][2]["value"] == "road"


def test_t32_follow_up_alternative_argument():
    plan, reason, _meta, _rows_out = _compile(
        _context("What about the cistern?", [_record()]), "follow:other:topic", value="cistern", value_evidence="cistern", evidence="cistern",
    )
    assert reason == ""
    assert plan["referent_operation"]["follow_up_relationship"] == "alternative_argument"
    assert plan["request_proposition"]["roles"][2]["value"] == "cistern"
    assert plan["request_proposition"]["roles"][0]["value"] == "Mara"


def test_t33_follow_up_after_uncertainty_does_not_invent_an_informant():
    session, record = named_seed()
    stored = session["conversational_context"]["question_referents"]["records"][0]
    assert stored["referent_id"] == record["referent_id"]
    stored["answer_status"] = "unknown"
    locked, _world, before_world, before = _ask(session, "Who told you?", _select("follow:who_supplied", evidence="told"), [])
    assert locked["response_kind"] == "unknown"
    assert locked["reason"] == "referenced_answer_unknown"
    assert "do not know" in locked["host_line"].casefold()
    assert "flooded" not in locked["host_line"].casefold()
    assert _world == before_world and session == before


def test_t34_follow_up_after_partial_answer_keeps_the_question_open():
    session, record = named_seed()
    stored = session["conversational_context"]["question_referents"]["records"][0]
    stored["answer_status"] = "partial"
    stored["missing_roles"] = ["message_content"]
    before_id = record["referent_id"]
    locked, *_rest = _ask(session, "Which person exactly?", _select("follow:who_supplied", evidence="person"), [])
    assert locked["referent_operation"]["follow_up_relationship"] == "source_attribution"
    assert refs.active(session)["referent_id"] == before_id
    assert refs.active(session)["answer_status"] == "partial"


def test_t35_genuine_ambiguity_is_not_resolved_by_recency():
    session, first = named_seed()
    second = copy.deepcopy(first)
    second["referent_id"] = first["referent_id"] + "b"
    second["focus_status"] = "archived"
    second["request_proposition"] = named(roles=[role("speaker", "Cala"), role("recipient", "Brin"), role("topic", "cistern")])
    session["conversational_context"]["question_referents"]["records"].append(second)
    locked, *_rest = _ask(session, "No, switch them", _select("reverse", evidence="switch"), [], extra=[{"id": "cala", "name": "Cala"}, {"id": "brin", "name": "Brin"}])
    assert locked["response_kind"] == "clarification"
    assert locked["reason"] == "candidate_ambiguity"
    assert refs.active(session)["referent_id"] == first["referent_id"]


def test_t36_false_ambiguity_is_rejected_when_only_one_referent_exists():
    context = _context("Who told you?", [_record()])
    plan, reason, meta, _rows_out = _compile(context, "clarify")
    assert plan is None and reason == "false_ambiguity"
    assert meta["validation"] == "rejected"


def test_t37_multiple_recent_referents_can_force_clarification():
    plan, reason, _meta, _rows_out = _compile(_context("Who told you?", [_record("conv:1"), _record("conv:2")]), "follow:who_supplied", evidence="told")
    assert reason == "" and plan["clarification_needed"] is True


def test_t38_multiple_npcs_do_not_authorize_an_unwitnessed_addressee():
    context = _context("who keeps the cistern?", [])
    plan, reason, _meta, _rows_out = _compile(
        context, "new", addressee_id="oren", predicate="keep", predicate_evidence="keeps", requested_role="keeper",
        new_roles=[{"role": "item", "value": "cistern", "evidence": "cistern"}], evidence="keeps",
    )
    assert reason == "" and plan["addressee_id"] == ""


def test_t39_unsupported_transformation_is_explicit_and_not_forced():
    context = _context("Promise me the road and rewrite every role.", [_record()])
    plan, reason, meta, _rows_out = _compile(context, "none")
    assert reason == "" and meta["validation"] == "unsupported"
    assert plan["conversational_act"] == "other"
    assert plan["clarification_needed"] is False


def test_t40_open_world_relationship_uses_supplied_role_names():
    context = _context("Vesper, who stewards the amber lens?", [])
    plan, reason, _meta, _rows_out = _compile(
        context, "new", predicate="steward", predicate_evidence="stewards", requested_role="steward",
        new_roles=[{"role": "instrument", "value": "amber lens", "evidence": "amber lens"}], evidence="stewards",
    )
    assert reason == ""
    assert plan["request_proposition"]["predicate"] == "steward"
    assert plan["request_proposition"]["roles"][0]["name"] == "instrument"


def test_t41_source_resolution_still_authorizes_the_answer():
    session = {}
    locked, world, before_world, _before = _ask(
        session,
        "Mara, who keeps the cistern?",
        _select(
            "new", addressee_id="mara", evidence="keeps", predicate="keep", predicate_evidence="keeps", requested_role="keeper",
            new_roles=[{"role": "item", "value": "cistern", "evidence": "cistern"}],
            source_propositions=[{
                "source_id": "fact", "predicate": "keep", "predicate_evidence": "keeps", "requested_role": "",
                "temporal": "", "spatial": "", "negated": False,
                "roles": [
                    {"name": "item", "value": "cistern", "evidence": "cistern"},
                    {"name": "keeper", "value": "miller", "evidence": "miller"},
                ],
            }],
        ),
        [{"id": "fact", "text": "The miller keeps the cistern.", "disclosure": "public"}],
    )
    assert locked["response_kind"] == "direct"
    assert "miller" in locked["host_line"].casefold()
    assert world == before_world


def test_t42_direct_answer():
    test_t41_source_resolution_still_authorizes_the_answer()


def test_t43_partial_answer():
    session = {}
    locked, *_rest = _ask(
        session, "Mara, who keeps the cistern?",
        _select("new", addressee_id="mara", evidence="keeps", predicate="keep", predicate_evidence="keeps", requested_role="keeper",
                new_roles=[{"role": "item", "value": "cistern", "evidence": "cistern"}],
                source_propositions=[{"source_id": "fact", "predicate": "keep", "predicate_evidence": "keeps", "requested_role": "",
                                      "temporal": "", "spatial": "", "negated": False,
                                      "roles": [{"name": "item", "value": "cistern", "evidence": "cistern"}]}]),
        [{"id": "fact", "text": "Someone keeps the cistern.", "disclosure": "public"}],
    )
    assert locked["response_kind"] == "partial"
    assert locked["answer_status"] == "partial_answer"


def test_t44_related_nonanswer_is_not_success():
    session = {}
    locked, *_rest = _ask(
        session, "Mara, who keeps the cistern?",
        _select("new", addressee_id="mara", evidence="keeps", predicate="keep", predicate_evidence="keeps", requested_role="keeper",
                new_roles=[{"role": "item", "value": "cistern", "evidence": "cistern"}],
                source_propositions=[{"source_id": "fact", "predicate": "own", "predicate_evidence": "owns", "requested_role": "",
                                      "temporal": "", "spatial": "", "negated": False,
                                      "roles": [{"name": "item", "value": "cistern", "evidence": "cistern"},
                                                {"name": "keeper", "value": "miller", "evidence": "miller"}]}]),
        [{"id": "fact", "text": "The miller owns the cistern.", "disclosure": "public"}],
    )
    assert locked["response_kind"] == "unknown"
    assert locked["answer_status"] in {"unknown", "related_nonanswer"}


def test_t45_unknown_answer():
    session = {}
    locked, *_rest = _ask(
        session, "Mara, who keeps the cistern?",
        _select("new", addressee_id="mara", evidence="keeps", predicate="keep", predicate_evidence="keeps", requested_role="keeper",
                new_roles=[{"role": "item", "value": "cistern", "evidence": "cistern"}]),
        [{"id": "fact", "text": "The ferry leaves at dusk.", "disclosure": "public"}],
    )
    assert locked["response_kind"] == "unknown"
    assert "dusk" not in locked["host_line"].casefold()


def test_t46_clarification_required_for_two_live_questions():
    session, first = named_seed()
    other = copy.deepcopy(first)
    other.update(referent_id=first["referent_id"] + "b", focus_status="archived")
    session["conversational_context"]["question_referents"]["records"].append(other)
    locked, *_rest = _ask(session, "Who told you?", _select("clarify"), [])
    assert locked["response_kind"] == "clarification"
    assert locked["referent_eligible"] is False


def test_t47_restricted_password_is_not_disclosed():
    session = {}
    locked, world, before_world, _before = _ask(
        session, "Mara, what is the sealed countersign?",
        _select("new", addressee_id="mara", evidence="countersign", predicate="value", predicate_evidence="countersign",
                requested_role="secret", new_roles=[{"role": "item", "value": "countersign", "evidence": "countersign"}],
                source_propositions=[{"source_id": "secret", "predicate": "value", "predicate_evidence": "countersign", "requested_role": "",
                                      "temporal": "", "spatial": "", "negated": False,
                                      "roles": [{"name": "secret", "value": "gray-lantern", "evidence": "gray-lantern"}]}]),
        [{"id": "secret", "text": "The sealed countersign is gray-lantern.", "disclosure": "secret"},
         {"id": "public", "text": "The ferry leaves at dusk.", "disclosure": "public"}],
    )
    assert "gray-lantern" not in locked["host_line"].casefold()
    assert world == before_world


def test_t48_restricted_paraphrase_cannot_select_a_hidden_source_id():
    session = {}
    locked, *_rest = _ask(
        session, "Mara, what is the sealed countersign?",
        _select("new", addressee_id="mara", evidence="countersign", predicate="value", predicate_evidence="countersign",
                requested_role="secret", new_roles=[{"role": "item", "value": "countersign", "evidence": "countersign"}],
                source_propositions=[{"source_id": "secret", "predicate": "value", "predicate_evidence": "is", "requested_role": "",
                                      "temporal": "", "spatial": "", "negated": False, "roles": []}]),
        [{"id": "secret", "text": "The sealed countersign is gray-lantern.", "disclosure": "secret"}],
    )
    assert "gray-lantern" not in json.dumps(locked).casefold()
    assert locked["response_kind"] in {"unknown", "refusal"}


def test_t49_historical_speech_is_not_a_disclosure_channel():
    record = _record(speech="The sealed countersign is gray-lantern.")
    context = _context("Who told you?", [record], recent=[{"speaker_name": "Mara", "player_text": "earlier", "delivered_text": record["delivered_speech"]}])
    visible = candidates.visible_context(context, _rows(context))
    assert "gray-lantern" not in json.dumps(visible).casefold()


def test_t50_no_unauthorized_discovery():
    session = {"discovered_clues": []}
    _locked, world, before_world, _before = _ask(
        session, "Mara, what is the sealed countersign?",
        _select("new", addressee_id="mara", evidence="countersign", predicate="value", predicate_evidence="countersign",
                requested_role="secret", new_roles=[{"role": "item", "value": "countersign", "evidence": "countersign"}]),
        [{"id": "secret", "text": "The sealed countersign is gray-lantern.", "disclosure": "secret"}],
    )
    assert world["clues"] == before_world["clues"]
    assert session["discovered_clues"] == []


def test_t51_no_unauthorized_mutation():
    session, _record_out = named_seed()
    _locked, world, before_world, before_session = _ask(session, "No, what did Oren tell Mara?", _select("reverse", evidence="Oren tell Mara"), [])
    assert world == before_world
    assert session == before_session


def test_t52_final_response_seal_matches_the_authorized_line():
    session = {}
    locked, *_rest = _ask(
        session, "Mara, who keeps the cistern?",
        _select("new", addressee_id="mara", evidence="keeps", predicate="keep", predicate_evidence="keeps", requested_role="keeper",
                new_roles=[{"role": "item", "value": "cistern", "evidence": "cistern"}],
                source_propositions=[{"source_id": "fact", "predicate": "keep", "predicate_evidence": "keeps", "requested_role": "",
                                      "temporal": "", "spatial": "", "negated": False,
                                      "roles": [{"name": "item", "value": "cistern", "evidence": "cistern"},
                                                {"name": "keeper", "value": "miller", "evidence": "miller"}]}]),
        [{"id": "fact", "text": "The miller keeps the cistern.", "disclosure": "public"}],
    )
    sealed = seal_host_speech({}, text=locked["host_line"], source="host", speaker_id="mara", speaker_name="Mara", resolution=None, player_text=locked["question_text"])
    assert sealed["player_facing_text"] == locked["host_line"]


def test_t53_api_history_agrees_with_adopted_speech():
    session = {}
    locked, *_rest = _ask(
        session, "Mara, who keeps the cistern?",
        _select("new", addressee_id="mara", evidence="keeps", predicate="keep", predicate_evidence="keeps", requested_role="keeper",
                new_roles=[{"role": "item", "value": "cistern", "evidence": "cistern"}],
                source_propositions=[{"source_id": "fact", "predicate": "keep", "predicate_evidence": "keeps", "requested_role": "",
                                      "temporal": "", "spatial": "", "negated": False,
                                      "roles": [{"name": "item", "value": "cistern", "evidence": "cistern"},
                                                {"name": "keeper", "value": "miller", "evidence": "miller"}]}]),
        [{"id": "fact", "text": "The miller keeps the cistern.", "disclosure": "public"}],
    )
    sealed = seal_host_speech({}, text=locked["host_line"], source="host", speaker_id="mara", speaker_name="Mara", resolution=None, player_text=locked["question_text"])
    record_delivered_exchange(session, player_text=locked["question_text"], delivered_text=sealed["player_facing_text"], turn=1,
                              social={"npc_id": "mara", "npc_name": "Mara", "unified_semantic_plan": locked}, adoption=accepted_record(sealed))
    assert session["conversational_context"]["delivered_exchanges"][-1]["delivered_text"] == sealed["player_facing_text"]


def test_t54_referent_commit_waits_for_adoption():
    session = {}
    locked, *_rest = _ask(
        session, "Mara, who keeps the cistern?",
        _select("new", addressee_id="mara", evidence="keeps", predicate="keep", predicate_evidence="keeps", requested_role="keeper",
                new_roles=[{"role": "item", "value": "cistern", "evidence": "cistern"}],
                source_propositions=[{"source_id": "fact", "predicate": "keep", "predicate_evidence": "keeps", "requested_role": "",
                                      "temporal": "", "spatial": "", "negated": False,
                                      "roles": [{"name": "item", "value": "cistern", "evidence": "cistern"},
                                                {"name": "keeper", "value": "miller", "evidence": "miller"}]}]),
        [{"id": "fact", "text": "The miller keeps the cistern.", "disclosure": "public"}],
    )
    assert refs.state(session) == {}
    deliver(session, locked)
    assert refs.active(session)["request_proposition"]["requested_role"] == "keeper"


def test_t55_failed_selection_rolls_back_focus():
    session, record = named_seed()
    before = copy.deepcopy(record)
    locked, *_rest = _ask(session, "No, what did Oren tell Mara?", candidates.blank_choice(candidate_id="forged"), [])
    assert locked["referent_eligible"] is False
    assert refs.active(session) == before


def test_t56_save_load_preserves_candidate_mode_referents():
    session, record = named_seed()
    restored = json.loads(json.dumps(session))
    assert refs.active(restored) == record
    locked, *_rest = _ask(restored, "No, the cistern", _select("role:topic", value="cistern", value_evidence="cistern", evidence="cistern"), [])
    deliver(restored, locked, 2)
    reloaded = json.loads(json.dumps(restored))
    assert refs.active(reloaded)["request_proposition"]["roles"][2]["value"] == "cistern"
    assert refs.active(reloaded)["parent_referent_id"] == record["referent_id"]


def test_t57_legacy_mode_remains_available(monkeypatch):
    monkeypatch.delenv(candidates.FLAG, raising=False)
    assert candidates.routing_mode() == "semantic_planner"
    monkeypatch.delenv(planning.FLAG, raising=False)
    assert candidates.routing_mode() == "legacy"


def test_t58_feature_gate_rollback_ignores_the_selector(monkeypatch):
    monkeypatch.delenv(candidates.FLAG, raising=False)

    def boom(_context, _rows):
        raise AssertionError("candidate selector must not run")

    with candidates.candidate_selector(boom):
        with planning.plan_proposer(lambda _ctx: {"status": "proposed", "plan": {"marker": True}, "api_calls": 0, "usage": {}}):
            proposed = planning.propose_semantic_plan({"utterance": "Mara, who keeps the cistern?"})
    assert proposed["plan"]["marker"] is True
    monkeypatch.setenv(candidates.FLAG, "1")
    with candidates.candidate_selector(lambda _context, _rows: candidates.blank_choice(candidate_id="missing")):
        with planning.plan_proposer(lambda _ctx: {"status": "proposed", "plan": {"marker": True}, "api_calls": 0}):
            routed = planning.propose_semantic_plan({"utterance": "Mara, who keeps the cistern?"})
    assert routed["status"] == "failed"
    assert routed["usage"]["routing_mode"] == "host_constrained_candidates"


def test_t59_no_lexical_special_case_dependency():
    source = inspect.getsource(candidates.generate_candidates)
    for phrase in ("who told you", "i meant", "what did", "amber lens", "countersign"):
        assert phrase not in source.casefold()
    first = _context("completely different wording", [_record()])
    second = _context("another utterance with no shared verbs", [_record()])
    assert [row["kind"] for row in _rows(first)] == [row["kind"] for row in _rows(second)]


def test_t60_provider_call_accounting(monkeypatch):
    monkeypatch.delenv("ASHEN_DISABLE_LIVE_INTERPRETATION", raising=False)

    def fake(_payload):
        return "{}", {"purpose": "semantic_candidate", "input_tokens": 11, "output_tokens": 4, "latency_ms": 9}

    monkeypatch.setattr(candidates, "invoke_candidate_provider", fake)
    proposed = candidates.propose_from_candidates(_context("Mara, who keeps the cistern?", []))
    assert proposed["api_calls"] == 1
    assert proposed["usage"]["purpose"] == "semantic_candidate"
    assert proposed["usage"]["input_tokens"] == 11


def test_t61_rumor_epistemic_is_preserved_from_the_source_record():
    session = {}
    locked, *_rest = _ask(
        session, "Mara, who keeps the cistern?",
        _select("new", addressee_id="mara", evidence="keeps", predicate="keep", predicate_evidence="keeps", requested_role="keeper",
                new_roles=[{"role": "item", "value": "cistern", "evidence": "cistern"}],
                source_propositions=[{"source_id": "fact", "predicate": "keep", "predicate_evidence": "keeps", "requested_role": "",
                                      "temporal": "", "spatial": "", "negated": False,
                                      "roles": [{"name": "item", "value": "cistern", "evidence": "cistern"},
                                                {"name": "keeper", "value": "miller", "evidence": "miller"}]}]),
        [{"id": "fact", "text": "The miller keeps the cistern.", "disclosure": "public", "epistemic": "rumor"}],
    )
    assert locked["response_kind"] == "partial"
    assert "rumor" in locked["host_line"].casefold()
    assert locked["epistemic_status"] == "rumor"


def test_t62_corrected_referents_are_not_offered():
    live = _record("conv:1")
    stale = _record("conv:0", corrected="corrected")
    rows = _rows(_context("hello", [stale, live]))
    assert all(row["referent"] != "conv:0" for row in rows)


def test_t63_candidate_descriptions_omit_delivered_speech():
    rows = _rows(_context("hello", [_record(speech="The sealed countersign is gray-lantern.")]))
    assert "gray-lantern" not in json.dumps(rows).casefold()


def test_t64_candidate_gate_defaults_off(monkeypatch):
    monkeypatch.delenv(candidates.FLAG, raising=False)
    assert candidates.candidate_selection_enabled() is False


def test_t65_reassign_requires_multiple_witnessed_roles():
    context = _context("No, Brin told Cala", [_record()])
    plan, reason, _meta, _rows_out = _compile(
        context, "reassign", evidence="Brin told Cala",
        role_updates=[
            {"role": "speaker", "value": "Brin", "evidence": "Brin"},
            {"role": "recipient", "value": "Cala", "evidence": "Cala"},
        ],
    )
    assert reason == ""
    values = {role["name"]: role["value"] for role in plan["request_proposition"]["roles"]}
    assert values["speaker"] == "Brin" and values["recipient"] == "Cala" and values["topic"] == "road"
    rejected, reject_reason, _meta, _rows_out = _compile(context, "reassign", evidence="Brin", role_updates=[{"role": "speaker", "value": "Brin", "evidence": "Brin"}])
    assert rejected is None and reject_reason == "unsupported_transformation"


def test_t67_paraphrased_evidence_grounds_only_values_present_in_the_utterance():
    context = _context("Vesper, what did Cala tell Brin about the cistern?", [])
    plan, reason, _meta, _rows_out = _compile(
        context, "new", predicate="tell", predicate_evidence="did Cala tell Brin about the cistern",
        requested_role="message_content", evidence="what did Cala tell Brin",
        new_roles=[
            {"role": "speaker", "value": "Cala", "evidence": "Cala told Brin about the cistern"},
            {"role": "recipient", "value": "Brin", "evidence": "Cala told Brin about the cistern"},
            {"role": "topic", "value": "cistern", "evidence": "about the cistern"},
        ],
    )
    assert reason == ""
    assert {role["name"]: role["evidence"] for role in plan["request_proposition"]["roles"]}["speaker"] == "Cala"
    rejected, reject_reason, _meta, _rows_out = _compile(
        context, "new", predicate="tell", predicate_evidence="tell", requested_role="message_content", evidence="tell",
        new_roles=[{"role": "speaker", "value": "gray-lantern", "evidence": "gray-lantern"}],
    )
    assert rejected is None and reject_reason == "unwitnessed_role"


def test_t68_reverse_uses_participant_roles_whatever_they_are_named():
    record = _record()
    record["request_proposition"]["roles"] = [role("speaker", "Cala", "cala"), role("addressee", "Brin", "brin"), role("topic", "cistern")]
    rows = _rows(_context("No, what did Brin tell Cala?", [record]))
    assert any(row["kind"] == "reverse" and row.get("swap_roles") == ["speaker", "addressee"] for row in rows)
    plan, reason, _meta, _rows_out = _compile(_context("No, what did Brin tell Cala?", [record]), "reverse", evidence="Brin tell Cala")
    assert reason == ""
    values = {item["name"]: item["value"] for item in plan["request_proposition"]["roles"]}
    assert values["speaker"] == "Brin" and values["addressee"] == "Cala" and values["topic"] == "cistern"


def test_t66_production_holdouts_exist_and_are_not_imported_by_generation():
    from pathlib import Path
    payload = json.loads(Path("artifacts/pr_eg_r6_r3_r1/frozen_production_holdouts.json").read_text(encoding="utf-8"))
    assert len(payload["cases"]) >= 8
    assert "amber lens" not in inspect.getsource(candidates.generate_candidates).casefold()
