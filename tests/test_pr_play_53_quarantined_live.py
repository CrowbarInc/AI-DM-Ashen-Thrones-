"""Quarantined live-provider narration stays off the player response.

These tests do not call a real provider. A fake client stands in for the
existing expression adapter. PR-PLAY-54 rejects the consequential fabrications
that PR-PLAY-53's heuristic accepted. Rejection still does not change the
player-facing response.
"""
from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from game import api, expressive_dialogue, provider_budget as budget
from game.anchored_investigation_narration import (
    authorize_anchored_investigation,
    preview_anchored_investigation,
)
from game.config import DEFAULT_MODEL_NAME
from game.expressive_dialogue import request_expression as _production_request_expression
from game.immutable_valid_response import validate_generated_response
from game.quarantined_investigation_narration import (
    EVIDENCE_ENV,
    FAULT_ENV,
    GATE_ENV,
    LABEL_ENV,
    LIVE_ENV,
    SAMPLE_ENV,
    _LivePrelude,
    clear_evidence,
    evidence_records,
    reset_live_budget,
)
from game.resolution_contract import contract_mapping_from_resolution
from tests.test_pr_play_52_quarantined_integration import (
    CANARIES,
    HIDDEN_FACTS,
    NOTICE,
    NOTICE_CLUE,
    _count_resolvers,
    _diff,
    _facing,
    _guard_writers,
    _mechanical,
    _resolution,
    _scrub,
    _seed,
    _snapshot,
)

ROUTE = "The missing patrol was last seen taking the northwest mud track past the crates."
PRELUDE = "Rain beads on the crowded board as you lean in for a closer look."
KEY_MISS = "You find a silver key beneath the board."


def _quiet_env(monkeypatch, tmp_path, *, live=False, fault="", sample="stub", reset=True):
    monkeypatch.setenv("ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT", "1")
    monkeypatch.setenv("ASHEN_DISABLE_LIVE_INTERPRETATION", "1")
    monkeypatch.setenv("ASHEN_DISABLE_EXPRESSION_GENERATION", "1")
    monkeypatch.setenv("ASHEN_DISABLE_PROVIDER_CALLS", "1")
    monkeypatch.setenv("ASHEN_DISABLE_PROVIDER_RETRIES", "1")
    monkeypatch.setenv("ASHEN_PLAYTEST_DISABLE_SDK_RETRIES", "1")
    monkeypatch.delenv("ASHEN_PROVIDER_USAGE_PATH", raising=False)
    monkeypatch.delenv("ASHEN_PROVIDER_REQUEST_LIMIT", raising=False)
    monkeypatch.setenv(GATE_ENV, "1")
    monkeypatch.setenv(SAMPLE_ENV, sample)
    monkeypatch.setenv(FAULT_ENV, fault)
    monkeypatch.setenv(LABEL_ENV, "pr53")
    monkeypatch.setenv(EVIDENCE_ENV, str(tmp_path / "quarantine"))
    if live:
        monkeypatch.setenv(LIVE_ENV, "1")
    else:
        monkeypatch.delenv(LIVE_ENV, raising=False)
    if reset:
        reset_live_budget()
    clear_evidence()


def _install_fake(monkeypatch, *, mode="ok", text=PRELUDE):
    calls = {"clients": 0, "create": 0, "key_supplied": False, "messages": None, "max_output_tokens": None, "contains_secret": lambda blob: False}

    class _Usage:
        input_tokens = 30
        output_tokens = 12
        total_tokens = 42

    class _Response:
        output_text = text
        usage = _Usage()
        model = DEFAULT_MODEL_NAME
        id = "resp_quarantine_test"

    class _Responses:
        def create(self, **kwargs):
            calls["create"] += 1
            calls["max_output_tokens"] = kwargs.get("max_output_tokens")
            calls["messages"] = kwargs.get("input")
            if mode == "timeout":
                raise TimeoutError("simulated_provider_timeout")
            if mode == "explode":
                raise RuntimeError("simulated_provider_exception")
            return _Response()

    class _OpenAI:
        def __init__(self, *args, **kwargs):
            calls["clients"] += 1
            secret = str(kwargs.get("api_key") or "")
            calls["key_supplied"] = len(secret) > 8
            calls["contains_secret"] = lambda blob, _secret=secret: bool(_secret) and _secret in blob
            self.responses = _Responses()

    import openai

    monkeypatch.setattr(openai, "OpenAI", _OpenAI, raising=False)
    return calls


def _play(tmp_path, monkeypatch, text, *, live=False, fault="", mode="ok", prelude=PRELUDE, scene_id="frontier_gate", reset=True, usage_path=None, request_limit=None):
    _seed(tmp_path, monkeypatch, scene_id)
    writers = _guard_writers(monkeypatch)
    resolvers = _count_resolvers(monkeypatch)
    calls = _install_fake(monkeypatch, mode=mode, text=prelude)
    from tests.helpers.live_model_guard import production_call_gpt

    monkeypatch.setattr("game.gm.call_gpt", production_call_gpt())
    monkeypatch.setattr("game.api.call_gpt", production_call_gpt())
    monkeypatch.setattr(expressive_dialogue, "request_expression", _production_request_expression)
    _quiet_env(monkeypatch, tmp_path, live=live, fault=fault, reset=reset)
    if usage_path is not None:
        monkeypatch.setenv("ASHEN_PROVIDER_USAGE_PATH", str(usage_path))
    if request_limit is not None:
        monkeypatch.setenv("ASHEN_PROVIDER_REQUEST_LIMIT", request_limit)
    client = TestClient(api.app)
    client.__enter__()
    try:
        response = client.post("/api/chat?ui_mode=player", json={"text": text})
    finally:
        try:
            client.__exit__(None, None, None)
        except Exception:
            pass
    return {
        "status_code": response.status_code,
        "body": response.json(),
        "final": _snapshot(),
        "writers": list(writers),
        "resolvers": dict(resolvers),
        "calls": calls,
        "quarantine": evidence_records(),
    }


def _user_blob(record) -> str:
    live = record.get("live_provider") if isinstance(record.get("live_provider"), dict) else {}
    return json.dumps({
        "hook_input": record.get("hook_input"),
        "generator_request": record.get("generator_request"),
        "provider_user_message": live.get("sanitized_provider_user_message"),
    }, ensure_ascii=False)


def test_live_flag_defaults_off(tmp_path, monkeypatch):
    run = _play(tmp_path, monkeypatch, NOTICE, live=False)
    record = run["quarantine"][0]
    assert run["status_code"] == 200
    assert record["provider_requests"] == 0
    assert record["live_provider"] == {"enabled": False}
    assert run["calls"]["clients"] == 0
    assert NOTICE_CLUE in _facing(run)
    assert PRELUDE not in json.dumps(run["body"])


def test_successful_investigation_stays_quarantined(tmp_path, monkeypatch):
    baseline = _play(tmp_path, monkeypatch, NOTICE, live=False)
    experimental = _play(tmp_path, monkeypatch, NOTICE, live=True)
    record = experimental["quarantine"][0]
    assert experimental["calls"]["create"] == 1
    assert experimental["calls"]["max_output_tokens"] == expressive_dialogue._OUTPUT_CAP
    assert experimental["calls"]["max_output_tokens"] <= 1000
    assert record["provider_requests"] == 1
    assert record["diagnostic"] == "heuristic_pass_pending_review"
    assert record["used_fallback"] is False
    assert record["raw_provider_text"] == PRELUDE
    assert record["live_provider"]["input_tokens"] == 30
    assert record["live_provider"]["output_tokens"] == 12
    assert record["live_provider"]["total_tokens"] == 42
    assert record["live_provider"]["retry_count"] == 0
    assert record["live_provider"]["estimated_cost"] is None
    assert NOTICE_CLUE in record["assembled"]
    assert record["assembled"].count(NOTICE_CLUE) == 1
    assert PRELUDE not in _facing(experimental)
    assert _facing(experimental) == _facing(baseline)
    assert _mechanical(_resolution(experimental)) == _mechanical(_resolution(baseline))
    assert _diff(_scrub(experimental["final"]), _scrub(baseline["final"])) == []
    assert experimental["writers"] == []
    assert experimental["resolvers"] == {"exploration": 1, "social": 0}
    blob = _user_blob(record)
    assert NOTICE in blob
    assert NOTICE_CLUE in blob
    for secret in list(CANARIES) + list(HIDDEN_FACTS) + ["notice_patrol_route", "skill_check", "OPENAI_API_KEY"]:
        assert secret not in blob
    dumped = json.dumps(record)
    assert "sk-" not in dumped
    assert experimental["calls"]["key_supplied"] is True
    assert experimental["calls"]["contains_secret"](dumped) is False


def test_rejected_fabrication_is_not_promoted(tmp_path, monkeypatch):
    baseline = _play(tmp_path, monkeypatch, NOTICE, live=False)
    experimental = _play(tmp_path, monkeypatch, NOTICE, live=True, prelude=KEY_MISS)
    record = experimental["quarantine"][0]
    assert record["diagnostic"] == "semantic_rejection"
    assert record["used_fallback"] is True
    assert record["validation"]["consequential_validation"]["decision"] == "FAIL"
    assert "silver key" not in record["assembled"]
    assert "silver key" not in _facing(experimental)
    assert _facing(experimental) == _facing(baseline)
    assert _mechanical(_resolution(experimental)) == _mechanical(_resolution(baseline))
    assert experimental["final"]["character"] == baseline["final"]["character"]
    assert "quarantine" not in json.dumps(experimental["body"]).casefold()


def test_limited_investigation_does_not_receive_the_route(tmp_path, monkeypatch):
    text = "I examine the rain barrel."
    baseline = _play(tmp_path, monkeypatch, text, live=False)
    experimental = _play(tmp_path, monkeypatch, text, live=True, prelude="You look around the barrel and learn nothing new.")
    record = experimental["quarantine"][0]
    mechanical = _mechanical(_resolution(experimental))
    assert mechanical["discovered_clues"] in ([], None)
    assert not mechanical["clue_text"]
    assert experimental["calls"]["create"] == 1
    assert ROUTE not in _user_blob(record)
    assert ROUTE not in (record.get("raw_provider_text") or "")
    assert _facing(experimental) == _facing(baseline)
    assert "Provider calls are disabled" in _facing(experimental)
    assert _diff(_scrub(experimental["final"]), _scrub(baseline["final"])) == []
    assert experimental["writers"] == []


def test_injected_fault_suppresses_the_live_call(tmp_path, monkeypatch):
    run = _play(tmp_path, monkeypatch, NOTICE, live=True, fault="timeout")
    record = run["quarantine"][0]
    assert run["calls"]["clients"] == 0
    assert record["provider_requests"] == 0
    assert record["diagnostic"] == "simulated_timeout"
    assert record["used_fallback"] is True
    assert NOTICE_CLUE in _facing(run)
    assert run["writers"] == []


def test_provider_timeout_leaves_the_turn_intact(tmp_path, monkeypatch):
    baseline = _play(tmp_path, monkeypatch, NOTICE, live=False)
    failed = _play(tmp_path, monkeypatch, NOTICE, live=True, mode="timeout")
    record = failed["quarantine"][0]
    assert failed["calls"]["create"] == 1
    assert record["diagnostic"] == "simulated_timeout"
    assert record["used_fallback"] is True
    assert record["live_provider"]["timeout"] is True
    assert record["live_provider"]["retry_count"] == 0
    assert _facing(failed) == _facing(baseline)
    assert _mechanical(_resolution(failed)) == _mechanical(_resolution(baseline))
    assert failed["writers"] == []


def test_provider_exception_is_not_retried(tmp_path, monkeypatch):
    run = _play(tmp_path, monkeypatch, NOTICE, live=True, mode="explode")
    record = run["quarantine"][0]
    assert run["calls"]["create"] == 1
    assert record["provider_requests"] == 1
    assert record["used_fallback"] is True
    assert NOTICE_CLUE in _facing(run)
    assert "simulated_provider_exception" not in _facing(run)
    generator = _LivePrelude("I examine the notice board.")
    generator.calls = 1
    with pytest.raises(RuntimeError, match="automatic_retry_forbidden"):
        generator.generate({"authorized_investigation": {}})
    assert run["calls"]["create"] == 1


def test_request_ceiling_blocks_dispatch(tmp_path, monkeypatch):
    for name, value in {
        "_REQUESTS": 0, "_RECORDS": [], "_EVENTS": [], "_ATTEMPTS": {},
        "_INPUT": 0, "_OUTPUT": 0, "_RESERVED_INPUT": 0, "_RESERVED_OUTPUT": 0,
        "_USAGE_KNOWN": True, "_STOPPED": False, "_STOP_REASON": "",
        "_INITIALIZED": False, "_LEDGER_PATH": None,
    }.items():
        monkeypatch.setattr(budget, name, value)
    monkeypatch.setenv("ASHEN_PROVIDER_USAGE_PATH", str(tmp_path / "usage.jsonl"))
    monkeypatch.setenv("ASHEN_PROVIDER_REQUEST_LIMIT", "0")
    monkeypatch.setenv("ASHEN_DISABLE_PROVIDER_CALLS", "1")
    monkeypatch.setenv("ASHEN_PLAYTEST_DISABLE_SDK_RETRIES", "1")
    monkeypatch.setattr(expressive_dialogue, "request_expression", _production_request_expression)
    calls = _install_fake(monkeypatch)
    reset_live_budget()
    generator = _LivePrelude(NOTICE)
    with pytest.raises(RuntimeError, match="request ceiling"):
        generator.generate({"authorized_investigation": {"target": "notice_board", "status": "discovered"}})
    assert calls["clients"] == 0
    assert generator.sent is False
    assert generator.calls == 1
    assert generator.diagnostic == "request ceiling"
    ledger = (tmp_path / "usage.jsonl").read_text(encoding="utf-8")
    assert "request ceiling" in ledger
    assert "sk-" not in ledger


def test_experiment_ceilings_refuse_before_dispatch(tmp_path, monkeypatch):
    import game.quarantined_investigation_narration as quarantine

    monkeypatch.setattr(quarantine, "_LIVE_SENT", MAX_SENT)
    run = _play(tmp_path, monkeypatch, NOTICE, live=True, reset=False)
    assert run["calls"]["clients"] == 0
    assert run["quarantine"][0]["diagnostic"] == "experiment_request_ceiling"
    reset_live_budget()
    monkeypatch.setattr(quarantine, "_LIVE_TOKENS", 10000)
    blocked = _play(tmp_path, monkeypatch, NOTICE, live=True, reset=False)
    assert blocked["calls"]["clients"] == 0
    assert blocked["quarantine"][0]["diagnostic"] == "experiment_token_ceiling"
    reset_live_budget()
    monkeypatch.setattr(expressive_dialogue, "_OUTPUT_CAP", 1001)
    oversized = _play(tmp_path, monkeypatch, NOTICE, live=True, reset=False)
    assert oversized["calls"]["clients"] == 0
    assert oversized["quarantine"][0]["diagnostic"] == "output_cap_exceeds_experiment"


MAX_SENT = 6


def _payload():
    return {
        "scene": {
            "public": {
                "location": "Cinderwatch Gate District",
                "summary": "Rain and a notice board.",
                "visible_facts": [
                    "The notice board lists taxes, curfew rules, and a warning about a missing patrol.",
                ],
            },
            "discovered_clues": [],
        }
    }


def _resolution_for(kind):
    if kind == "failed":
        return {
            "kind": "investigate", "success": False, "action_id": "notice_board",
            "interactable_id": "notice_board", "discovered_clues": [], "clue_text": "",
            "state_changes": {"skill_check_failed": True},
        }
    if kind == "observed":
        return {
            "kind": "investigate", "success": True, "action_id": "rain_barrel",
            "interactable_id": None, "discovered_clues": [], "clue_text": "",
            "state_changes": {},
        }
    return {
        "kind": "discover_clue", "success": True, "action_id": "notice_board",
        "interactable_id": "notice_board", "discovered_clues": [NOTICE_CLUE],
        "clue_text": NOTICE_CLUE, "state_changes": {},
    }


# `detected` is the PR-PLAY-53 heuristic result and stays locked.
# Consequential lines must now fail closed in the prelude gate.
FABRICATIONS = [
    ("find_key", "success", "You find a silver key beneath the board.", "fabricated_discovery", True, False),
    ("key_possession", "success", "A silver key now rests among your possessions.", "fabricated_discovery", True, True),
    ("acquire", "success", "You acquire a brass compass.", "fabricated_discovery", True, True),
    ("passage", "success", "The hidden passage opens before you.", "fabricated_discovery", True, True),
    ("culprit", "success", "You recognize the culprit immediately.", "fabricated_discovery", True, False),
    ("confess", "success", "The tavern runner confesses that he sold the patrol route.", "unauthorized_npc_knowledge", True, False),
    ("receive_route", "success", "You receive the patrol route and tuck it into your pack.", "fabricated_discovery", True, True),
    ("failed_as_success", "failed", "You succeed in uncovering the patrol route.", "outcome_contradiction", True, False),
    ("owned_key", "success", "The silver key is now yours.", "fabricated_discovery", True, False),
    ("invented_route", "observed", "You read that the patrol took the northwest mud track past the crates.", "fabricated_discovery", True, False),
    ("harmless_rain", "success", "Rain beads on the crowded board as you lean in for a closer look.", "harmless_embellishment", False, False),
    ("wax_seal", "success", "A cracked wax seal holds one corner of the top notice.", "nonconsequential_detail", False, False),
]


@pytest.mark.parametrize("case,kind,text,family,consequential,detected", FABRICATIONS)
def test_consequential_fabrication_detection(case, kind, text, family, consequential, detected):
    contract = authorize_anchored_investigation(_resolution_for(kind), _payload())

    class _Stub:
        def generate(self, request):
            return text

    preview = preview_anchored_investigation(contract, _Stub(), enabled=True)
    audit_resolution = {
        "kind": "investigate",
        "success": contract.outcome.success,
        "discovered_clues": list(contract.outcome.revealed),
        "state_changes": {},
    }
    audit = validate_generated_response(
        text,
        resolution=audit_resolution,
        contract=contract_mapping_from_resolution(audit_resolution),
    )
    assert audit["hard_valid"] is not detected
    decision = json.loads(preview.validation_json)["consequential_validation"]["decision"]
    if consequential:
        assert decision in {"FAIL", "REVIEW_REQUIRED"}
        assert preview.used_fallback is True
        assert preview.diagnostic == "semantic_rejection"
        assert text not in preview.preview_text
    else:
        assert decision == "PASS"
        assert preview.used_fallback is detected
        if not detected:
            assert preview.diagnostic == "heuristic_pass_pending_review"
