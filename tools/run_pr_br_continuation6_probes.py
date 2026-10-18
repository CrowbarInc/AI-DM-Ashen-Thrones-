#!/usr/bin/env python3
"""PR-BR continuation 6 focused live. Isolated storage. Maximum 6 completed turns."""
from __future__ import annotations

import json
import sys
import tempfile
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from game.api import app  # noqa: E402
from game.playability_eval import evaluate_playability  # noqa: E402
from game.resolution_contract import semantic_line_view  # noqa: E402
from tools.run_playability_validation import (  # noqa: E402
    _build_eval_payload,
    _final_emission_meta_from_chat_payload,
    _gm_text_from_chat_payload,
)
from tools.run_pr_br_level2_probes import _isolate_storage  # noqa: E402

MAX_COMPLETED = 6
MAX_DESTRUCTIONS = 2


def _scalar_slice(value: Any, limit: int = 280) -> Any:
    if isinstance(value, str):
        return value if len(value) <= limit else value[:limit] + "..."
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        out = {}
        for key, item in list(value.items())[:32]:
            if isinstance(item, (str, int, float, bool)) or item is None:
                out[str(key)] = _scalar_slice(item, limit)
            elif isinstance(item, dict):
                out[str(key)] = _scalar_slice(item, limit)
        return out
    if isinstance(value, list):
        return [_scalar_slice(item, limit) for item in value[:8]]
    return str(value)[:limit]


def _best_model_view(calls: list[dict[str, Any]], resolution: dict[str, Any]) -> dict[str, Any]:
    best: dict[str, Any] = {"status": "absent", "keeps_answer": False, "excerpt": ""}
    for call in calls:
        excerpt = str(call.get("model_player_facing_excerpt") or "")
        if not excerpt.strip():
            continue
        view = semantic_line_view(excerpt, resolution)
        if view.get("keeps_answer") or not best.get("excerpt"):
            best = {**view, "excerpt": excerpt, "purpose": call.get("purpose")}
            if view.get("keeps_answer"):
                break
    return best


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "artifacts" / "pr_br_continuation6" / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="prbr_c6_"))
    import game.api as api_module

    call_log: list[dict[str, Any]] = []
    real_call = api_module.call_gpt

    def wrapped(messages, **kwargs):
        result = real_call(messages, **kwargs)
        excerpt = ""
        if isinstance(result, dict):
            excerpt = str(result.get("player_facing_text") or "")[:700]
        call_log.append(
            {
                "purpose": kwargs.get("purpose"),
                "retry_attempt": kwargs.get("retry_attempt"),
                "retry_reason": kwargs.get("retry_reason"),
                "strict_social": bool(kwargs.get("strict_social")),
                "model_player_facing_excerpt": excerpt,
            }
        )
        return result

    api_module.call_gpt = wrapped
    completed: list[dict[str, Any]] = []
    aborted: list[dict[str, Any]] = []
    stop_reason = ""
    destructions = 0

    def persist() -> None:
        (out_dir / "turns.json").write_text(json.dumps(completed, indent=2, ensure_ascii=False), encoding="utf-8")
        (out_dir / "aborted.json").write_text(json.dumps(aborted, indent=2, ensure_ascii=False), encoding="utf-8")
        lines = ["# PR-BR Continuation 6 focused live transcript", ""]
        for index, row in enumerate(completed, start=1):
            lines.append(f"## T{index} {row.get('probe_id')} — {row.get('semantic_result')}")
            lines.append("")
            lines.append(f"Player: {row.get('player_text')}")
            lines.append("")
            lines.append(f"Model: {row.get('model_excerpt')}")
            lines.append("")
            lines.append(f"GM: {row.get('gm_text')}")
            lines.append("")
            lines.append(
                f"op={row.get('operation')} target={row.get('target_ref')} dim={row.get('dimensions')} "
                f"model={row.get('model_contract_status')} final={row.get('final_contract_status')} "
                f"final_kind={row.get('final_resolution_kind')} preserved={row.get('payload_preserved')} "
                f"destroyed={row.get('semantic_destruction')} calls={row.get('model_calls')}"
            )
            lines.append("")
        for row in aborted:
            lines.append(f"## ABORTED {row.get('probe_id')}")
            lines.append("")
            lines.append(str(row.get("error") or ""))
            lines.append("")
        (out_dir / "transcript.md").write_text("\n".join(lines), encoding="utf-8")

    def play(client: TestClient, probe_id: str, player_text: str) -> dict[str, Any] | None:
        nonlocal stop_reason, destructions
        if len(completed) >= MAX_COMPLETED or stop_reason:
            return None
        before = len(call_log)
        try:
            response = client.post("/api/chat", json={"text": player_text})
            if response.status_code >= 400:
                raise RuntimeError(f"http {response.status_code}: {response.text[:800]}")
            payload = response.json()
        except Exception as exc:
            aborted.append(
                {
                    "probe_id": probe_id,
                    "player_text": player_text,
                    "model_calls": len(call_log) - before,
                    "error_type": type(exc).__name__,
                    "error": traceback.format_exc(),
                }
            )
            stop_reason = f"mechanical:{type(exc).__name__}"
            persist()
            print(f"ABORT {probe_id} {type(exc).__name__}: {exc}", flush=True)
            return None
        gm_text = _gm_text_from_chat_payload(payload)
        resolution = payload.get("resolution") if isinstance(payload.get("resolution"), dict) else {}
        meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
        contract = meta.get("resolution_contract") if isinstance(meta.get("resolution_contract"), dict) else {}
        session = payload.get("session") if isinstance(payload.get("session"), dict) else {}
        focus = session.get("discourse_focus") if isinstance(session.get("discourse_focus"), dict) else {}
        gm_output = payload.get("gm_output") if isinstance(payload.get("gm_output"), dict) else {}
        gm_meta = gm_output.get("metadata") if isinstance(gm_output.get("metadata"), dict) else {}
        emission = gm_meta.get("emission_debug") if isinstance(gm_meta.get("emission_debug"), dict) else {}
        calls = call_log[before:]
        model_view = _best_model_view(calls, resolution)
        final_view = semantic_line_view(gm_text, resolution)
        destroyed = bool(model_view.get("keeps_answer") and not final_view.get("keeps_answer"))
        if destroyed:
            destructions += 1
        evaluation = evaluate_playability(
            _build_eval_payload(
                player_prompt=player_text,
                gm_text=gm_text,
                prior_player="",
                prior_gm="",
                debug_traces=[],
                gm_output=gm_output,
                resolution_contract=dict(contract) if contract else None,
            )
        )
        intent = (evaluation.get("mandatory_gates") or {}).get("player_intent_addressed") or {}
        evidence = (intent.get("evidence") or {}).get("resolution_contract") or {}
        row = {
            "probe_id": probe_id,
            "player_text": player_text,
            "gm_text": gm_text,
            "model_excerpt": model_view.get("excerpt"),
            "model_calls": len(calls),
            "generation_calls": calls,
            "contract_id": contract.get("contract_id"),
            "operation": contract.get("operation"),
            "request_kind": contract.get("request_kind"),
            "dimension": contract.get("dimension"),
            "dimensions": contract.get("dimensions"),
            "referent_provenance": contract.get("referent_provenance"),
            "discourse_ref": contract.get("discourse_ref"),
            "target_ref": contract.get("target_ref"),
            "ambiguous": contract.get("ambiguous"),
            "epistemic_mode": contract.get("epistemic_mode"),
            "model_contract_status": model_view.get("status"),
            "model_resolution_kind": model_view.get("resolution_kind"),
            "model_target_compatible": model_view.get("target_compatible"),
            "model_operation_compatible": model_view.get("operation_compatible"),
            "model_keeps_answer": bool(model_view.get("keeps_answer")),
            "final_contract_status": final_view.get("status"),
            "final_resolution_kind": final_view.get("resolution_kind"),
            "final_reasons": final_view.get("reasons"),
            "final_target_compatible": final_view.get("target_compatible"),
            "final_operation_compatible": final_view.get("operation_compatible"),
            "final_candidate_answer_target": final_view.get("candidate_answer_target"),
            "final_keeps_answer": bool(final_view.get("keeps_answer")),
            "payload_preserved": bool(model_view.get("keeps_answer") and final_view.get("keeps_answer")),
            "semantic_destruction": destroyed,
            "semantic_preservation": _scalar_slice(emission.get("semantic_preservation")),
            "resolution_contract_semantic": _scalar_slice(emission.get("resolution_contract_semantic")),
            "final_emission": _scalar_slice(_final_emission_meta_from_chat_payload(payload)),
            "active_claim": focus.get("active_claim"),
            "active_inspected": focus.get("active_inspected"),
            "assessment": evidence,
            "semantic_result": evaluation.get("semantic_result"),
            "resolution_kind": resolution.get("kind"),
        }
        completed.append(row)
        persist()
        print(
            f"T{len(completed)} {probe_id} eval={row['semantic_result']} op={row['operation']} "
            f"dim={row['dimensions']} model={row['model_contract_status']} final={row['final_contract_status']} "
            f"kind={row['final_resolution_kind']} preserved={row['payload_preserved']} "
            f"destroyed={destroyed} calls={row['model_calls']}",
            flush=True,
        )
        print(f"MODEL {str(row['model_excerpt'])[:400]}", flush=True)
        print(f"GM {str(row['gm_text'])[:480]}", flush=True)
        if destructions >= MAX_DESTRUCTIONS:
            stop_reason = "semantic_destruction_recurred"
        return row

    probes = (
        ("dimensionless_rumor", "What rumor are travelers repeating?"),
        ("repeat_rumor", "Repeat that rumor."),
        ("inspect_sheet", "Look the posted sheet over."),
        ("sheet_content", "What does it actually say?"),
        ("sheet_use", "Does it look like people use this often?"),
    )
    with TestClient(app) as client:
        _isolate_storage(tmp)
        for probe_id, player_text in probes:
            if stop_reason or len(completed) >= MAX_COMPLETED:
                break
            play(client, probe_id, player_text)

    summary = {
        "stamp": stamp,
        "isolated_storage": str(tmp),
        "completed_turns": len(completed),
        "aborted_turns": len(aborted),
        "model_calls": len(call_log),
        "semantic_fail": sum(1 for row in completed if row.get("semantic_result") == "FAIL"),
        "semantic_pass": sum(1 for row in completed if row.get("semantic_result") == "PASS"),
        "semantic_destructions": destructions,
        "payloads_preserved": sum(1 for row in completed if row.get("payload_preserved")),
        "stop_reason": stop_reason or None,
        "token_telemetry": "unavailable",
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    persist()
    print(json.dumps(summary), flush=True)
    print(out_dir, flush=True)
    return 0 if not str(stop_reason).startswith("mechanical") else 2


if __name__ == "__main__":
    raise SystemExit(main())
