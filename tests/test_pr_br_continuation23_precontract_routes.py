"""PR-BR C23: deterministic route probes. No paid model calls.

call_gpt and the interpretation client are patched to fail closed.
ASHEN_DISABLE_LIVE_INTERPRETATION keeps interpretation off even if a path asks.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from game.api import app
from game.defaults import (
    default_campaign,
    default_character,
    default_combat,
    default_conditions,
    default_session,
    default_world,
)
from game.semantic_interpreter import _invoke_interpretation_model
from game import storage
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _seed_campaign_start_storage

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "artifacts" / "pr_br_continuation23" / "q_probes.json"

PROBES = [
    ("Q1", "Who is nearby?"),
    ("Q2", "Can I find supplies nearby?"),
    ("Q3", "I ask the runner if there are supplies nearby."),
    ("Q4", "I listen at the door."),
    ("Q5", "I ask the guard and listen carefully."),
    ("Q6", "I inspect the footprints."),
    ("Q7", "I follow the road to the milestone."),
    ("Q8", "Would the road lead to the milestone?"),
    ("Q9", "I use the key on the door."),
    ("Q10", "What does the notice say?"),
    ("Q11", "I ask the tavern runner what he heard about the patrol."),
    ("Q12", "((ooc)) what should I roll?"),
    (
        "C22",
        'Thank you for the warning. Have you heard anything about who or what might be causing trouble there? Any chance I could find shelter or supplies nearby before investigating further?',
    ),
    (
        "C22-exact",
        'I nod thoughtfully, glancing toward the northwest where the crates stand drenched in rain. "Thank you for the warning. Have you heard anything about who or what might be causing trouble there? Any chance I could find shelter or supplies nearby before investigating further?',
    ),
]


def _seed(tmp_path, monkeypatch):
    monkeypatch.setenv("ASHEN_DISABLE_LIVE_INTERPRETATION", "1")
    _seed_campaign_start_storage(tmp_path, monkeypatch)
    session = default_session()
    session["active_scene_id"] = "frontier_gate"
    session["visited_scene_ids"] = ["frontier_gate"]
    session["turn_counter"] = 1
    storage.save_session(session)
    storage._save_json(storage.WORLD_PATH, default_world())
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())


def test_q_probes_do_not_call_models(tmp_path, monkeypatch):
    _seed(tmp_path, monkeypatch)
    calls = {"gpt": 0, "interpretation": 0}

    def fail_interpretation(*_args, **_kwargs):
        calls["interpretation"] += 1
        raise AssertionError("interpretation model invoked")

    def stub_gpt(*_args, **_kwargs):
        calls["gpt"] += 1
        return _gm_response("Stub narration. Nothing further is established.")

    monkeypatch.setattr("game.semantic_interpreter._invoke_interpretation_model", fail_interpretation)
    monkeypatch.setattr("game.api.call_gpt", stub_gpt)
    monkeypatch.setattr("game.gm.call_gpt", stub_gpt)
    assert _invoke_interpretation_model is not None

    from game.adjudication import classify_adjudication_query
    from game.intent_parser import segment_mixed_player_turn

    client = TestClient(app)
    rows = []
    for label, text in PROBES:
        _seed(tmp_path, monkeypatch)
        session = storage.load_session()
        world = storage.load_world()
        scene = storage.load_scene("frontier_gate")
        segmented = segment_mixed_player_turn(text)
        clause = segmented.get("adjudication_question_text") or text
        category = classify_adjudication_query(
            clause,
            has_active_interaction=False,
            session=session,
            world=world,
            scene=scene,
        )
        before = calls["gpt"]
        payload = client.post("/api/chat", json={"text": text}).json()
        resolution = payload.get("resolution") if isinstance(payload.get("resolution"), dict) else {}
        meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
        contract = meta.get("resolution_contract") if isinstance(meta.get("resolution_contract"), dict) else {}
        route = meta.get("intent_route_debug") if isinstance(meta.get("intent_route_debug"), dict) else {}
        gm = payload.get("gm_output") if isinstance(payload.get("gm_output"), dict) else {}
        gm_meta = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
        accepted = gm_meta.get("accepted_response") if isinstance(gm_meta.get("accepted_response"), dict) else {}
        seg = meta.get("turn_segmentation") if isinstance(meta.get("turn_segmentation"), dict) else payload.get("segmented_turn")
        rows.append(
            {
                "id": label,
                "input": text,
                "classifier_on_clause": category,
                "clause": clause if clause != text else None,
                "kind": resolution.get("kind"),
                "route_reason": route.get("route_reason") or meta.get("canonical_entry_reason"),
                "routed_to": route.get("routed_to"),
                "canonical_reason": meta.get("canonical_entry_reason"),
                "contract": bool(contract.get("contract_id")),
                "operation": contract.get("operation"),
                "dimension": contract.get("dimension"),
                "interlocutor_id": contract.get("interlocutor_id"),
                "gpt_calls_this_turn": calls["gpt"] - before,
                "accepted": bool(accepted.get("text")),
                "visible": str(gm.get("player_facing_text") or "")[:220],
                "scene": (payload.get("session") or {}).get("active_scene_id"),
                "segment": seg,
            }
        )
    assert calls["interpretation"] == 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({"gpt_stub_calls": calls["gpt"], "interpretation_calls": 0, "rows": rows}, indent=2), encoding="utf-8")
    assert len(rows) == len(PROBES)


def test_exact_c22_after_runner_still_bypasses_contract(tmp_path, monkeypatch):
    """Prior social turn, then the live C22 wording. The contract now exists first."""
    _seed(tmp_path, monkeypatch)

    def stub_gpt(*_args, **_kwargs):
        return _gm_response('The tavern runner says, "The patrol went northwest of the crates."')

    monkeypatch.setattr("game.semantic_interpreter._invoke_interpretation_model", lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("interpretation model")))
    monkeypatch.setattr("game.api.call_gpt", stub_gpt)
    monkeypatch.setattr("game.gm.call_gpt", stub_gpt)
    client = TestClient(app)
    first = client.post(
        "/api/chat",
        json={"text": "I ask the tavern runner what he heard about the patrol."},
    ).json()
    second = client.post(
        "/api/chat",
        json={
            "text": 'I nod thoughtfully, glancing toward the northwest where the crates stand drenched in rain. "Thank you for the warning. Have you heard anything about who or what might be causing trouble there? Any chance I could find shelter or supplies nearby before investigating further?'
        },
    ).json()
    resolution = second.get("resolution") if isinstance(second.get("resolution"), dict) else {}
    meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    contract = meta.get("resolution_contract") if isinstance(meta.get("resolution_contract"), dict) else {}
    gm = second.get("gm_output") if isinstance(second.get("gm_output"), dict) else {}
    gm_meta = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
    debug = gm_meta.get("emission_debug") if isinstance(gm_meta.get("emission_debug"), dict) else {}
    record = {
        "first_interlocutor": ((first.get("resolution") or {}).get("metadata") or {}).get("resolution_contract", {}).get("interlocutor_id")
        if isinstance(first.get("resolution"), dict)
        else None,
        "second_kind": resolution.get("kind"),
        "second_contract": bool(contract.get("contract_id")),
        "second_reason": meta.get("canonical_entry_reason"),
        "second_route": (meta.get("intent_route_debug") or {}).get("route_reason")
        if isinstance(meta.get("intent_route_debug"), dict)
        else None,
        "visible": str(gm.get("player_facing_text") or ""),
        "tags": gm.get("tags"),
        "path_kind": gm_meta.get("narration_path_kind") or gm.get("narration_path_kind"),
        "repair_kind": debug.get("response_type_repair_kind"),
        "final_emitted_source": (gm_meta.get("_final_emission_meta") or debug).get("final_emitted_source")
        if isinstance(gm_meta.get("_final_emission_meta") or debug, dict)
        else None,
        "debug_keys": sorted(debug.keys())[:40],
        "accepted": bool(((gm.get("metadata") or {}).get("accepted_response") or {}).get("text"))
        if isinstance(gm.get("metadata"), dict)
        else False,
    }
    path = ROOT / "artifacts" / "pr_br_continuation24" / "c22_after_runner_repaired.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    assert record["second_contract"] is True
    assert "The guard says" not in record["visible"]
    assert "In earshot right now" not in record["visible"]


def test_adjudication_branch_does_not_attach_contract():
    """Static: the unparsed arm attaches a contract before resolver selection."""
    source = (ROOT / "game" / "api.py").read_text(encoding="utf-8")
    start = source.index("Ordinary gameplay builds the Resolution Contract")
    end = source.index("if adjudication is not None:", start)
    arm = source[start:end]
    assert arm.index("attach_interaction_obligation(") < arm.index("select_resolver_family(")
    assert "resolve_adjudication_query(" not in arm
