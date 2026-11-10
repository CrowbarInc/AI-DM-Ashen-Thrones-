"""PR-PLAY-79A conversational continuity, grounded narration, and provider skip."""
import copy

import pytest

from game.api import deterministic_provider_skip_line
from game.authored_consequences import ENROLLMENT
from game.bounded_improvisation import LEDGER_KEY, focused_present_npc
from game.expressive_dialogue import (
    background_conversation,
    build_expression_prompt,
    set_expression_transport,
    validate_expression,
)
from game.general_purpose_actions import classify
from game.integrated_play import validate_narration
from game.player_initiative import decide
from tests.test_pr_play_76_physical import enable
from tests.test_pr_play_78_integrated import play


def gate():
    session = {
        "campaign_run_id": "alpha",
        "active_scene_id": "frontier_gate",
        "turn_counter": 2,
        ENROLLMENT: "alpha",
        LEDGER_KEY: {"entries": [], "physical_state": {}, "investigation_notes": []},
    }
    scene = {
        "scene": {
            "id": "frontier_gate",
            "location": "Frontier Gate",
            "visible_facts": ["The notice board lists a warning about a missing patrol."],
            "hidden_facts": ["The missing patrol was last seen taking the northwest mud track."],
            "discoverable_clues": [{
                "id": "route",
                "text": "The missing patrol was last seen taking the northwest mud track.",
            }],
            "interactables": [],
            "addressables": [],
        }
    }
    world = {
        "npcs": [
            {"id": "gate_guard", "name": "Gate Guard", "location": "frontier_gate", "role": "guard", "aliases": ["guard"]},
            {"id": "gate_serjeant", "name": "Gate Serjeant", "location": "frontier_gate", "role": "serjeant"},
        ],
        "world_state": {"flags": {}},
    }
    return session, scene, world


@pytest.fixture
def ready(monkeypatch):
    enable(monkeypatch)
    monkeypatch.setenv("ASHEN_EXPERIMENTAL_DYNAMIC_NPCS", "1")
    monkeypatch.setenv("ASHEN_DISABLE_EXPRESSION_GENERATION", "1")
    return gate()


def _say(session, scene, world, text):
    _plan, _result, said, _changed = play(text, session, scene, world)
    return said


FOLLOWUPS = [
    ("Who are you?", "gate guard"),
    ("What do you know about the missing patrol?", "missing patrol"),
    ("When did you last hear about them?", "not certain"),
    ("Do you think something happened?", "not certain"),
    ("What about the patrol again?", "missing patrol"),
]


def test_greeting_creates_the_active_interlocutor(ready):
    session, scene, world = ready
    said = _say(session, scene, world, "Hello, Gate Guard.")
    assert "hello" in said.casefold()
    assert "which person" not in said.casefold()
    slot = session["conversational_context"]["active_interlocutor"]
    assert slot["npc_id"] == "gate_guard"
    assert slot["status"] == "active"
    assert slot["scene_id"] == "frontier_gate"
    assert session["interaction_context"]["active_interaction_target_id"] == "gate_guard"
    assert session[LEDGER_KEY]["npc_focus"] == "gate_guard"


@pytest.mark.parametrize("text,fragment", FOLLOWUPS, ids=[f"follow-{i}" for i in range(len(FOLLOWUPS))])
def test_followups_stay_with_the_gate_guard(ready, text, fragment):
    session, scene, world = ready
    _say(session, scene, world, "Hello, Gate Guard.")
    said = _say(session, scene, world, text)
    low = said.casefold()
    assert "gate guard says" in low
    assert fragment in low
    assert "northwest" not in low
    assert "which person" not in low
    assert "which available" not in low
    assert session[LEDGER_KEY]["npc_focus"] == "gate_guard"


def test_player_need_not_repeat_the_name(ready):
    session, scene, world = ready
    _say(session, scene, world, "Hello, Gate Guard.")
    for text in [item[0] for item in FOLLOWUPS]:
        assert "gate guard" not in text.casefold() or text.startswith("What about")
        said = _say(session, scene, world, text)
        assert "which person" not in said.casefold()


DISTINCTIONS = [
    ("What does the notice board say?", "missing patrol", "which person"),
    ("Where am I?", "frontier gate", "which person"),
    ("What do I know about the patrol?", "missing patrol", "which person"),
]


@pytest.mark.parametrize("text,present,absent", DISTINCTIONS, ids=["board", "place", "memory"])
def test_non_npc_questions_are_not_routed_to_the_guard(ready, text, present, absent):
    session, scene, world = ready
    _say(session, scene, world, "Hello, Gate Guard.")
    decision = decide(text, scene=scene, world=world, session=session)
    assert decision is not None
    low = (decision.player_facing_text or "").casefold()
    assert present in low
    assert absent not in low
    assert decision.proposed_operation != "ASK"


def test_explicit_switch_overrides_the_guard(ready):
    session, scene, world = ready
    _say(session, scene, world, "Hello, Gate Guard.")
    said = _say(session, scene, world, "Hello, Gate Serjeant.")
    assert "gate serjeant says" in said.casefold()
    assert session[LEDGER_KEY]["npc_focus"] == "gate_serjeant"


def test_goodbye_ends_the_interlocutor(ready):
    session, scene, world = ready
    _say(session, scene, world, "Hello, Gate Guard.")
    said = _say(session, scene, world, "Goodbye.")
    assert "gate guard says" in said.casefold()
    assert session[LEDGER_KEY]["npc_focus"] is None
    assert session["conversational_context"]["active_interlocutor"]["status"] == "ended"


def test_leaving_the_scene_drops_the_interlocutor(ready):
    session, scene, world = ready
    _say(session, scene, world, "Hello, Gate Guard.")
    session["active_scene_id"] = "old_milestone"
    later = {
        "scene": {
            "id": "old_milestone",
            "location": "Old Milestone",
            "visible_facts": ["A stone milestone leans beside the northwest mud track."],
            "interactables": [],
            "addressables": [],
        }
    }
    assert focused_present_npc(session, later, world) is None
    assert session[LEDGER_KEY]["npc_focus"] is None
    said = _say(session, later, world, "Who are you?")
    assert "gate guard says" not in said.casefold()


def test_campaign_change_does_not_keep_the_guard(ready):
    session, scene, world = ready
    _say(session, scene, world, "Hello, Gate Guard.")
    other = copy.deepcopy(session)
    other["campaign_run_id"] = "beta"
    other[ENROLLMENT] = "beta"
    assert focused_present_npc(other, scene, world) is None


def test_hidden_patrol_route_is_not_spoken(ready):
    session, scene, world = ready
    _say(session, scene, world, "Hello, Gate Guard.")
    for text in ("Where is the hidden patrol captain?", "What is the payroll?"):
        said = _say(session, scene, world, text)
        low = said.casefold()
        assert "do not know" in low or "not certain" in low
        assert "northwest" not in low
        assert "payroll" not in low
        assert "which person" not in low


def test_save_roundtrip_keeps_the_interlocutor(ready):
    from game import storage
    session, scene, world = ready
    _say(session, scene, world, "Hello, Gate Guard.")
    _say(session, scene, world, "Who are you?")
    storage.save_session(session)
    restored = storage.load_session()
    assert restored[LEDGER_KEY]["npc_focus"] == "gate_guard"
    assert restored["conversational_context"]["active_interlocutor"]["npc_id"] == "gate_guard"
    said = _say(restored, scene, world, "What do you know about the missing patrol?")
    assert "missing patrol" in said.casefold()
    assert "northwest" not in said.casefold()


NARRATION = [
    ("The tracks continue northwest through the mud.", "The player found tracks leading northwest.", True),
    ("Your earlier examination suggests the trail bends toward the northwest.", "Tracks lead northwest.", True),
    ("The disturbed ground still points northwest.", "northwest mud track", True),
    ("Fresh blood confirms the patrol was attacked.", "Tracks lead northwest.", False),
    ("The patrol captain was dragged northwest.", "Tracks lead northwest.", False),
    ("You discover the hidden patrol camp.", "Tracks lead northwest.", False),
    ("The tracks bend southeast from the stone.", "Tracks lead northwest.", False),
    ("There is no hidden passage. The tracks continue northwest.", "Tracks lead northwest.", True),
    ("Dust lifts as you move the loose stone aside from the stonework.", "You move the loose stone. It is now aside.", True),
    ("You find gold beside a secret passage.", "You move the loose stone.", False),
]


@pytest.mark.parametrize("candidate,facts,adopt", NARRATION, ids=[f"narr-{i}" for i in range(len(NARRATION))])
def test_established_fact_paraphrase(candidate, facts, adopt):
    verdict = validate_narration(candidate, facts, session={"clue_knowledge": {}})
    assert verdict["adopt"] is adopt


def test_discovered_direction_is_reusable_when_the_sentence_omits_it():
    session = {"clue_knowledge": {"route": {"state": "discovered", "text": "tracks lead northwest"}}}
    verdict = validate_narration(
        "The disturbed ground still points northwest.",
        "The mud is churned.",
        session=session,
    )
    assert verdict["adopt"] is True


def test_identical_narration_is_not_a_variation():
    facts = "The tracks continue northwest."
    assert validate_narration(facts, facts)["adopt"] is False


def test_primary_narration_is_skipped_after_a_committed_line():
    skipped = deterministic_provider_skip_line(
        resolution={"metadata": {"engine_publication": "Gate Guard says hello.", "skip_primary_narration": True}},
        scene={}, world={}, session={}, player_text="Who are you?",
    )
    assert skipped == ("Gate Guard says hello.", "committed_engine_publication")
    assert deterministic_provider_skip_line(
        resolution={"metadata": {"engine_publication": "Keep the provider.", "skip_primary_narration": False}},
        scene={}, world={}, session={}, player_text="Look.",
    ) is None


LIVE_LINES = [
    "Hello. The rain is steady on the gate.",
    "I am the gate guard on this watch.",
    "I do not know more than the notice about a missing patrol.",
    "I am not certain when I last heard anything further.",
    "I do not know whether something happened.",
    "I do not know more than that same notice.",
]


def test_six_live_lines_publish_when_they_stay_inside_authority(ready, monkeypatch):
    session, scene, world = ready
    monkeypatch.setenv("ASHEN_BOUNDED_SPEECH", "1")
    monkeypatch.setenv("ASHEN_DISABLE_EXPRESSION_GENERATION", "0")
    monkeypatch.setattr("game.expressive_dialogue.expression_generation_disabled", lambda: False)
    lines = iter(LIVE_LINES)

    def transport(contract):
        text = next(lines)
        return {
            "ok": True, "sent": True, "text": text, "latency_ms": 1, "model": "bounded-transport",
            "usage": {"input_tokens": 12, "output_tokens": max(1, len(text) // 4), "total_tokens": 12 + max(1, len(text) // 4)},
        }

    monkeypatch.setattr("game.expressive_dialogue.request_expression", transport)
    try:
        published = []
        for text in [
            "Hello, Gate Guard.",
            "Who are you?",
            "What do you know about the missing patrol?",
            "When did you last hear about them?",
            "Do you think something happened?",
            "What about the patrol again?",
        ]:
            _say(session, scene, world, text)
            audit = session["last_background_expression"]
            assert audit["adopted"] is True
            published.append(audit["attempt"]["text"])
        assert len(published) == 6
        assert len(set(published)) == 6
        assert all("northwest" not in line.casefold() for line in published)
    finally:
        set_expression_transport(None)


def test_dialogue_prompt_names_the_question_and_not_the_hidden_route(ready):
    session, scene, world = ready
    _say(session, scene, world, "Hello, Gate Guard.")
    npc = {"id": "gate_guard", "name": "Gate Guard", "label": "Gate Guard", "role": "guard", "appearance": "a wet cloak"}
    from game.expressive_dialogue import build_expression_contract
    contract = build_expression_contract(
        player_text="What do you know about the missing patrol?",
        speaker_name="Gate Guard",
        speaker_id="gate_guard",
        fallback_line="The notice board lists a warning about a missing patrol.",
        fallback_source="background.authorized_identity_or_public",
        forced_operation="bounded_social_line",
        extra_facts=["The notice board lists a warning about a missing patrol."],
    )
    prompt = build_expression_prompt(contract)
    blob = (prompt["system"] + prompt["user"]).casefold()
    assert "missing patrol" in blob
    assert "northwest" not in blob
    assert "payroll" not in blob
    assert len(blob) < 2500
    background_conversation(npc, session=session, scene=scene, player_text="Where is the hidden camp?")


REJECTS = [
    ("I will pay you gold for the secret.", False),
    ("I have not seen more than the notice.", True),
    ("The patrol was last seen on the northwest mud track.", False),
    ("I am not certain about that.", True),
]


@pytest.mark.parametrize("spoken,adopt", REJECTS, ids=["pay", "hedge", "route", "uncertain"])
def test_expression_boundary(spoken, adopt):
    verdict = validate_expression(spoken, {
        "operation": "bounded_social_line",
        "authorized_propositions": ["The notice board lists a warning about a missing patrol."],
        "fallback_response": "I do not know about that.",
        "knowledge_posture": "unknown",
        "speaker_name": "Gate Guard",
        "entity_identities": [],
    })
    assert verdict["adopt"] is adopt


def test_unambiguous_followup_does_not_ask_the_provider_to_pick_a_person(ready, monkeypatch):
    session, scene, world = ready
    _say(session, scene, world, "Hello, Gate Guard.")
    monkeypatch.setattr(
        "game.live_chat_interpretation.production_live_interpretation_enabled",
        lambda: True,
    )
    from game.conversational_orchestration import deterministic_conversational_decision
    called = {"n": 0}

    def refuse(_contract):
        called["n"] += 1
        raise AssertionError("obvious follow-up must not call the provider")

    monkeypatch.setattr("game.expressive_dialogue.request_expression", refuse)
    decision = deterministic_conversational_decision(
        player_text="Who are you?", scene=scene, world=world, session=session, log=[],
    )
    assert decision is not None
    assert decision.category.name != "CLARIFY"
    assert "which person" not in (decision.player_facing_text or "").casefold()
    assert called["n"] == 0
    assert session[LEDGER_KEY]["npc_focus"] == "gate_guard"


CLARIFY = [
    ("Ask them.", "clarify"),
    ("Look over there.", "clarify"),
    ("Move that.", "clarify"),
]


@pytest.mark.parametrize("text,outcome", CLARIFY, ids=["ask", "look", "move"])
def test_genuine_ambiguity_still_clarifies(ready, text, outcome):
    session, scene, world = ready
    proposal = classify(text, scene=scene, world=world, session=session)
    assert proposal["outcome"] == outcome


def test_recent_exchange_is_bounded(ready):
    session, scene, world = ready
    _say(session, scene, world, "Hello, Gate Guard.")
    for _ in range(8):
        _say(session, scene, world, "Who are you?")
    recent = session["conversational_context"]["recent_exchange"]
    assert len(recent) <= 6
    assert all(item["npc_id"] == "gate_guard" for item in recent)
