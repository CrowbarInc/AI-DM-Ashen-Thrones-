"""Offline HTTP acceptance for examination communication reconciliation."""
import copy
import hashlib
import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from game import api, conversational_orchestration as co, exploration, live_chat_interpretation as live, storage
from game.integrated_play import _LANES
from game.provider_budget import snapshot as provider_snapshot
from tests.helpers import live_model_guard
from tests.helpers.turn_pipeline_http_fixtures import _patch_storage

ARTIFACTS = Path(__file__).resolve().parents[1] / "artifacts"
SHORT = ARTIFACTS / "pr_play_short_multiturn_live_validation"
EXTENDED = ARTIFACTS / "pr_play_extended_live_continuity_validation/live_execution"
POSITIVE = ARTIFACTS / "pr_play_positive_action_live_retest/live_continuation"
FOUNDATIONAL = ARTIFACTS / "pr_play_foundational_live_interpretation_validation"
ROUTE = "The missing patrol was last seen taking the northwest mud track past the crates."


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def captured(path):
    row = load(path)
    outcomes = row.get("interpreter_outcomes", row.get("interpretation_outcomes", []))
    raw = next((entry.get("result", entry)["raw_interpretation"] for entry in outcomes), None)
    request = row.get("request") or {"text": row["text"]}
    return request, raw


def state():
    return copy.deepcopy({
        name: getattr(storage, f"load_{name}")()
        for name in ("session", "character", "world", "active_scene", "combat", "conditions", "campaign")
    })


def trace(name, row):
    directory = os.environ.get("ASHEN_INSPECTION_EVIDENCE")
    if directory:
        target = Path(directory)
        target.mkdir(parents=True, exist_ok=True)
        (target / f"{name}.json").write_text(json.dumps(row, indent=2, default=str), encoding="utf-8")


@pytest.fixture
def replay(tmp_path, monkeypatch):
    _patch_storage(tmp_path, monkeypatch)
    fixture = (SHORT / "frontier_gate_fixture.json").read_bytes()
    assert hashlib.sha256(fixture).hexdigest() == "1ef169552fb8f62512a19993125978e174bb820d063a7fb4edf0284a4d3e845a"
    for name, content in json.loads(fixture)["files_utf8"].items():
        target = (storage.DATA_DIR / name).resolve()
        assert target.is_relative_to(storage.DATA_DIR.resolve())
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content.encode("utf-8"))
    monkeypatch.setattr(api, "DATA_DIR", storage.DATA_DIR)
    monkeypatch.setenv("ASHEN_DISABLE_PROVIDER_CALLS", "1")
    monkeypatch.setattr(api, "call_gpt", live_model_guard.production_call_gpt())
    _LANES.clear()
    calls = {}
    raw_response = None

    def record(owner, name, project=lambda result: result):
        original = getattr(owner, name)

        def capture(*args, **kwargs):
            result = original(*args, **kwargs)
            calls.setdefault(name, []).append(copy.deepcopy(project(result)))
            return result

        monkeypatch.setattr(owner, name, capture)

    record(api, "interpret_production_turn")
    record(co, "_inspection_communication_consistency", lambda pair: [
        pair[0], pair[1].to_public_dict() if pair[1] else None,
    ])
    record(api, "decision_from_interpretation_record", lambda decision: decision.to_public_dict())
    record(api, "normalized_action_from_interpretation")
    record(exploration, "resolve_exploration_action")
    record(api, "resolve_exploration_action")
    record(api, "advance_world_tick")

    def stub(*args, **kwargs):
        assert raw_response is not None, "Unexpected interpretation dispatch"
        calls.setdefault("offline_adapter", []).append(hashlib.sha256(raw_response.encode()).hexdigest())
        return {"ok": True, "sent": False, "text": raw_response}

    monkeypatch.setattr(live, "request_interpretation", stub)
    with TestClient(api.app) as http:
        def send(name, request, raw=None, duplicate=False):
            nonlocal raw_response
            calls.clear()
            raw_response = raw
            monkeypatch.setattr(live, "production_live_interpretation_enabled", lambda: raw is not None)
            before = state()
            provider_before = len(provider_snapshot()["records"])
            payload = {"client_request_id": name, **request}
            reply = http.post("/api/chat?ui_mode=player", json=payload)
            after = state()
            after_log = storage.load_log()
            first_calls = copy.deepcopy(calls)
            calls.clear()
            again = http.post("/api/chat?ui_mode=player", json=payload) if duplicate else None
            row = {
                "request": payload, "raw_interpretation": raw, "http_status": reply.status_code,
                "response": reply.json(), "before": before, "after": after, "host": first_calls,
                "duplicate": {"equal_response": again.json() == reply.json(), "equal_state": state() == after,
                              "equal_log": storage.load_log() == after_log,
                              "host": copy.deepcopy(calls)} if again is not None else None,
                "provider_records": len(provider_snapshot()["records"]) - provider_before,
                "persisted_log_resolution": (after_log[-1] or {}).get("resolution"),
            }
            trace(name, row)
            assert reply.status_code == 200 and row["provider_records"] == 0
            if duplicate:
                assert row["duplicate"] == {"equal_response": True, "equal_state": True, "equal_log": True, "host": {}}
            return row

        yield send
    _LANES.clear()


def play_capture(replay, path, name, duplicate=False):
    request, raw = captured(path)
    return replay(name, request, raw, duplicate)


def turn_delta(row):
    return row["after"]["session"]["turn_counter"] - row["before"]["session"]["turn_counter"]


def reason(row):
    return row["persisted_log_resolution"]["metadata"]["conversational_decision"]["reason"]


def test_extended_t01_exact(replay):
    row = play_capture(replay, EXTENDED / "T01.json", "extended-t01", duplicate=True)
    historical = load(EXTENDED / "T01.json")
    assert row["before"]["session"]["active_scene_id"] == historical["before"]["scene"]
    assert row["before"]["session"]["turn_counter"] == historical["before"]["turn"]
    assert row["before"]["session"]["clue_knowledge"] == historical["before"]["clue_knowledge"]
    assert len(row["host"]["offline_adapter"]) == 1
    assert row["host"]["interpret_production_turn"][0]["raw_interpretation"] == row["raw_interpretation"]
    if os.environ.get("ASHEN_INSPECTION_BASELINE") == "1":
        assert reason(row) == "unresolved_inspection_communication_conflict"
        assert row["response"] == historical["response"]
        assert turn_delta(row) == 0
        assert not row["host"].get("resolve_exploration_action")
        assert not row["host"].get("advance_world_tick")
        return
    assert_discovery(row, "notice_board", "notice_patrol_route")
    audit = row["persisted_log_resolution"]["metadata"]["live_chat_interpretation"]
    assert audit["raw_interpretation"] == row["raw_interpretation"]
    assert audit["record"]["communication"]["purpose"] == "QUESTION"
    normalized = audit["normalized_record"]
    assert (normalized["communication"]["recipient"], normalized["communication"]["purpose"]) == ("CHARACTER", "ACTION")
    assert normalized["action_components"] == audit["record"]["action_components"]
    assert normalized["contract_consistency"]["inspection_alias"] == "missing patrol warning"
    assert ROUTE in row["response"]["gm_output"]["player_facing_text"]


def gameplay_session(session):
    return {key: session.get(key) for key in (
        "active_scene_id", "visited_scene_ids", "current_date", "flags", "clocks",
        "turn_counter", "clue_knowledge", "pending_leads",
    )}


def assert_quiet(row, *, allow_untargeted=False):
    assert gameplay_session(row["before"]["session"]) == gameplay_session(row["after"]["session"])
    for key in ("character", "world", "active_scene", "combat", "conditions", "campaign"):
        assert row["before"][key] == row["after"][key], key
    receipts = row["host"].get("resolve_exploration_action", [])
    if allow_untargeted:
        assert len(receipts) == 1
        assert receipts[0]["metadata"]["referenced_surface_authority"] == "untargeted"
        assert receipts[0]["success"] is None and not receipts[0]["discovered_clues"]
    else:
        assert not receipts
    assert not row["host"].get("advance_world_tick")
    assert ROUTE not in json.dumps(row["response"])
    assert "CANARY_" not in json.dumps(row["response"])


def assert_discovery(row, target, clue):
    assert turn_delta(row) == 1
    assert len(row["host"]["advance_world_tick"]) == 1
    receipts = row["host"]["resolve_exploration_action"]
    assert len(receipts) == 1
    receipt = receipts[0]
    assert receipt["kind"] == "discover_clue" and receipt["success"] is True
    assert receipt["interactable_id"] == target and receipt["clue_id"] == clue
    assert row["persisted_log_resolution"]["clue_id"] == clue
    before = row["before"]["session"]
    after = row["after"]["session"]
    assert set(after["clue_knowledge"]) - set(before["clue_knowledge"]) == {clue}
    assert receipt["discovered_clues"][0] in json.dumps(row["response"])
    assert after["clocks"]["time_pressure"] - before["clocks"]["time_pressure"] == 1
    for key in ("active_scene_id", "visited_scene_ids", "current_date", "flags"):
        assert before.get(key) == after.get(key), key
    for key in ("character", "combat", "conditions", "campaign"):
        assert row["before"][key] == row["after"][key], key
    expected_scene = copy.deepcopy(row["before"]["active_scene"])
    expected_scene["scene"].setdefault("discovered_clues", []).extend(receipt["discovered_clues"])
    assert expected_scene == row["after"]["active_scene"]
    assert row["after"]["world"] == row["host"]["advance_world_tick"][0]["world"]


def test_extended_t04_exact(replay):
    # Reproduce the gate-to-milestone prefix using real HTTP transitions.
    for index in ("01", "02", "03"):
        play_capture(replay, EXTENDED / f"T{index}.json", f"extended-t04-prefix-{index}")
    row = play_capture(replay, EXTENDED / "T04.json", "extended-t04", duplicate=True)
    historical = load(EXTENDED / "T04.json")
    assert row["before"]["session"]["active_scene_id"] == historical["before"]["scene"]
    assert row["before"]["session"]["turn_counter"] == historical["before"]["turn"] + 1
    assert len(row["host"]["offline_adapter"]) == 1
    outcome = row["host"]["interpret_production_turn"][0]
    assert outcome["raw_interpretation"] == row["raw_interpretation"]
    assert outcome["record"]["communication"]["recipient"] == "MIXED"
    assert [c["operation_class"] for c in outcome["record"]["action_components"]] == ["MOVE", "INSPECT"]
    assert [c["target_ref"] for c in outcome["record"]["action_components"]] == [None, "prints"]
    assert_discovery(row, "prints", "milestone_mud_prints")
    audit = row["persisted_log_resolution"]["metadata"]["live_chat_interpretation"]
    assert audit["record"] == outcome["record"]
    normalized = audit["normalized_record"]
    assert normalized["action_components"] == outcome["record"]["action_components"][1:]
    assert normalized["contract_consistency"]["suppressed_component"] == outcome["record"]["action_components"][0]


@pytest.mark.parametrize("source", ["historical-n1", "positive-n1", "positive-n1-v", "extended-t11"])
def test_captured_positive_inspections(replay, source):
    paths = {
        "historical-n1": FOUNDATIONAL / "N1_trace.json",
        "positive-n1": POSITIVE / "N1_trace.json",
        "positive-n1-v": POSITIVE / "N1-V_trace.json",
        "extended-t11": EXTENDED / "T11.json",
    }
    row = play_capture(replay, paths[source], source, duplicate=True)
    assert len(row["host"]["offline_adapter"]) == 1
    assert_discovery(row, "notice_board", "notice_patrol_route")


def test_five_turn_continuity(replay):
    rows = [play_capture(replay, SHORT / "live_execution" / f"T{i}.json", f"short-t{i}", duplicate=i in (1, 4))
            for i in range(1, 6)]
    assert_discovery(rows[0], "notice_board", "notice_patrol_route")
    assert_discovery(rows[3], "prints", "milestone_mud_prints")
    assert [len(row["host"].get("offline_adapter", [])) for row in rows] == [1, 0, 0, 1, 0]
    assert [turn_delta(row) for row in rows] == [1, 0, 1, 1, 0]
    assert [len(row["host"].get("advance_world_tick", [])) for row in rows] == [1, 0, 1, 1, 0]
    assert rows[2]["after"]["session"]["active_scene_id"] == "old_milestone"
    assert rows[-1]["after"]["session"]["turn_counter"] == 7
    for row in (rows[1], rows[4]):
        assert gameplay_session(row["before"]["session"]) == gameplay_session(row["after"]["session"])
        assert row["before"]["character"] == row["after"]["character"]
        assert ROUTE in json.dumps(row["response"])
    assert rows[0]["before"]["character"] == rows[-1]["after"]["character"]


def envelope():
    return json.loads(captured(EXTENDED / "T01.json")[1])


@pytest.mark.parametrize("owner,purpose", [
    ("GM", "QUESTION"), ("GM", "DESCRIPTION"), ("GM", "ACTION"), ("CHARACTER", "ACTION"),
])
def test_positive_label_matrix(replay, owner, purpose):
    record = envelope()
    record["communication"].update(recipient=owner, purpose=purpose)
    name = f"label-{owner.lower()}-{purpose.lower()}"
    row = replay(name, {"text": "I take a closer look at the notice board."}, json.dumps(record))
    assert len(row["host"]["offline_adapter"]) == 1
    assert_discovery(row, "notice_board", "notice_patrol_route")
    decision = row["host"]["decision_from_interpretation_record"][-1]["proposed_record"]
    assert (decision["communication"]["recipient"], decision["communication"]["purpose"]) == ("CHARACTER", "ACTION")
    assert decision["action_components"] == record["action_components"]


@pytest.mark.parametrize("name,text", [
    ("notice-says", "What does the notice say?"),
    ("visible-scene", "What can I see here?"),
    ("missing-patrol-location", "Where was the patrol last seen?"),
    ("memory", "What do I remember about the notice?"),
    ("describe-object", "Describe the notice board."),
    ("already-visible", "What can I already see on the notice board?"),
    ("only-asking", "I only ask what I could learn from it."),
    ("conditional", "If I examined the notice, what might happen?"),
    ("without-contact", "Without touching or inspecting it, what can I already tell?"),
    ("negated", "I don't examine the notice board."),
    ("negated-formal", "I do not inspect the notice board."),
    ("negative-directive", "Do not examine the notice board."),
    ("possibility", "I might examine the notice board."),
    ("permission", "Can I examine the notice board?"),
    ("want-conditional", "I want a closer look at the notice board if the guards leave."),
    ("deferred", "I will examine the notice board when the crowd clears."),
    ("uncertain-want", "I may want a closer look at the notice board."),
    ("counterfactual", "I would have taken a closer look at the notice board."),
    ("movement-and-inspection", "I move to the doorway and inspect the notice."),
    ("take-and-examine", "I take the book and examine the notice."),
    ("cast-and-inspect", "I cast a spell and inspect the footprints."),
    ("dialogue-and-inspect", "I speak to the captain and inspect the board."),
    ("inspection-and-movement", "I want a closer look at the notice board and then I leave."),
    ("two-examinations", "I examine the notice board and inspect the roster board."),
    ("alternative", "I want a closer look at the notice board or I ask the captain."),
    ("unmodelled-tail", "I want a closer look at the warning about the missing patrol and teleport to the moon."),
    ("unknown-location-modifier", "I want a closer look at the warning about the missing patrol inside the locked chest."),
    ("unresolved-pronoun", "I want a closer look at it."),
    ("unresolved-alias", "I want a closer look at the warning about the missing caravan."),
    ("destination-scope", "I want a closer look at the notice board at the old milestone."),
])
def test_complete_utterance_controls(replay, name, text):
    record = envelope()
    row = replay(name, {"text": text}, json.dumps(record))
    assert_quiet(row, allow_untargeted=name == "unresolved-pronoun")
    before = row["before"]
    decision = co.decision_from_interpretation_record(record, player_text=text, scene=before["active_scene"],
        world=before["world"], session=before["session"], character=before["character"])
    assert decision.category != co.ConversationalDecisionCategory.EXECUTE


@pytest.mark.parametrize("variant", [
    "second-board", "second-warning", "direct-vs-reordered", "missing-current-object",
    "other-scene", "hidden", "invisible", "inaccessible", "gm-only", "nonpublic",
    "unsupported-npc", "unsupported-exit", "model-target-mismatch",
])
def test_authoritative_target_controls(replay, variant):
    record = envelope()
    scene = storage.load_active_scene()
    board = next(item for item in scene["scene"]["interactables"] if item["id"] == "notice_board")
    text = "I want a closer look at the warning about the missing patrol."
    if variant == "other-scene":
        play_capture(replay, EXTENDED / "T03.json", "cross-scene-setup")
        assert storage.load_session()["active_scene_id"] == "old_milestone"
    elif variant == "missing-current-object":
        scene["scene"]["interactables"].remove(board)
    elif variant in ("hidden", "invisible", "inaccessible", "gm-only", "nonpublic"):
        key, value = {
            "hidden": ("hidden", True), "invisible": ("visible", False),
            "inaccessible": ("accessible", False), "gm-only": ("gm_only", True),
            "nonpublic": ("public", False),
        }[variant]
        board[key] = value
    elif variant in ("second-board", "second-warning", "direct-vs-reordered", "model-target-mismatch"):
        another = {**board, "id": "alternate_board", "label": "Alternate board"}
        if variant == "second-board":
            text = "I want a closer look at the board."
        elif variant == "direct-vs-reordered":
            another["aliases"] = ["warning about the missing patrol"]
        elif variant == "model-target-mismatch":
            another["aliases"] = ["tax schedule"]
            record["action_components"][0]["target_ref"] = "alternate_board"
            record["references"]["permitted_entity_ids"] = ["alternate_board"]
        scene["scene"]["interactables"].append(another)
    else:
        from game.route_authority import authored_exit_rows

        target = "guard_captain" if variant == "unsupported-npc" else authored_exit_rows(scene)[0]["id"]
        text = "I want a closer look at the guard captain." if variant == "unsupported-npc" else text
        record["action_components"][0]["target_ref"] = target
        record["references"]["permitted_entity_ids"] = [target]
    if variant != "other-scene":
        storage.save_scene(scene)
    row = replay(variant, {"text": text}, json.dumps(record))
    assert_quiet(row)


@pytest.mark.parametrize("variant", [
    "no-action", "unsupported-action", "extra-targetless-move", "two-inspects", "null-target",
    "unpermitted-target", "unresolved-reference", "bad-evidence", "unsupported-status", "session-owner",
])
def test_model_contract_controls(replay, variant):
    record = envelope()
    if variant == "no-action":
        record["action_components"] = []
    elif variant == "unsupported-action":
        record["action_components"][0]["operation_class"] = "OTHER"
    elif variant in ("extra-targetless-move", "two-inspects"):
        second = {**record["action_components"][0], "order": 2}
        if variant == "extra-targetless-move":
            second.update(operation_class="MOVE", target_ref=None, description="Move to an unnamed place")
        record["action_components"].append(second)
    elif variant == "null-target":
        record["action_components"][0]["target_ref"] = None
    elif variant == "unpermitted-target":
        record["references"]["permitted_entity_ids"] = []
    elif variant == "unresolved-reference":
        record["references"]["unresolved_references"] = ["a private warning"]
    elif variant == "bad-evidence":
        record["communication"]["evidence_refs"] = ["hidden:0"]
    elif variant == "unsupported-status":
        record["interpretation_status"] = "UNSUPPORTED_REQUEST"
    else:
        record["communication"].update(recipient="SESSION", purpose="RULES")
    row = replay(variant, {"text": "I want a closer look at the warning about the missing patrol."}, json.dumps(record))
    assert_quiet(row)
