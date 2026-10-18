#!/usr/bin/env python3
"""PR-BR continuation 4 focused live resume. Isolated storage. Maximum 6 completed turns."""
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
from game.social_exchange_emission import _classify_strict_social_ownership_sentence  # noqa: E402
from game.social_exchange_fallback_catalog import (  # noqa: E402
    lawful_strict_social_dialogue_emergency_fallback_line,
    minimal_social_emergency_fallback_line,
    strict_social_ownership_terminal_fallback,
)
from tools.run_playability_validation import (  # noqa: E402
    _build_eval_payload,
    _final_emission_meta_from_chat_payload,
    _gm_text_from_chat_payload,
)
from tools.run_pr_br_level2_probes import _isolate_storage  # noqa: E402

MAX_COMPLETED = 6

CLAIM_ATTEMPTS = (
    (
        "claim_attempt_runner",
        "I stop beside the tavern runner and ask what rumor they have been calling out to the yard.",
    ),
    (
        "claim_attempt_serjeant",
        "I leave the runner and ask the gate serjeant what travelers have been repeating as they come through.",
    ),
)


def _claim_present(row: dict[str, Any] | None) -> bool:
    claim = (row or {}).get("active_claim")
    return isinstance(claim, dict) and bool(claim.get("id"))


def _is_catalog_fallback(text: str, resolution: dict[str, Any]) -> list[str]:
    visible = str(text or "").strip()
    hits: list[str] = []
    for name, factory in (
        ("minimal_social_emergency", minimal_social_emergency_fallback_line),
        ("lawful_strict_social_emergency", lawful_strict_social_dialogue_emergency_fallback_line),
        ("ownership_terminal", strict_social_ownership_terminal_fallback),
    ):
        try:
            if factory(resolution).strip() == visible:
                hits.append(name)
        except Exception:
            continue
    return hits


def _scalar_slice(value: Any, limit: int = 240) -> Any:
    if isinstance(value, str):
        return value if len(value) <= limit else value[:limit] + "..."
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    if isinstance(value, dict):
        out = {}
        for key, item in list(value.items())[:24]:
            if isinstance(item, (str, int, float, bool)) or item is None:
                out[str(key)] = _scalar_slice(item, limit)
            elif isinstance(item, dict):
                out[str(key)] = _scalar_slice(item, limit)
        return out
    if isinstance(value, list):
        return [_scalar_slice(item, limit) for item in value[:8]]
    return str(value)[:limit]


def main() -> int:
    voiced = 'Tavern Runner says, "Which do you mean? I cannot tell which one that refers to."'
    voiced_class = _classify_strict_social_ownership_sentence(voiced, {"social": {"npc_name": "Tavern Runner"}})
    if voiced_class != "social":
        print(f"PRECHECK_FAIL voiced clarification classified {voiced_class}", flush=True)
        return 3

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "artifacts" / "pr_br_continuation4" / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="prbr_c4_"))
    import game.api as api_module

    call_log: list[dict[str, Any]] = []
    real_call = api_module.call_gpt

    def wrapped(messages, **kwargs):
        result = real_call(messages, **kwargs)
        excerpt = ""
        proposals = 0
        if isinstance(result, dict):
            excerpt = str(result.get("player_facing_text") or "")[:500]
            raw_proposals = result.get("bounded_improvisation_proposals")
            if isinstance(raw_proposals, list):
                proposals = len(raw_proposals)
        call_log.append(
            {
                "purpose": kwargs.get("purpose"),
                "retry_attempt": kwargs.get("retry_attempt"),
                "retry_reason": kwargs.get("retry_reason"),
                "strict_social": bool(kwargs.get("strict_social")),
                "model_player_facing_excerpt": excerpt,
                "proposal_count": proposals,
            }
        )
        return result

    api_module.call_gpt = wrapped
    completed: list[dict[str, Any]] = []
    aborted: list[dict[str, Any]] = []
    stop_reason = ""

    def persist() -> None:
        (out_dir / "turns.json").write_text(json.dumps(completed, indent=2, ensure_ascii=False), encoding="utf-8")
        (out_dir / "aborted.json").write_text(json.dumps(aborted, indent=2, ensure_ascii=False), encoding="utf-8")
        lines = ["# PR-BR Continuation 4 focused live transcript", ""]
        for index, row in enumerate(completed, start=1):
            lines.append(f"## T{index} {row.get('probe_id')} — {row.get('semantic_result')}")
            lines.append("")
            lines.append(f"Player: {row.get('player_text')}")
            lines.append("")
            lines.append(f"GM: {row.get('gm_text')}")
            lines.append("")
            lines.append(
                f"op={row.get('operation')} kind={row.get('request_kind')} dim={row.get('dimension')} "
                f"dims={row.get('dimensions')} prov={row.get('referent_provenance')} "
                f"calls={row.get('model_calls')} fallback={row.get('catalog_fallback')}"
            )
            lines.append("")
        for row in aborted:
            lines.append(f"## ABORTED {row.get('probe_id')}")
            lines.append("")
            lines.append(f"Player: {row.get('player_text')}")
            lines.append("")
            lines.append("```")
            lines.append(str(row.get("error") or ""))
            lines.append("```")
            lines.append("")
        (out_dir / "transcript.md").write_text("\n".join(lines), encoding="utf-8")

    def play(client: TestClient, probe_id: str, player_text: str) -> dict[str, Any] | None:
        nonlocal stop_reason
        if len(completed) >= MAX_COMPLETED:
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
        obligation = meta.get("interaction_obligation") if isinstance(meta.get("interaction_obligation"), dict) else {}
        session = payload.get("session") if isinstance(payload.get("session"), dict) else {}
        focus = session.get("discourse_focus") if isinstance(session.get("discourse_focus"), dict) else {}
        gm_output = payload.get("gm_output") if isinstance(payload.get("gm_output"), dict) else {}
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
        ledger = session.get("bounded_improvisation") if isinstance(session.get("bounded_improvisation"), dict) else {}
        entries = [row for row in (ledger.get("entries") or []) if isinstance(row, dict) and row.get("kind") == "npc_claim"]
        calls = call_log[before:]
        row = {
            "probe_id": probe_id,
            "player_text": player_text,
            "gm_text": gm_text,
            "model_calls": len(calls),
            "generation_calls": calls,
            "contract": contract,
            "contract_id": contract.get("contract_id"),
            "operation": contract.get("operation"),
            "request_kind": contract.get("request_kind"),
            "dimension": contract.get("dimension"),
            "dimensions": contract.get("dimensions"),
            "referent_provenance": contract.get("referent_provenance"),
            "discourse_ref": contract.get("discourse_ref"),
            "target_ref": contract.get("target_ref"),
            "construction": contract.get("construction"),
            "ambiguous": contract.get("ambiguous"),
            "expected_resolution": contract.get("expected_resolution"),
            "epistemic_mode": contract.get("epistemic_mode"),
            "obligation": _scalar_slice(obligation),
            "live_resolution_mode": _scalar_slice(meta.get("live_resolution_mode")),
            "final_emission": _scalar_slice(_final_emission_meta_from_chat_payload(payload)),
            "discourse_focus": _scalar_slice(focus),
            "active_claim": focus.get("active_claim"),
            "actionable_lead": focus.get("active_actionable_lead"),
            "active_inspected": focus.get("active_inspected"),
            "claim_ledger_tail": _scalar_slice(entries[-1] if entries else None),
            "catalog_fallback": _is_catalog_fallback(gm_text, resolution),
            "assessment": evidence,
            "semantic_result": evaluation.get("semantic_result"),
            "resolution_kind": resolution.get("kind"),
        }
        completed.append(row)
        persist()
        print(
            f"T{len(completed)} {probe_id} {row['semantic_result']} op={row['operation']} "
            f"kind={row['request_kind']} dim={row['dimension']} dims={row['dimensions']} "
            f"prov={row['referent_provenance']} calls={row['model_calls']} fallback={row['catalog_fallback']}",
            flush=True,
        )
        print(f"CLAIM {row['active_claim']}", flush=True)
        print(f"GM {str(row['gm_text'])[:420]}", flush=True)
        return row

    with TestClient(app) as client:
        _isolate_storage(tmp)
        established = None
        for probe_id, player_text in CLAIM_ATTEMPTS:
            if stop_reason or len(completed) >= MAX_COMPLETED:
                break
            established = play(client, probe_id, player_text)
            if established is None or _claim_present(established):
                break
        if not stop_reason and _claim_present(established):
            source = play(client, "indirect_source", "Who did he hear that from?")
            if source and source.get("dimension") != "source":
                stop_reason = stop_reason or "source_not_recognized"
            if not stop_reason and len(completed) < MAX_COMPLETED:
                confidence = play(client, "indirect_confidence", "Does he trust the story?")
                if confidence and confidence.get("dimension") != "confidence":
                    stop_reason = stop_reason or "confidence_not_recognized"
        elif not stop_reason:
            stop_reason = stop_reason or "no_emitted_claim"
        if not stop_reason.startswith("mechanical") and len(completed) < MAX_COMPLETED:
            inspected = play(client, "inspect_object", "I stop at the posted sheet and look it over.")
            if inspected and inspected.get("ambiguous"):
                stop_reason = stop_reason or "inspect_ambiguous"
        if not str(stop_reason).startswith("mechanical") and len(completed) < MAX_COMPLETED:
            wear = play(client, "wear_use", "Does it look like people have handled it recently?")
            dims = set((wear or {}).get("dimensions") or [])
            if wear and not (dims & {"wear", "use", "change"}):
                stop_reason = stop_reason or "wear_not_recognized"
        lead = None
        if completed:
            lead = completed[-1].get("actionable_lead")
        if (
            not str(stop_reason).startswith("mechanical")
            and isinstance(lead, dict)
            and lead.get("id")
            and len(completed) < MAX_COMPLETED
        ):
            action = play(client, "referential_action", "I take that step.")
            if action and action.get("request_kind") != "action":
                stop_reason = stop_reason or "action_not_recognized"

    summary = {
        "stamp": stamp,
        "isolated_storage": str(tmp),
        "voiced_clarification_class": voiced_class,
        "completed_turns": len(completed),
        "aborted_turns": len(aborted),
        "model_calls": len(call_log),
        "semantic_fail": sum(1 for row in completed if row.get("semantic_result") == "FAIL"),
        "active_claim_observed": any(_claim_present(row) for row in completed),
        "stop_reason": stop_reason or None,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    persist()
    print(json.dumps(summary), flush=True)
    print(out_dir, flush=True)
    return 0 if not str(stop_reason).startswith("mechanical") else 2


if __name__ == "__main__":
    raise SystemExit(main())
