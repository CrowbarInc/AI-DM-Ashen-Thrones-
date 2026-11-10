"""PR-PLAY-77 bounded multi-step intent. Unsupported mechanics stay refusals."""
import copy
import json

import pytest

from game import storage
from game.authored_consequences import ENROLLMENT
from game.bounded_improvisation import LEDGER_KEY
from game.physical_adjudication import (
    commit_physical, interpret_plan_with_provider, plan_physical, validate_provider_plan,
)
from tests.test_pr_play_76_matrix import build
from tests.test_pr_play_76_physical import act, add, door, enable, said, stage


def _steps(result):
    if not result:
        return []
    return result["metadata"]["physical_adjudication"]["step_results"]


def _status(result, index):
    return _steps(result)[index]["status"]


@pytest.fixture
def ready(monkeypatch):
    enable(monkeypatch)
    return stage()


CASES = [
    ("I open the door.", "door", "A", "yes", "you open", None),
    ("I stand up and approach the bench.", "bench", "A", "yes", "beside", "SUCCEEDED"),
    ("Open the door and look inside.", "door", "A", "yes", "nothing concealed", "SUCCEEDED"),
    ("I push the crate away from the doorway and check the doorway.", "blocking", "A", "yes", "the doorway is clear", "SUCCEEDED"),
    ("I sit on the bench and stand up.", "bench", "A", "yes", "you stand", "SUCCEEDED"),
    ("I lift the cup and place the cup aside.", "cup", "A", "yes", "aside", "SUCCEEDED"),
    ("I approach the bench and sit on it.", "bench", "A", "yes", "you sit", "SUCCEEDED"),
    ("First open the door, then look inside.", "door", "A", "yes", "nothing concealed", "SUCCEEDED"),
    ("I will open the door and then look inside.", "door", "A", "yes", "you open", "SUCCEEDED"),
    ("Please open the door and look inside.", "door", "A", "yes", "nothing concealed", "SUCCEEDED"),
    ("I open the hatch and sit on the bench.", "bench", "E", "no", "not attempted", None),
    ("I open the locked door and look inside.", "locked", "D", "no", "not attempted", None),
    ("I push the crate and open the hatch.", "crate", "A", "yes", "not established", "FAILED"),
    ("I open the door and climb the milestone.", "door_milestone", "A", "yes", "no climbing check", "UNSUPPORTED"),
    ("Shut the door and look inside.", "open", "A", "yes", "nothing concealed", "SUCCEEDED"),
    ("I stand up and approach the bench.", "bench", "A", "yes", "beside the wooden bench", "SUCCEEDED"),
    ("Move the crate aside, then inspect it.", "crate", "A", "yes", "aside", "SUCCEEDED"),
    ("I approach the bench and read it.", "bench", "A", "yes", "beside", "SUCCEEDED"),
    ("I push the crate aside and look where it was.", "crate", "A", "yes", "aside", "SUCCEEDED"),
    ("If the door opens, look inside.", "door", "A", "no", "skipped", None),
    ("If the door opens, look inside.", "open", "A", "yes", "nothing concealed", None),
    ("If the crate moves, step through.", "crate", "A", "no", "skipped", None),
    ("If I can reach the ledge, try to climb it.", "milestone", "D", "no", "not established", None),
    ("I open the locked door and stand up.", "locked", "A", "yes", "locked", "SUCCEEDED"),
    ("I open the locked door and wave to the guard.", "locked", "D", "no", "not attempted", None),
    ("I sit on the bench.", "none", "E", "no", "not established", None),
    ("I sit on the bench.", "two_seats", "F", "no", "which seat", None),
    ("I sit down.", "two_seats", "F", "no", "which seat", None),
    ("I push the crate.", "two", "F", "no", "which do you mean", None),
    ("I open the hidden chest.", "hidden", "E", "no", "not established", None),
    ("Is the door open, and what is on the other side?", "door", "A", "no", "nothing was opened", None),
    ("Is the door open and what is on the other side?", "open", "A", "no", "nothing was opened", None),
    ("I stand up, approach the bench, sit on the bench, and step back.", "bench", "F", "no", "more than three", None),
    ("Open the door, wave, climb the milestone, and look around.", "door_milestone", "F", "no", "nothing has been attempted", None),
    ("I climb the milestone.", "milestone", "D", "no", "no climbing check", None),
    ("I pick up the cup and examine it.", "cup", "D", "no", "inventory", None),
    ("Can I move the crate, and is it heavy?", "crate", "A", "no", "nothing has been moved", None),
    ("I break the door and look inside.", "door", "C", "no", "not attempted", None),
    ("I teleport through the wall and sit.", "bench", "E", "no", "solid barrier", None),
    ("I push the pillar and stand up.", "pillar", "A", "yes", "cannot be moved", "SUCCEEDED"),
]


def _setup(name, session, scene):
    if name == "door_milestone":
        add(session, ident="door", label="wooden door", aliases=["door"], **door())
        scene["scene"]["interactables"].append({"id": "milestone", "label": "Weathered milestone", "aliases": ["milestone"]})
        return
    build(name, session, scene)


@pytest.mark.parametrize("text,setup,category,commit,fragment,later", CASES, ids=[f"S{i:02d}" for i in range(len(CASES))])
def test_sequence_case(ready, text, setup, category, commit, fragment, later):
    session, scene, _packed = ready
    _setup(setup, session, scene)
    before = copy.deepcopy(session[LEDGER_KEY])
    plan, result, _ = act(text, session, scene)
    assert plan is not None and plan["category"] == category
    assert fragment in said(plan, result).casefold()
    assert "SENTINEL" not in said(plan, result)
    if commit == "yes":
        assert result and result["success"] in {True, False}
        if later:
            assert _steps(result)[-1]["status"] == later
    else:
        assert result is None
        assert session[LEDGER_KEY]["physical_consequences"] == before["physical_consequences"]


def test_three_step_partial_success_keeps_the_move(ready):
    session, scene, packed = ready
    add(session, ident="crate", label="oak crate", aliases=["crate"], mobility="movable", weight="light", position="by the wall")
    scene["scene"]["interactables"].append({"id": "milestone", "label": "Weathered milestone", "aliases": ["milestone"]})
    plan, result, _ = act("I push the crate aside, climb the milestone, and look down the road.", session, scene, packed)
    assert result and "aside" in said(plan, result).casefold()
    assert "no climbing check" in said(plan, result).casefold()
    assert "not attempted" in said(plan, result).casefold()
    assert "hidden road" not in said(plan, result).casefold()
    assert session[LEDGER_KEY]["entries"][0]["properties"]["position"].startswith("aside")
    assert (session[LEDGER_KEY].get("position") or {}).get("kind") != "elevated"
    assert [step["status"] for step in _steps(result)] == ["SUCCEEDED", "UNSUPPORTED", "BLOCKED"]


def test_open_step_through_and_look_does_not_invent_a_room(ready):
    session, scene, packed = ready
    add(session, ident="door", label="wooden door", aliases=["door"], **door())
    plan, result, _ = act("Open the door, step through, and look around.", session, scene, packed)
    text = said(plan, result).casefold()
    assert "you open" in text and "no passage" in text and "not attempted" in text
    assert "room" not in text or "no hidden road, room" in text or "no passage" in text
    assert session[LEDGER_KEY]["entries"][0]["properties"]["open"] is True
    assert [step["status"] for step in _steps(result)] == ["SUCCEEDED", "UNSUPPORTED", "BLOCKED"]


def test_dependent_observation_does_not_run_after_failed_check(ready):
    session, scene, packed = ready
    add(session, ident="door", label="stuck door", aliases=["door"], **door(), skill_check={"skill_id": "athletics", "dc": 30})
    plan, result, _ = act("I open the door and look inside.", session, scene, packed)
    assert result["success"] is False
    assert result["skill_check"]["difficulty"] == 30
    assert "attempt fails" in said(plan, result).casefold()
    assert "nothing concealed" not in said(plan, result).casefold()
    assert session[LEDGER_KEY]["entries"][0]["properties"]["open"] is False
    assert _status(result, 1) == "BLOCKED"


def test_conditional_after_a_successful_open(ready):
    session, scene, packed = ready
    add(session, ident="door", label="wooden door", aliases=["door"], **door())
    plan, result, _ = act("Open the door, and if it opens, look inside.", session, scene, packed)
    assert "you open" in said(plan, result).casefold()
    assert "nothing concealed" in said(plan, result).casefold()
    assert _status(result, 1) == "SUCCEEDED"


def test_conditional_false_does_not_open_or_look(ready):
    session, scene, packed = ready
    add(session, ident="door", label="wooden door", aliases=["door"], **door())
    before = copy.deepcopy(session)
    plan, result, _ = act("If the door opens, look inside.", session, scene, packed)
    assert result is None and "skipped" in said(plan, None).casefold()
    assert session[LEDGER_KEY]["entries"] == before[LEDGER_KEY]["entries"]


def test_unknown_condition_does_not_invent_success(ready):
    session, scene, packed = ready
    before = copy.deepcopy(session)
    plan, result, _ = act("If I can reach the ledge, try to climb it.", session, scene, packed)
    assert result is None and "not established" in said(plan, None).casefold()
    assert "dc" not in said(plan, None).casefold()
    assert session[LEDGER_KEY] == before[LEDGER_KEY]


def test_missing_named_seat_is_not_a_clarification(ready):
    session, scene, packed = ready
    add(session, ident="bench", label="wooden bench", aliases=["bench"], use="seat", scene_id="yard")
    session["campaign_run_id"] = "beta"
    session[ENROLLMENT] = "beta"
    add(session, ident="stool", label="low stool", aliases=["stool"], use="seat")
    plan, result, _ = act("I sit on the bench.", session, scene, packed)
    assert plan["category"] == "E" and result is None
    assert "which seat" not in said(plan, None).casefold()
    assert "not established" in said(plan, None).casefold()
    assert "posture" not in session[LEDGER_KEY]


def test_zero_seats_are_not_found_and_two_seats_stay_ambiguous(ready):
    session, scene, packed = ready
    plan, result, _ = act("I sit on the bench.", session, scene, packed)
    assert plan["category"] == "E" and "not established" in said(plan, None).casefold()
    add(session, ident="a", label="oak bench", aliases=["bench"], use="seat")
    add(session, ident="b", label="pine bench", aliases=["bench"], use="seat")
    plan, result, _ = act("I sit on the bench.", session, scene, packed)
    assert plan["category"] == "F" and result is None and "which seat" in said(plan, None).casefold()


def test_shared_target_is_not_duplicated(ready):
    session, scene, packed = ready
    add(session, ident="crate", label="oak crate", aliases=["crate"], mobility="movable", weight="light", position="by the wall")
    act("Move the crate aside and inspect it.", session, scene, packed)
    assert len(session[LEDGER_KEY]["entries"]) == 1
    assert len([item for item in session[LEDGER_KEY]["physical_consequences"] if item["target_id"] == "crate"]) == 1


def test_read_only_compound_does_not_mutate(ready):
    session, scene, packed = ready
    add(session, ident="door", label="wooden door", aliases=["door"], **door())
    before = copy.deepcopy(session[LEDGER_KEY])
    plan, result, _ = act("Is the door open, and what is on the other side?", session, scene, packed)
    assert result is None and session[LEDGER_KEY] == before
    assert "closed" in said(plan, None).casefold() and "nothing was opened" in said(plan, None).casefold()


def test_combat_blocks_the_sequence_and_not_a_single_action(ready, monkeypatch):
    session, scene, packed = ready
    add(session, ident="door", label="wooden door", aliases=["door"], **door())
    monkeypatch.setattr("game.storage.load_combat", lambda: {"in_combat": True})
    plan, result, _ = act("I open the door and look inside.", session, scene, packed)
    assert result is None and "combat" in said(plan, None).casefold()
    plan, result, _ = act("I open the door.", session, scene, packed)
    assert result and result["success"] is True


def test_save_resume_keeps_partial_success_and_does_not_resume(ready):
    session, scene, packed = ready
    add(session, ident="crate", label="oak crate", aliases=["crate"], mobility="movable", weight="light", position="by the wall")
    scene["scene"]["interactables"].append({"id": "milestone", "label": "Weathered milestone", "aliases": ["milestone"]})
    act("I push the crate aside, climb the milestone, and look down the road.", session, scene, packed)
    assert session[LEDGER_KEY]["physical_plans"][-1]["automatic_resume"] is False
    storage.save_session(session)
    restored = storage.load_session()
    assert restored[LEDGER_KEY]["entries"][0]["properties"]["position"].startswith("aside")
    plan, result, _ = act("continue", restored, scene, packed)
    assert result is None and "resumes" in said(plan, None).casefold()
    assert len(restored[LEDGER_KEY]["physical_consequences"]) == 1


def test_repeated_open_does_not_duplicate_the_consequence(ready):
    session, scene, packed = ready
    add(session, ident="door", label="wooden door", aliases=["door"], **door())
    act("I open the door and look inside.", session, scene, packed)
    act("I open the door and look inside.", session, scene, packed)
    assert len(session[LEDGER_KEY]["physical_consequences"]) == 1
    assert session[LEDGER_KEY]["entries"][0]["properties"]["open"] is True


def test_cross_scene_object_is_invisible(ready):
    session, scene, packed = ready
    add(session, ident="door", label="wooden door", aliases=["door"], scene_id="other", **door())
    plan, result, _ = act("I open the door.", session, scene, packed)
    assert plan["category"] == "E" and result is None


def test_branch_flags_do_not_change(ready):
    session, scene, packed = ready
    add(session, ident="crate", label="oak crate", aliases=["crate"], mobility="movable", weight="light")
    before = copy.deepcopy(packed)
    act("I push the crate aside and look where it was.", session, scene, packed)
    assert packed == before


def test_provider_plan_validation(ready):
    session, scene, packed = ready
    add(session, ident="door", label="wooden door", aliases=["door"], **door())
    before = copy.deepcopy(session)
    assert validate_provider_plan({"steps": [{"operation": "open", "target_ref": "door", "depends_on": [], "condition": ""}]},
                                  session=session, scene=scene, world=packed)["accepted"]
    assert validate_provider_plan({"steps": [{"operation": "open", "success": True}] },
                                  session=session, scene=scene, world=packed)["reason"] == "unauthorized_field"
    assert validate_provider_plan({"steps": [{"operation": "open", "target_ref": "missing", "depends_on": [], "condition": ""}]},
                                  session=session, scene=scene, world=packed)["reason"] == "invented_target"
    assert validate_provider_plan({"steps": [{"operation": "open", "target_ref": "door", "depends_on": [0], "condition": ""}]},
                                  session=session, scene=scene, world=packed)["reason"] == "invalid_dependency"
    cyclic = {"steps": [
        {"operation": "open", "target_ref": "door", "depends_on": [1], "condition": ""},
        {"operation": "inspect_result", "target_ref": "inspection", "depends_on": [0], "condition": ""},
    ]}
    assert validate_provider_plan(cyclic, session=session, scene=scene, world=packed)["reason"] == "invalid_dependency"
    hidden = {"steps": [{"operation": "open", "target_ref": "SENTINEL_HIDDEN", "depends_on": [], "condition": ""}]}
    assert validate_provider_plan(hidden, session=session, scene=scene, world=packed)["accepted"] is False
    assert validate_provider_plan({"steps": []}, session=session, scene=scene, world=packed)["reason"] == "bound"
    assert session == before


def test_provider_agreement_is_used_only_as_a_stamp(ready):
    session, scene, packed = ready
    add(session, ident="door", label="wooden door", aliases=["door"], **door())
    text = "I open the door and look inside."
    proposal = {"steps": [
        {"operation": "open", "target_ref": "door", "depends_on": [], "condition": ""},
        {"operation": "inspect_result", "target_ref": "inspection", "depends_on": [0], "condition": ""},
    ]}
    verdict = interpret_plan_with_provider(text, session=session, scene=scene, world=packed, invoke=lambda _text: proposal)
    assert verdict["accepted"] and verdict["committed"] is False
    plan, result, _ = act(text, session, scene, packed)
    assert result["metadata"]["physical_adjudication"]["provider_plan"] == "accepted"
    assert session[LEDGER_KEY]["entries"][0]["properties"]["open"] is True
    rejected = interpret_plan_with_provider(text, session=session, scene=scene, world=packed,
                                           invoke=lambda _text: {"steps": [{"operation": "climb", "target_ref": "door", "depends_on": [], "condition": ""}]})
    assert rejected["accepted"] is False and rejected["reason"] == "deterministic_disagreement"


def test_provider_timeout_does_not_mutate(ready):
    session, scene, packed = ready
    add(session, ident="door", label="wooden door", aliases=["door"], **door())
    before = copy.deepcopy(session)
    outcome = interpret_plan_with_provider("I open the door and look inside.", session=session, scene=scene, world=packed,
                                          invoke=lambda _text: (_ for _ in ()).throw(TimeoutError()))
    assert outcome["accepted"] is False and outcome["retries"] == 0 and session == before


def test_proposed_plan_is_not_a_completed_fact(ready):
    session, scene, packed = ready
    add(session, ident="door", label="wooden door", aliases=["door"], **door())
    plan = plan_physical("I open the door and look inside.", session=session, scene=scene, world=packed)
    assert plan["mode"] == "interact"
    assert all(step.get("status") == "PROPOSED" for step in plan["steps"])
    assert "physical_consequences" in session[LEDGER_KEY]
    assert session[LEDGER_KEY]["physical_consequences"] == []


def test_latency_is_recorded_for_a_three_step_plan(ready):
    session, scene, packed = ready
    add(session, ident="door", label="wooden door", aliases=["door"], **door())
    _plan, result, _ = act("Open the door, step through, and look around.", session, scene, packed)
    latency = result["metadata"]["physical_adjudication"]["latency_ms"]
    assert 0 <= latency < 2000


def test_no_dc_is_invented_for_the_blocked_climb(ready):
    session, scene, packed = ready
    add(session, ident="crate", label="oak crate", aliases=["crate"], mobility="movable", weight="light")
    scene["scene"]["interactables"].append({"id": "milestone", "label": "Weathered milestone", "aliases": ["milestone"]})
    plan, result, _ = act("Push the crate aside, climb the milestone, and survey the road.", session, scene, packed)
    text = said(plan, result).casefold()
    assert "dc " not in text and "d20" not in text
    assert result["metadata"]["physical_adjudication"]["invented_dc"] is False
    assert result.get("skill_check") is None


OPEN_LOOK = [
    "I open the door and look inside.",
    "Open the door, then look inside.",
    "I open the door and then look inside.",
    "Let me open the door and look inside.",
    "Please open the door and look inside.",
    "I will open the door and look inside.",
    "First open the door, then look inside.",
    "Open the door; look inside.",
    "I open the door, and look inside.",
    "Kindly open the door and look inside.",
    "I open the door and check inside.",
    "Open the door and inspect inside.",
    "I unlatch the door and look inside.",
    "I open the door, then check inside.",
    "Let me unlatch the door and look inside.",
]
PUSH_LOOK = [
    "I push the crate aside and look where it was.",
    "Push the crate aside, then look where it was.",
    "Move the crate aside and inspect it.",
    "I shift the crate aside and look where it was.",
    "Slide the crate aside and inspect it.",
    "I shove the crate aside and look where it was.",
    "Nudge the crate aside, then inspect it.",
    "I pull the crate aside and look where it was.",
    "Push the crate away and inspect it.",
    "I move the crate aside and then inspect it.",
]
CLOSED_IF = [
    "If the door opens, look inside.",
    "If the door is open, look inside.",
    "If it opens, look inside.",
    "If the door opens, then look inside.",
    "If the wooden door opens, check inside.",
    "If the door opens, inspect inside.",
    "If the door is opened, look inside.",
    "If the door opens, peer inside.",
]
MISSING_BENCH = [
    "I sit on the bench.",
    "Let me sit on the bench.",
    "Please sit on the bench.",
    "I will sit on the bench.",
    "I rest on the bench.",
    "Have a seat on the bench.",
    "I take a seat on the bench.",
    "I'd like to sit on the bench.",
]
READONLY = [
    "Is the door open, and what is on the other side?",
    "Is the door closed, and what lies beyond?",
    "Is the door open and what is on the hidden side?",
    "Are we sure the door is open, and what is on the other side?",
    "Is the door open? What is on the other side?",
    "Was the door opened, and what lies beyond?",
    "Is the door open, and what lies beyond it?",
    "Does the door look open, and what is on the other side?",
]
TOO_MANY = [
    "I stand up, approach the bench, sit on the bench, and step back.",
    "Stand up, approach the bench, sit down, and step back.",
    "Open the door, step through, look around, and sit down.",
    "Push the crate, open the door, look inside, and step back.",
    "Approach the bench, sit on it, stand up, and step back.",
    "I open the door, close the door, open the door, and look inside.",
    "Sit on the bench, stand up, approach it, and step back.",
    "Open the door, wave, climb the milestone, and look around.",
]


@pytest.mark.parametrize("text", OPEN_LOOK, ids=[f"W{i:02d}" for i in range(len(OPEN_LOOK))])
def test_open_and_look_wording(ready, text):
    session, scene, packed = ready
    add(session, ident="door", label="wooden door", aliases=["door"], **door())
    plan, result, _ = act(text, session, scene, packed)
    assert "nothing concealed" in said(plan, result).casefold()
    assert session[LEDGER_KEY]["entries"][0]["properties"]["open"] is True


@pytest.mark.parametrize("text", PUSH_LOOK, ids=[f"P{i:02d}" for i in range(len(PUSH_LOOK))])
def test_push_and_inspect_wording(ready, text):
    session, scene, packed = ready
    add(session, ident="crate", label="oak crate", aliases=["crate"], mobility="movable", weight="light", position="by the wall")
    plan, result, _ = act(text, session, scene, packed)
    assert result and session[LEDGER_KEY]["entries"][0]["properties"]["position"].startswith("aside")
    assert len(session[LEDGER_KEY]["entries"]) == 1


@pytest.mark.parametrize("text", CLOSED_IF, ids=[f"C{i:02d}" for i in range(len(CLOSED_IF))])
def test_closed_condition_skips(ready, text):
    session, scene, packed = ready
    add(session, ident="door", label="wooden door", aliases=["door"], **door())
    before = copy.deepcopy(session[LEDGER_KEY]["entries"])
    plan, result, _ = act(text, session, scene, packed)
    assert result is None and session[LEDGER_KEY]["entries"] == before
    assert "skipped" in said(plan, None).casefold() or "not met" in said(plan, None).casefold() or "not established" in said(plan, None).casefold()


@pytest.mark.parametrize("text", MISSING_BENCH, ids=[f"B{i:02d}" for i in range(len(MISSING_BENCH))])
def test_missing_bench_is_not_ambiguous(ready, text):
    session, scene, packed = ready
    plan, result, _ = act(text, session, scene, packed)
    assert result is None and plan["category"] == "E"
    assert "which" not in said(plan, None).casefold()
    assert "not established" in said(plan, None).casefold()


@pytest.mark.parametrize("text", READONLY, ids=[f"R{i:02d}" for i in range(len(READONLY))])
def test_readonly_wording_does_not_open(ready, text):
    session, scene, packed = ready
    add(session, ident="door", label="wooden door", aliases=["door"], **door())
    plan, result, _ = act(text, session, scene, packed)
    assert result is None
    assert session[LEDGER_KEY]["entries"][0]["properties"]["open"] is False
    assert "nothing was opened" in said(plan, None).casefold() or "not established" in said(plan, None).casefold()


@pytest.mark.parametrize("text", TOO_MANY, ids=[f"T{i:02d}" for i in range(len(TOO_MANY))])
def test_more_than_three_attempts_nothing(ready, text):
    session, scene, packed = ready
    add(session, ident="door", label="wooden door", aliases=["door"], **door())
    add(session, ident="bench", label="wooden bench", aliases=["bench"], use="seat")
    add(session, ident="crate", label="oak crate", aliases=["crate"], mobility="movable", weight="light")
    before = copy.deepcopy(session[LEDGER_KEY])
    plan, result, _ = act(text, session, scene, packed)
    assert result is None and "nothing has been attempted" in said(plan, None).casefold()
    assert session[LEDGER_KEY]["entries"] == before["entries"]
    assert "posture" not in session[LEDGER_KEY]


def test_successful_step_records_a_consequence_id(ready):
    session, scene, packed = ready
    add(session, ident="door", label="wooden door", aliases=["door"], **door())
    _plan, result, _ = act("I open the door and look inside.", session, scene, packed)
    receipt = session[LEDGER_KEY]["physical_consequences"][0]
    assert receipt["action"] == "open" and receipt["result"]["open"] is True
    assert session[LEDGER_KEY]["physical_plans"][-1]["consequences"] == [receipt["id"]]
    assert session[LEDGER_KEY]["physical_plans"][-1]["automatic_resume"] is False


def test_flag_off_leaves_a_sequence_untouched(monkeypatch):
    session, scene, packed = stage()
    add(session, ident="door", label="wooden door", aliases=["door"], **door())
    before = copy.deepcopy(session)
    assert plan_physical("Open the door and look inside.", session=session, scene=scene, world=packed) is None
    assert session == before
