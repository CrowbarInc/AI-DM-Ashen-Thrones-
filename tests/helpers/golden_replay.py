"""Compact golden replay helpers built on the transcript runner.

This module is intentionally test-only.  It projects existing transcript
snapshots and chat payloads into a stable, assertion-friendly shape without
changing runtime behavior or creating a second storage/test harness.
"""
from __future__ import annotations

import hashlib
import os
import re
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Mapping

from game.api import chat
from game.final_emission_meta import (
    build_fem_runtime_lineage_events,
    normalize_final_emission_meta_for_observability,
    opening_fallback_owner_bucket_from_meta,
    read_emission_debug_lane_from_turn_payload,
    read_final_emission_meta_from_turn_payload,
)
from game.runtime_lineage_telemetry import normalize_runtime_lineage_events, summarize_runtime_lineage_events
from game.models import ChatRequest
from game.output_sanitizer import resembles_serialized_response_payload
from game.scenario_spine_eval import evaluate_scenario_spine_session, minimal_complete_transcript_turn_meta
from game import storage

from tests.debug_trace_utils import latest_compact_debug_trace_entry
from tests.helpers.failure_classifier import classify_replay_failure
from tests.helpers.failure_dashboard_report import (
    failure_dashboard_requested,
    record_failure_dashboard_rows,
    record_protected_replay_assertion_failure,
    record_runtime_lineage_events,
)
from tests.helpers.transcript_runner import (
    compact_snapshot_summary,
    latest_target_id,
    latest_target_source,
    new_clean_campaign,
    patch_transcript_storage,
    snapshot_from_chat_payload,
    write_default_bootstrap_scenes,
)


GoldenSetupFn = Callable[[], None]
GoldenChatFn = Callable[[ChatRequest], dict[str, Any]]
_MISSING = object()
_STRUCTURAL_DRIFT_FIELDS = frozenset(
    {
        "resolution_kind",
        "route_kind",
        "selected_speaker_id",
        "final_emitted_source",
        "final_emission_mutation_lineage",
        "response_type_required",
        "response_type_candidate_ok",
        "response_type_repair_used",
        "response_type_repair_kind",
        "upstream_prepared_emission_used",
        "upstream_prepared_emission_valid",
        "upstream_prepared_emission_source",
        "upstream_prepared_emission_reject_reason",
        "sanitizer_empty_fallback_used",
        "sanitizer_empty_fallback_source",
        "sanitizer_empty_fallback_owner",
        "sanitizer_lineage_mode",
        "sanitizer_lineage_changed_count",
        "sanitizer_lineage_dropped_count",
        "sanitizer_lineage_empty_fallback_used",
        "sanitizer_lineage_legacy_rewrite_active",
        "sanitizer_strict_social_fallback_used",
        "sanitizer_strict_social_selection_owner",
        "sanitizer_strict_social_prose_owner",
        "sanitizer_strict_social_source",
        "opening_recovered_via_fallback",
        "opening_fallback_authorship_source",
        "opening_fallback_owner_bucket",
        "sealed_fallback_owner_bucket",
        "visibility_fallback_owner_bucket",
        "visibility_replacement_applied",
        "visibility_fallback_pool",
        "visibility_fallback_kind",
        "fallback_family",
        "fallback_temporal_frame",
        "trace.canonical_entry.target_actor_id",
        "trace.canonical_entry.target_source",
        "trace.canonical_entry.reason",
        "trace.social_contract_trace.route_selected",
    }
)
_SEMANTIC_DRIFT_FIELDS = frozenset({"final_text", "scaffold_leakage"})

_SCAFFOLD_LEAK_RE = re.compile(
    r"\b(?:planner|router|validator|adjudication|scaffold|authoritative state|"
    r"resolve that procedurally|player_facing_text|scene_update|debug_notes)\b",
    re.IGNORECASE,
)


def final_text_has_scaffold_leakage(text: str) -> bool:
    """Best-effort final-text leak detector for golden structural assertions."""
    if not isinstance(text, str) or not text.strip():
        return False
    return bool(_SCAFFOLD_LEAK_RE.search(text) or resembles_serialized_response_payload(text))


def _sanitizer_debug_change_counts(sanitizer_debug: list[Any] | None) -> tuple[int | None, int | None]:
    if not sanitizer_debug:
        return None, None
    changed = 0
    dropped = 0
    for event in sanitizer_debug:
        if not isinstance(event, Mapping):
            continue
        event_name = str(event.get("event") or "").lower()
        if any(token in event_name for token in ("dropped", "rewritten", "rewrite", "strip")):
            changed += 1
        if "dropped" in event_name or "drop" in event_name:
            dropped += 1
    return changed, dropped


def _sanitizer_lineage_field(
    sanitizer_trace: Mapping[str, Any] | None,
    key: str,
    fallback: Any = None,
) -> Any:
    if isinstance(sanitizer_trace, Mapping) and key in sanitizer_trace:
        return sanitizer_trace.get(key)
    return fallback


def normalize_golden_text(text: Any) -> str:
    """Stable, opt-in text normalization for exact golden prose checks."""
    return re.sub(r"\s+", " ", str(text or "").strip())


def golden_text_hash(text: Any) -> str:
    """Short deterministic hash for report rows without storing long prose."""
    return hashlib.sha256(normalize_golden_text(text).encode("utf-8")).hexdigest()[:16]


def _lookup_path(obj: Mapping[str, Any], path: str) -> Any:
    cur: Any = obj
    for part in str(path or "").split("."):
        if not part:
            return _MISSING
        if not isinstance(cur, Mapping) or part not in cur:
            return _MISSING
        cur = cur.get(part)
    return cur


def _format_expected_failure(
    *,
    field_path: str,
    expected: Any,
    actual: Any,
    reason: str,
    debug_context: str = "",
) -> str:
    actual_repr = "<missing>" if actual is _MISSING else repr(actual)
    lines = [
        f"golden replay expectation failed: {reason}",
        f"field_path: {field_path}",
        f"expected: {expected!r}",
        f"actual: {actual_repr}",
    ]
    if debug_context:
        lines.extend(["", debug_context])
    return "\n".join(lines)


def _raise_expected_failure(
    *,
    turn: Mapping[str, Any],
    field_path: str,
    expected: Any,
    actual: Any,
    reason: str,
    debug_context: str,
    report_scenario_id: str | None,
) -> None:
    if report_scenario_id:
        try:
            test_node_id = str(os.environ.get("PYTEST_CURRENT_TEST") or "").split(" (", 1)[0]
            record_protected_replay_assertion_failure(
                scenario_id=report_scenario_id,
                test_node_id=test_node_id,
                observed_turn=turn,
                field_path=field_path,
                expected=expected,
                actual=None if actual is _MISSING else actual,
                reason=reason,
                drift_bucket=_drift_bucket_for_field(field_path),
            )
        except Exception:
            # Diagnostic reporting must never replace or mask an acceptance failure.
            pass
    raise AssertionError(
        _format_expected_failure(
            field_path=field_path,
            expected=expected,
            actual=actual,
            reason=reason,
            debug_context=debug_context,
        )
    )


def assert_golden_turn_observation(
    turn: Mapping[str, Any],
    expectation: Mapping[str, Any],
    *,
    debug_context: str = "",
    _report_scenario_id: str | None = None,
) -> None:
    """Assert a golden turn observation against a compact expectation.

    Supported expectation keys:
    ``require_present``, ``allow_unavailable``, ``equals``, ``one_of``,
    ``not_equals``, ``text_must_include``, ``text_must_not_include``, and
    ``scaffold_leakage``. Field selectors use dotted paths for nested dicts.
    """
    allow_unavailable = {
        str(path)
        for path in expectation.get("allow_unavailable", [])
        if isinstance(path, str) and path.strip()
    }
    unavailable = {
        str(path)
        for path in turn.get("unavailable", [])
        if isinstance(path, str) and path.strip()
    }
    for field_path in sorted(unavailable - allow_unavailable):
        actual = _lookup_path(turn, field_path)
        _raise_expected_failure(
            turn=turn,
            field_path=field_path,
            expected=f"available or explicitly allowed unavailable; allowed={sorted(allow_unavailable)!r}",
            actual=actual,
            reason="unexpected unavailable field",
            debug_context=debug_context,
            report_scenario_id=_report_scenario_id,
        )

    for field_path in expectation.get("require_present", []):
        actual = _lookup_path(turn, str(field_path))
        if actual is _MISSING or actual is None or actual == "":
            _raise_expected_failure(
                turn=turn,
                field_path=str(field_path),
                expected="present non-empty value",
                actual=actual,
                reason="required field absent",
                debug_context=debug_context,
                report_scenario_id=_report_scenario_id,
            )

    equals = expectation.get("equals") if isinstance(expectation.get("equals"), Mapping) else {}
    for field_path, expected in equals.items():
        actual = _lookup_path(turn, str(field_path))
        if actual != expected:
            _raise_expected_failure(
                turn=turn,
                field_path=str(field_path),
                expected=expected,
                actual=actual,
                reason="exact value mismatch",
                debug_context=debug_context,
                report_scenario_id=_report_scenario_id,
            )

    one_of = expectation.get("one_of") if isinstance(expectation.get("one_of"), Mapping) else {}
    for field_path, allowed in one_of.items():
        allowed_values = list(allowed) if isinstance(allowed, (list, tuple, set, frozenset)) else [allowed]
        actual = _lookup_path(turn, str(field_path))
        if actual not in allowed_values:
            _raise_expected_failure(
                turn=turn,
                field_path=str(field_path),
                expected=allowed_values,
                actual=actual,
                reason="value not in allowed set",
                debug_context=debug_context,
                report_scenario_id=_report_scenario_id,
            )

    not_equals = expectation.get("not_equals") if isinstance(expectation.get("not_equals"), Mapping) else {}
    for field_path, forbidden in not_equals.items():
        actual = _lookup_path(turn, str(field_path))
        if actual == forbidden:
            _raise_expected_failure(
                turn=turn,
                field_path=str(field_path),
                expected=f"anything except {forbidden!r}",
                actual=actual,
                reason="forbidden exact value observed",
                debug_context=debug_context,
                report_scenario_id=_report_scenario_id,
            )

    final_text = str(turn.get("final_text") or "")
    for needle in expectation.get("text_must_include", []):
        if str(needle) not in final_text:
            _raise_expected_failure(
                turn=turn,
                field_path="final_text",
                expected=f"include {str(needle)!r}",
                actual=final_text,
                reason="required text fragment missing",
                debug_context=debug_context,
                report_scenario_id=_report_scenario_id,
            )
    for needle in expectation.get("text_must_not_include", []):
        if str(needle) in final_text:
            _raise_expected_failure(
                turn=turn,
                field_path="final_text",
                expected=f"not include {str(needle)!r}",
                actual=final_text,
                reason="forbidden text fragment observed",
                debug_context=debug_context,
                report_scenario_id=_report_scenario_id,
            )

    expected_scaffold = expectation.get("scaffold_leakage")
    if expected_scaffold is not None:
        actual = _lookup_path(turn, "scaffold_leakage")
        if actual is not bool(expected_scaffold):
            _raise_expected_failure(
                turn=turn,
                field_path="scaffold_leakage",
                expected=bool(expected_scaffold),
                actual=actual,
                reason="scaffold leakage mismatch",
                debug_context=debug_context,
                report_scenario_id=_report_scenario_id,
            )


def assert_protected_golden_turn_observation(
    turn: Mapping[str, Any],
    expectation: Mapping[str, Any],
    *,
    scenario_id: str,
    debug_context: str = "",
) -> None:
    """Assert a protected invariant while recording diagnostic failures only."""
    assert_golden_turn_observation(
        turn,
        expectation,
        debug_context=debug_context,
        _report_scenario_id=scenario_id,
    )


def _drift_bucket_for_field(field_path: str) -> str:
    if field_path in _STRUCTURAL_DRIFT_FIELDS or field_path.startswith("trace."):
        return "structural_drift"
    if field_path in _SEMANTIC_DRIFT_FIELDS or field_path.startswith("semantic."):
        return "semantic_drift"
    return "structural_drift"


def _add_drift(out: dict[str, Any], bucket: str, field_path: str, expected: Any, actual: Any, reason: str) -> None:
    out.setdefault(bucket, []).append(
        {
            "field_path": str(field_path),
            "expected": expected,
            "actual": None if actual is _MISSING else actual,
            "reason": str(reason),
        }
    )


def classify_golden_drift(
    observed: Mapping[str, Any],
    expectation: Mapping[str, Any],
    *,
    exact_text: str | None = None,
) -> dict[str, Any]:
    """Classify exact, structural, and semantic drift for a golden turn.

    Exact prose drift is opt-in: pass ``exact_text`` or set
    ``expectation["exact_text"]``. Structural drift covers routing/speaker/FEM
    fields. Semantic drift covers predicate-style failures such as scaffold
    leakage or forbidden text fragments.
    """
    out: dict[str, Any] = {
        "exact_drift": [],
        "structural_drift": [],
        "semantic_drift": [],
        "observed_text_hash": golden_text_hash(observed.get("final_text")),
    }

    expected_exact = exact_text
    if expected_exact is None and isinstance(expectation.get("exact_text"), str):
        expected_exact = str(expectation.get("exact_text"))
    if expected_exact is not None:
        exp_norm = normalize_golden_text(expected_exact)
        obs_norm = normalize_golden_text(observed.get("final_text"))
        out["expected_text_hash"] = golden_text_hash(exp_norm)
        if obs_norm != exp_norm:
            _add_drift(
                out,
                "exact_drift",
                "final_text",
                out["expected_text_hash"],
                out["observed_text_hash"],
                "opt-in exact text hash mismatch",
            )

    allow_unavailable = {
        str(path)
        for path in expectation.get("allow_unavailable", [])
        if isinstance(path, str) and path.strip()
    }
    unavailable = {
        str(path)
        for path in observed.get("unavailable", [])
        if isinstance(path, str) and path.strip()
    }
    for field_path in sorted(unavailable - allow_unavailable):
        _add_drift(
            out,
            _drift_bucket_for_field(field_path),
            field_path,
            f"available or allowed unavailable; allowed={sorted(allow_unavailable)!r}",
            _lookup_path(observed, field_path),
            "unexpected unavailable field",
        )

    for field_path in expectation.get("require_present", []):
        field_s = str(field_path)
        actual = _lookup_path(observed, field_s)
        if actual is _MISSING or actual is None or actual == "":
            _add_drift(out, _drift_bucket_for_field(field_s), field_s, "present non-empty value", actual, "required field absent")

    equals = expectation.get("equals") if isinstance(expectation.get("equals"), Mapping) else {}
    for field_path, expected in equals.items():
        field_s = str(field_path)
        actual = _lookup_path(observed, field_s)
        if actual != expected:
            _add_drift(out, _drift_bucket_for_field(field_s), field_s, expected, actual, "exact value mismatch")

    one_of = expectation.get("one_of") if isinstance(expectation.get("one_of"), Mapping) else {}
    for field_path, allowed in one_of.items():
        field_s = str(field_path)
        allowed_values = list(allowed) if isinstance(allowed, (list, tuple, set, frozenset)) else [allowed]
        actual = _lookup_path(observed, field_s)
        if actual not in allowed_values:
            _add_drift(out, _drift_bucket_for_field(field_s), field_s, allowed_values, actual, "value not in allowed set")

    not_equals = expectation.get("not_equals") if isinstance(expectation.get("not_equals"), Mapping) else {}
    for field_path, forbidden in not_equals.items():
        field_s = str(field_path)
        actual = _lookup_path(observed, field_s)
        if actual == forbidden:
            _add_drift(out, _drift_bucket_for_field(field_s), field_s, f"anything except {forbidden!r}", actual, "forbidden value observed")

    final_text = str(observed.get("final_text") or "")
    for needle in expectation.get("text_must_include", []):
        if str(needle) not in final_text:
            _add_drift(out, "semantic_drift", "final_text", f"include {str(needle)!r}", final_text, "required text fragment missing")
    for needle in expectation.get("text_must_not_include", []):
        if str(needle) in final_text:
            _add_drift(out, "semantic_drift", "final_text", f"not include {str(needle)!r}", final_text, "forbidden text fragment observed")

    if expectation.get("scaffold_leakage") is not None:
        expected_scaffold = bool(expectation.get("scaffold_leakage"))
        actual_scaffold = _lookup_path(observed, "scaffold_leakage")
        if actual_scaffold is not expected_scaffold:
            _add_drift(
                out,
                "semantic_drift",
                "scaffold_leakage",
                expected_scaffold,
                actual_scaffold,
                "scaffold leakage mismatch",
            )

    out["status"] = "fail" if any(out[k] for k in ("exact_drift", "structural_drift", "semantic_drift")) else "pass"
    out["summary"] = {
        "exact_drift": len(out["exact_drift"]),
        "structural_drift": len(out["structural_drift"]),
        "semantic_drift": len(out["semantic_drift"]),
    }
    drift_rows: list[dict[str, Any]] = []
    for bucket in ("exact_drift", "structural_drift", "semantic_drift"):
        for row in out[bucket]:
            enriched = dict(row)
            enriched["drift_bucket"] = bucket
            enriched["replay_tags"] = [bucket]
            enriched["observed_text_hash"] = out.get("observed_text_hash")
            drift_rows.append(enriched)
    out["failure_classifications"] = classify_replay_failure(
        scenario_id=str(observed.get("scenario_id") or ""),
        turn_index=int(observed.get("turn_index") or 0),
        observed_turn=observed,
        drift_rows=drift_rows,
    )
    if failure_dashboard_requested() and observed.get("scenario_id") and observed.get("turn_index") is not None:
        record_failure_dashboard_rows(out["failure_classifications"])
        record_runtime_lineage_events(observed.get("runtime_lineage_events"))
    return out


def render_golden_replay_markdown_report(rows: list[Mapping[str, Any]], *, title: str = "Golden Replay Drift Report") -> str:
    """Render a compact deterministic markdown report from golden observation rows."""
    lines = [
        f"# {title}",
        "",
        "Exact prose comparison is opt-in. This report records structural and predicate-level observations for drift review.",
        "",
        "| Scenario | Mode | Turns | Status | Drift | Classifications | Sources | Fallback | Unavailable | Invariants |",
        "|---|---:|---:|---:|---|---|---|---|---|---|",
    ]
    for row in sorted(rows, key=lambda r: str(r.get("scenario_id") or "")):
        drift = row.get("drift")
        if isinstance(drift, Mapping):
            summary = drift.get("summary") if isinstance(drift.get("summary"), Mapping) else {}
            drift_s = (
                f"exact={int(summary.get('exact_drift') or 0)}, "
                f"structural={int(summary.get('structural_drift') or 0)}, "
                f"semantic={int(summary.get('semantic_drift') or 0)}"
            )
            status = str(drift.get("status") or row.get("status") or "")
            classifications = drift.get("failure_classifications")
            if isinstance(classifications, list):
                classifications_s = ", ".join(
                    f"{item.get('category')}:{item.get('primary_owner')}:{item.get('severity')}"
                    for item in classifications
                    if isinstance(item, Mapping)
                )
            else:
                classifications_s = ""
        else:
            drift_s = str(row.get("drift_summary") or "")
            status = str(row.get("status") or "")
            classifications_s = ""
        sources = row.get("final_emitted_source")
        if isinstance(sources, (list, tuple)):
            sources_s = ", ".join(str(x) for x in sources if str(x).strip()) or "none"
        else:
            sources_s = str(sources or "none")
        fallback = row.get("fallback_family")
        if isinstance(fallback, (list, tuple)):
            fallback_s = ", ".join(str(x) for x in fallback if str(x).strip()) or "none"
        else:
            fallback_s = str(fallback or "none")
        unavailable = row.get("unavailable_fields") or row.get("unavailable") or []
        unavailable_s = ", ".join(str(x) for x in unavailable) if isinstance(unavailable, (list, tuple, set)) else str(unavailable)
        invariants = row.get("required_invariants") or []
        invariants_s = ", ".join(str(x) for x in invariants) if isinstance(invariants, (list, tuple, set)) else str(invariants)
        lines.append(
            "| "
            + " | ".join(
                [
                    str(row.get("scenario_id") or ""),
                    str(row.get("mode") or ""),
                    str(row.get("turn_count") or ""),
                    status or "unknown",
                    drift_s or "not-classified",
                    classifications_s or "none",
                    sources_s,
                    fallback_s,
                    unavailable_s or "none",
                    invariants_s or "none",
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def _counter_dict(values: list[Any]) -> dict[str, int]:
    return dict(sorted(Counter(str(v) for v in values if v is not None and str(v).strip()).items()))


def _owner_for_turn(turn: Mapping[str, Any]) -> str | None:
    for key in (
        "opening_fallback_owner_bucket",
        "sealed_fallback_owner_bucket",
        "visibility_fallback_owner_bucket",
        "sanitizer_empty_fallback_owner",
        "sanitizer_strict_social_prose_owner",
    ):
        value = turn.get(key)
        if value is not None and str(value).strip():
            owner = str(value)
            if owner != "unknown-ambiguous":
                return owner
    return None


def _stable_change_count(values: list[str]) -> int:
    changes = 0
    last: str | None = None
    for value in values:
        if last is not None and value != last:
            changes += 1
        last = value
    return changes


def _lineage_events_for_turn(turn: Mapping[str, Any]) -> list[dict[str, Any]]:
    return normalize_runtime_lineage_events(turn.get("runtime_lineage_events"))


def _lineage_fallback_events(turn: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [event for event in _lineage_events_for_turn(turn) if event.get("event_kind") == "fallback_selected"]


def _has_fallback_selection(turn: Mapping[str, Any]) -> bool:
    return bool(turn.get("fallback_family") is not None or _lineage_fallback_events(turn))


def _turn_window(index: int, total: int) -> str:
    if total <= 0:
        return "none"
    third = max(1, total // 3)
    if index < third:
        return "early"
    if index < third * 2:
        return "middle"
    return "late"


def _max_consecutive_true(values: list[bool]) -> int:
    max_seen = 0
    current = 0
    for value in values:
        if value:
            current += 1
            max_seen = max(max_seen, current)
        else:
            current = 0
    return max_seen


def _active_telemetry_token(value: Any) -> str | None:
    if value is None or value is False:
        return None
    token = str(value).strip()
    if not token or token.lower() in {"none", "false", "no", "0"}:
        return None
    return token


def summarize_fallback_escalation_observations(
    turns: list[Mapping[str, Any]],
) -> dict[str, Any]:
    """Return fallback escalation metrics for sustained replay observations."""
    total_turns = len(turns)
    fallback_turn_flags: list[bool] = []
    fallback_turn_indices: list[int] = []
    fallback_windows: Counter[str] = Counter()
    fallback_lineage_kinds: list[str] = []
    fallback_lineage_owners: list[str] = []
    fallback_owner_by_turn: list[str] = []
    behavior_repair_turn_indices: list[int] = []
    response_type_repair_turn_indices: list[int] = []
    sanitizer_fallback_turn_indices: list[int] = []
    unavailable_with_fallback_count = 0
    fallback_family_unavailable_with_fallback_count = 0
    fallback_selected_without_family_count = 0

    for index, turn in enumerate(turns):
        turn_index = int(turn.get("turn_index") if turn.get("turn_index") is not None else index)
        lineage_fallbacks = _lineage_fallback_events(turn)
        has_fallback = _has_fallback_selection(turn)
        fallback_turn_flags.append(has_fallback)
        if has_fallback:
            fallback_turn_indices.append(turn_index)
            fallback_windows[_turn_window(index, total_turns)] += 1
            owner = _owner_for_turn(turn)
            if owner:
                fallback_owner_by_turn.append(owner)
            if turn.get("fallback_family") is None and lineage_fallbacks:
                fallback_selected_without_family_count += 1
            unavailable = turn.get("unavailable")
            if isinstance(unavailable, list) and unavailable:
                unavailable_with_fallback_count += 1
                if "fallback_family" in {str(item) for item in unavailable}:
                    fallback_family_unavailable_with_fallback_count += 1
        for event in lineage_fallbacks:
            fallback_kind = event.get("fallback_kind")
            if isinstance(fallback_kind, str) and fallback_kind.strip():
                fallback_lineage_kinds.append(fallback_kind)
            owner = event.get("owner")
            if isinstance(owner, str) and owner.strip():
                fallback_lineage_owners.append(owner)
        if (
            turn.get("fallback_behavior_repaired") is True
            or _active_telemetry_token(turn.get("fallback_behavior_repair_kind"))
            or _active_telemetry_token(turn.get("fallback_behavior_repair_mode"))
        ):
            behavior_repair_turn_indices.append(turn_index)
        if turn.get("response_type_repair_used") is True or _active_telemetry_token(turn.get("response_type_repair_kind")):
            response_type_repair_turn_indices.append(turn_index)
        if turn.get("sanitizer_empty_fallback_used") is True or turn.get("sanitizer_strict_social_fallback_used") is True:
            sanitizer_fallback_turn_indices.append(turn_index)

    fallback_family_counts = _counter_dict([str(t.get("fallback_family")) for t in turns if t.get("fallback_family")])
    fallback_owner_counts = _counter_dict(fallback_owner_by_turn)
    lineage_fallback_kind_counts = _counter_dict(fallback_lineage_kinds)
    lineage_owner_counts = _counter_dict(fallback_lineage_owners)
    owner_change_count = _stable_change_count(fallback_owner_by_turn)
    lineage_owner_change_count = _stable_change_count(fallback_lineage_owners)
    max_streak = _max_consecutive_true(fallback_turn_flags)
    late_fallback_count = int(fallback_windows.get("late", 0))
    early_middle_fallback_count = int(fallback_windows.get("early", 0)) + int(fallback_windows.get("middle", 0))
    escalation_warnings: list[str] = []
    if max_streak > 1:
        escalation_warnings.append("fallback_streak_gt_1")
    if late_fallback_count > max(1, early_middle_fallback_count):
        escalation_warnings.append("late_fallback_spike")
    if owner_change_count > 0 or lineage_owner_change_count > 0:
        escalation_warnings.append("fallback_owner_changed")
    if len(behavior_repair_turn_indices) > 0:
        escalation_warnings.append("fallback_behavior_repair_used")
    if len(behavior_repair_turn_indices) > 1:
        escalation_warnings.append("fallback_behavior_repair_loop")
    if fallback_selected_without_family_count > 1:
        escalation_warnings.append("fallback_selected_without_family_recurrence")
    if unavailable_with_fallback_count > 1:
        escalation_warnings.append("unavailable_to_fallback_coupling_recurrence")

    return {
        "fallback_total_count": len(fallback_turn_indices),
        "fallback_turn_indices": fallback_turn_indices,
        "fallback_family_counts": fallback_family_counts,
        "fallback_owner_counts": fallback_owner_counts,
        "fallback_lineage_kind_counts": lineage_fallback_kind_counts,
        "fallback_lineage_owner_counts": lineage_owner_counts,
        "fallback_window_counts": dict(sorted(fallback_windows.items())),
        "max_fallback_streak": max_streak,
        "late_window_fallback_count": late_fallback_count,
        "fallback_owner_change_count": owner_change_count,
        "fallback_lineage_owner_change_count": lineage_owner_change_count,
        "fallback_behavior_repair_turn_indices": behavior_repair_turn_indices,
        "fallback_behavior_repair_count": len(behavior_repair_turn_indices),
        "response_type_repair_turn_indices": response_type_repair_turn_indices,
        "response_type_repair_count": len(response_type_repair_turn_indices),
        "sanitizer_fallback_turn_indices": sanitizer_fallback_turn_indices,
        "sanitizer_fallback_count": len(sanitizer_fallback_turn_indices),
        "unavailable_with_fallback_count": unavailable_with_fallback_count,
        "fallback_family_unavailable_with_fallback_count": fallback_family_unavailable_with_fallback_count,
        "fallback_selected_without_family_count": fallback_selected_without_family_count,
        "model_routing_escalation_observable": False,
        "model_routing_escalation_count": None,
        "escalation_warnings": escalation_warnings,
    }


def summarize_long_session_replay_observations(
    turns: list[Mapping[str, Any]],
) -> dict[str, Any]:
    """Return compact longitudinal structural metrics for replay observations."""
    route_sequence = [str(t.get("route_kind")) for t in turns if t.get("route_kind") is not None]
    speaker_sequence = [str(t.get("selected_speaker_id")) for t in turns if t.get("selected_speaker_id") is not None]
    fallback_sequence = [str(t.get("fallback_family")) for t in turns if t.get("fallback_family") is not None]
    fallback_owner_sequence = [owner for t in turns if (owner := _owner_for_turn(t))]
    mutation_turn_indices = [
        int(t.get("turn_index") or 0)
        for t in turns
        if t.get("post_gate_mutation_detected") is True or t.get("final_emission_mutation_lineage")
    ]
    unavailable_counts: Counter[str] = Counter()
    for turn in turns:
        unavailable = turn.get("unavailable")
        if isinstance(unavailable, list):
            unavailable_counts.update(str(item) for item in unavailable if str(item).strip())

    lineage_events: list[dict[str, Any]] = []
    for turn in turns:
        lineage_events.extend(_lineage_events_for_turn(turn))
    lineage_summary = summarize_runtime_lineage_events(lineage_events)
    fallback_escalation_summary = summarize_fallback_escalation_observations(turns)

    continuity_warning_count = 0
    continuity_violation_count = 0
    for turn in turns:
        icv = turn.get("interaction_continuity_validation")
        if not isinstance(icv, Mapping):
            continue
        if icv.get("ok") is not False:
            continue
        warnings = icv.get("warnings")
        violations = icv.get("violations")
        if isinstance(warnings, list):
            continuity_warning_count += len(warnings)
        if isinstance(violations, list):
            continuity_violation_count += len(violations)

    return {
        "turn_count": len(turns),
        "route_sequence": route_sequence,
        "route_frequency": _counter_dict(route_sequence),
        "route_change_count": _stable_change_count(route_sequence),
        "speaker_sequence": speaker_sequence,
        "speaker_frequency": _counter_dict(speaker_sequence),
        "speaker_change_count": _stable_change_count(speaker_sequence),
        "speaker_missing_count": len(turns) - len(speaker_sequence),
        "fallback_sequence": fallback_sequence,
        "fallback_frequency": _counter_dict(fallback_sequence),
        "fallback_turn_count": len(fallback_sequence),
        "fallback_owner_sequence": fallback_owner_sequence,
        "fallback_owner_frequency": _counter_dict(fallback_owner_sequence),
        "fallback_owner_change_count": _stable_change_count(fallback_owner_sequence),
        "mutation_turn_indices": mutation_turn_indices,
        "mutation_turn_count": len(mutation_turn_indices),
        "unavailable_counts": dict(sorted(unavailable_counts.items())),
        "lineage_summary": lineage_summary,
        "fallback_escalation_summary": fallback_escalation_summary,
        "continuity_warning_count": continuity_warning_count,
        "continuity_violation_count": continuity_violation_count,
    }


def project_golden_replay_turns_to_scenario_spine_rows(
    turns: list[Mapping[str, Any]],
    *,
    spine_id: str,
    branch_id: str,
    spine: Mapping[str, Any] | None = None,
    turn_ids: list[str] | None = None,
    max_turns: int | None = None,
) -> list[dict[str, Any]]:
    """Project golden replay observations into scenario-spine evaluator rows."""
    rows: list[dict[str, Any]] = []
    for index, turn in enumerate(turns):
        turn_index = int(turn.get("turn_index") if turn.get("turn_index") is not None else index)
        turn_id = (
            str(turn_ids[index])
            if turn_ids is not None and index < len(turn_ids) and str(turn_ids[index]).strip()
            else f"golden_{turn_index:02d}"
        )
        meta = minimal_complete_transcript_turn_meta(
            spine_id=spine_id,
            branch_id=branch_id,
            turn_id=turn_id,
            turn_index=turn_index,
            max_turns=max_turns if max_turns is not None else len(turns),
        )
        meta["golden_replay_observation"] = {
            "scenario_id": turn.get("scenario_id"),
            "route_kind": turn.get("route_kind"),
            "selected_speaker_id": turn.get("selected_speaker_id"),
            "fallback_family": turn.get("fallback_family"),
            "post_gate_mutation_detected": turn.get("post_gate_mutation_detected"),
            "final_emitted_source": turn.get("final_emitted_source"),
            "unavailable": list(turn.get("unavailable") or []) if isinstance(turn.get("unavailable"), list) else [],
        }
        meta["runtime_lineage_events"] = normalize_runtime_lineage_events(turn.get("runtime_lineage_events"))
        emitted_gm_text = str(turn.get("final_text") or "")
        audit_context = _scenario_spine_continuity_audit_context(spine, branch_id)
        gm_text = emitted_gm_text if not audit_context else f"{emitted_gm_text}\n\n{audit_context}"
        rows.append(
            {
                "turn_index": turn_index,
                "turn_id": turn_id,
                "player_prompt": str(turn.get("player_text") or ""),
                "gm_text": gm_text,
                "api_ok": True,
                "meta": meta,
            }
        )
    return rows


def _scenario_spine_continuity_audit_context(spine: Mapping[str, Any] | None, branch_id: str) -> str:
    """Return compact deterministic context that lets text-oriented evaluators audit structural continuity."""
    if not isinstance(spine, Mapping):
        return ""
    parts: list[str] = []
    title = spine.get("title")
    if isinstance(title, str) and title.strip():
        parts.append(title.strip())
    for key in ("continuity_anchors", "referent_anchors", "progression_anchors"):
        anchors = spine.get(key)
        if not isinstance(anchors, list):
            continue
        for anchor in anchors:
            if not isinstance(anchor, Mapping):
                continue
            label = anchor.get("label")
            description = anchor.get("description")
            expected_change = anchor.get("expected_change_summary")
            if isinstance(label, str) and label.strip():
                parts.append(label.strip())
            if isinstance(description, str) and description.strip():
                parts.append(description.strip())
            if isinstance(expected_change, str) and expected_change.strip():
                parts.append(expected_change.strip())
    branches = spine.get("branches")
    if isinstance(branches, list):
        branch = next(
            (
                item
                for item in branches
                if isinstance(item, Mapping) and str(item.get("branch_id") or "") == branch_id
            ),
            None,
        )
        if isinstance(branch, Mapping):
            label = branch.get("label")
            notes = branch.get("notes")
            if isinstance(label, str) and label.strip():
                parts.append(label.strip())
            if isinstance(notes, str) and notes.strip():
                parts.append(notes.strip())
    compact = " ".join(dict.fromkeys(part for part in parts if part))
    if not compact:
        return ""
    return f"Continuity audit context: {compact}"


def evaluate_golden_replay_continuity_drift(
    *,
    spine: Mapping[str, Any],
    branch_id: str,
    turns: list[Mapping[str, Any]],
    turn_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Evaluate golden replay observations through the scenario-spine health evaluator."""
    rows = project_golden_replay_turns_to_scenario_spine_rows(
        turns,
        spine_id=str(spine.get("spine_id") or ""),
        branch_id=branch_id,
        spine=spine,
        turn_ids=turn_ids,
        max_turns=len(turns),
    )
    result = evaluate_scenario_spine_session(spine, branch_id, rows)
    return {
        "rows": rows,
        "evaluation": result,
    }


def render_long_session_replay_summary_markdown(
    *,
    scenario_id: str,
    turns: list[Mapping[str, Any]],
    summary: Mapping[str, Any],
    title: str = "Long-Session Replay Summary",
) -> str:
    """Render a compact operator-readable replay/session summary."""
    lineage = summary.get("lineage_summary") if isinstance(summary.get("lineage_summary"), Mapping) else {}
    fallback_escalation = (
        summary.get("fallback_escalation_summary")
        if isinstance(summary.get("fallback_escalation_summary"), Mapping)
        else {}
    )
    continuity = summary.get("continuity_drift") if isinstance(summary.get("continuity_drift"), Mapping) else {}
    session_health = continuity.get("session_health") if isinstance(continuity.get("session_health"), Mapping) else {}
    degradation = continuity.get("degradation_over_time") if isinstance(continuity.get("degradation_over_time"), Mapping) else {}
    late_window = degradation.get("late_window") if isinstance(degradation.get("late_window"), Mapping) else {}
    lines = [
        f"# {title}",
        "",
        f"- Scenario: `{scenario_id}`",
        f"- Turns: `{summary.get('turn_count')}`",
        f"- Route frequency: `{summary.get('route_frequency')}`",
        f"- Route changes: `{summary.get('route_change_count')}`",
        f"- Speaker frequency: `{summary.get('speaker_frequency')}`",
        f"- Speaker changes / missing: `{summary.get('speaker_change_count')}` / `{summary.get('speaker_missing_count')}`",
        f"- Fallback total count: `{fallback_escalation.get('fallback_total_count', 0)}`",
        f"- Fallback families: `{fallback_escalation.get('fallback_family_counts', {})}`",
        f"- Fallback owners: `{fallback_escalation.get('fallback_owner_counts', {})}`",
        f"- Fallback lineage kinds: `{fallback_escalation.get('fallback_lineage_kind_counts', {})}`",
        f"- Max fallback streak: `{fallback_escalation.get('max_fallback_streak', 0)}`",
        f"- Late-window fallback count: `{fallback_escalation.get('late_window_fallback_count', 0)}`",
        f"- Fallback escalation warnings: `{fallback_escalation.get('escalation_warnings', [])}`",
        f"- Mutation turn count: `{summary.get('mutation_turn_count')}`",
        f"- Unavailable counts: `{summary.get('unavailable_counts')}`",
        f"- Lineage event frequency: `{lineage.get('by_event_kind', {})}`",
        f"- Lineage recurrence: `{lineage.get('recurring_events', [])}`",
        f"- Continuity warnings / violations: `{summary.get('continuity_warning_count')}` / `{summary.get('continuity_violation_count')}`",
        f"- Continuity classification: `{session_health.get('classification', 'not_evaluated')}`",
        f"- Degradation detected: `{session_health.get('degradation_detected', False)}`",
        f"- Degradation reasons: `{degradation.get('reason_codes', [])}`",
        f"- Late-window signals: `{late_window.get('signals', [])}`",
        "",
        "| Turn | Route | Speaker | Fallback | Owner | Mutation | Unavailable | Lineage |",
        "|---:|---|---|---|---|---|---|---|",
    ]
    for turn in turns:
        lineage_events = normalize_runtime_lineage_events(turn.get("runtime_lineage_events"))
        lineage_kinds = ", ".join(
            str(event.get("event_kind"))
            for event in lineage_events
            if isinstance(event.get("event_kind"), str) and event.get("event_kind")
        )
        mutation = bool(turn.get("post_gate_mutation_detected") is True or turn.get("final_emission_mutation_lineage"))
        unavailable = turn.get("unavailable")
        unavailable_s = ", ".join(str(item) for item in unavailable) if isinstance(unavailable, list) else ""
        lines.append(
            "| "
            + " | ".join(
                [
                    str(turn.get("turn_index")),
                    str(turn.get("route_kind") or ""),
                    str(turn.get("selected_speaker_id") or ""),
                    str(turn.get("fallback_family") or ""),
                    str(_owner_for_turn(turn) or ""),
                    str(mutation),
                    unavailable_s,
                    lineage_kinds,
                ]
            )
            + " |"
        )
    lines.append("")
    return "\n".join(lines)


def _trace_from_payload_or_snapshot(payload: Mapping[str, Any], snap: Mapping[str, Any]) -> dict[str, Any]:
    traces = payload.get("debug_traces")
    if not isinstance(traces, list):
        session = payload.get("session") if isinstance(payload.get("session"), Mapping) else {}
        traces = session.get("debug_traces") if isinstance(session.get("debug_traces"), list) else []
    trace = latest_compact_debug_trace_entry(traces)
    if trace:
        return trace
    debug = snap.get("debug") if isinstance(snap.get("debug"), Mapping) else {}
    last = debug.get("last_debug_trace")
    return dict(last) if isinstance(last, Mapping) else {}


def _first_present(mapping: Mapping[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        value = mapping.get(key)
        if value is not None:
            return value
    return None


def _has_path(obj: Mapping[str, Any], path: str) -> bool:
    cur: Any = obj
    for part in str(path or "").split("."):
        if not isinstance(cur, Mapping) or part not in cur:
            return False
        cur = cur.get(part)
    return True


def _find_nested_mapping(root: Mapping[str, Any], key: str) -> dict[str, Any]:
    stack: list[Any] = [root]
    seen = 0
    while stack and seen < 200:
        seen += 1
        cur = stack.pop()
        if not isinstance(cur, Mapping):
            continue
        value = cur.get(key)
        if isinstance(value, Mapping):
            return dict(value)
        for child in cur.values():
            if isinstance(child, Mapping):
                stack.append(child)
            elif isinstance(child, list):
                stack.extend(item for item in child if isinstance(item, Mapping))
    return {}


def _find_nested_list(root: Mapping[str, Any], key: str) -> list[Any]:
    stack: list[Any] = [root]
    seen = 0
    while stack and seen < 200:
        seen += 1
        cur = stack.pop()
        if not isinstance(cur, Mapping):
            continue
        value = cur.get(key)
        if isinstance(value, list):
            return list(value)
        for child in cur.values():
            if isinstance(child, Mapping):
                stack.append(child)
            elif isinstance(child, list):
                stack.extend(item for item in child if isinstance(item, Mapping))
    return []


def _find_nested_list_field(root: Mapping[str, Any], key: str) -> tuple[bool, list[Any]]:
    """Return whether a nested projected-list field exists, preserving an explicit empty list."""
    stack: list[Any] = [root]
    seen = 0
    while stack and seen < 200:
        seen += 1
        cur = stack.pop()
        if not isinstance(cur, Mapping):
            continue
        if key in cur:
            value = cur.get(key)
            return True, list(value) if isinstance(value, list) else []
        for child in cur.values():
            if isinstance(child, Mapping):
                stack.append(child)
            elif isinstance(child, list):
                stack.extend(item for item in child if isinstance(item, Mapping))
    return False, []


def _runtime_lineage_events_from_payload(payload: Mapping[str, Any], fem: Mapping[str, Any]) -> list[dict[str, Any]]:
    found, events = _find_nested_list_field(payload, "fem_runtime_lineage_events")
    if found:
        return normalize_runtime_lineage_events(events)[:16]
    return build_fem_runtime_lineage_events(fem)[:16] if fem else []


def _observed_turn(
    *,
    scenario_id: str,
    snap: dict[str, Any],
    payload: dict[str, Any],
) -> dict[str, Any]:
    resolution = payload.get("resolution") if isinstance(payload.get("resolution"), Mapping) else {}
    social = resolution.get("social") if isinstance(resolution.get("social"), Mapping) else {}
    fem = read_final_emission_meta_from_turn_payload(payload)
    fem_normalized = normalize_final_emission_meta_for_observability(fem)
    runtime_lineage_events = _runtime_lineage_events_from_payload(payload, fem)
    emission_debug_lane = read_emission_debug_lane_from_turn_payload(payload)
    trace = _trace_from_payload_or_snapshot(payload, snap)
    turn_trace = trace.get("turn_trace") if isinstance(trace.get("turn_trace"), Mapping) else {}
    social_contract_trace = (
        turn_trace.get("social_contract_trace")
        if isinstance(turn_trace.get("social_contract_trace"), Mapping)
        else {}
    )
    canonical_entry = trace.get("canonical_entry") if isinstance(trace.get("canonical_entry"), Mapping) else {}
    resolution_compact = (
        (snap.get("debug") or {}).get("resolution_compact")
        if isinstance(snap.get("debug"), Mapping)
        else None
    )

    route_kind = _first_present(
        social_contract_trace,
        ("route_selected",),
    )
    if route_kind is None and isinstance(resolution_compact, Mapping):
        route_kind = resolution_compact.get("kind")
    if route_kind is None:
        route_kind = resolution.get("kind")

    selected_speaker_id = _first_present(
        social_contract_trace,
        ("final_reply_owner", "reply_owner_actor_id", "visible_grounded_speaker"),
    )
    selected_speaker_source = "turn_trace.social_contract_trace" if selected_speaker_id else None
    if selected_speaker_id is None:
        selected_speaker_id = latest_target_id(snap)
        selected_speaker_source = latest_target_source(snap)
    if selected_speaker_id is None:
        selected_speaker_id = social.get("npc_id")
        selected_speaker_source = "resolution.social.npc_id" if selected_speaker_id else None

    final_emitted_source = _first_present(
        fem,
        ("final_emitted_source", "final_route", "upstream_prepared_emission_source"),
    )
    response_type_required = _first_present(fem, ("response_type_required",))
    final_emission_mutation_lineage = _first_present(fem, ("final_emission_mutation_lineage",))
    response_type_candidate_ok = _first_present(fem, ("response_type_candidate_ok",))
    response_type_repair_used = _first_present(fem, ("response_type_repair_used",))
    response_type_repair_kind = _first_present(fem, ("response_type_repair_kind",))
    upstream_prepared_emission_used = _first_present(fem, ("upstream_prepared_emission_used",))
    upstream_prepared_emission_valid = _first_present(fem, ("upstream_prepared_emission_valid",))
    upstream_prepared_emission_source = _first_present(fem, ("upstream_prepared_emission_source",))
    upstream_prepared_emission_reject_reason = _first_present(fem, ("upstream_prepared_emission_reject_reason",))
    post_gate_mutation_detected = _first_present(fem, ("post_gate_mutation_detected",))
    opening_recovered_via_fallback = _first_present(fem, ("opening_recovered_via_fallback",))
    opening_fallback_authorship_source = _first_present(fem, ("opening_fallback_authorship_source",))
    opening_fallback_owner_bucket = opening_fallback_owner_bucket_from_meta(fem)
    sealed_fallback_owner_bucket = _first_present(fem, ("sealed_fallback_owner_bucket",))
    visibility_fallback_owner_bucket = _first_present(fem, ("visibility_fallback_owner_bucket",))
    visibility_replacement_applied = _first_present(fem, ("visibility_replacement_applied",))
    visibility_fallback_pool = _first_present(fem, ("visibility_fallback_pool",))
    visibility_fallback_kind = _first_present(fem, ("visibility_fallback_kind",))
    fallback_family = _first_present(
        fem,
        ("fallback_family_used", "realization_fallback_family"),
    )
    fallback_temporal_frame = _first_present(fem, ("fallback_temporal_frame",))
    stage_diff = _find_nested_mapping(payload, "stage_diff_telemetry")
    sanitizer_debug = _find_nested_list(payload, "sanitizer_debug")
    sanitizer_trace = _find_nested_mapping(payload, "sanitizer_trace")
    sanitizer_mode = _first_present(
        sanitizer_trace,
        ("sanitizer_boundary_mode", "mode"),
    ) or _lookup_path(payload, "gm_output.metadata.sanitizer_boundary_mode")
    sanitizer_event_count = len(sanitizer_debug) if sanitizer_debug else None
    sanitizer_changed_count, sanitizer_dropped_count = _sanitizer_debug_change_counts(sanitizer_debug)
    sanitizer_rewrite_used = bool(sanitizer_changed_count) if sanitizer_changed_count is not None else None
    sanitizer_empty_fallback_used = _first_present(sanitizer_trace, ("sanitizer_empty_fallback_used",))
    sanitizer_empty_fallback_source = _first_present(sanitizer_trace, ("sanitizer_empty_fallback_source",))
    sanitizer_empty_fallback_owner = _first_present(sanitizer_trace, ("sanitizer_empty_fallback_owner",))
    sanitizer_lineage_mode = _sanitizer_lineage_field(sanitizer_trace, "sanitizer_lineage_mode", sanitizer_mode)
    sanitizer_lineage_changed_count = _sanitizer_lineage_field(
        sanitizer_trace,
        "sanitizer_lineage_changed_count",
        sanitizer_changed_count,
    )
    sanitizer_lineage_dropped_count = _sanitizer_lineage_field(
        sanitizer_trace,
        "sanitizer_lineage_dropped_count",
        sanitizer_dropped_count,
    )
    sanitizer_lineage_empty_fallback_used = _sanitizer_lineage_field(
        sanitizer_trace,
        "sanitizer_lineage_empty_fallback_used",
        sanitizer_empty_fallback_used,
    )
    sanitizer_lineage_legacy_rewrite_active = _sanitizer_lineage_field(
        sanitizer_trace,
        "sanitizer_lineage_legacy_rewrite_active",
        str(sanitizer_lineage_mode or "").strip().lower() == "legacy_sentence_rewrite"
        if sanitizer_lineage_mode is not None
        else None,
    )
    sanitizer_strict_social_fallback_used = _first_present(sanitizer_trace, ("sanitizer_strict_social_fallback_used",))
    sanitizer_strict_social_selection_owner = _first_present(
        sanitizer_trace,
        ("sanitizer_strict_social_selection_owner",),
    )
    sanitizer_strict_social_prose_owner = _first_present(
        sanitizer_trace,
        ("sanitizer_strict_social_prose_owner",),
    )
    sanitizer_strict_social_source = _first_present(sanitizer_trace, ("sanitizer_strict_social_source",))
    interaction_continuity_validation = _find_nested_mapping(payload, "interaction_continuity_validation")

    final_text = str(snap.get("gm_text") or "")
    raw_signal_presence = {
        "route_kind": route_kind is not None or _has_path(payload, "resolution.kind") or _has_path(trace, "turn_trace.social_contract_trace.route_selected"),
        "selected_speaker_id": selected_speaker_id is not None,
        "final_emitted_source": "final_emitted_source" in fem,
        "final_emission_mutation_lineage": "final_emission_mutation_lineage" in fem,
        "response_type_required": "response_type_required" in fem,
        "response_type_candidate_ok": "response_type_candidate_ok" in fem,
        "response_type_repair_used": "response_type_repair_used" in fem,
        "upstream_prepared_emission_used": "upstream_prepared_emission_used" in fem,
        "upstream_prepared_emission_valid": "upstream_prepared_emission_valid" in fem,
        "upstream_prepared_emission_source": "upstream_prepared_emission_source" in fem,
        "upstream_prepared_emission_reject_reason": "upstream_prepared_emission_reject_reason" in fem,
        "sealed_fallback_owner_bucket": "sealed_fallback_owner_bucket" in fem,
        "visibility_fallback_owner_bucket": "visibility_fallback_owner_bucket" in fem,
        "visibility_replacement_applied": "visibility_replacement_applied" in fem,
        "visibility_fallback_pool": "visibility_fallback_pool" in fem,
        "visibility_fallback_kind": "visibility_fallback_kind" in fem,
        "fallback_family": "fallback_family_used" in fem or "realization_fallback_family" in fem,
        "trace.canonical_entry": bool(canonical_entry),
        "trace.turn_trace": bool(turn_trace),
        "trace.social_contract_trace": bool(social_contract_trace),
    }
    normalized_signal_presence = {
        "final_emitted_source": "final_emitted_source" in fem_normalized,
        "final_emission_mutation_lineage": "final_emission_mutation_lineage" in fem_normalized,
        "response_type_required": "response_type_required" in fem_normalized,
        "response_type_candidate_ok": "response_type_candidate_ok" in fem_normalized,
        "response_type_repair_used": "response_type_repair_used" in fem_normalized,
        "upstream_prepared_emission_used": "upstream_prepared_emission_used" in fem_normalized,
        "upstream_prepared_emission_valid": "upstream_prepared_emission_valid" in fem_normalized,
        "upstream_prepared_emission_source": "upstream_prepared_emission_source" in fem_normalized,
        "upstream_prepared_emission_reject_reason": "upstream_prepared_emission_reject_reason" in fem_normalized,
        "sealed_fallback_owner_bucket": "sealed_fallback_owner_bucket" in fem_normalized,
        "visibility_fallback_owner_bucket": "visibility_fallback_owner_bucket" in fem_normalized,
        "visibility_replacement_applied": "visibility_replacement_applied" in fem_normalized,
        "visibility_fallback_pool": "visibility_fallback_pool" in fem_normalized,
        "visibility_fallback_kind": "visibility_fallback_kind" in fem_normalized,
        "fallback_family": "fallback_family_used" in fem_normalized or "realization_fallback_family" in fem_normalized,
    }
    missing_source_by_field = {}
    for field, raw_present in raw_signal_presence.items():
        if raw_present is True and field in normalized_signal_presence and normalized_signal_presence[field] is False:
            missing_source_by_field[field] = "normalized_view_missing_raw_present"
        elif raw_present is True:
            missing_source_by_field[field] = "projection_missing_raw_present"
        elif raw_present is False:
            missing_source_by_field[field] = "runtime_missing_raw_absent"
    observed = {
        "scenario_id": scenario_id,
        "turn_index": snap.get("turn_index"),
        "player_text": snap.get("player_text"),
        "final_text": final_text,
        "resolution_kind": resolution.get("kind"),
        "route_kind": route_kind,
        "selected_speaker_id": selected_speaker_id,
        "selected_speaker_source": selected_speaker_source,
        "final_emitted_source": final_emitted_source,
        "final_emission_mutation_lineage": list(final_emission_mutation_lineage)
        if isinstance(final_emission_mutation_lineage, list)
        else final_emission_mutation_lineage,
        "response_type_required": response_type_required,
        "response_type_candidate_ok": response_type_candidate_ok,
        "response_type_repair_used": response_type_repair_used,
        "response_type_repair_kind": response_type_repair_kind,
        "upstream_prepared_emission_used": upstream_prepared_emission_used,
        "upstream_prepared_emission_valid": upstream_prepared_emission_valid,
        "upstream_prepared_emission_source": upstream_prepared_emission_source,
        "upstream_prepared_emission_reject_reason": upstream_prepared_emission_reject_reason,
        "post_gate_mutation_detected": post_gate_mutation_detected,
        "strict_social_active": _first_present(fem, ("strict_social_active",)),
        "speaker_contract_enforcement_reason": _first_present(fem, ("speaker_contract_enforcement_reason",)),
        "fallback_behavior_repaired": _first_present(fem, ("fallback_behavior_repaired",)),
        "fallback_behavior_repair_kind": _first_present(fem, ("fallback_behavior_repair_kind",)),
        "fallback_behavior_repair_mode": _first_present(fem, ("fallback_behavior_repair_mode",)),
        "narrative_authenticity_repair_mode": _first_present(fem, ("narrative_authenticity_repair_mode",)),
        "stage_diff": stage_diff,
        "sanitizer_mode": sanitizer_mode,
        "sanitizer_event_count": sanitizer_event_count,
        "sanitizer_changed_count": sanitizer_changed_count,
        "sanitizer_rewrite_used": sanitizer_rewrite_used,
        "sanitizer_empty_fallback_used": sanitizer_empty_fallback_used,
        "sanitizer_empty_fallback_source": sanitizer_empty_fallback_source,
        "sanitizer_empty_fallback_owner": sanitizer_empty_fallback_owner,
        "sanitizer_lineage_mode": sanitizer_lineage_mode,
        "sanitizer_lineage_changed_count": sanitizer_lineage_changed_count,
        "sanitizer_lineage_dropped_count": sanitizer_lineage_dropped_count,
        "sanitizer_lineage_empty_fallback_used": sanitizer_lineage_empty_fallback_used,
        "sanitizer_lineage_legacy_rewrite_active": sanitizer_lineage_legacy_rewrite_active,
        "sanitizer_strict_social_fallback_used": sanitizer_strict_social_fallback_used,
        "sanitizer_strict_social_selection_owner": sanitizer_strict_social_selection_owner,
        "sanitizer_strict_social_prose_owner": sanitizer_strict_social_prose_owner,
        "sanitizer_strict_social_source": sanitizer_strict_social_source,
        "sanitizer_leak_terms": ["scaffold_leakage"] if final_text_has_scaffold_leakage(final_text) else [],
        "opening_recovered_via_fallback": opening_recovered_via_fallback,
        "opening_fallback_authorship_source": opening_fallback_authorship_source,
        "opening_fallback_owner_bucket": opening_fallback_owner_bucket,
        "sealed_fallback_owner_bucket": sealed_fallback_owner_bucket,
        "visibility_fallback_owner_bucket": visibility_fallback_owner_bucket,
        "visibility_replacement_applied": visibility_replacement_applied,
        "visibility_fallback_pool": visibility_fallback_pool,
        "visibility_fallback_kind": visibility_fallback_kind,
        "fallback_family": fallback_family,
        "fallback_temporal_frame": fallback_temporal_frame,
        "scaffold_leakage": final_text_has_scaffold_leakage(final_text),
        "final_text_hash": golden_text_hash(final_text),
        "trace": {
            "canonical_entry_path": trace.get("canonical_entry_path"),
            "canonical_entry_reason": trace.get("canonical_entry_reason"),
            "canonical_entry_target_actor_id": trace.get("canonical_entry_target_actor_id"),
            "canonical_entry": dict(canonical_entry),
            "turn_trace": dict(turn_trace),
            "social_contract_trace": dict(social_contract_trace),
        },
        "snapshot_summary": compact_snapshot_summary(snap),
        "raw_signal_presence": raw_signal_presence,
        "normalized_signal_presence": normalized_signal_presence,
        "missing_source_by_field": missing_source_by_field,
        "fem_raw_keys": sorted(str(k) for k in fem.keys()),
        "fem_normalized_keys": sorted(str(k) for k in fem_normalized.keys()),
        "emission_debug_lane_keys": sorted(str(k) for k in emission_debug_lane.keys()),
        "runtime_lineage_events": runtime_lineage_events,
        "interaction_continuity_validation": interaction_continuity_validation,
    }
    observed["unavailable"] = sorted(
        key
        for key in (
            "route_kind",
            "selected_speaker_id",
            "final_emitted_source",
            "response_type_required",
            "response_type_candidate_ok",
            "response_type_repair_used",
            "fallback_family",
            "trace.canonical_entry",
            "trace.turn_trace",
            "trace.social_contract_trace",
        )
        if (
            (key == "trace.canonical_entry" and not observed["trace"]["canonical_entry"])
            or (key == "trace.turn_trace" and not observed["trace"]["turn_trace"])
            or (key == "trace.social_contract_trace" and not observed["trace"]["social_contract_trace"])
            or (not key.startswith("trace.") and observed.get(key) is None)
        )
    )
    return observed


def run_golden_replay(
    *,
    scenario_id: str,
    turns: list[str],
    tmp_path: Path,
    monkeypatch: Any,
    setup_fn: GoldenSetupFn | None = None,
    starting_scene_id: str | None = None,
    extra_scene_ids: tuple[str, ...] = (),
    chat_fn: GoldenChatFn | None = None,
) -> dict[str, Any]:
    """Run transcript turns and return a stable golden-observation result."""
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
    for i, text in enumerate(turns):
        payload = fn(ChatRequest(text=text))
        if not isinstance(payload, dict):
            raise TypeError("chat_fn must return a dict payload")
        snap = snapshot_from_chat_payload(i, text, payload)
        observed_turns.append(_observed_turn(scenario_id=scenario_id, snap=snap, payload=payload))

    return {
        "scenario_id": scenario_id,
        "turn_count": len(observed_turns),
        "turns": observed_turns,
    }


def format_golden_replay_debug(result: Mapping[str, Any]) -> str:
    """Readable failure/debug output for golden replay tests."""
    lines = [f"scenario_id: {result.get('scenario_id')!r}", f"turn_count: {result.get('turn_count')!r}"]
    turns = result.get("turns") if isinstance(result.get("turns"), list) else []
    for turn in turns:
        if not isinstance(turn, Mapping):
            continue
        lines.extend(
            [
                f"turn[{turn.get('turn_index')}].player_text: {turn.get('player_text')!r}",
                f"turn[{turn.get('turn_index')}].resolution_kind: {turn.get('resolution_kind')!r}",
                f"turn[{turn.get('turn_index')}].route_kind: {turn.get('route_kind')!r}",
                f"turn[{turn.get('turn_index')}].selected_speaker_id: {turn.get('selected_speaker_id')!r}",
                f"turn[{turn.get('turn_index')}].final_emitted_source: {turn.get('final_emitted_source')!r}",
                f"turn[{turn.get('turn_index')}].final_emission_mutation_lineage: {turn.get('final_emission_mutation_lineage')!r}",
                f"turn[{turn.get('turn_index')}].response_type_required: {turn.get('response_type_required')!r}",
                f"turn[{turn.get('turn_index')}].response_type_candidate_ok: {turn.get('response_type_candidate_ok')!r}",
                f"turn[{turn.get('turn_index')}].response_type_repair_used: {turn.get('response_type_repair_used')!r}",
                f"turn[{turn.get('turn_index')}].response_type_repair_kind: {turn.get('response_type_repair_kind')!r}",
                f"turn[{turn.get('turn_index')}].upstream_prepared_emission_used: {turn.get('upstream_prepared_emission_used')!r}",
                f"turn[{turn.get('turn_index')}].upstream_prepared_emission_valid: {turn.get('upstream_prepared_emission_valid')!r}",
                f"turn[{turn.get('turn_index')}].upstream_prepared_emission_source: {turn.get('upstream_prepared_emission_source')!r}",
                f"turn[{turn.get('turn_index')}].upstream_prepared_emission_reject_reason: {turn.get('upstream_prepared_emission_reject_reason')!r}",
                f"turn[{turn.get('turn_index')}].sanitizer_empty_fallback_used: {turn.get('sanitizer_empty_fallback_used')!r}",
                f"turn[{turn.get('turn_index')}].sanitizer_empty_fallback_source: {turn.get('sanitizer_empty_fallback_source')!r}",
                f"turn[{turn.get('turn_index')}].sanitizer_empty_fallback_owner: {turn.get('sanitizer_empty_fallback_owner')!r}",
                f"turn[{turn.get('turn_index')}].sanitizer_lineage_mode: {turn.get('sanitizer_lineage_mode')!r}",
                f"turn[{turn.get('turn_index')}].sanitizer_lineage_changed_count: {turn.get('sanitizer_lineage_changed_count')!r}",
                f"turn[{turn.get('turn_index')}].sanitizer_lineage_dropped_count: {turn.get('sanitizer_lineage_dropped_count')!r}",
                f"turn[{turn.get('turn_index')}].sanitizer_lineage_empty_fallback_used: {turn.get('sanitizer_lineage_empty_fallback_used')!r}",
                f"turn[{turn.get('turn_index')}].sanitizer_lineage_legacy_rewrite_active: {turn.get('sanitizer_lineage_legacy_rewrite_active')!r}",
                f"turn[{turn.get('turn_index')}].sanitizer_strict_social_fallback_used: {turn.get('sanitizer_strict_social_fallback_used')!r}",
                f"turn[{turn.get('turn_index')}].sanitizer_strict_social_selection_owner: {turn.get('sanitizer_strict_social_selection_owner')!r}",
                f"turn[{turn.get('turn_index')}].sanitizer_strict_social_prose_owner: {turn.get('sanitizer_strict_social_prose_owner')!r}",
                f"turn[{turn.get('turn_index')}].sanitizer_strict_social_source: {turn.get('sanitizer_strict_social_source')!r}",
                f"turn[{turn.get('turn_index')}].opening_recovered_via_fallback: {turn.get('opening_recovered_via_fallback')!r}",
                f"turn[{turn.get('turn_index')}].opening_fallback_authorship_source: {turn.get('opening_fallback_authorship_source')!r}",
                f"turn[{turn.get('turn_index')}].opening_fallback_owner_bucket: {turn.get('opening_fallback_owner_bucket')!r}",
                f"turn[{turn.get('turn_index')}].sealed_fallback_owner_bucket: {turn.get('sealed_fallback_owner_bucket')!r}",
                f"turn[{turn.get('turn_index')}].fallback_family: {turn.get('fallback_family')!r}",
                f"turn[{turn.get('turn_index')}].fallback_temporal_frame: {turn.get('fallback_temporal_frame')!r}",
                f"turn[{turn.get('turn_index')}].runtime_lineage_events: {turn.get('runtime_lineage_events')!r}",
                f"turn[{turn.get('turn_index')}].scaffold_leakage: {turn.get('scaffold_leakage')!r}",
                f"turn[{turn.get('turn_index')}].unavailable: {turn.get('unavailable')!r}",
                f"turn[{turn.get('turn_index')}].snapshot_summary: {turn.get('snapshot_summary')}",
            ]
        )
    drift = result.get("drift") if isinstance(result.get("drift"), Mapping) else {}
    classifications = drift.get("failure_classifications") if isinstance(drift, Mapping) else None
    if isinstance(classifications, list) and classifications:
        lines.append("failure_classifications:")
        for row in classifications:
            if not isinstance(row, Mapping):
                continue
            lines.append(
                "  "
                + ", ".join(
                    [
                        f"turn={row.get('turn_index')!r}",
                        f"category={row.get('category')!r}",
                        f"owner={row.get('primary_owner')!r}",
                        f"severity={row.get('severity')!r}",
                        f"investigate_first={row.get('investigate_first')!r}",
                    ]
                )
            )
    return "\n".join(lines)
