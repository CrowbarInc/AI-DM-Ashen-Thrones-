"""Player-directed actions that are not authored campaign choices."""
import copy

import pytest
from fastapi.testclient import TestClient

from game.authored_action_language import scene_publication_replacement
from game.authored_consequences import ENROLLMENT
from game.bounded_improvisation import LEDGER_KEY
from game.expressive_dialogue import background_conversation
from game.general_purpose_actions import classify, exploration_outcome, remember_general_resolution
from game.narrative_consistency import publication_conflict
from game.player_initiative import decide
from tests.test_pr_play_76_physical import add, enable
from tests.test_pr_play_78_integrated import play, prepare, stage

OPEN = [
    ("I want to follow the tracks farther.", "environmental_observation", "success_without_discovery", True),
    ("I try to determine which direction the patrol went.", "environmental_observation", "success_without_discovery", True),
    ("I look for somewhere to watch the road unnoticed.", "environmental_observation", "success_without_discovery", False),
    ("I search the roadside for another route.", "environmental_observation", "success_without_discovery", True),
    ("I want to investigate before deciding what to report.", "information", "read_only", False),
    ("I wait to see whether anyone comes along.", "environmental_observation", "read_only", False),
    ("I leave a marker so I can find this place again.", "physical_positioning", "missing_mechanic", False),
    ("I place a cairn beside the road.", "physical_positioning", "missing_mechanic", False),
    ("I look for a secret passage under the stone.", "world_expansion", "needs_authority", None),
]

SOCIAL = [
    ("I ask the guard to send someone with me.", False, "deployment"),
    ("Send a search party down the road.", False, "deployment"),
    ("Come with me and search the scrub.", False, "deployment"),
    ("What do we know about the prints?", True, "prints"),
]

NARRATION = [
    ("You arrive at the Rain Barrel Tavern and the room is warm.", "old_milestone", False, "other_location"),
    ("Rain spatters soot-dark stone across Cinderwatch's eastern gate while banners snap.", "old_milestone", False, "other_location"),
    ("You are still at Old Milestone. The prints fade into the scrub ahead of you.", "old_milestone", False, None),
    ("You arrive at the Rain Barrel Tavern and the room is warm.", "frontier_gate", True, None),
    ("The mud around the marker is churned with faint overlapping prints that fade.", "old_milestone", False, None),
]


def milestone():
    session = {
        "campaign_run_id": "alpha", "session_id": "alpha", ENROLLMENT: "alpha",
        "active_scene_id": "old_milestone",
        "clue_knowledge": {
            "notice_patrol_route": {"state": "discovered", "text": "notice"},
            "milestone_mud_prints": {"state": "discovered", "text": "prints"},
        },
        LEDGER_KEY: {"entries": [], "investigation_notes": [], "physical_state": {}},
    }
    scene = {"scene": {
        "id": "old_milestone",
        "location": "Old Milestone",
        "visible_facts": [
            "The mud around the marker is churned with faint overlapping prints that fade into the scrub.",
            "The track continues a short way past the stone before the next step is unclear.",
        ],
        "interactables": [],
        "hidden_facts": ["The hidden patrol captain waits behind the ridge with the payroll."],
        "discoverable_clues": [{"id": "secret", "text": "The hidden patrol captain waits behind the ridge with the payroll."}],
    }}
    world = {"npcs": [], "world_state": {"flags": {}}}
    return session, scene, world


@pytest.fixture
def ready(monkeypatch):
    enable(monkeypatch)
    return milestone()


@pytest.mark.parametrize("text,family,outcome,executes", OPEN, ids=[f"open-{i}" for i in range(len(OPEN))])
def test_open_ended_classification(ready, text, family, outcome, executes):
    session, scene, world = ready
    proposal = classify(text, scene=scene, world=world, session=session)
    assert proposal is not None
    assert proposal["family"] == family
    assert proposal["outcome"] == outcome
    decision = decide(text, scene=scene, world=world, session=session)
    if executes is not None:
        assert decision.requires_authoritative_execution is executes
    assert "patrol_survey" not in (decision.player_facing_text or "")
    assert "secret passage" not in (decision.player_facing_text or "").casefold() or "has not been" in (decision.player_facing_text or "").casefold()
    assert world["world_state"]["flags"] == {}


def test_follow_tracks_publishes_the_visible_trace_without_a_branch(ready):
    session, scene, world = ready
    proposal = classify("I want to follow the tracks farther.", scene=scene, world=world, session=session)
    assert proposal["operation"] == "OBSERVE_FACT"
    action = {
        "id": proposal["target"], "target_id": proposal["target"], "type": "observe",
        "label": "tracks", "prompt": "I want to follow the tracks farther.",
        "metadata": {"general_purpose_family": "environmental_observation"},
    }
    result = exploration_outcome(scene, action, prompt=action["prompt"], action_id=action["id"], label="tracks")
    said = result["metadata"]["engine_publication"].casefold()
    assert "prints" in said
    assert "no new route" in said
    assert "captain" not in said
    remember_general_resolution(session, scene, action["prompt"], result)
    assert session[LEDGER_KEY]["investigation_notes"]
    assert world["world_state"]["flags"] == {}


def test_marker_and_wait_do_not_mutate(ready):
    session, scene, world = ready
    before = copy.deepcopy(session)
    for text in ("I leave a marker so I can find this place again.", "I wait to see whether anyone comes along."):
        decision = decide(text, scene=scene, world=world, session=session)
        assert decision.requires_authoritative_execution is False
        assert decision.player_facing_text
    assert session[LEDGER_KEY]["entries"] == before[LEDGER_KEY]["entries"]
    assert world["world_state"]["flags"] == {}


@pytest.mark.parametrize("text,answers,fragment", SOCIAL)
def test_social_limits(ready, text, answers, fragment):
    session, scene, world = ready
    decision = decide(text, scene=scene, world=world, session=session)
    blob = (decision.player_facing_text or decision.primary_intention or "").casefold()
    if answers:
        assert decision.requires_authoritative_execution is False
    assert fragment in blob or fragment in (decision.reason or "")
    assert "payroll" not in blob


def test_negative_finding_is_recalled(ready):
    session, scene, world = ready
    session[LEDGER_KEY]["investigation_notes"].append({
        "scene_id": "old_milestone", "prompt": "struggle", "result": "No signs of a struggle are established here.",
    })
    decision = decide("What do we know about the prints?", scene=scene, world=world, session=session)
    assert "no signs of a struggle" in decision.player_facing_text.casefold()


@pytest.mark.parametrize("text,scene_id,transition,reason", NARRATION)
def test_location_consistency(text, scene_id, transition, reason):
    session = {"active_scene_id": scene_id, "campaign_run_id": "alpha"}
    resolution = {"resolved_transition": transition}
    conflict = publication_conflict(text, session=session, resolution=resolution)
    if reason:
        assert conflict and reason in conflict
        replaced = scene_publication_replacement(text, session=session, resolution=resolution)
        assert replaced and "still at" in replaced.casefold()
        assert "rain spatters" not in replaced.casefold()
    else:
        assert conflict is None


def test_object_state_and_hidden_fact(ready):
    session, scene, world = ready
    add(session, ident="stone", label="loose stone", aliases=["stone"], scene_id="old_milestone", position="beside the stonework")
    moved = "You shove the loose stone aside and leave the ground bare where it had been sitting."
    assert publication_conflict(moved, session=session, resolution={}, scene=scene)
    allowed = "The loose stone is beside the stonework, and it has not been moved from that place."
    assert publication_conflict(allowed, session=session, resolution={}, scene=scene) is None
    leaked = "The hidden patrol captain waits behind the ridge with the payroll, and he waves you over now."
    assert publication_conflict(leaked, session=session, resolution={}, scene=scene) == "hidden_fact"
    discovered = dict(session)
    discovered["clue_knowledge"] = {"secret": {"state": "discovered", "text": scene["scene"]["discoverable_clues"][0]["text"]}}
    assert publication_conflict(leaked, session=discovered, resolution={}, scene=scene) is None


def test_transition_allows_the_other_place(ready):
    session, _scene, _world = ready
    text = "You arrive at the Rain Barrel Tavern and the room is warm from the fire."
    assert publication_conflict(text, session=session, resolution={"resolved_transition": True}) is None


def test_short_text_is_not_a_setting_conflict(ready):
    session, _scene, _world = ready
    assert publication_conflict("You arrive at the tavern.", session=session, resolution={}) is None


def test_aside_matches_a_moved_stone(ready):
    session, scene, _world = ready
    add(session, ident="stone", label="loose stone", aliases=["stone"], scene_id="old_milestone", position="aside from the stonework")
    text = "You shove the loose stone aside and leave the ground bare where it had been sitting."
    assert publication_conflict(text, session=session, resolution={}, scene=scene) is None


def test_ordered_turns_do_not_overlap(ready):
    from game.integrated_play import ordered_turn
    session, _scene, _world = ready
    with ordered_turn(session["campaign_run_id"], mutating=True, request_key="one", text="look") as turn:
        turn.result = {"ok": True}
    with ordered_turn(session["campaign_run_id"], mutating=True, request_key="one", text="look") as again:
        assert again.duplicate is True
        assert again.result == {"ok": True}


def test_other_campaign_cannot_take_the_branch(ready):
    from game.authored_action_language import propose
    session, scene, world = ready
    session[ENROLLMENT] = "beta"
    assert propose("I survey the uncertain trail myself.", scene=scene, world=world, session=session) is None


def test_provider_cannot_invent_an_action_id(ready):
    import json
    from game.authored_action_language import propose
    from game.authored_consequences import FIXTURE
    session, scene, world = ready
    scene["scene"]["actions"] = json.loads(FIXTURE.read_text(encoding="utf-8"))["old_milestone"]
    rejected = propose(
        "The watch ought to hear about those uncertain marks.",
        scene=scene, world=world, session=session,
        invoke=lambda text, ids: {"action_id": "secret_rite", "confidence": 0.99, "ambiguity": "clear"},
    )
    assert rejected["kind"] == "decline"
    assert rejected.get("id") is None


def test_read_only_question_does_not_move_state(ready):
    session, scene, world = ready
    before = copy.deepcopy(session[LEDGER_KEY])
    decision = decide("What is visible from here?", scene=scene, world=world, session=session)
    assert decision.requires_authoritative_execution is False
    assert session[LEDGER_KEY] == before


def test_notes_are_scene_scoped(ready):
    session, scene, world = ready
    session[LEDGER_KEY]["investigation_notes"].append({
        "scene_id": "frontier_gate", "prompt": "gate", "result": "GATE_ONLY_NOTE",
    })
    decision = decide("What do we know about the prints?", scene=scene, world=world, session=session)
    assert "gate_only_note" not in decision.player_facing_text.casefold()


def test_committed_move_may_say_aside(ready):
    session, scene, _world = ready
    add(session, ident="stone", label="loose stone", aliases=["stone"], scene_id="old_milestone", position="beside the stonework")
    text = "You shove the loose stone aside and leave the ground bare where it had been sitting."
    assert publication_conflict(text, session=session, resolution={"state_changes": {"mutation": True}}, scene=scene) is None


def test_npc_cites_visible_fact_and_not_the_secret(ready):
    session, scene, _world = ready
    npc = {"id": "npc1", "name": "Mara", "label": "ordinary traveler", "role": "traveler",
           "appearance": "weathered cloak", "demeanor": "reserved", "social_receipts": []}
    said = background_conversation(npc, session=session, scene=scene, player_text="What do you make of the prints?")
    low = said.casefold()
    assert "prints" in low
    assert "captain" not in low
    assert "payroll" not in low
    secret = background_conversation(npc, session=session, scene=scene, player_text="Where is the hidden patrol captain?")
    assert "do not know" in secret.casefold()
    assert "payroll" not in secret.casefold()


def test_npc_remembers_what_the_player_said_without_adopting_it(ready):
    session, scene, _world = ready
    npc = {"id": "npc1", "name": "Mara", "label": "ordinary traveler", "role": "traveler",
           "appearance": "weathered cloak", "demeanor": "reserved", "social_receipts": []}
    first = background_conversation(npc, session=session, scene=scene, player_text="I tell you I found unclear prints.")
    assert "do not know whether" in first.casefold()
    assert "heard" in npc["social_receipts"]
    second = background_conversation(npc, session=session, scene=scene, player_text="What did I tell you?")
    assert "unclear prints" in second.casefold()
    assert "payroll" not in second.casefold()


def test_mixed_action_keeps_the_unsupported_step(monkeypatch):
    enable(monkeypatch)
    monkeypatch.setenv("ASHEN_EXPERIMENTAL_DYNAMIC_NPCS", "1")
    session, scene, world = stage()
    prepare("stone", session, scene)
    _plan, _result, said, changed = play("Move the stone aside and follow the tracks farther.", session, scene, world)
    low = said.casefold()
    assert "aside" in low or "not supported" in low or "not established" in low
    assert changed or "not" in low


def test_partial_sequence_keeps_the_first_result(monkeypatch):
    enable(monkeypatch)
    monkeypatch.setenv("ASHEN_EXPERIMENTAL_DYNAMIC_NPCS", "1")
    session, scene, world = stage()
    prepare("mixed", session, scene)
    _plan, result, said, _changed = play("Move the stone aside, climb the marker, and ask the traveler what they saw.", session, scene, world)
    assert result is not None
    assert "aside" in said.casefold()
    stone = next(entry for entry in session[LEDGER_KEY]["entries"] if entry.get("label") == "loose stone")
    assert str(stone["properties"]["position"]).startswith("aside")


DIALOGUE_TURNS = [
    ("Hello, Mara.", "hello"),
    ("Who are you?", "mara"),
    ("What is this place like?", "traveler is here"),
    ("What do you make of the marker?", "marker"),
    ("Have you seen the patrol?", "do not know"),
    ("I tell you the prints are unclear.", "whether"),
    ("What did I tell you?", "prints"),
    ("Thank you, Mara.", "thank"),
]


def test_eight_turn_dialogue_stays_in_identity(monkeypatch):
    enable(monkeypatch)
    monkeypatch.setenv("ASHEN_EXPERIMENTAL_DYNAMIC_NPCS", "1")
    session, scene, world = stage()
    prepare("traveler", session, scene)
    for text, fragment in DIALOGUE_TURNS:
        _plan, _result, said, _changed = play(text, session, scene, world)
        assert fragment in said.casefold(), text
        assert "northwest" not in said.casefold()
        assert "quest" not in said.casefold()


def test_save_roundtrip_keeps_the_note(tmp_path, monkeypatch):
    from game import api, storage
    from tests.test_pr_play_71_lifecycle import chat, configure, create, flags, reach, safe, start
    configure(tmp_path, monkeypatch)
    monkeypatch.setenv("ASHEN_EXPERIMENTAL_PLAYER_INITIATIVE", "1")
    monkeypatch.setenv("ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION", "1")
    monkeypatch.setenv("ASHEN_EXPERIMENTAL_WORLD_IMPROVISATION", "1")
    with TestClient(api.app) as client:
        identity = create(client)
        start(client)
        reach(client)
        spoken = chat(client, "I want to follow the tracks farther.")
        text = spoken["gm_output"]["player_facing_text"]
        assert storage.load_session()["active_scene_id"] == "old_milestone"
        assert flags().get("patrol_report") is not True
        assert flags().get("patrol_survey") is not True
        assert "captain waits" not in text.casefold()
        snap = safe(client.post("/api/snapshots", json={"label": "initiative"}))["snapshot"]["id"]
        notes = (storage.load_session().get(LEDGER_KEY) or {}).get("investigation_notes") or []
        create(client)
        safe(client.post("/api/snapshots/load", json={"snapshot_id": snap}))
        restored = storage.load_session()
        assert restored["campaign_run_id"] == identity
        assert restored["active_scene_id"] == "old_milestone"
        assert ((restored.get(LEDGER_KEY) or {}).get("investigation_notes") or []) == notes
        again = chat(client, "What do we know about the prints?")
        recalled = again["gm_output"]["player_facing_text"]
        assert "available choices" not in recalled.casefold()
        assert "prints" in recalled.casefold()
        assert flags().get("patrol_survey") is not True


def test_authored_report_still_commits(tmp_path, monkeypatch):
    from game import api, storage
    from tests.test_pr_play_71_lifecycle import chat, configure, create, flags, reach, start
    configure(tmp_path, monkeypatch)
    monkeypatch.setenv("ASHEN_EXPERIMENTAL_PLAYER_INITIATIVE", "1")
    with TestClient(api.app) as client:
        create(client)
        start(client)
        reach(client)
        spoken = chat(client, "I return to report the uncertain trail to the watch.")
        assert flags().get("patrol_report") is True
        assert flags().get("patrol_survey") is not True
        assert "rain spatters" not in spoken["gm_output"]["player_facing_text"].casefold()
        assert storage.load_session()["active_scene_id"] == "old_milestone"


def test_greeting_names_the_person_after_the_comma():
    from game.interaction_completion import addressed_person_nominal
    from game.ordinary_semantic_ownership import assess_addressee_grounding
    assert addressed_person_nominal("Hello, Gate Guard.") == "Gate Guard"
    scene = {"scene": {"id": "frontier_gate"}}
    world = {"npcs": [
        {"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate"},
        {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate"},
        {"id": "tavern_runner", "name": "Tavern Runner", "location": "frontier_gate"},
    ]}
    grounded = assess_addressee_grounding("Hello, Gate Guard.", scene=scene, world=world, session={})
    assert grounded["target_id"] == "gate_guard"
    assert grounded["operation_eligibility"] == "executable"


def test_cross_campaign_note_is_not_recalled(ready):
    session, scene, world = ready
    session[LEDGER_KEY]["investigation_notes"].append({
        "scene_id": "old_milestone", "prompt": "other", "result": "FOREIGN_NOTE",
    })
    other = dict(session)
    other["campaign_run_id"] = "beta"
    other[ENROLLMENT] = "beta"
    other[LEDGER_KEY] = {"entries": [], "investigation_notes": [], "physical_state": {}}
    decision = decide("What do we know about the prints?", scene=scene, world=world, session=other)
    assert "foreign_note" not in decision.player_facing_text.casefold()


ISOLATION = [
    ("read", "What is visible from here?"),
    ("ambiguous", "Look over there."),
    ("climb", "I climb the marker."),
    ("persuade", "I persuade the captain to confess."),
]


MORE = [
    ("I peer down the road.", "success_without_discovery"),
    ("I scan the road ahead.", "success_without_discovery"),
    ("I look farther along the track.", "success_without_discovery"),
    ("I chase the prints.", "success_without_discovery"),
    ("I trace the trail.", "success_without_discovery"),
    ("Which direction did the prints go?", "success_without_discovery"),
    ("I search for a route along the road.", "success_without_discovery"),
    ("What is visible from here?", "read_only"),
    ("What do we know?", "read_only"),
    ("I wait here.", "read_only"),
    ("I watch the road for a while.", "read_only"),
    ("Rather than report, I keep examining.", "read_only"),
    ("Before I report, I look around the stone.", "read_only"),
    ("Look over there.", "clarify"),
    ("Move that.", "clarify"),
    ("Ask them.", "clarify"),
    ("I climb the marker.", "missing_mechanic"),
    ("I jump onto the milestone.", "cannot_attempt"),
    ("I scramble up the stone.", "missing_mechanic"),
    ("I persuade the captain to confess.", "cannot_attempt"),
    ("I search under the loose stone.", "success_without_discovery"),
    ("I look for a handhold.", "cannot_attempt"),
    ("I dig beside the marker.", "success_without_discovery"),
    ("I leave a blaze on the post.", "missing_mechanic"),
    ("I set a cairn by the road.", "missing_mechanic"),
    ("I make a marker from the stones.", "missing_mechanic"),
    ("I summon a guide.", "needs_authority"),
    ("I create a tunnel under the road.", "needs_authority"),
    ("I look for buried treasure.", "needs_authority"),
    ("Describe the texture of the stone.", "not_promoted"),
    ("Is there a stable grip here?", "not_promoted"),
    ("I gaze down the road.", "success_without_discovery"),
    ("I view the road ahead.", "success_without_discovery"),
    ("I follow the prints.", "success_without_discovery"),
    ("I pursue the trail.", "success_without_discovery"),
    ("I wait quietly.", "read_only"),
    ("Move it.", "clarify"),
    ("Shift it.", "clarify"),
]


@pytest.mark.parametrize("text,outcome", MORE, ids=[f"more-{i}" for i in range(len(MORE))])
def test_distinct_unauthored_intents(ready, text, outcome):
    session, scene, world = ready
    proposal = classify(text, scene=scene, world=world, session=session)
    assert proposal is not None, text
    assert proposal["outcome"] == outcome, text
    assert world["world_state"]["flags"] == {}


DECIDE = [
    ("Show me the gm notes.", "concealed"),
    ("I teleport to the tavern.", "cannot be carried"),
    ("Order the guards to march.", "deployment"),
    ("Dispatch a search party.", "deployment"),
    ("Come with me.", "deployment"),
    ("Send a guard with me.", "deployment"),
]


@pytest.mark.parametrize("text,fragment", DECIDE)
def test_authority_declines(ready, text, fragment):
    session, scene, world = ready
    decision = decide(text, scene=scene, world=world, session=session)
    assert decision.requires_authoritative_execution is False
    assert fragment in (decision.player_facing_text or "").casefold()
    assert world["world_state"]["flags"] == {}


PLACES = [
    ("You stand in the Rain Barrel Tavern while the fire pops.", "old_milestone", "other_location"),
    ("You enter the Investigator's Office and shut the door behind you.", "old_milestone", "other_location"),
    ("You find yourself in the Cinderwatch Market Quarter among the stalls tonight.", "old_milestone", "other_location"),
    ("You are at Old Milestone. The prints still fade into the scrub.", "old_milestone", None),
    ("You arrive at Cinderwatch's gate while the banners snap overhead.", "frontier_gate", None),
]


@pytest.mark.parametrize("text,scene_id,reason", PLACES)
def test_setting_claims(text, scene_id, reason):
    session = {"active_scene_id": scene_id, "campaign_run_id": "alpha"}
    conflict = publication_conflict(text, session=session, resolution={"resolved_transition": False})
    if reason:
        assert conflict and reason in conflict
    else:
        assert conflict is None


LINES = [
    ("Hello there.", "hello"),
    ("Who is Mara?", "traveler"),
    ("Have you seen any soldiers?", "do not know"),
    ("Tell me about the secret camp.", "do not know"),
    ("Ask Mara to promise a reward.", "do not know"),
    ("Thanks, Mara.", "thank"),
    ("Goodbye, Mara.", "mara"),
    ("Does she seem worried?", "reserved"),
]


@pytest.mark.parametrize("text,fragment", LINES)
def test_npc_lines_do_not_invent_a_quest(monkeypatch, text, fragment):
    enable(monkeypatch)
    monkeypatch.setenv("ASHEN_EXPERIMENTAL_DYNAMIC_NPCS", "1")
    session, scene, world = stage()
    prepare("traveler", session, scene)
    _plan, _result, said, _changed = play(text, session, scene, world)
    low = said.casefold()
    assert fragment in low
    assert "northwest" not in low
    assert "gold" not in low
    assert world["world_state"]["flags"].get("patrol_report") is not True


@pytest.mark.parametrize("name,text", ISOLATION)
def test_existing_general_purpose_boundaries(ready, name, text):
    session, scene, world = ready
    scene["scene"]["addressables"] = []
    proposal = classify(text, scene=scene, world=world, session=session)
    if name == "read":
        assert proposal["outcome"] == "read_only"
    elif name == "ambiguous":
        assert proposal["outcome"] == "clarify"
    elif name == "climb":
        assert proposal["outcome"] in {"missing_mechanic", "cannot_attempt"}
    else:
        assert proposal["outcome"] in {"cannot_attempt", "clarify"}
    assert world["world_state"]["flags"] == {}
