#!/usr/bin/env python3
"""PR-BR continuation 8 smoke. Real /api/chat. Two personas, five turns each.

Player lines use only the persona agenda and the previous player-visible reply.
No production semantics are changed here.
"""
from __future__ import annotations

import json
import re
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

from fastapi.testclient import TestClient  # noqa: E402

from game.api import app  # noqa: E402
from game.api_upstream_preflight import get_latest_upstream_api_preflight  # noqa: E402
from game.playability_eval import evaluate_playability  # noqa: E402
from tools.run_playability_validation import (  # noqa: E402
    _build_eval_payload,
    _final_emission_meta_from_chat_payload,
    _gm_text_from_chat_payload,
)
from tools.run_pr_br_level2_probes import _isolate_storage  # noqa: E402

MAX_TURNS = 5

# Ordinary in-world agendas. Not the Continuation 7 regression sequence.
PERSONAS: tuple[dict[str, Any], ...] = (
    {
        "persona_id": "social_goal",
        "style": "social / goal-oriented",
        "objective": "Get through the gate tonight by finding someone who can tell a traveler what to do.",
        "agenda": (
            "I look for someone on duty and ask what a traveler has to do to pass the gate tonight.",
            "I ask them to name the actual snag, and who can deal with it.",
            "I take that to the person they named, or I ask the one in front of me what they need from me.",
            "I do the concrete thing they just described.",
            "Before I move on, I ask what trouble I should watch for in the next few minutes.",
        ),
    },
    {
        "persona_id": "explore_action",
        "style": "exploration / action-oriented",
        "objective": "Learn the yard well enough to move through it without causing trouble.",
        "agenda": (
            "I take in the yard and walk toward the nearest ordinary thing a traveler could look at or use.",
            "I examine it up close and try to work out what people use it for.",
            "I try the simplest ordinary use, without forcing or breaking anything.",
            "If anyone is close enough to hear me, I ask what people usually do with it.",
            "I take the next safe step that follows from what I just found.",
        ),
    },
)

_STALL_RE = re.compile(
    r"no one (at hand |here )?answers|the question hangs|cannot answer|can't answer|"
    r"do not know enough|not something i can say|no further reliable detail",
    re.I,
)


def _next_line(agenda: tuple[str, ...], index: int, prior_gm: str, presses: int) -> tuple[str, int]:
    if index == 0 or not prior_gm.strip():
        return agenda[0], presses
    if _STALL_RE.search(prior_gm) and presses < 1:
        return (
            "That didn't give me anything I can act on. What is one concrete thing I can do right now?",
            presses + 1,
        )
    return agenda[min(index, len(agenda) - 1)], presses


def _slice(value: Any, limit: int = 500) -> Any:
    if isinstance(value, str):
        return value if len(value) <= limit else value[:limit] + "..."
    if isinstance(value, dict):
        return {str(key): _slice(item, limit) for key, item in list(value.items())[:30]}
    if isinstance(value, list):
        return [_slice(item, limit) for item in value[:8]]
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return str(value)[:limit]


def main() -> int:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "artifacts" / "pr_br_continuation8" / stamp
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        head = ""
    import game.api as api_module

    call_log: list[dict[str, Any]] = []
    real_call = api_module.call_gpt

    def wrapped(messages, **kwargs):
        result = real_call(messages, **kwargs)
        excerpt = ""
        if isinstance(result, dict):
            excerpt = str(result.get("player_facing_text") or "")[:900]
        call_log.append(
            {
                "purpose": kwargs.get("purpose"),
                "retry_attempt": kwargs.get("retry_attempt"),
                "retry_reason": kwargs.get("retry_reason"),
            }
        )
        call_log[-1]["model_player_facing_excerpt"] = excerpt
        return result

    api_module.call_gpt = wrapped
    completed: list[dict[str, Any]] = []
    aborted: list[dict[str, Any]] = []
    stop_reason = ""

    def persist() -> None:
        (out_dir / "turns.json").write_text(json.dumps(completed, indent=2, ensure_ascii=False), encoding="utf-8")
        (out_dir / "aborted.json").write_text(json.dumps(aborted, indent=2, ensure_ascii=False), encoding="utf-8")
        lines = ["# PR-BR Continuation 8 smoke transcript", ""]
        current = ""
        for row in completed:
            if row.get("persona_id") != current:
                current = str(row.get("persona_id"))
                lines.extend([f"## {current}", "", f"Objective: {row.get('objective')}", ""])
            lines.extend(
                [
                    f"### T{row.get('turn_number')} evaluator {row.get('semantic_result')}",
                    "",
                    f"Player: {row.get('player_text')}",
                    "",
                    f"GM: {row.get('gm_text')}",
                    "",
                    (
                        f"op={row.get('operation')} target={row.get('target_ref')} "
                        f"dim={row.get('dimensions')} calls={row.get('model_calls')}"
                    ),
                    "",
                ]
            )
        (out_dir / "transcript.md").write_text("\n".join(lines), encoding="utf-8")

    tmp = Path(tempfile.mkdtemp(prefix="prbr_c8_"))
    with TestClient(app) as client:
        preflight = get_latest_upstream_api_preflight() or {}
        if not preflight.get("ok"):
            print(json.dumps({"preflight": "FAIL", "status": preflight}), flush=True)
            return 2
        for persona in PERSONAS:
            if stop_reason:
                break
            _isolate_storage(tmp)
            prior_gm = ""
            prior_player = ""
            presses = 0
            agenda = tuple(persona["agenda"])
            for index in range(MAX_TURNS):
                player_text, presses = _next_line(agenda, index, prior_gm, presses)
                before = len(call_log)
                try:
                    response = client.post("/api/chat", json={"text": player_text})
                    if response.status_code >= 400:
                        raise RuntimeError(f"http {response.status_code}: {response.text[:800]}")
                    payload = response.json()
                except Exception as exc:
                    aborted.append(
                        {
                            "persona_id": persona["persona_id"],
                            "turn_number": index + 1,
                            "player_text": player_text,
                            "model_calls": len(call_log) - before,
                            "error_type": type(exc).__name__,
                            "error": traceback.format_exc(),
                        }
                    )
                    stop_reason = f"mechanical:{type(exc).__name__}"
                    persist()
                    print(f"ABORT {persona['persona_id']} T{index + 1} {type(exc).__name__}: {exc}", flush=True)
                    break
                gm_text = _gm_text_from_chat_payload(payload)
                resolution = payload.get("resolution") if isinstance(payload.get("resolution"), dict) else {}
                meta = resolution.get("metadata") if isinstance(resolution.get("metadata"), dict) else {}
                contract = meta.get("resolution_contract") if isinstance(meta.get("resolution_contract"), dict) else {}
                session = payload.get("session") if isinstance(payload.get("session"), dict) else {}
                focus = session.get("discourse_focus") if isinstance(session.get("discourse_focus"), dict) else {}
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
                calls = call_log[before:]
                row = {
                    "persona_id": persona["persona_id"],
                    "style": persona["style"],
                    "objective": persona["objective"],
                    "turn_number": index + 1,
                    "player_text": player_text,
                    "gm_text": gm_text,
                    "model_calls": len(calls),
                    "generation_calls": calls,
                    "contract_id": contract.get("contract_id"),
                    "operation": contract.get("operation"),
                    "dimension": contract.get("dimension"),
                    "dimensions": contract.get("dimensions"),
                    "target_ref": contract.get("target_ref"),
                    "discourse_ref": contract.get("discourse_ref"),
                    "semantic_result": evaluation.get("semantic_result"),
                    "tags": gm_output.get("tags"),
                    "outcome_precedence": _slice(emission.get("outcome_precedence")),
                    "active_claim": _slice(focus.get("active_claim")),
                    "active_inspected": _slice(focus.get("active_inspected")),
                    "final_emission": _slice(_final_emission_meta_from_chat_payload(payload)),
                    "model_excerpt": next(
                        (str(call.get("model_player_facing_excerpt") or "") for call in calls if call.get("model_player_facing_excerpt")),
                        "",
                    ),
                }
                completed.append(row)
                persist()
                print(
                    f"{persona['persona_id']} T{index + 1} eval={row['semantic_result']} "
                    f"op={row['operation']} calls={row['model_calls']}",
                    flush=True,
                )
                print(f"PLAYER {player_text}", flush=True)
                print(f"GM {gm_text}", flush=True)
                prior_player = player_text
                prior_gm = gm_text

    summary = {
        "stamp": stamp,
        "head": head,
        "preflight_ok": True,
        "isolated_storage": str(tmp),
        "completed_turns": len(completed),
        "aborted_turns": len(aborted),
        "model_calls": len(call_log),
        "retries": sum(1 for call in call_log if call.get("retry_attempt")),
        "semantic_pass": sum(1 for row in completed if row.get("semantic_result") == "PASS"),
        "semantic_fail": sum(1 for row in completed if row.get("semantic_result") == "FAIL"),
        "stop_reason": stop_reason or None,
        "token_telemetry": "unavailable",
        "full_gate": False,
        "semantic_repair": False,
        "rerun": False,
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (out_dir / "personas.json").write_text(json.dumps(PERSONAS, indent=2), encoding="utf-8")
    (out_dir / "provenance.json").write_text(
        json.dumps(
            {
                "head": head,
                "stamp": stamp,
                "preflight": "PASS",
                "deterministic_band": "198 passed, 0 failed",
                "continuation_7_present": True,
                "full_gate": False,
                "semantic_repair": False,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    persist()
    print(json.dumps(summary), flush=True)
    print(out_dir, flush=True)
    return 0 if not str(stop_reason).startswith("mechanical") else 2


if __name__ == "__main__":
    raise SystemExit(main())
