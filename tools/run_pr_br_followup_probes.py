#!/usr/bin/env python3
"""PR-BR continuation 3 focused live probes. Isolated storage. Maximum 6 turns."""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient  # noqa: E402

from game.api import app  # noqa: E402
from game.playability_eval import evaluate_playability  # noqa: E402
from tools.run_playability_validation import _build_eval_payload, _gm_text_from_chat_payload  # noqa: E402
from tools.run_pr_br_level2_probes import _isolate_storage  # noqa: E402

MAX_TURNS = 6


def _turn(client: TestClient, call_log: list[int], probe_id: str, player_text: str) -> dict[str, Any]:
    before = len(call_log)
    payload = client.post("/api/chat", json={"text": player_text}).json()
    gm_text = _gm_text_from_chat_payload(payload)
    resolution = payload.get("resolution") if isinstance(payload.get("resolution"), dict) else {}
    meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
    contract = meta.get("resolution_contract") if isinstance(meta.get("resolution_contract"), dict) else {}
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
    return {
        "probe_id": probe_id,
        "player_text": player_text,
        "gm_text": gm_text,
        "model_calls": len(call_log) - before,
        "contract_id": contract.get("contract_id"),
        "operation": contract.get("operation"),
        "request_kind": contract.get("request_kind"),
        "dimension": contract.get("dimension"),
        "dimensions": contract.get("dimensions"),
        "referent_provenance": contract.get("referent_provenance"),
        "discourse_ref": contract.get("discourse_ref"),
        "construction": contract.get("construction"),
        "ambiguous": contract.get("ambiguous"),
        "active_claim": focus.get("active_claim"),
        "claim_truth_status": entries[-1].get("truth_status") if entries else None,
        "assessment": evidence,
        "semantic_result": evaluation.get("semantic_result"),
    }


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "artifacts" / "pr_br_followup" / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="prbr_followup_"))
    import game.api as api_module

    call_log: list[int] = []
    real_call = api_module.call_gpt

    def wrapped(messages, **kwargs):
        call_log.append(1)
        return real_call(messages, **kwargs)

    api_module.call_gpt = wrapped
    turns: list[dict[str, Any]] = []
    stop_reason = ""

    def play(client: TestClient, probe_id: str, player_text: str) -> dict[str, Any] | None:
        if len(turns) >= MAX_TURNS:
            return None
        row = _turn(client, call_log, probe_id, player_text)
        turns.append(row)
        print(
            f"T{len(turns)} {probe_id} {row['semantic_result']} op={row['operation']} "
            f"kind={row['request_kind']} dim={row['dimension']} prov={row['referent_provenance']} "
            f"calls={row['model_calls']}",
            flush=True,
        )
        print(f"CLAIM {row['active_claim']}", flush=True)
        print(f"GM {str(row['gm_text'])[:360]}", flush=True)
        (out_dir / "turns.json").write_text(json.dumps(turns, indent=2, ensure_ascii=False), encoding="utf-8")
        return row

    with TestClient(app) as client:
        _isolate_storage(tmp)
        established = play(
            client,
            "establish_claim",
            "I catch the tavern runner and ask what rumors travelers are repeating about the roads.",
        )
        claim = (established or {}).get("active_claim") if established else None
        if not claim:
            stop_reason = "no_emitted_claim"
        else:
            source = play(client, "indirect_source", "Who did he hear that from?")
            if not source or source.get("dimension") != "source":
                stop_reason = "source_not_recognized"
            else:
                confidence = play(client, "indirect_confidence", "Does he trust the story?")
                if not confidence or confidence.get("dimension") != "confidence":
                    stop_reason = "confidence_not_recognized"
        # Wear is a separate planned sequence. Skip it only after a recognition failure.
        if stop_reason in {"", "no_emitted_claim"} and len(turns) < MAX_TURNS:
            _isolate_storage(tmp)
            play(client, "inspect_object", "I stop at the posted sheet and look it over.")
            if len(turns) < MAX_TURNS and not stop_reason:
                wear = play(client, "wear_use", "Does it look like people have handled it recently?")
                if wear and "wear" not in (wear.get("dimensions") or []) and "use" not in (wear.get("dimensions") or []):
                    stop_reason = "wear_not_recognized"

    summary = {
        "stamp": stamp,
        "gameplay_turns": len(turns),
        "model_calls": sum(int(row["model_calls"]) for row in turns),
        "semantic_fail": sum(1 for row in turns if row["semantic_result"] == "FAIL"),
        "stop_reason": stop_reason or None,
        "healthy": not stop_reason,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary), flush=True)
    print(out_dir, flush=True)
    return 0 if not stop_reason else 2


if __name__ == "__main__":
    raise SystemExit(main())
