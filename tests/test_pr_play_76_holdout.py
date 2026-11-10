"""One pass over the frozen PR-PLAY-76 holdout. Do not edit the manifest to chase failures."""
import hashlib
import json
import os
from pathlib import Path

import pytest

from game import storage
from game.authored_consequences import ENROLLMENT
from tests.test_pr_play_76_matrix import build
from tests.test_pr_play_76_physical import act, add, door, enable, said, stage

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "artifacts" / "pr_play_76" / "frozen_holdout.json"
FROZEN_HASH = "23376bbe834138b4f5735d1917dcff4c55bdacca6c0d88d74c4b7b77b1410026"


def _build(setup, session, scene):
    if setup == "stool":
        add(session, ident="stool", label="low stool", aliases=["stool"], use="seat")
        return
    if setup == "easy":
        add(session, ident="door", label="wooden door", aliases=["door"], **door(), skill_check={"skill_id": "athletics", "dc": 1})
        return
    if setup == "door_milestone":
        add(session, ident="door", label="wooden door", aliases=["door"], **door())
        scene["scene"]["interactables"].append({"id": "milestone", "label": "Weathered milestone", "aliases": ["milestone"]})
        return
    build(setup, session, scene)


def test_frozen_holdout_once(monkeypatch, tmp_path):
    digest = hashlib.sha256(MANIFEST.read_bytes()).hexdigest()
    assert digest == FROZEN_HASH
    cases = json.loads(MANIFEST.read_text(encoding="utf-8"))
    assert len(cases) == 100
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
                if turn.get("sentinel"):
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
        "failures": failures,
    }
    (tmp_path / "holdout_results.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    evidence = os.environ.get("ASHEN_TEST_EVIDENCE_DIR")
    if evidence:
        Path(evidence, "holdout_results.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("passed", "failed", "multi_turn", "save_resume")}))
    # The frozen manifest is not edited. Failures stay visible.
    assert not failures, json.dumps(failures[:12], indent=2)
