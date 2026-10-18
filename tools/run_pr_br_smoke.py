#!/usr/bin/env python3
"""PR-BR Level 3 smoke gate. Isolated storage. Two personas, seven turns each."""
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
        "yard_reader",
        (
            "I walk the gate yard and stop at whatever is posted for travelers to read.",
            "I read that posting closely, especially anything about a patrol or a rule.",
            "Does the paper look recently handled, or has the weather had it for a while?",
            "Standing this close, is there a smell of ink, damp, or smoke on it?",
            "I ask the nearest person on duty what I am supposed to do about that warning.",
            "Where did they get that information?",
            "All right. I will do the next concrete thing they just described.",
        ),
    ),
    (
        "local_talk",
        (
            "I catch the tavern runner between errands and ask what a newcomer should watch for tonight.",
            "That last part — who passed it to you?",
            "Do you actually believe it, or are you just repeating it?",
            "If there is a place I should go because of that, point me at it.",
            "Take me as far as the gate allows toward that place.",
            "Before I commit, what can I see from here that confirms I am heading the right way?",
            "I take that step.",
        ),
    ),
)


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "artifacts" / "pr_br_smoke" / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix="prbr_smoke_"))
    _isolate_storage(tmp)
    runs: list[dict[str, Any]] = []
    with TestClient(app) as client:
        for persona_id, prompts in PERSONAS:
            _isolate_storage(tmp)
            turns: list[dict[str, Any]] = []
            prior_player = ""
            prior_gm = ""
            for idx, player_text in enumerate(prompts):
                payload = client.post("/api/chat", json={"text": player_text}).json()
                gm_text = _gm_text_from_chat_payload(payload)
                resolution = payload.get("resolution") if isinstance(payload.get("resolution"), dict) else {}
                meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
                contract = meta.get("resolution_contract") if isinstance(meta.get("resolution_contract"), dict) else {}
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
                row = {
                    "turn_index": idx,
                    "player_text": player_text,
                    "gm_text": gm_text,
                    "contract_id": contract.get("contract_id"),
                    "operation": contract.get("operation"),
                    "dimension": contract.get("dimension"),
                    "dimensions": contract.get("dimensions"),
                    "referent_provenance": contract.get("referent_provenance"),
                    "target": contract.get("target_ref"),
                    "discourse_ref": contract.get("discourse_ref"),
                    "epistemic_mode": contract.get("epistemic_mode"),
                    "semantic_result": evaluation.get("semantic_result"),
                    "assessment": ((evaluation.get("mandatory_gates") or {}).get("player_intent_addressed") or {}),
                }
                turns.append(row)
                print(
                    f"{persona_id} T{idx + 1} {row['semantic_result']} "
                    f"op={row['operation']} dim={row['dimension']} prov={row['referent_provenance']}",
                    flush=True,
                )
                print(f"GM: {gm_text[:280]}", flush=True)
                prior_player = player_text
                prior_gm = gm_text
            runs.append({"persona_id": persona_id, "turns": turns})
            (out_dir / f"{persona_id}.json").write_text(json.dumps(turns, indent=2, ensure_ascii=False), encoding="utf-8")
    summary = {
        "stamp": stamp,
        "isolated_storage": str(tmp),
        "personas": len(runs),
        "turns": sum(len(run["turns"]) for run in runs),
        "semantic_fail": sum(1 for run in runs for turn in run["turns"] if turn["semantic_result"] == "FAIL"),
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary), flush=True)
    print(out_dir, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
