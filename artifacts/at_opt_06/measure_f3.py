"""AT-OPT-06 provider-free F3 transition and instruction measurement.

Rebuilds the notice-board snapshot through production transition derivation
and build_messages. Does not call a provider. Writes only under
artifacts/at_opt_06/. Campaign state is copied to a temp directory.
Historical fixtures are not modified.
"""

from __future__ import annotations

import argparse
import copy
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
PLAYER = "I step back from the notice board."

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

AUTHORITY_MARKERS = (
    "You MUST NOT reveal hidden or undiscovered facts.",
    "FIRST-MENTION CONTRACT (MANDATORY):",
    "SPEAKER SELECTION CONTRACT (HARD RULE):",
    "SCENE STATE ANCHOR (MANDATORY):",
    "do not treat policy prose or the answer recipe as authority to create facts.",
)


def _bytes(obj) -> int:
    return len(json.dumps(obj, ensure_ascii=False).encode("utf-8"))


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def prepare_state() -> Path:
    temp = Path(tempfile.mkdtemp(prefix="at-opt-06-"))
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


def node_summary(node: dict | None) -> dict:
    if not isinstance(node, dict):
        return {"present": False}
    before = node.get("before_anchor") if isinstance(node.get("before_anchor"), dict) else {}
    after = node.get("after_anchor") if isinstance(node.get("after_anchor"), dict) else {}
    return {
        "present": True,
        "transition_required": node.get("transition_required"),
        "transition_type": node.get("transition_type"),
        "before_scene_id": before.get("scene_id"),
        "after_scene_id": after.get("scene_id"),
        "source_fields": list(node.get("source_fields") or []),
        "derivation_codes": list(node.get("derivation_codes") or []),
    }


def message_report(messages: list) -> dict:
    user = json.loads(messages[1]["content"])
    blob = json.dumps(messages, ensure_ascii=False).encode("utf-8")
    instructions = list(user.get("instructions") or [])
    obligations = user.get("narration_obligations") if isinstance(user.get("narration_obligations"), dict) else {}
    transition = user.get("transition") if isinstance(user.get("transition"), dict) else None
    plan = user.get("narrative_plan") if isinstance(user.get("narrative_plan"), dict) else {}
    joined = "\n".join(instructions)
    return {
        "blob_bytes": len(blob),
        "admission_estimate_tokens": max(1, (len(blob) // 3) + 64),
        "instruction_count": len(instructions),
        "instruction_bytes": _bytes(instructions),
        "instructions": instructions,
        "must_advance_scene": obligations.get("must_advance_scene"),
        "transition": node_summary(transition),
        "narrative_mode": plan.get("narrative_mode"),
        "scene_advancement": user.get("scene_advancement"),
        "first_mention_contract_present": "first_mention_contract" in user,
        "authority_markers": {marker: marker in joined for marker in AUTHORITY_MARKERS},
        "top_level_keys": sorted(user.keys()),
    }


def install_rederived(session: dict, plan: dict) -> dict:
    fresh = copy.deepcopy(session)
    bundle = fresh.get("_runtime_narration_plan_bundle_v1")
    if not isinstance(bundle, dict):
        raise RuntimeError("snapshot session has no narration plan bundle")
    replaced = copy.deepcopy(bundle)
    replaced["narrative_plan"] = copy.deepcopy(plan)
    fresh["_runtime_narration_plan_bundle_v1"] = replaced
    return fresh


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", choices=("before", "after"), required=True)
    args = parser.parse_args()

    from tests.helpers.storage_isolation import install

    state = prepare_state()
    install(state)
    import openai
    from game.ctir_runtime import detach_ctir
    from game.gm import build_messages, call_gpt
    from game.narrative_planning import _derive_transition_node, build_narrative_plan
    from game.narrative_plan_upstream import apply_upstream_narrative_role_reemphasis
    from game import storage
    import game.gm as gm_mod

    class _BlockedClient:
        def __init__(self, *args, **kwargs):
            PROVIDER_CALLS["openai_constructed"] += 1
            raise RuntimeError("AT-OPT-06 blocked a live provider client")

    openai.OpenAI = _BlockedClient

    def _blocked_call(*args, **kwargs):
        PROVIDER_CALLS["call_gpt"] += 1
        raise RuntimeError("AT-OPT-06 blocked call_gpt")

    gm_mod.call_gpt = _blocked_call

    campaign = storage._load_json(storage.CAMPAIGN_PATH, {})
    world = storage._load_json(storage.WORLD_PATH, {})
    session = storage.load_session()
    character = storage._load_json(storage.CHARACTER_PATH, {})
    combat = storage._load_json(storage.COMBAT_PATH, {})
    recent_log = storage.load_log()
    scene = storage.get_effective_scene(session, session["active_scene_id"])
    attached = session.get("_runtime_canonical_ctir_v1")
    if not isinstance(attached, dict):
        raise RuntimeError("snapshot has no attached CTIR")
    scene_before = session.get("active_scene_id")
    ctir_before = copy.deepcopy(attached)
    public_slice = {"scene_id": attached.get("scene_id"), "location_tokens": ["frontier_gate"]}
    direct_node, _codes = _derive_transition_node(attached, public_scene_slice=public_slice)
    plan = build_narrative_plan(ctir=attached, public_scene_slice=public_slice)
    # Production bundle construction applies this shaping pass after the plan is built.
    plan, _reemphasis = apply_upstream_narrative_role_reemphasis(plan)
    plan_node = plan.get("transition_node") if isinstance(plan, dict) else None
    ctir_mutated = attached != ctir_before

    def build(sess, text, profile):
        return build_messages(
            campaign,
            world,
            copy.deepcopy(sess),
            character,
            scene,
            combat,
            recent_log,
            text,
            resolution=None,
            scene_runtime=None,
            prompt_profile=profile,
        )

    stored_auto = message_report(build(session, PLAYER, "manual_play_auto"))
    rederived_session = install_rederived(session, plan)
    rederived_auto = message_report(build(rederived_session, PLAYER, "manual_play_auto"))
    rederived_compact = message_report(build(rederived_session, PLAYER, "manual_play_compact"))
    detached = copy.deepcopy(session)
    detach_ctir(detached)
    detached_auto = message_report(build(detached, PLAYER, "manual_play_auto"))
    scene_after = session.get("active_scene_id")

    resolution = attached.get("resolution") if isinstance(attached.get("resolution"), dict) else {}
    mutations = attached.get("state_mutations") if isinstance(attached.get("state_mutations"), dict) else {}
    result = {
        "phase": args.phase,
        "provider_calls": 0,
        "provider_client_constructed": PROVIDER_CALLS["openai_constructed"],
        "call_gpt_entries": PROVIDER_CALLS["call_gpt"],
        "recorded_provider_input_tokens": RECORDED_INPUT,
        "historical_snapshot_modified": False,
        "attached_player_input": attached.get("player_input"),
        "attached_scene_id": attached.get("scene_id"),
        "attached_resolved_transition": resolution.get("resolved_transition"),
        "attached_scene_mutation": mutations.get("scene"),
        "responsible_condition": "state_mutations.scene.scene_id is treated as a transition signal even when it equals ctir.scene_id",
        "ctir_mutated_by_derivation": ctir_mutated,
        "active_scene_id_before": scene_before,
        "active_scene_id_after": scene_after,
        "direct_transition_node": node_summary(direct_node),
        "plan_transition_node": node_summary(plan_node if isinstance(plan_node, dict) else None),
        "plan_narrative_mode": plan.get("narrative_mode") if isinstance(plan, dict) else None,
        "stored_bundle_auto": stored_auto,
        "rederived_plan_auto": rederived_auto,
        "rederived_plan_forced_compact": rederived_compact,
        "detached_auto": detached_auto,
        "call_gpt_symbol_is_blocked_wrapper": gm_mod.call_gpt is _blocked_call,
        "unused_import_guard": callable(call_gpt),
    }
    destination = OUT / f"f3_{args.phase}.json"
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "phase": args.phase,
        "provider_calls": 0,
        "openai_constructed": PROVIDER_CALLS["openai_constructed"],
        "call_gpt_entries": PROVIDER_CALLS["call_gpt"],
        "direct_required": result["direct_transition_node"].get("transition_required"),
        "direct_type": result["direct_transition_node"].get("transition_type"),
        "direct_before": result["direct_transition_node"].get("before_scene_id"),
        "direct_after": result["direct_transition_node"].get("after_scene_id"),
        "direct_sources": result["direct_transition_node"].get("source_fields"),
        "plan_mode": result["plan_narrative_mode"],
        "stored_instructions": stored_auto["instruction_count"],
        "stored_bytes": stored_auto["blob_bytes"],
        "stored_must_advance": stored_auto["must_advance_scene"],
        "rederived_instructions": rederived_auto["instruction_count"],
        "rederived_bytes": rederived_auto["blob_bytes"],
        "rederived_estimate": rederived_auto["admission_estimate_tokens"],
        "rederived_must_advance": rederived_auto["must_advance_scene"],
        "rederived_required": rederived_auto["transition"].get("transition_required"),
        "rederived_type": rederived_auto["transition"].get("transition_type"),
        "forced_compact_instructions": rederived_compact["instruction_count"],
        "detached_instructions": detached_auto["instruction_count"],
        "detached_bytes": detached_auto["blob_bytes"],
        "ctir_mutated": ctir_mutated,
        "scene_unchanged": scene_before == scene_after,
        "authority": rederived_auto["authority_markers"],
    }, indent=2))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise
