"""Offline readiness recovery; no experimental/test-module fixture imports."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

from tools.atgb import readiness as r

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts/atgb/atgb_r1_04"


@pytest.mark.parametrize("value", [None, "0", "1"])
@pytest.mark.parametrize("order", [
    ["tools.atgb.readiness", "game.live_chat_interpretation"],
    ["game.live_chat_interpretation", "tools.atgb.readiness"],
])
def test_fresh_import_safety(value, order):
    env = dict(os.environ)
    if value is None:
        env.pop(r.FLAG, None)
    else:
        env[r.FLAG] = value
    script = "import importlib,os; " + "; ".join(f"importlib.import_module({m!r})" for m in order)
    script += f"; assert os.environ.get({r.FLAG!r}) == {value!r}"
    result = subprocess.run([sys.executable, "-c", script], env=env, cwd=ROOT,
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr


def test_legacy_import_is_detected_and_restored():
    script = """
import os
from tools.atgb.readiness import import_fixture, FLAG
os.environ.pop(FLAG, None)
try:
    import_fixture('tests.test_pr_ef_r4_authorization')
except RuntimeError as error:
    assert str(error) == 'validation_fixture_import_side_effect'
else:
    raise AssertionError('legacy leak undetected')
assert FLAG not in os.environ
"""
    result = subprocess.run([sys.executable, "-c", script], cwd=ROOT,
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("original", [None, "0", "1"])
def test_sequential_modes_and_failure_restoration(monkeypatch, original):
    if original is None:
        monkeypatch.delenv(r.FLAG, raising=False)
    else:
        monkeypatch.setenv(r.FLAG, original)
    for live in (False, True, False, True):
        with r.execution_mode(live):
            assert os.environ[r.FLAG] == ("0" if live else "1")
        assert os.environ.get(r.FLAG) == original
    with pytest.raises(ValueError):
        with r.execution_mode(True):
            raise ValueError("controlled fixture failure")
    assert os.environ.get(r.FLAG) == original


def test_failed_import_restores_configuration(monkeypatch):
    before = dict(os.environ)
    def broken_import(_name):
        os.environ[r.FLAG] = "1"
        raise ValueError("controlled import failure")
    monkeypatch.setattr(r.importlib, "import_module", broken_import)
    with pytest.raises(ValueError):
        r.import_fixture("controlled_failure")
    assert dict(os.environ) == before


def record(purpose="QUESTION"):
    return {
        "communication_mode": "OTHER", "interpretation_status": "INTERPRETED",
        "player_intent": {"summary": "Revise pending ask"}, "asserted_premises": [],
        "requested_outcomes": [], "action_components": [],
        "references": {"permitted_entity_ids": [], "unresolved_references": []},
        "clarification_question": "", "correction": {"subject": "NONE", "note": ""},
        "communication": {"recipient": "GM", "purpose": purpose, "subject": "pending ask", "evidence_refs": []},
    }


def snapshot():
    from game import storage
    return copy.deepcopy(dict(session=storage.load_session(), world=storage.load_world(),
        scene=storage.load_active_scene(), character=storage.load_character(), combat=storage.load_combat()))


@pytest.fixture
def control(tmp_path, monkeypatch):
    from game import storage, provider_budget as budget
    from game.api import chat
    from game.models import ChatRequest
    from game.live_chat_interpretation import _contract
    data = r.seed_control(tmp_path / "control", monkeypatch)
    monkeypatch.setenv(r.FLAG, "0")
    monkeypatch.setenv("ASHEN_DISABLE_PROVIDER_CALLS", "0")
    monkeypatch.setenv("ASHEN_DISABLE_PROVIDER_RETRIES", "1")
    monkeypatch.setenv("ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT", "1")
    monkeypatch.setenv("ASHEN_PROVIDER_REQUEST_LIMIT", "2")
    monkeypatch.setenv("ASHEN_PROVIDER_USAGE_PATH", str(tmp_path / "usage.jsonl"))
    # Each deterministic test gets isolated accounting globals, as well as its store.
    for name, value in {"_INITIALIZED": False, "_LEDGER_PATH": None, "_REQUESTS": 0,
                        "_STOPPED": False, "_STOP_REASON": None, "_EVENTS": [],
                        "_RECORDS": [], "_ATTEMPTS": {}}.items():
        monkeypatch.setattr(budget, name, value)
    budget.initialize_accounting()
    _contract()
    before = snapshot()
    ask = record()
    ask["communication"] = {"recipient": "NPC", "purpose": "QUESTION", "subject": "road", "evidence_refs": []}
    ask["action_components"] = [{"order": 1, "description": "Ask one of them", "operation_class": "ASK", "target_ref": "sergeant_mara"}]
    ask["references"]["permitted_entity_ids"] = ["sergeant_mara"]
    monkeypatch.setattr("game.live_chat_interpretation.request_interpretation",
        lambda *a, **k: {"ok": True, "sent": False, "text": json.dumps(ask)})
    chat(ChatRequest(text="I ask one of them what happened."))
    after = snapshot()
    assert before["world"] == after["world"]
    assert before["session"]["turn_counter"] == after["session"]["turn_counter"]
    assert not r.pending_errors(after["session"], after["scene"], after["world"], after["character"])
    yield dict(live=True, model="gpt-4.1-mini", limit=2, store=data,
        **after, imports_before=r.flag_snapshot())


def config(control):
    return {key: value for key, value in control.items() if key != "combat"}


def test_genuine_pending_revision(control, monkeypatch):
    from game.api import chat
    from game.models import ChatRequest
    before = snapshot()
    monkeypatch.setattr("game.live_chat_interpretation.request_interpretation",
        lambda *a, **k: {"ok": True, "sent": False, "text": json.dumps(record("CORRECTION"))})
    text = "Instead, make that a question about the lamp."
    preflight = r.preflight(**config(control))
    assert preflight["failed_assertions"] == []
    response = r.guarded_trial(evidence_path=OUT / "preflight_valid.json", **config(control),
        execute=lambda: chat(ChatRequest(text=text)))
    after = snapshot()
    assert "revised" in response["gm_output"]["player_facing_text"].lower()
    for key in ("world", "scene", "character", "combat"):
        assert before[key] == after[key]
    assert before["session"]["turn_counter"] == after["session"]["turn_counter"]
    assert before["session"]["clocks"] == after["session"]["clocks"]
    pending = after["session"]["conversational_context"]["pending_intention"]
    assert pending["status"] == "pending" and pending["revised_text"] == text
    assert not r.pending_errors(after["session"], after["scene"], after["world"], after["character"])
    (OUT / "pending_control.json").write_text(json.dumps({"evidence_scope": "structural_only",
        "input_classification": "synthetic_positive_control", "before": before, "after": after,
        "response": response, "provider_admissions": 0}, indent=2), encoding="utf-8")


@pytest.mark.parametrize("fault", ["mode", "provider", "model", "import", "store", "limit", "ledger", "pending", "target", "actor", "scene", "executed", "retries", "tokens", "provider_disabled", "startup", "stale", "used_budget"])
def test_preflight_abort_has_no_dispatch_or_state_mutation(control, monkeypatch, fault):
    before = snapshot()
    options = config(control)
    if fault == "mode": monkeypatch.setenv(r.FLAG, "1")
    if fault == "provider": monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    if fault == "model": options["model"] = "unrequested-model"
    if fault == "import": options["imports_before"] = {}
    if fault == "store": options["store"] = ROOT / "data"
    if fault == "limit": monkeypatch.setenv("ASHEN_PROVIDER_REQUEST_LIMIT", "3")
    if fault == "ledger":
        from game import provider_budget
        monkeypatch.setattr(provider_budget, "_INITIALIZED", False)
    if fault == "pending": options["session"] = {}
    if fault == "target": options["world"] = {"npcs": []}
    if fault == "actor": options["character"] = {}
    if fault == "scene": options["scene"] = {"scene": {"id": "elsewhere"}}
    if fault == "executed":
        options["session"] = copy.deepcopy(options["session"])
        options["session"]["conversational_context"]["pending_intention"]["status"] = "executed"
    if fault == "retries": monkeypatch.setenv("ASHEN_DISABLE_PROVIDER_RETRIES", "0")
    if fault == "tokens": monkeypatch.setenv("ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT", "invalid")
    if fault == "provider_disabled": monkeypatch.setenv("ASHEN_DISABLE_PROVIDER_CALLS", "1")
    if fault == "startup": monkeypatch.setenv("ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT", "0")
    if fault == "stale":
        from game import storage
        session = storage.load_session()
        session["turn_counter"] += 1
        storage.save_session(session)
        before = snapshot()
    if fault == "used_budget":
        from game import provider_budget
        monkeypatch.setattr(provider_budget, "_REQUESTS", 1)
    result = r.guarded_trial(evidence_path=OUT / f"preflight_failure_{fault}.json", **options,
        execute=lambda: pytest.fail("trial executed after failed preflight"))
    assert result["classification"] == "validation_setup_failure"
    assert result["failed_assertions"]
    assert result["provider_admissions"] == (1 if fault == "used_budget" else 0)
    assert snapshot() == before


def test_disabled_mode_is_explicit(control, monkeypatch):
    options = config(control)
    with r.execution_mode(False):
        options.update(live=False, imports_before=r.flag_snapshot())
        assert r.preflight(**options)["classification"] == "ready"
    assert os.environ[r.FLAG] == "0"


@pytest.mark.parametrize("error", ["APIConnectionError", "InternalServerError"])
def test_failed_provider_does_not_execute_pending(control, monkeypatch, error):
    from game.api import chat
    from game.models import ChatRequest
    before = snapshot()
    monkeypatch.setattr("game.live_chat_interpretation.request_interpretation",
        lambda *a, **k: {"ok": False, "sent": True, "error": error})
    response = chat(ChatRequest(text="Instead, make that a question about the lamp."))
    assert "no gameplay action" in response["gm_output"]["player_facing_text"]
    assert snapshot() == before


@pytest.mark.parametrize("case_id", ["correction_pending", "correction_already_executed", "correction_nothing_pending"])
def test_frozen_revision_authority_through_direct_chat(control, monkeypatch, case_id):
    from game import storage
    from game.api import chat
    from game.models import ChatRequest
    cases = json.loads((ROOT / "tests/fixtures/pr_ef_r4_holdouts.json").read_text(encoding="utf-8"))["cases"]
    case = next(c for c in cases if c["id"] == case_id)
    session = storage.load_session()
    context = session["conversational_context"]
    if case_id != "correction_pending":
        previous = context.pop("pending_intention")
        context.pop("pending_clarification", None)
        if case_id == "correction_already_executed":
            # Synthetic executed-state negative control; does not execute the ask.
            previous["status"] = "executed"
            context["last_executed_intention"] = previous
        storage.save_session(session)
    monkeypatch.setattr("game.live_chat_interpretation.request_interpretation",
        lambda *a, **k: {"ok": True, "sent": False, "text": json.dumps(record("CORRECTION"))})
    before = snapshot()
    response = chat(ChatRequest(text=case["player"]))
    after = snapshot()
    assert not response["resolution"].get("social")
    phrase = {"correction_pending": "revised", "correction_already_executed": "cannot undo",
              "correction_nothing_pending": "what do you want to change"}[case_id]
    assert phrase in response["gm_output"]["player_facing_text"].lower()
    for key in ("world", "scene", "character", "combat"):
        assert before[key] == after[key]
    for key in ("turn_counter", "clocks"):
        assert before["session"][key] == after["session"][key]
