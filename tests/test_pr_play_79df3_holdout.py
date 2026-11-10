"""Developer-authored supplemental holdout for PR-PLAY-79D-F3.

The manifest is frozen. This module does not retune expected values.
It is not independent external validation.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from game import storage
from game.api import app
from game.player_http_projection import project_player_response
from game.publication_contract import (
    note_completed_publication,
    record_completed_publication,
    response_is_operational_refusal,
)
from tests.pr_play_79df3_harness import PRIOR, chat_turn, reset_budget, seed_gate

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tests" / "fixtures" / "pr_play_79df3_holdout.json"
DIGEST = ROOT / "tests" / "fixtures" / "pr_play_79df3_holdout.sha256"
RESULTS_PATH = ROOT / "artifacts" / "pr_play_79df3" / "holdout_results.jsonl"


def _flat(row: dict) -> dict:
    return {
        "operational": row["operational"],
        "refusal_category": row["refusal_category"],
        "failure_stage": row["failure_stage"],
        "events": len(row["publication_events"]),
        "pointer_unchanged": row["pointer_unchanged"],
        "requests_after": row["requests_after"],
        "provider_calls": row["provider_calls"],
        "tokens_after": row["tokens_after"],
        "turn_after": row["turn_after"],
        "world_unchanged": row["world_unchanged"],
        "character_unchanged": row["character_unchanged"],
        "hidden_exposed": row["hidden_exposed"],
        "provider_request_sent": row["provider_request_sent"],
        "status": row["status"],
        "visible": row["visible"],
        "log_class": row["log_class"],
        "gameplay_publication_completed": row["gameplay_publication_completed"],
    }


def _mismatch(actual: dict, expect: dict) -> list[str]:
    errors = []
    for key, wanted in expect.items():
        if key == "visible_contains":
            if str(wanted).casefold() not in str(actual.get("visible") or "").casefold():
                errors.append(f"visible_contains: {actual.get('visible')!r}")
            continue
        if actual.get(key) != wanted:
            errors.append(f"{key}: {actual.get(key)!r} != {wanted!r}")
    return errors


def _chat(case, root, monkeypatch, **extra):
    limits = {
        "request_limit": case.get("request_limit", "4"),
        "input_limit": case.get("input_limit", "100000"),
        "output_limit": case.get("output_limit", "100000"),
        "total_limit": case.get("total_limit", "200000"),
        "playtest": bool(case.get("playtest")),
        "interpret": case.get("interpret", True),
    }
    limits.update(extra)
    return _flat(chat_turn(root, monkeypatch, case.get("text", "Good day, Gate Guard."), **limits))


def _run(case: dict, root: Path, monkeypatch) -> dict:
    kind = case["procedure"]
    if kind == "chat":
        return _chat(case, root, monkeypatch)
    if kind == "accounting":
        blocked = root / "ledger-dir"
        blocked.mkdir(parents=True)
        return _flat(chat_turn(root, monkeypatch, "Good day, Gate Guard.", usage_path=blocked))
    if kind == "estimate":
        return _flat(chat_turn(root, monkeypatch, "Good day, Gate Guard.", estimate=0))
    if kind == "provider_exception":
        def create(**_kwargs):
            raise TimeoutError("secret prompt text")
        return _flat(chat_turn(root, monkeypatch, "Good day, Gate Guard.", create=create))
    if kind == "model_mismatch":
        def create(**_kwargs):
            usage = type("Usage", (), {"input_tokens": 2, "output_tokens": 1, "total_tokens": 3})()
            return type("Resp", (), {"model": "other-model", "output_text": "{}", "id": "r", "usage": usage})()
        return _flat(chat_turn(root, monkeypatch, "Good day, Gate Guard.", create=create))
    if kind == "malformed":
        def create(**_kwargs):
            usage = type("Usage", (), {"input_tokens": 2, "output_tokens": 1, "total_tokens": 3})()
            return type("Resp", (), {"model": "gpt-4.1-mini", "output_text": "not-json", "id": "r", "usage": usage})()
        return _flat(chat_turn(root, monkeypatch, "Good day, Gate Guard.", create=create))
    if kind == "context_leak":
        blocked = {
            "status": "blocked", "reason": "context_leak",
            "player_facing_text": "I can't interpret that from the current scene without using information you have not been shown.",
            "tags": ["interpretation_rejected", "non_mutating"], "record": None, "provider_requests": [],
        }
        return _flat(chat_turn(root, monkeypatch, "Good day, Gate Guard.", interpret_result=blocked))
    if kind == "accepted":
        spoken = 'Gate Guard says, "I do not know anything beyond the warning about a missing patrol."'
        session = {"campaign_run_id": "alpha", "turn_counter": 5, "last_publication": {"visible": PRIOR, "final": True, "dialogue_accepted": True, "campaign_run_id": "alpha"}}
        gm = {"metadata": {"expression_generation": {"decision": "adopted", "fallback_used": False, "candidate": "I do not know anything beyond the warning about a missing patrol.", "delivered_generated": True}}}
        record = note_completed_publication(session, text=spoken, gm=gm)
        return {"dialogue_accepted": record["dialogue_accepted"], "validation_outcome": record["validation_outcome"], "operational": response_is_operational_refusal({"resolution": {"kind": "question", "metadata": {}}})}
    if kind == "fallback":
        fallback = 'Gate Guard mutters, "Word is, check the notice board."'
        session = {"campaign_run_id": "alpha", "turn_counter": 5, "conversational_context": {"last_gm_exchange": {}}}
        gm = {"metadata": {"expression_generation": {"decision": "rejected", "fallback_used": True, "candidate": "The king paid them.", "delivered_generated": False}}}
        record = note_completed_publication(session, text=fallback, gm=gm)
        return {"dialogue_accepted": record["dialogue_accepted"], "validation_outcome": record["validation_outcome"], "operational": False, "king_absent": "king" not in record["visible"]}
    if kind == "physical":
        from tests.pr_play_79df_executor import ACCEPTED as line
        from tests.pr_play_79df_executor import physical
        acted = physical(monkeypatch, line, narrate=True)
        session = {"campaign_run_id": "alpha", "turn_counter": 2, "last_narration": {"adopted": True, "candidate": acted["published"]}}
        record = note_completed_publication(session, text=acted["published"])
        return {"calls": acted["calls"], "narration_published": record["narration_published"], "operational": False}
    if kind == "repeat":
        seed_gate(root, monkeypatch)
        monkeypatch.setenv("ASHEN_DISABLE_LIVE_INTERPRETATION", "1")
        monkeypatch.setenv("ASHEN_DISABLE_EXPRESSION_GENERATION", "1")
        monkeypatch.setenv("ASHEN_PUBLICATION_TRACE_PATH", str(root / "events.jsonl"))
        with TestClient(app) as client:
            reset_budget(root / "usage.jsonl")
            first = client.post("/api/chat?ui_mode=player", json={"text": "I examine the notice board.", "client_request_id": "h17a"})
            second = client.post("/api/chat?ui_mode=player", json={"text": "I examine the notice board.", "client_request_id": "h17b"})
        one = first.json()["gm_output"]["player_facing_text"]
        two = second.json()["gm_output"]["player_facing_text"]
        return {"canary_absent": "CANARY" not in one and "CANARY" not in two, "pointer_matches_second": storage.load_session()["last_publication"]["visible"] == two, "status": second.status_code}
    if kind == "continuation":
        seed_gate(root, monkeypatch)
        events = root / "events.jsonl"
        monkeypatch.setenv("ASHEN_PUBLICATION_TRACE_PATH", str(events))
        monkeypatch.setenv("ASHEN_PROVIDER_REQUEST_LIMIT", "0")
        monkeypatch.setenv("ASHEN_DISABLE_EXPRESSION_GENERATION", "1")
        monkeypatch.delenv("ASHEN_DISABLE_LIVE_INTERPRETATION", raising=False)
        monkeypatch.delenv("ASHEN_PLAYTEST_DISABLE_SDK_RETRIES", raising=False)
        with TestClient(app) as client:
            reset_budget(root / "usage.jsonl")
            client.post("/api/chat?ui_mode=player", json={"text": "Good day, Gate Guard.", "client_request_id": "h18a"})
            held = storage.load_session()["last_publication"]["visible"]
            monkeypatch.setenv("ASHEN_DISABLE_LIVE_INTERPRETATION", "1")
            monkeypatch.setenv("ASHEN_PROVIDER_REQUEST_LIMIT", "5")
            played = client.post("/api/chat?ui_mode=player", json={"text": "I examine the notice board.", "client_request_id": "h18b"})
        visible = played.json()["gm_output"]["player_facing_text"]
        lines = [json.loads(line) for line in events.read_text(encoding="utf-8").splitlines() if line.strip()] if events.exists() else []
        return {"refusal_events": 0 if not any("no gameplay action was taken" in line.get("final_player_facing_response", "") for line in lines) else 1, "gameplay_events": len(lines), "pointer_advanced": storage.load_session()["last_publication"]["visible"] == visible and visible != held, "canary_absent": "CANARY" not in visible}
    if kind == "save_reload":
        seed_gate(root, monkeypatch)
        monkeypatch.setenv("ASHEN_PUBLICATION_TRACE_PATH", str(root / "events.jsonl"))
        monkeypatch.setenv("ASHEN_PROVIDER_REQUEST_LIMIT", "0")
        monkeypatch.delenv("ASHEN_DISABLE_LIVE_INTERPRETATION", raising=False)
        monkeypatch.delenv("ASHEN_PLAYTEST_DISABLE_SDK_RETRIES", raising=False)
        with TestClient(app) as client:
            reset_budget(root / "usage.jsonl")
            client.post("/api/chat?ui_mode=player", json={"text": "Good day, Gate Guard.", "client_request_id": "h19"})
            created = client.post("/api/snapshots?ui_mode=player", json={"label": "holdout"})
            client.post("/api/snapshots/load?ui_mode=player", json={"snapshot_id": created.json()["snapshot"]["id"]})
        return {"pointer": storage.load_session()["last_publication"]["visible"], "turn": storage.load_session()["turn_counter"], "transcript_operational": any((item.get("log_meta") or {}).get("response_class") == "operational_refusal" for item in storage.load_log())}
    if kind == "cross_campaign":
        seed_gate(root / "alpha", monkeypatch)
        before = (root / "alpha" / "data" / "session.json").read_bytes()
        blocked = _flat(chat_turn(root / "beta", monkeypatch, "Good day, Gate Guard.", request_limit="0"))
        return {"alpha_unchanged": (root / "alpha" / "data" / "session.json").read_bytes() == before and blocked["operational"] is True}
    if kind == "projection":
        row = chat_turn(root, monkeypatch, "Good day, Gate Guard.", request_limit="0")
        projected = project_player_response({"ok": True, "gm_output": {"player_facing_text": row["visible"], "debug_notes": "hidden"}, "resolution": {"metadata": {"response_class": "operational_refusal", "refusal_category": "request ceiling"}}})
        encoded = json.dumps(projected)
        return {"resolution_empty": projected.get("resolution") == {}, "classification_hidden": "refusal_category" not in encoded and "debug_notes" not in encoded, "ok": projected.get("ok") is True, "visible": row["visible"]}
    if kind == "duplicate":
        seed_gate(root, monkeypatch)
        events = root / "events.jsonl"
        monkeypatch.setenv("ASHEN_PUBLICATION_TRACE_PATH", str(events))
        monkeypatch.setenv("ASHEN_PROVIDER_REQUEST_LIMIT", "0")
        monkeypatch.delenv("ASHEN_DISABLE_LIVE_INTERPRETATION", raising=False)
        monkeypatch.delenv("ASHEN_PLAYTEST_DISABLE_SDK_RETRIES", raising=False)
        with TestClient(app) as client:
            reset_budget(root / "usage.jsonl")
            client.post("/api/chat?ui_mode=player", json={"text": "Good day, Gate Guard.", "client_request_id": "same"})
            client.post("/api/chat?ui_mode=player", json={"text": "Good day, Gate Guard.", "client_request_id": "same"})
        text = events.read_text(encoding="utf-8") if events.exists() else ""
        return {"events": len([line for line in text.splitlines() if line.strip()]), "log_count": len(storage.load_log()), "pointer_unchanged": storage.load_session()["last_publication"]["visible"] == PRIOR}
    if kind == "server_error":
        class Response:
            status_code = 500
            body = json.dumps({"ok": False, "error": "You cannot act right now."}).encode()
        monkeypatch.setenv("ASHEN_PUBLICATION_TRACE_PATH", str(root / "events.jsonl"))
        row = record_completed_publication(Response(), source_handler="api_chat")
        return {"response_category": row["response_category"], "status_code": row["status_code"]}
    if kind == "classifier":
        return {
            "clarification_operational": response_is_operational_refusal({"resolution": {"kind": "conversational_clarify", "metadata": {"authoritative_mutation": False, "resolver_invoked": False, "processing_outcome": "clarification_required"}}}),
            "malformed_operational": response_is_operational_refusal({"resolution": {"kind": "interpretation_rejected", "metadata": {"authoritative_mutation": False, "resolver_invoked": False, "processing_outcome": "malformed_interpretation"}}}),
            "ceiling_operational": response_is_operational_refusal({"resolution": {"kind": "interpretation_rejected", "metadata": {"authoritative_mutation": False, "resolver_invoked": False, "processing_outcome": "input-token ceiling"}}}),
        }
    raise AssertionError(kind)


def test_frozen_supplemental_holdout(tmp_path, monkeypatch):
    raw = MANIFEST.read_bytes()
    digest = hashlib.sha256(raw).hexdigest()
    assert digest == DIGEST.read_text(encoding="utf-8").strip()
    manifest = json.loads(raw)
    assert manifest["external_validation"] is False
    assert len(manifest["cases"]) == 28
    results = []
    for case in manifest["cases"]:
        monkeypatch.undo()
        try:
            actual = _run(case, tmp_path / case["id"], monkeypatch)
            errors = _mismatch(actual, case["expect"])
        except Exception as exc:  # noqa: BLE001 - holdout records the failure
            actual = {}
            errors = [type(exc).__name__ + ": " + str(exc)]
        results.append({"id": case["id"], "pass": not errors, "errors": errors, "actual": actual, "expect": case["expect"]})
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    RESULTS_PATH.write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in results), encoding="utf-8")
    failed = [row["id"] + " " + "; ".join(row["errors"]) for row in results if row["errors"]]
    assert not failed, "\n".join(failed)
