#!/usr/bin/env python3
"""Advisory comparator for two scenario-spine artifact directories.

This tool is report-only. It reads already-written artifacts and never changes
runtime behavior, protected gates, or evaluator outcomes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from game.runtime_lineage_telemetry import normalize_runtime_lineage_events, summarize_runtime_lineage_events  # noqa: E402

SCORECARD_SCHEMA_VERSION = 1
RUNTIME_LINEAGE_FREQUENCY_KEYS = (
    "by_event_kind",
    "by_stage",
    "fallback_frequency",
    "fallback_authorship_frequency",
    "fallback_owner_bucket_frequency",
    "fallback_selection_owner_frequency",
    "fallback_content_owner_frequency",
    "speaker_repair_frequency",
    "mutation_kind_frequency",
    "gate_path_frequency",
    "by_recurrence_key",
)


def _read_json(path: Path) -> tuple[dict[str, Any], str | None]:
    if not path.is_file():
        return {}, "missing"
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {}, f"unreadable: {exc}"
    if not isinstance(raw, dict):
        return {}, "not_a_json_object"
    return raw, None


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def stable_text_fingerprint(text: Any) -> str | None:
    if text is None:
        return None
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()[:16]


def _as_turns(transcript: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    turns = transcript.get("turns")
    if not isinstance(turns, list):
        return []
    return [turn for turn in turns if isinstance(turn, Mapping)]


def _lookup_path(value: Mapping[str, Any], path: Sequence[str]) -> Any:
    cur: Any = value
    for part in path:
        if not isinstance(cur, Mapping):
            return None
        cur = cur.get(part)
    return cur


def _first_present(*values: Any) -> Any:
    for value in values:
        if value is not None:
            return value
    return None


def _turn_meta(turn: Mapping[str, Any]) -> Mapping[str, Any]:
    meta = turn.get("meta")
    return meta if isinstance(meta, Mapping) else {}


def _turn_fem(turn: Mapping[str, Any]) -> Mapping[str, Any]:
    fem = _turn_meta(turn).get("final_emission_meta")
    return fem if isinstance(fem, Mapping) else {}


def _turn_route(turn: Mapping[str, Any]) -> Any:
    meta = _turn_meta(turn)
    return _first_present(
        turn.get("route_kind"),
        turn.get("resolution_kind"),
        _lookup_path(meta, ("golden_replay_observation", "route_kind")),
        _lookup_path(meta, ("scenario_spine", "route_kind")),
    )


def _turn_speaker(turn: Mapping[str, Any]) -> Any:
    meta = _turn_meta(turn)
    return _first_present(
        turn.get("selected_speaker_id"),
        _lookup_path(meta, ("golden_replay_observation", "selected_speaker_id")),
        _lookup_path(meta, ("scenario_spine", "selected_speaker_id")),
        _lookup_path(_turn_fem(turn), ("selected_speaker_id",)),
    )


def _turn_fallback(turn: Mapping[str, Any]) -> Any:
    meta = _turn_meta(turn)
    fem = _turn_fem(turn)
    return _first_present(
        turn.get("fallback_family"),
        _lookup_path(meta, ("golden_replay_observation", "fallback_family")),
        fem.get("fallback_family_used"),
        fem.get("realization_fallback_family"),
        fem.get("final_emitted_source") if fem.get("final_route") == "replaced" else None,
    )


def _turn_text(turn: Mapping[str, Any]) -> Any:
    return _first_present(turn.get("gm_text"), turn.get("final_text"), turn.get("player_facing_text"))


def _turn_id(turn: Mapping[str, Any], index: int) -> str:
    value = _first_present(turn.get("turn_id"), turn.get("id"), turn.get("turn_index"), index)
    return str(value)


def _counter_dict(values: Sequence[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(v) for v in values if v is not None and str(v).strip()).items()))


def _frequency_delta(previous: Mapping[str, Any], current: Mapping[str, Any]) -> dict[str, Any]:
    prev = {str(k): int(v) for k, v in previous.items() if not isinstance(v, bool)}
    cur = {str(k): int(v) for k, v in current.items() if not isinstance(v, bool)}
    keys = sorted(set(prev) | set(cur))
    delta = {key: cur.get(key, 0) - prev.get(key, 0) for key in keys if cur.get(key, 0) != prev.get(key, 0)}
    return {
        "previous": dict(sorted(prev.items())),
        "current": dict(sorted(cur.items())),
        "delta": delta,
        "changed_key_count": len(delta),
    }


def _value_delta(previous: Any, current: Any) -> dict[str, Any]:
    return {"previous": previous, "current": current, "changed": previous != current}


def _identity_from_artifacts(transcript: Mapping[str, Any], health: Mapping[str, Any]) -> dict[str, Any]:
    sh = health.get("session_health") if isinstance(health.get("session_health"), Mapping) else {}
    first_meta: Mapping[str, Any] = {}
    turns = _as_turns(transcript)
    if turns:
        meta = _turn_meta(turns[0]).get("scenario_spine")
        first_meta = meta if isinstance(meta, Mapping) else {}
    return {
        "spine_id": _first_present(transcript.get("spine_id"), health.get("spine_id"), first_meta.get("spine_id")),
        "branch_id": _first_present(
            transcript.get("branch_id"),
            transcript.get("branch_id_resolved"),
            health.get("branch_id"),
            sh.get("branch_id"),
            first_meta.get("branch_id"),
        ),
    }


def _health_metrics(health: Mapping[str, Any]) -> dict[str, Any]:
    sh = health.get("session_health") if isinstance(health.get("session_health"), Mapping) else {}
    axes = health.get("axes") if isinstance(health.get("axes"), Mapping) else {}
    detected = health.get("detected_failures") if isinstance(health.get("detected_failures"), list) else []
    warnings = health.get("warnings") if isinstance(health.get("warnings"), list) else []
    checkpoints = health.get("checkpoint_results") if isinstance(health.get("checkpoint_results"), list) else []
    degradation = health.get("degradation_over_time") if isinstance(health.get("degradation_over_time"), Mapping) else {}

    axis_warning_counts: dict[str, int] = {}
    axis_failure_counts: dict[str, int] = {}
    tracked_axis_warning_counts: dict[str, int] = {}
    tracked_axis_failure_counts: dict[str, int] = {}
    for axis_name, axis in axes.items():
        if not isinstance(axis, Mapping):
            continue
        warnings_for_axis = axis.get("warning_codes") if isinstance(axis.get("warning_codes"), list) else []
        failures_for_axis = axis.get("failure_codes") if isinstance(axis.get("failure_codes"), list) else []
        axis_warning_counts[str(axis_name)] = len(warnings_for_axis)
        axis_failure_counts[str(axis_name)] = len(failures_for_axis)
        if any(token in str(axis_name) for token in ("continuity", "progression", "referent")):
            tracked_axis_warning_counts[str(axis_name)] = len(warnings_for_axis)
            tracked_axis_failure_counts[str(axis_name)] = len(failures_for_axis)

    checkpoint_issue_codes: Counter[str] = Counter()
    for checkpoint in checkpoints:
        if not isinstance(checkpoint, Mapping):
            continue
        issues = checkpoint.get("issues")
        if not isinstance(issues, list):
            continue
        for issue in issues:
            if isinstance(issue, Mapping):
                code = issue.get("code")
                if code is not None and str(code).strip():
                    checkpoint_issue_codes[str(code)] += 1

    return {
        "classification": sh.get("classification"),
        "status": _first_present(sh.get("status"), health.get("status")),
        "score": sh.get("score"),
        "overall_passed": sh.get("overall_passed"),
        "turn_count": _first_present(sh.get("turn_count"), health.get("turn_count")),
        "warning_count": len(warnings),
        "detected_failure_count": len(detected),
        "axis_warning_counts": dict(sorted(axis_warning_counts.items())),
        "axis_failure_counts": dict(sorted(axis_failure_counts.items())),
        "tracked_axis_warning_counts": dict(sorted(tracked_axis_warning_counts.items())),
        "tracked_axis_failure_counts": dict(sorted(tracked_axis_failure_counts.items())),
        "checkpoint_issue_counts": dict(sorted(checkpoint_issue_codes.items())),
        "degradation_reason_counts": _counter_dict(degradation.get("reason_codes") if isinstance(degradation.get("reason_codes"), list) else []),
        "progressive_degradation_detected": degradation.get("progressive_degradation_detected"),
    }


def _health_delta(previous: Mapping[str, Any], current: Mapping[str, Any]) -> dict[str, Any]:
    fields = ("classification", "status", "score", "overall_passed", "turn_count", "warning_count", "detected_failure_count", "progressive_degradation_detected")
    out = {field: _value_delta(previous.get(field), current.get(field)) for field in fields}
    out["axis_warning_counts"] = _frequency_delta(previous.get("axis_warning_counts", {}), current.get("axis_warning_counts", {}))
    out["axis_failure_counts"] = _frequency_delta(previous.get("axis_failure_counts", {}), current.get("axis_failure_counts", {}))
    out["tracked_axis_warning_counts"] = _frequency_delta(
        previous.get("tracked_axis_warning_counts", {}),
        current.get("tracked_axis_warning_counts", {}),
    )
    out["tracked_axis_failure_counts"] = _frequency_delta(
        previous.get("tracked_axis_failure_counts", {}),
        current.get("tracked_axis_failure_counts", {}),
    )
    out["checkpoint_issue_counts"] = _frequency_delta(previous.get("checkpoint_issue_counts", {}), current.get("checkpoint_issue_counts", {}))
    out["degradation_reason_counts"] = _frequency_delta(previous.get("degradation_reason_counts", {}), current.get("degradation_reason_counts", {}))
    changed_fields = [
        key
        for key, value in out.items()
        if (isinstance(value, Mapping) and (value.get("changed") is True or value.get("changed_key_count", 0) > 0))
    ]
    return {"previous": previous, "current": current, "deltas": out, "changed_fields": changed_fields}


def _runtime_lineage_events_from_transcript(transcript: Mapping[str, Any]) -> list[dict[str, Any]]:
    events: list[Any] = []
    for turn in _as_turns(transcript):
        meta = _turn_meta(turn)
        raw = meta.get("runtime_lineage_events")
        if isinstance(raw, list):
            events.extend(raw)
    return normalize_runtime_lineage_events(events)


def _runtime_lineage_summary(run_dir: Path, transcript: Mapping[str, Any]) -> tuple[dict[str, Any], str]:
    raw, error = _read_json(run_dir / "runtime_lineage_summary.json")
    if error is None:
        return raw, "runtime_lineage_summary.json"
    events = _runtime_lineage_events_from_transcript(transcript)
    if events:
        return summarize_runtime_lineage_events(events), "derived_from_transcript"
    return {}, "unavailable"


def _runtime_lineage_delta(previous: Mapping[str, Any], current: Mapping[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {
        "previous_total_events": int(previous.get("total_events") or 0),
        "current_total_events": int(current.get("total_events") or 0),
        "total_event_delta": int(current.get("total_events") or 0) - int(previous.get("total_events") or 0),
        "frequency_deltas": {},
    }
    changed = 0
    for key in RUNTIME_LINEAGE_FREQUENCY_KEYS:
        delta = _frequency_delta(
            previous.get(key) if isinstance(previous.get(key), Mapping) else {},
            current.get(key) if isinstance(current.get(key), Mapping) else {},
        )
        out["frequency_deltas"][key] = delta
        changed += int(delta["changed_key_count"])
    out["changed_key_count"] = changed
    return out


def _transcript_metrics(transcript: Mapping[str, Any]) -> dict[str, Any]:
    turns = _as_turns(transcript)
    return {
        "turn_count": int(transcript.get("turn_count") or len(turns)),
        "routes": _counter_dict([_turn_route(turn) for turn in turns]),
        "speakers": _counter_dict([_turn_speaker(turn) for turn in turns]),
        "fallbacks": _counter_dict([_turn_fallback(turn) for turn in turns]),
        "text_fingerprints": [stable_text_fingerprint(_turn_text(turn)) for turn in turns],
    }


def _transcript_delta(previous: Mapping[str, Any], current: Mapping[str, Any]) -> dict[str, Any]:
    prev_turns = _as_turns(previous)
    cur_turns = _as_turns(current)
    compared = min(len(prev_turns), len(cur_turns))
    per_turn: list[dict[str, Any]] = []
    route_delta_count = 0
    speaker_delta_count = 0
    fallback_delta_count = 0
    text_fingerprint_delta_count = 0

    for index in range(compared):
        prev = prev_turns[index]
        cur = cur_turns[index]
        deltas: dict[str, Any] = {}
        for field, getter in (
            ("route", _turn_route),
            ("speaker", _turn_speaker),
            ("fallback", _turn_fallback),
        ):
            prev_value = getter(prev)
            cur_value = getter(cur)
            if prev_value != cur_value:
                deltas[field] = {"previous": prev_value, "current": cur_value}
                if field == "route":
                    route_delta_count += 1
                elif field == "speaker":
                    speaker_delta_count += 1
                elif field == "fallback":
                    fallback_delta_count += 1
        prev_hash = stable_text_fingerprint(_turn_text(prev))
        cur_hash = stable_text_fingerprint(_turn_text(cur))
        if prev_hash != cur_hash:
            text_fingerprint_delta_count += 1
            deltas["text_fingerprint"] = {"previous": prev_hash, "current": cur_hash}
        if deltas:
            per_turn.append(
                {
                    "turn_index": index,
                    "previous_turn_id": _turn_id(prev, index),
                    "current_turn_id": _turn_id(cur, index),
                    "deltas": deltas,
                },
            )

    prev_metrics = _transcript_metrics(previous)
    cur_metrics = _transcript_metrics(current)
    return {
        "previous": prev_metrics,
        "current": cur_metrics,
        "total_turns_compared": compared,
        "extra_previous_turn_count": max(0, len(prev_turns) - compared),
        "extra_current_turn_count": max(0, len(cur_turns) - compared),
        "turn_count_delta": int(cur_metrics["turn_count"]) - int(prev_metrics["turn_count"]),
        "route_delta_count": route_delta_count,
        "speaker_delta_count": speaker_delta_count,
        "fallback_delta_count": fallback_delta_count,
        "text_fingerprint_delta_count": text_fingerprint_delta_count,
        "frequencies": {
            "routes": _frequency_delta(prev_metrics["routes"], cur_metrics["routes"]),
            "speakers": _frequency_delta(prev_metrics["speakers"], cur_metrics["speakers"]),
            "fallbacks": _frequency_delta(prev_metrics["fallbacks"], cur_metrics["fallbacks"]),
        },
        "per_turn_deltas": per_turn,
    }


def compare_scenario_spine_rerun_dirs(previous_dir: Path | str, current_dir: Path | str) -> dict[str, Any]:
    previous_path = Path(previous_dir)
    current_path = Path(current_dir)
    previous_transcript, previous_transcript_error = _read_json(previous_path / "transcript.json")
    current_transcript, current_transcript_error = _read_json(current_path / "transcript.json")
    previous_health, previous_health_error = _read_json(previous_path / "session_health_summary.json")
    current_health, current_health_error = _read_json(current_path / "session_health_summary.json")
    previous_branch_divergence, previous_branch_divergence_error = _read_json(previous_path / "branch_divergence.json")
    current_branch_divergence, current_branch_divergence_error = _read_json(current_path / "branch_divergence.json")

    previous_identity = _identity_from_artifacts(previous_transcript, previous_health)
    current_identity = _identity_from_artifacts(current_transcript, current_health)
    identity_mismatch_fields = [
        key for key in ("spine_id", "branch_id") if previous_identity.get(key) != current_identity.get(key)
    ]

    previous_lineage, previous_lineage_source = _runtime_lineage_summary(previous_path, previous_transcript)
    current_lineage, current_lineage_source = _runtime_lineage_summary(current_path, current_transcript)
    previous_health_metrics = _health_metrics(previous_health)
    current_health_metrics = _health_metrics(current_health)
    transcript_delta = _transcript_delta(previous_transcript, current_transcript)
    health_delta = _health_delta(previous_health_metrics, current_health_metrics)
    lineage_delta = _runtime_lineage_delta(previous_lineage, current_lineage)

    return {
        "schema_version": SCORECARD_SCHEMA_VERSION,
        "report_only": True,
        "previous_dir": str(previous_path),
        "current_dir": str(current_path),
        "missing_or_unavailable": {
            "previous": {
                "transcript.json": previous_transcript_error,
                "session_health_summary.json": previous_health_error,
                "runtime_lineage_summary.json": None if previous_lineage_source == "runtime_lineage_summary.json" else previous_lineage_source,
                "branch_divergence.json": previous_branch_divergence_error,
            },
            "current": {
                "transcript.json": current_transcript_error,
                "session_health_summary.json": current_health_error,
                "runtime_lineage_summary.json": None if current_lineage_source == "runtime_lineage_summary.json" else current_lineage_source,
                "branch_divergence.json": current_branch_divergence_error,
            },
        },
        "identity": {
            "previous": previous_identity,
            "current": current_identity,
            "mismatch": bool(identity_mismatch_fields),
            "mismatch_fields": identity_mismatch_fields,
        },
        "summary": {
            "identity_mismatch": bool(identity_mismatch_fields),
            "turn_count_delta": transcript_delta["turn_count_delta"],
            "route_delta_count": transcript_delta["route_delta_count"],
            "speaker_delta_count": transcript_delta["speaker_delta_count"],
            "fallback_delta_count": transcript_delta["fallback_delta_count"],
            "text_fingerprint_delta_count": transcript_delta["text_fingerprint_delta_count"],
            "health_changed_field_count": len(health_delta["changed_fields"]),
            "runtime_lineage_changed_key_count": lineage_delta["changed_key_count"],
            "runtime_lineage_total_event_delta": lineage_delta["total_event_delta"],
        },
        "transcript": transcript_delta,
        "health": health_delta,
        "runtime_lineage": {
            "previous_source": previous_lineage_source,
            "current_source": current_lineage_source,
            "previous": previous_lineage,
            "current": current_lineage,
            "delta": lineage_delta,
        },
        "branch_divergence": {
            "previous_available": previous_branch_divergence_error is None,
            "current_available": current_branch_divergence_error is None,
            "previous": previous_branch_divergence,
            "current": current_branch_divergence,
            "changed": previous_branch_divergence != current_branch_divergence,
        },
    }


def _cell(value: Any) -> str:
    text = str(value if value is not None else "")
    return text.replace("|", "\\|").replace("\n", " ") or "—"


def render_scenario_spine_rerun_delta_markdown(scorecard: Mapping[str, Any]) -> str:
    identity = scorecard.get("identity") if isinstance(scorecard.get("identity"), Mapping) else {}
    summary = scorecard.get("summary") if isinstance(scorecard.get("summary"), Mapping) else {}
    transcript = scorecard.get("transcript") if isinstance(scorecard.get("transcript"), Mapping) else {}
    health = scorecard.get("health") if isinstance(scorecard.get("health"), Mapping) else {}
    lineage = scorecard.get("runtime_lineage") if isinstance(scorecard.get("runtime_lineage"), Mapping) else {}
    missing = scorecard.get("missing_or_unavailable") if isinstance(scorecard.get("missing_or_unavailable"), Mapping) else {}
    branch_divergence = scorecard.get("branch_divergence") if isinstance(scorecard.get("branch_divergence"), Mapping) else {}

    lines = [
        "# Scenario-Spine Rerun Delta Advisory",
        "",
        "- Report only: `true`",
        f"- Previous dir: `{scorecard.get('previous_dir')}`",
        f"- Current dir: `{scorecard.get('current_dir')}`",
        "",
        "## Operator Summary",
        "",
    ]
    if identity.get("mismatch"):
        lines.append(f"- **Identity mismatch:** `{identity.get('mismatch_fields', [])}`")
    else:
        lines.append("- Identity mismatch: `false`")
    lines.extend(
        [
            f"- Turn count delta: `{summary.get('turn_count_delta', 0)}`",
            f"- Route / speaker / fallback deltas: `{summary.get('route_delta_count', 0)}` / `{summary.get('speaker_delta_count', 0)}` / `{summary.get('fallback_delta_count', 0)}`",
            f"- Text fingerprint deltas: `{summary.get('text_fingerprint_delta_count', 0)}`",
            f"- Health changed fields: `{summary.get('health_changed_field_count', 0)}`",
            f"- Runtime-lineage changed keys / event delta: `{summary.get('runtime_lineage_changed_key_count', 0)}` / `{summary.get('runtime_lineage_total_event_delta', 0)}`",
            "",
            "## Identity",
            "",
            f"- Previous: `{identity.get('previous', {})}`",
            f"- Current: `{identity.get('current', {})}`",
            "",
            "## Availability",
            "",
        ],
    )
    for side in ("previous", "current"):
        values = missing.get(side) if isinstance(missing.get(side), Mapping) else {}
        unavailable = {k: v for k, v in values.items() if v}
        lines.append(f"- {side.title()}: `{unavailable or {}}`")

    health_deltas = health.get("deltas") if isinstance(health.get("deltas"), Mapping) else {}
    lines.extend(["", "## Health Delta", ""])
    for key in ("classification", "status", "score", "overall_passed", "warning_count", "detected_failure_count", "progressive_degradation_detected"):
        delta = health_deltas.get(key) if isinstance(health_deltas.get(key), Mapping) else {}
        if delta.get("changed"):
            lines.append(f"- {key}: `{delta.get('previous')}` -> `{delta.get('current')}`")
    for key, label in (
        ("tracked_axis_warning_counts", "Continuity/progression/referent warnings"),
        ("tracked_axis_failure_counts", "Continuity/progression/referent failures"),
        ("checkpoint_issue_counts", "Checkpoint issues"),
        ("degradation_reason_counts", "Degradation reasons"),
    ):
        delta = health_deltas.get(key) if isinstance(health_deltas.get(key), Mapping) else {}
        lines.append(f"- {label}: `{delta.get('delta', {})}`")

    frequencies = transcript.get("frequencies") if isinstance(transcript.get("frequencies"), Mapping) else {}
    lines.extend(
        [
            "",
            "## Transcript Delta",
            "",
            f"- Route frequency deltas: `{(frequencies.get('routes') or {}).get('delta', {}) if isinstance(frequencies.get('routes'), Mapping) else {}}`",
            f"- Speaker frequency deltas: `{(frequencies.get('speakers') or {}).get('delta', {}) if isinstance(frequencies.get('speakers'), Mapping) else {}}`",
            f"- Fallback frequency deltas: `{(frequencies.get('fallbacks') or {}).get('delta', {}) if isinstance(frequencies.get('fallbacks'), Mapping) else {}}`",
            "",
            "| Turn | Previous Turn ID | Current Turn ID | Drift Fields |",
            "|---:|---|---|---|",
        ],
    )
    rows = transcript.get("per_turn_deltas") if isinstance(transcript.get("per_turn_deltas"), list) else []
    if rows:
        for row in rows[:20]:
            if not isinstance(row, Mapping):
                continue
            deltas = row.get("deltas") if isinstance(row.get("deltas"), Mapping) else {}
            lines.append(
                "| "
                + " | ".join(
                    [
                        _cell(row.get("turn_index")),
                        _cell(row.get("previous_turn_id")),
                        _cell(row.get("current_turn_id")),
                        _cell(", ".join(str(k) for k in sorted(deltas)) or "none"),
                    ],
                )
                + " |",
            )
    else:
        lines.append("| — | — | — | none |")

    lineage_delta = lineage.get("delta") if isinstance(lineage.get("delta"), Mapping) else {}
    lineage_freqs = lineage_delta.get("frequency_deltas") if isinstance(lineage_delta.get("frequency_deltas"), Mapping) else {}
    lines.extend(
        [
            "",
            "## Runtime Lineage Delta",
            "",
            f"- Previous source: `{lineage.get('previous_source', 'unavailable')}`",
            f"- Current source: `{lineage.get('current_source', 'unavailable')}`",
            f"- Total event delta: `{lineage_delta.get('total_event_delta', 0)}`",
            f"- Event kind deltas: `{(lineage_freqs.get('by_event_kind') or {}).get('delta', {}) if isinstance(lineage_freqs.get('by_event_kind'), Mapping) else {}}`",
            f"- Fallback kind deltas: `{(lineage_freqs.get('fallback_frequency') or {}).get('delta', {}) if isinstance(lineage_freqs.get('fallback_frequency'), Mapping) else {}}`",
            f"- Speaker repair deltas: `{(lineage_freqs.get('speaker_repair_frequency') or {}).get('delta', {}) if isinstance(lineage_freqs.get('speaker_repair_frequency'), Mapping) else {}}`",
            f"- Mutation kind deltas: `{(lineage_freqs.get('mutation_kind_frequency') or {}).get('delta', {}) if isinstance(lineage_freqs.get('mutation_kind_frequency'), Mapping) else {}}`",
            f"- Gate path deltas: `{(lineage_freqs.get('gate_path_frequency') or {}).get('delta', {}) if isinstance(lineage_freqs.get('gate_path_frequency'), Mapping) else {}}`",
            "",
            "## Branch Divergence",
            "",
            f"- Previous available: `{branch_divergence.get('previous_available', False)}`",
            f"- Current available: `{branch_divergence.get('current_available', False)}`",
            f"- Changed: `{branch_divergence.get('changed', False)}`",
            "",
        ],
    )
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Compare two scenario-spine artifact directories (advisory/report-only).")
    parser.add_argument("--previous", required=True, type=Path, help="Previous scenario-spine artifact directory.")
    parser.add_argument("--current", required=True, type=Path, help="Current scenario-spine artifact directory.")
    parser.add_argument("--out", required=True, type=Path, help="Markdown output path.")
    parser.add_argument("--json-out", type=Path, default=None, help="Optional JSON scorecard output path.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    scorecard = compare_scenario_spine_rerun_dirs(args.previous, args.current)
    _write_text(args.out, render_scenario_spine_rerun_delta_markdown(scorecard))
    if args.json_out:
        _write_json(args.json_out, scorecard)
    print(f"Wrote {args.out}")
    if args.json_out:
        print(f"Wrote {args.json_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
