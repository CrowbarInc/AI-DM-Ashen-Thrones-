#!/usr/bin/env python3
"""One PR-BR continuation smoke gate. Two personas, six turns. Isolated storage."""
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

PERSONAS: tuple[tuple[str, tuple[str, ...]], ...] = (
    (
        "road_talk",
        (
            "I greet the tavern runner and ask what a newcomer should watch for on the road.",
            "Who did he hear that from?",
            "Does he trust it, or is it only talk?",
            "Walk me toward the notice board, if you can leave your spot.",
            "If you have to stay, tell me the condition that would let you go.",
            "Give me one plain thing you are willing to say before I move on.",
        ),
    ),
    (
        "yard_look",
        (
            "I look over the yard for whatever is posted for travelers.",
            "I read the uppermost notice.",
            "Does the sheet look recently handled?",
            "Up close, what does the sheet smell like?",
            "I ask the nearest guard to point me toward a safe next step inside the yard.",
            "I take that step, staying inside the yard.",
        ),
    ),
)


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "artifacts" / "pr_br_enforcement_smoke" / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="prbr_enf_smoke_"))
    import game.api as api_module

    call_log: list[int] = []
    real_call = api_module.call_gpt

    def wrapped(messages, **kwargs):
        call_log.append(1)
        return real_call(messages, **kwargs)

    api_module.call_gpt = wrapped
    runs: list[dict[str, Any]] = []
    with TestClient(app) as client:
        for persona_id, prompts in PERSONAS:
            _isolate_storage(tmp)
            turns: list[dict[str, Any]] = []
            for idx, player_text in enumerate(prompts):
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
                row = {
                    "turn_index": idx,
                    "player_text": player_text,
                    "gm_text": gm_text,
                    "model_calls": len(call_log) - before,
                    "operation": contract.get("operation"),
                    "dimension": contract.get("dimension"),
                    "referent_provenance": contract.get("referent_provenance"),
                    "discourse_ref": contract.get("discourse_ref"),
                    "active_claim": focus.get("active_claim"),
                    "assessment": (intent.get("evidence") or {}).get("resolution_contract"),
                    "semantic_result": evaluation.get("semantic_result"),
                }
                turns.append(row)
                print(
                    f"{persona_id} T{idx + 1} {row['semantic_result']} op={row['operation']} "
                    f"dim={row['dimension']} prov={row['referent_provenance']} calls={row['model_calls']}",
                    flush=True,
                )
                print(f"GM {gm_text[:260]}", flush=True)
            runs.append({"persona_id": persona_id, "turns": turns})
            (out_dir / f"{persona_id}.json").write_text(json.dumps(turns, indent=2, ensure_ascii=False), encoding="utf-8")
    summary = {
        "stamp": stamp,
        "turns": sum(len(run["turns"]) for run in runs),
        "model_calls": sum(t["model_calls"] for run in runs for t in run["turns"]),
        "semantic_fail": sum(1 for run in runs for t in run["turns"] if t["semantic_result"] == "FAIL"),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary), flush=True)
    print(out_dir, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
