#!/usr/bin/env python3
"""PR-BR continuation 12 focused live check. Maximum 6 completed turns.

Exercises fast-path success and abstention-to-interpretation in one session.
Not a smoke test and not a 4x10 gate. No repair-and-rerun.
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
from game.playability_eval import evaluate_playability  # noqa: E402
from tools.run_playability_validation import (  # noqa: E402
    _build_eval_payload,
    _gm_text_from_chat_payload,
)
from tools.run_pr_br_level2_probes import _isolate_storage  # noqa: E402

MAX_COMPLETED = 6

TURNS: tuple[dict[str, str], ...] = (
    {
        "shape": "compound social inquiry",
        "intended": "Find the person working the gate and ask what is required to pass tonight.",
        "text": "I look around for whoever is minding the gate and ask what it takes to get inside tonight.",
    },
    {
        "shape": "elliptical follow-up",
        "intended": "Ask how recent the thing just said is, or abstain if nothing was claimed.",
        "text": "How recently?",
    },
    {
        "shape": "obvious canonical inspection",
        "intended": "Inspect the notice board that is already in the scene.",
        "text": "I examine the notice board.",
    },
    {
        "shape": "object use question",
        "intended": "Learn what the posted notice is for.",
        "text": "I stay with that posted sheet and try to figure out what people actually use it for.",
    },
    {
        "shape": "referential action",
        "intended": "Do the concrete thing the previous speaker suggested, not place a foot on a step.",
        "text": "Alright, I'll do what he just told me to do.",
    },
    {
        "shape": "multi-reference interpersonal question",
        "intended": "Ask the current person about the thing just under discussion.",
        "text": "I turn to him and ask about it.",
    },
)


def _slice(value: Any, limit: int = 700) -> Any:
    if isinstance(value, str):
        return value if len(value) <= limit else value[:limit] + "..."
    if isinstance(value, dict):
        return {str(key): _slice(item, limit) for key, item in list(value.items())[:40]}
    if isinstance(value, list):
        return [_slice(item, limit) for item in value[:12]]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return str(value)[:limit]


def _slot(focus: dict, name: str) -> Any:
    slot = focus.get(name)
    if not isinstance(slot, dict):
        return None
    return {"id": slot.get("id"), "label": slot.get("label"), "kind": slot.get("kind")}


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "artifacts" / "pr_br_continuation12" / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        head = ""

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
            excerpt = str(result.get("player_facing_text") or "")[:1200]
        generation_log.append(
            {
                "purpose": kwargs.get("purpose"),
                "retry_attempt": kwargs.get("retry_attempt"),
                "retry_reason": kwargs.get("retry_reason"),
                "model_player_facing_excerpt": excerpt,
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
    premise_hits = 0

    def persist() -> None:
        (out_dir / "turns.json").write_text(json.dumps(completed, indent=2, ensure_ascii=False), encoding="utf-8")
        (out_dir / "aborted.json").write_text(json.dumps(aborted, indent=2, ensure_ascii=False), encoding="utf-8")
        (out_dir / "generation_calls.json").write_text(json.dumps(generation_log, indent=2, ensure_ascii=False), encoding="utf-8")
        (out_dir / "interpretation_calls.json").write_text(
            json.dumps(interpretation_log, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        lines = ["# PR-BR Continuation 12 focused live transcript", ""]
        for row in completed:
            lines.extend(
                [
                    f"## T{row.get('turn_number')} {row.get('shape')}",
                    "",
                    f"Intended: {row.get('intended_meaning')}",
                    "",
                    f"Player: {row.get('player_text')}",
                    "",
                    f"Generated: {row.get('generated_candidate')}",
                    "",
                    f"GM: {row.get('gm_text')}",
                    "",
                    (
                        f"fast={row.get('fast_path_used')} completeness={row.get('semantic_completeness')} "
                        f"abstain={row.get('abstention_reason')} interpreter={row.get('interpreter_invoked')} "
                        f"op={row.get('operation')} target={row.get('canonical_target')} "
                        f"eval={row.get('semantic_result')}"
                    ),
                    "",
                ]
            )
        (out_dir / "transcript.md").write_text("\n".join(lines), encoding="utf-8")

    tmp = Path(tempfile.mkdtemp(prefix="prbr_c12_"))
    with TestClient(app) as client:
        preflight = get_latest_upstream_api_preflight() or {}
        if not preflight.get("ok"):
            print(json.dumps({"preflight": "FAIL", "status": preflight}), flush=True)
            return 2
        _isolate_storage(tmp)
        prior_gm = ""
        prior_player = ""
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
            construction = contract.get("construction") if isinstance(contract.get("construction"), dict) else {}
            session = payload.get("session") if isinstance(payload.get("session"), dict) else {}
            gm_output = payload.get("gm_output") if isinstance(payload.get("gm_output"), dict) else {}
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
            target = contract.get("target_ref") if isinstance(contract.get("target_ref"), dict) else {}
            proposal = construction.get("interpretation_proposal") if isinstance(construction.get("interpretation_proposal"), dict) else {}
            focus = session.get("discourse_focus") if isinstance(session.get("discourse_focus"), dict) else {}
            turn_generations = generation_log[gen_before:]
            generated = ""
            for call in turn_generations:
                excerpt = str(call.get("model_player_facing_excerpt") or "").strip()
                if excerpt:
                    generated = excerpt
            lowered = gm_text.lower()
            premise = "no such thing" in lowered or "no such person" in lowered or "there is no guard" in lowered
            if premise and contract.get("interlocutor_id"):
                premise_hits += 1
            row = {
                "turn_number": len(completed) + 1,
                "shape": spec["shape"],
                "intended_meaning": spec["intended"],
                "player_text": player_text,
                "generated_candidate": generated,
                "gm_text": gm_text,
                "fast_path_used": construction.get("fast_path_used"),
                "semantic_completeness": construction.get("semantic_completeness"),
                "fast_path_abstained": construction.get("fast_path_abstained"),
                "abstention_reason": construction.get("fast_path_abstention_reason"),
                "interpreter_invoked": construction.get("model_interpreter_invoked"),
                "proposal_source": construction.get("proposal_source"),
                "proposed_operation": proposal.get("primary_operation"),
                "proposed_target": proposal.get("proposed_target_id") or proposal.get("raw_target_text"),
                "proposed_supporting": proposal.get("supporting_operations"),
                "proposed_subject": proposal.get("conversational_subject"),
                "proposed_interlocutor": proposal.get("interlocutor_id"),
                "proposed_dimension": proposal.get("dimension"),
                "canonical_candidates": _slice(construction.get("canonical_candidates"), 180),
                "validator_status": construction.get("validation_status"),
                "validator_reason": construction.get("abstention_reason"),
                "operation": contract.get("operation"),
                "canonical_target": target.get("id_or_text"),
                "discourse_ref": contract.get("discourse_ref"),
                "interlocutor_id": contract.get("interlocutor_id"),
                "conversational_subject": contract.get("conversational_subject"),
                "dimension": contract.get("dimension"),
                "ambiguous": contract.get("ambiguous"),
                "contract_id": contract.get("contract_id"),
                "discourse_commit_allowed": construction.get("discourse_commit_allowed"),
                "active_interlocutor": _slot(focus, "active_interlocutor"),
                "active_claim": _slot(focus, "active_claim"),
                "active_inspected": _slot(focus, "active_inspected"),
                "actionable_lead": _slot(focus, "active_actionable_lead"),
                "previous_action": _slot(focus, "last_attempted_action"),
                "semantic_result": evaluation.get("semantic_result"),
                "premise_contradicted": premise,
                "generation_calls_this_turn": len(generation_log) - gen_before,
                "interpretation_calls_this_turn": len(interpretation_log) - interp_before,
                "focus": _slice(focus, 240),
                "telemetry": session.get("interpretation_telemetry"),
            }
            completed.append(row)
            persist()
            print(
                f"T{row['turn_number']} fast={row['fast_path_used']} complete={row['semantic_completeness']} "
                f"abstain={row['abstention_reason']} model={row['interpreter_invoked']} op={row['operation']} "
                f"eval={row['semantic_result']} gen={row['generation_calls_this_turn']} "
                f"interp={row['interpretation_calls_this_turn']}",
                flush=True,
            )
            print(f"PLAYER {player_text}", flush=True)
            print(f"GM {gm_text}", flush=True)
            prior_player = player_text
            prior_gm = gm_text
            if premise_hits >= 2:
                stop_reason = "systemic:canonical_premise_contradiction"
                print(f"STOP {stop_reason}", flush=True)
                break
            if row["interpreter_invoked"] and row.get("interpretation_error") and "schema" in str(row.get("interpretation_error") or "").lower():
                stop_reason = "mechanical:interpretation_schema"
                print(f"STOP {stop_reason}", flush=True)
                break

    summary = {
        "stamp": stamp,
        "head": head,
        "completed_turns": len(completed),
        "fast_path_turns": sum(1 for row in completed if row.get("fast_path_used")),
        "abstentions": sum(1 for row in completed if row.get("fast_path_abstained")),
        "interpreted_turns": sum(1 for row in completed if row.get("interpreter_invoked")),
        "generation_calls": len(generation_log),
        "interpretation_calls": len(interpretation_log),
        "evaluator_model_calls": 0,
        "retries": sum(1 for call in generation_log if int(call.get("retry_attempt") or 0) > 0),
        "aborted": len(aborted),
        "semantic_pass": sum(1 for row in completed if row.get("semantic_result") == "PASS"),
        "semantic_fail": sum(1 for row in completed if row.get("semantic_result") == "FAIL"),
        "premise_contradictions": premise_hits,
        "stop_reason": stop_reason or None,
        "max_completed": MAX_COMPLETED,
        "smoke": False,
        "full_gate": False,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    persist()
    print(json.dumps(summary), flush=True)
    print(out_dir, flush=True)
    return 0 if not str(stop_reason).startswith("mechanical") else 2


if __name__ == "__main__":
    raise SystemExit(main())
