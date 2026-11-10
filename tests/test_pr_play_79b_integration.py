"""PR-PLAY-79B chat routing and publication ownership.

Development coverage for ordinary NPC questions and for turns that already
have a final sentence. Not a frozen holdout.
"""
import copy

import pytest

from game.api import deterministic_provider_skip_line
from game.authored_action_language import decision_for, propose
from game.authored_consequences import ENROLLMENT
from game.bounded_improvisation import LEDGER_KEY
from game.integrated_play import validate_narration
from game.player_initiative import decide
from game.publication_contract import (
    ADJUDICATION_RESULT,
    CLARIFICATION_REQUIRED,
    FAILURE,
    FINAL_ENGINE_RESPONSE,
    KNOWN_REPEAT_LINE,
    LIVE_EXPRESSION_REQUESTED,
    UNSUPPORTED_ACTION,
    narration_skip,
    stamp,
    summarize_provider_rows,
)
from tests.test_pr_play_76_physical import enable
from tests.test_pr_play_78_integrated import play
from tests.test_pr_play_78a_authored import _scene, _world
from tests.test_pr_play_79a_continuity import gate


@pytest.fixture
def ready(monkeypatch):
    enable(monkeypatch)
    monkeypatch.setenv("ASHEN_EXPERIMENTAL_DYNAMIC_NPCS", "1")
    monkeypatch.setenv("ASHEN_DISABLE_EXPRESSION_GENERATION", "1")
    monkeypatch.setenv("ASHEN_EXPERIMENTAL_INTEGRATED_NARRATION", "0")
    return gate()


def _say(session, scene, world, text):
    _plan, result, said, _changed = play(text, session, scene, world)
    return said, result


NPC_QUESTIONS = [
    "What do you know about the missing patrol?",
    "When did you last hear about them?",
    "What about the patrol again?",
    "Do you think something happened?",
    "Who are you?",
    "What happened to the patrol?",
    "Did you see the patrol leave?",
    "How long has the patrol been gone?",
]


@pytest.mark.parametrize("text", NPC_QUESTIONS, ids=[f"npc-{index}" for index in range(len(NPC_QUESTIONS))])
def test_ordinary_npc_questions_are_not_authored_choices(ready, text):
    session, scene, world = ready
    _say(session, scene, world, "Hello, Gate Guard.")
    decision = decision_for(text, scene=scene, world=world, session=session)
    assert decision is None
    said, _result = _say(session, scene, world, text)
    low = said.casefold()
    assert "not available here yet" not in low
    assert "nothing was attempted" not in low
    assert "which person" not in low


def test_six_followups_stay_with_the_guard(ready):
    session, scene, world = ready
    lines = ["Hello, Gate Guard.", *NPC_QUESTIONS[:6]]
    for text in lines:
        said, _result = _say(session, scene, world, text)
        assert "which person" not in said.casefold()
        assert "not available here yet" not in said.casefold()
    slot = session["conversational_context"]["active_interlocutor"]
    assert slot["npc_id"] == "gate_guard"
    assert slot["status"] == "active"
    assert session[LEDGER_KEY]["npc_focus"] == "gate_guard"


DISTINCTIONS = [
    ("What does the notice board say?", "missing patrol", "which person"),
    ("Where am I?", "frontier gate", "which person"),
    ("What do I know about the patrol?", "missing patrol", "which person"),
]


@pytest.mark.parametrize("text,present,absent", DISTINCTIONS, ids=["board", "place", "memory"])
def test_non_npc_questions_stay_out_of_authored_matching(ready, text, present, absent):
    session, scene, world = ready
    _say(session, scene, world, "Hello, Gate Guard.")
    assert decision_for(text, scene=scene, world=world, session=session) is None
    decision = decide(text, scene=scene, world=world, session=session)
    low = (decision.player_facing_text or "").casefold()
    assert present in low
    assert absent not in low
    assert decision.proposed_operation != "ASK"


def test_asking_the_guard_is_not_an_authored_execution(ready):
    session, scene, world = ready
    _say(session, scene, world, "Hello, Gate Guard.")
    text = "I ask the guard what he knows about the patrol."
    assert decision_for(text, scene=scene, world=world, session=session) is None
    said, _result = _say(session, scene, world, text)
    assert "not available here yet" not in said.casefold()


def test_reporting_findings_can_still_select_the_authored_action(monkeypatch):
    enable(monkeypatch)
    session, scene = _scene("old_milestone")
    got = propose(
        "I report the uncertain trail to the watch.",
        scene=scene, world=_world(), session=session,
    )
    assert got is not None
    assert got["kind"] == "execute"
    assert got["id"] == "patrol_report"


def test_survey_question_does_not_execute_the_choice(monkeypatch):
    enable(monkeypatch)
    session, scene = _scene("old_milestone")
    got = propose("Can I survey the trail yet?", scene=scene, world=_world(), session=session)
    assert got["kind"] == "answer"
    assert got.get("id") is None


CONTRACTS = [
    (FINAL_ENGINE_RESPONSE, "You examine the milestone again.", "publication_contract"),
    (CLARIFICATION_REQUIRED, "Which of the two guards do you mean?", "publication_contract"),
    (UNSUPPORTED_ACTION, "That part is not supported here.", "publication_contract"),
    (FAILURE, "That part was not carried out.", "publication_contract"),
]


@pytest.mark.parametrize("contract,text,reason", CONTRACTS, ids=["final", "clarify", "unsupported", "failure"])
def test_completed_contracts_skip_primary_narration(contract, text, reason):
    meta = stamp({"engine_publication": text}, contract)
    skipped = deterministic_provider_skip_line(
        resolution={"kind": "interact", "metadata": meta},
        scene={}, world={}, session={}, player_text="look",
    )
    assert skipped == (text, reason)


def test_nonempty_text_without_a_contract_does_not_skip_primary():
    skipped = deterministic_provider_skip_line(
        resolution={"metadata": {"engine_publication": "Keep the provider.", "skip_primary_narration": False}},
        scene={}, world={}, session={}, player_text="Look.",
    )
    assert skipped is None


def test_already_searched_is_a_final_engine_response():
    skipped = narration_skip(
        {"kind": "already_searched", "metadata": {"action_outcome": "valid_no_new_information"}},
        scene={}, session={},
    )
    assert skipped == (KNOWN_REPEAT_LINE, "final_engine_response")
    again = deterministic_provider_skip_line(
        resolution={"kind": "already_searched", "metadata": {}},
        scene={}, world={}, session={}, player_text="I look around the milestone.",
    )
    assert again[0] == KNOWN_REPEAT_LINE
    assert again[1] == "final_engine_response"


def test_adjudication_uses_one_bounded_expression_then_stops(monkeypatch):
    monkeypatch.setenv("ASHEN_EXPERIMENTAL_INTEGRATED_NARRATION", "1")
    monkeypatch.setattr(
        "game.integrated_play.maybe_narrate",
        lambda facts, session=None, scene=None: {"text": "You shift the loose stone aside."},
    )
    meta = stamp({"engine_publication": "You move the loose stone. It is now aside."}, ADJUDICATION_RESULT)
    first = narration_skip({"kind": "interact", "metadata": meta}, scene={}, session={})
    assert first == ("You shift the loose stone aside.", "bounded_live_expression")
    second = narration_skip({"kind": "interact", "metadata": meta}, scene={}, session={})
    assert second[1] == "publication_contract"
    assert meta["bounded_expression_attempted"] is True


def test_rejected_expression_keeps_the_mechanical_line(monkeypatch):
    monkeypatch.setenv("ASHEN_EXPERIMENTAL_INTEGRATED_NARRATION", "1")
    monkeypatch.setattr("game.integrated_play.maybe_narrate", lambda *args, **kwargs: None)
    meta = stamp({"engine_publication": "You move the loose stone. It is now aside."}, ADJUDICATION_RESULT)
    skipped = narration_skip({"kind": "interact", "metadata": meta}, scene={}, session={})
    assert skipped == ("You move the loose stone. It is now aside.", "adjudication_result")


def test_live_expression_request_is_not_inferred_from_text_alone():
    meta = stamp({}, LIVE_EXPRESSION_REQUESTED)
    assert narration_skip({"kind": "observe", "metadata": meta}, scene={}, session={}) is None


RELEVANT = [
    ("You shift the loose stone aside.", "You move the loose stone. It is now aside.", True),
    ("Dust lifts as you move the loose stone aside.", "You move the loose stone. It is now aside.", True),
    ("The disturbed ground still points northwest.", "northwest mud track", True),
    ("There is nothing opposing you in this situation.", "You move away. No new place was created.", False),
    ("You find gold beside a secret passage.", "You move the loose stone.", False),
    ("Fresh blood confirms the patrol was attacked.", "Tracks lead northwest.", False),
]


@pytest.mark.parametrize("candidate,facts,adopt", RELEVANT, ids=[f"rel-{index}" for index in range(len(RELEVANT))])
def test_narration_must_mention_the_committed_outcome(candidate, facts, adopt):
    assert validate_narration(candidate, facts, session={"clue_knowledge": {}})["adopt"] is adopt


def test_established_northwest_paraphrase_remains_allowed():
    verdict = validate_narration(
        "The tracks continue northwest through the mud.",
        "The player found tracks leading northwest.",
        session={"clue_knowledge": {}},
    )
    assert verdict["adopt"] is True
    assert "irrelevant" not in verdict["reasons"]


def test_conversation_survives_save_and_resume(ready):
    session, scene, world = ready
    _say(session, scene, world, "Hello, Gate Guard.")
    _say(session, scene, world, "What do you know about the missing patrol?")
    restored = copy.deepcopy(session)
    said, _result = _say(restored, scene, world, "What about the patrol again?")
    assert "missing patrol" in said.casefold()
    assert restored[LEDGER_KEY]["npc_focus"] == "gate_guard"
    assert "northwest" not in said.casefold()


def test_other_campaign_does_not_keep_the_guard(ready):
    session, scene, world = ready
    _say(session, scene, world, "Hello, Gate Guard.")
    other = copy.deepcopy(session)
    other["campaign_run_id"] = "beta"
    other[ENROLLMENT] = "beta"
    said, _result = _say(other, scene, world, "What do you know about the missing patrol?")
    assert "gate guard says" not in said.casefold()
    assert session[LEDGER_KEY]["npc_focus"] == "gate_guard"


def test_leaving_the_scene_drops_the_question_route(ready):
    session, scene, world = ready
    _say(session, scene, world, "Hello, Gate Guard.")
    session["active_scene_id"] = "old_milestone"
    later = {"scene": {"id": "old_milestone", "location": "Old Milestone", "visible_facts": ["A stone milestone leans beside the road."], "interactables": [], "addressables": []}}
    said, _result = _say(session, later, world, "What about the patrol again?")
    assert session[LEDGER_KEY]["npc_focus"] is None
    assert "gate guard says" not in said.casefold()


def test_goodbye_then_a_patrol_question_does_not_resume(ready):
    session, scene, world = ready
    _say(session, scene, world, "Hello, Gate Guard.")
    _say(session, scene, world, "Goodbye.")
    decision = decision_for(
        "What do you know about the missing patrol?", scene=scene, world=world, session=session,
    )
    assert session[LEDGER_KEY]["npc_focus"] is None
    assert decision is None or decision.proposed_operation != "ASK"


ROUTE_CASES = [
    ("Who are you?", None),
    ("What is your name?", None),
    ("When did the patrol leave?", None),
    ("Do you know who was on it?", None),
    ("What is this place like?", None),
    ("You mentioned the patrol earlier. What else?", None),
    ("I ask the guard whether the patrol returned.", None),
    ("What does the notice board say?", None),
    ("Where am I?", None),
    ("What do I know about the patrol?", None),
]


@pytest.mark.parametrize("text,expected", ROUTE_CASES, ids=[f"route-{index}" for index in range(len(ROUTE_CASES))])
def test_active_guard_questions_skip_the_authored_menu(ready, text, expected):
    session, scene, world = ready
    _say(session, scene, world, "Hello, Gate Guard.")
    decision = decision_for(text, scene=scene, world=world, session=session)
    assert decision is expected


AUTHORITY = [
    ("You discover a hidden camp past the stone.", "Tracks lead northwest.", "consequential_or_hidden"),
    ("The patrol captain was dragged northwest.", "Tracks lead northwest.", "consequential_or_hidden"),
    ("You find gold under the milestone.", "The stone is aside.", "consequential_or_hidden"),
    ("The tracks bend southeast from the stone.", "Tracks lead northwest.", "unestablished_direction"),
    ("You climb the milestone.", "The stone is aside.", "invented_success"),
    ("You open a secret door in the stone.", "The stone is aside.", "invented_success"),
    ("There is nothing opposing you in this situation.", "You step back from the milestone.", "irrelevant"),
    ("The gate is now open.", "The gate remains closed.", "dropped_outcome"),
]


@pytest.mark.parametrize("candidate,facts,reason", AUTHORITY, ids=[f"auth-{index}" for index in range(len(AUTHORITY))])
def test_authority_rejections_keep_their_reasons(candidate, facts, reason):
    verdict = validate_narration(candidate, facts, session={"clue_knowledge": {}})
    assert verdict["adopt"] is False
    assert reason in verdict["reasons"]


GROUNDED = [
    ("The weathered stone is still beside the northwest track.", "A weathered stone stands beside the northwest track."),
    ("You move the loose stone aside.", "You move the loose stone. It is now aside."),
    ("The mud prints remain where you found them.", "Faint mud prints circle the milestone."),
    ("You are still at the old milestone.", "You are at the old milestone."),
    ("The notice still names the missing patrol.", "The notice names a missing patrol."),
]


@pytest.mark.parametrize("candidate,facts", GROUNDED, ids=[f"ground-{index}" for index in range(len(GROUNDED))])
def test_grounded_paraphrase_is_accepted(candidate, facts):
    verdict = validate_narration(candidate, facts, session={"clue_knowledge": {}})
    assert verdict["adopt"] is True


EMPTY_CONTRACTS = [
    FINAL_ENGINE_RESPONSE,
    CLARIFICATION_REQUIRED,
    UNSUPPORTED_ACTION,
    FAILURE,
    ADJUDICATION_RESULT,
]


@pytest.mark.parametrize("contract", EMPTY_CONTRACTS, ids=[f"empty-{index}" for index in range(len(EMPTY_CONTRACTS))])
def test_contract_without_a_sentence_does_not_skip_primary(contract):
    meta = stamp({}, contract)
    assert narration_skip({"kind": "observe", "metadata": meta}, scene={}, session={}) is None


MORE_GROUNDED = [
    ("The old milestone is still in front of you.", "The old milestone stands in the mud."),
    ("You step back, leaving the milestone where it stands.", "You step back from the milestone."),
    ("The loose stone is now aside.", "The loose stone is aside."),
    ("No new place was created when you moved away.", "You move away. No new place was created."),
    ("The missing patrol is still only a notice.", "The notice names a missing patrol."),
    ("Faint prints still mark the mud.", "Faint prints mark the mud."),
    ("You remain beside the gate guard.", "You move beside the gate guard."),
    ("The closed gate stays closed.", "The gate is closed."),
]


@pytest.mark.parametrize("candidate,facts", MORE_GROUNDED, ids=[f"more-{index}" for index in range(len(MORE_GROUNDED))])
def test_more_committed_outcomes_can_be_paraphrased(candidate, facts):
    assert validate_narration(candidate, facts, session={"clue_knowledge": {}})["adopt"] is True


ACCOUNTING = [
    ([], 0, 0),
    ([{"event": "admitted", "attempt_id": "a"}], 0, 0),
    ([{"event": "completed", "attempt_id": "a", "sent": True, "total_tokens": 12, "input_tokens": 10, "output_tokens": 2}], 1, 12),
    ([{"event": "completed", "attempt_id": "a", "sent": False}], 0, 0),
    ([{"event": "completed", "attempt_id": "a", "sent": True, "total_tokens": 5, "retry_attempt": 1, "accepted": False, "input_tokens": 4, "output_tokens": 1}], 1, 5),
    ([{"event": "completed", "sent": True, "total_tokens": 3, "input_tokens": 2, "output_tokens": 1}, {"event": "completed", "sent": True, "total_tokens": 4, "input_tokens": 3, "output_tokens": 1}], 2, 7),
    ([{"event": "completed", "attempt_id": "same", "sent": True, "total_tokens": 9, "input_tokens": 8, "output_tokens": 1}, {"event": "completed", "attempt_id": "same", "sent": True, "total_tokens": 9, "input_tokens": 8, "output_tokens": 1}], 1, 9),
    ([{"event": "dispatch_attempted", "attempt_id": "z"}, {"event": "completed", "attempt_id": "z", "sent": True, "total_tokens": 6, "input_tokens": 5, "output_tokens": 1}], 1, 6),
]


@pytest.mark.parametrize("rows,requests,tokens", ACCOUNTING, ids=[f"acct-{index}" for index in range(len(ACCOUNTING))])
def test_provider_rows_are_counted_without_duplicate_traces(rows, requests, tokens):
    summary = summarize_provider_rows(rows)
    assert summary["requests"] == requests
    assert summary["total_tokens"] == tokens


def test_duplicate_provider_traces_count_once():
    rows = [
        {"event": "admitted", "attempt_id": "a", "purpose": "primary_turn"},
        {"event": "dispatch_attempted", "attempt_id": "a"},
        {"event": "completed", "attempt_id": "a", "sent": True, "input_tokens": 100, "output_tokens": 20, "total_tokens": 120, "accepted": True},
        {"event": "completed", "attempt_id": "a", "sent": True, "input_tokens": 100, "output_tokens": 20, "total_tokens": 120, "accepted": True},
        {"event": "completed", "attempt_id": "b", "sent": False, "total_tokens": 0},
        {"event": "completed", "attempt_id": "c", "sent": True, "retry_attempt": 1, "input_tokens": 40, "output_tokens": 10, "total_tokens": 50, "accepted": False},
    ]
    summary = summarize_provider_rows(rows)
    assert summary["requests"] == 2
    assert summary["input_tokens"] == 140
    assert summary["output_tokens"] == 30
    assert summary["total_tokens"] == 170
    assert summary["retries"] == 1
    assert summary["rejected_tokens"] == 50
    assert summary["fallbacks"] == 1


def test_duplicate_skip_does_not_call_expression_twice(monkeypatch):
    calls = {"n": 0}

    def _narrate(facts, session=None, scene=None):
        calls["n"] += 1
        return {"text": "You shift the loose stone aside."}

    monkeypatch.setattr("game.integrated_play.maybe_narrate", _narrate)
    meta = stamp({"engine_publication": "You move the loose stone. It is now aside."}, ADJUDICATION_RESULT)
    resolution = {"kind": "interact", "metadata": meta}
    deterministic_provider_skip_line(resolution=resolution, scene={}, world={}, session={}, player_text="move the stone")
    deterministic_provider_skip_line(resolution=resolution, scene={}, world={}, session={}, player_text="move the stone")
    assert calls["n"] == 1
