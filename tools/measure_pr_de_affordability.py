"""PR-DE deterministic affordability benchmark. No provider calls. No production saves."""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
from unittest.mock import patch

import game.gm as gm
from game.defaults import default_campaign, default_character, default_combat, default_conditions
from game.storage import DATA_DIR

ROOT = Path(__file__).resolve().parents[1]
OUT_ROOT = ROOT / "artifacts" / "affordability"
PR_DE = ROOT / "artifacts" / "pr_de_contract_deduplication"

MIRRORS = (
    ("anti_railroading_contract", "anti_railroading"),
    ("context_separation_contract", "context_separation"),
    ("player_facing_narration_purity_contract", "player_facing_narration_purity"),
    ("social_response_structure_contract", "social_response_structure"),
    ("interaction_continuity_contract", "interaction_continuity"),
    ("fallback_behavior", "fallback_behavior"),
    ("conversational_memory_window", "conversational_memory_window"),
)

WATCH = [
    DATA_DIR / "session.json",
    DATA_DIR / "world.json",
    DATA_DIR / "combat.json",
    DATA_DIR / "session_log.jsonl",
    DATA_DIR / "character.json",
    DATA_DIR / "campaign.json",
]


def _load_pr_dd():
    path = ROOT / "artifacts" / "pr_dd_context_budget_architecture" / "measure_pr_dd.py"
    spec = importlib.util.spec_from_file_location("measure_pr_dd", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _json_equal(left, right) -> bool:
    try:
        return _canonical(left) == _canonical(right)
    except (TypeError, ValueError):
        return False


def _mtimes() -> dict:
    out = {}
    for path in WATCH:
        out[path.name] = path.stat().st_mtime_ns if path.exists() else None
    return out


def _tokenizer_count(text: str):
    try:
        import tiktoken
    except ImportError:
        return None, "unavailable_estimate_ceil_chars_div_4"
    try:
        encoding = tiktoken.get_encoding("o200k_base")
        name = "tiktoken_o200k_base"
    except Exception:
        encoding = tiktoken.get_encoding("cl100k_base")
        name = "tiktoken_cl100k_base"
    return len(encoding.encode(text)), name


def _speaker(payload: dict) -> str:
    speaker = payload.get("speaker_selection") if isinstance(payload.get("speaker_selection"), dict) else {}
    interlocutor = payload.get("active_interlocutor") if isinstance(payload.get("active_interlocutor"), dict) else {}
    primary = str(speaker.get("primary_speaker_id") or interlocutor.get("npc_id") or "").strip()
    return primary


def _authority(payload: dict) -> dict:
    mechanical = payload.get("mechanical_resolution") if isinstance(payload.get("mechanical_resolution"), dict) else {}
    social = mechanical.get("social") if isinstance(mechanical.get("social"), dict) else {}
    decision = payload.get("gm_resolution_decision") if isinstance(payload.get("gm_resolution_decision"), dict) else {}
    contract = payload.get("resolution_contract") if isinstance(payload.get("resolution_contract"), dict) else {}
    recipe = payload.get("decision_facing_answer_recipe") if isinstance(payload.get("decision_facing_answer_recipe"), dict) else {}
    scene = payload.get("scene") if isinstance(payload.get("scene"), dict) else {}
    public = scene.get("public") if isinstance(scene.get("public"), dict) else {}
    hidden = ((scene.get("gm_only") or {}) if isinstance(scene.get("gm_only"), dict) else {}).get("hidden_facts") or []
    return {
        "resolution_kind": mechanical.get("kind") or payload.get("resolution_kind"),
        "resolver": ((mechanical.get("metadata") or {}) if isinstance(mechanical.get("metadata"), dict) else {}).get("selected_resolver"),
        "contract_operation": contract.get("operation"),
        "reply_plan_kind": social.get("reply_plan_kind"),
        "npc_speech_authority": social.get("npc_speech_authority"),
        "objective_world_fact_authority": social.get("objective_world_fact_authority"),
        "durable_state_mutation_allowed": social.get("durable_state_mutation_allowed"),
        "permitted_state_mutations": decision.get("permitted_state_mutations"),
        "answer_operation": ((recipe.get("turn_operation") or {}) if isinstance(recipe.get("turn_operation"), dict) else {}).get("response_operation"),
        "visible_fact_count": len(public.get("visible_facts") or []) if isinstance(public.get("visible_facts"), list) else None,
        "hidden_fact_count": len(hidden) if isinstance(hidden, list) else None,
        "skill_check_present": bool(payload.get("skill_check") or mechanical.get("skill_check")),
        "scene_transition_already_occurred": payload.get("scene_transition_already_occurred"),
        "target_scene_id": mechanical.get("target_scene_id"),
    }


def _duplicates(payload: dict) -> list[dict]:
    policy = payload.get("response_policy") if isinstance(payload.get("response_policy"), dict) else {}
    rows = []
    for top_key, policy_key in MIRRORS:
        top_present = top_key in payload
        policy_present = policy_key in policy
        equal = top_present and policy_present and _json_equal(payload.get(top_key), policy.get(policy_key))
        top_bytes = len(json.dumps(payload.get(top_key), ensure_ascii=False).encode("utf-8")) if top_present else 0
        rows.append({
            "top_level_field": top_key,
            "policy_child": f"response_policy.{policy_key}",
            "top_level_present": top_present,
            "policy_child_present": policy_present,
            "exact_json_equal": equal,
            "serialized_duplicate_bytes": top_bytes if equal else 0,
            "top_level_bytes": top_bytes,
            "expected_saving_bytes": top_bytes if equal else 0,
            "removed_by_this_phase": False,
        })
    snapshot_present = "interaction_continuity" in payload
    snapshot_equal = (
        snapshot_present
        and "interaction_continuity" in policy
        and _json_equal(payload.get("interaction_continuity"), policy.get("interaction_continuity"))
    )
    rows.append({
        "top_level_field": "interaction_continuity",
        "policy_child": "response_policy.interaction_continuity",
        "top_level_present": snapshot_present,
        "policy_child_present": "interaction_continuity" in policy,
        "exact_json_equal": snapshot_equal,
        "serialized_duplicate_bytes": 0,
        "top_level_bytes": len(json.dumps(payload.get("interaction_continuity"), ensure_ascii=False).encode("utf-8")) if snapshot_present else 0,
        "expected_saving_bytes": 0,
        "removed_by_this_phase": False,
        "note": "distinct smaller snapshot; retain even when the contract mirror is removed",
    })
    return rows


def _record(fixture_id: str, interaction_class: str, player: str, messages, *, source: str, designation: str, limitation: str = ""):
    blob, system, user_parts, payload = _DD._split(messages)
    payload = payload if isinstance(payload, dict) else {}
    policy = payload.get("response_policy") if isinstance(payload.get("response_policy"), dict) else {}
    instructions = payload.get("instructions") if isinstance(payload.get("instructions"), list) else []
    projection = payload.get("provider_context_projection") if isinstance(payload.get("provider_context_projection"), dict) else {}
    exact_tokens, tokenizer_name = _tokenizer_count(blob)
    duplicates = _duplicates(payload)
    authority = _authority(payload)
    return {
        "fixture_id": fixture_id,
        "interaction_class": interaction_class,
        "player_input": player,
        "resolver": authority.get("resolver"),
        "response_envelope": gm._provider_response_contract_from_messages(messages),
        "projection_selected": projection.get("selected") is True,
        "projection_mode": projection.get("mode"),
        "serialized_bytes": len(blob.encode("utf-8")),
        "character_count": len(blob),
        "estimated_input_tokens": (len(blob) + 3) // 4,
        "exact_input_tokens": exact_tokens,
        "tokenizer": tokenizer_name,
        "payload_sha256": _sha(blob),
        "system_prompt_bytes": len(system.encode("utf-8")),
        "response_policy_bytes": len(json.dumps(policy, ensure_ascii=False).encode("utf-8")) if policy else 0,
        "instruction_bytes": len(json.dumps(instructions, ensure_ascii=False).encode("utf-8")) if instructions else 0,
        "instruction_text_bytes": sum(len(item.encode("utf-8")) for item in instructions if isinstance(item, str)),
        "conversation_history_bytes": len(json.dumps({
            "recent_log": payload.get("recent_log"),
            "selected_conversational_memory": payload.get("selected_conversational_memory"),
            "conversational_memory_window": (
                payload.get("conversational_memory_window")
                if isinstance(payload.get("conversational_memory_window"), dict)
                else policy.get("conversational_memory_window")
            ),
        }, ensure_ascii=False).encode("utf-8")),
        "authorized_speaker": _speaker(payload),
        "authority_outcome": authority,
        "fixture_source": source,
        "designation": designation,
        "limitation": limitation,
        "message_count": len(messages),
        "duplicate_verification": duplicates,
        "exact_duplicate_bytes": sum(row["serialized_duplicate_bytes"] for row in duplicates),
        "response_policy_children": sorted(policy.keys()),
        "build_messages_boundary": "json.dumps(payload, ensure_ascii=False) joined to the system prompt with a newline",
        "api_serialization_note": "game.api may later rewrite the user message with ensure_ascii=True; that rewrite is not this hash",
    }, payload


def _build_required():
    from tests.test_combat_resolution import _scene_with_goblin
    from tests.test_pr_db_speaker_grounding import TURN_1, TURN_2, TURN_3

    rows = []
    payloads = {}

    def add_social(fixture_id, interaction_class, text, *, prior=None, bind=False, source, designation="authored"):
        session, scene, world, resolution, view = _DD._social(text, prior=prior, bind=bind)
        messages = _DD._messages_for(resolution, session, scene, world, text)
        record, payload = _record(
            fixture_id, interaction_class, text, messages, source=source, designation=designation,
        )
        record["resolver"] = record["resolver"] or view.get("resolver")
        rows.append(record)
        payloads[fixture_id] = payload

    add_social(
        "S1", "harmless_npc_preference", TURN_1,
        source="tests.test_pr_db_speaker_grounding.TURN_1 via measure_pr_dd._social",
    )
    add_social(
        "S2", "experiential_followup", TURN_2, prior=[TURN_1],
        source="TURN_2 after TURN_1; PR-DD increments turn_counter between turns",
    )
    add_social(
        "S3", "multi_turn_continuation", TURN_3, prior=[TURN_1, TURN_2],
        source="TURN_3 after TURN_1 and TURN_2; PR-DD increments turn_counter between turns",
    )
    add_social(
        "F1", "authored_factual_question", "Captain, what do you know about the missing patrol?",
        bind=True,
        source="authored frontier_gate; player line from PR-DD F1 / tests/test_pr_cp_authorized_finalization.py",
    )
    add_social(
        "C1", "consequential_social", "Does rain make it easier to assassinate the captain?",
        bind=True, source="authored frontier_gate; PR-DC negative control line",
    )
    add_social(
        "H1", "hidden_information_question", "Where is the secret tunnel?",
        bind=True, source="authored frontier_gate; PR-DC negative control line",
    )

    explore_lines = [
        ("N1", "notice_board_inspection", "I examine the notice board for anything unusual.", "PR-DD notice-board line"),
        ("O1", "ordinary_observation", "I look around.", "PR-DD ordinary observation"),
        ("M1", "ordinary_movement", "I walk closer to the notice board.", "PR-DD movement line; destination may stay unbound"),
        ("T1", "scene_transition", "Enter Cinderwatch", "authored frontier_gate exit"),
    ]
    for fixture_id, interaction_class, text, source in explore_lines:
        session, scene, world, resolution, view = _DD._explore(text)
        messages = _DD._messages_for(resolution, session, scene, world, text)
        record, payload = _record(fixture_id, interaction_class, text, messages, source=source, designation="authored")
        record["resolver"] = record["resolver"] or view.get("resolver")
        record["limitation"] = "" if view.get("kind") else "resolution kind missing"
        if fixture_id == "M1" and not (payload.get("mechanical_resolution") or {}).get("resolved_transition"):
            record["limitation"] = "movement line did not bind an exit; inherited PR-DD limitation"
        rows.append(record)
        payloads[fixture_id] = payload

    from game.exploration import resolve_exploration_action
    from game.live_resolution import attach_interaction_obligation
    from game.scene_actions import normalize_scene_action

    skill_scene = {"scene": {"id": "x", "location": "X", "skill_check_defaults": {"investigate": {"skill_id": "perception", "dc": 8}}}}
    skill_character = default_character()
    skill_character.setdefault("skills", {})["perception"] = 2
    action = normalize_scene_action({"id": "inv", "label": "Investigate", "type": "investigate", "prompt": "Search."})
    skill_session = {"active_scene_id": "x", "turn_counter": 1, "scene_state": {"active_scene_id": "x"}}
    skill_world = {"npcs": []}
    skill_resolution = resolve_exploration_action(
        skill_scene, skill_session, skill_world, action, raw_player_text="Search.",
        character=skill_character, list_scene_ids=lambda: [],
    )
    attach_interaction_obligation(
        skill_resolution, player_text="Search.", session=skill_session, normalized_action=action,
        scene_id="x", scene=skill_scene, world=skill_world, enable_model_interpretation=False,
    )
    skill_messages = _DD._messages_for(
        skill_resolution, skill_session, skill_scene, skill_world, "Search.", character=skill_character,
    )
    record, payload = _record(
        "K1", "synthetic_skill_check", "Search.", skill_messages,
        source="tests/test_exploration_skill_checks.py shape; scene id x",
        designation="synthetic",
        limitation="synthetic scene; not authored campaign state",
    )
    rows.append(record)
    payloads["K1"] = payload

    combat_scene = {"scene": _scene_with_goblin()["scene"]}
    combat_state = {
        "in_combat": True, "round": 1, "initiative_order": [], "turn_index": 0,
        "active_actor_id": "galinor", "player_turn_used": False,
    }
    with patch("game.combat.roll_die", return_value=10):
        from game.combat import resolve_attack
        attack = resolve_attack(default_character(), combat_scene, "quarterstaff", "goblin_1", [], default_conditions())
    combat_session = {"active_scene_id": "frontier_gate", "turn_counter": 1, "scene_state": {"active_scene_id": "frontier_gate"}}
    combat_world = {"npcs": []}
    attach_interaction_obligation(
        attack, player_text="I attack the goblin with my quarterstaff.", session=combat_session,
        normalized_action={"type": "attack", "prompt": "I attack the goblin with my quarterstaff.", "label": "Attack"},
        scene_id="frontier_gate", scene=combat_scene, world=combat_world, enable_model_interpretation=False,
    )
    combat_messages = _DD._messages_for(
        attack, combat_session, combat_scene, combat_world,
        "I attack the goblin with my quarterstaff.", combat=combat_state,
    )
    record, payload = _record(
        "B1", "synthetic_combat", "I attack the goblin with my quarterstaff.", combat_messages,
        source="tests/test_combat_resolution.py::_scene_with_goblin; roll_die patched to 10",
        designation="synthetic",
        limitation="goblin is a test fixture; authored scenes have no enemies",
    )
    rows.append(record)
    payloads["B1"] = payload
    return rows, payloads


def _diff_paths(left, right, prefix=""):
    diffs = []
    if type(left) is not type(right) and not (isinstance(left, (int, float)) and isinstance(right, (int, float))):
        diffs.append({"path": prefix or "$", "left": _preview(left), "right": _preview(right), "kind": "type"})
        return diffs
    if isinstance(left, dict):
        keys = list(dict.fromkeys([*left.keys(), *right.keys()]))
        for key in keys:
            path = f"{prefix}.{key}" if prefix else str(key)
            if key not in left:
                diffs.append({"path": path, "left": None, "right": _preview(right[key]), "kind": "added"})
            elif key not in right:
                diffs.append({"path": path, "left": _preview(left[key]), "right": None, "kind": "removed"})
            else:
                diffs.extend(_diff_paths(left[key], right[key], path))
        return diffs
    if isinstance(left, list):
        if len(left) != len(right):
            diffs.append({"path": prefix, "left": f"len {len(left)}", "right": f"len {len(right)}", "kind": "length"})
        for index, (item_left, item_right) in enumerate(zip(left, right)):
            diffs.extend(_diff_paths(item_left, item_right, f"{prefix}[{index}]"))
        return diffs
    if left != right:
        diffs.append({"path": prefix or "$", "left": _preview(left), "right": _preview(right), "kind": "value"})
    return diffs


def _preview(value) -> str:
    text = json.dumps(value, ensure_ascii=False, default=str) if not isinstance(value, str) else value
    if len(text) > 180:
        return text[:177] + "..."
    return text


def _classify_diff(path: str, left: str, right: str) -> str:
    blob = f"{path} {left} {right}".lower()
    if "clue_text_digest" in blob:
        return "B_python_hash_seed_digest"
    if any(token in blob for token in ("pr-db", "pr-dd", "builder_source", "turn_id", "turn_stamp")):
        return "B_measurement_harness"
    if path.endswith("turn_counter") or path.endswith("turn_index"):
        return "A_fixture_reconstruction_turn_counter"
    if "contract_id" in path:
        return "A_generated_contract_id_from_turn_index"
    if any(token in path.lower() for token in ("timestamp", "created_at", "updated_at", "uuid", "nonce")):
        return "A_expected_dynamic"
    return "D_unresolved"


def _hash_stability():
    """Compare PR-DC and PR-DD reconstructions of S2 and S3. Does not change gameplay."""
    from tests.test_pr_db_speaker_grounding import TURN_1, TURN_2, TURN_3, _gate_session_scene, play_turn

    db_path = ROOT / "artifacts" / "pr_db_speaker_grounding" / "_measure.py"
    spec = importlib.util.spec_from_file_location("pr_db_measure", db_path)
    db = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(db)

    def pr_dc_messages(texts):
        session, scene, world = _gate_session_scene()
        result = None
        for text in texts:
            result = play_turn(session, scene, world, text)
        scene = dict(scene)
        scene.pop("_is_canon", None)
        messages = db._messages_for(result, session, scene, world, texts[-1])
        blob, payload, _envelope = db._payload_from_messages(messages)
        return blob, payload, int(session.get("turn_counter") or 0)

    def pr_dd_messages(text, prior):
        session, scene, world, resolution, _view = _DD._social(text, prior=prior, bind=False)
        messages = _DD._messages_for(resolution, session, scene, world, text)
        blob, _system, _users, payload = _DD._split(messages)
        return blob, payload, int(session.get("turn_counter") or 0)

    cases = []
    for fixture_id, current, prior, pr_dc_hash, pr_dc_bytes in (
        ("S2", TURN_2, [TURN_1], "2c48c12d57a8ca9d81f60d7de9a7386e6251cce484cc9df4728988a6265d2f52", 98123),
        ("S3", TURN_3, [TURN_1, TURN_2], "c22f940c438c62ad7ff26582a86f2dbeddb7d55b4316f72e5a5ed43b7ca5f3a6", 98061),
    ):
        dc_blob, dc_payload, dc_counter = pr_dc_messages([*prior, current])
        dd_blob, dd_payload, dd_counter = pr_dd_messages(current, prior)
        diffs = _diff_paths(dc_payload, dd_payload)
        grouped: dict[str, int] = {}
        classified = []
        for row in diffs:
            bucket = _classify_diff(row["path"], str(row.get("left")), str(row.get("right")))
            grouped[bucket] = grouped.get(bucket, 0) + 1
            if len(classified) < 80:
                classified.append({**row, "bucket": bucket})
        cases.append({
            "fixture_id": fixture_id,
            "pr_dc_recorded_bytes": pr_dc_bytes,
            "pr_dc_recorded_sha256": pr_dc_hash,
            "pr_dc_reconstructed_bytes": len(dc_blob.encode("utf-8")),
            "pr_dc_reconstructed_sha256": _sha(dc_blob),
            "pr_dc_matches_recorded_hash": _sha(dc_blob) == pr_dc_hash,
            "pr_dd_reconstructed_bytes": len(dd_blob.encode("utf-8")),
            "pr_dd_reconstructed_sha256": _sha(dd_blob),
            "byte_counts_equal": len(dc_blob.encode("utf-8")) == len(dd_blob.encode("utf-8")),
            "hashes_equal": _sha(dc_blob) == _sha(dd_blob),
            "pr_dc_turn_counter_after_replay": dc_counter,
            "pr_dd_turn_counter_after_replay": dd_counter,
            "pr_dc_stamp": "pr-db",
            "pr_dd_stamp": "pr-dd",
            "diff_count": len(diffs),
            "diff_buckets": grouped,
            "diffs_sample": classified,
            "cause": _stability_cause(grouped),
            "stamp_in_provider_payload": any("pr-db" in json.dumps(row) or "pr-dd" in json.dumps(row) for row in classified),
        })
    return {"cases": cases}


def _write_csv(path: Path, rows: list[dict]) -> None:
    fields = [
        "fixture_id", "interaction_class", "player_input", "resolver", "response_envelope",
        "projection_selected", "projection_mode", "serialized_bytes", "character_count",
        "estimated_input_tokens", "exact_input_tokens", "tokenizer", "payload_sha256",
        "system_prompt_bytes", "response_policy_bytes", "instruction_bytes",
        "conversation_history_bytes", "authorized_speaker", "authority_outcome",
        "fixture_source", "designation", "limitation", "message_count", "exact_duplicate_bytes",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            flat = {key: row.get(key) for key in fields}
            flat["authority_outcome"] = json.dumps(row.get("authority_outcome"), ensure_ascii=False, sort_keys=True)
            writer.writerow(flat)


def _stability_cause(grouped: dict) -> str:
    unexplained = grouped.get("D_unresolved", 0)
    explained = (
        "PR-DC replays S2/S3 without incrementing turn_counter, so the contract id is "
        "sha1(turn_index|player text) at the session's initial counter. PR-DD increments "
        "turn_counter after each prior turn, which changes turn_index and therefore the "
        "contract id. Those identifiers have equal length, so the byte count matches and "
        "the hash does not. The builder stamps pr-db and pr-dd are not present in the "
        "serialized provider payload."
    )
    if unexplained:
        return explained + f" {unexplained} differing path(s) remain unresolved."
    return explained


def _documented_dynamic(path: str, left, right) -> bool:
    blob = f"{path} {left} {right}"
    return "clue_text_digest:" in blob


def _compare(baseline: dict, revised_rows: list[dict], revised_payloads: dict) -> dict:
    base_payload_dir = OUT_ROOT / "baseline" / "payloads"
    comparisons = []
    for revised in revised_rows:
        fixture_id = revised["fixture_id"]
        before = next(row for row in baseline["fixtures"] if row["fixture_id"] == fixture_id)
        before_payload = json.loads((base_payload_dir / f"{fixture_id}.json").read_text(encoding="utf-8"))
        after_payload = revised_payloads[fixture_id]
        restored = dict(after_payload)
        policy = restored.get("response_policy") if isinstance(restored.get("response_policy"), dict) else {}
        restored_fields = []
        for top_key, policy_key in MIRRORS:
            if top_key in before_payload and top_key not in restored and policy_key in policy:
                restored[top_key] = policy[policy_key]
                restored_fields.append(top_key)
        unexplained = [
            row for row in _diff_paths(before_payload, restored)
            if not _documented_dynamic(row["path"], row.get("left"), row.get("right"))
        ]
        dynamic = [
            row for row in _diff_paths(before_payload, restored)
            if _documented_dynamic(row["path"], row.get("left"), row.get("right"))
        ]
        canonical_equal = not unexplained
        reduction = before["serialized_bytes"] - revised["serialized_bytes"]
        comparisons.append({
            "fixture_id": fixture_id,
            "baseline_bytes": before["serialized_bytes"],
            "revised_bytes": revised["serialized_bytes"],
            "absolute_reduction": reduction,
            "percentage_reduction": round(100 * reduction / before["serialized_bytes"], 3) if before["serialized_bytes"] else 0,
            "estimated_token_reduction": before["estimated_input_tokens"] - revised["estimated_input_tokens"],
            "baseline_sha256": before["payload_sha256"],
            "revised_sha256": revised["payload_sha256"],
            "removed_duplicate_fields": [
                row["top_level_field"]
                for row in before["duplicate_verification"]
                if row["exact_json_equal"] and row["top_level_field"] != "interaction_continuity"
            ],
            "retained_policy_fields": revised["response_policy_children"],
            "projection_selected": revised["projection_selected"],
            "response_envelope": revised["response_envelope"],
            "restored_fields": restored_fields,
            "normalized_payloads_equivalent": canonical_equal,
            "documented_dynamic_differences": dynamic,
            "unexplained_diff_count": len(unexplained),
            "unexplained_diffs": unexplained[:40],
        })
    return {"comparisons": comparisons}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("baseline", "post"), required=True)
    args = parser.parse_args()
    before = _mtimes()
    rows, payloads = _build_required()
    stability = _hash_stability() if args.phase == "baseline" else None
    after = _mtimes()
    phase_dir = OUT_ROOT / ("baseline" if args.phase == "baseline" else "post_change")
    payload_dir = phase_dir / "payloads"
    payload_dir.mkdir(parents=True, exist_ok=True)
    PR_DE.mkdir(parents=True, exist_ok=True)
    for fixture_id, payload in payloads.items():
        (payload_dir / f"{fixture_id}.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8",
        )
    document = {
        "cycle": "PR-DE",
        "phase": args.phase,
        "live_provider_calls": 0,
        "serialization_boundary": "build_messages output; ensure_ascii=False; sha256 of system\\nuser",
        "estimate": "ceil(chars/4)",
        "python_hash_seed": __import__("os").environ.get("PYTHONHASHSEED"),
        "production_mtime_unchanged": before == after,
        "mtimes_before": before,
        "mtimes_after": after,
        "fixtures": rows,
        "hash_stability": stability,
    }
    if args.phase == "post":
        baseline = json.loads((OUT_ROOT / "baseline" / "pr_de.json").read_text(encoding="utf-8"))
        document["comparison"] = _compare(baseline, rows, payloads)
    (phase_dir / "pr_de.json").write_text(json.dumps(document, indent=2), encoding="utf-8")
    _write_csv(phase_dir / "pr_de.csv", rows)
    if args.phase == "post":
        _write_combined_csv(document)
    print(json.dumps({
        "phase": args.phase,
        "production_mtime_unchanged": before == after,
        "fixtures": [
            {
                "id": row["fixture_id"],
                "bytes": row["serialized_bytes"],
                "tokens": row["estimated_input_tokens"],
                "sha256": row["payload_sha256"],
                "envelope": row["response_envelope"],
                "projection": row["projection_selected"],
                "duplicate_bytes": row["exact_duplicate_bytes"],
                "speaker": row["authorized_speaker"],
            }
            for row in rows
        ],
    }, indent=2))


def _write_combined_csv(post_document: dict) -> None:
    baseline = json.loads((OUT_ROOT / "baseline" / "pr_de.json").read_text(encoding="utf-8"))
    by_id = {row["fixture_id"]: row for row in post_document["fixtures"]}
    path = PR_DE / "PR-DE_prompt_measurements.csv"
    fields = [
        "fixture_id", "interaction_class", "player_input", "resolver", "response_envelope",
        "projection_selected", "baseline_bytes", "revised_bytes", "absolute_reduction",
        "percentage_reduction", "baseline_estimated_tokens", "revised_estimated_tokens",
        "estimated_token_reduction", "exact_tokens", "baseline_sha256", "revised_sha256",
        "system_prompt_bytes", "response_policy_bytes", "instruction_bytes",
        "conversation_history_bytes", "authorized_speaker", "authority_outcome",
        "fixture_source", "designation", "removed_duplicate_fields", "normalized_equivalent",
    ]
    comparisons = {row["fixture_id"]: row for row in post_document["comparison"]["comparisons"]}
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for before in baseline["fixtures"]:
            revised = by_id[before["fixture_id"]]
            comparison = comparisons[before["fixture_id"]]
            writer.writerow({
                "fixture_id": before["fixture_id"],
                "interaction_class": before["interaction_class"],
                "player_input": before["player_input"],
                "resolver": revised.get("resolver"),
                "response_envelope": revised.get("response_envelope"),
                "projection_selected": revised.get("projection_selected"),
                "baseline_bytes": before["serialized_bytes"],
                "revised_bytes": revised["serialized_bytes"],
                "absolute_reduction": comparison["absolute_reduction"],
                "percentage_reduction": comparison["percentage_reduction"],
                "baseline_estimated_tokens": before["estimated_input_tokens"],
                "revised_estimated_tokens": revised["estimated_input_tokens"],
                "estimated_token_reduction": comparison["estimated_token_reduction"],
                "exact_tokens": revised.get("exact_input_tokens"),
                "baseline_sha256": before["payload_sha256"],
                "revised_sha256": revised["payload_sha256"],
                "system_prompt_bytes": revised["system_prompt_bytes"],
                "response_policy_bytes": revised["response_policy_bytes"],
                "instruction_bytes": revised["instruction_bytes"],
                "conversation_history_bytes": revised["conversation_history_bytes"],
                "authorized_speaker": revised["authorized_speaker"],
                "authority_outcome": json.dumps(revised["authority_outcome"], ensure_ascii=False, sort_keys=True),
                "fixture_source": revised["fixture_source"],
                "designation": revised["designation"],
                "removed_duplicate_fields": ";".join(comparison["removed_duplicate_fields"]),
                "normalized_equivalent": comparison["normalized_payloads_equivalent"],
            })


if __name__ == "__main__":
    _DD = _load_pr_dd()
    main()
