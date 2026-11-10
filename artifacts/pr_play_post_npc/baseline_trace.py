"""Provider-free decision trace for the post-NPC handoff failures.

Replays the recorded twelve utterances on the seeded frontier-gate campaign.
Does not call a live provider. Writes only under artifacts/pr_play_post_npc/.
"""
from __future__ import annotations

import json
import os
import socket
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
LABEL = sys.argv[1] if len(sys.argv) > 1 else "baseline"
DATA = OUT / f"{LABEL}_run"
sys.path.insert(0, str(ROOT))

os.environ["ASHEN_TEST_EVIDENCE_DIR"] = str(OUT)
os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "1"
os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_RETRIES"] = "1"
os.environ.pop("ASHEN_PLAYTEST_DISABLE_SDK_RETRIES", None)
os.environ.pop("ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION", None)
os.environ.pop("ASHEN_EXPERIMENTAL_DYNAMIC_NPCS", None)
os.environ.pop("ASHEN_EXPERIMENTAL_PLAYER_INITIATIVE", None)
os.environ.pop("ASHEN_EXPERIMENTAL_WORLD_IMPROVISATION", None)
os.environ.pop("OPENAI_API_KEY", None)

TURNS = [
    ("T01", "I stop under the gate and look around. What is actually in front of me?"),
    ("T02", "Gate Guard, do you have a moment?"),
    ("T03", "You mentioned the patrol. What have you heard?"),
    ("T04", "I walk over to the notice board and put a hand on the frame."),
    ("T05", "Read me the missing-patrol notice, not the tax lines."),
    ("T06", "I try to copy the patrol warning onto my sleeve with a bit of mud so I won't forget the wording."),
    ("T07", "Handle it."),
    ("T08", "Don't send me anywhere yet. I'll choose after I know what the board actually says."),
    ("T09", "What did that notice say about where the patrol was last seen?"),
    ("T10", "Can I trade my dry cloak for the tavern runner's stew?"),
    ("T11", "I follow the missing patrol rumor toward the northwest track."),
    ("T12", "I step back from the notice board."),
]


class _Monkey:
    def setenv(self, key, value):
        os.environ[key] = str(value)

    def delenv(self, key, raising=True):
        if key not in os.environ and raising:
            raise KeyError(key)
        os.environ.pop(key, None)

    def setattr(self, target, name, value, raising=True):
        if isinstance(target, str):
            module_name, attr = target.rsplit(".", 1)
            module = sys.modules[module_name]
            setattr(module, attr, value)
            return
        setattr(target, name, value)


def _decision_view(decision):
    if decision is None:
        return None
    category = getattr(decision, "category", None)
    return {
        "category": getattr(category, "value", str(category)),
        "reason": getattr(decision, "reason", None),
        "family": getattr(decision, "intent_family", None),
        "operation": getattr(decision, "proposed_operation", None),
        "target": getattr(decision, "proposed_target", None),
        "facing": getattr(decision, "player_facing_text", None),
        "policy": getattr(decision, "execution_policy", None),
        "references": list(getattr(decision, "context_references", None) or [])[:8],
    }


def main() -> None:
    import game.api as api_mod
    import game.conversational_continuity as continuity
    import game.conversational_orchestration as orch
    import game.gm as gm_mod
    import game.live_chat_interpretation as live
    import game.player_interpretation_bridge as bridge
    import game.unified_semantic_planning as planning

    traces: list[dict] = []
    current = {"id": None}

    real_continuity = continuity.continuity_directive
    real_decision = orch.deterministic_conversational_decision
    real_bridge = bridge.normalized_action_from_interpretation
    real_interpret = live.interpret_production_turn
    real_plan = planning.planning_decision

    def traced_continuity(player_text, **kwargs):
        directive = real_continuity(player_text, **kwargs)
        traces.append({
            "turn": current["id"],
            "stage": "continuity_directive",
            "text": player_text,
            "directive": None if directive is None else {
                "action": directive.get("action"),
                "reason": directive.get("reason"),
                "owner": directive.get("owner"),
                "npc_id": directive.get("npc_id"),
                "line": str(directive.get("line") or "")[:240],
            },
        })
        return directive

    def traced_plan(**kwargs):
        decision = real_plan(**kwargs)
        traces.append({
            "turn": current["id"],
            "stage": "planning_decision",
            "text": kwargs.get("player_text"),
            "decision": _decision_view(decision),
        })
        return decision

    def traced_decision(**kwargs):
        text = kwargs.get("player_text") or ""
        scene = kwargs.get("scene")
        world = kwargs.get("world")
        session = kwargs.get("session")
        clause = None
        grounded = None
        try:
            exits = orch._exit_rows(scene)
            analyzed = orch._analyze_clause(text, exits)
            destination = str(analyzed.get("destination") or "")
            catalog = orch._catalog(scene, world)
            hits = orch._ground_catalog_target(
                destination, catalog, {"npc", "inspect_target", "perceive_target"},
            ) if destination else []
            clause = {
                "operation": analyzed.get("operation"),
                "destination": destination,
                "consequential": analyzed.get("consequential"),
                "purpose": analyzed.get("purpose"),
            }
            grounded = [{"id": item[0], "kind": item[1].get("kind")} for item in hits]
        except Exception as exc:
            clause = {"error": type(exc).__name__ + ": " + str(exc)[:200]}
        ctx = session.get("conversational_context") if isinstance(session, dict) else {}
        interaction = session.get("interaction_context") if isinstance(session, dict) else {}
        decision = real_decision(**kwargs)
        traces.append({
            "turn": current["id"],
            "stage": "deterministic_conversational_decision",
            "text": text,
            "clause": clause,
            "destination_grounded_as_local": grounded,
            "active_interaction_target": (interaction or {}).get("active_interaction_target_id") if isinstance(interaction, dict) else None,
            "delivered_count": len((ctx or {}).get("delivered_exchanges") or []) if isinstance(ctx, dict) else 0,
            "decision": _decision_view(decision),
        })
        return decision

    def traced_bridge(record, **kwargs):
        action, meta = real_bridge(record, **kwargs)
        components = []
        if isinstance(record, dict):
            for component in record.get("action_components") or []:
                if isinstance(component, dict):
                    components.append({
                        "operation": component.get("operation_class"),
                        "target": component.get("target_ref"),
                    })
        traces.append({
            "turn": current["id"],
            "stage": "normalized_action_from_interpretation",
            "text": kwargs.get("player_text"),
            "components": components,
            "accepted": meta.get("accepted") if isinstance(meta, dict) else None,
            "reason": meta.get("reason") if isinstance(meta, dict) else None,
            "operation": meta.get("operation") if isinstance(meta, dict) else None,
            "target_ref": meta.get("target_ref") if isinstance(meta, dict) else None,
            "engine_type": meta.get("engine_type") if isinstance(meta, dict) else None,
            "action_type": action.get("type") if isinstance(action, dict) else None,
            "action_id": action.get("id") if isinstance(action, dict) else None,
        })
        return action, meta

    def traced_interpret(**kwargs):
        outcome = real_interpret(**kwargs)
        record = outcome.get("record") if isinstance(outcome, dict) else None
        components = []
        if isinstance(record, dict):
            for component in record.get("action_components") or []:
                if isinstance(component, dict):
                    components.append({
                        "operation": component.get("operation_class"),
                        "target": component.get("target_ref"),
                    })
        traces.append({
            "turn": current["id"],
            "stage": "interpret_production_turn",
            "text": kwargs.get("player_text"),
            "status": outcome.get("status") if isinstance(outcome, dict) else None,
            "reason": outcome.get("reason") if isinstance(outcome, dict) else None,
            "components": components,
        })
        return outcome

    continuity.continuity_directive = traced_continuity
    planning.planning_decision = traced_plan
    api_mod.deterministic_conversational_decision = traced_decision
    api_mod.normalized_action_from_interpretation = traced_bridge
    api_mod.interpret_production_turn = traced_interpret

    calls = []
    real_connect = socket.create_connection

    def guarded_connect(address, *args, **kwargs):
        host = address[0] if isinstance(address, tuple) else str(address)
        if host not in {"127.0.0.1", "localhost", "::1"}:
            raise OSError(f"blocked non-local connect to {host}")
        return real_connect(address, *args, **kwargs)

    socket.create_connection = guarded_connect
    try:
        import openai
        openai.OpenAI = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("live provider client blocked"))
    except Exception:
        pass

    original_call = gm_mod.call_gpt

    def counting_call(*args, **kwargs):
        calls.append(kwargs.get("purpose"))
        return original_call(*args, **kwargs)

    gm_mod.call_gpt = counting_call
    api_mod.call_gpt = counting_call

    from game.verification_budget import apply_verification_budget
    from tests.helpers.storage_isolation import install
    from tests.pr_play_79df3_harness import seed_gate
    from fastapi.testclient import TestClient
    from game import storage

    apply_verification_budget()
    install(DATA)
    seed_gate(DATA, _Monkey())
    rows = []
    with TestClient(api_mod.app) as client:
        for turn_id, text in TURNS:
            current["id"] = turn_id
            before = len(traces)
            started = time.perf_counter()
            response = client.post("/api/chat?ui_mode=player", json={"text": text, "client_request_id": turn_id})
            body = response.json()
            visible = str((body.get("gm_output") or {}).get("player_facing_text") or "")
            session = storage.load_session() or {}
            log = storage.load_log() or []
            resolution = log[-1].get("resolution") if log and isinstance(log[-1], dict) else {}
            meta = resolution.get("metadata") if isinstance(resolution, dict) else {}
            rows.append({
                "id": turn_id,
                "player_text": text,
                "status": response.status_code,
                "visible": visible,
                "elapsed_ms": round((time.perf_counter() - started) * 1000, 3),
                "scene_id": session.get("active_scene_id"),
                "turn_counter": session.get("turn_counter"),
                "publication": (session.get("last_publication") or {}).get("visible") if isinstance(session.get("last_publication"), dict) else None,
                "kind": resolution.get("kind") if isinstance(resolution, dict) else None,
                "response_class": (meta or {}).get("response_class"),
                "refusal_category": (meta or {}).get("refusal_category"),
                "stages": traces[before:],
            })
            print(json.dumps({"id": turn_id, "visible": visible[:160], "stages": len(rows[-1]["stages"])}, ensure_ascii=False), flush=True)
    payload = {
        "live_provider_calls": 0,
        "call_gpt_entries": calls,
        "turns": rows,
    }
    (OUT / f"{LABEL}_trace.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise
