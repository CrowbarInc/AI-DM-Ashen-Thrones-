"""AT-OPT-03 provider-free primary-narration context measurement.

Reads the PR-PLAY-79D-F3 pre-continuation snapshot and historical ledgers.
Does not call a provider and does not modify production prompt construction.
Writes only under artifacts/at_opt_03/. State is copied to a temporary directory.
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
OPT01_BLOB = 83902
OPT01_ESTIMATE = 28031

os.environ["ASHEN_TEST_EVIDENCE_DIR"] = str(OUT)
os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "1"
os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_RETRIES"] = "1"
os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ.pop("ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION", None)
os.environ.pop("OPENAI_API_KEY", None)

sys.path.insert(0, str(ROOT))


def _bytes(obj) -> int:
    return len(json.dumps(obj, ensure_ascii=False).encode("utf-8"))


def _chars(obj) -> int:
    return len(json.dumps(obj, ensure_ascii=False))


def section_table(payload: dict) -> list[dict]:
    rows = []
    for key, value in payload.items():
        rows.append({"key": key, "bytes": _bytes(value), "chars": _chars(value)})
    rows.sort(key=lambda row: row["bytes"], reverse=True)
    return rows


def child_table(value, limit: int = 16) -> list[dict]:
    if not isinstance(value, dict):
        return []
    rows = [{"key": key, "bytes": _bytes(child)} for key, child in value.items()]
    rows.sort(key=lambda row: row["bytes"], reverse=True)
    return rows[:limit]


def walk_strings(obj, path: str, found: list) -> None:
    if isinstance(obj, str):
        if len(obj) >= 80:
            found.append((path, obj))
        return
    if isinstance(obj, dict):
        for key, child in obj.items():
            walk_strings(child, f"{path}.{key}" if path else str(key), found)
    elif isinstance(obj, list):
        for index, child in enumerate(obj[:40]):
            walk_strings(child, f"{path}[{index}]", found)


def debug_key_paths(obj, path: str = "") -> list[dict]:
    found = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            here = f"{path}.{key}" if path else str(key)
            if key == "debug":
                found.append(
                    {
                        "path": here,
                        "bytes": _bytes(value),
                        "child_keys": sorted(value)[:16] if isinstance(value, dict) else type(value).__name__,
                    }
                )
            else:
                found.extend(debug_key_paths(value, here))
    elif isinstance(obj, list):
        for index, value in enumerate(obj[:30]):
            found.extend(debug_key_paths(value, f"{path}[{index}]"))
    return found


def duplicate_strings(payload: dict) -> dict:
    found: list[tuple[str, str]] = []
    walk_strings(payload, "", found)
    groups: dict[str, list] = {}
    for path, text in found:
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        groups.setdefault(digest, []).append({"path": path, "bytes": len(text.encode("utf-8"))})
    repeated = []
    extra = 0
    for rows in groups.values():
        if len(rows) < 2:
            continue
        extra += rows[0]["bytes"] * (len(rows) - 1)
        repeated.append({"copies": len(rows), "bytes_each": rows[0]["bytes"], "paths": [row["path"] for row in rows]})
    repeated.sort(key=lambda row: row["bytes_each"] * (row["copies"] - 1), reverse=True)
    return {
        "strings_at_least_80_chars": len(found),
        "duplicate_groups": len(repeated),
        "extra_bytes_if_later_copies_removed": extra,
        "largest_groups": repeated[:12],
    }


def drop_key_recursive(obj, key_name: str):
    if isinstance(obj, dict):
        return {key: drop_key_recursive(value, key_name) for key, value in obj.items() if key != key_name}
    if isinstance(obj, list):
        return [drop_key_recursive(value, key_name) for value in obj]
    return obj


def equal_json(left, right) -> bool:
    try:
        return json.dumps(left, ensure_ascii=False, sort_keys=True) == json.dumps(right, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError):
        return False


def partial_policy_projection(payload: dict) -> tuple[dict, dict]:
    """Offline only. Keep unequal turn-packet policy children. Do not mutate the input."""
    projected = copy.deepcopy(payload)
    policy = projected.get("response_policy")
    packet = projected.get("turn_packet")
    info = {"applied": False, "dropped_keys": [], "kept_keys": [], "dropped_bytes": 0}
    if not isinstance(policy, dict) or not isinstance(packet, dict) or not isinstance(packet.get("response_policy"), dict):
        return projected, info
    nested = packet["response_policy"]
    kept = {}
    for key, value in nested.items():
        if key in policy and equal_json(value, policy.get(key)):
            info["dropped_keys"].append(key)
            info["dropped_bytes"] += _bytes(value)
        else:
            kept[key] = value
            info["kept_keys"].append(key)
    if info["dropped_keys"]:
        if kept:
            packet["response_policy"] = kept
        else:
            packet.pop("response_policy", None)
        info["applied"] = True
    return projected, info


def opening_closed(payload: dict) -> bool:
    opening = payload.get("opening_narration_obligations")
    if isinstance(opening, dict) and opening.get("opening_mode") is False:
        return True
    realization = payload.get("opening_scene_realization")
    return isinstance(realization, dict) and realization.get("opening_mode") is False


def drop_closed_opening(payload: dict) -> tuple[dict, list[str]]:
    projected = copy.deepcopy(payload)
    removed = []
    if not opening_closed(projected):
        return projected, removed
    for key in list(projected):
        if key.startswith("opening_"):
            projected.pop(key, None)
            removed.append(key)
    return projected, removed


def message_blob(system: str, user_payload: dict) -> dict:
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
    ]
    blob = json.dumps(messages, ensure_ascii=False).encode("utf-8")
    return {
        "message_count": 2,
        "system_bytes": len(system.encode("utf-8")),
        "system_chars": len(system),
        "user_bytes": len(messages[1]["content"].encode("utf-8")),
        "user_chars": len(messages[1]["content"]),
        "blob_bytes": len(blob),
        "admission_estimate_tokens": max(1, (len(blob) // 3) + 64),
    }


def summarize_messages(messages: list, label: str) -> dict:
    system = messages[0]["content"]
    user = json.loads(messages[1]["content"])
    stats = message_blob(system, user)
    stats["label"] = label
    stats["top_sections"] = section_table(user)[:25]
    stats["system_is_narration_only"] = "NARRATION-ONLY RESPONSE CONTRACT" in system
    return stats, user, system


def compact_gate_from_payload(payload: dict) -> dict:
    obligations = payload.get("narration_obligations") if isinstance(payload.get("narration_obligations"), dict) else {}
    mechanical = payload.get("mechanical_resolution") if isinstance(payload.get("mechanical_resolution"), dict) else {}
    uncertainty = payload.get("uncertainty_hint")
    follow = payload.get("follow_up_pressure")
    anchor = payload.get("active_topic_anchor")
    blockers = []
    if obligations.get("is_opening_scene") or obligations.get("must_advance_scene"):
        blockers.append("narration_obligations_opening_or_advance")
    if mechanical.get("requires_check"):
        blockers.append("requires_check")
    if isinstance(uncertainty, dict) and uncertainty:
        blockers.append("uncertainty_hint_nonempty")
    if isinstance(anchor, dict) and anchor.get("active"):
        blockers.append("active_topic_anchor")
    if isinstance(follow, dict) and follow:
        blockers.append("follow_up_pressure_nonempty")
    return {
        "payload_visible_blockers": blockers,
        "would_be_blocked_by_visible_fields": bool(blockers),
        "uncertainty_hint": uncertainty if _bytes(uncertainty) < 400 else {"bytes": _bytes(uncertainty)},
        "follow_up_pressure": follow if _bytes(follow) < 400 else {"bytes": _bytes(follow)},
        "active_topic_anchor": anchor if _bytes(anchor) < 400 else {"bytes": _bytes(anchor)},
        "obligation_flags": {
            "is_opening_scene": obligations.get("is_opening_scene"),
            "must_advance_scene": obligations.get("must_advance_scene"),
            "active_npc_reply_expected": obligations.get("active_npc_reply_expected"),
        },
    }


def experiment(name: str, baseline: dict, system: str, payload: dict, note: str, removed: list[str]) -> dict:
    stats = message_blob(system, payload)
    return {
        "name": name,
        "note": note,
        "removed_or_transformed": removed,
        "blob_bytes": stats["blob_bytes"],
        "user_bytes": stats["user_bytes"],
        "system_bytes": stats["system_bytes"],
        "admission_estimate_tokens": stats["admission_estimate_tokens"],
        "blob_bytes_delta": stats["blob_bytes"] - baseline["blob_bytes"],
        "estimate_delta": stats["admission_estimate_tokens"] - baseline["admission_estimate_tokens"],
        "authority_note": note,
    }


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def prepare_state() -> Path:
    temp = Path(tempfile.mkdtemp(prefix="at-opt-03-"))
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
    meta_path = OUT / "snapshot_keys.json"
    meta_path.write_text(
        json.dumps(
            {
                "snapshot_top_keys": sorted(snapshot.keys()),
                "session_turn": session.get("turn_counter"),
                "scene": session.get("active_scene_id"),
                "snapshot_log_entries": len(log_entries),
                "scene_files_source": "F3 http_data scenes; the snapshot does not contain scene files",
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    return target


def iter_jsonl(path: Path):
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            yield json.loads(line)


def high_cost_rows() -> list[dict]:
    cycles = {
        "79": ROOT / "artifacts" / "pr_play_79" / "live_data" / "provider_usage.jsonl",
        "79A": ROOT / "artifacts" / "pr_play_79a" / "live_data" / "provider_usage.jsonl",
        "79B": ROOT / "artifacts" / "pr_play_79b" / "live_data" / "provider_usage.jsonl",
        "79C": ROOT / "artifacts" / "pr_play_79c" / "live_data" / "provider_usage.jsonl",
        "79D-F3": ROOT / "artifacts" / "pr_play_79df3" / "http_data" / "provider_usage.jsonl",
    }
    rows = []
    for cycle, path in cycles.items():
        for event in iter_jsonl(path) or []:
            if event.get("event") == "completed" and event.get("sent") is True and int(event.get("input_tokens") or 0) > 20000:
                rows.append(
                    {
                        "cycle": cycle,
                        "attempt_id": event.get("attempt_id"),
                        "purpose": event.get("purpose"),
                        "owner": event.get("owner"),
                        "input_tokens": event.get("input_tokens"),
                        "output_tokens": event.get("output_tokens"),
                        "total_tokens": event.get("total_tokens"),
                        "latency_ms": event.get("latency_ms"),
                        "model": event.get("model"),
                        "refusal": event.get("refusal"),
                        "completion_status": event.get("completion_status"),
                        "time": event.get("time"),
                        "prompt_stored": False,
                    }
                )
    return rows


def log_samples() -> dict:
    """Read-only samples. Player text is taken from log keys when present."""
    interesting = ("player", "text", "input", "utterance", "kind", "visible", "player_facing")
    samples = {}
    paths = {
        "79": ROOT / "artifacts" / "pr_play_79" / "live_data" / "session_log.jsonl",
        "79A": ROOT / "artifacts" / "pr_play_79a" / "live_data" / "session_log.jsonl",
        "79B": ROOT / "artifacts" / "pr_play_79b" / "live_data" / "session_log.jsonl",
        "79C": ROOT / "artifacts" / "pr_play_79c" / "live_data" / "session_log.jsonl",
        "79D-F3": F3 / "session_log.jsonl",
    }
    for cycle, path in paths.items():
        entries = list(iter_jsonl(path) or [])
        keys = sorted({key for entry in entries[:8] if isinstance(entry, dict) for key in entry})
        texts = []
        for entry in entries:
            if not isinstance(entry, dict):
                continue
            for key, value in entry.items():
                if any(token in key.lower() for token in interesting) and isinstance(value, str) and value.strip():
                    texts.append({"key": key, "text": value.strip()[:180]})
            if len(texts) >= 8:
                break
        samples[cycle] = {"entries": len(entries), "keys_in_first_entries": keys, "text_samples": texts[:8]}
    return samples


def main() -> None:
    from tests.helpers.storage_isolation import install

    state = prepare_state()
    install(state)
    import openai
    from game import storage
    from game.gm import (
        NARRATION_ONLY_SYSTEM_PROMPT,
        SYSTEM_PROMPT,
        build_messages,
        collect_narration_context_call_kwargs,
    )
    from game.gm_retry import build_retry_prompt_for_failure
    from game.immutable_valid_response import regeneration_feedback
    from game.physical_adjudication import disabled_retreat_skip
    from game.prompt_context import _compact_manual_play_instructions

    class _BlockedClient:
        def __init__(self, *args, **kwargs):
            raise RuntimeError("AT-OPT-03 blocked a live provider client")

    openai.OpenAI = _BlockedClient

    campaign = storage._load_json(storage.CAMPAIGN_PATH, {})
    world = storage._load_json(storage.WORLD_PATH, {})
    session = storage.load_session()
    character = storage._load_json(storage.CHARACTER_PATH, {})
    combat = storage._load_json(storage.COMBAT_PATH, {})
    recent_log = storage.load_log()
    scene = storage.get_effective_scene(session, session["active_scene_id"])
    user_text = "I step back from the notice board."

    messages = build_messages(
        campaign,
        world,
        copy.deepcopy(session),
        character,
        scene,
        combat,
        recent_log,
        user_text,
        resolution=None,
        scene_runtime=None,
        prompt_profile="manual_play_auto",
    )
    baseline, payload, system = summarize_messages(messages, "f3_snapshot_resolution_none")
    provider_client_constructed = False

    policy = payload.get("response_policy") if isinstance(payload.get("response_policy"), dict) else {}
    packet = payload.get("turn_packet") if isinstance(payload.get("turn_packet"), dict) else {}
    nested = packet.get("response_policy") if isinstance(packet.get("response_policy"), dict) else {}
    nested_compare = []
    for key, value in nested.items():
        root_value = policy.get(key)
        unequal_detail = None
        if key in policy and not equal_json(value, root_value):
            nested_keys = set(value) if isinstance(value, dict) else set()
            root_keys = set(root_value) if isinstance(root_value, dict) else set()
            unequal_detail = {
                "nested_type": type(value).__name__,
                "root_type": type(root_value).__name__,
                "keys_only_in_nested": sorted(nested_keys - root_keys),
                "keys_only_in_root": sorted(root_keys - nested_keys),
            }
        nested_compare.append(
            {
                "key": key,
                "nested_bytes": _bytes(value),
                "root_bytes": _bytes(root_value) if key in policy else None,
                "present_on_root": key in policy,
                "json_equal_to_root": key in policy and equal_json(value, root_value),
                "unequal_detail": unequal_detail,
            }
        )
    contracts = packet.get("contracts") if isinstance(packet.get("contracts"), dict) else {}
    contract_compare = []
    for key, value in contracts.items():
        contract_compare.append(
            {
                "key": key,
                "bytes": _bytes(value),
                "json_equal_to_root_policy": key in policy and equal_json(value, policy.get(key)),
            }
        )

    projected, partial_info = partial_policy_projection(payload)
    no_debug = drop_key_recursive(payload, "debug")
    no_opening, opening_keys = drop_closed_opening(payload)
    no_validator = copy.deepcopy(payload)
    validator_removed = False
    plan = no_validator.get("dialogue_social_plan")
    if isinstance(plan, dict) and "validator" in plan:
        plan.pop("validator", None)
        validator_removed = True
    combined = drop_key_recursive(projected, "debug")
    combined, _opening_also = drop_closed_opening(combined)
    if isinstance(combined.get("dialogue_social_plan"), dict):
        combined["dialogue_social_plan"].pop("validator", None)

    compact_lines = _compact_manual_play_instructions(
        mode_instruction="Narration mode: standard. Use 1-4 concise paragraphs with a balance of description and pacing.",
        narration_obligations=payload.get("narration_obligations") if isinstance(payload.get("narration_obligations"), dict) else {},
        response_policy=policy,
        has_active_interlocutor=bool(payload.get("active_interlocutor")),
        social_authority=False,
        has_scene_change_context=False,
        naming_line=None,
        answer_style_hints=[],
        narrative_plan_present=isinstance(payload.get("narrative_plan"), dict),
        narrative_mode_instruction_lines=[],
    )
    compact_payload = copy.deepcopy(payload)
    compact_payload["instructions"] = compact_lines

    narration_only_stats = message_blob(NARRATION_ONLY_SYSTEM_PROMPT, payload)
    experiments = [
        experiment(
            "partial_equal_turn_packet_policy",
            baseline,
            system,
            projected,
            "Equal turn_packet.response_policy children are removed. Unequal children stay. Root response_policy stays.",
            partial_info["dropped_keys"],
        ),
        experiment(
            "drop_nested_debug_keys",
            baseline,
            system,
            no_debug,
            "Every object key named debug is removed from a copy. This includes referent and packet debug.",
            ["debug"],
        ),
        experiment(
            "drop_opening_keys_when_opening_mode_false",
            baseline,
            system,
            no_opening,
            "opening_* keys are removed only when the payload already says this is not an opening.",
            opening_keys,
        ),
        experiment(
            "drop_dialogue_validator",
            baseline,
            system,
            no_validator,
            "dialogue_social_plan.validator is removed from the copy. The rest of the plan stays.",
            ["dialogue_social_plan.validator"] if validator_removed else [],
        ),
        experiment(
            "replace_instructions_with_existing_compact_list",
            baseline,
            system,
            compact_payload,
            "User instructions are replaced by the existing compact-instruction helper. Response policy stays. Narrative-mode lines were not copied into the compact list, so this understates the compact instruction block.",
            ["instructions"],
        ),
        {
            "name": "narration_only_system_prompt_on_same_user_payload",
            "note": "System text is swapped for the narration-only prompt. The user payload, including structured-claim instructions, is unchanged. This is not a legal envelope change.",
            "removed_or_transformed": ["system_prompt_schema"],
            "blob_bytes": narration_only_stats["blob_bytes"],
            "admission_estimate_tokens": narration_only_stats["admission_estimate_tokens"],
            "blob_bytes_delta": narration_only_stats["blob_bytes"] - baseline["blob_bytes"],
            "estimate_delta": narration_only_stats["admission_estimate_tokens"] - baseline["admission_estimate_tokens"],
        },
    ]
    combined_stats = message_blob(system, combined)
    experiments.append(
        {
            "name": "combined_equal_policy_debug_opening_validator",
            "note": "Stacks the equal-policy, debug, closed-opening, and validator removals. Does not remove unequal policy or the standing instruction list.",
            "removed_or_transformed": partial_info["dropped_keys"] + ["debug"] + _opening_also + (["validator"] if validator_removed else []),
            "blob_bytes": combined_stats["blob_bytes"],
            "admission_estimate_tokens": combined_stats["admission_estimate_tokens"],
            "blob_bytes_delta": combined_stats["blob_bytes"] - baseline["blob_bytes"],
            "estimate_delta": combined_stats["admission_estimate_tokens"] - baseline["admission_estimate_tokens"],
        }
    )

    utterances = [
        "I step back from the notice board.",
        "What do I see?",
        "Hello, Gate Guard.",
        "I look closely at the notice board.",
        "I push the nearest crate.",
        "What did we already learn about the patrol?",
        "I wait and listen.",
        "Something feels wrong here. What should I do?",
    ]
    utterance_rows = []
    for text in utterances:
        built = build_messages(
            campaign,
            world,
            copy.deepcopy(session),
            character,
            scene,
            combat,
            recent_log,
            text,
            resolution=None,
            scene_runtime=None,
            prompt_profile="manual_play_auto",
        )
        stats, body, _system_text = summarize_messages(built, text)
        utterance_rows.append(
            {
                "player_text": text,
                "retreat_skip_sentence": disabled_retreat_skip(text, session),
                "blob_bytes": stats["blob_bytes"],
                "admission_estimate_tokens": stats["admission_estimate_tokens"],
                "system_is_narration_only": stats["system_is_narration_only"],
                "instruction_bytes": next((row["bytes"] for row in stats["top_sections"] if row["key"] == "instructions"), None),
                "response_policy_bytes": next((row["bytes"] for row in stats["top_sections"] if row["key"] == "response_policy"), None),
                "recent_log_bytes": next((row["bytes"] for row in stats["top_sections"] if row["key"] == "recent_log"), None),
                "player_input_bytes": next((row["bytes"] for row in stats["top_sections"] if row["key"] == "player_input"), None),
                "compact_gate": compact_gate_from_payload(body),
                "delta_blob_vs_step_back": stats["blob_bytes"] - baseline["blob_bytes"],
            }
        )

    retry_samples = []
    for failure_class in ("validator_voice", "echo_or_repetition", "scene_stall", "unresolved_question"):
        text = build_retry_prompt_for_failure(
            {"failure_class": failure_class, "reasons": [failure_class]},
            response_policy=policy,
            gm_output={"player_facing_text": "The gate stays where it is."},
            player_text=user_text,
        )
        retry_samples.append({"source": "build_retry_prompt_for_failure", "failure_class": failure_class, "bytes": len(text.encode("utf-8")), "chars": len(text)})
    feedback = regeneration_feedback(["structured_contract_failure"], resolution=None, audit=None)
    retry_samples.append({"source": "regeneration_feedback_without_resolution", "bytes": len(feedback.encode("utf-8")), "chars": len(feedback)})

    route_rows = []
    try:
        import openai as openai_mod
        from game.api import build_messages as api_build_messages
        from game.api import chat
        from game.gm import call_gpt as real_call_gpt
        from game.models import ChatRequest

        captured = {"builds": 0, "calls": 0}

        def _recording_build(*args, **kwargs):
            captured["builds"] += 1
            return build_messages(*args, **kwargs)

        def _recording_call(messages, **kwargs):
            captured["calls"] += 1
            return real_call_gpt(messages, **kwargs)

        import game.api as api_mod
        import game.gm as gm_mod

        api_mod.build_messages = _recording_build
        gm_mod.call_gpt = _recording_call
        api_mod.call_gpt = _recording_call
        openai_mod.OpenAI = _BlockedClient

        pristine = {
            "session": (state / "session.json").read_text(encoding="utf-8"),
            "world": (state / "world.json").read_text(encoding="utf-8"),
            "log": (state / "session_log.jsonl").read_text(encoding="utf-8") if (state / "session_log.jsonl").exists() else "",
        }
        for text in (
            "I step back from the notice board.",
            "What do I see?",
            "Hello, Gate Guard.",
        ):
            (state / "session.json").write_text(pristine["session"], encoding="utf-8")
            (state / "world.json").write_text(pristine["world"], encoding="utf-8")
            (state / "session_log.jsonl").write_text(pristine["log"], encoding="utf-8")
            before = dict(captured)
            try:
                response = chat(ChatRequest(text=text))
                gm = response.get("gm_output") if isinstance(response, dict) else {}
                visible = str((gm or {}).get("player_facing_text") or "")[:240]
                tags = list((gm or {}).get("tags") or []) if isinstance(gm, dict) else []
                error = None
            except Exception as exc:  # noqa: BLE001 — record the blocker, do not continue into a provider.
                visible = ""
                tags = []
                error = f"{type(exc).__name__}: {exc}"
                if "live provider" in str(exc):
                    provider_client_constructed = True
            route_rows.append(
                {
                    "player_text": text,
                    "build_messages_calls": captured["builds"] - before["builds"],
                    "call_gpt_entries": captured["calls"] - before["calls"],
                    "visible_prefix": visible,
                    "tags": tags[:12],
                    "error": error,
                }
            )
    except Exception:
        route_rows.append({"error": traceback.format_exc(limit=8)})

    user_bytes = baseline["user_bytes"]
    attributed = []
    for row in baseline["top_sections"]:
        share = (row["bytes"] / user_bytes) if user_bytes else 0
        attributed.append(
            {
                **row,
                "share_of_user_json": round(share, 4),
                "bytes_div_3": row["bytes"] // 3,
            }
        )
    scaffold_keys = {
        "response_policy",
        "instructions",
        "turn_packet",
        "narrative_plan",
        "referent_tracking",
        "dialogue_social_plan",
        "narration_visibility",
        "scene_state_anchor_contract",
        "speaker_selection",
        "narration_obligations",
        "player_expression_contract",
        "bounded_improvisation",
        "first_mention_contract",
        "interaction_continuity",
    }
    state_keys = {
        "scene",
        "character",
        "campaign",
        "recent_log",
        "clues",
        "player_input",
        "lead_context",
        "combat",
        "session",
        "selected_conversational_memory",
        "mechanical_resolution",
    }
    by_key = {row["key"]: row["bytes"] for row in baseline["top_sections"]}
    result = {
        "classification": "RECONSTRUCTED",
        "provider_calls": 0,
        "provider_client_constructed": provider_client_constructed,
        "recorded_provider_input_tokens": RECORDED_INPUT,
        "opt01_reconstruction_blob_bytes": OPT01_BLOB,
        "opt01_admission_estimate": OPT01_ESTIMATE,
        "basis": "F3 snapshot 2026-11-08T16-50-45_8caf7aff session, F3 http_data scene files, current working-tree build_messages, resolution None, prompt_profile manual_play_auto. Not the captured provider payload.",
        "full_system_prompt_bytes": len(SYSTEM_PROMPT.encode("utf-8")),
        "narration_only_system_prompt_bytes": len(NARRATION_ONLY_SYSTEM_PROMPT.encode("utf-8")),
        "baseline": baseline,
        "matches_opt01_blob_bytes": baseline["blob_bytes"] == OPT01_BLOB,
        "estimate_minus_recorded": baseline["admission_estimate_tokens"] - RECORDED_INPUT,
        "section_attribution": attributed,
        "scaffold_bytes": sum(by_key.get(key, 0) for key in scaffold_keys),
        "gameplay_state_bytes": sum(by_key.get(key, 0) for key in state_keys),
        "response_policy_children": child_table(policy),
        "turn_packet_children": child_table(packet),
        "narrative_plan_children": child_table(payload.get("narrative_plan")),
        "nested_policy_compare": nested_compare,
        "turn_packet_contract_compare": contract_compare,
        "partial_policy_info": partial_info,
        "duplicate_strings": duplicate_strings(payload),
        "compact_gate": compact_gate_from_payload(payload),
        "instruction_count": len(payload.get("instructions") or []) if isinstance(payload.get("instructions"), list) else None,
        "compact_instruction_count": len(compact_lines),
        "compact_instruction_bytes": _bytes(compact_lines),
        "experiments": experiments,
        "utterances_resolution_none": utterance_rows,
        "production_route_samples": route_rows,
        "retry_instruction_samples": retry_samples,
        "historical_over_20000": high_cost_rows(),
        "session_log_samples": log_samples(),
        "recent_log_entries_loaded": len(recent_log),
        "transition_keys": sorted(payload["transition"]) if isinstance(payload.get("transition"), dict) else None,
        "transition_required": (payload.get("transition") or {}).get("transition_required") if isinstance(payload.get("transition"), dict) else None,
        "debug_key_paths": debug_key_paths(payload),
        "instruction_lines_mentioning_debug": sum(
            1 for line in (payload.get("instructions") or []) if isinstance(line, str) and "debug" in line.lower()
        ),
        "active_scene_id": session.get("active_scene_id"),
        "turn_counter": session.get("turn_counter"),
    }
    (OUT / "measurements.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({
        "blob_bytes": baseline["blob_bytes"],
        "estimate": baseline["admission_estimate_tokens"],
        "matches_opt01": result["matches_opt01_blob_bytes"],
        "scaffold_bytes": result["scaffold_bytes"],
        "state_bytes": result["gameplay_state_bytes"],
        "experiments": [{k: row.get(k) for k in ("name", "blob_bytes_delta", "estimate_delta")} for row in experiments],
        "routes": route_rows,
        "high_cost": len(result["historical_over_20000"]),
        "provider_client_constructed": provider_client_constructed,
    }, indent=2))
    shutil.rmtree(state.parent, ignore_errors=True)


if __name__ == "__main__":
    main()
