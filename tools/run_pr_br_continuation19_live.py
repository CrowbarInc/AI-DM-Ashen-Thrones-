#!/usr/bin/env python3
"""PR-BR continuation 19 focused live check. Maximum 4 completed turns.

One isolated session. Natural wording. No third-bell prompt.
No independent smoke, no 4x10 gate, no repair-and-rerun.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.pop("ASHEN_DISABLE_LIVE_INTERPRETATION", None)

from fastapi.testclient import TestClient  # noqa: E402

from game.api import app  # noqa: E402
from game.api_upstream_preflight import get_latest_upstream_api_preflight  # noqa: E402
from game.immutable_valid_response import semantic_equal  # noqa: E402
from game.interpretation_proposal import span_is_malformed  # noqa: E402
from game.playability_eval import evaluate_playability  # noqa: E402
from game.proposition_authority import classify_propositions, unauthorized_authoritative_rules  # noqa: E402
from tools.run_playability_validation import (  # noqa: E402
    _build_eval_payload,
    _gm_text_from_chat_payload,
)
from tools.run_pr_br_level2_probes import _isolate_storage  # noqa: E402

MAX_COMPLETED = 4

TURNS: tuple[dict[str, str], ...] = (
    {
        "shape": "local condition inquiry",
        "intended": "Ask the tavern runner what travelers are saying about the gate tonight.",
        "text": "I ask the tavern runner what travelers are saying about the gate tonight.",
        "social": "ask",
    },
    {
        "shape": "source follow-up",
        "intended": "Ask the same speaker where that account came from.",
        "text": "Who told you that?",
        "social": "ask",
    },
    {
        "shape": "approach and ask",
        "intended": "Walk to the cloth merchant and ask whether anyone came through from the north road today.",
        "text": "I walk over to the cloth merchant and ask whether anyone has come through from the north road today.",
        "social": "ask",
    },
    {
        "shape": "ordinary inspection",
        "intended": "Read the notice board.",
        "text": "I look over the notice board and read what is posted.",
        "social": "",
    },
)


def _last_user(messages: Any) -> str:
    if not isinstance(messages, list):
        return ""
    for message in reversed(messages):
        if isinstance(message, dict) and message.get("role") == "user":
            return str(message.get("content") or "")[:1200]
    return ""


def _authority_rows(text: str, corpus: str) -> list[dict[str, Any]]:
    rows = []
    for row in classify_propositions(text, authored_corpus=corpus):
        rows.append(
            {
                "proposition": str(row.get("text") or "")[:400],
                "authority_class": row.get("kind"),
                "grounded": bool(row.get("grounded")),
                "epistemic_framing": row.get("epistemic_status"),
                "consequential": bool(row.get("consequential")),
                "family": row.get("family"),
            }
        )
    return rows


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "artifacts" / "pr_br_continuation19" / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        head = ""

    import game.api as api_module
    import game.semantic_interpreter as interpreter_module
    import game.storage as storage

    generation_log: list[dict[str, Any]] = []
    interpretation_log: list[dict[str, Any]] = []
    real_call = api_module.call_gpt
    real_invoke = interpreter_module._invoke_interpretation_model

    def wrapped_generation(messages, **kwargs):
        result = real_call(messages, **kwargs)
        excerpt = ""
        if isinstance(result, dict):
            excerpt = str(result.get("player_facing_text") or "")[:2000]
        generation_log.append(
            {
                "purpose": kwargs.get("purpose"),
                "retry_attempt": kwargs.get("retry_attempt"),
                "retry_reason": kwargs.get("retry_reason"),
                "model_player_facing_excerpt": excerpt,
                "feedback_excerpt": _last_user(messages) if int(kwargs.get("retry_attempt") or 0) > 0 else "",
            }
        )
        return result

    def wrapped_interpretation(messages):
        interpretation_log.append({"event": "attempt"})
        try:
            text = real_invoke(messages)
        except Exception as exc:
            interpretation_log[-1]["error"] = f"{type(exc).__name__}: {exc}"[:500]
            raise
        interpretation_log[-1]["output_excerpt"] = str(text)[:1500]
        return text

    api_module.call_gpt = wrapped_generation
    interpreter_module._invoke_interpretation_model = wrapped_interpretation

    completed: list[dict[str, Any]] = []
    aborted: list[dict[str, Any]] = []
    stop_reason = ""
    social_act_misclassifications = 0

    def persist() -> None:
        (out_dir / "turns.json").write_text(json.dumps(completed, indent=2, ensure_ascii=False), encoding="utf-8")
        (out_dir / "aborted.json").write_text(json.dumps(aborted, indent=2, ensure_ascii=False), encoding="utf-8")
        (out_dir / "generation_calls.json").write_text(
            json.dumps(generation_log, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (out_dir / "interpretation_calls.json").write_text(
            json.dumps(interpretation_log, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        lines = ["# PR-BR Continuation 19 focused live transcript", ""]
        for row in completed:
            lines.extend(
                [
                    f"## T{row.get('turn_number')} {row.get('shape')}",
                    "",
                    f"Intended: {row.get('intended_meaning')}",
                    "",
                    f"Player: {row.get('player_text')}",
                    "",
                    f"Contract: op={row.get('operation')} target={row.get('target')} "
                    f"interlocutor={row.get('interlocutor')} dimension={row.get('dimension')}",
                    "",
                    f"Attempt 1: {row.get('generation_attempt_1')}",
                    "",
                    f"Attempt 2: {row.get('generation_attempt_2') or 'none'}",
                    "",
                    f"Accepted ({row.get('accepted_provenance')}): {row.get('accepted_response_text')}",
                    "",
                    f"Emitted: {row.get('final_emitted_response')}",
                    "",
                    f"Authority: {json.dumps(row.get('authority_review') or [], ensure_ascii=False)}",
                    "",
                ]
            )
        (out_dir / "transcript.md").write_text("\n".join(lines), encoding="utf-8")

    tmp = Path(tempfile.mkdtemp(prefix="prbr_c19_"))
    with TestClient(app) as client:
        preflight = get_latest_upstream_api_preflight() or {}
        if not preflight.get("ok"):
            print(json.dumps({"preflight": "FAIL", "status": preflight.get("status") or preflight.get("reason")}), flush=True)
            return 2
        _isolate_storage(tmp)
        prior_gm = ""
        prior_player = ""
        prior_claim = None
        prior_interlocutor = None
        for spec in TURNS:
            if len(completed) >= MAX_COMPLETED or stop_reason:
                break
            player_text = spec["text"]
            gen_before = len(generation_log)
            interp_before = len(interpretation_log)
            try:
                response = client.post("/api/chat", json={"text": player_text})
                if response.status_code >= 400:
                    raise RuntimeError(f"http {response.status_code}: {response.text[:800]}")
                payload = response.json()
            except Exception as exc:
                aborted.append(
                    {
                        "turn_number": len(completed) + 1,
                        "player_text": player_text,
                        "error_type": type(exc).__name__,
                        "error": traceback.format_exc(),
                    }
                )
                stop_reason = f"mechanical:{type(exc).__name__}"
                persist()
                print(f"ABORT T{len(completed) + 1} {type(exc).__name__}: {exc}", flush=True)
                break
            gm_text = _gm_text_from_chat_payload(payload)
            resolution = payload.get("resolution") if isinstance(payload.get("resolution"), dict) else {}
            meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
            contract = meta.get("resolution_contract") if isinstance(meta.get("resolution_contract"), dict) else {}
            session = payload.get("session") if isinstance(payload.get("session"), dict) else {}
            gm_output = payload.get("gm_output") if isinstance(payload.get("gm_output"), dict) else {}
            gm_meta = gm_output.get("metadata") if isinstance(gm_output.get("metadata"), dict) else {}
            accepted = gm_meta.get("accepted_response") if isinstance(gm_meta.get("accepted_response"), dict) else {}
            emission = gm_meta.get("emission_debug") if isinstance(gm_meta.get("emission_debug"), dict) else {}
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
            turn_generations = generation_log[gen_before:]
            attempt_1 = ""
            attempt_2 = ""
            feedback = ""
            for index, call in enumerate(turn_generations):
                excerpt = str(call.get("model_player_facing_excerpt") or "").strip()
                if index == 0:
                    attempt_1 = excerpt
                elif index == 1:
                    attempt_2 = excerpt
                    feedback = str(call.get("feedback_excerpt") or "")
            accepted_text = str(accepted.get("text") or "")
            exact = bool(accepted_text) and gm_text == accepted_text
            semantic = bool(accepted_text) and (exact or semantic_equal(gm_text, accepted_text))
            hard = accepted.get("hard_validation") if isinstance(accepted.get("hard_validation"), dict) else {}
            attempt_1_hard = gm_meta.get("hard_validation_attempt_1") if isinstance(gm_meta.get("hard_validation_attempt_1"), dict) else {}
            provenance = str(accepted.get("provenance") or "")
            attempts = len(turn_generations)
            target = contract.get("target_ref") if isinstance(contract.get("target_ref"), dict) else {}
            discourse = contract.get("discourse_ref") if isinstance(contract.get("discourse_ref"), dict) else {}
            focus = session.get("discourse_focus") if isinstance(session.get("discourse_focus"), dict) else {}
            construction = contract.get("construction") if isinstance(contract.get("construction"), dict) else {}
            scene = storage.load_scene(str(session.get("active_scene_id") or "frontier_gate"))
            from game.immutable_valid_response import _authored_corpus

            corpus = _authored_corpus(scene if isinstance(scene, dict) else None)
            emitted_authority = _authority_rows(gm_text, corpus)
            unauthorized_emitted = unauthorized_authoritative_rules(gm_text, corpus)
            target_text = str(target.get("id_or_text") or "")
            pseudo_entity = bool(target_text) and " " in target_text and span_is_malformed(target_text)
            claim_after = focus.get("active_claim") if isinstance(focus.get("active_claim"), dict) else None
            row = {
                "turn_number": len(completed) + 1,
                "shape": spec["shape"],
                "player_input": player_text,
                "player_text": player_text,
                "intended_meaning": spec["intended"],
                "operation": contract.get("operation"),
                "target": target_text,
                "interlocutor": contract.get("interlocutor_id"),
                "dimension": contract.get("dimension"),
                "active_claim_before": prior_claim,
                "active_interlocutor_before": prior_interlocutor,
                "fast_path_or_interpreter": construction.get("operation_source") or construction.get("provenance") or (
                    "interpreter" if (len(interpretation_log) - interp_before) else "fast_path"
                ),
                "interpretation_calls_this_turn": len(interpretation_log) - interp_before,
                "resolution_contract": {
                    "contract_id": contract.get("contract_id"),
                    "operation": contract.get("operation"),
                    "interlocutor_id": contract.get("interlocutor_id"),
                    "dimension": contract.get("dimension"),
                    "expected_resolution": contract.get("expected_resolution"),
                    "target": target_text,
                    "discourse_ref": discourse,
                    "abstention_reason": construction.get("abstention_reason"),
                },
                "generation_attempt_1": attempt_1,
                "attempt_1_hard_valid": attempt_1_hard.get("hard_valid"),
                "hard_invalid_reasons": list(attempt_1_hard.get("reasons") or hard.get("reasons") or []),
                "attempt_1_accepted": provenance == "initial_generation",
                "regeneration_invoked": attempts > 1,
                "regeneration_feedback": feedback,
                "generation_attempt_2": attempt_2 or None,
                "accepted_provenance": provenance,
                "accepted_response_text": accepted_text,
                "state_committed_from_attempt": provenance,
                "discourse_committed_from_attempt": provenance,
                "final_emitted_response": gm_text,
                "accepted_emitted_exact_match": exact,
                "accepted_emitted_semantic_match": semantic,
                "presentation_only_difference": bool(semantic and not exact),
                "semantic_degradation_after_acceptance": bool(accepted_text) and not semantic,
                "legacy_would_emit": str(emission.get("legacy_would_emit") or "")[:1600],
                "evaluator_result": evaluation.get("semantic_result"),
                "generation_attempts": attempts,
                "active_claim_after": claim_after,
                "active_interlocutor_after": focus.get("active_interlocutor"),
                "authority_review": emitted_authority,
                "unauthorized_emitted": [str(item.get("text") or "")[:240] for item in unauthorized_emitted],
                "pseudo_entity_target": pseudo_entity,
                "immutable": accepted.get("immutable"),
                "skipped_mutators": list(accepted.get("skipped_mutators") or []),
            }
            completed.append(row)
            persist()
            print(
                f"T{row['turn_number']} op={row['operation']} target={row['target']} "
                f"interlocutor={row['interlocutor']} dim={row['dimension']} prov={provenance} exact={exact} "
                f"attempts={attempts} eval={row['evaluator_result']}",
                flush=True,
            )
            print(f"PLAYER {player_text}", flush=True)
            print(f"EMIT {gm_text}", flush=True)
            prior_player = player_text
            prior_gm = gm_text
            prior_claim = claim_after
            prior_interlocutor = focus.get("active_interlocutor")
            if spec.get("social") == "ask" and contract.get("operation") == "act":
                social_act_misclassifications += 1
            if unauthorized_emitted and provenance in {"initial_generation", "regeneration"}:
                stop_reason = "unsupported_authoritative_rule_emitted"
            elif accepted_text and not semantic:
                stop_reason = "accepted_response_mutated"
            elif attempts > 2:
                stop_reason = "generation_attempts_exceeded"
            elif pseudo_entity:
                stop_reason = "clause_sized_pseudo_entity"
            elif social_act_misclassifications >= 2:
                stop_reason = "social_ask_repeatedly_act"
            elif provenance in {"initial_generation", "regeneration"} and hard.get("hard_valid") is False:
                stop_reason = "hard_invalid_reached_player"
            if stop_reason:
                print(f"STOP {stop_reason}", flush=True)
                break

    summary = {
        "stamp": stamp,
        "head": head,
        "completed_turns": len(completed),
        "gameplay_generation_calls": len(generation_log),
        "interpretation_calls": len(interpretation_log),
        "evaluator_model_calls": 0,
        "regeneration_calls": sum(1 for call in generation_log if int(call.get("retry_attempt") or 0) > 0),
        "generation_attempts_over_two": sum(1 for row in completed if int(row.get("generation_attempts") or 0) > 2),
        "accepted_mutations": sum(1 for row in completed if row.get("semantic_degradation_after_acceptance")),
        "exact_matches": sum(1 for row in completed if row.get("accepted_emitted_exact_match")),
        "evaluator_pass": sum(1 for row in completed if row.get("evaluator_result") == "PASS"),
        "unauthorized_emitted": sum(1 for row in completed if row.get("unauthorized_emitted")),
        "pseudo_entity_targets": sum(1 for row in completed if row.get("pseudo_entity_target")),
        "social_ask_as_act": social_act_misclassifications,
        "aborted": len(aborted),
        "stop_reason": stop_reason or None,
        "independent_smoke": False,
        "full_gate": False,
        "semantic_repair_rerun": False,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    persist()
    print(json.dumps(summary), flush=True)
    print(out_dir, flush=True)
    return 0 if not str(stop_reason).startswith("mechanical") else 2


if __name__ == "__main__":
    raise SystemExit(main())
