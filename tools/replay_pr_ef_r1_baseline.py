"""Production HTTP checks of frozen holdouts with captured real interpretations.

No external calls. Every expression starts in the authored scene; confirmation
gets a genuine pending two-step proposal through the same API first.
"""
import copy
import json
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"

import pytest
from fastapi.testclient import TestClient
from game import storage
from game.api import app
from tests.test_pr_ef_gm_authority import seed_scene
from tests.test_pr_du_player_pipeline import _fake_gm_for_resolution

OUT = ROOT / "artifacts/pr_ef_r1"
captured = json.loads((ROOT / "artifacts/pr_ef_gm_authority/live_holdouts.json").read_text(encoding="utf-8"))
rows = []
for observed in captured["rows"]:
    with tempfile.TemporaryDirectory(prefix="pr_ef_holdout_", dir=ROOT/"development/tmp") as temp, pytest.MonkeyPatch.context() as mp:
        seed_scene(Path(temp), mp)
        os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "0"
        os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "0"
        raw = observed["outcome"]["raw_interpretation"]
        wire_calls = []
        def replay_wire(messages, **kwargs):
            wire_calls.append(messages[1]["content"].splitlines()[0])
            return {"ok": True, "sent": False, "text": raw}
        mp.setattr("game.live_chat_interpretation.request_interpretation", replay_wire)
        mp.setattr("game.api.call_gpt", _fake_gm_for_resolution)
        client = TestClient(app)
        if observed["expected"] == "CONFIRMATION":
            setup = client.post("/api/chat", json={"text": "I inspect the courtyard lantern, then I walk through the courtyard gate."}).json()
            assert setup["resolution"]["kind"] == "conversational_clarify"
        before, world = copy.deepcopy(storage.load_session()), copy.deepcopy(storage.load_world())
        enabled_before = os.environ.get("ASHEN_DISABLE_LIVE_INTERPRETATION")
        data = client.post("/api/chat", json={"text": observed["player"]}).json()
        after = storage.load_session()
        resolution = data.get("resolution") or {}
        decision = (resolution.get("metadata") or {}).get("conversational_decision") or {}
        kind, expected = resolution.get("kind"), observed["expected"]
        nonmutating = before.get("turn_counter") == after.get("turn_counter") and world == storage.load_world()
        if expected in {"GM", "SESSION"}:
            passed = nonmutating and decision.get("communication_owner") in {expected, "GM" if expected == "SESSION" else expected}
        elif expected in {"CORRECTION", "WITHDRAWAL"}:
            passed = nonmutating and decision.get("communication_purpose") == expected
        elif expected == "MIXED":
            passed = nonmutating and decision.get("communication_owner") == "MIXED" and bool(decision.get("secondary_intentions"))
        elif expected == "AMBIGUOUS":
            passed = nonmutating and decision.get("category") == "CLARIFY"
        elif expected == "CONFIRMATION":
            passed = kind in {"investigate", "observe", "discover_clue"} and after["turn_counter"] == before["turn_counter"] + 1
        elif expected == "NPC":
            passed = (resolution.get("social") or {}).get("npc_id") == "sergeant_mara"
        else:
            passed = kind == "scene_transition"
        rows.append({"player": observed["player"], "expected": expected, "pass": passed, "nonmutating": nonmutating,
                     "interpretation_disabled_before": enabled_before, "interpretation_disabled_after": os.environ.get("ASHEN_DISABLE_LIVE_INTERPRETATION"),
                     "wire_calls": wire_calls,
                     "decision": decision, "resolution": resolution, "response": data.get("gm_output", {}).get("player_facing_text")})
        print(observed["player"], passed, kind, flush=True)
(OUT/"baseline_recorded_holdouts.json").write_text(json.dumps({"live": False, "source": "captured live holdout interpretations", "rows": rows, "passed": sum(r["pass"] for r in rows), "total": len(rows)}, indent=2), encoding="utf-8")
