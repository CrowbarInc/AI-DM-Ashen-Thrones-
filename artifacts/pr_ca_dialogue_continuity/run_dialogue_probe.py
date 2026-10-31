#!/usr/bin/env python3
"""PR-CA bounded multi-turn live dialogue validation.

Measurement only. Reuses the PR-BX live instrumentation, but keeps one
isolated baker session alive across four consecutive player turns.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "artifacts" / "pr_bx_narration_only_micro_live" / "run_probes.py"
OUT = ROOT / "artifacts" / "pr_ca_dialogue_continuity" / "evidence"

spec = importlib.util.spec_from_file_location("pr_bx_run_probes", SOURCE)
if spec is None or spec.loader is None:
    raise RuntimeError(f"could not load {SOURCE}")
bx = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = bx
spec.loader.exec_module(bx)

bx.OUT = OUT

TURNS = (
    ("T1", "Baker, which loaf do you usually keep for yourself?"),
    ("T2", "Surely you have a favorite. What makes you reluctant to say?"),
    ("T3", "Fair enough. Which loaf would you recommend to someone who has never bought bread here?"),
    ("T4", "Thanks. I'll remember your recommendation."),
)


def save(name: str, value) -> None:
    bx.save(name, value)


def _token_sum(calls: list[dict], field: str) -> int:
    total = 0
    for call in calls:
        value = (call.get("usage") or {}).get(field)
        if isinstance(value, int):
            total += value
    return total


def _generation_rows(calls: list[dict]) -> list[dict]:
    rows = []
    for call in calls:
        if call.get("kind") == "generation":
            rows.append(call)
    return rows


def _turn_stop_reason(digest: dict) -> str | None:
    envelope = digest.get("selected_envelope")
    if digest.get("consequential_realization_required") and envelope == "narration_only":
        return f"{digest.get('turn')} consequential realization entered narration_only"
    if envelope == "narration_only" and digest.get("accepted_model_authored_declarations"):
        return f"{digest.get('turn')} narration-only path accepted model-authored declarations"
    if digest.get("meaningful_model_generation") and not digest.get("c18_exact_equal"):
        return f"C18 divergence on {digest.get('turn')}"
    if digest.get("authority_problems"):
        return f"unauthorized state/provenance on {digest.get('turn')}: {digest.get('authority_problems')}"
    if digest.get("player_facing_leakage"):
        return f"player-facing metadata leakage on {digest.get('turn')}: {digest.get('player_facing_leakage')}"
    generations = _generation_rows(digest.get("_raw_calls") or [])
    models = {
        str(call.get("response_model") or call.get("model") or "")
        for call in generations
        if call.get("response_model") or call.get("model")
    }
    if models and not all("gpt-4.1-mini" in model for model in models):
        return f"model family mismatch on {digest.get('turn')}: {sorted(models)}"
    return None


def run_turn(client, turn_id: str, player_text: str) -> dict:
    before = bx.snapshot()
    save(f"{turn_id}/state_before.json", before)
    decisions_at = len(bx.DECISIONS)
    calls_at = len(bx.CALLS)
    bx.CURRENT["probe"] = turn_id
    bx.status(f"RUNNING {turn_id}")
    error = None
    payload: dict = {}
    http_status = None
    try:
        response = client.post("/api/chat", json={"text": player_text})
        http_status = response.status_code
        payload = response.json()
    except Exception:
        error = traceback.format_exc()
        payload = {}
    after = bx.snapshot()
    calls = bx.CALLS[calls_at:]
    decisions = bx.DECISIONS[decisions_at:]
    gm = payload.get("gm_output") if isinstance(payload.get("gm_output"), dict) else {}
    meta = gm.get("metadata") if isinstance(gm.get("metadata"), dict) else {}
    review = meta.get("decision_review") if isinstance(meta.get("decision_review"), dict) else {}
    c18 = bx.c18_report(gm)
    problems = bx.authority_problems(before, after)
    generations = _generation_rows(calls)
    parsed = []
    for index, call in enumerate(generations, start=1):
        contract = str(call.get("provider_response_contract") or "structured_realization")
        parsed_row = bx.parse_generation(str(call.get("raw_output") or ""), contract)
        parsed.append(parsed_row)
        save(
            f"{turn_id}/raw_generation_attempt_{index}.json",
            {
                "response_id": call.get("response_id"),
                "model": call.get("response_model") or call.get("model"),
                "usage": call.get("usage"),
                "latency_seconds": call.get("latency_seconds"),
                "input_chars": call.get("input_chars"),
                "recipe_present": call.get("recipe_present"),
                "retry_context_present": call.get("retry_context_present"),
                "provider_response_contract": contract,
                "declared_claims_in_system_prompt": call.get("declared_claims_in_system_prompt"),
                "api_response_schema_present": call.get("api_response_schema_present"),
                "error": call.get("error"),
                "parsed": parsed_row,
            },
        )
    first_decision = decisions[0] if decisions else {}
    recipe = first_decision.get("decision_facing_answer_recipe")
    selected = first_decision.get("envelope_selection") if isinstance(first_decision.get("envelope_selection"), dict) else {}
    save(f"{turn_id}/resolution_contract.json", first_decision.get("contract") or {})
    save(f"{turn_id}/gm_resolution_decision.json", first_decision.get("decision") or {})
    save(f"{turn_id}/decision_facing_answer_recipe.json", recipe or {})
    save(f"{turn_id}/envelope_selection.json", selected)
    save(f"{turn_id}/state_after.json", after)
    save(f"{turn_id}/api_response.json", payload)
    validation = {
        "attempt_1": review.get("attempt_1"),
        "attempt_2": review.get("attempt_2"),
        "retry_context": review.get("retry_context"),
        "acceptance": review.get("acceptance"),
        "hard_validation_attempt_1": meta.get("hard_validation_attempt_1"),
        "hard_validation_attempt_2": meta.get("hard_validation_attempt_2"),
        "regeneration_feedback": meta.get("regeneration_feedback"),
        "regeneration_invoked": meta.get("regeneration_invoked"),
        "provider_response_contract": meta.get("provider_response_contract"),
    }
    save(f"{turn_id}/validation.json", validation)
    save(f"{turn_id}/c18.json", c18)
    accepted_envelope = c18.get("accepted_realization_envelope") or {}
    normalization = {
        "application_realization_envelope": accepted_envelope,
        "parser_attempts": [
            {
                "attempt": index,
                "provider_response_contract": row.get("provider_response_contract"),
                "structural_shape": row.get("structural_shape"),
                "declared_claims": row.get("declared_claims"),
                "normalized_empty_declarations": row.get("normalized_empty_declarations"),
                "declaration_authorship": row.get("declaration_authorship"),
                "structured_contract_failure": row.get("structured_contract_failure"),
                "structured_contract_reason": row.get("structured_contract_reason"),
                "player_facing_text": row.get("player_facing_text"),
            }
            for index, row in enumerate(parsed, start=1)
        ],
    }
    save(f"{turn_id}/normalization.json", normalization)
    upstream = bool(meta.get("upstream_api_error")) if isinstance(meta, dict) else False
    meaningful = any(bool(call.get("meaningful_generation")) for call in generations)
    emitted = c18.get("emitted")
    leakage = bx.player_facing_leakage(emitted if isinstance(emitted, str) else None)
    claims = accepted_envelope.get("declared_claims")
    authored = bool(accepted_envelope.get("declaration_authorship")) or (
        isinstance(claims, list) and any(isinstance(item, dict) and item for item in claims)
    )
    digest = {
        "turn": turn_id,
        "player": player_text,
        "prior_conversational_context": {
            "temporal": before["temporal"],
            "conversation_log_tail": _conversation_tail(),
        },
        "http_status": http_status,
        "error": error,
        "upstream_api_error": meta.get("upstream_api_error") if isinstance(meta, dict) else None,
        "meaningful_model_generation": meaningful and not upstream,
        "emitted": emitted,
        "sealed": c18["sealed"],
        "accepted": c18["accepted"],
        "c18_exact_equal": c18["exact_equal"],
        "c18_mutation_blocked": c18["mutation_blocked"],
        "provenance": c18["provenance"],
        "attempt": c18["attempt"],
        "acceptance": review.get("acceptance"),
        "selected_envelope": selected.get("selected_envelope"),
        "response_operation": selected.get("response_operation"),
        "declaration_expectation": selected.get("declaration_expectation"),
        "consequentiality": selected.get("consequential_realization_required"),
        "consequential_realization_required": selected.get("consequential_realization_required"),
        "declaration_channel_exposed": selected.get("declaration_channel_exposed"),
        "selector_projection_only": selected.get("projection_only"),
        "selector_authority_owner": selected.get("authority_owner"),
        "selector_reason": selected.get("reason"),
        "provider_response_contracts": [str(call.get("provider_response_contract") or "") for call in generations],
        "declared_claims_in_any_generation_system_prompt": any(
            bool(call.get("declared_claims_in_system_prompt")) for call in generations
        ),
        "api_response_schema_present": any(bool(call.get("api_response_schema_present")) for call in generations),
        "normalized_declared_claims": accepted_envelope.get("declared_claims"),
        "normalized_empty_declarations": accepted_envelope.get("normalized_empty_declarations"),
        "declaration_authorship": accepted_envelope.get("declaration_authorship"),
        "accepted_model_authored_declarations": authored,
        "provider_attempts": len(generations),
        "retry": len(generations) > 1 or bool(meta.get("regeneration_invoked")),
        "retry_reasons": validation.get("retry_context"),
        "input_tokens": _token_sum(generations, "input_tokens"),
        "output_tokens": _token_sum(generations, "output_tokens"),
        "total_tokens": _token_sum(generations, "total_tokens"),
        "initial_player_facing_text": (parsed[0].get("player_facing_text") if parsed else None),
        "initial_structural_shape": (parsed[0].get("structural_shape") if parsed else None),
        "initial_declared_claims": (parsed[0].get("declared_claims") if parsed else None),
        "initial_contract_failure": (parsed[0].get("structured_contract_failure") if parsed else None),
        "initial_contract_reason": (parsed[0].get("structured_contract_reason") if parsed else None),
        "retry_player_facing_text": (parsed[1].get("player_facing_text") if len(parsed) > 1 else None),
        "retry_structural_shape": (parsed[1].get("structural_shape") if len(parsed) > 1 else None),
        "retry_declared_claims": (parsed[1].get("declared_claims") if len(parsed) > 1 else None),
        "validation_attempt_1_reasons": (
            (review.get("attempt_1") or {}).get("reasons") if isinstance(review.get("attempt_1"), dict) else None
        ),
        "validation_attempt_2_reasons": (
            (review.get("attempt_2") or {}).get("reasons") if isinstance(review.get("attempt_2"), dict) else None
        ),
        "regeneration_feedback": meta.get("regeneration_feedback"),
        "player_facing_leakage": leakage,
        "authority_problems": problems,
        "temporal_after": after["temporal"],
        "state_changes": {"before": before, "after": after},
        "provenance_changes": {
            "before": before["temporal"],
            "after": after["temporal"],
        },
        "calls": [bx.compact_call(call) for call in calls],
        "_raw_calls": calls,
        "contract_id": (first_decision.get("contract") or {}).get("contract_id")
        if isinstance(first_decision.get("contract"), dict)
        else None,
        "recipe_schema": (recipe or {}).get("schema") if isinstance(recipe, dict) else None,
        "recipe_turn_operation": (recipe or {}).get("turn_operation") if isinstance(recipe, dict) else None,
    }
    digest["stop_reason"] = _turn_stop_reason(digest)
    digest.pop("_raw_calls", None)
    save(f"{turn_id}/digest.json", digest)
    return digest


def _conversation_tail() -> list[dict]:
    path = bx.storage.SESSION_LOG_PATH
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines()[-12:]:
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            rows.append({"raw": line})
    return rows


def main(prelive_only: bool = False) -> int:
    dump_after = os.environ.get("PR_CA_DUMP_AFTER")
    if dump_after:
        import faulthandler

        faulthandler.enable()
        faulthandler.dump_traceback_later(int(dump_after), exit=True)
    OUT.mkdir(parents=True, exist_ok=True)
    prelive = bx.phase0_prelive()
    if not prelive["passed"]:
        bx.status("PHASE0 FAIL " + "; ".join(prelive["failures"]))
        return 3
    bx.status("PHASE0 PASS")
    if prelive_only:
        bx.status("PRELIVE ONLY")
        return 0
    save(
        "run_started.json",
        {
            "utc": datetime.now(timezone.utc).isoformat(),
            "turns": [{"id": turn_id, "player": player} for turn_id, player in TURNS],
            "note": "One persistent isolated baker session; no reset between turns.",
            "phase0_passed": True,
        },
    )
    bx.seed("dialogue_session", "baker")
    completed: list[dict] = []
    halt = None
    bx.status("STARTING")
    client = bx.TestClient(bx.api.app)
    save("preflight.json", bx.preflight.get_latest_upstream_api_preflight())
    for turn_id, player_text in TURNS:
        digest = run_turn(client, turn_id, player_text)
        completed.append(digest)
        save("completed.json", completed)
        if not digest["meaningful_model_generation"]:
            halt = f"infrastructure/provider failure on {turn_id}"
            bx.status(f"HALT {halt}")
            break
        if digest.get("stop_reason"):
            halt = digest["stop_reason"]
            bx.status(f"HALT {halt}")
            break
        bx.status(f"DONE {turn_id}")
    save("full_conversation_log_tail.json", _conversation_tail())
    save(
        "run_finished.json",
        {
            "halt": halt,
            "turns_recorded": [row.get("turn") for row in completed],
            "model_calls": len(bx.CALLS),
            "gameplay_generations": sum(1 for call in bx.CALLS if call.get("kind") == "generation"),
            "utc": datetime.now(timezone.utc).isoformat(),
        },
    )
    bx.status(f"FINISHED halt={halt}")
    return 0 if halt is None else 2


if __name__ == "__main__":
    raise SystemExit(main(prelive_only="--prelive-only" in sys.argv))
