"""PR-EF-R3 read-only investigation runner.

Does not modify production gameplay code or the active campaign.
Disposable copies live under artifacts/pr_ef_r3/disposable_state.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent
DISP = OUT / "disposable_state"
DISP.mkdir(parents=True, exist_ok=True)
os.environ["ASHEN_DATA_DIR"] = str(DISP)
os.environ["ASHEN_PROVIDER_REQUEST_LIMIT"] = "12"
os.environ["ASHEN_PROVIDER_INPUT_TOKEN_LIMIT"] = "60000"
os.environ["ASHEN_PROVIDER_OUTPUT_TOKEN_LIMIT"] = "5000"
os.environ["ASHEN_PROVIDER_TOTAL_TOKEN_LIMIT"] = "65000"
os.environ["ASHEN_PROVIDER_USAGE_PATH"] = str(OUT / "fresh_probes.usage.jsonl")

# Import production modules only after the data directory is redirected.
from experiments.pr_do.eligibility import evaluate_eligibility
from experiments.pr_dq.world import build_disposable_world
from game.conversational_orchestration import decision_from_interpretation_record
from game.gm import NARRATION_ONLY_SYSTEM_PROMPT, SYSTEM_PROMPT
from game.live_chat_interpretation import interpret_production_turn
from game.ordinary_semantic_ownership import establish_ordinary_gameplay_contract
from game.player_interpretation_bridge import normalized_action_from_interpretation, visible_catalog
from game.provider_budget import snapshot


def save(name: str, value) -> None:
    path = OUT / name
    if isinstance(value, str):
        path.write_text(value, encoding="utf-8")
    else:
        path.write_text(json.dumps(value, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def load_behavior():
    return json.loads((ROOT / "artifacts/pr_ef_r2/behavior_1.json").read_text(encoding="utf-8"))


def find_snapshot(row: dict, which: str):
    state = row.get(which) or {}
    if not isinstance(state, dict):
        return {}
    # Harness snapshots are nested differently across cycles. Search one level.
    if "world" in state or "session" in state or "scene" in state:
        return state
    for value in state.values():
        if isinstance(value, dict) and ("world" in value or "npcs" in value or "session" in value):
            return value
    return state


def scene_world_session(snapshot_obj: dict):
    scene = snapshot_obj.get("scene")
    world = snapshot_obj.get("world")
    session = snapshot_obj.get("session") or {}
    if scene is None and isinstance(snapshot_obj.get("campaign_state"), dict):
        blob = snapshot_obj["campaign_state"]
        scene, world, session = blob.get("scene"), blob.get("world"), blob.get("session") or {}
    return scene, world, session


def npc_ids(world, scene_id):
    found = []
    for npc in (world or {}).get("npcs") or []:
        if isinstance(npc, dict) and str(npc.get("location") or "") == scene_id:
            found.append({"id": npc.get("id"), "name": npc.get("name"), "location": npc.get("location")})
    return found


def record_of(row):
    live = ((row.get("resolution") or {}).get("metadata") or {}).get("live_chat_interpretation") or {}
    record = live.get("record")
    if isinstance(record, dict):
        return copy.deepcopy(record)
    return None


def eligibility_of(record):
    if not isinstance(record, dict):
        return None
    components = record.get("action_components") or []
    refs = record.get("references") or {}
    correction = record.get("correction") or {}
    return evaluate_eligibility(
        communication_mode=str(record.get("communication_mode") or ""),
        interpretation_status=str(record.get("interpretation_status") or ""),
        operation_classes=[str(c.get("operation_class") or "") for c in components if isinstance(c, dict)],
        target_ids=[c.get("target_ref") for c in components if isinstance(c, dict)],
        component_orders=[int(c.get("order") or i + 1) for i, c in enumerate(components) if isinstance(c, dict)],
        unresolved_references=list(refs.get("unresolved_references") or []),
        permitted_ids=set(refs.get("permitted_entity_ids") or []),
        declared_ids=list(refs.get("permitted_entity_ids") or []),
        correction_subject=str(correction.get("subject") or "NONE"),
        engine_channel=None,
    )


def decision_view(decision):
    if decision is None:
        return None
    data = decision.__dict__.copy()
    for key in ("proposed_record", "context_update"):
        if key in data:
            data[key] = "<present>" if data[key] else None
    return data


def contract_view(contract):
    construction = contract.get("construction") if isinstance(contract, dict) else {}
    binding = (construction or {}).get("entity_binding") or {}
    return {
        "operation": contract.get("operation"),
        "interlocutor_id": contract.get("interlocutor_id"),
        "ambiguous": contract.get("ambiguous"),
        "expected_resolution": contract.get("expected_resolution"),
        "binding_status": binding.get("status"),
        "proposed_interlocutor": binding.get("proposed_interlocutor"),
        "bound_interlocutor_id": binding.get("bound_interlocutor_id"),
        "authority_reasons": binding.get("authority_reasons"),
        "explicit_new_interlocutor": binding.get("explicit_new_interlocutor"),
        "authority_conflict": (construction or {}).get("authority_conflict"),
        "pre_bridge_status": ((construction or {}).get("pre_bridge_addressee_binding") or {}).get("status"),
        "pre_bridge_reasons": ((construction or {}).get("pre_bridge_addressee_binding") or {}).get("authority_reasons"),
        "validation_status": (construction or {}).get("validation_status"),
    }


def faction_rows(world):
    rows = []
    for faction in (world or {}).get("factions") or []:
        if isinstance(faction, dict):
            rows.append({
                "id": faction.get("id"),
                "pressure": faction.get("pressure"),
                "agenda_progress": faction.get("agenda_progress"),
            })
    return rows


def changed_world_clocks(before, after):
    b = ((before or {}).get("world_state") or {}).get("clocks") or {}
    a = ((after or {}).get("world_state") or {}).get("clocks") or {}
    keys = set(b) | set(a)
    diffs = {}
    for key in sorted(keys):
        if b.get(key) != a.get(key):
            diffs[key] = {"before": b.get(key), "after": a.get(key)}
    return diffs


def hash_files(paths):
    out = {}
    for rel in paths:
        path = ROOT / rel
        out[rel] = hashlib.sha256(path.read_bytes()).hexdigest() if path.exists() else None
    return out


def main():
    behavior = load_behavior()
    rows = {row["turn"]: row for row in behavior["rows"]}
    focus = [rows[n] for n in (26, 27, 31, 33)]
    turn33 = rows[33]
    before = find_snapshot(turn33, "state_before")
    after = find_snapshot(turn33, "state_after")
    scene, world, session = scene_world_session(before)
    scene_after, world_after, session_after = scene_world_session(after)
    historical_world = world
    fixture = build_disposable_world()
    # The behavior snapshot stores world/session but not the scene document.
    # The PR-DQ fixture is the scene those turns actually used.
    if not isinstance(scene, dict):
        scene = fixture["scenes"][fixture["session"]["active_scene_id"]]
    if not isinstance(world, dict):
        world = fixture["world"]
    if not isinstance(session, dict) or not session:
        session = fixture["session"]
    scene_id = str((scene.get("scene") or scene).get("id") or fixture["session"]["active_scene_id"])

    production = [
        "game/ordinary_semantic_ownership.py",
        "game/live_chat_interpretation.py",
        "game/conversational_orchestration.py",
        "game/immutable_valid_response.py",
        "game/player_interpretation_bridge.py",
        "game/api.py",
        "game/referent_tracking.py",
        "game/world.py",
    ]
    r2_hashes = json.loads((ROOT / "artifacts/pr_ef_r2/source_hashes.json").read_text(encoding="utf-8"))
    current_hashes = hash_files(list(r2_hashes) + production)
    hash_match = {key: current_hashes.get(key) == r2_hashes.get(key) for key in r2_hashes}

    captured = []
    for row in focus:
        record = record_of(row)
        decision = decision_from_interpretation_record(record or {}, player_text=row["player"], scene=scene, world=world, session=session)
        action, bridge = (None, None)
        if record is not None and isinstance(scene, dict) and isinstance(world, dict):
            action, bridge = normalized_action_from_interpretation(record, scene=scene, world=world, player_text=row["player"])
        captured.append({
            "turn": row["turn"],
            "player": row["player"],
            "historical_response": row["response"],
            "historical_critical": row["critical"],
            "historical_nonmutating": row["nonmutating"],
            "historical_provider_calls": row["provider_calls"],
            "communication": (record or {}).get("communication"),
            "communication_mode": (record or {}).get("communication_mode"),
            "interpretation_status": (record or {}).get("interpretation_status"),
            "correction": (record or {}).get("correction"),
            "unresolved_references": ((record or {}).get("references") or {}).get("unresolved_references"),
            "action_components": [
                {"operation": c.get("operation_class"), "target": c.get("target_ref"), "description": c.get("description")}
                for c in ((record or {}).get("action_components") or []) if isinstance(c, dict)
            ],
            "clarification_question": (record or {}).get("clarification_question"),
            "public_evidence_keys": list(((record or {}).get("public_evidence") or {}).keys()),
            "eligibility": eligibility_of(record),
            "replayed_decision": decision_view(decision),
            "bridge": bridge,
        })

    # Two-NPC override: same captured record, extra visible person.
    two_npc = {"available": isinstance(world, dict) and isinstance(scene, dict)}
    if two_npc["available"]:
        world2 = copy.deepcopy(world)
        world2.setdefault("npcs", [])
        world2["npcs"].append({
            "id": "corporal_bren",
            "name": "Corporal Bren",
            "location": scene_id,
            "role": "guard",
        })
        record = record_of(turn33)
        action, bridge = normalized_action_from_interpretation(record, scene=scene, world=world2, player_text=turn33["player"])
        marked = copy.deepcopy(record)
        marked.setdefault("references", {})["unresolved_references"] = ["one of them"]
        marked_action, marked_bridge = normalized_action_from_interpretation(
            marked, scene=scene, world=world2, player_text=turn33["player"]
        )
        from game.live_chat_interpretation import mark_live_interpretation_consumed, reset_live_interpretation_consumed
        resolution = {"kind": "pending", "metadata": {}, "prompt": turn33["player"]}
        reset_live_interpretation_consumed()
        lexical_contract = establish_ordinary_gameplay_contract(
            copy.deepcopy(resolution),
            player_text=turn33["player"],
            session=copy.deepcopy(session) if isinstance(session, dict) else {},
            scene_id=scene_id,
            scene=scene,
            world=world2,
            visible_turns=[],
            normalized_action=action,
        )
        mark_live_interpretation_consumed()
        consumed_contract = establish_ordinary_gameplay_contract(
            {"kind": "pending", "metadata": {}, "prompt": turn33["player"]},
            player_text=turn33["player"],
            session=copy.deepcopy(session) if isinstance(session, dict) else {},
            scene_id=scene_id,
            scene=scene,
            world=world2,
            visible_turns=[],
            normalized_action=action,
        )
        contract = consumed_contract
        two_npc.update({
            "scene_id": scene_id,
            "original_visible_npcs": npc_ids(world, scene_id),
            "augmented_visible_npcs": npc_ids(world2, scene_id),
            "catalog_npc_ids": sorted(k for k, v in visible_catalog(scene, world2).items() if v.get("kind") == "npc"),
            "bridge_with_provider_target": bridge,
            "bridge_when_plural_marked_unresolved": marked_bridge,
            "contract_when_interpretation_not_yet_consumed": contract_view(lexical_contract),
            "contract_after_bridge_override": contract_view(contract),
            "normalized_target": None if not action else action.get("target_id"),
        })

    # Historical state mutation for the ambiguous turn.
    clocks_before = ((session or {}).get("clocks") if isinstance(session, dict) else None)
    clocks_after = ((session_after or {}).get("clocks") if isinstance(session_after, dict) else None)
    mutation = {
        "snapshot_keys_before": sorted(before.keys()) if isinstance(before, dict) else [],
        "scene_id": scene_id,
        "visible_npcs_before": npc_ids(world, scene_id),
        "factions_before": faction_rows(world),
        "factions_after": faction_rows(world_after),
        "world_clock_diffs": changed_world_clocks(world, world_after),
        "turn_counter_before": (session or {}).get("turn_counter") if isinstance(session, dict) else None,
        "turn_counter_after": (session_after or {}).get("turn_counter") if isinstance(session_after, dict) else None,
        "session_clocks_before": clocks_before,
        "session_clocks_after": clocks_after,
        "time_pressure_before": (session or {}).get("clocks", {}).get("time_pressure") if isinstance(session, dict) and isinstance(session.get("clocks"), dict) else None,
        "time_pressure_after": (session_after or {}).get("clocks", {}).get("time_pressure") if isinstance(session_after, dict) and isinstance(session_after.get("clocks"), dict) else None,
    }

    # Token graph from the preserved eleven-turn conversation.
    usage_path = ROOT / "artifacts/pr_ef_r2/conversation_3.usage.jsonl"
    usage = [json.loads(line) for line in usage_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    conversation = json.loads((ROOT / "artifacts/pr_ef_r2/conversation_3.json").read_text(encoding="utf-8"))
    cursor = 0
    turns = []
    for row in conversation["rows"]:
        calls = usage[cursor:cursor + row["provider_calls"]]
        cursor += row["provider_calls"]
        turns.append({
            "turn": row["turn"],
            "player": row["player"],
            "response": row["response"],
            "provider_calls": row["provider_calls"],
            "elapsed_ms": row["elapsed_ms"],
            "calls": [
                {
                    "purpose": call.get("purpose"),
                    "input_tokens": call.get("input_tokens"),
                    "output_tokens": call.get("output_tokens"),
                    "total_tokens": call.get("total_tokens"),
                    "model": call.get("model"),
                }
                for call in calls
            ],
            "input_tokens": sum(call.get("input_tokens") or 0 for call in calls),
            "output_tokens": sum(call.get("output_tokens") or 0 for call in calls),
        })
    by_purpose = {}
    for call in usage:
        bucket = by_purpose.setdefault(call.get("purpose") or "unknown", {"calls": 0, "input_tokens": 0, "output_tokens": 0})
        bucket["calls"] += 1
        bucket["input_tokens"] += call.get("input_tokens") or 0
        bucket["output_tokens"] += call.get("output_tokens") or 0

    prompt_sizes = {
        "system_prompt_chars": len(SYSTEM_PROMPT),
        "narration_only_system_prompt_chars": len(NARRATION_ONLY_SYSTEM_PROMPT),
        "system_prompt_whitespace_tokens_estimate": len(SYSTEM_PROMPT.split()),
        "note": "Historical strict-social user payloads were not persisted. Character counts are current source measurements, not token facts.",
    }

    save("source_hash_comparison.json", {"r2": r2_hashes, "current": current_hashes, "r2_match": hash_match})
    save("captured_failure_replay.json", captured)
    save("two_npc_authority_replay.json", two_npc)
    save("ambiguous_turn_state_mutation.json", mutation)
    save("conversation_3_call_graph.json", {"turns": turns, "by_purpose": by_purpose, "usage_rows": len(usage), "cursor_consumed": cursor})
    save("prompt_size_measurements.json", prompt_sizes)
    print(json.dumps({
        "hash_match": hash_match,
        "visible_npcs": mutation["visible_npcs_before"],
        "two_npc_bridge": two_npc.get("bridge_with_provider_target"),
        "two_npc_marked": two_npc.get("bridge_when_plural_marked_unresolved"),
        "contract": two_npc.get("contract_after_bridge_override"),
        "factions_before": mutation["factions_before"],
        "factions_after": mutation["factions_after"],
        "turn_counter": [mutation["turn_counter_before"], mutation["turn_counter_after"]],
        "time_pressure": [mutation["time_pressure_before"], mutation["time_pressure_after"]],
        "by_purpose": by_purpose,
        "scene_found": bool(scene),
        "world_found": bool(world),
    }, indent=2, default=str))

    # Fresh interpretation-only probes. No narration, no world save.
    os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "0"
    os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "0"
    if os.environ.get("PR_EF_R3_SKIP_FRESH") == "1" or not isinstance(scene, dict) or not isinstance(world, dict):
        save("fresh_probe_status.json", {"ran": False, "reason": "skipped_or_missing_scene"})
        return
    world2 = copy.deepcopy(world)
    world2.setdefault("npcs", []).append({"id": "corporal_bren", "name": "Corporal Bren", "location": scene_id, "role": "guard"})
    session2 = copy.deepcopy(session) if isinstance(session, dict) else {}
    probes = [
        ("ambiguous_plural", "I ask one of them what happened.", world2, []),
        ("explicit_npc", "I ask Sergeant Mara what happened.", world2, []),
        ("gm_about_npc", "What is the sergeant worried about?", world2, []),
        ("followup_meaning", "What does she mean by the road?", world, [
            {"player_input": "I ask Mara about the north road.", "player_facing_text": 'Sergeant Mara mutters, "Word is, the street beyond the gate is the north road."',
             "resolution": {"success": True, "kind": "question", "social": {"target_resolved": True, "npc_id": "sergeant_mara", "npc_name": "Sergeant Mara"}}}
        ]),
        ("correction", "Instead, make that a question about the lamp.", world, []),
        ("withdrawal", "Never mind, forget that.", world, []),
        ("mixed", "I ask the sergeant who owns the lantern, and then I open the gate.", world2, []),
        ("descriptive", "What does the courtyard look like right now?", world, []),
        ("knowledge", "I ask Mara who gave the order to bar the gate.", world, []),
        ("consequential", "I draw my sword and attack the sergeant.", world2, []),
    ]
    fresh = []
    for name, text, probe_world, log in probes:
        try:
            outcome = interpret_production_turn(player_text=text, mode="IC", scene=scene, world=probe_world, log=log, session=session2)
        except Exception as exc:
            fresh.append({"probe": name, "player": text, "error": type(exc).__name__, "detail": str(exc)[:500]})
            break
        record = outcome.get("record") if isinstance(outcome.get("record"), dict) else None
        decision = decision_from_interpretation_record(record or {}, player_text=text, scene=scene, world=probe_world, session=session2) if record else None
        action, bridge = (None, None)
        if record is not None:
            action, bridge = normalized_action_from_interpretation(record, scene=scene, world=probe_world, player_text=text)
        fresh.append({
            "probe": name,
            "player": text,
            "status": outcome.get("status"),
            "reason": outcome.get("reason"),
            "blocked_text": outcome.get("player_facing_text"),
            "communication": None if record is None else record.get("communication"),
            "communication_mode": None if record is None else record.get("communication_mode"),
            "unresolved_references": None if record is None else (record.get("references") or {}).get("unresolved_references"),
            "components": None if record is None else [
                {"operation": c.get("operation_class"), "target": c.get("target_ref")}
                for c in (record.get("action_components") or []) if isinstance(c, dict)
            ],
            "correction": None if record is None else record.get("correction"),
            "eligibility_disposition": outcome.get("eligibility_disposition"),
            "decision_category": None if decision is None else str(decision.category),
            "decision_owner": None if decision is None else decision.communication_owner,
            "decision_purpose": None if decision is None else decision.communication_purpose,
            "decision_reason": None if decision is None else decision.reason,
            "requires_execution": None if decision is None else decision.requires_authoritative_execution,
            "bridge_accepted": None if not isinstance(bridge, dict) else bridge.get("accepted"),
            "bridge_reason": None if not isinstance(bridge, dict) else bridge.get("reason"),
            "bridge_target": None if not isinstance(bridge, dict) else bridge.get("target_ref"),
            "input_tokens": ((outcome.get("provider_requests") or [{}])[0] or {}).get("input_tokens"),
            "output_tokens": ((outcome.get("provider_requests") or [{}])[0] or {}).get("output_tokens"),
        })
        budget = snapshot()
        if budget.get("stopped"):
            fresh.append({"probe": "budget_stop", "reason": budget.get("stop_reason")})
            break
    save("fresh_interpretation_probes.json", fresh)
    save("fresh_probe_budget.json", snapshot())
    print("FRESH", json.dumps(fresh, indent=2, default=str)[:8000])


if __name__ == "__main__":
    main()
