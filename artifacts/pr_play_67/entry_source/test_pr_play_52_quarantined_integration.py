"""Quarantined investigation narration on the existing chat pipeline.

Provider transports stay disabled. The exploration resolver decides each outcome.
"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import shutil
import statistics
import time

import pytest
from fastapi.testclient import TestClient

from game import api, exploration, storage
from game.defaults import default_campaign, default_character, default_combat, default_conditions, default_session, default_world
from game.quarantined_investigation_narration import (
    EVIDENCE_ENV,
    FAULT_ENV,
    GATE_ENV,
    LABEL_ENV,
    SAMPLE_ENV,
    clear_evidence,
    evidence_records,
    hook_is_active,
    observe_completed_investigation,
)
from tests.helpers.turn_pipeline_http_fixtures import _patch_storage

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "pr_play_52"
NOTICE = "I examine the notice board."
PRINTS = "I examine the footprints."
NOTICE_CLUE = "The missing patrol was last seen taking the northwest mud track past the crates."
PRINT_CLUE = (
    "Faint overlapping prints mark the mud around the old milestone, "
    "but their number, origin, and direction stay unclear."
)
CANARIES = (
    "CANARY_UNDISCOVERED_CLUE",
    "CANARY_GM_NOTE",
    "CANARY_NPC_MOTIVE",
    "CANARY_HIDDEN_DESTINATION",
    "CANARY_QUEST_TWIST",
    "CANARY_MECHANICAL_ID",
    "CANARY_UNRELATED_WORLD",
)
HIDDEN_FACTS = (
    "An agent of a noble house is watching new arrivals from the square's edge.",
    "A contact tied to the Ash Cowl smuggling web is scouting the crowd for arcane talent.",
    "The threadbare watcher is waiting on a coordinated signal from someone already past the checkpoint.",
    "A spotter above the lane is matching faces to a written list paid for in silver.",
)
RESULTS: list[dict] = []


def _forbid_provider(monkeypatch):
    calls = {"openai": 0}

    class OpenAI:
        def __init__(self, *args, **kwargs):
            calls["openai"] += 1
            raise AssertionError("real provider client constructed")

    try:
        import openai
    except Exception:
        openai = None
    if openai is not None:
        monkeypatch.setattr(openai, "OpenAI", OpenAI, raising=False)
    monkeypatch.setenv("ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT", "1")
    monkeypatch.setenv("ASHEN_DISABLE_LIVE_INTERPRETATION", "1")
    monkeypatch.setenv("ASHEN_DISABLE_EXPRESSION_GENERATION", "1")
    monkeypatch.setenv("ASHEN_DISABLE_PROVIDER_CALLS", "1")
    monkeypatch.setenv("ASHEN_DISABLE_PROVIDER_RETRIES", "1")
    return calls


def _seed(tmp_path, monkeypatch, scene_id: str):
    _patch_storage(tmp_path, monkeypatch)
    if storage.SCENES_DIR.exists():
        shutil.rmtree(storage.SCENES_DIR)
    storage.SCENES_DIR.mkdir(parents=True, exist_ok=True)
    for path in (ROOT / "data" / "scenes").glob("*.json"):
        shutil.copy2(path, storage.SCENES_DIR / path.name)
    scene_path = storage.scene_path(scene_id)
    scene = json.loads(scene_path.read_text(encoding="utf-8"))
    hidden = list(scene["scene"].get("hidden_facts") or [])
    hidden.append("CANARY_HIDDEN_DESTINATION")
    scene["scene"]["hidden_facts"] = hidden
    scene["scene"]["gm_notes"] = ["CANARY_GM_NOTE"]
    scene["scene"]["private_notes"] = "CANARY_NPC_MOTIVE"
    scene["scene"]["discoverable_clues"] = list(scene["scene"].get("discoverable_clues") or [])
    scene["scene"]["discoverable_clues"].append({
        "id": "CANARY_MECHANICAL_ID",
        "text": "CANARY_UNDISCOVERED_CLUE",
    })
    storage._save_json(scene_path, scene)
    world = default_world()
    world["gm_only"] = {"motivation": "CANARY_NPC_MOTIVE", "quest": "CANARY_QUEST_TWIST"}
    world["unrelated_state"] = "CANARY_UNRELATED_WORLD"
    storage._save_json(storage.WORLD_PATH, world)
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    session = default_session()
    session["active_scene_id"] = scene_id
    session["visited_scene_ids"] = [scene_id]
    session["campaign_started"] = True
    session["turn_counter"] = 1
    session["gm_notes"] = ["CANARY_GM_NOTE"]
    session["quest_journal"] = [{"secret": "CANARY_QUEST_TWIST"}]
    storage.save_session(session)
    storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")
    return {
        "session": copy.deepcopy(storage.load_session()),
        "world": copy.deepcopy(storage.load_world()),
        "character": copy.deepcopy(storage.load_character()),
        "combat": copy.deepcopy(storage.load_combat()),
    }


def _snapshot():
    return {
        "session": storage.load_session(),
        "world": storage.load_world(),
        "character": storage.load_character(),
        "combat": storage.load_combat(),
        "conditions": storage.load_conditions() if storage.CONDITIONS_PATH.exists() else None,
        "log": storage.load_log(),
        "scene_id": (storage.load_session() or {}).get("active_scene_id"),
    }


def _guard_writers(monkeypatch):
    hits = []

    def wrap(name, original):
        def guarded(*args, **kwargs):
            if hook_is_active():
                hits.append(name)
                raise AssertionError(f"quarantine hook called {name}")
            return original(*args, **kwargs)
        return guarded

    monkeypatch.setattr(storage, "_atomic_save_json", wrap("_atomic_save_json", storage._atomic_save_json))
    monkeypatch.setattr(storage, "_save_json", wrap("_save_json", storage._save_json))
    monkeypatch.setattr(storage, "append_log", wrap("append_log", storage.append_log))
    monkeypatch.setattr(storage, "save_session", wrap("save_session", storage.save_session))
    monkeypatch.setattr(storage, "save_world", wrap("save_world", storage.save_world))
    monkeypatch.setattr(storage, "save_character", wrap("save_character", storage.save_character))
    monkeypatch.setattr(storage, "save_combat", wrap("save_combat", storage.save_combat))
    return hits


def _count_resolvers(monkeypatch):
    counts = {"exploration": 0, "social": 0}
    explore = exploration.resolve_exploration_action

    def wrapped_explore(*args, **kwargs):
        counts["exploration"] += 1
        return explore(*args, **kwargs)

    import game.social as social
    social_fn = social.resolve_social_action

    def wrapped_social(*args, **kwargs):
        counts["social"] += 1
        return social_fn(*args, **kwargs)

    monkeypatch.setattr(exploration, "resolve_exploration_action", wrapped_explore)
    monkeypatch.setattr(api, "resolve_exploration_action", wrapped_explore)
    monkeypatch.setattr(social, "resolve_social_action", wrapped_social)
    monkeypatch.setattr(api, "resolve_social_action", wrapped_social)
    return counts


def _play(tmp_path, monkeypatch, scene_id, text, *, gate=False, sample="stub", fault="", label="run"):
    initial = _seed(tmp_path, monkeypatch, scene_id)
    provider = _forbid_provider(monkeypatch)
    writers = _guard_writers(monkeypatch)
    resolvers = _count_resolvers(monkeypatch)
    if gate:
        monkeypatch.setenv(GATE_ENV, "1")
        monkeypatch.setenv(SAMPLE_ENV, sample)
        monkeypatch.setenv(FAULT_ENV, fault)
        monkeypatch.setenv(LABEL_ENV, label)
        monkeypatch.setenv(EVIDENCE_ENV, str(tmp_path / "quarantine"))
    else:
        monkeypatch.delenv(GATE_ENV, raising=False)
        monkeypatch.delenv(SAMPLE_ENV, raising=False)
        monkeypatch.delenv(FAULT_ENV, raising=False)
        monkeypatch.delenv(EVIDENCE_ENV, raising=False)
    clear_evidence()
    started = time.perf_counter()
    with TestClient(api.app) as client:
        response = client.post("/api/chat?ui_mode=player", json={"text": text})
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
    body = response.json()
    return {
        "status_code": response.status_code,
        "elapsed_ms": elapsed_ms,
        "body": body,
        "initial": initial,
        "final": _snapshot(),
        "provider_clients": provider["openai"],
        "hook_writer_calls": list(writers),
        "resolver_calls": dict(resolvers),
        "quarantine": evidence_records(),
        "player_text": text,
        "scene_id": scene_id,
        "gate": gate,
        "sample": sample if gate else None,
        "fault": fault if gate else None,
    }


def _facing(run) -> str:
    gm = (run["body"].get("gm_output") or {}) if isinstance(run["body"], dict) else {}
    return str(gm.get("player_facing_text") or "")


def _resolution(run) -> dict:
    body = run["body"] if isinstance(run["body"], dict) else {}
    if isinstance(body.get("resolution"), dict):
        return body["resolution"]
    log = run["final"]["log"]
    if log and isinstance(log[-1].get("resolution"), dict):
        return log[-1]["resolution"]
    return {}


def _mechanical(resolution: dict) -> dict:
    changes = resolution.get("state_changes") if isinstance(resolution.get("state_changes"), dict) else {}
    return {
        "kind": resolution.get("kind"),
        "success": resolution.get("success"),
        "action_id": resolution.get("action_id"),
        "interactable_id": resolution.get("interactable_id"),
        "clue_id": resolution.get("clue_id"),
        "clue_text": resolution.get("clue_text"),
        "discovered_clues": resolution.get("discovered_clues"),
        "resolved_transition": resolution.get("resolved_transition"),
        "target_scene_id": resolution.get("target_scene_id"),
        "state_changes": {
            "clue_revealed": changes.get("clue_revealed"),
            "already_searched": changes.get("already_searched"),
            "skill_check_failed": changes.get("skill_check_failed"),
            "interactable_id": changes.get("interactable_id"),
        },
    }


# Generated per run. Clue ids, scene ids, and mechanical fields are not in this set.
_VOLATILE_KEYS = {
    "timestamp", "timestamps", "created_at", "updated_at", "run_id", "trace_id",
    "campaign_run_id", "session_id", "canonical_gm_object_id",
}
_VOLATILE_SUFFIXES = ("_ms", "_stamp", "_stamp_v1")


def _volatile_key(key: str) -> bool:
    return (
        key in _VOLATILE_KEYS
        or "timestamp" in key
        or "latency" in key
        or "stamp" in key
        or key.endswith(_VOLATILE_SUFFIXES)
    )


def _scrub(value):
    if isinstance(value, dict):
        return {
            key: _scrub(item)
            for key, item in value.items()
            if not _volatile_key(str(key))
        }
    if isinstance(value, list):
        return [_scrub(item) for item in value]
    if isinstance(value, str) and len(value) >= 20 and value[4:5] == "-" and "T" in value[:30]:
        return "<timestamp>"
    return value


def _diff(left, right, path="$"):
    if type(left) is not type(right):
        return [f"{path}: {type(left).__name__} != {type(right).__name__}"]
    if isinstance(left, dict):
        rows = []
        for key in sorted(set(left) | set(right)):
            if key not in left or key not in right:
                rows.append(f"{path}.{key}: present {key in left} vs {key in right}")
            else:
                rows.extend(_diff(left[key], right[key], f"{path}.{key}"))
        return rows
    if isinstance(left, list):
        if len(left) != len(right):
            return [f"{path}: len {len(left)} != {len(right)}"]
        rows = []
        for index, (a, b) in enumerate(zip(left, right)):
            rows.extend(_diff(a, b, f"{path}[{index}]"))
        return rows
    if left != right:
        return [f"{path}: {left!r} != {right!r}"]
    return []


def _public_compare(run_a, run_b):
    facing = _facing(run_a) == _facing(run_b)
    mechanical = _mechanical(_resolution(run_a)) == _mechanical(_resolution(run_b))
    state = _diff(_scrub(run_a["final"]), _scrub(run_b["final"]))
    return {"player_facing_identical": facing, "mechanical_identical": mechanical, "state_differences": state}


def _blob(*parts) -> str:
    return json.dumps(parts, ensure_ascii=False)


def _assert_no_canaries(payload: str):
    leaked = [item for item in list(CANARIES) + list(HIDDEN_FACTS) if item in payload]
    for token in ("notice_patrol_route", "milestone_mud_prints", "market_quarter", "old_milestone"):
        if token in payload:
            leaked.append(token)
    assert leaked == [], leaked


@pytest.fixture(scope="module", autouse=True)
def _persist_results():
    RESULTS.clear()
    yield
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "integration_results.json").write_text(json.dumps(RESULTS, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _record(name, payload):
    RESULTS.append({"name": name, **payload})


def test_gate_defaults_off(tmp_path, monkeypatch):
    run = _play(tmp_path, monkeypatch, "frontier_gate", NOTICE, gate=False, label="notice_baseline_gate")
    assert run["status_code"] == 200, run["body"]
    assert run["quarantine"] == []
    assert run["provider_clients"] == 0
    assert run["resolver_calls"]["exploration"] == 1
    assert NOTICE_CLUE in (_resolution(run).get("clue_text") or "")
    assert "quarantine" not in json.dumps(run["body"]).casefold()
    _record("gate_off_notice", {
        "mechanical": _mechanical(_resolution(run)),
        "player_facing": _facing(run),
        "resolver_calls": run["resolver_calls"],
        "provider_clients": run["provider_clients"],
        "quarantine_records": 0,
    })


def test_notice_board_paired_gameplay(tmp_path, monkeypatch):
    baseline = _play(tmp_path, monkeypatch, "frontier_gate", NOTICE, gate=False, label="notice_baseline")
    experimental = _play(
        tmp_path, monkeypatch, "frontier_gate", NOTICE,
        gate=True, sample="A1", label="notice_experimental",
    )
    compared = _public_compare(baseline, experimental)
    resolution = _resolution(experimental)
    quarantine = experimental["quarantine"]
    assert baseline["status_code"] == experimental["status_code"] == 200
    assert resolution.get("success") is True
    assert resolution.get("clue_text") == NOTICE_CLUE
    assert compared["player_facing_identical"] is True
    assert compared["mechanical_identical"] is True
    assert compared["state_differences"] == [], "\n".join(compared["state_differences"])
    assert baseline["resolver_calls"] == experimental["resolver_calls"] == {"exploration": 1, "social": 0}
    assert experimental["provider_clients"] == 0
    assert experimental["hook_writer_calls"] == []
    assert len(quarantine) == 1
    record = quarantine[0]
    assert record["diagnostic"] == "heuristic_pass_pending_review"
    assert record["used_fallback"] is False
    assert record["anchors"][0]["text"] == NOTICE_CLUE
    assert record["assembled"].endswith(NOTICE_CLUE)
    assert record["raw_provider_text"] in record["assembled"]
    assert record["generator_calls"] == 1
    assert record["sample"] == "A1"
    assert NOTICE_CLUE not in record["raw_provider_text"]
    hook_blob = _blob(record["hook_input"], record.get("generator_request"), record.get("authorized_narration_projection"))
    _assert_no_canaries(hook_blob)
    assert record["assembled"] not in _facing(experimental)
    assert "quarantine" not in json.dumps(experimental["body"]).casefold()
    _record("notice_board", {
        "baseline": {"mechanical": _mechanical(_resolution(baseline)), "player_facing": _facing(baseline),
                     "resolver_calls": baseline["resolver_calls"], "elapsed_ms": baseline["elapsed_ms"]},
        "experimental": {"mechanical": _mechanical(resolution), "player_facing": _facing(experimental),
                         "resolver_calls": experimental["resolver_calls"], "elapsed_ms": experimental["elapsed_ms"],
                         "diagnostic": record["diagnostic"], "assembled": record["assembled"],
                         "raw_provider_text": record["raw_provider_text"], "anchors": record["anchors"],
                         "hook_input": record["hook_input"], "projection": record["authorized_narration_projection"],
                         "validation": record["validation"], "timings": _timings(record)},
        "comparison": compared,
        "provider_clients": experimental["provider_clients"],
        "hook_writer_calls": experimental["hook_writer_calls"],
    })


def test_footprints_paired_gameplay(tmp_path, monkeypatch):
    baseline = _play(tmp_path, monkeypatch, "old_milestone", PRINTS, gate=False, label="prints_baseline")
    experimental = _play(
        tmp_path, monkeypatch, "old_milestone", PRINTS,
        gate=True, sample="B1", label="prints_experimental",
    )
    compared = _public_compare(baseline, experimental)
    resolution = _resolution(experimental)
    record = experimental["quarantine"][0]
    assert resolution.get("success") is True
    assert resolution.get("clue_text") == PRINT_CLUE
    assert compared["player_facing_identical"] is True
    assert compared["mechanical_identical"] is True
    assert compared["state_differences"] == [], "\n".join(compared["state_differences"])
    assert experimental["resolver_calls"] == {"exploration": 1, "social": 0}
    assert experimental["provider_clients"] == 0
    assert experimental["hook_writer_calls"] == []
    assert record["used_fallback"] is False, json.dumps({
        "diagnostic": record.get("diagnostic"),
        "validation": record.get("validation"),
        "error": record.get("error"),
        "anchors": [anchor.get("text") for anchor in record.get("anchors") or []],
    }, ensure_ascii=False)[:2000]
    assert record["anchors"][0]["text"] == PRINT_CLUE
    assert record["assembled"].count(PRINT_CLUE) == 1
    for forbidden in ("exactly three", "culprit", "salt fortress", "hidden passage", "the patrol went"):
        assert forbidden not in record["assembled"].casefold()
    _assert_no_canaries(_blob(record["hook_input"], record.get("generator_request")))
    assert record["assembled"] not in _facing(experimental)
    _record("footprints", {
        "baseline": {"mechanical": _mechanical(_resolution(baseline)), "player_facing": _facing(baseline),
                     "elapsed_ms": baseline["elapsed_ms"]},
        "experimental": {"mechanical": _mechanical(resolution), "player_facing": _facing(experimental),
                         "elapsed_ms": experimental["elapsed_ms"], "diagnostic": record["diagnostic"],
                         "assembled": record["assembled"], "raw_provider_text": record["raw_provider_text"],
                         "anchors": record["anchors"], "hook_input": record["hook_input"],
                         "projection": record["authorized_narration_projection"], "validation": record["validation"],
                         "timings": _timings(record)},
        "comparison": compared,
        "provider_clients": experimental["provider_clients"],
        "hook_writer_calls": experimental["hook_writer_calls"],
        "resolver_calls": experimental["resolver_calls"],
    })


def _timings(record: dict) -> dict:
    return {
        key: record.get(key)
        for key in (
            "projection_build_ms", "projection_ms", "saved_lookup_ms", "validation_ms",
            "assembly_ms", "serialization_ms", "evidence_write_ms", "hook_work_ms", "total_hook_ms",
        )
    }


def test_saved_responses_stay_paired(tmp_path, monkeypatch):
    expected = {
        "A1": ("frontier_gate", NOTICE, NOTICE_CLUE, False),
        "A2": ("frontier_gate", NOTICE, NOTICE_CLUE, False),
        "B1": ("old_milestone", PRINTS, PRINT_CLUE, False),
        "B2": ("old_milestone", PRINTS, PRINT_CLUE, False),
    }
    rows = []
    for sample, (scene_id, text, clue, fallback) in expected.items():
        run = _play(tmp_path, monkeypatch, scene_id, text, gate=True, sample=sample, label=f"replay_{sample}")
        record = run["quarantine"][0]
        assert _resolution(run).get("clue_text") == clue
        assert record["raw_provider_text"]
        assert record["extraction_matches_raw"] is True
        assert record["anchors"][0]["text"] == clue
        assert record["assembled"].count(clue) == 1
        assert record["used_fallback"] is fallback
        assert record["generator_calls"] == 1
        assert record["provider_requests"] == 0
        assert run["provider_clients"] == 0
        _assert_no_canaries(_blob(record["hook_input"], record.get("generator_request")))
        rows.append({
            "sample": sample,
            "diagnostic": record["diagnostic"],
            "used_fallback": record["used_fallback"],
            "raw_provider_text": record["raw_provider_text"],
            "assembled": record["assembled"],
            "anchors": record["anchors"],
            "validation": record["validation"],
            "player_facing": _facing(run),
            "mechanical": _mechanical(_resolution(run)),
        })
    mismatched = _play(tmp_path, monkeypatch, "old_milestone", PRINTS, gate=True, sample="A1", label="mismatch_A1_on_prints")
    mismatch = mismatched["quarantine"][0]
    assert mismatch["diagnostic"] == "incorrect_investigation_response_pairing"
    assert mismatch["used_fallback"] is True
    assert mismatch["anchors"][0]["text"] == PRINT_CLUE
    assert mismatch["raw_provider_text"] not in mismatch["assembled"]
    assert mismatch["generator_calls"] == 0
    assert _facing(mismatched) == _facing(_play(tmp_path, monkeypatch, "old_milestone", PRINTS, gate=False))
    rows.append({
        "sample": "A1_on_footprints",
        "diagnostic": mismatch["diagnostic"],
        "used_fallback": True,
        "raw_provider_text": mismatch["raw_provider_text"],
        "assembled": mismatch["assembled"],
        "anchors": mismatch["anchors"],
    })
    _record("saved_replays", {"rows": rows})


def test_anchor_integrity_follows_the_resolver(tmp_path, monkeypatch):
    monkeypatch.setenv("ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT", "1")
    monkeypatch.setenv("ASHEN_DISABLE_LIVE_INTERPRETATION", "1")
    monkeypatch.setenv("ASHEN_DISABLE_EXPRESSION_GENERATION", "1")
    monkeypatch.setenv("ASHEN_DISABLE_PROVIDER_CALLS", "1")
    _seed(tmp_path, monkeypatch, "frontier_gate")
    monkeypatch.setenv(GATE_ENV, "1")
    monkeypatch.setenv(SAMPLE_ENV, "stub")
    monkeypatch.setenv(FAULT_ENV, "")
    monkeypatch.setenv(LABEL_ENV, "anchor_sequence")
    monkeypatch.setenv(EVIDENCE_ENV, str(tmp_path / "quarantine"))
    from tests.helpers.live_model_guard import production_call_gpt

    # Repeat searches are not on the deterministic skip path, so production
    # would call the narrator. Restore that function with provider calls
    # disabled; the OpenAI constructor remains blocked by the test guard.
    monkeypatch.setattr("game.gm.call_gpt", production_call_gpt())
    monkeypatch.setattr("game.api.call_gpt", production_call_gpt())
    clear_evidence()

    def post(text):
        client = TestClient(api.app)
        client.__enter__()
        try:
            return client.post("/api/chat?ui_mode=player", json={"text": text})
        finally:
            try:
                client.__exit__(None, None, None)
            except Exception:
                # Starlette's test portal can cancel on a second lifespan in this
                # process. The HTTP response above is the gameplay result.
                pass

    first = post(NOTICE)
    second = post(NOTICE)
    barrel = post("I examine the rain barrel.")
    assert first.status_code == second.status_code == barrel.status_code == 200
    records = evidence_records()
    assert records[0]["anchors"][0]["text"] == NOTICE_CLUE
    assert records[0]["anchors"][0]["status"] == "newly_revealed"
    known = records[1]
    assert known["diagnostic"] != "unexpected_experimental_hook_exception"
    assert all(anchor["status"] != "newly_revealed" for anchor in known["anchors"])
    assert NOTICE_CLUE in known["assembled"]
    assert "nothing new" in known["assembled"].casefold()
    barrel_body = barrel.json()
    barrel_resolution = barrel_body.get("resolution") if isinstance(barrel_body.get("resolution"), dict) else {}
    barrel_record = records[2] if len(records) > 2 else None
    discovered = barrel_resolution.get("discovered_clues") or []
    if barrel_record and barrel_record.get("anchors"):
        for anchor in barrel_record["anchors"]:
            if anchor["status"] == "newly_revealed":
                assert anchor["text"] in discovered
        assert "CANARY_UNDISCOVERED_CLUE" not in barrel_record["assembled"]
    elif barrel_record:
        assert barrel_record.get("assembled") in (None, "")
        assert NOTICE_CLUE not in json.dumps(barrel_record.get("hook_input"))
    _record("anchor_integrity", {
        "first": {"diagnostic": records[0]["diagnostic"], "anchors": records[0]["anchors"], "assembled": records[0]["assembled"]},
        "previously_known": {"diagnostic": known["diagnostic"], "anchors": known["anchors"], "assembled": known["assembled"],
                             "mechanical": _mechanical(second.json().get("resolution") or {})},
        "rain_barrel": {
            "player_facing": (barrel_body.get("gm_output") or {}).get("player_facing_text"),
            "mechanical": _mechanical(barrel_resolution),
            "quarantine": barrel_record,
        },
    })


@pytest.mark.parametrize("fault,sample,diagnostic", [
    ("", "missing", "missing_saved_prelude"),
    ("", "empty", "invalid_prelude"),
    ("", "malformed", "invalid_prelude"),
    ("", "unsafe", "semantic_rejection"),
    ("assembly_exception", "stub", "generator_or_renderer_error"),
    ("invalid_projection", "stub", "invalid_authorized_projection"),
    ("", "A1", "incorrect_investigation_response_pairing"),
    ("timeout", "stub", "simulated_timeout"),
    ("evidence_write", "stub", "heuristic_pass_pending_review"),
    ("unexpected", "stub", "unexpected_experimental_hook_exception"),
])
def test_failure_stays_outside_gameplay(tmp_path, monkeypatch, fault, sample, diagnostic):
    scene_id, text, clue = ("old_milestone", PRINTS, PRINT_CLUE) if sample == "A1" else ("frontier_gate", NOTICE, NOTICE_CLUE)
    baseline = _play(tmp_path, monkeypatch, scene_id, text, gate=False)
    failed = _play(
        tmp_path, monkeypatch, scene_id, text,
        gate=True, sample=sample, fault=fault, label=f"fault_{fault or sample}",
    )
    compared = _public_compare(baseline, failed)
    record = failed["quarantine"][0]
    assert failed["status_code"] == 200
    assert compared["player_facing_identical"] is True
    assert compared["mechanical_identical"] is True
    assert compared["state_differences"] == [], "\n".join(compared["state_differences"])
    assert _resolution(failed).get("clue_text") == clue
    assert failed["resolver_calls"]["exploration"] == 1
    assert failed["provider_clients"] == 0
    assert failed["hook_writer_calls"] == []
    assert record["diagnostic"] == diagnostic
    if fault == "evidence_write":
        assert record["evidence_write"] == "failed"
    if diagnostic != "invalid_authorized_projection":
        assert any(anchor["text"] == clue for anchor in record.get("anchors") or [])
    else:
        assert record.get("anchors") == []
        assert clue not in (record.get("assembled") or "")
    assert record.get("generator_calls", 0) <= 1
    _record("failure_" + (fault or sample), {
        "diagnostic": record["diagnostic"],
        "evidence_write": record.get("evidence_write"),
        "used_fallback": record.get("used_fallback"),
        "player_facing_identical": True,
        "mechanical": _mechanical(_resolution(failed)),
        "assembled": record.get("assembled"),
        "anchors": record.get("anchors"),
        "error": record.get("error"),
    })


def test_hook_overhead_distribution(tmp_path, monkeypatch):
    run = _play(tmp_path, monkeypatch, "frontier_gate", NOTICE, gate=True, sample="A1", label="perf_source")
    record = run["quarantine"][0]
    scene = storage.load_active_scene()
    resolution = _resolution(run)
    known = tuple(row["text"] for row in record["hook_input"]["narration_payload"]["scene"]["discovered_clues"])
    monkeypatch.setenv(GATE_ENV, "1")
    monkeypatch.setenv(SAMPLE_ENV, "A1")
    monkeypatch.setenv(FAULT_ENV, "")
    monkeypatch.setenv(LABEL_ENV, "perf")
    monkeypatch.setenv(EVIDENCE_ENV, str(tmp_path / "perf"))
    samples = []
    for _ in range(31):
        clear_evidence()
        observed = observe_completed_investigation(
            resolution=resolution,
            scene=scene,
            known_clue_texts=known,
            player_text=NOTICE,
        )
        samples.append(observed)
    def series(key):
        values = [row[key] for row in samples if isinstance(row.get(key), (int, float))]
        values_sorted = sorted(values)
        return {
            "n": len(values),
            "mean_ms": round(statistics.fmean(values), 3) if values else None,
            "median_ms": round(statistics.median(values), 3) if values else None,
            "max_ms": round(max(values), 3) if values else None,
            "min_ms": round(min(values), 3) if values else None,
        }
    work = series("hook_work_ms")
    total = series("total_hook_ms")
    write = series("evidence_write_ms")
    outlier = None
    totals = [row["total_hook_ms"] for row in samples]
    median = statistics.median(totals)
    if totals and max(totals) > max(3 * median, median + 25):
        outlier = max(totals)
    assert all(row["diagnostic"] == "heuristic_pass_pending_review" for row in samples)
    assert all(row["anchors"][0]["text"] == NOTICE_CLUE for row in samples)
    _record("performance", {
        "in_turn": _timings(record),
        "full_turn_elapsed_ms": run["elapsed_ms"],
        "repeats": 31,
        "hook_work": work,
        "total_with_evidence": total,
        "evidence_write": write,
        "projection_build": series("projection_build_ms"),
        "saved_lookup": series("saved_lookup_ms"),
        "validation": series("validation_ms"),
        "assembly": series("assembly_ms"),
        "outlier_total_ms": outlier,
        "provider_latency_included": False,
        "note": "Repeated on the resolution and scene captured from the gameplay turn. No provider call.",
    })
