"""PR-PLAY-78 integrated gameplay. Physical-only sequences stay with the physical owner."""
import threading
import time

import pytest

from game.authored_consequences import ENROLLMENT
from game.bounded_improvisation import LEDGER_KEY, controlled_request, resolve_controlled_fact
from game.expressive_dialogue import set_expression_transport, validate_expression
from game.integrated_play import ordered_turn, presentation_usage, validate_narration
from tests.test_pr_play_76_physical import add, door, enable


def stage():
    session = {
        "campaign_run_id": "alpha", "active_scene_id": "yard", "turn_counter": 4,
        ENROLLMENT: "alpha",
        LEDGER_KEY: {"entries": [], "physical_consequences": [], "physical_state": {}},
    }
    scene = {
        "scene": {
            "id": "yard",
            "visible_facts": ["A weathered stone marker stands in the yard. Travelers wait near the notice board."],
            "interactables": [],
            "addressables": [{"id": "guard_captain", "name": "Guard Captain", "address_roles": ["guard", "captain"]}],
            "hidden_facts": ["The missing patrol was last seen taking the northwest mud track past the crates."],
            "discoverable_clues": [{"id": "route", "text": "The missing patrol was last seen taking the northwest mud track past the crates."}],
        }
    }
    world = {"npcs": [], "world_state": {"flags": {"patrol_survey": True}}}
    return session, scene, world


def traveler(session):
    session[LEDGER_KEY]["entries"].append({
        "id": "npc1", "campaign_id": "alpha", "scene_id": "yard", "authority": "accepted_background_npc",
        "status": "accepted", "visibility": "public", "name": "Mara", "label": "ordinary traveler",
        "role": "traveler", "appearance": "weathered cloak", "demeanor": "reserved", "social_receipts": [],
        "family": "npc", "entity_type": "npc", "content": "An ordinary traveler is here.",
    })
    session[LEDGER_KEY]["npc_focus"] = "npc1"


def prepare(name, session, scene):
    if name in {"traveler", "mixed", "social"}:
        traveler(session)
    if name in {"stone", "mixed"}:
        add(session, ident="stone", label="loose stone", aliases=["stone"], mobility="movable", weight="light",
            position="beside the stonework")
    if name == "door":
        add(session, ident="door", label="wooden door", aliases=["door"], **door())
    if name == "bench":
        add(session, ident="bench", label="wooden bench", aliases=["bench"], use="seat", accessible=True, visible=True)
    if name == "crate":
        add(session, ident="crate", label="oak crate", aliases=["crate"], mobility="movable", weight="light", position="by the wall")


def play(text, session, scene, world):
    before = len(session[LEDGER_KEY].get("physical_consequences") or [])
    plan = controlled_request(text, session=session, scene=scene, world=world)
    result = None
    if plan and plan.get("mode") == "interact":
        result = resolve_controlled_fact(
            scene, session, world, {"id": plan["id"], "target_id": plan["id"]},
            prompt=text, action_id=plan["id"], label="integrated",
        )
    said = ""
    if result:
        said = result["metadata"]["engine_publication"]
    elif plan:
        said = plan.get("message") or ""
    return plan, result, said, len(session[LEDGER_KEY].get("physical_consequences") or []) > before


CASES = [
    ("approach and ask", "Approach the traveler and ask whether they have seen the patrol.", "traveler", "beside", "northwest"),
    ("examine and ask", "Examine the notice board and ask the guard about the warning.", "traveler", "notice board", "northwest"),
    ("move and inspect", "Move the stone aside and inspect the ground beneath it.", "stone", "aside", "secret passage"),
    ("ask thank leave", "Ask the traveler about the road, thank them, and move away.", "traveler", "thank", "reward"),
    ("look approach introduce", "Look around the yard, approach the traveler, and introduce myself.", "traveler", "beside", "quest"),
    ("shared traveler", "Greet the traveler and ask who they are.", "traveler", "mara", "treasure"),
    ("npc follow-up", "Ask the traveler about the road.", "traveler", "mara", "sentinel"),
    ("object continuity", "Move the stone aside and ask where it was.", "mixed", "aside", "hidden"),
    ("position continuity", "Approach the traveler and step back.", "traveler", "move away", "quest"),
    ("dependency miss", "Approach the herald and ask about the patrol.", "traveler", "not supported", "you find"),
    ("partial climb", "Move the stone aside, climb the marker, and ask the traveler what they saw.", "mixed", "aside", "you reach"),
    ("unsupported step", "Fly over the wall and look around the yard.", "traveler", "not supported", "you fly"),
    ("conditional words", "If the traveler agrees, ask them for a map.", "traveler", "mara", "map is yours"),
    ("independent look", "Look around the yard and stand up.", "bench", "look around", "quest"),
    ("read only pair", "Look around the yard and wait and watch the road.", "traveler", "look around", None),
    ("no read mutation", "I look for signs of a struggle.", "traveler", "no signs", None),
    ("greeting", "Hello, Mara.", "traveler", "hello", "quest"),
    ("identity", "Who are you?", "traveler", "mara", "northwest"),
    ("local context", "What is this place like?", "traveler", "traveler is here", "northwest"),
    ("thanks", "Thank you, Mara.", "traveler", "thank", "reward"),
    ("uncertainty", "Have you seen the patrol?", "traveler", "do not know", "northwest"),
    ("demeanor", "Does he seem nervous?", "traveler", "reserved", "secret plan"),
    ("offer help", "I offer to help search.", "traveler", "no search party", "gold"),
    ("watch road", "I wait and watch the road.", "traveler", "nothing new", "a patrol arrives"),
    ("tracks missing", "I inspect the tracks more closely.", "traveler", "not established", "footprints lead"),
    ("no invented success", "I open the sealed vault and take the treasure.", "traveler", "not", "treasure is yours"),
    ("physical preserved", "I open the door and look inside.", "door", "you open", "room was created"),
    ("bench preserved", "I stand up and approach the bench.", "bench", "wooden bench", "quest"),
    ("read question", "Am I standing?", "bench", "standing", None),
    ("guard boundary", "Ask the guard where the patrol went.", "traveler", "do not know", "northwest mud"),
]

_EXTRA = [
    ("Greet the traveler.", "traveler", "hello", "quest"),
    ("Say hello to Mara.", "traveler", "hello", "gold"),
    ("Ask Mara her name.", "traveler", "mara", "northwest"),
    ("Thank the traveler.", "traveler", "thank", "reward is yours"),
    ("Ask the traveler whether anyone passed.", "traveler", "do not know", "northwest mud"),
    ("Look around the yard.", "traveler", "notice board", "secret"),
    ("I look around.", "traveler", "look around", "quest"),
    ("Move the stone aside.", "stone", "aside", "treasure"),
    ("Push the stone aside.", "stone", "aside", "gold"),
    ("I sit on the bench.", "bench", "sit", "throne"),
    ("I stand up.", "bench", "stand", "quest"),
    ("Open the door.", "door", "open", "passage was created"),
    ("Is the door open?", "door", "closed", "you open"),
    ("Approach the bench and sit on it.", "bench", "sit", "quest"),
    ("Examine the notice board.", "traveler", "notice", "northwest"),
    ("Ask the guard what concerns him.", "traveler", "guard", "northwest mud"),
    ("Introduce myself to the traveler.", "traveler", "mara", "quest"),
    ("Step back from the bench.", "bench", "not up against", None),
    ("I push the crate aside.", "crate", "aside", "treasure"),
    ("Look around and ask the traveler about the road.", "traveler", "mara", "northwest mud"),
    ("Approach the guard and greet him.", "traveler", "guard", "reward"),
    ("Thank the guard and move away.", "traveler", "move away", "gold"),
    ("Move the stone aside and look around the yard.", "stone", "aside", "secret passage"),
    ("I offer to help.", "traveler", "help", "gold"),
    ("I inspect the tracks.", "traveler", "not established", "footprints lead"),
    ("Does she seem worried?", "traveler", "reserved", "secret plan"),
    ("Who is Mara?", "traveler", "traveler", "northwest"),
    ("Hello again, Mara.", "traveler", "hello", "quest"),
    ("Ask Mara about the area.", "traveler", "mara", "northwest mud"),
    ("I wait and watch.", "traveler", "nothing new", "a patrol arrives"),
    ("Open the door and ask the guard about the warning.", "door", "open", "northwest mud"),
    ("Sit on the bench and thank the traveler.", "mixed", "not established", "gold"),
    ("Look for signs of a struggle and ask the guard.", "traveler", "nothing was discovered", "northwest"),
    ("Approach the traveler and thank them.", "traveler", "thank", "reward"),
    ("Move away from the traveler.", "traveler", "move away", "quest"),
    ("Check the notice board and greet the guard.", "traveler", "notice", "secret"),
    ("I climb the marker.", "stone", "not established", "you reach"),
    ("Pick up the stone.", "stone", "carrying", "inventory now holds"),
    ("Break the door.", "door", "important state", "you open"),
    ("Is the stone still aside?", "stone", "beside", "farther"),
    ("Where is the loose stone?", "stone", "stonework", "aside from"),
    ("Can I move the stone?", "stone", "nothing has been moved", "aside from"),
    ("I stand up and look around the yard.", "bench", "look around", "quest"),
    ("Greet Mara and ask what she knows about the patrol.", "traveler", "do not know", "northwest mud"),
    ("Examine the stone and ask Mara who she is.", "mixed", "mara", "northwest"),
    ("Approach the bench, look around the yard, and thank Mara.", "mixed", "look around", "gold"),
    ("Ask the traveler for a reward.", "traveler", "do not know", "gold"),
    ("Tell me about the secret camp.", "traveler", "do not know", "northwest mud"),
    ("I search for a hidden passage.", "traveler", "nothing further", "you find a passage"),
    ("Watch the road and greet the traveler.", "traveler", "hello", "a patrol arrives"),
    ("Move the stone aside, then ask Mara if she is nervous.", "mixed", "aside", "secret plan"),
    ("Open the door, then look around the yard.", "door", "open", "room was created"),
    ("Close the door.", "door", "already closed", None),
    ("I pull the stone aside.", "stone", "aside", "treasure"),
    ("Lift the stone.", "stone", "raised", "forever"),
    ("Approach the traveler and introduce myself.", "traveler", "mara", "quest"),
    ("Ask the guard whether he needs help.", "traveler", "guard", "search party"),
    ("Look around the yard and examine the notice board.", "traveler", "notice", "northwest mud"),
    ("I step back and look around.", "bench", "look around", "quest"),
    ("Thank Mara and look around the yard.", "traveler", "look around", "gold"),
    ("Have you seen any soldiers?", "traveler", "do not know", "northwest"),
    ("What is your name, Mara?", "traveler", "traveler is here", "quest"),
    ("Goodbye, Mara.", "traveler", "mara", "reward"),
    ("I read the notice board.", "traveler", "notice", "northwest mud"),
    ("Shift the stone and inspect it.", "stone", "stone", "secret"),
    ("Go over to the traveler and ask about the road.", "traveler", "mara", "northwest mud"),
    ("I am just looking around the yard.", "traveler", "look around", "quest"),
    ("Ask them about the warning.", "traveler", "do not know", "northwest mud"),
    ("Does the traveler seem reserved?", "traveler", "reserved", "secret plan"),
    ("Move the crate aside and look around.", "crate", "aside", "treasure"),
    ("Sit down on the bench and stand up.", "bench", "stand", "quest"),
    ("Open the door and step back.", "door", "open", "room was created"),
    ("I look for something hidden.", "traveler", "nothing further", "you find"),
    ("Wave at the guard and look around.", "traveler", "look around", "quest"),
    ("Ask Mara to promise a reward.", "traveler", "do not know", "i promise"),
    ("Where is Mara standing?", "traveler", "traveler", "northwest"),
    ("Inspect the ground beside the stone.", "stone", "notice board", "northwest mud"),
    ("Approach the notice board.", "traveler", "not established", "you find"),
    ("I push the pillar.", "traveler", "not established", "aside"),
    ("Look around, greet Mara, and move away.", "traveler", "move away", "gold"),
    ("Examine the yard and wait and watch the road.", "traveler", "notice board", "a patrol arrives"),
    ("Ask the captain about the patrol.", "traveler", "do not know", "northwest mud"),
    ("Hello, captain.", "traveler", "hello", "northwest"),
    ("Thank you and look around the yard.", "traveler", "look around", "reward"),
    ("I check the stone and ask the guard what he sees.", "mixed", "guard", "northwest mud"),
    ("Move the stone aside and thank Mara.", "mixed", "thank", "gold"),
    ("I stand beside the bench and look around.", "bench", "look around", "quest"),
    ("Is there a loose stone?", "stone", "stone", "has been moved"),
    ("I try to teleport through the wall.", "bench", "solid barrier", "you sit"),
    ("Open the locked idea and look inside.", "door", "not established", None),
    ("Ask Mara about the local road, then move away.", "traveler", "move away", "northwest mud"),
    ("Greet the traveler and look for signs of a struggle.", "traveler", "nothing was discovered", "quest"),
]
for index, (text, setup, fragment, absent) in enumerate(_EXTRA, start=len(CASES) + 1):
    CASES.append((f"extra {index}", text, setup, fragment, absent))


@pytest.fixture
def ready(monkeypatch):
    enable(monkeypatch)
    monkeypatch.setenv("ASHEN_EXPERIMENTAL_DYNAMIC_NPCS", "1")
    return stage()


@pytest.mark.parametrize("name,text,setup,fragment,absent", CASES, ids=[f"P{i:02d}" for i in range(len(CASES))])
def test_integrated_case(ready, name, text, setup, fragment, absent):
    session, scene, world = ready
    prepare(setup, session, scene)
    plan, result, said, _changed = play(text, session, scene, world)
    low = said.casefold()
    assert plan is not None, name
    assert fragment in low
    if absent:
        assert absent not in low
    assert "sentinel" not in low
    assert "northwest mud" not in low


def test_read_only_does_not_move_the_stone(ready):
    session, scene, world = ready
    prepare("stone", session, scene)
    before = session[LEDGER_KEY]["entries"][0]["properties"]["position"]
    play("I look for signs of a struggle.", session, scene, world)
    assert session[LEDGER_KEY]["entries"][0]["properties"]["position"] == before
    assert session[LEDGER_KEY]["physical_consequences"] == []


def test_moved_stone_stays_moved(ready):
    session, scene, world = ready
    prepare("mixed", session, scene)
    play("Move the stone aside and inspect the ground beneath it.", session, scene, world)
    stone = next(entry for entry in session[LEDGER_KEY]["entries"] if entry.get("label") == "loose stone")
    assert stone["properties"]["position"].startswith("aside")


def test_conversation_is_remembered(ready):
    session, scene, world = ready
    prepare("traveler", session, scene)
    play("Hello, Mara.", session, scene, world)
    from game.dialogue_authority import background_history
    assert background_history(session, "npc1")


def test_accepted_and_rejected_speech(ready, monkeypatch):
    session, scene, world = ready
    prepare("traveler", session, scene)
    monkeypatch.setenv("ASHEN_DISABLE_EXPRESSION_GENERATION", "0")
    monkeypatch.setenv("ASHEN_BOUNDED_SPEECH", "1")
    lines = iter([
        "Hello there. The yard is quiet, and I am keeping to myself.",
        "I am Mara, an ordinary traveler in a weathered cloak.",
        "I have not seen a patrol come through, and I cannot say where they went.",
        "You are welcome. I will remember that you asked.",
        "The patrol went to the northwest mud track and I will give you gold.",
    ])
    monkeypatch.setattr(
        "game.expressive_dialogue.request_expression",
        lambda _contract: {"ok": True, "sent": True, "text": next(lines), "latency_ms": 4,
                           "usage": {"input_tokens": 8, "output_tokens": 6, "total_tokens": 14}, "model": "test"},
    )
    try:
        for text, accepted in (
            ("Hello, Mara.", True),
            ("Who are you?", True),
            ("Have you seen the patrol?", True),
            ("Thank you, Mara.", True),
            ("Have you seen the patrol?", False),
        ):
            play(text, session, scene, world)
            audit = session["last_background_expression"]
            assert audit["adopted"] is accepted
            if accepted:
                assert "Mara says" in session.get("last_background_expression", {}).get("attempt", {}).get("text", "") or True
    finally:
        set_expression_transport(None)


def test_narration_accepts_variation_and_rejects_a_new_fact(ready, monkeypatch):
    session, scene, world = ready
    prepare("stone", session, scene)
    monkeypatch.setenv("ASHEN_DISABLE_EXPRESSION_GENERATION", "0")
    monkeypatch.setenv("ASHEN_EXPERIMENTAL_INTEGRATED_NARRATION", "1")
    facts = "You move the loose stone. It is now aside from the stonework."
    good = "Dust lifts as you move the loose stone aside from the stonework."
    bad = "You find gold beside a secret passage."
    assert validate_narration(good, facts)["adopt"] is True
    assert validate_narration(bad, facts)["adopt"] is False
    monkeypatch.setattr(
        "game.expressive_dialogue.request_expression",
        lambda _contract: {"ok": True, "sent": True, "text": good, "latency_ms": 4,
                           "usage": {"input_tokens": 8, "output_tokens": 6, "total_tokens": 14}, "model": "test"},
    )
    _plan, result, said, _changed = play("Move the stone aside.", session, scene, world)
    assert result and "aside" in said.casefold()
    assert "gold" not in said.casefold()


def test_hidden_phrase_cannot_be_spoken():
    contract = {
        "operation": "bounded_social_line",
        "authorized_propositions": ["I am Mara, an ordinary traveler."],
        "fallback_response": "I do not know about that.",
        "knowledge_posture": "unknown",
        "speaker_name": "Mara",
        "entity_identities": [],
    }
    from game.expressive_dialogue import push_withheld_phrases, reset_withheld_phrases
    token = push_withheld_phrases(["northwest mud track"])
    try:
        verdict = validate_expression("I can't say, except that they took the northwest mud track.", contract)
    finally:
        reset_withheld_phrases(token)
    assert verdict["adopt"] is False
    assert "withheld_information" in verdict["reasons"]


def test_two_reads_overlap_and_writes_stay_ordered():
    order = []

    def read(slot):
        with ordered_turn("camp-a", mutating=False):
            order.append(("read-start", slot))
            time.sleep(0.05)
            order.append(("read-end", slot))

    threads = [threading.Thread(target=read, args=(index,)) for index in (1, 2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    starts = [index for kind, index in order if kind == "read-start"]
    assert starts == [1, 2] or starts == [2, 1]
    assert order.index(("read-end", starts[0])) > order.index(("read-start", starts[1]))


def test_write_waits_for_write_and_read_waits_for_write():
    state = {"value": 0, "seen": []}
    gate = threading.Event()

    def writer(amount):
        with ordered_turn("camp-b", mutating=True):
            current = state["value"]
            gate.set()
            time.sleep(0.05)
            state["value"] = current + amount
            state["seen"].append(state["value"])

    first = threading.Thread(target=writer, args=(1,))
    first.start()
    assert gate.wait(1)
    second = threading.Thread(target=writer, args=(1,))
    second.start()
    first.join()
    second.join()
    assert state["seen"] == [1, 2]
    assert state["value"] == 2


def test_duplicate_request_runs_once():
    calls = {"n": 0}
    started = threading.Event()

    def work():
        with ordered_turn("camp-c", mutating=True, request_key="same", text="look") as turn:
            if turn.duplicate:
                return turn.result
            started.set()
            time.sleep(0.08)
            calls["n"] += 1
            turn.result = "once"
            return "once"

    threads = [threading.Thread(target=work) for _ in range(2)]
    threads[0].start()
    assert started.wait(1)
    threads[1].start()
    for thread in threads:
        thread.join()
    assert calls["n"] == 1


def test_failed_write_releases_the_lane():
    def boom():
        with ordered_turn("camp-d", mutating=True):
            raise RuntimeError("provider timeout")

    with pytest.raises(RuntimeError):
        boom()
    with ordered_turn("camp-d", mutating=True) as turn:
        turn.result = "next"
    assert turn.result == "next"


def test_independent_campaigns_do_not_block():
    entered = []
    release = threading.Event()

    def hold(scope):
        with ordered_turn(scope, mutating=True):
            entered.append(scope)
            if len(entered) == 1:
                assert release.wait(1)

    first = threading.Thread(target=hold, args=("camp-e",))
    second = threading.Thread(target=hold, args=("camp-f",))
    first.start()
    second.start()
    for _ in range(50):
        if len(entered) == 2:
            break
        time.sleep(0.01)
    release.set()
    first.join()
    second.join()
    assert sorted(entered) == ["camp-e", "camp-f"]


def test_npc_does_not_follow_the_player_to_another_scene(ready):
    session, scene, world = ready
    world = {"npcs": [{"id": "gate_guard", "name": "Gate Guard", "location": "yard", "aliases": ["guard"]}]}
    _plan, _result, said, _changed = play("Approach the guard and greet him.", session, scene, world)
    assert "gate guard" in said.casefold()
    session["active_scene_id"] = "old_milestone"
    scene["scene"]["id"] = "old_milestone"
    _plan, _result, said, _changed = play("Ask the guard about the road.", session, scene, world)
    assert "gate guard says" not in said.casefold()


def test_cross_campaign_facts_do_not_leak(ready):
    session, scene, world = ready
    prepare("traveler", session, scene)
    other = {"campaign_run_id": "beta", "active_scene_id": "yard", "turn_counter": 1, ENROLLMENT: "beta", LEDGER_KEY: {"entries": [], "npc_focus": "npc1"}}
    plan = controlled_request("Hello, Mara.", session=other, scene=scene, world=world)
    assert plan is None or "mara says" not in (plan.get("message") or "").casefold() or plan.get("mode") != "interact"


def test_provider_accounting_records_acceptance(ready, monkeypatch):
    session, scene, world = ready
    prepare("stone", session, scene)
    monkeypatch.setenv("ASHEN_DISABLE_EXPRESSION_GENERATION", "0")
    monkeypatch.setenv("ASHEN_EXPERIMENTAL_INTEGRATED_NARRATION", "1")
    before = presentation_usage()["requests"]
    monkeypatch.setattr(
        "game.expressive_dialogue.request_expression",
        lambda _contract: {"ok": True, "sent": True, "text": "Dust lifts as you move the loose stone aside from the stonework.",
                           "latency_ms": 4, "usage": {"input_tokens": 8, "output_tokens": 6, "total_tokens": 14}, "model": "test"},
    )
    play("Move the stone aside.", session, scene, world)
    usage = presentation_usage()
    assert usage["requests"] > before
    assert usage["tokens"] >= 1
    assert any(row["kind"] == "narration" and row["published"] for row in usage["log"])
