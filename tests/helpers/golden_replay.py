"""Compact golden replay helpers built on the transcript runner.

This module is intentionally test-only.  It projects existing transcript
snapshots and chat payloads into a stable, assertion-friendly shape without
changing runtime behavior or creating a second storage/test harness.
"""
from __future__ import annotations

import json
import os
from collections import Counter
from pathlib import Path
from typing import Any, Callable, Mapping

from game.api import chat
from game.runtime_lineage_telemetry import normalize_runtime_lineage_events
from tests.helpers.runtime_lineage_reporting import build_runtime_lineage_summary
from game.models import ChatRequest
from game.scenario_spine_eval import evaluate_scenario_spine_session, minimal_complete_transcript_turn_meta
from game import storage

from tests.helpers.failure_classifier import classify_replay_failure
from tests.helpers.golden_replay_projection import (
    MISSING as _MISSING,
    NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
    _echo_overlap_band,
    final_text_has_scaffold_leakage,
    golden_text_hash,
    lookup_observation_path as _lookup_path,
    normalize_golden_text,
    project_turn_observation,
    protected_observation_drift_bucket,
)
from tests.helpers.failure_dashboard_report import (
    failure_dashboard_requested,
    record_failure_dashboard_rows,
    record_protected_replay_assertion_failure,
    record_runtime_lineage_events,
)
from tests.helpers.transcript_runner import (
    new_clean_campaign,
    patch_transcript_storage,
    snapshot_from_chat_payload,
    write_default_bootstrap_scenes,
)


GoldenSetupFn = Callable[[], None]
GoldenChatFn = Callable[[ChatRequest], dict[str, Any]]
REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTIER_GATE_LONG_SESSION_SOURCE_PATH = "data/validation/scenario_spines/frontier_gate_long_session.json"
FRONTIER_GATE_LONG_SESSION_PATH = REPO_ROOT / FRONTIER_GATE_LONG_SESSION_SOURCE_PATH
PROTECTED_NO_SCAFFOLD_TERMS = ("planner", "router", "validator", "adjudication", "scaffold")
PROTECTED_SOCIAL_RESOLUTION_KINDS = ("question", "social", "social_exchange", "dialogue")
PROTECTED_SOCIAL_ROUTE_KINDS = ("social", "question", "social_engine", "dialogue")
PROTECTED_DIALOGUE_TRACE_ROUTES = ("social", "dialogue")
PROTECTED_GLOBAL_SCENE_FALLBACK_SOURCE = "global_scene_fallback"


def protected_no_scaffold_expectation(*, extra_terms: tuple[str, ...] = ()) -> dict[str, Any]:
    """Protected replay fragment for the shared player-facing scaffold leak lock."""
    return {
        "text_must_not_include": [*extra_terms, *PROTECTED_NO_SCAFFOLD_TERMS],
        "scaffold_leakage": False,
    }


def protected_unavailable_expectation(*field_paths: str) -> dict[str, Any]:
    """Protected replay fragment for explicitly optional projected observation fields."""
    return {"allow_unavailable": list(field_paths)}


def protected_route_expectation(
    *,
    include_resolution_kind: bool = False,
    include_route_kind: bool = True,
    include_trace_route: bool = False,
) -> dict[str, Any]:
    """Protected replay fragment for social/dialogue route-shape observations."""
    one_of: dict[str, list[str]] = {}
    if include_resolution_kind:
        one_of["resolution_kind"] = list(PROTECTED_SOCIAL_RESOLUTION_KINDS)
    if include_route_kind:
        one_of["route_kind"] = list(PROTECTED_SOCIAL_ROUTE_KINDS)
    if include_trace_route:
        one_of["trace.social_contract_trace.route_selected"] = list(PROTECTED_DIALOGUE_TRACE_ROUTES)
    return {"one_of": one_of}


def protected_source_expectation(*, disallow_global_scene_fallback: bool = True) -> dict[str, Any]:
    """Protected replay fragment for final source locks."""
    if not disallow_global_scene_fallback:
        return {}
    return {"not_equals": {"final_emitted_source": PROTECTED_GLOBAL_SCENE_FALLBACK_SOURCE}}


def protected_structural_expectation(
    *,
    require_present: tuple[str, ...] | list[str] = (),
    allow_unavailable: tuple[str, ...] | list[str] = (),
    equals: Mapping[str, Any] | None = None,
    one_of: Mapping[str, Any] | None = None,
    not_equals: Mapping[str, Any] | None = None,
    include_resolution_kind: bool = False,
    include_route_kind: bool = True,
    include_trace_route: bool = False,
    disallow_global_scene_fallback: bool = False,
    no_scaffold: bool = True,
    extra_no_scaffold_terms: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Compose common protected replay structural expectation fragments."""
    out: dict[str, Any] = {}

    if require_present:
        out["require_present"] = list(require_present)

    if allow_unavailable:
        out.update(protected_unavailable_expectation(*allow_unavailable))

    if equals:
        out["equals"] = dict(equals)

    route_fragment = protected_route_expectation(
        include_resolution_kind=include_resolution_kind,
        include_route_kind=include_route_kind,
        include_trace_route=include_trace_route,
    )
    route_one_of = route_fragment.get("one_of") if isinstance(route_fragment.get("one_of"), Mapping) else {}
    custom_one_of = dict(one_of) if one_of else {}
    merged_one_of = {**route_one_of, **custom_one_of}
    if merged_one_of:
        out["one_of"] = merged_one_of

    source_fragment = protected_source_expectation(
        disallow_global_scene_fallback=disallow_global_scene_fallback,
    )
    source_not_equals = source_fragment.get("not_equals") if isinstance(source_fragment.get("not_equals"), Mapping) else {}
    custom_not_equals = dict(not_equals) if not_equals else {}
    merged_not_equals = {**source_not_equals, **custom_not_equals}
    if merged_not_equals:
        out["not_equals"] = merged_not_equals

    if no_scaffold:
        out.update(protected_no_scaffold_expectation(extra_terms=extra_no_scaffold_terms))

    return out


def protected_social_structural_base(
    *,
    selected_speaker_id: str,
    canonical_target_id: str | None = None,
    require_present: tuple[str, ...] | list[str] = (),
    allow_unavailable: tuple[str, ...] | list[str] = ("fallback_family",),
    equals: Mapping[str, Any] | None = None,
    one_of: Mapping[str, Any] | None = None,
    not_equals: Mapping[str, Any] | None = None,
    require_resolution_kind: bool = False,
    require_route_kind: bool = False,
    require_final_emitted_source: bool = False,
    require_trace_target: bool = False,
    require_trace_route: bool = False,
    include_resolution_kind: bool = False,
    include_route_kind: bool = True,
    include_trace_route: bool = False,
    disallow_global_scene_fallback: bool = False,
    extra_no_scaffold_terms: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Compose common protected social/dialogue structural expectation fragments."""
    required = ["final_text"]
    if require_resolution_kind:
        required.append("resolution_kind")
    if require_route_kind:
        required.append("route_kind")
    required.extend(["selected_speaker_id", *list(require_present)])
    if require_final_emitted_source:
        required.append("final_emitted_source")
    if require_trace_target:
        required.append("trace.canonical_entry.target_actor_id")
    if require_trace_route:
        required.append("trace.social_contract_trace.route_selected")

    expected_equals: dict[str, Any] = {"selected_speaker_id": selected_speaker_id}
    if canonical_target_id is not None:
        expected_equals["trace.canonical_entry.target_actor_id"] = canonical_target_id
    if equals:
        expected_equals.update(equals)

    return protected_structural_expectation(
        require_present=tuple(required),
        allow_unavailable=allow_unavailable,
        equals=expected_equals,
        one_of=one_of,
        not_equals=not_equals,
        include_resolution_kind=include_resolution_kind,
        include_route_kind=include_route_kind,
        include_trace_route=include_trace_route,
        disallow_global_scene_fallback=disallow_global_scene_fallback,
        extra_no_scaffold_terms=extra_no_scaffold_terms,
    )


def load_frontier_gate_long_session_spine() -> dict[str, Any]:
    """Load the authoritative Frontier Gate long-session replay fixture."""
    return json.loads(FRONTIER_GATE_LONG_SESSION_PATH.read_text(encoding="utf-8"))


def _frontier_gate_branch(branch_id: str) -> Mapping[str, Any]:
    raw = load_frontier_gate_long_session_spine()
    return next(b for b in raw["branches"] if b["branch_id"] == branch_id)


def frontier_gate_branch_prompts(branch_id: str, max_turns: int | None = None) -> list[str]:
    branch = _frontier_gate_branch(branch_id)
    turns = branch["turns"] if max_turns is None else branch["turns"][:max_turns]
    return [str(turn["player_prompt"]) for turn in turns]


def frontier_gate_branch_turn_ids(branch_id: str, max_turns: int | None = None) -> list[str]:
    branch = _frontier_gate_branch(branch_id)
    turns = branch["turns"] if max_turns is None else branch["turns"][:max_turns]
    return [str(turn["turn_id"]) for turn in turns]


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


def _drift_bucket_for_field(field_path: str) -> str:
    return protected_observation_drift_bucket(field_path)


def _allow_unavailable_paths(expectation: Mapping[str, Any]) -> set[str]:
    return {
        str(path)
        for path in expectation.get("allow_unavailable", [])
        if isinstance(path, str) and path.strip()
    }


def _unavailable_paths(observed: Mapping[str, Any]) -> set[str]:
    return {
        str(path)
        for path in observed.get("unavailable", [])
        if isinstance(path, str) and path.strip()
    }


def _evaluate_golden_expectation(
    observed: Mapping[str, Any],
    expectation: Mapping[str, Any],
) -> list[dict[str, Any]]:
    """Return compact drift rows for shared golden expectation evaluation."""
    issues: list[dict[str, Any]] = []

    def _issue(
        field_path: str,
        expected: Any,
        actual: Any,
        reason: str,
        *,
        drift_bucket: str | None = None,
    ) -> None:
        issues.append(
            {
                "field_path": str(field_path),
                "expected": expected,
                "actual": actual,
                "reason": str(reason),
                "drift_bucket": drift_bucket if drift_bucket is not None else _drift_bucket_for_field(field_path),
            }
        )

    allow_unavailable = _allow_unavailable_paths(expectation)
    for field_path in sorted(_unavailable_paths(observed) - allow_unavailable):
        _issue(
            field_path,
            f"available or allowed unavailable; allowed={sorted(allow_unavailable)!r}",
            _lookup_path(observed, field_path),
            "unexpected unavailable field",
        )

    for field_path in expectation.get("require_present", []):
        field_s = str(field_path)
        actual = _lookup_path(observed, field_s)
        if actual is _MISSING or actual is None or actual == "":
            _issue(field_s, "present non-empty value", actual, "required field absent")

    equals = expectation.get("equals") if isinstance(expectation.get("equals"), Mapping) else {}
    for field_path, expected in equals.items():
        field_s = str(field_path)
        actual = _lookup_path(observed, field_s)
        if actual != expected:
            _issue(field_s, expected, actual, "exact value mismatch")

    one_of = expectation.get("one_of") if isinstance(expectation.get("one_of"), Mapping) else {}
    for field_path, allowed in one_of.items():
        field_s = str(field_path)
        allowed_values = list(allowed) if isinstance(allowed, (list, tuple, set, frozenset)) else [allowed]
        actual = _lookup_path(observed, field_s)
        if actual not in allowed_values:
            _issue(field_s, allowed_values, actual, "value not in allowed set")

    not_equals = expectation.get("not_equals") if isinstance(expectation.get("not_equals"), Mapping) else {}
    for field_path, forbidden in not_equals.items():
        field_s = str(field_path)
        actual = _lookup_path(observed, field_s)
        if actual == forbidden:
            _issue(field_s, f"anything except {forbidden!r}", actual, "forbidden value observed")

    final_text = str(observed.get("final_text") or "")
    for needle in expectation.get("text_must_include", []):
        if str(needle) not in final_text:
            _issue(
                "final_text",
                f"include {str(needle)!r}",
                final_text,
                "required text fragment missing",
                drift_bucket="semantic_drift",
            )
    for needle in expectation.get("text_must_not_include", []):
        if str(needle) in final_text:
            _issue(
                "final_text",
                f"not include {str(needle)!r}",
                final_text,
                "forbidden text fragment observed",
                drift_bucket="semantic_drift",
            )

    expected_scaffold = expectation.get("scaffold_leakage")
    if expected_scaffold is not None:
        actual_scaffold = _lookup_path(observed, "scaffold_leakage")
        if actual_scaffold is not bool(expected_scaffold):
            _issue(
                "scaffold_leakage",
                bool(expected_scaffold),
                actual_scaffold,
                "scaffold leakage mismatch",
                drift_bucket="semantic_drift",
            )

    return issues


def _assert_expected_for_issue(issue: Mapping[str, Any], expectation: Mapping[str, Any]) -> Any:
    if issue.get("reason") == "unexpected unavailable field":
        allow_unavailable = _allow_unavailable_paths(expectation)
        return f"available or explicitly allowed unavailable; allowed={sorted(allow_unavailable)!r}"
    return issue.get("expected")


def _assert_reason_for_issue(issue: Mapping[str, Any]) -> str:
    reason = str(issue.get("reason") or "")
    if reason == "forbidden value observed":
        return "forbidden exact value observed"
    return reason


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
    for issue in _evaluate_golden_expectation(turn, expectation):
        _raise_expected_failure(
            turn=turn,
            field_path=str(issue["field_path"]),
            expected=_assert_expected_for_issue(issue, expectation),
            actual=issue["actual"],
            reason=_assert_reason_for_issue(issue),
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

    for issue in _evaluate_golden_expectation(observed, expectation):
        _add_drift(
            out,
            str(issue["drift_bucket"]),
            str(issue["field_path"]),
            issue["expected"],
            issue["actual"],
            str(issue["reason"]),
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


_RESPONSE_DELTA_SIGNAL_KEYS = frozenset(
    {
        "response_delta_checked",
        "response_delta_failed",
        "response_delta_repaired",
        "response_delta_kind",
        "response_delta_kind_detected",
        "response_delta_echo_overlap_ratio",
        "response_delta_echo_overlap_band",
        "response_delta_skip_reason",
        "response_delta_trigger_source",
    }
)


def _response_delta_kind_for_turn(turn: Mapping[str, Any]) -> str | None:
    for key in ("response_delta_kind", "response_delta_kind_detected"):
        value = turn.get(key)
        if value is not None and str(value).strip():
            return str(value).strip()
    return None


def summarize_response_delta_observations(turns: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Summarize existing response-delta/FEM signals without judging prose semantics."""
    checked_count = 0
    failed_count = 0
    repaired_count = 0
    unknown_count = 0
    kind_values: list[str] = []
    echo_bands: list[str] = []

    for turn in turns:
        if not any(key in turn and turn.get(key) is not None for key in _RESPONSE_DELTA_SIGNAL_KEYS):
            unknown_count += 1
            continue
        if turn.get("response_delta_checked") is True:
            checked_count += 1
        if turn.get("response_delta_failed") is True:
            failed_count += 1
        if turn.get("response_delta_repaired") is True:
            repaired_count += 1
        kind = _response_delta_kind_for_turn(turn)
        if kind:
            kind_values.append(kind)
        band = _echo_overlap_band(turn.get("response_delta_echo_overlap_band"))
        if band is None:
            band = _echo_overlap_band(turn.get("response_delta_echo_overlap_ratio"))
        if band:
            echo_bands.append(band)

    return {
        "response_delta_checked_count": checked_count,
        "response_delta_failed_count": failed_count,
        "response_delta_repaired_count": repaired_count,
        "response_delta_kind_counts": _counter_dict(kind_values),
        "response_delta_unknown_count": unknown_count,
        "echo_overlap_band_counts": _counter_dict(echo_bands),
    }


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


def _fallback_owner_for_rerun_turn(turn: Mapping[str, Any]) -> str | None:
    owner = _owner_for_turn(turn)
    if owner:
        return owner
    for event in _lineage_fallback_events(turn):
        for key in ("fallback_selection_owner", "fallback_content_owner", "owner"):
            value = event.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


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


def _rerun_value(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _rerun_text_hash(turn: Mapping[str, Any]) -> str | None:
    if "final_text" not in turn:
        return None
    return golden_text_hash(turn.get("final_text"))


def _frequency_delta(previous: Mapping[str, int], current: Mapping[str, int]) -> dict[str, Any]:
    prev = {str(k): int(v) for k, v in previous.items()}
    cur = {str(k): int(v) for k, v in current.items()}
    keys = sorted(set(prev) | set(cur))
    delta = {key: cur.get(key, 0) - prev.get(key, 0) for key in keys if cur.get(key, 0) != prev.get(key, 0)}
    return {
        "previous": dict(sorted(prev.items())),
        "current": dict(sorted(cur.items())),
        "delta": delta,
        "changed_key_count": len(delta),
    }


def _runtime_lineage_events_for_turns(turns: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for turn in turns:
        events.extend(_lineage_events_for_turn(turn))
    return events


def _runtime_lineage_delta(previous: Mapping[str, Any], current: Mapping[str, Any]) -> dict[str, Any]:
    frequency_keys = (
        "by_event_kind",
        "by_stage",
        "fallback_frequency",
        "fallback_selection_owner_frequency",
        "fallback_content_owner_frequency",
        "speaker_repair_frequency",
        "mutation_kind_frequency",
        "gate_path_frequency",
        "by_recurrence_key",
    )
    out: dict[str, Any] = {
        "previous_total_events": int(previous.get("total_events") or 0),
        "current_total_events": int(current.get("total_events") or 0),
        "total_event_delta": int(current.get("total_events") or 0) - int(previous.get("total_events") or 0),
        "frequency_deltas": {},
    }
    changed = 0
    for key in frequency_keys:
        delta = _frequency_delta(
            previous.get(key) if isinstance(previous.get(key), Mapping) else {},
            current.get(key) if isinstance(current.get(key), Mapping) else {},
        )
        out["frequency_deltas"][key] = delta
        changed += int(delta["changed_key_count"])
    out["changed_key_count"] = changed
    return out


def compare_golden_replay_reruns(
    previous_observations: list[Mapping[str, Any]],
    current_observations: list[Mapping[str, Any]],
) -> dict[str, Any]:
    """Return a compact, report-only drift scorecard for two golden replay runs.

    The comparator is intentionally non-authoritative: it never raises, never
    decides pass/fail, and treats absent optional projection fields as ``None``.
    """

    previous_turns = [turn for turn in previous_observations if isinstance(turn, Mapping)]
    current_turns = [turn for turn in current_observations if isinstance(turn, Mapping)]
    compared = min(len(previous_turns), len(current_turns))
    per_turn_deltas: list[dict[str, Any]] = []

    speaker_delta_count = 0
    route_delta_count = 0
    fallback_delta_count = 0
    text_fingerprint_delta_count = 0
    scaffold_delta_count = 0
    runtime_lineage_delta_count = 0
    semantic_delta_frequency_delta_count = 0

    for index in range(compared):
        prev = previous_turns[index]
        cur = current_turns[index]
        row: dict[str, Any] = {
            "turn_index": index,
            "previous_turn_id": prev.get("turn_id"),
            "current_turn_id": cur.get("turn_id"),
            "deltas": {},
        }

        prev_speaker = _rerun_value(prev.get("selected_speaker_id"))
        cur_speaker = _rerun_value(cur.get("selected_speaker_id"))
        if prev_speaker != cur_speaker:
            speaker_delta_count += 1
            row["deltas"]["speaker"] = {"previous": prev_speaker, "current": cur_speaker}

        prev_route = _rerun_value(prev.get("route_kind"))
        cur_route = _rerun_value(cur.get("route_kind"))
        if prev_route != cur_route:
            route_delta_count += 1
            row["deltas"]["route"] = {"previous": prev_route, "current": cur_route}

        prev_fallback_family = _rerun_value(prev.get("fallback_family"))
        cur_fallback_family = _rerun_value(cur.get("fallback_family"))
        prev_fallback_owner = _fallback_owner_for_rerun_turn(prev)
        cur_fallback_owner = _fallback_owner_for_rerun_turn(cur)
        if prev_fallback_family != cur_fallback_family or prev_fallback_owner != cur_fallback_owner:
            fallback_delta_count += 1
            row["deltas"]["fallback"] = {
                "previous_family": prev_fallback_family,
                "current_family": cur_fallback_family,
                "previous_owner": prev_fallback_owner,
                "current_owner": cur_fallback_owner,
            }

        prev_hash = _rerun_text_hash(prev)
        cur_hash = _rerun_text_hash(cur)
        if prev_hash != cur_hash:
            text_fingerprint_delta_count += 1
            row["deltas"]["text_fingerprint"] = {"previous": prev_hash, "current": cur_hash}

        prev_scaffold = prev.get("scaffold_leakage") if "scaffold_leakage" in prev else None
        cur_scaffold = cur.get("scaffold_leakage") if "scaffold_leakage" in cur else None
        if prev_scaffold != cur_scaffold:
            scaffold_delta_count += 1
            row["deltas"]["scaffold"] = {"previous": prev_scaffold, "current": cur_scaffold}

        response_delta_fields: dict[str, Any] = {}
        for field in (
            "response_delta_checked",
            "response_delta_failed",
            "response_delta_repaired",
            "response_delta_kind",
            "response_delta_echo_overlap_band",
        ):
            prev_value = prev.get(field) if field in prev else None
            cur_value = cur.get(field) if field in cur else None
            if prev_value != cur_value:
                response_delta_fields[field] = {"previous": prev_value, "current": cur_value}
        if response_delta_fields:
            semantic_delta_frequency_delta_count += 1
            row["deltas"]["response_delta"] = response_delta_fields

        prev_lineage = build_runtime_lineage_summary(_lineage_events_for_turn(prev))
        cur_lineage = build_runtime_lineage_summary(_lineage_events_for_turn(cur))
        lineage_delta = _runtime_lineage_delta(prev_lineage, cur_lineage)
        if lineage_delta["total_event_delta"] != 0 or lineage_delta["changed_key_count"] > 0:
            runtime_lineage_delta_count += 1
            row["deltas"]["runtime_lineage"] = lineage_delta

        if row["deltas"]:
            per_turn_deltas.append(row)

    previous_lineage_summary = build_runtime_lineage_summary(_runtime_lineage_events_for_turns(previous_turns))
    current_lineage_summary = build_runtime_lineage_summary(_runtime_lineage_events_for_turns(current_turns))
    previous_fallback_owners = [_fallback_owner_for_rerun_turn(turn) for turn in previous_turns]
    current_fallback_owners = [_fallback_owner_for_rerun_turn(turn) for turn in current_turns]
    previous_response_delta_summary = summarize_response_delta_observations(previous_turns)
    current_response_delta_summary = summarize_response_delta_observations(current_turns)

    return {
        "schema_version": 1,
        "report_only": True,
        "previous_turn_count": len(previous_turns),
        "current_turn_count": len(current_turns),
        "total_turns_compared": compared,
        "extra_previous_turn_count": max(0, len(previous_turns) - compared),
        "extra_current_turn_count": max(0, len(current_turns) - compared),
        "summary": {
            "speaker_delta_count": speaker_delta_count,
            "route_delta_count": route_delta_count,
            "fallback_delta_count": fallback_delta_count,
            "text_fingerprint_delta_count": text_fingerprint_delta_count,
            "scaffold_delta_count": scaffold_delta_count,
            "runtime_lineage_delta_count": runtime_lineage_delta_count,
            "semantic_delta_frequency_delta_count": semantic_delta_frequency_delta_count,
        },
        "frequencies": {
            "speakers": _frequency_delta(
                _counter_dict([turn.get("selected_speaker_id") for turn in previous_turns]),
                _counter_dict([turn.get("selected_speaker_id") for turn in current_turns]),
            ),
            "routes": _frequency_delta(
                _counter_dict([turn.get("route_kind") for turn in previous_turns]),
                _counter_dict([turn.get("route_kind") for turn in current_turns]),
            ),
            "fallback_families": _frequency_delta(
                _counter_dict([turn.get("fallback_family") for turn in previous_turns]),
                _counter_dict([turn.get("fallback_family") for turn in current_turns]),
            ),
            "fallback_owners": _frequency_delta(
                _counter_dict(previous_fallback_owners),
                _counter_dict(current_fallback_owners),
            ),
            "runtime_lineage": _runtime_lineage_delta(previous_lineage_summary, current_lineage_summary),
            "response_delta": {
                "previous": previous_response_delta_summary,
                "current": current_response_delta_summary,
                "semantic_delta_frequency_delta_count": semantic_delta_frequency_delta_count,
                "checked": _frequency_delta(
                    {"checked": previous_response_delta_summary["response_delta_checked_count"]},
                    {"checked": current_response_delta_summary["response_delta_checked_count"]},
                ),
                "failed": _frequency_delta(
                    {"failed": previous_response_delta_summary["response_delta_failed_count"]},
                    {"failed": current_response_delta_summary["response_delta_failed_count"]},
                ),
                "repaired": _frequency_delta(
                    {"repaired": previous_response_delta_summary["response_delta_repaired_count"]},
                    {"repaired": current_response_delta_summary["response_delta_repaired_count"]},
                ),
                "kinds": _frequency_delta(
                    previous_response_delta_summary["response_delta_kind_counts"],
                    current_response_delta_summary["response_delta_kind_counts"],
                ),
                "echo_overlap_bands": _frequency_delta(
                    previous_response_delta_summary["echo_overlap_band_counts"],
                    current_response_delta_summary["echo_overlap_band_counts"],
                ),
                "unknown": _frequency_delta(
                    {"unknown": previous_response_delta_summary["response_delta_unknown_count"]},
                    {"unknown": current_response_delta_summary["response_delta_unknown_count"]},
                ),
            },
        },
        "per_turn_deltas": per_turn_deltas,
    }


def _active_telemetry_token(value: Any) -> str | None:
    if value is None or value is False:
        return None
    token = str(value).strip()
    if not token or token.lower() in {"none", "false", "no", "0"}:
        return None
    return token


def _fallback_unavailable_is_scene_action_speaker_optional(
    turn: Mapping[str, Any],
    unavailable: list[Any],
) -> bool:
    unavailable_fields = {str(item) for item in unavailable if str(item).strip()}
    if unavailable_fields != {"selected_speaker_id"}:
        return False
    route_kind = str(turn.get("route_kind") or "").strip().lower()
    response_type_required = str(turn.get("response_type_required") or "").strip().lower()
    final_source = str(turn.get("final_emitted_source") or "").strip()
    if route_kind in {"dialogue", "social", "question", "social_engine"}:
        return False
    return route_kind in {"undecided", "action"} or response_type_required in {
        "neutral_narration",
        "action_outcome",
    } or final_source in {
        NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
        "passive_scene_pressure_fallback",
        "global_scene_fallback",
        "anti_reset_local_continuation_fallback",
    }


def _fallback_selection_is_scene_action_nonblocking(turn: Mapping[str, Any]) -> bool:
    if turn.get("selected_speaker_id") is not None:
        return False
    route_kind = str(turn.get("route_kind") or "").strip().lower()
    if route_kind in {"dialogue", "social", "question", "social_engine"}:
        return False
    response_type_required = str(turn.get("response_type_required") or "").strip().lower()
    final_source = str(turn.get("final_emitted_source") or "").strip()
    fallback_family = str(turn.get("fallback_family") or "").strip()
    return route_kind in {"undecided", "action"} or response_type_required in {
        "neutral_narration",
        "action_outcome",
    } or final_source in {
        NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
        "passive_scene_pressure_fallback",
        "global_scene_fallback",
        "anti_reset_local_continuation_fallback",
    } or fallback_family in {
        NEUTRAL_REPLY_SPEAKER_GROUNDING_BRIDGE_FAMILY,
        "gate_terminal_repair",
    }


def summarize_fallback_escalation_observations(
    turns: list[Mapping[str, Any]],
) -> dict[str, Any]:
    """Return fallback escalation metrics for sustained replay observations."""
    total_turns = len(turns)
    fallback_turn_flags: list[bool] = []
    scene_action_nonblocking_fallback_turn_flags: list[bool] = []
    blocking_fallback_turn_flags: list[bool] = []
    fallback_turn_indices: list[int] = []
    fallback_windows: Counter[str] = Counter()
    fallback_lineage_kinds: list[str] = []
    fallback_lineage_owners: list[str] = []
    fallback_owner_by_turn: list[str] = []
    behavior_repair_turn_indices: list[int] = []
    response_type_repair_turn_indices: list[int] = []
    sanitizer_fallback_turn_indices: list[int] = []
    unavailable_with_fallback_count = 0
    blocking_unavailable_with_fallback_count = 0
    scene_action_speaker_optional_unavailable_count = 0
    fallback_family_unavailable_with_fallback_count = 0
    fallback_selected_without_family_count = 0

    for index, turn in enumerate(turns):
        turn_index = int(turn.get("turn_index") if turn.get("turn_index") is not None else index)
        lineage_fallbacks = _lineage_fallback_events(turn)
        has_fallback = _has_fallback_selection(turn)
        scene_action_nonblocking_fallback = has_fallback and _fallback_selection_is_scene_action_nonblocking(turn)
        fallback_turn_flags.append(has_fallback)
        scene_action_nonblocking_fallback_turn_flags.append(scene_action_nonblocking_fallback)
        blocking_fallback_turn_flags.append(has_fallback and not scene_action_nonblocking_fallback)
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
                if _fallback_unavailable_is_scene_action_speaker_optional(turn, unavailable):
                    scene_action_speaker_optional_unavailable_count += 1
                else:
                    blocking_unavailable_with_fallback_count += 1
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
    max_scene_action_nonblocking_streak = _max_consecutive_true(scene_action_nonblocking_fallback_turn_flags)
    max_blocking_streak = _max_consecutive_true(blocking_fallback_turn_flags)
    late_fallback_count = int(fallback_windows.get("late", 0))
    early_middle_fallback_count = int(fallback_windows.get("early", 0)) + int(fallback_windows.get("middle", 0))
    escalation_warnings: list[str] = []
    if max_blocking_streak > 1:
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
    if blocking_unavailable_with_fallback_count > 1:
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
        "max_scene_action_nonblocking_fallback_streak": max_scene_action_nonblocking_streak,
        "max_blocking_fallback_streak": max_blocking_streak,
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
        "blocking_unavailable_with_fallback_count": blocking_unavailable_with_fallback_count,
        "scene_action_speaker_optional_unavailable_count": scene_action_speaker_optional_unavailable_count,
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
    lineage_summary = build_runtime_lineage_summary(lineage_events)
    fallback_escalation_summary = summarize_fallback_escalation_observations(turns)
    response_delta_summary = summarize_response_delta_observations(turns)

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
        "response_delta_summary": response_delta_summary,
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
    response_delta = summary.get("response_delta_summary") if isinstance(summary.get("response_delta_summary"), Mapping) else {}
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
        (
            "- Max fallback streak blocking / scene-action nonblocking: "
            f"`{fallback_escalation.get('max_blocking_fallback_streak', 0)}` / "
            f"`{fallback_escalation.get('max_scene_action_nonblocking_fallback_streak', 0)}`"
        ),
        f"- Late-window fallback count: `{fallback_escalation.get('late_window_fallback_count', 0)}`",
        (
            "- Fallback unavailable blocking / scene-action speaker optional: "
            f"`{fallback_escalation.get('blocking_unavailable_with_fallback_count', 0)}` / "
            f"`{fallback_escalation.get('scene_action_speaker_optional_unavailable_count', 0)}`"
        ),
        f"- Fallback escalation warnings: `{fallback_escalation.get('escalation_warnings', [])}`",
        f"- Mutation turn count: `{summary.get('mutation_turn_count')}`",
        f"- Response-delta checked / failed / repaired: "
        f"`{response_delta.get('response_delta_checked_count', 0)}` / "
        f"`{response_delta.get('response_delta_failed_count', 0)}` / "
        f"`{response_delta.get('response_delta_repaired_count', 0)}`",
        f"- Response-delta kinds: `{response_delta.get('response_delta_kind_counts', {})}`",
        f"- Response-delta unknown count: `{response_delta.get('response_delta_unknown_count', 0)}`",
        f"- Echo-overlap bands: `{response_delta.get('echo_overlap_band_counts', {})}`",
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


def _observed_turn(
    *,
    scenario_id: str,
    snap: dict[str, Any],
    payload: dict[str, Any],
    replay_identity: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Backward-compatible wrapper around ``project_turn_observation``."""
    return project_turn_observation(
        {
            "scenario_id": scenario_id,
            "snap": snap,
            "payload": payload,
            "replay_identity": replay_identity,
        }
    )


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
    source_path: str | Path | None = None,
    branch_id: str | None = None,
    turn_ids: list[str] | None = None,
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
        replay_identity: dict[str, Any] = {}
        if source_path is not None:
            replay_identity["source_path"] = str(source_path)
        if branch_id is not None:
            replay_identity["branch_id"] = str(branch_id)
        if turn_ids is not None and i < len(turn_ids) and str(turn_ids[i]).strip():
            replay_identity["turn_id"] = str(turn_ids[i])
        observed_turns.append(
            _observed_turn(
                scenario_id=scenario_id,
                snap=snap,
                payload=payload,
                replay_identity=replay_identity,
            )
        )

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
                f"turn[{turn.get('turn_index')}].source_path: {turn.get('source_path')!r}",
                f"turn[{turn.get('turn_index')}].branch_id: {turn.get('branch_id')!r}",
                f"turn[{turn.get('turn_index')}].turn_id: {turn.get('turn_id')!r}",
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
