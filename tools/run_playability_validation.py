#!/usr/bin/env python3
"""Run fixed playability scenarios through ``POST /api/chat`` and attach ``evaluate_playability`` output.

The evaluator is the only scoring authority: this script does not interpret GM behavior,
recompute scores, or apply pass/fail thresholds beyond writing evaluator fields into artifacts.
"""

from __future__ import annotations

import argparse
import copy
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
from game.storage import load_character, load_combat, load_log, load_session, load_world  # noqa: E402
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


def _utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _state_snapshot() -> dict[str, Any]:
    """Capture canonical persisted runtime state through existing storage APIs."""
    return {
        "session": copy.deepcopy(load_session()),
        "world": copy.deepcopy(load_world()),
        "combat": copy.deepcopy(load_combat()),
        "character": copy.deepcopy(load_character()),
        "log_entries": copy.deepcopy(load_log()),
    }


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
        "semantic_result": eval_out.get("semantic_result"),
        "mandatory_gates": eval_out.get("mandatory_gates"),
        "diagnostic_quality": eval_out.get("diagnostic_quality"),
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
    run_scenario._last_state_before = _state_snapshot()  # type: ignore[attr-defined]

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
        # Presentation only: dead-turn validity comes from FEM ``dead_turn`` via
        # per_turn_dead_turn_visibility, not from ``ok`` / ``error`` strings.
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


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _reported_result(summary: Mapping[str, Any]) -> str:
    semantic = summary.get("semantic_result")
    if isinstance(semantic, str) and semantic:
        return semantic
    overall = summary.get("overall") if isinstance(summary.get("overall"), Mapping) else {}
    return "PASS" if bool(overall.get("passed")) else "FAIL"


def _evaluation_artifact(
    *,
    spec: PlayabilityScenario,
    turns: list[dict[str, Any]],
    summary: Mapping[str, Any],
) -> dict[str, Any]:
    """Expose the existing evaluator's criteria without adding new scoring."""
    return {
        "artifact_version": 1,
        "scenario_id": spec.scenario_id,
        "result": _reported_result(summary),
        "pass_fail_source": (
            "summary.overall.passed from the final turn's evaluate_playability(...) output; "
            "run_gameplay_validation may force overall.passed false for dead-turn/infra invalidation."
        ),
        "current_success_definition": {
            "semantic_result": summary.get("semantic_result"),
            "mandatory_gates": summary.get("mandatory_gates"),
            "diagnostic_quality": summary.get("diagnostic_quality"),
            "overall_passed": (summary.get("overall") or {}).get("passed")
            if isinstance(summary.get("overall"), Mapping)
            else None,
            "overall_score": (summary.get("overall") or {}).get("score")
            if isinstance(summary.get("overall"), Mapping)
            else None,
            "overall_rating": (summary.get("overall") or {}).get("rating")
            if isinstance(summary.get("overall"), Mapping)
            else None,
            "run_gameplay_validation": summary.get("run_gameplay_validation"),
            "dead_turn_report": summary.get("dead_turn_report"),
        },
        "criteria": {
            "axis_thresholds": {
                "direct_answer": "axis passes when score >= 15/25",
                "player_intent": "axis passes when score >= 15/25",
                "logical_escalation": "axis passes when score >= 15/25",
                "immersion": "axis passes when score >= 15/25",
                "overall": "semantic result passes only when run validity, mandatory gates, and diagnostic threshold pass",
            },
            "per_turn_evidence": [
                {
                    "turn_index": t.get("turn_index"),
                    "player_prompt": t.get("player_prompt"),
                    "gm_text": t.get("gm_text"),
                    "resolution_kind": t.get("resolution_kind"),
                    "api_ok": t.get("api_ok"),
                    "api_error": t.get("api_error"),
                    "playability_eval": t.get("playability_eval"),
                    "narrative_authenticity_eval": t.get("narrative_authenticity_eval"),
                    "dead_turn_visibility": t.get("dead_turn_visibility"),
                    "_final_emission_meta": t.get("_final_emission_meta"),
                }
                for t in turns
            ],
        },
        "summary": dict(summary),
    }


def _metadata_artifact(
    *,
    spec: PlayabilityScenario,
    run_id: str,
    started_at: str,
    finished_at: str,
    artifact_dir: Path,
    apply_reset: bool,
    caller_kind: str,
    base_url: str | None,
    upstream_dependent_run_gate: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "artifact_version": 1,
        "run_id": run_id,
        "scenario_id": spec.scenario_id,
        "scenario_description": spec.description,
        "started_at": started_at,
        "finished_at": finished_at,
        "simulator": {
            "runner": "tools/run_playability_validation.py",
            "player_type": "fixed scripted natural-language prompts",
            "prompt_count": len(spec.player_prompts),
            "prompts": list(spec.player_prompts),
            "entrypoint": "/api/chat",
            "caller_kind": caller_kind,
            "base_url": base_url,
            "apply_reset_before_scenario": apply_reset,
            "random_seed": None,
        },
        "artifact_paths": {
            "transcript_md": str((artifact_dir / "transcript.md").resolve()),
            "evaluation_json": str((artifact_dir / "evaluation.json").resolve()),
            "state_before_json": str((artifact_dir / "state_before.json").resolve()),
            "state_after_json": str((artifact_dir / "state_after.json").resolve()),
            "metadata_json": str((artifact_dir / "metadata.json").resolve()),
            "legacy_transcript_json": str((artifact_dir / "transcript.json").resolve()),
            "legacy_summary_json": str((artifact_dir / "summary.json").resolve()),
            "run_debug_json": str((artifact_dir / "run_debug.json").resolve()),
        },
        "upstream_dependent_run_gate": dict(upstream_dependent_run_gate),
    }


def _transcript_markdown(
    *,
    spec: PlayabilityScenario,
    run_id: str,
    started_at: str,
    finished_at: str,
    turns: list[dict[str, Any]],
    summary: Mapping[str, Any],
    caller_kind: str,
) -> str:
    result = _reported_result(summary)
    overall = summary.get("overall") if isinstance(summary.get("overall"), Mapping) else {}
    mandatory_gates = summary.get("mandatory_gates") if isinstance(summary.get("mandatory_gates"), Mapping) else {}
    diagnostic_quality = (
        summary.get("diagnostic_quality") if isinstance(summary.get("diagnostic_quality"), Mapping) else {}
    )
    failures = summary.get("failures") if isinstance(summary.get("failures"), list) else []
    warnings = summary.get("warnings") if isinstance(summary.get("warnings"), list) else []

    lines = [
        f"# Simulation Run: {run_id}",
        "",
        f"Scenario: {spec.scenario_id}",
        f"Objective: {spec.description}",
        "Player: fixed scripted natural-language prompts",
        f"Transport: {caller_kind} `/api/chat`",
        "Seed: none",
        f"Started: {started_at}",
        f"Finished: {finished_at}",
        f"Semantic Result: {result}",
        "",
    ]

    if mandatory_gates:
        lines.extend(["# Result", "", f"Semantic Result: {result}", "", "Mandatory Gates:"])
        for name, gate in mandatory_gates.items():
            if isinstance(gate, Mapping):
                lines.append(f"- {name}: `{gate.get('status')}` ({', '.join(map(str, gate.get('reason_codes') or []))})")
        lines.extend(
            [
                "",
                f"Diagnostic Quality: `{json.dumps(diagnostic_quality, ensure_ascii=False, sort_keys=True)}`",
                "",
            ]
        )

    for t in turns:
        idx = int(t.get("turn_index") or 0) + 1
        lines.extend(
            [
                f"## Turn {idx}",
                "",
                "### PLAYER",
                "",
                str(t.get("player_prompt") or ""),
                "",
                "### GM",
                "",
                str(t.get("gm_text") or ""),
                "",
                "### Runtime Notes",
                "",
                f"- api_ok: `{t.get('api_ok')}`",
                f"- api_error: `{t.get('api_error')}`",
                f"- resolution_kind: `{t.get('resolution_kind')}`",
            ]
        )
        dead = t.get("dead_turn_visibility")
        if isinstance(dead, Mapping):
            lines.append(f"- dead_turn_visibility: `{json.dumps(dead, ensure_ascii=False, sort_keys=True)}`")
        pe = t.get("playability_eval")
        if isinstance(pe, Mapping):
            pe_overall = pe.get("overall") if isinstance(pe.get("overall"), Mapping) else {}
            lines.append(f"- playability_overall: `{json.dumps(pe_overall, ensure_ascii=False, sort_keys=True)}`")
            lines.append(
                f"- semantic_result: `{json.dumps(pe.get('semantic_result'), ensure_ascii=False, sort_keys=True)}`"
            )
            gates = pe.get("mandatory_gates") if isinstance(pe.get("mandatory_gates"), Mapping) else {}
            lines.append(f"- mandatory_gates: `{json.dumps(gates, ensure_ascii=False, sort_keys=True)}`")
        lines.append("")

    lines.extend(
        [
            "# Evaluation",
            "",
            f"Reported Result: {result}",
            "",
            (
                "The result above is copied from the playability evaluator's semantic authority. "
                "Mandatory gate failures are not overridden by diagnostic quality scores."
            ),
            "",
            f"Overall: `{json.dumps(overall, ensure_ascii=False, sort_keys=True)}`",
            f"Mandatory Gates: `{json.dumps(mandatory_gates, ensure_ascii=False, sort_keys=True)}`",
            f"Diagnostic Quality: `{json.dumps(diagnostic_quality, ensure_ascii=False, sort_keys=True)}`",
        ]
    )
    if failures:
        lines.extend(["", "Failures:"])
        lines.extend(f"- {str(item)}" for item in failures)
    if warnings:
        lines.extend(["", "Warnings:"])
        lines.extend(f"- {str(item)}" for item in warnings)
    lines.append("")
    return "\n".join(lines)


def _write_observability_artifacts(
    *,
    run_dir: Path,
    run_id: str,
    spec: PlayabilityScenario,
    started_at: str,
    finished_at: str,
    turns: list[dict[str, Any]],
    summary: Mapping[str, Any],
    state_before: Mapping[str, Any],
    state_after: Mapping[str, Any],
    apply_reset: bool,
    caller_kind: str,
    base_url: str | None,
    upstream_dependent_run_gate: Mapping[str, Any],
) -> None:
    _write_json(run_dir / "state_before.json", state_before)
    _write_json(run_dir / "state_after.json", state_after)
    _write_json(run_dir / "evaluation.json", _evaluation_artifact(spec=spec, turns=turns, summary=summary))
    _write_json(
        run_dir / "metadata.json",
        _metadata_artifact(
            spec=spec,
            run_id=run_id,
            started_at=started_at,
            finished_at=finished_at,
            artifact_dir=run_dir,
            apply_reset=apply_reset,
            caller_kind=caller_kind,
            base_url=base_url,
            upstream_dependent_run_gate=upstream_dependent_run_gate,
        ),
    )
    _write_text(
        run_dir / "transcript.md",
        _transcript_markdown(
            spec=spec,
            run_id=run_id,
            started_at=started_at,
            finished_at=finished_at,
            turns=turns,
            summary=summary,
            caller_kind=caller_kind,
        ),
    )


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

    def _run_batch(chat_call: ChatCaller, *, caller_kind: str) -> None:
        for spec in to_run:
            run_dir = base_dir / f"{stamp}_{spec.scenario_id}"
            started_at = _utc_iso()
            turns, summary = run_scenario(
                spec,
                chat_call=chat_call,
                apply_reset=apply_reset,
                upstream_dependent_run_gate=gate,
            )
            state_after = _state_snapshot()
            finished_at = _utc_iso()
            state_before = getattr(run_scenario, "_last_state_before", {})
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
            _write_observability_artifacts(
                run_dir=run_dir,
                run_id=f"{stamp}_{spec.scenario_id}",
                spec=spec,
                started_at=started_at,
                finished_at=finished_at,
                turns=turns,
                summary=summary,
                state_before=state_before if isinstance(state_before, Mapping) else {},
                state_after=state_after,
                apply_reset=apply_reset,
                caller_kind=caller_kind,
                base_url=args.base_url,
                upstream_dependent_run_gate=gate,
            )
            print(f"Wrote {run_dir / 'transcript.json'}")
            print(f"Wrote {run_dir / 'transcript.md'}")
            print(f"Wrote {run_dir / 'summary.json'}")

    if args.base_url:
        _run_batch(_make_http_caller(args.base_url, timeout_s=args.http_timeout), caller_kind="http")
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

            _run_batch(chat_call, caller_kind="in-process TestClient")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
