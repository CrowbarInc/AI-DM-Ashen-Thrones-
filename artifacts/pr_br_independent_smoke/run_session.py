#!/usr/bin/env python3
"""Independent PR-BR 10-turn smoke. Validation harness only. No product changes.

One isolated frontier-gate session. Opening via POST /api/start_campaign.
Each gameplay turn is POST /api/chat. Player lines arrive on inbox.jsonl
after the previous player-visible reply. Does not stop on semantic failure.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.pop("ASHEN_DISABLE_LIVE_INTERPRETATION", None)

from fastapi.testclient import TestClient  # noqa: E402

from game import storage  # noqa: E402
from game.api import app  # noqa: E402
from game.api_upstream_preflight import get_latest_upstream_api_preflight  # noqa: E402
from game.defaults import default_campaign, default_character, default_combat, default_conditions  # noqa: E402
from game.playability_eval import evaluate_playability  # noqa: E402
from game.resolution_contract import (  # noqa: E402
    detect_semantic_degradation,
    resolution_coverage,
    semantic_line_view,
)
from tests.helpers.golden_replay_fixtures import seed_frontier_gate_world  # noqa: E402
from tests.helpers.turn_pipeline_http_fixtures import _write_campaign_start_scene_files  # noqa: E402
from tools.run_playability_validation import (  # noqa: E402
    _build_eval_payload,
    _gm_text_from_chat_payload,
)

MAX_TURNS = 10
STAMP = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
OUT = ROOT / "artifacts" / "pr_br_independent_smoke" / STAMP
INBOX = OUT / "inbox.jsonl"


def _isolate_storage(tmp: Path) -> None:
    storage.BASE_DIR = tmp
    storage.DATA_DIR = tmp / "data"
    storage.WORLD_PATH = storage.DATA_DIR / "world.json"
    storage.SCENES_DIR = storage.DATA_DIR / "scenes"
    storage.CHARACTER_PATH = storage.DATA_DIR / "character.json"
    storage.CAMPAIGN_PATH = storage.DATA_DIR / "campaign.json"
    storage.SESSION_PATH = storage.DATA_DIR / "session.json"
    storage.COMBAT_PATH = storage.DATA_DIR / "combat.json"
    storage.CONDITIONS_PATH = storage.DATA_DIR / "conditions.json"
    storage.SESSION_LOG_PATH = storage.DATA_DIR / "session_log.jsonl"
    storage.DATA_DIR.mkdir(parents=True, exist_ok=True)
    storage.SCENES_DIR.mkdir(parents=True, exist_ok=True)
    storage._save_json(storage.CAMPAIGN_PATH, default_campaign())
    storage._save_json(storage.CHARACTER_PATH, default_character())
    storage._save_json(storage.COMBAT_PATH, default_combat())
    storage._save_json(storage.CONDITIONS_PATH, default_conditions())
    if storage.SESSION_PATH.exists():
        storage.SESSION_PATH.unlink()
    storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")
    _write_campaign_start_scene_files()
    seed_frontier_gate_world()


def _git(args: list[str]) -> str:
    try:
        return subprocess.check_output(["git", *args], cwd=ROOT, text=True, stderr=subprocess.STDOUT).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        return str(exc)


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


def _read_inbox() -> list[dict[str, Any]]:
    if not INBOX.exists():
        return []
    rows = []
    for line in INBOX.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _status(text: str) -> None:
    (OUT / "status.txt").write_text(text + "\n", encoding="utf-8")
    print(text, flush=True)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "turns").mkdir(exist_ok=True)
    INBOX.write_text("", encoding="utf-8")
    head = _git(["rev-parse", "HEAD"])
    preflight = {
        "stamp": STAMP,
        "head": head,
        "head_subject": _git(["log", "-1", "--format=%s"]),
        "isolated_storage": True,
        "product_path": ["/api/start_campaign", "/api/chat"],
        "max_gameplay_turns": MAX_TURNS,
        "semantic_repair_applied": False,
        "player_fed_regression_internals": False,
        "c15_modules": {
            "resolution_contract": (ROOT / "game" / "resolution_contract.py").exists(),
            "discourse_state": (ROOT / "game" / "discourse_state.py").exists(),
            "semantic_interpreter": (ROOT / "game" / "semantic_interpreter.py").exists(),
            "interpretation_proposal": (ROOT / "game" / "interpretation_proposal.py").exists(),
        },
    }
    (OUT / "preflight.json").write_text(json.dumps(preflight, indent=2), encoding="utf-8")

    import game.api as api_module
    import game.semantic_interpreter as interpreter_module

    generation_log: list[dict[str, Any]] = []
    interpretation_log: list[dict[str, Any]] = []
    real_call = api_module.call_gpt
    real_invoke = interpreter_module._invoke_interpretation_model

    def wrapped_generation(messages, **kwargs):
        result = real_call(messages, **kwargs)
        excerpt = ""
        model_name = ""
        if isinstance(result, dict):
            excerpt = str(result.get("player_facing_text") or "")
            model_name = str(result.get("model") or result.get("selected_model") or "")
        generation_log.append(
            {
                "purpose": kwargs.get("purpose"),
                "retry_attempt": kwargs.get("retry_attempt"),
                "retry_reason": kwargs.get("retry_reason"),
                "model": model_name,
                "model_player_facing_text": excerpt,
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
        interpretation_log[-1]["output_text"] = str(text)
        return text

    api_module.call_gpt = wrapped_generation
    interpreter_module._invoke_interpretation_model = wrapped_interpretation

    isolated = OUT / "isolated_data"
    _isolate_storage(isolated)
    session_meta = {}
    try:
        session_meta = {
            "campaign_run_id": storage.load_session().get("campaign_run_id"),
            "session_id": storage.load_session().get("session_id"),
            "active_scene_id": storage.load_session().get("active_scene_id"),
            "log_empty": storage.SESSION_LOG_PATH.read_text(encoding="utf-8").strip() == "",
            "character": storage.load_character().get("name"),
        }
    except Exception as exc:
        session_meta = {"error": str(exc)}
    preflight["session_after_isolate"] = session_meta
    (OUT / "preflight.json").write_text(json.dumps(preflight, indent=2), encoding="utf-8")

    completed: list[dict[str, Any]] = []
    visible_lines = ["# Player-visible transcript", ""]

    def persist() -> None:
        (OUT / "turns.json").write_text(json.dumps(completed, indent=2, ensure_ascii=False), encoding="utf-8")
        (OUT / "generation_calls.json").write_text(json.dumps(generation_log, indent=2, ensure_ascii=False), encoding="utf-8")
        (OUT / "interpretation_calls.json").write_text(
            json.dumps(interpretation_log, indent=2, ensure_ascii=False), encoding="utf-8"
        )
        (OUT / "visible.md").write_text("\n".join(visible_lines) + "\n", encoding="utf-8")

    with TestClient(app) as client:
        upstream = get_latest_upstream_api_preflight() or {}
        preflight["upstream_ok"] = bool(upstream.get("ok"))
        preflight["upstream_status"] = {k: upstream.get(k) for k in ("ok", "status", "error", "model") if k in upstream}
        (OUT / "preflight.json").write_text(json.dumps(preflight, indent=2), encoding="utf-8")
        if not upstream.get("ok"):
            _status("PREFLIGHT_FAIL")
            return 2

        gen_before = len(generation_log)
        opening_resp = client.post("/api/start_campaign")
        if opening_resp.status_code >= 400:
            (OUT / "opening_error.txt").write_text(opening_resp.text[:4000], encoding="utf-8")
            _status(f"OPENING_HTTP_{opening_resp.status_code}")
            return 2
        opening_payload = opening_resp.json()
        opening_text = _gm_text_from_chat_payload(opening_payload)
        (OUT / "opening.json").write_text(
            json.dumps(
                {
                    "gm_text": opening_text,
                    "ok": opening_payload.get("ok"),
                    "generation_calls": generation_log[gen_before:],
                },
                indent=2,
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        visible_lines.extend(["## Opening", "", opening_text, ""])
        persist()
        _status("OPENING_READY")

        prior_player = ""
        prior_gm = opening_text
        processed = 0
        while len(completed) < MAX_TURNS:
            rows = _read_inbox()
            if processed >= len(rows):
                time.sleep(0.4)
                continue
            spec = rows[processed]
            processed += 1
            if spec.get("stop"):
                _status("STOP_REQUESTED")
                break
            player_text = str(spec.get("text") or "").strip()
            if not player_text:
                continue
            gen_before = len(generation_log)
            interp_before = len(interpretation_log)
            try:
                response = client.post("/api/chat", json={"text": player_text})
                if response.status_code >= 400:
                    raise RuntimeError(f"http {response.status_code}: {response.text[:800]}")
                payload = response.json()
            except Exception:
                (OUT / "abort.txt").write_text(traceback.format_exc(), encoding="utf-8")
                _status(f"ABORT_TURN_{len(completed) + 1}")
                persist()
                return 2

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
                excerpt = str(call.get("model_player_facing_text") or "").strip()
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
            authority = gm_output.get("bounded_improvisation_authority")
            ledger = session.get("bounded_improvisation") if isinstance(session.get("bounded_improvisation"), dict) else {}
            gates = evaluation.get("mandatory_gates") if isinstance(evaluation.get("mandatory_gates"), dict) else {}
            failing_gates = [
                name
                for name, gate in gates.items()
                if isinstance(gate, dict) and gate.get("status") == "FAIL"
            ]
            row = {
                "turn_number": len(completed) + 1,
                "player_text": player_text,
                "visible_motivation": spec.get("motivation"),
                "intended_meaning": spec.get("intended"),
                "generated_candidate": generated,
                "gm_text": gm_text,
                "gm_tags": gm_output.get("tags"),
                "best_safe_candidate": best,
                "final_selected_candidate": final_selected,
                "best_candidate_emitted": best_emitted,
                "best_safe_invalidation": emission.get("best_safe_invalidation"),
                "satisfied_candidate": str(emission.get("satisfied_candidate") or ""),
                "initial_safe_candidate": str(emission.get("initial_safe_candidate") or ""),
                "candidate_transitions": emission.get("candidate_transitions") or [],
                "outcome_precedence": emission.get("outcome_precedence"),
                "telemetry_semantic_degradation": emission.get("semantic_degradation"),
                "telemetry_semantic_degradation_reasons": emission.get("semantic_degradation_reasons"),
                "initial_satisfaction": _view_brief(initial_view),
                "final_satisfaction": _view_brief(final_view),
                "initial_coverage": _coverage_brief(initial_coverage),
                "final_coverage": _coverage_brief(final_coverage),
                "detector_semantic_degradation": bool(degradation.get("degraded")),
                "detector_semantic_degradation_reasons": list(degradation.get("reasons") or []),
                "fast_path_used": construction.get("fast_path_used"),
                "semantic_completeness": construction.get("semantic_completeness"),
                "fast_path_abstained": construction.get("fast_path_abstained"),
                "abstention_reason": construction.get("fast_path_abstention_reason"),
                "interpreter_invoked": construction.get("model_interpreter_invoked"),
                "proposal_source": construction.get("proposal_source"),
                "validation_status": construction.get("validation_status"),
                "validator_reason": construction.get("abstention_reason"),
                "interpretation_proposal": proposal,
                "operation": contract.get("operation"),
                "canonical_target": target.get("id_or_text"),
                "target_ref": target,
                "discourse_ref": contract.get("discourse_ref"),
                "interlocutor_id": contract.get("interlocutor_id"),
                "conversational_subject": contract.get("conversational_subject"),
                "dimension": contract.get("dimension"),
                "dimensions": contract.get("dimensions"),
                "expected_resolution": contract.get("expected_resolution"),
                "ambiguous": contract.get("ambiguous"),
                "contract_id": contract.get("contract_id"),
                "contract": contract,
                "active_interlocutor": _slot(focus, "active_interlocutor"),
                "active_claim": _slot(focus, "active_claim"),
                "active_inspected": _slot(focus, "active_inspected"),
                "actionable_lead": _slot(focus, "active_actionable_lead"),
                "previous_action": _slot(focus, "last_attempted_action"),
                "discourse_focus": focus,
                "authority": authority,
                "bounded_ledger_tail": {
                    "entries": (ledger.get("entries") or [])[-4:],
                    "rejected": (ledger.get("rejected") or [])[-4:],
                },
                "semantic_result": evaluation.get("semantic_result"),
                "failing_gates": failing_gates,
                "evaluation": evaluation,
                "generation_calls_this_turn": len(generation_log) - gen_before,
                "interpretation_calls_this_turn": len(interpretation_log) - interp_before,
                "turn_generation_calls": turn_generations,
                "turn_interpretation_calls": interpretation_log[interp_before:],
                "resolution_kind": resolution.get("kind"),
                "api_ok": payload.get("ok"),
            }
            completed.append(row)
            (OUT / "turns" / f"turn_{row['turn_number']:02d}.json").write_text(
                json.dumps(row, indent=2, ensure_ascii=False), encoding="utf-8"
            )
            visible_lines.extend(
                [
                    f"## Turn {row['turn_number']}",
                    "",
                    f"Player: {player_text}",
                    "",
                    f"GM: {gm_text}",
                    "",
                ]
            )
            persist()
            prior_player = player_text
            prior_gm = gm_text
            _status(f"TURN_READY {row['turn_number']}")

    summary = {
        "stamp": STAMP,
        "head": head,
        "completed_turns": len(completed),
        "generation_calls": len(generation_log),
        "interpretation_calls": len(interpretation_log),
        "retries": sum(1 for call in generation_log if int(call.get("retry_attempt") or 0) > 0),
        "evaluator_model_calls": 0,
        "semantic_repair": False,
        "rerun": False,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    _status("SESSION_COMPLETE")
    print(str(OUT), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
