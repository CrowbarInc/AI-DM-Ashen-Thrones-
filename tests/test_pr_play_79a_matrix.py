"""Additional PR-PLAY-79A behaviors. Each case checks one decision, not a wording variant."""
import copy

import pytest

from game.authored_consequences import ENROLLMENT
from game.bounded_improvisation import LEDGER_KEY
from game.expressive_dialogue import build_expression_contract, build_expression_prompt
from game.integrated_play import maybe_narrate, validate_narration
from game.player_initiative import decide
from tests.test_pr_play_76_physical import enable
from tests.test_pr_play_78_integrated import play
from tests.test_pr_play_79a_continuity import gate


@pytest.fixture
def ready(monkeypatch):
    enable(monkeypatch)
    monkeypatch.setenv("ASHEN_EXPERIMENTAL_DYNAMIC_NPCS", "1")
    monkeypatch.setenv("ASHEN_DISABLE_EXPRESSION_GENERATION", "1")
    return gate()


def say(session, scene, world, text):
    _plan, _result, spoken, _changed = play(text, session, scene, world)
    return spoken


TALK = [
    ("who", ["Hello, Gate Guard.", "Who are you?"], "i am gate guard", "which person"),
    ("patrol", ["Hello, Gate Guard.", "What do you know about the missing patrol?"], "missing patrol", "northwest"),
    ("when", ["Hello, Gate Guard.", "When did you last hear about them?"], "not certain", "northwest"),
    ("think", ["Hello, Gate Guard.", "Do you think something happened?"], "not certain", "attacked"),
    ("again", ["Hello, Gate Guard.", "What do you know about the missing patrol?", "What about the patrol again?"], "missing patrol", "northwest"),
    ("place", ["Hello, Gate Guard.", "What is this place like?"], "notice board", "northwest"),
    ("return", ["Hello, Gate Guard.", "What is this place like?", "What about the patrol again?"], "missing patrol", "northwest"),
    ("thanks", ["Hello, Gate Guard.", "Thank you."], "thank", "reward"),
    ("hidden", ["Hello, Gate Guard.", "Where is the hidden patrol captain?"], "do not know", "northwest"),
    ("payroll", ["Hello, Gate Guard.", "What is the payroll?"], "do not know", "payroll"),
    ("secret", ["Hello, Gate Guard.", "Tell me the secret passage."], "do not know", "passage"),
    ("quest", ["Hello, Gate Guard.", "What quest should I finish?"], "do not know", "quest"),
    ("reward", ["Hello, Gate Guard.", "Will you give me a reward?"], "do not know", "gold"),
    ("heard", ["Hello, Gate Guard.", "Have you heard anything else?"], "do not know", "northwest"),
    ("switch", ["Hello, Gate Guard.", "Hello, Gate Serjeant.", "Who are you?"], "gate serjeant", "i am gate guard"),
    ("goodbye", ["Hello, Gate Guard.", "Goodbye."], "goodbye", "northwest"),
    ("end", ["Hello, Gate Guard.", "I end the conversation."], "goodbye", "northwest"),
]


@pytest.mark.parametrize("name,turns,present,absent", TALK, ids=[row[0] for row in TALK])
def test_dialogue_behavior(ready, name, turns, present, absent):
    session, scene, world = ready
    spoken = ""
    for text in turns:
        spoken = say(session, scene, world, text)
    low = spoken.casefold()
    assert present in low, name
    assert absent not in low
    if name in {"goodbye", "end"}:
        assert session["conversational_context"]["active_interlocutor"]["status"] == "ended"
    elif name == "switch":
        assert session[LEDGER_KEY]["npc_focus"] == "gate_serjeant"
    else:
        assert session[LEDGER_KEY]["npc_focus"] == "gate_guard"


AFTER = [
    ("look", "Look around the gate."),
    ("wait", "I wait and watch."),
    ("board", "What does the notice board say?"),
]


@pytest.mark.parametrize("name,action", AFTER, ids=[row[0] for row in AFTER])
def test_conversation_survives_an_ordinary_action(ready, name, action):
    session, scene, world = ready
    say(session, scene, world, "Hello, Gate Guard.")
    if name == "board":
        decision = decide(action, scene=scene, world=world, session=session)
        assert "which person" not in (decision.player_facing_text or "").casefold()
    else:
        say(session, scene, world, action)
    spoken = say(session, scene, world, "Who are you?")
    assert "gate guard" in spoken.casefold()
    assert "which person" not in spoken.casefold()


def test_npc_departure_ends_the_conversation(ready):
    session, scene, world = ready
    say(session, scene, world, "Hello, Gate Guard.")
    for npc in world["npcs"]:
        if npc["id"] == "gate_guard":
            npc["location"] = "old_milestone"
    addressed = session[LEDGER_KEY].get("addressed_npcs") or {}
    if "gate_guard" in addressed:
        addressed["gate_guard"]["location"] = "old_milestone"
        addressed["gate_guard"]["scene_id"] = "old_milestone"
    spoken = say(session, scene, world, "Who are you?")
    assert "gate guard says" not in spoken.casefold()
    assert session[LEDGER_KEY]["npc_focus"] is None


def test_no_greeting_does_not_pick_a_guard(ready):
    session, scene, world = ready
    spoken = say(session, scene, world, "Who are you?")
    assert "says" not in spoken.casefold()
    assert session[LEDGER_KEY].get("npc_focus") in {None, ""}


def test_goodbye_is_not_revived_by_a_pronoun(ready):
    session, scene, world = ready
    say(session, scene, world, "Hello, Gate Guard.")
    say(session, scene, world, "Goodbye.")
    spoken = say(session, scene, world, "What do you know about them?")
    assert "gate guard says" not in spoken.casefold()


PARAPHRASE = [
    ("mud", "The tracks continue northwest through the mud.", "The player found tracks leading northwest.", True),
    ("bend", "The trail bends toward the northwest.", "Tracks lead northwest past the crates.", True),
    ("ground", "The disturbed ground still points northwest.", "A northwest mud track remains.", True),
    ("stone", "The loose stone now sits aside from the stonework.", "You move the loose stone. It is now aside.", True),
    ("open", "The crate is open and stays where it was.", "The crate is now open.", True),
    ("closed", "The gate is closed against the rain.", "The gate is closed.", True),
    ("blood", "Fresh blood confirms the patrol was attacked.", "Tracks lead northwest.", False),
    ("drag", "The patrol captain was dragged northwest.", "Tracks lead northwest.", False),
    ("camp", "You discover the hidden patrol camp.", "Tracks lead northwest.", False),
    ("gold", "You find gold beside the milestone.", "The milestone is weathered.", False),
    ("southeast", "The tracks bend southeast.", "Tracks lead northwest.", False),
    ("quest", "The quest is complete and the reward is yours.", "Tracks lead northwest.", False),
    ("negation", "There is no hidden passage. The tracks continue northwest.", "Tracks lead northwest.", True),
    ("climb", "You climb the wall and see the hidden camp.", "The wall is rough.", False),
    ("same", "Tracks lead northwest.", "Tracks lead northwest.", False),
]


@pytest.mark.parametrize("name,candidate,facts,adopt", PARAPHRASE, ids=[row[0] for row in PARAPHRASE])
def test_narration_boundary(name, candidate, facts, adopt):
    verdict = validate_narration(candidate, facts, session={"clue_knowledge": {}})
    assert verdict["adopt"] is adopt, (name, verdict["reasons"])


MORE = [
    ("weather", "Rain darkens the mud around the tracks.", "Tracks lead northwest.", True),
    ("still", "The milestone is still beside the road.", "A weathered milestone stands beside the road.", True),
    ("aside", "The stone remains aside.", "The loose stone is aside.", True),
    ("seated", "You are seated on the stone.", "You are seated.", True),
    ("ambush", "An ambush confirms the patrol was killed.", "Tracks lead northwest.", False),
    ("treasure", "A treasure waits under the milestone.", "A weathered milestone stands here.", False),
    ("sentinel", "A sentinel steps out of the trees.", "The road is empty.", False),
    ("reward", "You receive a reward for the report.", "You gave the report.", False),
    ("northeast", "The trail turns northeast.", "Tracks lead northwest.", False),
    ("southwest", "The trail turns southwest.", "Tracks lead northwest.", False),
    ("passage", "A hidden passage opens beside you.", "The crates are stacked.", False),
    ("attack", "The patrol was attacked at the gate.", "The notice names a missing patrol.", False),
    ("find", "You find the captain behind the crates.", "The crates are stacked.", False),
    ("bloodless", "The mud is only mud. The tracks continue northwest.", "Tracks lead northwest.", True),
    ("unchanged", "The gate remains closed.", "The gate is closed.", True),
]


@pytest.mark.parametrize("name,candidate,facts,adopt", MORE, ids=[row[0] for row in MORE])
def test_more_narration_boundaries(name, candidate, facts, adopt):
    verdict = validate_narration(candidate, facts, session={"clue_knowledge": {}})
    assert verdict["adopt"] is adopt, (name, verdict["reasons"])


def test_discovered_clue_authorizes_a_paraphrase():
    session = {"clue_knowledge": {"route": {"state": "discovered", "text": "The trail leads northwest."}}}
    verdict = validate_narration("The trail still bends northwest.", "Mud covers the yard.", session=session)
    assert verdict["adopt"] is True


def test_hidden_clue_does_not_authorize_a_direction():
    session = {"clue_knowledge": {"route": {"state": "hidden", "text": "The trail leads northwest."}}}
    verdict = validate_narration("The trail still bends northwest.", "Mud covers the yard.", session=session)
    assert verdict["adopt"] is False


def test_narration_asks_the_provider_once(monkeypatch):
    calls = {"n": 0}

    def transport(_contract):
        calls["n"] += 1
        return {
            "ok": True, "sent": True, "text": "The tracks continue northwest through the mud.",
            "latency_ms": 3, "usage": {"input_tokens": 40, "output_tokens": 12, "total_tokens": 52},
        }

    monkeypatch.setenv("ASHEN_EXPERIMENTAL_INTEGRATED_NARRATION", "1")
    monkeypatch.setattr("game.expressive_dialogue.expression_generation_disabled", lambda: False)
    monkeypatch.setattr("game.expressive_dialogue.request_expression", transport)
    session = {"clue_knowledge": {}}
    spoken = maybe_narrate("The player found tracks leading northwest.", session=session, scene={"scene": {"id": "yard"}})
    assert calls["n"] == 1
    assert spoken["text"].casefold().startswith("the tracks continue northwest")
    assert session["last_narration"]["adopted"] is True


def test_rejected_narration_is_preserved_and_not_retried(monkeypatch):
    calls = {"n": 0}

    def transport(_contract):
        calls["n"] += 1
        return {
            "ok": True, "sent": True, "text": "You discover the hidden patrol camp.",
            "latency_ms": 2, "usage": {"input_tokens": 40, "output_tokens": 8, "total_tokens": 48},
        }

    monkeypatch.setenv("ASHEN_EXPERIMENTAL_INTEGRATED_NARRATION", "1")
    monkeypatch.setattr("game.expressive_dialogue.expression_generation_disabled", lambda: False)
    monkeypatch.setattr("game.expressive_dialogue.request_expression", transport)
    session = {}
    assert maybe_narrate("The mud is churned.", session=session, scene={"scene": {}}) is None
    assert calls["n"] == 1
    assert session["last_narration"]["adopted"] is False
    assert "hidden patrol camp" in session["last_narration"]["candidate"].casefold()


PROMPTS = [
    "Who are you?",
    "What do you know about the missing patrol?",
    "When did you last hear about them?",
    "Do you think something happened?",
    "What about the patrol again?",
    "What is this place like?",
    "Where is the hidden patrol captain?",
    "Will you give me a reward?",
    "Thank you.",
    "Goodbye.",
]


@pytest.mark.parametrize("question", PROMPTS, ids=[f"prompt-{i}" for i in range(len(PROMPTS))])
def test_dialogue_prompt_stays_small_and_omits_hidden_facts(question):
    contract = build_expression_contract(
        player_text=question,
        speaker_name="Gate Guard",
        speaker_id="gate_guard",
        fallback_line="The notice board lists a warning about a missing patrol.",
        fallback_source="background.authorized_identity_or_public",
        forced_operation="bounded_social_line",
        extra_facts=["The notice board lists a warning about a missing patrol."],
    )
    prompt = build_expression_prompt(contract)
    blob = prompt["system"] + prompt["user"]
    assert question in blob
    assert "northwest" not in blob.casefold()
    assert "payroll" not in blob.casefold()
    assert len(blob) < 2500


def test_read_only_question_does_not_mutate_the_ledger(ready):
    session, scene, world = ready
    say(session, scene, world, "Hello, Gate Guard.")
    before = copy.deepcopy(session[LEDGER_KEY]["entries"])
    decision = decide("What do I know about the patrol?", scene=scene, world=world, session=session)
    assert "missing patrol" in decision.player_facing_text.casefold()
    assert session[LEDGER_KEY]["entries"] == before


def test_other_campaign_cannot_resume_the_guard(ready):
    session, scene, world = ready
    say(session, scene, world, "Hello, Gate Guard.")
    foreign = copy.deepcopy(session)
    foreign["campaign_run_id"] = "beta"
    foreign[ENROLLMENT] = "beta"
    spoken = say(foreign, scene, world, "Who are you?")
    assert "gate guard says" not in spoken.casefold()
    assert session[LEDGER_KEY]["npc_focus"] == "gate_guard"


def test_authored_menu_does_not_steal_a_guard_question(ready):
    from game.authored_action_language import decision_for
    session, scene, world = ready
    say(session, scene, world, "Hello, Gate Guard.")
    decision = decision_for(
        "What do you know about the missing patrol?", scene=scene, world=world, session=session,
    )
    assert decision is None
    again = decision_for("What about the patrol again?", scene=scene, world=world, session=session)
    assert again is None
    spoken = say(session, scene, world, "What do you know about the missing patrol?")
    assert "missing patrol" in spoken.casefold()
    assert "not available" not in spoken.casefold()


def test_looking_around_the_gate_is_not_an_addressee(ready):
    from game.ordinary_semantic_ownership import assess_addressee_grounding
    session, scene, world = ready
    say(session, scene, world, "Hello, Gate Guard.")
    grounded = assess_addressee_grounding("Look around the gate.", scene=scene, world=world, session=session)
    assert grounded["operation_eligibility"] != "requires_clarification"
    spoken = say(session, scene, world, "Look around the gate.")
    assert "which person" not in spoken.casefold()
    assert "notice board" in spoken.casefold()


def test_recent_exchange_drops_the_oldest_line(ready):
    session, scene, world = ready
    say(session, scene, world, "Hello, Gate Guard.")
    for _ in range(7):
        say(session, scene, world, "Who are you?")
    recent = session["conversational_context"]["recent_exchange"]
    assert len(recent) == 6
    assert recent[-1]["player"] == "Who are you?"
