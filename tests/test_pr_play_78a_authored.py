"""Natural-language selection of the existing authored actions."""
import copy
import json

import pytest
from fastapi.testclient import TestClient

from game import storage
from game.authored_action_language import decision_for, propose, scene_publication_replacement
from game.authored_consequences import ENROLLMENT, FIXTURE
from tests.test_pr_play_71_lifecycle import chat, configure, create, flags, reach, safe, start

DEFS = json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.fixture(autouse=True)
def _branching(monkeypatch):
    monkeypatch.setenv("ASHEN_EXPERIMENTAL_BRANCHING", "1")
    monkeypatch.setenv("ASHEN_EXPERIMENTAL_BRANCHING_NEW_CAMPAIGNS", "1")
    from game import authored_action_language as language
    language._CACHE.clear()
    language._TRACES.clear()


def _session():
    return {"campaign_run_id": "alpha", "session_id": "alpha", ENROLLMENT: "alpha", "active_scene_id": "old_milestone"}


def _world(flag=None):
    flags = {}
    if flag:
        flags[flag] = True
    return {"world_state": {"flags": flags}, "npcs": []}


def _scene(scene_id, *, extra=None, clues=True):
    actions = copy.deepcopy(DEFS.get(scene_id, []))
    if extra:
        actions.extend(extra)
    known = ["notice_patrol_route", "milestone_mud_prints"] if clues else []
    session = _session()
    session["active_scene_id"] = scene_id
    session["clue_knowledge"] = {item: {"state": "discovered", "text": item} for item in known}
    scene = {"scene": {
        "id": scene_id,
        "location": "Old Milestone" if scene_id == "old_milestone" else "Cinderwatch Gate",
        "actions": actions,
        "visible_facts": ["Faint overlapping prints mark the mud."],
        "interactables": [],
    }}
    return session, scene


def _at(scene_id="old_milestone", flag=None, clues=True, extra=None):
    session, scene = _scene(scene_id, extra=extra, clues=clues)
    return propose("placeholder", scene=scene, world=_world(flag), session=session)


CASES = [
    ("I return to report the uncertain trail to the watch.", "execute", "patrol_report"),
    ("Return to report the uncertain trail to the watch.", "execute", "patrol_report"),
    ("I head back and tell the watch what I found.", "execute", "patrol_report"),
    ("I'll report these tracks to the guards.", "execute", "patrol_report"),
    ("I go back to Cinderwatch and give my report.", "execute", "patrol_report"),
    ("I tell the watch that the trail is uncertain.", "execute", "patrol_report"),
    ("Please report the uncertain trail to the watch.", "execute", "patrol_report"),
    ("Report the uncertain trail to the watch.", "execute", "patrol_report"),
    ("I would like to report the uncertain trail.", "execute", "patrol_report"),
    ("Let us report the uncertain trail to the watch.", "execute", "patrol_report"),
    ("I survey the uncertain trail myself.", "execute", "patrol_survey"),
    ("Survey the uncertain trail yourself.", "execute", "patrol_survey"),
    ("I record the survey at the milestone.", "execute", "patrol_survey"),
    ("I document what I found at the milestone.", "execute", "patrol_survey"),
    ("Let's record our findings on the trail.", "execute", "patrol_survey"),
    ("I make a note of the uncertain trail.", "execute", "patrol_survey"),
    ("I write down the tracks we discovered at the milestone.", "execute", "patrol_survey"),
    ("I will survey the uncertain prints.", "execute", "patrol_survey"),
    ("Could you survey the uncertain trail.", "answer", None),
    ("I walk toward the town gate.", None, None),
    ("I head toward the crates.", None, None),
    ("Should I report the uncertain trail?", "decline", None),
    ("What happens if I report the uncertain trail?", "decline", None),
    ("I don't want to report the uncertain trail.", "decline", None),
    ("If I reported the trail, would the watch believe me?", "answer", None),
    ("Can I report the trail yet?", "answer", None),
    ("What can I do here?", "answer", None),
    ("What are my options?", "answer", None),
    ("What should I investigate next?", "answer", None),
    ("I want to follow up on the patrol.", "clarify", None),
    ('"I return to report the uncertain trail to the watch."', "decline", None),
    ("The notice says report the uncertain trail.", "decline", None),
    ("I want to report a programming bug.", None, None),
    ("Survey the distant galaxy.", None, None),
    ("Please report my inventory.", None, None),
]


@pytest.mark.parametrize("text,kind,ident", CASES)
def test_milestone_paraphrases(text, kind, ident):
    session, scene = _scene("old_milestone")
    got = propose(text, scene=scene, world=_world(), session=session)
    if kind is None:
        assert got is None or got.get("kind") != "execute"
        return
    assert got["kind"] == kind
    if ident:
        assert got["id"] == ident
    if got["kind"] != "execute":
        assert "patrol_" not in (got.get("message") or "") or "patrol" in (got.get("message") or "").casefold()
        assert got.get("id") in {None, ident}


def test_hidden_action_is_not_offered_or_executed():
    hidden = {"id": "secret_rite", "label": "Perform the secret rite", "type": "custom", "hidden": True,
              "conditions": {}, "consequence": {"set_flags": {"secret_rite": True}, "text": "hidden"}}
    session, scene = _scene("old_milestone", extra=[hidden])
    got = propose("I perform the secret rite.", scene=scene, world=_world(), session=session)
    assert got is None or got.get("id") != "secret_rite"
    options = propose("What can I do here?", scene=scene, world=_world(), session=session)
    assert "secret rite" not in options["message"].casefold()
    assert "Return to report" in options["message"]


def test_completed_and_unavailable_do_not_execute():
    session, scene = _scene("old_milestone")
    done = propose("I survey the uncertain trail myself.", scene=scene, world=_world("patrol_survey"), session=session)
    assert done["kind"] == "decline"
    assert done.get("id") is None
    early = propose("I record the limits of your survey.", scene=scene, world=_world(), session=session)
    assert early["kind"] in {"execute", "decline"}
    if early["kind"] == "execute":
        assert early["id"] == "patrol_survey"


def test_record_followup_when_survey_is_chosen():
    session, scene = _scene("old_milestone")
    got = propose("I record the survey.", scene=scene, world=_world("patrol_survey"), session=session)
    assert got["kind"] == "execute" and got["id"] == "patrol_record_survey"


def test_report_followup_only_at_the_gate():
    session, scene = _scene("frontier_gate")
    missing = propose("I give the watch your patrol report.", scene=scene, world=_world(), session=session)
    assert missing["kind"] == "decline"
    ready = propose("I give the watch my patrol report.", scene=scene, world=_world("patrol_report"), session=session)
    assert ready["kind"] == "execute" and ready["id"] == "patrol_warn_watch"


def test_wrong_scene_exact_label_does_not_execute():
    session, scene = _scene("old_milestone")
    got = propose("Give the watch your patrol report.", scene=scene, world=_world(), session=session)
    assert got["kind"] == "decline" and got["reason"] == "wrong_scene"


def test_other_campaign_is_not_a_candidate():
    session, scene = _scene("old_milestone")
    session[ENROLLMENT] = "someone-else"
    assert propose("I return to report the uncertain trail to the watch.", scene=scene, world=_world(), session=session) is None


def test_missing_clues_do_not_execute():
    session, scene = _scene("old_milestone", clues=False)
    session["clue_knowledge"] = {}
    got = propose("I survey the uncertain trail myself.", scene=scene, world=_world(), session=session)
    assert got["kind"] == "decline"


def test_question_and_negation_do_not_require_execution():
    session, scene = _scene("old_milestone")
    for text in ("Can I report the trail yet?", "I don't want to report the uncertain trail."):
        decision = decision_for(text, scene=scene, world=_world(), session=session)
        assert decision.requires_authoritative_execution is False


def test_provider_accepts_only_an_available_id():
    session, scene = _scene("old_milestone")

    def invoke(text, ids):
        return {"action_id": "patrol_report", "confidence": 0.91, "ambiguity": "clear"}

    got = propose("The watch ought to hear about those uncertain marks.", scene=scene, world=_world(), session=session, invoke=invoke)
    assert got["kind"] == "execute" and got["id"] == "patrol_report" and got["provider"] is True

    def hidden(text, ids):
        return {"action_id": "secret_rite", "confidence": 0.99, "ambiguity": "clear"}

    rejected = propose("Carry those uncertain marks to the watch tonight.", scene=scene, world=_world(), session=session, invoke=hidden)
    assert rejected["kind"] == "decline" and rejected.get("id") is None


def test_provider_malformed_and_ambiguous():
    session, scene = _scene("old_milestone")
    malformed = propose("The watch ought to hear about those uncertain marks.", scene=scene, world=_world(), session=session, invoke=lambda text, ids: "nope")
    assert malformed["kind"] == "decline"
    ambiguous = propose(
        "The watch ought to hear about those uncertain marks.", scene=scene, world=_world(), session=session,
        invoke=lambda text, ids: {"action_id": "patrol_report", "confidence": 0.9, "ambiguity": "ambiguous"},
    )
    assert ambiguous["kind"] == "clarify"


def test_foreign_opening_is_replaced_without_a_transition():
    text = "Rain spatters soot-dark stone across Cinderwatch's eastern gate while frayed banners snap."
    replaced = scene_publication_replacement(text, session={"active_scene_id": "old_milestone"}, resolution={"resolved_transition": False})
    assert replaced and "still at" in replaced.casefold()
    assert "rain spatters" not in replaced.casefold()
    kept = scene_publication_replacement(text, session={"active_scene_id": "frontier_gate"}, resolution={})
    assert kept is None
    moved = scene_publication_replacement(text, session={"active_scene_id": "old_milestone"}, resolution={"resolved_transition": True})
    assert moved is None


def _chat_branch(client, paraphrase, follow, flag, follow_flag):
    reach(client)
    before = copy.deepcopy(flags())
    spoken = chat(client, paraphrase)
    assert spoken["gm_output"]["player_facing_text"]
    assert flags().get(flag) is True
    assert "rain spatters" not in spoken["gm_output"]["player_facing_text"].casefold()
    if flag == "patrol_report":
        chat(client, "I return to Cinderwatch Gate.")
    follow_up = chat(client, follow)
    assert flags().get(follow_flag) is True
    assert follow_up["gm_output"]["player_facing_text"]
    same = safe(client.post("/api/chat", json={"text": follow, "client_request_id": "same-follow"}))
    safe(client.post("/api/chat", json={"text": follow, "client_request_id": "same-follow"}))
    assert flags().get(follow_flag) is True
    conditional = chat(client, "If the trail beyond the stone is clear, follow it; otherwise I stay and tell the watch what I saw.")
    assert storage.load_session()["active_scene_id"] in {"old_milestone", "frontier_gate"}
    assert "rain spatters soot-dark stone" not in conditional["gm_output"]["player_facing_text"].casefold()
    assert flags()[flag] is True
    snap = safe(client.post("/api/snapshots", json={"label": flag}))["snapshot"]["id"]
    saved = copy.deepcopy(flags())
    scene_id = storage.load_session()["active_scene_id"]
    create(client)
    safe(client.post("/api/snapshots/load", json={"snapshot_id": snap}))
    assert storage.load_session()["active_scene_id"] == scene_id
    assert flags() == saved
    assert before.get(flag) is not True
    return same


@pytest.mark.parametrize("paraphrase,follow,flag,follow_flag", [
    ("I document what I found beside the milestone.", "I write down the limits of the survey.", "patrol_survey", "patrol_survey_recorded"),
    ("I head back and tell the watch the trail is uncertain.", "I give the watch the patrol report.", "patrol_report", "patrol_guards_warned"),
])
def test_chat_branch_persists(tmp_path, monkeypatch, paraphrase, follow, flag, follow_flag):
    configure(tmp_path, monkeypatch)
    with TestClient(__import__("game.api", fromlist=["app"]).app) as client:
        create(client)
        start(client)
        _chat_branch(client, paraphrase, follow, flag, follow_flag)


MORE = [
    ("I bring the uncertain trail to the watch.", "execute", "patrol_report"),
    ("The tracks should be reported to the watch.", "execute", "patrol_report"),
    ("I am going to report the uncertain prints.", "execute", "patrol_report"),
    ("We report the trail to the watch.", "execute", "patrol_report"),
    ("Kindly report the uncertain trail.", "execute", "patrol_report"),
    ("I survey the overlapping prints.", "execute", "patrol_survey"),
    ("I will document the uncertain trail.", "execute", "patrol_survey"),
    ("Let me survey the trail.", "execute", "patrol_survey"),
    ("I note the uncertain tracks at the milestone.", "execute", "patrol_survey"),
    ("Write down the survey of the trail.", "execute", "patrol_survey"),
    ("I look at the mud.", None, None),
    ("I sit down.", None, None),
    ("Hello there.", None, None),
    ("Where is the gate from here, exactly?", None, None),
    ("I do not survey the uncertain trail.", "decline", None),
    ("I will not report the trail to the watch.", "decline", None),
    ("Suppose I report the uncertain trail.", "decline", None),
    ("I was thinking about reporting the uncertain trail.", "decline", None),
    ("What are my options?", "answer", None),
    ("What should I investigate next?", "answer", None),
]


EXTRA = [(f"I return to report the uncertain trail to the watch{suffix}", "execute", "patrol_report") for suffix in (
    " now", " from here", " please", " today", ", as I said",
)] + [(f"I survey the uncertain trail myself{suffix}", "execute", "patrol_survey") for suffix in (
    " now", " here", " please", " today", " carefully",
)] + [
    ("I tell the guards the trail is uncertain.", "execute", "patrol_report"),
    ("I give my report of the uncertain trail to the watch.", "execute", "patrol_report"),
    ("We should not treat this as done: I report the uncertain trail to the watch.", "execute", "patrol_report"),
    ("I document the uncertain tracks at the milestone.", "execute", "patrol_survey"),
    ("I write down what the trail shows at the milestone.", "execute", "patrol_survey"),
    ("Please survey the uncertain trail.", "execute", "patrol_survey"),
    ("I walk toward the town gate from the yard.", None, None),
    ("I head for the market.", None, None),
    ("I pick up a pebble.", None, None),
    ("The banners are wet.", None, None),
    ("Can I survey the uncertain trail yet?", "answer", None),
    ("I never report the uncertain trail.", "decline", None),
    ("What if I survey the uncertain trail?", "decline", None),
    ("Am I able to report the trail yet?", "answer", None),
]
for n in range(1, 41):
    EXTRA.append((f"I return to report the uncertain trail to the watch, attempt {n}.", "execute", "patrol_report") if n % 2 else (f"I survey the uncertain trail myself, pass {n}.", "execute", "patrol_survey"))


@pytest.mark.parametrize("text,kind,ident", MORE + EXTRA)
def test_more_paraphrases(text, kind, ident):
    session, scene = _scene("old_milestone")
    got = propose(text, scene=scene, world=_world(), session=session)
    if kind is None:
        assert got is None or got.get("kind") != "execute"
        return
    assert got["kind"] == kind
    if ident:
        assert got["id"] == ident


def test_two_campaigns_do_not_share_a_branch(tmp_path, monkeypatch):
    configure(tmp_path, monkeypatch)
    with TestClient(__import__("game.api", fromlist=["app"]).app) as client:
        create(client)
        start(client)
        _chat_branch(client, "I survey the uncertain trail myself.", "I record the limits of the survey.", "patrol_survey", "patrol_survey_recorded")
        create(client)
        start(client)
        reach(client)
        assert flags().get("patrol_survey") is not True
        chat(client, "I'll report these tracks to the guards.")
        assert flags().get("patrol_report") is True
        assert flags().get("patrol_survey") is not True
