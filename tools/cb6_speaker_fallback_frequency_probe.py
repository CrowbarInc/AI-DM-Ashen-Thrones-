#!/usr/bin/env python3
"""CB6 — read-only speaker/fallback runtime frequency probe.

Aggregates existing measurement artifacts and BV3D-scoped FEM lineage scans.
Does not modify runtime behavior, replay acceptance, or emit-path modules.

Outputs:
  artifacts/cb6_speaker_fallback_frequency.json
  stdout summary (markdown-friendly)

Usage (repo root):
  py tools/cb6_speaker_fallback_frequency_probe.py
  py tools/cb6_speaker_fallback_frequency_probe.py --write-md docs/audits/CB6_probe_snapshot.md
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game.runtime_lineage_telemetry import (  # noqa: E402
    RUNTIME_LINEAGE_EVENT_FALLBACK_SELECTED,
    RUNTIME_LINEAGE_EVENT_SPEAKER_REPAIR,
    summarize_runtime_lineage_events,
)
from tools.bv3d_measurement_scope import scan_measurement_fem_turns  # noqa: E402
from tools.fallback_incidence_report import build_fallback_incidence_report  # noqa: E402

SCHEMA_VERSION = 1
OUT_JSON = ROOT / "artifacts" / "cb6_speaker_fallback_frequency.json"

BV1_SUMMARY = ROOT / "artifacts" / "bv1_fallback_summary.json"
BV1B_SUMMARY = ROOT / "artifacts" / "bv1b_fallback_summary.json"
BUG_RECURRENCE = ROOT / "artifacts" / "golden_replay" / "bug_recurrence_history.json"


def _load_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _pct(num: int, den: int) -> float | None:
    if den <= 0:
        return None
    return round(100.0 * num / den, 4)


def _iter_recurrence_rows(history: Mapping[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for section_key in ("key_forecasts", "keys", "recurrence_keys"):
        section = history.get(section_key)
        if isinstance(section, list):
            for row in section:
                if isinstance(row, dict):
                    rows.append({**row, "_source_section": section_key})
    forecast = history.get("recurrence_forecast")
    if isinstance(forecast, dict):
        nested = forecast.get("key_forecasts")
        if isinstance(nested, list):
            for row in nested:
                if isinstance(row, dict):
                    rows.append({**row, "_source_section": "recurrence_forecast.key_forecasts"})
    return rows


def _extract_recurrence_speaker_metrics(history: Mapping[str, Any]) -> dict[str, Any]:
    speaker_rows: list[dict[str, Any]] = []
    for row in _iter_recurrence_rows(history):
        rk = str(row.get("recurrence_key") or "")
        if "speaker" not in rk.lower():
            continue
        speaker_rows.append(
            {
                "recurrence_key": rk,
                "occurrence_count": row.get("occurrence_count"),
                "field_path": row.get("field_path"),
                "category": row.get("category"),
                "owner_drift_bucket": row.get("owner_drift_bucket"),
                "source_section": row.get("_source_section"),
            }
        )
    raw_projection_rows = sum(
        int(row.get("occurrence_count") or 0)
        for row in speaker_rows
        if "projection|selected_speaker_id" in str(row.get("recurrence_key") or "")
    )
    unique_defects_note = (
        "BV8A: 8 raw projection-key rows collapse to 1 historical defect "
        "(vocative_override_after_prior_continuity backfill duplication)."
    )
    return {
        "speaker_recurrence_key_count": len(speaker_rows),
        "raw_projection_key_row_count": raw_projection_rows,
        "speaker_recurrence_rows": speaker_rows,
        "dedupe_note": unique_defects_note,
        "protected_replay_regression_recurrence_rate": history.get("protected_replay_regression_recurrence_rate"),
        "highest_governance_load_owner": (
            (history.get("portfolio_governance_summary") or {}).get("highest_governance_load_owner")
            if isinstance(history.get("portfolio_governance_summary"), dict)
            else (
                (history.get("recurrence_forecast") or {}).get("forecast_summary", {}).get("highest_governance_load_owner")
                if isinstance(history.get("recurrence_forecast"), dict)
                and isinstance((history.get("recurrence_forecast") or {}).get("forecast_summary"), dict)
                else history.get("highest_governance_load_owner")
            )
        ),
    }


def _classify_fallback_event(kind: str | None) -> str:
    """Map fallback_kind tokens to CB6 fallback event families (read-side taxonomy)."""
    if not kind:
        return "unknown_fallback"
    k = kind.strip().lower()
    if "scene_opening" in k or k == "scene_opening":
        return "opening_fallback"
    if "visibility" in k or "referential_clarity" in k:
        return "visibility_fallback"
    if "sealed" in k:
        return "sealed_fallback"
    if "deterministic" in k or "opening_deterministic" in k:
        return "deterministic_fallback"
    if "sanitizer" in k:
        return "sanitizer_triggered_fallback"
    if "repair" in k or "prepared_emission" in k or "response_type" in k:
        return "repair_triggered_fallback"
    return "other_fallback"


def _fallback_family_counts(report: Mapping[str, Any]) -> dict[str, int]:
    freq = report.get("frequency")
    kinds: dict[str, int] = {}
    if isinstance(freq, dict):
        raw = freq.get("fallback_kind")
        if isinstance(raw, dict):
            kinds = {str(k): int(v) for k, v in raw.items()}
    out: dict[str, int] = {}
    for kind, count in kinds.items():
        fam = _classify_fallback_event(kind)
        out[fam] = out.get(fam, 0) + count
    return dict(sorted(out.items()))


def _scan_bv3d_corpus() -> dict[str, Any]:
    turns, fem_count, _ = scan_measurement_fem_turns()
    events: list[dict[str, Any]] = []
    for turn in turns:
        meta = turn.get("meta") if isinstance(turn.get("meta"), dict) else {}
        lineage = meta.get("runtime_lineage_events")
        if isinstance(lineage, list):
            events.extend(e for e in lineage if isinstance(e, dict))
    lineage_summary = summarize_runtime_lineage_events(events)
    fallback_report = build_fallback_incidence_report(turns)
    speaker_event_count = int(lineage_summary.get("by_event_kind", {}).get(RUNTIME_LINEAGE_EVENT_SPEAKER_REPAIR, 0))
    fallback_turns = int(fallback_report.get("fallback_turn_count") or 0)
    eligible = int(fallback_report.get("eligible_turn_count") or fem_count)
    return {
        "measurement_scope": "BV3D",
        "eligible_fem_turns": eligible,
        "lineage_total_events": lineage_summary.get("total_events"),
        "speaker_repair_events": speaker_event_count,
        "speaker_repair_rate_pct": _pct(speaker_event_count, eligible),
        "speaker_repair_kinds": lineage_summary.get("speaker_repair_frequency") or {},
        "fallback_turns": fallback_turns,
        "fallback_trigger_rate_pct": round(float(fallback_report.get("fallback_trigger_rate") or 0) * 100, 4),
        "fallback_family_counts": _fallback_family_counts(fallback_report),
        "fallback_kind_raw": (fallback_report.get("frequency") or {}).get("fallback_kind") if isinstance(fallback_report.get("frequency"), dict) else {},
        "lineage_by_event_kind": lineage_summary.get("by_event_kind") or {},
    }


def build_cb6_report() -> dict[str, Any]:
    bv1 = _load_json(BV1_SUMMARY)
    bv1b = _load_json(BV1B_SUMMARY)
    recurrence = _extract_recurrence_speaker_metrics(_load_json(BUG_RECURRENCE))
    bv3d = _scan_bv3d_corpus()

    bv1_eligible = int(bv1.get("eligible_turn_count") or 0)
    bv1_fb = int(bv1.get("fallback_turn_count") or 0)
    bv1b_eligible = int(bv1b.get("eligible_turn_count") or 0)
    bv1b_fb = int(bv1b.get("fallback_turn_count") or 0)

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "advisory_only": True,
        "report_only": True,
        "measurement_sources": [
            str(BV1_SUMMARY.relative_to(ROOT)),
            str(BV1B_SUMMARY.relative_to(ROOT)),
            str(BUG_RECURRENCE.relative_to(ROOT)),
            "tools/bv3d_measurement_scope.py (live rescan)",
        ],
        "speaker_frequency": {
            "bv3d_corpus": {
                "speaker_repair_events": bv3d["speaker_repair_events"],
                "eligible_fem_turns": bv3d["eligible_fem_turns"],
                "speaker_repair_rate_pct": bv3d["speaker_repair_rate_pct"],
                "repair_kinds": bv3d["speaker_repair_kinds"],
            },
            "protected_replay_recurrence": recurrence,
            "event_definitions": {
                "speaker_adoption": "Post-emission speaker identity accepted without repair (inferred: no speaker_repair lineage event on turn).",
                "speaker_mismatch": "Protected replay field drift on selected_speaker_id or strict-social wrong-speaker scenario failure.",
                "speaker_relocation": "Route/target change with selected_speaker_id movement (protected: trace.canonical_entry.*, route_kind).",
                "speaker_correction": "Lineage event_kind=speaker_repair with repair_kind token (e.g. canonical_rewrite, narrator_neutral).",
                "speaker_override": "Vocative/direct-address override scenarios (protected: vocative_override_after_prior_continuity).",
                "speaker_finalize_divergence": "Finalize stack divergence between dialogue plan and emitted speaker (BX/BT parity probes; not separately counted in BV3D corpus).",
            },
        },
        "fallback_frequency": {
            "bv1_legacy_snapshot": {
                "eligible_fem_turns": bv1_eligible,
                "fallback_turns": bv1_fb,
                "fallback_trigger_rate_pct": round(float(bv1.get("fallback_trigger_rate") or 0) * 100, 4),
                "fallback_event_count": bv1.get("fallback_event_count"),
                "family_counts": _fallback_family_counts({"frequency": {"fallback_kind": (bv1.get("frequency") or {}).get("fallback_kind")}}),
            },
            "bv1b_bv3d_snapshot": {
                "eligible_fem_turns": bv1b_eligible,
                "fallback_turns": bv1b_fb,
                "fallback_trigger_rate_pct": round(float(bv1b.get("fallback_trigger_rate") or 0) * 100, 4),
                "fallback_event_count": bv1b.get("fallback_event_count"),
                "family_counts": _fallback_family_counts({"frequency": {"fallback_kind": (bv1b.get("frequency") or {}).get("fallback_kind")}}),
            },
            "bv3d_live_rescan": bv3d,
            "event_definitions": {
                "opening_fallback": "fallback_kind scene_opening or diegetic scene_opening family.",
                "visibility_fallback": "referential_clarity_hard_replacement / visibility selection owner paths.",
                "sealed_fallback": "sealed_passive_scene_pressure_fallback or sealed-gate owner bucket.",
                "deterministic_fallback": "opening_deterministic_fallback content owner or upstream_prepared opening.",
                "sanitizer_triggered_fallback": "sanitizer_* protected fields or sanitizer stage lineage (sparse in artifact corpus).",
                "repair_triggered_fallback": "response_type_prepared_emission, gate_terminal_repair realization family, repair-triggered replacements.",
            },
        },
        "replay_vs_runtime_comparison": {
            "protected_replay_speaker_recurrence": {
                "raw_projection_row_count": recurrence.get("raw_projection_key_row_count"),
                "unique_historical_defects": 1,
                "note": recurrence.get("dedupe_note"),
            },
            "observed_runtime_speaker_repair_rate_pct_bv3d": bv3d["speaker_repair_rate_pct"],
            "observed_runtime_fallback_trigger_rate_pct_bv1_legacy": round(float(bv1.get("fallback_trigger_rate") or 0) * 100, 4),
            "observed_runtime_fallback_trigger_rate_pct_bv3d": bv3d["fallback_trigger_rate_pct"],
            "interpretation": (
                "Protected replay recurrence measures acceptance failures and governance keys, not turn-level "
                "incidence. Runtime artifact incidence varies sharply by corpus scope (legacy 69% vs BV3D 1%)."
            ),
        },
        "confidence_assessment": {
            "speaker_runtime_incidence": "low",
            "fallback_runtime_incidence": "medium",
            "replay_recurrence_separation": "high",
            "rationale": {
                "speaker": "BV3D corpus shows 0 speaker_repair events across 95 FEM turns; recurrence history is protected-replay-only and backfill-inflated.",
                "fallback": "BV1B/BV3D agree at 1.05% on scoped corpus; legacy BV1 snapshot remains 69.16% on wider artifact set — scope dominates rate.",
            },
        },
    }


def _render_md(report: dict[str, Any]) -> str:
    sp = report["speaker_frequency"]["bv3d_corpus"]
    fb_legacy = report["fallback_frequency"]["bv1_legacy_snapshot"]
    fb_current = report["fallback_frequency"]["bv3d_live_rescan"]
    rec = report["speaker_frequency"]["protected_replay_recurrence"]
    lines = [
        "# CB6 Probe Snapshot (generated)",
        "",
        f"Generated: {report['generated_at']}",
        "",
        "## Speaker (BV3D corpus)",
        f"- speaker_repair_events: {sp['speaker_repair_events']} / {sp['eligible_fem_turns']} FEM turns ({sp['speaker_repair_rate_pct']}%)",
        f"- protected recurrence raw projection rows: {rec.get('raw_projection_key_row_count')} (unique defects: 1 per BV8A)",
        "",
        "## Fallback",
        f"- BV1 legacy rate: {fb_legacy['fallback_trigger_rate_pct']}% ({fb_legacy['fallback_turns']}/{fb_legacy['eligible_fem_turns']})",
        f"- BV3D rate: {fb_current['fallback_trigger_rate_pct']}% ({fb_current['fallback_turns']}/{fb_current['eligible_fem_turns']})",
        "",
    ]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=OUT_JSON,
        help=f"JSON output path (default: {OUT_JSON.relative_to(ROOT)})",
    )
    parser.add_argument("--write-md", type=Path, default=None, help="Optional markdown snapshot path.")
    args = parser.parse_args(argv)

    report = build_cb6_report()
    out_path = args.output.resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(_render_md(report))
    print(f"Wrote {out_path}")
    if args.write_md is not None:
        args.write_md.write_text(_render_md(report) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
