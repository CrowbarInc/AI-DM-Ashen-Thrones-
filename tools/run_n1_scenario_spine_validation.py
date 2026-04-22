#!/usr/bin/env python3
"""Deterministic N1 scenario-spine / longitudinal continuity CLI (tooling only).

Delegates to ``tests.helpers.n1_scenarios`` fixtures and ``run_n1_scenario_and_analyze``;
does not implement analyzer or harness logic and does not touch ``game/``.

Exit codes (``main`` / process):

- ``0`` — command succeeded; for ``run``, no executed branch ended with
  ``final_session_verdict == "fail"``.
- ``1`` — ``run`` completed but at least one executed branch has verdict ``fail``.
- ``2`` — operator error (unknown scenario, bad branch, invalid flags, invalid
  ``--max-turns``, etc.); message on stderr prefixed with ``error:``.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence
from dataclasses import replace
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def _positive_max_turns(text: str) -> int:
    """``argparse`` type for ``--max-turns`` (strict positive integers)."""
    raw = str(text).strip()
    try:
        n = int(raw, 10)
    except ValueError as e:
        msg = f"--max-turns must be a base-10 integer (got {text!r})"
        raise argparse.ArgumentTypeError(msg) from e
    if n < 1:
        raise argparse.ArgumentTypeError("--max-turns must be >= 1")
    return n


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tests.helpers.n1_continuity_analysis import (  # noqa: E402
    N1ContinuityIssue,
    analyze_n1_branch_longitudinal_continuity,
    deterministic_continuity_report_json,
)
from tests.helpers.n1_scenario_spine_contract import N1BranchComparisonSummary, N1SessionHealthSummary  # noqa: E402
from tests.helpers.n1_scenario_spine_harness import (  # noqa: E402
    compare_n1_branch_session_health_summaries,
    deterministic_json_dumps,
    emit_n1_session_health_artifact_dict,
)
from tests.helpers.n1_scenarios import (  # noqa: E402
    N1RegisteredScenario,
    get_n1_registered_scenario,
    n1_default_fixture_deterministic_config,
    n1_fixture_fake_gm_responder,
    n1_player_texts_from_run,
    n1_registered_scenario_ids,
    n1_registered_scenarios,
    run_n1_scenario_and_analyze,
)
from tests.helpers.synthetic_profiles import default_placeholder_profile  # noqa: E402


def _comparison_summary_jsonable(summary: N1BranchComparisonSummary) -> dict[str, Any]:
    return {
        "branch_point_id": summary.branch_point_id,
        "compared_branch_ids": list(summary.compared_branch_ids),
        "divergence_detected": summary.divergence_detected,
        "per_branch_final_scene_id": dict(sorted(summary.per_branch_final_scene_id.items(), key=lambda kv: kv[0])),
        "per_branch_suffix_fingerprint": dict(
            sorted(summary.per_branch_suffix_fingerprint.items(), key=lambda kv: kv[0]),
        ),
        "reason_codes": list(summary.reason_codes),
        "scenario_spine_id": summary.scenario_spine_id,
        "shared_prefix_fingerprint": summary.shared_prefix_fingerprint,
        "shared_prefix_turn_count": summary.shared_prefix_turn_count,
    }


def _issue_jsonable(issue: N1ContinuityIssue) -> dict[str, Any]:
    return {
        "category": issue.category,
        "detail": issue.detail,
        "first_seen_turn": issue.first_seen_turn,
        "last_seen_turn": issue.last_seen_turn,
        "reason_code": issue.reason_code,
        "severity": issue.severity,
    }


def _issue_sort_key(issue: N1ContinuityIssue) -> tuple[str, str, str, int, int]:
    fs = issue.first_seen_turn if issue.first_seen_turn is not None else -1
    ls = issue.last_seen_turn if issue.last_seen_turn is not None else -1
    return (issue.severity, issue.category, issue.reason_code, fs, ls)


def _build_deterministic_config(
    *,
    profile: object,
    seed: int | None,
    max_turns: int | None,
    spec: N1RegisteredScenario,
) -> Any:
    base = n1_default_fixture_deterministic_config(profile)
    need = int(spec.min_scripted_player_turns())
    mx = int(max_turns) if max_turns is not None else int(base.max_turns)
    if mx < need:
        raise ValueError(
            f"--max-turns={mx} is below the scripted player-line minimum ({need}) for scenario "
            f"{spec.scenario_id!r}; raise --max-turns or pick a different scenario",
        )
    sd = int(seed) if seed is not None else int(base.seed)
    return replace(base, seed=sd, max_turns=mx)


def _branch_artifact_dir(artifact_root: Path, scenario_id: str, branch_id: str) -> Path:
    return artifact_root / scenario_id / branch_id


def _write_branch_outputs(
    *,
    artifact_root: Path,
    scenario_id: str,
    summary: N1SessionHealthSummary,
    longitudinal_report: object,
) -> tuple[Path, Path]:
    out_dir = _branch_artifact_dir(artifact_root, scenario_id, summary.branch_id)
    out_dir.mkdir(parents=True, exist_ok=True)
    sh_path = out_dir / "session_health.json"
    cr_path = out_dir / "continuity_report.json"
    sh_path.write_text(
        deterministic_json_dumps(emit_n1_session_health_artifact_dict(summary)),
        encoding="utf-8",
    )
    cr_path.write_text(deterministic_continuity_report_json(longitudinal_report), encoding="utf-8")
    return sh_path, cr_path


def _top_merged_codes(codes: Sequence[str], *, limit: int = 12) -> tuple[str, ...]:
    ordered = tuple(sorted(codes))
    return ordered[:limit]


def _print_run_summary_line(
    *,
    scenario_id: str,
    branch_id: str,
    run_id: str,
    final_session_verdict: str,
    severity_counters: Mapping[str, int],
    merged_reason_codes_top: Sequence[str],
    session_health: str,
    continuity_report: str,
    branch_comparison: str,
) -> None:
    """One stdout line per logical run; keys are stable for log parsers."""

    tops = ",".join(_top_merged_codes(merged_reason_codes_top))
    sev_json = json.dumps(dict(sorted(severity_counters.items())), sort_keys=True, separators=(",", ":"))
    print(
        "scenario_id="
        + scenario_id
        + " branch_id="
        + branch_id
        + " run_id="
        + run_id
        + " final_session_verdict="
        + final_session_verdict
        + " severity_counters="
        + sev_json
        + " merged_reason_codes_top="
        + tops
        + " session_health="
        + session_health
        + " continuity_report="
        + continuity_report
        + " branch_comparison="
        + branch_comparison,
    )


def _run_one_branch(
    *,
    spec: N1RegisteredScenario,
    branch_id: str,
    profile: object,
    deterministic_config: Any,
    artifact_root: Path,
) -> tuple[N1SessionHealthSummary, object, Path, Path]:
    branches_by_id = {b.branch_id: b for b in spec.branches}
    if branch_id not in branches_by_id:
        known = ", ".join(sorted(branches_by_id))
        raise ValueError(
            f"invalid --branch {branch_id!r} for scenario {spec.scenario_id!r} "
            f"(valid branch ids: {known})",
        )
    branch = branches_by_id[branch_id]
    analyzed = run_n1_scenario_and_analyze(
        spine=spec.spine,
        branch_point=spec.branch_point,
        branch=branch,
        profile=profile,
        deterministic_config=deterministic_config,
        shared_prefix_player_texts=spec.shared_prefix_player_texts,
        fake_gm_responder=n1_fixture_fake_gm_responder(),
    )
    sh_p, cr_p = _write_branch_outputs(
        artifact_root=artifact_root,
        scenario_id=spec.scenario_id,
        summary=analyzed.summary,
        longitudinal_report=analyzed.longitudinal_report,
    )
    return analyzed.summary, analyzed.longitudinal_report, sh_p, cr_p


def _run_compare_branches(
    *,
    spec: N1RegisteredScenario,
    profile: object,
    deterministic_config: Any,
    artifact_root: Path,
) -> tuple[bool, Path | None]:
    if not spec.supports_compare_branches:
        raise ValueError(
            f"scenario {spec.scenario_id!r} does not support --compare-branches "
            f"(linear / single-branch fixture); omit the flag or use --scenario n1_branch_divergence",
        )
    analyses: list[Any] = []
    summaries: list[N1SessionHealthSummary] = []
    branch_texts: dict[str, tuple[str, ...]] = {}
    for branch in sorted(spec.branches, key=lambda b: b.branch_id):
        analyzed = run_n1_scenario_and_analyze(
            spine=spec.spine,
            branch_point=spec.branch_point,
            branch=branch,
            profile=profile,
            deterministic_config=deterministic_config,
            shared_prefix_player_texts=spec.shared_prefix_player_texts,
            fake_gm_responder=n1_fixture_fake_gm_responder(),
        )
        analyses.append(analyzed)
        summaries.append(analyzed.summary)
        branch_texts[analyzed.summary.branch_id] = n1_player_texts_from_run(analyzed.run_result)
        sh_p, cr_p = _write_branch_outputs(
            artifact_root=artifact_root,
            scenario_id=spec.scenario_id,
            summary=analyzed.summary,
            longitudinal_report=analyzed.longitudinal_report,
        )
        _print_run_summary_line(
            scenario_id=spec.scenario_id,
            branch_id=analyzed.summary.branch_id,
            run_id=analyzed.summary.run_id,
            final_session_verdict=analyzed.summary.final_session_verdict,
            severity_counters=analyzed.longitudinal_report.severity_counters,
            merged_reason_codes_top=analyzed.longitudinal_report.merged_reason_codes,
            session_health=str(sh_p),
            continuity_report=str(cr_p),
            branch_comparison="-",
        )

    comparison = compare_n1_branch_session_health_summaries(
        scenario_spine_id=spec.spine.scenario_spine_id,
        branch_point=spec.branch_point,
        summaries=tuple(summaries),
        branch_full_player_texts=branch_texts,
    )
    branch_issues = analyze_n1_branch_longitudinal_continuity(
        spine=spec.spine,
        branch_point=spec.branch_point,
        summaries=tuple(sorted(summaries, key=lambda s: s.branch_id)),
        comparison=comparison,
    )
    cmp_path = artifact_root / spec.scenario_id / "branch_comparison.json"
    cmp_path.parent.mkdir(parents=True, exist_ok=True)
    bundle = {
        "branch_analyzer_issues": [_issue_jsonable(i) for i in sorted(branch_issues, key=_issue_sort_key)],
        "branch_comparison_summary": _comparison_summary_jsonable(comparison),
        "scenario_spine_id": spec.spine.scenario_spine_id,
    }
    cmp_path.write_text(deterministic_json_dumps(bundle), encoding="utf-8")
    merged_sev: dict[str, int] = {}
    for a in analyses:
        for k, v in a.longitudinal_report.severity_counters.items():
            merged_sev[str(k)] = merged_sev.get(str(k), 0) + int(v)
    issue_codes = [i.reason_code for i in branch_issues]
    _print_run_summary_line(
        scenario_id=spec.scenario_id,
        branch_id="*compare*",
        run_id="*multi*",
        final_session_verdict="*multi*",
        severity_counters=merged_sev,
        merged_reason_codes_top=issue_codes,
        session_health="-",
        continuity_report="-",
        branch_comparison=str(cmp_path),
    )
    any_fail = any(s.final_session_verdict == "fail" for s in summaries)
    return any_fail, cmp_path


def cmd_list(*, as_json: bool) -> int:
    rows = []
    for spec in n1_registered_scenarios():
        rows.append(
            {
                "branches": [b.branch_id for b in sorted(spec.branches, key=lambda b: b.branch_id)],
                "description": spec.description,
                "scenario_id": spec.scenario_id,
                "supports_compare_branches": spec.supports_compare_branches,
            },
        )
    if as_json:
        print(json.dumps(rows, sort_keys=True, separators=(",", ":")))
    else:
        for row in rows:
            branches = ",".join(row["branches"])
            print(
                f"{row['scenario_id']}\tcompare={row['supports_compare_branches']}\tbranches={branches}",
            )
    return 0


def _execute_spec(
    spec: N1RegisteredScenario,
    *,
    profile: object,
    artifact_root: Path,
    seed: int | None,
    max_turns: int | None,
    compare_branches: bool,
    branch_id: str | None,
) -> bool:
    """Return True if any executed branch has ``final_session_verdict == 'fail'``."""
    det = _build_deterministic_config(profile=profile, seed=seed, max_turns=max_turns, spec=spec)
    if compare_branches:
        failed, _ = _run_compare_branches(
            spec=spec,
            profile=profile,
            deterministic_config=det,
            artifact_root=artifact_root,
        )
        return failed
    if spec.supports_compare_branches and not branch_id:
        opts = ", ".join(sorted(b.branch_id for b in spec.branches))
        raise ValueError(
            f"scenario {spec.scenario_id!r} is multi-branch; pass --branch <id> ({opts}) "
            f"or use --compare-branches",
        )
    bid = branch_id or spec.branches[0].branch_id
    summary, report, sh_p, cr_p = _run_one_branch(
        spec=spec,
        branch_id=bid,
        profile=profile,
        deterministic_config=det,
        artifact_root=artifact_root,
    )
    _print_run_summary_line(
        scenario_id=spec.scenario_id,
        branch_id=summary.branch_id,
        run_id=summary.run_id,
        final_session_verdict=summary.final_session_verdict,
        severity_counters=report.severity_counters,
        merged_reason_codes_top=report.merged_reason_codes,
        session_health=str(sh_p),
        continuity_report=str(cr_p),
        branch_comparison="-",
    )
    return summary.final_session_verdict == "fail"


def cmd_run(args: argparse.Namespace) -> int:
    profile = default_placeholder_profile()
    artifact_root = Path(args.artifact_dir).resolve()
    artifact_root.mkdir(parents=True, exist_ok=True)

    if args.all:
        any_fail = False
        for sid in n1_registered_scenario_ids():
            spec = get_n1_registered_scenario(sid)
            use_compare = bool(spec.supports_compare_branches)
            if _execute_spec(
                spec,
                profile=profile,
                artifact_root=artifact_root,
                seed=args.seed,
                max_turns=args.max_turns,
                compare_branches=use_compare,
                branch_id=None,
            ):
                any_fail = True
        return 1 if any_fail else 0

    spec = get_n1_registered_scenario(str(args.scenario))
    if args.compare_branches and not spec.supports_compare_branches:
        raise ValueError(
            f"scenario {spec.scenario_id!r} does not support --compare-branches "
            f"(linear / single-branch fixture); omit the flag or use --scenario n1_branch_divergence",
        )

    failed = _execute_spec(
        spec,
        profile=profile,
        artifact_root=artifact_root,
        seed=args.seed,
        max_turns=args.max_turns,
        compare_branches=bool(args.compare_branches),
        branch_id=args.branch,
    )
    return 1 if failed else 0


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="N1 scenario-spine / longitudinal continuity validation (deterministic, tooling-only).",
        epilog="Exit: 0 success, 1 run verdict fail, 2 operator/config error. See module docstring.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    pl = sub.add_parser("list", help="Print registered scenarios (stable scenario_id order).")
    pl.add_argument(
        "--json",
        action="store_true",
        dest="emit_json",
        help="Print one JSON array (sorted keys, compact separators).",
    )
    pl.set_defaults(func=lambda a: cmd_list(as_json=a.emit_json))

    pr = sub.add_parser(
        "run",
        help="Run one scenario or all; writes JSON artifacts under --artifact-dir.",
    )
    pr.add_argument(
        "--artifact-dir",
        default=str(ROOT / "artifacts" / "n1_scenario_spine_validation"),
        help="Artifact root (created if missing; default: artifacts/n1_scenario_spine_validation/).",
    )
    pr.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Override deterministic seed (default: fixture seed in n1_default_fixture_deterministic_config).",
    )
    pr.add_argument(
        "--max-turns",
        type=_positive_max_turns,
        default=None,
        help=(
            "Override N1DeterministicRunConfig.max_turns (fingerprint only; runner still uses only "
            "scripted prefix+suffix lines). Integer >= 1 and >= each scenario's scripted line minimum."
        ),
    )
    g = pr.add_mutually_exclusive_group(required=True)
    g.add_argument("--scenario", type=str, default=None, help="Registered scenario_id (see ``list``).")
    g.add_argument("--all", action="store_true", help="Run every scenario in stable scenario_id order.")
    pr.add_argument(
        "--branch",
        type=str,
        default=None,
        help="Branch id for multi-branch scenarios only; ignored with --compare-branches or --all.",
    )
    pr.add_argument(
        "--compare-branches",
        action="store_true",
        help="Multi-branch scenarios only: run each branch, then emit branch_comparison.json.",
    )
    pr.set_defaults(func=cmd_run)
    return p


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
