#!/usr/bin/env python3
"""PR-BT deterministic provider payload measurement.

Reconstructs the three PR-BS probes without model/API calls by loading the
saved isolated probe state/resolution and calling ``game.gm.build_messages``.
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

OUT = ROOT / "artifacts" / "pr_bt_policy_instruction_deduplication"
BASELINE = ROOT / "artifacts" / "pr_bs_cooperative_gm_micro_live" / "evidence"

PROBES = (
    (
        "P1",
        "chapel",
        "I examine the split wooden yoke and the torn leather hanger closely. What does this damage suggest?",
    ),
    ("P2", "baker", "Baker, which loaf do you usually keep for yourself?"),
    (
        "P3",
        "chapel",
        "Looking at the split wooden yoke and the torn leather hanger, maybe someone cut it deliberately. Does that fit what I'm seeing?",
    ),
)

BEFORE = {
    "P1": {"total": 110450, "instructions": 25788, "response_policy": 20630, "system_prompt": 12975, "turn_packet": 10676},
    "P2": {"total": 121438, "instructions": 26675, "response_policy": 21237, "system_prompt": 12975, "turn_packet": 10640},
    "P3": {"total": 110665, "instructions": 25856, "response_policy": 20913, "system_prompt": 12975, "turn_packet": 10910},
}


def _chars(value: Any) -> int:
    return len(json.dumps(value, ensure_ascii=False, default=str))


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _system_and_payload(messages: list[dict[str, str]]) -> tuple[str, dict[str, Any]]:
    system = ""
    payload: dict[str, Any] = {}
    for msg in messages:
        if msg.get("role") == "system":
            system = str(msg.get("content") or "")
        elif msg.get("role") == "user":
            parsed = json.loads(str(msg.get("content") or "{}"))
            if isinstance(parsed, dict):
                payload = parsed
    return system, payload


def _component_counts(messages: list[dict[str, str]]) -> dict[str, int]:
    system, payload = _system_and_payload(messages)
    instructions = payload.get("instructions") if isinstance(payload.get("instructions"), list) else []
    policy = payload.get("response_policy") if isinstance(payload.get("response_policy"), dict) else {}
    turn_packet = payload.get("turn_packet") if isinstance(payload.get("turn_packet"), dict) else {}
    recipe = payload.get("decision_facing_answer_recipe") if isinstance(payload.get("decision_facing_answer_recipe"), dict) else {}
    schema_terms = {
        "system_realization_envelope": system[system.find("Return valid JSON only") :] if "Return valid JSON only" in system else "",
        "schema_instruction_keys": [
            "declared_claims",
            "narration",
            "player_facing_text",
            "tags",
            "improvisation_proposals",
            "scene_update",
            "activate_scene_id",
            "new_scene_draft",
            "world_updates",
            "suggested_action",
        ],
    }
    return {
        "total_provider_chars": _chars(messages),
        "system_prompt_chars": len(system),
        "user_json_chars": _chars(payload),
        "instructions_chars": _chars(instructions),
        "instructions_count": len(instructions),
        "response_policy_chars": _chars(policy),
        "turn_packet_chars": _chars(turn_packet),
        "decision_facing_answer_recipe_chars": _chars(recipe),
        "schema_output_contract_chars_separable": _chars(schema_terms),
        "context_separation_contract_chars": _chars(payload.get("context_separation_contract")),
        "fallback_behavior_chars": _chars(payload.get("fallback_behavior")),
    }


def _rule_presence(payload: dict[str, Any], system: str) -> dict[str, bool]:
    text = "\n".join(str(x) for x in payload.get("instructions") or []) + "\n" + system
    policy = payload.get("response_policy") if isinstance(payload.get("response_policy"), dict) else {}
    recipe = payload.get("decision_facing_answer_recipe") if isinstance(payload.get("decision_facing_answer_recipe"), dict) else {}
    return {
        "authority_generated_prose_not_authoritative": "Declarations do not authorize themselves" in system,
        "authority_decision_claims_constrain_realization": bool(recipe) and "gm_resolution_decision" in text,
        "recipe_cannot_grant_authority": "recipe is guidance only" in text.lower() or "does not add authority" in text.lower(),
        "inference_uncertainty_visible": "uncertainty" in text.lower() and isinstance(policy.get("narrative_authority"), dict),
        "player_hypothesis_preserved": "hypoth" in text.lower(),
        "npc_incidental_bounded": "bounded incidental" in text.lower() and "npc_claim" in system,
        "declaration_lane_visible": "declared_claims" in system and "declaration_mode" in system,
        "ordinary_narration_need_not_be_declared": "Mundane sensory texture" in system,
        "fallback_unknown_visible": isinstance(policy.get("fallback_behavior"), dict) and "partial answer" in text.lower(),
        "invalid_output_no_prose_escape": "Return valid JSON only" in system,
        "structured_envelope_explicit": all(k in system for k in ("narration", "player_facing_text", "declared_claims")),
        "raw_internal_json_no_player_leak": "structured metadata must never be spoken to the player" in system,
    }


def _point_storage(probe_id: str, evidence_root: Path | None = None) -> None:
    from game import storage

    source = BASELINE / probe_id / "isolated" / "data"
    target = (evidence_root or OUT) / "evidence" / probe_id / "isolated" / "data"
    if target.exists():
        shutil.rmtree(target)
    shutil.copytree(source, target)
    storage.BASE_DIR = target.parent
    storage.DATA_DIR = target
    storage.SCENES_DIR = target / "scenes"
    for attr, filename in {
        "WORLD_PATH": "world.json",
        "SESSION_PATH": "session.json",
        "CAMPAIGN_PATH": "campaign.json",
        "CHARACTER_PATH": "character.json",
        "COMBAT_PATH": "combat.json",
        "CONDITIONS_PATH": "conditions.json",
        "SESSION_LOG_PATH": "session_log.jsonl",
    }.items():
        setattr(storage, attr, target / filename)


def _fake_gm() -> dict[str, Any]:
    return {
        "declared_claims": [],
        "narration": "Measured deterministic placeholder.",
        "player_facing_text": "Measured deterministic placeholder.",
        "tags": [],
        "improvisation_proposals": None,
        "scene_update": None,
        "activate_scene_id": None,
        "new_scene_draft": None,
        "world_updates": None,
        "suggested_action": None,
        "debug_notes": "pr_bt_measurement_no_model_call",
    }


def reconstruct_probe(probe_id: str, player: str, *, out_dir: Path | None = None) -> dict[str, Any]:
    from game import storage
    from game.gm import build_messages

    evidence_root = out_dir or OUT
    _point_storage(probe_id, evidence_root)
    api_response = _load_json(BASELINE / probe_id / "api_response.json")
    resolution = api_response.get("resolution") if isinstance(api_response, dict) else None
    if not isinstance(resolution, dict):
        raise RuntimeError(f"{probe_id}: saved PR-BS resolution missing")
    session = storage.load_session()
    world = storage.load_world()
    scene = storage.load_scene(session["active_scene_id"])
    messages = build_messages(
        storage.load_campaign(),
        world,
        session,
        storage.load_character(),
        scene,
        storage.load_combat(),
        [],
        player,
        resolution=resolution,
        scene_runtime={},
    )
    system, payload = _system_and_payload(messages)
    counts = _component_counts(messages)
    evidence_dir = evidence_root / "evidence" / probe_id
    evidence_dir.mkdir(parents=True, exist_ok=True)
    (evidence_dir / "provider_request_generation_1.json").write_text(
        json.dumps({"provider_input": messages, "measurements": counts}, indent=2, ensure_ascii=False, default=str),
        encoding="utf-8",
    )
    (evidence_dir / "rule_presence.json").write_text(
        json.dumps(_rule_presence(payload, system), indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    return {"probe": probe_id, "player": player, "measurements": counts, "rule_presence": _rule_presence(payload, system)}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = [reconstruct_probe(probe_id, player) for probe_id, _scene, player in PROBES]
    summary: dict[str, Any] = {"method": __doc__, "before": BEFORE, "after": {}, "savings": {}, "rule_presence": {}}
    for row in rows:
        probe = row["probe"]
        after = row["measurements"]
        before = BEFORE[probe]
        summary["after"][probe] = after
        summary["rule_presence"][probe] = row["rule_presence"]
        summary["savings"][probe] = {
            "total_chars_removed": before["total"] - after["total_provider_chars"],
            "total_percent_removed": round((before["total"] - after["total_provider_chars"]) / before["total"] * 100, 2),
            "instructions_chars_removed": before["instructions"] - after["instructions_chars"],
            "system_prompt_chars_removed": before["system_prompt"] - after["system_prompt_chars"],
            "response_policy_chars_delta": after["response_policy_chars"] - before["response_policy"],
            "turn_packet_chars_delta": after["turn_packet_chars"] - before["turn_packet"],
        }
    removed = [v["total_chars_removed"] for v in summary["savings"].values()]
    summary["fixed_reduction_common_to_all_three"] = min(removed)
    (OUT / "p1_p2_p3_measurements.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
