"""One frozen developer-authored holdout for PR-PLAY-79B. Not external validation.

The fixture is hashed below and is not edited after a failure.
"""
import copy
import hashlib
import json
from pathlib import Path

import pytest

from game.authored_action_language import decision_for
from game.bounded_improvisation import LEDGER_KEY
from game.integrated_play import validate_narration
from game.publication_contract import narration_skip, summarize_provider_rows
from tests.test_pr_play_76_physical import enable
from tests.test_pr_play_78_integrated import play
from tests.test_pr_play_79a_continuity import gate

FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "fixtures" / "pr_play_79b_holdout.json"
HOLDOUT_HASH = "1fb2ad2a59fa7342a4f723403efa363332206dfbb295152e5a0784ad4be4fee6"
RESULTS = Path(__file__).resolve().parents[1] / "artifacts" / "pr_play_79b" / "holdout_results.json"


def _say(session, scene, world, text):
    _plan, _result, said, _changed = play(text, session, scene, world)
    return said


def _run(case):
    lane = case["lane"]
    if lane == "route":
        session, scene, world = gate()
        for text in case["turns"][:-1]:
            _say(session, scene, world, text)
        decision = decision_for(case["turns"][-1], scene=scene, world=world, session=session)
        said = _say(session, scene, world, case["turns"][-1])
        ok = decision is None and case["absent"] not in said.casefold()
        ok = ok and session[LEDGER_KEY].get("npc_focus") == "gate_guard"
        return ok, said[:180]
    if lane == "contract":
        skipped = narration_skip({"kind": case["kind"], "metadata": case["metadata"]}, scene={}, session={})
        if case["text"] is None:
            return skipped is None, str(skipped)
        return skipped == (case["text"], case["reason"]), str(skipped)
    if lane == "narration":
        verdict = validate_narration(case["candidate"], case["facts"], session={"clue_knowledge": {}})
        return verdict["adopt"] is case["adopt"], str(verdict["reasons"])
    if lane == "save":
        session, scene, world = gate()
        for text in case["turns"][:-1]:
            _say(session, scene, world, text)
        restored = copy.deepcopy(session)
        said = _say(restored, scene, world, case["resume"])
        low = said.casefold()
        ok = case["absent"] not in low and "not available" not in low
        ok = ok and restored[LEDGER_KEY].get("npc_focus") == "gate_guard"
        ok = ok and session[LEDGER_KEY].get("npc_focus") == "gate_guard"
        return ok, said[:180]
    if lane == "account":
        summary = summarize_provider_rows(case["rows"])
        ok = summary["requests"] == case["requests"] and summary["total_tokens"] == case["tokens"]
        return ok, str(summary)
    return False, "unknown lane"


@pytest.fixture(autouse=True)
def _flags(monkeypatch):
    enable(monkeypatch)
    monkeypatch.setenv("ASHEN_EXPERIMENTAL_DYNAMIC_NPCS", "1")
    monkeypatch.setenv("ASHEN_DISABLE_EXPRESSION_GENERATION", "1")
    monkeypatch.setenv("ASHEN_EXPERIMENTAL_INTEGRATED_NARRATION", "0")


def test_frozen_holdout_runs_once():
    raw = FIXTURE.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == HOLDOUT_HASH
    document = json.loads(raw)
    assert document["external_validation"] is False
    results = []
    for case in document["cases"]:
        ok, detail = _run(case)
        results.append({"id": case["id"], "lane": case["lane"], "ok": ok, "detail": detail})
    RESULTS.parent.mkdir(parents=True, exist_ok=True)
    RESULTS.write_text(json.dumps({
        "hash": HOLDOUT_HASH,
        "passed": sum(1 for row in results if row["ok"]),
        "failed": sum(1 for row in results if not row["ok"]),
        "results": results,
    }, indent=2), encoding="utf-8")
    failed = [row for row in results if not row["ok"]]
    assert not failed
