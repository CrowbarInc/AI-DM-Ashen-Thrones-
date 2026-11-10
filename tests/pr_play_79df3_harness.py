"""Isolated HTTP harness for operational-refusal classification.

Storage stays under the test temporary directory. Provider admission is real.
"""
from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

from fastapi.testclient import TestClient

from game import provider_budget as budget
from game import storage
from game.api import app
from game.publication_contract import OPERATIONAL_REFUSAL

PRIOR = 'Gate Guard says, "The notice board mentions a missing patrol."'
CANARIES = (
    "CANARY_UNDISCOVERED_CLUE",
    "CANARY_GM_NOTE",
    "CANARY_NPC_MOTIVE",
    "CANARY_HIDDEN_DESTINATION",
    "CANARY_QUEST_TWIST",
    "CANARY_MECHANICAL_ID",
    "CANARY_UNRELATED_WORLD",
)


def reset_budget(path: Path) -> None:
    if path.exists() and path.is_file():
        path.unlink()
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
    os.environ["ASHEN_PROVIDER_USAGE_PATH"] = str(path)


def seed_gate(tmp_path, monkeypatch):
    from tests.test_pr_play_52_quarantined_integration import _seed

    _seed(tmp_path, monkeypatch, "frontier_gate")
    session = storage.load_session()
    session["turn_counter"] = 4
    session["last_publication"] = {
        "owner": "integrated_play.commit_integrated",
        "contract": "FINAL_ENGINE_RESPONSE",
        "final": True,
        "dialogue_accepted": True,
        "dialogue_published": True,
        "visible": PRIOR,
        "turn": 4,
        "campaign_run_id": session.get("campaign_run_id"),
    }
    storage.save_session(session)
    return session


def _events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def chat_turn(
    tmp_path,
    monkeypatch,
    text: str,
    *,
    request_limit: str = "4",
    input_limit: str = "100000",
    output_limit: str = "100000",
    total_limit: str = "200000",
    playtest: bool = False,
    interpret: bool = True,
    client_request_id: str | None = None,
    create=None,
    estimate=None,
    interpret_result=None,
    events_name: str = "events.jsonl",
    usage_path: Path | None = None,
):
    """Post one real /api/chat turn and report publication classification."""
    seed_gate(tmp_path, monkeypatch)
    events = tmp_path / events_name
    if events.exists():
        events.unlink()
    monkeypatch.setenv("ASHEN_PUBLICATION_TRACE_PATH", str(events))
    monkeypatch.setenv("ASHEN_PROVIDER_REQUEST_LIMIT", request_limit)
    monkeypatch.setenv("ASHEN_PROVIDER_INPUT_TOKEN_LIMIT", input_limit)
    monkeypatch.setenv("ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT", output_limit)
    monkeypatch.setenv("ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT", total_limit)
    monkeypatch.setenv("ASHEN_DISABLE_PROVIDER_RETRIES", "1")
    monkeypatch.setenv("ASHEN_DISABLE_EXPRESSION_GENERATION", "1")
    monkeypatch.delenv("ASHEN_DISABLE_PROVIDER_CALLS", raising=False)
    if playtest:
        monkeypatch.setenv("ASHEN_PLAYTEST_DISABLE_SDK_RETRIES", "1")
    else:
        monkeypatch.delenv("ASHEN_PLAYTEST_DISABLE_SDK_RETRIES", raising=False)
    if interpret:
        monkeypatch.delenv("ASHEN_DISABLE_LIVE_INTERPRETATION", raising=False)
    else:
        monkeypatch.setenv("ASHEN_DISABLE_LIVE_INTERPRETATION", "1")
    if create is not None:
        import openai
        from game import config

        monkeypatch.setattr(config, "get_openai_api_key", lambda: "stub-only")
        monkeypatch.setattr(openai, "OpenAI", lambda **_kw: type("Client", (), {"responses": type("Responses", (), {"create": staticmethod(create)})()})())
    if estimate is not None:
        import experiments.pr_dp.prompt as prompt

        monkeypatch.setattr(prompt, "estimate_input_tokens", lambda *_a, **_k: estimate)
    if interpret_result is not None:
        monkeypatch.setattr("game.api.interpret_production_turn", lambda **_k: interpret_result)
    usage_path = usage_path or (tmp_path / f"usage-{uuid.uuid4().hex}.jsonl")
    before_world = json.dumps(storage.load_world(), sort_keys=True)
    before_character = json.dumps(storage.load_character(), sort_keys=True)
    before = storage.load_session()
    calls = {"n": 0}

    def counting_create(**kwargs):
        calls["n"] += 1
        return create(**kwargs)

    if create is not None:
        import openai

        monkeypatch.setattr(openai, "OpenAI", lambda **_kw: type("Client", (), {"responses": type("Responses", (), {"create": staticmethod(counting_create)})()})())
    with TestClient(app) as client:
        reset_budget(usage_path)
        started = budget.snapshot()
        response = client.post(
            "/api/chat?ui_mode=player",
            json={"text": text, "client_request_id": client_request_id or uuid.uuid4().hex},
        )
        ended = budget.snapshot()
    body = response.json()
    after = storage.load_session()
    log = storage.load_log()
    meta = {}
    if log:
        resolution = log[-1].get("resolution") if isinstance(log[-1], dict) else {}
        meta = (resolution or {}).get("metadata") if isinstance(resolution, dict) else {}
        meta = meta if isinstance(meta, dict) else {}
    visible = str((body.get("gm_output") or {}).get("player_facing_text") or "")
    pointer = after.get("last_publication") if isinstance(after.get("last_publication"), dict) else {}
    prior = before.get("last_publication") if isinstance(before.get("last_publication"), dict) else {}
    response_class = meta.get("response_class") or "gameplay"
    return {
        "status": response.status_code,
        "ok": body.get("ok"),
        "visible": visible,
        "body": body,
        "response_class": response_class,
        "refusal_category": meta.get("refusal_category"),
        "failure_stage": meta.get("failure_stage"),
        "provider_request_sent": meta.get("provider_request_sent"),
        "gameplay_publication_completed": meta.get("gameplay_publication_completed"),
        "publication_events": _events(events),
        "pointer_before": prior.get("visible"),
        "pointer_after": pointer.get("visible"),
        "pointer_unchanged": pointer.get("visible") == prior.get("visible"),
        "turn_before": before.get("turn_counter"),
        "turn_after": after.get("turn_counter"),
        "requests_before": started.get("requests") or 0,
        "requests_after": ended.get("requests") or 0,
        "tokens_after": ended.get("total_tokens") or 0,
        "world_unchanged": json.dumps(storage.load_world(), sort_keys=True) == before_world,
        "character_unchanged": json.dumps(storage.load_character(), sort_keys=True) == before_character,
        "hidden_exposed": any(token in visible or token in json.dumps(body) for token in CANARIES),
        "provider_calls": calls["n"],
        "log_class": (log[-1].get("log_meta") or {}).get("response_class") if log else None,
        "operational": response_class == OPERATIONAL_REFUSAL,
    }
