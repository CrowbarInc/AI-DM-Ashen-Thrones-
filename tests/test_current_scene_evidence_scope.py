"""Offline HTTP replay of the original Frontier Gate evidence leak."""

import json
import os

import pytest

from game import conversational_orchestration as co, live_chat_interpretation as live, storage
from tests.test_inspection_communication_admission import (
    EXTENDED, ROUTE, assert_discovery, assert_quiet, gameplay_session, load, play_capture, reason, replay, trace,
)
from tests.test_incidental_posture_action_decomposition import interpretation
from tests.test_repeat_statement_routing_ownership import CAPTAIN, PRINTS, historical_snapshot


def prefix(replay, monkeypatch, *, discover=False, through=7):
    for index in range(1, through + 1):
        source = EXTENDED / f"T{index:02}.json"
        recorded = load(source)
        with monkeypatch.context() as historical:
            if index == 1:
                reconcile = co._inspection_communication_consistency
                historical.setattr(co, "_inspection_communication_consistency",
                                   lambda record, text, **kw: reconcile(record, text + " now", **kw))
            if index == 4 and not discover:
                historical.setattr(co, "_normalize_inspection_posture", lambda record, *args, **kw: record)
            row = play_capture(replay, source, recorded["request"]["client_request_id"])
        if not discover:
            assert historical_snapshot() == recorded["after"]
            assert row["response"]["gm_output"]["player_facing_text"] == recorded["player_facing_text"]
        elif index == 4:
            assert_discovery(row, "prints", "milestone_mud_prints")


@pytest.fixture(scope="module")
def timeline_snapshots():
    return {}


@pytest.fixture
def timeline(replay, monkeypatch, timeline_snapshots):
    def restore(*, discover=False, through=7):
        key = discover, through
        root = storage.DATA_DIR
        if key not in timeline_snapshots:
            prefix(replay, monkeypatch, discover=discover, through=through)
            timeline_snapshots[key] = {
                path.relative_to(root): path.read_bytes() for path in root.rglob("*") if path.is_file()
            }
        else:
            for relative, content in timeline_snapshots[key].items():
                target = root / relative
                if not target.exists() or target.read_bytes() != content:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(content)
    return restore


def test_exact_t08(replay, monkeypatch):
    prefix(replay, monkeypatch)
    source = EXTENDED / "T08.json"
    recorded = load(source)
    assert historical_snapshot() == recorded["before"]
    original_adapter = live.request_interpretation
    interpretation_context = []

    def capture(messages, **kwargs):
        interpretation_context.extend(messages)
        return original_adapter(messages, **kwargs)

    monkeypatch.setattr(live, "request_interpretation", capture)
    log = storage.load_log()
    row = play_capture(replay, source, recorded["request"]["client_request_id"], duplicate=True)
    outcome, = row["host"]["interpret_production_turn"]
    assert outcome["raw_interpretation"] == recorded["interpreter_outcomes"][0]["result"]["raw_interpretation"]
    assert outcome["record"] == recorded["interpreter_outcomes"][0]["result"]["record"]
    assert historical_snapshot() == recorded["after"]
    assert_quiet(row)
    row["interpretation_context"] = interpretation_context
    row["conversation_prefix"] = log
    row["public_evidence_candidates"] = co.public_conversation_evidence(row["before"]["active_scene"], log)
    trace("exact-t08", row)
    if os.environ.get("ASHEN_SCENE_SCOPE_BASELINE") == "1":
        assert reason(row) == "communication_before_execution"
        assert row["response"] == recorded["response"]
    else:
        answer = row["response"]["gm_output"]["player_facing_text"]
        assert "not established" in answer.lower()
        assert "overlapping prints" not in answer
        assert reason(row) == "current_observation_unestablished"


GATE_CONTROLS = [
    ("overview", "What can I see around me?", "Cinderwatch Gate District"),
    ("relative-front", "What is directly in front of me?", "not established"),
    ("ground-tracks", "Are there tracks on the ground here?", "not established"),
    ("offscene-sightline", "Can I see the old milestone from here?", "not established"),
    ("notice-presence", "Is the notice board still nearby?", "notice board"),
    ("guard-plural", "Are the guards still at this gate?", "not established"),
    ("road-adjacency", "What is beside the road?", "not established"),
    ("mud-sightline", "Is the muddy ground visible from here?", "not established"),
    ("present-see", "Can I see the footprints?", "not established"),
    ("present-position", "Are the prints in front of me?", "not established"),
    ("notice-contents", "What is on the notice board?", "lists taxes"),
    ("speaker-presence", "Is the captain here?", "Guard Captain"),
    ("present-demonstrative", "Are those prints still in front of me?", "not established"),
    ("false-premise", "Is the abandoned wagon here?", "not established"),
]
RECALL_CONTROLS = [
    ("prior-scene", "What did I see at the old milestone?", "Earlier, at Old Milestone", "Old Milestone"),
    ("inspection-detail", "What did I notice about the footprints?", "not established", PRINTS),
    ("past-encounter", "Where did I encounter those tracks?", "not established", "At Old Milestone"),
    ("unread-notice", "What did the notice board say?", "not established", "not established"),
    ("patrol-knowledge", "What did I learn about the missing patrol?", "not established", "not established"),
    ("remember-place", "Do I remember the mud near the milestone?", "Earlier, at Old Milestone", PRINTS),
    ("past-sight", "Did I see footprints earlier?", "not established", "At Old Milestone"),
    ("past-location", "Where were the prints?", "Earlier, at Old Milestone", "At Old Milestone"),
    ("past-discovery", "What did I discover at the milestone?", "not established", PRINTS),
    ("find-location", "Where did I see those prints?", "Earlier, at Old Milestone", "At Old Milestone"),
]
BARE_REFERENCES = [
    ("those-prints", "those prints"),
    ("same-tracks", "the same tracks"),
    ("that-notice", "that notice"),
    ("earlier-markings", "the markings I saw earlier"),
    ("left-place", "the place we just left"),
    ("back-there", "what I found back there"),
    ("captain-warning", "the captain's warning"),
    ("muddy-patch", "that muddy patch"),
]


def verify_information(name, row, expected=None, *, forbid_discovery=True):
    assert_quiet(row)
    for key in ("scene_state", "lead_registry", "npc_runtime", "position", "character_position"):
        assert row["before"]["session"].get(key) == row["after"]["session"].get(key), (name, key)
    answer = row["response"]["gm_output"]["player_facing_text"]
    assert answer
    if expected:
        assert expected.casefold() in answer.casefold().replace("not been established", "not established"), (name, answer)
    decision = row["persisted_log_resolution"]["metadata"].get("conversational_decision") or {}
    assert decision.get("requires_authoritative_execution") is not True
    assert "An agent of a noble house" not in answer
    if row["before"]["session"]["active_scene_id"] == "frontier_gate":
        assert "The mud around the marker is churned" not in answer
    if forbid_discovery:
        assert PRINTS not in answer
    row["evidence_scope"] = {
        "active_scene": row["before"]["session"]["active_scene_id"],
        "prior_scenes": row["before"]["session"]["visited_scene_ids"],
        "known_clues": row["before"]["session"]["clue_knowledge"],
        "undiscovered_clues": sorted({"milestone_mud_prints", "notice_patrol_route"}
                                    - row["before"]["session"]["clue_knowledge"].keys()),
        "route_and_admission": decision,
        "published_evidence_refs": decision.get("context_references") or [],
        "current_public_evidence": co.public_conversation_evidence(row["before"]["active_scene"], []),
        "changed_state_sections": [key for key in row["before"] if row["before"][key] != row["after"][key]],
    }
    trace(name, row)
    return decision


@pytest.mark.parametrize("discover", [False, True], ids=["undiscovered", "discovered"])
@pytest.mark.parametrize(("label", "text", "expected"), GATE_CONTROLS, ids=[row[0] for row in GATE_CONTROLS])
def test_gate_observation(replay, timeline, discover, label, text, expected):
    timeline(discover=discover)
    name = f"gate-{label}-{int(discover)}"
    row = replay(name, {"text": text}, duplicate=True)
    decision = verify_information(name, row, expected)
    assert decision["authorization"]["scene_id"] == "frontier_gate"
    assert not any(ref.startswith(("reply:", "historical", "clue_knowledge:"))
                   for ref in decision["context_references"])


@pytest.mark.parametrize("discover", [False, True], ids=["undiscovered", "discovered"])
@pytest.mark.parametrize(("label", "text", "before", "after"), RECALL_CONTROLS, ids=[r[0] for r in RECALL_CONTROLS])
def test_historical_recall(replay, timeline, discover, label, text, before, after):
    timeline(discover=discover)
    name = f"recall-{label}-{int(discover)}"
    row = replay(name, {"text": text}, duplicate=True)
    verify_information(name, row, after if discover else before, forbid_discovery=not discover)


@pytest.mark.parametrize("discover", [False, True], ids=["undiscovered", "discovered"])
@pytest.mark.parametrize(("label", "text"), BARE_REFERENCES, ids=[r[0] for r in BARE_REFERENCES])
def test_bare_reference(replay, timeline, discover, label, text):
    timeline(discover=discover)
    name = f"reference-{label}-{int(discover)}"
    row = replay(name, {"text": text}, duplicate=True)
    verify_information(name, row)


@pytest.mark.parametrize(("label", "text", "expected"), [
    ("prints-current", "Are the prints still here?", "faint overlapping prints"),
    ("milestone-current", "Can I see the old milestone from here?", "weathered"),
    ("precise-front", "Are the prints in front of me?", "not established"),
    ("prior-notice-here", "Is the notice board still nearby?", "not established"),
    ("prior-npc-here", "Is the captain here?", "not established"),
])
def test_at_old_milestone(replay, timeline, label, text, expected):
    timeline(through=4)
    name = f"milestone-{label}"
    row = replay(name, {"text": text}, duplicate=True)
    verify_information(name, row, expected)
    assert row["before"]["session"]["active_scene_id"] == "old_milestone"


@pytest.mark.parametrize(("label", "purpose", "components", "evidence"), [
    ("old-reply-only", "QUESTION", [("ASK", None, "Ask the GM")], ["reply:0"]),
    ("independent-operation", "QUESTION", [("MOVE", None, "Move"), ("ASK", None, "Ask")], ["reply:0"]),
    ("unsupported-subject", "DESCRIPTION", [], ["reply:0", "visible:3"]),
    ("wrong-scene-target", "QUESTION", [("ASK", "prints", "Ask about prints")], ["reply:0"]),
])
def test_unresolved_interpretation_scope(replay, timeline, label, purpose, components, evidence):
    timeline()
    name = f"interpretation-{label}"
    raw = interpretation(*components, recipient="GM", purpose=purpose, evidence=evidence)
    row = replay(name, {"text": "Are those prints still in front of me?"}, json.dumps(raw), duplicate=True)
    decision = verify_information(name, row)
    if label == "wrong-scene-target":
        assert row["host"]["interpret_production_turn"][0]["status"] == "blocked"
        assert not decision.get("context_references")
    else:
        assert decision["reason"] == "current_observation_unestablished"
    assert len(row["host"]["offline_adapter"]) == 1


def test_captain_recall_after_successful_dialogue(replay, timeline):
    timeline()
    setup = play_capture(replay, EXTENDED / "T10.json", "scope-t10", duplicate=True)
    assert setup["response"]["gm_output"]["player_facing_text"] == CAPTAIN
    assert len(setup["host"]["advance_world_tick"]) == 1
    name = "captain-past-dialogue"
    row = replay(name, {"text": "What did the captain tell me earlier?"}, duplicate=True)
    verify_information(name, row, "patrol went missing near the old milestone")


def test_discovered_notice_recall_across_scenes(replay):
    inspected = play_capture(replay, EXTENDED / "T01.json", "scope-t01", duplicate=True)
    assert_discovery(inspected, "notice_board", "notice_patrol_route")
    play_capture(replay, EXTENDED / "T03.json", "scope-t03")
    row = replay("remote-notice-recall", {"text": "What did the notice board say?"}, duplicate=True)
    assert row["response"]["gm_output"]["player_facing_text"] == ROUTE
    assert row["before"]["session"]["active_scene_id"] == "old_milestone"
    assert row["before"]["character"] == row["after"]["character"]
    assert row["before"]["world"] == row["after"]["world"]
    assert gameplay_session(row["before"]["session"]) == gameplay_session(row["after"]["session"])
    assert not row["host"].get("advance_world_tick")


def test_return_and_reexamine(replay, timeline):
    timeline()
    returned = play_capture(replay, EXTENDED / "T03.json", "scope-return-to-milestone", duplicate=True)
    assert returned["after"]["session"]["active_scene_id"] == "old_milestone"
    assert not returned["after"]["session"]["clue_knowledge"]
    assert len(returned["host"]["advance_world_tick"]) == 1
    name = "scope-reexamine-after-return"
    row = replay(name, {"text": "Can I examine the prints again?"}, duplicate=True)
    # Returning alone did not examine. The explicit examination question has
    # the established local resolver available once an attempt is committed.
    verify_information(name, row)
    examined = play_capture(replay, EXTENDED / "T04.json", "scope-reinspect-commit", duplicate=True)
    assert_discovery(examined, "prints", "milestone_mud_prints")


def test_captured_t12_remains_information_only(replay, timeline):
    timeline(discover=True)
    play_capture(replay, EXTENDED / "T10.json", "scope-t12-captain")
    row = play_capture(replay, EXTENDED / "T12.json", "scope-t12", duplicate=True)
    verify_information("scope-t12", row)
    assert CAPTAIN not in row["response"]["gm_output"]["player_facing_text"]


def test_authoritative_location_conflict():
    wrong_scene = {"scene": {"id": "old_milestone", "location": "Old Milestone",
                             "visible_facts": ["The prints go northwest."]}}
    decision = co.decision_from_interpretation_record(
        None, player_text="Are the prints still here?", scene=wrong_scene,
        session={"active_scene_id": "frontier_gate"},
    )
    assert decision.reason == "current_observation_unestablished"
    assert decision.authorization["scene_id"] == "frontier_gate"
    assert not decision.context_references
    assert "northwest" not in decision.player_facing_text
    trace("contract-authority-mismatch", {"scene": wrong_scene, "decision": decision.to_public_dict()})


def test_overview_hides_internal_scene_entities():
    scene = {"scene": {"id": "gate", "location": "Gate", "interactables": [
        {"id": "notice", "label": "Public notice"},
        {"id": "hidden", "label": "Hidden Cache", "hidden": True},
        {"id": "memo", "label": "Private memo", "gm_only": True},
        {"id": "door", "label": "Unseen door", "visible": False},
        {"id": "alcove", "label": "Sealed alcove", "accessible": False},
    ], "exits": [{"label": "Secret exit", "hidden": True}]}}
    decision = co.deterministic_conversational_decision(player_text="What can I see?", scene=scene)
    assert decision.context_references == ["active_scene_public_summary"]
    assert decision.player_facing_text == "You are at Gate. Visible points of interest: Public notice."
    trace("contract-hidden-entities", {"scene": scene, "decision": decision.to_public_dict()})


def test_mixed_refusal_rechecks_candidate_provenance():
    scene = {"id": "gate", "visible_facts": ["The gate is crowded."]}
    record = interpretation(
        ("MOVE", None, "Move toward the prints"), recipient="MIXED", purpose="QUESTION",
        evidence=["reply:0", "visible:0"],
    )
    record["public_evidence"] = {"reply:0": "The mud at the milestone has prints.",
                                 "visible:0": "The previous location is visible."}
    decision = co.decision_from_interpretation_record(
        record, player_text="Are those prints here? If they are, I'll follow them.",
        scene=scene, session={"active_scene_id": "gate"},
    )
    assert decision.category == co.ConversationalDecisionCategory.CLARIFY
    assert decision.context_references == ["visible:0"]
    assert "The gate is crowded." in decision.player_facing_text
    assert "milestone" not in decision.player_facing_text
    assert "previous location" not in decision.player_facing_text
    assert not decision.requires_authoritative_execution
    trace("contract-mixed-refusal", {"scene": scene, "record": record, "decision": decision.to_public_dict()})


def test_current_presence_while_captain_is_active(replay, timeline):
    timeline(discover=True)
    play_capture(replay, EXTENDED / "T10.json", "scope-active-captain")
    name = "scope-active-captain-present-question"
    row = replay(name, {"text": "Are those prints still visible?"}, duplicate=True)
    decision = verify_information(name, row, "not established")
    assert decision["reason"] == "current_observation_unestablished"


def test_inspection_capability_from_another_scene(replay, timeline):
    timeline()
    name = "scope-offscene-inspection-capability"
    row = replay(name, {"text": "Can I inspect the milestone?"}, duplicate=True)
    verify_information(name, row)
    assert row["before"]["session"]["active_scene_id"] == "frontier_gate"


def test_no_captain_recall_before_dialogue(replay, timeline):
    timeline()
    name = "scope-captain-before-dialogue"
    row = replay(name, {"text": "What did the captain tell me earlier?"}, duplicate=True)
    verify_information(name, row)
    assert CAPTAIN not in row["response"]["gm_output"]["player_facing_text"]
    assert "patrol went missing" not in row["response"]["gm_output"]["player_facing_text"]
