"""Observation only: six unique live turns, isolated state, no repairs or reruns."""
from __future__ import annotations

import json
import sys
import traceback
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent
CALLS = []
HTTP = []
TURNS = []
CURRENT = {"turn": None, "kind": "other", "retry_attempt": 0}


def save(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


import openai
import httpx
from openai.resources.responses import Responses

original_create = Responses.create
original_send = httpx.Client.send


def observe_create(self, *args, **kwargs):
    row = {**CURRENT, "index": len(CALLS) + 1, "request": kwargs,
           "started": datetime.now(timezone.utc).isoformat()}
    CALLS.append(row)
    save("model_calls.json", CALLS)
    try:
        result = original_create(self, *args, **kwargs)
        row["raw_output"] = result.output_text
        row["response"] = result.model_dump(mode="json")
        return result
    except Exception as exc:
        row["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        save("model_calls.json", CALLS)


def observe_send(self, request, *args, **kwargs):
    if "/responses" not in str(request.url):
        return original_send(self, request, *args, **kwargs)
    row = {**CURRENT, "index": len(HTTP) + 1, "method": request.method,
           "endpoint": str(request.url).split("?")[0]}
    HTTP.append(row)
    try:
        response = original_send(self, request, *args, **kwargs)
        row["status"] = response.status_code
        return response
    except Exception as exc:
        row["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        save("http_attempts.json", HTTP)


Responses.create = observe_create
httpx.Client.send = observe_send

from fastapi.testclient import TestClient
from game import storage
import game.api as api
import game.semantic_interpreter as interpreter
import game.api_upstream_preflight as preflight
from game.defaults import (default_scene, default_session, default_world,
                           default_campaign, default_character, default_combat, default_conditions)
from game.gm import _safe_json


def snapshot():
    return {"session": storage.load_session(), "world": storage.load_world(),
            "scene": storage.load_scene(storage.load_session()["active_scene_id"])}


def wrap(fn, kind):
    def observed(*args, **kwargs):
        prior = dict(CURRENT)
        CURRENT.update(kind=kind, retry_attempt=kwargs.get("retry_attempt", 0))
        if kind == "generation":
            save(f"{CURRENT['turn']}_after_player_before_generation_{len(CALLS)}.json", snapshot())
        try:
            result = fn(*args, **kwargs)
            if kind == "generation":
                save(f"{CURRENT['turn']}_parsed_generation_{len(CALLS)}.json", result)
            return result
        finally:
            CURRENT.clear()
            CURRENT.update(prior)
    return observed


api.call_gpt = wrap(api.call_gpt, "generation")
interpreter._invoke_interpretation_model = wrap(interpreter._invoke_interpretation_model, "interpretation")
preflight.run_upstream_api_preflight = wrap(preflight.run_upstream_api_preflight, "preflight")


def seed(sequence):
    base = OUT / f"isolated_{sequence}"
    storage.BASE_DIR = base
    storage.DATA_DIR = base / "data"
    storage.SCENES_DIR = storage.DATA_DIR / "scenes"
    for attr, filename in {"WORLD_PATH": "world.json", "SESSION_PATH": "session.json",
            "CAMPAIGN_PATH": "campaign.json", "CHARACTER_PATH": "character.json",
            "COMBAT_PATH": "combat.json", "CONDITIONS_PATH": "conditions.json",
            "SESSION_LOG_PATH": "session_log.jsonl"}.items():
        setattr(storage, attr, storage.DATA_DIR / filename)
    storage.SCENES_DIR.mkdir(parents=True, exist_ok=True)
    for base_sid in ("frontier_gate", "market_quarter", "old_milestone"):
        storage._save_json(storage.scene_path(base_sid), default_scene(base_sid))
    sid = "loom_workshop" if sequence == "A" else "cloth_stall"
    scene = default_scene(sid)
    scene["scene"].update(id=sid, location="Loom workshop" if sequence == "A" else "Market cloth stall",
                          summary="A wooden loom stands in a workshop." if sequence == "A" else "A cloth seller stands at a market stall.",
                          visible_facts=["The wooden loom beam is cracked.", "The loom's iron brace is bent."] if sequence == "A" else ["A cloth seller stands beside folded cloth at a market stall."],
                          interactables=[{"id": "loom", "label": "wooden loom", "aliases": ["loom beam", "beam", "iron brace", "brace"]}] if sequence == "A" else [],
                          discoverable_clues=[], exits=[])
    world = default_world()
    world["npcs"] = [] if sequence == "A" else [{"id": "cloth_seller", "name": "Cloth Seller", "location": sid, "topics": []}]
    session = default_session()
    session.update(active_scene_id=sid, visited_scene_ids=[sid], turn_counter=1)
    for path, value in [(storage.WORLD_PATH, world), (storage.SESSION_PATH, session),
            (storage.CAMPAIGN_PATH, default_campaign()), (storage.CHARACTER_PATH, default_character()),
            (storage.COMBAT_PATH, default_combat()), (storage.CONDITIONS_PATH, default_conditions()),
            (storage.scene_path(sid), scene)]:
        storage._save_json(path, value)
    storage.SESSION_LOG_PATH.touch()
    save(f"setup_{sequence}.json", snapshot())


def main():
    if (OUT / "run_started.json").exists() and ((OUT / "model_calls.json").exists() or (OUT / "turns.json").exists()):
        raise SystemExit("Run already started. No reruns allowed.")
    if (OUT / "run_started.json").exists():
        save("startup_fixture_error.json", {"error": "Startup scene validation: default frontier_gate referenced missing old_milestone", "gameplay_turns": 0, "model_calls": 0, "resolution": "Completed default scene fixture before any gameplay/API attempt"})
    save("run_started.json", {"utc": datetime.now(timezone.utc).isoformat(), "max_turns": 6})
    seed("A")
    streak = 0
    stop = None
    with TestClient(api.app) as client:
        save("preflight.json", preflight.get_latest_upstream_api_preflight())
        print("READY", flush=True)
        for expected in ["A1", "A2", "A3", "B1", "B2", "B3"]:
            line = sys.stdin.readline().strip()
            if not line or line == "STOP":
                stop = "operator stopped or input ended"
                break
            turn, player = line.split("\t", 1)
            if turn != expected:
                stop = f"Unexpected turn {turn}; expected {expected}"
                break
            if turn == "B1":
                seed("B")
            CURRENT["turn"] = turn
            before = snapshot()
            count = len(CALLS)
            row = {"turn": turn, "player": player, "before": before}
            TURNS.append(row)
            save("turns.json", TURNS)
            try:
                response = client.post("/api/chat", json={"text": player})
                row.update(http_status=response.status_code, payload=response.json(), after=snapshot())
            except Exception:
                row.update(error=traceback.format_exc(), after=snapshot())
            row["calls"] = CALLS[count:]
            gm = row.get("payload", {}).get("gm_output", {})
            meta = gm.get("metadata", {})
            accepted = meta.get("accepted_response", {})
            emitted = gm.get("player_facing_text", "")
            row.update(sealed=accepted.get("text"), emitted=emitted, provenance=accepted.get("provenance"))
            gen = [c for c in row["calls"] if c["kind"] == "generation"]
            parsed = [_safe_json(c.get("raw_output", ""), require_structured_claims=True) for c in gen]
            row["parsed_raw_attempts"] = parsed
            valid = any(not p.get("metadata", {}).get("structured_contract_failure") for p in parsed)
            streak = 0 if valid else streak + 1
            if emitted.strip().startswith("{") or '"declared_claims"' in emitted:
                stop = "raw JSON reached player"
            elif accepted.get("text") != emitted:
                stop = "C18 sealed/emitted exactness break"
            elif streak >= 2:
                stop = "two consecutive turns without valid structured envelope"
            row["stop_reason"] = stop
            save(f"{turn}_full_trace.json", row)
            save("turns.json", TURNS)
            print(json.dumps({"turn": turn, "emitted": emitted, "provenance": row["provenance"],
                              "generation_calls": len(gen), "stop": stop}), flush=True)
            if stop:
                break
            print("READY " + expected, flush=True)
    save("run_finished.json", {"turns": len(TURNS), "stop_reason": stop,
                               "model_calls": len(CALLS), "http_attempts": len(HTTP)})
    print("FINISHED", flush=True)


if __name__ == "__main__":
    main()
