#!/usr/bin/env python3
"""C21 focused live validation. One isolated session, at most six turns.

The player model sees only the player-visible transcript. No repair, no rerun.
"""
from __future__ import annotations

import json
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.pop("ASHEN_DISABLE_LIVE_INTERPRETATION", None)

from fastapi.testclient import TestClient  # noqa: E402

from game import storage  # noqa: E402
from game.api import app  # noqa: E402
from game.api_upstream_preflight import run_upstream_api_preflight  # noqa: E402
from game.config import MODEL_NAME, get_openai_api_key  # noqa: E402
from game.defaults import default_campaign, default_character, default_combat, default_conditions  # noqa: E402
from game.immutable_valid_response import semantic_equal  # noqa: E402
from game.incidental_entity import referential_person_nominal  # noqa: E402
from game.playability_eval import evaluate_playability  # noqa: E402
from game.proposition_authority import classify_propositions, unauthorized_authoritative_rules  # noqa: E402
from tests.helpers.golden_replay_fixtures import seed_frontier_gate_world  # noqa: E402
from tests.helpers.turn_pipeline_http_fixtures import _write_campaign_start_scene_files  # noqa: E402
from tools.run_playability_validation import _build_eval_payload, _gm_text_from_chat_payload  # noqa: E402

MAX_TURNS = 6
STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
OUT = ROOT / "artifacts" / "pr_br_continuation21" / "live" / STAMP

PLAYER_BRIEF = """You are Galinor, a level-1 wandering wizard who has just reached a frontier gate in bad weather.
You want to understand the situation in front of you and make ordinary progress: food, shelter, passage, or whatever the people and place actually offer.
Talk to people who are present, look at things that catch your eye, and follow up on what they say.
You know only the transcript below. Reply with only your next action, in first person, one to three sentences.
"""


def _isolate(tmp: Path) -> None:
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


def _player_line(transcript: str) -> str:
    from openai import OpenAI

    client = OpenAI(api_key=get_openai_api_key())
    response = client.responses.create(
        model=MODEL_NAME,
        input=[
            {"role": "system", "content": PLAYER_BRIEF},
            {"role": "user", "content": transcript[-6000:]},
        ],
    )
    text = str(getattr(response, "output_text", "") or "").strip()
    text = text.strip().strip('"')
    return " ".join(text.split())[:500]


def _early_stop(record: dict[str, Any]) -> str:
    if record.get("accepted_emitted_semantic_match") is False:
        return "c18_mismatch"
    if int(record.get("generation_attempt_count") or 0) > 2:
        return "attempts_over_two"
    if record.get("unauthorized_emitted"):
        return "unsupported_consequential_emitted"
    binding = record.get("entity_binding") if isinstance(record.get("entity_binding"), dict) else {}
    if binding.get("status") == "bound_incidental":
        label = str(binding.get("label") or "")
        if referential_person_nominal(label) is None and referential_person_nominal("the " + label) is None:
            return "malformed_incidental_persisted"
    return ""


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    import game.api as api_module
    import game.semantic_interpreter as interpreter_module

    generation_log: list[dict[str, Any]] = []
    interpretation_log: list[dict[str, Any]] = []
    real_call = api_module.call_gpt
    real_invoke = interpreter_module._invoke_interpretation_model

    def wrapped_generation(messages, **kwargs):
        result = real_call(messages, **kwargs)
        excerpt = ""
        if isinstance(result, dict):
            excerpt = str(result.get("player_facing_text") or "")
        generation_log.append(
            {
                "purpose": kwargs.get("purpose"),
                "retry_attempt": kwargs.get("retry_attempt"),
                "retry_reason": kwargs.get("retry_reason"),
                "model_player_facing_text": excerpt,
            }
        )
        return result

    def wrapped_interpretation(messages):
        interpretation_log.append({"event": "attempt"})
        text = real_invoke(messages)
        interpretation_log[-1]["output_chars"] = len(str(text or ""))
        return text

    api_module.call_gpt = wrapped_generation
    interpreter_module._invoke_interpretation_model = wrapped_interpretation

    isolated = OUT / "isolated_data"
    _isolate(isolated)
    upstream = run_upstream_api_preflight() or {}
    (OUT / "preflight.json").write_text(
        json.dumps({"ok": bool(upstream.get("ok")), "status": upstream.get("status"), "error": upstream.get("error")}, indent=2),
        encoding="utf-8",
    )
    if not upstream.get("ok"):
        print("PREFLIGHT_FAIL", flush=True)
        return 2

    completed: list[dict[str, Any]] = []
    visible = ["# Player-visible transcript", ""]
    player_calls = 0
    stop_reason = ""

    with TestClient(app) as client:
        opening = client.post("/api/start_campaign")
        if opening.status_code >= 400:
            (OUT / "opening_error.txt").write_text(opening.text[:4000], encoding="utf-8")
            print("OPENING_FAIL", flush=True)
            return 2
        opening_text = _gm_text_from_chat_payload(opening.json())
        visible.extend(["## Opening", "", opening_text, ""])
        prior_player = ""
        prior_gm = opening_text
        opening_generations = len(generation_log)

        for index in range(1, MAX_TURNS + 1):
            transcript = "\n".join(visible)
            try:
                player_text = _player_line(transcript)
                player_calls += 1
            except Exception:
                (OUT / "abort.txt").write_text(traceback.format_exc(), encoding="utf-8")
                stop_reason = "player_model_error"
                break
            if not player_text:
                stop_reason = "empty_player"
                break
            gen_before = len(generation_log)
            interp_before = len(interpretation_log)
            try:
                response = client.post("/api/chat", json={"text": player_text})
                if response.status_code >= 400:
                    raise RuntimeError(response.text[:800])
                payload = response.json()
            except Exception:
                (OUT / "abort.txt").write_text(traceback.format_exc(), encoding="utf-8")
                stop_reason = f"abort_turn_{index}"
                break

            gm_text = _gm_text_from_chat_payload(payload)
            resolution = payload.get("resolution") if isinstance(payload.get("resolution"), dict) else {}
            meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
            contract = meta.get("resolution_contract") if isinstance(meta.get("resolution_contract"), dict) else {}
            construction = contract.get("construction") if isinstance(contract.get("construction"), dict) else {}
            binding = construction.get("entity_binding") if isinstance(construction.get("entity_binding"), dict) else {}
            gm_output = payload.get("gm_output") if isinstance(payload.get("gm_output"), dict) else {}
            gm_meta = gm_output.get("metadata") if isinstance(gm_output.get("metadata"), dict) else {}
            accepted = gm_meta.get("accepted_response") if isinstance(gm_meta.get("accepted_response"), dict) else {}
            turn_generations = generation_log[gen_before:]
            evaluation = evaluate_playability(
                _build_eval_payload(
                    player_prompt=player_text,
                    gm_text=gm_text,
                    prior_player=prior_player,
                    prior_gm=prior_gm,
                    debug_traces=[],
                    gm_output=gm_output,
                    resolution_contract=dict(contract) if contract else None,
                )
            )
            emitted_rules = unauthorized_authoritative_rules(gm_text)
            record = {
                "turn": index,
                "player_text": player_text,
                "operation": contract.get("operation"),
                "dimension": contract.get("dimension"),
                "dimensions": contract.get("dimensions"),
                "interlocutor_id": contract.get("interlocutor_id"),
                "discourse_ref": contract.get("discourse_ref"),
                "target_ref": contract.get("target_ref"),
                "entity_binding": binding,
                "contract_expected": contract.get("expected_resolution"),
                "initial_generation": (turn_generations[0].get("model_player_facing_text") if turn_generations else ""),
                "generation_attempt_count": len(turn_generations),
                "retry_invoked": any(int(call.get("retry_attempt") or 0) >= 1 or call.get("retry_reason") for call in turn_generations),
                "accepted_text": accepted.get("text"),
                "accepted_provenance": accepted.get("provenance"),
                "final_emitted_response": gm_text,
                "accepted_emitted_semantic_match": semantic_equal(str(accepted.get("text") or ""), gm_text),
                "hard_validation_attempt_1": gm_meta.get("hard_validation_attempt_1"),
                "regeneration_feedback": gm_meta.get("regeneration_feedback"),
                "authority_emitted": classify_propositions(gm_text),
                "unauthorized_emitted": emitted_rules,
                "interpretation_calls": len(interpretation_log) - interp_before,
                "offline_evaluator": {
                    "semantic_result": evaluation.get("semantic_result"),
                    "score": (evaluation.get("overall") or {}).get("score") if isinstance(evaluation.get("overall"), dict) else None,
                },
                "discourse_after": (payload.get("session") or {}).get("discourse_focus") if isinstance(payload.get("session"), dict) else None,
            }
            completed.append(record)
            visible.extend([f"## Turn {index}", "", f"Player: {player_text}", "", gm_text, ""])
            prior_player = player_text
            prior_gm = gm_text
            (OUT / "turns.json").write_text(json.dumps(completed, indent=2, ensure_ascii=False), encoding="utf-8")
            (OUT / "visible.md").write_text("\n".join(visible) + "\n", encoding="utf-8")
            reason = _early_stop(record)
            print(f"TURN {index} op={record['operation']} match={record['accepted_emitted_semantic_match']}", flush=True)
            if reason:
                stop_reason = reason
                break

    summary = {
        "stamp": STAMP,
        "completed": len(completed),
        "stop_reason": stop_reason,
        "opening_generation_calls": opening_generations if "opening_generations" in dir() else None,
        "gameplay_generation_calls": len(generation_log) - (opening_generations if "opening_generations" in dir() else 0),
        "interpretation_calls": len(interpretation_log),
        "retry_generation_calls": sum(1 for call in generation_log if int(call.get("retry_attempt") or 0) >= 1 or call.get("retry_reason")),
        "player_model_calls": player_calls,
        "evaluator_model_calls": 0,
        "player_model": MODEL_NAME,
    }
    # opening_generations is set inside the with-block; recompute from the log split stored on records
    gameplay_calls = sum(int(row.get("generation_attempt_count") or 0) for row in completed)
    summary["gameplay_generation_calls"] = gameplay_calls
    summary["opening_generation_calls"] = len(generation_log) - gameplay_calls
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUT / "generation_calls.json").write_text(json.dumps(generation_log, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUT / "visible.md").write_text("\n".join(visible) + "\n", encoding="utf-8")
    print(json.dumps(summary), flush=True)
    return 0 if not stop_reason else 1


if __name__ == "__main__":
    raise SystemExit(main())
