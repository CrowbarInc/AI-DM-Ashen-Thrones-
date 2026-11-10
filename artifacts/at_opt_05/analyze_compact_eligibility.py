"""AT-OPT-05 provider-free compact-eligibility and transition-flag analysis.

Does not call a provider. Does not modify production instruction selection.
Writes only under artifacts/at_opt_05/. Campaign state is copied to a temp directory.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
F3 = ROOT / "artifacts" / "pr_play_79df3" / "http_data"
SNAPSHOT = F3 / "snapshots" / "2026-11-08T16-50-45_8caf7aff.json"
RECORDED_INPUT = 22777

os.environ["ASHEN_TEST_EVIDENCE_DIR"] = str(OUT)
os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "1"
os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_RETRIES"] = "1"
os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ.pop("ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION", None)
os.environ.pop("OPENAI_API_KEY", None)
sys.path.insert(0, str(ROOT))

PROVIDER_CALLS = {"openai_constructed": 0, "call_gpt": 0}


def _bytes(obj) -> int:
    return len(json.dumps(obj, ensure_ascii=False).encode("utf-8"))


def message_stats(messages: list) -> dict:
    system = messages[0]["content"]
    user_text = messages[1]["content"]
    user = json.loads(user_text)
    blob = json.dumps(messages, ensure_ascii=False).encode("utf-8")
    return {
        "system_bytes": len(system.encode("utf-8")),
        "user_bytes": len(user_text.encode("utf-8")),
        "blob_bytes": len(blob),
        "admission_estimate_tokens": max(1, (len(blob) // 3) + 64),
        "user": user,
    }


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def prepare_state() -> Path:
    temp = Path(tempfile.mkdtemp(prefix="at-opt-05-"))
    target = temp / "f3_state"
    shutil.copytree(F3, target, ignore=shutil.ignore_patterns("provider_usage.jsonl", "snapshots"))
    snapshot = load_json(SNAPSHOT)
    session = snapshot.get("session") if isinstance(snapshot, dict) else None
    if not isinstance(session, dict):
        raise RuntimeError("snapshot has no session object")
    (target / "session.json").write_text(json.dumps(session, ensure_ascii=False), encoding="utf-8")
    for name in ("world", "character", "combat"):
        body = snapshot.get(name)
        if isinstance(body, dict):
            (target / f"{name}.json").write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")
    log_entries = snapshot.get("log_entries") if isinstance(snapshot.get("log_entries"), list) else []
    log_text = "".join(json.dumps(entry, ensure_ascii=False) + "\n" for entry in log_entries if isinstance(entry, dict))
    (target / "session_log.jsonl").write_text(log_text, encoding="utf-8")
    (target / "provider_usage.jsonl").write_text("", encoding="utf-8")
    return target


def transition_view(payload: dict) -> dict:
    obligations = payload.get("narration_obligations") if isinstance(payload.get("narration_obligations"), dict) else {}
    transition = payload.get("transition") if isinstance(payload.get("transition"), dict) else None
    plan = payload.get("narrative_plan") if isinstance(payload.get("narrative_plan"), dict) else {}
    node = plan.get("transition_node") if isinstance(plan.get("transition_node"), dict) else transition
    before = (node or {}).get("before_anchor") if isinstance(node, dict) else None
    after = (node or {}).get("after_anchor") if isinstance(node, dict) else None
    before_scene = before.get("scene_id") if isinstance(before, dict) else None
    after_scene = after.get("scene_id") if isinstance(after, dict) else None
    compact = payload.get("prompt_debug") if isinstance(payload.get("prompt_debug"), dict) else {}
    # prompt_debug is stripped from the public payload. Selection is inferred from instruction shape below.
    return {
        "must_advance_scene": obligations.get("must_advance_scene"),
        "is_opening_scene": obligations.get("is_opening_scene"),
        "active_npc_reply_expected": obligations.get("active_npc_reply_expected"),
        "transition_required": None if transition is None else transition.get("transition_required"),
        "transition_type": None if transition is None else transition.get("transition_type"),
        "before_scene_id": before_scene,
        "after_scene_id": after_scene,
        "same_scene": bool(before_scene and after_scene and before_scene == after_scene),
        "source_fields": list((transition or {}).get("source_fields") or []),
        "derivation_codes": list((transition or {}).get("derivation_codes") or []),
        "narrative_mode": plan.get("narrative_mode"),
        "scene_advancement": payload.get("scene_advancement"),
        "uncertainty_present": isinstance(payload.get("uncertainty_hint"), dict) and bool(payload.get("uncertainty_hint")),
        "follow_up_present": isinstance(payload.get("follow_up_pressure"), dict) and bool(payload.get("follow_up_pressure")),
        "active_topic": bool((payload.get("active_topic_anchor") or {}).get("active"))
        if isinstance(payload.get("active_topic_anchor"), dict)
        else False,
        "requires_check": bool((payload.get("mechanical_resolution") or {}).get("requires_check"))
        if isinstance(payload.get("mechanical_resolution"), dict)
        else False,
        "instruction_count": len(payload.get("instructions") or []),
        "instruction_bytes": _bytes(payload.get("instructions")),
        "visible_fact_count": len(((payload.get("scene") or {}).get("public") or {}).get("visible_facts") or [])
        if isinstance(payload.get("scene"), dict)
        else None,
        "recent_log_count": len(payload.get("recent_log") or []) if isinstance(payload.get("recent_log"), list) else None,
        "memory_count": len(payload.get("selected_conversational_memory") or [])
        if isinstance(payload.get("selected_conversational_memory"), list)
        else None,
        "compact_debug_present_in_public_payload": "compact_prompt" in compact,
    }


def eligibility_blockers(view: dict) -> list[str]:
    blockers = []
    if view.get("is_opening_scene") or view.get("must_advance_scene"):
        blockers.append("opening_or_must_advance_scene")
    if view.get("requires_check"):
        blockers.append("requires_check")
    if view.get("uncertainty_present"):
        blockers.append("uncertainty_hint")
    if view.get("active_topic"):
        blockers.append("active_topic_anchor")
    if view.get("follow_up_present"):
        blockers.append("follow_up_pressure")
    return blockers


def summarize_build(messages: list, *, label: str, profile: str) -> dict:
    stats = message_stats(messages)
    user = stats.pop("user")
    view = transition_view(user)
    instructions = list(user.get("instructions") or [])
    return {
        "label": label,
        "prompt_profile": profile,
        **stats,
        "view": view,
        "eligibility_blockers_visible_on_public_payload": eligibility_blockers(view),
        "instruction_lines": instructions,
        "top_level_keys": sorted(user.keys()),
        "response_policy_keys": sorted((user.get("response_policy") or {}).keys())
        if isinstance(user.get("response_policy"), dict)
        else [],
    }


def diff_instructions(full_lines: list[str], compact_lines: list[str]) -> dict:
    full_set = list(full_lines)
    compact_set = set(compact_lines)
    only_full = [line for line in full_set if line not in compact_set]
    only_compact = [line for line in compact_lines if line not in set(full_lines)]
    return {
        "full_count": len(full_lines),
        "compact_count": len(compact_lines),
        "only_in_full": only_full,
        "only_in_compact": only_compact,
        "only_in_full_bytes": _bytes(only_full),
        "shared_count": len([line for line in full_lines if line in compact_set]),
    }


def dropped_key_report(full_payload_keys: list[str], compact_keys: list[str], full_user: dict, compact_user: dict) -> list[dict]:
    policy = full_user.get("response_policy") if isinstance(full_user.get("response_policy"), dict) else {}
    rows = []
    for key in sorted(set(full_payload_keys) - set(compact_keys)):
        value = full_user.get(key)
        policy_value = policy.get(key) if key in policy else None
        equal = False
        if key in policy:
            equal = json.dumps(value, ensure_ascii=False, sort_keys=True) == json.dumps(
                policy_value, ensure_ascii=False, sort_keys=True
            )
        rows.append(
            {
                "key": key,
                "bytes": _bytes(value),
                "present_on_response_policy": key in policy,
                "json_equal_to_response_policy": equal,
            }
        )
    return rows


def node_summary(node: dict | None, *, label: str) -> dict:
    if not isinstance(node, dict):
        return {"label": label, "present": False}
    before = node.get("before_anchor") if isinstance(node.get("before_anchor"), dict) else {}
    after = node.get("after_anchor") if isinstance(node.get("after_anchor"), dict) else {}
    return {
        "label": label,
        "present": True,
        "transition_required": node.get("transition_required"),
        "transition_type": node.get("transition_type"),
        "before_scene_id": before.get("scene_id"),
        "after_scene_id": after.get("scene_id"),
        "same_scene": bool(before.get("scene_id") and before.get("scene_id") == after.get("scene_id")),
        "source_fields": list(node.get("source_fields") or []),
        "derivation_codes": list(node.get("derivation_codes") or []),
    }


def scan_recorded_nodes() -> list[dict]:
    paths = [
        SNAPSHOT,
        F3 / "session.json",
        ROOT / "artifacts" / "pr_play_79b" / "live_data" / "session.json",
        ROOT / "artifacts" / "pr_play_79" / "live_data" / "session.json",
    ]
    snap_dir = ROOT / "artifacts" / "pr_play_79b" / "live_data" / "snapshots"
    if snap_dir.exists():
        snaps = sorted(snap_dir.glob("*.json"))
        paths.extend(snaps[:2])
        if len(snaps) > 2:
            paths.append(snaps[-1])
    rows = []
    for path in paths:
        if not path.exists() or path.stat().st_size > 20_000_000:
            rows.append({"path": str(path.relative_to(ROOT)), "skipped": True})
            continue
        try:
            body = load_json(path)
        except (OSError, json.JSONDecodeError) as exc:
            rows.append({"path": str(path.relative_to(ROOT)), "error": type(exc).__name__})
            continue
        found = []

        def walk(obj, trail: str) -> None:
            if isinstance(obj, dict):
                if "transition_required" in obj and "transition_type" in obj and "source_fields" in obj:
                    before = obj.get("before_anchor") if isinstance(obj.get("before_anchor"), dict) else {}
                    after = obj.get("after_anchor") if isinstance(obj.get("after_anchor"), dict) else {}
                    found.append(
                        {
                            "trail": trail,
                            "transition_required": obj.get("transition_required"),
                            "transition_type": obj.get("transition_type"),
                            "before": before.get("scene_id"),
                            "after": after.get("scene_id"),
                            "same_scene": bool(before.get("scene_id") and before.get("scene_id") == after.get("scene_id")),
                            "source_fields": list(obj.get("source_fields") or []),
                        }
                    )
                    return
                for key, child in obj.items():
                    if key in {"log_entries", "chat_history", "transcript"}:
                        continue
                    walk(child, f"{trail}.{key}" if trail else str(key))
            elif isinstance(obj, list) and trail.endswith("snapshots"):
                return

        session = body.get("session") if isinstance(body, dict) and isinstance(body.get("session"), dict) else body
        ctir = session.get("_runtime_canonical_ctir_v1") if isinstance(session, dict) else None
        player = None
        resolved = None
        scene_mutation = None
        if isinstance(ctir, dict):
            player = ctir.get("player_input")
            resolution = ctir.get("resolution") if isinstance(ctir.get("resolution"), dict) else {}
            resolved = resolution.get("resolved_transition")
            scene_mutation = (ctir.get("state_mutations") or {}).get("scene") if isinstance(ctir.get("state_mutations"), dict) else None
        walk(session if isinstance(session, dict) else {}, "")
        rows.append(
            {
                "path": str(path.relative_to(ROOT)),
                "ctir_player_input": player,
                "ctir_resolved_transition": resolved,
                "ctir_scene_mutation": scene_mutation,
                "nodes": found[:6],
                "node_count": len(found),
            }
        )
    return rows


def main() -> None:
    from tests.helpers.storage_isolation import install

    state = prepare_state()
    install(state)
    import openai
    from game.ctir_runtime import detach_ctir
    from game.gm import build_messages, call_gpt
    from game.narrative_planning import _derive_transition_node, build_narrative_plan
    from game import storage
    from game import ctir as ctir_mod

    class _BlockedClient:
        def __init__(self, *args, **kwargs):
            PROVIDER_CALLS["openai_constructed"] += 1
            raise RuntimeError("AT-OPT-05 blocked a live provider client")

    openai.OpenAI = _BlockedClient

    def _blocked_call(*args, **kwargs):
        PROVIDER_CALLS["call_gpt"] += 1
        raise RuntimeError("AT-OPT-05 blocked call_gpt")

    import game.gm as gm_mod

    gm_mod.call_gpt = _blocked_call

    campaign = storage._load_json(storage.CAMPAIGN_PATH, {})
    world = storage._load_json(storage.WORLD_PATH, {})
    session = storage.load_session()
    character = storage._load_json(storage.CHARACTER_PATH, {})
    combat = storage._load_json(storage.COMBAT_PATH, {})
    recent_log = storage.load_log()
    scene = storage.get_effective_scene(session, session["active_scene_id"])
    attached = session.get("_runtime_canonical_ctir_v1") if isinstance(session, dict) else None
    attached_player = attached.get("player_input") if isinstance(attached, dict) else None
    attached_resolution = attached.get("resolution") if isinstance(attached, dict) and isinstance(attached.get("resolution"), dict) else {}
    attached_scene_mutation = (
        (attached.get("state_mutations") or {}).get("scene")
        if isinstance(attached, dict) and isinstance(attached.get("state_mutations"), dict)
        else None
    )

    def build(sess, text, profile, resolution=None):
        return build_messages(
            campaign,
            world,
            copy.deepcopy(sess),
            character,
            scene,
            combat,
            recent_log,
            text,
            resolution=resolution,
            scene_runtime=None,
            prompt_profile=profile,
        )

    step = "I step back from the notice board."
    attached_auto = summarize_build(build(session, step, "manual_play_auto"), label="f3_attached_auto", profile="manual_play_auto")
    attached_compact = summarize_build(
        build(session, step, "manual_play_compact"),
        label="f3_attached_forced_compact",
        profile="manual_play_compact",
    )
    attached_full = summarize_build(build(session, step, "full"), label="f3_attached_full_profile", profile="full")
    detached_session = copy.deepcopy(session)
    detach_ctir(detached_session)
    detached_auto = summarize_build(
        build(detached_session, step, "manual_play_auto"),
        label="f3_detached_auto",
        profile="manual_play_auto",
    )
    detached_full = summarize_build(
        build(detached_session, step, "full"),
        label="f3_detached_full_profile",
        profile="full",
    )

    utterances = [
        "I step back from the notice board.",
        "I look closely at the notice board.",
        "I push the nearest crate.",
        "Hello, Gate Guard.",
        "What do I see?",
        "What did we already learn about the patrol?",
        "I walk through the gate into the district.",
        "I wait and listen.",
    ]
    matrix = []
    for text in utterances:
        for name, sess in (("attached", session), ("detached", detached_session)):
            built = summarize_build(build(sess, text, "manual_play_auto"), label=f"{name}:{text}", profile="manual_play_auto")
            matrix.append(
                {
                    "attachment": name,
                    "player_text": text,
                    "blob_bytes": built["blob_bytes"],
                    "admission_estimate_tokens": built["admission_estimate_tokens"],
                    "instruction_count": built["view"]["instruction_count"],
                    "instruction_bytes": built["view"]["instruction_bytes"],
                    "blockers": built["eligibility_blockers_visible_on_public_payload"],
                    "transition_required": built["view"]["transition_required"],
                    "same_scene": built["view"]["same_scene"],
                    "must_advance_scene": built["view"]["must_advance_scene"],
                    "narrative_mode": built["view"]["narrative_mode"],
                    "uncertainty_present": built["view"]["uncertainty_present"],
                    "follow_up_present": built["view"]["follow_up_present"],
                    "active_topic": built["view"]["active_topic"],
                    "requires_check": built["view"]["requires_check"],
                }
            )

    base = ctir_mod.build_ctir(
        turn_id="at-opt-05",
        scene_id="frontier_gate",
        player_input="I examine the notice board.",
        builder_source="artifacts.at_opt_05.analyze_compact_eligibility",
    )
    public_slice = {"scene_id": "frontier_gate", "location_tokens": ["frontier_gate"]}
    variants = {
        "no_signal": copy.deepcopy(base),
        "same_scene_id_only": copy.deepcopy(base),
        "different_scene_id_only": copy.deepcopy(base),
        "activate_scene_id": copy.deepcopy(base),
        "target_scene_id": copy.deepcopy(base),
        "resolved_transition": copy.deepcopy(base),
        "state_change_arrived": copy.deepcopy(base),
        "time_skip": copy.deepcopy(base),
    }
    variants["same_scene_id_only"]["state_mutations"] = {"scene": {"scene_id": "frontier_gate"}, "session": {}, "combat": {}, "clues_leads": {}}
    variants["different_scene_id_only"]["state_mutations"] = {"scene": {"scene_id": "old_milestone"}, "session": {}, "combat": {}, "clues_leads": {}}
    variants["activate_scene_id"]["state_mutations"] = {"scene": {"activate_scene_id": "old_milestone"}, "session": {}, "combat": {}, "clues_leads": {}}
    variants["target_scene_id"]["resolution"] = {"kind": "scene_transition", "target_scene_id": "old_milestone", "resolved_transition": False}
    variants["resolved_transition"]["resolution"] = {"kind": "scene_transition", "resolved_transition": True, "target_scene_id": "old_milestone"}
    variants["state_change_arrived"]["resolution"] = {"kind": "travel", "state_changes": {"arrived_at_scene": True}, "target_scene_id": "old_milestone"}
    variants["time_skip"]["resolution"] = {
        "kind": "custom",
        "metadata": {"transition_type": "time_skip", "time_anchor_before": "day:3:night", "time_anchor_after": "day:4:dawn"},
    }
    derived = []
    for label, body in variants.items():
        node, _codes = _derive_transition_node(body, public_scene_slice=public_slice)
        plan = build_narrative_plan(ctir=body, public_scene_slice=public_slice)
        plan_node = plan.get("transition_node") if isinstance(plan, dict) else None
        derived.append(
            {
                "variant": label,
                "direct": node_summary(node, label=label),
                "plan_mode": plan.get("narrative_mode") if isinstance(plan, dict) else None,
                "plan_node": node_summary(plan_node if isinstance(plan_node, dict) else None, label=label),
            }
        )

    recorded_ctir_node = None
    if isinstance(attached, dict):
        recorded_node, _codes = _derive_transition_node(attached, public_scene_slice=public_slice)
        recorded_ctir_node = node_summary(recorded_node, label="f3_attached_ctir_rederived")

    full_user = json.loads(build(session, step, "manual_play_auto")[1]["content"])
    compact_user = json.loads(build(session, step, "manual_play_compact")[1]["content"])
    instruction_diff = diff_instructions(list(full_user.get("instructions") or []), list(compact_user.get("instructions") or []))
    dropped = dropped_key_report(
        sorted(full_user.keys()),
        sorted(compact_user.keys()),
        full_user,
        compact_user,
    )
    policy = full_user.get("response_policy") if isinstance(full_user.get("response_policy"), dict) else {}
    authority_names = [
        "narrative_authority",
        "anti_railroading",
        "context_separation",
        "player_facing_narration_purity",
        "narrative_authenticity",
        "fallback_behavior",
        "no_validator_voice",
        "answer_completeness",
    ]
    policy_presence = {name: name in policy for name in authority_names}

    def savings(left: dict, right: dict) -> dict:
        delta = right["blob_bytes"] - left["blob_bytes"]
        return {
            "from": left["label"],
            "to": right["label"],
            "full_blob_bytes": left["blob_bytes"],
            "compact_blob_bytes": right["blob_bytes"],
            "absolute_byte_reduction": left["blob_bytes"] - right["blob_bytes"],
            "percentage_reduction": round((left["blob_bytes"] - right["blob_bytes"]) / left["blob_bytes"] * 100, 2) if left["blob_bytes"] else None,
            "estimate_reduction": left["admission_estimate_tokens"] - right["admission_estimate_tokens"],
            "full_estimate": left["admission_estimate_tokens"],
            "compact_estimate": right["admission_estimate_tokens"],
            "signed_blob_delta_compact_minus_full": delta,
        }

    result = {
        "provider_calls": 0,
        "provider_client_constructed": PROVIDER_CALLS["openai_constructed"],
        "call_gpt_entries": PROVIDER_CALLS["call_gpt"],
        "call_gpt_symbol_is_blocked_wrapper": gm_mod.call_gpt is _blocked_call,
        "unused_import_guard": callable(call_gpt),
        "recorded_provider_input_tokens": RECORDED_INPUT,
        "attached_ctir_player_input": attached_player,
        "attached_ctir_resolved_transition": attached_resolution.get("resolved_transition"),
        "attached_ctir_scene_mutation": attached_scene_mutation,
        "attached_ctir_scene_id": attached.get("scene_id") if isinstance(attached, dict) else None,
        "rederived_from_attached_ctir": recorded_ctir_node,
        "builds": {
            "attached_auto": {k: v for k, v in attached_auto.items() if k != "instruction_lines"},
            "attached_forced_compact": {k: v for k, v in attached_compact.items() if k != "instruction_lines"},
            "attached_full_profile": {k: v for k, v in attached_full.items() if k != "instruction_lines"},
            "detached_auto": {k: v for k, v in detached_auto.items() if k != "instruction_lines"},
            "detached_full_profile": {k: v for k, v in detached_full.items() if k != "instruction_lines"},
        },
        "savings": {
            "forced_compact_vs_attached_auto": savings(attached_auto, attached_compact),
            "detached_auto_vs_attached_auto": savings(attached_auto, detached_auto),
            "detached_auto_vs_detached_full": savings(detached_full, detached_auto),
        },
        "instruction_diff_attached_auto_vs_forced_compact": instruction_diff,
        "keys_absent_from_forced_compact": dropped,
        "response_policy_authority_keys_present": policy_presence,
        "utterance_matrix": matrix,
        "synthetic_transition_nodes": derived,
        "recorded_nodes": scan_recorded_nodes(),
        "attached_auto_instructions": attached_auto["instruction_lines"],
        "forced_compact_instructions": attached_compact["instruction_lines"],
        "detached_auto_instructions": detached_auto["instruction_lines"],
    }
    (OUT / "eligibility_analysis.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "provider_calls": result["provider_calls"],
        "openai_constructed": result["provider_client_constructed"],
        "call_gpt_entries": result["call_gpt_entries"],
        "attached_player": attached_player,
        "attached_resolved_transition": result["attached_ctir_resolved_transition"],
        "attached_scene_mutation": attached_scene_mutation,
        "rederived": recorded_ctir_node,
        "attached_auto_bytes": attached_auto["blob_bytes"],
        "attached_auto_instructions": attached_auto["view"]["instruction_count"],
        "attached_auto_blockers": attached_auto["eligibility_blockers_visible_on_public_payload"],
        "forced_compact_bytes": attached_compact["blob_bytes"],
        "forced_compact_instructions": attached_compact["view"]["instruction_count"],
        "detached_auto_bytes": detached_auto["blob_bytes"],
        "detached_auto_instructions": detached_auto["view"]["instruction_count"],
        "detached_auto_blockers": detached_auto["eligibility_blockers_visible_on_public_payload"],
        "detached_transition_required": detached_auto["view"]["transition_required"],
        "only_in_full_count": len(instruction_diff["only_in_full"]),
        "synthetic": [
            {"variant": row["variant"], "required": row["direct"]["transition_required"], "type": row["direct"]["transition_type"], "mode": row["plan_mode"]}
            for row in derived
        ],
    }, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise
