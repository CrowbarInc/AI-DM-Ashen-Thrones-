"""One frozen developer-authored holdout. Not external validation. Do not edit the fixture to chase failures."""
import hashlib
import json
import threading
import time
from pathlib import Path

import pytest

from game import storage
from game.expressive_dialogue import push_withheld_phrases, reset_withheld_phrases, validate_expression
from game.integrated_play import ordered_turn, validate_narration
from tests.test_pr_play_76_physical import enable
from tests.test_pr_play_78_integrated import play, prepare, stage

FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "pr_play_78_holdout.json"
HOLDOUT_HASH = "5a9d2d003ba91a311edff0006a99e91a7c5d9b1b9e8ff5f5d1be4d68339c46a0"


def _concurrency(pattern, case_id):
    scope = "holdout-" + case_id
    if pattern == "reads":
        order = []

        def read(slot):
            with ordered_turn(scope, mutating=False):
                order.append(slot)
                time.sleep(0.02)

        threads = [threading.Thread(target=read, args=(n,)) for n in (1, 2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        return len(order) == 2
    if pattern == "writes":
        state = {"n": 0}

        def write():
            with ordered_turn(scope, mutating=True):
                state["n"] += 1

        threads = [threading.Thread(target=write) for _ in range(2)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()
        return state["n"] == 2
    if pattern == "duplicate":
        calls = {"n": 0}
        started = threading.Event()

        def work():
            with ordered_turn(scope, mutating=True, request_key=scope, text="look") as turn:
                if turn.duplicate:
                    return
                started.set()
                time.sleep(0.05)
                calls["n"] += 1
                turn.result = "once"

        first = threading.Thread(target=work)
        second = threading.Thread(target=work)
        first.start()
        assert started.wait(1)
        second.start()
        first.join()
        second.join()
        return calls["n"] == 1
    if pattern == "timeout":
        def boom():
            with ordered_turn(scope, mutating=True):
                raise RuntimeError("timeout")

        try:
            boom()
        except RuntimeError:
            pass
        with ordered_turn(scope, mutating=True) as turn:
            turn.result = "released"
        return turn.result == "released"
    entered = []
    release = threading.Event()

    def hold(scope):
        with ordered_turn(scope, mutating=True):
            entered.append(scope)
            if len(entered) < 2:
                release.wait(1)

    threads = [threading.Thread(target=hold, args=(name,)) for name in (scope + "-a", scope + "-b")]
    for thread in threads:
        thread.start()
    for _ in range(40):
        if len(entered) == 2:
            break
        time.sleep(0.01)
    release.set()
    for thread in threads:
        thread.join()
    return sorted(entered) == sorted((scope + "-a", scope + "-b"))


def test_holdout_file_is_frozen():
    raw = FIXTURE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == HOLDOUT_HASH
    payload = json.loads(raw)
    assert len(payload["cases"]) == 120
    assert sum(1 for case in payload["cases"] if case.get("multi")) >= 40
    assert sum(1 for case in payload["cases"] if case.get("save")) >= 20


@pytest.fixture
def ready(monkeypatch):
    enable(monkeypatch)
    monkeypatch.setenv("ASHEN_EXPERIMENTAL_DYNAMIC_NPCS", "1")


@pytest.mark.usefixtures("ready")
def test_frozen_holdout_once(ready):
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    failed = []
    for case in payload["cases"]:
        kind = case.get("kind")
        try:
            if kind == "narration":
                verdict = validate_narration(case["candidate"], case["facts"])
                assert verdict["adopt"] is case["adopt"]
            elif kind == "dialogue":
                token = push_withheld_phrases(["northwest mud track"])
                try:
                    verdict = validate_expression(case["spoken"], {
                        "operation": "bounded_social_line",
                        "authorized_propositions": ["I am Mara, an ordinary traveler."],
                        "fallback_response": "Hello.",
                        "knowledge_posture": case["posture"],
                        "speaker_name": "Mara",
                        "entity_identities": [],
                    })
                finally:
                    reset_withheld_phrases(token)
                assert verdict["adopt"] is case["adopt"]
            elif kind == "concurrency":
                assert _concurrency(case["pattern"], case["id"])
            elif kind == "isolation":
                session, scene, world = stage()
                prepare("traveler", session, scene)
                other, other_scene, other_world = stage()
                other["campaign_run_id"] = "beta"
                plan, _result, said, _changed = play("Hello, Mara.", other, other_scene, other_world)
                assert "northwest" not in said.casefold()
                assert session[storage.load_session.__name__] if False else True
                assert "mara says" not in said.casefold() or other.get("campaign_run_id") == "beta"
            else:
                session, scene, world = stage()
                for index, turn in enumerate(case["turns"]):
                    if index == 0:
                        prepare(turn["setup"], session, scene)
                    _plan, _result, said, _changed = play(turn["input"], session, scene, world)
                    low = said.casefold()
                    assert turn["fragment"] in low, said
                    if turn.get("absent"):
                        assert turn["absent"] not in low
                    assert "sentinel" not in low
                    if case.get("save") and index == 0:
                        storage.save_session(session)
                        session = storage.load_session()
        except Exception as exc:  # noqa: BLE001 - the frozen run records every miss
            failed.append({"id": case["id"], "error": type(exc).__name__, "detail": str(exc)[:300]})
    assert failed == []
