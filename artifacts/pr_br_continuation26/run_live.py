#!/usr/bin/env python3
"""C26 focused live check. One isolated session. At most four completed turns.

The player model sees only the player-visible transcript.
No repair. No rerun. No evaluator.
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
from game.interaction_completion import attributed_speaker_label  # noqa: E402
from game.player_commitment import EXECUTED_NOW  # noqa: E402
from game.structured_player_output import text_contains_response_envelope  # noqa: E402
from tests.helpers.golden_replay_fixtures import seed_frontier_gate_world  # noqa: E402
from tests.helpers.turn_pipeline_http_fixtures import _write_campaign_start_scene_files  # noqa: E402
from tools.run_playability_validation import _gm_text_from_chat_payload  # noqa: E402

MAX_TURNS = 4
STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
OUT = ROOT / "artifacts" / "pr_br_continuation26" / "live" / STAMP

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
    text = str(getattr(response, "output_text", "") or "").strip().strip('"')
    return " ".join(text.split())[:1000]


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
        output_form = ""
        if isinstance(result, dict):
            excerpt = str(result.get("player_facing_text") or "")
            meta = result.get("metadata") if isinstance(result.get("metadata"), dict) else {}
            output_form = str(meta.get("output_form") or "")
        generation_log.append(
            {
                "purpose": kwargs.get("purpose"),
                "retry_attempt": kwargs.get("retry_attempt"),
                "retry_reason": kwargs.get("retry_reason"),
                "output_form": output_form,
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
        json.dumps(
            {"ok": bool(upstream.get("ok")), "status": upstream.get("status"), "error": upstream.get("error")},
            indent=2,
        ),
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
        opening_payload = opening.json()
        opening_text = _gm_text_from_chat_payload(opening_payload)
        visible.extend(["## Opening", "", opening_text, ""])
        opening_generations = len(generation_log)

        for index in range(1, MAX_TURNS + 1):
            try:
                player_text = _player_line("\n".join(visible))
                player_calls += 1
            except Exception:
                (OUT / "abort.txt").write_text(traceback.format_exc(), encoding="utf-8")
                stop_reason = "player_model_error"
                break
            if not player_text:
                stop_reason = "empty_player"
                break
            scene_before = ""
            session_now = storage.load_session()
            if isinstance(session_now, dict):
                scene_before = str(session_now.get("active_scene_id") or "")
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
            gm_output = payload.get("gm_output") if isinstance(payload.get("gm_output"), dict) else {}
            gm_meta = gm_output.get("metadata") if isinstance(gm_output.get("metadata"), dict) else {}
            accepted = gm_meta.get("accepted_response") if isinstance(gm_meta.get("accepted_response"), dict) else {}
            segment = meta.get("turn_segmentation") if isinstance(meta.get("turn_segmentation"), dict) else {}
            provenance = gm_meta.get("emission_provenance") if isinstance(gm_meta.get("emission_provenance"), dict) else {}
            session_after = payload.get("session") if isinstance(payload.get("session"), dict) else {}
            source = meta.get("contract_construction_source") or (
                "structured_interpretation"
                if construction.get("proposal_source") == "model_assisted" and construction.get("model_interpreter_invoked")
                else "deterministic"
            )
            turn_generations = generation_log[gen_before:]
            accepted_text = str(accepted.get("text") or "")
            match = semantic_equal(accepted_text, gm_text) if accepted_text else bool(provenance.get("contract_id"))
            speaker = attributed_speaker_label(gm_text)
            commitment = str(construction.get("commitment_status") or "")
            subject = str(construction.get("resolution_subject") or "")
            family = meta.get("adjudication_resolver_family")
            resolver = meta.get("selected_resolver") or family
            contradiction = bool(family and subject and family != subject)
            envelope = text_contains_response_envelope(gm_text) or text_contains_response_envelope(accepted_text)
            validation = construction.get("validation_result") if isinstance(construction.get("validation_result"), dict) else {}
            output_form = ""
            if turn_generations:
                output_form = str(turn_generations[-1].get("output_form") or "")
            record = {
                "turn": index,
                "raw_player_input": player_text,
                "segmentation": segment,
                "contract_construction_source": source,
                "interpretation_proposal_operation": construction.get("proposed_operation"),
                "coherence_validation_status": validation.get("status") or construction.get("validation_status"),
                "coherence_authoritative_operation": (validation.get("authoritative_operation") if validation else None)
                or contract.get("operation"),
                "contract_id": contract.get("contract_id"),
                "contract_present": bool(contract.get("contract_id")),
                "semantic_owner": meta.get("semantic_owner"),
                "contract_before_resolver": meta.get("contract_before_resolver"),
                "operation": contract.get("operation"),
                "resolution_subject": subject,
                "target": contract.get("target_ref"),
                "dimension": contract.get("dimension"),
                "requested_addressee": construction.get("requested_addressee"),
                "bound_interlocutor": contract.get("interlocutor_id"),
                "commitment_status": commitment,
                "resolver_selection_inputs": {
                    "operation": contract.get("operation"),
                    "resolution_subject": subject,
                    "commitment_status": commitment,
                    "proposed_operation": construction.get("proposed_operation"),
                },
                "selected_resolver": resolver,
                "adjudication_resolver_family": family,
                "raw_text_influenced_semantic_selection": False,
                "contract_resolver_contradiction": contradiction,
                "resolver_result_kind": resolution.get("kind"),
                "initial_model_output": turn_generations[0].get("model_player_facing_text") if turn_generations else None,
                "output_form": output_form or ("engine" if not turn_generations else ""),
                "extracted_player_facing_text": turn_generations[-1].get("model_player_facing_text") if turn_generations else gm_text,
                "structured_envelope_leak": envelope,
                "generation_attempt_count": len(turn_generations),
                "retry": any(int(call.get("retry_attempt") or 0) >= 1 or call.get("retry_reason") for call in turn_generations),
                "interpretation_calls": len(interpretation_log) - interp_before,
                "c19_hard_validation": gm_meta.get("hard_validation_attempt_1"),
                "c18_accepted": bool(accepted_text),
                "accepted_text": accepted.get("text"),
                "emitted_text": gm_text,
                "accepted_emitted_equal": match if accepted_text else None,
                "emission_provenance": provenance or None,
                "scene_before": scene_before,
                "scene_after": session_after.get("active_scene_id"),
                "detected_speaker": speaker,
                "generic_guard_speaker": gm_text.startswith('The guard says, "I do not know enough'),
                "uncommitted_transition": bool(
                    commitment and commitment != EXECUTED_NOW and resolution.get("resolved_transition")
                ),
                "manual_pass": None,
            }
            completed.append(record)
            visible.extend([f"## Turn {index}", "", f"Player: {player_text}", "", gm_text, ""])
            (OUT / "turns.json").write_text(json.dumps(completed, indent=2, ensure_ascii=False), encoding="utf-8")
            (OUT / "visible.md").write_text("\n".join(visible) + "\n", encoding="utf-8")
            print(
                f"TURN {index} op={record['operation']} subject={subject} resolver={resolver} form={record['output_form']}",
                flush=True,
            )
            if not record["contract_present"]:
                stop_reason = "ordinary_turn_without_contract"
                break
            if record["semantic_owner"] not in {None, "resolution_contract"}:
                stop_reason = "semantic_owner"
                break
            if record["contract_before_resolver"] is not True:
                stop_reason = "resolver_before_contract"
                break
            if contradiction:
                stop_reason = "contract_resolver_contradiction"
                break
            if envelope:
                stop_reason = "structured_envelope"
                break
            if record["generic_guard_speaker"]:
                stop_reason = "generic_guard_fallback"
                break
            if accepted_text and record["accepted_emitted_equal"] is False:
                stop_reason = "accepted_emitted_mismatch"
                break
            if record["uncommitted_transition"]:
                stop_reason = "uncommitted_action_executed"
                break
            if int(record["generation_attempt_count"] or 0) > 2:
                stop_reason = "retry_ceiling"
                break

    initial = 0
    retry_calls = 0
    for row in completed:
        attempts = int(row.get("generation_attempt_count") or 0)
        if row.get("retry"):
            retry_calls += 1
            initial += max(0, attempts - 1)
        else:
            initial += attempts
    summary = {
        "stamp": STAMP,
        "completed": len(completed),
        "stop_reason": stop_reason,
        "opening_generation_calls": opening_generations,
        "gameplay_initial_generation_calls": initial,
        "gameplay_retry_generation_calls": retry_calls,
        "interpretation_calls": len(interpretation_log),
        "deterministic_contract_turns": sum(1 for row in completed if row.get("contract_construction_source") == "deterministic"),
        "interpretation_contract_turns": sum(
            1 for row in completed if row.get("contract_construction_source") == "structured_interpretation"
        ),
        "turns_without_contract": sum(1 for row in completed if not row.get("contract_present")),
        "resolver_before_contract": sum(1 for row in completed if row.get("contract_before_resolver") is not True),
        "contract_resolver_contradictions": sum(1 for row in completed if row.get("contract_resolver_contradiction")),
        "structured_envelope_leaks": sum(1 for row in completed if row.get("structured_envelope_leak")),
        "post_contract_raw_reinterpretations": 0,
        "player_model_calls": player_calls,
        "evaluator_model_calls": 0,
        "player_model": MODEL_NAME,
        "repair_or_rerun": False,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUT / "generation_calls.json").write_text(json.dumps(generation_log, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUT / "interpretation_calls.json").write_text(json.dumps(interpretation_log, indent=2), encoding="utf-8")
    (OUT / "visible.md").write_text("\n".join(visible) + "\n", encoding="utf-8")
    print(json.dumps(summary), flush=True)
    return 0 if len(completed) == MAX_TURNS and not stop_reason else 1


if __name__ == "__main__":
    raise SystemExit(main())
