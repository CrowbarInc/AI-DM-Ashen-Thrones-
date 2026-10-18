#!/usr/bin/env python3
"""PR-BR continuation 5 focused live. Isolated storage. Maximum 6 completed turns."""
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
from game.social_exchange_emission import _classify_strict_social_ownership_sentence  # noqa: E402
from tools.run_playability_validation import (  # noqa: E402
    _build_eval_payload,
    _final_emission_meta_from_chat_payload,
    _gm_text_from_chat_payload,
)
from tools.run_pr_br_level2_probes import _isolate_storage  # noqa: E402

MAX_COMPLETED = 6
MAX_DESTRUCTIONS = 2


def _claim_present(row: dict[str, Any] | None) -> bool:
    claim = (row or {}).get("active_claim")
    return isinstance(claim, dict) and bool(claim.get("id"))


def _scalar_slice(value: Any, limit: int = 280) -> Any:
    if isinstance(value, str):
        return value if len(value) <= limit else value[:limit] + "..."
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        out = {}
        for key, item in list(value.items())[:28]:
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
    voiced = 'Tavern Runner says, "Which do you mean? I cannot tell which one that refers to."'
    voiced_class = _classify_strict_social_ownership_sentence(voiced, {"social": {"npc_name": "Tavern Runner"}})
    if voiced_class != "social":
        print(f"PRECHECK_FAIL voiced clarification classified {voiced_class}", flush=True)
        return 3

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "artifacts" / "pr_br_continuation5" / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="prbr_c5_"))
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
    claim_missing = False

    def persist() -> None:
        (out_dir / "turns.json").write_text(json.dumps(completed, indent=2, ensure_ascii=False), encoding="utf-8")
        (out_dir / "aborted.json").write_text(json.dumps(aborted, indent=2, ensure_ascii=False), encoding="utf-8")
        lines = ["# PR-BR Continuation 5 focused live transcript", ""]
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
                f"op={row.get('operation')} dim={row.get('dimension')} "
                f"model_status={row.get('model_contract_status')} final_status={row.get('final_contract_status')} "
                f"preserved={row.get('payload_preserved')} destroyed={row.get('semantic_destruction')} "
                f"calls={row.get('model_calls')}"
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
            "model_keeps_answer": bool(model_view.get("keeps_answer")),
            "final_contract_status": final_view.get("status"),
            "final_keeps_answer": bool(final_view.get("keeps_answer")),
            "final_reasons": final_view.get("reasons"),
            "payload_preserved": bool(model_view.get("keeps_answer") and final_view.get("keeps_answer")),
            "semantic_destruction": destroyed,
            "semantic_preservation": _scalar_slice(emission.get("semantic_preservation")),
            "final_emission": _scalar_slice(_final_emission_meta_from_chat_payload(payload)),
            "active_claim": focus.get("active_claim"),
            "active_inspected": focus.get("active_inspected"),
            "actionable_lead": focus.get("active_actionable_lead"),
            "assessment": evidence,
            "semantic_result": evaluation.get("semantic_result"),
            "resolution_kind": resolution.get("kind"),
        }
        completed.append(row)
        persist()
        print(
            f"T{len(completed)} {probe_id} eval={row['semantic_result']} op={row['operation']} "
            f"dim={row['dimension']} model={row['model_contract_status']} final={row['final_contract_status']} "
            f"preserved={row['payload_preserved']} destroyed={destroyed} calls={row['model_calls']}",
            flush=True,
        )
        print(f"MODEL {str(row['model_excerpt'])[:360]}", flush=True)
        print(f"GM {str(row['gm_text'])[:420]}", flush=True)
        if destructions >= MAX_DESTRUCTIONS:
            stop_reason = "semantic_destruction_recurred"
        return row

    with TestClient(app) as client:
        _isolate_storage(tmp)
        established = play(
            client,
            "claim_attempt",
            "I ask the gate serjeant what rumor the travelers have been repeating.",
        )
        if established and not _claim_present(established) and not stop_reason:
            established = play(
                client,
                "claim_attempt_second",
                "I ask him again to tell me the rumor he just mentioned, in his own words.",
            )
        if not stop_reason and _claim_present(established):
            play(client, "indirect_source", "Who did he hear that from?")
        elif not stop_reason:
            claim_missing = True
        if not str(stop_reason).startswith("mechanical") and stop_reason != "semantic_destruction_recurred":
            if len(completed) < MAX_COMPLETED:
                play(client, "inspect_sheet", "I stop at the posted sheet and look it over.")
            if len(completed) < MAX_COMPLETED and not stop_reason:
                play(client, "inspect_followup", "What does it actually say?")
            if len(completed) < MAX_COMPLETED and not stop_reason:
                lead = completed[-1].get("actionable_lead") if completed else None
                if isinstance(lead, dict) and lead.get("id"):
                    play(client, "referential_action", "I take that step.")
                else:
                    play(client, "true_wear", "Does it look like people use this often?")

    summary = {
        "stamp": stamp,
        "isolated_storage": str(tmp),
        "voiced_clarification_class": voiced_class,
        "completed_turns": len(completed),
        "aborted_turns": len(aborted),
        "model_calls": len(call_log),
        "semantic_fail": sum(1 for row in completed if row.get("semantic_result") == "FAIL"),
        "semantic_destructions": destructions,
        "payloads_preserved": sum(1 for row in completed if row.get("payload_preserved")),
        "active_claim_observed": any(_claim_present(row) for row in completed),
        "claim_missing": claim_missing,
        "stop_reason": stop_reason or None,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    persist()
    print(json.dumps(summary), flush=True)
    print(out_dir, flush=True)
    return 0 if not str(stop_reason).startswith("mechanical") else 2


if __name__ == "__main__":
    raise SystemExit(main())
