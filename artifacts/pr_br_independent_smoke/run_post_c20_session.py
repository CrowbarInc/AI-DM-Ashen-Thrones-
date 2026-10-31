#!/usr/bin/env python3
"""Independent 10-turn smoke after Continuation 20. Validation harness only.

No product behavior change. One isolated session. Opening via POST /api/start_campaign.
Each gameplay turn is POST /api/chat. Player lines arrive on inbox.jsonl after the
previous player-visible reply. Does not stop on a mediocre or questionable turn.
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
from game.immutable_valid_response import semantic_equal  # noqa: E402
from game.playability_eval import evaluate_playability  # noqa: E402
from game.proposition_authority import classify_propositions, unauthorized_authoritative_rules  # noqa: E402
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

PERSONA = """Galinor, a level-1 wandering wizard who has just reached a frontier gate in bad weather.
He wants to understand the situation in front of him, get useful information, and make ordinary progress: food, shelter, passage, or whatever the people and place actually offer.
He talks to people who are present, looks at things that catch his eye, follows up on what they say, and changes approach when someone stops helping.
He knows only the opening narration, later player-visible replies, and that he is Galinor arriving at this gate.
He does not know internal contracts, validators, authority labels, or any prior session.
"""


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
    return {
        "id": slot.get("id"),
        "label": slot.get("label"),
        "kind": slot.get("kind"),
        "epistemic_status": slot.get("epistemic_status"),
        "turn_index": slot.get("turn_index"),
        "source": slot.get("source"),
    }


def _read_inbox() -> list[dict[str, Any]]:
    if not INBOX.exists():
        return []
    rows = []
    for line in INBOX.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def _status(text: str) -> None:
    (OUT / "status.txt").write_text(text + "\n", encoding="utf-8")
    print(text, flush=True)


def _discourse_proof(session: dict[str, Any] | None) -> dict[str, Any]:
    focus = {}
    if isinstance(session, dict):
        raw = session.get("discourse_focus")
        focus = raw if isinstance(raw, dict) else {}
    names = (
        "active_claim",
        "active_interlocutor",
        "active_inspected",
        "last_attempted_action",
        "active_actionable_lead",
    )
    return {name: focus.get(name) for name in names}


def _persistence_snapshot() -> dict[str, Any]:
    session: dict[str, Any] = {}
    try:
        loaded = storage.load_session()
        session = loaded if isinstance(loaded, dict) else {}
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}
    ledger = session.get("bounded_improvisation")
    ledger = ledger if isinstance(ledger, dict) else {}
    scene_id = str(session.get("active_scene_id") or "frontier_gate")
    scene: dict[str, Any] = {}
    world: dict[str, Any] = {}
    try:
        loaded_scene = storage.load_scene(scene_id)
        scene = loaded_scene if isinstance(loaded_scene, dict) else {}
    except Exception as exc:
        scene = {"error": str(exc)}
    try:
        loaded_world = storage.load_world()
        world = loaded_world if isinstance(loaded_world, dict) else {}
    except Exception as exc:
        world = {"error": str(exc)}
    body = scene.get("scene") if isinstance(scene.get("scene"), dict) else scene
    npcs = world.get("npcs") if isinstance(world.get("npcs"), list) else []
    return {
        "session_id": session.get("session_id"),
        "campaign_run_id": session.get("campaign_run_id"),
        "active_scene_id": scene_id,
        "discourse_focus": session.get("discourse_focus"),
        "incidental_entities": ledger.get("incidental_entities") or [],
        "ledger_entries": ledger.get("entries") or [],
        "ledger_rejected": ledger.get("rejected") or [],
        "npc_ids": [
            {"id": row.get("id"), "name": row.get("name"), "location": row.get("location")}
            for row in npcs
            if isinstance(row, dict)
        ],
        "visible_facts": body.get("visible_facts") if isinstance(body, dict) else None,
        "discoverable_clues": body.get("discoverable_clues") if isinstance(body, dict) else None,
        "log_bytes": storage.SESSION_LOG_PATH.stat().st_size if storage.SESSION_LOG_PATH.exists() else 0,
    }


def _authority_rows(text: str, corpus: str) -> list[dict[str, Any]]:
    rows = []
    for row in classify_propositions(text, authored_corpus=corpus):
        rows.append(
            {
                "proposition": str(row.get("text") or "")[:500],
                "authority_class": row.get("kind"),
                "grounded": bool(row.get("grounded")),
                "epistemic_framing": row.get("epistemic_status"),
                "consequential": bool(row.get("consequential")),
                "family": row.get("family"),
            }
        )
    return rows


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "turns").mkdir(exist_ok=True)
    INBOX.write_text("", encoding="utf-8")
    (OUT / "persona.md").write_text(PERSONA, encoding="utf-8")
    head = _git(["rev-parse", "HEAD"])
    preflight = {
        "stamp": STAMP,
        "head": head,
        "head_subject": _git(["log", "-1", "--format=%s"]),
        "head_date": _git(["log", "-1", "--format=%ci"]),
        "game_worktree": _git(["status", "--short", "--", "game", "tools", "tests"]),
        "behavior_changes_before_run": False,
        "isolated_storage": True,
        "product_path": ["/api/start_campaign", "/api/chat"],
        "max_gameplay_turns": MAX_TURNS,
        "semantic_repair_applied": False,
        "player_fed_regression_internals": False,
        "evaluator_model_calls": 0,
        "synthetic_player_model_calls": 0,
    }
    (OUT / "preflight.json").write_text(json.dumps(preflight, indent=2), encoding="utf-8")

    import game.api as api_module
    import game.semantic_interpreter as interpreter_module
    from game.immutable_valid_response import _authored_corpus

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
    before = _persistence_snapshot()
    isolation = {
        "storage_root": str(isolated),
        "player_campaign_untouched": True,
        "before_opening": before,
        "discourse_before_opening": _discourse_proof(before if isinstance(before, dict) else {}),
        "incidental_entities_before_opening": before.get("incidental_entities") if isinstance(before, dict) else None,
        "session_log_empty": storage.SESSION_LOG_PATH.read_text(encoding="utf-8").strip() == "",
        "character": storage.load_character().get("name"),
        "scene_seed": "authored frontier_gate via seed_frontier_gate_world after default campaign-start scenes",
        "extra_test_facts_injected": False,
    }
    # discourse proof from the session object, not the snapshot wrapper
    try:
        isolation["discourse_before_opening"] = _discourse_proof(storage.load_session())
    except Exception as exc:
        isolation["discourse_before_opening_error"] = str(exc)
    (OUT / "isolation.json").write_text(json.dumps(isolation, indent=2, ensure_ascii=False), encoding="utf-8")

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
        after_open = _persistence_snapshot()
        isolation["after_opening_before_turn_1"] = after_open
        try:
            isolation["discourse_after_opening"] = _discourse_proof(storage.load_session())
        except Exception as exc:
            isolation["discourse_after_opening_error"] = str(exc)
        (OUT / "isolation.json").write_text(json.dumps(isolation, indent=2, ensure_ascii=False), encoding="utf-8")
        (OUT / "opening.json").write_text(
            json.dumps(
                {
                    "gm_text": opening_text,
                    "ok": opening_payload.get("ok"),
                    "generation_calls": generation_log[gen_before:],
                    "authoritative_state": after_open,
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
            binding = construction.get("entity_binding") if isinstance(construction.get("entity_binding"), dict) else {}
            session = payload.get("session") if isinstance(payload.get("session"), dict) else {}
            gm_output = payload.get("gm_output") if isinstance(payload.get("gm_output"), dict) else {}
            gm_meta = gm_output.get("metadata") if isinstance(gm_output.get("metadata"), dict) else {}
            accepted = gm_meta.get("accepted_response") if isinstance(gm_meta.get("accepted_response"), dict) else {}
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
            attempt_1 = ""
            attempt_2 = ""
            for index, call in enumerate(turn_generations):
                excerpt = str(call.get("model_player_facing_text") or "").strip()
                if index == 0:
                    attempt_1 = excerpt
                elif index == 1:
                    attempt_2 = excerpt
            attempt_1_hard = gm_meta.get("hard_validation_attempt_1") if isinstance(gm_meta.get("hard_validation_attempt_1"), dict) else {}
            attempt_2_hard = gm_meta.get("hard_validation_attempt_2") if isinstance(gm_meta.get("hard_validation_attempt_2"), dict) else {}
            accepted_text = str(accepted.get("text") or "")
            provenance = str(accepted.get("provenance") or "")
            exact = bool(accepted_text) and gm_text == accepted_text
            semantic = bool(accepted_text) and (exact or semantic_equal(gm_text, accepted_text))
            scene = storage.load_scene(str(session.get("active_scene_id") or "frontier_gate"))
            corpus = _authored_corpus(scene if isinstance(scene, dict) else None)
            persisted = _persistence_snapshot()
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
                "generation_attempt_1": attempt_1,
                "generation_attempt_2": attempt_2 or None,
                "attempt_1_hard_valid": attempt_1_hard.get("hard_valid"),
                "attempt_1_reasons": list(attempt_1_hard.get("reasons") or []),
                "attempt_2_hard_valid": attempt_2_hard.get("hard_valid"),
                "attempt_2_reasons": list(attempt_2_hard.get("reasons") or []),
                "regeneration_invoked": bool(gm_meta.get("regeneration_invoked")) or len(turn_generations) > 1,
                "regeneration_feedback": gm_meta.get("regeneration_feedback"),
                "rejected_attempt_2_reasons": gm_meta.get("rejected_attempt_2_reasons"),
                "generation_attempt_count": gm_meta.get("generation_attempt_count") or len(turn_generations),
                "accepted_provenance": provenance,
                "accepted_response_text": accepted_text,
                "accepted_immutable": accepted.get("immutable"),
                "final_emitted_response": gm_text,
                "gm_text": gm_text,
                "accepted_emitted_exact_match": exact,
                "accepted_emitted_semantic_match": semantic,
                "gm_tags": gm_output.get("tags"),
                "best_safe_candidate": emission.get("best_safe_candidate"),
                "final_selected_candidate": emission.get("final_selected_candidate"),
                "best_safe_invalidation": emission.get("best_safe_invalidation"),
                "candidate_transitions": emission.get("candidate_transitions") or [],
                "fast_path_used": construction.get("fast_path_used"),
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
                "dimension": contract.get("dimension"),
                "dimensions": contract.get("dimensions"),
                "expected_resolution": contract.get("expected_resolution"),
                "ambiguous": contract.get("ambiguous"),
                "binding_status": binding.get("status"),
                "entity_class": binding.get("entity_class"),
                "proposed_interlocutor": binding.get("proposed_interlocutor"),
                "bound_interlocutor": binding.get("bound_interlocutor_id"),
                "entity_id": binding.get("entity_id"),
                "authority_reasons": list(binding.get("authority_reasons") or []),
                "entity_binding": binding,
                "contract": contract,
                "active_interlocutor": _slot(focus, "active_interlocutor"),
                "active_claim": _slot(focus, "active_claim"),
                "active_inspected": _slot(focus, "active_inspected"),
                "actionable_lead": _slot(focus, "active_actionable_lead"),
                "previous_action": _slot(focus, "last_attempted_action"),
                "discourse_focus": focus,
                "authority_generated": _authority_rows(attempt_1, corpus),
                "authority_retry": _authority_rows(attempt_2, corpus) if attempt_2 else [],
                "authority_emitted": _authority_rows(gm_text, corpus),
                "unauthorized_generated": [str(item.get("text") or "")[:300] for item in unauthorized_authoritative_rules(attempt_1, corpus)],
                "unauthorized_retry": [str(item.get("text") or "")[:300] for item in unauthorized_authoritative_rules(attempt_2, corpus)] if attempt_2 else [],
                "unauthorized_emitted": [str(item.get("text") or "")[:300] for item in unauthorized_authoritative_rules(gm_text, corpus)],
                "semantic_result": evaluation.get("semantic_result"),
                "failing_gates": failing_gates,
                "evaluation": evaluation,
                "generation_calls_this_turn": len(generation_log) - gen_before,
                "interpretation_calls_this_turn": len(interpretation_log) - interp_before,
                "turn_generation_calls": turn_generations,
                "turn_interpretation_calls": interpretation_log[interp_before:],
                "persistence": persisted,
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
        "synthetic_player_model_calls": 0,
        "semantic_repair": False,
        "rerun": False,
        "behavior_changes_during_run": False,
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    _status("SESSION_COMPLETE")
    print(str(OUT), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
