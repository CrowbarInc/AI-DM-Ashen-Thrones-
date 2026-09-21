#!/usr/bin/env python3
"""PR-AC isolated multi-turn semantic playability calibration runner.

Diagnostic only. Uses the existing ``POST /api/chat`` seam, campaign reset,
and ``evaluate_playability``. Does not score or reinterpret those outputs.
Does not change production gameplay behavior.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game.api_upstream_preflight import (  # noqa: E402
    get_latest_upstream_api_preflight,
    log_upstream_api_preflight_at_startup,
)
from game.campaign_reset import apply_new_campaign_hard_reset  # noqa: E402
from game.dead_turn_report_visibility import per_turn_dead_turn_visibility  # noqa: E402
from game.interaction_context import inspect as inspect_interaction_context  # noqa: E402
from game.leads import SESSION_LEAD_REGISTRY_KEY  # noqa: E402
from game.narrative_authenticity_eval import evaluate_narrative_authenticity  # noqa: E402
from game.playability_eval import evaluate_playability  # noqa: E402
from game.storage import (  # noqa: E402
    load_active_scene,
    load_character,
    load_combat,
    load_session,
    load_world,
)
from game.upstream_dependent_run_gate import compute_upstream_dependent_run_gate  # noqa: E402
from game.upstream_dependent_run_gate_presentation import (  # noqa: E402
    build_upstream_dependent_run_gate_operator,
)

DEFAULT_SCENARIOS = ROOT / "data" / "validation" / "semantic_playability_calibration_r2" / "scenarios.json"
DEFAULT_OUT = ROOT / "artifacts" / "semantic_playability_calibration_r2"


def _utc_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _compact_lead_row(lead_id: str, row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "id": lead_id,
        "title": row.get("title"),
        "type": row.get("type"),
        "lifecycle": row.get("lifecycle"),
        "status": row.get("status"),
        "next_step": row.get("next_step"),
        "discovery_source": row.get("discovery_source"),
    }


def _scene_runtime_pending(session: Mapping[str, Any], scene_id: str) -> list[Any]:
    runtime = session.get("scene_runtime")
    if not isinstance(runtime, Mapping):
        return []
    scene_rt = runtime.get(scene_id)
    if not isinstance(scene_rt, Mapping):
        return []
    pending = scene_rt.get("pending_leads")
    return list(pending) if isinstance(pending, list) else []


def _relevant_state() -> dict[str, Any]:
    session = load_session()
    world = load_world()
    scene_wrap = load_active_scene()
    combat = load_combat()
    character = load_character()
    scene = scene_wrap.get("scene") if isinstance(scene_wrap, Mapping) else {}
    if not isinstance(scene, Mapping):
        scene = {}
    scene_id = str(scene.get("id") or "")
    registry = session.get(SESSION_LEAD_REGISTRY_KEY) if isinstance(session, Mapping) else {}
    leads = []
    if isinstance(registry, Mapping):
        for lid, row in registry.items():
            if isinstance(row, Mapping):
                leads.append(_compact_lead_row(str(lid), row))
    world_npcs = []
    raw_npcs = world.get("npcs") if isinstance(world, Mapping) else None
    if isinstance(raw_npcs, Mapping):
        for nid, npc in raw_npcs.items():
            if isinstance(npc, Mapping):
                world_npcs.append(
                    {
                        "id": nid,
                        "name": npc.get("name"),
                        "location": npc.get("location") or npc.get("scene_id"),
                        "status": npc.get("status"),
                    }
                )
    elif isinstance(raw_npcs, list):
        for npc in raw_npcs:
            if isinstance(npc, Mapping):
                world_npcs.append(
                    {
                        "id": npc.get("id"),
                        "name": npc.get("name"),
                        "location": npc.get("location") or npc.get("scene_id"),
                        "status": npc.get("status"),
                    }
                )
    interaction = inspect_interaction_context(session) if isinstance(session, dict) else {}
    last_debug = session.get("last_action_debug") if isinstance(session, Mapping) else None
    compact_debug = None
    if isinstance(last_debug, Mapping):
        compact_debug = {
            k: last_debug.get(k)
            for k in (
                "kind",
                "parsed_intent",
                "normalized_action",
                "route_choice",
                "resolution_kind",
                "error",
            )
            if k in last_debug
        }
    traces = session.get("debug_traces") if isinstance(session, Mapping) else None
    last_trace = traces[-1] if isinstance(traces, list) and traces else None
    compact_trace = None
    if isinstance(last_trace, Mapping):
        intent_block = last_trace.get("intent") if isinstance(last_trace.get("intent"), Mapping) else {}
        compact_trace = {
            "parsed_intent": last_trace.get("parsed_intent") or intent_block.get("parsed"),
            "intent": last_trace.get("intent"),
            "classification": last_trace.get("classification"),
            "resolution_path": last_trace.get("resolution_path"),
            "response_type_contract": last_trace.get("response_type_contract"),
            "social_contract_trace": last_trace.get("social_contract_trace"),
            "authoritative_state_changes": last_trace.get("authoritative_state_changes"),
            "interaction_after": last_trace.get("interaction_after"),
            "clues": last_trace.get("clues"),
            "leads": last_trace.get("leads"),
            "route_choice": last_trace.get("route_choice") or last_trace.get("route_selected"),
            "canonical_entry": last_trace.get("canonical_entry"),
        }
    world_state = world.get("world_state") if isinstance(world, Mapping) else None
    return {
        "scene_id": scene_id,
        "scene_location": scene.get("location"),
        "scene_mode": scene.get("mode"),
        "visible_facts": list(scene.get("visible_facts") or []) if isinstance(scene.get("visible_facts"), list) else [],
        "addressables": [
            {"id": a.get("id"), "name": a.get("name"), "kind": a.get("kind")}
            for a in (scene.get("addressables") or [])
            if isinstance(a, Mapping)
        ],
        "interactables": [
            {"id": i.get("id"), "label": i.get("label"), "type": i.get("type")}
            for i in (scene.get("interactables") or [])
            if isinstance(i, Mapping)
        ],
        "exits": [
            {"label": e.get("label"), "target_scene_id": e.get("target_scene_id")}
            for e in (scene.get("exits") or [])
            if isinstance(e, Mapping)
        ],
        "turn_counter": session.get("turn_counter") if isinstance(session, Mapping) else None,
        "campaign_started": session.get("campaign_started") if isinstance(session, Mapping) else None,
        "interaction": {
            "active_interaction_target_id": interaction.get("active_interaction_target_id"),
            "active_interaction_kind": interaction.get("active_interaction_kind"),
            "interaction_mode": interaction.get("interaction_mode"),
            "engagement_level": interaction.get("engagement_level"),
        },
        "known_clues": (session.get("known_clues") if isinstance(session, Mapping) else None),
        "pending_leads_projection": _scene_runtime_pending(session if isinstance(session, Mapping) else {}, scene_id),
        "lead_registry": leads,
        "world_npcs": world_npcs,
        "world_state_flags": (
            {k: world_state.get(k) for k in list(world_state)[:20]}
            if isinstance(world_state, Mapping)
            else None
        ),
        "combat_active": bool((combat or {}).get("active")) if isinstance(combat, Mapping) else False,
        "character_name": (character or {}).get("name") if isinstance(character, Mapping) else None,
        "last_action_debug": compact_debug,
        "last_turn_trace": compact_trace,
    }


def _gm_text(payload: Mapping[str, Any]) -> str:
    gm = payload.get("gm_output")
    if isinstance(gm, Mapping):
        raw = gm.get("player_facing_text")
        if isinstance(raw, str):
            return raw
    return ""


def _resolution_compact(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    res = payload.get("resolution")
    if not isinstance(res, Mapping):
        return None
    return {
        "kind": res.get("kind"),
        "action_id": res.get("action_id"),
        "requires_check": res.get("requires_check"),
        "clue_id": res.get("clue_id"),
        "clue_text": res.get("clue_text"),
        "success": res.get("success"),
        "outcome": res.get("outcome"),
        "check_request": res.get("check_request") if isinstance(res.get("check_request"), Mapping) else None,
        "state_changes": res.get("state_changes") if isinstance(res.get("state_changes"), Mapping) else None,
        "metadata_keys": sorted(res["metadata"].keys()) if isinstance(res.get("metadata"), Mapping) else [],
    }


def _fem_compact(payload: Mapping[str, Any]) -> dict[str, Any]:
    gm = payload.get("gm_output")
    if not isinstance(gm, Mapping):
        return {}
    fem = gm.get("_final_emission_meta")
    if not isinstance(fem, Mapping):
        return {}
    return {
        k: fem.get(k)
        for k in (
            "emission_class",
            "realization_path",
            "fallback_family_used",
            "realization_fallback_family",
            "authorship_source",
            "dead_turn",
            "truncation",
            "repair_applied",
            "model_called",
            "selected_model",
        )
        if k in fem
    }


def _payload_evidence(payload: Mapping[str, Any]) -> dict[str, Any]:
    gm = payload.get("gm_output") if isinstance(payload.get("gm_output"), Mapping) else {}
    return {
        "ok": payload.get("ok"),
        "error": payload.get("error"),
        "resolution": _resolution_compact(payload),
        "final_emission": _fem_compact(payload),
        "gm_keys": sorted(gm.keys()) if gm else [],
        "has_oc": bool(isinstance(gm, Mapping) and gm.get("oc")),
    }


def run_case(case: Mapping[str, Any], *, chat_call, apply_reset: bool) -> dict[str, Any]:
    if apply_reset:
        apply_new_campaign_hard_reset()
    prompts = [str(p) for p in (case.get("player_prompts") or [])]
    turns: list[dict[str, Any]] = []
    prior_player = ""
    prior_gm = ""
    for idx, prompt in enumerate(prompts):
        state_before = _relevant_state()
        payload = chat_call(prompt)
        if not isinstance(payload, dict):
            payload = {"ok": False, "error": "chat caller returned non-dict"}
        gm_text = _gm_text(payload)
        gm_out = payload.get("gm_output") if isinstance(payload.get("gm_output"), dict) else {}
        eval_in = {
            "player_prompt": prompt,
            "gm_text": gm_text,
        }
        if prior_player:
            eval_in["prior_player_prompt"] = prior_player
        if prior_gm:
            eval_in["prior_gm_text"] = prior_gm
        traces = None
        sess = payload.get("session")
        if isinstance(sess, Mapping) and "debug_traces" in sess:
            traces = sess.get("debug_traces")
        if traces is not None:
            eval_in["debug_traces"] = traces
        if gm_out:
            eval_in["gm_output"] = dict(gm_out)
        playability = evaluate_playability(eval_in)
        fem = _fem_compact(payload)
        dead_vis = per_turn_dead_turn_visibility(
            {"_final_emission_meta": payload.get("gm_output", {}).get("_final_emission_meta") if isinstance(payload.get("gm_output"), Mapping) else {}, "ok": bool(payload.get("ok"))},
            turn_index=idx,
        )
        na_eval = evaluate_narrative_authenticity(
            {
                "player_prompt": prompt,
                "prior_player_prompt": prior_player,
                "prior_gm_text": prior_gm,
            },
            payload,
            payload.get("gm_output", {}).get("_final_emission_meta") if isinstance(payload.get("gm_output"), Mapping) else {},
        )
        state_after = _relevant_state()
        turns.append(
            {
                "turn_index": idx,
                "player_input": prompt,
                "gm_text": gm_text,
                "api_ok": bool(payload.get("ok")),
                "api_error": payload.get("error"),
                "state_before": state_before,
                "state_after": state_after,
                "runtime_evidence": _payload_evidence(payload),
                "playability_eval": playability,
                "narrative_authenticity_eval": na_eval,
                "dead_turn_visibility": dead_vis,
                "final_emission": fem,
                "semantic_result": playability.get("semantic_result"),
            }
        )
        prior_player = prompt
        prior_gm = gm_text
    return {
        "case_id": case.get("case_id"),
        "family": case.get("family"),
        "scenario": case.get("scenario"),
        "initial_objective": case.get("initial_objective"),
        "behaviors": case.get("behaviors"),
        "content": case.get("content"),
        "turn_count": len(turns),
        "turns": turns,
        "completed": all(t.get("api_ok") for t in turns) if turns else False,
    }


def _markdown_case(result: Mapping[str, Any]) -> str:
    lines = [
        f"# {result.get('case_id')} — {result.get('scenario')}",
        "",
        f"Objective: {result.get('initial_objective')}",
        f"Family: {result.get('family')}",
        f"Turns: {result.get('turn_count')}",
        f"Completed: {result.get('completed')}",
        "",
    ]
    for turn in result.get("turns") or []:
        idx = int(turn.get("turn_index") or 0) + 1
        pe = turn.get("playability_eval") if isinstance(turn.get("playability_eval"), Mapping) else {}
        ev = turn.get("runtime_evidence") if isinstance(turn.get("runtime_evidence"), Mapping) else {}
        res = ev.get("resolution") if isinstance(ev.get("resolution"), Mapping) else {}
        fem = turn.get("final_emission") if isinstance(turn.get("final_emission"), Mapping) else {}
        before = turn.get("state_before") if isinstance(turn.get("state_before"), Mapping) else {}
        after = turn.get("state_after") if isinstance(turn.get("state_after"), Mapping) else {}
        trace = after.get("last_turn_trace") if isinstance(after.get("last_turn_trace"), Mapping) else {}
        intent = trace.get("intent") if isinstance(trace.get("intent"), Mapping) else {}
        lines.extend(
            [
                f"## Turn {idx}",
                "",
                "### Player",
                "",
                str(turn.get("player_input") or ""),
                "",
                "### GM",
                "",
                str(turn.get("gm_text") or ""),
                "",
                "### Evidence",
                "",
                f"- semantic_result: `{turn.get('semantic_result')}`",
                f"- api_ok: `{turn.get('api_ok')}`",
                f"- resolution.kind: `{res.get('kind')}`",
                f"- parsed_intent: `{json.dumps(intent.get('parsed'), ensure_ascii=False)}`",
                f"- normalized: `{json.dumps(intent.get('normalized'), ensure_ascii=False)}`",
                f"- classification: `{json.dumps(trace.get('classification'), ensure_ascii=False)}`",
                f"- resolution_path: `{json.dumps(trace.get('resolution_path'), ensure_ascii=False)}`",
                f"- interaction_after: `{json.dumps(after.get('interaction'), ensure_ascii=False)}`",
                f"- scene: `{before.get('scene_id')}` -> `{after.get('scene_id')}`",
                f"- lead_registry: `{json.dumps(after.get('lead_registry'), ensure_ascii=False)}`",
                f"- pending_leads: `{json.dumps(after.get('pending_leads_projection'), ensure_ascii=False)}`",
                f"- world_npcs: `{json.dumps(after.get('world_npcs'), ensure_ascii=False)}`",
                f"- final_emission: `{json.dumps(fem, ensure_ascii=False)}`",
                f"- playability_overall: `{json.dumps(pe.get('overall'), ensure_ascii=False)}`",
                f"- mandatory_gates: `{json.dumps(pe.get('mandatory_gates'), ensure_ascii=False)}`",
                "",
            ]
        )
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run PR-AC semantic playability calibration cases.")
    parser.add_argument("--scenarios", type=Path, default=DEFAULT_SCENARIOS)
    parser.add_argument("--artifact-dir", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--case", action="append", dest="cases", help="Run only these case ids.")
    parser.add_argument("--no-reset", action="store_true")
    args = parser.parse_args(argv)

    spec = _load_json(args.scenarios)
    cases = spec.get("scenarios") if isinstance(spec.get("scenarios"), list) else []
    if args.cases:
        wanted = set(args.cases)
        cases = [c for c in cases if isinstance(c, Mapping) and c.get("case_id") in wanted]
    if not cases:
        print("No matching cases.", file=sys.stderr)
        return 2
    args.artifact_dir = args.artifact_dir.resolve()

    if get_latest_upstream_api_preflight() is None:
        log_upstream_api_preflight_at_startup()
    gate = compute_upstream_dependent_run_gate()
    gate_op = build_upstream_dependent_run_gate_operator(gate)
    if gate.get("manual_testing_blocked"):
        print(f"[upstream_dependent_run_gate] {gate_op.get('compact_banner')}", file=sys.stderr)
        print(f"[upstream_dependent_run_gate] action_hint: {gate_op.get('action_hint')}", file=sys.stderr)
        return 1

    stamp = _utc_slug()
    from fastapi.testclient import TestClient

    from game.api import app

    campaign: dict[str, Any] = {
        "report_version": 1,
        "generated_at": _utc_iso(),
        "stamp": stamp,
        "corpus_id": spec.get("corpus_id"),
        "upstream_dependent_run_gate": dict(gate),
        "cases": [],
    }
    apply_reset = not args.no_reset
    with TestClient(app) as client:
        def chat_call(text: str) -> dict[str, Any]:
            try:
                resp = client.post("/api/chat", json={"text": text})
            except Exception as exc:
                return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
            try:
                data = resp.json()
            except Exception:
                return {"ok": False, "error": "non-json response", "status_code": getattr(resp, "status_code", None)}
            return data if isinstance(data, dict) else {"ok": False, "error": "json was not an object"}

        for case in cases:
            started = _utc_iso()
            result = run_case(case, chat_call=chat_call, apply_reset=apply_reset)
            result["started_at"] = started
            result["finished_at"] = _utc_iso()
            case_dir = args.artifact_dir / "runs" / f"{stamp}_{result['case_id']}"
            _write_json(case_dir / "run.json", result)
            _write_text(case_dir / "transcript.md", _markdown_case(result))
            campaign["cases"].append(
                {
                    "case_id": result.get("case_id"),
                    "scenario": result.get("scenario"),
                    "family": result.get("family"),
                    "turn_count": result.get("turn_count"),
                    "completed": result.get("completed"),
                    "semantic_results": [t.get("semantic_result") for t in result.get("turns") or []],
                    "artifact": str((case_dir / "run.json").relative_to(ROOT)).replace("\\", "/"),
                }
            )
            print(f"Wrote {case_dir / 'transcript.md'}")

    _write_json(args.artifact_dir / f"{stamp}_campaign.json", campaign)
    print(f"Wrote {args.artifact_dir / (stamp + '_campaign.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
