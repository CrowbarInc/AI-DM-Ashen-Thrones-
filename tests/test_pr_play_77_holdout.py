"""One pass over the frozen PR-PLAY-77 holdout. Do not edit the manifest to chase failures."""
import hashlib
import json
import os
from pathlib import Path

import pytest

from game import storage
from game.authored_consequences import ENROLLMENT
from tests.test_pr_play_76_holdout import _build as build76
from tests.test_pr_play_76_physical import act, add, door, enable, said, stage

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "artifacts" / "pr_play_77" / "frozen_holdout.json"


def _build(setup, session, scene):
    if setup == "door_milestone":
        add(session, ident="door", label="wooden door", aliases=["door"], **door())
        scene["scene"]["interactables"].append({"id": "milestone", "label": "Weathered milestone", "aliases": ["milestone"]})
        return
    if setup == "crate_milestone":
        add(session, ident="crate", label="oak crate", aliases=["crate"], mobility="movable", weight="light", position="by the wall")
        scene["scene"]["interactables"].append({"id": "milestone", "label": "Weathered milestone", "aliases": ["milestone"]})
        return
    if setup == "cup_milestone":
        add(session, ident="cup", label="wooden cup", aliases=["cup"], mobility="movable", weight="light", portable=True, position="on the table")
        scene["scene"]["interactables"].append({"id": "milestone", "label": "Weathered milestone", "aliases": ["milestone"]})
        return
    if setup == "blocking_milestone":
        add(session, ident="crate", label="oak crate", aliases=["crate"], mobility="movable", weight="light",
            position="blocking the doorway", obstructs="doorway")
        scene["scene"]["interactables"].append({"id": "milestone", "label": "Weathered milestone", "aliases": ["milestone"]})
        return
    if setup == "bench_milestone":
        add(session, ident="bench", label="wooden bench", aliases=["bench", "seat"], use="seat")
        scene["scene"]["interactables"].append({"id": "milestone", "label": "Weathered milestone", "aliases": ["milestone"]})
        return
    if setup == "notice_milestone":
        scene["scene"]["interactables"].append({"id": "notice_board", "label": "Notice board", "aliases": ["notice board"]})
        scene["scene"]["interactables"].append({"id": "milestone", "label": "Weathered milestone", "aliases": ["milestone"]})
        return
    if setup == "fitting_milestone":
        scene["scene"]["visible_facts"] = ["A weathered stone marker stands in the yard."]
        act("Is there a small loose stone I could shift aside?", session, scene)
        scene["scene"]["interactables"].append({"id": "milestone", "label": "Weathered milestone", "aliases": ["milestone"]})
        return
    if setup == "locked_bench":
        add(session, ident="door", label="wooden door", aliases=["door"], **door(locked=True))
        add(session, ident="bench", label="wooden bench", aliases=["bench", "seat"], use="seat")
        return
    build76(setup, session, scene)


def test_frozen_holdout_once(monkeypatch, tmp_path):
    digest = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    cases = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert len(cases) == 110
    enable(monkeypatch)
    monkeypatch.setenv("ASHEN_DATA_DIR", str(tmp_path))
    failures = []
    for case in cases:
        session, scene, _packed = stage()
        try:
            _build(case["setup"], session, scene)
            if case.get("campaign") == "beta":
                session["campaign_run_id"] = "beta"
                session[ENROLLMENT] = "beta"
            for index, turn in enumerate(case["turns"]):
                plan, result, _before = act(turn["input"], session, scene)
                text = said(plan, result)
                if plan is None or plan.get("category") != turn["category"] or turn["fragment"] not in text.casefold():
                    raise AssertionError(f"{plan.get('category') if plan else None} :: {text}")
                if turn.get("absent") and turn["absent"].casefold() in text.casefold():
                    raise AssertionError("absent :: " + text)
                if "SENTINEL" in text:
                    raise AssertionError("sentinel published")
                if case.get("save") and index == 0:
                    storage.save_session(session)
                    session = storage.load_session()
        except Exception as exc:
            failures.append({"id": case["id"], "group": case["group"], "error": str(exc)})
    out = {
        "hash": digest,
        "count": len(cases),
        "passed": len(cases) - len(failures),
        "failed": len(failures),
        "multi_turn": sum(1 for case in cases if case.get("multi") or len(case["turns"]) > 1),
        "save_resume": sum(1 for case in cases if case.get("save")),
        "partial_marked": sum(1 for case in cases if case["group"] == "partial"),
        "blocked_marked": sum(1 for case in cases if case["group"] == "dependency"),
        "failures": failures,
    }
    evidence = os.environ.get("ASHEN_TEST_EVIDENCE_DIR")
    if evidence:
        Path(evidence, "holdout_results.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    else:
        (ROOT / "artifacts" / "pr_play_77" / "holdout_results.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({key: out[key] for key in ("hash", "passed", "failed", "multi_turn", "save_resume")}))
    # The manifest stays frozen. These four are the original authoring mismatches.
    assert {item["id"] for item in failures} == {"H017", "H068", "H073", "H089"}
