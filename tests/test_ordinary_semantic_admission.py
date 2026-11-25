"""Real HTTP admission before time, gameplay and publication authority."""
import copy
import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from game import storage
from game.api import app
from game.integrated_play import _LANES
from game.provider_budget import snapshot
from tests.pr_play_79df3_harness import CANARIES, seed_gate


def state():
    return copy.deepcopy({"session": storage.load_session(), "character": storage.load_character(),
                          "world": storage.load_world(), "scene": storage.load_active_scene(),
                          "combat": storage.load_combat()})


@pytest.mark.parametrize("case,text,terms", [
    ("headcount", "Do we know how many people took the northwest track?", ("No reliable count", "zero")),
    ("headcount_variant", "How many scouts crossed the ridge?", ("No reliable count", "zero")),
    ("comparison", "How does the notice compare with what the captain said?", ("cannot establish both accounts", "accounts should I compare")),
    ("unanswered_inventory", "Am I carrying a spellbook?", ("inventory records", "Spellbook")),
    ("shelter", "I shelter my spellbook under the notice board.", ("Nothing has been attempted", "specific action")),
    ("plan", "The patrol used the northwest track, so I plan to look for footprints there.", ("Nothing has been attempted", "resolve now")),
    ("negated_travel", "Instead of entering the gate, I wait beside the rain barrel.", ("Nothing has been attempted", "specific action")),
    ("unclassified", "I rearrange the echoes into a ladder.", ("Nothing has been attempted", "specific action")),
])
def test_http_nonexecution_is_relevant_and_preserves_authority(tmp_path, monkeypatch, case, text, terms):
    seed_gate(tmp_path, monkeypatch)
    _LANES.clear()
    for key in ("ASHEN_DISABLE_PROVIDER_CALLS", "ASHEN_DISABLE_LIVE_INTERPRETATION", "ASHEN_DISABLE_EXPRESSION_GENERATION", "ASHEN_DISABLE_PROVIDER_RETRIES"):
        monkeypatch.setenv(key, "1")
    monkeypatch.delenv("ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION", raising=False)
    before = state()
    providers = len(snapshot()["records"])
    with TestClient(app) as client:
        first = client.post("/api/chat?ui_mode=player", json={"text": text, "client_request_id": case})
        second = client.post("/api/chat?ui_mode=player", json={"text": text, "client_request_id": case})
    after = state()
    body = first.json()
    visible = body["gm_output"]["player_facing_text"]
    log = storage.load_log()[-1]
    decision = log["resolution"]["metadata"]["conversational_decision"]
    checks = {
        "http_ok": first.status_code == second.status_code == 200,
        "identical_duplicate": body == second.json(),
        "addresses_request": (case == "unanswered_inventory" or text in visible) and all(t in visible for t in terms),
        "no_secret_disclosure": all(canary not in visible for canary in CANARIES),
        "no_provider_dispatch": len(snapshot()["records"]) == providers,
        "no_executable_obligation": not decision["requires_authoritative_execution"],
    }
    checks.update({"unchanged_" + k: before[k] == after[k] for k in ("character", "world", "scene", "combat")})
    checks.update({"unchanged_" + k: before["session"].get(k) == after["session"].get(k)
                   for k in ("turn_counter", "clocks", "scene_state", "active_scene_id", "last_publication")})
    evidence = os.environ.get("ASHEN_ORDINARY_ADMISSION_EVIDENCE")
    if evidence:
        out = Path(evidence)
        out.mkdir(parents=True, exist_ok=True)
        (out / (case + ".json")).write_text(json.dumps({"input": text, "before": before, "after": after,
            "admission": decision, "response": body, "log": log, "assertions": checks,
            "provider_dispatches": len(snapshot()["records"]) - providers}, indent=2), encoding="utf-8")
    assert all(checks.values()), checks
    _LANES.clear()


def test_contract_permission_does_not_depend_on_raw_vocabulary():
    from game.ordinary_semantic_ownership import ordinary_admission_decision
    unresolved = {"contract_id": "test", "operation": "unresolved", "raw_input": "same words"}
    assert ordinary_admission_decision(unresolved).disposition == "CLARIFICATION"
    attempted = {**unresolved, "operation": "act", "construction": {
        "commitment_status": "executed_now", "resolution_subject": "world_action"}}
    assert ordinary_admission_decision(attempted) is None
