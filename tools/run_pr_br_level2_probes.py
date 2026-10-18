#!/usr/bin/env python3
"""PR-BR Level 2 focused live probes through the real /api/chat path.

Uses an isolated storage directory so the player's saved campaign is not reset.
Hard cap: 10 gameplay turns.
"""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient

from game import storage
from game.api import app
from game.defaults import default_campaign, default_character, default_combat, default_conditions
from game.playability_eval import evaluate_playability
from tests.helpers.golden_replay_fixtures import seed_frontier_gate_world
from tests.helpers.turn_pipeline_http_fixtures import _write_campaign_start_scene_files
from tools.run_playability_validation import _build_eval_payload, _gm_text_from_chat_payload

ROOT = Path(__file__).resolve().parents[1]
MAX_TURNS = 10

PROBES: tuple[tuple[str, str], ...] = (
    (
        "establish_inspected",
        "I step under the frayed banner and look at the cloth itself, not the crowd.",
    ),
    (
        "perception_smell_referent",
        "This close, what does it smell like?",
    ),
    (
        "perception_wear_referent",
        "Is the wear on it from the weather, or does it look recently handled?",
    ),
    (
        "establish_claim",
        "I catch the stew-seller's attention and ask what rumor he has been repeating tonight.",
    ),
    (
        "claim_source",
        "Where did you hear that?",
    ),
    (
        "claim_confidence",
        "How sure are you, honestly?",
    ),
    (
        "follow_lead",
        "All right. I follow that lead.",
    ),
)

REPAIR_PROBES: tuple[tuple[str, str], ...] = (
    (
        "establish_inspected",
        "I step under the frayed banner and look at the cloth itself, not the crowd.",
    ),
    (
        "perception_smell_referent",
        "This close, what does it smell like?",
    ),
    (
        "claim_source_in_utterance",
        "I ask the stew-seller where he heard the rumor he has been repeating.",
    ),
)


def _utc_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _isolate_storage(tmp: Path) -> None:
    storage.BASE_DIR = tmp
    storage.DATA_DIR = tmp / "data"
    storage.WORLD_PATH = storage.DATA_DIR / "world.json"
    storage.SCENES_DIR = storage.DATA_DIR / "scenes"
    storage.CHARACTER_PATH = storage.DATA_DIR / "character.json"
    storage.CAMPAIGN_PATH = storage.DATA_DIR / "campaign.json"
    storage.SESSION_PATH = storage.DATA_DIR / "session.json"
    storage.COMBAT_PATH = storage.DATA_DIR / "combat.json"
    storage.CONDITIONS_PATH = storage.DATA_DIR / "conditions.json"
    storage.SESSION_LOG_PATH = storage.DATA_DIR / "session_log.jsonl"
    storage.DATA_DIR.mkdir(parents=True, exist_ok=True)
    storage.SCENES_DIR.mkdir(parents=True, exist_ok=True)
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    if storage.SESSION_PATH.exists():
        storage.SESSION_PATH.unlink()
    storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")
    _write_campaign_start_scene_files()
    seed_frontier_gate_world()


def _compact(value: Any, limit: int = 500) -> Any:
    if isinstance(value, str):
        return value if len(value) <= limit else value[:limit] + "..."
    if isinstance(value, dict):
        return {str(k): _compact(v, limit) for k, v in value.items()}
    if isinstance(value, list):
        return [_compact(v, limit) for v in value[:12]]
    return value


def _generation_slice(messages: list) -> dict[str, Any]:
    user = ""
    if len(messages) > 1 and isinstance(messages[1], dict):
        user = str(messages[1].get("content") or "")
    projected = None
    try:
        payload = json.loads(user)
    except json.JSONDecodeError:
        payload = {}
    if isinstance(payload, dict):
        projected = payload.get("resolution_contract")
    return {
        "resolution_contract_in_prompt": isinstance(projected, dict),
        "prompt_contract": projected if isinstance(projected, dict) else None,
    }


def main() -> int:
    repair = "--repair" in sys.argv
    suite = REPAIR_PROBES if repair else PROBES
    turn_cap = 3 if repair else MAX_TURNS
    stamp = _utc_slug()
    out_dir = ROOT / "artifacts" / "pr_br_level2" / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="prbr_l2_"))
    _isolate_storage(tmp)

    import game.api as api_module

    call_log: list[dict[str, Any]] = []
    real_call = api_module.call_gpt

    def wrapped_call(messages, **kwargs):
        call_log.append({"generation": _generation_slice(messages), "kwargs": {k: kwargs.get(k) for k in ("purpose", "retry_attempt", "retry_reason")}})
        return real_call(messages, **kwargs)

    api_module.call_gpt = wrapped_call

    turns: list[dict[str, Any]] = []
    unsatisfied_streak = 0
    with TestClient(app) as client:
        for idx, (probe_id, player_text) in enumerate(suite):
            if len(turns) >= turn_cap:
                break
            calls_before = len(call_log)
            payload = client.post("/api/chat", json={"text": player_text}).json()
            calls = call_log[calls_before:]
            gm_text = _gm_text_from_chat_payload(payload)
            gm_output = payload.get("gm_output") if isinstance(payload.get("gm_output"), dict) else {}
            resolution = payload.get("resolution") if isinstance(payload.get("resolution"), dict) else {}
            meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
            contract = meta.get("resolution_contract") if isinstance(meta.get("resolution_contract"), dict) else {}
            obligation = meta.get("interaction_obligation") if isinstance(meta.get("interaction_obligation"), dict) else {}
            session = payload.get("session") if isinstance(payload.get("session"), dict) else {}
            focus = session.get("discourse_focus") if isinstance(session.get("discourse_focus"), dict) else {}
            emission = {}
            gm_meta = gm_output.get("metadata") if isinstance(gm_output.get("metadata"), dict) else {}
            debug = gm_meta.get("emission_debug") if isinstance(gm_meta.get("emission_debug"), dict) else {}
            if isinstance(debug.get("resolution_contract_semantic"), dict):
                emission = debug["resolution_contract_semantic"]
            live = debug.get("live_resolution_mode") if isinstance(debug.get("live_resolution_mode"), dict) else {}
            evaluation = evaluate_playability(
                _build_eval_payload(
                    player_prompt=player_text,
                    gm_text=gm_text,
                    prior_player=turns[-1]["player_text"] if turns else "",
                    prior_gm=turns[-1]["gm_text"] if turns else "",
                    debug_traces=payload.get("debug_traces"),
                    gm_output=gm_output,
                    resolution_contract=contract or None,
                )
            )
            intent = (evaluation.get("mandatory_gates") or {}).get("player_intent_addressed") or {}
            row = {
                "turn_index": idx,
                "probe_id": probe_id,
                "player_text": player_text,
                "gm_text": gm_text,
                "api_ok": bool(payload.get("ok")),
                "api_error": payload.get("error"),
                "contract_id": contract.get("contract_id"),
                "resolution_contract": contract,
                "interaction_obligation": obligation,
                "discourse_focus": focus,
                "authority_route": {
                    "mode": live.get("mode"),
                    "requested_dimension": live.get("requested_dimension"),
                    "contract_id": live.get("contract_id"),
                    "reason_codes": live.get("reason_codes"),
                    "proposal_created": live.get("proposal_created"),
                },
                "generation_calls": calls,
                "model_calls_this_turn": len(calls),
                "final_emission_semantic": emission,
                "retry_preserved": bool(contract.get("retry_preserved")),
                "semantic_result": evaluation.get("semantic_result"),
                "intent_gate": {
                    "status": intent.get("status"),
                    "reason_codes": intent.get("reason_codes"),
                    "resolution_contract": (intent.get("evidence") or {}).get("resolution_contract"),
                },
                "tags": gm_output.get("tags") if isinstance(gm_output.get("tags"), list) else [],
            }
            turns.append(row)
            (out_dir / "turns.json").write_text(json.dumps(turns, indent=2, ensure_ascii=False), encoding="utf-8")
            print(
                f"TURN {idx + 1} {probe_id} semantic={row['semantic_result']} "
                f"dim={contract.get('dimension')} op={contract.get('operation')} "
                f"prov={contract.get('referent_provenance')} calls={len(calls)}",
                flush=True,
            )
            print(f"GM: {gm_text[:400]}", flush=True)
            status = str((row["intent_gate"].get("resolution_contract") or {}).get("assessment_status") or "")
            if status == "unsatisfied" or row["semantic_result"] == "FAIL":
                unsatisfied_streak += 1
            else:
                unsatisfied_streak = 0
            if unsatisfied_streak >= 3:
                print("EARLY STOP: three semantic failures in a row", flush=True)
                break
            target = row.get("target") if isinstance(row.get("target"), dict) else {}
            target_text = str(target.get("id_or_text") or "").strip().lower().rstrip("?")
            raw = player_text.strip().lower().rstrip("?")
            if target_text and target_text == raw:
                print("EARLY STOP: target still echoes the raw utterance", flush=True)
                break

    summary = {
        "stamp": stamp,
        "isolated_storage": str(tmp),
        "gameplay_turns": len(turns),
        "model_calls": sum(int(t["model_calls_this_turn"]) for t in turns),
        "semantic_failures": [t["probe_id"] for t in turns if t["semantic_result"] != "PASS"],
        "turns": [
            {
                "probe_id": t["probe_id"],
                "semantic_result": t["semantic_result"],
                "contract_id": t["contract_id"],
                "dimension": (t["resolution_contract"] or {}).get("dimension"),
                "operation": (t["resolution_contract"] or {}).get("operation"),
                "referent_provenance": (t["resolution_contract"] or {}).get("referent_provenance"),
                "assessment": (t["intent_gate"].get("resolution_contract") or {}).get("assessment_status"),
            }
            for t in turns
        ],
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    lines = ["# PR-BR Level 2 probes", ""]
    for turn in turns:
        lines.extend(
            [
                f"## {turn['probe_id']}",
                "",
                f"Player: {turn['player_text']}",
                "",
                f"GM: {turn['gm_text']}",
                "",
                f"Semantic: `{turn['semantic_result']}`",
                "",
                f"Contract: `{json.dumps(_compact(turn['resolution_contract']), ensure_ascii=False)}`",
                "",
                f"Obligation: `{json.dumps(_compact(turn['interaction_obligation']), ensure_ascii=False)}`",
                "",
                f"Discourse: `{json.dumps(_compact(turn['discourse_focus']), ensure_ascii=False)}`",
                "",
                f"Authority: `{json.dumps(turn['authority_route'], ensure_ascii=False)}`",
                "",
                f"Emission: `{json.dumps(_compact(turn['final_emission_semantic']), ensure_ascii=False)}`",
                "",
                f"Evaluator: `{json.dumps(_compact(turn['intent_gate']), ensure_ascii=False)}`",
                "",
            ]
        )
    (out_dir / "transcript.md").write_text("\n".join(lines), encoding="utf-8")
    print(str(out_dir), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
