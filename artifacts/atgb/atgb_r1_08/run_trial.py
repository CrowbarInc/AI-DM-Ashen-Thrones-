"""Bounded R1-08 evidence runner; never imports the historical runner or tests."""
import copy
import dataclasses
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")


def normalize(value):
    if dataclasses.is_dataclass(value):
        return normalize(dataclasses.asdict(value))
    if isinstance(value, dict):
        return {str(k): normalize(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [normalize(v) for v in value]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def main(label, preview=False):
    assert label in {"L1", "L2", "L3", "L4"}
    # A parent must inspect each result before manually starting the next process.
    previous = [json.loads(p.read_text()) for p in OUT.glob("L*/accounting.json")]
    assert sum(p["requests"] for p in previous) < 4
    assert all(not p["stopped"] and p["pending_requests"] == 0 and p["total_tokens"] is not None for p in previous)
    assert not preview, "No preview execution in measured runner"
    for prior in OUT.glob("L*/state_integrity.json"):
        integrity = json.loads(prior.read_text())
        assert all(integrity["unchanged"][k] for k in ("world", "scene", "character", "combat")), "prior_authority_failure"
        assert all(integrity["unchanged_session_fields"].values()), "prior_time_failure"
    for prior in OUT.glob("L*/preflight.json"):
        assert not json.loads(prior.read_text())["failed_assertions"], "prior_preflight_failure"
    dest = OUT / label
    dest.mkdir(exist_ok=False)
    inherited = {k: v for k, v in os.environ.items() if k.startswith("ASHEN_")}
    # Record names only; configuration secrets are never dumped.
    write(dest / "inherited_environment_names.json", sorted(inherited))
    experimental = {k: os.environ.get(k) for k in ("ASHEN_UNIFIED_SEMANTIC_PLANNING", "ASHEN_HOST_CONSTRAINED_CANDIDATES")}
    assert all(v in (None, "", "0", "false", "False") for v in experimental.values()), "unexpected_experimental_flag"
    for key, value in {
        "ASHEN_DISABLE_LIVE_INTERPRETATION": "0", "ASHEN_DISABLE_PROVIDER_CALLS": "0",
        "ASHEN_DISABLE_PROVIDER_RETRIES": "1", "ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT": "1",
        "ASHEN_PROVIDER_REQUEST_LIMIT": "1", "ASHEN_PROVIDER_INPUT_TOKEN_LIMIT": "16000",
        "ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT": "2000", "ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT": "18000",
        "ASHEN_PROVIDER_USAGE_PATH": str(dest / "provider_usage.jsonl"),
    }.items():
        os.environ[key] = value
    # Token ceilings permit the existing pathway; admission ceiling is one.
    from tools.atgb import readiness as r
    from tools.atgb.baseline import load_baseline
    from tools.atgb.isolation import prepare_isolated_store
    from pytest import MonkeyPatch
    imports_before = r.flag_snapshot()
    load_baseline(ROOT)
    if label in {"L1", "L2", "L3"}:
        store = prepare_isolated_store(dest / "store", scenario_id="S08")
        os.environ["ASHEN_DATA_DIR"] = str(store)
    else:
        # Bind every storage path to a safe directory before importing gameplay.
        os.environ["ASHEN_DATA_DIR"] = str(dest / "control/data")
    import openai
    sdk_clients = []
    actual_openai = openai.OpenAI

    class NoRetryOpenAI(actual_openai):
        def __init__(self, *args, **kwargs):
            kwargs["max_retries"] = 0
            super().__init__(*args, **kwargs)
            sdk_clients.append({"max_retries": self.max_retries})
            assert self.max_retries == 0

    openai.OpenAI = NoRetryOpenAI
    from game import storage, provider_budget as budget
    from game.api import chat
    from game.models import ChatRequest
    from game import live_chat_interpretation as live
    patch = MonkeyPatch()
    # Storage imported while bound to the isolated directory. Restore the active
    # player-directory environment for the readiness guard, as in R1-04's scoped
    # storage fixture. This does not change the already imported storage paths.
    if "ASHEN_DATA_DIR" in inherited:
        os.environ["ASHEN_DATA_DIR"] = inherited["ASHEN_DATA_DIR"]
    else:
        os.environ.pop("ASHEN_DATA_DIR", None)
    experimental = {k: os.environ.get(k) for k in experimental}
    assert all(v in (None, "", "0", "false", "False") for v in experimental.values())
    assert os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1").rstrip("/") == "https://api.openai.com/v1"

    def state():
        return copy.deepcopy(dict(session=storage.load_session(), world=storage.load_world(),
            scene=storage.load_active_scene(), character=storage.load_character(),
            combat=storage.load_combat(), log=storage.load_log()))

    if label in {"L1", "L2", "L3"}:
        # Replay preserved reconstructed S08.1 context, not an S08.2 result.
        source = ROOT / "artifacts/atgb/atgb_r1_03/L1"
        base = json.loads((source / "before.json").read_text(encoding="utf-8"))
        assert len(base["log"]) == 1
        assert not (base["session"].get("conversational_context") or {}).get("pending_intention")
        for key in ("world", "character", "combat"):
            storage._save_json(getattr(storage, key.upper() + "_PATH"), base[key])
        session = copy.deepcopy(base["session"])
        # Fresh runtime identities; semantic context is preserved verbatim.
        for key in ("session_id", "campaign_run_id"):
            if key in session:
                session[key] = uuid.uuid4().hex
        storage.save_session(session)
        storage.save_scene(base["scene"])
        storage.SESSION_LOG_PATH.write_text("".join(json.dumps(row) + "\n" for row in base["log"]), encoding="utf-8")
        write(dest / "setup.json", {**json.loads((source / "setup.json").read_text()),
            "data_dir": str(store), "source": "R1-03 preserved S08.1 reconstruction, independent copy",
            "historical_equivalence": "not bit-identical; reconstructed intermediate session and fresh runtime identity"})
        text = "No, I was asking about the people, not the weather." if label == "L3" else "I meant the people, not the weather."
    else:
        store = r.seed_control(dest / "control", patch)
        write(dest / "setup_before.json", state())
        # This is the R1-04 deterministic setup only. The measured correction is live.
        ask = {"communication_mode": "OTHER", "interpretation_status": "INTERPRETED",
            "player_intent": {"summary": "Ask one of them what happened"}, "asserted_premises": [],
            "requested_outcomes": [], "action_components": [{"order": 1, "description": "Ask one of them", "operation_class": "ASK", "target_ref": "sergeant_mara"}],
            "references": {"permitted_entity_ids": ["sergeant_mara"], "unresolved_references": []},
            "clarification_question": "", "correction": {"subject": "NONE", "note": ""},
            "communication": {"recipient": "NPC", "purpose": "QUESTION", "subject": "road", "evidence_refs": []}}
        live._contract()
        with MonkeyPatch.context() as setup_patch:
            setup_patch.setattr(live, "request_interpretation", lambda *a, **k: {"ok": True, "sent": False, "text": json.dumps(ask)})
            write(dest / "setup_response.json", chat(ChatRequest(text="I ask one of them what happened.")))
        text = "Instead, make that a question about the lamp."
    budget.initialize_accounting()
    before = state()
    write(dest / "before.json", before)
    write(dest / "configuration.json", {"provider": "OpenAI Responses", "model": "gpt-4.1-mini",
        "sdk_max_retries": 0, "application_retries": 0, "automatic_trial_retries": 0,
        "experimental_flags": experimental, "pid": os.getpid(), "input": text,
        "pass_prior_admissions": sum(p["requests"] for p in previous),
        "token_limits": budget.limits(), "production_request_interpretation_restored": live.request_interpretation.__module__ == "game.live_chat_interpretation"})
    traces = []
    functions = {"request_interpretation", "interpret_production_turn", "_pending_revision_decision",
        "_communication_decision", "decision_from_interpretation_record", "public_conversation_evidence",
        "decision_from_bridge_rejection", "assess_addressee_grounding", "authorize_information_turn",
        "planning_decision", "bind", "_blocked"}
    local_keys = {"messages", "estimated_input", "evidence", "raw", "parsed", "record", "call",
        "communication", "pending", "executed", "purpose", "components", "answer", "selected",
        "refs", "reason", "leaks", "player_text", "text", "grounding"}

    def profile(frame, event, value):
        name = frame.f_code.co_name
        if event == "return" and name in functions and str(ROOT) in frame.f_code.co_filename:
            traces.append({"function": name, "file": str(Path(frame.f_code.co_filename).relative_to(ROOT)),
                "line": frame.f_code.co_firstlineno, "return": normalize(value),
                "locals": {k: normalize(v) for k, v in frame.f_locals.items() if k in local_keys}})

    def execute():
        if preview:
            def capture_only(messages, *, estimated_input):
                write(dest / "request_payload.json", {"destination": "https://api.openai.com/v1/responses",
                    "model": "gpt-4.1-mini", "input": messages, "temperature": 0,
                    "max_output_tokens": live._OUTPUT_CAP,
                    "text": {"format": {"type": "json_schema", "name": "pr_dr_interpretation", "strict": True,
                        "schema": live.production_interpretation_schema()}},
                    "estimated_input_tokens": estimated_input,
                    "preview_only": True, "provider_admissions": 0})
                return {"ok": False, "sent": False, "reason": "offline_payload_preview"}
            patch.setattr(live, "request_interpretation", capture_only)
        sys.setprofile(profile)
        try:
            return chat(ChatRequest(text=text))
        finally:
            sys.setprofile(None)

    start = time.perf_counter()
    try:
        response = r.guarded_trial(evidence_path=dest / "preflight.json", execute=execute,
            live=True, model="gpt-4.1-mini", limit=1, store=store,
            **{k: before[k] for k in ("session", "scene", "world", "character")},
            imports_before=imports_before, require_pending=label == "L4")
        write(dest / "response.json", response)
    except Exception as error:
        write(dest / "runner_error.json", {"exception_type": type(error).__name__})
    finally:
        write(dest / "timing.json", {"end_to_end_ms": round((time.perf_counter() - start) * 1000, 3), "sdk_clients": sdk_clients})
        write(dest / "traces.json", traces)
        write(dest / "accounting.json", budget.snapshot())
        after = state()
        write(dest / "after.json", after)
        write(dest / "state_integrity.json", {
            "unchanged": {k: before[k] == after[k] for k in before},
            "unchanged_session_fields": {k: before["session"].get(k) == after["session"].get(k) for k in ("turn_counter", "clocks", "active_scene_id", "current_date")},
            "pending_before": (before["session"].get("conversational_context") or {}).get("pending_intention"),
            "pending_after": (after["session"].get("conversational_context") or {}).get("pending_intention")})
        patch.undo()


if __name__ == "__main__":
    main(sys.argv[1], preview="--preview" in sys.argv[2:])
