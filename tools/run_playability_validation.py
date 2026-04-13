#!/usr/bin/env python3
"""Run fixed playability scenarios through ``POST /api/chat`` and attach ``evaluate_playability`` output.

The evaluator is the only scoring authority: this script does not interpret GM behavior,
recompute scores, or apply pass/fail thresholds beyond writing evaluator fields into artifacts.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game.api_upstream_preflight import (  # noqa: E402
    get_latest_upstream_api_preflight,
    log_upstream_api_preflight_at_startup,
)
from game.campaign_reset import apply_new_campaign_hard_reset  # noqa: E402
from game.upstream_dependent_run_gate import compute_upstream_dependent_run_gate  # noqa: E402
from game.upstream_dependent_run_gate_presentation import build_upstream_dependent_run_gate_operator  # noqa: E402
from game.dead_turn_report_visibility import (  # noqa: E402
    build_dead_turn_run_report,
    enrich_playability_rollup_dict,
    per_turn_dead_turn_visibility,
)
from game.narrative_authenticity_eval import evaluate_narrative_authenticity  # noqa: E402
from game.playability_eval import evaluate_playability, rollup_playability_gameplay_validation  # noqa: E402


@dataclass(frozen=True)
class PlayabilityScenario:
    """Preset player lines only; rubric lives in ``game.playability_eval``."""

    scenario_id: str
    description: str
    player_prompts: tuple[str, ...]


# Canonical ids — prompt lines mirror ``tests/test_playability_eval.py`` exemplars.
SCENARIOS: dict[str, PlayabilityScenario] = {
    "p1_direct_answer": PlayabilityScenario(
        "p1_direct_answer",
        "Direct-answer axis: clear question then bounded-partial style follow-up.",
        (
            "Who commands the watch here?",
            "Who stole the relic from the chapel?",
        ),
    ),
    "p2_respect_intent": PlayabilityScenario(
        "p2_respect_intent",
        "Player-intent axis: broad opener then narrowing follow-up.",
        (
            "Tell me about the thief.",
            "Who exactly was seen near the dye vats?",
        ),
    ),
    "p3_logical_escalation": PlayabilityScenario(
        "p3_logical_escalation",
        "Logical-escalation axis: observation then pressed detail on the same topic.",
        (
            "What do I see at the gate?",
            "I press again: what is actually posted on the notice?",
        ),
    ),
    "p4_immersion": PlayabilityScenario(
        "p4_immersion",
        "Immersion axis: minimal diegetic beat (GM text comes from the engine).",
        ("I glance at the notice.",),
    ),
}


def _utc_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _gm_text_from_chat_payload(payload: Mapping[str, Any]) -> str:
    gm = payload.get("gm_output")
    if isinstance(gm, Mapping):
        raw = gm.get("player_facing_text")
        if isinstance(raw, str):
            return raw
    return ""


def _resolution_kind(payload: Mapping[str, Any]) -> Any:
    res = payload.get("resolution")
    if isinstance(res, Mapping):
        return res.get("kind")
    return None


def _session_debug_traces(payload: Mapping[str, Any]) -> Any:
    sess = payload.get("session")
    if isinstance(sess, Mapping) and "debug_traces" in sess:
        return sess.get("debug_traces")
    return None


def _final_emission_meta_from_chat_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    gm = payload.get("gm_output")
    if not isinstance(gm, Mapping):
        return {}
    fem = gm.get("_final_emission_meta")
    return dict(fem) if isinstance(fem, Mapping) else {}


def _build_eval_payload(
    *,
    player_prompt: str,
    gm_text: str,
    prior_player: str,
    prior_gm: str,
    debug_traces: Any,
    gm_output: Mapping[str, Any] | None,
) -> dict[str, Any]:
    out: dict[str, Any] = {
        "player_prompt": player_prompt,
        "gm_text": gm_text,
    }
    if prior_player:
        out["prior_player_prompt"] = prior_player
    if prior_gm:
        out["prior_gm_text"] = prior_gm
    if debug_traces is not None:
        out["debug_traces"] = debug_traces
    if isinstance(gm_output, Mapping):
        out["gm_output"] = dict(gm_output)
    return out


def summary_from_eval(
    scenario_id: str,
    eval_out: Mapping[str, Any],
    *,
    run_gameplay_validation: Mapping[str, Any] | None = None,
    dead_turn_report: Mapping[str, Any] | None = None,
    upstream_dependent_run_gate: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Session summary JSON: thin mirror of evaluator top-level fields (no reinterpretation)."""
    axes = eval_out.get("axes")
    axis_scores: dict[str, Any] = {}
    if isinstance(axes, Mapping):
        for k, v in axes.items():
            if isinstance(v, Mapping) and "score" in v:
                axis_scores[str(k)] = v.get("score")
    summ = eval_out.get("summary") if isinstance(eval_out.get("summary"), Mapping) else {}
    out: dict[str, Any] = {
        "report_version": 3,
        "scenario_id": scenario_id,
        "overall": eval_out.get("overall"),
        "axis_scores": axis_scores,
        "failures": summ.get("failures"),
        "warnings": summ.get("warnings"),
    }
    if isinstance(run_gameplay_validation, Mapping):
        out["run_gameplay_validation"] = dict(run_gameplay_validation)
    if isinstance(dead_turn_report, Mapping):
        out["dead_turn_report"] = dict(dead_turn_report)
    if isinstance(upstream_dependent_run_gate, Mapping):
        out["upstream_dependent_run_gate"] = dict(upstream_dependent_run_gate)
        out["upstream_dependent_run_gate_operator"] = build_upstream_dependent_run_gate_operator(
            upstream_dependent_run_gate
        )
    return out


ChatCaller = Callable[[str], dict[str, Any]]


def _make_http_caller(base_url: str, *, timeout_s: float) -> ChatCaller:
    root = base_url.rstrip("/")

    def call(text: str) -> dict[str, Any]:
        url = f"{root}/api/chat"
        body = json.dumps({"text": text}).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                raw = resp.read().decode("utf-8")
            return json.loads(raw)
        except urllib.error.HTTPError as exc:
            try:
                payload = json.loads(exc.read().decode("utf-8"))
            except Exception:
                payload = {"ok": False, "error": str(exc), "status_code": exc.code}
            return payload if isinstance(payload, dict) else {"ok": False, "error": str(exc)}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    return call


def run_scenario(
    spec: PlayabilityScenario,
    *,
    chat_call: ChatCaller,
    apply_reset: bool,
    upstream_dependent_run_gate: Mapping[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return (turn_records, summary_json_dict)."""
    if apply_reset:
        apply_new_campaign_hard_reset()

    turns_out: list[dict[str, Any]] = []
    prior_player = ""
    prior_gm = ""

    for idx, player_prompt in enumerate(spec.player_prompts):
        payload = chat_call(player_prompt)
        if not isinstance(payload, dict):
            payload = {"ok": False, "error": "chat caller returned non-dict"}

        gm_text = _gm_text_from_chat_payload(payload)
        gm_out = payload.get("gm_output") if isinstance(payload.get("gm_output"), dict) else {}
        eval_in = _build_eval_payload(
            player_prompt=player_prompt,
            gm_text=gm_text,
            prior_player=prior_player,
            prior_gm=prior_gm,
            debug_traces=_session_debug_traces(payload),
            gm_output=gm_out,
        )
        playability_eval = evaluate_playability(eval_in)
        turn_packet = {
            "player_prompt": player_prompt,
            "prior_player_prompt": prior_player,
            "prior_gm_text": prior_gm,
        }
        fem = _final_emission_meta_from_chat_payload(payload)
        na_eval = evaluate_narrative_authenticity(
            turn_packet,
            payload,
            fem,
        )
        api_ok = bool(payload.get("ok"))
        dead_vis = per_turn_dead_turn_visibility({"_final_emission_meta": fem, "ok": api_ok}, turn_index=idx)

        turns_out.append(
            {
                "turn_index": idx,
                "player_prompt": player_prompt,
                "gm_text": gm_text,
                "resolution_kind": _resolution_kind(payload),
                "playability_eval": playability_eval,
                "narrative_authenticity_eval": na_eval,
                "api_ok": api_ok,
                "api_error": payload.get("error"),
                "_final_emission_meta": fem,
                "dead_turn_visibility": dead_vis,
            }
        )

        prior_player = player_prompt
        prior_gm = gm_text

    last_eval = turns_out[-1]["playability_eval"] if turns_out else evaluate_playability({})
    rollup = rollup_playability_gameplay_validation(turns_out)
    rollup = enrich_playability_rollup_dict(turns_out, rollup)
    dead_rep = build_dead_turn_run_report(turns_out)
    summary = summary_from_eval(
        spec.scenario_id,
        last_eval,
        run_gameplay_validation=rollup,
        dead_turn_report=dead_rep,
        upstream_dependent_run_gate=upstream_dependent_run_gate,
    )
    return turns_out, summary


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Run playability scenarios via /api/chat and record evaluate_playability(...) per turn.",
    )
    p.add_argument("--list", action="store_true", help="Print scenario ids and exit.")
    p.add_argument("--scenario", metavar="ID", help=f"One of: {', '.join(sorted(SCENARIOS))}.")
    p.add_argument("--all", action="store_true", help="Run every defined scenario (each with optional reset).")
    p.add_argument(
        "--no-reset",
        action="store_true",
        help="Skip apply_new_campaign_hard_reset() before each scenario (default: reset).",
    )
    p.add_argument(
        "--artifact-dir",
        type=Path,
        default=ROOT / "artifacts" / "playability_validation",
        help="Root directory for run folders (default: artifacts/playability_validation).",
    )
    p.add_argument(
        "--base-url",
        default=None,
        metavar="URL",
        help="If set, POST chat to this origin (e.g. http://127.0.0.1:8000). Default: in-process TestClient.",
    )
    p.add_argument(
        "--http-timeout",
        type=float,
        default=180.0,
        help="Seconds for remote /api/chat when --base-url is set (default: 180).",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.list:
        for sid in sorted(SCENARIOS):
            s = SCENARIOS[sid]
            print(f"{sid}\t{len(s.player_prompts)} turns\t{s.description}")
        return 0

    if args.all:
        to_run = [SCENARIOS[k] for k in sorted(SCENARIOS)]
    elif args.scenario:
        if args.scenario not in SCENARIOS:
            print(f"Unknown scenario {args.scenario!r}. Use --list.", file=sys.stderr)
            return 2
        to_run = [SCENARIOS[args.scenario]]
    else:
        _build_parser().print_help()
        return 2

    if get_latest_upstream_api_preflight() is None:
        log_upstream_api_preflight_at_startup()
    gate = compute_upstream_dependent_run_gate()
    gate_op = build_upstream_dependent_run_gate_operator(gate)
    if gate.get("manual_testing_blocked"):
        b = gate_op.get("compact_banner")
        if isinstance(b, str) and b.strip():
            print(f"[upstream_dependent_run_gate] {b.strip()}", file=sys.stderr)
        print(f"[upstream_dependent_run_gate] action_hint: {gate_op.get('action_hint')}", file=sys.stderr)
        print(
            "[upstream_dependent_run_gate] Playability validation blocked: cached upstream preflight "
            f"invalidates live narration (health_class={gate.get('preflight_health_class')!r}).",
            file=sys.stderr,
        )
        return 1
    if not gate.get("preflight_available"):
        b = gate_op.get("compact_banner")
        if isinstance(b, str) and b.strip():
            print(f"[upstream_dependent_run_gate] {b.strip()}", file=sys.stderr)
        print(f"[upstream_dependent_run_gate] action_hint: {gate_op.get('action_hint')}", file=sys.stderr)
        print(
            "[upstream_dependent_run_gate] Preflight unavailable — startup_run_valid is false; "
            "artifacts record block_reason for downstream review "
            f"({gate.get('block_reason')!r}).",
            file=sys.stderr,
        )

    apply_reset = not args.no_reset
    stamp = _utc_slug()
    base_dir: Path = args.artifact_dir

    def _run_batch(chat_call: ChatCaller) -> None:
        for spec in to_run:
            run_dir = base_dir / f"{stamp}_{spec.scenario_id}"
            turns, summary = run_scenario(
                spec,
                chat_call=chat_call,
                apply_reset=apply_reset,
                upstream_dependent_run_gate=gate,
            )
            transcript = {
                "report_version": 2,
                "scenario_id": spec.scenario_id,
                "scenario_description": spec.description,
                "upstream_dependent_run_gate": dict(gate),
                "upstream_dependent_run_gate_operator": build_upstream_dependent_run_gate_operator(gate),
                "dead_turn_report": summary.get("dead_turn_report"),
                "turns": [
                    {
                        "turn_index": t["turn_index"],
                        "player_prompt": t["player_prompt"],
                        "gm_text": t["gm_text"],
                        "resolution_kind": t["resolution_kind"],
                        "playability_eval": t["playability_eval"],
                        "narrative_authenticity_eval": t.get("narrative_authenticity_eval"),
                        "dead_turn_visibility": t.get("dead_turn_visibility"),
                    }
                    for t in turns
                ],
            }
            _write_json(run_dir / "transcript.json", transcript)
            _write_json(run_dir / "summary.json", summary)
            _write_json(
                run_dir / "run_debug.json",
                {
                    "report_version": 1,
                    "scenario_id": spec.scenario_id,
                    "turns": turns,
                    "summary": summary,
                },
            )
            print(f"Wrote {run_dir / 'transcript.json'}")
            print(f"Wrote {run_dir / 'summary.json'}")

    if args.base_url:
        _run_batch(_make_http_caller(args.base_url, timeout_s=args.http_timeout))
    else:
        from fastapi.testclient import TestClient

        from game.api import app

        def _post_json(client: Any, text: str) -> dict[str, Any]:
            resp = client.post("/api/chat", json={"text": text})
            try:
                data = resp.json()
            except Exception:
                return {
                    "ok": False,
                    "error": "non-json response",
                    "status_code": getattr(resp, "status_code", None),
                }
            return data if isinstance(data, dict) else {"ok": False, "error": "json was not an object"}

        with TestClient(app) as client:

            def chat_call(text: str) -> dict[str, Any]:
                return _post_json(client, text)

            _run_batch(chat_call)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
