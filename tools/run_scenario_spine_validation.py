#!/usr/bin/env python3
"""Drive scenario-spine branches through ``POST /api/chat``, record transcripts, and run ``evaluate_scenario_spine_session``.

The spine evaluator is the health authority; this script records turns and writes evaluator output to artifacts.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game.campaign_reset import apply_new_campaign_hard_reset  # noqa: E402
from game.scenario_spine import (  # noqa: E402
    ScenarioBranch,
    ScenarioSpine,
    ScenarioTurn,
    scenario_spine_from_dict,
    validate_scenario_spine_definition,
)
from game.scenario_spine_eval import (  # noqa: E402
    evaluate_scenario_spine_branch_divergence,
    evaluate_scenario_spine_session,
)
from game.scenario_spine_opening_convergence import (  # noqa: E402
    capture_opening_convergence_meta_from_chat_payload,
)

DEFAULT_SPINE_PATH = ROOT / "data" / "validation" / "scenario_spines" / "frontier_gate_long_session.json"
DEFAULT_ARTIFACT_ROOT = ROOT / "artifacts" / "scenario_spine_validation"
DEFAULT_BRANCH_ID = "branch_social_inquiry"
SMOKE_TURN_CAP = 5
# Cap rows rendered in compact_operator_summary.md for C1-A opening convergence failures.
_OPENING_CONVERGENCE_FAILURE_TABLE_MAX_ROWS = 12

# Mirrors ``game.scenario_spine_eval`` private alias table for CLI resolution only.
_BRANCH_ALIASES: dict[str, str] = {
    "social_investigation": "branch_social_inquiry",
    "direct_intrusion": "branch_direct_intrusion",
    "cautious_observation": "branch_cautious_observe",
}

ChatCaller = Callable[[str], dict[str, Any]]


def _utc_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def resolve_spine_path(spine_arg: str | None) -> Path:
    """Resolve ``--spine`` to a filesystem path (default canonical fixture)."""
    if not spine_arg:
        return DEFAULT_SPINE_PATH
    p = Path(spine_arg)
    if p.is_file():
        return p.resolve()
    candidate = ROOT / "data" / "validation" / "scenario_spines" / f"{spine_arg.removesuffix('.json')}.json"
    if candidate.is_file():
        return candidate.resolve()
    return p.resolve()


def load_spine(path: Path) -> tuple[ScenarioSpine, list[str]]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    spine = scenario_spine_from_dict(raw)
    return spine, validate_scenario_spine_definition(spine)


def resolve_branch_id(spine: ScenarioSpine, branch_id: str) -> str | None:
    bid = str(branch_id).strip()
    ids = {b.branch_id for b in spine.branches}
    if bid in ids:
        return bid
    mapped = _BRANCH_ALIASES.get(bid)
    if mapped and mapped in ids:
        return mapped
    return None


def get_branch(spine: ScenarioSpine, branch_id: str) -> ScenarioBranch | None:
    resolved = resolve_branch_id(spine, branch_id)
    if resolved is None:
        return None
    for b in spine.branches:
        if b.branch_id == resolved:
            return b
    return None


def effective_turn_limit(branch_len: int, *, smoke: bool, max_turns: int | None) -> int:
    n = branch_len
    if max_turns is not None:
        n = min(n, max_turns)
    if smoke:
        n = min(n, SMOKE_TURN_CAP)
    return max(0, n)


def branch_listing_labels(turn_count: int) -> tuple[bool, str]:
    """(full_length_eligible, branch_role_note)."""
    eligible = turn_count >= 20
    if eligible:
        return True, "full-length scripted path (>= 20 turns)"
    return False, "alternate / smoke path - short scripted branch (not a full long-session validation run)"


def operator_branch_scope(
    spine_turns: int,
    executed: int,
    *,
    smoke_flag: bool,
) -> str:
    if spine_turns < 20:
        return "alternate_short"
    if smoke_flag or executed < spine_turns:
        return "smoke"
    return "full"


def _gm_text_from_chat_payload(payload: Mapping[str, Any]) -> str:
    gm = payload.get("gm_output")
    if isinstance(gm, Mapping):
        raw = gm.get("player_facing_text")
        if isinstance(raw, str):
            return raw
    return ""


def _narration_seam_from_chat_payload(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    gm = payload.get("gm_output")
    if not isinstance(gm, Mapping):
        return None
    md = gm.get("metadata")
    if not isinstance(md, Mapping):
        return None
    seam = md.get("narration_seam")
    if not isinstance(seam, Mapping):
        return None
    # Keep as plain dict for JSON serialization; evaluator expects Mapping.
    return {str(k): seam[k] for k in sorted(seam, key=str)}


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


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _first_failing_checkpoint_id(ev: Mapping[str, Any]) -> str | None:
    for cp in ev.get("checkpoint_results") or []:
        if isinstance(cp, dict) and cp.get("passed") is False:
            cid = cp.get("checkpoint_id")
            return str(cid) if cid is not None else None
    return None


def _suggested_debug_focus(ev: Mapping[str, Any]) -> str:
    fails = ev.get("detected_failures") or []
    if not isinstance(fails, list) or not fails:
        return "none (inspect warnings or checkpoint weak signals if present)"
    axis_counts: dict[str, int] = {}
    for f in fails:
        if isinstance(f, dict):
            ax = str(f.get("axis") or "session")
            axis_counts[ax] = axis_counts.get(ax, 0) + 1
    dom = max(axis_counts, key=lambda k: axis_counts[k])
    guide = {
        "state_continuity": "state continuity",
        "referent_persistence": "referent persistence",
        "world_project_progression": "progression",
        "narrative_grounding": "grounding",
        "branch_coherence": "branch routing",
        "session": "API availability or session wiring",
    }
    return guide.get(dom, dom)


def _opening_convergence_verdict_human(verdict: str) -> str:
    v = str(verdict or "").strip().lower()
    if v == "pass":
        return "**Pass** — no hard opening-convergence failures on evaluated opening turn(s)."
    if v == "fail":
        return "**Fail** — at least one hard opening-convergence signal (see table below)."
    if v in ("no_observations", ""):
        return "**No observations** — no opening-turn rows were evaluated (opening meta absent or skipped)."
    return f"**{verdict}**"


def _opening_convergence_md_lines(eval_result: Mapping[str, Any]) -> list[str]:
    sh = eval_result.get("session_health") if isinstance(eval_result.get("session_health"), dict) else {}
    verdict_raw = str(sh.get("opening_convergence_verdict") or "")
    n_checked = int(sh.get("opening_turns_checked") or 0)
    n_missing = int(sh.get("opening_plan_missing_count") or 0)
    n_invalid = int(sh.get("opening_invalid_plan_count") or 0)
    n_seam = int(sh.get("opening_seam_failure_count") or 0)
    n_anchor = int(sh.get("opening_anchor_grounding_failures") or 0)
    n_stock = int(sh.get("opening_stock_fallback_hits") or 0)
    n_resume = int(sh.get("opening_resume_entry_checked") or 0)
    n_backed = int(sh.get("opening_plan_backed_count") or 0)
    rep_first = sh.get("opening_repeated_generic_first_line")

    lines = [
        "",
        "## C1-A opening convergence (observational)",
        "",
        _opening_convergence_verdict_human(verdict_raw),
        "",
        "### Counts (opening turns)",
        "",
        f"- **Opening turns checked:** {n_checked}",
        f"- **Plan-backed openings:** {n_backed}",
        f"- **Missing plan / scene_opening:** {n_missing}",
        f"- **Invalid recorded scene_opening:** {n_invalid}",
        f"- **Seam hard failures** (`scene_opening_seam_invalid`): {n_seam}",
        f"- **Anchor grounding failures:** {n_anchor}",
        f"- **Stock opener phrase hits** (warning-style unless verdict fail): {n_stock}",
        f"- **Resume-entry openings checked:** {n_resume}",
        f"- **Repeated generic first-line** (warning-style unless verdict fail): {rep_first}",
        "",
        "### Opening convergence failures (compact table)",
        "",
    ]
    details = sh.get("opening_convergence_failure_details") or []
    if isinstance(details, list) and details:
        cap = _OPENING_CONVERGENCE_FAILURE_TABLE_MAX_ROWS
        lines.extend(
            [
                "| Turn | Opening reason | Scene id | Marker | Seam / anchors | Source |",
                "|-----:|----------------|----------|--------|----------------|--------|",
            ],
        )
        shown = 0
        for d in details:
            if shown >= cap:
                break
            if not isinstance(d, dict):
                lines.append(f"| — | _(non-dict row)_ | | `{d!r}` | | |")
                shown += 1
                continue
            tid = d.get("turn_index")
            oreason = str(d.get("opening_reason") or "").replace("|", "\\|")
            sid = str(d.get("scene_id") or "").replace("|", "\\|") or "—"
            marker = str(d.get("marker") or "").replace("|", "\\|")
            seam = str(d.get("seam_failure_reason") or "").replace("|", "\\|")
            anch = str(d.get("anchor_grounding_category") or "").replace("|", "\\|")
            seam_anch = " / ".join(x for x in (seam, anch) if x) or "—"
            src = str(d.get("suspected_source") or "").replace("|", "\\|")
            lines.append(f"| `{tid}` | {oreason} | {sid} | `{marker}` | {seam_anch} | `{src}` |")
            shown += 1
        rest = len(details) - shown
        if rest > 0:
            lines.append("")
            lines.append(f"_… {rest} more failure row(s) not shown (cap {cap})._")
    else:
        lines.append("_No failure rows — either **pass** or **no observations**._")
    return lines


def build_operator_summary_md(
    *,
    spine_id: str,
    branch_id: str,
    spine_branch_turns: int,
    executed_turns: int,
    scope_label: str,
    eval_result: Mapping[str, Any],
) -> str:
    sh = eval_result.get("session_health") if isinstance(eval_result.get("session_health"), dict) else {}
    classification = sh.get("classification", "")
    score = sh.get("score", "")
    axes = eval_result.get("axes") if isinstance(eval_result.get("axes"), dict) else {}
    fails = eval_result.get("detected_failures") or []
    warns = eval_result.get("warnings") or []
    top_fail = fails[:8] if isinstance(fails, list) else []
    top_warn = warns[:8] if isinstance(warns, list) else []
    first_cp = _first_failing_checkpoint_id(eval_result)
    focus = _suggested_debug_focus(eval_result)

    lines = [
        f"# Scenario spine validation — {spine_id} / {branch_id}",
        "",
        f"- **Scenario id:** `{spine_id}`",
        f"- **Branch id:** `{branch_id}`",
        f"- **Scripted branch turns:** {spine_branch_turns}",
        f"- **Executed turns this run:** {executed_turns}",
        f"- **Run scope:** {scope_label}",
        "",
        "## Session health",
        "",
        f"- **Classification:** {classification}",
        f"- **Score:** {score}",
        f"- **Overall passed (evaluator):** {sh.get('overall_passed')}",
        "",
        "## Axes",
        "",
        "| Axis | Passed | Failure codes | Warning codes |",
        "|------|--------|---------------|---------------|",
    ]
    for axis_key in sorted(axes.keys(), key=str):
        ax = axes[axis_key]
        if not isinstance(ax, dict):
            continue
        passed = ax.get("passed")
        fc = ", ".join(str(x) for x in (ax.get("failure_codes") or []) if x is not None)
        wc = ", ".join(str(x) for x in (ax.get("warning_codes") or []) if x is not None)
        lines.append(f"| `{axis_key}` | {passed} | {fc} | {wc} |")

    lines += _opening_convergence_md_lines(eval_result)
    lines += [
        "",
        "## Top failures",
        "",
    ]
    if top_fail:
        for item in top_fail:
            if isinstance(item, dict):
                lines.append(f"- `{item.get('axis')}` **{item.get('code')}** — {item.get('detail')}")
            else:
                lines.append(f"- {item!r}")
    else:
        lines.append("- _(none)_")

    lines += ["", "## Top warnings", ""]
    if top_warn:
        for item in top_warn:
            if isinstance(item, dict):
                lines.append(f"- `{item.get('axis')}` **{item.get('code')}** — {item.get('detail')}")
            else:
                lines.append(f"- {item!r}")
    else:
        lines.append("- _(none)_")

    lines += [
        "",
        "## First failing checkpoint",
        "",
        f"- `{first_cp}`" if first_cp else "- _(none)_",
        "",
        "## Suggested next debugging area",
        "",
        f"- **{focus}**",
        "",
        "## Fixture notes",
        "",
        "- `branch_social_inquiry` (25 turns) is the default **full** scripted long-session branch for this fixture.",
        "- `branch_direct_intrusion` and `branch_cautious_observe` are **short alternate** paths: useful for divergence, ",
        "  smoke, and routing checks - not described here as 60-90 minute full-session branches unless expanded later.",
        "",
    ]
    return "\n".join(lines)


@dataclass(frozen=True)
class BranchRunResult:
    branch_id_requested: str
    branch_id_resolved: str
    run_dir: Path
    eval_result: dict[str, Any]
    executed_turns: int
    spine_branch_turns: int
    scope_label: str


def _session_health_from_eval(eval_result: Mapping[str, Any]) -> dict[str, Any]:
    sh = eval_result.get("session_health")
    return sh if isinstance(sh, dict) else {}


def _long_spine_branch(session_health: Mapping[str, Any]) -> bool:
    return int(session_health.get("scripted_turn_count") or 0) >= 20


def _long_branch_row(session_health: Mapping[str, Any]) -> bool:
    return bool(session_health.get("full_length_branch")) or _long_spine_branch(session_health)


def build_aggregate_session_health_summary(
    spine: ScenarioSpine,
    branch_results: Sequence[BranchRunResult],
    *,
    smoke: bool,
    max_turns: int | None,
    run_timestamp: str,
) -> dict[str, Any]:
    """Spine-level aggregate for ``--all-branches`` runs; JSON-serializable."""
    results = list(branch_results)
    branches_run = [r.branch_id_resolved for r in results]
    branch_turn_counts: dict[str, int] = {}
    branch_classifications: dict[str, str] = {}
    branch_failures: dict[str, list[Any]] = {}
    branch_warnings: dict[str, list[Any]] = {}
    degradation_over_time_by_branch: dict[str, Any] = {}

    total_executed_turns = 0
    long_branch_count = 0

    for r in results:
        ev = r.eval_result
        sh = _session_health_from_eval(ev)
        bid = r.branch_id_resolved
        tc = int(sh.get("turn_count", r.executed_turns))
        branch_turn_counts[bid] = tc
        total_executed_turns += tc
        branch_classifications[bid] = str(sh.get("classification") or "")
        fails = ev.get("detected_failures") or []
        warns = ev.get("warnings") or []
        branch_failures[bid] = list(fails) if isinstance(fails, list) else []
        branch_warnings[bid] = list(warns) if isinstance(warns, list) else []
        deg = ev.get("degradation_over_time")
        degradation_over_time_by_branch[bid] = deg if isinstance(deg, dict) else {}
        if _long_branch_row(sh):
            long_branch_count += 1

    long_scripted_results = [r for r in results if _long_spine_branch(_session_health_from_eval(r.eval_result))]
    coverage_turn_total = sum(
        int(_session_health_from_eval(r.eval_result).get("turn_count", r.executed_turns)) for r in long_scripted_results
    )
    long_targets_complete = all(
        bool(_session_health_from_eval(r.eval_result).get("full_length_branch")) for r in long_scripted_results
    )
    long_targets_all_passed = bool(long_scripted_results) and all(
        bool(_session_health_from_eval(r.eval_result).get("overall_passed")) for r in long_scripted_results
    )
    coverage_band_met = (
        not smoke
        and bool(long_scripted_results)
        and long_targets_complete
        and 40 <= coverage_turn_total <= 60
    )

    all_full_length_branches_passed = bool(long_scripted_results) and all(
        bool(_session_health_from_eval(r.eval_result).get("full_length_branch"))
        and bool(_session_health_from_eval(r.eval_result).get("overall_passed"))
        for r in long_scripted_results
    )

    transcripts_for_div: dict[str, list[dict[str, Any]]] = {}
    for r in results:
        path = r.run_dir / "transcript.json"
        raw = json.loads(path.read_text(encoding="utf-8"))
        turns = raw.get("turns")
        transcripts_for_div[r.branch_id_resolved] = list(turns) if isinstance(turns, list) else []

    branch_divergence = evaluate_scenario_spine_branch_divergence(spine, transcripts_for_div)

    return {
        "schema_version": 1,
        "spine_id": spine.spine_id,
        "run_timestamp": run_timestamp,
        "branches_run": branches_run,
        "branch_turn_counts": dict(sorted(branch_turn_counts.items(), key=lambda kv: kv[0])),
        "total_executed_turns": total_executed_turns,
        "long_branch_count": long_branch_count,
        "coverage_band_met": coverage_band_met,
        "all_full_length_branches_passed": all_full_length_branches_passed,
        "branch_classifications": dict(sorted(branch_classifications.items(), key=lambda kv: kv[0])),
        "branch_failures": {k: branch_failures[k] for k in sorted(branch_failures)},
        "branch_warnings": {k: branch_warnings[k] for k in sorted(branch_warnings)},
        "degradation_over_time_by_branch": dict(
            sorted(degradation_over_time_by_branch.items(), key=lambda kv: kv[0]),
        ),
        "branch_divergence": branch_divergence,
        "aggregate_meta": {
            "smoke": smoke,
            "max_turns": max_turns,
            "coverage_turn_total_long_scripted_branches": coverage_turn_total,
            "long_scripted_branch_ids": [r.branch_id_resolved for r in long_scripted_results],
            "long_targets_complete": long_targets_complete,
            "long_targets_all_passed": long_targets_all_passed,
        },
    }


def build_aggregate_operator_summary_md(
    spine: ScenarioSpine,
    aggregate: Mapping[str, Any],
    branch_results: Sequence[BranchRunResult],
) -> str:
    """Markdown companion for ``aggregate_session_health_summary.json``."""
    meta = aggregate.get("aggregate_meta") if isinstance(aggregate.get("aggregate_meta"), dict) else {}
    smoke = bool(meta.get("smoke"))
    max_turns = meta.get("max_turns")
    div = aggregate.get("branch_divergence") if isinstance(aggregate.get("branch_divergence"), dict) else {}
    div_score = div.get("divergence_score", "")
    div_distinct = div.get("distinct_outcomes_detected", "")
    div_bleed = div.get("shared_prompt_bleed_detected", "")
    cov_met = aggregate.get("coverage_band_met")
    cov_note = (
        "40–60 turn band (full-length / scripted≥20 branches only) met"
        if cov_met
        else "40–60 band not claimed (smoke/partial/short aggregate or total outside band)"
    )

    lines = [
        f"# Scenario spine validation — aggregate / {aggregate.get('spine_id', spine.spine_id)}",
        "",
        f"- **Run timestamp:** `{aggregate.get('run_timestamp', '')}`",
        f"- **Branches run:** {', '.join(str(x) for x in (aggregate.get('branches_run') or []))}",
        f"- **Smoke:** {smoke} · **max_turns:** {max_turns}",
        f"- **Total executed turns (all branches):** {aggregate.get('total_executed_turns', '')}",
        f"- **Long-branch row count:** {aggregate.get('long_branch_count', '')}",
        f"- **Coverage:** {cov_note} (`coverage_band_met={cov_met}`)",
        f"- **All long-scripted branches passed:** `{aggregate.get('all_full_length_branches_passed')}`",
        "",
        "## Branch table",
        "",
        "| Branch | Scripted turns | Executed turns | Classification | Score | Opening verdict | Degradation (progressive) |",
        "|--------|----------------|----------------|----------------|-------|-----------------|---------------------------|",
    ]

    branches_run = list(aggregate.get("branches_run") or [])
    deg_by = (
        aggregate.get("degradation_over_time_by_branch")
        if isinstance(aggregate.get("degradation_over_time_by_branch"), dict)
        else {}
    )
    by_resolved: dict[str, BranchRunResult] = {r.branch_id_resolved: r for r in branch_results}

    def _md_cell(s: Any) -> str:
        t = str(s).replace("|", "\\|").replace("\n", " ")
        return t or "—"

    for bid in branches_run:
        r = by_resolved.get(bid)
        sh = _session_health_from_eval(r.eval_result) if r else {}
        scripted = int(sh.get("scripted_turn_count") or (r.spine_branch_turns if r else 0))
        executed = int(sh.get("turn_count") or (r.executed_turns if r else 0))
        cls = str(aggregate.get("branch_classifications", {}).get(bid, sh.get("classification", "")))
        score = sh.get("score", "")
        open_v = sh.get("opening_convergence_verdict", "")
        deg = deg_by.get(bid) if isinstance(deg_by.get(bid), dict) else {}
        prog = deg.get("progressive_degradation_detected", "") if isinstance(deg, dict) else ""
        lines.append(
            "| "
            + " | ".join(
                (
                    f"`{bid}`",
                    str(scripted),
                    str(executed),
                    _md_cell(cls),
                    _md_cell(score),
                    _md_cell(open_v),
                    _md_cell(prog),
                ),
            )
            + " |",
        )

    lines += [
        "",
        "## Divergence (cross-branch)",
        "",
        f"- **Divergence score:** {div_score}",
        f"- **Distinct outcomes detected:** {div_distinct}",
        f"- **Shared prompt bleed:** {div_bleed}",
        f"- **Reason codes:** {', '.join(str(x) for x in (div.get('reason_codes') or []) if x is not None) or '_(none)_'}",
        "",
        "## Degradation (per branch)",
        "",
    ]
    for bid in branches_run:
        deg = deg_by.get(bid) if isinstance(deg_by.get(bid), dict) else {}
        reasons = ", ".join(str(x) for x in (deg.get("reason_codes") or []) if x is not None) if isinstance(deg, dict) else ""
        prog = deg.get("progressive_degradation_detected") if isinstance(deg, dict) else None
        lines.append(f"- **`{bid}`:** progressive={prog}; reason_codes={reasons or '_(none)_'}")

    top_branch = ""
    top_axis = ""
    best_n = -1
    for r in branch_results:
        ev = r.eval_result
        fails = ev.get("detected_failures") or []
        n = len(fails) if isinstance(fails, list) else 0
        if n > best_n:
            best_n = n
            top_branch = r.branch_id_resolved
            top_axis = _suggested_debug_focus(ev) if n else ""
    lines += [
        "",
        "## Top blocking branch / axis",
        "",
    ]
    if best_n > 0:
        lines.append(f"- **Branch:** `{top_branch}` ({best_n} failure row(s))")
        lines.append(f"- **Suggested axis focus:** {top_axis}")
    else:
        lines.append("- _(no detected_failures rows across branches)_")

    lines.append("")
    return "\n".join(lines)


def write_aggregate_spine_artifacts(
    spine: ScenarioSpine,
    aggregate_dir: Path,
    branch_results: Sequence[BranchRunResult],
    *,
    smoke: bool,
    max_turns: int | None,
    run_timestamp: str,
) -> None:
    """Write spine-level aggregate JSON/Markdown under ``aggregate_dir`` (``…/<stamp>/<spine_id>/``)."""
    agg = build_aggregate_session_health_summary(
        spine,
        branch_results,
        smoke=smoke,
        max_turns=max_turns,
        run_timestamp=run_timestamp,
    )
    _write_json(aggregate_dir / "aggregate_session_health_summary.json", agg)
    _write_text(
        aggregate_dir / "aggregate_operator_summary.md",
        build_aggregate_operator_summary_md(spine, agg, branch_results),
    )


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
            out = payload if isinstance(payload, dict) else {"ok": False, "error": str(exc)}
            if "status_code" not in out:
                out = {**out, "status_code": exc.code}
            return out
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    return call


def run_scenario_spine_branch(
    spine: ScenarioSpine,
    branch: ScenarioBranch,
    *,
    branch_id_requested: str,
    chat_call: ChatCaller,
    apply_reset: bool,
    smoke: bool,
    max_turns: int | None,
    run_dir: Path,
    resume_entry_first_turn: bool = False,
) -> BranchRunResult:
    resolved = branch.branch_id
    limit = effective_turn_limit(len(branch.turns), smoke=smoke, max_turns=max_turns)
    turns_to_run: Sequence[ScenarioTurn] = branch.turns[:limit]
    scope_label = operator_branch_scope(len(branch.turns), len(turns_to_run), smoke_flag=smoke)

    if apply_reset:
        apply_new_campaign_hard_reset()

    if resume_entry_first_turn:
        from game.narrative_plan_upstream import mark_session_narration_resume_entry_pending
        from game.storage import load_session, save_session

        _sess = load_session()
        mark_session_narration_resume_entry_pending(_sess)
        save_session(_sess)

    debug_rows: list[dict[str, Any]] = []
    eval_rows: list[dict[str, Any]] = []

    for idx, st in enumerate(turns_to_run):
        payload = chat_call(st.player_prompt)
        if not isinstance(payload, dict):
            payload = {"ok": False, "error": "chat caller returned non-dict"}

        gm_text = _gm_text_from_chat_payload(payload)
        api_ok = bool(payload.get("ok", False))
        api_err = payload.get("error")
        res_kind = _resolution_kind(payload)

        meta_safe: dict[str, Any] = {}
        sc = payload.get("status_code")
        if isinstance(sc, int):
            meta_safe["status_code"] = sc
        if isinstance(payload, dict):
            meta_safe["opening_convergence"] = capture_opening_convergence_meta_from_chat_payload(payload)
            seam = _narration_seam_from_chat_payload(payload)
            if seam:
                meta_safe["narration_seam"] = seam

        eval_rows.append(
            {
                "turn_index": idx,
                "turn_id": st.turn_id,
                "player_prompt": st.player_prompt,
                "gm_text": gm_text,
                "api_ok": api_ok,
                "api_error": api_err,
                "resolution_kind": res_kind,
                "meta": meta_safe,
            },
        )
        debug_rows.append(
            {
                "turn_index": idx,
                "turn_id": st.turn_id,
                "player_prompt": st.player_prompt,
                "gm_text": gm_text,
                "api_ok": api_ok,
                "api_error": api_err,
                "resolution_kind": res_kind,
                "meta": meta_safe if meta_safe else None,
                "debug_traces": _session_debug_traces(payload),
                "chat_response": dict(payload) if isinstance(payload, dict) else payload,
            },
        )

    eval_result = evaluate_scenario_spine_session(spine, resolved, eval_rows)

    transcript = {
        "schema_version": 1,
        "spine_id": spine.spine_id,
        "branch_id": resolved,
        "branch_id_requested": branch_id_requested,
        "turn_count": len(eval_rows),
        "turns": eval_rows,
    }
    _write_json(run_dir / "transcript.json", transcript)
    _write_json(run_dir / "session_health_summary.json", eval_result)
    _write_json(
        run_dir / "run_debug.json",
        {
            "schema_version": 1,
            "spine_id": spine.spine_id,
            "branch_id_resolved": resolved,
            "branch_id_requested": branch_id_requested,
            "smoke": smoke,
            "max_turns": max_turns,
            "apply_reset": apply_reset,
            "resume_entry_first_turn": resume_entry_first_turn,
            "turns_debug": debug_rows,
        },
    )
    md = build_operator_summary_md(
        spine_id=spine.spine_id,
        branch_id=resolved,
        spine_branch_turns=len(branch.turns),
        executed_turns=len(turns_to_run),
        scope_label=scope_label,
        eval_result=eval_result,
    )
    _write_text(run_dir / "compact_operator_summary.md", md)

    return BranchRunResult(
        branch_id_requested=branch_id_requested,
        branch_id_resolved=resolved,
        run_dir=run_dir,
        eval_result=eval_result,
        executed_turns=len(turns_to_run),
        spine_branch_turns=len(branch.turns),
        scope_label=scope_label,
    )


def cmd_list(spine: ScenarioSpine) -> None:
    print(f"spine_id:\t{spine.spine_id}")
    print(f"title:\t{spine.title or '(untitled)'}")
    print("branches:")
    for b in sorted(spine.branches, key=lambda x: x.branch_id):
        eligible, note = branch_listing_labels(len(b.turns))
        elig_s = "yes" if eligible else "no"
        print(f"  {b.branch_id}\tturns={len(b.turns)}\tfull_length_eligible={elig_s}\t{note}")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="Run scenario-spine branches via /api/chat and write scenario_spine_eval artifacts.",
    )
    p.add_argument(
        "--spine",
        metavar="PATH_OR_ID",
        default=None,
        help=f"Spine JSON path or id under data/validation/scenario_spines/ (default: {DEFAULT_SPINE_PATH.relative_to(ROOT)}).",
    )
    p.add_argument("--branch", metavar="BRANCH_ID", help="Single branch id (aliases allowed).")
    p.add_argument("--all-branches", action="store_true", help="Run every branch in the spine.")
    p.add_argument("--list", action="store_true", help="Print spine summary and branch table, then exit.")
    p.add_argument(
        "--no-reset",
        action="store_true",
        help="Skip apply_new_campaign_hard_reset() before each branch (default: reset).",
    )
    p.add_argument(
        "--artifact-dir",
        type=Path,
        default=DEFAULT_ARTIFACT_ROOT,
        help="Root directory for timestamped runs (default: artifacts/scenario_spine_validation/).",
    )
    p.add_argument(
        "--base-url",
        default=None,
        metavar="URL",
        help="POST /api/chat to this origin. Omit for in-process FastAPI TestClient.",
    )
    p.add_argument(
        "--http-timeout",
        type=float,
        default=180.0,
        help="HTTP timeout seconds when --base-url is set (default: 180).",
    )
    p.add_argument(
        "--max-turns",
        type=int,
        default=None,
        metavar="N",
        help="Cap executed turns per branch (after smoke cap if both apply).",
    )
    p.add_argument(
        "--smoke",
        action="store_true",
        help=f"Limit turns to {SMOKE_TURN_CAP} (or lower if --max-turns is lower).",
    )
    p.add_argument(
        "--resume-entry-first-turn",
        action="store_true",
        help="After reset (if any), mark snapshot-resume pending on session before the first scripted turn.",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    spine_path = resolve_spine_path(args.spine)

    if not spine_path.is_file():
        print(f"Spine file not found: {spine_path}", file=sys.stderr)
        return 2

    spine, val_errs = load_spine(spine_path)
    if val_errs:
        print("Scenario spine validation failed:", file=sys.stderr)
        for e in val_errs:
            print(f"  - {e}", file=sys.stderr)
        return 1

    if args.list:
        cmd_list(spine)
        return 0

    if args.all_branches:
        branches_to_run = sorted(spine.branches, key=lambda b: b.branch_id)
        branch_requested: list[tuple[str, ScenarioBranch]] = [(b.branch_id, b) for b in branches_to_run]
    elif args.branch:
        br = get_branch(spine, args.branch)
        if br is None:
            known = ", ".join(sorted(b.branch_id for b in spine.branches))
            print(f"Unknown branch {args.branch!r}. Known: {known}", file=sys.stderr)
            return 2
        branch_requested = [(args.branch, br)]
    else:
        br = get_branch(spine, DEFAULT_BRANCH_ID)
        if br is None:
            print(f"Default branch {DEFAULT_BRANCH_ID!r} missing from spine.", file=sys.stderr)
            return 2
        branch_requested = [(DEFAULT_BRANCH_ID, br)]

    stamp = _utc_slug()
    base_out: Path = args.artifact_dir.resolve()
    apply_reset = not args.no_reset

    def _execute(chat_call: ChatCaller) -> int:
        results: list[BranchRunResult] = []
        for req_id, br_obj in branch_requested:
            resolved_id = br_obj.branch_id
            run_dir = base_out / stamp / spine.spine_id / resolved_id
            res = run_scenario_spine_branch(
                spine,
                br_obj,
                branch_id_requested=req_id,
                chat_call=chat_call,
                apply_reset=apply_reset,
                smoke=bool(args.smoke),
                max_turns=args.max_turns,
                run_dir=run_dir,
                resume_entry_first_turn=bool(args.resume_entry_first_turn),
            )
            results.append(res)
            print(f"Wrote {run_dir / 'transcript.json'}")
            print(f"Wrote {run_dir / 'session_health_summary.json'}")
            print(f"Wrote {run_dir / 'compact_operator_summary.md'}")

        if args.all_branches:
            agg_dir = base_out / stamp / spine.spine_id
            ts = datetime.now(timezone.utc).isoformat()
            write_aggregate_spine_artifacts(
                spine,
                agg_dir,
                results,
                smoke=bool(args.smoke),
                max_turns=args.max_turns,
                run_timestamp=ts,
            )
            print(f"Wrote {agg_dir / 'aggregate_session_health_summary.json'}")
            print(f"Wrote {agg_dir / 'aggregate_operator_summary.md'}")

        if args.all_branches and len(results) > 1:
            full_ids = [r.branch_id_resolved for r in results if r.scope_label == "full"]
            alt_ids = [r.branch_id_resolved for r in results if r.scope_label == "alternate_short"]
            sm_ids = [r.branch_id_resolved for r in results if r.scope_label == "smoke"]
            print("")
            print("All-branches summary:")
            print(f"  full-length runs: {', '.join(full_ids) or '(none)'}")
            print(f"  alternate-short branches: {', '.join(alt_ids) or '(none)'}")
            print(f"  smoke/partial runs: {', '.join(sm_ids) or '(none)'}")

        return 0

    if args.base_url:
        return _execute(_make_http_caller(args.base_url, timeout_s=args.http_timeout))

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
        if not isinstance(data, dict):
            return {"ok": False, "error": "json was not an object"}
        if "ok" not in data:
            data = {**data, "ok": resp.status_code < 400}
        return data

    with TestClient(app) as client:

        def chat_call(text: str) -> dict[str, Any]:
            return _post_json(client, text)

        return _execute(chat_call)


if __name__ == "__main__":
    raise SystemExit(main())
