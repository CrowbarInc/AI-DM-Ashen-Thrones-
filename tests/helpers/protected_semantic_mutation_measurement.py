"""BY2 — protected replay semantic mutation measurement (tests only).

Runs the BW protected corpus with BY1 semantic mutation probes enabled,
compares probe-on vs probe-off non-interference, and emits corpus reports.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import pytest

from game.api import chat
from game.models import ChatRequest
from game import storage

from tests.helpers.transcript_runner import (
    new_clean_campaign,
    patch_transcript_storage,
    write_default_bootstrap_scenes,
)
from tests.helpers.transcript_snapshots import snapshot_from_chat_payload
from tests.helpers.golden_replay_projection import (
    project_turn_observation,
    protected_observation_field_paths,
)
from tests.helpers.golden_replay_trend import (
    ProtectedReplayScenarioSpec,
    execute_protected_replay_corpus,
    protected_replay_scenario_specs,
    turn_identity_key,
    write_deterministic_json,
)
from tests.helpers.post_speaker_finalize_probe import chain_enforce_phase_marker
from tests.helpers.semantic_mutation_attribution import (
    _TraceCollector,
    finalize_semantic_mutation_trace_for_turn,
    install_semantic_mutation_probes,
    new_trace_collector,
    reset_trace_collector,
)

BY2_REPORT_SCHEMA_VERSION = 1
BY3_REPORT_SCHEMA_VERSION = 1

BY2_BASELINE_GAP_TURN = "wrong_speaker_strict_social_emission|idx:0"

BY2_BASELINE_GAP_SNAPSHOT: dict[str, Any] = {
    "turn_identity": BY2_BASELINE_GAP_TURN,
    "semantic_mutation_changed_count": 0,
    "trace_continuity": False,
    "post_gate_mutation_detected": True,
    "first_semantic_mutation_bucket": None,
    "first_semantic_mutation_source": None,
    "missing_checkpoint": "writer_or_pre_policy_checkpoint",
}

SEMANTIC_MUTATION_SUMMARY_FIELDS: tuple[str, ...] = (
    "first_semantic_mutation_bucket",
    "first_semantic_mutation_source",
    "semantic_mutation_changed_count",
    "semantic_mutation_unknown_count",
    "semantic_mutation_risk_score",
    "semantic_mutation_risk_band",
    "semantic_mutation_trace_complete",
    "trace_continuity",
)


def install_semantic_mutation_probe_session(
    monkeypatch: Any,
    collector: _TraceCollector,
) -> SimpleNamespace:
    """Install BY1 wrappers and speaker phase marker for full replay runs."""
    phase = SimpleNamespace(after_enforce=False)
    chain_enforce_phase_marker(monkeypatch, phase)
    install_semantic_mutation_probes(monkeypatch, collector, phase=phase)
    return phase


def run_golden_replay_with_semantic_mutation_probe(
    *,
    scenario_id: str,
    turns: list[str],
    tmp_path: Path,
    monkeypatch: Any,
    collector: _TraceCollector,
    phase: SimpleNamespace,
    setup_fn: Any | None = None,
    starting_scene_id: str | None = None,
    extra_scene_ids: tuple[str, ...] = (),
    chat_fn: Any | None = None,
    source_path: str | Path | None = None,
    branch_id: str | None = None,
    turn_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Run transcript turns with per-turn semantic mutation trace attachment."""
    patch_transcript_storage(monkeypatch, tmp_path)
    write_default_bootstrap_scenes()
    for sid in extra_scene_ids:
        path = storage.scene_path(sid)
        if not path.exists():
            from game.defaults import default_scene

            storage._save_json(path, default_scene(sid))
    if not storage.SESSION_LOG_PATH.exists():
        storage.SESSION_LOG_PATH.write_text("", encoding="utf-8")

    new_clean_campaign(starting_scene_id=starting_scene_id)
    if setup_fn is not None:
        setup_fn()

    fn = chat_fn or chat
    observed_turns: list[dict[str, Any]] = []
    trace_records: list[dict[str, Any]] = []

    for i, text in enumerate(turns):
        reset_trace_collector(collector)
        phase.after_enforce = False

        payload = fn(ChatRequest(text=text))
        if not isinstance(payload, dict):
            raise TypeError("chat_fn must return a dict payload")
        snap = snapshot_from_chat_payload(i, text, payload)

        trace_record = finalize_semantic_mutation_trace_for_turn(
            collector,
            replay_final_text=str(snap.get("gm_text") or ""),
        )
        trace_records.append(trace_record)

        replay_identity: dict[str, Any] = {}
        if source_path is not None:
            replay_identity["source_path"] = str(source_path)
        if branch_id is not None:
            replay_identity["branch_id"] = str(branch_id)
        if turn_ids is not None and i < len(turn_ids) and str(turn_ids[i]).strip():
            replay_identity["turn_id"] = str(turn_ids[i])

        observed_turns.append(
            project_turn_observation(
                {
                    "scenario_id": scenario_id,
                    "snap": snap,
                    "payload": payload,
                    "replay_identity": replay_identity or None,
                    "semantic_mutation_trace": trace_record,
                }
            )
        )

    return {
        "scenario_id": scenario_id,
        "turn_count": len(observed_turns),
        "turns": observed_turns,
        "semantic_mutation_records": trace_records,
    }


def _run_scenario_spec_with_semantic_probe(
    spec: ProtectedReplayScenarioSpec,
    *,
    storage_root: Path,
    monkeypatch: Any,
    collector: _TraceCollector,
    phase: SimpleNamespace,
) -> list[dict[str, Any]]:
    from tests.helpers.golden_replay_fixtures import golden_replay_chat_stubs
    from tests.helpers.golden_replay_trend import _gpt_callback_from_lines

    golden_replay_chat_stubs(
        monkeypatch,
        gpt_callback=_gpt_callback_from_lines(spec.gpt_lines),
        suppress_exploration=spec.suppress_exploration,
        suppress_intent=spec.suppress_intent,
    )
    result = run_golden_replay_with_semantic_mutation_probe(
        scenario_id=spec.scenario_id,
        turns=list(spec.turns),
        tmp_path=storage_root,
        monkeypatch=monkeypatch,
        collector=collector,
        phase=phase,
        setup_fn=spec.setup_fn,
    )
    turns = result.get("turns")
    if not isinstance(turns, list):
        raise TypeError(f"scenario {spec.scenario_id!r} did not return turn observations")
    return [dict(turn) for turn in turns if isinstance(turn, Mapping)]


def execute_protected_replay_corpus_with_semantic_mutation_probe(
    *,
    storage_root: Path,
    monkeypatch: Any,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Execute protected corpus with BY1 probe; return observations and trace records."""
    collector = new_trace_collector()
    phase = install_semantic_mutation_probe_session(monkeypatch, collector)
    observations: list[dict[str, Any]] = []
    trace_records: list[dict[str, Any]] = []

    for spec in protected_replay_scenario_specs():
        scenario_turns = _run_scenario_spec_with_semantic_probe(
            spec,
            storage_root=storage_root,
            monkeypatch=monkeypatch,
            collector=collector,
            phase=phase,
        )
        observations.extend(scenario_turns)
        for turn in scenario_turns:
            trace_records.append(_trace_record_from_observed_turn(turn))

    return observations, trace_records


def _trace_record_from_observed_turn(turn: Mapping[str, Any]) -> dict[str, Any]:
    """Reconstruct trace record fields already projected onto the observation."""
    return {
        key: turn.get(key)
        for key in (
            *SEMANTIC_MUTATION_SUMMARY_FIELDS,
            "first_semantic_mutation_sequence",
            "first_semantic_mutation_checkpoint_id",
            "first_semantic_mutation_owner",
            "first_semantic_mutation_kind",
            "semantic_mutation_cross_bucket_count",
        )
        if turn.get(key) is not None or key in {
            "semantic_mutation_trace_complete",
            "trace_continuity",
        }
    }


def turn_measurement_row(
    turn: Mapping[str, Any],
    *,
    trace_record: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Stable per-turn measurement row for BY2 reports."""
    record = dict(trace_record) if isinstance(trace_record, Mapping) else _trace_record_from_observed_turn(turn)
    return {
        "turn_identity": turn_identity_key(turn),
        "scenario_id": turn.get("scenario_id"),
        "turn_index": turn.get("turn_index"),
        "turn_id": turn.get("turn_id"),
        "final_text_hash": turn.get("final_text_hash"),
        "post_gate_mutation_detected": turn.get("post_gate_mutation_detected"),
        "first_semantic_mutation_bucket": record.get("first_semantic_mutation_bucket"),
        "first_semantic_mutation_source": record.get("first_semantic_mutation_source"),
        "first_semantic_mutation_checkpoint_id": record.get("first_semantic_mutation_checkpoint_id"),
        "semantic_mutation_changed_count": int(record.get("semantic_mutation_changed_count") or 0),
        "semantic_mutation_unknown_count": int(record.get("semantic_mutation_unknown_count") or 0),
        "semantic_mutation_risk_score": int(record.get("semantic_mutation_risk_score") or 0),
        "semantic_mutation_risk_band": record.get("semantic_mutation_risk_band"),
        "semantic_mutation_trace_complete": bool(record.get("semantic_mutation_trace_complete")),
        "trace_continuity": record.get("trace_continuity", True),
    }


def protected_field_values(turn: Mapping[str, Any]) -> dict[str, Any]:
    """Extract protected observation field values from one turn."""
    out: dict[str, Any] = {}
    for path in protected_observation_field_paths():
        if path in turn:
            out[path] = turn.get(path)
        unavailable = turn.get("unavailable")
        if isinstance(unavailable, list) and path in unavailable:
            out[path] = {"status": "unavailable"}
    return out


def assert_probe_non_interference(
    baseline_turns: Sequence[Mapping[str, Any]],
    probed_turns: Sequence[Mapping[str, Any]],
) -> None:
    """Assert probe-enabled replay matches baseline final text and protected fields."""
    if len(baseline_turns) != len(probed_turns):
        raise AssertionError(
            f"turn count mismatch: baseline={len(baseline_turns)} probed={len(probed_turns)}"
        )

    for baseline, probed in zip(baseline_turns, probed_turns):
        identity = turn_identity_key(baseline)
        probed_identity = turn_identity_key(probed)
        if identity != probed_identity:
            raise AssertionError(f"turn identity mismatch: {identity!r} vs {probed_identity!r}")

        if str(baseline.get("final_text") or "") != str(probed.get("final_text") or ""):
            raise AssertionError(f"{identity}: final_text changed with probe enabled")

        if baseline.get("final_text_hash") != probed.get("final_text_hash"):
            raise AssertionError(f"{identity}: final_text_hash changed with probe enabled")

        baseline_protected = protected_field_values(baseline)
        probed_protected = protected_field_values(probed)
        if baseline_protected != probed_protected:
            raise AssertionError(f"{identity}: protected observation fields changed with probe enabled")


def _is_attributable_first_mutation(record: Mapping[str, Any]) -> bool:
    changed = int(record.get("semantic_mutation_changed_count") or 0)
    if changed <= 0:
        return False
    bucket = record.get("first_semantic_mutation_bucket")
    source = record.get("first_semantic_mutation_source")
    return bool(bucket and str(bucket) != "unknown" and str(source or "").strip())


def build_corpus_summary(turn_rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Aggregate corpus-level semantic mutation measurement."""
    total = len(turn_rows)
    mutated = [row for row in turn_rows if int(row.get("semantic_mutation_changed_count") or 0) > 0]
    attributable = [row for row in mutated if _row_is_attributable(row)]
    unknown_first = [
        row
        for row in mutated
        if not _row_is_attributable(row)
    ]

    bucket_counter: Counter[str] = Counter()
    source_counter: Counter[str] = Counter()
    risk_scores: list[int] = []

    for row in mutated:
        bucket = row.get("first_semantic_mutation_bucket")
        if bucket and str(bucket) != "unknown":
            bucket_counter[str(bucket)] += 1
        source = row.get("first_semantic_mutation_source")
        if source and str(source).strip():
            source_counter[str(source)] += 1
        risk_scores.append(int(row.get("semantic_mutation_risk_score") or 0))

    coverage_rate = (len(attributable) / len(mutated)) if mutated else 1.0
    mean_risk = (sum(risk_scores) / len(risk_scores)) if risk_scores else 0.0

    high_risk = sorted(
        [row for row in turn_rows if int(row.get("semantic_mutation_risk_score") or 0) >= 40],
        key=lambda row: (
            -int(row.get("semantic_mutation_risk_score") or 0),
            str(row.get("turn_identity") or ""),
        ),
    )

    return {
        "total_turns": total,
        "mutated_turns": len(mutated),
        "attributable_first_mutations": len(attributable),
        "first_source_coverage_rate": round(coverage_rate, 4),
        "unknown_first_source_count": len(unknown_first),
        "bucket_distribution": dict(sorted(bucket_counter.items())),
        "top_mutation_sources": [
            {"source": source, "count": count}
            for source, count in source_counter.most_common(10)
        ],
        "semantic_mutation_risk_mean": round(mean_risk, 2),
        "semantic_mutation_risk_max": max(risk_scores) if risk_scores else 0,
        "representative_high_risk_turns": [
            {
                "turn_identity": row.get("turn_identity"),
                "scenario_id": row.get("scenario_id"),
                "turn_index": row.get("turn_index"),
                "first_semantic_mutation_bucket": row.get("first_semantic_mutation_bucket"),
                "first_semantic_mutation_source": row.get("first_semantic_mutation_source"),
                "semantic_mutation_risk_score": row.get("semantic_mutation_risk_score"),
            }
            for row in high_risk[:5]
        ],
    }


def _row_is_attributable(row: Mapping[str, Any]) -> bool:
    bucket = row.get("first_semantic_mutation_bucket")
    source = row.get("first_semantic_mutation_source")
    if int(row.get("semantic_mutation_changed_count") or 0) <= 0:
        return False
    return bool(bucket and str(bucket) != "unknown" and str(source or "").strip())


def _likely_owner_from_turn(turn: Mapping[str, Any]) -> str | None:
    for key in (
        "final_emitted_source",
        "visibility_fallback_owner_bucket",
        "sealed_fallback_owner_bucket",
        "opening_fallback_owner_bucket",
        "sanitizer_empty_fallback_owner",
    ):
        value = turn.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def _missing_checkpoint_hint(
    turn: Mapping[str, Any],
    row: Mapping[str, Any],
) -> str:
    if int(row.get("semantic_mutation_changed_count") or 0) <= 0:
        if turn.get("post_gate_mutation_detected") is True:
            return "writer_or_pre_policy_checkpoint"
        return "none"

    if row.get("trace_continuity") is False:
        return "continuity_join_between_checkpoints"

    checkpoint = row.get("first_semantic_mutation_checkpoint_id")
    if checkpoint:
        return str(checkpoint)

    if not row.get("semantic_mutation_trace_complete"):
        return "trace_not_complete"

    return "first_mutation_source_unclassified"


def _by3_instrumentation_target(
    turn: Mapping[str, Any],
    row: Mapping[str, Any],
) -> str:
    missing = _missing_checkpoint_hint(turn, row)
    if missing == "writer_or_pre_policy_checkpoint":
        return "instrument upstream writer/raw candidate before policy_output"
    if missing == "continuity_join_between_checkpoints":
        return "add intermediate checkpoint between broken continuity seam"
    if row.get("first_semantic_mutation_source") == "broken_checkpoint_continuity":
        return "repair checkpoint ordering or add bridging producer stamp"

    bucket = row.get("first_semantic_mutation_bucket")
    if bucket == "unknown":
        likely = _likely_owner_from_turn(turn)
        if likely:
            return f"stamp ordered checkpoint for owner hint {likely}"
        return "classify earliest changed layer into canonical bucket"

    if int(row.get("semantic_mutation_unknown_count") or 0) > 1:
        return "attribute later unattributed changes after first mutation"

    return "none"


def identify_attribution_gaps(
    turns: Sequence[Mapping[str, Any]],
    *,
    turn_rows: Sequence[Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    """Surface unknown/incomplete traces for BY3 follow-up."""
    rows = list(turn_rows) if turn_rows is not None else [turn_measurement_row(turn) for turn in turns]
    gaps: list[dict[str, Any]] = []

    for turn, row in zip(turns, rows):
        changed = int(row.get("semantic_mutation_changed_count") or 0)
        attributable = _row_is_attributable(row)
        continuity = row.get("trace_continuity", True)
        trace_complete = bool(row.get("semantic_mutation_trace_complete"))
        post_gate = turn.get("post_gate_mutation_detected") is True

        needs_gap = (
            (changed > 0 and not attributable)
            or (changed > 0 and continuity is False)
            or (changed > 0 and not trace_complete)
            or (post_gate and changed == 0)
        )
        if not needs_gap:
            continue

        gaps.append(
            {
                "turn_identity": row.get("turn_identity"),
                "scenario_id": row.get("scenario_id"),
                "turn_index": row.get("turn_index"),
                "turn_id": row.get("turn_id"),
                "observed_text_transition": {
                    "final_text_hash": row.get("final_text_hash"),
                    "first_semantic_mutation_before_hash": turn.get("first_semantic_mutation_before_hash"),
                    "first_semantic_mutation_after_hash": turn.get("first_semantic_mutation_after_hash"),
                    "post_gate_mutation_detected": post_gate,
                },
                "missing_checkpoint": _missing_checkpoint_hint(turn, row),
                "likely_owner": _likely_owner_from_turn(turn),
                "recommended_by3_instrumentation_target": _by3_instrumentation_target(turn, row),
                "first_semantic_mutation_bucket": row.get("first_semantic_mutation_bucket"),
                "first_semantic_mutation_source": row.get("first_semantic_mutation_source"),
                "semantic_mutation_risk_score": row.get("semantic_mutation_risk_score"),
            }
        )

    return gaps


def build_protected_semantic_mutation_report(
    turns: Sequence[Mapping[str, Any]],
    *,
    turn_rows: Sequence[Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build stable JSON report payload for BY2."""
    rows = list(turn_rows) if turn_rows is not None else [turn_measurement_row(turn) for turn in turns]
    summary = build_corpus_summary(rows)
    gaps = identify_attribution_gaps(turns, turn_rows=rows)
    return {
        "schema_version": BY2_REPORT_SCHEMA_VERSION,
        "corpus": "protected_replay",
        "corpus_scenario_ids": [spec.scenario_id for spec in protected_replay_scenario_specs()],
        "summary": summary,
        "attribution_gaps": gaps,
        "turns": list(rows),
    }


def render_protected_semantic_mutation_report_markdown(report: Mapping[str, Any]) -> str:
    """Render human-readable BY2 corpus report."""
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    gaps = report.get("attribution_gaps") if isinstance(report.get("attribution_gaps"), list) else []

    lines = [
        "# Protected Semantic Mutation Report (BY2)",
        "",
        f"- schema version: {report.get('schema_version')}",
        f"- corpus: {report.get('corpus')}",
        f"- total turns: {summary.get('total_turns')}",
        f"- mutated turns: {summary.get('mutated_turns')}",
        f"- attributable first mutations: {summary.get('attributable_first_mutations')}",
        f"- first-source coverage rate: {float(summary.get('first_source_coverage_rate') or 0):.2%}",
        f"- unknown first-source count: {summary.get('unknown_first_source_count')}",
        f"- semantic mutation risk (mean / max): {summary.get('semantic_mutation_risk_mean')} / {summary.get('semantic_mutation_risk_max')}",
        "",
        "## Bucket distribution",
        "",
    ]

    bucket_distribution = summary.get("bucket_distribution")
    if isinstance(bucket_distribution, Mapping) and bucket_distribution:
        for bucket, count in sorted(bucket_distribution.items()):
            lines.append(f"- {bucket}: {count}")
    else:
        lines.append("- (none)")

    lines.extend(["", "## Top mutation sources", ""])
    top_sources = summary.get("top_mutation_sources")
    if isinstance(top_sources, list) and top_sources:
        for item in top_sources:
            if isinstance(item, Mapping):
                lines.append(f"- {item.get('source')}: {item.get('count')}")
    else:
        lines.append("- (none)")

    high_risk = summary.get("representative_high_risk_turns")
    lines.extend(["", "## Representative high-risk turns", ""])
    if isinstance(high_risk, list) and high_risk:
        for item in high_risk:
            if isinstance(item, Mapping):
                lines.append(
                    f"- {item.get('turn_identity')}: risk={item.get('semantic_mutation_risk_score')} "
                    f"bucket={item.get('first_semantic_mutation_bucket')} source={item.get('first_semantic_mutation_source')}"
                )
    else:
        lines.append("- (none)")

    lines.extend(["", "## Attribution gaps", ""])
    if gaps:
        for gap in gaps:
            if not isinstance(gap, Mapping):
                continue
            lines.append(
                f"- {gap.get('turn_identity')}: missing={gap.get('missing_checkpoint')} "
                f"likely_owner={gap.get('likely_owner')} "
                f"by3={gap.get('recommended_by3_instrumentation_target')}"
            )
    else:
        lines.append("- (none)")

    lines.append("")
    return "\n".join(lines)


def write_protected_semantic_mutation_reports(
    report: Mapping[str, Any],
    out_dir: Path,
) -> dict[str, str]:
    """Write BY2 JSON and Markdown reports."""
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "protected_semantic_mutation_report.json"
    md_path = out_dir / "protected_semantic_mutation_report.md"
    write_deterministic_json(json_path, report)
    md_path.write_text(render_protected_semantic_mutation_report_markdown(report), encoding="utf-8")
    return {
        "json": str(json_path),
        "markdown": str(md_path),
    }


def _turn_row_by_identity(
    turn_rows: Sequence[Mapping[str, Any]],
    turn_identity: str,
) -> dict[str, Any] | None:
    for row in turn_rows:
        if str(row.get("turn_identity") or "") == turn_identity:
            return dict(row)
    return None


def build_strict_social_semantic_mutation_report(
    turns: Sequence[Mapping[str, Any]],
    *,
    turn_rows: Sequence[Mapping[str, Any]] | None = None,
    by2_baseline: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build BY3 strict-social instrumentation report with before/after coverage."""
    rows = list(turn_rows) if turn_rows is not None else [turn_measurement_row(turn) for turn in turns]
    summary = build_corpus_summary(rows)
    gaps = identify_attribution_gaps(turns, turn_rows=rows)

    baseline_row = dict(BY2_BASELINE_GAP_SNAPSHOT)
    if isinstance(by2_baseline, Mapping):
        baseline_turns = by2_baseline.get("turns")
        if isinstance(baseline_turns, list):
            loaded = _turn_row_by_identity(baseline_turns, BY2_BASELINE_GAP_TURN)
            if isinstance(loaded, Mapping) and int(loaded.get("semantic_mutation_changed_count") or 0) <= 0:
                baseline_row = dict(loaded)
                baseline_row.setdefault("missing_checkpoint", "writer_or_pre_policy_checkpoint")

    after_row = _turn_row_by_identity(rows, BY2_BASELINE_GAP_TURN) or {}
    gap_closed = (
        int(after_row.get("semantic_mutation_changed_count") or 0) > 0
        and after_row.get("trace_continuity") is not False
        and _row_is_attributable(after_row)
    )

    return {
        "schema_version": BY3_REPORT_SCHEMA_VERSION,
        "corpus": "protected_replay",
        "by3_instrumentation": {
            "checkpoints_added": [
                "writer_raw_candidate",
                "final_emission_gate_entry",
                "strict_social_trunk_entry",
                "normalized_social_candidate",
                "speaker_contract_enforcement",
                "strict_social_pre_terminal_pipeline",
            ],
        },
        "before_after_coverage": {
            "target_turn": BY2_BASELINE_GAP_TURN,
            "before_by2": {
                "semantic_mutation_changed_count": baseline_row.get("semantic_mutation_changed_count"),
                "trace_continuity": baseline_row.get("trace_continuity"),
                "post_gate_mutation_detected": baseline_row.get("post_gate_mutation_detected"),
                "first_semantic_mutation_bucket": baseline_row.get("first_semantic_mutation_bucket"),
                "first_semantic_mutation_source": baseline_row.get("first_semantic_mutation_source"),
                "missing_checkpoint": baseline_row.get("missing_checkpoint"),
            },
            "after_by3": {
                "semantic_mutation_changed_count": after_row.get("semantic_mutation_changed_count"),
                "trace_continuity": after_row.get("trace_continuity"),
                "post_gate_mutation_detected": after_row.get("post_gate_mutation_detected"),
                "first_semantic_mutation_bucket": after_row.get("first_semantic_mutation_bucket"),
                "first_semantic_mutation_source": after_row.get("first_semantic_mutation_source"),
                "first_semantic_mutation_checkpoint_id": after_row.get("first_semantic_mutation_checkpoint_id"),
            },
            "gap_closed": gap_closed,
        },
        "summary": summary,
        "attribution_gaps": gaps,
        "remaining_by4_candidates": [
            {
                "turn_identity": gap.get("turn_identity"),
                "missing_checkpoint": gap.get("missing_checkpoint"),
                "recommended_by3_instrumentation_target": gap.get("recommended_by3_instrumentation_target"),
            }
            for gap in gaps
            if isinstance(gap, Mapping)
        ],
        "turns": list(rows),
    }


def render_strict_social_semantic_mutation_report_markdown(report: Mapping[str, Any]) -> str:
    """Render human-readable BY3 strict-social instrumentation report."""
    summary = report.get("summary") if isinstance(report.get("summary"), Mapping) else {}
    coverage = (
        report.get("before_after_coverage")
        if isinstance(report.get("before_after_coverage"), Mapping)
        else {}
    )
    before = coverage.get("before_by2") if isinstance(coverage.get("before_by2"), Mapping) else {}
    after = coverage.get("after_by3") if isinstance(coverage.get("after_by3"), Mapping) else {}
    gaps = report.get("attribution_gaps") if isinstance(report.get("attribution_gaps"), list) else []
    remaining = (
        report.get("remaining_by4_candidates")
        if isinstance(report.get("remaining_by4_candidates"), list)
        else []
    )

    lines = [
        "# Strict-Social Semantic Mutation Report (BY3)",
        "",
        f"- schema version: {report.get('schema_version')}",
        f"- corpus: {report.get('corpus')}",
        f"- total turns: {summary.get('total_turns')}",
        f"- mutated turns: {summary.get('mutated_turns')}",
        f"- attributable first mutations: {summary.get('attributable_first_mutations')}",
        f"- first-source coverage rate: {float(summary.get('first_source_coverage_rate') or 0):.2%}",
        f"- unknown first-source count: {summary.get('unknown_first_source_count')}",
        "",
        "## Before/after BY3 coverage",
        "",
        f"- target turn: {coverage.get('target_turn')}",
        f"- gap closed: {coverage.get('gap_closed')}",
        "",
        "### Before (BY2)",
        "",
        f"- changed_count: {before.get('semantic_mutation_changed_count')}",
        f"- trace_continuity: {before.get('trace_continuity')}",
        f"- post_gate_mutation_detected: {before.get('post_gate_mutation_detected')}",
        f"- first bucket/source: {before.get('first_semantic_mutation_bucket')} / {before.get('first_semantic_mutation_source')}",
        f"- missing checkpoint: {before.get('missing_checkpoint')}",
        "",
        "### After (BY3)",
        "",
        f"- changed_count: {after.get('semantic_mutation_changed_count')}",
        f"- trace_continuity: {after.get('trace_continuity')}",
        f"- post_gate_mutation_detected: {after.get('post_gate_mutation_detected')}",
        f"- first bucket/source: {after.get('first_semantic_mutation_bucket')} / {after.get('first_semantic_mutation_source')}",
        f"- first checkpoint: {after.get('first_semantic_mutation_checkpoint_id')}",
        "",
        "## Bucket distribution",
        "",
    ]

    bucket_distribution = summary.get("bucket_distribution")
    if isinstance(bucket_distribution, Mapping) and bucket_distribution:
        for bucket, count in sorted(bucket_distribution.items()):
            lines.append(f"- {bucket}: {count}")
    else:
        lines.append("- (none)")

    lines.extend(["", "## Top mutation sources", ""])
    top_sources = summary.get("top_mutation_sources")
    if isinstance(top_sources, list) and top_sources:
        for item in top_sources:
            if isinstance(item, Mapping):
                lines.append(f"- {item.get('source')}: {item.get('count')}")
    else:
        lines.append("- (none)")

    lines.extend(["", "## Remaining attribution gaps", ""])
    if gaps:
        for gap in gaps:
            if not isinstance(gap, Mapping):
                continue
            lines.append(
                f"- {gap.get('turn_identity')}: missing={gap.get('missing_checkpoint')} "
                f"likely_owner={gap.get('likely_owner')}"
            )
    else:
        lines.append("- (none)")

    lines.extend(["", "## Remaining BY4 candidates", ""])
    if remaining:
        for item in remaining:
            if isinstance(item, Mapping):
                lines.append(
                    f"- {item.get('turn_identity')}: {item.get('missing_checkpoint')} "
                    f"({item.get('recommended_by3_instrumentation_target')})"
                )
    else:
        lines.append("- (none)")

    lines.append("")
    return "\n".join(lines)


def write_strict_social_semantic_mutation_reports(
    report: Mapping[str, Any],
    out_dir: Path,
) -> dict[str, str]:
    """Write BY3 JSON and Markdown reports."""
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "strict_social_semantic_mutation_report.json"
    md_path = out_dir / "strict_social_semantic_mutation_report.md"
    write_deterministic_json(json_path, report)
    md_path.write_text(render_strict_social_semantic_mutation_report_markdown(report), encoding="utf-8")
    return {
        "json": str(json_path),
        "markdown": str(md_path),
    }


def measure_strict_social_semantic_mutation_corpus(
    *,
    storage_root: Path,
    monkeypatch: Any | None = None,
    out_dir: Path | None = None,
    by2_baseline: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Run protected corpus with BY3 probes, verify non-interference, optionally write BY3 reports."""
    baseline_patch = pytest.MonkeyPatch()
    try:
        baseline = execute_protected_replay_corpus(
            storage_root=storage_root / "baseline",
            monkeypatch=baseline_patch,
        )
    finally:
        baseline_patch.undo()

    probed_patch = pytest.MonkeyPatch()
    try:
        probed, _trace_records = execute_protected_replay_corpus_with_semantic_mutation_probe(
            storage_root=storage_root / "probed",
            monkeypatch=probed_patch,
        )
    finally:
        probed_patch.undo()

    if monkeypatch is not None:
        pass

    assert_probe_non_interference(baseline, probed)

    turn_rows = [turn_measurement_row(turn) for turn in probed]
    by2_report = build_protected_semantic_mutation_report(probed, turn_rows=turn_rows)
    by3_report = build_strict_social_semantic_mutation_report(
        probed,
        turn_rows=turn_rows,
        by2_baseline=by2_baseline,
    )

    written: dict[str, str] = {}
    if out_dir is not None:
        written = write_strict_social_semantic_mutation_reports(by3_report, out_dir)

    return {
        "baseline_turns": baseline,
        "probed_turns": probed,
        "turn_rows": turn_rows,
        "by2_report": by2_report,
        "by3_report": by3_report,
        "written_artifacts": written,
    }


def measure_protected_replay_semantic_mutation_corpus(
    *,
    storage_root: Path,
    monkeypatch: Any | None = None,
    out_dir: Path | None = None,
) -> dict[str, Any]:
    """Run protected corpus with probe, verify non-interference, optionally write reports."""
    baseline_patch = pytest.MonkeyPatch()
    try:
        baseline = execute_protected_replay_corpus(
            storage_root=storage_root / "baseline",
            monkeypatch=baseline_patch,
        )
    finally:
        baseline_patch.undo()

    probed_patch = pytest.MonkeyPatch()
    try:
        probed, _trace_records = execute_protected_replay_corpus_with_semantic_mutation_probe(
            storage_root=storage_root / "probed",
            monkeypatch=probed_patch,
        )
    finally:
        probed_patch.undo()

    if monkeypatch is not None:
        # Allow callers to pass a fixture monkeypatch for API compatibility; patches are isolated above.
        pass

    assert_probe_non_interference(baseline, probed)

    turn_rows = [turn_measurement_row(turn) for turn in probed]
    report = build_protected_semantic_mutation_report(probed, turn_rows=turn_rows)

    written: dict[str, str] = {}
    if out_dir is not None:
        written = write_protected_semantic_mutation_reports(report, out_dir)

    return {
        "baseline_turns": baseline,
        "probed_turns": probed,
        "turn_rows": turn_rows,
        "report": report,
        "written_artifacts": written,
    }


__all__ = [
    "BY2_BASELINE_GAP_TURN",
    "BY2_REPORT_SCHEMA_VERSION",
    "BY3_REPORT_SCHEMA_VERSION",
    "assert_probe_non_interference",
    "build_protected_semantic_mutation_report",
    "build_strict_social_semantic_mutation_report",
    "execute_protected_replay_corpus_with_semantic_mutation_probe",
    "identify_attribution_gaps",
    "measure_protected_replay_semantic_mutation_corpus",
    "measure_strict_social_semantic_mutation_corpus",
    "render_protected_semantic_mutation_report_markdown",
    "render_strict_social_semantic_mutation_report_markdown",
    "turn_measurement_row",
    "write_protected_semantic_mutation_reports",
    "write_strict_social_semantic_mutation_reports",
]
