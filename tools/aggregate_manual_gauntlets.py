#!/usr/bin/env python3
"""Read-only aggregation of manual gauntlet run artifacts (``*_summary.json`` anchors).

Scans an artifacts directory for per-run summaries and optional sibling JSON files,
then emits a compact JSON rollup and optional Markdown review under ``reports/``.

Does not execute gauntlets; see ``tools/run_manual_gauntlet.py`` for runs.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

AGGREGATE_REPORT_VERSION = 1
_SUMMARY_SUFFIX = "_summary.json"
_KEY_EVENTS_SUFFIX = "_key_events.json"
_SNIPPETS_SUFFIX = "_snippets.json"
_TRANSCRIPT_SUFFIX = "_transcript.md"


# --- discovery & paths ---


def discover_summary_paths(artifacts_dir: Path) -> list[Path]:
    """Return all ``*_summary.json`` paths under ``artifacts_dir`` (recursive)."""
    if not artifacts_dir.is_dir():
        return []
    return sorted(artifacts_dir.rglob(f"*{_SUMMARY_SUFFIX}"))


def artifact_base_from_summary_path(summary_path: Path) -> str:
    name = summary_path.name
    if not name.endswith(_SUMMARY_SUFFIX):
        raise ValueError(f"not a summary path: {summary_path}")
    return name[: -len(_SUMMARY_SUFFIX)]


def infer_sibling_paths(summary_path: Path) -> dict[str, Path]:
    base = artifact_base_from_summary_path(summary_path)
    parent = summary_path.parent
    return {
        "base": base,
        "summary": summary_path,
        "key_events": parent / f"{base}{_KEY_EVENTS_SUFFIX}",
        "snippets": parent / f"{base}{_SNIPPETS_SUFFIX}",
        "transcript": parent / f"{base}{_TRANSCRIPT_SUFFIX}",
    }


# --- JSON ---


def load_json_file(path: Path) -> tuple[Any | None, str | None]:
    """Load JSON from ``path``; on failure return ``(None, warning_message)``."""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as e:
        return None, f"read failed {path}: {e}"
    try:
        return json.loads(raw), None
    except json.JSONDecodeError as e:
        return None, f"invalid JSON {path}: {e}"


# --- normalization ---


def _coerce_str(val: Any) -> str | None:
    if val is None:
        return None
    s = str(val).strip()
    return s if s else None


def _coerce_int(val: Any) -> int | None:
    if val is None:
        return None
    if isinstance(val, bool):
        return None
    if isinstance(val, int):
        return val
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _parse_started_sort_key(started_utc: str | None, fallback_mtime: float) -> float:
    if started_utc:
        try:
            # Accept ...Z and offset-aware ISO from summaries
            s = started_utc.replace("Z", "+00:00")
            dt = datetime.fromisoformat(s)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.timestamp()
        except (TypeError, ValueError):
            pass
    return fallback_mtime


def normalize_run_bundle(
    summary_path: Path,
    *,
    warnings: list[str],
) -> dict[str, Any] | None:
    """Map one summary file (+ optional siblings) to a normalized run record."""
    data, w = load_json_file(summary_path)
    if w:
        warnings.append(w)
        return None
    if not isinstance(data, dict):
        warnings.append(f"summary is not an object: {summary_path}")
        return None

    siblings = infer_sibling_paths(summary_path)
    base = siblings["base"]

    operator_notes = _coerce_str(data.get("operator_notes"))
    if operator_notes is None:
        operator_notes = _coerce_str(data.get("notes"))

    transcript_path = _coerce_str(data.get("transcript_path"))
    if not transcript_path and siblings["transcript"].is_file():
        transcript_path = str(siblings["transcript"].resolve())

    event_count = _coerce_int(data.get("event_count"))
    key_events_path = siblings["key_events"]
    snippets_path = siblings["snippets"]

    ke_exists = key_events_path.is_file()
    sn_exists = snippets_path.is_file()

    if event_count is None and ke_exists:
        ke_data, ke_w = load_json_file(key_events_path)
        if ke_w:
            warnings.append(ke_w)
        elif isinstance(ke_data, list):
            event_count = len(ke_data)

    return {
        "artifact_base": base,
        "summary_path": str(summary_path.resolve()),
        "gauntlet_id": _coerce_str(data.get("gauntlet_id")) or "",
        "label": _coerce_str(data.get("label")) or "",
        "description": _coerce_str(data.get("description")) or "",
        "started_utc": _coerce_str(data.get("started_utc")),
        "turn_count": _coerce_int(data.get("turn_count")),
        "operator_verdict": _coerce_str(data.get("operator_verdict")),
        "operator_notes": operator_notes,
        "event_count": event_count if event_count is not None else 0,
        "transcript_path": transcript_path,
        "key_events_path": str(key_events_path.resolve()) if ke_exists else None,
        "snippets_path": str(snippets_path.resolve()) if sn_exists else None,
        "_sort_mtime": summary_path.stat().st_mtime,
    }


def filter_runs(
    runs: list[dict[str, Any]],
    *,
    gauntlet_id: str | None,
    objective: str | None,
    verdict: str | None,
) -> list[dict[str, Any]]:
    out = runs
    if gauntlet_id is not None:
        gid = gauntlet_id.strip().lower()
        out = [r for r in out if r.get("gauntlet_id", "").lower() == gid]
    if objective is not None:
        sub = objective.casefold()
        out = [
            r
            for r in out
            if sub in (r.get("label") or "").casefold()
            or sub in (r.get("description") or "").casefold()
        ]
    if verdict is not None:
        vwant = verdict.strip().casefold()
        out = [r for r in out if (r.get("operator_verdict") or "").strip().casefold() == vwant]
    return out


def sort_runs_newest_first(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def key(r: dict[str, Any]) -> float:
        return _parse_started_sort_key(r.get("started_utc"), float(r.get("_sort_mtime", 0)))

    return sorted(runs, key=key, reverse=True)


def strip_internal_fields(run: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in run.items() if not k.startswith("_")}


# --- aggregation ---


def verdict_rank(verdict: str | None) -> int:
    if not verdict:
        return 3
    v = verdict.strip().upper()
    if v == "FAIL":
        return 0
    if v == "PARTIAL":
        return 1
    if v == "PASS":
        return 2
    return 3


def compute_metrics(runs: list[dict[str, Any]]) -> dict[str, Any]:
    verdict_counts: Counter[str] = Counter()
    runs_with_verdict = 0
    turn_vals: list[int] = []
    gauntlet_ids: set[str] = set()
    started_dates: list[str] = []

    runs_with_events = 0
    runs_with_snippets = 0

    for r in runs:
        gv = r.get("operator_verdict")
        if gv:
            runs_with_verdict += 1
            verdict_counts[str(gv).strip().upper()] += 1
        tc = r.get("turn_count")
        if isinstance(tc, int):
            turn_vals.append(tc)
        gid = r.get("gauntlet_id")
        if gid:
            gauntlet_ids.add(str(gid))
        su = r.get("started_utc")
        if su:
            started_dates.append(str(su))

        ec = r.get("event_count")
        if isinstance(ec, int) and ec > 0:
            runs_with_events += 1

        sp = r.get("snippets_path")
        if sp:
            p = Path(sp)
            if p.is_file():
                data, _w = load_json_file(p)
                if isinstance(data, list) and len(data) > 0:
                    runs_with_snippets += 1

    avg_turn: float | None
    if turn_vals:
        avg_turn = round(sum(turn_vals) / len(turn_vals), 2)
    else:
        avg_turn = None

    date_range: dict[str, str | None] = {"min": None, "max": None}
    if started_dates:
        date_range["min"] = min(started_dates)
        date_range["max"] = max(started_dates)

    return {
        "total_runs": len(runs),
        "runs_with_verdict": runs_with_verdict,
        "verdict_counts": dict(sorted(verdict_counts.items())),
        "average_turn_count": avg_turn,
        "unique_gauntlet_ids": sorted(gauntlet_ids),
        "runs_with_events": runs_with_events,
        "runs_with_snippets": runs_with_snippets,
        "date_range_covered": date_range,
    }


def rollup_key_events(
    runs: list[dict[str, Any]],
    *,
    warnings: list[str],
) -> dict[str, Any]:
    by_name: Counter[str] = Counter()
    by_stage: Counter[str] = Counter()

    for r in runs:
        kp = r.get("key_events_path")
        if not kp:
            continue
        path = Path(kp)
        if not path.is_file():
            continue
        data, w = load_json_file(path)
        if w:
            warnings.append(w)
            continue
        if not isinstance(data, list):
            warnings.append(f"key_events is not an array: {path}")
            continue
        for ev in data:
            if not isinstance(ev, dict):
                continue
            name = ev.get("name")
            stage = ev.get("stage")
            if name is not None and str(name).strip():
                by_name[str(name).strip()] += 1
            if stage is not None and str(stage).strip():
                by_stage[str(stage).strip()] += 1

    return {
        "by_name": dict(by_name.most_common()),
        "by_stage": dict(by_stage.most_common()),
    }


def load_snippets_list(path: Path, warnings: list[str]) -> list[dict[str, Any]]:
    data, w = load_json_file(path)
    if w:
        warnings.append(w)
        return []
    if not isinstance(data, list):
        warnings.append(f"snippets is not an array: {path}")
        return []
    return [x for x in data if isinstance(x, dict)]


def build_compact_run_for_json(run: dict[str, Any]) -> dict[str, Any]:
    r = strip_internal_fields(run)
    # Keep paths relative-friendly but already absolute from normalization
    return {
        "gauntlet_id": r.get("gauntlet_id"),
        "label": r.get("label"),
        "started_utc": r.get("started_utc"),
        "operator_verdict": r.get("operator_verdict"),
        "operator_notes": r.get("operator_notes"),
        "turn_count": r.get("turn_count"),
        "event_count": r.get("event_count"),
        "summary_path": r.get("summary_path"),
        "transcript_path": r.get("transcript_path"),
        "key_events_path": r.get("key_events_path"),
        "snippets_path": r.get("snippets_path"),
    }


def render_markdown(
    aggregate: dict[str, Any],
    *,
    runs: list[dict[str, Any]],
    include_snippets: bool,
    warnings: list[str],
    max_snippet_examples: int = 8,
    max_snippet_runs: int = 5,
) -> str:
    lines: list[str] = []
    lines.append("# Manual gauntlet aggregate review")
    lines.append("")
    lines.append(f"- Generated (UTC): `{aggregate.get('generated_utc')}`")
    lines.append(f"- Source: `{aggregate.get('source_dir')}`")
    lines.append(f"- Runs in report: **{aggregate['metrics']['total_runs']}**")
    vc = aggregate["metrics"].get("verdict_counts") or {}
    if vc:
        lines.append(f"- Verdicts: {', '.join(f'{k}: {v}' for k, v in vc.items())}")
    lines.append("")

    flt = aggregate.get("filters") or {}
    if any(flt.get(k) for k in ("gauntlet_id", "objective", "verdict", "limit")):
        lines.append("## Filters applied")
        lines.append("")
        lines.append(f"```json\n{json.dumps(flt, indent=2)}\n```")
        lines.append("")

    if aggregate.get("event_rollup") and (
        aggregate["event_rollup"].get("by_name") or aggregate["event_rollup"].get("by_stage")
    ):
        lines.append("## Key event rollup (counts)")
        lines.append("")
        bn = aggregate["event_rollup"].get("by_name") or {}
        bs = aggregate["event_rollup"].get("by_stage") or {}
        if bn:
            lines.append("### By name (top 15)")
            for name, cnt in list(bn.items())[:15]:
                lines.append(f"- `{name}`: {cnt}")
            lines.append("")
        if bs:
            lines.append("### By stage (top 15)")
            for st, cnt in list(bs.items())[:15]:
                lines.append(f"- `{st}`: {cnt}")
            lines.append("")

    # Group by gauntlet_id; FAIL/PARTIAL first within each group
    by_gid: dict[str, list[dict[str, Any]]] = {}
    for r in runs:
        gid = r.get("gauntlet_id") or "(unknown)"
        by_gid.setdefault(str(gid), []).append(r)

    lines.append("## Runs by gauntlet")
    lines.append("")

    for gid in sorted(by_gid.keys(), key=lambda x: (x == "(unknown)", x.lower())):
        group = by_gid[gid]
        group.sort(key=lambda r: (verdict_rank(r.get("operator_verdict")), r.get("started_utc") or ""))
        lines.append(f"### `{gid}`")
        lines.append("")
        for r in group:
            v = r.get("operator_verdict") or "—"
            su = r.get("started_utc") or "—"
            tc = r.get("turn_count")
            tc_s = str(tc) if tc is not None else "—"
            label = (r.get("label") or "").replace("\n", " ")
            if len(label) > 120:
                label = label[:117] + "..."
            lines.append(f"- **{v}** · {su} · turns: {tc_s} · {label or '—'}")
            lines.append(f"  - summary: `{r.get('summary_path')}`")
            if r.get("transcript_path"):
                lines.append(f"  - transcript: `{r.get('transcript_path')}`")
        lines.append("")

    notes_runs = [strip_internal_fields(r) for r in runs if r.get("operator_notes")]
    if notes_runs:
        lines.append("## Operator notes")
        lines.append("")
        notes_runs.sort(key=lambda r: (verdict_rank(r.get("operator_verdict")), r.get("started_utc") or ""))
        for r in notes_runs:
            lines.append(f"### {r.get('gauntlet_id')} — {r.get('operator_verdict') or '—'} ({r.get('started_utc')})")
            lines.append("")
            lines.append(r.get("operator_notes") or "")
            lines.append("")

    if include_snippets:
        lines.append("## Notable snippets (sampled)")
        lines.append("")
        prio = sorted(
            runs,
            key=lambda r: (verdict_rank(r.get("operator_verdict")), -float(r.get("_sort_mtime", 0))),
        )
        shown = 0
        runs_used = 0
        for r in prio:
            if shown >= max_snippet_examples or runs_used >= max_snippet_runs:
                break
            sp = r.get("snippets_path")
            if not sp:
                continue
            path = Path(sp)
            if not path.is_file():
                continue
            snippets = load_snippets_list(path, warnings)
            if not snippets:
                continue
            runs_used += 1
            lines.append(
                f"### {r.get('gauntlet_id')} ({r.get('operator_verdict') or '—'}) — {path.name}"
            )
            lines.append("")
            for sn in snippets[:2]:
                if shown >= max_snippet_examples:
                    break
                kind = sn.get("kind", "?")
                turn = sn.get("turn", "?")
                reason = sn.get("reason") or ""
                lines.append(f"- Turn {turn} · **{kind}** · {reason}")
                before = sn.get("before")
                after = sn.get("after")
                if before:
                    lines.append(f"  - before: {str(before)[:300]}{'…' if len(str(before)) > 300 else ''}")
                if after:
                    lines.append(f"  - after: {str(after)[:300]}{'…' if len(str(after)) > 300 else ''}")
                shown += 1
            lines.append("")
            if shown >= max_snippet_examples:
                break
        if shown == 0:
            lines.append("_No snippet files loaded._")
            lines.append("")

    if warnings:
        lines.append("## Warnings")
        lines.append("")
        for w in warnings[:50]:
            lines.append(f"- {w}")
        if len(warnings) > 50:
            lines.append(f"- _… and {len(warnings) - 50} more_")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def print_stdout_summary(
    aggregate: dict[str, Any],
    *,
    json_path: Path | None,
    md_path: Path | None,
) -> None:
    m = aggregate.get("metrics") or {}
    print(f"Runs analyzed: {m.get('total_runs', 0)}")
    vc = m.get("verdict_counts") or {}
    if vc:
        parts = [f"{k}={v}" for k, v in vc.items()]
        print("Verdicts: " + ", ".join(parts))
    dr = (m.get("date_range_covered") or {}) if isinstance(m.get("date_range_covered"), dict) else {}
    if dr.get("min") and dr.get("max"):
        print(f"Date range: {dr['min']} … {dr['max']}")
    if json_path:
        print(f"Wrote JSON: {json_path.resolve()}")
    if md_path:
        print(f"Wrote Markdown: {md_path.resolve()}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Aggregate manual gauntlet *_summary.json artifacts.")
    p.add_argument(
        "--artifacts-dir",
        type=Path,
        default=ROOT / "artifacts" / "manual_gauntlets",
        help="Directory to scan for *_summary.json (default: artifacts/manual_gauntlets)",
    )
    p.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "artifacts" / "manual_gauntlets" / "reports",
        help="Directory for aggregate outputs (default: artifacts/manual_gauntlets/reports)",
    )
    p.add_argument("--limit", type=int, default=None, help="Keep only the N newest runs after filters.")
    p.add_argument("--gauntlet-id", type=str, default=None, help="Filter by gauntlet id (e.g. g5).")
    p.add_argument(
        "--objective",
        type=str,
        default=None,
        help="Filter: substring match on summary label or description (case-insensitive).",
    )
    p.add_argument(
        "--verdict",
        type=str,
        default=None,
        help="Filter by operator_verdict (case-insensitive, exact match).",
    )
    p.add_argument(
        "--include-events",
        action="store_true",
        help="Roll up key_events.json name/stage counts across runs.",
    )
    p.add_argument(
        "--include-snippets",
        action="store_true",
        help="Include a small sampled snippets section in Markdown output.",
    )
    p.add_argument("--json-only", action="store_true", help="Do not write the Markdown file.")
    p.add_argument("--stdout", action="store_true", help="Print a compact summary to the console.")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    artifacts_dir = args.artifacts_dir.resolve()
    output_dir = args.output_dir.resolve()

    warnings: list[str] = []
    if not artifacts_dir.is_dir():
        warnings.append(f"artifacts dir missing or not a directory: {artifacts_dir}")

    summary_paths = discover_summary_paths(artifacts_dir)
    runs_raw: list[dict[str, Any]] = []
    for sp in summary_paths:
        norm = normalize_run_bundle(sp, warnings=warnings)
        if norm:
            runs_raw.append(norm)

    runs = filter_runs(
        runs_raw,
        gauntlet_id=args.gauntlet_id,
        objective=args.objective,
        verdict=args.verdict,
    )
    runs = sort_runs_newest_first(runs)
    if args.limit is not None and args.limit >= 0:
        runs = runs[: args.limit]

    metrics = compute_metrics(runs)
    event_rollup: dict[str, Any] = {}
    if args.include_events:
        event_rollup = rollup_key_events(runs, warnings=warnings)

    now = datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%dT%H-%M-%SZ")
    generated_utc = now.strftime("%Y-%m-%dT%H:%M:%SZ")

    aggregate: dict[str, Any] = {
        "report_version": AGGREGATE_REPORT_VERSION,
        "generated_utc": generated_utc,
        "source_dir": str(artifacts_dir),
        "filters": {
            "gauntlet_id": args.gauntlet_id,
            "objective": args.objective,
            "verdict": args.verdict,
            "limit": args.limit,
        },
        "metrics": metrics,
        "event_rollup": event_rollup if args.include_events else {"by_name": {}, "by_stage": {}},
        "runs": [build_compact_run_for_json(r) for r in runs],
        "warnings": [],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    json_name = f"manual_gauntlet_aggregate_{stamp}.json"
    json_path = output_dir / json_name

    md_path: Path | None = None
    md_text = ""
    if not args.json_only:
        md_name = f"manual_gauntlet_aggregate_{stamp}.md"
        md_path = output_dir / md_name
        md_text = render_markdown(
            aggregate,
            runs=runs,
            include_snippets=bool(args.include_snippets),
            warnings=warnings,
        )

    aggregate["warnings"] = list(warnings)
    json_path.write_text(json.dumps(aggregate, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    if md_path is not None:
        md_path.write_text(md_text, encoding="utf-8")

    if args.stdout:
        print_stdout_summary(aggregate, json_path=json_path, md_path=md_path)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
