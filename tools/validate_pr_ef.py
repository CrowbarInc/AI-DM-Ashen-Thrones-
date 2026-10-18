"""Bounded PR-EF API/semantic validation, using disposable authored campaign data.

No production data is loaded into the fixture. --live enables the existing
OpenAI interpretation/narration boundary; default uses labelled test doubles.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true")
    parser.add_argument("--holdouts", action="store_true")
    parser.add_argument("--out", required=True)
    parser.add_argument("--call-limit", type=int, default=16)
    parser.add_argument("--replay", help="Replay raw interpretations and narration from a captured live run")
    args = parser.parse_args()
    out = Path(args.out).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    os.environ.update({
        "ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT": "1",
        "ASHEN_DISABLE_LIVE_INTERPRETATION": "0",
        "ASHEN_DISABLE_PROVIDER_CALLS": "0",
        "ASHEN_PROVIDER_REQUEST_LIMIT": str(args.call_limit),
        "ASHEN_PROVIDER_INPUT_TOKEN_LIMIT": "160000",
        "ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT": "16000",
        "ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT": "176000",
        "ASHEN_PROVIDER_TIMEOUT_SECONDS": "25",
        "ASHEN_NARRATION_MAX_OUTPUT_TOKENS": "1600",
        "ASHEN_PROVIDER_USAGE_PATH": str(out.with_suffix(".usage.jsonl")),
    })
    import pytest
    from fastapi.testclient import TestClient
    from game import storage
    from game.api import app
    from game.provider_budget import snapshot
    from game.live_chat_interpretation import interpret_production_turn
    from tests.test_pr_ef_gm_authority import seed_scene, scripted_interpretation, TEN_TURNS
    from tests.test_pr_du_player_pipeline import _fake_gm_for_resolution
    from game.conversational_orchestration import decision_from_interpretation_record

    with tempfile.TemporaryDirectory(prefix="pr_ef_", dir=ROOT / "development" / "tmp") as temp, pytest.MonkeyPatch.context() as mp:
        seed_scene(Path(temp), mp)
        # Historical experiment packages deliberately disable interpretation on import.
        # Restore this harness's explicit mode after all fixture imports.
        os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "0"
        if not args.live:
            mp.setattr("game.live_chat_interpretation.request_interpretation", scripted_interpretation)
            mp.setattr("game.api.call_gpt", _fake_gm_for_resolution)
        if args.replay:
            captured = json.loads(Path(args.replay).read_text(encoding="utf-8"))
            replay_current = {}
            def replay_interpretation(messages, **kwargs):
                nonlocal replay_current
                text = messages[1]["content"].splitlines()[0].removeprefix("Utterance: ")
                row = next(row for row in captured["rows"] if row["player"] == text)
                replay_current = row
                raw = row["resolution"]["metadata"]["live_chat_interpretation"]["raw_interpretation"]
                return {"ok": True, "sent": False, "text": raw}
            def replay_narration(messages):
                text = replay_current["response"]
                return {"player_facing_text": text, "tags": [], "scene_update": None,
                        "activate_scene_id": None, "new_scene_draft": None,
                        "world_updates": None, "suggested_action": None, "debug_notes": "recorded_live_narration"}
            mp.setattr("game.live_chat_interpretation.request_interpretation", replay_interpretation)
            mp.setattr("game.api.call_gpt", replay_narration)
        client = TestClient(app)
        rows = []
        expressions = json.loads((ROOT / "artifacts/pr_ef_gm_authority/holdouts.json").read_text()) if args.holdouts else [(text, None) for text in TEN_TURNS]
        for number, (text, expected) in enumerate(expressions, 1):
            before, world = copy.deepcopy(storage.load_session()), copy.deepcopy(storage.load_world())
            calls_before = snapshot()["requests"]
            started = time.perf_counter()
            print(f"Turn {number}: {text}", flush=True)
            if args.holdouts:
                outcome = interpret_production_turn(player_text=text, mode="AUTO", scene=storage.load_active_scene(), world=world, session=before, log=storage.load_log())
                record = outcome.get("record")
                communication = (record or {}).get("communication") or {}
                actual = communication.get("recipient")
                if expected in {"CORRECTION", "CONFIRMATION", "WITHDRAWAL"}:
                    actual = communication.get("purpose")
                decision = decision_from_interpretation_record(record, player_text=text, scene=storage.load_active_scene(), world=world).to_public_dict()
                row = {"turn": number, "player": text, "expected": expected, "actual": actual, "pass": actual == expected,
                       "outcome": outcome, "decision": decision}
            else:
                response = client.post("/api/chat?ui_mode=player", json={"text": text, "ui_mode": "player"})
                data = response.json()
                after = storage.load_session()
                resolution = data.get("resolution") or {}
                if number == 6:
                    storage.save_session(copy.deepcopy(after))
                    assert storage.load_session().get("conversational_context") == after.get("conversational_context")
                metadata = resolution.get("metadata") or {}
                decision = metadata.get("conversational_decision") or {}
                row = {"turn": number, "player": text, "http_status": response.status_code,
                       "response": data.get("gm_output", {}).get("player_facing_text"), "resolution": resolution,
                       "decision": decision, "world_changed": storage.load_world() != world,
                       "changed_session_keys": sorted(key for key in set(before) | set(after) if before.get(key) != after.get(key)),
                       "before_turn": before.get("turn_counter"), "after_turn": after.get("turn_counter"),
                       "scene": after.get("active_scene_id"), "context_after": after.get("conversational_context")}
                expected_nonmutating = number in {1, 2, 3, 6, 8, 9}
                row["state_pass"] = not expected_nonmutating or (before.get("turn_counter") == after.get("turn_counter") and not row["world_changed"])
            row.update(elapsed_ms=round((time.perf_counter() - started) * 1000, 3), provider_calls=snapshot()["requests"] - calls_before)
            rows.append(row)
            payload = {"live": args.live, "replay": args.replay, "holdouts": args.holdouts, "transport": "production FastAPI TestClient /api/chat" if not args.holdouts else "production interpretation contract", "rows": rows, "provider": snapshot()}
            out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
            print(json.dumps({k: row[k] for k in ("response", "actual", "pass", "state_pass", "elapsed_ms", "provider_calls") if k in row}), flush=True)


if __name__ == "__main__":
    main()
