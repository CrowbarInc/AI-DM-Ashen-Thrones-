"""PR-PLAY-61 controlled investigation through the application chat route.

One live attempt per supported action. Fault cases do not call the provider.
"""
from __future__ import annotations

import json
import os
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
OUT = ROOT / "artifacts" / "pr_play_61"
LIVE_DIR = OUT / "live_session"
os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_RETRIES"] = "1"
os.environ["ASHEN_PLAYTEST_DISABLE_SDK_RETRIES"] = "1"
os.environ["ASHEN_PROVIDER_REQUEST_LIMIT"] = "8"
os.environ["ASHEN_PROVIDER_INPUT_TOKEN_LIMIT"] = "12000"
os.environ["ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT"] = "2000"
os.environ["ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT"] = "15000"
os.environ["ASHEN_PROVIDER_USAGE_PATH"] = str(OUT / "provider_usage.jsonl")

from fastapi.testclient import TestClient

from game import integrated_investigation_narration as integrated
from game import quarantined_investigation_narration as q
from game import storage
from tests.test_pr_play_52_quarantined_integration import _seed
from tests.test_pr_play_57_integrated_narration import ROUTE

NOTICE = "I examine the notice board."
BARREL = "I examine the rain barrel."
REPEAT = "I examine the notice board again."
LOOK = "I look around the gate."
ACTIONS = [NOTICE, BARREL, REPEAT, LOOK]


def redact(value):
    if isinstance(value, str):
        import re
        return re.sub(r"sk-[A-Za-z0-9_\-]{8,}", "[REDACTED]", value)
    if isinstance(value, dict):
        return {key: redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def key_present() -> bool:
    try:
        from game.config import get_openai_api_key
        return bool(get_openai_api_key())
    except Exception:
        return False


def authority() -> dict:
    session = storage.load_session()
    overlay = (session.get("runtime_scene_overlays") or {}).get("frontier_gate") or {}
    character = storage.load_character()
    world = storage.load_world()
    return {
        "campaign_run_id": session.get("campaign_run_id"),
        "scene": session.get("active_scene_id"),
        "visited": session.get("visited_scene_ids"),
        "player": character.get("id"),
        "hp": character.get("hp"),
        "inventory": character.get("inventory"),
        "equipment": character.get("equipment"),
        "clues": overlay.get("discovered_clues"),
        "state_flags": overlay.get("state_flags"),
        "npcs": session.get("npc_runtime"),
        "quests": session.get("quest_journal"),
        "conditions": storage.load_conditions() if storage.CONDITIONS_PATH.exists() else None,
        "combat": storage.load_combat(),
        "world_flags": (world.get("world_state") or {}).get("flags"),
        "clocks": session.get("clocks"),
    }


def mechanical(body: dict) -> dict:
    resolution = body.get("resolution") if isinstance(body.get("resolution"), dict) else {}
    changes = resolution.get("state_changes") if isinstance(resolution.get("state_changes"), dict) else {}
    return {
        "kind": resolution.get("kind"),
        "success": resolution.get("success"),
        "action_id": resolution.get("action_id"),
        "interactable_id": resolution.get("interactable_id"),
        "clue_text": resolution.get("clue_text"),
        "discovered_clues": resolution.get("discovered_clues"),
        "state_changes": {
            "clue_revealed": changes.get("clue_revealed"),
            "already_searched": changes.get("already_searched"),
            "items_added": changes.get("items_added"),
            "npc_changes": changes.get("npc_changes"),
        },
    }


def facing(body: dict) -> str:
    gm = body.get("gm_output") if isinstance(body.get("gm_output"), dict) else {}
    return str(gm.get("player_facing_text") or "")


def post_all(texts: list[str]) -> list[dict]:
    from game.api import app
    client = TestClient(app)
    client.__enter__()
    rows = []
    try:
        for text in texts:
            started = time.perf_counter()
            response = client.post("/api/chat?ui_mode=player", json={"text": text})
            elapsed = round((time.perf_counter() - started) * 1000, 3)
            body = response.json()
            record = q.evidence_records()[-1] if q.evidence_records() else None
            rows.append({
                "input": text,
                "status_code": response.status_code,
                "http_ms": elapsed,
                "facing": facing(body),
                "published_marker": ((body.get("gm_output") or {}).get("metadata") or {}).get(
                    "experimental_integrated_narration"),
                "mechanical": mechanical(body),
                "authority": authority(),
                "quarantine": compact_record(record),
            })
    finally:
        try:
            client.__exit__(None, None, None)
        except Exception:
            pass
    return rows


def compact_record(record: dict | None) -> dict | None:
    if not isinstance(record, dict):
        return None
    live = record.get("live_provider") if isinstance(record.get("live_provider"), dict) else {}
    validation = record.get("validation") if isinstance(record.get("validation"), dict) else {}
    return {
        "eligible": record.get("eligible"),
        "diagnostic": record.get("diagnostic"),
        "error_type": record.get("error_type"),
        "mode": record.get("mode"),
        "used_fallback": record.get("used_fallback"),
        "player_facing_published": record.get("player_facing_published"),
        "decision": validation.get("decision"),
        "semantic_decision": (validation.get("semantic") or {}).get("decision") if isinstance(validation.get("semantic"), dict) else None,
        "coverage_decision": (validation.get("coverage") or {}).get("decision") if isinstance(validation.get("coverage"), dict) else None,
        "legacy_hard_valid": (validation.get("legacy") or {}).get("hard_valid") if isinstance(validation.get("legacy"), dict) else None,
        "raw_provider_text": record.get("raw_provider_text"),
        "assembled": record.get("assembled"),
        "provider_requests": record.get("provider_requests"),
        "validation_ms": record.get("validation_ms"),
        "total_integrated_ms": record.get("total_integrated_ms"),
        "provider_latency_ms": live.get("provider_latency_ms"),
        "input_tokens": live.get("input_tokens"),
        "output_tokens": live.get("output_tokens"),
        "total_tokens": live.get("total_tokens"),
        "model": live.get("model"),
        "anchors": record.get("anchors"),
    }


def enable_publication(session_id: str, *, live: bool) -> None:
    os.environ[q.GATE_ENV] = "1"
    os.environ[q.MODE_ENV] = "integrated"
    os.environ[q.PUBLICATION_ENV] = "1"
    os.environ[q.PUBLICATION_SESSION_ENV] = session_id
    os.environ[q.EVIDENCE_ENV] = str(OUT / "quarantine_evidence")
    if live:
        os.environ[q.LIVE_ENV] = "1"
        os.environ.pop(q.FAULT_ENV, None)
        os.environ.pop(q.SAMPLE_ENV, None)
    else:
        os.environ.pop(q.LIVE_ENV, None)


def disable_publication() -> None:
    for name in (q.GATE_ENV, q.MODE_ENV, q.PUBLICATION_ENV, q.PUBLICATION_SESSION_ENV, q.LIVE_ENV, q.FAULT_ENV, q.SAMPLE_ENV):
        os.environ.pop(name, None)


class _Patch:
    def setattr(self, target, name, value):
        setattr(target, name, value)


def run() -> dict:
    OUT.mkdir(parents=True, exist_ok=True)
    usage = OUT / "provider_usage.jsonl"
    if usage.exists():
        usage.unlink()
    evidence_dir = OUT / "quarantine_evidence"
    if evidence_dir.exists():
        for child in evidence_dir.glob("*.json"):
            child.unlink()
    present = key_present()
    from game.provider_budget import snapshot
    q.reset_live_budget()
    q.clear_evidence()
    disable_publication()
    _seed(OUT / "control_session", _Patch(), "frontier_gate")
    initial_control = authority()
    control_state = post_state()
    control_actions = post_all(ACTIONS)
    control_final = authority()

    q.reset_live_budget()
    q.clear_evidence()
    _seed(LIVE_DIR, _Patch(), "frontier_gate")
    session_id = storage.load_session()["campaign_run_id"]
    enable_publication(session_id, live=present)
    os.environ[q.LABEL_ENV] = "pr_play_61"
    initial_live = authority()
    live_state = post_state()
    live_actions = post_all(ACTIONS)
    live_final = authority()
    published = [row for row in live_actions if row.get("published_marker") == "published"]
    fallbacks = [row for row in live_actions if row.get("quarantine") and row["quarantine"].get("used_fallback") is True]
    provider_requests = sum(int((row.get("quarantine") or {}).get("provider_requests") or 0) for row in live_actions)

    failures = failure_injection()
    isolation = isolation_check(session_id)
    usage_rows = []
    if usage.exists():
        usage_rows = [json.loads(line) for line in usage.read_text(encoding="utf-8").splitlines() if line.strip()]
    result = {
        "key_present": present,
        "live_narration": "TESTED" if present else "NOT TESTED",
        "campaign_fixture": "data/scenes/frontier_gate.json",
        "scene": "frontier_gate",
        "authorized_discovery": ROUTE,
        "actions": ACTIONS,
        "session_id": session_id,
        "control": {"initial": initial_control, "state": control_state, "actions": control_actions, "final": control_final},
        "live": {"initial": initial_live, "state": live_state, "actions": live_actions, "final": live_final},
        "published_count": len(published),
        "fallback_count": len(fallbacks),
        "provider_requests": provider_requests,
        "provider_snapshot": snapshot(),
        "usage_events": usage_rows,
        "failures": failures,
        "isolation": isolation,
        "authority_match": {key: control_final.get(key) == live_final.get(key) for key in control_final},
    }
    (OUT / "experiment_results.json").write_text(
        json.dumps(redact(result), indent=2, ensure_ascii=False), encoding="utf-8")
    return result


def post_state() -> dict:
    from game.api import app
    client = TestClient(app)
    client.__enter__()
    try:
        response = client.get("/api/state?ui_mode=player")
        body = response.json()
        session = body.get("session") if isinstance(body.get("session"), dict) else {}
        scene = body.get("scene") if isinstance(body.get("scene"), dict) else {}
        scene_body = scene.get("scene") if isinstance(scene.get("scene"), dict) else {}
        return {
            "status_code": response.status_code,
            "scene_id": session.get("active_scene_id") or scene_body.get("id"),
            "campaign_started": session.get("campaign_started"),
            "player_visible": sorted(session.keys()) if isinstance(session, dict) else [],
            "ok": body.get("ok", response.status_code == 200),
        }
    finally:
        try:
            client.__exit__(None, None, None)
        except Exception:
            pass


def failure_injection() -> list[dict]:
    cases = []
    original = integrated.run_integrated_hook

    def play(name, text, *, sample="", fault="", generator_text=None):
        q.clear_evidence()
        q.reset_live_budget()
        _seed(OUT / "faults" / name, _Patch(), "frontier_gate")
        enable_publication(storage.load_session()["campaign_run_id"], live=False)
        os.environ[q.SAMPLE_ENV] = sample
        os.environ[q.FAULT_ENV] = fault
        if generator_text is not None:
            integrated.run_integrated_hook = lambda value, prose=generator_text: original(
                value, generator=q._Replay(prose, ""))
        else:
            integrated.run_integrated_hook = original
        before = authority()
        try:
            row = post_all([text])[0]
        except Exception as exc:
            row = {"error_type": type(exc).__name__, "error": traceback.format_exc()[-500:]}
        finally:
            integrated.run_integrated_hook = original
        after = authority()
        continued = None
        try:
            os.environ.pop(q.SAMPLE_ENV, None)
            os.environ.pop(q.FAULT_ENV, None)
            integrated.run_integrated_hook = lambda value: original(
                value, generator=q._Replay("You examine the board again and nothing new is established. " + ROUTE, ""))
            continued = post_all([REPEAT])[0]
        except Exception as exc:
            continued = {"error_type": type(exc).__name__}
        finally:
            integrated.run_integrated_hook = original
        cases.append({
            "name": name,
            "before_clues": before.get("clues"),
            "after_clues": after.get("clues"),
            "inventory_unchanged": before.get("inventory") == after.get("inventory"),
            "hp_unchanged": before.get("hp") == after.get("hp"),
            "npcs_unchanged": before.get("npcs") == after.get("npcs"),
            "scene_unchanged": before.get("scene") == after.get("scene") == "frontier_gate",
            "action": row,
            "continuation": {
                "status_code": (continued or {}).get("status_code"),
                "published": (continued or {}).get("published_marker"),
                "facing": (continued or {}).get("facing"),
                "decision": ((continued or {}).get("quarantine") or {}).get("decision"),
            },
        })

    play("provider_unavailable", NOTICE, fault="provider_error")
    play("provider_timeout", NOTICE, fault="timeout")
    play("empty", NOTICE, sample="empty")
    play("malformed", NOTICE, sample="malformed")
    play("validation_fail", NOTICE, sample="unsafe")
    play("review_required", NOTICE, sample="stub")
    play("validation_error", NOTICE, sample="malformed")
    play("unauthorized_inventory", NOTICE, sample="unsafe")
    play("unauthorized_persistent", NOTICE, generator_text=(
        "The guard captain dies where he stands. The eastern gate remains open."))
    play("missing_discovery", NOTICE, sample="stub")
    play("take_key", "I take the silver key from the notice board.", sample="unsafe")
    return cases


def isolation_check(live_session_id: str) -> dict:
    q.clear_evidence()
    _seed(OUT / "other_session", _Patch(), "frontier_gate")
    other = storage.load_session()["campaign_run_id"]
    enable_publication(live_session_id, live=False)
    original = integrated.run_integrated_hook
    integrated.run_integrated_hook = lambda value: original(value, generator=q._Replay(ROUTE, ""))
    try:
        row = post_all([NOTICE])[0]
    finally:
        integrated.run_integrated_hook = original
    return {
        "other_session": other,
        "bound_session": live_session_id,
        "distinct": other != live_session_id,
        "published_marker": row.get("published_marker"),
        "facing_is_route": row.get("facing") == ROUTE,
    }


if __name__ == "__main__":
    try:
        result = run()
    except Exception:
        traceback.print_exc()
        raise
    print(json.dumps({
        "key_present": result["key_present"],
        "published_count": result["published_count"],
        "fallback_count": result["fallback_count"],
        "provider_requests": result["provider_requests"],
        "authority_match": result["authority_match"],
        "isolation": result["isolation"],
        "decisions": [((row.get("quarantine") or {}).get("decision")) for row in result["live"]["actions"]],
        "http": [row.get("http_ms") for row in result["live"]["actions"]],
    }, indent=2))
