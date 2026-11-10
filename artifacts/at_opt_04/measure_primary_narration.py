"""AT-OPT-04 provider-free primary narration measurement.

Rebuilds the PR-PLAY-79D-F3 step-back request through build_messages.
Does not call a provider. Writes only under artifacts/at_opt_04/.
State is copied to a temporary directory.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import inspect
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
F3 = ROOT / "artifacts" / "pr_play_79df3" / "http_data"
SNAPSHOT = F3 / "snapshots" / "2026-11-08T16-50-45_8caf7aff.json"
PLAYER_TEXT = "I step back from the notice board."

os.environ["ASHEN_TEST_EVIDENCE_DIR"] = str(OUT)
os.environ["ASHEN_DISABLE_PROVIDER_CALLS"] = "1"
os.environ["ASHEN_DISABLE_LIVE_INTERPRETATION"] = "1"
os.environ["ASHEN_DISABLE_EXPRESSION_GENERATION"] = "1"
os.environ["ASHEN_DISABLE_PROVIDER_RETRIES"] = "1"
os.environ["ASHEN_THRONES_SKIP_UPSTREAM_API_PREFLIGHT"] = "1"
os.environ.pop("ASHEN_EXPERIMENTAL_PHYSICAL_ADJUDICATION", None)
os.environ.pop("OPENAI_API_KEY", None)

sys.path.insert(0, str(ROOT))


def _dumps(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _sha(value) -> str:
    return hashlib.sha256(_dumps(value).encode("utf-8")).hexdigest()


def _json_equal(left, right) -> bool:
    try:
        return _dumps(left) == _dumps(right)
    except (TypeError, ValueError):
        return False


def _file_sha(path: Path) -> str | None:
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def prepare_state() -> Path:
    temp = Path(tempfile.mkdtemp(prefix="at-opt-04-"))
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


def section_hashes(payload: dict) -> dict:
    hashes = {}
    for key, value in payload.items():
        if key == "turn_packet" and isinstance(value, dict):
            packet = dict(value)
            nested = packet.pop("response_policy", None)
            hashes["turn_packet_without_response_policy"] = _sha(packet)
            hashes["turn_packet_keys"] = list(value.keys())
            if isinstance(nested, dict):
                hashes["nested_policy_key_sha256"] = {name: _sha(item) for name, item in nested.items()}
            else:
                hashes["nested_policy_key_sha256"] = None
            continue
        hashes[key] = _sha(value)
    return hashes


def state_hashes(root: Path, scene_id: str | None) -> dict:
    names = [
        "session.json",
        "world.json",
        "character.json",
        "combat.json",
        "campaign.json",
        "conditions.json",
        "session_log.jsonl",
        "provider_usage.jsonl",
    ]
    found = {name: _file_sha(root / name) for name in names}
    if scene_id:
        found[f"scenes/{scene_id}.json"] = _file_sha(root / "scenes" / f"{scene_id}.json")
    return found


def measure(assert_optimized: bool) -> dict:
    state = prepare_state()
    from tests.helpers.storage_isolation import install

    install(state)
    import openai
    from game import storage
    from game.gm import build_messages
    import game.gm as gm

    constructed = {"count": 0}

    class _BlockedClient:
        def __init__(self, *args, **kwargs):
            constructed["count"] += 1
            raise RuntimeError("AT-OPT-04 blocked a live provider client")

    openai.OpenAI = _BlockedClient
    gpt_calls = {"count": 0}

    def _refuse_gpt(*_args, **_kwargs):
        gpt_calls["count"] += 1
        raise RuntimeError("AT-OPT-04 refused call_gpt")

    gm.call_gpt = _refuse_gpt

    campaign = storage._load_json(storage.CAMPAIGN_PATH, {})
    world = storage._load_json(storage.WORLD_PATH, {})
    session = storage.load_session()
    character = storage._load_json(storage.CHARACTER_PATH, {})
    combat = storage._load_json(storage.COMBAT_PATH, {})
    recent_log = storage.load_log()
    scene_id = session.get("active_scene_id")
    scene = storage.get_effective_scene(session, scene_id)
    before_disk = state_hashes(state, scene_id)
    inputs = {
        "campaign": copy.deepcopy(campaign),
        "world": copy.deepcopy(world),
        "session": copy.deepcopy(session),
        "character": copy.deepcopy(character),
        "scene": copy.deepcopy(scene),
        "combat": copy.deepcopy(combat),
        "recent_log": copy.deepcopy(recent_log),
    }
    captured: dict = {}
    real_omit = gm.omit_duplicate_turn_packet_policy

    def _capture(payload):
        captured["input"] = copy.deepcopy(payload)
        captured["policy_id"] = id(payload.get("response_policy")) if isinstance(payload, dict) else None
        captured["packet_id"] = id(payload.get("turn_packet")) if isinstance(payload, dict) else None
        result = real_omit(payload)
        captured["output"] = copy.deepcopy(result)
        captured["input_after"] = copy.deepcopy(payload)
        captured["result_policy_id"] = id(result.get("response_policy")) if isinstance(result, dict) else None
        return result

    gm.omit_duplicate_turn_packet_policy = _capture
    messages = build_messages(
        inputs["campaign"],
        inputs["world"],
        inputs["session"],
        inputs["character"],
        inputs["scene"],
        inputs["combat"],
        inputs["recent_log"],
        PLAYER_TEXT,
        resolution=None,
        scene_runtime=None,
        prompt_profile="manual_play_auto",
    )
    after_disk = state_hashes(state, scene_id)
    user = json.loads(messages[1]["content"])
    blob = json.dumps(messages, ensure_ascii=False).encode("utf-8")
    pre = captured.get("input") if isinstance(captured.get("input"), dict) else {}
    pre_policy = pre.get("response_policy") if isinstance(pre.get("response_policy"), dict) else {}
    pre_packet = pre.get("turn_packet") if isinstance(pre.get("turn_packet"), dict) else {}
    pre_nested = pre_packet.get("response_policy") if isinstance(pre_packet.get("response_policy"), dict) else {}
    final_policy = user.get("response_policy") if isinstance(user.get("response_policy"), dict) else {}
    final_packet = user.get("turn_packet") if isinstance(user.get("turn_packet"), dict) else {}
    final_nested = final_packet.get("response_policy") if isinstance(final_packet.get("response_policy"), dict) else {}
    equal_keys = []
    preserved = []
    reasons = {}
    details = {}
    for key, value in pre_nested.items():
        if key in pre_policy and _json_equal(value, pre_policy.get(key)):
            equal_keys.append(key)
            reasons[key] = "json_equal_to_root"
        elif key not in pre_policy:
            preserved.append(key)
            reasons[key] = "absent_from_root"
        else:
            preserved.append(key)
            reasons[key] = "value_differs"
            root_value = pre_policy.get(key)
            nested_keys = set(value) if isinstance(value, dict) else set()
            root_keys = set(root_value) if isinstance(root_value, dict) else set()
            details[key] = {
                "nested_type": type(value).__name__,
                "root_type": type(root_value).__name__,
                "keys_only_in_nested": sorted(nested_keys - root_keys),
                "keys_only_in_root": sorted(root_keys - nested_keys),
                "pre_omit_sha256": _sha(value),
            }
    helper_input = captured.get("input")
    helper_output = captured.get("output")
    idempotent = False
    if isinstance(helper_input, dict) and isinstance(helper_output, dict):
        once = real_omit(copy.deepcopy(helper_input))
        twice = real_omit(once)
        idempotent = _dumps(helper_output) == _dumps(once) == _dumps(twice)
    obligations = user.get("narration_obligations") if isinstance(user.get("narration_obligations"), dict) else {}
    report = {
        "cycle": "AT-OPT-04",
        "classification": "RECONSTRUCTED",
        "player_text": PLAYER_TEXT,
        "resolution": None,
        "prompt_profile": "manual_play_auto",
        "snapshot": "artifacts/pr_play_79df3/http_data/snapshots/2026-11-08T16-50-45_8caf7aff.json",
        "scene_files_source": "F3 http_data scenes; the snapshot does not contain scene files",
        "historical_request_gap": (
            "The captured F3 provider payload was not stored. Current chat() does not build "
            "this prompt for the step-back. This run calls build_messages directly, matching AT-OPT-03."
        ),
        "session_turn": session.get("turn_counter"),
        "scene_id": scene_id,
        "provider_calls": 0,
        "provider_client_constructed": constructed["count"] > 0,
        "provider_client_constructions": constructed["count"],
        "call_gpt_entries": gpt_calls["count"],
        "build_messages_calls": 1,
        "message_count": len(messages),
        "user_json_parses": isinstance(user, dict),
        "system_bytes": len(messages[0]["content"].encode("utf-8")),
        "user_bytes": len(messages[1]["content"].encode("utf-8")),
        "blob_bytes": len(blob),
        "admission_estimate_tokens": max(1, (len(blob) // 3) + 64),
        "estimate_method": "(utf-8 byte length of json.dumps(messages, ensure_ascii=False) // 3) + 64; not a provider tokenizer count",
        "instruction_count": len(user.get("instructions")) if isinstance(user.get("instructions"), list) else None,
        "must_advance_scene": obligations.get("must_advance_scene"),
        "is_opening_scene": obligations.get("is_opening_scene"),
        "disk_unchanged": before_disk == after_disk,
        "disk_hashes": before_disk,
        "passed_object_mutated": {
            name: inputs[name] != original
            for name, original in {
                "campaign": campaign,
                "world": world,
                "session": session,
                "character": character,
                "scene": scene,
                "combat": combat,
                "recent_log": recent_log,
            }.items()
        },
        "helper_input_mutated": captured.get("input") != captured.get("input_after"),
        "root_policy_object_preserved_by_helper": (
            isinstance(captured.get("output"), dict)
            and captured.get("result_policy_id") == captured.get("policy_id")
        ),
        "helper_idempotent_on_pre_omit_input": idempotent,
        "omit_function_sha256": hashlib.sha256(inspect.getsource(real_omit).encode("utf-8")).hexdigest(),
        "pre_omit_root_policy_keys": list(pre_policy.keys()),
        "pre_omit_nested_keys": list(pre_nested.keys()),
        "equal_nested_keys": equal_keys,
        "preserved_nested_keys": preserved,
        "preservation_reasons": reasons,
        "differing_value_details": details,
        "final_root_policy_keys": list(final_policy.keys()),
        "final_nested_policy_present": isinstance(final_packet.get("response_policy"), dict),
        "final_nested_keys": list(final_nested.keys()),
        "equal_keys_still_in_final_nested": [key for key in equal_keys if key in final_nested],
        "preserved_keys_missing_from_final_nested": [key for key in preserved if key not in final_nested],
        "root_missing_equal_keys": [key for key in equal_keys if key not in final_policy],
        "final_root_policy_sha256": _sha(final_policy),
        "final_preserved_value_sha256": {key: _sha(final_nested.get(key)) for key in preserved if key in final_nested},
        "section_sha256": section_hashes(user),
        "top_level_keys": list(user.keys()),
    }
    problems = []
    if report["provider_client_constructed"] or report["call_gpt_entries"]:
        problems.append("provider_dispatch")
    if not report["disk_unchanged"]:
        problems.append("gameplay_files_changed")
    if report["helper_input_mutated"]:
        problems.append("helper_mutated_input")
    if not report["user_json_parses"] or report["message_count"] != 2:
        problems.append("malformed_request")
    if not report["root_policy_object_preserved_by_helper"]:
        problems.append("root_policy_object_replaced")
    if assert_optimized:
        if not equal_keys:
            problems.append("no_equal_keys_observed")
        if not preserved:
            problems.append("no_preserved_keys_observed")
        if report["equal_keys_still_in_final_nested"]:
            problems.append("equal_keys_retained")
        if report["preserved_keys_missing_from_final_nested"]:
            problems.append("preserved_keys_dropped")
        if report["root_missing_equal_keys"]:
            problems.append("root_lost_equal_keys")
        if not report["helper_idempotent_on_pre_omit_input"]:
            problems.append("helper_not_idempotent")
        if set(report["final_nested_keys"]) != set(preserved):
            problems.append("final_nested_key_set_mismatch")
    report["problems"] = problems
    report["assert_optimized"] = assert_optimized
    shutil.rmtree(state.parent, ignore_errors=True)
    return report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--assert-optimized", action="store_true")
    args = parser.parse_args()
    report = measure(args.assert_optimized)
    destination = args.out
    if not destination.is_absolute():
        destination = ROOT / destination
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({
        "out": str(destination.relative_to(ROOT)).replace("\\", "/"),
        "blob_bytes": report["blob_bytes"],
        "admission_estimate_tokens": report["admission_estimate_tokens"],
        "equal_nested_keys": len(report["equal_nested_keys"]),
        "preserved_nested_keys": report["preserved_nested_keys"],
        "equal_keys_still_in_final_nested": report["equal_keys_still_in_final_nested"],
        "problems": report["problems"],
        "provider_client_constructions": report["provider_client_constructions"],
        "call_gpt_entries": report["call_gpt_entries"],
    }, indent=2))
    return 2 if report["problems"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
