"""Compact golden replay helpers built on the transcript runner.

This module is intentionally test-only.  It projects existing transcript
snapshots and chat payloads into a stable, assertion-friendly shape without
changing runtime behavior or creating a second storage/test harness.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Callable, Mapping

from game.api import chat
from game.final_emission_meta import (
    normalize_final_emission_meta_for_observability,
    opening_fallback_owner_bucket_from_meta,
    read_emission_debug_lane_from_turn_payload,
    read_final_emission_meta_from_turn_payload,
)
from game.models import ChatRequest
from game.output_sanitizer import resembles_serialized_response_payload
from game import storage

from tests.debug_trace_utils import latest_compact_debug_trace_entry
from tests.helpers.failure_classifier import classify_replay_failure
from tests.helpers.failure_dashboard_report import (
    failure_dashboard_requested,
    record_failure_dashboard_rows,
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


def assert_golden_turn_observation(
    turn: Mapping[str, Any],
    expectation: Mapping[str, Any],
    *,
    debug_context: str = "",
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
        raise AssertionError(
            _format_expected_failure(
                field_path=field_path,
                expected=f"available or explicitly allowed unavailable; allowed={sorted(allow_unavailable)!r}",
                actual=actual,
                reason="unexpected unavailable field",
                debug_context=debug_context,
            )
        )

    for field_path in expectation.get("require_present", []):
        actual = _lookup_path(turn, str(field_path))
        if actual is _MISSING or actual is None or actual == "":
            raise AssertionError(
                _format_expected_failure(
                    field_path=str(field_path),
                    expected="present non-empty value",
                    actual=actual,
                    reason="required field absent",
                    debug_context=debug_context,
                )
            )

    equals = expectation.get("equals") if isinstance(expectation.get("equals"), Mapping) else {}
    for field_path, expected in equals.items():
        actual = _lookup_path(turn, str(field_path))
        if actual != expected:
            raise AssertionError(
                _format_expected_failure(
                    field_path=str(field_path),
                    expected=expected,
                    actual=actual,
                    reason="exact value mismatch",
                    debug_context=debug_context,
                )
            )

    one_of = expectation.get("one_of") if isinstance(expectation.get("one_of"), Mapping) else {}
    for field_path, allowed in one_of.items():
        allowed_values = list(allowed) if isinstance(allowed, (list, tuple, set, frozenset)) else [allowed]
        actual = _lookup_path(turn, str(field_path))
        if actual not in allowed_values:
            raise AssertionError(
                _format_expected_failure(
                    field_path=str(field_path),
                    expected=allowed_values,
                    actual=actual,
                    reason="value not in allowed set",
                    debug_context=debug_context,
                )
            )

    not_equals = expectation.get("not_equals") if isinstance(expectation.get("not_equals"), Mapping) else {}
    for field_path, forbidden in not_equals.items():
        actual = _lookup_path(turn, str(field_path))
        if actual == forbidden:
            raise AssertionError(
                _format_expected_failure(
                    field_path=str(field_path),
                    expected=f"anything except {forbidden!r}",
                    actual=actual,
                    reason="forbidden exact value observed",
                    debug_context=debug_context,
                )
            )

    final_text = str(turn.get("final_text") or "")
    for needle in expectation.get("text_must_include", []):
        if str(needle) not in final_text:
            raise AssertionError(
                _format_expected_failure(
                    field_path="final_text",
                    expected=f"include {str(needle)!r}",
                    actual=final_text,
                    reason="required text fragment missing",
                    debug_context=debug_context,
                )
            )
    for needle in expectation.get("text_must_not_include", []):
        if str(needle) in final_text:
            raise AssertionError(
                _format_expected_failure(
                    field_path="final_text",
                    expected=f"not include {str(needle)!r}",
                    actual=final_text,
                    reason="forbidden text fragment observed",
                    debug_context=debug_context,
                )
            )

    expected_scaffold = expectation.get("scaffold_leakage")
    if expected_scaffold is not None:
        actual = _lookup_path(turn, "scaffold_leakage")
        if actual is not bool(expected_scaffold):
            raise AssertionError(
                _format_expected_failure(
                    field_path="scaffold_leakage",
                    expected=bool(expected_scaffold),
                    actual=actual,
                    reason="scaffold leakage mismatch",
                    debug_context=debug_context,
                )
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
                f"turn[{turn.get('turn_index')}].fallback_family: {turn.get('fallback_family')!r}",
                f"turn[{turn.get('turn_index')}].fallback_temporal_frame: {turn.get('fallback_temporal_frame')!r}",
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
