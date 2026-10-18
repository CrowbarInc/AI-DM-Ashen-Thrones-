#!/usr/bin/env python3
"""PR-BR continuation 2 focused probes. Isolated storage. Maximum 8 gameplay turns."""
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

REMAINDER: tuple[tuple[str, str], ...] = (
    ("action_request", "Walk me as far as the yard allows toward the notice board."),
    ("perception_smell", "What does the paper on that board smell like?"),
)


PROBES: tuple[tuple[str, str], ...] = (
    ("establish_claim", "I catch the tavern runner and ask what travelers have been saying about the roads."),
    ("claim_source", "Who passed that on to you?"),
    ("claim_confidence", "How sure are you about it?"),
    ("action_request", "If that points somewhere nearby, take me there."),
    ("inspect_board", "I step over to the notice board and look at the paper."),
    ("perception_smell", "This close, what does the paper smell like?"),
)


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "artifacts" / "pr_br_enforcement" / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="prbr_enf_"))
    _isolate_storage(tmp)
    import game.api as api_module

    call_log: list[int] = []
    real_call = api_module.call_gpt

    def wrapped(messages, **kwargs):
        call_log.append(1)
        return real_call(messages, **kwargs)

    api_module.call_gpt = wrapped
    suite = REMAINDER if "--remainder" in sys.argv else PROBES
    turns: list[dict[str, Any]] = []
    with TestClient(app) as client:
        for idx, (probe_id, player_text) in enumerate(suite):
            if len(turns) >= 8:
                break
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
            row = {
                "probe_id": probe_id,
                "player_text": player_text,
                "gm_text": gm_text,
                "model_calls": len(call_log) - before,
                "contract_id": contract.get("contract_id"),
                "operation": contract.get("operation"),
                "request_kind": contract.get("request_kind"),
                "dimension": contract.get("dimension"),
                "referent_provenance": contract.get("referent_provenance"),
                "discourse_ref": contract.get("discourse_ref"),
                "active_claim": focus.get("active_claim"),
                "assessment": evidence,
                "semantic_result": evaluation.get("semantic_result"),
            }
            turns.append(row)
            print(
                f"T{idx + 1} {probe_id} {row['semantic_result']} op={row['operation']} "
                f"dim={row['dimension']} prov={row['referent_provenance']} calls={row['model_calls']}",
                flush=True,
            )
            print(f"CLAIM {row['active_claim']}", flush=True)
            print(f"GM {gm_text[:320]}", flush=True)
            (out_dir / "turns.json").write_text(json.dumps(turns, indent=2, ensure_ascii=False), encoding="utf-8")
    summary = {
        "stamp": stamp,
        "gameplay_turns": len(turns),
        "model_calls": sum(int(t["model_calls"]) for t in turns),
        "semantic_fail": sum(1 for t in turns if t["semantic_result"] == "FAIL"),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary), flush=True)
    print(out_dir, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
