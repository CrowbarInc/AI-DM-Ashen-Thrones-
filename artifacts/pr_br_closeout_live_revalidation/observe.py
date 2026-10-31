"""PR-BR closeout live revalidation. Observation only. Maximum four gameplay turns.

No repairs, no reruns, no extra turns. One process so startup preflight is counted once.
Turns arrive through inbox.json. The operator decides the next player line after each result.
"""
from __future__ import annotations

import json
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent
CALLS: list[dict] = []
HTTP: list[dict] = []
TURNS: list[dict] = []
BOUNDED: list[dict] = []
DECISIONS: list[dict] = []
CURRENT = {"turn": None, "kind": "other", "retry_attempt": 0}
MAX_TURNS = 4


def save(name, value):
    path = OUT / name
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def status(text: str) -> None:
    (OUT / "status.txt").write_text(text, encoding="utf-8")
    print(text, flush=True)


import httpx
from openai.resources.responses import Responses

original_create = Responses.create
original_send = httpx.Client.send


def _usage(dump: dict) -> dict:
    usage = dump.get("usage") if isinstance(dump, dict) else None
    if not isinstance(usage, dict):
        return {}
    return {
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        "total_tokens": usage.get("total_tokens"),
        "input_tokens_details": usage.get("input_tokens_details"),
        "output_tokens_details": usage.get("output_tokens_details"),
    }


def observe_create(self, *args, **kwargs):
    row = {
        "index": len(CALLS) + 1,
        "turn": CURRENT.get("turn"),
        "kind": CURRENT.get("kind"),
        "retry_attempt": kwargs.get("retry_attempt", CURRENT.get("retry_attempt", 0)),
        "model": kwargs.get("model"),
        "started": datetime.now(timezone.utc).isoformat(),
        "input_chars": len(json.dumps(kwargs.get("input"), default=str)),
    }
    CALLS.append(row)
    save("model_calls.json", CALLS)
    try:
        result = original_create(self, *args, **kwargs)
        dump = result.model_dump(mode="json")
        row["raw_output"] = result.output_text
        row["response_id"] = dump.get("id")
        row["response_model"] = dump.get("model")
        row["usage"] = _usage(dump)
        row["status"] = dump.get("status")
        return result
    except Exception as exc:
        row["error"] = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        row["finished"] = datetime.now(timezone.utc).isoformat()
        save("model_calls.json", CALLS)


def observe_send(self, request, *args, **kwargs):
    if "/responses" not in str(request.url):
        return original_send(self, request, *args, **kwargs)
    row = {
        "index": len(HTTP) + 1,
        "turn": CURRENT.get("turn"),
        "kind": CURRENT.get("kind"),
        "method": request.method,
        "endpoint": str(request.url).split("?")[0],
    }
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
import game.immutable_valid_response as immutable
import game.live_resolution as live_resolution
from game.defaults import (
    default_scene,
    default_session,
    default_world,
    default_campaign,
    default_character,
    default_combat,
    default_conditions,
)
from game.gm import _safe_json


def temporal_slice(session: dict | None) -> dict:
    session = session or {}
    focus = session.get("discourse_focus") if isinstance(session.get("discourse_focus"), dict) else {}
    provenance = session.get("narration_temporal_provenance")
    if not isinstance(provenance, dict):
        provenance = {}
    return {
        "gm_inferences": provenance.get("gm_inferences") or [],
        "player_hypotheses": provenance.get("player_hypotheses") or [],
        "accepted_incidentals": provenance.get("accepted_incidentals") or [],
        "rejected_consequential": provenance.get("rejected_consequential") or [],
        "active_claim": focus.get("active_claim"),
        "discourse_focus": focus,
        "turn_counter": session.get("turn_counter"),
        "active_scene_id": session.get("active_scene_id"),
    }


def scene_slice(scene_doc: dict | None) -> dict:
    scene = (scene_doc or {}).get("scene") if isinstance(scene_doc, dict) else {}
    if not isinstance(scene, dict):
        scene = {}
    return {
        "id": scene.get("id"),
        "location": scene.get("location"),
        "summary": scene.get("summary"),
        "visible_facts": list(scene.get("visible_facts") or []),
        "hidden_facts": list(scene.get("hidden_facts") or []),
        "discoverable_clues": list(scene.get("discoverable_clues") or []),
        "exits": list(scene.get("exits") or []),
        "interactables": list(scene.get("interactables") or []),
    }


def faction_slice(world: dict | None) -> list:
    rows = []
    for faction in (world or {}).get("factions") or []:
        if isinstance(faction, dict):
            rows.append({
                "id": faction.get("id"),
                "agenda_progress": faction.get("agenda_progress"),
                "pressure": faction.get("pressure"),
            })
    return rows


def snapshot():
    session = storage.load_session()
    world = storage.load_world()
    scene = storage.load_scene(session["active_scene_id"])
    return {
        "temporal": temporal_slice(session),
        "scene": scene_slice(scene),
        "factions": faction_slice(world),
        "npc_ids": [n.get("id") for n in (world.get("npcs") or []) if isinstance(n, dict)],
    }


def wrap(fn, kind):
    def observed(*args, **kwargs):
        prior = dict(CURRENT)
        CURRENT.update(kind=kind, retry_attempt=kwargs.get("retry_attempt", 0))
        try:
            return fn(*args, **kwargs)
        finally:
            CURRENT.clear()
            CURRENT.update(prior)
    return observed


def observe_decision(resolution, **kwargs):
    result = original_attach(resolution, **kwargs)
    metadata = resolution.get("metadata") if isinstance(resolution, dict) else {}
    contract = metadata.get("resolution_contract") if isinstance(metadata, dict) else {}
    decision = metadata.get("gm_resolution_decision") if isinstance(metadata, dict) else {}
    if not isinstance(decision, dict):
        from game.gm_resolution_decision import DECISION_METADATA_KEY
        decision = metadata.get(DECISION_METADATA_KEY) if isinstance(metadata, dict) else {}
    session = kwargs.get("session") if isinstance(kwargs.get("session"), dict) else {}
    scene = kwargs.get("scene") if isinstance(kwargs.get("scene"), dict) else {}
    row = {
        "index": len(DECISIONS) + 1,
        "turn": CURRENT.get("turn"),
        "contract": contract if isinstance(contract, dict) else {},
        "decision": decision if isinstance(decision, dict) else {},
        "temporal": temporal_slice(session),
        "scene": scene_slice(scene),
    }
    DECISIONS.append(row)
    save("decisions.json", DECISIONS)
    save(f"{CURRENT.get('turn') or 'startup'}_decision_{row['index']}.json", row)
    return result


original_attach = live_resolution.attach_gm_resolution_decision
live_resolution.attach_gm_resolution_decision = observe_decision
api.call_gpt = wrap(api.call_gpt, "generation")
interpreter._invoke_interpretation_model = wrap(interpreter._invoke_interpretation_model, "interpretation")
preflight.run_upstream_api_preflight = wrap(preflight.run_upstream_api_preflight, "preflight")


def trace_bounded(frame, event, arg):
    if event == "call" and frame.f_code.co_name == "_bounded_keep":
        text = frame.f_locals.get("candidate_text", "")
        BOUNDED.append({
            "turn": CURRENT.get("turn"),
            "candidate_text": str(text)[:2000],
            "at": datetime.now(timezone.utc).isoformat(),
        })
        save("bounded_keep_invocations.json", BOUNDED)
    return trace_bounded


def observe_preserve(fn):
    def observed(*args, **kwargs):
        prior = sys.gettrace()
        sys.settrace(trace_bounded)
        try:
            return fn(*args, **kwargs)
        finally:
            sys.settrace(prior)
    return observed


immutable.run_preserve_if_valid = observe_preserve(immutable.run_preserve_if_valid)


def point_storage(sequence: str) -> None:
    base = OUT / f"isolated_{sequence}"
    storage.BASE_DIR = base
    storage.DATA_DIR = base / "data"
    storage.SCENES_DIR = storage.DATA_DIR / "scenes"
    for attr, filename in {
        "WORLD_PATH": "world.json",
        "SESSION_PATH": "session.json",
        "CAMPAIGN_PATH": "campaign.json",
        "CHARACTER_PATH": "character.json",
        "COMBAT_PATH": "combat.json",
        "CONDITIONS_PATH": "conditions.json",
        "SESSION_LOG_PATH": "session_log.jsonl",
    }.items():
        setattr(storage, attr, storage.DATA_DIR / filename)
    storage.SCENES_DIR.mkdir(parents=True, exist_ok=True)


def seed(sequence: str) -> None:
    point_storage(sequence)
    for base_sid in ("frontier_gate", "market_quarter", "old_milestone"):
        storage._save_json(storage.scene_path(base_sid), default_scene(base_sid))
    if sequence == "A":
        sid = "chapel_belfry"
        scene = default_scene(sid)
        scene["scene"].update(
            id=sid,
            location="Chapel belfry",
            summary="A bronze bell hangs from a timber frame.",
            visible_facts=[
                "The bell's wooden yoke is split.",
                "The bell's leather hanger is torn.",
            ],
            hidden_facts=[],
            discoverable_clues=[],
            exits=[],
            enemies=[],
            actions=[],
            interactables=[{
                "id": "chapel_bell",
                "label": "chapel bell",
                "aliases": ["bell", "wooden yoke", "yoke", "leather hanger", "hanger"],
            }],
        )
        world = default_world()
        world["npcs"] = []
    else:
        sid = "bread_stall"
        scene = default_scene(sid)
        scene["scene"].update(
            id=sid,
            location="Bread stall",
            summary="A baker stands at a bread stall.",
            visible_facts=["A baker stands beside loaves at a bread stall."],
            hidden_facts=[],
            discoverable_clues=[],
            exits=[],
            enemies=[],
            actions=[],
            addressables=[{
                "id": "baker",
                "name": "Baker",
                "scene_id": sid,
                "kind": "npc",
                "addressable": True,
                "address_priority": 0,
                "address_roles": ["baker", "vendor"],
                "aliases": ["baker"],
            }],
            interactables=[],
        )
        world = default_world()
        world["npcs"] = [{
            "id": "baker",
            "name": "Baker",
            "location": sid,
            "topics": [],
        }]
    session = default_session()
    session.update(active_scene_id=sid, visited_scene_ids=[sid], turn_counter=1)
    for path, value in [
        (storage.WORLD_PATH, world),
        (storage.SESSION_PATH, session),
        (storage.CAMPAIGN_PATH, default_campaign()),
        (storage.CHARACTER_PATH, default_character()),
        (storage.COMBAT_PATH, default_combat()),
        (storage.CONDITIONS_PATH, default_conditions()),
        (storage.scene_path(sid), scene),
    ]:
        storage._save_json(path, value)
    storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")
    save(f"setup_{sequence}.json", snapshot())


def wait_inbox() -> dict:
    inbox = OUT / "inbox.json"
    while True:
        if inbox.exists():
            try:
                data = json.loads(inbox.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                time.sleep(0.2)
                continue
            inbox.unlink(missing_ok=True)
            return data
        time.sleep(0.4)


def compact_contract(contract: dict) -> dict:
    return {
        "contract_id": contract.get("contract_id"),
        "operation": contract.get("operation"),
        "dimension": contract.get("dimension"),
        "dimensions": contract.get("dimensions"),
        "conversational_subject": contract.get("conversational_subject"),
        "target": contract.get("target"),
        "raw_input": contract.get("raw_input"),
        "epistemic_mode": contract.get("epistemic_mode"),
    }


def compact_decision(decision: dict) -> dict:
    return {
        "contract_id": decision.get("contract_id"),
        "outcome_classification": decision.get("outcome_classification"),
        "epistemic_acts": decision.get("epistemic_acts"),
        "realization_claims": decision.get("realization_claims"),
        "narration_constraints": decision.get("narration_constraints"),
        "unresolved_qualifiers": decision.get("unresolved_qualifiers"),
        "proposed_facts": decision.get("proposed_facts"),
    }


def main() -> None:
    if (OUT / "run_started.json").exists():
        raise SystemExit("Run already started. No reruns allowed.")
    save("run_started.json", {"utc": datetime.now(timezone.utc).isoformat(), "max_turns": MAX_TURNS})
    seed("A")
    status("STARTING")
    with TestClient(api.app) as client:
        save("preflight.json", preflight.get_latest_upstream_api_preflight())
        status("READY")
        expected = ["A1", "A2", "A3", "B1"]
        halt = None
        while True:
            command = wait_inbox()
            turn = str(command.get("turn") or "")
            if turn == "STOP":
                halt = halt or "operator stop"
                break
            if len(TURNS) >= MAX_TURNS:
                halt = "four-turn budget exhausted"
                break
            if not expected or turn != expected[0]:
                halt = f"Unexpected turn {turn}; expected {expected[0] if expected else 'none'}"
                save("command_error.json", {"got": command, "halt": halt})
                break
            expected.pop(0)
            if turn == "B1":
                seed("B")
            player = str(command.get("player") or "")
            CURRENT["turn"] = turn
            before = snapshot()
            decisions_at = len(DECISIONS)
            calls_at = len(CALLS)
            bounded_at = len(BOUNDED)
            row = {"turn": turn, "player": player, "before": before}
            TURNS.append(row)
            status(f"RUNNING {turn}")
            try:
                response = client.post("/api/chat", json={"text": player})
                payload = response.json()
                row.update(http_status=response.status_code, payload=payload, after=snapshot())
            except Exception:
                row.update(error=traceback.format_exc(), after=snapshot())
                payload = {}
            row["calls"] = CALLS[calls_at:]
            row["decisions"] = DECISIONS[decisions_at:]
            row["bounded_keep"] = BOUNDED[bounded_at:]
            gm = (row.get("payload") or {}).get("gm_output") or {}
            meta = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
            accepted = meta.get("accepted_response") if isinstance(meta.get("accepted_response"), dict) else {}
            review = meta.get("decision_review") if isinstance(meta.get("decision_review"), dict) else {}
            emitted = str(gm.get("player_facing_text") or "")
            sealed = accepted.get("text")
            gen = [c for c in row["calls"] if c.get("kind") == "generation"]
            parsed = []
            for call in gen:
                raw = call.get("raw_output") or ""
                save(f"{turn}_raw_envelope_attempt_{len(parsed) + 1}.json", {"raw_output": raw, "usage": call.get("usage"), "model": call.get("response_model") or call.get("model")})
                try:
                    parsed.append(_safe_json(raw, require_structured_claims=True))
                except Exception as exc:
                    parsed.append({"parse_error": f"{type(exc).__name__}: {exc}", "raw_output": raw})
            row["parsed_raw_attempts"] = parsed
            row.update(sealed=sealed, emitted=emitted, provenance=accepted.get("provenance"))
            first_decision = row["decisions"][0] if row["decisions"] else {}
            digest = {
                "turn": turn,
                "player": player,
                "http_status": row.get("http_status"),
                "error": row.get("error"),
                "emitted": emitted,
                "sealed": sealed,
                "c18_equal": sealed == emitted,
                "provenance": accepted.get("provenance"),
                "acceptance_why": (review.get("acceptance") or {}).get("why") if isinstance(review.get("acceptance"), dict) else None,
                "attempt_1_reasons": (review.get("attempt_1") or {}).get("reasons") if isinstance(review.get("attempt_1"), dict) else None,
                "attempt_2_reasons": (review.get("attempt_2") or {}).get("reasons") if isinstance(review.get("attempt_2"), dict) else None,
                "contract": compact_contract(first_decision.get("contract") or {}),
                "decision": compact_decision(first_decision.get("decision") or {}),
                "temporal_input": first_decision.get("temporal"),
                "temporal_output": row["after"]["temporal"],
                "scene_before": before["scene"],
                "scene_after": row["after"]["scene"],
                "factions_before": before["factions"],
                "factions_after": row["after"]["factions"],
                "bounded_keep_invoked": bool(row["bounded_keep"]),
                "bounded_keep": row["bounded_keep"],
                "generation_calls": len(gen),
                "interpretation_calls": sum(1 for c in row["calls"] if c.get("kind") == "interpretation"),
                "other_calls": sum(1 for c in row["calls"] if c.get("kind") not in {"generation", "interpretation", "preflight"}),
                "call_usage": [
                    {"kind": c.get("kind"), "model": c.get("response_model") or c.get("model"), "usage": c.get("usage"), "error": c.get("error")}
                    for c in row["calls"]
                ],
            }
            row["digest"] = digest
            mechanical = None
            if emitted.strip().startswith("{") or '"declared_claims"' in emitted:
                mechanical = "raw structured JSON reached player"
            elif sealed != emitted:
                mechanical = "C18 sealed/emitted exactness break"
            elif digest["acceptance_why"] == "bounded_sentence_preservation" or digest["bounded_keep_invoked"]:
                mechanical = "prose-only preservation escape"
            elif before["scene"]["visible_facts"] != row["after"]["scene"]["visible_facts"]:
                mechanical = "authored visible facts changed"
            elif before["scene"]["hidden_facts"] != row["after"]["scene"]["hidden_facts"] or before["scene"]["discoverable_clues"] != row["after"]["scene"]["discoverable_clues"]:
                mechanical = "hidden facts or clues changed"
            row["mechanical_stop"] = mechanical
            save(f"{turn}_full_trace.json", row)
            save(f"{turn}_digest.json", digest)
            save("turns.json", [{"turn": t["turn"], "player": t["player"], "emitted": t.get("emitted"), "mechanical_stop": t.get("mechanical_stop")} for t in TURNS])
            save("outbox.json", digest)
            if mechanical:
                halt = mechanical
                status(f"HALT {turn} {mechanical}")
                break
            status(f"DONE {turn}")
    save("run_finished.json", {
        "turns": [t["turn"] for t in TURNS],
        "halt": halt,
        "model_calls": len(CALLS),
        "http_attempts": len(HTTP),
        "bounded_keep": len(BOUNDED),
    })
    status("FINISHED")


if __name__ == "__main__":
    main()
