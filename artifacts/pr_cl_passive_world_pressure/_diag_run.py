"""PR-CL diagnostic runner. Local, stubbed provider, no live calls."""
from __future__ import annotations

import copy
import json
from pathlib import Path

from fastapi.testclient import TestClient
from pytest import MonkeyPatch

from game import storage
from game.api import app
from game.response_policy_enforcement import escalate_passive_scene
from tests.helpers.replay_fem_read_smoke import read_turn_debug_notes
from tests.helpers.turn_pipeline_http_fixtures import _gm_response, _seed_shared_world

OUT = Path(__file__).resolve().parent
PHRASES = (
    '"',
    "cuts through the crowd",
    "stops at your shoulder",
    "comes straight to you",
    "squares up to you",
    "breaks the silence first",
    "if you're moving on this, move now",
    "question the runner",
    "work the notice",
    "east-road trail",
    "east road",
    "ask me now",
)


def _slim_npc(npc: dict) -> dict:
    return {
        "id": npc.get("id"),
        "name": npc.get("name"),
        "location": npc.get("location") or npc.get("scene_id"),
        "availability": npc.get("availability"),
        "current_agenda": npc.get("current_agenda"),
        "agenda_move_to_scene_id": npc.get("agenda_move_to_scene_id"),
    }


def _slim_faction(row: dict) -> dict:
    return {
        "id": row.get("id"),
        "name": row.get("name"),
        "pressure": row.get("pressure"),
        "agenda_progress": row.get("agenda_progress"),
    }


def snapshot(label: str) -> dict:
    session = storage.load_session()
    world = storage.load_world()
    scene = storage.load_scene("scene_investigate")
    inner = scene.get("scene") if isinstance(scene, dict) else {}
    runtime = (session.get("scene_runtime") or {}).get("scene_investigate") or {}
    return {
        "label": label,
        "current_date": session.get("current_date"),
        "turn_counter": session.get("turn_counter"),
        "session_clocks": copy.deepcopy(session.get("clocks")),
        "world_clocks": copy.deepcopy((world.get("world_state") or {}).get("clocks")),
        "world_flags": copy.deepcopy((world.get("world_state") or {}).get("flags")),
        "projects": copy.deepcopy(world.get("projects") or []),
        "event_log": copy.deepcopy(world.get("event_log") or []),
        "factions": [_slim_faction(row) for row in (world.get("factions") or []) if isinstance(row, dict)],
        "npcs": [_slim_npc(row) for row in (world.get("npcs") or []) if isinstance(row, dict)],
        "visible_facts": list(inner.get("visible_facts") or []),
        "scene_id": inner.get("id"),
        "scene_location": inner.get("location"),
        "runtime": {
            "passive_action_streak": runtime.get("passive_action_streak"),
            "last_player_action_passive": runtime.get("last_player_action_passive"),
            "last_player_action_text": runtime.get("last_player_action_text"),
            "momentum_exchanges_since": runtime.get("momentum_exchanges_since"),
            "momentum_next_due_in": runtime.get("momentum_next_due_in"),
            "recent_player_actions": runtime.get("recent_player_actions"),
            "recent_contextual_leads": runtime.get("recent_contextual_leads"),
            "pending_leads": runtime.get("pending_leads"),
        },
    }


def _contract(resolution: dict) -> dict:
    meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    contract = meta.get("resolution_contract") if isinstance(meta.get("resolution_contract"), dict) else {}
    accepted = meta.get("accepted_response") if isinstance(meta.get("accepted_response"), dict) else {}
    return {
        "kind": resolution.get("kind"),
        "selected_resolver": meta.get("selected_resolver"),
        "operation": contract.get("operation"),
        "interlocutor_id": contract.get("interlocutor_id"),
        "resolution_subject": contract.get("resolution_subject"),
        "passive_interruption_wait": (resolution.get("metadata") or {}).get("passive_interruption_wait")
        if isinstance(resolution.get("metadata"), dict)
        else None,
        "world_tick_events": resolution.get("world_tick_events"),
        "immutable": accepted.get("immutable"),
        "accepted_text": accepted.get("text"),
        "accepted_provenance": accepted.get("provenance"),
        "hard_valid": ((accepted.get("hard_validation") or {}) if isinstance(accepted.get("hard_validation"), dict) else {}).get("hard_valid"),
    }


def _facing_record(data: dict, pressure_log: list) -> dict:
    gm = data.get("gm_output") or {}
    text = str(gm.get("player_facing_text") or "")
    low = text.lower()
    meta = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
    accepted = meta.get("accepted_response") if isinstance(meta.get("accepted_response"), dict) else {}
    return {
        "status": data.get("ok"),
        "player_facing_text": text,
        "matched_phrases": [phrase for phrase in PHRASES if phrase in low or (phrase == '"' and '"' in text)],
        "tags": gm.get("tags"),
        "debug_notes": read_turn_debug_notes(data),
        "final_route": gm.get("final_route") or meta.get("final_route"),
        "fallback_kind": gm.get("fallback_kind") or meta.get("fallback_kind"),
        "retry_failure_class": gm.get("retry_failure_class"),
        "contract": _contract(data.get("resolution") or {}),
        "accepted_response": {
            "immutable": accepted.get("immutable"),
            "provenance": accepted.get("provenance"),
            "text": accepted.get("text"),
            "hard_validation": accepted.get("hard_validation"),
        },
        "pressure_hook": list(pressure_log),
    }


def _install_stubs(monkeypatch: MonkeyPatch, gpt_text: str, pressure_log: list) -> None:
    def _gpt(_messages):
        return _gm_response(gpt_text)

    def _wrapped_pressure(gm, **kwargs):
        before = str((gm or {}).get("player_facing_text") or "") if isinstance(gm, dict) else ""
        out = escalate_passive_scene(gm, **kwargs)
        after = str((out or {}).get("player_facing_text") or "") if isinstance(out, dict) else ""
        pressure_log.append(
            {
                "before": before,
                "after": after,
                "changed": before != after,
                "tags": (out or {}).get("tags") if isinstance(out, dict) else None,
                "debug_notes": (out or {}).get("debug_notes") if isinstance(out, dict) else None,
            }
        )
        return out

    monkeypatch.setattr("game.api.call_gpt", _gpt)
    monkeypatch.setattr("game.api.parse_social_intent", lambda *_a, **_k: None)
    monkeypatch.setattr("game.api.parse_exploration_intent", lambda *_a, **_k: None)
    monkeypatch.setattr("game.api.parse_intent", lambda *_a, **_k: None)
    monkeypatch.setattr("game.response_policy_enforcement.escalate_passive_scene", _wrapped_pressure)
    monkeypatch.setattr("game.api.escalate_passive_scene", _wrapped_pressure, raising=False)


def _post(client: TestClient, text: str, pressure_log: list) -> dict:
    before = snapshot("before_turn")
    resp = client.post("/api/chat", json={"text": text})
    data = resp.json()
    return {
        "input": text,
        "http_status": resp.status_code,
        "before": before,
        "response": _facing_record(data, pressure_log),
        "after": snapshot("after_turn"),
    }


def _seed_facts(facts: list[str]) -> None:
    scene = copy.deepcopy(storage.load_scene("scene_investigate"))
    scene.pop("_is_canon", None)
    scene["scene"]["visible_facts"] = list(facts)
    storage.save_scene(scene)


def run_target_tense(tmp: Path) -> dict:
    monkeypatch = MonkeyPatch()
    pressure_log: list = []
    _seed_shared_world(tmp, monkeypatch)
    _seed_facts(
        [
            "Guards keep glancing at a missing patrol notice beside the checkpoint.",
            "A tavern runner lingers under an awning, selling rumors for coin.",
        ]
    )
    initial = snapshot("initial")
    _install_stubs(
        monkeypatch,
        "Rain beads on the checkpoint while nobody moves first.",
        pressure_log,
    )
    client = TestClient(app)
    turn = _post(client, "I wait.", pressure_log)
    monkeypatch.undo()
    return {"case": "target_single_tense_wait", "initial": initial, "turns": [turn]}


def run_target_repeat(tmp: Path) -> dict:
    monkeypatch = MonkeyPatch()
    pressure_log: list = []
    _seed_shared_world(tmp, monkeypatch)
    _seed_facts(
        [
            "A guard leans near the checkpoint, watching the road.",
            "A missing patrol notice curls in the damp beside him.",
        ]
    )
    initial = snapshot("initial")
    _install_stubs(
        monkeypatch,
        "The damp air hangs over the gate as everyone watches everyone else.",
        pressure_log,
    )
    client = TestClient(app)
    first = _post(client, "I wait.", pressure_log)
    pressure_log.clear()
    second = _post(client, "I hold position and watch.", pressure_log)
    monkeypatch.undo()
    return {"case": "target_repeated_passive", "initial": initial, "turns": [first, second]}


def run_quiet(tmp: Path) -> dict:
    monkeypatch = MonkeyPatch()
    pressure_log: list = []
    _seed_shared_world(tmp, monkeypatch)
    _seed_facts(
        [
            "Filing shelves crowd one wall; loose papers curl at the edges.",
            "A brass compass sits beside a blot of spilled ink on the desk.",
        ]
    )
    # Remove faction pressure that would cross a threshold on this tick.
    world = storage.load_world()
    for row in world.get("factions") or []:
        if isinstance(row, dict):
            row["pressure"] = 0
            row["agenda_progress"] = 0
    world["projects"] = []
    storage._save_json(storage.WORLD_PATH, world)
    initial = snapshot("initial")
    _install_stubs(monkeypatch, "The lamp stays steady over the desk.", pressure_log)
    client = TestClient(app)
    turn = _post(client, "I wait.", pressure_log)
    monkeypatch.undo()
    return {"case": "A_quiet_wait", "initial": initial, "turns": [turn]}


def run_scheduled(tmp: Path) -> dict:
    monkeypatch = MonkeyPatch()
    pressure_log: list = []
    _seed_shared_world(tmp, monkeypatch)
    _seed_facts(["A brass compass sits beside a blot of spilled ink on the desk."])
    world = storage.load_world()
    for row in world.get("factions") or []:
        if isinstance(row, dict) and row.get("id") == "house_verevin":
            row["pressure"] = 2
            row["agenda_progress"] = 0
        elif isinstance(row, dict):
            row["pressure"] = 0
            row["agenda_progress"] = 0
    storage._save_json(storage.WORLD_PATH, world)
    initial = snapshot("initial")
    _install_stubs(monkeypatch, "The lamp stays steady over the desk.", pressure_log)
    client = TestClient(app)
    turn = _post(client, "I wait.", pressure_log)
    monkeypatch.undo()
    return {"case": "B_scheduled_faction_threshold", "initial": initial, "turns": [turn]}


def run_mobile_npc(tmp: Path) -> dict:
    monkeypatch = MonkeyPatch()
    pressure_log: list = []
    _seed_shared_world(tmp, monkeypatch)
    _seed_facts(["A brass compass sits beside a blot of spilled ink on the desk."])
    world = storage.load_world()
    for row in world.get("factions") or []:
        if isinstance(row, dict):
            row["pressure"] = 0
            row["agenda_progress"] = 0
    for row in world.get("npcs") or []:
        if isinstance(row, dict) and row.get("id") == "tavern_runner":
            row["availability"] = "mobile"
            row["agenda_move_to_scene_id"] = "scene_investigate"
            row["location"] = "frontier_gate"
    storage._save_json(storage.WORLD_PATH, world)
    initial = snapshot("initial")
    _install_stubs(monkeypatch, "The lamp stays steady over the desk.", pressure_log)
    client = TestClient(app)
    turn = _post(client, "I wait.", pressure_log)
    monkeypatch.undo()
    return {"case": "C_mobile_npc_pending_move", "initial": initial, "turns": [turn]}


def run_repeated_quiet(tmp: Path) -> dict:
    monkeypatch = MonkeyPatch()
    pressure_log: list = []
    _seed_shared_world(tmp, monkeypatch)
    _seed_facts(["A brass compass sits beside a blot of spilled ink on the desk."])
    world = storage.load_world()
    for row in world.get("factions") or []:
        if isinstance(row, dict):
            row["pressure"] = 0
            row["agenda_progress"] = 0
    storage._save_json(storage.WORLD_PATH, world)
    initial = snapshot("initial")
    _install_stubs(monkeypatch, "The lamp stays steady over the desk.", pressure_log)
    client = TestClient(app)
    first = _post(client, "I wait.", pressure_log)
    pressure_log.clear()
    second = _post(client, "I hold position and watch.", pressure_log)
    monkeypatch.undo()
    return {"case": "E_repeated_quiet_wait", "initial": initial, "turns": [first, second]}


def run_valid_atmosphere(tmp: Path) -> dict:
    monkeypatch = MonkeyPatch()
    pressure_log: list = []
    _seed_shared_world(tmp, monkeypatch)
    session = storage.load_session()
    scene_runtime = session.setdefault("scene_runtime", {}).setdefault("scene_investigate", {})
    scene_runtime["recent_contextual_leads"] = [
        {
            "key": "tattered-man-by-the-shuttered-well",
            "kind": "visible_suspicious_figure",
            "subject": "the tattered man",
            "position": "by the shuttered well",
            "named": False,
            "positioned": True,
            "mentions": 2,
            "last_turn": 1,
        }
    ]
    storage.save_session(session)
    initial = snapshot("initial")
    line = "The square stays hushed except for the scrape of boots on wet stone."
    _install_stubs(monkeypatch, line, pressure_log)
    client = TestClient(app)
    turn = _post(client, "I wait.", pressure_log)
    monkeypatch.undo()
    return {"case": "F_valid_atmosphere", "initial": initial, "turns": [turn]}


def main() -> None:
    import tempfile

    results = []
    runners = (
        run_target_tense,
        run_target_repeat,
        run_quiet,
        run_scheduled,
        run_mobile_npc,
        run_repeated_quiet,
        run_valid_atmosphere,
    )
    for runner in runners:
        with tempfile.TemporaryDirectory() as raw:
            results.append(runner(Path(raw)))
    (OUT / "PR-CL_diagnostic_raw.json").write_text(
        json.dumps(results, indent=2, default=str),
        encoding="utf-8",
    )
    print("wrote", OUT / "PR-CL_diagnostic_raw.json")


if __name__ == "__main__":
    main()
