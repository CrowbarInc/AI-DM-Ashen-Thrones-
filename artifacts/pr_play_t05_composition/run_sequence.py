"""Provider-free continuation for the post-AT-OPT gameplay evaluation.

Seeds the established frontier-gate campaign as already started. Does not call
the campaign-opening route. Provider clients and non-local sockets are blocked.
Writes only under artifacts/pr_play_post_opt/.
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
OUT = Path(__file__).resolve().parent/sys.argv[1]/"twelve_turn"
OUT.mkdir(parents=True,exist_ok=True)
DATA = OUT / "run_data"
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
    {
        "id": "T01",
        "category": "scene_inspection",
        "text": "I stop under the gate and look around. What is actually in front of me?",
    },
    {
        "id": "T02",
        "category": "npc_interaction",
        "text": "Gate Guard, do you have a moment?",
    },
    {
        "id": "T03",
        "category": "follow_up",
        "text": "You mentioned the patrol. What have you heard?",
    },
    {
        "id": "T04",
        "category": "physical_interaction",
        "text": "I walk over to the notice board and put a hand on the frame.",
    },
    {
        "id": "T05",
        "category": "investigation",
        "text": "Read me the missing-patrol notice, not the tax lines.",
    },
    {
        "id": "T06",
        "category": "improvisation",
        "text": "I try to copy the patrol warning onto my sleeve with a bit of mud so I won't forget the wording.",
    },
    {
        "id": "T07",
        "category": "ambiguous_request",
        "text": "Handle it.",
    },
    {
        "id": "T08",
        "category": "player_agency",
        "text": "Don't send me anywhere yet. I'll choose after I know what the board actually says.",
    },
    {
        "id": "T09",
        "category": "recall",
        "text": "What did that notice say about where the patrol was last seen?",
    },
    {
        "id": "T10",
        "category": "unexpected_request",
        "text": "Can I trade my dry cloak for the tavern runner's stew?",
    },
    {
        "id": "T11",
        "category": "scene_progression",
        "text": "I follow the missing patrol rumor toward the northwest track.",
    },
    {
        "id": "T12",
        "category": "retreat",
        "text": "I step back from the notice board.",
    },
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


def _state():
    from game import storage

    session = storage.load_session() or {}
    world = storage.load_world() or {}
    flags = ((world.get("world_state") or {}).get("flags") or {}) if isinstance(world, dict) else {}
    ledger = session.get("bounded_improvisation_ledger") if isinstance(session.get("bounded_improvisation_ledger"), dict) else {}
    position = ledger.get("position") if isinstance(ledger.get("position"), dict) else {}
    pointer = session.get("last_publication") if isinstance(session.get("last_publication"), dict) else {}
    clues = session.get("discovered_clues")
    clue_ids = []
    if isinstance(clues, list):
        for item in clues:
            if isinstance(item, dict):
                clue_ids.append(item.get("id") or item.get("text"))
            else:
                clue_ids.append(item)
    return {
        "scene_id": session.get("active_scene_id"),
        "visited_scene_ids": list(session.get("visited_scene_ids") or []),
        "turn_counter": session.get("turn_counter"),
        "campaign_started": session.get("campaign_started"),
        "publication_visible": pointer.get("visible"),
        "publication_contract": pointer.get("contract"),
        "dialogue_accepted": pointer.get("dialogue_accepted"),
        "position_kind": position.get("kind"),
        "discovered_clues": clue_ids,
        "patrol_survey": flags.get("patrol_survey"),
        "patrol_report": flags.get("patrol_report"),
        "log_entries": len(storage.load_log() or []),
    }


def _log_tail():
    from game import storage

    log = storage.load_log() or []
    if not log or not isinstance(log[-1], dict):
        return {}
    row = log[-1]
    resolution = row.get("resolution") if isinstance(row.get("resolution"), dict) else {}
    meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    log_meta = row.get("log_meta") if isinstance(row.get("log_meta"), dict) else {}
    gm = row.get("gm_output") if isinstance(row.get("gm_output"), dict) else {}
    if not gm and isinstance(row.get("gm"), dict):
        gm = row["gm"]
    tags = gm.get("tags") if isinstance(gm.get("tags"), list) else []
    transition = resolution.get("transition") if isinstance(resolution.get("transition"), dict) else {}
    return {
        "player_text": row.get("player_text") or row.get("text"),
        "kind": resolution.get("kind"),
        "success": resolution.get("success"),
        "resolved_transition": resolution.get("resolved_transition"),
        "target_scene_id": resolution.get("target_scene_id"),
        "response_class": meta.get("response_class") or log_meta.get("response_class"),
        "refusal_category": meta.get("refusal_category"),
        "failure_stage": meta.get("failure_stage"),
        "publication_contract": meta.get("publication_contract"),
        "gameplay_publication_completed": meta.get("gameplay_publication_completed"),
        "provider_request_sent": meta.get("provider_request_sent"),
        "skip_primary_narration": meta.get("skip_primary_narration"),
        "route": meta.get("route") or meta.get("parser_lane") or meta.get("owner"),
        "transition_required": transition.get("transition_required"),
        "transition_type": transition.get("transition_type"),
        "tags": [str(tag) for tag in tags if isinstance(tag, str)][:12],
        "log_meta_keys": sorted(log_meta.keys())[:40],
        "metadata_keys": sorted(meta.keys())[:40],
    }


def _events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            rows.append(json.loads(line))
    return rows


def main() -> None:
    from game.verification_budget import VerificationBudgetRejected, apply_verification_budget, resolve_verification_budget
    from game.provider_budget import ProviderBudgetRefused, admit_request, limits
    import game.provider_budget as budget
    import game.gm as gm_mod
    import game.api as api_mod

    calls = []
    admissions = []
    network = []
    real_connect = socket.create_connection

    def guarded_connect(address, *args, **kwargs):
        host = address[0] if isinstance(address, tuple) else str(address)
        if host not in {"127.0.0.1", "localhost", "::1"}:
            network.append(host)
            raise OSError(f"blocked non-local connect to {host}")
        return real_connect(address, *args, **kwargs)

    socket.create_connection = guarded_connect

    class BlockedClient:
        def __init__(self, *args, **kwargs):
            network.append("openai.OpenAI")
            raise RuntimeError("live provider client blocked")

    try:
        import openai

        openai.OpenAI = BlockedClient
    except Exception:
        openai = None

    original_call = gm_mod.call_gpt

    def counting_call(*args, **kwargs):
        started = time.perf_counter()
        calls.append({"entered": True, "purpose": kwargs.get("purpose")})
        try:
            result = original_call(*args, **kwargs)
        except Exception as exc:
            calls[-1]["error"] = type(exc).__name__
            calls[-1]["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 3)
            raise
        meta = result.get("metadata") if isinstance(result, dict) else {}
        accounting = meta.get("provider_accounting") if isinstance(meta, dict) else {}
        calls[-1]["elapsed_ms"] = round((time.perf_counter() - started) * 1000, 3)
        calls[-1]["disabled"] = bool(meta.get("provider_calls_disabled")) if isinstance(meta, dict) else None
        calls[-1]["request_count"] = accounting.get("request_count") if isinstance(accounting, dict) else None
        calls[-1]["tags"] = list(result.get("tags") or [])[:8] if isinstance(result, dict) else []
        return result

    gm_mod.call_gpt = counting_call
    api_mod.call_gpt = counting_call

    original_admit = budget.admit_request

    def counting_admit(**kwargs):
        attempt = original_admit(**kwargs)
        admissions.append({
            "purpose": kwargs.get("purpose"),
            "owner": kwargs.get("owner"),
            "estimated_input": kwargs.get("estimated_input"),
            "max_output": kwargs.get("max_output"),
            "refusal": attempt.refusal,
            "dispatched": attempt.dispatched,
        })
        return attempt

    budget.admit_request = counting_admit

    record = apply_verification_budget()
    ceiling = limits()
    rejected_historical = False
    try:
        resolve_verification_budget(total=200000)
    except VerificationBudgetRejected:
        rejected_historical = True
    oversized_sent = {"n": 0}

    def oversized_invoke():
        oversized_sent["n"] += 1
        raise AssertionError("oversized request reached dispatch")

    oversized = counting_admit(purpose="primary_turn", owner="preflight", estimated_input=28000, max_output=600)
    oversized_error = None
    try:
        oversized.dispatch(oversized_invoke)
    except ProviderBudgetRefused as exc:
        oversized_error = type(exc).__name__
    within_sent = {"n": 0}

    def within_invoke():
        within_sent["n"] += 1
        return type("Usage", (), {"usage": type("U", (), {"input_tokens": 11, "output_tokens": 3, "total_tokens": 14})(), "id": "local-stub", "model": "local-stub"})()

    within = counting_admit(purpose="expression", owner="preflight", estimated_input=100, max_output=40)
    within_error = None
    try:
        within.dispatch(within_invoke)
    except Exception as exc:
        within_error = type(exc).__name__

    preflight = {
        "verification_budget": record,
        "limits": list(ceiling) if ceiling is not None else None,
        "historical_200000_rejected": rejected_historical,
        "ceiling_after_rejection": list(limits()) if limits() is not None else None,
        "oversized_estimated_input": 28000,
        "oversized_refusal": oversized.refusal,
        "oversized_dispatched": oversized.dispatched,
        "oversized_invoke_calls": oversized_sent["n"],
        "oversized_error": oversized_error,
        "within_budget_refusal": within.refusal,
        "within_budget_dispatched": within.dispatched,
        "within_budget_local_stub_calls": within_sent["n"],
        "within_budget_error": within_error,
        "live_provider_calls": 0,
    }
    (OUT / "preflight.json").write_text(json.dumps(preflight, indent=2), encoding="utf-8")

    from tests.helpers.storage_isolation import install
    from tests.pr_play_79df3_harness import seed_gate
    from fastapi.testclient import TestClient
    from game import storage
    from game.config import DEFAULT_MODEL_NAME, MODEL_NAME

    install(DATA)
    seed_gate(DATA, _Monkey())
    events_path = OUT / "publication_events.jsonl"
    if events_path.exists():
        events_path.unlink()
    os.environ["ASHEN_PUBLICATION_TRACE_PATH"] = str(events_path)
    os.environ["ASHEN_PROVIDER_USAGE_PATH"] = str(DATA / "provider_usage.jsonl")
    budget._REQUESTS = 0
    budget._STOPPED = False
    budget._STOP_REASON = ""
    budget._INITIALIZED = False
    budget._INPUT = 0
    budget._OUTPUT = 0
    budget._RESERVED_INPUT = 0
    budget._RESERVED_OUTPUT = 0
    budget._USAGE_KNOWN = True
    budget._LEDGER_PATH = None
    budget._EVENTS.clear()
    budget._ATTEMPTS.clear()
    budget._RECORDS.clear()

    import copy
    import game.response_policy_enforcement as policy
    import game.diegetic_fallback_narration as diegetic
    import game.immutable_valid_response as ivr
    traces = []
    active_turn = {}
    def wrap(module, name):
        original = getattr(module, name)
        def traced(*args, **kwargs):
            entry = {"turn": active_turn.get("id"), "function": module.__name__+"."+name,
                     "args": copy.deepcopy(args), "kwargs": copy.deepcopy(kwargs)}
            traces.append(entry)
            value = original(*args, **kwargs)
            entry["result"] = copy.deepcopy(value)
            return value
        setattr(module, name, traced)
    for module, names in [(policy, ["enforce_scene_momentum", "apply_response_policy_enforcement"]),
                          (diegetic, ["render_scene_momentum_diegetic_append"]),
                          (ivr, ["validate_generated_response", "seal_accepted_response", "run_preserve_if_valid"])]:
        for name in names: wrap(module, name)
    def full_state():
        return copy.deepcopy({"session": storage.load_session(), "character": storage.load_character(),
                              "world": storage.load_world(), "log": storage.load_log()})
    rows = []
    call_cursor = 0
    admit_cursor = 2
    with TestClient(api_mod.app) as client:
        for turn in TURNS:
            active_turn.update(turn)
            full_before = full_state()
            before = _state()
            before_requests = budget.snapshot().get("requests") or 0
            started = time.perf_counter()
            error = None
            body = None
            status = None
            try:
                response = client.post(
                    "/api/chat?ui_mode=player",
                    json={"text": turn["text"], "client_request_id": turn["id"]},
                )
                status = response.status_code
                body = response.json()
            except Exception as exc:
                error = {"type": type(exc).__name__, "message": str(exc)[:500], "trace": traceback.format_exc()[-1500:]}
            elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
            after = _state()
            visible = ""
            if isinstance(body, dict):
                visible = str((body.get("gm_output") or {}).get("player_facing_text") or "")
            new_calls = calls[call_cursor:]
            call_cursor = len(calls)
            new_admits = admissions[admit_cursor:]
            admit_cursor = len(admissions)
            new_events = _events(events_path)
            rows.append({
                "full_before": full_before,
                "full_after": full_state(),
                "http_response": body,
                "id": turn["id"],
                "category": turn["category"],
                "player_text": turn["text"],
                "status": status,
                "ok": body.get("ok") if isinstance(body, dict) else None,
                "visible": visible,
                "elapsed_ms": elapsed_ms,
                "error": error,
                "before": before,
                "after": after,
                "state_changed": before != after,
                "scene_changed": before.get("scene_id") != after.get("scene_id"),
                "turn_changed": before.get("turn_counter") != after.get("turn_counter"),
                "publication_changed": before.get("publication_visible") != after.get("publication_visible"),
                "log": _log_tail(),
                "call_gpt_entries": new_calls,
                "admissions": new_admits,
                "provider_requests_before": before_requests,
                "provider_requests_after": budget.snapshot().get("requests") or 0,
                "publication_event_count": len(new_events),
                "latest_publication_event": new_events[-1].get("final_player_facing_response") if new_events else None,
                "provider_output_class": "deterministic_engine",
            })
            print(json.dumps({
                "id": turn["id"],
                "status": status,
                "ms": elapsed_ms,
                "scene": after.get("scene_id"),
                "turn": after.get("turn_counter"),
                "class": rows[-1]["log"].get("response_class"),
                "calls": len(new_calls),
                "visible": visible[:180],
            }, ensure_ascii=False), flush=True)

    summary = {
        "milestone": "PR-PLAY post-optimization gameplay evaluation",
        "pr_play_80_opened": False,
        "provider_mode": "deterministic_engine_provider_calls_disabled",
        "live_provider_calls": 0,
        "network_blocks": network,
        "openai_client_constructed": "openai.OpenAI" in network,
        "call_gpt_entries": len(calls),
        "gameplay_admissions_after_preflight": admissions[2:],
        "preflight_admissions": admissions[:2],
        "provider_requests": budget.snapshot().get("requests") or 0,
        "provider_tokens": budget.snapshot().get("total_tokens") or 0,
        "model_name_configured": bool(MODEL_NAME),
        "default_model_name": DEFAULT_MODEL_NAME,
        "model_name_is_default_family": str(DEFAULT_MODEL_NAME).startswith("gpt-"),
        "api_key_present_after_pop": bool(os.environ.get("OPENAI_API_KEY")),
        "physical_adjudication": os.environ.get("ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION"),
        "dynamic_npcs": os.environ.get("ASHEN_EXPERIMENTAL_DYNAMIC_NPCS"),
        "player_initiative": os.environ.get("ASHEN_EXPERIMENTAL_PLAYER_INITIATIVE"),
        "world_improvisation": os.environ.get("ASHEN_EXPERIMENTAL_WORLD_IMPROVISATION"),
        "interpretation_disabled": os.environ.get("ASHEN_DISABLE_LIVE_INTERPRETATION"),
        "expression_disabled": os.environ.get("ASHEN_DISABLE_EXPRESSION_GENERATION"),
        "provider_calls_disabled": os.environ.get("ASHEN_DISABLE_PROVIDER_CALLS"),
        "verification_total": os.environ.get("ASHEN_VERIFICATION_BUDGET_TOTAL"),
        "turns": len(rows),
        "final_state": rows[-1]["after"] if rows else None,
    }
    (OUT / "stage_trace.json").write_text(json.dumps(traces, indent=2, default=str), encoding="utf-8")
    (OUT / "turns.json").write_text(json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUT / "sequence_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({k: summary[k] for k in ("turns", "live_provider_calls", "call_gpt_entries", "provider_requests", "network_blocks")}, indent=2))


if __name__ == "__main__":
    main()
