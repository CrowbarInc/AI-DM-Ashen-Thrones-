"""Offline replay and ownership controls for delivered statements."""
import copy
import os

import pytest

from game import api, conversational_continuity as continuity, conversational_orchestration as co
from game import dialogue_authority, ordinary_semantic_ownership, social, storage
from game.clues import get_all_known_clue_ids, get_all_known_clue_texts
from tests.test_inspection_communication_admission import (
    EXTENDED, SHORT, assert_discovery, captured, gameplay_session, load, reason, replay, state, trace,
)

CAPTAIN = 'Guard Captain mutters, "Word is, a patrol went missing near the old milestone."'
PRINTS = "Faint overlapping prints mark the mud around the old milestone, but their number, origin, and direction stay unclear."
T12 = "Do those prints tell us which way the patrol went?"


def historical_snapshot():
    session, character, world = (storage.load_session(), storage.load_character(), storage.load_world())
    return {
        "campaign_id": session["campaign_run_id"], "session_id": session["session_id"],
        "scene": session["active_scene_id"], "visited": session["visited_scene_ids"],
        "date": session["current_date"], "turn": session["turn_counter"],
        "time_pressure": session["clocks"]["time_pressure"], "clocks": session["clocks"],
        "clue_ids": sorted(get_all_known_clue_ids(session)),
        "clue_texts": sorted(get_all_known_clue_texts(session)),
        "clue_knowledge": session.get("clue_knowledge") or {}, "flags": session.get("flags") or {},
        "inventory": character["inventory"], "spells": character["spells"], "hp": character["hp"],
        "world_flags": world["world_state"]["flags"],
        "interlocutor": (session.get("scene_state") or {}).get("current_interlocutor"),
        "log_count": len(storage.load_log()),
    }


def play_prefix(replay, monkeypatch, *, discover=False):
    for index in range(1, 12):
        source = EXTENDED / f"T{index:02}.json"
        if discover and index == 4:
            request, raw = captured(SHORT / "live_execution/T4.json")
            row = replay("counterfactual-discovery", request, raw)
            assert_discovery(row, "prints", "milestone_mud_prints")
            continue
        historical = load(source)
        request, raw = captured(source)
        with monkeypatch.context() as historical_t01:
            if index == 1:
                # Restore the recorded T01 admission failure only while building
                # the historical prefix. The current T01 repair has its own test.
                reconcile = co._inspection_communication_consistency

                def old_admission(record, text, **kwargs):
                    return reconcile(record, text + " now", **kwargs)

                historical_t01.setattr(co, "_inspection_communication_consistency", old_admission)
            if index == 4:
                # Preserve the recorded clue-free timeline for the historical
                # T12 control. T04's repaired outcome has its own exact replay.
                historical_t01.setattr(co, "_normalize_inspection_posture", lambda record, *args, **kwargs: record)
            if index == 8 and not discover:
                # Keep the exact delivered history for T12's original
                # reproduction. T08's publication fix has its own HTTP replay.
                historical_t01.setattr(co, "_current_observation_decision", lambda *args, **kwargs: None)
            if not discover:
                assert historical_snapshot() == historical["before"]
            row = replay(f"{'discovered' if discover else 'original'}-T{index:02}", request, raw)
        if not discover:
            assert historical_snapshot() == historical["after"]
            assert row["response"]["gm_output"]["player_facing_text"] == historical["player_facing_text"]


@pytest.mark.parametrize("discover", [False, True], ids=["original", "counterfactual"])
def test_exact_t12(replay, monkeypatch, discover):
    if discover and os.environ.get("ASHEN_REPEAT_BASELINE") == "1":
        pytest.skip("Pre-edit reproduction uses the original clue state.")
    play_prefix(replay, monkeypatch, discover=discover)
    source = EXTENDED / "T12.json"
    historical = load(source)
    if not discover:
        assert historical_snapshot() == historical["before"]
    request, _ = captured(source)
    session = storage.load_session()
    clue = session["clue_knowledge"].get("milestone_mud_prints")
    if discover:
        assert clue == {"state": "discovered", "source_scene": "old_milestone",
                        "source_interactable": "prints", "presentation": "explicit", "text": PRINTS}
    else:
        assert clue is None
    text = request["text"]
    routing = []
    for module, name in ((api, "deterministic_conversational_decision"),
                         (co, "_discovery_recall_decision"),
                         (co, "_gm_information_decision"),
                         (co, "decision_from_delivered_exchange"),
                         (co, "_active_dialogue_followup_decision"),
                         (ordinary_semantic_ownership, "assess_addressee_grounding"),
                         (social, "resolve_social_action"),
                         (continuity, "_best_exchange"),
                         (dialogue_authority, "classify_answer_sufficiency")):
        original = getattr(module, name)

        def capture(*args, _original=original, _name=name, **kwargs):
            result = _original(*args, **kwargs)
            routing.append([_name, copy.deepcopy(result.to_public_dict() if hasattr(result, "to_public_dict") else result)])
            return result

        monkeypatch.setattr(module, name, capture)
    label = "counterfactual-t12" if discover else "exact-t12"
    row = replay(label, request, duplicate=True)
    trace(label + "-routing", {
        "routing": routing, "conversation_before": session.get("conversational_context"),
        "recall_cues": {name: bool(pattern.search(text))
                        for name in ("_REPEAT", "_MEANING", "_DEICTIC", "_AGAIN", "_EARLIER",
                                     "_CONTEXTUAL_STATEMENT_RE", "_POSSESSIVE_STATEMENT_RE")
                        if (pattern := getattr(continuity, name, None)) is not None},
        "player_tokens": continuity._tokens(text),
    })
    if os.environ.get("ASHEN_REPEAT_BASELINE") == "1":
        assert reason(row) == "repeat_delivered_statement"
        assert row["response"] == historical["response"]
        assert historical_snapshot() == historical["after"]
        assert not row["host"].get("interpret_production_turn")
    else:
        assert reason(row) == "information_unresolved"
        assert row["host"]["interpret_production_turn"] == [{
            "status": "skipped", "reason": "provider_calls_disabled", "record": None, "provider_requests": [],
        }]
        line = row["response"]["gm_output"]["player_facing_text"]
        assert line == "I haven't resolved that question from the disclosed information."
        assert PRINTS not in line and CAPTAIN not in line
        assert not row["persisted_log_resolution"]["metadata"]["resolver_invoked"]
        assert not any(name == "resolve_social_action" for name, _ in routing)
    assert_read_only(row)
    assert row["after"] == state()


def assert_read_only(row):
    assert gameplay_session(row["before"]["session"]) == gameplay_session(row["after"]["session"])
    for key in ("character", "world", "active_scene", "combat", "conditions", "campaign"):
        assert row["before"][key] == row["after"][key], key
    for name in ("advance_world_tick", "resolve_exploration_action", "offline_adapter"):
        assert not row["host"].get(name), name


@pytest.fixture
def conversation():
    """Synthetic history controls with a stable NPC proposition and a second voice."""
    session = {}
    scene = {"id": "frontier_gate", "interactables": [{"id": "notice_board", "label": "Notice board"}]}
    world = {"npcs": [
        {"id": "guard_captain", "name": "Guard Captain", "location": "frontier_gate"},
        {"id": "officer", "name": "Officer Vale", "location": "frontier_gate"},
    ]}

    def add(voice="captain", *, content=None, player_text=None, scene_id="frontier_gate"):
        name, npc_id, default, question = {
            "captain": ("Guard Captain", "guard_captain", "A patrol went missing near the old milestone.",
                        "I ask the guard captain about the patrol."),
            "officer": ("Officer Vale", "officer", "The notice is posted beside the crates.",
                        "I ask Officer Vale about the notice."),
            "gm": ("", "", "A few refugees cross the square.", "What do I see?"),
            "player": ("", "", "I will return after dark.", "I will return after dark."),
        }[voice]
        line = content or default
        return continuity.record_delivered_exchange(
            session, player_text=player_text or question, scene_id=scene_id,
            delivered_text=f'{name} says, "{line}"' if name else line,
            social={"npc_id": npc_id, "npc_name": name} if npc_id else {},
            ownership="npc" if npc_id else voice,
        )

    return session, scene, world, add


def evaluate(name, conversation, text):
    session, scene, world, _ = conversation
    before = copy.deepcopy(conversation[:3])
    directive = continuity.continuity_directive(text, session=session, scene=scene, world=world)
    assert conversation[:3] == before
    trace(name, {"request": text, "scene": scene, "world": world, "session": session, "directive": directive,
                 "candidate": "continuity_directive", "state_delta": {}})
    return directive or {}


@pytest.mark.parametrize("label,text", [
    ("prints-bearing", T12),
    ("patrol-destination", "Where did the patrol go?"),
    ("footprints-meaning", "What do the footprints indicate?"),
    ("track-visibility", "Can I still see the tracks?"),
    ("known-discovery", "What did I discover at the milestone?"),
    ("patrol-last-sighting", "Where was the patrol last seen?"),
    ("notice-presence", "Is the notice still here?"),
    ("current-scene", "What can I see from this location?"),
    ("tracks-inference", "What do the tracks tell me?"),
    ("notice-discovery", "What did I learn from the notice?"),
    ("distinct-bearings", "Did the patrol go north or south?"),
    ("counts", "How many members did the patrol have?"),
    ("repeat-world-event", "Did the patrol repeat the route?"),
    ("tell-again-world-fact", "Tell me where the patrol went again."),
    ("again-discovery-question", "Tell me again what I learned from the notice."),
    ("remind-world-event", "Remind me what the patrol did."),
    ("question-about-object", "What was that notice for?"),
    ("earlier-world-event", "Where did the patrol go earlier?"),
    ("same-world-event", "Did the patrol take the same road?"),
    ("quoted-repeat", 'I write "repeat the patrol warning" in my notebook.'),
    ("repeat-physical-action", "Can you repeat the notice board inspection about the patrol?"),
    ("npc-command", "I ask the captain to repeat the patrol warning."),
])
def test_world_questions_do_not_repeat(conversation, label, text):
    _, _, _, add = conversation
    add()
    got = evaluate(label, conversation, text)
    assert got.get("reason") not in {
        "repeat_delivered_statement", "delivered_speaker_attribution", "absent_npc_reference",
    }
    assert "patrol went missing" not in got.get("line", "")


@pytest.mark.parametrize("label,text,voice,speaker,needle", [
    ("named-last-speech", "What did the captain just say?", "captain", "guard_captain", "patrol went missing"),
    ("repeat-named", "Repeat what the captain told me.", "captain", "guard_captain", "patrol went missing"),
    ("possessive-pronoun", "What was his last statement?", "captain", "guard_captain", "patrol went missing"),
    ("remind-pronoun", "Remind me what she said.", "officer", "officer", "notice is posted"),
    ("bare-repeat", "Can you repeat that?", "captain", "guard_captain", "patrol went missing"),
    ("tell-again-named", "Tell me again what the officer said.", "officer", "officer", "notice is posted"),
    ("named-subject", "What did the captain say about the patrol?", "captain", "guard_captain", "patrol went missing"),
    ("pronoun-subject", "Repeat what he told me about the tracks.", "captain", "guard_captain", "Tracks overlap"),
    ("attributed-pronoun-topic", "What did she say about the notice?", "officer", "officer", "notice is posted"),
    ("possessive-name", "What was the captain's answer?", "captain", "guard_captain", "patrol went missing"),
    ("contextual-last-statement", "What was that last statement?", "captain", "guard_captain", "patrol went missing"),
    ("simpler-words", "Say that again in simpler words.", "captain", "guard_captain", "patrol went missing"),
    ("topic-return", "Go back to what was said about the patrol.", "captain", "guard_captain", "patrol went missing"),
    ("who-mentioned", "Who mentioned the patrol?", "captain", "guard_captain", "patrol went missing"),
])
def test_grounded_statement_recall(conversation, label, text, voice, speaker, needle):
    _, _, _, add = conversation
    add(voice, content="Tracks overlap beside the marker." if label == "pronoun-subject" else None)
    got = evaluate(label, conversation, text)
    assert got.get("action") == "answer"
    assert got["npc_id"] == speaker
    assert needle in got["line"]


@pytest.mark.parametrize("label,text,setup,expected_speaker,expected_line", [
    ("empty", "Can you repeat that?", (), "", ""),
    ("speakerless", "Can you repeat that?", ("gm",), "", ""),
    ("player-only", "Can you repeat that?", ("player",), "", ""),
    ("two-voices", "Remind me what she said.", ("captain", "officer"), "", ""),
    ("named-among-two", "What did the captain say?", ("captain", "officer"), "guard_captain", "patrol went missing"),
    ("missing-topic", "Repeat what the captain told me about the treasury.", ("captain",), "", ""),
    ("missing-speaker", "Tell me again what the officer said.", ("captain",), "", ""),
    ("unrelated-intervening", "What did the captain say about the patrol?", ("captain", "gm", "officer"), "guard_captain", "patrol went missing"),
    ("gm-intervenes", "Can you repeat that?", ("captain", "gm"), "", ""),
    ("named-absent", "What did the captain say?", ("captain", "leave"), "guard_captain", "patrol went missing"),
    ("absent-world-question", T12, ("captain", "leave"), "", ""),
    ("similar-topics", "What did the captain say about the patrol?", ("captain", "alternate"), "", ""),
    ("protected-row", "What did the captain say?", ("protected",), "", ""),
    ("uncertain-row", "What did the captain say?", ("uncertain",), "guard_captain", "could not tell"),
    ("no-substitution", "What did Officer Vale say?", ("captain",), "", ""),
    ("same-voice-explicit-last", "What was his last statement?", ("captain", "alternate"), "guard_captain", "patrol waited"),
])
def test_history_boundaries(conversation, label, text, setup, expected_speaker, expected_line):
    _, scene, _, add = conversation
    for item in setup:
        if item == "leave":
            scene["id"] = "old_milestone"
        elif item == "alternate":
            add(content="The patrol waited for the storm to pass.", player_text="I ask about the patrol.")
        elif item == "protected":
            row = add()
            row["authorization_source"] = "dialogue_authority.disclosure_denied"
            row["delivered_text"] = "CANARY_PRIVATE_CLUE_02"
            row["supplied_text"] = row["delivered_text"]
        elif item == "uncertain":
            add(content="I could not tell you where the patrol went.")
        else:
            add(item)
    got = evaluate(label, conversation, text)
    if expected_line:
        assert got.get("action") == "answer"
        assert got.get("npc_id") == expected_speaker
        assert expected_line in got["line"]
    else:
        assert got.get("action") in (None, "clarify")
        assert got.get("npc_id", "") == expected_speaker
        assert "is not here" not in got.get("line", "")
        assert "CANARY" not in got.get("line", "")


@pytest.mark.parametrize("label,text,in_reply", [
    ("http-bare-recall", "Can you repeat that?", "patrol went missing near the old milestone"),
    ("http-named-recall", "Repeat what the captain told me.", "patrol went missing near the old milestone"),
    ("http-named-question", "What did the captain just say?", "patrol went missing near the old milestone"),
    ("http-missing-topic", "What did the captain say about the treasury?", "established"),
    ("http-unread-notice", "Where was the patrol last seen?", "has not been established"),
])
def test_http_information_only(replay, label, text, in_reply):
    request, raw = captured(EXTENDED / "T10.json")
    captain = replay(label + "-setup", request, raw)
    assert captain["response"]["gm_output"]["player_facing_text"] == CAPTAIN
    assert captain["after"]["session"]["turn_counter"] == captain["before"]["session"]["turn_counter"] + 1
    row = replay(label, {"text": text}, duplicate=True)
    line = row["response"]["gm_output"]["player_facing_text"]
    assert in_reply in line.casefold()
    if label == "http-unread-notice":
        assert reason(row) != "repeat_delivered_statement" and CAPTAIN not in line
    assert_read_only(row)


def test_http_captured_captain_speech(replay):
    request, raw = captured(EXTENDED / "T10.json")
    row = replay("http-captured-captain", request, raw, duplicate=True)
    assert row["response"]["gm_output"]["player_facing_text"] == CAPTAIN
    after, before = row["after"], row["before"]
    assert set(after["session"]["clue_knowledge"]) - set(before["session"].get("clue_knowledge", {})) == {
        "social_frontier_gate_guard_captain_patrol", "lead_frontier_gate_old_milestone",
    }
    assert after["character"] == before["character"]
    assert after["session"]["turn_counter"] == before["session"]["turn_counter"] + 1
    assert len(row["host"]["advance_world_tick"]) == 1


def test_http_current_scene_without_active_npc(replay):
    row = replay("http-current-scene", {"text": "What can I see from here?"}, duplicate=True)
    assert reason(row) == "visible_scene_context_answer"
    assert "Cinderwatch Gate District" in row["response"]["gm_output"]["player_facing_text"]
    assert_read_only(row)


def test_http_current_scene_with_active_npc_declines_repeat(replay):
    request, raw = captured(EXTENDED / "T10.json")
    replay("http-active-current-scene-setup", request, raw)
    text = "What can I see from this location?"
    before = state()
    assert continuity.continuity_directive(text, session=before["session"],
                                           scene=before["active_scene"], world=before["world"]) is None
    row = replay("http-active-current-scene", {"text": text}, duplicate=True)
    assert reason(row) == "visible_scene_context_answer"
    assert "Cinderwatch Gate District" in row["response"]["gm_output"]["player_facing_text"]
    assert_read_only(row)


@pytest.mark.parametrize("label,text,kind,topic", [
    ("http-direct-patrol", "I ask the captain about the patrol.", "question", "patrol"),
    ("http-direct-report", "I tell the captain what I found.", "social_probe", None),
    ("http-pronoun-speech", "I ask whether he knows anything else.", "conversational_clarify", None),
])
def test_http_directed_speech_keeps_legacy_route(replay, label, text, kind, topic):
    initial = state()
    assert continuity.continuity_directive(text, session=initial["session"],
                                           scene=initial["active_scene"], world=initial["world"]) is None
    row = replay(label, {"text": text}, duplicate=True)
    resolution = row["persisted_log_resolution"]
    assert (resolution.get("metadata", {}).get("conversational_decision") or {}).get("reason") != "repeat_delivered_statement"
    before, after = row["before"], row["after"]
    assert resolution["kind"] == kind
    line = row["response"]["gm_output"]["player_facing_text"]
    if kind == "conversational_clarify":
        assert reason(row) == "unresolved_addressee" and "Nothing has been attempted" in line
        assert CAPTAIN not in line
        assert_read_only(row)
        return
    assert resolution["success"] is True
    assert resolution["social"]["npc_id"] == "guard_captain"
    assert resolution["social"]["target_resolved"] is True
    assert after["session"]["turn_counter"] == before["session"]["turn_counter"] + 1
    assert len(row["host"]["advance_world_tick"]) == 1
    assert (resolution["social"]["topic_revealed"] or {}).get("id") == topic
    if topic:
        assert line == CAPTAIN
        assert set(after["session"]["clue_knowledge"]) - set(before["session"]["clue_knowledge"]) == {
            "social_frontier_gate_guard_captain_patrol", "lead_frontier_gate_old_milestone",
        }
    else:
        assert CAPTAIN not in line
        assert after["session"]["clue_knowledge"] == before["session"]["clue_knowledge"]
    assert not resolution["resolved_transition"] and not row["host"].get("resolve_exploration_action")
    assert after["character"] == before["character"]
