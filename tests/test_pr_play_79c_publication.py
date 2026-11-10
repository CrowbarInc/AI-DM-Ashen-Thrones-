"""PR-PLAY-79C dialogue publication and action-result fidelity.

Development checks. The frozen holdout is a separate file and is not this module.
"""
import copy

import pytest

from game.authored_action_language import decision_for, propose
from game.authored_consequences import ENROLLMENT
from game.bounded_improvisation import LEDGER_KEY
from game.expressive_dialogue import build_expression_prompt, validate_expression
from game.integrated_play import maybe_narrate, validate_narration
from game.physical_adjudication import commit_physical, plan_physical
from game.publication_contract import (
    ADJUDICATION_RESULT,
    CLARIFICATION_REQUIRED,
    FAILURE,
    FINAL_ENGINE_RESPONSE,
    LIVE_EXPRESSION_REQUESTED,
    UNSUPPORTED_ACTION,
    narration_skip,
    summarize_provider_rows,
)
from tests.test_pr_play_76_physical import add, door, enable, stage
from tests.test_pr_play_78_integrated import play
from tests.test_pr_play_78a_authored import _scene, _world
from tests.test_pr_play_79a_continuity import gate


@pytest.fixture
def ready(monkeypatch):
    enable(monkeypatch)
    monkeypatch.setenv("ASHEN_EXPERIMENTAL_DYNAMIC_NPCS", "1")
    monkeypatch.setenv("ASHEN_EXPERIMENTAL_INTEGRATED_NARRATION", "1")
    monkeypatch.setenv("ASHEN_BOUNDED_SPEECH", "1")
    return gate()


def _say(session, scene, world, text):
    _plan, result, said, changed = play(text, session, scene, world)
    return said, result, changed


def _physical(text, session, scene):
    world = {"npcs": [], "world_state": {"flags": {}}}
    plan = plan_physical(text, session=session, scene=scene, world=world)
    result = None
    if plan and plan.get("mode") == "interact":
        result = commit_physical(
            scene, session, world, {"id": plan["id"], "target_id": plan["id"]},
            prompt=text, action_id=plan["id"], label="physical",
        )
    said = ""
    if result:
        said = result["metadata"]["engine_publication"]
    elif plan:
        said = plan.get("message") or ""
    return plan, result, said


SPEECH = [
    ("Hello, Gate Guard.", "hello", "says"),
    ("Who are you?", "gate guard", "says"),
    ("What do you know about the missing patrol?", "do not know", "says"),
    ("When did you last hear about them?", "not certain", "says"),
    ("Do you think something happened?", "not certain", "says"),
    ("What is this place like?", "notice board", "says"),
    ("What about the patrol again?", "missing patrol", "says"),
    ("You mentioned the patrol earlier. What else?", "missing patrol", "says"),
    ("Thank you.", "thank", "says"),
    ("Goodbye.", "goodbye", "says"),
]


@pytest.mark.parametrize("text,present,marker", SPEECH, ids=[f"speech-{index}" for index in range(len(SPEECH))])
def test_accepted_host_speech_is_what_the_player_reads(ready, monkeypatch, text, present, marker):
    calls = {"n": 0}

    def _rewrite(facts, session=None, scene=None):
        calls["n"] += 1
        return {"text": "The Gate Guard stands by the notice board and watches the crowd."}

    monkeypatch.setattr("game.integrated_play.maybe_narrate", _rewrite)
    session, scene, world = ready
    _say(session, scene, world, "Hello, Gate Guard.")
    calls["n"] = 0
    said, result, _changed = _say(session, scene, world, text)
    low = said.casefold()
    assert present in low
    assert marker in low
    assert "stands by the notice board and watches" not in low
    assert calls["n"] == 0
    assert result["metadata"]["publication_contract"] == FINAL_ENGINE_RESPONSE
    assert result["metadata"]["skip_primary_narration"] is True
    trace = session["last_publication"]
    assert trace["dialogue_published"] is True
    assert trace["narration_requested"] is False
    assert trace["visible"] == said


def _allow_expression(monkeypatch, text):
    monkeypatch.setattr("game.expressive_dialogue.expression_generation_disabled", lambda: False)

    def _reply(_contract):
        return {"ok": True, "sent": True, "text": text, "usage": {}, "latency_ms": 1}

    monkeypatch.setattr("game.expressive_dialogue.request_expression", _reply)


def test_provider_speech_is_published_without_a_narration_call(ready, monkeypatch):
    calls = {"n": 0}

    def _rewrite(facts, session=None, scene=None):
        calls["n"] += 1
        return {"text": "The guard looks toward you."}

    monkeypatch.setattr("game.integrated_play.maybe_narrate", _rewrite)
    _allow_expression(monkeypatch, "Evening. What can I do for you?")
    session, scene, world = ready
    said, result, _changed = _say(session, scene, world, "Hello, Gate Guard.")
    assert 'Gate Guard says, "Evening. What can I do for you?"' == said
    assert calls["n"] == 0
    assert result["metadata"]["integrated_play"]["live_dialogue"] is True
    assert session["last_publication"]["dialogue_accepted"] is True
    assert session["last_publication"]["dialogue_published"] is True


def test_uncertain_provider_line_must_say_it_does_not_know(ready, monkeypatch):
    _allow_expression(monkeypatch, "I do not know anything beyond the warning about a missing patrol.")
    session, scene, world = ready
    _say(session, scene, world, "Hello, Gate Guard.")
    said, _result, _changed = _say(session, scene, world, "What do you know about the missing patrol?")
    low = said.casefold()
    assert "i do not know" in low
    assert "says" in low
    assert "northwest" not in low
    assert session["last_background_expression"]["adopted"] is True


def test_hidden_route_is_not_spoken(ready, monkeypatch):
    _allow_expression(monkeypatch, "They were last seen taking the northwest mud track.")
    session, scene, world = ready
    _say(session, scene, world, "Hello, Gate Guard.")
    said, _result, _changed = _say(session, scene, world, "What do you know about the missing patrol?")
    assert "northwest" not in said.casefold()
    assert session["last_background_expression"]["adopted"] is False
    assert "do not know" in said.casefold()


def test_empty_provider_line_keeps_the_host_sentence(ready, monkeypatch):
    _allow_expression(monkeypatch, "   ")
    session, scene, world = ready
    said, _result, _changed = _say(session, scene, world, "Hello, Gate Guard.")
    assert 'Gate Guard says, "Hello."' == said
    assert session["last_background_expression"]["adopted"] is False


def test_malformed_provider_symbols_are_not_published(ready, monkeypatch):
    _allow_expression(monkeypatch, "The speech authority allows a different answer.")
    session, scene, world = ready
    said, _result, _changed = _say(session, scene, world, "Hello, Gate Guard.")
    assert "speech authority" not in said.casefold()
    assert "hello" in said.casefold()
    assert session["last_background_expression"]["adopted"] is False


def test_looking_and_speaking_keeps_the_speech(ready, monkeypatch):
    monkeypatch.setattr(
        "game.integrated_play.maybe_narrate",
        lambda facts, session=None, scene=None: {"text": "You take in the gate."},
    )
    session, scene, world = ready
    said, result, _changed = _say(session, scene, world, "Look around and ask the Gate Guard who they are.")
    low = said.casefold()
    assert "you take in the gate." in low
    assert "says" in low
    assert "gate guard" in low
    assert result["metadata"]["integrated_play"]["dialogue_published"] is True
    assert session["last_publication"]["narration_published"] is True


def test_look_around_can_still_use_live_narration(ready, monkeypatch):
    monkeypatch.setattr(
        "game.integrated_play.maybe_narrate",
        lambda facts, session=None, scene=None: {"text": "Rain beads on the notice board."},
    )
    session, scene, world = ready
    said, _result, _changed = _say(session, scene, world, "Look around.")
    assert said == "Rain beads on the notice board."
    assert session["last_publication"]["narration_requested"] is True
    assert session["last_publication"]["dialogue_published"] is False


def test_speech_is_not_duplicated(ready):
    session, scene, world = ready
    said, _result, _changed = _say(session, scene, world, "Hello, Gate Guard.")
    assert said.casefold().count("hello") == 1


def test_six_turns_keep_the_same_speaker(ready):
    session, scene, world = ready
    lines = [
        "Hello, Gate Guard.",
        "Who are you?",
        "What do you know about the missing patrol?",
        "When did you last hear about them?",
        "Do you think something happened?",
        "What about the patrol again?",
    ]
    for text in lines:
        said, _result, _changed = _say(session, scene, world, text)
        assert "gate guard says" in said.casefold()
        assert "northwest" not in said.casefold()
    assert session["conversational_context"]["active_interlocutor"]["npc_id"] == "gate_guard"


def test_switch_names_the_new_speaker(ready):
    session, scene, world = ready
    _say(session, scene, world, "Hello, Gate Guard.")
    said, _result, _changed = _say(session, scene, world, "Hello, Gate Serjeant.")
    assert "gate serjeant says" in said.casefold()
    who, _result, _changed = _say(session, scene, world, "Who are you?")
    assert "gate serjeant" in who.casefold()
    assert "i am gate guard," not in who.casefold()


def test_goodbye_ends_the_exchange(ready):
    session, scene, world = ready
    _say(session, scene, world, "Hello, Gate Guard.")
    said, _result, _changed = _say(session, scene, world, "Goodbye.")
    assert "goodbye" in said.casefold()
    assert session["conversational_context"]["active_interlocutor"]["status"] == "ended"


def test_leaving_the_scene_drops_the_guard(ready):
    session, scene, world = ready
    _say(session, scene, world, "Hello, Gate Guard.")
    session["active_scene_id"] = "old_milestone"
    later = {"scene": {"id": "old_milestone", "visible_facts": ["A stone milestone leans beside the road."], "interactables": [], "addressables": []}}
    said, _result, _changed = _say(session, later, world, "What about the patrol again?")
    assert session[LEDGER_KEY]["npc_focus"] is None
    assert "gate guard says" not in said.casefold()


def test_other_campaign_does_not_keep_the_speaker(ready):
    session, scene, world = ready
    _say(session, scene, world, "Hello, Gate Guard.")
    other = {
        "campaign_run_id": "beta",
        "active_scene_id": "frontier_gate",
        "turn_counter": 2,
        ENROLLMENT: "beta",
        LEDGER_KEY: {"entries": [], "physical_state": {}, "investigation_notes": []},
    }
    said, _result, _changed = _say(other, scene, world, "Who are you?")
    assert "i am gate guard" not in said.casefold()
    assert session["conversational_context"]["active_interlocutor"]["npc_id"] == "gate_guard"
    assert other.get("conversational_context", {}).get("active_interlocutor", {}).get("npc_id") != "gate_guard"


def test_notice_memory_and_place_are_not_guard_refusals(ready):
    session, scene, world = ready
    _say(session, scene, world, "Hello, Gate Guard.")
    for text in ("What does the notice board say?", "Where am I?", "What do I know about the patrol?"):
        assert decision_for(text, scene=scene, world=world, session=session) is None


def test_report_sentence_can_still_select_the_authored_action(monkeypatch):
    enable(monkeypatch)
    session, scene = _scene("old_milestone")
    got = propose("I report the uncertain trail to the watch.", scene=scene, world=_world(), session=session)
    assert got["kind"] == "execute"
    assert got["id"] == "patrol_report"


def test_survey_question_does_not_take_the_branch(monkeypatch):
    enable(monkeypatch)
    session, scene = _scene("old_milestone")
    got = propose("Can I survey the trail yet?", scene=scene, world=_world(), session=session)
    assert got["kind"] == "answer"


def test_copied_session_still_answers_the_guard(ready):
    session, scene, world = ready
    _say(session, scene, world, "Hello, Gate Guard.")
    _say(session, scene, world, "What do you know about the missing patrol?")
    restored = copy.deepcopy(session)
    said, _result, _changed = _say(restored, scene, world, "What about the patrol again?")
    assert "missing patrol" in said.casefold()
    assert "says" in said.casefold()
    assert session["conversational_context"]["active_interlocutor"]["npc_id"] == "gate_guard"


def test_uncertainty_prompt_requires_the_marker():
    prompt = build_expression_prompt({
        "operation": "bounded_social_line",
        "speaker_name": "Gate Guard",
        "player_question": "What do you know about the missing patrol?",
        "authorized_propositions": ["The notice board lists a warning about a missing patrol."],
        "knowledge_posture": "unknown",
    })
    assert "I do not know" in prompt["user"]
    assert "not certain" in prompt["user"]


def test_greeting_prompt_does_not_demand_uncertainty():
    prompt = build_expression_prompt({
        "operation": "bounded_social_line",
        "speaker_name": "Gate Guard",
        "player_question": "Hello, Gate Guard.",
        "authorized_propositions": ["Hello."],
        "knowledge_posture": "delivered",
    })
    assert "must include" not in prompt["user"]


def _yard():
    session, scene, _world = stage()
    scene["scene"]["interactables"].append(
        {"id": "milestone", "label": "Weathered milestone", "aliases": ["milestone"]}
    )
    return session, scene


PHYSICAL = [
    ("step-back-noop", "I step back from the milestone.", False, "position is unchanged", "not up against"),
    ("step-back-bare", "I step back.", False, "not beside anything", "not up against"),
    ("open", "I open the door.", True, "you open", "hidden"),
    ("already", "I open the door.", False, "already open", "secret"),
    ("move-unknown", "I try to move the door.", False, "not established", "you move the"),
    ("climb", "I climb the milestone.", False, "no climbing check", "you reach"),
    ("wait", "I wait and watch the road.", False, "nothing new approaches", "ambush"),
    ("struggle", "I look for signs of a struggle.", False, "no signs of a struggle", "blood"),
]


@pytest.mark.parametrize("name,text,commit,present,absent", PHYSICAL, ids=[row[0] for row in PHYSICAL])
def test_physical_publication_matches_the_outcome(ready, name, text, commit, present, absent):
    session, scene = _yard()
    if name in {"open", "already", "move-unknown"}:
        add(session, ident="door", label="wooden door", aliases=["door"], **door())
    if name == "already":
        _physical("I open the door.", session, scene)
    if name in {"wait", "struggle"}:
        said, result, changed = _say(session, scene, {"npcs": [], "world_state": {"flags": {}}}, text)
        assert present in said.casefold()
        assert absent not in said.casefold()
        assert changed is commit
        return
    _plan, result, said = _physical(text, session, scene)
    low = said.casefold()
    assert present in low
    assert absent not in low
    assert bool(result and result["state_changes"]["mutation"]) is commit


def test_step_back_after_approach_names_the_milestone(ready):
    session, scene = _yard()
    _physical("I approach the milestone.", session, scene)
    _plan, result, said = _physical("I step back from the milestone.", session, scene)
    assert said == "You step back from the Weathered milestone."
    assert result["state_changes"]["mutation"] is True
    assert session[LEDGER_KEY]["position"]["kind"] == "back"


def test_step_back_from_the_wrong_object_does_not_move(ready):
    session, scene = _yard()
    add(session, ident="bench", label="wooden bench", aliases=["bench"], use="seat")
    _physical("I approach the bench.", session, scene)
    _plan, result, said = _physical("I step back from the milestone.", session, scene)
    assert "was not taken" in said.casefold()
    assert "unchanged" in said.casefold()
    assert result["state_changes"]["mutation"] is False
    assert session[LEDGER_KEY]["position"]["kind"] == "beside"


def test_second_step_back_is_a_no_op(ready):
    session, scene = _yard()
    _physical("I approach the milestone.", session, scene)
    _physical("I step back from the milestone.", session, scene)
    _plan, result, said = _physical("I step back from the milestone.", session, scene)
    assert "already back" in said.casefold()
    assert "unchanged" in said.casefold()
    assert result["state_changes"]["mutation"] is False


def test_two_crates_ask_which_one(ready):
    session, scene = _yard()
    add(session, ident="a", label="oak crate", aliases=["crate"], mobility="movable", weight="light")
    add(session, ident="b", label="pine crate", aliases=["crate"], mobility="movable", weight="light")
    plan, result, said = _physical("Push the crate.", session, scene)
    assert plan["mode"] == "clarify"
    assert result is None
    assert "which" in said.casefold()
    assert session[LEDGER_KEY].get("physical_state", {}) == {}


def test_failed_check_does_not_open_the_door(ready):
    session, scene = _yard()
    add(session, ident="door", label="stuck door", aliases=["door"], **door(), skill_check={"skill_id": "athletics", "dc": 30})
    _plan, result, said = _physical("I open the door.", session, scene)
    assert "fails" in said.casefold()
    assert result["success"] is False
    assert result["state_changes"]["mutation"] is False


def test_marker_touch_and_aside_are_not_invented(ready):
    session, scene = _yard()
    before = copy.deepcopy(session[LEDGER_KEY])
    for text in ("I leave a marker.", "I touch the milestone.", "I move aside.", "I wait briefly."):
        plan = plan_physical(text, session=session, scene=scene, world={"npcs": []})
        assert plan is None
        assert session[LEDGER_KEY] == before


def test_following_visible_tracks_does_not_change_place(ready):
    session, scene = _yard()
    scene["scene"]["visible_facts"] = ["Faint tracks mark the mud beside the milestone."]
    said, _result, changed = _say(session, scene, {"npcs": [], "world_state": {"flags": {}}}, "I follow the tracks.")
    assert "faint tracks mark the mud" in said.casefold()
    assert changed is False
    assert session["active_scene_id"] == "yard"


def test_rejected_narration_keeps_the_step_back_sentence(ready, monkeypatch):
    monkeypatch.setattr("game.integrated_play.maybe_narrate", lambda *args, **kwargs: None)
    session, scene = _yard()
    from game.bounded_improvisation import resolve_controlled_fact, controlled_request
    text = "I step back from the milestone."
    plan = controlled_request(text, session=session, scene=scene, world={"npcs": []})
    result = resolve_controlled_fact(
        scene, session, {"npcs": []}, {"id": plan["id"], "target_id": plan["id"]},
        prompt=text, action_id=plan["id"], label="physical",
    )
    said = result["metadata"]["engine_publication"]
    assert "step back from the milestone" in said.casefold()
    assert "unchanged" in said.casefold()
    assert "not up against" not in said.casefold()


NARRATION = [
    ("The guard looks toward you.", 'Gate Guard says, "Evening. What can I do for you?"', False, "dropped_speech"),
    ("The guard glances over. \"Evening. What can I do for you?\"", 'Gate Guard says, "Evening. What can I do for you?"', True, ""),
    ("You step back from the milestone.", "You try to step back from the milestone. You are not beside it, so your position is unchanged.", False, "invented_success"),
    ("You are not up against anything here.", "You try to step back from the milestone. You are not beside it, so your position is unchanged.", False, "irrelevant"),
    ("You stay put, not beside the milestone, and your position is unchanged.", "You try to step back from the milestone. You are not beside it, so your position is unchanged.", True, ""),
    ("You step back, leaving the milestone where it stands.", "You step back from the milestone.", True, ""),
    ("You discover a hidden camp past the stone.", "Tracks lead northwest.", False, "consequential_or_hidden"),
    ("You find gold under the milestone.", "The stone is aside.", False, "consequential_or_hidden"),
    ("The tracks bend southeast from the stone.", "Tracks lead northwest.", False, "unestablished_direction"),
    ("You climb the milestone.", "The stone is aside.", False, "invented_success"),
    ("The gate is now open.", "The gate remains closed.", False, "dropped_outcome"),
    ("You are given a reward of silver.", "You look around the yard.", False, "consequential_or_hidden"),
]


@pytest.mark.parametrize("candidate,facts,adopt,reason", NARRATION, ids=[f"narr-{index}" for index in range(len(NARRATION))])
def test_narration_keeps_speech_and_the_committed_outcome(candidate, facts, adopt, reason):
    verdict = validate_narration(candidate, facts, session={"clue_knowledge": {}})
    assert verdict["adopt"] is adopt
    if reason:
        assert reason in verdict["reasons"]


def test_relevant_live_narration_can_publish():
    verdict = validate_narration(
        "You move the loose stone aside.",
        "You move the loose stone. It is now aside.",
        session={"clue_knowledge": {}},
    )
    assert verdict["adopt"] is True


CONTRACTS = [
    FINAL_ENGINE_RESPONSE,
    CLARIFICATION_REQUIRED,
    UNSUPPORTED_ACTION,
    FAILURE,
    ADJUDICATION_RESULT,
    LIVE_EXPRESSION_REQUESTED,
]


@pytest.mark.parametrize("contract", CONTRACTS, ids=[f"contract-{index}" for index in range(len(CONTRACTS))])
def test_a_contract_without_a_sentence_does_not_skip(contract):
    skipped = narration_skip({"kind": "observe", "metadata": {"publication_contract": contract}}, scene={}, session={})
    assert skipped is None


def test_final_engine_sentence_skips_primary_narration():
    skipped = narration_skip(
        {"kind": "interact", "metadata": {
            "publication_contract": FINAL_ENGINE_RESPONSE,
            "engine_publication": 'Gate Guard says, "Hello."',
        }},
        scene={}, session={},
    )
    assert skipped[0] == 'Gate Guard says, "Hello."'
    assert skipped[1] == "publication_contract"


def test_read_only_question_does_not_move(ready):
    session, scene = _yard()
    add(session, ident="bench", label="wooden bench", aliases=["bench"], use="seat")
    _physical("I approach the bench.", session, scene)
    before = copy.deepcopy(session[LEDGER_KEY]["position"])
    plan, result, said = _physical("Am I beside the bench?", session, scene)
    assert result is None
    assert "beside" in said.casefold()
    assert session[LEDGER_KEY]["position"] == before


def test_hidden_sentinel_is_absent_from_the_greeting(ready):
    session, scene, world = ready
    scene["scene"]["hidden_facts"].append("SENTINEL_HIDDEN_PAYROLL")
    said, _result, _changed = _say(session, scene, world, "Hello, Gate Guard.")
    assert "sentinel" not in said.casefold()
    assert "payroll" not in said.casefold()


def test_provider_rows_ignore_duplicate_traces():
    rows = [
        {"event": "admitted", "attempt_id": "a"},
        {"event": "completed", "attempt_id": "a", "sent": True, "input_tokens": 10, "output_tokens": 2, "total_tokens": 12, "accepted": True},
        {"event": "completed", "attempt_id": "a", "sent": True, "input_tokens": 10, "output_tokens": 2, "total_tokens": 12, "accepted": True},
        {"event": "completed", "attempt_id": "b", "sent": False},
        {"event": "completed", "attempt_id": "c", "sent": True, "retry_attempt": 1, "input_tokens": 4, "output_tokens": 1, "total_tokens": 5, "accepted": False},
    ]
    summary = summarize_provider_rows(rows)
    assert summary["requests"] == 2
    assert summary["input_tokens"] == 14
    assert summary["output_tokens"] == 3
    assert summary["retries"] == 1
    assert summary["fallbacks"] == 1
    assert summary["rejected_tokens"] == 5


def test_expression_validator_rejects_an_empty_line():
    verdict = validate_expression("", {"operation": "bounded_social_line", "knowledge_posture": "delivered", "authorized_propositions": ["Hello."]})
    assert verdict["adopt"] is False


def test_narration_helper_stays_available_for_a_committed_fact(ready, monkeypatch):
    monkeypatch.setattr("game.expressive_dialogue.expression_generation_disabled", lambda: False)
    monkeypatch.setattr(
        "game.expressive_dialogue.request_expression",
        lambda _contract: {"ok": True, "text": "You move up beside the milestone.", "usage": {}, "latency_ms": 1},
    )
    session, scene = _yard()
    spoken = maybe_narrate("You move beside the milestone.", session=session, scene=scene)
    assert spoken["text"] == "You move up beside the milestone."


MORE = [
    ("I sit on the bench.", "bench", "you sit", True),
    ("I stand up.", "bench", "already standing", False),
    ("Where is the bench?", "bench", "no position is established", False),
    ("Could I open the door?", "door", "is closed", False),
    ("I close the door.", "open-door", "already closed", False),
    ("I push the pillar.", "pillar", "cannot be moved", False),
    ("I sit on the bench.", "far", "not accessible", False),
    ("Push it.", "one-crate", "which object", False),
    ("I lift the cup.", "cup", "raised", True),
    ("I place the cup aside.", "cup-lifted", "aside", True),
]


@pytest.mark.parametrize("text,setup,present,commit", MORE, ids=[f"more-{index}" for index in range(len(MORE))])
def test_more_physical_results_stay_specific(ready, text, setup, present, commit):
    session, scene = _yard()
    if setup == "bench":
        add(session, ident="bench", label="wooden bench", aliases=["bench"], use="seat")
    elif setup == "door":
        add(session, ident="door", label="wooden door", aliases=["door"], **door())
    elif setup == "open-door":
        add(session, ident="door", label="wooden door", aliases=["door"], **door())
    elif setup == "pillar":
        add(session, ident="pillar", label="stone pillar", aliases=["pillar"], mobility="immovable")
    elif setup == "far":
        add(session, ident="bench", label="wooden bench", aliases=["bench"], use="seat", accessible=False)
    elif setup == "one-crate":
        add(session, ident="crate", label="oak crate", aliases=["crate"], mobility="movable", weight="light", position="by the wall")
    elif setup in {"cup", "cup-lifted"}:
        add(session, ident="cup", label="wooden cup", aliases=["cup"], mobility="movable", weight="light", position="on the table")
        if setup == "cup-lifted":
            _physical("I lift the cup.", session, scene)
    _plan, result, said = _physical(text, session, scene)
    assert present in said.casefold()
    if result is None:
        assert commit is False
    else:
        assert bool(result["state_changes"]["mutation"]) is commit


def test_dialogue_after_a_look_still_names_the_guard(ready):
    session, scene, world = ready
    _say(session, scene, world, "Hello, Gate Guard.")
    _say(session, scene, world, "Look around.")
    said, _result, _changed = _say(session, scene, world, "Who are you?")
    assert "gate guard says" in said.casefold()
    assert "northwest" not in said.casefold()


def test_unsupported_gesture_does_not_claim_success(ready):
    session, scene = _yard()
    plan, result, said = _physical("I wave at the milestone.", session, scene)
    if plan is None:
        assert result is None
        assert said == ""
    else:
        assert "not" in said.casefold()
        assert not (result and result["state_changes"]["mutation"])
