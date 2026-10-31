#!/usr/bin/env python3
"""C22 focused live check. One isolated session, at most five completed turns.

The player model sees only the player-visible transcript. No repair, no rerun.
"""
from __future__ import annotations

import json
import os
import re
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
from game.incidental_entity import (  # noqa: E402
    nominal_semantic_head,
    personhood_of_span,
    referential_head,
    referential_person_nominal,
)
from game.interaction_completion import attributed_speaker_label  # noqa: E402
from game.player_commitment import EXECUTED_NOW  # noqa: E402
from game.proposition_authority import classify_propositions, unauthorized_authoritative_rules  # noqa: E402
from tests.helpers.golden_replay_fixtures import seed_frontier_gate_world  # noqa: E402
from tests.helpers.turn_pipeline_http_fixtures import _write_campaign_start_scene_files  # noqa: E402
from tools.run_playability_validation import _gm_text_from_chat_payload  # noqa: E402

MAX_TURNS = 5
STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
OUT = ROOT / "artifacts" / "pr_br_continuation22" / "live" / STAMP

PLAYER_BRIEF = """You are Galinor, a level-1 wandering wizard who has just reached a frontier gate in bad weather.
You want to understand the situation in front of you and make ordinary progress: food, shelter, passage, or whatever the people and place actually offer.
Talk to people who are present, look at things that catch your eye, and follow up on what they say.
You know only the transcript below. Reply with only your next action, in first person, one to three sentences.
"""

_SOCIAL_RE = re.compile(
    r"\b(?:ask|asks|asked|asking|tell|tells|told|question|questions|request|requests|speak to|talk to)\b",
    re.IGNORECASE,
)
_SUPPORTING_PERCEPTION_RE = re.compile(
    r"\blisten(?:ing)?\s+carefully\b|\bwatch(?:ing)?\s+(?:his|her|their)\s+reaction\b",
    re.IGNORECASE,
)


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
    return " ".join(text.split())[:1000]


def _person_label_ok(label: str) -> bool:
    if referential_person_nominal(label):
        return True
    return referential_person_nominal("the " + label) is not None


def _scene_id(payload: dict[str, Any]) -> str:
    session = payload.get("session") if isinstance(payload.get("session"), dict) else {}
    world = payload.get("world") if isinstance(payload.get("world"), dict) else {}
    return str(
        session.get("active_scene_id")
        or world.get("active_scene_id")
        or (session.get("scene") or {}).get("id")
        if isinstance(session.get("scene"), dict)
        else ""
        or ""
    )


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
    opening_generations = 0
    previous_interlocutor = ""
    perception_steals = 0

    with TestClient(app) as client:
        opening = client.post("/api/start_campaign")
        if opening.status_code >= 400:
            (OUT / "opening_error.txt").write_text(opening.text[:4000], encoding="utf-8")
            print("OPENING_FAIL", flush=True)
            return 2
        opening_payload = opening.json()
        opening_text = _gm_text_from_chat_payload(opening_payload)
        visible.extend(["## Opening", "", opening_text, ""])
        prior_scene = _scene_id(opening_payload)
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
            span = str(binding.get("proposed_span") or "")
            label = str(binding.get("label") or "")
            head = referential_head(span) or referential_head(label) or nominal_semantic_head(span) or nominal_semantic_head(label)
            kind = personhood_of_span(span) if span else personhood_of_span(label) if label else "none"
            if kind == "absent" and not span and not label:
                kind = "none"
            personhood = "person" if kind == "person" else "not_person" if kind not in {"none", "absent"} else "none"
            session = storage.load_session()
            stored = [
                str(row.get("label") or "")
                for row in (session.get("bounded_improvisation") or {}).get("incidental_entities") or []
                if isinstance(row, dict)
            ]
            rejected_persisted = bool(
                binding.get("status") != "bound_incidental"
                and label
                and label in stored
                and not _person_label_ok(label)
            )
            speaker = attributed_speaker_label(gm_text)
            binding_status = str(construction.get("addressee_binding_status") or binding.get("status") or "")
            requested = str(construction.get("requested_addressee") or "")
            commitment = str(construction.get("commitment_status") or "")
            scene_after = _scene_id(payload) or prior_scene
            transition_executed = bool(resolution.get("resolved_transition")) or scene_after != prior_scene
            social = bool(_SOCIAL_RE.search(player_text))
            supporting = bool(_SUPPORTING_PERCEPTION_RE.search(player_text))
            perception_stole = bool(social and supporting and contract.get("operation") == "perceive")
            if perception_stole:
                perception_steals += 1
            unresolved = binding_status in {"unresolved", "ambiguous", "rejected_consequential"} and bool(requested)
            speaker_conflict = False
            if unresolved and speaker and contract.get("interlocutor_id") in {None, ""}:
                speaker_head = nominal_semantic_head(speaker) or ""
                requested_head = nominal_semantic_head(requested) or ""
                if speaker_head and requested_head and speaker_head != requested_head:
                    hard = gm_meta.get("hard_validation_attempt_1") if isinstance(gm_meta.get("hard_validation_attempt_1"), dict) else {}
                    if hard.get("hard_valid") is not False and semantic_equal(str(accepted.get("text") or ""), gm_text):
                        speaker_conflict = True
            emitted_rules = unauthorized_authoritative_rules(gm_text)
            record = {
                "turn": index,
                "player_text": player_text,
                "clause_intent_candidates": construction.get("interpretation_proposal"),
                "primary_committed_intent": construction.get("primary_operation") or contract.get("operation"),
                "secondary_supporting_intents": construction.get("secondary_operations"),
                "commitment_modality": commitment,
                "operation": contract.get("operation"),
                "dimension": contract.get("dimension"),
                "dimensions": contract.get("dimensions"),
                "target": contract.get("target_ref"),
                "requested_addressee": requested or None,
                "binding_status": binding_status or None,
                "resolved_interlocutor": contract.get("interlocutor_id"),
                "state_transition_requested": resolution.get("kind"),
                "state_transition_executed": transition_executed,
                "transition_target": resolution.get("target_scene_id"),
                "scene_before": prior_scene,
                "scene_after": scene_after,
                "initial_generation": (turn_generations[0].get("model_player_facing_text") if turn_generations else ""),
                "detected_speaker": speaker,
                "generation_attempt_count": len(turn_generations),
                "retry_invoked": any(
                    int(call.get("retry_attempt") or 0) >= 1 or call.get("retry_reason") for call in turn_generations
                ),
                "hard_validation_attempt_1": gm_meta.get("hard_validation_attempt_1"),
                "accepted_text": accepted.get("text"),
                "accepted_provenance": accepted.get("provenance"),
                "final_emitted_response": gm_text,
                "accepted_emitted_semantic_match": semantic_equal(str(accepted.get("text") or ""), gm_text),
                "state_discourse_commits": {
                    "interlocutor_id": contract.get("interlocutor_id"),
                    "discourse_ref": contract.get("discourse_ref"),
                    "incidental_entities": stored,
                    "rejected_response_committed": False,
                },
                "perception_stole_primary": perception_stole,
                "uncommitted_action_executed": bool(commitment and commitment != EXECUTED_NOW and transition_executed),
                "wrong_speaker_unresolved": speaker_conflict,
                "entity_binding": binding,
                "resolved_referential_head": head or None,
                "personhood_result": personhood,
                "unauthorized_emitted": emitted_rules,
                "authority_emitted": classify_propositions(gm_text),
                "interpretation_calls": len(interpretation_log) - interp_before,
                "rejected_label_persisted": rejected_persisted,
                "manual_pass": None,
            }
            completed.append(record)
            visible.extend([f"## Turn {index}", "", f"Player: {player_text}", "", gm_text, ""])
            prior_scene = scene_after
            (OUT / "turns.json").write_text(json.dumps(completed, indent=2, ensure_ascii=False), encoding="utf-8")
            (OUT / "visible.md").write_text("\n".join(visible) + "\n", encoding="utf-8")
            reason = ""
            if record["accepted_emitted_semantic_match"] is False:
                reason = "c18_mismatch"
            elif int(record["generation_attempt_count"] or 0) > 2:
                reason = "attempts_over_two"
            elif emitted_rules:
                reason = "unsupported_consequential_emitted"
            elif record["uncommitted_action_executed"]:
                reason = "uncommitted_action_executed"
            elif speaker_conflict:
                reason = "unresolved_addressee_wrong_speaker"
            elif previous_interlocutor and record.get("resolved_interlocutor") == previous_interlocutor and unresolved:
                reason = "stale_interlocutor_after_unresolved_addressee"
            elif binding.get("status") == "bound_incidental" and label and not _person_label_ok(label):
                reason = "malformed_incidental_persisted"
            elif rejected_persisted:
                reason = "rejected_candidate_persisted"
            elif perception_steals >= 2:
                reason = "supporting_perception_repeatedly_stole_ask"
            print(
                f"TURN {index} op={record['operation']} commit={commitment} bind={binding_status} "
                f"scene={scene_after} match={record['accepted_emitted_semantic_match']}",
                flush=True,
            )
            if reason:
                stop_reason = reason
                break
            if record.get("resolved_interlocutor"):
                previous_interlocutor = str(record.get("resolved_interlocutor"))

    gameplay_calls = sum(int(row.get("generation_attempt_count") or 0) for row in completed)
    retry_calls = sum(
        1
        for call in generation_log[opening_generations:]
        if int(call.get("retry_attempt") or 0) >= 1 or call.get("retry_reason")
    )
    summary = {
        "stamp": STAMP,
        "completed": len(completed),
        "stop_reason": stop_reason,
        "opening_generation_calls": opening_generations,
        "gameplay_initial_generation_calls": max(0, gameplay_calls - retry_calls),
        "gameplay_retry_generation_calls": retry_calls,
        "gameplay_generation_calls": gameplay_calls,
        "interpretation_calls": len(interpretation_log),
        "player_model_calls": player_calls,
        "evaluator_model_calls": 0,
        "player_model": MODEL_NAME,
        "repair_or_rerun": False,
        "perception_steals": perception_steals,
        "uncommitted_actions_executed": sum(1 for row in completed if row.get("uncommitted_action_executed")),
        "wrong_speaker_unresolved": sum(1 for row in completed if row.get("wrong_speaker_unresolved")),
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUT / "generation_calls.json").write_text(json.dumps(generation_log, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUT / "visible.md").write_text("\n".join(visible) + "\n", encoding="utf-8")
    print(json.dumps(summary), flush=True)
    print(f"OUT {OUT}", flush=True)
    return 0 if not stop_reason and len(completed) == MAX_TURNS else 1


if __name__ == "__main__":
    raise SystemExit(main())
