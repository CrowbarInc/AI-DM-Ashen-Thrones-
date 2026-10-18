#!/usr/bin/env python3
"""PR-BR continuation 15 focused live check. Maximum 4 completed turns.

Natural interaction after the content, clarification, and additive-coverage gate.
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
from game.resolution_contract import (  # noqa: E402
    detect_semantic_degradation,
    resolution_coverage,
    semantic_line_view,
)
from tools.run_playability_validation import (  # noqa: E402
    _build_eval_payload,
    _gm_text_from_chat_payload,
)
from tools.run_pr_br_level2_probes import _isolate_storage  # noqa: E402

MAX_COMPLETED = 4

TURNS: tuple[dict[str, str], ...] = (
    {
        "shape": "ordinary control",
        "intended": "Inspect the notice board as an ordinary canonical control.",
        "text": "I stop at the gate and read the notice board from top to bottom.",
    },
    {
        "shape": "ambiguous follow-up",
        "intended": "Ask when an unresolved 'that' began, so clarification is necessary if more than one posting is plausible.",
        "text": "When did that happen?",
    },
    {
        "shape": "content inquiry",
        "intended": "Ask what travelers have actually been reporting.",
        "text": "I ask the gate guard what the travelers have been telling people as they arrive.",
    },
    {
        "shape": "additive dimension",
        "intended": "Ask what the board is for, where a useful answer may also mention when something was posted.",
        "text": "What do people come to that board for?",
    },
)


def _slice(value: Any, limit: int = 700) -> Any:
    if isinstance(value, str):
        return value if len(value) <= limit else value[:limit] + "..."
    if isinstance(value, dict):
        return {str(key): _slice(item, limit) for key, item in list(value.items())[:40]}
    if isinstance(value, list):
        return [_slice(item, limit) for item in value[:24]]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return str(value)[:limit]


def _slot(focus: dict, name: str) -> Any:
    slot = focus.get(name)
    if not isinstance(slot, dict):
        return None
    return {"id": slot.get("id"), "label": slot.get("label"), "kind": slot.get("kind")}


def _view_brief(view: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": view.get("status"),
        "reasons": view.get("reasons"),
        "resolution_kind": view.get("resolution_kind"),
        "dimension_compatible": view.get("dimension_compatible"),
        "keeps_answer": view.get("keeps_answer"),
        "rank": view.get("rank"),
    }


def _coverage_brief(coverage: dict[str, Any]) -> dict[str, Any]:
    return {
        "required_dimensions": coverage.get("required_dimensions"),
        "covered_dimensions": coverage.get("covered_dimensions"),
        "complete": coverage.get("complete"),
        "dimension": coverage.get("dimension"),
        "operation": coverage.get("operation"),
        "expected_resolution": coverage.get("expected_resolution"),
    }


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "artifacts" / "pr_br_continuation15" / stamp
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
            excerpt = str(result.get("player_facing_text") or "")[:1600]
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
    degradations = 0
    emission_mismatches = 0

    def persist() -> None:
        (out_dir / "turns.json").write_text(json.dumps(completed, indent=2, ensure_ascii=False), encoding="utf-8")
        (out_dir / "aborted.json").write_text(json.dumps(aborted, indent=2, ensure_ascii=False), encoding="utf-8")
        (out_dir / "generation_calls.json").write_text(json.dumps(generation_log, indent=2, ensure_ascii=False), encoding="utf-8")
        (out_dir / "interpretation_calls.json").write_text(
            json.dumps(interpretation_log, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        lines = ["# PR-BR Continuation 15 focused live transcript", ""]
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
                        f"op={row.get('operation')} target={row.get('canonical_target')} "
                        f"interlocutor={row.get('interlocutor_id')} dimension={row.get('dimension')} "
                        f"eval={row.get('semantic_result')} "
                        f"initial={row.get('initial_satisfaction')} final={row.get('final_satisfaction')} "
                        f"best_emitted={row.get('best_candidate_emitted')} "
                        f"degraded={row.get('semantic_degradation')}"
                    ),
                    "",
                ]
            )
        (out_dir / "transcript.md").write_text("\n".join(lines), encoding="utf-8")

    tmp = Path(tempfile.mkdtemp(prefix="prbr_c15_"))
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
            gm_meta = gm_output.get("metadata") if isinstance(gm_output.get("metadata"), dict) else {}
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
            target = contract.get("target_ref") if isinstance(contract.get("target_ref"), dict) else {}
            proposal = construction.get("interpretation_proposal") if isinstance(construction.get("interpretation_proposal"), dict) else {}
            focus = session.get("discourse_focus") if isinstance(session.get("discourse_focus"), dict) else {}
            turn_generations = generation_log[gen_before:]
            generated = ""
            for call in turn_generations:
                excerpt = str(call.get("model_player_facing_excerpt") or "").strip()
                if excerpt:
                    generated = excerpt
            initial_view = semantic_line_view(generated, resolution) if generated else {}
            final_view = semantic_line_view(gm_text, resolution)
            initial_coverage = resolution_coverage(generated, resolution) if generated else {}
            final_coverage = resolution_coverage(gm_text, resolution)
            best = str(emission.get("best_safe_candidate") or "").strip()
            final_selected = str(emission.get("final_selected_candidate") or gm_text or "").strip()
            best_emitted = (not best) or best[:160] in gm_text or gm_text[:160] in best
            degradation = detect_semantic_degradation(generated, gm_text, resolution) if generated else {"degraded": False, "reasons": []}
            degraded = bool(degradation.get("degraded"))
            if degraded:
                degradations += 1
            if best and not best_emitted:
                emission_mismatches += 1
            transitions = emission.get("candidate_transitions") if isinstance(emission.get("candidate_transitions"), list) else []
            row = {
                "turn_number": len(completed) + 1,
                "shape": spec["shape"],
                "intended_meaning": spec["intended"],
                "player_text": player_text,
                "generated_candidate": generated,
                "gm_text": gm_text,
                "best_safe_candidate": best[:1600],
                "final_selected_candidate": final_selected[:1600],
                "best_candidate_emitted": best_emitted,
                "best_safe_invalidation": emission.get("best_safe_invalidation"),
                "satisfied_candidate": str(emission.get("satisfied_candidate") or "")[:1600],
                "candidate_transitions": _slice(transitions, 280),
                "outcome_precedence": emission.get("outcome_precedence"),
                "replacement_reason": (emission.get("outcome_precedence") or {}).get("replacement_reason")
                if isinstance(emission.get("outcome_precedence"), dict)
                else None,
                "initial_satisfaction": _view_brief(initial_view),
                "final_satisfaction": _view_brief(final_view),
                "initial_coverage": _coverage_brief(initial_coverage),
                "final_coverage": _coverage_brief(final_coverage),
                "semantic_degradation": degraded,
                "semantic_degradation_reasons": list(degradation.get("reasons") or []),
                "fast_path_used": construction.get("fast_path_used"),
                "semantic_completeness": construction.get("semantic_completeness"),
                "fast_path_abstained": construction.get("fast_path_abstained"),
                "abstention_reason": construction.get("fast_path_abstention_reason"),
                "interpreter_invoked": construction.get("model_interpreter_invoked"),
                "proposal_source": construction.get("proposal_source"),
                "proposed_operation": proposal.get("primary_operation"),
                "proposed_target": proposal.get("proposed_target_id") or proposal.get("raw_target_text"),
                "proposed_subject": proposal.get("conversational_subject"),
                "proposed_interlocutor": proposal.get("interlocutor_id"),
                "proposed_dimension": proposal.get("dimension"),
                "validator_status": construction.get("validation_status"),
                "validator_reason": construction.get("abstention_reason"),
                "operation": contract.get("operation"),
                "canonical_target": target.get("id_or_text"),
                "discourse_ref": contract.get("discourse_ref"),
                "interlocutor_id": contract.get("interlocutor_id"),
                "conversational_subject": contract.get("conversational_subject"),
                "dimension": contract.get("dimension"),
                "dimensions": contract.get("dimensions"),
                "expected_resolution": contract.get("expected_resolution"),
                "ambiguous": contract.get("ambiguous"),
                "contract_id": contract.get("contract_id"),
                "active_interlocutor": _slot(focus, "active_interlocutor"),
                "active_claim": _slot(focus, "active_claim"),
                "active_inspected": _slot(focus, "active_inspected"),
                "actionable_lead": _slot(focus, "active_actionable_lead"),
                "previous_action": _slot(focus, "last_attempted_action"),
                "semantic_result": evaluation.get("semantic_result"),
                "generation_calls_this_turn": len(generation_log) - gen_before,
                "interpretation_calls_this_turn": len(interpretation_log) - interp_before,
                "focus": _slice(focus, 240),
            }
            completed.append(row)
            persist()
            print(
                f"T{row['turn_number']} op={row['operation']} dim={row['dimension']} "
                f"target={row['canonical_target']} interlocutor={row['interlocutor_id']} "
                f"eval={row['semantic_result']} initial={row['initial_satisfaction'].get('status')} "
                f"final={row['final_satisfaction'].get('status')} "
                f"best_emitted={best_emitted} degraded={degraded} "
                f"gen={row['generation_calls_this_turn']} interp={row['interpretation_calls_this_turn']}",
                flush=True,
            )
            print(f"PLAYER {player_text}", flush=True)
            print(f"GEN {generated}", flush=True)
            print(f"GM {gm_text}", flush=True)
            prior_player = player_text
            prior_gm = gm_text
            if degraded:
                stop_reason = "systemic:semantic_degradation"
                print(f"STOP {stop_reason}", flush=True)
                break
            if emission_mismatches:
                stop_reason = "systemic:best_safe_not_emitted"
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
        "semantic_degradations": degradations,
        "best_safe_emission_mismatches": emission_mismatches,
        "stop_reason": stop_reason or None,
        "max_completed": MAX_COMPLETED,
        "smoke": False,
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
